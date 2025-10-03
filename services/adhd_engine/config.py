"""
Configuration management for ADHD Accommodation Engine.

Uses Pydantic Settings for environment-based configuration.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    redis_db: int = 6

    # Workspace Configuration
    workspace_id: str = "/Users/hue/code/dopemux-mvp"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"

    # Monitor Intervals (seconds)
    energy_monitor_interval: int = 300
    attention_monitor_interval: int = 180
    cognitive_monitor_interval: int = 120
    break_monitor_interval: int = 60
    hyperfocus_monitor_interval: int = 300

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
