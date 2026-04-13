export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type Summary = {
  transactions_total: number;
  transactions_processed: number;
  transactions_duplicates: number;
  transactions_invalid_schema: number;
  groups_total: number;
  groups_ready: number;
  draft_invoices_created: number;
  draft_invoices_ready: number;
  final_invoices_materialized: number;
  export_errors: number;
  queue_lag: number;
  latency_avg_seconds: number;
  latency_p95_seconds: number;
  latency_p99_seconds: number;
  throughput_tps: number;
  generated_at: string;
};

export type RawTransaction = {
  id: number;
  drf: string;
  transaction_type: string;
  status: string;
  department_code: string;
  counterparty_name: string;
  transaction_date: string;
  received_at: string;
};

export type AggregationGroup = {
  id: number;
  drf: string;
  status: string;
  department_code: string;
  counterparty_name: string;
  income_count: number;
  vat_count: number;
  total_count: number;
  validation_error: string;
  updated_at: string;
};

export type DraftInvoice = {
  id: number;
  drf: string;
  status: string;
  department_code: string;
  counterparty_name: string;
  total_vat_amount: string;
  total_with_vat: string;
  created_at: string;
};

export type FinalInvoice = {
  id: number;
  invoice_number: string;
  drf: string;
  status: string;
  export_status: string;
  department_code: string;
  total_with_vat: string;
  created_at: string;
};

export type ExportRecord = {
  id: number;
  final_invoice: number;
  invoice_number: string;
  status: string;
  destination: string;
  last_error: string;
  updated_at: string;
};

export type ProcessingError = {
  id: number;
  stage: string;
  code: string;
  message: string;
  retryable: boolean;
  resolved: boolean;
  created_at: string;
};
