# Deployment

Each folder is self-contained: `Dockerfile` + `docker-compose.yml` + `.env.example`.
Commands below are run **inside the respective folder**.

## Backend (API + PostgreSQL)

```bash
cd backend
cp .env.example .env        # set JWT_SECRET, SUPERUSER_PASSWORD, POSTGRES_PASSWORD
docker compose up -d --build
curl localhost:8000/health  # {"status":"ok"}
```

- `db` — `postgres:16-alpine`, data in the `pg-data` volume, healthchecked.
- `api` — starts after `db` is healthy, exposed on **:8000**. `DATABASE_URL` is
  built from the `POSTGRES_*` variables by compose.

### Without Docker

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env        # point DATABASE_URL at your PostgreSQL
uvicorn app.main:app --reload
pytest                      # runs against a temporary SQLite DB
# against PostgreSQL — use a separate DB, all its tables are DROPPED
# (the run refuses DB names without "test"):
TEST_DATABASE_URL=postgresql+psycopg://schedule:schedule@localhost:5432/schedule_test pytest
```

### Local PostgreSQL on Kali

Kali disables PostgreSQL by default. Start it and create the database once:

```bash
sudo systemctl start postgresql@18-main
sudo -u postgres psql -c "CREATE USER schedule WITH PASSWORD 'schedule';" -c "CREATE DATABASE schedule OWNER schedule;"
```

If `CREATE DATABASE` fails with *collation version mismatch* (after a glibc
upgrade), refresh the template first — safe on a cluster without user data:

```bash
sudo -u postgres psql -c "ALTER DATABASE template1 REFRESH COLLATION VERSION;" -c "ALTER DATABASE postgres REFRESH COLLATION VERSION;"
```

### Environment variables

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `postgresql+psycopg://schedule:schedule@localhost:5432/schedule` | SQLAlchemy URL |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | `schedule` | compose only |
| `JWT_SECRET` | `change-me-in-production` | token signing key |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` | token lifetime |
| `SUPERUSER_USERNAME` | `harak1r1` | bootstrapped superuser |
| `SUPERUSER_PASSWORD` | *(empty)* | empty = don't create |
| `ALLOW_REGISTRATION` | `true` | open sign-up |
| `CORS_ORIGINS` | `*` | comma-separated origins |

## Flutter (web build served by nginx)

```bash
cd flutter
API_URL=http://localhost:8000 docker compose up -d --build
# open http://localhost:8080
```

`API_URL` is baked in at build time (`--dart-define`) and must be reachable
**from the browser**, not from the container. The server URL can also be
changed at runtime on the login screen.

### Mobile / desktop builds

```bash
cd flutter
flutter pub get
flutter run --dart-define=API_URL=http://10.0.2.2:8000   # Android emulator → host
flutter build apk --dart-define=API_URL=https://api.example.com
```

## Telegram bot

```bash
cd python
cp .env.example .env        # BOT_TOKEN from @BotFather, ACCESS_PASSWORD
docker compose up -d --build
```

SQLite lives in the `bot-data` volume (`DB_PATH=/data/schedule.db`).
Locally: `pip install -r requirements.txt && BOT_TOKEN=... python bot.py`.

## Running everything together

The three compose files are independent. Start the backend first, then the web
app with `API_URL` pointing at it; the bot is unrelated to both.
