# `backend/app/models.py`

ORM models (SQLAlchemy 2 typed `Mapped[...]` style). Full column reference:
[database.md](../../database.md).

- **`User`** — account. Relationships: `settings` (one-to-one) and `events`
  (one-to-many), both `cascade="all, delete-orphan"`, so deleting a user
  deletes their settings and events.
- **`UserSettings`** — per-user `travel_time_minutes`, `day_start`, `day_end`
  (`HH:MM` strings, same as in the bot).
- **`Event`** — one occurrence. Recurring events share `series_id`;
  `series_infinite` marks series that are extended on read. The repeat pattern
  is stored on every row (`repeat_type`, `repeat_interval_days`,
  `repeat_days_on/off`, `series_start`). `needs_travel_time` defaults to `False`.

Adding a column here requires a migration for existing databases — see
[migrations.md](../../migrations.md).

Times are stored as `HH:MM` strings rather than `TIME` to keep the free-slot
algorithm identical to the bot's.
