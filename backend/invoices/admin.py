from django.contrib import admin

from invoices import models


@admin.register(models.Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "mnemonic")
    list_filter = ("code",)
    search_fields = ("name", "code", "mnemonic")


@admin.register(models.Counterparty)
class CounterpartyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "address", "inn")
    search_fields = ("name", "inn", "address")


@admin.register(models.DepartmentAccess)
class DepartmentAccessAdmin(admin.ModelAdmin):
    list_display = ("user", "department")
    list_filter = ("department",)


@admin.register(models.RawTransaction)
class RawTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "drf",
        "type",
        "status",
        "department",
        "counterparty",
        "date",
        "received_at",
    )
    list_filter = ("status", "type", "department", "date")
    search_fields = ("drf", "external_id", "payload_hash")


@admin.register(models.AggregationGroup)
class AggregationGroupAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "drf",
        "status",
        "income_count",
        "vat_count",
        "total_count",
        "department",
        "counterparty",
        "transaction_date",
        "updated_at",
    )
    list_filter = ("status", "department", "transaction_date")
    search_fields = ("drf",)


class DraftInvoiceLineInline(admin.TabularInline):
    model = models.DraftInvoiceLine
    extra = 0


@admin.register(models.DraftInvoice)
class DraftInvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "group",
        "status",
        "department",
        "counterparty",
        "transaction_date",
        "total_with_vat",
        "total_vat_amount",
    )
    list_filter = ("status", "department", "transaction_date")
    search_fields = ("group__drf",)
    inlines = [DraftInvoiceLineInline]


class FinalInvoiceLineInline(admin.TabularInline):
    model = models.FinalInvoiceLine
    extra = 0


@admin.register(models.FinalInvoice)
class FinalInvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "number",
        "sequence_number",
        "status",
        "department",
        "issue_date",
        "total_with_vat",
    )
    list_filter = ("status", "department", "issue_date")
    search_fields = ("number", "sequence_number")
    inlines = [FinalInvoiceLineInline]


@admin.register(models.ExportRecord)
class ExportRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "final_invoice", "status", "destination", "updated_at")
    list_filter = ("status", "destination")


@admin.register(models.ProcessingError)
class ProcessingErrorAdmin(admin.ModelAdmin):
    list_display = ("id", "stage", "code", "retryable", "resolved", "created_at")
    list_filter = ("stage", "retryable", "resolved")
    search_fields = ("code", "message")


@admin.register(models.InboundMessageLog)
class InboundMessageLogAdmin(admin.ModelAdmin):
    list_display = ("id", "drf", "source", "status", "received_at")
    list_filter = ("source", "status")
    search_fields = ("drf", "payload_hash", "message_id")


@admin.register(models.IdempotencyRecord)
class IdempotencyRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "payload_hash", "drf", "times_seen", "first_seen_at", "last_seen_at")
    search_fields = ("payload_hash", "drf")


@admin.register(models.InvoiceNumberSequence)
class InvoiceNumberSequenceAdmin(admin.ModelAdmin):
    list_display = ("department", "sequence_date", "version", "last_value", "updated_at")
    list_filter = ("department", "version", "sequence_date")


@admin.register(models.InvoiceStatusHistory)
class InvoiceStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("final_invoice", "from_status", "to_status", "changed_by", "created_at")
    list_filter = ("to_status", "created_at")


@admin.register(models.InvoiceFieldChangeHistory)
class InvoiceFieldChangeHistoryAdmin(admin.ModelAdmin):
    list_display = ("final_invoice", "field_name", "changed_by", "created_at")
    list_filter = ("field_name", "created_at")


@admin.register(models.MaterializationJob)
class MaterializationJobAdmin(admin.ModelAdmin):
    list_display = ("id", "group", "draft_invoice", "status", "attempt", "started_at", "finished_at")
    list_filter = ("status",)


@admin.register(models.ExportAttempt)
class ExportAttemptAdmin(admin.ModelAdmin):
    list_display = ("id", "export_record", "attempt_no", "status", "duration_ms", "created_at")
    list_filter = ("status",)
