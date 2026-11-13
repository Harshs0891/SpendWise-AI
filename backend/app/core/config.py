from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "SpendWise AI"
    app_version: str = "0.1.0"
    environment: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database configuration
    database_url: str

    # Comma-free JSON array in environment, e.g. ["https://app.example.com"].
    # Local development origins remain the defaults.
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Gemini API configuration. Optional for core finance features.
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-3.8-flash"

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
