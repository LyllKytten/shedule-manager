# `backend/app/main.py`

Application entry point — `uvicorn app.main:app`.

## What it does

- **`lifespan`** — runs once on startup: `init_db()` creates missing tables,
  then `ensure_superuser()` creates the configured superuser (see
  [bootstrap.py](bootstrap.py.md)).
- **`app`** — the `FastAPI` instance (title *Schedule Manager API*). Swagger UI
  is available at `/docs`.
- **CORS** — origins from `CORS_ORIGINS` (comma-separated). With `*`,
  credentials are disabled as the CORS spec requires; the app sends the token in
  a header, so it doesn't need them.
- **Routers** — `auth`, `events`, `settings`, `admin`.
- **`GET /health`** — liveness probe, returns `{"status": "ok"}`.
