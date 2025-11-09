"""
Configuration settings for ADHD Accommodation Engine.
"""

import os
from typing import List


class Settings:
    """
    Application settings loaded from environment variables.
    """
    
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
    zen_url: str = os.getenv("ZEN_URL", "http://localhost:3003")
    workspace_id: str = os.getenv("ADHD_WORKSPACE_ID", os.getcwd())
    
    # Monitor settings
    monitor_check_interval: int = int(os.getenv("MONITOR_CHECK_INTERVAL", "60"))
    energy_decay_rate: float = float(os.getenv("ENERGY_DECAY_RATE", "0.95"))
    attention_reset_threshold: int = int(os.getenv("ATTENTION_RESET_THRESHOLD", "300"))
    
    # ML settings
    enable_ml_predictions: bool = os.getenv("ENABLE_ML_PREDICTIONS", "true").lower() == "true"
    ml_model_path: str = os.getenv("ML_MODEL_PATH", "/app/models")

    # Background prediction service (Phase 3.4)
    enable_background_predictions: bool = os.getenv("ENABLE_BACKGROUND_PREDICTIONS", "true").lower() == "true"


# Global settings instance
settings = Settings()

# Backwards-compatible aliases used throughout the legacy code/tests
ALLOWED_ORIGINS = settings.allowed_origins
