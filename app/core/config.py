"""Application configuration, loaded from environment variables / .env file."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the FutVantage API.

    Values are read from environment variables first, falling back to a
    local `.env` file (see `.env.example`) for local development.
    """

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "FutVantage API"
    environment: str = "development"
    api_v1_prefix: str = "/api/v1"

    # Origins allowed to call this API from a browser (the frontend's dev
    # server and, later, its deployed URL). Comma-separated in the env var.
    cors_allowed_origins: list[str] = ["http://localhost:3000"]

    # Populated once the database is wired up (next feature); kept optional
    # for now so the app can boot without a running Postgres instance.
    database_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    """Returns a cached Settings instance so `.env` is only parsed once."""
    return Settings()
