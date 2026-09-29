import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import User, UserSettings
from app.security import hash_password

log = logging.getLogger(__name__)


def create_user(db: Session, username: str, password: str, is_superuser: bool = False) -> User:
    user = User(
        username=username,
        password_hash=hash_password(password),
        is_superuser=is_superuser,
        settings=UserSettings(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def ensure_superuser(db: Session) -> None:
    """Creates the configured superuser on startup if it doesn't exist yet."""
    s = get_settings()
    if db.scalar(select(User).where(User.username == s.superuser_username)):
        return
    if not s.superuser_password:
        log.warning(
            "SUPERUSER_PASSWORD is empty - superuser '%s' was not created. "
            "Set it in .env or run: python -m scripts.create_superuser",
            s.superuser_username,
        )
        return
    create_user(db, s.superuser_username, s.superuser_password, is_superuser=True)
    log.info("Superuser '%s' created", s.superuser_username)
