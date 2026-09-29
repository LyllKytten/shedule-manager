# Account system

Accounts exist only in the **backend** (used by the Flutter app). The Telegram
bot still uses its single shared password (`ACCESS_PASSWORD`).

## Users

- Stored in the `users` table; passwords are hashed with **bcrypt**.
- Every user gets a `user_settings` row on creation and only ever sees their own
  events (every query filters by `user_id`).
- `is_active = false` blocks login and invalidates existing tokens (checked on
  every request).
- `is_superuser = true` gives access to `/admin/*` and the *Manage users* screen.

## Tokens

`POST /auth/login` returns a JWT (HS256) with `sub = user id` and `exp`.
Lifetime: `ACCESS_TOKEN_EXPIRE_MINUTES` (default 7 days). Signing key:
`JWT_SECRET` — **must** be changed in production:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

The Flutter app stores the token in `shared_preferences` and drops it on any 401.

## Superuser `harak1r1`

The superuser is configured through environment variables in `backend/.env`:

```env
SUPERUSER_USERNAME=harak1r1
SUPERUSER_PASSWORD=          # <- fill in yourself
```

On every startup the backend checks whether a user named `SUPERUSER_USERNAME`
exists. If not:

- `SUPERUSER_PASSWORD` set → the superuser is created;
- `SUPERUSER_PASSWORD` empty → nothing is created and a warning is logged.

Changing `SUPERUSER_PASSWORD` later does **not** change an existing account's
password. Use the app (*Settings → Change password*) or the script below.

### Creating / resetting it manually

```bash
# local
cd backend && python -m scripts.create_superuser            # prompts for password
# docker
docker compose exec api python -m scripts.create_superuser
```

The script creates the user, or — if it already exists — resets its password
and makes it an active superuser. `--username other` works for any name.

## Registration

`ALLOW_REGISTRATION=true` (default) lets anyone create a normal account via
`/auth/register`. Set it to `false` for a private instance; then only a
superuser can add accounts (`POST /admin/users` / *Manage users*).

## Admin safety rules

A superuser cannot disable, demote or delete **their own** account through the
admin API, so the instance can't be locked out by accident.
