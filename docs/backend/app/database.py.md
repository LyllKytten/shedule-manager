# `backend/app/database.py`

SQLAlchemy setup.

- **`engine`** — created from `DATABASE_URL` with `pool_pre_ping=True`, so
  connections dropped by PostgreSQL are detected and replaced.
- **`SessionLocal`** — session factory; `expire_on_commit=False` so objects can
  still be serialized after `commit()`.
- **`Base`** — declarative base all models inherit from.
- **`get_db()`** — FastAPI dependency: one session per request, always closed.
- **`init_db()`** — imports `app.models` (registers tables) and runs
  `create_all`. Only creates missing tables; it never alters existing ones —
  introduce Alembic when columns need to change on a live database.
