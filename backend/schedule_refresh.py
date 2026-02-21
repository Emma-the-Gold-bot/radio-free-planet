from __future__ import annotations

import argparse
import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from station_registry import StationRegistry
from schedule_pipeline.ingestion import run_ingestion
from schedule_pipeline.resolver import build_now_playing


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "static" / "data"
STATIONS_PATH = DATA_DIR / "stations.json"
SCHEDULE_SOURCES_PATH = DATA_DIR / "schedule_sources.json"
SCHEDULES_PATH = DATA_DIR / "schedules.json"
NOW_PLAYING_PATH = DATA_DIR / "now_playing.json"
SCRAPE_REPORT_PATH = DATA_DIR / "scrape_health_report.json"


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    temp.replace(path)


async def run_refresh_once(dry_run: bool = False) -> dict[str, Any]:
    registry = StationRegistry(STATIONS_PATH)
    stations = registry.list_stations()
    schedules, health_report = await run_ingestion(
        stations=stations,
        source_rules_path=SCHEDULE_SOURCES_PATH,
        schedules_output_path=SCHEDULES_PATH,
        scrape_report_path=SCRAPE_REPORT_PATH,
        dry_run=dry_run,
    )
    now_playing_payload = build_now_playing(schedules)
    if not dry_run:
        _atomic_write_json(NOW_PLAYING_PATH, now_playing_payload)

    return {
        "stations_total": len(stations),
        "schedules_written": len(schedules),
        "now_playing_count": now_playing_payload["count"],
        "failed_scrapes": health_report["failed_stations"],
        "dry_run": dry_run,
    }


def run_backfill(hours: int) -> dict[str, Any]:
    schedules_path = SCHEDULES_PATH
    if not schedules_path.exists():
        raise RuntimeError("Cannot backfill without schedules.json. Run refresh first.")

    raw = json.loads(schedules_path.read_text(encoding="utf-8"))
    schedules = raw.get("schedules", [])
    # Backfill checks expected coverage at hourly slices.
    now = datetime.now(timezone.utc)
    slices = []
    for hour in range(hours):
        ts = now - timedelta(hours=hour)
        active = 0
        for schedule in schedules:
            tz_name = schedule.get("timezone") or "UTC"
            # Keep this lightweight: count as active if schedule has entries for local weekday.
            # Resolver remains source of truth.
            try:
                local_day = ts.astimezone(ZoneInfo(tz_name)).weekday()
            except Exception:
                local_day = ts.weekday()
            day_name = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][local_day]
            if schedule.get("schedule", {}).get(day_name):
                active += 1
        slices.append({"timestamp": ts.isoformat(), "stations_with_schedule": active})
    return {"hours": hours, "slices": slices}


async def run_worker(interval_seconds: int, dry_run: bool = False) -> None:
    while True:
        started = time.time()
        result = await run_refresh_once(dry_run=dry_run)
        print(
            f"[schedule-worker] refreshed stations={result['schedules_written']} "
            f"now_playing={result['now_playing_count']} failed={result['failed_scrapes']}"
        )
        elapsed = time.time() - started
        sleep_for = max(1, interval_seconds - int(elapsed))
        time.sleep(sleep_for)


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh schedules and now-playing snapshots.")
    parser.add_argument("--dry-run", action="store_true", help="Run pipeline without writing JSON files.")
    parser.add_argument("--worker", action="store_true", help="Run forever with interval-based refresh.")
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=300,
        help="Refresh interval for worker mode. Default is 300 seconds.",
    )
    parser.add_argument(
        "--backfill-hours",
        type=int,
        default=0,
        help="Emit hourly coverage slices for N previous hours.",
    )
    args = parser.parse_args()

    if args.worker:
        asyncio.run(run_worker(interval_seconds=args.interval_seconds, dry_run=args.dry_run))
        return

    summary = asyncio.run(run_refresh_once(dry_run=args.dry_run))
    print(json.dumps(summary, indent=2))
    if args.backfill_hours > 0:
        print(json.dumps(run_backfill(args.backfill_hours), indent=2))


if __name__ == "__main__":
    main()

