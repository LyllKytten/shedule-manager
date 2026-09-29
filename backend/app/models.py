from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    settings: Mapped["UserSettings"] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    events: Mapped[list["Event"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    travel_time_minutes: Mapped[int] = mapped_column(Integer, default=30)
    day_start: Mapped[str] = mapped_column(String(5), default="08:00")  # HH:MM
    day_end: Mapped[str] = mapped_column(String(5), default="23:00")  # HH:MM

    user: Mapped[User] = relationship(back_populates="settings")


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(255))
    date: Mapped[date] = mapped_column(Date, index=True)
    start_time: Mapped[str] = mapped_column(String(5))  # HH:MM
    duration_minutes: Mapped[int] = mapped_column(Integer)
    needs_travel_time: Mapped[bool] = mapped_column(Boolean, default=False)
    series_id: Mapped[str | None] = mapped_column(String(32), index=True, nullable=True)
    repeat_type: Mapped[str | None] = mapped_column(String(16), nullable=True)
    repeat_interval_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Shift cycle (repeat_type "cycle"): N days with the event, then M days without.
    repeat_days_on: Mapped[int | None] = mapped_column(Integer, nullable=True)
    repeat_days_off: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # First day of the series; the anchor the repeat pattern is counted from.
    series_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    series_infinite: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    user: Mapped[User] = relationship(back_populates="events")
