"""
Configuration settings for ADHD Accommodation Engine.
"""

import os
from typing import List, Optional


DEV_ENVIRONMENTS = {"dev", "development", "local", "test", "testing"}
WEAK_ADHD_API_KEYS = {
    "dev-key-123",
    "CHANGE_ME_generate_with_openssl_rand_hex_32_placeholder",
}


def runtime_environment() -> str:
    """Return the resolved runtime environment name.

    A blank/whitespace ``ENVIRONMENT`` must not shadow ``DPMX_ENV``: the env var
    can be *present but empty* (e.g. ``ENVIRONMENT:`` in compose), and a naive
    ``os.getenv("ENVIRONMENT", os.getenv("DPMX_ENV", ...))`` would return ``""``
    and fall through to ``development`` — silently disabling fail-closed auth in
    a production runtime. Consult each source in priority order and only accept a
    non-empty value.
    """
    for value in (os.getenv("ENVIRONMENT"), os.getenv("DPMX_ENV")):
        candidate = (value or "").strip().lower()
        if candidate:
            return candidate
    return "development"


def is_development_environment(environment: str | None = None) -> bool:
    return (environment or runtime_environment()).strip().lower() in DEV_ENVIRONMENTS


def clean_secret_value(value: str | None, *, weak_values: set[str]) -> str:
    resolved = (value or "").strip()
    if not resolved or resolved in weak_values:
        return ""
    return resolved


def require_runtime_secret(var_name: str, *, weak_values: set[str]) -> str:
    resolved = clean_secret_value(os.getenv(var_name), weak_values=weak_values)
    if resolved:
        return resolved

    environment = runtime_environment()
    if is_development_environment(environment):
        return ""

    raise RuntimeError(
        f"{var_name} must be set to a non-placeholder value when ENVIRONMENT={environment}"
    )


class Settings:
    """
    Application settings loaded from environment variables.
    """
    
    # Server settings
    environment: str = runtime_environment()
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
    api_key: str = require_runtime_secret(
        "ADHD_ENGINE_API_KEY",
        weak_values=WEAK_ADHD_API_KEYS,
    )
    
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
