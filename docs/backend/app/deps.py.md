# `backend/app/deps.py`

Reusable FastAPI dependencies for authentication.

- **`oauth2_scheme`** — reads `Authorization: Bearer <token>`; also makes the
  *Authorize* button in Swagger UI work against `/auth/login`.
- **`get_current_user`** — decodes the token, loads the user, and raises `401`
  if the token is invalid, the user no longer exists or is disabled.
- **`get_current_superuser`** — `get_current_user` + `403` unless
  `is_superuser`. Applied to the whole admin router.
