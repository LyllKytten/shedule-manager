# `backend/scripts/create_superuser.py`

Interactive CLI to create or reset a superuser without putting the password in
any file.

```bash
cd backend
python -m scripts.create_superuser                  # username from SUPERUSER_USERNAME (harak1r1)
python -m scripts.create_superuser --username alice
docker compose exec api python -m scripts.create_superuser
```

Prompts twice for the password (hidden, min. 8 chars). If the user exists, its
password is replaced and it is set active + superuser; otherwise it is created.
Runs `init_db()` first so it also works on an empty database.
