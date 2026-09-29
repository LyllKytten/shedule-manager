# `backend/app/routers/settings.py`

Prefix `/settings`, tag `settings`.

| Endpoint | Description |
|---|---|
| `GET ""` | The current user's travel time and working hours. |
| `PATCH ""` | Partial update. `day_end` earlier than `day_start` is valid and means the day ends after midnight. |

Equivalent to the bot's `/settings`, `/travel_time` and `/working_hours`.
