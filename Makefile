SHELL := /bin/bash

COUNT ?= 1000
FILE ?= artifacts/load-tests/transactions.jsonl
BASE_URL ?= http://localhost:8080
USERNAME ?= admin
PASSWORD ?= AdminPassword123
BATCH_SIZE ?= 50

K6_DOCKER := docker run --rm -i --network=host --user $(shell id -u):$(shell id -g) -v $(PWD):/work -w /work/load-tests grafana/k6:0.57.0

.PHONY: up down build migrate seed superuser test generate-jsonl publish-jsonl k6-precheck smoke steady burst longrun bench-summary

up:
	docker compose up -d --build

down:
	docker compose down

build:
	docker compose build

migrate:
	docker compose exec backend python manage.py migrate

seed:
	docker compose exec backend python manage.py seed_mvp --with-demo-users

superuser:
	docker compose exec backend python manage.py createsuperuser

test:
	docker compose exec backend python manage.py test

generate-jsonl:
	python3 scripts/generate_transactions.py --target-records $(COUNT) --output-file $(FILE)

publish-jsonl:
	docker compose exec backend python /app/scripts/publish_jsonl_to_rabbit.py --file /app/$(FILE) --rabbit-url amqp://$${RABBITMQ_DEFAULT_USER:-guest}:$${RABBITMQ_DEFAULT_PASS:-guest}@rabbitmq:5672// --queue-name transactions

k6-precheck:
	@attempt=1; \
	until curl -fsS $(BASE_URL)/healthz >/dev/null; do \
	  if [ $$attempt -ge 30 ]; then \
	    echo "k6 precheck failed: $(BASE_URL)/healthz is unavailable after 30 attempts"; \
	    exit 1; \
	  fi; \
	  echo "k6 precheck: waiting for healthz (attempt $$attempt/30)"; \
	  attempt=$$((attempt + 1)); \
	  sleep 2; \
	done
	@attempt=1; \
	until curl -fsS $(BASE_URL)/readyz >/dev/null; do \
	  if [ $$attempt -ge 30 ]; then \
	    echo "k6 precheck failed: $(BASE_URL)/readyz is unavailable after 30 attempts"; \
	    exit 1; \
	  fi; \
	  echo "k6 precheck: waiting for readyz (attempt $$attempt/30)"; \
	  attempt=$$((attempt + 1)); \
	  sleep 2; \
	done

smoke:
	@$(MAKE) k6-precheck BASE_URL=$(BASE_URL)
	mkdir -p artifacts/load-tests
	$(K6_DOCKER) run --summary-export /work/artifacts/load-tests/smoke_summary.json -e BASE_URL=$(BASE_URL) -e USERNAME=$(USERNAME) -e PASSWORD=$(PASSWORD) -e BATCH_SIZE=$(BATCH_SIZE) smoke.js

steady:
	@$(MAKE) k6-precheck BASE_URL=$(BASE_URL)
	mkdir -p artifacts/load-tests
	$(K6_DOCKER) run --summary-export /work/artifacts/load-tests/steady_summary.json -e BASE_URL=$(BASE_URL) -e USERNAME=$(USERNAME) -e PASSWORD=$(PASSWORD) -e BATCH_SIZE=$(BATCH_SIZE) steady.js

burst:
	@$(MAKE) k6-precheck BASE_URL=$(BASE_URL)
	mkdir -p artifacts/load-tests
	$(K6_DOCKER) run --summary-export /work/artifacts/load-tests/burst_summary.json -e BASE_URL=$(BASE_URL) -e USERNAME=$(USERNAME) -e PASSWORD=$(PASSWORD) -e BATCH_SIZE=$(BATCH_SIZE) burst.js

longrun:
	@$(MAKE) k6-precheck BASE_URL=$(BASE_URL)
	mkdir -p artifacts/load-tests
	$(K6_DOCKER) run --summary-export /work/artifacts/load-tests/longrun_summary.json -e BASE_URL=$(BASE_URL) -e USERNAME=$(USERNAME) -e PASSWORD=$(PASSWORD) -e BATCH_SIZE=$(BATCH_SIZE) long-run.js

bench-summary:
	docker compose exec backend python manage.py bench_summary --output-dir /app/artifacts/load-tests --prometheus-url http://prometheus:9090
