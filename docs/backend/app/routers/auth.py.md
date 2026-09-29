# `backend/app/routers/auth.py`

Prefix `/auth`, tag `auth`.

| Endpoint | Description |
|---|---|
| `POST /register` | Creates a normal user. `403` when `ALLOW_REGISTRATION=false`, `409` when the name is taken. |
| `POST /login` | OAuth2 password form (`application/x-www-form-urlencoded`). Returns a JWT. `401` for wrong credentials, `403` for disabled accounts. The error does not reveal whether the username exists. |
| `GET /me` | The current user. |
| `POST /change-password` | Requires the old password. `204` on success. |
