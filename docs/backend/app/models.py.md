# `backend/app/models.py`

ORM models (SQLAlchemy 2 typed `Mapped[...]` style). Full column reference:
[database.md](../../database.md).

- **`User`** — account. Relationships: `settings` (one-to-one) and `events`
  (one-to-many), both `cascade="all, delete-orphan"`, so deleting a user
  deletes their settings and events.
- **`UserSettings`** — per-user `travel_time_minutes`, `day_start`, `day_end`
  (`HH:MM` strings, same as in the bot).
- **`Event`** — one occurrence. Recurring events share `series_id`;
  `series_infinite` marks series that are extended on read.

Times are stored as `HH:MM` strings rather than `TIME` to keep the free-slot
algorithm identical to the bot's.
