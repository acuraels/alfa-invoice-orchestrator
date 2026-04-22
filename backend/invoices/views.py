import csv
import os
from io import StringIO

from django.db import connection
from django.http import HttpResponse
from django.utils import timezone
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest, multiprocess
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.role_scope import RoleScopedQuerysetMixin
from invoices.metrics import (
    transactions_duplicate_total,
    transactions_invalid_schema_total,
    transactions_published_total,
    transactions_received_total,
)
from invoices.models import (
    AggregationGroup,
    DraftInvoice,
    ExportRecord,
    FinalInvoice,
    IdempotencyRecord,
    InboundMessageLog,
    ProcessingError,
    RawTransaction,
)
from invoices.schemas import TransactionPayloadSerializer
from invoices.serializers import (
    AggregationGroupSerializer,
    DraftInvoiceSerializer,
    ExportRecordSerializer,
    FinalInvoiceSerializer,
    InboundMessageLogSerializer,
    ProcessingErrorSerializer,
    RawTransactionSerializer,
)
from invoices.services import reprocess_aggregation_group, retry_final_invoice, summary_snapshot
from invoices.tasks import process_transaction_task
from invoices.utils import stable_payload_hash


class HealthzView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        return Response({"status": "ok", "time": timezone.now().isoformat()})


class ReadyzView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception as exc:  # noqa: BLE001
            return Response({"status": "error", "db": str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({"status": "ready", "db": "ok"})


class MetricsView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        multiproc_dir = os.getenv("PROMETHEUS_MULTIPROC_DIR")
        if multiproc_dir:
            registry = CollectorRegistry()
            multiprocess.MultiProcessCollector(registry)
            return HttpResponse(generate_latest(registry), content_type=CONTENT_TYPE_LATEST)
        return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)


class IngestTransactionsView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        payloads = request.data
        if isinstance(payloads, dict) and "transactions" in payloads:
            payloads = payloads["transactions"]

        if not isinstance(payloads, list):
            return Response({"detail": "Expected array of transactions"}, status=status.HTTP_400_BAD_REQUEST)

        accepted = 0
        duplicates = 0
        published = 0
        invalid = 0

        for payload in payloads:
            tx_serializer = TransactionPayloadSerializer(data=payload)
            if not tx_serializer.is_valid():
                invalid += 1
                transactions_invalid_schema_total.inc()
                InboundMessageLog.objects.create(
                    drf=str(payload.get("drf", "")),
                    source=InboundMessageLog.Source.API,
                    payload_hash=stable_payload_hash(payload),
                    payload=payload,
                    status=InboundMessageLog.Status.VALIDATION_ERROR,
                    error_message=str(tx_serializer.errors),
                )
                continue

            tx = tx_serializer.validated_data
            payload_hash = stable_payload_hash(payload)
            transactions_received_total.labels(type=tx["type"]).inc()
            accepted += 1

            if IdempotencyRecord.objects.filter(payload_hash=payload_hash).exists():
                duplicates += 1
                transactions_duplicate_total.inc()
                InboundMessageLog.objects.create(
                    drf=tx["drf"],
                    source=InboundMessageLog.Source.API,
                    payload_hash=payload_hash,
                    payload=payload,
                    status=InboundMessageLog.Status.DUPLICATE,
                    error_message="Duplicate on ingest",
                )
                continue

            inbound = InboundMessageLog.objects.create(
                drf=tx["drf"],
                source=InboundMessageLog.Source.API,
                payload_hash=payload_hash,
                payload=payload,
                status=InboundMessageLog.Status.RECEIVED,
            )
            process_transaction_task.apply_async(
                args=[payload, inbound.id, InboundMessageLog.Source.API],
                queue="transactions",
            )
            inbound.status = InboundMessageLog.Status.PUBLISHED
            inbound.save(update_fields=["status", "updated_at"])
            published += 1
            transactions_published_total.inc()

        return Response(
            {
                "accepted": accepted,
                "duplicates": duplicates,
                "published": published,
                "invalid": invalid,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class RawTransactionViewSet(RoleScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = RawTransactionSerializer
    queryset = RawTransaction.objects.select_related("counterparty", "department").all().order_by("-received_at")
    role_scope_department_field = "department__code"


class AggregationGroupViewSet(RoleScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = AggregationGroupSerializer
    queryset = (
        AggregationGroup.objects.select_related("counterparty", "department")
        .all()
        .order_by("-updated_at")
    )
    role_scope_department_field = "department__code"

    @action(detail=True, methods=["post"])
    def reprocess(self, request, pk=None):
        group = self.get_object()
        draft = reprocess_aggregation_group(group)
        return Response(
            {
                "group_id": group.id,
                "status": group.status,
                "draft_invoice_id": getattr(draft, "id", None),
            }
        )


class DraftInvoiceViewSet(RoleScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = DraftInvoiceSerializer
    queryset = (
        DraftInvoice.objects.select_related("group", "counterparty", "department")
        .prefetch_related("lines")
        .all()
        .order_by("-updated_at")
    )
    role_scope_department_field = "department__code"


class FinalInvoiceViewSet(RoleScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = FinalInvoiceSerializer
    queryset = (
        FinalInvoice.objects.select_related("counterparty", "department", "draft_invoice")
        .prefetch_related("lines")
        .all()
        .order_by("-created_at")
    )
    role_scope_department_field = "department__code"

    @action(detail=True, methods=["post"])
    def retry(self, request, pk=None):
        final_invoice = self.get_object()
        export_record = retry_final_invoice(final_invoice)
        return Response(
            {
                "final_invoice_id": final_invoice.id,
                "export_record_id": export_record.id,
                "status": export_record.status,
            }
        )


class ExportRecordViewSet(RoleScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = ExportRecordSerializer
    queryset = (
        ExportRecord.objects.select_related("final_invoice")
        .prefetch_related("attempts")
        .all()
        .order_by("-updated_at")
    )
    role_scope_department_field = "final_invoice__department__code"


class ProcessingErrorViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = ProcessingErrorSerializer
    queryset = ProcessingError.objects.all().order_by("-created_at")


class InboundLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = InboundMessageLogSerializer
    queryset = InboundMessageLog.objects.all().order_by("-received_at")


class SummaryReportView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(summary_snapshot())


class LoadTestSummaryView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(summary_snapshot())


class ExportCsvReportView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        invoices = FinalInvoice.objects.select_related("department", "counterparty").order_by("-created_at")
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(
            [
                "number",
                "drf",
                "department",
                "counterparty",
                "issue_date",
                "vat_rate",
                "total_vat_amount",
                "total_with_vat",
                "status",
                "export_status",
            ]
        )
        for invoice in invoices:
            writer.writerow(
                [
                    invoice.number,
                    invoice.drf,
                    invoice.department.code,
                    invoice.counterparty.name,
                    invoice.issue_date.isoformat(),
                    str(invoice.vat_rate),
                    str(invoice.total_vat_amount),
                    str(invoice.total_with_vat),
                    invoice.status,
                    invoice.export_status,
                ]
            )

        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="final_invoices.csv"'
        return response
