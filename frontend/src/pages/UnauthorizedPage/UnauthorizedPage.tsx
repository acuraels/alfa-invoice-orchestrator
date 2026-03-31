import { LogIn } from 'lucide-react';
import { Link } from 'react-router-dom';
import './UnauthorizedPage.css';

export function UnauthorizedPage() {
  return (
    <section className="page unauthorized-page">
      <div className="unauthorized-page__card">
        <p className="unauthorized-page__code">401</p>
        <h1>Вы не авторизованы</h1>
        <p>Для доступа к этой странице нужно сначала выполнить вход в систему.</p>
        <div className="unauthorized-page__actions">
          <Link to="/login" className="button button-primary">
            <LogIn size={18} />
            <span>Войти</span>
          </Link>
        </div>
      </div>
    </section>
  );
}
