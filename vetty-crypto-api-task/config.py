from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "vetty-crypto-api"
    app_version: str = "1.0.0"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 8000
    api_key: str = "change-me"

    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    coingecko_api_key: str | None = None
    coingecko_timeout_seconds: float = 5.0

    cache_ttl_seconds: int = 60
    webhook_url: str | None = None
    webhook_timeout_seconds: float = 3.0
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=False, extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()