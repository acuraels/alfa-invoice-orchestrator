import { LogOut } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import './Header.css';

export function Header() {
  const location = useLocation();
  const isLogoutPage = location.pathname === '/logout';

  return (
    <header className="header">
      <div className="header__inner">
        <Link to="/invoice-list" className="header__brand" aria-label="Перейти к списку счетов-фактур">
          <img src="/logo.png" alt="" className="header__brand-logo" />
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
