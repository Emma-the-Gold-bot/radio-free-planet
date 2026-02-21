# Static Directory Notes

`frontend/` is now the canonical web application codepath.

This directory is retained for:

- canonical datasets in `data/`
- IONOS fallback proxy in `proxy.php`
- static-only deployment assets

If you deploy backend-first, serve `frontend/` via FastAPI from `backend/main.py`.
