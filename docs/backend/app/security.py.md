# `backend/app/security.py`

Password hashing and JWT handling.

| Function | Description |
|---|---|
| `hash_password(pw)` | bcrypt with a random salt |
| `verify_password(pw, hash)` | constant-time bcrypt check; returns `False` for malformed hashes instead of raising |
| `create_access_token(user_id)` | JWT with `sub` = user id (string) and `exp`, signed with `JWT_SECRET` |
| `decode_access_token(token)` | user id, or `None` if the signature is wrong, the token expired or `sub` is missing |

Uses the `bcrypt` and `PyJWT` packages directly (no passlib).
