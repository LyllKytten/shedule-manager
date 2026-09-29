import os

# Токен бота передаётся только через переменную окружения BOT_TOKEN
# (или файл .env при запуске через docker compose). Не храните токен в коде.
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# Пароль для входа в бота. Пользователь должен прислать его текстом первым
# сообщением — бот проверит и сразу удалит это сообщение из чата.
# Обязательно смените значение по умолчанию!
ACCESS_PASSWORD = os.environ.get("ACCESS_PASSWORD", "CHANGE_ME")

# Путь к файлу SQLite. В Docker указывает на примонтированный том.
DB_PATH = os.environ.get("DB_PATH", "schedule.db")
