import { useParams } from 'react-router-dom';
import { Header } from '../../components/Header/Header';

export function InvoiceDetailsPage() {
  const { id } = useParams<{ id: string }>();

  return (
    <>
      <Header />
      <main className="page page-shell">
        <section className="content-card">
          <p className="content-card__eyebrow">Invoice</p>
          <h1>Карточка счета-фактуры</h1>
          <p>UUID: {id}</p>
        </section>
      </main>
    </>
  );
}
