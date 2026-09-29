# `backend/app/routers/admin.py`

Prefix `/admin`, tag `admin`. The whole router depends on
`get_current_superuser`, so every endpoint returns `403` for normal users.

| Endpoint | Description |
|---|---|
| `GET /users` | All users ordered by id. |
| `POST /users` | Creates a user (optionally superuser). Works even with registration disabled. |
| `PATCH /users/{id}` | Toggle `is_active` / `is_superuser`. |
| `DELETE /users/{id}` | Deletes the user with their settings and events. |

Self-protection: PATCH and DELETE on your own id return `400`, so the last
superuser can't lock themselves out.
