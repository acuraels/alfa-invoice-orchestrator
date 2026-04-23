import csv
import os
from io import StringIO

from django.db import connection
from django.db.models import Q
from django.http import HttpResponse
from django.utils import timezone
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, generate_latest, multiprocess
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.role_scope import RoleScopedQuerysetMixin, filter_queryset_by_role
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
from invoices.schemas import InvoiceListQuerySerializer, TransactionPayloadSerializer
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
                "sequence_number",
                "department",
                "counterparty",
                "issue_date",
                "vat_rate",
                "total_vat_amount",
                "total_with_vat",
                "status",
            ]
        )
        for invoice in invoices:
            writer.writerow(
                [
                    invoice.number,
                    invoice.sequence_number,
                    invoice.department.code,
                    invoice.counterparty.name,
                    invoice.issue_date.isoformat(),
                    str(invoice.vat_rate),
                    str(invoice.total_vat_amount),
                    str(invoice.total_with_vat),
                    invoice.status,
                ]
            )

        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="final_invoices.csv"'
        return response


class InvoiceListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        raw_status = request.query_params.getlist("status")
        raw_department_ids = request.query_params.getlist("departmentId")
        data = {
            "tab": request.query_params.get("tab"),
            "counterparty": request.query_params.get("counterparty", ""),
        }

        if request.query_params.get("dateFrom") is not None:
            data["dateFrom"] = request.query_params.get("dateFrom")
        if request.query_params.get("dateTo") is not None:
            data["dateTo"] = request.query_params.get("dateTo")
        if raw_status:
            data["status"] = raw_status
        if raw_department_ids:
            data["departmentId"] = raw_department_ids
        if request.query_params.get("page") is not None:
            data["page"] = request.query_params.get("page")
        if request.query_params.get("size") is not None:
            data["size"] = request.query_params.get("size")

        serializer = InvoiceListQuerySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        params = serializer.validated_data

        statuses = params.get("status")
        if not statuses:
            if params["tab"] == "to_process":
                statuses = [
                    DraftInvoice.Status.PROJECT_CREATED,
                    DraftInvoice.Status.VALIDATING_ERROR,
                ]
            else:
                statuses = [
                    FinalInvoice.Status.INVOICE_CREATED,
                    FinalInvoice.Status.SENDING_ERROR,
                    FinalInvoice.Status.SENT,
                ]

        draft_statuses = [status for status in statuses if status in DraftInvoice.Status.values]
        final_statuses = [status for status in statuses if status in FinalInvoice.Status.values]

        counterparty = params.get("counterparty", "").strip()
        date_from = params.get("dateFrom")
        date_to = params.get("dateTo")
        department_ids = params.get("departmentId") or []

        draft_qs = DraftInvoice.objects.select_related("group", "counterparty", "department").all()
        final_qs = FinalInvoice.objects.select_related("counterparty", "department").all()

        draft_qs = filter_queryset_by_role(draft_qs, request.user, "department")
        final_qs = filter_queryset_by_role(final_qs, request.user, "department")

        if counterparty:
            search_filter = Q(counterparty__name__icontains=counterparty) | Q(
                counterparty__inn__icontains=counterparty
            )
            draft_qs = draft_qs.filter(search_filter)
            final_qs = final_qs.filter(search_filter)

        if date_from:
            draft_qs = draft_qs.filter(transaction_date__gte=date_from)
            final_qs = final_qs.filter(issue_date__gte=date_from)

        if date_to:
            draft_qs = draft_qs.filter(transaction_date__lte=date_to)
            final_qs = final_qs.filter(issue_date__lte=date_to)

        if department_ids:
            draft_qs = draft_qs.filter(department__public_id__in=department_ids)
            final_qs = final_qs.filter(department__public_id__in=department_ids)

        if draft_statuses:
            draft_qs = draft_qs.filter(status__in=draft_statuses)
        else:
            draft_qs = draft_qs.none()

        if final_statuses:
            final_qs = final_qs.filter(status__in=final_statuses)
        else:
            final_qs = final_qs.none()

        items = []
        for draft in draft_qs:
            issue_date = draft.transaction_date
            items.append(
                {
                    "id": str(draft.id),
                    "number": draft.group.drf,
                    "counterpartyName": draft.counterparty.name,
                    "status": draft.status,
                    "issueDate": issue_date.isoformat() if issue_date else None,
                    "_sort_date": issue_date or draft.created_at.date(),
                    "_created_at": draft.created_at,
                }
            )

        for final_invoice in final_qs:
            issue_date = final_invoice.issue_date
            items.append(
                {
                    "id": str(final_invoice.id),
                    "number": final_invoice.number,
                    "counterpartyName": final_invoice.counterparty.name,
                    "status": final_invoice.status,
                    "issueDate": issue_date.isoformat() if issue_date else None,
                    "_sort_date": issue_date or final_invoice.created_at.date(),
                    "_created_at": final_invoice.created_at,
                }
            )

        items.sort(key=lambda item: (item["_sort_date"], item["_created_at"]), reverse=True)

        total_elements = len(items)
        size = params["size"]
        page = params["page"]
        total_pages = (total_elements + size - 1) // size if total_elements else 0
        start = (page - 1) * size
        end = start + size

        page_items = items[start:end]
        for item in page_items:
            item.pop("_sort_date", None)
            item.pop("_created_at", None)

        return Response(
            {
                "totalElements": total_elements,
                "totalPages": total_pages,
                "items": page_items,
            }
        )
