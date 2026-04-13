from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from time import perf_counter

from django.db import IntegrityError, transaction
from django.db.models import Count, F, Min, Q
from django.utils import timezone

from invoices.metrics import (
    aggregation_group_size_histogram,
    aggregation_groups_created_total,
    aggregation_groups_ready_total,
    aggregation_groups_validation_error_total,
    db_read_duration_seconds,
    db_write_duration_seconds,
    draft_invoices_created_total,
    draft_invoices_validation_error_total,
    export_attempt_duration_seconds,
    final_invoices_created_total,
    final_invoices_export_error_total,
    final_invoices_export_ready_total,
    layer2_materialization_duration_seconds,
    layer2_materialization_error_total,
    layer2_materialization_total,
    last_successful_processing_timestamp,
    open_groups_gauge,
    queue_backlog_gauge,
    retry_attempts_total,
    transaction_to_draft_latency_seconds,
    transfer_backlog_gauge,
    transactions_ack_total,
    transactions_duplicate_total,
    transactions_invalid_schema_total,
)
from invoices.models import (
    AggregationGroup,
    Counterparty,
    Department,
    DraftInvoice,
    DraftInvoiceLine,
    ExportAttempt,
    ExportRecord,
    FinalInvoice,
    FinalInvoiceLine,
    IdempotencyRecord,
    InboundMessageLog,
    InvoiceFieldChangeHistory,
    InvoiceNumberSequence,
    InvoiceStatusHistory,
    MaterializationJob,
    ProcessingError,
    RawTransaction,
)
from invoices.schemas import TransactionPayloadSerializer
from invoices.utils import stable_payload_hash

MONEY_QUANT = Decimal("0.0001")
VAT_TOLERANCE = Decimal("0.05")


@dataclass
class ProcessResult:
    status: str
    message: str = ""
    group_id: int | None = None
    draft_invoice_id: int | None = None


def q(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def _record_error(
    *,
    stage: str,
    code: str,
    message: str,
    payload: dict,
    retryable: bool = True,
    raw_transaction: RawTransaction | None = None,
    group: AggregationGroup | None = None,
    draft: DraftInvoice | None = None,
    final: FinalInvoice | None = None,
) -> ProcessingError:
    return ProcessingError.objects.create(
        stage=stage,
        code=code,
        message=message,
        payload=payload,
        retryable=retryable,
        raw_transaction=raw_transaction,
        aggregation_group=group,
        draft_invoice=draft,
        final_invoice=final,
    )


def _update_gauges() -> None:
    start = perf_counter()
    open_count = AggregationGroup.objects.filter(status=AggregationGroup.Status.OPEN).count()
    backlog = InboundMessageLog.objects.filter(
        status__in=[
            InboundMessageLog.Status.RECEIVED,
            InboundMessageLog.Status.PUBLISHED,
            InboundMessageLog.Status.PROCESSING,
        ]
    ).count()
    db_read_duration_seconds.observe(perf_counter() - start)
    open_groups_gauge.set(open_count)
    queue_backlog_gauge.set(backlog)


def _get_refs(payload: dict) -> tuple[Counterparty, Department]:
    counterparty = Counterparty.objects.get(pk=payload["counterpartyId"])
    department = Department.objects.get(pk=payload["departmentId"])
    return counterparty, department


def _upsert_group(
    *,
    payload: dict,
    counterparty: Counterparty,
    department: Department,
) -> AggregationGroup:
    start = perf_counter()
    group, created = AggregationGroup.objects.get_or_create(drf=payload["drf"])
    db_write_duration_seconds.observe(perf_counter() - start)

    if created:
        aggregation_groups_created_total.inc()

    errors: list[str] = []
    if group.counterparty_id is None:
        group.counterparty = counterparty
    elif group.counterparty_id != counterparty.id:
        errors.append("counterpartyId mismatch in drf group")

    if group.department_id is None:
        group.department = department
    elif group.department_id != department.id:
        errors.append("departmentId mismatch in drf group")

    incoming_date = payload["date"]
    if group.transaction_date is None:
        group.transaction_date = incoming_date
    elif group.transaction_date != incoming_date:
        errors.append("date mismatch in drf group")

    if errors:
        group.status = AggregationGroup.Status.VALIDATION_ERROR
        joined = "; ".join(errors)
        if group.validation_error:
            group.validation_error = f"{group.validation_error}; {joined}"
        else:
            group.validation_error = joined
        aggregation_groups_validation_error_total.inc()

    return group


def _recalculate_group_counts(group: AggregationGroup) -> None:
    stats_start = perf_counter()
    stats = group.raw_transactions.values("transaction_type").annotate(cnt=Count("id"))
    db_read_duration_seconds.observe(perf_counter() - stats_start)

    counts = {item["transaction_type"]: item["cnt"] for item in stats}
    group.income_count = counts.get(RawTransaction.TxType.INCOME, 0)
    group.vat_count = counts.get(RawTransaction.TxType.VAT, 0)
    group.total_count = group.income_count + group.vat_count
    aggregation_group_size_histogram.observe(group.total_count)



def _mark_group_open_or_ready(group: AggregationGroup) -> None:
    if group.status == AggregationGroup.Status.VALIDATION_ERROR:
        return

    if group.income_count >= 1 and group.vat_count == 1:
        group.status = AggregationGroup.Status.READY
        group.ready_at = timezone.now()
        aggregation_groups_ready_total.inc()
    elif group.vat_count > 1:
        group.status = AggregationGroup.Status.VALIDATION_ERROR
        group.validation_error = "Group must contain exactly 1 VAT transaction"
        aggregation_groups_validation_error_total.inc()
    else:
        group.status = AggregationGroup.Status.OPEN



def _set_draft_error(group: AggregationGroup, message: str) -> DraftInvoice:
    draft, _ = DraftInvoice.objects.get_or_create(
        group=group,
        defaults={
            "counterparty": group.counterparty,
            "department": group.department,
            "transaction_date": group.transaction_date,
        },
    )
    draft.status = DraftInvoice.Status.VALIDATION_ERROR
    draft.validation_error = message
    draft.save(update_fields=["status", "validation_error", "updated_at"])
    group.status = AggregationGroup.Status.VALIDATION_ERROR
    group.validation_error = message
    group.save(update_fields=["status", "validation_error", "updated_at"])
    draft_invoices_validation_error_total.inc()
    aggregation_groups_validation_error_total.inc()
    _record_error(
        stage=ProcessingError.Stage.AGGREGATION,
        code="DRAFT_BUILD_ERROR",
        message=message,
        payload={"drf": group.drf},
        retryable=True,
        group=group,
        draft=draft,
    )
    return draft


def build_draft_invoice(group: AggregationGroup) -> DraftInvoice:
    tx_start = perf_counter()
    txs = list(group.raw_transactions.filter(status=RawTransaction.Status.PROCESSED).order_by("id"))
    db_read_duration_seconds.observe(perf_counter() - tx_start)

    incomes = [tx for tx in txs if tx.transaction_type == RawTransaction.TxType.INCOME]
    vat_txs = [tx for tx in txs if tx.transaction_type == RawTransaction.TxType.VAT]

    if not incomes:
        return _set_draft_error(group, "Group must contain at least 1 INCOME transaction")
    if len(vat_txs) != 1:
        return _set_draft_error(group, "Group must contain exactly 1 VAT transaction")

    vat_tx = vat_txs[0]

    draft, created = DraftInvoice.objects.get_or_create(
        group=group,
        defaults={
            "counterparty": group.counterparty,
            "department": group.department,
            "transaction_date": group.transaction_date,
            "vat_rate": vat_tx.vat_rate,
        },
    )
    if created:
        draft_invoices_created_total.inc()

    draft.counterparty = group.counterparty
    draft.department = group.department
    draft.transaction_date = group.transaction_date
    draft.vat_rate = vat_tx.vat_rate
    draft.validation_error = ""

    DraftInvoiceLine.objects.filter(draft_invoice=draft).delete()

    total_with_vat = Decimal("0")
    vat_from_lines = Decimal("0")

    for line_no, income_tx in enumerate(incomes, start=1):
        amount_without_vat = q(income_tx.quantity * income_tx.unit_price)
        line_vat_amount = q(amount_without_vat * income_tx.vat_rate)
        line_total = q(amount_without_vat + line_vat_amount)

        DraftInvoiceLine.objects.create(
            draft_invoice=draft,
            raw_transaction=income_tx,
            line_no=line_no,
            product_name=income_tx.product_name,
            unit=income_tx.unit_measure,
            quantity=income_tx.quantity,
            unit_price=income_tx.unit_price,
            amount_without_vat=amount_without_vat,
            vat_amount=line_vat_amount,
            total_amount=line_total,
        )

        total_with_vat += line_total
        vat_from_lines += line_vat_amount

    vat_from_lines = q(vat_from_lines)
    total_with_vat = q(total_with_vat)

    vat_diff = abs(vat_tx.vat_amount - vat_from_lines)
    if vat_diff > VAT_TOLERANCE:
        return _set_draft_error(
            group,
            f"VAT mismatch: VAT tx {vat_tx.vat_amount} != line vat sum {vat_from_lines}",
        )

    draft.total_vat_amount = vat_tx.vat_amount
    draft.total_with_vat = total_with_vat
    draft.status = DraftInvoice.Status.READY
    draft.save()

    group.status = AggregationGroup.Status.DRAFT
    group.validation_error = ""
    group.last_processed_at = timezone.now()
    group.save(update_fields=["status", "validation_error", "last_processed_at", "updated_at"])

    min_received = group.raw_transactions.aggregate(min_ts=Min("received_at"))["min_ts"]
    if min_received:
        latency = (timezone.now() - min_received).total_seconds()
        if latency >= 0:
            transaction_to_draft_latency_seconds.observe(latency)

    return draft


def process_transaction_payload(
    payload: dict,
    *,
    source: str = InboundMessageLog.Source.API,
    inbound_log_id: int | None = None,
) -> ProcessResult:
    payload_hash = stable_payload_hash(payload)

    serializer = TransactionPayloadSerializer(data=payload)
    if not serializer.is_valid():
        transactions_invalid_schema_total.inc()
        inbound = None
        if inbound_log_id:
            inbound = InboundMessageLog.objects.filter(id=inbound_log_id).first()
        if inbound is None:
            inbound = InboundMessageLog.objects.create(
                drf=str(payload.get("drf", "")),
                source=source,
                payload_hash=payload_hash,
                payload=payload,
                status=InboundMessageLog.Status.VALIDATION_ERROR,
                error_message=str(serializer.errors),
            )
        else:
            inbound.status = InboundMessageLog.Status.VALIDATION_ERROR
            inbound.error_message = str(serializer.errors)
            inbound.save(update_fields=["status", "error_message", "updated_at"])

        _record_error(
            stage=ProcessingError.Stage.INGEST,
            code="INVALID_SCHEMA",
            message=str(serializer.errors),
            payload=payload,
            retryable=False,
        )
        return ProcessResult(status="invalid", message=str(serializer.errors))

    data = serializer.validated_data

    with transaction.atomic():
        if inbound_log_id:
            inbound = InboundMessageLog.objects.select_for_update().get(pk=inbound_log_id)
            inbound.status = InboundMessageLog.Status.PROCESSING
            inbound.drf = data["drf"]
            inbound.payload_hash = payload_hash
            inbound.save(update_fields=["status", "drf", "payload_hash", "updated_at"])
        else:
            inbound = InboundMessageLog.objects.create(
                drf=data["drf"],
                source=source,
                payload_hash=payload_hash,
                payload=payload,
                status=InboundMessageLog.Status.PROCESSING,
            )

        try:
            idempotency = IdempotencyRecord.objects.create(
                payload_hash=payload_hash,
                drf=data["drf"],
                source=source,
                inbound_log=inbound,
            )
        except IntegrityError:
            transactions_duplicate_total.inc()
            IdempotencyRecord.objects.filter(payload_hash=payload_hash).update(
                times_seen=F("times_seen") + 1,
                last_seen_at=timezone.now(),
            )
            inbound.status = InboundMessageLog.Status.DUPLICATE
            inbound.error_message = "Duplicate payload"
            inbound.save(update_fields=["status", "error_message", "updated_at"])
            transactions_ack_total.inc()
            _update_gauges()
            return ProcessResult(status="duplicate", message="duplicate payload")

        try:
            refs_start = perf_counter()
            counterparty, department = _get_refs(data)
            db_read_duration_seconds.observe(perf_counter() - refs_start)
        except (Counterparty.DoesNotExist, Department.DoesNotExist) as exc:
            inbound.status = InboundMessageLog.Status.VALIDATION_ERROR
            inbound.error_message = str(exc)
            inbound.save(update_fields=["status", "error_message", "updated_at"])
            transactions_invalid_schema_total.inc()
            _record_error(
                stage=ProcessingError.Stage.INGEST,
                code="UNKNOWN_REFERENCE",
                message=str(exc),
                payload=payload,
                retryable=False,
            )
            return ProcessResult(status="invalid", message=str(exc))

        group = _upsert_group(payload=data, counterparty=counterparty, department=department)

        raw_start = perf_counter()
        raw_tx = RawTransaction.objects.create(
            inbound_log=inbound,
            aggregation_group=group,
            external_id=data.get("transactionId", ""),
            drf=data["drf"],
            transaction_type=data["type"],
            counterparty=counterparty,
            department=department,
            transaction_date=data["date"],
            product_name=data.get("productName", ""),
            unit_measure=data.get("unitMeasure", ""),
            quantity=data.get("quantity", Decimal("0")),
            unit_price=data.get("unitPrice", Decimal("0")),
            vat_rate=data["vatRate"],
            vat_amount=data.get("vatAmount", Decimal("0")),
            payload_hash=payload_hash,
            payload=payload,
            status=RawTransaction.Status.PROCESSED,
            processed_at=timezone.now(),
        )
        db_write_duration_seconds.observe(perf_counter() - raw_start)

        idempotency.raw_transaction = raw_tx
        idempotency.save(update_fields=["raw_transaction", "last_seen_at"])

        _recalculate_group_counts(group)
        _mark_group_open_or_ready(group)
        group.last_processed_at = timezone.now()
        group.save()

        draft = None
        if group.status == AggregationGroup.Status.READY:
            draft = build_draft_invoice(group)

        inbound.status = InboundMessageLog.Status.PROCESSED
        inbound.error_message = ""
        inbound.save(update_fields=["status", "error_message", "updated_at"])

    transactions_ack_total.inc()
    last_successful_processing_timestamp.set(timezone.now().timestamp())
    _update_gauges()
    return ProcessResult(
        status="ok",
        group_id=group.id,
        draft_invoice_id=getattr(draft, "id", None),
    )


def generate_invoice_number(*, department: Department, date, version: str = "00") -> str:
    while True:
        with transaction.atomic():
            try:
                seq = InvoiceNumberSequence.objects.select_for_update().get(
                    department=department,
                    sequence_date=date,
                    version=version,
                )
            except InvoiceNumberSequence.DoesNotExist:
                try:
                    seq = InvoiceNumberSequence.objects.create(
                        department=department,
                        sequence_date=date,
                        version=version,
                        last_value=0,
                    )
                except IntegrityError:
                    continue
                seq = InvoiceNumberSequence.objects.select_for_update().get(pk=seq.pk)

            seq.last_value += 1
            seq.save(update_fields=["last_value", "updated_at"])
            return f"{version}/{department.mnemonic}/{date.strftime('%d%m%y')}/{seq.last_value:08d}"


def materialize_draft_invoice(draft: DraftInvoice) -> FinalInvoice | None:
    started = perf_counter()
    job = MaterializationJob.objects.create(
        group=draft.group,
        draft_invoice=draft,
        status=MaterializationJob.Status.PENDING,
        attempt=draft.retry_count + 1,
    )

    try:
        with transaction.atomic():
            if hasattr(draft, "final_invoice"):
                job.status = MaterializationJob.Status.SUCCESS
                job.finished_at = timezone.now()
                job.save(update_fields=["status", "finished_at"])
                return draft.final_invoice

            invoice_number = generate_invoice_number(
                department=draft.department,
                date=draft.transaction_date,
                version="00",
            )

            final_invoice = FinalInvoice.objects.create(
                draft_invoice=draft,
                invoice_number=invoice_number,
                drf=draft.group.drf,
                counterparty=draft.counterparty,
                department=draft.department,
                transaction_date=draft.transaction_date,
                vat_rate=draft.vat_rate,
                total_vat_amount=draft.total_vat_amount,
                total_with_vat=draft.total_with_vat,
                status=FinalInvoice.Status.MATERIALIZED,
                export_status=FinalInvoice.Status.EXPORT_READY,
            )

            lines = [
                FinalInvoiceLine(
                    final_invoice=final_invoice,
                    line_no=line.line_no,
                    product_name=line.product_name,
                    unit=line.unit,
                    quantity=line.quantity,
                    unit_price=line.unit_price,
                    amount_without_vat=line.amount_without_vat,
                    vat_amount=line.vat_amount,
                    total_amount=line.total_amount,
                )
                for line in draft.lines.all().order_by("line_no")
            ]
            FinalInvoiceLine.objects.bulk_create(lines)

            ExportRecord.objects.create(
                final_invoice=final_invoice,
                status=ExportRecord.Status.READY,
                destination="csv",
            )

            InvoiceStatusHistory.objects.create(
                final_invoice=final_invoice,
                from_status="",
                to_status=FinalInvoice.Status.MATERIALIZED,
                reason="Materialized from Layer1 draft",
            )
            InvoiceStatusHistory.objects.create(
                final_invoice=final_invoice,
                from_status=FinalInvoice.Status.MATERIALIZED,
                to_status=FinalInvoice.Status.EXPORT_READY,
                reason="Export record created",
            )

            InvoiceFieldChangeHistory.objects.create(
                final_invoice=final_invoice,
                field_name="invoice_number",
                old_value="",
                new_value=invoice_number,
            )

            draft.status = DraftInvoice.Status.MATERIALIZED
            draft.materialized_at = timezone.now()
            draft.save(update_fields=["status", "materialized_at", "updated_at"])

            draft.group.status = AggregationGroup.Status.MATERIALIZED
            draft.group.last_processed_at = timezone.now()
            draft.group.save(update_fields=["status", "last_processed_at", "updated_at"])

            job.status = MaterializationJob.Status.SUCCESS
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "finished_at"])

            layer2_materialization_total.inc()
            final_invoices_created_total.inc()
            final_invoices_export_ready_total.inc()
            return final_invoice
    except Exception as exc:  # noqa: BLE001
        layer2_materialization_error_total.inc()
        draft.status = DraftInvoice.Status.MATERIALIZATION_ERROR
        draft.retry_count += 1
        draft.validation_error = str(exc)
        draft.save(update_fields=["status", "retry_count", "validation_error", "updated_at"])

        job.status = MaterializationJob.Status.ERROR
        job.error_message = str(exc)
        job.finished_at = timezone.now()
        job.save(update_fields=["status", "error_message", "finished_at"])

        _record_error(
            stage=ProcessingError.Stage.MATERIALIZATION,
            code="L2_MATERIALIZATION_ERROR",
            message=str(exc),
            payload={"draft_invoice_id": draft.id},
            draft=draft,
            group=draft.group,
        )
        return None
    finally:
        layer2_materialization_duration_seconds.observe(perf_counter() - started)


def materialize_ready_drafts(limit: int = 100) -> dict[str, int]:
    backlog = DraftInvoice.objects.filter(status=DraftInvoice.Status.READY).count()
    transfer_backlog_gauge.set(backlog)

    drafts = list(
        DraftInvoice.objects.select_related("group", "department", "counterparty")
        .filter(status=DraftInvoice.Status.READY)
        .order_by("created_at")[:limit]
    )

    success = 0
    errors = 0
    for draft in drafts:
        result = materialize_draft_invoice(draft)
        if result is None:
            errors += 1
        else:
            success += 1

    transfer_backlog_gauge.set(DraftInvoice.objects.filter(status=DraftInvoice.Status.READY).count())
    _update_gauges()
    return {"picked": len(drafts), "success": success, "errors": errors}


def retry_failed_drafts(limit: int = 50) -> int:
    drafts = DraftInvoice.objects.filter(status=DraftInvoice.Status.MATERIALIZATION_ERROR).order_by("updated_at")[:limit]
    retried = 0
    for draft in drafts:
        retry_attempts_total.inc()
        draft.status = DraftInvoice.Status.READY
        draft.save(update_fields=["status", "updated_at"])
        retried += 1
    return retried


def retry_final_invoice(final_invoice: FinalInvoice) -> ExportRecord:
    started = perf_counter()
    export_record, _ = ExportRecord.objects.get_or_create(
        final_invoice=final_invoice,
        defaults={"status": ExportRecord.Status.RETRY_PENDING, "destination": "csv"},
    )

    old_status = final_invoice.export_status
    final_invoice.export_status = FinalInvoice.Status.RETRY_PENDING
    final_invoice.status = FinalInvoice.Status.RETRY_PENDING
    final_invoice.save(update_fields=["export_status", "status", "updated_at"])

    export_record.status = ExportRecord.Status.RETRY_PENDING
    export_record.last_error = ""
    export_record.save(update_fields=["status", "last_error", "updated_at"])

    next_attempt = export_record.attempts.count() + 1
    ExportAttempt.objects.create(
        export_record=export_record,
        attempt_no=next_attempt,
        status=ExportAttempt.Status.SUCCESS,
        duration_ms=1,
    )
    retry_attempts_total.inc()
    export_attempt_duration_seconds.observe(perf_counter() - started)
    final_invoices_export_error_total.inc()

    InvoiceStatusHistory.objects.create(
        final_invoice=final_invoice,
        from_status=old_status,
        to_status=FinalInvoice.Status.RETRY_PENDING,
        reason="Manual retry requested",
    )
    return export_record


def reprocess_aggregation_group(group: AggregationGroup) -> DraftInvoice | None:
    group.status = AggregationGroup.Status.OPEN
    group.validation_error = ""
    group.save(update_fields=["status", "validation_error", "updated_at"])

    _recalculate_group_counts(group)
    _mark_group_open_or_ready(group)
    group.save(update_fields=["status", "ready_at", "income_count", "vat_count", "total_count", "updated_at"])

    if group.status == AggregationGroup.Status.READY:
        return build_draft_invoice(group)
    return None


def summary_snapshot() -> dict:
    read_start = perf_counter()
    totals = {
        "transactions_total": RawTransaction.objects.count(),
        "transactions_processed": RawTransaction.objects.filter(status=RawTransaction.Status.PROCESSED).count(),
        "transactions_duplicates": InboundMessageLog.objects.filter(status=InboundMessageLog.Status.DUPLICATE).count(),
        "transactions_invalid_schema": InboundMessageLog.objects.filter(
            status=InboundMessageLog.Status.VALIDATION_ERROR
        ).count(),
        "groups_total": AggregationGroup.objects.count(),
        "groups_ready": AggregationGroup.objects.filter(status=AggregationGroup.Status.READY).count()
        + AggregationGroup.objects.filter(status=AggregationGroup.Status.DRAFT).count(),
        "draft_invoices_created": DraftInvoice.objects.count(),
        "draft_invoices_ready": DraftInvoice.objects.filter(status=DraftInvoice.Status.READY).count(),
        "final_invoices_materialized": FinalInvoice.objects.count(),
        "export_errors": ExportRecord.objects.filter(status=ExportRecord.Status.ERROR).count(),
        "queue_lag": InboundMessageLog.objects.filter(
            status__in=[
                InboundMessageLog.Status.RECEIVED,
                InboundMessageLog.Status.PUBLISHED,
                InboundMessageLog.Status.PROCESSING,
            ]
        ).count(),
    }

    latencies = []
    for final_invoice in FinalInvoice.objects.select_related("draft_invoice__group").all()[:5000]:
        draft = final_invoice.draft_invoice
        if not draft:
            continue
        first_tx = draft.group.raw_transactions.aggregate(min_ts=Min("received_at"))["min_ts"]
        if first_tx:
            latencies.append((final_invoice.materialized_at - first_tx).total_seconds())

    db_read_duration_seconds.observe(perf_counter() - read_start)

    latencies_sorted = sorted(latencies)

    def percentile(values: list[float], p: float) -> float:
        if not values:
            return 0.0
        k = (len(values) - 1) * p
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return float(values[int(k)])
        d0 = values[f] * (c - k)
        d1 = values[c] * (k - f)
        return float(d0 + d1)

    duration_seconds = 1.0
    first_tx_time = RawTransaction.objects.order_by("received_at").values_list("received_at", flat=True).first()
    last_tx_time = RawTransaction.objects.order_by("received_at").values_list("received_at", flat=True).last()
    if first_tx_time and last_tx_time and last_tx_time > first_tx_time:
        duration_seconds = (last_tx_time - first_tx_time).total_seconds()

    throughput = totals["transactions_processed"] / max(duration_seconds, 1.0)

    return {
        **totals,
        "latency_avg_seconds": float(sum(latencies_sorted) / len(latencies_sorted)) if latencies_sorted else 0.0,
        "latency_p95_seconds": percentile(latencies_sorted, 0.95),
        "latency_p99_seconds": percentile(latencies_sorted, 0.99),
        "throughput_tps": throughput,
        "cpu_ram_snapshot_note": "Use Prometheus/cAdvisor panels for live CPU/RAM snapshot",
        "generated_at": timezone.now().isoformat(),
    }
