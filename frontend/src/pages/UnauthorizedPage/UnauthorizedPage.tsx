import { LogIn } from 'lucide-react';
import { Link } from 'react-router-dom';
import './UnauthorizedPage.css';

export function UnauthorizedPage() {
  return (
    <section className="page unauthorized-page">
      <div className="unauthorized-page__card">
        <p className="unauthorized-page__code">403</p>
        <h1>Доступ запрещен</h1>
        <p>У вашей учетной записи нет прав для просмотра этой страницы.</p>
        <div className="unauthorized-page__actions">
          <Link to="/login" className="button button-primary">
            <LogIn size={18} />
            <span>Перейти ко входу</span>
          </Link>
        </div>
      </div>
    </section>
  );
}
