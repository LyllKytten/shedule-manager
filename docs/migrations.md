# Database migrations

The backend creates missing **tables** on startup, but never changes existing
ones. Schema changes to an existing database ship as numbered SQL files in
[`backend/migrations/`](../backend/migrations) and are applied by hand, in order.

If the backend starts on a database that is missing columns it needs, it
refuses to start with:

```
RuntimeError: Database schema is outdated: table 'events' lacks [...]
Apply the SQL files in backend/migrations/ (see docs/migrations.md).
```

A **fresh** database (first start) needs no migrations — it is created complete.

| File | What it does | Rollback |
|---|---|---|
| `001_repeat_patterns.sql` | Adds `events.repeat_days_on`, `repeat_days_off`, `series_start` (nullable) and fills `series_start` for existing series | `001_repeat_patterns.rollback.sql` |

All migrations are additive and idempotent (safe to run twice) and run inside a
transaction: either everything is applied or nothing.

## Applying on the server (Docker) — safe procedure

Run in `~/shedule-manager/backend` on the VM.

**1. Backup first**

```bash
sudo docker compose exec -T db pg_dump -U schedule schedule > ~/backup-before-001.sql
ls -lh ~/backup-before-001.sql        # must not be 0 bytes
```

**2. Get the new code** (don't rebuild yet)

```bash
cd ~/shedule-manager && git pull && cd backend
```

**3. Apply the migration** — the old backend keeps running; it ignores new columns

```bash
sudo docker compose exec -T db psql -U schedule -d schedule -v ON_ERROR_STOP=1 \
  < migrations/001_repeat_patterns.sql
```

Expected output: `BEGIN`, three `ALTER TABLE`, `UPDATE <n>`, `COMMIT`.
Any `ERROR` means nothing was changed (transaction rolled back) — stop and check.

**4. Verify**

```bash
sudo docker compose exec db psql -U schedule -d schedule -c '\d events'
```

`repeat_days_on`, `repeat_days_off` and `series_start` must be listed.

**5. Deploy the new backend**

```bash
sudo docker compose up -d --build
sudo docker compose logs api | tail -5     # "Application startup complete"
```

## If something goes wrong

- **Step 3 printed an ERROR:** nothing changed; the old backend still works.
- **New backend misbehaves:** go back to the previous code
  (`git checkout <previous-commit> && sudo docker compose up -d --build`) — the
  old version works with the new columns present, no rollback SQL needed.
- **Full restore from backup** (loses changes made after the backup):

  ```bash
  sudo docker compose stop api
  sudo docker compose exec -T db psql -U schedule -d postgres \
    -c "DROP DATABASE schedule WITH (FORCE)" -c "CREATE DATABASE schedule OWNER schedule"
  sudo docker compose exec -T db psql -U schedule -d schedule < ~/backup-before-001.sql
  sudo docker compose start api
  ```

## Local database (no Docker)

```bash
cd backend
PGPASSWORD=schedule psql -h localhost -U schedule -d schedule -v ON_ERROR_STOP=1 \
  -f migrations/001_repeat_patterns.sql
```

## Writing a new migration

1. Change the model in `app/models.py`.
2. Add `backend/migrations/00N_<name>.sql`: `BEGIN; … COMMIT;`, use
   `IF NOT EXISTS` / `IF EXISTS`, prefer nullable columns or ones with defaults,
   never drop or rename in the same release that stops using a column.
3. Add a `.rollback.sql` and a doc in `docs/backend/migrations/`.
4. Rehearse on a copy (throwaway schema or `schedule_test`) before production.
