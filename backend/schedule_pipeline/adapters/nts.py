"""NTS Radio — Tier 1 API adapter using nts.live/api/v2.

NTS has two channels. The /api/v2/live endpoint returns the currently playing
show plus ~17 upcoming shows per channel, with full metadata including genres,
timestamps, and show details.
"""

from __future__ import annotations

import html
import re
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import httpx

from ..contracts import DAYS, ShowSlot, StationSchedule, empty_week_schedule, now_utc_iso
from ..genres import normalize_genre


NTS_LIVE_URL = "https://www.nts.live/api/v2/live"
NTS_TIMEZONE = "Europe/London"


def _parse_nts_genres(details: dict[str, Any]) -> tuple[str, str]:
    genres = details.get("genres", [])
    if genres:
        raw = genres[0].get("value", "eclectic")
        return normalize_genre(raw)
    moods = details.get("moods", [])
    if moods:
        return normalize_genre(moods[0].get("value", "eclectic"))
    return normalize_genre("eclectic")


def _clean_title(raw_title: str) -> str:
    cleaned = html.unescape(raw_title)
    cleaned = re.sub(r"\s*\(R\)\s*$", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip()


def _extract_host(details: dict[str, Any], broadcast_title: str) -> str:
    name = details.get("name", "")
    if " w/ " in broadcast_title.lower():
        parts = broadcast_title.split(" w/ ", 1)
        if len(parts) == 2:
            return parts[1].strip() or name or "NTS"
    if " W/ " in broadcast_title:
        parts = broadcast_title.split(" W/ ", 1)
        if len(parts) == 2:
            return parts[1].strip() or name or "NTS"
    return name or "NTS"


def _parse_broadcast(
    broadcast: dict[str, Any],
    tz: ZoneInfo,
) -> ShowSlot | None:
    title_raw = broadcast.get("broadcast_title", "")
    start_ts = broadcast.get("start_timestamp")
    end_ts = broadcast.get("end_timestamp")
    if not title_raw or not start_ts or not end_ts:
        return None

    try:
        start_dt = datetime.fromisoformat(start_ts.replace("Z", "+00:00")).astimezone(tz)
        end_dt = datetime.fromisoformat(end_ts.replace("Z", "+00:00")).astimezone(tz)
    except (ValueError, TypeError):
        return None

    title = _clean_title(title_raw)
    details = broadcast.get("embeds", {}).get("details", {})
    genre, raw_genre = _parse_nts_genres(details)
    host = _extract_host(details, title_raw)
    image = None
    media = details.get("media", {})
    if isinstance(media, dict):
        image = media.get("picture_large") or media.get("background_large")

    return ShowSlot(
        title=title,
        host=host,
        start_time=start_dt.strftime("%H:%M"),
        end_time=end_dt.strftime("%H:%M"),
        day_of_week=start_dt.weekday(),
        genre=genre,
        raw_genre=raw_genre,
        description=details.get("description"),
        image_url=image,
    )


async def fetch(station: dict[str, Any]) -> StationSchedule:
    """Fetch schedule for an NTS channel (1 or 2)."""
    errors: list[str] = []
    schedule = empty_week_schedule()
    tz_name = station.get("timezone", NTS_TIMEZONE)
    tz = ZoneInfo(tz_name)

    station_id = station["id"]
    # Map station_id to NTS channel index: nts-1 / nts-radio-1 -> 0, nts-2 / nts-radio-2 -> 1
    channel_idx = 0
    if any(x in station_id for x in ("nts-2", "nts-radio-2")):
        channel_idx = 1

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(NTS_LIVE_URL)
        resp.raise_for_status()
        data = resp.json()

    channels = data.get("results", [])
    if channel_idx >= len(channels):
        errors.append(f"nts_channel_{channel_idx}_not_found")
        return _fallback(station, tz_name, errors)

    channel = channels[channel_idx]

    # "now" is the current broadcast
    now_broadcast = channel.get("now")
    if now_broadcast:
        slot = _parse_broadcast(now_broadcast, tz)
        if slot:
            day_name = DAYS[slot.day_of_week]
            schedule[day_name].append(slot)

    # "next", "next2" ... "next17" are upcoming
    for i in range(1, 20):
        key = "next" if i == 1 else f"next{i}"
        broadcast = channel.get(key)
        if not broadcast:
            continue
        slot = _parse_broadcast(broadcast, tz)
        if slot:
            day_name = DAYS[slot.day_of_week]
            # Deduplicate by time range
            existing = {(s.start_time, s.end_time) for s in schedule[day_name]}
            if (slot.start_time, slot.end_time) not in existing:
                schedule[day_name].append(slot)

    for day in DAYS:
        schedule[day].sort(key=lambda s: s.start_time)

    has_data = any(schedule[d] for d in DAYS)
    return StationSchedule(
        station_id=station_id,
        station_name=station.get("name", f"NTS Radio {channel_idx + 1}"),
        timezone_name=tz_name,
        source_tier="tier1_api",
        confidence=0.90 if has_data else 0.50,
        schedule=schedule,
        last_success=now_utc_iso(),
        errors=errors,
    )


def _fallback(
    station: dict[str, Any], tz_name: str, errors: list[str]
) -> StationSchedule:
    return StationSchedule(
        station_id=station["id"],
        station_name=station.get("name", "NTS Radio"),
        timezone_name=tz_name,
        source_tier="tier1_api",
        confidence=0.30,
        schedule=empty_week_schedule(),
        last_success=now_utc_iso(),
        errors=errors,
    )
