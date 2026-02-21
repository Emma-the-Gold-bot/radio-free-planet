from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Any

from .contracts import DAYS, StationSchedule, ShowSlot


def _to_minutes(hhmm: str) -> int:
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


def _slot_matches_local_time(slot: ShowSlot, local_minutes: int) -> bool:
    start = _to_minutes(slot.start_time)
    end = _to_minutes(slot.end_time)

    if start == end:
        return True
    if end > start:
        return start <= local_minutes < end
    return local_minutes >= start or local_minutes < end


def resolve_now_playing_for_station(
    station_schedule: StationSchedule,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    now_utc = now_utc or datetime.now(timezone.utc)
    zone = ZoneInfo(station_schedule.timezone_name)
    local_now = now_utc.astimezone(zone)
    day_key = DAYS[local_now.weekday()]
    local_minutes = local_now.hour * 60 + local_now.minute
    slots = station_schedule.schedule.get(day_key, [])

    matched = None
    for slot in slots:
        if _slot_matches_local_time(slot, local_minutes):
            matched = slot
            break

    payload: dict[str, Any] = {
        "station_id": station_schedule.station_id,
        "station_name": station_schedule.station_name,
        "timezone": station_schedule.timezone_name,
        "resolved_at": now_utc.isoformat(),
        "derived_from_schedule": True,
        "source_tier": station_schedule.source_tier,
        "confidence": station_schedule.confidence,
        "show": None,
    }

    if matched:
        payload["show"] = matched.to_dict()
        payload["show_title"] = matched.title
        payload["host"] = matched.host
        payload["genre"] = matched.genre
        payload["raw_genre"] = matched.raw_genre
        payload["start_time"] = matched.start_time
        payload["end_time"] = matched.end_time
    return payload


def build_now_playing(schedules: list[StationSchedule], now_utc: datetime | None = None) -> dict[str, Any]:
    now_utc = now_utc or datetime.now(timezone.utc)
    entries = [resolve_now_playing_for_station(sched, now_utc=now_utc) for sched in schedules]
    return {
        "timestamp": now_utc.isoformat(),
        "count": len(entries),
        "now_playing": entries,
    }

