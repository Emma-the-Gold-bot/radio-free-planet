# Radio Agnostic v0.4.0 - Release Summary

## 🎉 Major Milestone: 36 Stations!

### What's New in v0.4.0

We've expanded from 21 to **36 stations** - a 71% increase! This release focuses on adding premier internet radio and community stations from around the world.

### 📊 By The Numbers

- **36 Total Stations** (up from 21)
- **26 Browser-Ready** (72% - no proxy needed!)
- **10 CORS-Proxied** (28%)
- **46 Unique Genres**
- **4 Countries**: USA, UK, France, Germany, Belgium, Canada
- **12 Cities** represented

### 🌍 Geographic Coverage

**USA (21 stations):**
- West Coast: Seattle, San Francisco, L.A., Berkeley, Stanford
- East Coast: NYC, Jersey City, Brooklyn, Boston, DC
- Midwest: Milwaukee, Ann Arbor, Lexington
- South: Atlanta, Austin

**UK/Europe (14 stations):**
- London: 9 stations (NTS, Worldwide, Soho, Threads, etc.)
- Glasgow: Subcity Radio
- Paris: FIP, Le Mellotron
- Berlin: Cashmere Radio, Hirschmilch
- Brussels: Kiosk Radio

**Canada (1 station):**
- Calgary: CJSW

### 🎵 New Stations Added (15)

**Ambient/Chill:**
- SomaFM Groove Salad (San Francisco)
- SomaFM Drone Zone (San Francisco)

**Eclectic/Alternative:**
- Radio Paradise (California)
- FIP Radio France (Paris)

**Electronic/Underground:**
- NTS Radio (London)
- Worldwide FM (London)
- Kiosk Radio (Brussels)
- The Lot Radio (Brooklyn)
- Cashmere Radio (Berlin)
- dublab (Los Angeles)

**Jazz/Soul:**
- Le Mellotron (Paris)
- Soho Radio (London)

**Bass/Grime/Experimental:**
- Subcity Radio (Glasgow)
- Threads Radio (London)

**Dance/Techno:**
- FRISKY Radio (NYC)
- Hirschmilch Radio (Berlin)
- KISS 2020s (London)

### 🎯 Key Features

1. **"What's On Now"** - Live schedule calculation
2. **Genre Filtering** - 46 genres to choose from
3. **Time Remaining** - Shows how much time is left in current program
4. **Schedule Builder** - Create personal listening schedules
5. **PWA Support** - Install as mobile app
6. **Static Deployment** - No backend required

### 📁 File Structure

```
radio-agnostic/static/
├── index.html              # 8KB - App shell
├── app.js                  # 20KB - Core logic with schedules
├── styles.css              # 12KB - Main styles
├── scheduler.css           # 8KB - Schedule styles
├── manifest.json           # 4KB - PWA manifest
├── DEPLOY.md               # 12KB - Deployment guide
└── data/
    ├── stations.json       # 24KB - 36 stations
    ├── schedules.json      # 164KB - Weekly schedules
    └── now_playing.json    # 8KB - Current shows
```

**Total Size: ~260KB** (without audio)

### 🚀 Quick Start

```bash
# Test locally
cd static/
python3 -m http.server 8000

# Open http://localhost:8000
```

### 📦 Deploy to Production

Upload all files in `static/` to any web host:
- IONOS
- Netlify
- GitHub Pages
- Vercel
- Any static hosting

### 🎧 Station Categories

**Public Radio (9):**
KEXP, NPR, WNYC, WQXR (×3), KUT, KUTX, FIP

**College Radio (10):**
KALX, CJSW, WMSE, WCBN, WRFL, KZSU, KXLU, WNYU, WREK, dublab

**Internet Radio (15):**
SomaFM (×2), Radio Paradise, NTS, Worldwide, Kiosk, The Lot,
Cashmere, Le Mellotron, Soho, Subcity, Threads, FRISKY, KISS, Hirschmilch

**Specialty (2):**
WFMU, WFMU Ichiban

### 🔄 Maintenance

To update schedules:
```bash
python3 fetch_schedules.py
# Commit changes
# Redeploy
```

### 📈 Next Steps / Roadmap

- [ ] Scrape more schedule data (NTS, SomaFM, etc.)
- [ ] Add more college radio stations
- [ ] User accounts for cross-device schedules
- [ ] Export to calendar (.ics)
- [ ] Show reminders/notifications
- [ ] Dark/light theme toggle

---

**Built with vanilla JavaScript. No frameworks. No dependencies.**

**License:** MIT

**Stream content belongs to respective stations.**

**Schedule data scraped from public sources.**
