import { useState } from 'react';
import { isAxiosError } from 'axios';
import toast from 'react-hot-toast';
import { Lock, ShieldCheck } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../../services/authService';
import './LogInPage.css';

type FormValues = {
  login: string;
  password: string;
};

type FormErrors = Partial<Record<keyof FormValues, string>>;

const initialValues: FormValues = {
  login: '',
  password: '',
};

export function LogInPage() {
  const navigate = useNavigate();
  const [values, setValues] = useState<FormValues>(initialValues);
  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validate = (formValues: FormValues) => {
    const nextErrors: FormErrors = {};

    if (!formValues.login.trim()) {
      nextErrors.login = 'Введите логин.';
    }

    if (!formValues.password.trim()) {
      nextErrors.password = 'Введите пароль.';
    }

    return nextErrors;
  };

  const handleChange = (field: keyof FormValues, value: string) => {
    setValues((current) => ({ ...current, [field]: value }));

    if (errors[field]) {
      setErrors((current) => ({ ...current, [field]: undefined }));
    }
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const nextErrors = validate(values);
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length > 0) {
      toast.error('Заполните логин и пароль.');
      return;
    }

    try {
      setIsSubmitting(true);

      const response = await authService.login({
        username: values.login.trim(),
        password: values.password,
      });

      toast.success(`Вход выполнен: ${response.user.username} (${response.user.role}).`);
      setValues((current) => ({ ...current, password: '' }));
      navigate('/invoice-list');
    } catch (error) {
      if (isAxiosError(error) && error.response?.status === 401) {
        toast.error('Неверный логин или пароль.');
      } else {
        toast.error('Не удалось выполнить вход. Попробуйте позднее.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSsoClick = () => {
    toast('Функционал корпоративного SSO в разработке.', {
      icon: '🚧',
    });
  };

  return (
    <section className="page login-page">
      <div className="login-page__card">
        <h1>Вход в систему</h1>

        <form className="login-page__form" onSubmit={handleSubmit} noValidate>
          <label className="login-page__group">
            <span>Логин</span>
            <input
              type="text"
              value={values.login}
              onChange={(event) => handleChange('login', event.target.value)}
              placeholder="ivanov_aa"
              autoComplete="username"
              disabled={isSubmitting}
              className={errors.login ? 'login-page__input login-page__input--error' : 'login-page__input'}
            />
            {errors.login && <small className="login-page__error">{errors.login}</small>}
          </label>

          <label className="login-page__group">
            <span>Пароль</span>
            <input
              type="password"
              value={values.password}
              onChange={(event) => handleChange('password', event.target.value)}
              placeholder="SuperSecretPassword123"
              autoComplete="current-password"
              disabled={isSubmitting}
              className={errors.password ? 'login-page__input login-page__input--error' : 'login-page__input'}
            />
            {errors.password && <small className="login-page__error">{errors.password}</small>}
          </label>

          <button type="submit" className="login-page__submit" disabled={isSubmitting}>
            {isSubmitting ? 'Входим...' : 'Войти'}
          </button>
        </form>

        <div className="login-page__divider">
          <span>или</span>
        </div>

        <button type="button" className="login-page__sso" onClick={handleSsoClick} disabled={isSubmitting}>
          <Lock size={18} />
          <span>Войти через корпоративный SSO</span>
          <ShieldCheck size={18} className="login-page__sso-check" />
        </button>
      </div>
    </section>
  );
}
