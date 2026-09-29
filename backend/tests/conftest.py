import os
import tempfile

import pytest

# Must be set before `app` is imported: the engine is created at import time.
# TEST_DATABASE_URL runs the suite against a real database (e.g. PostgreSQL).
# WARNING: all tables in that database are dropped before and after the run.
_test_url = os.environ.get("TEST_DATABASE_URL")
if not _test_url:
    _test_url = f"sqlite:///{os.path.join(tempfile.mkdtemp(), 'test.db')}"
else:
    # Safety net: refuse to wipe a database whose name doesn't say it's for tests.
    from sqlalchemy.engine import make_url

    _db_name = make_url(_test_url).database or ""
    if "test" not in _db_name.lower():
        raise pytest.UsageError(
            f"TEST_DATABASE_URL points at database '{_db_name}'. The test run drops all "
            "tables, so the database name must contain 'test' (e.g. schedule_test)."
        )
os.environ["DATABASE_URL"] = _test_url
os.environ["SUPERUSER_USERNAME"] = "harak1r1"
os.environ["SUPERUSER_PASSWORD"] = "test-superuser-pass"
os.environ["JWT_SECRET"] = "test-secret"


@pytest.fixture(scope="session", autouse=True)
def _clean_database():
    from app import models  # noqa: F401
    from app.database import Base, engine

    Base.metadata.drop_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
