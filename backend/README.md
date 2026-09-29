# Schedule Manager — Backend

FastAPI + SQLAlchemy + PostgreSQL REST API with JWT accounts.

```bash
cp .env.example .env          # set JWT_SECRET, SUPERUSER_PASSWORD
docker compose up -d --build  # API on :8000, Swagger UI on /docs
```

Local: `pip install -r requirements-dev.txt && uvicorn app.main:app --reload`, tests: `pytest`.

Docs: [API](../docs/api.md) · [accounts](../docs/accounts.md) · [database](../docs/database.md) · [per-file docs](../docs/backend/)
