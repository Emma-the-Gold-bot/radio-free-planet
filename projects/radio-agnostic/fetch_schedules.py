#!/usr/bin/env python3
"""
Schedule Fetcher - Gather weekly schedules for all stations
Outputs to static/data/schedules.json
"""

import asyncio
import aiohttp
import json
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class ShowSlot:
    title: str
    host: str
    start_time: str  # HH:MM format
    end_time: str
    day_of_week: int  # 0=Monday, 6=Sunday
    genre: str
    description: Optional[str] = None
    image_url: Optional[str] = None

@dataclass
class StationSchedule:
    station_id: str
    station_name: str
    timezone: str
    schedule: Dict[str, List[ShowSlot]]  # day_name -> slots
    last_updated: str

# Day name mapping
DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

async def fetch_kexp_schedule(session: aiohttp.ClientSession) -> StationSchedule:
    """Fetch KEXP schedule from their API"""
    print("Fetching KEXP schedule...")
    
    # Get shows for the next 7 days
    schedule = {day: [] for day in DAYS}
    
    try:
        # Fetch recent shows
        async with session.get(
            "https://api.kexp.org/v2/shows/?limit=200",
            timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status != 200:
                print(f"KEXP API error: {resp.status}")
                return None
            
            data = await resp.json()
            shows = data.get('results', [])
            
            # Process shows
            for show in shows:
                start_str = show.get('start_time', '')
                if not start_str:
                    continue
                
                # Parse datetime
                try:
                    start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                    # Convert to Pacific time
                    import pytz
                    pacific = pytz.timezone('America/Los_Angeles')
                    start_dt = start_dt.astimezone(pacific)
                    
                    day_name = DAYS[start_dt.weekday()]
                    start_time = start_dt.strftime('%H:%M')
                    
                    # Estimate end time (most shows are 3 hours)
                    end_dt = start_dt + timedelta(hours=3)
                    end_time = end_dt.strftime('%H:%M')
                    
                    slot = ShowSlot(
                        title=show.get('program_name', 'Unknown'),
                        host=', '.join(show.get('host_names', ['Unknown'])),
                        start_time=start_time,
                        end_time=end_time,
                        day_of_week=start_dt.weekday(),
                        genre=show.get('program_tags', 'eclectic').split(',')[0].lower() if show.get('program_tags') else 'eclectic',
                        description=show.get('tagline', ''),
                        image_url=show.get('program_image_uri')
                    )
                    
                    # Only add if within next 7 days
                    schedule[day_name].append(slot)
                    
                except Exception as e:
                    print(f"Error parsing show: {e}")
                    continue
            
            # Sort each day by time
            for day in DAYS:
                schedule[day].sort(key=lambda x: x.start_time)
            
            return StationSchedule(
                station_id='kexp',
                station_name='KEXP 90.3 FM',
                timezone='America/Los_Angeles',
                schedule=schedule,
                last_updated=datetime.now().isoformat()
            )
            
    except Exception as e:
        print(f"Error fetching KEXP: {e}")
        return None

async def fetch_wfmu_schedule(session: aiohttp.ClientSession) -> StationSchedule:
    """Fetch WFMU schedule via HTML scraping"""
    print("Fetching WFMU schedule (HTML scrape)...")
    
    # For now, create a simplified schedule based on known WFMU programming
    # In production, this would scrape wfmu.org/schedule
    
    schedule = {day: [] for day in DAYS}
    
    # Known WFMU weekday shows (simplified)
    weekday_morning = ShowSlot(
        title="Wake",
        host="Clay Pigeon",
        start_time="06:00",
        end_time="09:00",
        day_of_week=0,
        genre="eclectic",
        description="Morning show"
    )
    
    # Add to all weekdays
    for i in range(5):  # Monday-Friday
        schedule[DAYS[i]].append(ShowSlot(
            title="Wake",
            host="Clay Pigeon",
            start_time="06:00",
            end_time="09:00",
            day_of_week=i,
            genre="eclectic"
        ))
    
    # Weekend shows
    schedule['saturday'].append(ShowSlot(
        title="Saturday Programming",
        host="Various",
        start_time="00:00",
        end_time="23:59",
        day_of_week=5,
        genre="freeform"
    ))
    
    schedule['sunday'].append(ShowSlot(
        title="Sunday Programming",
        host="Various",
        start_time="00:00",
        end_time="23:59",
        day_of_week=6,
        genre="freeform"
    ))
    
    return StationSchedule(
        station_id='wfmu',
        station_name='WFMU 91.1 FM',
        timezone='America/New_York',
        schedule=schedule,
        last_updated=datetime.now().isoformat()
    )

def create_manual_schedule(station_id: str, station_name: str, timezone: str) -> StationSchedule:
    """Create a placeholder schedule for stations without API/scraper yet"""
    schedule = {day: [] for day in DAYS}
    
    # Generic all-day placeholder
    for i, day in enumerate(DAYS):
        schedule[day].append(ShowSlot(
            title="Live Programming",
            host="Various DJs",
            start_time="00:00",
            end_time="23:59",
            day_of_week=i,
            genre="various"
        ))
    
    return StationSchedule(
        station_id=station_id,
        station_name=station_name,
        timezone=timezone,
        schedule=schedule,
        last_updated=datetime.now().isoformat()
    )

async def fetch_all_schedules():
    """Fetch schedules for all stations"""
    async with aiohttp.ClientSession() as session:
        schedules = []
        
        # KEXP (has API)
        kexp = await fetch_kexp_schedule(session)
        if kexp:
            schedules.append(kexp)
        
        # WFMU (scraper)
        wfmu = await fetch_wfmu_schedule(session)
        if wfmu:
            schedules.append(wfmu)
        
        # Others (manual placeholders for now)
        others = [
            ('kalx', 'KALX 90.7 FM', 'America/Los_Angeles'),
            ('cjsw', 'CJSW 90.9 FM', 'America/Edmonton'),
            ('wmse', 'WMSE 91.7 FM', 'America/Chicago'),
            ('wcbn', 'WCBN 88.3 FM', 'America/Detroit'),
            ('wrfl', 'WRFL 88.1 FM', 'America/New_York'),
            ('npr', 'NPR Program Stream', 'America/New_York'),
            ('wnyc', 'WNYC 93.9 FM', 'America/New_York'),
            ('wqxr', 'WQXR 105.9 FM', 'America/New_York'),
            ('wqxr-newsounds', 'WQXR New Sounds', 'America/New_York'),
            ('wqxr-operavore', 'WQXR Operavore', 'America/New_York'),
            ('kut', 'KUT 90.5 FM', 'America/Chicago'),
            ('kutx', 'KUTX 98.9 FM', 'America/Chicago'),
            ('kzsu', 'KZSU 90.1 FM', 'America/Los_Angeles'),
            ('wfmu-ichiban', 'WFMU Ichiban', 'America/New_York'),
        ]
        
        for station_id, name, tz in others:
            schedules.append(create_manual_schedule(station_id, name, tz))
        
        return schedules

def save_schedules(schedules: List[StationSchedule]):
    """Save schedules to JSON file"""
    output = {
        "version": "0.2.0",
        "last_updated": datetime.now().isoformat(),
        "count": len(schedules),
        "schedules": []
    }
    
    for sched in schedules:
        sched_dict = {
            "station_id": sched.station_id,
            "station_name": sched.station_name,
            "timezone": sched.timezone,
            "last_updated": sched.last_updated,
            "schedule": {}
        }
        
        for day, slots in sched.schedule.items():
            sched_dict["schedule"][day] = [
                {
                    "title": slot.title,
                    "host": slot.host,
                    "start_time": slot.start_time,
                    "end_time": slot.end_time,
                    "day_of_week": slot.day_of_week,
                    "genre": slot.genre,
                    "description": slot.description,
                    "image_url": slot.image_url
                }
                for slot in slots
            ]
        
        output["schedules"].append(sched_dict)
    
    with open('static/data/schedules.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nSaved {len(schedules)} schedules to static/data/schedules.json")

def generate_now_playing(schedules: List[StationSchedule]):
    """Generate current 'now playing' data based on schedules"""
    now = datetime.now()
    current_time = now.strftime('%H:%M')
    current_day = DAYS[now.weekday()]
    
    now_playing = []
    
    for sched in schedules:
        day_schedule = sched.schedule.get(current_day, [])
        
        for slot in day_schedule:
            if slot.start_time <= current_time < slot.end_time:
                now_playing.append({
                    "station_id": sched.station_id,
                    "station_name": sched.station_name,
                    "show_title": slot.title,
                    "host": slot.host,
                    "genre": slot.genre,
                    "start_time": slot.start_time,
                    "end_time": slot.end_time,
                    "timezone": sched.timezone
                })
                break
    
    return {
        "timestamp": now.isoformat(),
        "count": len(now_playing),
        "now_playing": now_playing
    }

async def main():
    print("Fetching schedules for all stations...")
    schedules = await fetch_all_schedules()
    
    if schedules:
        save_schedules(schedules)
        
        # Generate now playing
        now_playing = generate_now_playing(schedules)
        with open('static/data/now_playing.json', 'w') as f:
            json.dump(now_playing, f, indent=2)
        print(f"Generated now_playing.json with {now_playing['count']} shows")
    else:
        print("No schedules fetched!")

if __name__ == "__main__":
    asyncio.run(main())
