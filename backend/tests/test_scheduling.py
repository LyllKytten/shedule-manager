from app.scheduling import compute_free_slots, end_time


def ev(start, dur, travel=True):
    return {"start_time": start, "duration_minutes": dur, "needs_travel_time": travel}


def test_end_time():
    assert end_time("09:30", 90) == "11:00"


def test_empty_day_is_fully_free():
    assert compute_free_slots([], "08:00", "23:00", 30) == [("08:00", "23:00")]


def test_travel_buffer_only_when_needed():
    events = [ev("10:00", 60, travel=True), ev("14:00", 60, travel=False)]
    assert compute_free_slots(events, "08:00", "18:00", 30) == [
        ("08:00", "10:00"),
        ("11:30", "14:00"),
        ("15:00", "18:00"),
    ]


def test_working_day_across_midnight():
    assert compute_free_slots([ev("22:00", 60, False)], "20:00", "01:00", 0) == [
        ("20:00", "22:00"),
        ("23:00", "01:00"),
    ]
