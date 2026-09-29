# `backend/migrations/001_repeat_patterns.sql`

Adds the columns needed for the *work days*, *weekends* and *shift cycle*
repeat options. How to apply it safely: [migrations.md](../../migrations.md).

| Column | Type | Meaning |
|---|---|---|
| `repeat_days_on` | INTEGER NULL | cycle: days with the event (the `5` in 5:2) |
| `repeat_days_off` | INTEGER NULL | cycle: days without it (the `2` in 5:2) |
| `series_start` | DATE NULL | day the repeat pattern is counted from |

Existing series get `series_start` = their earliest remaining occurrence, which
lies on the same repeat grid, so auto-extension of infinite series continues
unchanged.

Properties: one transaction, `ADD COLUMN IF NOT EXISTS` (re-running only prints
"already exists, skipping" notices), no existing values are modified besides
the `series_start` backfill. Adding nullable columns doesn't rewrite the table
in PostgreSQL, so it's instant regardless of size.
