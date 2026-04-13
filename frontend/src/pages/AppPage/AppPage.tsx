import { useCallback, useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import { Link } from 'react-router-dom';
import { authService } from '../../services/authService';
import { invoicesService } from '../../services/invoicesService';
import type {
  AggregationGroup,
  DraftInvoice,
  ExportRecord,
  FinalInvoice,
  ProcessingError,
  RawTransaction,
  Summary,
} from '../../types/invoices';
import './AppPage.css';

type Tab =
  | 'dashboard'
  | 'raw'
  | 'groups'
  | 'drafts'
  | 'finals'
  | 'exports'
  | 'errors'
  | 'charts';

const TAB_CONFIG: Array<{ tab: Tab; path: string; label: string }> = [
  { tab: 'dashboard', path: '/dashboard', label: 'Dashboard' },
  { tab: 'raw', path: '/raw-transactions', label: 'Raw transactions' },
  { tab: 'groups', path: '/aggregation-groups', label: 'Aggregation groups' },
  { tab: 'drafts', path: '/draft-invoices', label: 'Draft invoices' },
  { tab: 'finals', path: '/final-invoices', label: 'Final invoices' },
  { tab: 'exports', path: '/exports', label: 'Export statuses' },
  { tab: 'errors', path: '/errors', label: 'Errors' },
  { tab: 'charts', path: '/charts', label: 'Charts' },
];

function fmt(value: number | string) {
  if (typeof value === 'number') {
    return Number.isInteger(value) ? value.toString() : value.toFixed(3);
  }
  return value;
}

function formatDate(value: string) {
  if (!value) return '';
  return new Date(value).toLocaleString();
}

export function AppPage({ tab }: { tab: Tab }) {
  const user = authService.getCurrentUser();

  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [rawTransactions, setRawTransactions] = useState<RawTransaction[]>([]);
  const [groups, setGroups] = useState<AggregationGroup[]>([]);
  const [drafts, setDrafts] = useState<DraftInvoice[]>([]);
  const [finals, setFinals] = useState<FinalInvoice[]>([]);
  const [exports, setExports] = useState<ExportRecord[]>([]);
  const [errors, setErrors] = useState<ProcessingError[]>([]);

  const shouldLoad = useMemo(
    () => ({
      dashboard: tab === 'dashboard' || tab === 'charts',
      raw: tab === 'raw',
      groups: tab === 'groups',
      drafts: tab === 'drafts',
      finals: tab === 'finals',
      exports: tab === 'exports',
      errors: tab === 'errors',
    }),
    [tab]
  );

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      if (shouldLoad.dashboard) {
        setSummary(await invoicesService.getSummary());
      }
      if (shouldLoad.raw) {
        setRawTransactions(await invoicesService.getRawTransactions());
      }
      if (shouldLoad.groups) {
        setGroups(await invoicesService.getAggregationGroups());
      }
      if (shouldLoad.drafts) {
        setDrafts(await invoicesService.getDraftInvoices());
      }
      if (shouldLoad.finals) {
        setFinals(await invoicesService.getFinalInvoices());
      }
      if (shouldLoad.exports) {
        setExports(await invoicesService.getExportRecords());
      }
      if (shouldLoad.errors) {
        setErrors(await invoicesService.getErrors());
      }
    } catch {
      toast.error('Не удалось загрузить данные');
    } finally {
      setLoading(false);
    }
  }, [shouldLoad.dashboard, shouldLoad.drafts, shouldLoad.errors, shouldLoad.exports, shouldLoad.finals, shouldLoad.groups, shouldLoad.raw]);

  useEffect(() => {
    loadData();
    const interval = window.setInterval(loadData, 10000);
    return () => window.clearInterval(interval);
  }, [loadData]);

  async function handleRetry(finalInvoiceId: number) {
    try {
      await invoicesService.retryFinalInvoice(finalInvoiceId);
      toast.success(`Retry запрошен для invoice #${finalInvoiceId}`);
      loadData();
    } catch {
      toast.error('Retry завершился ошибкой');
    }
  }

  async function handleReprocess(groupId: number) {
    try {
      await invoicesService.reprocessGroup(groupId);
      toast.success(`Reprocess запущен для group #${groupId}`);
      loadData();
    } catch {
      toast.error('Reprocess завершился ошибкой');
    }
  }

  return (
    <main className="app-page">
      <div className="app-page__top">
        <div>
          <h1>Alfa Invoice MVP</h1>
          <p>
            Пользователь: <strong>{user?.username}</strong> ({user?.role})
          </p>
        </div>
        <div className="app-page__actions">
          <a href="/api/v1/reports/export.csv" className="app-page__link" target="_blank" rel="noreferrer">
            CSV export
          </a>
          <Link to="/logout" className="app-page__link app-page__link--danger">
            Logout
          </Link>
        </div>
      </div>

      <nav className="app-page__nav">
        {TAB_CONFIG.map((item) => (
          <Link
            key={item.tab}
            to={item.path}
            className={item.tab === tab ? 'app-page__tab app-page__tab--active' : 'app-page__tab'}
          >
            {item.label}
          </Link>
        ))}
      </nav>

      {loading && <p className="app-page__loading">Loading...</p>}

      {tab === 'dashboard' && summary && (
        <section className="cards-grid">
          <article className="metric-card">
            <span>Transactions total</span>
            <strong>{summary.transactions_total}</strong>
          </article>
          <article className="metric-card">
            <span>Processed</span>
            <strong>{summary.transactions_processed}</strong>
          </article>
          <article className="metric-card">
            <span>Duplicates</span>
            <strong>{summary.transactions_duplicates}</strong>
          </article>
          <article className="metric-card">
            <span>Schema errors</span>
            <strong>{summary.transactions_invalid_schema}</strong>
          </article>
          <article className="metric-card">
            <span>Groups ready</span>
            <strong>{summary.groups_ready}</strong>
          </article>
          <article className="metric-card">
            <span>Final invoices</span>
            <strong>{summary.final_invoices_materialized}</strong>
          </article>
          <article className="metric-card">
            <span>Latency p95</span>
            <strong>{fmt(summary.latency_p95_seconds)} s</strong>
          </article>
          <article className="metric-card">
            <span>Throughput</span>
            <strong>{fmt(summary.throughput_tps)} tx/s</strong>
          </article>
        </section>
      )}

      {tab === 'raw' && (
        <section className="registry">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>DRF</th>
                <th>Type</th>
                <th>Status</th>
                <th>Department</th>
                <th>Counterparty</th>
                <th>Received</th>
              </tr>
            </thead>
            <tbody>
              {rawTransactions.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.drf}</td>
                  <td>{item.transaction_type}</td>
                  <td>{item.status}</td>
                  <td>{item.department_code}</td>
                  <td>{item.counterparty_name}</td>
                  <td>{formatDate(item.received_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === 'groups' && (
        <section className="registry">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>DRF</th>
                <th>Status</th>
                <th>Counts</th>
                <th>Validation error</th>
                <th>Updated</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {groups.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.drf}</td>
                  <td>{item.status}</td>
                  <td>
                    {item.income_count}/{item.vat_count}/{item.total_count}
                  </td>
                  <td>{item.validation_error}</td>
                  <td>{formatDate(item.updated_at)}</td>
                  <td>
                    <button type="button" onClick={() => handleReprocess(item.id)}>
                      Reprocess
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === 'drafts' && (
        <section className="registry">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>DRF</th>
                <th>Status</th>
                <th>Department</th>
                <th>Total VAT</th>
                <th>Total with VAT</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {drafts.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.drf}</td>
                  <td>{item.status}</td>
                  <td>{item.department_code}</td>
                  <td>{item.total_vat_amount}</td>
                  <td>{item.total_with_vat}</td>
                  <td>{formatDate(item.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === 'finals' && (
        <section className="registry">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Invoice #</th>
                <th>DRF</th>
                <th>Status</th>
                <th>Export status</th>
                <th>Total</th>
                <th>Created</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {finals.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.invoice_number}</td>
                  <td>{item.drf}</td>
                  <td>{item.status}</td>
                  <td>{item.export_status}</td>
                  <td>{item.total_with_vat}</td>
                  <td>{formatDate(item.created_at)}</td>
                  <td>
                    <button type="button" onClick={() => handleRetry(item.id)}>
                      Retry
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === 'exports' && (
        <section className="registry">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Invoice #</th>
                <th>Status</th>
                <th>Destination</th>
                <th>Last error</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {exports.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.invoice_number}</td>
                  <td>{item.status}</td>
                  <td>{item.destination}</td>
                  <td>{item.last_error}</td>
                  <td>{formatDate(item.updated_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === 'errors' && (
        <section className="registry">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Stage</th>
                <th>Code</th>
                <th>Message</th>
                <th>Retryable</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {errors.map((item) => (
                <tr key={item.id}>
                  <td>{item.id}</td>
                  <td>{item.stage}</td>
                  <td>{item.code}</td>
                  <td>{item.message}</td>
                  <td>{item.retryable ? 'yes' : 'no'}</td>
                  <td>{formatDate(item.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      {tab === 'charts' && summary && (
        <section className="charts-page">
          <h2>Load/processing overview</h2>
          <div className="bar">
            <span>Transactions processed</span>
            <div className="bar__track">
              <div
                className="bar__fill"
                style={{ width: `${Math.min(100, (summary.transactions_processed / Math.max(summary.transactions_total, 1)) * 100)}%` }}
              />
            </div>
            <strong>
              {summary.transactions_processed}/{summary.transactions_total}
            </strong>
          </div>
          <div className="bar">
            <span>Groups ready</span>
            <div className="bar__track">
              <div
                className="bar__fill bar__fill--blue"
                style={{ width: `${Math.min(100, (summary.groups_ready / Math.max(summary.groups_total, 1)) * 100)}%` }}
              />
            </div>
            <strong>
              {summary.groups_ready}/{summary.groups_total}
            </strong>
          </div>
          <div className="bar">
            <span>Final invoices materialized</span>
            <div className="bar__track">
              <div
                className="bar__fill bar__fill--green"
                style={{
                  width: `${Math.min(100, (summary.final_invoices_materialized / Math.max(summary.draft_invoices_created, 1)) * 100)}%`,
                }}
              />
            </div>
            <strong>
              {summary.final_invoices_materialized}/{summary.draft_invoices_created}
            </strong>
          </div>
        </section>
      )}
    </main>
  );
}
