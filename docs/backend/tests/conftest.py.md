# `backend/tests/conftest.py`

Pytest bootstrap. Sets environment variables **before** `app` is imported
(the engine and cached settings are created at import time):

- `DATABASE_URL` → `TEST_DATABASE_URL` if set, otherwise a fresh SQLite file in
  a temp dir (so tests need no PostgreSQL by default);
- `SUPERUSER_USERNAME=harak1r1`, `SUPERUSER_PASSWORD=test-superuser-pass`, so
  startup bootstrapping is exercised;
- `JWT_SECRET=test-secret`.

The session-wide `_clean_database` fixture drops all tables before and after
the run, so every run starts from an empty schema.

Run against PostgreSQL:

```bash
TEST_DATABASE_URL=postgresql+psycopg://schedule:schedule@localhost:5432/schedule_test pytest
```

**Warning:** this drops all tables in that database. As a safety net the run
aborts unless the database name contains `test`. Create one once with:

```bash
sudo -u postgres psql -c "CREATE DATABASE schedule_test OWNER schedule;"
```
