# `backend/tests/test_scheduling.py`

Unit tests for `app/scheduling.py`, no database involved.

| Test | Checks |
|---|---|
| `test_end_time` | end time arithmetic |
| `test_empty_day_is_fully_free` | no events → whole working day is free |
| `test_travel_buffer_only_when_needed` | travel buffer added only after events with `needs_travel_time` |
| `test_working_day_across_midnight` | `20:00–01:00` working day |
