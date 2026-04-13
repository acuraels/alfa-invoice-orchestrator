from celery import shared_task
from django.utils import timezone

from invoices.metrics import (
    processor_duration_seconds,
    transactions_consumed_total,
    transactions_dlq_total,
    transactions_nack_total,
)
from invoices.models import InboundMessageLog
from invoices.services import materialize_ready_drafts, process_transaction_payload, retry_failed_drafts


@shared_task(
    bind=True,
    name="invoices.process_transaction",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_transaction_task(self, payload: dict, inbound_log_id: int | None = None, source: str = "API"):
    transactions_consumed_total.inc()
    with processor_duration_seconds.time():
        try:
            result = process_transaction_payload(payload, source=source, inbound_log_id=inbound_log_id)
            return {"status": result.status, "group_id": result.group_id, "draft_invoice_id": result.draft_invoice_id}
        except Exception as exc:  # noqa: BLE001
            transactions_nack_total.inc()
            if self.request.retries >= self.max_retries:
                transactions_dlq_total.inc()
                if inbound_log_id:
                    InboundMessageLog.objects.filter(id=inbound_log_id).update(
                        status=InboundMessageLog.Status.ERROR,
                        error_message=f"DLQ: {exc}",
                        updated_at=timezone.now(),
                    )
            raise


@shared_task(name="invoices.materialize_ready_drafts")
def materialize_ready_drafts_task(limit: int = 200):
    return materialize_ready_drafts(limit=limit)


@shared_task(name="invoices.retry_failed_drafts")
def retry_failed_drafts_task(limit: int = 100):
    return {"retried": retry_failed_drafts(limit=limit)}
