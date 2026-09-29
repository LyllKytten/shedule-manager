from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, read from environment variables / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://schedule:schedule@localhost:5432/schedule"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    # Superuser created on startup if it does not exist yet.
    # Leave the password empty to skip creation (a warning is logged).
    superuser_username: str = "harak1r1"
    superuser_password: str = ""

    # If false, only a superuser can create new accounts (POST /admin/users).
    allow_registration: bool = True

    # Comma-separated list of allowed CORS origins ("*" for any).
    cors_origins: str = "*"


@lru_cache
def get_settings() -> Settings:
    return Settings()
