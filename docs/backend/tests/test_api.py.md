# `backend/tests/test_api.py`

End-to-end tests through FastAPI's `TestClient` (runs the lifespan, so tables
and the superuser are created).

| Test | Checks |
|---|---|
| `test_superuser_bootstrapped` | `harak1r1` exists after startup and is a superuser |
| `test_register_and_events_flow` | register → login → weekly series of 3 → free slots with travel buffer → delete series |
| `test_infinite_series_extends` | a daily infinite series has an occurrence ~8 months later (auto-extension) |
| `test_admin_only_for_superuser` | `/admin/users` is `403` for users, works for the superuser |
| `test_travel_time_off_by_default` | events are created without travel buffer unless asked |
| `test_repeat_weekdays_and_weekends` | Mon–Fri skips weekends (start on a Saturday); Sat–Sun |
| `test_repeat_cycle_5_2` | 5:2 cycle dates and stored pattern |
| `test_infinite_cycle_keeps_phase_when_extended` | a 3:2 cycle extended 8 months later is still in phase |
| `test_cycle_requires_days` | `cycle` without both day counts → 400 |
| `test_events_are_isolated_per_user` | a new user sees none of the other users' events |

Run: `cd backend && pytest`.
