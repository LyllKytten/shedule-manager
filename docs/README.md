# Documentation

| Document | What it covers |
|---|---|
| [architecture.md](architecture.md) | Components, how they talk to each other, request flow, design decisions |
| [database.md](database.md) | PostgreSQL schema (backend) and SQLite schema (Telegram bot) |
| [api.md](api.md) | REST API reference for the backend |
| [accounts.md](accounts.md) | Account system, JWT auth, superuser `harak1r1` |
| [deployment.md](deployment.md) | Running every part with Docker or locally, env variables |
| [flutter.md](flutter.md) | Flutter app structure and screens |
| [python-bot.md](python-bot.md) | The original Telegram bot |
| [git-hooks.md](git-hooks.md) | Repo git hooks (commit-message cleanup) |
| [backend/](backend/) | One doc per backend source file (mirrors `backend/`) |

## Backend file docs

- `app/` — [`__init__.py`](backend/app/__init__.py.md), [`main.py`](backend/app/main.py.md), [`config.py`](backend/app/config.py.md), [`database.py`](backend/app/database.py.md), [`models.py`](backend/app/models.py.md), [`schemas.py`](backend/app/schemas.py.md), [`security.py`](backend/app/security.py.md), [`deps.py`](backend/app/deps.py.md), [`scheduling.py`](backend/app/scheduling.py.md), [`bootstrap.py`](backend/app/bootstrap.py.md)
- `app/routers/` — [`__init__.py`](backend/app/routers/__init__.py.md), [`auth.py`](backend/app/routers/auth.py.md), [`events.py`](backend/app/routers/events.py.md), [`settings.py`](backend/app/routers/settings.py.md), [`admin.py`](backend/app/routers/admin.py.md)
- `scripts/` — [`__init__.py`](backend/scripts/__init__.py.md), [`create_superuser.py`](backend/scripts/create_superuser.py.md)
- `tests/` — [`conftest.py`](backend/tests/conftest.py.md), [`test_scheduling.py`](backend/tests/test_scheduling.py.md), [`test_api.py`](backend/tests/test_api.py.md)
