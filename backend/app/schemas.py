import re
import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _check_time(v: str) -> str:
    if not _TIME_RE.match(v):
        raise ValueError("time must be HH:MM")
    return v


# ---------- auth / users ----------

class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    is_active: bool
    is_superuser: bool
    created_at: dt.datetime


class AdminUserCreate(Credentials):
    is_superuser: bool = False


class AdminUserUpdate(BaseModel):
    is_active: bool | None = None
    is_superuser: bool | None = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)


# ---------- events ----------

class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    date: dt.date
    start_time: str
    duration_minutes: int = Field(gt=0, le=24 * 60)
    needs_travel_time: bool = True
    repeat_type: Literal["daily", "weekly", "custom"] | None = None
    repeat_interval_days: int | None = Field(default=None, gt=0)
    # Number of occurrences including the first one; null + repeat_type = infinite series.
    occurrences: int | None = Field(default=1, gt=0, le=1000)

    _v_time = field_validator("start_time")(_check_time)


class EventUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    date: dt.date | None = None
    start_time: str | None = None
    duration_minutes: int | None = Field(default=None, gt=0, le=24 * 60)
    needs_travel_time: bool | None = None

    @field_validator("start_time")
    @classmethod
    def _v_time(cls, v):
        return None if v is None else _check_time(v)


class EventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    date: dt.date
    start_time: str
    end_time: str
    duration_minutes: int
    needs_travel_time: bool
    series_id: str | None
    repeat_type: str | None
    repeat_interval_days: int | None
    series_infinite: bool


class FreeSlot(BaseModel):
    start: str
    end: str


class FreeSlotsOut(BaseModel):
    date: dt.date
    slots: list[FreeSlot]


# ---------- settings ----------

class SettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    travel_time_minutes: int
    day_start: str
    day_end: str


class SettingsUpdate(BaseModel):
    travel_time_minutes: int | None = Field(default=None, ge=0, le=24 * 60)
    day_start: str | None = None
    day_end: str | None = None

    @field_validator("day_start", "day_end")
    @classmethod
    def _v_time(cls, v):
        return None if v is None else _check_time(v)
