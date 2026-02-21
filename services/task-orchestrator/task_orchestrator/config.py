"""
Task-Orchestrator Configuration - Environment-based settings.

Centralizes all configuration from environment variables.
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Settings:
    """Task-Orchestrator configuration."""
    
    # Environment
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "dev"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "info").upper())
    
    # Service identification
    service_name: str = "task-orchestrator"
    
    # Instance configuration
    instance_name: str = field(default_factory=lambda: os.getenv("DOPEMUX_INSTANCE", "default"))
    port_base: int = field(default_factory=lambda: int(os.getenv("PORT_BASE", "3000")))
    port: int = 0  # Set in __post_init__
    
    # Leantime connection
    leantime_url: str = field(default_factory=lambda: os.getenv("LEANTIME_URL", "http://leantime:8080"))
    leantime_token: str = field(default_factory=lambda: os.getenv("LEANTIME_TOKEN", ""))
    
    # Redis
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://redis:6379"))
    redis_password: str = field(default_factory=lambda: os.getenv("REDIS_PASSWORD", ""))
    redis_db: int = 2  # Separate DB for orchestrator
    
    # ConPort
    conport_url: str = field(default_factory=lambda: os.getenv("CONPORT_URL", "http://conport:8005"))
    
    # Workspace
    workspace_id: str = field(
        default_factory=lambda: os.getenv(
            "WORKSPACE_ID",
            os.getenv("DOPEMUX_WORKSPACE_ROOT", os.getcwd())
        )
    )
    
    # ADHD configuration
    adhd_config: Dict[str, Any] = field(default_factory=lambda: {
        "max_concurrent_tasks": 3,
        "break_enforcement": True,
        "context_switch_penalty": 0.3,
        "energy_level_matching": True,
        "implicit_progress_tracking": True,
        "break_interval_minutes": 25,
        "mandatory_break_minutes": 90,
        "hyperfocus_warning_minutes": 60
    })
    
    def __post_init__(self):
        """Compute derived configuration values."""
        self.port = int(os.getenv("PORT", str(self.port_base + 14)))  # Task-Orchestrator port


# Global settings instance
settings = Settings()
