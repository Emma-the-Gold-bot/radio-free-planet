# Radio Agnostic - Stream Status Report

## Summary
- **Total Stations:** 51
- **Streams Available:** 51 (100%)
- **CORS Blocked (need proxy):** 11 stations
- **CORS Open (direct):** 40 stations

## The Issue
Many streams that worked before may not work now due to:
1. **CORS proxy service issues** - corsproxy.io may be rate-limiting or blocking
2. **HTTP/HTTPS mixed content** - 17 streams use HTTP (blocked on HTTPS sites)
3. **Stream URL changes** - some stations may have updated their URLs

## CORS-Blocked Stations (Require Proxy)
These 11 stations need the proxy to work in browsers:
- WFMU 91.1 FM
- KALX 90.7 FM  
- WNYC 93.9 FM
- WQXR 105.9 FM
- WQXR New Sounds
- WQXR Operavore
- KUT 90.5 FM
- KUTX 98.9 FM
- KZSU 90.1 FM
- WFMU Ichiban
- FIP Radio France

## Quick Fixes to Try

### Option 1: Test Without Proxy
1. Open the app in browser
2. Open Developer Tools (F12)
3. Go to Console tab
4. Try playing a CORS-blocked station
5. Look for error messages

### Option 2: Alternative Proxy
If corsproxy.io is failing, try these alternatives:
- `https://api.allorigins.win/get?url=`
- `https://api.codetabs.com/v1/proxy?quest=`

Change in app.js:
```javascript
const CONFIG = {
  corsProxy: 'https://api.allorigins.win/get?url=',
  // ...
};
```

### Option 3: Deploy with Proxy
For production, deploy a simple CORS proxy alongside the app:

**proxy.php** (on your IONOS hosting):
```php
<?php
$url = $_GET['url'];
header('Access-Control-Allow-Origin: *');
readfile($url);
?>
```

Then update CONFIG:
```javascript
corsProxy: '/proxy.php?url='
```

## Testing Checklist
- [ ] Test KEXP (CORS open - should work directly)
- [ ] Test Radio Paradise (CORS open - should work)
- [ ] Test WFMU (CORS blocked - needs proxy)
- [ ] Check browser console for errors
- [ ] Check if proxy is being used (look for corsproxy.io in Network tab)

## Recommended Next Steps
1. Test the app locally with browser console open
2. Identify which specific error messages appear
3. Either fix proxy issues or switch to alternative proxy
4. Consider setting up your own proxy on IONOS for reliability

---
Generated: 2026-02-18
