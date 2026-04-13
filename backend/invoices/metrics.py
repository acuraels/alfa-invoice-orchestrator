import time

from prometheus_client import Counter, Gauge, Histogram

transactions_received_total = Counter(
    "transactions_received_total",
    "Transactions received",
    labelnames=("type",),
)
transactions_published_total = Counter("transactions_published_total", "Transactions published")
transactions_duplicate_total = Counter("transactions_duplicate_total", "Duplicate transactions")
transactions_invalid_schema_total = Counter(
    "transactions_invalid_schema_total", "Schema invalid transactions"
)

transactions_consumed_total = Counter("transactions_consumed_total", "Transactions consumed")
transactions_ack_total = Counter("transactions_ack_total", "Transactions ack")
transactions_nack_total = Counter("transactions_nack_total", "Transactions nack")
transactions_dlq_total = Counter("transactions_dlq_total", "Transactions sent to dlq")
processor_duration_seconds = Histogram(
    "processor_duration_seconds",
    "Processor duration",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)

aggregation_groups_created_total = Counter(
    "aggregation_groups_created_total", "Aggregation groups created"
)
aggregation_groups_ready_total = Counter("aggregation_groups_ready_total", "Aggregation groups ready")
aggregation_groups_validation_error_total = Counter(
    "aggregation_groups_validation_error_total", "Aggregation validation errors"
)
aggregation_group_size_histogram = Histogram(
    "aggregation_group_size_histogram",
    "Transactions in aggregation group",
    buckets=(1, 2, 3, 5, 8, 13, 21, 34, 55),
)
draft_invoices_created_total = Counter("draft_invoices_created_total", "Draft invoices created")
draft_invoices_validation_error_total = Counter(
    "draft_invoices_validation_error_total", "Draft invoice validation errors"
)
transaction_to_draft_latency_seconds = Histogram(
    "transaction_to_draft_latency_seconds",
    "Latency from tx to draft",
    buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60, 120),
)
open_groups_gauge = Gauge("open_groups_gauge", "Open groups")

layer2_materialization_total = Counter("layer2_materialization_total", "Layer2 materializations")
layer2_materialization_error_total = Counter(
    "layer2_materialization_error_total", "Layer2 materialization errors"
)
layer2_materialization_duration_seconds = Histogram(
    "layer2_materialization_duration_seconds",
    "Layer2 materialization duration",
    buckets=(0.01, 0.1, 0.25, 0.5, 1, 2, 5, 10),
)
retry_attempts_total = Counter("retry_attempts_total", "Retry attempts")
transfer_backlog_gauge = Gauge("transfer_backlog_gauge", "Transfer backlog")

final_invoices_created_total = Counter("final_invoices_created_total", "Final invoices created")
final_invoices_export_ready_total = Counter(
    "final_invoices_export_ready_total", "Final invoices export ready"
)
final_invoices_export_error_total = Counter(
    "final_invoices_export_error_total", "Final invoices export error"
)
export_attempt_duration_seconds = Histogram(
    "export_attempt_duration_seconds",
    "Export attempt duration",
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1, 2),
)

db_write_duration_seconds = Histogram(
    "db_write_duration_seconds",
    "DB write duration",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1),
)
db_read_duration_seconds = Histogram(
    "db_read_duration_seconds",
    "DB read duration",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1),
)
queue_backlog_gauge = Gauge("queue_backlog_gauge", "Queue backlog")
last_successful_processing_timestamp = Gauge(
    "last_successful_processing_timestamp", "Unix timestamp of last successful processing"
)


def now() -> float:
    return time.perf_counter()


def observe_db_write(start: float) -> None:
    db_write_duration_seconds.observe(time.perf_counter() - start)


def observe_db_read(start: float) -> None:
    db_read_duration_seconds.observe(time.perf_counter() - start)
