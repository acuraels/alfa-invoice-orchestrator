import { useEffect, useState } from 'react';
import { Plus, Pencil, Trash2, X, ChevronDown } from 'lucide-react';
import { Header } from '../../components/Header/Header';
import './AdminPanelPage.css';

type AdminUser = {
  id: string;
  fullName: string;
  email: string;
  role: 'user' | 'admin';
  departments: string[];
  createdAt: string;
};

type UserModalMode = 'create' | 'edit';

const departmentOptions = ['IT Division', 'Finance', 'Operations', 'HR', 'Sales', 'Marketing'];

const users: AdminUser[] = [
  {
    id: '1',
    fullName: 'Anna Ivanova',
    email: 'anna.ivanova@company.com',
    role: 'user',
    departments: ['IT Division', 'Finance'],
    createdAt: '2025-01-15',
  },
  {
    id: '2',
    fullName: 'Sergey Petrov',
    email: 'sergey.petrov@company.com',
    role: 'user',
    departments: ['Finance'],
    createdAt: '2025-02-20',
  },
  {
    id: '3',
    fullName: 'Maria Sokolova',
    email: 'maria.sokolova@company.com',
    role: 'admin',
    departments: ['IT Division', 'Operations', 'HR'],
    createdAt: '2024-11-10',
  },
];

export function AdminPanelPage() {
  const [modalMode, setModalMode] = useState<UserModalMode | null>(null);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);

  useEffect(() => {
    if (!modalMode) {
      return;
    }

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setModalMode(null);
        setSelectedUser(null);
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [modalMode]);

  const openCreateModal = () => {
    setSelectedUser(null);
    setModalMode('create');
  };

  const openEditModal = (user: AdminUser) => {
    setSelectedUser(user);
    setModalMode('edit');
  };

  const closeModal = () => {
    setModalMode(null);
    setSelectedUser(null);
  };

  const modalTitle = modalMode === 'edit' ? 'Редактировать пользователя' : 'Создать пользователя';
  const modalDescription =
    modalMode === 'edit'
      ? 'Обновите информацию о пользователе и назначение департаментов.'
      : 'Добавьте нового пользователя с учетными данными и доступом к департаментам.';
  const submitLabel = modalMode === 'edit' ? 'Сохранить изменения' : 'Создать пользователя';

  return (
    <>
      <Header />
      <main className="page admin-panel-page">
        <div className="admin-panel-page__container">
          <section className="admin-panel-page__hero">
            <div>
              <h1>Панель администратора</h1>
              <p>Управление учетными записями и доступом</p>
            </div>

            <button type="button" className="admin-panel-page__create-button" onClick={openCreateModal}>
              <Plus size={18} />
              <span>Создать пользователя</span>
            </button>
          </section>

          <section className="admin-panel-table-card">
            <div className="admin-panel-table">
              <div className="admin-panel-table__head">
                <span>Имя</span>
                <span>Email</span>
                <span>Роль</span>
                <span>Департаменты</span>
                <span>Создан</span>
                <span>Действия</span>
              </div>

              <div className="admin-panel-table__body">
                {users.map((user) => (
                  <article key={user.id} className="admin-panel-table__row">
                    <div className="admin-panel-table__cell admin-panel-table__cell--name">{user.fullName}</div>
                    <div className="admin-panel-table__cell admin-panel-table__cell--email">{user.email}</div>
                    <div className="admin-panel-table__cell">
                      <span className={user.role === 'admin' ? 'admin-role-badge admin-role-badge--admin' : 'admin-role-badge admin-role-badge--user'}>
                        {user.role === 'admin' ? 'Admin' : 'User'}
                      </span>
                    </div>
                    <div className="admin-panel-table__cell">
                      <div className="admin-departments">
                        {user.departments.map((department) => (
                          <span key={department} className="admin-departments__tag">
                            {department}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div className="admin-panel-table__cell admin-panel-table__cell--date">{user.createdAt}</div>
                    <div className="admin-panel-table__cell">
                      <div className="admin-panel-actions">
                        <button
                          type="button"
                          className="admin-panel-actions__button"
                          aria-label={`Редактировать ${user.fullName}`}
                          onClick={() => openEditModal(user)}
                        >
                          <Pencil size={17} />
                        </button>
                        <button type="button" className="admin-panel-actions__button" aria-label={`Удалить ${user.fullName}`}>
                          <Trash2 size={17} />
                        </button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </section>
        </div>
      </main>

      {modalMode && (
        <div className="admin-user-modal">
          <div className="admin-user-modal__backdrop" onClick={closeModal} />
          <section className="admin-user-modal__dialog" aria-modal="true" role="dialog">
            <button type="button" className="admin-user-modal__close" onClick={closeModal} aria-label="Закрыть">
              <X size={18} />
            </button>

            <header className="admin-user-modal__header">
              <h2>{modalTitle}</h2>
              <p>{modalDescription}</p>
            </header>

            <form className="admin-user-form">
              <label className="admin-user-form__field">
                <span>
                  Полное имя <strong>*</strong>
                </span>
                <input
                  type="text"
                  defaultValue={selectedUser?.fullName ?? ''}
                  placeholder="Введите полное имя"
                />
              </label>

              <label className="admin-user-form__field">
                <span>
                  Email <strong>*</strong>
                </span>
                <input
                  type="email"
                  defaultValue={selectedUser?.email ?? ''}
                  placeholder="user@company.com"
                />
              </label>

              <label className="admin-user-form__field">
                <span>
                  Пароль {modalMode === 'create' ? <strong>*</strong> : <small>(оставьте пустым, чтобы сохранить текущий)</small>}
                </span>
                <input type="password" placeholder="Введите пароль" />
              </label>

              <label className="admin-user-form__field">
                <span>
                  Роль <strong>*</strong>
                </span>
                <div className="admin-user-form__select">
                  <select defaultValue={selectedUser?.role ?? ''}>
                    <option value="" disabled>
                      Выберите роль
                    </option>
                    <option value="user">Пользователь</option>
                    <option value="admin">Администратор</option>
                  </select>
                  <ChevronDown size={18} />
                </div>
              </label>

              <div className="admin-user-form__field">
                <span>
                  Департаменты <strong>*</strong>
                </span>
                <div className="admin-user-form__departments">
                  {departmentOptions.map((department) => {
                    const checked = selectedUser?.departments.includes(department) ?? false;

                    return (
                      <label key={department} className="admin-user-form__department">
                        <input type="checkbox" defaultChecked={checked} />
                        <span>{department}</span>
                      </label>
                    );
                  })}
                </div>
                <p className="admin-user-form__hint">
                  Выберите один или несколько департаментов для этого пользователя
                </p>
              </div>

              <div className="admin-user-form__actions">
                <button type="button" className="admin-user-form__button admin-user-form__button--secondary" onClick={closeModal}>
                  Отмена
                </button>
                <button type="submit" className="admin-user-form__button admin-user-form__button--primary">
                  {submitLabel}
                </button>
              </div>
            </form>
          </section>
        </div>
      )}
    </>
  );
}
