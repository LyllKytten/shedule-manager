# `backend/app/scheduling.py`

Domain logic ported from the Telegram bot (`python/utils.py`,
`python/database.py`), independent of HTTP.

## Constants

- `INFINITE_INITIAL_HORIZON_DAYS = 90` — rows created up front for an infinite series.
- `INFINITE_EXTEND_BUFFER_DAYS = 30` — extra margin when extending.

## Functions

### `compute_free_slots(events, day_start, day_end, travel_time_minutes)`
1. Treats `day_end <= day_start` as ending the next day.
2. Builds busy intervals `[start, start + duration (+ travel if needs_travel_time)]`.
3. Sorts and merges overlapping intervals.
4. Returns the gaps inside the working day as `(HH:MM, HH:MM)` tuples.

Accepts both dicts and ORM objects.

### `end_time(start_time, duration_minutes)`
`"09:30", 90 → "11:00"` (wraps past midnight).

### `is_occurrence(day, rule)` / `occurrence_dates(rule, first)`
The single definition of every repeat pattern. `rule` holds `repeat_type`,
`repeat_interval_days`, `repeat_days_on`, `repeat_days_off`, `series_start`:

| repeat_type | occurs when |
|---|---|
| `daily` / `weekly` / `custom` | `(day - series_start) % interval == 0` |
| `weekdays` | Monday–Friday |
| `weekends` | Saturday–Sunday |
| `cycle` | `(day - series_start) % (on + off) < on` |

`occurrence_dates` yields matching days from `first` onwards, forever; callers
stop by count or date.

### `create_events(db, user_id, data)`
- no `repeat_type` → one event;
- `repeat_type` + `occurrences = n` → `n` rows `interval` days apart, shared
  `series_id` (only if `n > 1`);
- `repeat_type` + `occurrences = None` → infinite series, rows for 90 days.

Interval: `daily` = 1, `weekly` = 7, `custom` = `repeat_interval_days`. For
`weekdays` / `weekends` / `cycle` the first occurrence is the first matching
day on or after `date`. `needs_travel_time` defaults to `False`.

### `extend_series_if_needed(db, user_id, until)`
For each infinite series whose last row is before `until`, adds the next
occurrences (same pattern, anchored on `series_start`) until `until + 30 days`.
Series created before migration 001 without `series_start` are anchored on
their last row. Called by every read endpoint. Deleting the
series removes all rows, so nothing is extended any more.
