# `backend/app/database.py`

SQLAlchemy setup.

- **`engine`** — created from `DATABASE_URL` with `pool_pre_ping=True`, so
  connections dropped by PostgreSQL are detected and replaced.
- **`SessionLocal`** — session factory; `expire_on_commit=False` so objects can
  still be serialized after `commit()`.
- **`Base`** — declarative base all models inherit from.
- **`get_db()`** — FastAPI dependency: one session per request, always closed.
- **`init_db()`** — imports `app.models` (registers tables) and runs
  `create_all`, then `_check_schema()`. `create_all` only creates missing
  tables and never alters existing ones.
- **`_check_schema()`** — compares the `events` columns in the database with
  the model; if any are missing, startup fails with a message pointing at
  [migrations.md](../../migrations.md) instead of failing on every request.
