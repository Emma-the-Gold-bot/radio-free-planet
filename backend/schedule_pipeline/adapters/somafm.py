"""SomaFM — Tier 1 API adapter using somafm.com/channels.json.

SomaFM channels are continuous-format (no discrete show schedule). We pull
channel metadata (genre, description, listeners, DJ) and create a single
all-day slot per day with accurate genre information.
"""

from __future__ import annotations

from typing import Any

import httpx

from ..contracts import DAYS, ShowSlot, StationSchedule, empty_week_schedule, now_utc_iso
from ..genres import normalize_genre


SOMAFM_CHANNELS_URL = "https://somafm.com/channels.json"

# Maps our station_id suffix to the SomaFM channel id
CHANNEL_MAP: dict[str, str] = {
    "somafm-groove": "groovesalad",
    "somafm-drone": "dronezone",
    "somafm-defcon": "defcon",
    "somafm-deepspace": "deepspaceone",
    "somafm-underground": "u80s",
    "somafm-lush": "lush",
    "somafm-folkfwd": "folkfwd",
    "somafm-covers": "covers",
    "somafm-indie": "indiepop",
    "somafm-metal": "metal",
    "somafm-fluid": "fluid",
    "somafm-cliqhop": "cliqhop",
    "somafm-dubstep": "dubstep",
    "somafm-bagel": "bagel",
    "somafm-bootliquor": "bootliquor",
    "somafm-seventies": "seventies",
    "somafm-secretagent": "secretagent",
    "somafm-sonic": "sonicuniverse",
    "somafm-suburbs": "suburbsofgoa",
    "somafm-thistle": "thistle",
    "somafm-brfm": "brfm",
}


async def fetch(station: dict[str, Any]) -> StationSchedule:
    errors: list[str] = []
    station_id = station["id"]
    channel_key = CHANNEL_MAP.get(station_id, station_id.replace("somafm-", ""))

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(SOMAFM_CHANNELS_URL)
        resp.raise_for_status()
        data = resp.json()

    channel_info = None
    for ch in data.get("channels", []):
        if ch.get("id") == channel_key:
            channel_info = ch
            break

    if not channel_info:
        errors.append(f"somafm_channel_not_found:{channel_key}")
        return StationSchedule(
            station_id=station_id,
            station_name=station.get("name", f"SomaFM {channel_key}"),
            timezone_name="America/Los_Angeles",
            source_tier="tier1_api",
            confidence=0.40,
            schedule=empty_week_schedule(),
            last_success=now_utc_iso(),
            errors=errors,
        )

    raw_genre = channel_info.get("genre", "eclectic")
    genre, raw = normalize_genre(raw_genre.split("|")[0].strip() if "|" in raw_genre else raw_genre)
    title = channel_info.get("title", channel_key.title())
    description = channel_info.get("description")
    dj = channel_info.get("dj", "SomaFM")
    image = channel_info.get("xlimage") or channel_info.get("image")

    schedule = empty_week_schedule()
    for day_index, day_name in enumerate(DAYS):
        schedule[day_name].append(
            ShowSlot(
                title=title,
                host=dj,
                start_time="00:00",
                end_time="23:59",
                day_of_week=day_index,
                genre=genre,
                raw_genre=raw,
                description=description,
                image_url=image,
            )
        )

    return StationSchedule(
        station_id=station_id,
        station_name=station.get("name", f"SomaFM - {title}"),
        timezone_name="America/Los_Angeles",
        source_tier="tier1_api",
        confidence=0.85,
        schedule=schedule,
        last_success=now_utc_iso(),
        errors=errors,
    )
