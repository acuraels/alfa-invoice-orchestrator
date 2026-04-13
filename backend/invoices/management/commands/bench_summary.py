import csv
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from django.core.management.base import BaseCommand

from invoices.services import summary_snapshot


def query_prometheus(prometheus_url: str, promql: str) -> float | None:
    params = urlencode({"query": promql})
    url = f"{prometheus_url.rstrip('/')}/api/v1/query?{params}"
    try:
        with urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
            result = payload.get("data", {}).get("result", [])
            if not result:
                return None
            value = result[0].get("value", [None, None])[1]
            return float(value) if value is not None else None
    except Exception:  # noqa: BLE001
        return None


class Command(BaseCommand):
    help = "Build load test summary artifacts in JSON/CSV/Markdown"

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            default="/app/artifacts/load-tests",
            help="Directory for summary files",
        )
        parser.add_argument(
            "--prometheus-url",
            default="http://prometheus:9090",
            help="Prometheus URL for infra snapshot",
        )

    def handle(self, *args, **options):
        output_dir = Path(options["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        summary = summary_snapshot()

        prom_url = options["prometheus_url"]
        cpu_backend = query_prometheus(
            prom_url,
            'sum(rate(container_cpu_usage_seconds_total{name=~".*backend.*"}[5m]))',
        )
        cpu_worker = query_prometheus(
            prom_url,
            'sum(rate(container_cpu_usage_seconds_total{name=~".*worker.*"}[5m]))',
        )
        cpu_postgres = query_prometheus(
            prom_url,
            'sum(rate(container_cpu_usage_seconds_total{name=~".*postgres.*"}[5m]))',
        )
        mem_backend = query_prometheus(
            prom_url,
            'sum(container_memory_working_set_bytes{name=~".*backend.*"})',
        )

        summary["infra_snapshot"] = {
            "cpu_backend": cpu_backend,
            "cpu_worker": cpu_worker,
            "cpu_postgres": cpu_postgres,
            "mem_backend": mem_backend,
        }

        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        json_path = output_dir / f"summary_{ts}.json"
        csv_path = output_dir / f"summary_{ts}.csv"
        md_path = output_dir / f"summary_{ts}.md"

        json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["metric", "value"])
            for key, value in summary.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        writer.writerow([f"{key}.{sub_key}", sub_value])
                else:
                    writer.writerow([key, value])

        md_lines = ["# Load Test Summary", ""]
        for key, value in summary.items():
            if isinstance(value, dict):
                md_lines.append(f"## {key}")
                for sub_key, sub_value in value.items():
                    md_lines.append(f"- {sub_key}: {sub_value}")
            else:
                md_lines.append(f"- {key}: {value}")
        md_lines.append("")
        md_path.write_text("\n".join(md_lines), encoding="utf-8")

        latest_json = output_dir / "summary_latest.json"
        latest_csv = output_dir / "summary_latest.csv"
        latest_md = output_dir / "summary_latest.md"
        latest_json.write_text(json_path.read_text(encoding="utf-8"), encoding="utf-8")
        latest_csv.write_text(csv_path.read_text(encoding="utf-8"), encoding="utf-8")
        latest_md.write_text(md_path.read_text(encoding="utf-8"), encoding="utf-8")

        self.stdout.write(self.style.SUCCESS(f"Written: {json_path}"))
        self.stdout.write(self.style.SUCCESS(f"Written: {csv_path}"))
        self.stdout.write(self.style.SUCCESS(f"Written: {md_path}"))
