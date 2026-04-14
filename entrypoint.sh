#!/bin/sh
set -eu

ROLE="${1:-web}"
TRANSACTIONS_QUEUE="${CELERY_TRANSACTIONS_QUEUE:-transactions}"
MATERIALIZATION_QUEUE="${CELERY_MATERIALIZATION_QUEUE:-materialization}"
MAINTENANCE_QUEUE="${CELERY_MAINTENANCE_QUEUE:-maintenance}"
WORKER_TX_CONCURRENCY="${CELERY_WORKER_TRANSACTIONS_CONCURRENCY:-4}"
WORKER_MATERIALIZATION_CONCURRENCY="${CELERY_WORKER_MATERIALIZATION_CONCURRENCY:-2}"
BEAT_SCHEDULE_FILE="${CELERY_BEAT_SCHEDULE_FILE:-/tmp/celerybeat-schedule}"

cd /app/backend

if [ -n "${PROMETHEUS_MULTIPROC_DIR:-}" ]; then
  mkdir -p "$PROMETHEUS_MULTIPROC_DIR"
  if [ "$ROLE" = "web" ]; then
    rm -f "$PROMETHEUS_MULTIPROC_DIR"/* || true
  fi
fi

wait_for_db() {
  until python - <<'PY' >/dev/null 2>&1
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
import django
django.setup()
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("SELECT 1")
    cursor.fetchone()
PY
  do
    echo "Database unavailable, waiting 2s..."
    sleep 2
  done
}

prepare_app() {
  python manage.py migrate --noinput
  python manage.py bootstrap_superuser
  python manage.py seed_mvp --with-demo-users
}

case "$ROLE" in
  web)
    wait_for_db
    prepare_app
    exec gunicorn backend.wsgi:application --bind 0.0.0.0:8000 --workers 2 --timeout 120
    ;;
  worker)
    wait_for_db
    exec celery -A backend worker -l info \
      -Q "$TRANSACTIONS_QUEUE" \
      --concurrency "$WORKER_TX_CONCURRENCY" \
      --hostname "worker.transactions@%h"
    ;;
  worker-materialization)
    wait_for_db
    exec celery -A backend worker -l info \
      -Q "$MATERIALIZATION_QUEUE,$MAINTENANCE_QUEUE" \
      --concurrency "$WORKER_MATERIALIZATION_CONCURRENCY" \
      --hostname "worker.materialization@%h"
    ;;
  beat)
    wait_for_db
    exec celery -A backend beat -l info --schedule "$BEAT_SCHEDULE_FILE"
    ;;
  *)
    exec "$@"
    ;;
esac
