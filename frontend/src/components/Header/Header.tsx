import { useMemo, useState } from 'react';
import { ChevronDown, LayoutList, LogOut, Settings2 } from 'lucide-react';
import { Link, useLocation } from 'react-router-dom';
import { getStoredUser } from '../../utils/authStorage';
import './Header.css';

export function Header() {
  const location = useLocation();
  const user = getStoredUser();
  const [isAccountMenuOpen, setIsAccountMenuOpen] = useState(false);

  const isLogoutPage = location.pathname === '/logout';
  const isInvoiceListPage = location.pathname.startsWith('/invoice-list');
  const isAdminPage = location.pathname === '/admin-panel';

  const accountLabel = useMemo(() => {
    if (!user) {
      return null;
    }

    return {
      name: user.full_name || user.login,
      login: user.login,
    };
  }, [user]);

  return (
    <header className="header">
      <div className="header__inner">
        <Link to="/invoice-list" className="header__brand" aria-label="Перейти к поступлениям">
          <img src="/logo.png" alt="" className="header__brand-logo" />
          <span>Alfa Orchestrator</span>
        </Link>

        {!isLogoutPage && (
          <div className="header__nav">
            <Link
              to="/invoice-list"
              className={isInvoiceListPage ? 'header__nav-link header__nav-link--active' : 'header__nav-link'}
            >
              <LayoutList size={17} />
              <span>Поступления</span>
            </Link>

            {accountLabel && (
              <div className="header__account">
                <button
                  type="button"
                  className={
                    isAccountMenuOpen
                      ? 'header__account-button header__account-button--open'
                      : 'header__account-button'
                  }
                  onClick={() => setIsAccountMenuOpen((current) => !current)}
                  aria-expanded={isAccountMenuOpen}
                  aria-label="Аккаунт"
                >
                  <span className="header__account-text">
                    <strong>{accountLabel.name}</strong>
                    <small>{accountLabel.login}</small>
                  </span>
                  <ChevronDown size={16} />
                </button>

                {isAccountMenuOpen && (
                  <div className="header__account-menu">
                    {user?.role === 'admin' && (
                      <Link
                        to="/admin-panel"
                        className={
                          isAdminPage
                            ? 'header__account-menu-link header__account-menu-link--active'
                            : 'header__account-menu-link'
                        }
                        onClick={() => setIsAccountMenuOpen(false)}
                      >
                        <Settings2 size={16} />
                        <span>Админ-панель</span>
                      </Link>
                    )}

                    <Link
                      to="/logout"
                      className="header__account-menu-link"
                      onClick={() => setIsAccountMenuOpen(false)}
                    >
                      <LogOut size={16} />
                      <span>Выйти</span>
                    </Link>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
