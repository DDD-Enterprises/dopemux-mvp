"""
Configuration settings for ADHD Accommodation Engine.
"""

import os
from typing import List, Optional


class Settings:
    """
    Application settings loaded from environment variables.
    """
    
    # Server settings
    api_port: int = int(os.getenv("API_PORT", "8095"))
    host: str = os.getenv("HOST", "0.0.0.0")
    # Backward/forward-compatible alias used by startup logging paths
    api_host: str = os.getenv("API_HOST", os.getenv("HOST", "0.0.0.0"))
    
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
    
    # ConPort / DopeconBridge
    conport_url: str = os.getenv("CONPORT_URL", "http://localhost:3010")
    pal_url: str = os.getenv("PAL_URL", os.getenv("ZEN_URL", "http://localhost:3003"))  # Backward compat with ZEN_URL
    workspace_id: str = os.getenv("ADHD_WORKSPACE_ID", os.getcwd())
    dopecon_bridge_url: str = os.getenv("DOPECON_BRIDGE_URL", os.getenv("CONPORT_BRIDGE_URL", "http://localhost:3016"))
    dopecon_bridge_token: Optional[str] = os.getenv("DOPECON_BRIDGE_TOKEN")
    dopecon_bridge_source_plane: str = os.getenv("DOPECON_BRIDGE_SOURCE_PLANE", "cognitive_plane")
    task_orchestrator_url: str = os.getenv("TASK_ORCHESTRATOR_URL", "http://task-orchestrator:8000")
    
    # Monitor settings
    monitor_check_interval: int = int(os.getenv("MONITOR_CHECK_INTERVAL", "60"))
    energy_decay_rate: float = float(os.getenv("ENERGY_DECAY_RATE", "0.95"))
    attention_reset_threshold: int = int(os.getenv("ATTENTION_RESET_THRESHOLD", "300"))
    energy_monitor_interval: int = int(os.getenv("ENERGY_MONITOR_INTERVAL", "60"))
    attention_monitor_interval: int = int(
        os.getenv("ATTENTION_MONITOR_INTERVAL", os.getenv("ATTENTION_CHECK_INTERVAL", "60"))
    )
    cognitive_monitor_interval: int = int(os.getenv("COGNITIVE_MONITOR_INTERVAL", "60"))
    break_monitor_interval: int = int(os.getenv("BREAK_MONITOR_INTERVAL", "60"))
    hyperfocus_monitor_interval: int = int(os.getenv("HYPERFOCUS_MONITOR_INTERVAL", "60"))
    
    # ML settings
    enable_ml_predictions: bool = os.getenv("ENABLE_ML_PREDICTIONS", "true").lower() == "true"
    ml_model_path: str = os.getenv("ML_MODEL_PATH", "/app/models")

    # Background prediction service (Phase 3.4)
    enable_background_predictions: bool = os.getenv("ENABLE_BACKGROUND_PREDICTIONS", "true").lower() == "true"

    # Mobile Push (Phase 10.3)
    enable_mobile_push: bool = os.getenv("ENABLE_MOBILE_PUSH", "false").lower() == "true"
    ntfy_topic: str = os.getenv("NTFY_TOPIC", "adhd-dopemux-dev")

    # ML Loop (Phase 10.4)
    ml_retrain_interval_hours: int = int(os.getenv("ML_RETRAIN_INTERVAL_HOURS", "24"))
    min_training_samples: int = int(os.getenv("MIN_TRAINING_SAMPLES", "50"))


# Global settings instance
settings = Settings()

# Backwards-compatible aliases used throughout the legacy code/tests
ALLOWED_ORIGINS = settings.allowed_origins
