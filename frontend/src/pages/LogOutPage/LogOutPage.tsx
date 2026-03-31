import { LogIn } from 'lucide-react';
import { Link } from 'react-router-dom';
import './LogOutPage.css';

export function LogOutPage() {
  return (
    <section className="page logout-page">
      <div className="logout-page__card">
        <h1>Вы вышли из системы</h1>
        <p>Текущая сессия завершена.</p>
        <div className="logout-page__actions">
          <Link to="/login" className="button button-primary">
            <LogIn size={18} />
            <span>Войти</span>
          </Link>
        </div>
      </div>
    </section>
  );
}
