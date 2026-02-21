"""Continuous-format station adapter — Tier 2 (enriched seed).

For stations that broadcast a single format 24/7 without discrete show blocks
(Radio Paradise, dublab, Hirschmilch, etc.). Pulls genre/metadata from
station registry and creates all-day slots with accurate genre tagging.
"""

from __future__ import annotations

from typing import Any

from ..contracts import DAYS, ShowSlot, StationSchedule, empty_week_schedule, now_utc_iso
from ..genres import normalize_genre


async def fetch(station: dict[str, Any], rules: dict[str, Any] | None = None) -> StationSchedule:
    rules = rules or {}
    station_id = station["id"]
    tz_name = station.get("timezone", "UTC")
    station_genres = station.get("genres", [])

    title = rules.get("program_title", station.get("name", "Live Programming"))
    host = rules.get("host", "Various DJs")
    default_genre_raw = rules.get("genre") or (station_genres[0] if station_genres else "eclectic")
    genre, raw = normalize_genre(default_genre_raw)
    description = rules.get("description")

    schedule = empty_week_schedule()
    for day_index, day_name in enumerate(DAYS):
        schedule[day_name].append(
            ShowSlot(
                title=title,
                host=host,
                start_time="00:00",
                end_time="23:59",
                day_of_week=day_index,
                genre=genre,
                raw_genre=raw,
                description=description,
            )
        )

    return StationSchedule(
        station_id=station_id,
        station_name=station.get("name", station_id),
        timezone_name=tz_name,
        source_tier="tier2_enriched",
        confidence=float(rules.get("confidence", 0.65)),
        schedule=schedule,
        last_success=now_utc_iso(),
        errors=[],
    )
