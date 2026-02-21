from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


@dataclass(slots=True)
class ShowSlot:
    title: str
    host: str
    start_time: str
    end_time: str
    day_of_week: int
    genre: str
    raw_genre: str | None = None
    description: str | None = None
    image_url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "host": self.host,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "day_of_week": self.day_of_week,
            "genre": self.genre,
            "raw_genre": self.raw_genre,
            "description": self.description,
            "image_url": self.image_url,
        }


@dataclass(slots=True)
class StationSchedule:
    station_id: str
    station_name: str
    timezone_name: str
    source_tier: str
    confidence: float
    schedule: dict[str, list[ShowSlot]]
    last_success: str
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "station_id": self.station_id,
            "station_name": self.station_name,
            "timezone": self.timezone_name,
            "source_tier": self.source_tier,
            "confidence": self.confidence,
            "last_updated": self.last_success,
            "errors": self.errors,
            "schedule": {
                day: [slot.to_dict() for slot in self.schedule.get(day, [])]
                for day in DAYS
            },
        }


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def empty_week_schedule() -> dict[str, list[ShowSlot]]:
    return {day: [] for day in DAYS}

