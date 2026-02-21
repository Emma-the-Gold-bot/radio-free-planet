from pathlib import Path
from datetime import datetime, timezone
from typing import Any
import json

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from station_registry import StationRegistry
from stream_proxy import create_router as create_proxy_router
from schedule_refresh import run_refresh_once


PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
STATIONS_PATH = PROJECT_ROOT / "static" / "data" / "stations.json"
NOW_PLAYING_PATH = PROJECT_ROOT / "static" / "data" / "now_playing.json"

registry = StationRegistry(STATIONS_PATH)

app = FastAPI(title="Radio Agnostic", version="0.7.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(create_proxy_router(registry), prefix="/api/proxy")


def parse_show_payload(item: dict[str, Any]) -> dict[str, Any] | None:
    show = item.get("show")
    if isinstance(show, dict):
        return show

    title = item.get("show_title")
    if not title:
        return None
    genre = item.get("genre")
    normalized_genres = [genre] if isinstance(genre, str) and genre else []
    return {
        "title": title,
        "host": item.get("host") or "Unknown Host",
        "start_time": item.get("start_time"),
        "end_time": item.get("end_time"),
        "genre": genre,
        "genres": normalized_genres,
        "raw_genre": item.get("raw_genre"),
    }


@app.get("/api/stations")
async def get_stations() -> list[dict[str, Any]]:
    return registry.list_stations()


@app.get("/api/stations/{station_id}")
async def get_station(station_id: str) -> dict[str, Any]:
    station = registry.get_station(station_id)
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")
    return station


@app.get("/api/genres")
async def get_genres() -> list[str]:
    return registry.list_genres()


@app.get("/api/now-playing")
async def get_now_playing(
    genre: str | None = None,
    station_id: str | None = Query(default=None),
    limit: int = 200,
) -> list[dict[str, Any]]:
    if not NOW_PLAYING_PATH.exists():
        return []
    if station_id and not registry.is_known_station(station_id):
        return []

    data = json.loads(NOW_PLAYING_PATH.read_text(encoding="utf-8"))
    entries = data if isinstance(data, list) else data.get("now_playing", [])

    results = []
    for item in entries:
        item_station_id = item.get("station_id")
        if station_id and item_station_id != station_id:
            continue

        station = registry.get_station(item_station_id) if item_station_id else None
        if not station:
            continue
        if station.get("health_status") == "bad":
            continue

        show = parse_show_payload(item) or {}
        show_genres = show.get("genres") or ([show.get("genre")] if show.get("genre") else [])
        if genre and genre.lower() not in [g.lower() for g in show_genres if isinstance(g, str)]:
            continue

        results.append(
            {
                "station": station,
                "show": show,
                "started_at": item.get("started_at") or item.get("resolved_at"),
                "derived_from_schedule": item.get("derived_from_schedule", False),
            }
        )

    return results[:limit]


@app.post("/api/admin/reload-stations")
async def reload_stations() -> dict[str, Any]:
    registry.reload()
    return {"status": "ok", "version": registry.version, "stations": len(registry.list_stations())}


@app.post("/api/admin/refresh-schedules")
async def refresh_schedules(dry_run: bool = False) -> dict[str, Any]:
    summary = await run_refresh_once(dry_run=dry_run)
    return {"status": "ok", **summary}


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    return {
        "status": "healthy",
        "stations_count": len(registry.list_stations()),
        "stations_version": registry.version,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
