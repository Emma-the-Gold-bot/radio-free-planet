# Public Radio Aggregator App - Technical Plan

## MVP Station Targets (Phase 1)

| Station | Location | Why | Data Source |
|---------|----------|-----|-------------|
| KEXP | Seattle, WA | Legendary, excellent API | Official API |
| KCRW | Los Angeles, CA | Strong web presence, good music | Official API |
| WFMU | Jersey City, NJ | The gold standard of weird | Schedule scraping |
| KALX | Berkeley, CA | College radio, solid web | Schedule scraping |
| WRUV | Burlington, VT | Small but well-documented | Schedule scraping |
| Radio Rethink | Various | Already has web tuner | Reverse engineer or partner |
| KPCC/LAist | Los Angeles, CA | NPR affiliate, good data | NPR API |
| WBUR | Boston, MA | NPR affiliate | NPR API |
| KUTX | Austin, TX | Music focus, younger audience | Schedule scraping |
| CKUT | Montreal, QC | Canadian college radio | Schedule scraping |

## Core User Stories

1. **Browse by genre** — "Show me punk/indie rock playing now"
2. **Save shows** — "I like this Thursday 10pm show on KEXP"
3. **Build schedules** — "My Monday: Morning becomes eclectic at 9, then KALX at noon"
4. **Quick play** — One-tap streaming from discovery feed

## Architecture

### Backend Stack

```
Node.js/Express or Python/FastAPI
├── PostgreSQL (station metadata, user schedules)
├── Redis (caching now-playing state)
├── Elasticsearch (genre/topic search)
├── Bull/Redis (job queue for scraping)
└── S3/Local (station logos, fallback assets)
```

### Frontend Stack

```
React Native (iOS/Android)
└── Alternatives: Flutter, or PWA with Capacitor

Key Libraries:
├── react-native-track-player (audio streaming)
├── react-native-maps (geographic browse v2)
└── @tanstack/react-query (data fetching/caching)
```

## Backend Components

### 1. Station Registry Service

```typescript
interface Station {
  id: string;
  callsign: string;
  name: string;
  location: {
    city: string;
    state: string;
    country: string;
    lat: number;
    lng: number;
  };
  streams: Stream[];
  dataSource: 'api' | 'scrape' | 'manual';
  apiEndpoint?: string;
  scheduleUrl?: string;
  timezone: string;
  genres: string[]; // Station's overall genres
}

interface Stream {
  format: 'mp3' | 'aac' | 'hls' | 'icecast';
  url: string;
  quality: 'low' | 'medium' | 'high';
  isPrimary: boolean;
}
```

### 2. Schedule Aggregator (The Hard Part)

**For stations with APIs (KEXP, NPR):**
- Poll every 15 minutes
- Store in PostgreSQL with conflict resolution

**For stations requiring scraping (WFMU, KALX):**
- Puppeteer/Playwright scrapers
- CSS selectors per station (fragile, needs monitoring)
- Fallback: Manual schedule entry for small stations

**Unified Schedule Schema:**
```typescript
interface Show {
  id: string;
  stationId: string;
  title: string;
  description?: string;
  startTime: Date;
  endTime: Date;
  timezone: string;
  hosts?: string[];
  genres: string[]; // Normalized tags: "punk", "indie", "jazz", "talk"
  recurring: boolean;
  recurrencePattern?: string; // iCal RRULE style
}
```

**Genre Normalizer:**
Critical piece — every station uses different taxonomy.
- "Indie Rock" → `indie`
- "Post-punk" → `punk`
- "Jazz & Beyond" → `jazz`

Needs a mapping layer that learns/improves over time.

### 3. Now Playing Service

```typescript
// Runs every minute via cron/scheduled job
async function updateNowPlaying() {
  for (const station of activeStations) {
    const currentShow = await getCurrentShow(station.id);
    await redis.setex(`nowplaying:${station.id}`, 60, JSON.stringify({
      show: currentShow,
      streamUrl: station.getActiveStream(),
      startedAt: new Date()
    }));
  }
}
```

**Query endpoint:**
```
GET /api/now-playing?genre=punk&limit=20
→ Returns stations currently playing punk shows
```

### 4. User Schedule Service

```typescript
interface UserSchedule {
  id: string;
  userId: string;
  name: string; // "Workday Morning", "Late Night Weird"
  slots: ScheduleSlot[];
  isActive: boolean;
}

interface ScheduleSlot {
  dayOfWeek: 0-6;
  time: "HH:MM";
  stationId: string;
  showId?: string; // optional: specific show vs "play this station"
}

// Auto-play when schedule slot activates
```

## Frontend Structure

### Tab Navigation

1. **Discover** (Home)
   - "Now Playing" feed (reverse chronological)
   - Genre filter pills (horizontal scroll)
   - Station cards with: logo, show name, genre tags, play button

2. **Schedule** (Your Calendars)
   - List of user-created schedules
   - Create/edit schedule interface
   - Timeline view (what's coming up)

3. **Browse** (Map + List)
   - Geographic map (v2) OR list view grouped by city (v1)
   - Station detail pages with full schedule

4. **Settings**
   - Audio quality preference
   - Notification settings ("Your show starts in 5 min")
   - Export/backup schedules

### Key Screens (Wireframe Logic)

**Discover Feed:**
```
┌─────────────────────────────┐
│ 🔍 Search stations/shows    │
├─────────────────────────────┤
│ [All] [Indie] [Punk] [Jazz] │ ← Genre filters
├─────────────────────────────┤
│ ┌─────────────────────────┐ │
│ │ KEXP                    │ │
│ │ Morning Show            │ │
│ │ Indie • Rock            │ │
│ │ ▶️  8:00 AM - 11:00 AM  │ │
│ └─────────────────────────┘ │
│ ┌─────────────────────────┐ │
│ │ WFMU                    │ │
│ │ Downtown Soulville      │ │
│ │ Soul • R&B              │ │
│ │ ▶️  9:00 AM - 12:00 PM  │ │
│ └─────────────────────────┘ │
└─────────────────────────────┘
```

**Create Schedule:**
```
┌─────────────────────────────┐
│ Schedule Name: [________]   │
├─────────────────────────────┤
│ Monday                      │
│ 8:00 AM → KEXP Morning Show │
│ 12:00 PM → KALX            │
│ [+ Add slot]                │
├─────────────────────────────┤
│ Tuesday                     │
│ [+ Add slot]                │
└─────────────────────────────┘
```

## Data Challenges & Mitigations

### 1. Stream Reliability
- **Problem:** College station streams go down, change URLs
- **Solution:** Health check every 5 minutes, fallback to next stream URL, alert admin if all fail

### 2. Schedule Accuracy
- **Problem:** Shows run late, get preempted
- **Solution:** "Report issue" button for users, manual override capability for admins, weight stations with realtime "now playing" APIs higher

### 3. Genre Consistency
- **Problem:** Every station categorizes differently
- **Solution:** Start with 20 core genre tags, map station-specific terms, allow user corrections ("This isn't punk, it's post-punk")

### 4. Timezones
- **Problem:** Station in Seattle, user in NYC, show starts at 9am PST
- **Solution:** Store all times in station local time with timezone, convert to user timezone on display

## Development Phases

### Phase 1: Foundation (Weeks 1-4)
- Scaffold backend API
- Implement 2-3 API-based stations (KEXP, NPR affiliates)
- Basic React Native app with play/pause
- Simple "now playing" feed (no genre filters yet)

### Phase 2: Discovery (Weeks 5-8)
- Add 5 scraping-based stations
- Genre filter system
- Elasticsearch integration
- Show saving (bookmarks)

### Phase 3: Schedules (Weeks 9-12)
- User schedule creation
- Push notifications for show start
- Background audio handling
- Offline mode / cache

### Phase 4: Polish + Scale (Weeks 13-16)
- Map/geographic browse (v2)
- Station detail pages with full schedules
- Performance optimization
- Open source release?

## MVP Definition (What "Working" Means)

Can a user:
1. Open app
2. See 5+ stations with current shows
3. Filter by "indie" or "punk"
4. Tap play and hear audio
5. Save a show to a personal schedule
6. Get notified when that show starts

## Potential Roadblocks

1. **Legal:** Are we allowed to aggregate streams? (Generally yes for public radio, but check station terms)
2. **Rate limits:** Some APIs restrict calls
3. **Maintenance:** Scrapers break when sites redesign — budget 2hrs/month per scraped station
4. **Discovery:** Getting users to find the app — that's the real battle

## Questions for You

1. Are you a developer, or do you need technical help building this?
2. What's your timeline — quick hack or serious long-term project?
3. iOS-first, Android-first, or both simultaneously?
4. Do you want this open source, or keep it yours?

---

Plan written: 2026-02-15
By: Emma (the ghost in your machine)
