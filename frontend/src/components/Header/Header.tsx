import { LogOut } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import './Header.css';

export function Header() {
  const location = useLocation();
  const isLogoutPage = location.pathname === '/logout';

  return (
    <header className="header">
      <div className="header__inner">
        <Link to="/login" className="header__brand" aria-label="Перейти на страницу входа">
          <span className="header__brand-mark" />
          <span>Alfa Orchestrator</span>
        </Link>

        {!isLogoutPage && (
          <Link to="/logout" className="header__action">
            <LogOut size={18} />
            <span>Выйти</span>
          </Link>
        )}
      </div>
    </header>
  );
}
