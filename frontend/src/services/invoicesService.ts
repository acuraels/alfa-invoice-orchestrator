import { api } from '../utils/api';
import type {
  AggregationGroup,
  DraftInvoice,
  ExportRecord,
  FinalInvoice,
  PaginatedResponse,
  ProcessingError,
  RawTransaction,
  Summary,
} from '../types/invoices';

const BASE = '/api/v1';

export const invoicesService = {
  getSummary() {
    return api.get<Summary>(`${BASE}/reports/summary`);
  },

  getRawTransactions() {
    return api.get<PaginatedResponse<RawTransaction>>(`${BASE}/raw-transactions`).then((response) => response.results);
  },

  getAggregationGroups() {
    return api
      .get<PaginatedResponse<AggregationGroup>>(`${BASE}/aggregation-groups`)
      .then((response) => response.results);
  },

  getDraftInvoices() {
    return api.get<PaginatedResponse<DraftInvoice>>(`${BASE}/draft-invoices`).then((response) => response.results);
  },

  getFinalInvoices() {
    return api.get<PaginatedResponse<FinalInvoice>>(`${BASE}/final-invoices`).then((response) => response.results);
  },

  getExportRecords() {
    return api.get<PaginatedResponse<ExportRecord>>(`${BASE}/export-records`).then((response) => response.results);
  },

  getErrors() {
    return api
      .get<PaginatedResponse<ProcessingError>>(`${BASE}/processing-errors`)
      .then((response) => response.results);
  },

  retryFinalInvoice(id: number) {
    return api.post(`${BASE}/final-invoices/${id}/retry/`);
  },

  reprocessGroup(id: number) {
    return api.post(`${BASE}/aggregation-groups/${id}/reprocess/`);
  },
};
