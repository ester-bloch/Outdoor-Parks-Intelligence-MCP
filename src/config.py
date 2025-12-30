"""Configuration management using Pydantic settings."""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    nps_api_key: Optional[str] = None
    nps_api_base_url: str = "https://developer.nps.gov/api/v1"
    log_level: str = "INFO"
    log_json: bool = False  # Whether to output logs in JSON format
    log_include_timestamp: bool = True  # Whether to include timestamps in logs
    server_name: str = "National Parks"


# Global settings instance
settings = Settings()
