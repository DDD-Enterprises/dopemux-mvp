"""
DopeconBridge Configuration - Environment-based settings.

Centralizes all configuration from environment variables with
sensible defaults for development.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Settings:
    """Multi-instance aware configuration for DopeconBridge."""
    
    # Environment
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "dev"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "info").upper())
    
    # Instance configuration
    instance_name: str = field(default_factory=lambda: os.getenv("DOPEMUX_INSTANCE", "default"))
    port_base: int = field(default_factory=lambda: int(os.getenv("PORT_BASE", "3000")))
    container_prefix: str = ""  # Set in __post_init__
    network_name: str = ""  # Set in __post_init__
    
    # Service port (PORT_BASE + 16)
    port: int = 0  # Set in __post_init__
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    service_name: str = field(default_factory=lambda: os.getenv("SERVICE_NAME", "dopecon-bridge"))
    health_check_path: str = field(default_factory=lambda: os.getenv("HEALTH_CHECK_PATH", "/health"))
    
    # Service discovery URLs
    task_master_url: str = ""  # Set in __post_init__
    task_orchestrator_url: str = ""  # Set in __post_init__
    leantime_bridge_url: str = ""  # Set in __post_init__
    conport_url: str = field(default_factory=lambda: os.getenv("CONPORT_URL", "http://conport:3020"))
    
    # Database
    postgres_url: str = field(
        default_factory=lambda: os.getenv(
            "POSTGRES_URL", 
            "postgresql+asyncpg://dopemux:dopemux_password@postgres:5432/dopemux_tasks"
        )
    )
    db_pool_size: int = 20
    db_max_overflow: int = 30
    
    # Redis
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://redis:6379"))
    redis_password: str = field(default_factory=lambda: os.getenv("REDIS_PASSWORD", ""))
    
    # Qdrant (optional vector db)
    qdrant_url: str = field(default_factory=lambda: os.getenv("QDRANT_URL", "http://qdrant:6333"))
    qdrant_enabled: bool = field(default_factory=lambda: os.getenv("QDRANT_ENABLED", "true").lower() == "true")
    
    # JWT Auth
    secret_key: str = field(
        default_factory=lambda: os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: List[str] = field(default_factory=list)
    
    # OpenAI for embeddings
    openai_api_key: Optional[str] = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    
    # Workspace (fixed for this project)
    default_workspace_id: str = "/Users/hue/code/dopemux-mvp"
    
    def __post_init__(self):
        """Compute derived configuration values."""
        # Container prefix from instance name
        self.container_prefix = os.getenv("CONTAINER_PREFIX", f"mcp-{self.instance_name}")
        self.network_name = os.getenv("NETWORK_NAME", f"mcp-network-{self.instance_name}")
        
        # Port calculation
        self.port = int(os.getenv("PORT", str(self.port_base + 16)))
        
        # Service URLs from container prefix
        self.task_master_url = f"http://{self.container_prefix}-task-master-ai:3005"
        self.task_orchestrator_url = f"http://{self.container_prefix}-task-orchestrator:3014"
        self.leantime_bridge_url = f"http://{self.container_prefix}-leantime-bridge:3015"
        
        # CORS origins
        origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080")
        self.allowed_origins = [o.strip() for o in origins_str.split(",") if o.strip()]


# Global settings instance
settings = Settings()
