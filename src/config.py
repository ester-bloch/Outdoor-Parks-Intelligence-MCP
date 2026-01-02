"""Configuration management using Pydantic settings."""

import sys
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = ".env"
if "pytest" in sys.modules:
    _ENV_FILE = None


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE, env_file_encoding="utf-8", case_sensitive=False
    )

    nps_api_key: Optional[str] = None
    nps_api_base_url: str = "https://developer.nps.gov/api/v1"
    airvisual_api_key: Optional[str] = None
    airvisual_api_base_url: str = "https://api.airvisual.com/v2"  # blocked by netfree for this point of time, will get open soon
    openweather_api_key: Optional[str] = None
    openweather_api_base_url: str = "https://api.openweathermap.org/data/2.5"
    open_meteo_api_base_url: str = "https://api.open-meteo.com/v1"
    log_level: str = "INFO"
    log_json: bool = False  # Whether to output logs in JSON format
    log_include_timestamp: bool = True  # Whether to include timestamps in logs
    server_name: str = "National Parks"


# Global settings instance
settings = Settings()
