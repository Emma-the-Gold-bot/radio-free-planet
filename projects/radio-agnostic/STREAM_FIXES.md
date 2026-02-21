# Stream Compatibility Solutions

## Problem Analysis

Out of 21 tested stations:
- **14% work directly** in browser (3 stations)
- **9.5% need CORS proxy** (2 stations)
- **57% are unreachable** (SSL errors, timeouts, dead URLs)

## Working Streams (Use These)

| Station | URL | Bitrate | Notes |
|---------|-----|---------|-------|
| KEXP | https://kexp-mp3-128.streamguys1.com/kexp128.mp3 | 128k | Perfect |
| KALX | http://stream.kalx.berkeley.edu:8000/kalx-128.mp3 | 128k | No CORS, but works |
| CJSW | https://stream.cjsw.com/cjsw.mp3 | 128k | Perfect |

## Fix Strategy by Category

### 1. SSL Certificate Errors (StreamGuys1 CDN)

**Problem:** Hostname on certificate doesn't match requested hostname
**Example:** `kcrw.streamguys1.com` cert is for `*.streamguys1.com` or different domain

**Fix Options:**

A) **Disable SSL verification** (backend proxy only - NOT browser)
```python
# In Python requests/aiohttp
async with aiohttp.ClientSession() as session:
    async with session.get(url, ssl=False) as resp:
        # Stream will work but insecure
```

B) **Find alternate URL** (recommended)
Search for station's alternate stream endpoints:
- Check station's website "Listen Live" page
- Look for direct Icecast URLs vs CDN URLs
- Try HTTP instead of HTTPS for older servers

C) **Proxy through backend** (most reliable)
Browser → Your Backend → Stream (SSL verification disabled on backend)

### 2. CORS-Restricted Streams (WFMU, KGNU)

**Problem:** `Access-Control-Allow-Origin` set to specific domain, not `*`

**Fix Options:**

A) **CORS Proxy** (quick fix)
```javascript
// Use a public CORS proxy
const proxyUrl = 'https://cors-anywhere.herokuapp.com/';
const streamUrl = proxyUrl + 'https://stream0.wfmu.org/freeform-128k';
```
⚠️ Public proxies are unreliable/rate-limited

B) **Self-hosted CORS proxy** (better)
Add to your FastAPI backend:
```python
@app.get("/proxy/stream/{station_id}")
async def proxy_stream(station_id: str):
    station = stations_db.get(station_id)
    if not station:
        raise HTTPException(404)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(station.streams[0].url, ssl=False) as resp:
            return StreamingResponse(
                resp.content,
                media_type=resp.headers.get('Content-Type', 'audio/mpeg'),
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "icy-name": resp.headers.get("icy-name", ""),
                }
            )
```

C) **Request CORS whitelisting** (best long-term)
Contact station webmaster:
"Hi, I'm building a public radio aggregator app. Could you add our domain to your CORS whitelist? We need `Access-Control-Allow-Origin: *` or our specific domain."

### 3. Timeout/Unresponsive Streams

**Stations:** WBUR, CKUT, CFMU, KDVS

**Diagnosis:**
```bash
# Test if server is up at all
ping stream.kdvs.org
# Test specific port
telnet stream.kdvs.org 8000
# Test with curl
curl -v http://archives.kdvs.org:8000/kdvs128mp3
```

**Likely causes:**
- Server temporarily down
- IP blocking/filtering
- Port changed
- Stream URL changed

**Fix:** Find updated URLs via:
- Station's website "Listen" page
- Stream URL directories (streamfinder.com, radio-locator.com)
- Direct contact with station

### 4. HTTP 404 Errors (Moved URLs)

**Stations:** CIUT, NPR News, WMSE, BBC World Service

**These URLs are outdated.** Need to find current ones:

**NPR News:**
- Try: https://npr-ice.streamguys1.com/live.mp3
- Or: https://live-audio.pc.cdn.bitgravity.com/live-audio/liveradio/npr/838858/npr.mp3

**BBC World Service:**
- Likely returns HLS playlist (.m3u8), not MP3
- Try: https://stream.live.vc.bbcmedia.co.uk/bbc_world_service
- HLS needs different player handling

**CIUT, WMSE:**
- Check station websites for updated URLs
- May have moved to HTTPS-only
- May have changed streaming provider

## Recommended Architecture

```
Browser → Frontend (Vanilla JS)
   ↓
Backend API (FastAPI)
   ↓
Stream Router:
   ├─ CORS-OK streams → Browser direct
   ├─ CORS-blocked → Proxy through backend
   └─ Dead streams → Mark unavailable
```

## Implementation Priority

### Phase 1: Use What Works
Start with the 3 confirmed working streams:
- KEXP
- KALX  
- CJSW

### Phase 2: Add Proxy for CORS-Blocked
Add backend proxy for:
- WFMU
- KGNU

### Phase 3: Fix Broken Streams
For each broken stream:
1. Visit station website
2. Find current stream URL
3. Test with validator
4. Update database

### Phase 4: Scale
- Build scraper to auto-detect stream URLs
- Community submission form for new stations
- Fallback chains (if primary fails, try backup)

## Quick Wins

**SSL Bypass (for development only):**
```python
# backend/stream_proxy.py
import aiohttp
import ssl

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

async def fetch_stream(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, ssl=ssl_context) as resp:
            return resp
```

**Stream URL Sources:**
- Radio-locator.com API
- CommunityRadio.org directory
- Station websites directly
- icecast directory (dir.xiph.org)

## Next Steps

1. Choose 3-5 working stations for MVP
2. Implement backend CORS proxy
3. Add stream health monitoring (ping every 5 min)
4. Build URL updater tool
