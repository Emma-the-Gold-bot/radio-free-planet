"""FIP (Radio France) — Tier 1 API adapter using fip-metadata.fly.dev.

FIP is a continuous-format station (no discrete show blocks in the traditional
sense). The metadata API provides current and next track information. We model
this as all-day programming slots with FIP's signature eclectic genre.
"""

from __future__ import annotations

from typing import Any

import httpx

from ..contracts import DAYS, ShowSlot, StationSchedule, empty_week_schedule, now_utc_iso
from ..genres import normalize_genre


FIP_METADATA_URL = "https://fip-metadata.fly.dev/api/metadata/fip"


async def fetch(station: dict[str, Any]) -> StationSchedule:
    errors: list[str] = []
    station_id = station["id"]
    tz_name = station.get("timezone", "Europe/Paris")

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(FIP_METADATA_URL)
        resp.raise_for_status()
        data = resp.json()

    station_name_api = data.get("stationName", "FIP")
    genre, raw = normalize_genre("eclectic")

    now_track = data.get("now", {})
    current_artist = ""
    current_title = ""
    if now_track:
        first_line = now_track.get("firstLine", {})
        second_line = now_track.get("secondLine", {})
        current_title = first_line.get("title", "") or ""
        current_artist = second_line.get("title", "") or ""

    description = f"Now: {current_artist} - {current_title}" if current_artist else None

    schedule = empty_week_schedule()
    for day_index, day_name in enumerate(DAYS):
        schedule[day_name].append(
            ShowSlot(
                title="FIP — Éclectisme Musical",
                host="FIP",
                start_time="00:00",
                end_time="23:59",
                day_of_week=day_index,
                genre=genre,
                raw_genre=raw,
                description=description,
                image_url=None,
            )
        )

    return StationSchedule(
        station_id=station_id,
        station_name=station.get("name", f"FIP ({station_name_api})"),
        timezone_name=tz_name,
        source_tier="tier1_api",
        confidence=0.80,
        schedule=schedule,
        last_success=now_utc_iso(),
        errors=errors,
    )
