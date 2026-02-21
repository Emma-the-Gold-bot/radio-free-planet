"""WFMU — Tier 2 HTML scraper for wfmu.org/schedule."""

from __future__ import annotations

import re
from typing import Any

import httpx
from bs4 import BeautifulSoup

from ..contracts import DAYS, ShowSlot, StationSchedule, empty_week_schedule, now_utc_iso
from ..genres import normalize_genre


WFMU_SCHEDULE_URL = "https://wfmu.org/schedule"


def _parse_time_range(value: str) -> tuple[str, str] | None:
    value = value.strip().lower()
    match = re.search(
        r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)\s*[-–]\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)",
        value,
    )
    if not match:
        return None
    h1, m1, p1 = int(match.group(1)), int(match.group(2) or "0"), match.group(3)
    h2, m2, p2 = int(match.group(4)), int(match.group(5) or "0"), match.group(6)

    if p1 == "pm" and h1 != 12:
        h1 += 12
    if p1 == "am" and h1 == 12:
        h1 = 0
    if p2 == "pm" and h2 != 12:
        h2 += 12
    if p2 == "am" and h2 == 12:
        h2 = 0
    return f"{h1:02d}:{m1:02d}", f"{h2:02d}:{m2:02d}"


async def fetch(station: dict[str, Any]) -> StationSchedule:
    errors: list[str] = []
    schedule = empty_week_schedule()

    async with httpx.AsyncClient(timeout=25.0) as client:
        resp = await client.get(WFMU_SCHEDULE_URL)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

    blocks = soup.find_all(["tr", "div", "li"])
    for block in blocks:
        text = block.get_text(" ", strip=True)
        parsed_time = _parse_time_range(text)
        if not parsed_time:
            continue

        title = block.get("data-title") or text.split("-")[0].strip()[:120]
        day_name = None
        lowered = text.lower()
        for day in DAYS:
            if day in lowered:
                day_name = day
                break
        if day_name is None:
            continue

        start_time, end_time = parsed_time
        genre, raw_genre = normalize_genre("freeform")
        schedule[day_name].append(
            ShowSlot(
                title=title or "WFMU Show",
                host="WFMU",
                start_time=start_time,
                end_time=end_time,
                day_of_week=DAYS.index(day_name),
                genre=genre,
                raw_genre=raw_genre,
            )
        )

    if not any(schedule[day] for day in DAYS):
        errors.append("wfmu_schedule_parse_empty")

    for day in DAYS:
        schedule[day].sort(key=lambda s: s.start_time)

    has_data = any(schedule[d] for d in DAYS)
    return StationSchedule(
        station_id=station["id"],
        station_name=station.get("name", "WFMU"),
        timezone_name=station.get("timezone", "America/New_York"),
        source_tier="tier2_html",
        confidence=0.75 if has_data else 0.40,
        schedule=schedule,
        last_success=now_utc_iso(),
        errors=errors,
    )
