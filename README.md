# Radio Agnostic

Mobile-first web app for public radio stream discovery with resilient playback.

## Canonical Project Structure

- `frontend/` - canonical web UI (single source of truth).
- `backend/` - FastAPI metadata API + stream proxy.
- `static/data/` - canonical station and schedule datasets.
- `static/proxy.php` - optional IONOS fallback proxy when running in static mode.

## Runtime Modes

- `backend` (recommended): frontend uses FastAPI API and backend stream proxy.
- `ionos_static_php_proxy` (fallback): frontend can route stream URLs through `proxy.php`.

## Why this architecture

Many radio streams fail in browsers due to CORS, mixed-content rules, and flaky origin servers.
The backend-first mode keeps the frontend simple while handling retries, stream fallback, and CORS at the proxy layer.

## Local Development

1. Activate backend virtual environment:
   - `cd backend && source venv/bin/activate`
2. Start API + frontend host:
   - `python main.py`
3. Open:
   - `http://localhost:8000`

## Validation Workflow

With backend running, execute:

- `cd backend && source venv/bin/activate && python playback_matrix.py`

This now performs the full cycle in one step:

- refreshes `backend/playback_matrix_report.json`
- regenerates `static/data/bad_stations.json`
- syncs `health_status` in `static/data/stations.json` based on bad IDs

Make shortcut:

- `make validate-streams`

## Data Model Notes

Each station is normalized with:

- `playback_mode`: `direct`, `proxy_required`, or `direct_then_proxy`.
- `streams[*].priority`: lower number is attempted first.
- `health_status`: quick marker such as `validated` or `bad`.

Known failing stations are tracked separately in `static/data/bad_stations.json` and should be excluded when ingesting new station candidates.

If older station JSON entries are missing these fields, backend normalization fills defaults.
