from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Event, User
from app.schemas import EventCreate, EventOut, EventUpdate, FreeSlot, FreeSlotsOut
from app.scheduling import compute_free_slots, create_events, end_time, extend_series_if_needed

router = APIRouter(prefix="/events", tags=["events"])


def _out(e: Event) -> EventOut:
    return EventOut(
        id=e.id,
        title=e.title,
        date=e.date,
        start_time=e.start_time,
        end_time=end_time(e.start_time, e.duration_minutes),
        duration_minutes=e.duration_minutes,
        needs_travel_time=e.needs_travel_time,
        series_id=e.series_id,
        repeat_type=e.repeat_type,
        repeat_interval_days=e.repeat_interval_days,
        series_infinite=e.series_infinite,
    )


def _get_own(db: Session, user: User, event_id: int) -> Event:
    event = db.get(Event, event_id)
    if event is None or event.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Event not found")
    return event


@router.get("", response_model=list[EventOut])
def list_events(
    start: date | None = Query(None, description="Inclusive start date (default: today)"),
    end: date | None = Query(None, description="Inclusive end date (default: start)"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start = start or date.today()
    end = end or start
    if end < start:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "end must be >= start")
    extend_series_if_needed(db, user.id, end)
    rows = db.scalars(
        select(Event)
        .where(Event.user_id == user.id, Event.date >= start, Event.date <= end)
        .order_by(Event.date, Event.start_time)
    ).all()
    return [_out(e) for e in rows]


@router.get("/week", response_model=list[EventOut])
def week(
    start: date | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start = start or date.today()
    return list_events(start, start + timedelta(days=6), user, db)


@router.get("/free", response_model=FreeSlotsOut)
def free_slots(
    day: date | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    day = day or date.today()
    return _free_for_range(db, user, day, day)[0]


@router.get("/free/week", response_model=list[FreeSlotsOut])
def free_week(
    start: date | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    start = start or date.today()
    return _free_for_range(db, user, start, start + timedelta(days=6))


def _free_for_range(db: Session, user: User, start: date, end: date) -> list[FreeSlotsOut]:
    """Free slots for every day in [start, end], loading all events with one query."""
    extend_series_if_needed(db, user.id, end)
    events = db.scalars(
        select(Event).where(Event.user_id == user.id, Event.date >= start, Event.date <= end)
    ).all()
    by_day: dict[date, list[Event]] = {}
    for e in events:
        by_day.setdefault(e.date, []).append(e)

    s = user.settings
    result = []
    for i in range((end - start).days + 1):
        day = start + timedelta(days=i)
        slots = compute_free_slots(by_day.get(day, []), s.day_start, s.day_end, s.travel_time_minutes)
        result.append(FreeSlotsOut(date=day, slots=[FreeSlot(start=a, end=b) for a, b in slots]))
    return result


@router.post("", response_model=list[EventOut], status_code=status.HTTP_201_CREATED)
def create(body: EventCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.repeat_type == "custom" and not body.repeat_interval_days:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "repeat_interval_days required for custom")
    if body.repeat_type is None and body.occurrences is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "infinite series requires repeat_type")
    return [_out(e) for e in create_events(db, user.id, body.model_dump())]


@router.get("/{event_id}", response_model=EventOut)
def get(event_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _out(_get_own(db, user, event_id))


@router.patch("/{event_id}", response_model=EventOut)
def update(
    event_id: int,
    body: EventUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    event = _get_own(db, user, event_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(event, field, value)
    db.commit()
    return _out(event)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_one(event_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.delete(_get_own(db, user, event_id))
    db.commit()


@router.delete("/series/{series_id}")
def delete_series(series_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = db.execute(
        delete(Event).where(Event.user_id == user.id, Event.series_id == series_id)
    )
    db.commit()
    if result.rowcount == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Series not found")
    return {"deleted": result.rowcount}
