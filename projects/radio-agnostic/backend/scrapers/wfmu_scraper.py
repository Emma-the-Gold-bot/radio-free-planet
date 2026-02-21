"""
WFMU Scraper
WFMU doesn't have a public API, so we scrape their schedule pages
This is more fragile but necessary for the weird wonderful world of WFMU
"""
from fastapi import APIRouter, HTTPException
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Optional
import re

router = APIRouter()

WFMU_BASE = "https://wfmu.org"

# WFMU genre mappings - they use freeform categories
WFMU_GENRE_MAP = {
    "rock": ["rock", "indie", "punk", "garage", "post-punk"],
    "experimental": ["noise", "experimental", "avant-garde", "electronic"],
    "soul": ["soul", "r&b", "funk"],
    "jazz": ["jazz", "free jazz", "bebop"],
    "world": ["world", "international", "african", "latin"],
    "talk": ["talk", "interviews", "spoken word"]
}

async def fetch_wfmu_schedule():
    """Fetch and parse WFMU's schedule page"""
    async with httpx.AsyncClient() as client:
        # WFMU schedule page
        resp = await client.get(f"{WFMU_BASE}/schedule", timeout=30.0)
        resp.raise_for_status()
        return resp.text

def parse_wfmu_schedule(html: str) -> List[dict]:
    """Parse WFMU schedule HTML"""
    soup = BeautifulSoup(html, 'html.parser')
    shows = []
    
    # WFMU's schedule is in a table or list format
    # This is a simplified parser - you'll need to inspect the actual HTML structure
    schedule_table = soup.find('table', class_='schedule') or soup.find('div', class_='schedule')
    
    if schedule_table:
        rows = schedule_table.find_all(['tr', 'div'], class_=re.compile('show|program'))
        
        for row in rows:
            try:
                # Extract show info - adjust selectors based on actual HTML
                time_elem = row.find(['td', 'span', 'div'], class_=re.compile('time|hour'))
                name_elem = row.find(['td', 'a', 'span'], class_=re.compile('name|title|program'))
                host_elem = row.find(['td', 'span'], class_=re.compile('host|dj'))
                desc_elem = row.find(['td', 'div'], class_=re.compile('desc|description'))
                
                show = {
                    "name": name_elem.get_text(strip=True) if name_elem else "Unknown",
                    "host": host_elem.get_text(strip=True) if host_elem else None,
                    "time": time_elem.get_text(strip=True) if time_elem else None,
                    "description": desc_elem.get_text(strip=True) if desc_elem else None,
                    "url": name_elem.get('href') if name_elem and name_elem.name == 'a' else None
                }
                
                # Infer genres from description
                show["genres"] = infer_genres(show.get("description", ""))
                
                shows.append(show)
            except Exception as e:
                print(f"Error parsing row: {e}")
                continue
    
    return shows

def infer_genres(description: str) -> List[str]:
    """Infer genres from show description"""
    desc_lower = description.lower()
    genres = []
    
    for genre, keywords in WFMU_GENRE_MAP.items():
        if any(keyword in desc_lower for keyword in keywords):
            genres.append(genre)
    
    return genres if genres else ["freeform"]

@router.get("/schedule")
async def wfmu_schedule():
    """Get WFMU's schedule (scraped)"""
    try:
        html = await fetch_wfmu_schedule()
        shows = parse_wfmu_schedule(html)
        
        return {
            "station_id": "wfmu",
            "scraped_at": datetime.now().isoformat(),
            "shows": shows,
            "count": len(shows)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to scrape WFMU: {str(e)}")

@router.get("/now-playing")
async def wfmu_now_playing():
    """Get WFMU's current show (from scraped schedule)"""
    try:
        html = await fetch_wfmu_schedule()
        shows = parse_wfmu_schedule(html)
        
        # Find current show based on time
        now = datetime.now()
        current_hour = now.hour
        
        current_show = None
        for show in shows:
            show_time = show.get("time", "")
            if show_time:
                try:
                    # Parse time like "9:00 AM" or "14:00"
                    hour = parse_hour(show_time)
                    if hour == current_hour:
                        current_show = show
                        break
                except:
                    continue
        
        return {
            "station_id": "wfmu",
            "show": current_show,
            "scraped_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get WFMU now playing: {str(e)}")

def parse_hour(time_str: str) -> int:
    """Parse hour from time string"""
    # Handle formats like "9:00 AM", "2:00 PM", "14:00"
    time_str = time_str.strip().lower()
    
    # Remove minutes if present
    time_str = re.sub(r':\d+', '', time_str)
    
    # Handle AM/PM
    is_pm = 'pm' in time_str
    is_am = 'am' in time_str
    
    # Extract number
    match = re.search(r'(\d+)', time_str)
    if not match:
        raise ValueError(f"Cannot parse hour from: {time_str}")
    
    hour = int(match.group(1))
    
    if is_pm and hour != 12:
        hour += 12
    elif is_am and hour == 12:
        hour = 0
    
    return hour

@router.post("/refresh")
async def refresh_wfmu_data():
    """Manually trigger a refresh of WFMU data"""
    try:
        html = await fetch_wfmu_schedule()
        shows = parse_wfmu_schedule(html)
        
        return {
            "status": "success",
            "message": f"Scraped {len(shows)} shows from WFMU",
            "shows_count": len(shows),
            "scraped_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
