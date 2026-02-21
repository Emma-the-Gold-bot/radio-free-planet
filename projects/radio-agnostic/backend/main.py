from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, time
import json

app = FastAPI(title="Radio Agnostic", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for MVP (replace with PostgreSQL later)
stations_db = {}
shows_db = {}
user_schedules_db = {}
now_playing_cache = {}

# Data Models
class Stream(BaseModel):
    format: str  # mp3, aac, hls
    url: str
    quality: str
    is_primary: bool = True

class Location(BaseModel):
    city: str
    state: str
    country: str
    lat: float
    lng: float

class Station(BaseModel):
    id: str
    callsign: str
    name: str
    location: Location
    streams: List[Stream]
    website: str
    timezone: str
    genres: List[str]
    data_source: str  # api, scrape, manual

class Show(BaseModel):
    id: str
    station_id: str
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: datetime
    timezone: str
    hosts: Optional[List[str]]
    genres: List[str]
    recurring: bool = True

class ScheduleSlot(BaseModel):
    day_of_week: int  # 0=Monday, 6=Sunday
    time: str  # HH:MM
    station_id: str
    show_id: Optional[str]

class UserSchedule(BaseModel):
    id: str
    name: str
    slots: List[ScheduleSlot]
    is_active: bool = True

# Seed data - KEXP
kexp = Station(
    id="kexp",
    callsign="KEXP",
    name="KEXP 90.3 FM Seattle",
    location=Location(
        city="Seattle",
        state="WA",
        country="USA",
        lat=47.6062,
        lng=-122.3321
    ),
    streams=[
        Stream(format="mp3", url="https://kexp-mp3-128.streamguys1.com/kexp128.mp3", quality="high", is_primary=True),
        Stream(format="aac", url="https://kexp-aac-128.streamguys1.com/kexp128.aac", quality="high", is_primary=False)
    ],
    website="https://kexp.org",
    timezone="America/Los_Angeles",
    genres=["indie", "alternative", "rock", "electronic"],
    data_source="api"
)
stations_db["kexp"] = kexp

# Seed data - WFMU
wfmu = Station(
    id="wfmu",
    callsign="WFMU",
    name="WFMU 91.1 FM Jersey City",
    location=Location(
        city="Jersey City",
        state="NJ",
        country="USA",
        lat=40.7282,
        lng=-74.0776
    ),
    streams=[
        Stream(format="mp3", url="https://stream0.wfmu.org/freeform-128k", quality="high", is_primary=True),
        Stream(format="mp3", url="https://stream0.wfmu.org/freeform-64k", quality="low", is_primary=False)
    ],
    website="https://wfmu.org",
    timezone="America/New_York",
    genres=["freeform", "experimental", "punk", "indie", "noise"],
    data_source="scrape"
)
stations_db["wfmu"] = wfmu

# Seed data - KALX (CORS-blocked, use proxy)
kalx = Station(
    id="kalx",
    callsign="KALX",
    name="KALX 90.7 FM Berkeley",
    location=Location(
        city="Berkeley",
        state="CA",
        country="USA",
        lat=37.8715,
        lng=-122.2730
    ),
    streams=[
        Stream(format="mp3", url="http://stream.kalx.berkeley.edu:8000/kalx-128.mp3", quality="high", is_primary=True)
    ],
    website="https://kalx.berkeley.edu",
    timezone="America/Los_Angeles",
    genres=["college", "indie", "punk", "experimental"],
    data_source="scrape"
)
stations_db["kalx"] = kalx

# Seed data - CJSW (Calgary - WORKING)
cjsw = Station(
    id="cjsw",
    callsign="CJSW",
    name="CJSW 90.9 FM Calgary",
    location=Location(
        city="Calgary",
        state="AB",
        country="Canada",
        lat=51.0447,
        lng=-114.0719
    ),
    streams=[
        Stream(format="mp3", url="https://stream.cjsw.com/cjsw.mp3", quality="high", is_primary=True)
    ],
    website="https://cjsw.com",
    timezone="America/Edmonton",
    genres=["community", "indie", "experimental", "electronic"],
    data_source="api"
)
stations_db["cjsw"] = cjsw

# Seed data - WMSE Milwaukee (WORKING)
wmse = Station(
    id="wmse",
    callsign="WMSE",
    name="WMSE 91.7 FM Milwaukee",
    location=Location(
        city="Milwaukee",
        state="WI",
        country="USA",
        lat=43.0389,
        lng=-87.9065
    ),
    streams=[
        Stream(format="mp3", url="https://wmse.streamguys1.com/wmse128mp3", quality="high", is_primary=True)
    ],
    website="https://wmse.org",
    timezone="America/Chicago",
    genres=["college", "indie", "rock", "punk"],
    data_source="api"
)
stations_db["wmse"] = wmse

# Seed data - WCBN Ann Arbor (WORKING)
wcbn = Station(
    id="wcbn",
    callsign="WCBN",
    name="WCBN 88.3 FM Ann Arbor",
    location=Location(
        city="Ann Arbor",
        state="MI",
        country="USA",
        lat=42.2808,
        lng=-83.7430
    ),
    streams=[
        Stream(format="mp3", url="http://floyd.wcbn.org:8000/wcbn-hi.mp3", quality="high", is_primary=True)
    ],
    website="https://wcbn.org",
    timezone="America/Detroit",
    genres=["freeform", "college", "experimental", "jazz"],
    data_source="api"
)
stations_db["wcbn"] = wcbn

# Seed data - WRFL Lexington (WORKING)
wrfl = Station(
    id="wrfl",
    callsign="WRFL",
    name="WRFL 88.1 FM Lexington",
    location=Location(
        city="Lexington",
        state="KY",
        country="USA",
        lat=38.0406,
        lng=-84.5037
    ),
    streams=[
        Stream(format="mp3", url="http://wrfl.fm/stream.mp3", quality="high", is_primary=True)
    ],
    website="https://wrfl.fm",
    timezone="America/New_York",
    genres=["college", "indie", "rock", "hip-hop"],
    data_source="api"
)
stations_db["wrfl"] = wrfl

# Seed data - NPR Program Stream (WORKING)
npr = Station(
    id="npr",
    callsign="NPR",
    name="NPR Program Stream",
    location=Location(
        city="Washington",
        state="DC",
        country="USA",
        lat=38.9072,
        lng=-77.0369
    ),
    streams=[
        Stream(format="mp3", url="https://npr-ice.streamguys1.com/live.mp3", quality="high", is_primary=True)
    ],
    website="https://npr.org",
    timezone="America/New_York",
    genres=["news", "talk", "public affairs"],
    data_source="api"
)
stations_db["npr"] = npr

# Seed data - WNYC 93.9 FM (CORS-blocked, use proxy)
wnyc = Station(
    id="wnyc",
    callsign="WNYC",
    name="WNYC 93.9 FM New York",
    location=Location(
        city="New York",
        state="NY",
        country="USA",
        lat=40.7128,
        lng=-74.0060
    ),
    streams=[
        Stream(format="mp3", url="https://fm939.wnyc.org/wnycfm", quality="high", is_primary=True)
    ],
    website="https://wnyc.org",
    timezone="America/New_York",
    genres=["news", "talk", "public affairs"],
    data_source="api"
)
stations_db["wnyc"] = wnyc

# Seed data - WQXR 105.9 FM (CORS-blocked, use proxy)
wqxr = Station(
    id="wqxr",
    callsign="WQXR",
    name="WQXR 105.9 FM New York",
    location=Location(
        city="New York",
        state="NY",
        country="USA",
        lat=40.7128,
        lng=-74.0060
    ),
    streams=[
        Stream(format="mp3", url="https://stream.wqxr.org/wqxr", quality="high", is_primary=True)
    ],
    website="https://wqxr.org",
    timezone="America/New_York",
    genres=["classical", "opera"],
    data_source="api"
)
stations_db["wqxr"] = wqxr

# Seed data - WQXR New Sounds (CORS-blocked, use proxy)
wqxr_newsounds = Station(
    id="wqxr-newsounds",
    callsign="WQXR-Q2",
    name="WQXR New Sounds",
    location=Location(
        city="New York",
        state="NY",
        country="USA",
        lat=40.7128,
        lng=-74.0060
    ),
    streams=[
        Stream(format="mp3", url="https://q2stream.wqxr.org/q2", quality="high", is_primary=True)
    ],
    website="https://wqxr.org/newsounds",
    timezone="America/New_York",
    genres=["experimental", "new music", "contemporary"],
    data_source="api"
)
stations_db["wqxr-newsounds"] = wqxr_newsounds

# Seed data - WQXR Operavore (CORS-blocked, use proxy)
wqxr_operavore = Station(
    id="wqxr-operavore",
    callsign="WQXR-Opera",
    name="WQXR Operavore",
    location=Location(
        city="New York",
        state="NY",
        country="USA",
        lat=40.7128,
        lng=-74.0060
    ),
    streams=[
        Stream(format="mp3", url="https://opera-stream.wqxr.org/operavore", quality="high", is_primary=True)
    ],
    website="https://wqxr.org/operavore",
    timezone="America/New_York",
    genres=["opera", "classical"],
    data_source="api"
)
stations_db["wqxr-operavore"] = wqxr_operavore

# Seed data - KUT Austin (CORS-blocked, use proxy)
kut = Station(
    id="kut",
    callsign="KUT",
    name="KUT 90.5 FM Austin",
    location=Location(
        city="Austin",
        state="TX",
        country="USA",
        lat=30.2672,
        lng=-97.7431
    ),
    streams=[
        Stream(format="mp3", url="https://streams.kut.org/4426_128.mp3?aw_0_1st.playerid=kut-free", quality="high", is_primary=True),
        Stream(format="aac", url="https://streams.kut.org/4426_56?aw_0_1st.playerid=kut-free", quality="medium", is_primary=False)
    ],
    website="https://kut.org",
    timezone="America/Chicago",
    genres=["news", "npr", "talk"],
    data_source="api"
)
stations_db["kut"] = kut

# Seed data - KUTX Austin (CORS-blocked, use proxy)
kutx = Station(
    id="kutx",
    callsign="KUTX",
    name="KUTX 98.9 FM Austin",
    location=Location(
        city="Austin",
        state="TX",
        country="USA",
        lat=30.2672,
        lng=-97.7431
    ),
    streams=[
        Stream(format="mp3", url="https://streams.kut.org/4428_192.mp3?aw_0_1st.playerid=kutx-free", quality="high", is_primary=True),
        Stream(format="aac", url="https://streams.kut.org/4428_56?aw_0_1st.playerid=kutx-free", quality="medium", is_primary=False)
    ],
    website="https://kutx.org",
    timezone="America/Chicago",
    genres=["indie", "americana", "alternative"],
    data_source="api"
)
stations_db["kutx"] = kutx

# Seed data - KZSU Stanford (CORS-blocked, use proxy)
kzsu = Station(
    id="kzsu",
    callsign="KZSU",
    name="KZSU 90.1 FM Stanford",
    location=Location(
        city="Stanford",
        state="CA",
        country="USA",
        lat=37.4241,
        lng=-122.1661
    ),
    streams=[
        Stream(format="mp3", url="http://kzsu-streams.stanford.edu/kzsu-1-128.mp3", quality="high", is_primary=True)
    ],
    website="https://kzsu.stanford.edu",
    timezone="America/Los_Angeles",
    genres=["freeform", "college", "experimental"],
    data_source="api"
)
stations_db["kzsu"] = kzsu

# Seed data - WFMU Ichiban (CORS-blocked, use proxy)
wfmu_ichiban = Station(
    id="wfmu-ichiban",
    callsign="WFMU-Ichiban",
    name="WFMU Ichiban",
    location=Location(
        city="Jersey City",
        state="NJ",
        country="USA",
        lat=40.7282,
        lng=-74.0776
    ),
    streams=[
        Stream(format="mp3", url="http://stream0.wfmu.org/ichiban", quality="high", is_primary=True)
    ],
    website="https://wfmu.org/ichiban",
    timezone="America/New_York",
    genres=["japanese", "psychedelic", "garage"],
    data_source="api"
)
stations_db["wfmu-ichiban"] = wfmu_ichiban

@app.get("/api/stations")
async def get_stations():
    """Get all stations"""
    return list(stations_db.values())

@app.get("/api/stations/{station_id}")
async def get_station(station_id: str):
    """Get a specific station"""
    if station_id not in stations_db:
        raise HTTPException(status_code=404, detail="Station not found")
    return stations_db[station_id]

@app.get("/api/now-playing")
async def get_now_playing(genre: Optional[str] = None, limit: int = 20):
    """Get what's currently playing, optionally filtered by genre"""
    results = []
    
    for station_id, cache_entry in now_playing_cache.items():
        show = cache_entry.get("show")
        if show:
            # Filter by genre if specified
            if genre and genre.lower() not in [g.lower() for g in show.genres]:
                continue
            results.append({
                "station": stations_db.get(station_id),
                "show": show,
                "started_at": cache_entry.get("started_at")
            })
    
    return results[:limit]

@app.get("/api/stations/{station_id}/schedule")
async def get_station_schedule(station_id: str):
    """Get schedule for a specific station"""
    if station_id not in stations_db:
        raise HTTPException(status_code=404, detail="Station not found")
    
    station_shows = [s for s in shows_db.values() if s.station_id == station_id]
    return sorted(station_shows, key=lambda x: x.start_time)

@app.post("/api/schedules")
async def create_schedule(schedule: UserSchedule):
    """Create a new user schedule"""
    user_schedules_db[schedule.id] = schedule
    return schedule

@app.get("/api/schedules/{schedule_id}")
async def get_schedule(schedule_id: str):
    """Get a specific schedule"""
    if schedule_id not in user_schedules_db:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return user_schedules_db[schedule_id]

@app.get("/api/genres")
async def get_genres():
    """Get all available genres across stations"""
    all_genres = set()
    for station in stations_db.values():
        all_genres.update(station.genres)
    for show in shows_db.values():
        all_genres.update(show.genres)
    return sorted(list(all_genres))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "stations_count": len(stations_db),
        "shows_count": len(shows_db),
        "timestamp": datetime.now().isoformat()
    }

# Import and register scraper routes
from scrapers.kexp_scraper import router as kexp_router
from scrapers.wfmu_scraper import router as wfmu_router

app.include_router(kexp_router, prefix="/api/scrapers/kexp")
app.include_router(wfmu_router, prefix="/api/scrapers/wfmu")

# Import and register stream proxy
from stream_proxy import router as proxy_router
app.include_router(proxy_router, prefix="/api/proxy")

# Serve frontend from FastAPI so browser can use a single URL.
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
