from functools import lru_cache
from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.db_url import resolve_database_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Prefer a full connection string (Supabase "URI" / Session or Transaction pooler).
    database_url: str = Field(default="", validation_alias="DATABASE_URL")
    supabase_db_url: str = Field(default="", validation_alias="SUPABASE_DB_URL")

    # Optional discrete Supabase Postgres parts (used when DATABASE_URL is unset).
    supabase_db_host: str = Field(default="", validation_alias="SUPABASE_DB_HOST")
    supabase_db_password: str = Field(default="", validation_alias="SUPABASE_DB_PASSWORD")
    supabase_db_user: str = Field(default="postgres", validation_alias="SUPABASE_DB_USER")
    supabase_db_name: str = Field(default="postgres", validation_alias="SUPABASE_DB_NAME")
    supabase_db_port: int = Field(default=5432, validation_alias="SUPABASE_DB_PORT")
    supabase_db_sslmode: str = Field(default="require", validation_alias="SUPABASE_DB_SSLMODE")

    # Optional Supabase project metadata (not required for SQLAlchemy; useful for docs/ops).
    supabase_url: str = Field(default="", validation_alias="SUPABASE_URL")
    supabase_anon_key: str = Field(default="", validation_alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str = Field(default="", validation_alias="SUPABASE_SERVICE_ROLE_KEY")

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    @model_validator(mode="after")
    def _resolve_database_url(self) -> "Settings":
        resolved = resolve_database_url(
            database_url=self.database_url,
            supabase_db_url=self.supabase_db_url,
            supabase_db_host=self.supabase_db_host,
            supabase_db_password=self.supabase_db_password,
            supabase_db_user=self.supabase_db_user,
            supabase_db_name=self.supabase_db_name,
            supabase_db_port=self.supabase_db_port,
            supabase_db_sslmode=self.supabase_db_sslmode,
        )
        object.__setattr__(self, "database_url", resolved)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    get_settings.cache_clear()
