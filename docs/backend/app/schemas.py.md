# `backend/app/schemas.py`

Pydantic models for request validation and response shapes.

`datetime` is imported as `dt` on purpose: several models have a field named
`date`, which would otherwise shadow the `date` type inside the class body.

| Schema | Direction | Notes |
|---|---|---|
| `Credentials` | in | username `[A-Za-z0-9_.-]{3,64}`, password 8–128 |
| `Token` | out | `access_token`, `token_type="bearer"` |
| `UserOut` | out | never includes the password hash |
| `AdminUserCreate` / `AdminUserUpdate` | in | admin endpoints |
| `PasswordChange` | in | |
| `EventCreate` | in | `start_time` validated as `HH:MM`; `duration_minutes` 1–1440; `occurrences` 1–1000 or `null` for infinite; `needs_travel_time` default `false`; `repeat_type` incl. `weekdays` / `weekends` / `cycle` (+ `repeat_days_on/off` 1–365) |
| `EventUpdate` | in | all fields optional (partial update) |
| `EventOut` | out | adds computed `end_time`; includes `repeat_days_on/off`, `series_start` |
| `FreeSlot` / `FreeSlotsOut` | out | |
| `SettingsOut` / `SettingsUpdate` | out / in | travel time 0–1440, times `HH:MM` |

`_check_time` is the shared `HH:MM` validator (00:00–23:59).
