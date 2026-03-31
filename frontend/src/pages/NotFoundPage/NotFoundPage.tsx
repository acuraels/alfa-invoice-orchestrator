import { LogIn } from 'lucide-react';
import { Link } from 'react-router-dom';
import './NotFoundPage.css';

export function NotFoundPage() {
  return (
    <section className="page not-found-page">
      <div className="not-found-page__card">
        <p className="not-found-page__code">404</p>
        <h1>Такой страницы не существует</h1>
        <p>Проверьте адрес страницы и попробуйте выполнить вход заново.</p>
        <div className="not-found-page__actions">
          <Link to="/login" className="button button-primary">
            <LogIn size={18} />
            <span>Войти</span>
          </Link>
        </div>
      </div>
    </section>
  );
}
