import { useState } from 'react';
import { Link } from 'react-router-dom';
import { CheckCheck, ChevronDown, Download, Search } from 'lucide-react';
import { Header } from '../../components/Header/Header';
import './InvoiceListPage.css';

type InvoiceStatus = 'created' | 'validation_error' | 'sent' | 'send_error';
type InvoiceTab = 'to-process' | 'to-proceed';

type InvoiceListItem = {
  id: string;
  sequenceNumber: number;
  counterparty: string;
  status: InvoiceStatus;
  department: string;
  departmentCode: string;
  createdAt: string;
  issueDate: string;
};

const STATUS_CONFIG: Record<InvoiceStatus, { label: string; className: string }> = {
  created: { label: 'Создан', className: 'invoice-status invoice-status--created' },
  validation_error: {
    label: 'Ошибка валидации',
    className: 'invoice-status invoice-status--validation-error',
  },
  sent: { label: 'Отправлено', className: 'invoice-status invoice-status--sent' },
  send_error: { label: 'Ошибка отправки', className: 'invoice-status invoice-status--send-error' },
};

const PROCESSING_INVOICES: InvoiceListItem[] = [
  {
    id: '44f4f375-4670-48b3-a48e-bae4f80a5ba1',
    sequenceNumber: 304,
    counterparty: 'ООО "ТехноКорп"',
    status: 'validation_error',
    department: 'МОУЗV',
    departmentCode: 'MOU3V',
    issueDate: '2026-10-22',
    createdAt: '22 октября 19:42',
  },
  {
    id: '423e4f1d-2414-4c7d-94ca-572a09fe85d0',
    sequenceNumber: 305,
    counterparty: 'ООО "БизнесПартнер"',
    status: 'created',
    department: 'FIN01',
    departmentCode: 'FIN01',
    issueDate: '2026-10-22',
    createdAt: '22 октября 18:30',
  },
  {
    id: 'e27b7df5-42ab-4fd3-b646-b66220a14326',
    sequenceNumber: 306,
    counterparty: 'ЗАО "СтройГрупп"',
    status: 'created',
    department: 'OPS12',
    departmentCode: 'OPS12',
    issueDate: '2026-10-22',
    createdAt: '22 октября 16:15',
  },
];

const PROCESSED_INVOICES: InvoiceListItem[] = [
  {
    id: '938a34de-c660-4385-86c4-91f61c983ce4',
    sequenceNumber: 301,
    counterparty: 'ООО "МегаСистемс"',
    status: 'sent',
    department: 'МОУЗV',
    departmentCode: 'MOU3V',
    issueDate: '2026-10-21',
    createdAt: '21 октября 14:20',
  },
  {
    id: '006fe5fc-b66f-4104-a370-620b77ac4e96',
    sequenceNumber: 302,
    counterparty: 'ООО "ТрейдКомпани"',
    status: 'sent',
    department: 'FIN01',
    departmentCode: 'FIN01',
    issueDate: '2026-10-21',
    createdAt: '21 октября 11:05',
  },
  {
    id: '6db5a28d-c137-4363-b648-b4b2856dd49d',
    sequenceNumber: 303,
    counterparty: 'ООО "ПромСнаб"',
    status: 'send_error',
    department: 'OPS12',
    departmentCode: 'OPS12',
    issueDate: '2026-10-21',
    createdAt: '21 октября 09:30',
  },
];

const formatInvoiceNumber = (departmentCode: string, issueDate: string, sequenceNumber: number) => {
  const [year, month, day] = issueDate.split('-');
  const shortYear = year.slice(-2);
  const sequence = String(sequenceNumber).padStart(8, '0');

  return `00/${departmentCode}/${shortYear}${month}${day}/${sequence}`;
};

export function InvoiceListPage() {
  const [activeTab, setActiveTab] = useState<InvoiceTab>('to-process');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);

  const invoices = activeTab === 'to-process' ? PROCESSING_INVOICES : PROCESSED_INVOICES;
  const allSelected = invoices.length > 0 && selectedIds.length === invoices.length;

  const handleTabChange = (tab: InvoiceTab) => {
    setActiveTab(tab);
    setSelectedIds([]);
  };

  const handleSelectAll = () => {
    setSelectedIds(allSelected ? [] : invoices.map((invoice) => invoice.id));
  };

  const handleToggleInvoice = (invoiceId: string) => {
    setSelectedIds((current) =>
      current.includes(invoiceId) ? current.filter((id) => id !== invoiceId) : [...current, invoiceId],
    );
  };

  return (
    <>
      <Header />
      <main className="page invoice-list-page">
        <div className="invoice-list-page__container">
          <section className="invoice-list-page__main">
            <div className="invoice-tabs" role="tablist" aria-label="Список счетов-фактур">
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'to-process'}
                className={activeTab === 'to-process' ? 'invoice-tabs__button invoice-tabs__button--active' : 'invoice-tabs__button'}
                onClick={() => handleTabChange('to-process')}
              >
                К обработке
              </button>
              <button
                type="button"
                role="tab"
                aria-selected={activeTab === 'to-proceed'}
                className={activeTab === 'to-proceed' ? 'invoice-tabs__button invoice-tabs__button--active' : 'invoice-tabs__button'}
                onClick={() => handleTabChange('to-proceed')}
              >
                Обработано
              </button>
            </div>

            {activeTab === 'to-process' && (
              <section className="invoice-toolbar">
                <div className="invoice-toolbar__selection">
                  <button type="button" className="invoice-toolbar__ghost-button" onClick={handleSelectAll}>
                    {allSelected ? 'Снять выбор' : 'Выбрать все'}
                  </button>
                  {selectedIds.length > 0 && (
                    <p className="invoice-toolbar__selection-text">
                      Выбрано: {selectedIds.length} из {invoices.length}
                    </p>
                  )}
                </div>

                <button
                  type="button"
                  className="invoice-toolbar__primary-button"
                  disabled={selectedIds.length === 0}
                >
                  <CheckCheck size={18} />
                  <span>Утвердить ({selectedIds.length})</span>
                </button>
              </section>
            )}

            <div className="invoice-list">
              {invoices.map((invoice) => {
                const isSelected = selectedIds.includes(invoice.id);

                return (
                  <article
                    key={invoice.id}
                    className={isSelected ? 'invoice-card invoice-card--selected' : 'invoice-card'}
                  >
                    {activeTab === 'to-process' && (
                      <label className="invoice-card__checkbox">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => handleToggleInvoice(invoice.id)}
                          aria-label={`Выбрать ${formatInvoiceNumber(
                            invoice.departmentCode,
                            invoice.issueDate,
                            invoice.sequenceNumber,
                          )}`}
                        />
                        <span />
                      </label>
                    )}

                    <Link to={`/invoice-list/${invoice.id}`} className="invoice-card__link">
                      <div className="invoice-card__summary">
                        <div className="invoice-card__heading">
                          <h2>
                            {formatInvoiceNumber(invoice.departmentCode, invoice.issueDate, invoice.sequenceNumber)}
                          </h2>
                          <span className={STATUS_CONFIG[invoice.status].className}>
                            {STATUS_CONFIG[invoice.status].label}
                          </span>
                        </div>
                        <p>{invoice.counterparty}</p>
                      </div>

                      <time className="invoice-card__date">{invoice.createdAt}</time>
                    </Link>
                  </article>
                );
              })}
            </div>
          </section>

          <aside className="invoice-sidebar">
            <section className="invoice-filters">
              <h2>Фильтры</h2>

              <div className="invoice-field">
                <label htmlFor="counterparty-search">Контрагент</label>
                <div className="invoice-input invoice-input--leading-icon">
                  <Search size={18} />
                  <input id="counterparty-search" type="text" placeholder="Поиск..." />
                </div>
              </div>

              <div className="invoice-field">
                <label htmlFor="date-from">Дата от</label>
                <div className="invoice-input invoice-input--date">
                  <input id="date-from" type="date" />
                </div>
              </div>

              <div className="invoice-field">
                <label htmlFor="date-to">Дата до</label>
                <div className="invoice-input invoice-input--date">
                  <input id="date-to" type="date" />
                </div>
              </div>

              <div className="invoice-field">
                <label htmlFor="status-filter">Статус</label>
                <div className="invoice-select">
                  <select id="status-filter" defaultValue="all">
                    <option value="all">Все</option>
                  </select>
                  <ChevronDown size={18} />
                </div>
              </div>

              <div className="invoice-field">
                <label htmlFor="department-filter">Департаменты</label>
                <div className="invoice-select">
                  <select id="department-filter" defaultValue="all">
                    <option value="all">Все</option>
                  </select>
                  <ChevronDown size={18} />
                </div>
              </div>

              <button type="button" className="invoice-sidebar__export-button">
                <Download size={18} />
                <span>Export</span>
              </button>
            </section>

            <section className="invoice-summary">
              <p>Найдено: {invoices.length} счета</p>
            </section>
          </aside>
        </div>
      </main>
    </>
  );
}
