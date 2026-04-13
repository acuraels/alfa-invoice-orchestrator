#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from celery import Celery


def main():
    parser = argparse.ArgumentParser(description="Publish JSONL transactions into RabbitMQ as Celery tasks")
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--rabbit-url", default="amqp://guest:guest@localhost:5672//")
    parser.add_argument("--queue-name", default="transactions")
    parser.add_argument("--task-name", default="invoices.process_transaction")
    parser.add_argument("--batch-size", type=int, default=200)
    args = parser.parse_args()

    app = Celery("publisher", broker=args.rabbit_url)

    published = 0
    with args.file.open("r", encoding="utf-8") as handle:
        chunk: list[dict] = []
        for line in handle:
            line = line.strip()
            if not line:
                continue
            chunk.append(json.loads(line))
            if len(chunk) >= args.batch_size:
                for payload in chunk:
                    app.send_task(
                        args.task_name,
                        args=[payload, None, "RABBIT_DIRECT"],
                        queue=args.queue_name,
                    )
                    published += 1
                chunk = []

        for payload in chunk:
            app.send_task(
                args.task_name,
                args=[payload, None, "RABBIT_DIRECT"],
                queue=args.queue_name,
            )
            published += 1

    print(f"Published {published} messages from {args.file} to queue {args.queue_name}")


if __name__ == "__main__":
    main()
