"""
Configuration settings for ADHD Accommodation Engine.
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import ConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    model_config = ConfigDict(extra='ignore')

    # Server settings
    api_port: int = int(os.getenv("API_PORT", "8095"))
    host: str = os.getenv("HOST", "0.0.0.0")

    # CORS settings
    allowed_origins: List[str] = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8097,http://adhd-dashboard:8097"
    ).split(",")

    # Authentication
    api_key: str = os.getenv("ADHD_ENGINE_API_KEY", "dev-key-123")

    # Redis settings
    redis_url: str = os.getenv("REDIS_URL", "redis://redis-primary:6379")

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # ConPort integration
    conport_url: str = os.getenv("CONPORT_URL", "http://localhost:3010")

    # Monitor settings
    monitor_check_interval: int = int(os.getenv("MONITOR_CHECK_INTERVAL", "60"))  # seconds
    energy_decay_rate: float = float(os.getenv("ENERGY_DECAY_RATE", "0.95"))  # per hour
    attention_reset_threshold: int = int(os.getenv("ATTENTION_RESET_THRESHOLD", "300"))  # seconds

    # ML settings (for future use)
    enable_ml_predictions: bool = os.getenv("ENABLE_ML_PREDICTIONS", "false").lower() == "true"
    ml_model_path: str = os.getenv("ML_MODEL_PATH", "/app/models")


# Global settings instance
settings = Settings()