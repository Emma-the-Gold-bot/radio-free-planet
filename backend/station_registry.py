from __future__ import annotations

from pathlib import Path
from typing import Any
import json


class StationRegistry:
    """Loads station metadata from the shared static dataset."""

    def __init__(self, stations_path: Path):
        self.stations_path = stations_path
        self._stations_by_id: dict[str, dict[str, Any]] = {}
        self._version = "unknown"
        self.reload()

    @property
    def version(self) -> str:
        return self._version

    def reload(self) -> None:
        raw = json.loads(self.stations_path.read_text(encoding="utf-8"))
        self._version = str(raw.get("version", "unknown"))
        self._stations_by_id = {}

        for station in raw.get("stations", []):
            normalized = self._normalize_station(station)
            self._stations_by_id[normalized["id"]] = normalized

    def list_stations(self) -> list[dict[str, Any]]:
        return list(self._stations_by_id.values())

    def get_station(self, station_id: str) -> dict[str, Any] | None:
        return self._stations_by_id.get(station_id)

    def list_genres(self) -> list[str]:
        genres: set[str] = set()
        for station in self._stations_by_id.values():
            genres.update(station.get("genres", []))
        return sorted(genres)

    def resolve_stream_candidates(self, station_id: str, stream_index: int | None = None) -> list[dict[str, Any]]:
        station = self.get_station(station_id)
        if not station:
            return []

        streams = station.get("streams", [])
        if not streams:
            return []

        if stream_index is not None:
            if 0 <= stream_index < len(streams):
                return [streams[stream_index]]
            return []

        return streams

    def is_allowed_stream(self, station_id: str, stream_url: str) -> bool:
        station = self.get_station(station_id)
        if not station:
            return False
        return any(stream.get("url") == stream_url for stream in station.get("streams", []))

    def _normalize_station(self, station: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(station)

        normalized.setdefault("callsign", normalized.get("name", "Unknown Station"))
        normalized.setdefault("cors_status", "unknown")
        normalized["playback_mode"] = normalized.get(
            "playback_mode",
            "direct_then_proxy" if normalized.get("cors_status") == "open" else "proxy_required",
        )

        streams = [dict(s) for s in normalized.get("streams", [])]
        streams.sort(key=lambda s: (s.get("priority", 9999), 0 if s.get("is_primary") else 1))

        for idx, stream in enumerate(streams):
            stream.setdefault("priority", idx)
            stream.setdefault("is_primary", idx == 0)
            stream.setdefault("quality", "unknown")
            stream.setdefault("format", "unknown")

        normalized["streams"] = streams
        return normalized
