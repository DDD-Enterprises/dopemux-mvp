"""
Configuration settings for Claude Brain Service.
"""

import os
from typing import List

from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # API Settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8080, env="API_PORT")
    debug: bool = Field(default=False, env="DEBUG")

    # CORS Settings
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Redis Cache
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    cache_ttl_seconds: int = Field(default=3600, env="CACHE_TTL_SECONDS")
    cache_max_memory_mb: int = Field(default=100, env="CACHE_MAX_MEMORY_MB")

    # AI Provider API Keys
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openrouter_api_key: str = Field(default="", env="OPENROUTER_API_KEY")
    groq_api_key: str = Field(default="", env="GROQ_API_KEY")

    # Integrated Services
    adhd_engine_url: str = Field(default="http://localhost:8095", env="ADHD_ENGINE_URL")
    adhd_engine_api_key: str = Field(default="", env="ADHD_ENGINE_API_KEY")

    conport_url: str = Field(default="http://localhost:5455", env="CONPORT_URL")
    conport_api_key: str = Field(default="", env="CONPORT_API_KEY")

    serena_url: str = Field(default="http://localhost:8003", env="SERENA_URL")
    serena_api_key: str = Field(default="", env="SERENA_API_KEY")

    # Cost Optimization
    cost_optimization_enabled: bool = Field(default=True, env="COST_OPTIMIZATION_ENABLED")
    daily_budget_limit: float = Field(default=10.0, env="DAILY_BUDGET_LIMIT")
    monthly_budget_limit: float = Field(default=100.0, env="MONTHLY_BUDGET_LIMIT")

    # Circuit Breaker Settings
    circuit_breaker_failure_threshold: int = Field(default=5, env="CIRCUIT_BREAKER_FAILURE_THRESHOLD")
    circuit_breaker_recovery_timeout: int = Field(default=60, env="CIRCUIT_BREAKER_RECOVERY_TIMEOUT")

    # ADHD Optimization
    progressive_disclosure_enabled: bool = Field(default=True, env="PROGRESSIVE_DISCLOSURE_ENABLED")
    cognitive_load_monitoring: bool = Field(default=True, env="COGNITIVE_LOAD_MONITORING")

    # Performance Limits
    max_concurrent_requests: int = Field(default=10, env="MAX_CONCURRENT_REQUESTS")
    request_timeout_seconds: int = Field(default=60, env="REQUEST_TIMEOUT_SECONDS")

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
