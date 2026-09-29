# `backend/app/routers/events.py`

Prefix `/events`, tag `events`. Every query is scoped to the current user;
another user's event id returns `404` (not `403`), so ids don't leak.

| Endpoint | Description |
|---|---|
| `GET ""` | Events in `[start, end]` (defaults: today, same day). Extends infinite series first. |
| `GET /week` | 7 days from `start`; reuses `list_events`. |
| `GET /free` | Free slots for `day` using the user's settings. |
| `GET /free/week` | Free slots for each of the 7 days from `start` (one list item per day). |
| `POST ""` | Creates one event or a series via `scheduling.create_events`. Validates that `custom` has an interval and that infinite (`occurrences: null`) has a `repeat_type`. |
| `GET /{id}` | One event. |
| `PATCH /{id}` | Partial update of one occurrence. |
| `DELETE /{id}` | Deletes one occurrence. |
| `DELETE /series/{series_id}` | Deletes all occurrences; returns the count, `404` if none. |

Helpers: `_out` converts a model to `EventOut` (adds `end_time`); `_get_own`
loads an event and checks ownership; `_free_for_range` computes free slots for
every day of a date range from a single events query (used by `/free` and
`/free/week`).

Note: `/week`, `/free` and `/series/...` are declared before or don't collide
with `/{event_id}` because `event_id` is an `int` path parameter.
