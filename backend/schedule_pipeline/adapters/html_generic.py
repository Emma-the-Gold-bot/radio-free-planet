"""Generic HTML schedule scraper — Tier 2.

Configurable per-station via schedule_sources.json rules. Supports common
schedule page patterns used by community and college radio stations.

Configuration in schedule_sources.json:
{
    "station_id": {
        "tier": "tier2_html",
        "adapter": "html_generic",
        "schedule_url": "https://station.example.com/schedule",
        "selectors": {
            "day_block": ".schedule-day",
            "show_block": ".show-entry",
            "title": ".show-title",
            "host": ".show-host",
            "time": ".show-time"
        },
        "time_format": "12h"
    }
}
"""

from __future__ import annotations

import re
from typing import Any

import httpx
from bs4 import BeautifulSoup, Tag

from ..contracts import DAYS, ShowSlot, StationSchedule, empty_week_schedule, now_utc_iso
from ..genres import normalize_genre


_DAY_PATTERNS: dict[str, list[str]] = {
    "monday": ["monday", "mon", "lundi", "lunes"],
    "tuesday": ["tuesday", "tue", "tues", "mardi", "martes"],
    "wednesday": ["wednesday", "wed", "mercredi", "miércoles", "miercoles"],
    "thursday": ["thursday", "thu", "thur", "thurs", "jeudi", "jueves"],
    "friday": ["friday", "fri", "vendredi", "viernes"],
    "saturday": ["saturday", "sat", "samedi", "sábado", "sabado"],
    "sunday": ["sunday", "sun", "dimanche", "domingo"],
}


def _detect_day(text: str) -> str | None:
    lowered = text.lower().strip()
    for day, patterns in _DAY_PATTERNS.items():
        for pattern in patterns:
            if pattern in lowered:
                return day
    return None


def _parse_time_12h(raw: str) -> str | None:
    match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm|a\.m\.|p\.m\.)", raw, re.IGNORECASE)
    if not match:
        return None
    h = int(match.group(1))
    m = int(match.group(2) or "0")
    period = match.group(3).lower().replace(".", "")
    if period == "pm" and h != 12:
        h += 12
    if period == "am" and h == 12:
        h = 0
    return f"{h:02d}:{m:02d}"


def _parse_time_24h(raw: str) -> str | None:
    match = re.search(r"(\d{1,2}):(\d{2})", raw)
    if not match:
        return None
    h, m = int(match.group(1)), int(match.group(2))
    if 0 <= h <= 23 and 0 <= m <= 59:
        return f"{h:02d}:{m:02d}"
    return None


def _extract_time_range(text: str, time_format: str = "12h") -> tuple[str, str] | None:
    if time_format == "24h":
        times = re.findall(r"\d{1,2}:\d{2}", text)
        if len(times) >= 2:
            t1 = _parse_time_24h(times[0])
            t2 = _parse_time_24h(times[1])
            if t1 and t2:
                return t1, t2
    else:
        match = re.search(
            r"(\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.))"
            r"\s*[-–—to]+\s*"
            r"(\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.))",
            text,
            re.IGNORECASE,
        )
        if match:
            t1 = _parse_time_12h(match.group(1))
            t2 = _parse_time_12h(match.group(2))
            if t1 and t2:
                return t1, t2
    return None


def _select_text(element: Tag, selector: str | None) -> str:
    if not selector:
        return ""
    found = element.select_one(selector)
    return found.get_text(strip=True) if found else ""


async def fetch(
    station: dict[str, Any],
    rules: dict[str, Any] | None = None,
) -> StationSchedule:
    rules = rules or {}
    errors: list[str] = []
    schedule = empty_week_schedule()
    station_id = station["id"]
    tz_name = station.get("timezone", "UTC")

    schedule_url = rules.get("schedule_url")
    if not schedule_url:
        website = station.get("website", "")
        schedule_url = f"{website.rstrip('/')}/schedule" if website else None

    if not schedule_url:
        errors.append("no_schedule_url_configured")
        return StationSchedule(
            station_id=station_id,
            station_name=station.get("name", station_id),
            timezone_name=tz_name,
            source_tier="tier2_html",
            confidence=0.0,
            schedule=schedule,
            last_success=now_utc_iso(),
            errors=errors,
        )

    selectors = rules.get("selectors", {})
    time_format = rules.get("time_format", "12h")
    default_genre = rules.get("default_genre", station.get("genres", ["eclectic"])[0] if station.get("genres") else "eclectic")

    try:
        async with httpx.AsyncClient(timeout=25.0, follow_redirects=True) as client:
            resp = await client.get(schedule_url, headers={"User-Agent": "RadioAgnostic/1.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as exc:
        errors.append(f"html_fetch_error:{exc}")
        return StationSchedule(
            station_id=station_id,
            station_name=station.get("name", station_id),
            timezone_name=tz_name,
            source_tier="tier2_html",
            confidence=0.0,
            schedule=schedule,
            last_success=now_utc_iso(),
            errors=errors,
        )

    if selectors.get("day_block") and selectors.get("show_block"):
        _parse_structured(soup, schedule, selectors, time_format, default_genre, errors)
    else:
        _parse_heuristic(soup, schedule, time_format, default_genre, errors)

    for day in DAYS:
        schedule[day].sort(key=lambda s: s.start_time)

    has_data = any(schedule[d] for d in DAYS)
    if not has_data:
        errors.append("html_parse_empty")

    return StationSchedule(
        station_id=station_id,
        station_name=station.get("name", station_id),
        timezone_name=tz_name,
        source_tier="tier2_html",
        confidence=0.70 if has_data else 0.20,
        schedule=schedule,
        last_success=now_utc_iso(),
        errors=errors,
    )


def _parse_structured(
    soup: BeautifulSoup,
    schedule: dict[str, list[ShowSlot]],
    selectors: dict[str, str],
    time_format: str,
    default_genre: str,
    errors: list[str],
) -> None:
    day_blocks = soup.select(selectors["day_block"])
    for day_block in day_blocks:
        day_text = day_block.get_text(" ", strip=True)[:100]
        day = _detect_day(day_text)
        if not day:
            heading = day_block.find(["h2", "h3", "h4", "th", "dt"])
            if heading:
                day = _detect_day(heading.get_text(strip=True))
        if not day:
            continue

        show_blocks = day_block.select(selectors["show_block"])
        for show_el in show_blocks:
            full_text = show_el.get_text(" ", strip=True)
            title = _select_text(show_el, selectors.get("title")) or full_text[:80]
            host = _select_text(show_el, selectors.get("host")) or "Unknown Host"
            time_text = _select_text(show_el, selectors.get("time")) or full_text
            time_range = _extract_time_range(time_text, time_format)
            if not time_range:
                continue

            genre_text = _select_text(show_el, selectors.get("genre"))
            genre, raw_genre = normalize_genre(genre_text or default_genre)

            schedule[day].append(
                ShowSlot(
                    title=title,
                    host=host,
                    start_time=time_range[0],
                    end_time=time_range[1],
                    day_of_week=DAYS.index(day),
                    genre=genre,
                    raw_genre=raw_genre,
                )
            )


def _parse_heuristic(
    soup: BeautifulSoup,
    schedule: dict[str, list[ShowSlot]],
    time_format: str,
    default_genre: str,
    errors: list[str],
) -> None:
    """Fallback: walk all text-bearing elements and try to extract schedule data."""
    current_day: str | None = None

    for el in soup.find_all(["h1", "h2", "h3", "h4", "h5", "tr", "div", "li", "dt", "dd", "p", "td"]):
        text = el.get_text(" ", strip=True)
        if not text or len(text) < 3:
            continue

        detected_day = _detect_day(text)
        if detected_day and len(text) < 30:
            current_day = detected_day
            continue

        time_range = _extract_time_range(text, time_format)
        if not time_range:
            continue

        day = detected_day or current_day
        if not day:
            continue

        title_text = re.sub(
            r"\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)\s*[-–—to]+\s*"
            r"\d{1,2}(?::\d{2})?\s*(?:am|pm|a\.m\.|p\.m\.)",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()
        title_text = re.sub(r"\d{1,2}:\d{2}\s*[-–—]\s*\d{1,2}:\d{2}", "", title_text).strip()
        title_text = title_text.strip(" -–—|:").strip()

        if not title_text or len(title_text) < 2:
            title_text = "Programming"

        genre, raw_genre = normalize_genre(default_genre)
        schedule[day].append(
            ShowSlot(
                title=title_text[:120],
                host="Unknown Host",
                start_time=time_range[0],
                end_time=time_range[1],
                day_of_week=DAYS.index(day),
                genre=genre,
                raw_genre=raw_genre,
            )
        )
