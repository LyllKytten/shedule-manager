# `backend/app/__init__.py`

Empty marker that makes `app` a Python package, so modules import each other as
`from app.models import User` and uvicorn can load `app.main:app`.
