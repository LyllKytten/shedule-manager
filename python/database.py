import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta

import config

DB_PATH = config.DB_PATH
DATE_FMT = "%Y-%m-%d"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _column_exists(conn, table, column):
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                date TEXT NOT NULL,               -- YYYY-MM-DD
                start_time TEXT NOT NULL,         -- HH:MM
                duration_minutes INTEGER NOT NULL,
                needs_travel_time INTEGER NOT NULL DEFAULT 1,  -- добавлять ли время на дорогу после события
                series_id TEXT,                   -- группирует повторяющиеся события
                repeat_type TEXT,                 -- daily / weekly / custom / NULL
                repeat_interval_days INTEGER,      -- шаг повторения в днях
                series_infinite INTEGER NOT NULL DEFAULT 0,  -- 1 = серия без конца, подгружается по мере надобности
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                user_id INTEGER PRIMARY KEY,
                travel_time_minutes INTEGER NOT NULL DEFAULT 30,
                day_start TEXT NOT NULL DEFAULT '08:00',
                day_end TEXT NOT NULL DEFAULT '23:00',
                is_authorized INTEGER NOT NULL DEFAULT 0
            )
            """
        )

        # Миграция для баз, созданных предыдущей версией бота
        migrations = [
            ("events", "needs_travel_time", "INTEGER NOT NULL DEFAULT 1"),
            ("events", "series_id", "TEXT"),
            ("events", "repeat_type", "TEXT"),
            ("events", "repeat_interval_days", "INTEGER"),
            ("events", "series_infinite", "INTEGER NOT NULL DEFAULT 0"),
            ("settings", "is_authorized", "INTEGER NOT NULL DEFAULT 0"),
        ]
        for table, col, decl in migrations:
            if not _column_exists(conn, table, col):
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {decl}")


def ensure_user(user_id):
    with get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO settings (user_id) VALUES (?)", (user_id,))


# ---------- авторизация ----------

def is_authorized(user_id):
    ensure_user(user_id)
    with get_connection() as conn:
        row = conn.execute(
            "SELECT is_authorized FROM settings WHERE user_id=?", (user_id,)
        ).fetchone()
        return bool(row and row["is_authorized"])


def set_authorized(user_id, value: bool):
    ensure_user(user_id)
    with get_connection() as conn:
        conn.execute(
            "UPDATE settings SET is_authorized=? WHERE user_id=?", (1 if value else 0, user_id)
        )


# ---------- события ----------

def add_event(
    user_id,
    title,
    date,
    start_time,
    duration_minutes,
    needs_travel_time=1,
    series_id=None,
    repeat_type=None,
    repeat_interval_days=None,
):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO events
               (user_id, title, date, start_time, duration_minutes,
                needs_travel_time, series_id, repeat_type, repeat_interval_days, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                title,
                date,
                start_time,
                duration_minutes,
                1 if needs_travel_time else 0,
                series_id,
                repeat_type,
                repeat_interval_days,
                datetime.now().isoformat(),
            ),
        )
        return cur.lastrowid


def add_recurring_event(
    user_id,
    title,
    date,
    start_time,
    duration_minutes,
    needs_travel_time,
    repeat_type,
    interval_days,
    occurrences,
):
    """
    Создаёт `occurrences` событий начиная с `date`, каждое следующее — через
    `interval_days` дней. Если occurrences > 1, все события связываются общим
    series_id, чтобы их можно было редактировать/удалять как группу.
    """
    series_id = uuid.uuid4().hex if occurrences > 1 else None
    start_date = datetime.strptime(date, DATE_FMT)
    ids = []
    for i in range(occurrences):
        occ_date = (start_date + timedelta(days=interval_days * i)).strftime(DATE_FMT)
        eid = add_event(
            user_id,
            title,
            occ_date,
            start_time,
            duration_minutes,
            needs_travel_time,
            series_id,
            repeat_type,
            interval_days,
        )
        ids.append(eid)
    return ids, series_id


# Сколько дней вперёд материализуем сразу при создании бесконечной серии.
INFINITE_INITIAL_HORIZON_DAYS = 90
# Насколько дальше запрошенной даты подгружаем при автопродлении —
# запас, чтобы не приходилось продлевать на каждый вызов.
INFINITE_EXTEND_BUFFER_DAYS = 30


def add_infinite_series(
    user_id,
    title,
    date,
    start_time,
    duration_minutes,
    needs_travel_time,
    repeat_type,
    interval_days,
    horizon_days=INFINITE_INITIAL_HORIZON_DAYS,
):
    """
    Создаёт бесконечно повторяющуюся серию: сразу материализует события на
    ближайшие `horizon_days` дней и помечает их series_infinite=1. Дальнейшие
    вхождения подгружаются автоматически функцией extend_series_if_needed,
    когда пользователь запрашивает расписание/свободное время на более
    позднюю дату.
    """
    series_id = uuid.uuid4().hex
    start_date = datetime.strptime(date, DATE_FMT)
    until_dt = start_date + timedelta(days=horizon_days)
    with get_connection() as conn:
        cur_date = start_date
        while cur_date <= until_dt:
            conn.execute(
                """INSERT INTO events
                   (user_id, title, date, start_time, duration_minutes,
                    needs_travel_time, series_id, repeat_type, repeat_interval_days,
                    series_infinite, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    user_id,
                    title,
                    cur_date.strftime(DATE_FMT),
                    start_time,
                    duration_minutes,
                    1 if needs_travel_time else 0,
                    series_id,
                    repeat_type,
                    interval_days,
                    1,
                    datetime.now().isoformat(),
                ),
            )
            cur_date += timedelta(days=interval_days)
    return series_id


def extend_series_if_needed(user_id, until_date, buffer_days=INFINITE_EXTEND_BUFFER_DAYS):
    """
    Для каждой бесконечной серии пользователя проверяет, покрыта ли дата
    `until_date` уже созданными событиями; если нет — досоздаёт вхождения
    (по шаблону последнего известного вхождения серии) с запасом в
    `buffer_days` дней, чтобы не продлевать на каждый мелкий запрос.
    """
    until_dt = datetime.strptime(until_date, DATE_FMT)
    with get_connection() as conn:
        series_rows = conn.execute(
            """SELECT series_id, MAX(date) AS last_date
               FROM events WHERE user_id=? AND series_infinite=1
               GROUP BY series_id""",
            (user_id,),
        ).fetchall()

        for row in series_rows:
            series_id = row["series_id"]
            last_date = row["last_date"]
            if last_date is None or datetime.strptime(last_date, DATE_FMT) >= until_dt:
                continue

            template = conn.execute(
                "SELECT * FROM events WHERE user_id=? AND series_id=? AND date=? LIMIT 1",
                (user_id, series_id, last_date),
            ).fetchone()
            if not template:
                continue

            interval = template["repeat_interval_days"] or 1
            target = until_dt + timedelta(days=buffer_days)
            cur_date = datetime.strptime(last_date, DATE_FMT)
            while cur_date < target:
                cur_date += timedelta(days=interval)
                conn.execute(
                    """INSERT INTO events
                       (user_id, title, date, start_time, duration_minutes,
                        needs_travel_time, series_id, repeat_type, repeat_interval_days,
                        series_infinite, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        user_id,
                        template["title"],
                        cur_date.strftime(DATE_FMT),
                        template["start_time"],
                        template["duration_minutes"],
                        template["needs_travel_time"],
                        series_id,
                        template["repeat_type"],
                        interval,
                        1,
                        datetime.now().isoformat(),
                    ),
                )


def get_events(user_id, date=None):
    with get_connection() as conn:
        if date:
            rows = conn.execute(
                "SELECT * FROM events WHERE user_id=? AND date=? ORDER BY start_time",
                (user_id, date),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM events WHERE user_id=? ORDER BY date, start_time",
                (user_id,),
            ).fetchall()
        return [dict(r) for r in rows]


def get_events_range(user_id, start_date, end_date):
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM events WHERE user_id=? AND date>=? AND date<=? ORDER BY date, start_time",
            (user_id, start_date, end_date),
        ).fetchall()
        return [dict(r) for r in rows]


def get_event(event_id, user_id):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM events WHERE id=? AND user_id=?", (event_id, user_id)
        ).fetchone()
        return dict(row) if row else None


def delete_event(event_id, user_id):
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM events WHERE id=? AND user_id=?", (event_id, user_id))
        return cur.rowcount > 0


def delete_series(series_id, user_id):
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM events WHERE series_id=? AND user_id=?", (series_id, user_id)
        )
        return cur.rowcount


def update_event(event_id, user_id, **fields):
    allowed = {"title", "date", "start_time", "duration_minutes", "needs_travel_time"}
    sets, values = [], []
    for k, v in fields.items():
        if k in allowed:
            sets.append(f"{k}=?")
            values.append(v)
    if not sets:
        return False
    values.extend([event_id, user_id])
    with get_connection() as conn:
        cur = conn.execute(
            f"UPDATE events SET {', '.join(sets)} WHERE id=? AND user_id=?", values
        )
        return cur.rowcount > 0


# ---------- настройки ----------

def get_settings(user_id):
    ensure_user(user_id)
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM settings WHERE user_id=?", (user_id,)).fetchone()
        return dict(row)


def set_travel_time(user_id, minutes):
    ensure_user(user_id)
    with get_connection() as conn:
        conn.execute(
            "UPDATE settings SET travel_time_minutes=? WHERE user_id=?", (minutes, user_id)
        )


def set_working_hours(user_id, day_start, day_end):
    ensure_user(user_id)
    with get_connection() as conn:
        conn.execute(
            "UPDATE settings SET day_start=?, day_end=? WHERE user_id=?",
            (day_start, day_end, user_id),
        )
