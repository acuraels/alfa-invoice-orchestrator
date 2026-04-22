from rest_framework import serializers

from invoices.models import (
    AggregationGroup,
    DraftInvoice,
    DraftInvoiceLine,
    ExportAttempt,
    ExportRecord,
    FinalInvoice,
    FinalInvoiceLine,
    InboundMessageLog,
    ProcessingError,
    RawTransaction,
)
from invoices.schemas import IngestTransactionsSerializer


class RawTransactionSerializer(serializers.ModelSerializer):
    counterparty_name = serializers.CharField(source="counterparty.name", read_only=True)
    department_code = serializers.CharField(source="department.code", read_only=True)
    counterparty_id = serializers.UUIDField(source="counterparty.public_id", read_only=True)
    department_id = serializers.UUIDField(source="department.public_id", read_only=True)

    class Meta:
        model = RawTransaction
        fields = [
            "id",
            "external_id",
            "drf",
            "transaction_type",
            "counterparty",
            "counterparty_name",
            "counterparty_id",
            "department",
            "department_code",
            "department_id",
            "transaction_date",
            "amount",
            "debit_account",
            "credit_account",
            "product_name",
            "unit_measure",
            "quantity",
            "unit_price",
            "vat_rate",
            "vat_amount",
            "created_at",
            "status",
            "validation_error",
            "payload_hash",
            "received_at",
            "processed_at",
        ]


class AggregationGroupSerializer(serializers.ModelSerializer):
    counterparty_name = serializers.CharField(source="counterparty.name", read_only=True)
    department_code = serializers.CharField(source="department.code", read_only=True)

    class Meta:
        model = AggregationGroup
        fields = [
            "id",
            "drf",
            "status",
            "counterparty",
            "counterparty_name",
            "department",
            "department_code",
            "transaction_date",
            "income_count",
            "vat_count",
            "total_count",
            "validation_error",
            "ready_at",
            "created_at",
            "updated_at",
        ]


class DraftInvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = DraftInvoiceLine
        fields = [
            "id",
            "line_no",
            "product_name",
            "unit",
            "quantity",
            "unit_price",
            "amount_without_vat",
            "vat_amount",
            "total_amount",
        ]


class DraftInvoiceSerializer(serializers.ModelSerializer):
    lines = DraftInvoiceLineSerializer(many=True, read_only=True)
    drf = serializers.CharField(source="group.drf", read_only=True)
    counterparty_name = serializers.CharField(source="counterparty.name", read_only=True)
    department_code = serializers.CharField(source="department.code", read_only=True)

    class Meta:
        model = DraftInvoice
        fields = [
            "id",
            "group",
            "drf",
            "counterparty",
            "counterparty_name",
            "department",
            "department_code",
            "transaction_date",
            "vat_rate",
            "total_vat_amount",
            "total_with_vat",
            "status",
            "validation_error",
            "retry_count",
            "materialized_at",
            "created_at",
            "updated_at",
            "lines",
        ]


class FinalInvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinalInvoiceLine
        fields = [
            "product_name",
            "unit",
            "quantity",
            "unit_price",
            "amount_without_vat",
            "vat_amount",
            "total_amount",
        ]


class FinalInvoiceSerializer(serializers.ModelSerializer):
    lines = FinalInvoiceLineSerializer(many=True, read_only=True)
    counterpartyId = serializers.UUIDField(source="counterparty.public_id", read_only=True)
    createdAt = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = FinalInvoice
        fields = [
            "number",
            "issue_date",
            "counterpartyId",
            "payment_doc_number",
            "payment_doc_date",
            "vat_rate",
            "total_vat_amount",
            "total_with_vat",
            "createdAt",
            "lines",
        ]


class ExportAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExportAttempt
        fields = ["id", "attempt_no", "status", "duration_ms", "error_message", "created_at"]


class ExportRecordSerializer(serializers.ModelSerializer):
    attempts = ExportAttemptSerializer(many=True, read_only=True)
    invoice_number = serializers.CharField(source="final_invoice.number", read_only=True)

    class Meta:
        model = ExportRecord
        fields = [
            "id",
            "final_invoice",
            "invoice_number",
            "status",
            "destination",
            "last_error",
            "last_attempt_at",
            "exported_at",
            "created_at",
            "updated_at",
            "attempts",
        ]


class ProcessingErrorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProcessingError
        fields = [
            "id",
            "stage",
            "code",
            "message",
            "retryable",
            "resolved",
            "raw_transaction",
            "aggregation_group",
            "draft_invoice",
            "final_invoice",
            "created_at",
        ]


class InboundMessageLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = InboundMessageLog
        fields = [
            "id",
            "message_id",
            "drf",
            "source",
            "payload_hash",
            "status",
            "error_message",
            "received_at",
            "updated_at",
        ]


class IngestRequestSerializer(IngestTransactionsSerializer):
    pass


class IngestResponseSerializer(serializers.Serializer):
    accepted = serializers.IntegerField()
    duplicates = serializers.IntegerField()
    published = serializers.IntegerField()
    invalid = serializers.IntegerField()
