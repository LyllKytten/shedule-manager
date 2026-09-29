# Schedule Manager

Personal schedule manager with travel-time-aware free-slot calculation,
recurring (including infinite) events and working days that may cross midnight.

It comes in two flavours that share the same scheduling rules:

- a **Telegram bot** (the original project), and
- a **Flutter app** (Android / iOS / Web / Linux) backed by a **REST API** with
  real user accounts and PostgreSQL.

## Repository layout

| Folder | Stack | Description |
|---|---|---|
| [`python/`](python/) | Python, pyTelegramBotAPI, SQLite | Telegram bot |
| [`backend/`](backend/) | Python, FastAPI, SQLAlchemy, PostgreSQL, JWT | API for the Flutter app, account system |
| [`flutter/`](flutter/) | Flutter / Dart, Material 3 | Graphical client |
| [`docs/`](docs/) | Markdown | Architecture, API, database, deployment, per-file backend docs |

Each of `python/`, `backend/` and `flutter/` has its own `Dockerfile`,
`docker-compose.yml` and `.env.example` and can be deployed independently.

## Features

- Events with title, date, start time, duration and a per-event
  **"travel time after"** flag.
- **Free time** for a day: gaps in the working day, with the travel buffer
  added only after events that need it.
- **Repeats**: daily, weekly, every N days, work days (Mon–Fri), weekends or
  shift cycles like 5:2 / 3:2; 4 / 8 / 12 / custom times or
  **forever** (materialized 90 days ahead, auto-extended when you look further).
- Edit one occurrence; delete one occurrence or the whole series.
- Day and week views; the week shows either your plans or the free time of
  each day. Per-user travel time and working hours.
- **Accounts** (backend/app): registration, login, password change, superuser
  admin panel for managing users.

## Quick start (Docker)

```bash
# 1. Backend + PostgreSQL  → http://localhost:8000  (Swagger: /docs)
cd backend && cp .env.example .env    # set JWT_SECRET and SUPERUSER_PASSWORD
docker compose up -d --build

# 2. Flutter web app       → http://localhost:8080
cd ../flutter && API_URL=http://localhost:8000 docker compose up -d --build

# 3. Telegram bot (optional, independent)
cd ../python && cp .env.example .env  # set BOT_TOKEN and ACCESS_PASSWORD
docker compose up -d --build
```

Local development without Docker is described in
[docs/deployment.md](docs/deployment.md).

## Superuser

The backend creates the superuser **`harak1r1`** on startup once
`SUPERUSER_PASSWORD` is set in `backend/.env` (it's intentionally left empty in
`.env.example`). Alternatively:

```bash
cd backend && python -m scripts.create_superuser
```

Details: [docs/accounts.md](docs/accounts.md).

## Tests

```bash
cd backend && pip install -r requirements-dev.txt && pytest
cd flutter && flutter analyze && flutter test
```

## Git hooks

```bash
git config core.hooksPath .githooks
```

Enables the `commit-msg` hook that strips AI-tool attribution lines from commit
messages — see [docs/git-hooks.md](docs/git-hooks.md).

## Documentation

Start at [docs/README.md](docs/README.md):
[architecture](docs/architecture.md) ·
[API](docs/api.md) ·
[database](docs/database.md) ·
[accounts](docs/accounts.md) ·
[deployment](docs/deployment.md) ·
[Flutter app](docs/flutter.md) ·
[Telegram bot](docs/python-bot.md) ·
[backend file docs](docs/backend/)
