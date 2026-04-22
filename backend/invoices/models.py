from decimal import Decimal

from django.conf import settings
from django.db import models


class Department(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=128)
    mnemonic = models.CharField(max_length=8)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["code"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class Counterparty(models.Model):
    id = models.PositiveIntegerField(primary_key=True)
    name = models.CharField(max_length=255)
    inn = models.CharField(max_length=16, blank=True, default="")
    kpp = models.CharField(max_length=16, blank=True, default="")
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["inn"]),
        ]

    def __str__(self) -> str:
        return f"{self.id} {self.name}"


class DepartmentAccess(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="department_access")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="user_access")
    role = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "department"], name="uniq_department_access"),
        ]


class InboundMessageLog(models.Model):
    class Source(models.TextChoices):
        API = "API", "API"
        SCRIPT = "SCRIPT", "Script"
        RABBIT_DIRECT = "RABBIT_DIRECT", "Rabbit direct"

    class Status(models.TextChoices):
        RECEIVED = "RECEIVED", "Received"
        PUBLISHED = "PUBLISHED", "Published"
        PROCESSING = "PROCESSING", "Processing"
        PROCESSED = "PROCESSED", "Processed"
        VALIDATION_ERROR = "VALIDATION_ERROR", "Validation error"
        DUPLICATE = "DUPLICATE", "Duplicate"
        ERROR = "ERROR", "Error"

    message_id = models.CharField(max_length=64, blank=True, default="")
    drf = models.CharField(max_length=64, blank=True, default="")
    source = models.CharField(max_length=32, choices=Source.choices, default=Source.API)
    payload_hash = models.CharField(max_length=64)
    payload = models.JSONField()
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.RECEIVED)
    error_message = models.TextField(blank=True, default="")
    received_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["drf"]),
            models.Index(fields=["status"]),
            models.Index(fields=["received_at"]),
            models.Index(fields=["payload_hash"]),
        ]


class AggregationGroup(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        READY = "READY", "Ready"
        DRAFT = "DRAFT", "Draft built"
        VALIDATION_ERROR = "VALIDATION_ERROR", "Validation error"
        MATERIALIZED = "MATERIALIZED", "Materialized"

    drf = models.CharField(max_length=64, unique=True)
    counterparty = models.ForeignKey(
        Counterparty,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="aggregation_groups",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="aggregation_groups",
    )
    transaction_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.OPEN)
    income_count = models.PositiveIntegerField(default=0)
    vat_count = models.PositiveIntegerField(default=0)
    total_count = models.PositiveIntegerField(default=0)
    validation_error = models.TextField(blank=True, default="")
    last_processed_at = models.DateTimeField(null=True, blank=True)
    ready_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["drf"]),
            models.Index(fields=["status"]),
            models.Index(fields=["transaction_date"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["updated_at"]),
            models.Index(fields=["counterparty"]),
            models.Index(fields=["department"]),
        ]

    def __str__(self) -> str:
        return f"{self.drf} [{self.status}]"


class RawTransaction(models.Model):
    class TxType(models.TextChoices):
        INCOME = "INCOME", "Income"
        VAT = "VAT", "VAT"

    class Status(models.TextChoices):
        RECEIVED = "RECEIVED", "Received"
        VALIDATION_ERROR = "VALIDATION_ERROR", "Validation error"
        DUPLICATE = "DUPLICATE", "Duplicate"
        PROCESSED = "PROCESSED", "Processed"

    inbound_log = models.ForeignKey(
        InboundMessageLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="raw_transactions",
    )
    aggregation_group = models.ForeignKey(
        AggregationGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="raw_transactions",
    )
    external_id = models.CharField(max_length=128, blank=True, default="")
    drf = models.CharField(max_length=64)
    transaction_type = models.CharField(max_length=16, choices=TxType.choices)
    counterparty = models.ForeignKey(
        Counterparty,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="raw_transactions",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="raw_transactions",
    )
    invoice = models.ForeignKey(
        "FinalInvoice",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    transaction_date = models.DateField(null=True, blank=True)

    product_name = models.CharField(max_length=255, blank=True, default="")
    unit_measure = models.CharField(max_length=32, blank=True, default="")
    quantity = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    unit_price = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    vat_rate = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal("0"))
    vat_amount = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))

    payload_hash = models.CharField(max_length=64)
    payload = models.JSONField()
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.RECEIVED)
    validation_error = models.TextField(blank=True, default="")
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["drf"]),
            models.Index(fields=["status"]),
            models.Index(fields=["transaction_date"]),
            models.Index(fields=["received_at"]),
            models.Index(fields=["payload_hash"]),
            models.Index(fields=["counterparty"]),
            models.Index(fields=["department"]),
            models.Index(fields=["invoice"]),
        ]


class IdempotencyRecord(models.Model):
    payload_hash = models.CharField(max_length=64, unique=True)
    drf = models.CharField(max_length=64, blank=True, default="")
    source = models.CharField(max_length=32, blank=True, default="")
    inbound_log = models.ForeignKey(
        InboundMessageLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="idempotency_records",
    )
    raw_transaction = models.ForeignKey(
        RawTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="idempotency_records",
    )
    times_seen = models.PositiveIntegerField(default=1)
    first_seen_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["payload_hash"]),
            models.Index(fields=["drf"]),
            models.Index(fields=["first_seen_at"]),
        ]


class DraftInvoice(models.Model):
    class Status(models.TextChoices):
        PROJECT_CREATED = "project_created", "Project created"
        VALIDATING_ERROR = "validating_error", "Validating error"

    group = models.OneToOneField(AggregationGroup, on_delete=models.CASCADE, related_name="draft_invoice")
    counterparty = models.ForeignKey(Counterparty, on_delete=models.PROTECT, related_name="draft_invoices")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="draft_invoices")
    transaction_date = models.DateField()
    vat_rate = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal("0"))
    total_vat_amount = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    total_with_vat = models.DecimalField(max_digits=16, decimal_places=4, default=Decimal("0"))
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PROJECT_CREATED)
    validation_error = models.TextField(blank=True, default="")
    retry_count = models.PositiveIntegerField(default=0)
    materialized_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["transaction_date"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["department"]),
            models.Index(fields=["counterparty"]),
        ]


class DraftInvoiceLine(models.Model):
    draft_invoice = models.ForeignKey(DraftInvoice, on_delete=models.CASCADE, related_name="lines")
    raw_transaction = models.ForeignKey(
        RawTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="draft_lines",
    )
    line_no = models.PositiveIntegerField()
    product_name = models.CharField(max_length=255)
    unit = models.CharField(max_length=32)
    quantity = models.DecimalField(max_digits=16, decimal_places=4)
    unit_price = models.DecimalField(max_digits=16, decimal_places=4)
    amount_without_vat = models.DecimalField(max_digits=16, decimal_places=4)
    vat_amount = models.DecimalField(max_digits=16, decimal_places=4)
    total_amount = models.DecimalField(max_digits=16, decimal_places=4)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["draft_invoice", "line_no"], name="uniq_draft_line_no"),
        ]


class InvoiceNumberSequence(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="invoice_sequences")
    sequence_date = models.DateField()
    version = models.CharField(max_length=2, default="00")
    last_value = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["department", "sequence_date", "version"],
                name="uniq_department_sequence_daily",
            ),
        ]
        indexes = [
            models.Index(fields=["sequence_date"]),
            models.Index(fields=["department", "sequence_date"]),
        ]


class FinalInvoice(models.Model):
    class Status(models.TextChoices):
        INVOICE_CREATED = "invoice_created", "Invoice created"
        SENDING_ERROR = "sending_error", "Sending error"
        SENT = "sent", "Sent"

    draft_invoice = models.OneToOneField(
        DraftInvoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="final_invoice",
    )
    invoice_number = models.CharField(max_length=64, unique=True)
    drf = models.CharField(max_length=64)
    counterparty = models.ForeignKey(Counterparty, on_delete=models.PROTECT, related_name="final_invoices")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="final_invoices")
    transaction_date = models.DateField()
    vat_rate = models.DecimalField(max_digits=6, decimal_places=4)
    total_vat_amount = models.DecimalField(max_digits=16, decimal_places=4)
    total_with_vat = models.DecimalField(max_digits=16, decimal_places=4)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.INVOICE_CREATED)
    export_status = models.CharField(max_length=32, choices=Status.choices, default=Status.INVOICE_CREATED)
    materialized_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["drf"]),
            models.Index(fields=["status"]),
            models.Index(fields=["export_status"]),
            models.Index(fields=["transaction_date"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["department"]),
            models.Index(fields=["counterparty"]),
        ]


class FinalInvoiceLine(models.Model):
    final_invoice = models.ForeignKey(FinalInvoice, on_delete=models.CASCADE, related_name="lines")
    line_no = models.PositiveIntegerField()
    product_name = models.CharField(max_length=255)
    unit = models.CharField(max_length=32)
    quantity = models.DecimalField(max_digits=16, decimal_places=4)
    unit_price = models.DecimalField(max_digits=16, decimal_places=4)
    amount_without_vat = models.DecimalField(max_digits=16, decimal_places=4)
    vat_amount = models.DecimalField(max_digits=16, decimal_places=4)
    total_amount = models.DecimalField(max_digits=16, decimal_places=4)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["final_invoice", "line_no"], name="uniq_final_line_no"),
        ]


class ExportRecord(models.Model):
    class Status(models.TextChoices):
        READY = "READY", "Ready"
        SENT = "SENT", "Sent"
        ERROR = "ERROR", "Error"
        RETRY_PENDING = "RETRY_PENDING", "Retry pending"

    final_invoice = models.OneToOneField(FinalInvoice, on_delete=models.CASCADE, related_name="export_record")
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.READY)
    destination = models.CharField(max_length=64, default="csv")
    last_error = models.TextField(blank=True, default="")
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    exported_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["updated_at"]),
        ]


class ExportAttempt(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        ERROR = "ERROR", "Error"

    export_record = models.ForeignKey(ExportRecord, on_delete=models.CASCADE, related_name="attempts")
    attempt_no = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=Status.choices)
    duration_ms = models.PositiveIntegerField(default=0)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["export_record", "attempt_no"], name="uniq_export_attempt_no"),
        ]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]


class InvoiceStatusHistory(models.Model):
    final_invoice = models.ForeignKey(FinalInvoice, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=32, blank=True, default="")
    to_status = models.CharField(max_length=32)
    reason = models.CharField(max_length=255, blank=True, default="")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoice_status_changes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["to_status"]),
        ]


class InvoiceFieldChangeHistory(models.Model):
    final_invoice = models.ForeignKey(FinalInvoice, on_delete=models.CASCADE, related_name="field_history")
    field_name = models.CharField(max_length=128)
    old_value = models.TextField(blank=True, default="")
    new_value = models.TextField(blank=True, default="")
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoice_field_changes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["field_name"]),
            models.Index(fields=["created_at"]),
        ]


class MaterializationJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SUCCESS = "SUCCESS", "Success"
        ERROR = "ERROR", "Error"
        RETRY = "RETRY", "Retry"

    group = models.ForeignKey(
        AggregationGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="materialization_jobs",
    )
    draft_invoice = models.ForeignKey(
        DraftInvoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="materialization_jobs",
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    attempt = models.PositiveIntegerField(default=1)
    error_message = models.TextField(blank=True, default="")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["started_at"]),
        ]


class ProcessingError(models.Model):
    class Stage(models.TextChoices):
        INGEST = "INGEST", "Ingest"
        PROCESSOR = "PROCESSOR", "Processor"
        AGGREGATION = "AGGREGATION", "Aggregation"
        MATERIALIZATION = "MATERIALIZATION", "Materialization"
        EXPORT = "EXPORT", "Export"

    stage = models.CharField(max_length=32, choices=Stage.choices)
    code = models.CharField(max_length=64)
    message = models.TextField()
    payload = models.JSONField(default=dict, blank=True)
    retryable = models.BooleanField(default=True)
    resolved = models.BooleanField(default=False)
    raw_transaction = models.ForeignKey(
        RawTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processing_errors",
    )
    aggregation_group = models.ForeignKey(
        AggregationGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processing_errors",
    )
    draft_invoice = models.ForeignKey(
        DraftInvoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processing_errors",
    )
    final_invoice = models.ForeignKey(
        FinalInvoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processing_errors",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["stage"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["resolved"]),
        ]
