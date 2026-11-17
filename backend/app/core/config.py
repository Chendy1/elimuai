"""Central configuration. All values come from environment variables; no secrets in code."""
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    secret_key: str = Field(default="dev-only-change-me", min_length=8)
    database_url: str = "postgresql+psycopg://elimuai:change-me-local-only@localhost:5432/elimuai"
    cors_origins: str = "http://localhost:3000"
    frontend_url: str = "http://localhost:3000"
    session_ttl_hours: int = 336  # 14 days, absolute
    reset_token_ttl_minutes: int = 30

    @property
    def cookie_secure(self) -> bool:
        """Secure cookies everywhere except local development and tests."""
        return self.app_env not in ("development", "test")

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
