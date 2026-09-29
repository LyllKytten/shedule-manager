from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a session and closes it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Import models so they are registered on Base.metadata before create_all.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _check_schema()


def _check_schema():
    """
    create_all() never adds columns to existing tables. If the database was created
    by an older version, refuse to start and point at the migration to run.
    """
    from sqlalchemy import inspect

    existing = {c["name"] for c in inspect(engine).get_columns("events")}
    missing = {c.name for c in Base.metadata.tables["events"].columns} - existing
    if missing:
        raise RuntimeError(
            f"Database schema is outdated: table 'events' lacks {sorted(missing)}. "
            "Apply the SQL files in backend/migrations/ (see docs/migrations.md)."
        )
