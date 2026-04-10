#!/bin/sh
set -eu

cd /app/backend

echo "Applying database migrations..."
until python manage.py migrate --noinput; do
  echo "Database is unavailable, retrying in 2 seconds..."
  sleep 2
done

echo "Bootstrapping initial superuser if configured..."
python manage.py bootstrap_superuser

echo "Starting Django development server..."
exec python manage.py runserver 0.0.0.0:8000
