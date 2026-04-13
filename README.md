# Alfa Invoice MVP Orchestrator

MVP-система формирования счетов-фактур из потока проводок с полным внутренним pipeline:

`mock ABS producer -> RabbitMQ -> Celery processor (Layer 1) -> cron-daemon/beat -> Layer 2 -> REST API -> Web App -> Prometheus/Grafana -> k6`.

## 1) Что такое Layer 1 и Layer 2

### Layer 1 (raw/intermediate)
Сырой и промежуточный контур обработки:
- `RawTransaction`
- `InboundMessageLog`
- `IdempotencyRecord`
- `AggregationGroup` (`1 drf = 1 group`)
- `DraftInvoice`, `DraftInvoiceLine`
- `ProcessingError`
- `InvoiceNumberSequence`

Layer 1 хранит вход, статусы первичной валидации, дедупликацию, draft-результат и ошибки.

### Layer 2 (final/read/export-ready)
Материализованный read/export слой:
- `FinalInvoice`, `FinalInvoiceLine`
- `ExportRecord`, `ExportAttempt`
- `InvoiceStatusHistory`
- `InvoiceFieldChangeHistory`
- `MaterializationJob`

Layer 2 используется Web Service/Web App для чтения, отчетов, retry/export workflow.

## 2) Что делает cron-daemon

`Celery beat` запускает фоновые задачи:
- выбор `DraftInvoice(status=READY)`
- materialization в Layer 2 (`FinalInvoice` + lines + export record)
- retry для `MATERIALIZATION_ERROR`
- обновление backlog/open gauges

## 3) End-to-end pipeline

1. Producer (скрипт или API ingest) генерирует payload.
2. Сообщения публикуются в RabbitMQ (очередь `transactions`).
3. Celery worker consumer:
   - валидирует schema
   - проверяет idempotency (`payload_hash`)
   - сохраняет `RawTransaction`
   - агрегирует по `drf`
   - строит `DraftInvoice` при готовности группы
4. Celery beat материализует draft в Layer 2.
5. API/Web App читают Layer 1/Layer 2.
6. Метрики экспортируются в Prometheus, графики в Grafana.
7. Нагрузка генерируется k6 или прямой publish JSONL->Rabbit.

## 4) Бизнес-правило `1 drf = 1 invoice flow`

- `1 drf = 1 aggregation group = 1 draft invoice`.
- В группе: `1..N INCOME` + ровно `1 VAT`.
- Внутри группы должны совпадать `counterpartyId`, `departmentId`, `date`.
- Несовпадение -> `VALIDATION_ERROR`.

## 5) Сервисы (docker compose)

- `nginx` (gateway)
- `backend` (Django + DRF + /metrics)
- `worker` (Celery consumer)
- `beat` (cron-daemon)
- `postgres`
- `rabbitmq` (+ management)
- `mock_abs_producer` (опционально, профиль `tools`)
- `prometheus`
- `grafana`
- `postgres_exporter`
- `rabbitmq_exporter`
- `cadvisor`
- `webapp` (React/Vite)

## 6) Запуск docker compose (с нуля)

```bash
git clone <repo-url>
cd alfa-invoice-orchestrator
cp .env.example .env
make up
```

Проверка статуса:

```bash
docker compose ps
```

Остановка:

```bash
make down
```

## 7) Миграции

```bash
make migrate
```

## 8) Seed данных

```bash
make seed
```

Создаются:
- Department IDs: `101..104` (`factoring/accounting/taxation/acquiring`)
- Counterparty IDs: `10001..10005`
- admin user из `.env`
- demo role users (`factoring_user`, `accounting_user`, `taxation_user`, `acquiring_user`, пароль `password`)

## 9) Admin

- URL: `http://localhost:8080/admin/` (через nginx)
- Логин: `DJANGO_SUPERUSER_USERNAME`
- Пароль: `DJANGO_SUPERUSER_PASSWORD`

## 10) Генерация mock JSONL

```bash
make generate-jsonl COUNT=10000
```

Прямой запуск:

```bash
python3 scripts/generate_transactions.py \
  --target-records 10000 \
  --output-file artifacts/load-tests/transactions.jsonl \
  --min-income-lines-per-drf 1 \
  --max-income-lines-per-drf 5 \
  --allowed-vat-rates 0.1,0.2 \
  --random-seed 42 \
  --batch-size 200
```

## 11) Публикация JSONL в RabbitMQ

```bash
make publish-jsonl FILE=artifacts/load-tests/transactions.jsonl
```

Прямой запуск:

```bash
python3 scripts/publish_jsonl_to_rabbit.py \
  --file artifacts/load-tests/transactions.jsonl \
  --rabbit-url amqp://guest:guest@localhost:5672// \
  --queue-name transactions \
  --task-name invoices.process_transaction \
  --batch-size 200
```

## 12) k6 нагрузка

Все сценарии бьют в `POST /api/v1/ingest/transactions`.

```bash
make smoke
make steady
make burst
make longrun
```

Артефакты:
- `artifacts/load-tests/smoke_summary.json`
- `artifacts/load-tests/steady_summary.json`
- `artifacts/load-tests/burst_summary.json`
- `artifacts/load-tests/longrun_summary.json`

## 13) URL-ы

- Backend gateway: `http://localhost:8080`
- API docs (Swagger): `http://localhost:8080/api/docs/`
- API schema: `http://localhost:8080/api/schema/`
- Web App: `http://localhost:8080/`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`
- RabbitMQ management: `http://localhost:15672`
- Direct backend (container): `http://localhost:8001`

## 14) Где смотреть summary/цифры

1. API:
```bash
GET /api/v1/reports/summary
GET /api/v1/reports/load-test-summary
GET /api/v1/reports/export.csv
```

2. Management command:
```bash
make bench-summary
```

Пишет:
- `artifacts/load-tests/summary_*.json`
- `artifacts/load-tests/summary_*.csv`
- `artifacts/load-tests/summary_*.md`
- latest copies: `summary_latest.*`

3. Grafana dashboard:
- `Alfa Invoice MVP` (auto-provisioned)

## 15) Ограничения MVP

- Нет реальной внешней доставки export (симуляция через `ExportRecord/ExportAttempt`).
- Нет полноценного RBAC UI, только role-based scope на API.
- Retry export реализован как MVP-state transition.
- Фокус на демонстрацию полного pipeline, измеримость и bottlenecks.

---

## API Endpoints

### Technical
- `GET /healthz`
- `GET /readyz`
- `GET /metrics`

### Ingest
- `POST /api/v1/ingest/transactions`

### Layer 1
- `GET /api/v1/raw-transactions`
- `GET /api/v1/aggregation-groups`
- `GET /api/v1/aggregation-groups/{id}`
- `POST /api/v1/aggregation-groups/{id}/reprocess`
- `GET /api/v1/draft-invoices`
- `GET /api/v1/draft-invoices/{id}`

### Layer 2
- `GET /api/v1/final-invoices`
- `GET /api/v1/final-invoices/{id}`
- `POST /api/v1/final-invoices/{id}/retry`
- `GET /api/v1/export-records`

### Reports
- `GET /api/v1/reports/summary`
- `GET /api/v1/reports/export.csv`
- `GET /api/v1/reports/load-test-summary`

### Additional operational views
- `GET /api/v1/processing-errors`
- `GET /api/v1/inbound-logs`

---

## Метрики (custom)

- Ingest: `transactions_received_total`, `transactions_published_total`, `transactions_duplicate_total`, `transactions_invalid_schema_total`
- Processor: `transactions_consumed_total`, `transactions_ack_total`, `transactions_nack_total`, `transactions_dlq_total`, `processor_duration_seconds`
- Aggregation/Layer1: `aggregation_groups_created_total`, `aggregation_groups_ready_total`, `aggregation_groups_validation_error_total`, `aggregation_group_size_histogram`, `draft_invoices_created_total`, `draft_invoices_validation_error_total`, `transaction_to_draft_latency_seconds`, `open_groups_gauge`
- Cron/transfer: `layer2_materialization_total`, `layer2_materialization_error_total`, `layer2_materialization_duration_seconds`, `retry_attempts_total`, `transfer_backlog_gauge`
- Layer2/export: `final_invoices_created_total`, `final_invoices_export_ready_total`, `final_invoices_export_error_total`, `export_attempt_duration_seconds`
- DB/infra: `db_write_duration_seconds`, `db_read_duration_seconds`, `queue_backlog_gauge`, `last_successful_processing_timestamp`

Infra metrics через exporters/cAdvisor также доступны в Prometheus.

---

## Make targets

- `make up`
- `make down`
- `make build`
- `make migrate`
- `make seed`
- `make superuser`
- `make test`
- `make generate-jsonl COUNT=...`
- `make publish-jsonl FILE=...`
- `make smoke`
- `make steady`
- `make burst`
- `make longrun`
- `make bench-summary`
