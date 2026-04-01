# Alfa Invoice Orchestrator

Backend для локальной разработки и проверки JWT-аутентификации, ролей доступа и PostgreSQL-конфигурации. Репозиторий также содержит frontend, но в рамках текущей задачи подготовлен полноценный Django + Django REST Framework backend с удобным запуском локально и через Docker.

## Стек

- Python 3.12
- Django
- Django REST Framework
- djangorestframework-simplejwt
- PostgreSQL
- Docker
- docker compose

## Что реализовано

- JWT-аутентификация через `djangorestframework-simplejwt`
- `POST /api/auth/refresh/`
- Access token на 15 минут
- Refresh token на 7 дней
- Кастомная модель пользователя с ролью
- Django admin с управлением ролями
- Базовая архитектура для фильтрации queryset по роли
- Docker-setup с PostgreSQL и автоматическими миграциями
- Базовые тесты auth API

## JWT API

### Refresh

`POST /api/auth/refresh/`

Request:

```json
{
  "refresh": "<jwt_refresh>"
}
```

Response `200 OK`:

```json
{
  "access": "<new_jwt_access>"
}
```

### Передача access token

Используется заголовок:

```text
Authorization: Bearer <access_token>
```

## Роли

- `admin` — полный доступ ко всем данным
- `factoring` — доступ только к подразделению `Факторинг`
- `accounting` — доступ только к подразделению `Бухучет`
- `taxation` — доступ только к подразделению `Налогообложение`
- `acquiring` — доступ только к подразделению `Эквайринг`

Фильтрация для будущих viewset'ов и API заложена в `common/role_scope.py`. Там есть:

- `filter_queryset_by_role(queryset, user, department_field="department")`
- `RoleScopedQuerysetMixin`

Пример использования:

```python
from common.role_scope import RoleScopedQuerysetMixin


class InvoiceViewSet(RoleScopedQuerysetMixin, ModelViewSet):
    queryset = Invoice.objects.all()
    role_scope_department_field = "department"
```

## Требования

- Python 3.12+
- PostgreSQL 15+ или совместимый
- Docker и Docker Compose Plugin

## Переменные окружения

Скопируйте шаблон:

```bash
cp .env.example .env
```

Основные переменные:

- `SECRET_KEY` — Django secret key
- `DEBUG` — режим отладки
- `ALLOWED_HOSTS` — список хостов через запятую
- `TIME_ZONE` — timezone проекта
- `POSTGRES_DB` — имя базы данных
- `POSTGRES_USER` — пользователь PostgreSQL
- `POSTGRES_PASSWORD` — пароль PostgreSQL
- `POSTGRES_HOST` — хост PostgreSQL
- `POSTGRES_PORT` — порт PostgreSQL
- `POSTGRES_EXPOSED_PORT` — внешний порт контейнерного PostgreSQL на хосте
- `DJANGO_SUPERUSER_USERNAME` — логин начального администратора
- `DJANGO_SUPERUSER_EMAIL` — email начального администратора
- `DJANGO_SUPERUSER_PASSWORD` — пароль начального администратора

`.env` не должен попадать в git.

## Запуск локально без Docker

1. Создайте и активируйте виртуальное окружение.
2. Скопируйте `.env.example` в `.env` и укажите параметры вашего PostgreSQL.
3. Установите зависимости.
4. Примените миграции.
5. Создайте суперпользователя.
6. Запустите сервер.

Команды:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Запуск через Docker

Базовый сценарий:

```bash
git clone <repo-url>
cd alfa-invoice-orchestrator
cp .env.example .env
docker compose up --build
```

После старта будут автоматически выполнены:

- установка зависимостей из `requirements.txt`
- применение миграций
- попытка создать начального администратора из `DJANGO_SUPERUSER_*`
- запуск Django на `http://localhost:8000`

Админка доступна на `http://localhost:8000/admin/`.
PostgreSQL из Docker по умолчанию будет доступен на `127.0.0.1:5433`, чтобы не конфликтовать с локальной БД на стандартном `5432`.

Если нужно вручную выполнить команды в контейнере:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py test
```

## Примеры curl

### Refresh

```bash
curl -X POST http://localhost:8000/api/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "<jwt_refresh>"
  }'
```

## Типовой workflow первого запуска

1. Клонировать репозиторий.
2. Скопировать `.env.example` в `.env`.
3. При необходимости поменять креды PostgreSQL и суперпользователя.
4. Выполнить `docker compose up --build`.
5. Авторизоваться в admin или использовать bootstrap-пользователя из `.env`.
6. Проверить auth endpoints.

## Тесты

Есть базовые тесты auth API и JWT flow.

Запуск локально:

```bash
python manage.py test
```

Запуск в Docker:

```bash
docker compose exec backend python manage.py test
```

## Структура проекта

```text
.
├── backend/                # Django project settings, urls, ASGI/WSGI
├── common/                 # Общие utilities, включая role scope helper
├── users/                  # Кастомный пользователь, auth API, admin, tests
├── frontend/               # Frontend часть репозитория
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── requirements.txt
└── manage.py
```
