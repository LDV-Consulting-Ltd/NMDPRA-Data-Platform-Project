"""Tanna connector configuration (environment-driven)."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TannaConnectorSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    connector_token: str = Field(default="", validation_alias="TANNA_CONNECTOR_TOKEN")
    connector_version: str = "0.1"
    module_id: str = "petrogrid"
    module_name: str = "PetroGrid"

    @property
    def normalized_token(self) -> str:
        return self.connector_token.strip()


@lru_cache
def get_tanna_config() -> TannaConnectorSettings:
    return TannaConnectorSettings()


def reset_tanna_config_cache() -> None:
    get_tanna_config.cache_clear()
