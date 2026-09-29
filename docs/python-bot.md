# Telegram bot (`python/`)

The original project. Full user-facing description (in Russian) is in
[`python/README.md`](../python/README.md).

| File | Role |
|---|---|
| `bot.py` | Command handlers (`/add`, `/schedule`, `/week`, `/free`, `/edit`, `/delete`, `/settings`, …), step-by-step dialogs, password gate |
| `database.py` | SQLite access: events, finite/infinite series, settings, authorization flag |
| `utils.py` | Date/time parsing (`сегодня`, `завтра`, `25.12`, ISO), free-slot calculation |
| `config.py` | `BOT_TOKEN`, `ACCESS_PASSWORD`, `DB_PATH` — all from environment |

Changes made during the restructure:

- The bot token is no longer hardcoded; `BOT_TOKEN` must be set (the bot exits
  with a clear message otherwise).
- `DB_PATH` is configurable so the SQLite file can live in a Docker volume.
