from django.urls import include, path
from rest_framework.routers import DefaultRouter

from invoices.views import (
    AggregationGroupViewSet,
    DraftInvoiceViewSet,
    ExportCsvReportView,
    ExportRecordViewSet,
    FinalInvoiceViewSet,
    HealthzView,
    InboundLogViewSet,
    IngestTransactionsView,
    LoadTestSummaryView,
    MetricsView,
    ProcessingErrorViewSet,
    RawTransactionViewSet,
    ReadyzView,
    SummaryReportView,
)

class OptionalSlashRouter(DefaultRouter):
    trailing_slash = "/?"


router = OptionalSlashRouter()
router.register("raw-transactions", RawTransactionViewSet, basename="raw-transactions")
router.register("aggregation-groups", AggregationGroupViewSet, basename="aggregation-groups")
router.register("draft-invoices", DraftInvoiceViewSet, basename="draft-invoices")
router.register("final-invoices", FinalInvoiceViewSet, basename="final-invoices")
router.register("export-records", ExportRecordViewSet, basename="export-records")
router.register("processing-errors", ProcessingErrorViewSet, basename="processing-errors")
router.register("inbound-logs", InboundLogViewSet, basename="inbound-logs")

raw_list = RawTransactionViewSet.as_view({"get": "list"})
raw_detail = RawTransactionViewSet.as_view({"get": "retrieve"})
group_list = AggregationGroupViewSet.as_view({"get": "list"})
group_detail = AggregationGroupViewSet.as_view({"get": "retrieve"})
group_reprocess = AggregationGroupViewSet.as_view({"post": "reprocess"})
draft_list = DraftInvoiceViewSet.as_view({"get": "list"})
draft_detail = DraftInvoiceViewSet.as_view({"get": "retrieve"})
final_list = FinalInvoiceViewSet.as_view({"get": "list"})
final_detail = FinalInvoiceViewSet.as_view({"get": "retrieve"})
final_retry = FinalInvoiceViewSet.as_view({"post": "retry"})
export_list = ExportRecordViewSet.as_view({"get": "list"})
export_detail = ExportRecordViewSet.as_view({"get": "retrieve"})

urlpatterns = [
    path("healthz", HealthzView.as_view(), name="healthz"),
    path("healthz/", HealthzView.as_view(), name="healthz-slash"),
    path("readyz", ReadyzView.as_view(), name="readyz"),
    path("readyz/", ReadyzView.as_view(), name="readyz-slash"),
    path("metrics", MetricsView.as_view(), name="metrics"),
    path("metrics/", MetricsView.as_view(), name="metrics-slash"),
    path("api/v1/ingest/transactions", IngestTransactionsView.as_view(), name="ingest-transactions"),
    path("api/v1/ingest/transactions/", IngestTransactionsView.as_view(), name="ingest-transactions-slash"),
    path("api/v1/reports/summary", SummaryReportView.as_view(), name="summary-report"),
    path("api/v1/reports/summary/", SummaryReportView.as_view(), name="summary-report-slash"),
    path("api/v1/reports/load-test-summary", LoadTestSummaryView.as_view(), name="load-test-summary"),
    path("api/v1/reports/load-test-summary/", LoadTestSummaryView.as_view(), name="load-test-summary-slash"),
    path("api/v1/reports/export.csv", ExportCsvReportView.as_view(), name="export-csv"),
    path("api/v1/reports/export.csv/", ExportCsvReportView.as_view(), name="export-csv-slash"),
    path("api/v1/raw-transactions", raw_list, name="raw-transactions-noslash"),
    path("api/v1/raw-transactions/<int:pk>", raw_detail, name="raw-transaction-detail-noslash"),
    path("api/v1/aggregation-groups", group_list, name="aggregation-groups-noslash"),
    path("api/v1/aggregation-groups/<int:pk>", group_detail, name="aggregation-group-detail-noslash"),
    path("api/v1/aggregation-groups/<int:pk>/reprocess", group_reprocess, name="aggregation-group-reprocess-noslash"),
    path("api/v1/draft-invoices", draft_list, name="draft-invoices-noslash"),
    path("api/v1/draft-invoices/<int:pk>", draft_detail, name="draft-invoice-detail-noslash"),
    path("api/v1/final-invoices", final_list, name="final-invoices-noslash"),
    path("api/v1/final-invoices/<int:pk>", final_detail, name="final-invoice-detail-noslash"),
    path("api/v1/final-invoices/<int:pk>/retry", final_retry, name="final-invoice-retry-noslash"),
    path("api/v1/export-records", export_list, name="export-records-noslash"),
    path("api/v1/export-records/<int:pk>", export_detail, name="export-record-detail-noslash"),
    path("api/v1/", include(router.urls)),
]
