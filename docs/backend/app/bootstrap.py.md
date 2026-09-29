# `backend/app/bootstrap.py`

User creation helpers shared by the API, startup and the CLI script.

- **`create_user(db, username, password, is_superuser=False)`** — hashes the
  password, creates the user together with a default `UserSettings` row, commits.
- **`ensure_superuser(db)`** — called on startup. If no user named
  `SUPERUSER_USERNAME` (default `harak1r1`) exists and `SUPERUSER_PASSWORD` is
  set, creates it as a superuser. With an empty password it only logs a
  warning. It never modifies an existing user. See [accounts.md](../../accounts.md).
