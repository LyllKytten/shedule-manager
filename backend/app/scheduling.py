"""Scheduling logic ported from the Telegram bot (python/utils.py, python/database.py)."""

import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Event

TIME_FMT = "%H:%M"

# How many days ahead an infinite series is materialized on creation.
INFINITE_INITIAL_HORIZON_DAYS = 90
# Extra margin when auto-extending, so we don't extend on every request.
INFINITE_EXTEND_BUFFER_DAYS = 30


def parse_time(s: str) -> datetime:
    return datetime.strptime(s.strip(), TIME_FMT)


def end_time(start_time: str, duration_minutes: int) -> str:
    return (parse_time(start_time) + timedelta(minutes=duration_minutes)).strftime(TIME_FMT)


def compute_free_slots(events, day_start: str, day_end: str, travel_time_minutes: int):
    """
    events: iterable of objects/dicts with start_time (HH:MM), duration_minutes and
    needs_travel_time. After an event with needs_travel_time, `travel_time_minutes`
    is reserved before time counts as free again. If day_end <= day_start the
    working day is treated as crossing midnight.
    Returns a list of (start, end) HH:MM tuples within [day_start, day_end].
    """
    day_start_dt = parse_time(day_start)
    day_end_dt = parse_time(day_end)
    if day_end_dt <= day_start_dt:
        day_end_dt += timedelta(days=1)

    busy = []
    for e in events:
        get = e.get if isinstance(e, dict) else lambda k, d=None, _e=e: getattr(_e, k, d)
        start = parse_time(get("start_time"))
        end = start + timedelta(minutes=get("duration_minutes"))
        if get("needs_travel_time", True):
            end += timedelta(minutes=travel_time_minutes)
        busy.append((start, end))

    busy.sort()
    merged = []
    for start, end in busy:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))

    free = []
    cursor = day_start_dt
    for start, end in merged:
        start = max(start, day_start_dt)
        end = min(end, day_end_dt)
        if start > cursor:
            free.append((cursor, min(start, day_end_dt)))
        cursor = max(cursor, end)
    if cursor < day_end_dt:
        free.append((cursor, day_end_dt))

    return [(s.strftime(TIME_FMT), e.strftime(TIME_FMT)) for s, e in free if e > s]


def _new_event(user_id: int, template: dict, occ_date: date, series_id, infinite: bool) -> Event:
    return Event(
        user_id=user_id,
        title=template["title"],
        date=occ_date,
        start_time=template["start_time"],
        duration_minutes=template["duration_minutes"],
        needs_travel_time=template["needs_travel_time"],
        series_id=series_id,
        repeat_type=template.get("repeat_type"),
        repeat_interval_days=template.get("repeat_interval_days"),
        series_infinite=infinite,
    )


def create_events(db: Session, user_id: int, data: dict) -> list[Event]:
    """
    Creates a single event, a finite series (`occurrences` > 1) or an infinite
    series (repeat_type set and occurrences is None). Occurrences of a series
    share a series_id.
    """
    repeat_type = data.get("repeat_type")
    interval = {"daily": 1, "weekly": 7}.get(repeat_type) or data.get("repeat_interval_days") or 1
    data = {**data, "repeat_interval_days": interval if repeat_type else None}
    occurrences = data.get("occurrences")
    start: date = data["date"]

    if not repeat_type:
        events = [_new_event(user_id, data, start, None, False)]
    elif occurrences is None:
        series_id = uuid.uuid4().hex
        until = start + timedelta(days=INFINITE_INITIAL_HORIZON_DAYS)
        events, cur = [], start
        while cur <= until:
            events.append(_new_event(user_id, data, cur, series_id, True))
            cur += timedelta(days=interval)
    else:
        series_id = uuid.uuid4().hex if occurrences > 1 else None
        events = [
            _new_event(user_id, data, start + timedelta(days=interval * i), series_id, False)
            for i in range(occurrences)
        ]

    db.add_all(events)
    db.commit()
    return events


def extend_series_if_needed(
    db: Session, user_id: int, until: date, buffer_days: int = INFINITE_EXTEND_BUFFER_DAYS
) -> None:
    """Materializes further occurrences of infinite series so `until` is covered."""
    rows = db.execute(
        select(Event.series_id, func.max(Event.date))
        .where(Event.user_id == user_id, Event.series_infinite.is_(True))
        .group_by(Event.series_id)
    ).all()

    added = False
    for series_id, last_date in rows:
        if last_date is None or last_date >= until:
            continue
        tpl = db.scalars(
            select(Event).where(
                Event.user_id == user_id, Event.series_id == series_id, Event.date == last_date
            ).limit(1)
        ).first()
        if tpl is None:
            continue
        template = {
            "title": tpl.title,
            "start_time": tpl.start_time,
            "duration_minutes": tpl.duration_minutes,
            "needs_travel_time": tpl.needs_travel_time,
            "repeat_type": tpl.repeat_type,
            "repeat_interval_days": tpl.repeat_interval_days,
        }
        interval = tpl.repeat_interval_days or 1
        target = until + timedelta(days=buffer_days)
        cur = last_date
        while cur < target:
            cur += timedelta(days=interval)
            db.add(_new_event(user_id, template, cur, series_id, True))
            added = True
    if added:
        db.commit()
