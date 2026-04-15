import { ChevronDown, Clock3, Plus, Search, Trash2 } from 'lucide-react';
import { useParams } from 'react-router-dom';
import { Header } from '../../components/Header/Header';
import './InvoiceDetailsPage.css';

type InvoiceLine = {
  id: string;
  productName: string;
  unit: string;
  quantity: string;
  unitPrice: string;
  amountWithoutVat: string;
  vatAmount: string;
  totalAmount: string;
};

const invoiceLines: InvoiceLine[] = [
  {
    id: 'line-1',
    productName: 'Лицензия на ПО (годовая)',
    unit: 'шт',
    quantity: '5',
    unitPrice: '1000',
    amountWithoutVat: '5000.00',
    vatAmount: '1000.00',
    totalAmount: '6000.00',
  },
  {
    id: 'line-2',
    productName: 'Услуги технической поддержки',
    unit: 'час',
    quantity: '10',
    unitPrice: '100',
    amountWithoutVat: '1000.00',
    vatAmount: '200.00',
    totalAmount: '1200.00',
  },
];

export function InvoiceDetailsPage() {
  const { id } = useParams<{ id: string }>();

  return (
    <>
      <Header />
      <main className="page invoice-details-page">
        <div className="invoice-details-page__container">
          <section className="invoice-details-topbar">
            <div className="invoice-details-topbar__identity">
              <h1>Редактор</h1>
              <span className="invoice-details-topbar__status">Черновик</span>
            </div>

            <div className="invoice-details-topbar__controls">
              <div className="invoice-details-select invoice-details-select--version">
                <Clock3 size={16} />
                <span className="invoice-details-select__label">Версия:</span>
                <select defaultValue="v3">
                  <option value="v3">v3</option>
                </select>
                <span className="invoice-details-select__meta">2026-04-09 14:30</span>
                <ChevronDown size={16} />
              </div>

              <label className="invoice-details-select invoice-details-select--department">
                <span className="invoice-details-select__label">Департамент:</span>
                <select defaultValue="факторинг">
                  <option value="бухгалтерия">бухгалтерия</option>
                  <option value="налоговая">налоговая</option>
                  <option value="управление">управление</option>
                  <option value="факторинг">факторинг</option>
                </select>
                <ChevronDown size={16} />
              </label>
            </div>
          </section>

          <section className="invoice-details-version-note">
            <div className="invoice-details-version-note__title">
              <Clock3 size={18} />
              <span>Версия 3</span>
              <time>2026-04-09 14:30</time>
            </div>
            <p>Автор: Анна Иванова • Обновлены наименования товаров и количество</p>
          </section>

          <section className="invoice-details-card">
            <h2>Детали документа</h2>

            <div className="invoice-details-form">
              <label className="invoice-details-field invoice-details-field--wide">
                <span>
                  Номер счета-фактуры <strong>*</strong>
                </span>
                <input type="text" defaultValue="00/МОУЗV/260407/00000765" />
              </label>

              <label className="invoice-details-field">
                <span>Дата выставления</span>
                <div className="invoice-details-input invoice-details-input--date">
                  <input type="date" defaultValue="2026-04-07" />
                </div>
              </label>

              <label className="invoice-details-field">
                <span>Контрагент</span>
                <div className="invoice-details-input invoice-details-input--search">
                  <Search size={18} />
                  <input type="text" defaultValue='ООО "ТехКорп Солюшнс"' />
                </div>
              </label>

              <label className="invoice-details-field">
                <span>ИНН контрагента</span>
                <input type="text" defaultValue="7701234567" />
              </label>

              <label className="invoice-details-field invoice-details-field--wide">
                <span>Адрес контрагента</span>
                <input type="text" defaultValue="г. Москва, Деловой проспект, д. 123, 101000" />
              </label>

              <label className="invoice-details-field">
                <span>Номер платежного документа</span>
                <input type="text" defaultValue="ПП-12345" />
              </label>

              <label className="invoice-details-field">
                <span>Дата платежного документа</span>
                <div className="invoice-details-input invoice-details-input--date">
                  <input type="date" defaultValue="2026-04-07" />
                </div>
              </label>
            </div>
          </section>

          <section className="invoice-details-card">
            <div className="invoice-details-card__header">
              <h2>Позиции счета-фактуры</h2>
              <span className="invoice-details-card__hint">UUID документа: {id}</span>
            </div>

            <div className="invoice-lines-table">
              <div className="invoice-lines-table__head">
                <span>Наименование товара/услуги</span>
                <span>Единица</span>
                <span>Количество</span>
                <span>Цена за ед.</span>
                <span>Сумма без НДС</span>
                <span>Сумма НДС (20%)</span>
                <span>Итоговая сумма</span>
                <span />
              </div>

              <div className="invoice-lines-table__body">
                {invoiceLines.map((line) => (
                  <div key={line.id} className="invoice-lines-table__row">
                    <div className="invoice-lines-table__cell">
                      <input type="text" defaultValue={line.productName} />
                    </div>

                    <div className="invoice-lines-table__cell">
                      <div className="invoice-details-input invoice-details-input--compact-select">
                        <select defaultValue={line.unit}>
                          <option value={line.unit}>{line.unit}</option>
                        </select>
                        <ChevronDown size={16} />
                      </div>
                    </div>

                    <div className="invoice-lines-table__cell">
                      <input type="text" defaultValue={line.quantity} />
                    </div>

                    <div className="invoice-lines-table__cell">
                      <input type="text" defaultValue={line.unitPrice} />
                    </div>

                    <div className="invoice-lines-table__cell invoice-lines-table__cell--readonly">
                      {line.amountWithoutVat}
                    </div>
                    <div className="invoice-lines-table__cell invoice-lines-table__cell--readonly">{line.vatAmount}</div>
                    <div className="invoice-lines-table__cell invoice-lines-table__cell--readonly">
                      {line.totalAmount}
                    </div>

                    <button type="button" className="invoice-lines-table__delete" aria-label="Удалить строку">
                      <Trash2 size={18} />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div className="invoice-details-card__footer">
              <button type="button" className="invoice-details-add-row">
                <Plus size={18} />
                <span>Добавить строку</span>
              </button>
            </div>
          </section>

          <section className="invoice-details-actions">
            <div className="invoice-details-actions__summary">
              <div className="invoice-details-actions__row">
                <span>Сумма НДС:</span>
                <strong>1200.00 ₽</strong>
              </div>

              <div className="invoice-details-actions__row invoice-details-actions__row--total">
                <span>Общая сумма:</span>
                <strong>7200.00 ₽</strong>
              </div>

              <div className="invoice-details-actions__buttons">
                <button
                  type="button"
                  className="invoice-details-actions__button invoice-details-actions__button--secondary"
                >
                  Сохранить черновик
                </button>
                <button
                  type="button"
                  className="invoice-details-actions__button invoice-details-actions__button--primary"
                >
                  Утвердить и отправить
                </button>
              </div>
            </div>
          </section>
        </div>
      </main>
    </>
  );
}
