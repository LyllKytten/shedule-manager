import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def login(client, username, password):
    r = client.post("/auth/login", data={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_superuser_bootstrapped(client):
    h = login(client, "harak1r1", "test-superuser-pass")
    me = client.get("/auth/me", headers=h).json()
    assert me["username"] == "harak1r1" and me["is_superuser"] is True


def test_register_and_events_flow(client):
    r = client.post("/auth/register", json={"username": "alice", "password": "alicepass1"})
    assert r.status_code == 201
    h = login(client, "alice", "alicepass1")

    r = client.post(
        "/events",
        headers=h,
        json={
            "title": "Gym", "date": "2026-10-01", "start_time": "10:00",
            "duration_minutes": 60, "needs_travel_time": True,
            "repeat_type": "weekly", "occurrences": 3,
        },
    )
    assert r.status_code == 201
    created = r.json()
    assert [e["date"] for e in created] == ["2026-10-01", "2026-10-08", "2026-10-15"]
    assert created[0]["end_time"] == "11:00"

    free = client.get("/events/free", headers=h, params={"day": "2026-10-01"}).json()
    assert free["slots"][0] == {"start": "08:00", "end": "10:00"}
    assert free["slots"][1]["start"] == "11:30"  # 30 min travel buffer

    r = client.delete(f"/events/series/{created[0]['series_id']}", headers=h)
    assert r.json() == {"deleted": 3}


def test_infinite_series_extends(client):
    h = login(client, "alice", "alicepass1")
    r = client.post(
        "/events",
        headers=h,
        json={
            "title": "Standup", "date": "2026-10-01", "start_time": "09:00",
            "duration_minutes": 15, "repeat_type": "daily", "occurrences": None,
        },
    )
    assert r.status_code == 201
    far = client.get("/events", headers=h, params={"start": "2027-06-01"}).json()
    assert len(far) == 1 and far[0]["series_infinite"] is True


def test_admin_only_for_superuser(client):
    h_alice = login(client, "alice", "alicepass1")
    assert client.get("/admin/users", headers=h_alice).status_code == 403
    h_admin = login(client, "harak1r1", "test-superuser-pass")
    users = client.get("/admin/users", headers=h_admin).json()
    assert {u["username"] for u in users} >= {"harak1r1", "alice"}


def test_free_week(client):
    client.post("/auth/register", json={"username": "carol", "password": "carolpass1"})
    h = login(client, "carol", "carolpass1")
    client.post(
        "/events",
        headers=h,
        json={"title": "Work", "date": "2026-10-02", "start_time": "09:00",
              "duration_minutes": 480, "needs_travel_time": False},
    )
    week = client.get("/events/free/week", headers=h, params={"start": "2026-10-01"}).json()
    assert [d["date"] for d in week] == [f"2026-10-0{i}" for i in range(1, 8)]
    assert week[0]["slots"] == [{"start": "08:00", "end": "23:00"}]  # empty day
    assert week[1]["slots"] == [
        {"start": "08:00", "end": "09:00"},
        {"start": "17:00", "end": "23:00"},
    ]


def _create(client, h, **fields):
    body = {"title": "X", "date": "2026-10-01", "start_time": "09:00", "duration_minutes": 30}
    r = client.post("/events", headers=h, json={**body, **fields})
    assert r.status_code == 201, r.text
    return r.json()


def test_travel_time_off_by_default(client):
    h = login(client, "alice", "alicepass1")
    assert _create(client, h)[0]["needs_travel_time"] is False


def test_repeat_weekdays_and_weekends(client):
    h = login(client, "alice", "alicepass1")
    # 2026-10-03 is a Saturday: weekdays start on Monday the 5th and skip the weekend.
    days = [e["date"] for e in _create(client, h, date="2026-10-03", repeat_type="weekdays", occurrences=6)]
    assert days == ["2026-10-05", "2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09", "2026-10-12"]
    # 2026-09-30 is a Wednesday.
    days = [e["date"] for e in _create(client, h, date="2026-09-30", repeat_type="weekends", occurrences=4)]
    assert days == ["2026-10-03", "2026-10-04", "2026-10-10", "2026-10-11"]


def test_repeat_cycle_5_2(client):
    h = login(client, "alice", "alicepass1")
    created = _create(client, h, repeat_type="cycle", repeat_days_on=5, repeat_days_off=2, occurrences=8)
    assert [e["date"][-2:] for e in created] == ["01", "02", "03", "04", "05", "08", "09", "10"]
    assert created[0]["repeat_days_on"] == 5 and created[0]["series_start"] == "2026-10-01"


def test_infinite_cycle_keeps_phase_when_extended(client):
    h = login(client, "alice", "alicepass1")
    _create(client, h, title="Shift", date="2026-10-01", repeat_type="cycle",
            repeat_days_on=3, repeat_days_off=2, occurrences=None)
    # 3:2 has a 5-day period; 2027-06-01 is day 243 -> 243 % 5 = 3 -> day off,
    # 2027-06-03 is day 245 -> 0 -> on.
    def shift_on(day):
        return any(e["title"] == "Shift" for e in client.get("/events", headers=h, params={"start": day}).json())
    assert not shift_on("2027-06-01")
    assert shift_on("2027-06-03")


def test_cycle_requires_days(client):
    h = login(client, "alice", "alicepass1")
    r = client.post("/events", headers=h, json={
        "title": "X", "date": "2026-10-01", "start_time": "09:00", "duration_minutes": 30,
        "repeat_type": "cycle", "repeat_days_on": 5})
    assert r.status_code == 400


def test_events_are_isolated_per_user(client):
    client.post("/auth/register", json={"username": "bob", "password": "bobpass12"})
    h_bob = login(client, "bob", "bobpass12")
    assert client.get("/events", headers=h_bob, params={"start": "2026-10-01"}).json() == []
