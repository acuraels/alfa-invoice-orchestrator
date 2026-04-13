#!/usr/bin/env python3
import argparse
import json
import random
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

DEPARTMENT_IDS = [101, 102, 103, 104]
COUNTERPARTY_IDS = [10001, 10002, 10003, 10004, 10005]
PRODUCTS = [
    "Factoring Service",
    "Accounting Service",
    "Tax Advisory",
    "Acquiring Maintenance",
    "Backoffice Support",
]
UNITS = ["pcs", "service", "hour"]


def q(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def parse_rates(raw: str) -> list[Decimal]:
    rates = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        rates.append(Decimal(item))
    if not rates:
        raise argparse.ArgumentTypeError("allowed vat rates list cannot be empty")
    return rates


def build_group(drf: str, tx_date: date, min_lines: int, max_lines: int, vat_rates: list[Decimal]):
    department_id = random.choice(DEPARTMENT_IDS)
    counterparty_id = random.choice(COUNTERPARTY_IDS)
    vat_rate = random.choice(vat_rates)
    incomes = []

    line_count = random.randint(min_lines, max_lines)
    vat_total = Decimal("0")

    for line_idx in range(1, line_count + 1):
        quantity = q(Decimal(str(random.uniform(1, 20))))
        unit_price = q(Decimal(str(random.uniform(100, 5000))))
        amount_without_vat = q(quantity * unit_price)
        vat_amount = q(amount_without_vat * vat_rate)
        vat_total += vat_amount

        incomes.append(
            {
                "transactionId": f"{drf}-INC-{line_idx:03d}",
                "drf": drf,
                "type": "INCOME",
                "counterpartyId": counterparty_id,
                "departmentId": department_id,
                "date": tx_date.isoformat(),
                "productName": random.choice(PRODUCTS),
                "unitMeasure": random.choice(UNITS),
                "quantity": str(quantity),
                "unitPrice": str(unit_price),
                "vatRate": str(vat_rate),
            }
        )

    vat_tx = {
        "transactionId": f"{drf}-VAT-001",
        "drf": drf,
        "type": "VAT",
        "counterpartyId": counterparty_id,
        "departmentId": department_id,
        "date": tx_date.isoformat(),
        "vatRate": str(vat_rate),
        "vatAmount": str(q(vat_total)),
    }

    return incomes + [vat_tx]


def generate_records(
    target_records: int,
    min_lines: int,
    max_lines: int,
    vat_rates: list[Decimal],
) -> list[dict]:
    records: list[dict] = []
    drf_seq = 1

    while len(records) < target_records:
        tx_date = date.today() - timedelta(days=random.randint(0, 14))
        drf = f"DRF-{tx_date.strftime('%Y%m%d')}-{drf_seq:08d}"
        drf_seq += 1
        records.extend(build_group(drf, tx_date, min_lines, max_lines, vat_rates))

    return records[:target_records]


def main():
    parser = argparse.ArgumentParser(description="Generate mock transactions JSONL for Alfa invoice flow")
    parser.add_argument("--target-records", "--count", type=int, default=1000)
    parser.add_argument("--output-file", type=Path, default=Path("artifacts/load-tests/transactions.jsonl"))
    parser.add_argument("--min-income-lines-per-drf", type=int, default=1)
    parser.add_argument("--max-income-lines-per-drf", type=int, default=5)
    parser.add_argument("--allowed-vat-rates", type=parse_rates, default=parse_rates("0.1,0.2"))
    parser.add_argument("--random-seed", type=int, default=42)
    parser.add_argument("--batch-size", type=int, default=100)
    args = parser.parse_args()

    if args.min_income_lines_per_drf > args.max_income_lines_per_drf:
        raise ValueError("min-income-lines-per-drf must be <= max-income-lines-per-drf")

    random.seed(args.random_seed)

    records = generate_records(
        target_records=args.target_records,
        min_lines=args.min_income_lines_per_drf,
        max_lines=args.max_income_lines_per_drf,
        vat_rates=args.allowed_vat_rates,
    )

    args.output_file.parent.mkdir(parents=True, exist_ok=True)
    with args.output_file.open("w", encoding="utf-8") as handle:
        for idx in range(0, len(records), args.batch_size):
            for payload in records[idx : idx + args.batch_size]:
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    print(f"Generated {len(records)} records -> {args.output_file}")


if __name__ == "__main__":
    main()
