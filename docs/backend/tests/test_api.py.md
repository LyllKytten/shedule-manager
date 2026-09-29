# `backend/tests/test_api.py`

End-to-end tests through FastAPI's `TestClient` (runs the lifespan, so tables
and the superuser are created).

| Test | Checks |
|---|---|
| `test_superuser_bootstrapped` | `harak1r1` exists after startup and is a superuser |
| `test_register_and_events_flow` | register → login → weekly series of 3 → free slots with travel buffer → delete series |
| `test_infinite_series_extends` | a daily infinite series has an occurrence ~8 months later (auto-extension) |
| `test_admin_only_for_superuser` | `/admin/users` is `403` for users, works for the superuser |
| `test_events_are_isolated_per_user` | a new user sees none of the other users' events |

Run: `cd backend && pytest`.
