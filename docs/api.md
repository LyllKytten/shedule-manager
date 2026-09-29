# Backend REST API

Base URL: `http://localhost:8000` by default. Interactive docs (Swagger UI) are
served at **`/docs`**, the OpenAPI schema at `/openapi.json`.

All endpoints except `/health`, `/auth/login` and `/auth/register` need
`Authorization: Bearer <token>`.

Dates are `YYYY-MM-DD`, times are `HH:MM` (24h). Errors look like
`{"detail": "message"}` (or a list of validation errors with HTTP 422).

## Auth

| Method | Path | Body | Response |
|---|---|---|---|
| POST | `/auth/register` | `{"username", "password"}` (password ≥ 8) | `201` user; `403` if `ALLOW_REGISTRATION=false`; `409` if taken |
| POST | `/auth/login` | **form-urlencoded** `username`, `password` | `{"access_token", "token_type": "bearer"}` |
| GET | `/auth/me` | — | current user |
| POST | `/auth/change-password` | `{"old_password", "new_password"}` | `204` |

User object: `{"id", "username", "is_active", "is_superuser", "created_at"}`.

## Events

| Method | Path | Query / Body | Response |
|---|---|---|---|
| GET | `/events` | `start` (default today), `end` (default = start) | list of events, ordered by date, time |
| GET | `/events/week` | `start` (default today) | events for `start` … `start+6` |
| GET | `/events/free` | `day` (default today) | `{"date", "slots": [{"start", "end"}]}` |
| GET | `/events/free/week` | `start` (default today) | 7 items `{"date", "slots"}`, one per day, empty days included |
| POST | `/events` | see below | `201` list of created occurrences |
| GET | `/events/{id}` | — | event |
| PATCH | `/events/{id}` | any of `title`, `date`, `start_time`, `duration_minutes`, `needs_travel_time` | event (only this occurrence changes) |
| DELETE | `/events/{id}` | — | `204` |
| DELETE | `/events/series/{series_id}` | — | `{"deleted": n}` |

Read endpoints auto-extend infinite series up to the requested date.

### Create body

```json
{
  "title": "Gym",
  "date": "2026-10-01",
  "start_time": "18:00",
  "duration_minutes": 90,
  "needs_travel_time": true,
  "repeat_type": "weekly",          // null | "daily" | "weekly" | "custom"
  "repeat_interval_days": null,     // required when repeat_type = "custom"
  "occurrences": 8                  // incl. the first; null = infinite (needs repeat_type)
}
```

Event object:

```json
{
  "id": 1, "title": "Gym", "date": "2026-10-01",
  "start_time": "18:00", "end_time": "19:30", "duration_minutes": 90,
  "needs_travel_time": true, "series_id": "9f…", "repeat_type": "weekly",
  "repeat_interval_days": 7, "series_infinite": false
}
```

## Settings

| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/settings` | — | `{"travel_time_minutes", "day_start", "day_end"}` |
| PATCH | `/settings` | any of the three fields | updated settings |

## Admin (superuser only, otherwise `403`)

| Method | Path | Body | Response |
|---|---|---|---|
| GET | `/admin/users` | — | list of users |
| POST | `/admin/users` | `{"username", "password", "is_superuser"}` | `201` user |
| PATCH | `/admin/users/{id}` | `{"is_active"?, "is_superuser"?}` | user (not allowed on yourself) |
| DELETE | `/admin/users/{id}` | — | `204` (not allowed on yourself; deletes their events) |

## Meta

`GET /health` → `{"status": "ok"}`

## curl example

```bash
TOKEN=$(curl -s -X POST localhost:8000/auth/login \
  -d 'username=harak1r1&password=YOUR_PASSWORD' | jq -r .access_token)

curl -s localhost:8000/events/free?day=2026-10-01 -H "Authorization: Bearer $TOKEN"
```
