"""Schedule ingestion pipeline.

Orchestrates adapter dispatch, schedule validation, and output serialization.
"""

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contracts import DAYS, StationSchedule, now_utc_iso
from .adapters.registry import run_adapter


@dataclass(slots=True)
class ScrapeHealth:
    station_id: str
    source_tier: str
    confidence: float
    success: bool
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "station_id": self.station_id,
            "source_tier": self.source_tier,
            "confidence": self.confidence,
            "success": self.success,
            "errors": self.errors,
        }


def is_healthy_station(station: dict[str, Any]) -> bool:
    return station.get("health_status") != "bad"


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    temp_path.replace(path)


def validate_schedule_quality(station_schedule: StationSchedule) -> list[str]:
    warnings: list[str] = []
    for day in DAYS:
        slots = station_schedule.schedule.get(day, [])
        seen_ranges: set[tuple[str, str, str]] = set()
        for slot in slots:
            key = (slot.title, slot.start_time, slot.end_time)
            if key in seen_ranges:
                warnings.append(
                    f"{day}:duplicate_slot:{slot.title}:{slot.start_time}-{slot.end_time}"
                )
            seen_ranges.add(key)
            if not re.match(r"^\d{2}:\d{2}$", slot.start_time) or not re.match(
                r"^\d{2}:\d{2}$", slot.end_time
            ):
                warnings.append(f"{day}:invalid_time_format:{slot.title}")
    return warnings


async def build_station_schedule(
    station: dict[str, Any],
    source_rules: dict[str, Any],
) -> tuple[StationSchedule, ScrapeHealth]:
    station_id = station["id"]
    station_rules = source_rules.get("stations", {}).get(
        station_id, source_rules.get("default", {})
    )
    errors: list[str] = []

    try:
        schedule = await run_adapter(station, station_rules)
    except Exception as exc:
        errors.append(f"adapter_error:{exc}")
        from .adapters import seed
        schedule = await seed.fetch(station)

    quality_warnings = validate_schedule_quality(schedule)
    if quality_warnings:
        schedule.errors.extend(quality_warnings)

    return schedule, ScrapeHealth(
        station_id=station_id,
        source_tier=schedule.source_tier,
        confidence=schedule.confidence,
        success=len(errors) == 0,
        errors=errors + quality_warnings,
    )


async def build_schedules_for_stations(
    stations: list[dict[str, Any]],
    source_rules: dict[str, Any],
    concurrency: int = 10,
) -> tuple[list[StationSchedule], list[ScrapeHealth]]:
    semaphore = asyncio.Semaphore(concurrency)

    async def _build(station: dict[str, Any]) -> tuple[StationSchedule, ScrapeHealth]:
        async with semaphore:
            return await build_station_schedule(station, source_rules)

    results = await asyncio.gather(
        *[_build(s) for s in stations], return_exceptions=True
    )

    schedules: list[StationSchedule] = []
    health_rows: list[ScrapeHealth] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            sid = stations[i]["id"]
            health_rows.append(
                ScrapeHealth(
                    station_id=sid,
                    source_tier="error",
                    confidence=0.0,
                    success=False,
                    errors=[str(result)],
                )
            )
        else:
            sched, health = result
            schedules.append(sched)
            health_rows.append(health)

    return schedules, health_rows


def schedules_payload(schedules: list[StationSchedule]) -> dict[str, Any]:
    return {
        "version": "0.4.0",
        "last_updated": now_utc_iso(),
        "count": len(schedules),
        "schedules": [schedule.to_dict() for schedule in schedules],
    }


def scrape_report_payload(health_rows: list[ScrapeHealth]) -> dict[str, Any]:
    stale_count = sum(1 for row in health_rows if not row.success)
    return {
        "version": "0.2.0",
        "generated_at": now_utc_iso(),
        "stations_checked": len(health_rows),
        "failed_stations": stale_count,
        "rows": [row.to_dict() for row in health_rows],
    }


def load_source_rules(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"default": {"tier": "tier3_seed"}, "stations": {}}
    return json.loads(path.read_text(encoding="utf-8"))


async def run_ingestion(
    stations: list[dict[str, Any]],
    source_rules_path: Path,
    schedules_output_path: Path,
    scrape_report_path: Path,
    dry_run: bool = False,
) -> tuple[list[StationSchedule], dict[str, Any]]:
    healthy_stations = [s for s in stations if is_healthy_station(s)]
    source_rules = load_source_rules(source_rules_path)
    schedules, health_rows = await build_schedules_for_stations(
        healthy_stations, source_rules
    )
    schedules_json = schedules_payload(schedules)
    health_json = scrape_report_payload(health_rows)
    if not dry_run:
        _atomic_write_json(schedules_output_path, schedules_json)
        _atomic_write_json(scrape_report_path, health_json)
    return schedules, health_json
