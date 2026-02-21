# Deployment Profiles

## Profile C: Backend-first (recommended)

Use this for highest stream playback success.

### Components
- `frontend/` served by FastAPI.
- `backend/main.py` exposes `/api/*` metadata + `/api/proxy/*`.
- `static/data/*.json` provides shared station/schedule data.

### Start
- `cd backend`
- `source venv/bin/activate`
- `python main.py`

### Public hosting
- Deploy backend app (VPS/container).
- Serve `http(s)` to users from the backend host.

## Profile B: Static + PHP proxy on IONOS (fallback)

Use this when you need static hosting and cannot run Python backend.

### Components
- Upload frontend assets as static files.
- Upload `static/proxy.php`.
- Keep `static/data/stations.json` and schedule files available.

### Frontend mode switch
Set in `index.html` before loading `app.js`:

```html
<script>
  window.RADIO_AGNOSTIC_MODE = "ionos_static_php_proxy";
  window.RADIO_AGNOSTIC_PHP_PROXY = "/proxy.php?url=";
</script>
```

## Notes

- No deployment profile can guarantee 100% stream uptime.
- Backend-first provides best practical coverage by handling retries, fallback, and CORS at the proxy layer.
