import { Header } from '../../components/Header/Header';

export function AdminPanelPage() {
  return (
    <>
      <Header />
      <main className="page page-shell">
        <section className="content-card">
          <p className="content-card__eyebrow">Admin</p>
          <h1>Панель администратора</h1>
          <p>Страница доступна только пользователям с ролью `admin`.</p>
        </section>
      </main>
    </>
  );
}
