# `backend/app/config.py`

Typed settings loaded from environment variables and an optional `.env` file
(pydantic-settings; names are case-insensitive, e.g. `JWT_SECRET` → `jwt_secret`).

## `Settings`

| Field | Default | Used by |
|---|---|---|
| `database_url` | local PostgreSQL | [database.py](database.py.md) |
| `jwt_secret`, `jwt_algorithm`, `access_token_expire_minutes` | `change-me…`, `HS256`, 7 days | [security.py](security.py.md) |
| `superuser_username`, `superuser_password` | `harak1r1`, empty | [bootstrap.py](bootstrap.py.md) |
| `allow_registration` | `True` | [routers/auth.py](routers/auth.py.md) |
| `cors_origins` | `*` | [main.py](main.py.md) |

## `get_settings()`

Cached (`lru_cache`) so the environment is read once per process. Tests set env
vars **before** importing the app for that reason (see
[tests/conftest.py](../tests/conftest.py.md)).
