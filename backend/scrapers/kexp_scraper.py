"""
KEXP API Scraper
KEXP has a well-documented API - this is the easy one
"""
from fastapi import APIRouter, HTTPException
import httpx
from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel

router = APIRouter()

KEXP_API_BASE = "https://api.kexp.org/v2"

class KEXPShow(BaseModel):
    id: int
    name: str
    host: str
    start_time: str
    end_time: str
    image_uri: str = None

@router.get("/now-playing")
async def kexp_now_playing():
    """Get KEXP's current show and track"""
    async with httpx.AsyncClient() as client:
        # Get current show
        show_resp = await client.get(f"{KEXP_API_BASE}/shows/?limit=1&is_current=true")
        show_data = show_resp.json()
        
        # Get current track
        play_resp = await client.get(f"{KEXP_API_BASE}/plays/?limit=1")
        play_data = play_resp.json()
        
        return {
            "station_id": "kexp",
            "show": show_data.get("results", [{}])[0] if show_data.get("results") else None,
            "current_track": play_data.get("results", [{}])[0] if play_data.get("results") else None
        }

@router.get("/schedule/today")
async def kexp_schedule_today():
    """Get KEXP's schedule for today"""
    async with httpx.AsyncClient() as client:
        today = datetime.now().strftime("%Y-%m-%d")
        resp = await client.get(
            f"{KEXP_API_BASE}/shows/",
            params={
                "start_time_with_tz": today,
                "limit": 50
            }
        )
        data = resp.json()
        return {
            "station_id": "kexp",
            "date": today,
            "shows": data.get("results", [])
        }

@router.get("/schedule/week")
async def kexp_schedule_week():
    """Get KEXP's schedule for the week"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{KEXP_API_BASE}/shows/",
            params={"limit": 200}
        )
        data = resp.json()
        return {
            "station_id": "kexp",
            "shows": data.get("results", [])
        }

@router.post("/refresh")
async def refresh_kexp_data():
    """Manually trigger a refresh of KEXP data"""
    try:
        # Get today's schedule
        async with httpx.AsyncClient() as client:
            today = datetime.now().strftime("%Y-%m-%d")
            resp = await client.get(
                f"{KEXP_API_BASE}/shows/",
                params={"limit": 200}
            )
            data = resp.json()
            
            shows = data.get("results", [])
            
            return {
                "status": "success",
                "message": f"Refreshed {len(shows)} shows",
                "shows_count": len(shows)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
