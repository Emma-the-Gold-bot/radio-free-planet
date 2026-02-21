"""Tier 3 seed adapter — fallback for stations without known schedule sources.

Creates a generic all-day placeholder schedule using whatever genre metadata
is available from the station registry.
"""

from __future__ import annotations

from typing import Any

from ..contracts import DAYS, ShowSlot, StationSchedule, empty_week_schedule, now_utc_iso
from ..genres import normalize_genre


async def fetch(station: dict[str, Any], **_: Any) -> StationSchedule:
    station_id = station["id"]
    tz_name = station.get("timezone", "UTC")
    station_genres = station.get("genres", [])

    genre = "variety"
    raw = "various"
    if station_genres:
        genre, raw = normalize_genre(str(station_genres[0]))

    schedule = empty_week_schedule()
    for day_index, day_name in enumerate(DAYS):
        schedule[day_name].append(
            ShowSlot(
                title="Live Programming",
                host="Various DJs",
                start_time="00:00",
                end_time="23:59",
                day_of_week=day_index,
                genre=genre,
                raw_genre=raw,
            )
        )

    return StationSchedule(
        station_id=station_id,
        station_name=station.get("name", station_id),
        timezone_name=tz_name,
        source_tier="tier3_seed",
        confidence=0.50,
        schedule=schedule,
        last_success=now_utc_iso(),
        errors=[],
    )
