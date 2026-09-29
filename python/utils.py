from datetime import datetime, timedelta

TIME_FMT = "%H:%M"
DATE_FMT = "%Y-%m-%d"


def parse_time(s):
    return datetime.strptime(s.strip(), TIME_FMT)


def parse_date(s):
    s = s.strip().lower()
    today = datetime.now().date()
    if s in ("сегодня", "today"):
        return today.strftime(DATE_FMT)
    if s in ("завтра", "tomorrow"):
        return (today + timedelta(days=1)).strftime(DATE_FMT)
    for fmt in (DATE_FMT, "%d.%m.%Y", "%d.%m"):
        try:
            d = datetime.strptime(s, fmt)
            if fmt == "%d.%m":
                d = d.replace(year=today.year)
            return d.strftime(DATE_FMT)
        except ValueError:
            continue
    raise ValueError("Не удалось распознать дату")


def format_date_human(date_str):
    d = datetime.strptime(date_str, DATE_FMT)
    return d.strftime("%d.%m.%Y")


def compute_free_slots(events, day_start, day_end, travel_time_minutes):
    """
    events: список dict с полями start_time (HH:MM), duration_minutes и,
    опционально, needs_travel_time (0/1, по умолчанию 1). После события, для
    которого needs_travel_time не равен 0, резервируется `travel_time_minutes`
    (время на дорогу), прежде чем время снова считается свободным. Если
    needs_travel_time=0, буфер после этого события не добавляется.
    Возвращает список кортежей (начало, конец) в пределах [day_start, day_end].
    """
    day_start_dt = parse_time(day_start)
    day_end_dt = parse_time(day_end)
    # Рабочий день уходит за полночь (например 06:30–01:00) — сдвигаем конец
    # на следующие сутки, иначе day_end окажется "раньше" day_start.
    if day_end_dt <= day_start_dt:
        day_end_dt += timedelta(days=1)

    busy = []
    for e in events:
        start = parse_time(e["start_time"])
        end = start + timedelta(minutes=e["duration_minutes"])
        needs_travel = e.get("needs_travel_time", 1)
        buffer_minutes = travel_time_minutes if needs_travel else 0
        end_with_travel = end + timedelta(minutes=buffer_minutes)
        busy.append((start, end_with_travel))

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
