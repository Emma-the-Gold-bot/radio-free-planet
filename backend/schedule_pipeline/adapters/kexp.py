"""KEXP 90.3 FM — Tier 1 API adapter using api.kexp.org/v2.

The KEXP API returns historical broadcasts (the last N shows aired). We build
a weekly schedule template by grouping broadcasts by weekday and program,
keeping the most recent instance of each program per day, and computing end
times from adjacent shows.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from ..contracts import DAYS, ShowSlot, StationSchedule, empty_week_schedule, now_utc_iso
from ..genres import normalize_genre


KEXP_API_BASE = "https://api.kexp.org/v2"


def _round_to_slot(minutes: int) -> int:
    """Round to nearest 30-minute slot for deduplication.

    KEXP shows are typically 1-3 hour blocks, so a 30-minute window safely
    merges instances that start a few minutes apart on different weeks.
    """
    return (minutes // 30) * 30


async def fetch(station: dict[str, Any]) -> StationSchedule:
    errors: list[str] = []
    tz_name = station.get("timezone", "America/Los_Angeles")
    tz = ZoneInfo(tz_name)

    # Collect raw broadcasts grouped by weekday
    day_broadcasts: dict[int, list[dict[str, Any]]] = defaultdict(list)

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(f"{KEXP_API_BASE}/shows/", params={"limit": 300})
        resp.raise_for_status()
        data = resp.json()

        for show in data.get("results", []):
            start_raw = show.get("start_time")
            if not start_raw:
                continue
            try:
                start_dt = datetime.fromisoformat(start_raw.replace("Z", "+00:00"))
                start_local = start_dt.astimezone(tz)
                day_broadcasts[start_local.weekday()].append({
                    "program_name": show.get("program_name") or "Unknown Show",
                    "host_names": show.get("host_names") or [],
                    "program_tags": show.get("program_tags") or "eclectic",
                    "tagline": show.get("tagline"),
                    "program_image_uri": show.get("program_image_uri"),
                    "start_local": start_local,
                    "start_minutes": start_local.hour * 60 + start_local.minute,
                })
            except Exception as exc:
                errors.append(f"kexp_parse:{exc}")

    schedule = empty_week_schedule()

    for weekday in range(7):
        broadcasts = day_broadcasts.get(weekday, [])
        if not broadcasts:
            continue

        # Deduplicate: group by (program_name, rounded_start_time), keep most recent
        seen: dict[tuple[str, int], dict[str, Any]] = {}
        for bc in broadcasts:
            key = (bc["program_name"], _round_to_slot(bc["start_minutes"]))
            existing = seen.get(key)
            if not existing or bc["start_local"] > existing["start_local"]:
                seen[key] = bc

        # Sort by start time
        unique_broadcasts = sorted(seen.values(), key=lambda b: b["start_minutes"])

        # Compute end times from next show's start
        for i, bc in enumerate(unique_broadcasts):
            if i + 1 < len(unique_broadcasts):
                end_minutes = unique_broadcasts[i + 1]["start_minutes"]
            else:
                end_minutes = unique_broadcasts[0]["start_minutes"] if unique_broadcasts else 1439
                if end_minutes <= bc["start_minutes"]:
                    end_minutes = 1439  # midnight

            end_h, end_m = divmod(end_minutes, 60)
            start_h, start_m = divmod(bc["start_minutes"], 60)
            genre, raw_genre = normalize_genre(bc["program_tags"])
            host_names = bc["host_names"]

            day_name = DAYS[weekday]
            schedule[day_name].append(
                ShowSlot(
                    title=bc["program_name"],
                    host=", ".join(host_names) if host_names else "Unknown Host",
                    start_time=f"{start_h:02d}:{start_m:02d}",
                    end_time=f"{end_h:02d}:{end_m:02d}",
                    day_of_week=weekday,
                    genre=genre,
                    raw_genre=raw_genre,
                    description=bc.get("tagline"),
                    image_url=bc.get("program_image_uri"),
                )
            )

    has_data = any(schedule[d] for d in DAYS)
    return StationSchedule(
        station_id=station["id"],
        station_name=station.get("name", "KEXP"),
        timezone_name=tz_name,
        source_tier="tier1_api",
        confidence=0.95 if has_data else 0.55,
        schedule=schedule,
        last_success=now_utc_iso(),
        errors=errors,
    )
