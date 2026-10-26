#!/usr/bin/env python3
# ******************************************************************************
# * @file    config.py
# * @author  Simeon Marlokov
# * @brief   Application settings, loaded from environment / .env
# * @date    25.10.2026
# ******************************************************************************
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "quickbase-interview-backend"
    app_env: str = "local"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"
    cors_origins: list[str] = []

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    # Transition flag. The httpOnly cookie is always set; the JSON body token stays while this is true.
    auth_return_token_in_body: bool = True
    # Comma-separated peer addresses allowed to supply X-Forwarded-For. Empty disables the header.
    trusted_proxies: str = ""
    rate_limit_login_email: int = 10
    rate_limit_login_email_window_seconds: int = 900
    rate_limit_login_ip: int = 50
    rate_limit_login_ip_window_seconds: int = 900
    rate_limit_user_per_minute: int = 20
    rate_limit_organization_per_minute: int = 200

    # Empty key = LLM endpoints answer 503, the rest of the app still works
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"
    # Comma-separated, tried in order when the main model is overloaded (503/429) or hangs
    gemini_fallback_models: str = "gemini-3.5-flash"
    # Per attempt: no first chunk within this time = model treated as overloaded -> retry/fall back
    gemini_first_chunk_timeout_seconds: float = 20.0
    # Whole request, once streaming: also sent to Google as the server-side generation deadline
    gemini_request_timeout_seconds: float = 180.0
    gemini_max_retries: int = 1
    gemini_temperature: float = 0.2
    # gemini calls the provider. fake replays YAML scripts and never calls Gemini.
    llm_provider: Literal["gemini", "fake"] = "gemini"
    llm_fake_script_path: str | None = None
    agent_max_tool_iterations: int = 5
    agent_history_max_messages: int = 40

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "db"
    postgres_port: int = 5432
    # API role: LOGIN, no superuser, no BYPASSRLS. Migrations and seed keep POSTGRES_USER.
    postgres_app_user: str = "qai_app"
    postgres_app_password: str = "qai-app-password"
    # Dev seed only. The seed command refuses to run when APP_ENV=production.
    seed_user_password: str = "admin123"

    @property
    def gemini_fallback_model_list(self) -> list[str]:
        return [m.strip() for m in self.gemini_fallback_models.split(",") if m.strip()]

    def _database_url(self, username: str, password: str) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=username,
            password=password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )

    @property
    def database_url(self) -> URL:
        """Runtime connection. Subject to row-level security."""
        return self._database_url(self.postgres_app_user, self.postgres_app_password)

    @property
    def migration_database_url(self) -> URL:
        """Owner connection used by Alembic and the seed. Bypasses RLS when it is a superuser."""
        return self._database_url(self.postgres_user, self.postgres_password)


@lru_cache
def get_settings() -> Settings:
    return Settings()
