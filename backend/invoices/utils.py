import csv
import hashlib
import json
from pathlib import Path
from typing import Iterable

from django.utils import timezone


def stable_payload_hash(payload: dict) -> str:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_csv(path: Path, headers: list[str], rows: Iterable[list[str]]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        for row in rows:
            writer.writerow(row)


def utc_now_iso() -> str:
    return timezone.now().isoformat()
