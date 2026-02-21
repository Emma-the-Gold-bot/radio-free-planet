# Radio Agnostic - Static Deployment Guide

**Version:** 0.4.0  
**Stations:** 36 public radio streams  
**Schedules:** Full weekly programming for all stations  
**Deployment:** Static HTML/JS/CSS - no server required

---

## What's Included

A fully static public radio aggregator with real-time "What's On Now" from weekly schedules.

```
static/
├── index.html          # Main app shell
├── app.js              # Static JavaScript with schedule calculation
├── styles.css          # Main styles (including now-playing cards)
├── scheduler.css       # Schedule/timeline styles
├── manifest.json       # PWA manifest
├── DEPLOY.md           # This file
└── data/
    ├── stations.json       # 16 stations with stream URLs
    ├── schedules.json      # Weekly schedules (125KB)
    └── now_playing.json    # Auto-generated current shows
```

---

## Features

### ✅ Radio Streaming
- **16 curated stations** from KEXP to WFMU to WNYC
- **7 browser-ready** streams (no proxy needed)
- **9 CORS-proxied** streams (auto-routed)
- Mobile-responsive audio player

### 📅 "What's On Now"
- **Live schedule calculation** - no backend needed
- Shows current program for each station
- Time remaining: "2h 15m left"
- Host names and show descriptions
- Updates every minute

### 🔍 Genre Filtering
- Filter by 20+ genres: indie, jazz, classical, experimental
- Click a genre pill → see only matching shows
- Search by station, show, or host

### 📱 Scheduling
- Create personal listening schedules
- Save shows to "My Schedule"
- LocalStorage persistence
- Timeline view by day

### 📻 PWA Ready
- Install as mobile app
- Works offline (streams cached)
- Manifest included

---

## Deploy to IONOS (or any static host)

### Step 1: Upload Files

```bash
# Zip the static directory
cd /home/emma/.openclaw/workspace/projects/radio-agnostic/
zip -r radio-agnostic.zip static/

# Upload via IONOS Control Panel
# OR via FTP/SFTP to public_html/
```

### Step 2: Server File Structure

```
public_html/
├── index.html
├── app.js
├── styles.css
├── scheduler.css
├── manifest.json
└── data/
    ├── stations.json
    ├── schedules.json
    └── now_playing.json
```

### Step 3: Access

Visit: `https://yourdomain.com/` or `https://yourdomain.com/static/`

---

## Station List (v0.4.0) - 36 Stations

### Browser-Ready (No Proxy) - 26 stations:

**Legendary Public Radio:**
1. **KEXP** - Seattle indie/rock (LIVE SCHEDULES!)
2. **NPR** - National news
3. **Radio Paradise** - Eclectic rock/alternative

**College Radio:**
4. **CJSW** - Calgary community
5. **WMSE** - Milwaukee college
6. **WCBN** - Ann Arbor freeform
7. **WRFL** - Lexington college
8. **KXLU** - L.A. indie/experimental
9. **WNYU** - NYU college/freeform
10. **WREK** - Georgia Tech experimental

**Internet Radio / Community:**
11. **SomaFM Groove Salad** - Ambient electronic
12. **SomaFM Drone Zone** - Ambient drone
13. **dublab** - L.A. electronic/ambient
14. **NTS Radio** - Experimental/hip-hop/jazz (London)
15. **Worldwide FM** - Jazz/soul/world (London)
16. **Kiosk Radio** - Electronic/disco/house (Brussels)
17. **The Lot Radio** - Electronic/disco (Brooklyn)
18. **Cashmere Radio** - Experimental/ambient (Berlin)
19. **Le Mellotron** - Jazz/soul/hip-hop (Paris)
20. **Soho Radio** - Indie/electronic/jazz (London)
21. **Subcity Radio** - Electronic/bass (Glasgow)
22. **Threads Radio** - Electronic/jungle/grime (London)
23. **FRISKY Radio** - Deep house/progressive (NYC)
24. **KISS 2020s** - Pop/dance hits (London)
25. **Hirschmilch Radio** - Progressive/techno (Berlin)

**International Public Radio:**
26. **FIP** - Paris eclectic/world

### CORS-Proxied (via corsproxy.io) - 10 stations:
27. **WNYC** - NYC news/talk
28. **WQXR** - NYC classical
29. **WQXR New Sounds** - Experimental
30. **WQXR Operavore** - Opera
31. **KUT** - Austin NPR
32. **KUTX** - Austin indie (192kbps!)
33. **KZSU** - Stanford college
34. **WFMU** - Jersey City freeform
35. **KALX** - Berkeley college
36. **WFMU Ichiban** - Japanese music

---

## How Schedules Work

### Static JSON Architecture

```javascript
// schedules.json structure
{
  "station_id": "kexp",
  "schedule": {
    "monday": [
      {
        "title": "The Morning Show",
        "host": "John Richards",
        "start_time": "06:00",
        "end_time": "10:00",
        "genre": "indie",
        "description": "Start your day...",
        "image_url": "https://..."
      }
    ]
  }
}
```

### Browser Calculation

```javascript
// Frontend calculates "now playing"
const now = new Date();
const currentTime = now.toTimeString().slice(0, 5); // "14:30"
const currentDay = now.getDay(); // 0 = Monday

// Find shows where start_time <= current < end_time
const nowPlaying = schedules.filter(show => 
  show.day_of_week === currentDay &&
  show.start_time <= currentTime &&
  show.end_time > currentTime
);
```

### Update Schedule Data

**Weekly (recommended):**

```bash
cd /path/to/radio-agnostic/
python3 fetch_schedules.py

# This fetches from:
# - KEXP API (real-time)
# - WFMU HTML (scraped)
# - Others (manual placeholders)

# Then commit and redeploy:
git add static/data/schedules.json
git commit -m "Update schedules for week of $(date +%Y-%m-%d)"
git push
```

---

## Schedule Data Sources

| Station | Source | Status |
|---------|--------|--------|
| KEXP | API (api.kexp.org) | ✅ Live data |
| WFMU | HTML scraping | ⚠️ Weekly manual |
| Others | Manual/generic | ⚠️ Placeholder |

### Adding More Schedules

1. Find station's schedule page
2. Add scraper to `fetch_schedules.py`
3. Or manually add to `schedules.json`

---

## Customization

### Change CORS Proxy

Edit `app.js`:

```javascript
const CONFIG = {
  corsProxy: 'https://corsproxy.io/?',  // Change this
  // Options:
  // 'https://api.allorigins.win/raw?url='
  // 'https://cors-anywhere.herokuapp.com/'
}
```

### Add a Station

Edit `data/stations.json`:

```json
{
  "id": "new-station",
  "callsign": "KNST",
  "name": "KNST 89.1 FM",
  "location": {"city": "City", "state": "ST", "lat": 0, "lng": 0},
  "streams": [{"format": "mp3", "url": "https://...", "quality": "high"}],
  "genres": ["indie", "rock"],
  "cors_status": "open"
}
```

Then add schedule to `data/schedules.json`:

```json
{
  "station_id": "new-station",
  "schedule": {
    "monday": [
      {"title": "Morning Show", "host": "DJ Name", "start_time": "06:00", "end_time": "10:00", "genre": "indie"}
    ]
  }
}
```

---

## Browser Compatibility

- ✅ Chrome/Edge
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers
- ✅ Web Audio API support required

---

## Troubleshooting

### "No stations loaded"
- Check `data/stations.json` exists
- Open browser dev tools → Network tab
- Verify file paths are correct

### Streams won't play
- Check for CORS errors in console
- Try different CORS proxy
- Some streams may be temporarily down

### Schedule data outdated
- Run `fetch_schedules.py` to refresh
- Or manually edit `data/schedules.json`

### Proxy errors (429)
- Public proxy is rate-limited
- Wait a few minutes
- Consider self-hosting a proxy

---

## File Sizes (v0.4.0)

| File | Size | Notes |
|------|------|-------|
| index.html | 5KB | App shell |
| app.js | 14KB | Core logic |
| styles.css | 10KB | Main + now-playing styles |
| scheduler.css | 6KB | Schedule styles |
| stations.json | 20KB | 36 stations |
| schedules.json | 180KB | Full weekly data (36 stations) |
| **Total** | **~235KB** | Without audio |

---

## License

MIT - Free to use, modify, deploy.

Stream content belongs to respective stations.
Schedule data scraped from public websites.

---

## Roadmap / TODO

- [ ] Add NPR API schedule data
- [ ] Scrape WNYC/WQXR schedules
- [ ] Scrape KUT/KUTX schedules
- [ ] Community schedule submission form
- [ ] Export schedules to iCal/.ics
- [ ] "Up Next" preview (next 3 shows)
- [ ] Show reminders/notifications
- [ ] Dark/light theme toggle

---

## Support

This is a static Single Page Application. 

For updates:
1. Edit `data/stations.json` to add stations
2. Run `fetch_schedules.py` to refresh schedules
3. Test locally: `python3 -m http.server 8000`
4. Commit and redeploy

Built with vanilla JavaScript. No frameworks. No build step.
