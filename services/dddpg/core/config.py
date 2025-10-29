"""DDDPG Configuration"""

from pydantic_settings import BaseSettings
from enum import Enum


class DeploymentMode(str, Enum):
    MINIMAL = "minimal"
    STANDARD = "standard"
    FULL = "full"


class DDDPGConfig(BaseSettings):
    mode: DeploymentMode = DeploymentMode.STANDARD
    storage_backend: str = "postgres"
    redis_url: str = "redis://localhost:6379"
    auth_enabled: bool = False
    adhd_mode: bool = True
    default_page_size: int = 3
    
    class Config:
        env_prefix = "DDDPG_"


__all__ = ["DDDPGConfig", "DeploymentMode"]
