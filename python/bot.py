from datetime import datetime, timedelta
from functools import wraps

import telebot
from telebot import types

import config
import database as db
import utils

if not config.BOT_TOKEN:
    raise SystemExit("BOT_TOKEN не задан: export BOT_TOKEN=... или впишите в .env")

bot = telebot.TeleBot(config.BOT_TOKEN)
db.init_db()

# Временное состояние мастера /add, ключ — chat_id
pending = {}


def send_error(chat_id, text):
    bot.send_message(chat_id, f"⚠️ {text}")


def events_keyboard(events, prefix):
    markup = types.InlineKeyboardMarkup()
    for e in events:
        icon = "🚗" if e.get("needs_travel_time", 1) else ""
        label = f"{utils.format_date_human(e['date'])} {e['start_time']} — {e['title']} {icon}".strip()
        markup.add(types.InlineKeyboardButton(label, callback_data=f"{prefix}:{e['id']}"))
    return markup


# ============================================================
# Авторизация по паролю
# ============================================================

def require_auth(handler):
    @wraps(handler)
    def wrapper(message, *args, **kwargs):
        if not db.is_authorized(message.from_user.id):
            start_login(message)
            return
        return handler(message, *args, **kwargs)
    return wrapper


def require_auth_cb(handler):
    @wraps(handler)
    def wrapper(call, *args, **kwargs):
        if not db.is_authorized(call.from_user.id):
            bot.answer_callback_query(call.id, "Сначала войдите: отправьте /start")
            return
        return handler(call, *args, **kwargs)
    return wrapper


def start_login(message):
    db.ensure_user(message.from_user.id)
    msg = bot.send_message(message.chat.id, "🔒 Введите пароль для доступа к боту:")
    bot.register_next_step_handler(msg, check_password)


def check_password(message):
    entered = (message.text or "").strip()
    # Сообщение с паролем сразу удаляется, чтобы он не оставался в истории чата.
    try:
        bot.delete_message(message.chat.id, message.message_id)
    except Exception:
        pass
    if entered == config.ACCESS_PASSWORD:
        db.set_authorized(message.from_user.id, True)
        bot.send_message(message.chat.id, "✅ Доступ разрешён. Отправьте /start, чтобы увидеть команды.")
    else:
        msg = bot.send_message(message.chat.id, "❌ Неверный пароль, попробуйте снова:")
        bot.register_next_step_handler(msg, check_password)


# ============================================================
# /start, /cancel
# ============================================================

@bot.message_handler(commands=["start", "help"])
@require_auth
def cmd_start(message):
    text = (
        "Привет! Я бот-расписание.\n\n"
        "/add — добавить событие\n"
        "/schedule [дата] — показать расписание (по умолчанию сегодня)\n"
        "/week [дата] — все события за 7 дней вперёд (по умолчанию с сегодня)\n"
        "/free [дата] — свободное время на дату\n"
        "/edit — изменить событие\n"
        "/delete — удалить событие\n"
        "/settings — время на дорогу домой и рабочие часы\n"
        "/cancel — отменить текущее действие\n\n"
        "Дату можно указывать как: сегодня, завтра, 25.12 или 2026-12-25\n"
        "🚗 у события — после него закладывается время на дорогу домой."
    )
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["cancel"])
def cmd_cancel(message):
    pending.pop(message.chat.id, None)
    bot.clear_step_handler_by_chat_id(message.chat.id)
    bot.send_message(message.chat.id, "Действие отменено.")


# ============================================================
# /add — название → дата → время → длительность → travel time → повтор
# ============================================================

@bot.message_handler(commands=["add"])
@require_auth
def cmd_add(message):
    pending[message.chat.id] = {}
    msg = bot.send_message(message.chat.id, "Название события?")
    bot.register_next_step_handler(msg, add_step_title)


def add_step_title(message):
    if message.text.startswith("/"):
        pending.pop(message.chat.id, None)
        cmd_cancel(message)
        return
    pending.setdefault(message.chat.id, {})["title"] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Дата? (сегодня / завтра / 25.12 / 2026-12-25)")
    bot.register_next_step_handler(msg, add_step_date)


def add_step_date(message):
    try:
        date = utils.parse_date(message.text)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Не понял дату, попробуйте ещё раз:")
        bot.register_next_step_handler(msg, add_step_date)
        return
    pending.setdefault(message.chat.id, {})["date"] = date
    msg = bot.send_message(message.chat.id, "Время начала? (ЧЧ:ММ)")
    bot.register_next_step_handler(msg, add_step_time)


def add_step_time(message):
    try:
        utils.parse_time(message.text)
    except ValueError:
        msg = bot.send_message(message.chat.id, "Формат времени ЧЧ:ММ, попробуйте ещё раз:")
        bot.register_next_step_handler(msg, add_step_time)
        return
    pending.setdefault(message.chat.id, {})["start_time"] = message.text.strip()
    msg = bot.send_message(message.chat.id, "Длительность в минутах?")
    bot.register_next_step_handler(msg, add_step_duration)


def add_step_duration(message):
    try:
        duration = int(message.text.strip())
        if duration <= 0:
            raise ValueError
    except ValueError:
        msg = bot.send_message(message.chat.id, "Введите положительное число минут:")
        bot.register_next_step_handler(msg, add_step_duration)
        return
    state = pending.setdefault(message.chat.id, {})
    state["duration_minutes"] = duration

    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Да", callback_data="travel:yes"),
        types.InlineKeyboardButton("Нет", callback_data="travel:no"),
    )
    bot.send_message(
        message.chat.id,
        "Нужно ли закладывать время на дорогу домой после этого события?",
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("travel:"))
@require_auth_cb
def cb_travel_toggle(call):
    state = pending.get(call.message.chat.id)
    if state is None:
        bot.answer_callback_query(call.id, "Сессия добавления устарела, начните заново: /add")
        return
    state["needs_travel_time"] = 1 if call.data.endswith("yes") else 0
    bot.answer_callback_query(call.id)

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Не повторять", callback_data="repeat:none"))
    markup.add(
        types.InlineKeyboardButton("Каждый день", callback_data="repeat:daily"),
        types.InlineKeyboardButton("Каждую неделю", callback_data="repeat:weekly"),
    )
    markup.add(types.InlineKeyboardButton("Через N дней…", callback_data="repeat:custom"))
    bot.edit_message_text(
        "Повторять событие?",
        call.message.chat.id,
        call.message.message_id,
        reply_markup=markup,
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("repeat:"))
@require_auth_cb
def cb_repeat_choice(call):
    state = pending.get(call.message.chat.id)
    if state is None:
        bot.answer_callback_query(call.id, "Сессия добавления устарела, начните заново: /add")
        return
    choice = call.data.split(":")[1]
    bot.answer_callback_query(call.id)

    if choice == "none":
        state["repeat_type"] = None
        state["repeat_interval_days"] = None
        finalize_add(call.message.chat.id, call.from_user.id, occurrences=1)
        return

    if choice == "daily":
        state["repeat_type"] = "daily"
        state["repeat_interval_days"] = 1
    elif choice == "weekly":
        state["repeat_type"] = "weekly"
        state["repeat_interval_days"] = 7
    elif choice == "custom":
        msg = bot.send_message(call.message.chat.id, "Через сколько дней повторять? (число)")
        bot.register_next_step_handler(msg, add_step_custom_interval)
        return

    ask_occurrences(call.message.chat.id)


def ask_occurrences(chat_id):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("4 раза", callback_data="occ:4"),
        types.InlineKeyboardButton("8 раз", callback_data="occ:8"),
        types.InlineKeyboardButton("12 раз", callback_data="occ:12"),
    )
    markup.add(types.InlineKeyboardButton("♾ Бесконечно", callback_data="occ:infinite"))
    markup.add(types.InlineKeyboardButton("Своё число…", callback_data="occ:custom"))
    bot.send_message(chat_id, "Сколько раз повторить? (включая первое)", reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith("occ:"))
@require_auth_cb
def cb_occurrences_choice(call):
    state = pending.get(call.message.chat.id)
    if state is None:
        bot.answer_callback_query(call.id, "Сессия добавления устарела, начните заново: /add")
        return
    choice = call.data.split(":")[1]
    bot.answer_callback_query(call.id)

    if choice == "custom":
        msg = bot.send_message(call.message.chat.id, "Сколько раз повторить? (число)")
        bot.register_next_step_handler(msg, add_step_occurrences)
        return
    if choice == "infinite":
        finalize_add(call.message.chat.id, call.from_user.id, occurrences=None)
        return
    finalize_add(call.message.chat.id, call.from_user.id, occurrences=int(choice))


def add_step_custom_interval(message):
    try:
        interval = int(message.text.strip())
        if interval <= 0:
            raise ValueError
    except ValueError:
        msg = bot.send_message(message.chat.id, "Введите положительное число дней:")
        bot.register_next_step_handler(msg, add_step_custom_interval)
        return
    state = pending.get(message.chat.id)
    if state is None:
        send_error(message.chat.id, "Сессия добавления устарела, начните заново: /add")
        return
    state["repeat_type"] = "custom"
    state["repeat_interval_days"] = interval
    ask_occurrences(message.chat.id)


def add_step_occurrences(message):
    try:
        occurrences = int(message.text.strip())
        if occurrences <= 0:
            raise ValueError
    except ValueError:
        msg = bot.send_message(message.chat.id, "Введите положительное число:")
        bot.register_next_step_handler(msg, add_step_occurrences)
        return
    finalize_add(message.chat.id, message.from_user.id, occurrences)


def finalize_add(chat_id, user_id, occurrences):
    state = pending.pop(chat_id, None)
    if state is None:
        send_error(chat_id, "Сессия добавления устарела, начните заново: /add")
        return
    interval = state.get("repeat_interval_days") or 1
    summary = (
        f"✅ Добавлено: {state['title']} — {utils.format_date_human(state['date'])} "
        f"{state['start_time']}, {state['duration_minutes']} мин."
    )

    if occurrences is None:
        db.add_infinite_series(
            user_id,
            state["title"],
            state["date"],
            state["start_time"],
            state["duration_minutes"],
            state.get("needs_travel_time", 1),
            state.get("repeat_type"),
            interval,
        )
        summary += (
            f"\nПовтор: ♾ бесконечно, интервал {interval} дн. "
            "(события создаются заранее и автоматически продлеваются при запросе расписания на будущее)."
        )
        bot.send_message(chat_id, summary)
        return

    ids, series_id = db.add_recurring_event(
        user_id,
        state["title"],
        state["date"],
        state["start_time"],
        state["duration_minutes"],
        state.get("needs_travel_time", 1),
        state.get("repeat_type"),
        interval,
        occurrences,
    )
    if occurrences > 1:
        summary += f"\nПовтор: {occurrences} раз(а), интервал {interval} дн."
    bot.send_message(chat_id, summary)


# ============================================================
# /schedule
# ============================================================

@bot.message_handler(commands=["schedule"])
@require_auth
def cmd_schedule(message):
    parts = message.text.split(maxsplit=1)
    date_arg = parts[1] if len(parts) > 1 else "сегодня"
    try:
        date = utils.parse_date(date_arg)
    except ValueError:
        send_error(message.chat.id, "Не понял дату.")
        return
    db.extend_series_if_needed(message.from_user.id, date)
    events = db.get_events(message.from_user.id, date)
    if not events:
        bot.send_message(message.chat.id, f"На {utils.format_date_human(date)} событий нет.")
        return
    lines = [f"📅 Расписание на {utils.format_date_human(date)}:"]
    for e in events:
        start = utils.parse_time(e["start_time"])
        end_time = (start + timedelta(minutes=e["duration_minutes"])).strftime("%H:%M")
        icon = " 🚗" if e.get("needs_travel_time", 1) else ""
        lines.append(f"• {e['start_time']}–{end_time} — {e['title']}{icon}")
    bot.send_message(message.chat.id, "\n".join(lines))


# ============================================================
# /week — все события за 7 дней вперёд
# ============================================================

@bot.message_handler(commands=["week"])
@require_auth
def cmd_week(message):
    parts = message.text.split(maxsplit=1)
    start_arg = parts[1] if len(parts) > 1 else "сегодня"
    try:
        start_date = utils.parse_date(start_arg)
    except ValueError:
        send_error(message.chat.id, "Не понял дату.")
        return
    start_dt = datetime.strptime(start_date, utils.DATE_FMT)
    end_date = (start_dt + timedelta(days=6)).strftime(utils.DATE_FMT)

    db.extend_series_if_needed(message.from_user.id, end_date)
    events = db.get_events_range(message.from_user.id, start_date, end_date)
    if not events:
        bot.send_message(
            message.chat.id,
            f"С {utils.format_date_human(start_date)} по {utils.format_date_human(end_date)} событий нет.",
        )
        return

    lines = [f"🗓 События с {utils.format_date_human(start_date)} по {utils.format_date_human(end_date)}:"]
    current_date = None
    for e in events:
        if e["date"] != current_date:
            current_date = e["date"]
            lines.append(f"\n{utils.format_date_human(current_date)}:")
        start = utils.parse_time(e["start_time"])
        end_time = (start + timedelta(minutes=e["duration_minutes"])).strftime("%H:%M")
        icon = " 🚗" if e.get("needs_travel_time", 1) else ""
        lines.append(f"• {e['start_time']}–{end_time} — {e['title']}{icon}")
    bot.send_message(message.chat.id, "\n".join(lines))


# ============================================================
# /free
# ============================================================

@bot.message_handler(commands=["free"])
@require_auth
def cmd_free(message):
    parts = message.text.split(maxsplit=1)
    date_arg = parts[1] if len(parts) > 1 else "сегодня"
    try:
        date = utils.parse_date(date_arg)
    except ValueError:
        send_error(message.chat.id, "Не понял дату.")
        return
    settings = db.get_settings(message.from_user.id)
    db.extend_series_if_needed(message.from_user.id, date)
    events = db.get_events(message.from_user.id, date)
    free = utils.compute_free_slots(
        events, settings["day_start"], settings["day_end"], settings["travel_time_minutes"]
    )
    if not free:
        bot.send_message(message.chat.id, f"На {utils.format_date_human(date)} свободного времени нет.")
        return
    lines = [f"🟢 Свободное время на {utils.format_date_human(date)}:"]
    for s, e in free:
        lines.append(f"• {s}–{e}")
    bot.send_message(message.chat.id, "\n".join(lines))


# ============================================================
# /edit
# ============================================================

@bot.message_handler(commands=["edit"])
@require_auth
def cmd_edit(message):
    events = db.get_events(message.from_user.id)
    if not events:
        bot.send_message(message.chat.id, "Событий нет.")
        return
    bot.send_message(message.chat.id, "Что редактируем?", reply_markup=events_keyboard(events, "edit"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("edit:"))
@require_auth_cb
def cb_edit_pick(call):
    event_id = int(call.data.split(":")[1])
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Название", callback_data=f"editf:title:{event_id}"),
        types.InlineKeyboardButton("Дата", callback_data=f"editf:date:{event_id}"),
    )
    markup.add(
        types.InlineKeyboardButton("Время начала", callback_data=f"editf:start_time:{event_id}"),
        types.InlineKeyboardButton("Длительность", callback_data=f"editf:duration_minutes:{event_id}"),
    )
    markup.add(
        types.InlineKeyboardButton("Время на дорогу после 🚗", callback_data=f"editf:needs_travel_time:{event_id}")
    )
    bot.edit_message_text("Что изменить?", call.message.chat.id, call.message.message_id, reply_markup=markup)


@bot.callback_query_handler(func=lambda c: c.data.startswith("editf:"))
@require_auth_cb
def cb_edit_field(call):
    _, field, event_id = call.data.split(":")
    event_id = int(event_id)

    if field == "needs_travel_time":
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Да", callback_data=f"editv:needs_travel_time:1:{event_id}"),
            types.InlineKeyboardButton("Нет", callback_data=f"editv:needs_travel_time:0:{event_id}"),
        )
        bot.edit_message_text(
            "Закладывать время на дорогу после этого события?",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
        )
        return

    prompts = {
        "title": "Новое название:",
        "date": "Новая дата (сегодня/завтра/25.12/2026-12-25):",
        "start_time": "Новое время начала (ЧЧ:ММ):",
        "duration_minutes": "Новая длительность в минутах:",
    }
    msg = bot.send_message(call.message.chat.id, prompts[field])
    bot.register_next_step_handler(msg, edit_apply, field=field, event_id=event_id)


@bot.callback_query_handler(func=lambda c: c.data.startswith("editv:"))
@require_auth_cb
def cb_edit_value(call):
    _, field, value, event_id = call.data.split(":")
    ok = db.update_event(int(event_id), call.from_user.id, **{field: int(value)})
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "✅ Изменено." if ok else "Не удалось найти событие.",
        call.message.chat.id,
        call.message.message_id,
    )


def edit_apply(message, field, event_id):
    value = message.text.strip()
    try:
        if field == "date":
            value = utils.parse_date(value)
        elif field == "start_time":
            utils.parse_time(value)
        elif field == "duration_minutes":
            value = int(value)
            if value <= 0:
                raise ValueError
    except ValueError:
        send_error(message.chat.id, "Некорректное значение, изменение отменено.")
        return
    ok = db.update_event(event_id, message.from_user.id, **{field: value})
    bot.send_message(message.chat.id, "✅ Изменено." if ok else "Не удалось найти событие.")


# ============================================================
# /delete
# ============================================================

@bot.message_handler(commands=["delete"])
@require_auth
def cmd_delete(message):
    events = db.get_events(message.from_user.id)
    if not events:
        bot.send_message(message.chat.id, "Событий нет.")
        return
    bot.send_message(message.chat.id, "Что удаляем?", reply_markup=events_keyboard(events, "del"))


@bot.callback_query_handler(func=lambda c: c.data.startswith("del:"))
@require_auth_cb
def cb_delete(call):
    event_id = int(call.data.split(":")[1])
    event = db.get_event(event_id, call.from_user.id)
    if not event:
        bot.answer_callback_query(call.id)
        bot.edit_message_text("Не удалось найти событие.", call.message.chat.id, call.message.message_id)
        return

    if event.get("series_id"):
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Только это", callback_data=f"delonly:{event_id}"),
            types.InlineKeyboardButton("Всю серию", callback_data=f"delseries:{event['series_id']}"),
        )
        bot.answer_callback_query(call.id)
        bot.edit_message_text(
            "Это повторяющееся событие. Удалить только его или всю серию?",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=markup,
        )
        return

    ok = db.delete_event(event_id, call.from_user.id)
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "🗑 Удалено." if ok else "Не удалось найти событие.",
        call.message.chat.id,
        call.message.message_id,
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("delonly:"))
@require_auth_cb
def cb_delete_only(call):
    event_id = int(call.data.split(":")[1])
    ok = db.delete_event(event_id, call.from_user.id)
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        "🗑 Удалено." if ok else "Не удалось найти событие.",
        call.message.chat.id,
        call.message.message_id,
    )


@bot.callback_query_handler(func=lambda c: c.data.startswith("delseries:"))
@require_auth_cb
def cb_delete_series(call):
    series_id = call.data.split(":", 1)[1]
    count = db.delete_series(series_id, call.from_user.id)
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        f"🗑 Удалено событий: {count}.", call.message.chat.id, call.message.message_id
    )


# ============================================================
# /settings
# ============================================================

@bot.message_handler(commands=["settings"])
@require_auth
def cmd_settings(message):
    s = db.get_settings(message.from_user.id)
    text = (
        f"⏱ Время на дорогу домой: {s['travel_time_minutes']} мин.\n"
        f"🕗 Рабочие часы: {s['day_start']}–{s['day_end']}\n\n"
        "/travel_time <минуты> — изменить время на дорогу\n"
        "/working_hours <ЧЧ:ММ> <ЧЧ:ММ> — изменить рабочие часы\n\n"
        "Время на дорогу применяется только к тем событиям, у которых при "
        "создании (или в /edit) включена опция «Время на дорогу после 🚗»."
    )
    bot.send_message(message.chat.id, text)


@bot.message_handler(commands=["travel_time"])
@require_auth
def cmd_travel_time(message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip().isdigit():
        send_error(message.chat.id, "Использование: /travel_time 30")
        return
    minutes = int(parts[1].strip())
    db.set_travel_time(message.from_user.id, minutes)
    bot.send_message(message.chat.id, f"✅ Время на дорогу домой: {minutes} мин.")


@bot.message_handler(commands=["working_hours"])
@require_auth
def cmd_working_hours(message):
    parts = message.text.split()
    if len(parts) != 3:
        send_error(message.chat.id, "Использование: /working_hours 08:00 23:00")
        return
    try:
        utils.parse_time(parts[1])
        utils.parse_time(parts[2])
    except ValueError:
        send_error(message.chat.id, "Формат времени ЧЧ:ММ")
        return
    db.set_working_hours(message.from_user.id, parts[1], parts[2])
    bot.send_message(message.chat.id, f"✅ Рабочие часы: {parts[1]}–{parts[2]}")


if __name__ == "__main__":
    print("Бот запущен...")
    bot.infinity_polling()
