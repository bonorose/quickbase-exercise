#!/usr/bin/env python3
# ******************************************************************************
# * @file    config.py
# * @author  Simeon Marlokov
# * @brief   Application settings, loaded from environment / .env
# * @date    25.10.2026
# ******************************************************************************
from functools import lru_cache

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

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "db"
    postgres_port: int = 5432

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+asyncpg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
