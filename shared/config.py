"""
Configuration Management System for ADHD Services

Provides centralized configuration management with environment overrides,
validation, and dynamic reloading capabilities for all ADHD services.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List, Type, Union
from pathlib import Path
from dataclasses import dataclass, field, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class Environment(str, Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://dopemux_age:dopemux_age_dev_password@dopemux-postgres-age:5432/dopemux_knowledge_graph"
    )
    pool_min_size: int = 5
    pool_max_size: int = 20
    connection_timeout: float = 30.0


@dataclass
class RedisConfig:
    """Redis configuration."""
    url: str = os.getenv("REDIS_URL", "redis://redis-primary:6379")
    max_connections: int = 20
    connection_timeout: float = 5.0
    retry_on_timeout: bool = True


@dataclass
class CacheConfig:
    """Cache configuration."""
    default_ttl: int = 300  # 5 minutes
    max_memory_mb: int = 100


@dataclass
class ServiceDiscoveryConfig:
    """Service discovery configuration."""
    dns_timeout: float = 5.0
    health_check_interval: int = 30
    enable_dns_fallback: bool = True


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    enabled: bool = True
    metrics_interval: int = 60  # seconds
    health_check_interval: int = 30
    log_level: str = "INFO"


@dataclass
class SecurityConfig:
    """Security configuration."""
    cors_allow_origins: List[str] = field(default_factory=lambda: ["http://localhost:3000"])
    cors_allow_methods: List[str] = field(default_factory=lambda: ["GET", "POST"])
    cors_allow_headers: List[str] = field(default_factory=lambda: ["Content-Type", "Authorization", "X-API-Key"])
    rate_limit_requests: int = 100
    rate_limit_window_seconds: int = 60
    enable_api_auth: bool = True
    api_key_header: str = "X-API-Key"


@dataclass
class ADHDServiceConfig:
    """ADHD-specific service configuration."""
    user_id: Optional[str] = None
    workspace_id: str = "/Users/hue/code/dopemux-mvp"
    complexity_threshold: float = 0.6
    session_timeout_minutes: int = 120
    break_frequency_minutes: int = 25
    energy_check_interval: int = 30
    context_switch_threshold: int = 10


@dataclass
class ApplicationConfig:
    """Main application configuration."""
    environment: Environment = Environment.DEVELOPMENT
    service_name: str = "unknown"

    # Component configs
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    service_discovery: ServiceDiscoveryConfig = field(default_factory=ServiceDiscoveryConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    adhd: ADHDServiceConfig = field(default_factory=ADHDServiceConfig)

    # Service-specific settings
    api_port: int = 8000
    api_host: str = "0.0.0.0"
    log_level: str = "INFO"
    debug_mode: bool = False


class ConfigurationManager:
    """
    Centralized configuration management system.

    Provides environment-based configuration with validation,
    hot reloading, and structured access patterns.
    """

    def __init__(self, service_name: str = "unknown"):
        self.service_name = service_name
        self.config = ApplicationConfig(service_name=service_name)
        self.config_files: List[Path] = []
        self.environment_overrides: Dict[str, Any] = {}
        self.validators: List[callable] = []

        # Setup default config files
        self._setup_config_files()

        # Setup validators
        self._setup_validators()

    def _setup_config_files(self):
        """Setup configuration file search paths."""
        # Service-specific config
        service_config = Path(f"config/{self.service_name}.json")
        self.config_files.append(service_config)

        # Global config
        global_config = Path("config/global.json")
        self.config_files.append(global_config)

        # Environment-specific config
        env = os.getenv("ENVIRONMENT", "development")
        env_config = Path(f"config/{env}.json")
        self.config_files.append(env_config)

    def _setup_validators(self):
        """Setup configuration validators."""
        self.validators.extend([
            self._validate_database_config,
            self._validate_redis_config,
            self._validate_security_config,
            self._validate_network_config
        ])

    async def load_config(self) -> ApplicationConfig:
        """
        Load configuration from files and environment.

        Returns:
            Loaded and validated configuration
        """
        # Load from config files
        for config_file in self.config_files:
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        file_config = json.load(f)
                        self._merge_config(file_config)
                    logger.info(f"Loaded config from {config_file}")
                except Exception as e:
                    logger.warning(f"Failed to load config from {config_file}: {e}")

        # Apply environment overrides
        self._apply_environment_overrides()

        # Validate configuration
        await self._validate_config()

        logger.info(f"Configuration loaded for service: {self.service_name}")
        return self.config

    def _merge_config(self, file_config: Dict[str, Any]):
        """
        Merge file configuration into main config.

        Args:
            file_config: Configuration from file
        """
        # Handle nested configurations
        for key, value in file_config.items():
            if hasattr(self.config, key):
                current_value = getattr(self.config, key)
                if hasattr(current_value, '__dict__'):
                    # Nested config object
                    for nested_key, nested_value in value.items():
                        if hasattr(current_value, nested_key):
                            setattr(current_value, nested_key, nested_value)
                else:
                    # Simple value
                    setattr(self.config, key, value)

    def _apply_environment_overrides(self):
        """Apply environment variable overrides."""
        # Environment
        if env := os.getenv("ENVIRONMENT"):
            try:
                self.config.environment = Environment(env.lower())
            except ValueError:
                logger.warning(f"Invalid ENVIRONMENT: {env}")

        # Database
        if db_url := os.getenv("DATABASE_URL"):
            self.config.database.url = db_url

        # Redis
        if redis_url := os.getenv("REDIS_URL"):
            self.config.redis.url = redis_url

        # Security
        if origins := os.getenv("ALLOWED_ORIGINS"):
            self.config.security.cors_allow_origins = origins.split(",")

        # Service-specific
        if port := os.getenv("API_PORT"):
            self.config.api_port = int(port)
        if host := os.getenv("API_HOST"):
            self.config.api_host = host
        if log_level := os.getenv("LOG_LEVEL"):
            self.config.log_level = log_level
            self.config.monitoring.log_level = log_level

        # ADHD-specific
        if user_id := os.getenv("ADHD_USER_ID"):
            self.config.adhd.user_id = user_id
        if workspace_id := os.getenv("WORKSPACE_ID"):
            self.config.adhd.workspace_id = workspace_id

    async def _validate_config(self):
        """Validate configuration."""
        for validator in self.validators:
            await validator()

    async def _validate_database_config(self):
        """Validate database configuration."""
        db_config = self.config.database

        if not db_config.url:
            raise ValueError("Database URL is required")

        if not db_config.url.startswith("postgresql://"):
            raise ValueError("Only PostgreSQL databases are supported")

        if db_config.pool_max_size < db_config.pool_min_size:
            raise ValueError("Pool max size must be >= min size")

    async def _validate_redis_config(self):
        """Validate Redis configuration."""
        redis_config = self.config.redis

        if not redis_config.url:
            raise ValueError("Redis URL is required")

        if not redis_config.url.startswith(("redis://", "rediss://")):
            raise ValueError("Invalid Redis URL format")

        if redis_config.max_connections < 1:
            raise ValueError("Max connections must be >= 1")

    async def _validate_security_config(self):
        """Validate security configuration."""
        security_config = self.config.security

        # Validate CORS origins
        for origin in security_config.cors_allow_origins:
            if not origin.startswith(("http://", "https://")):
                logger.warning(f"CORS origin may be invalid: {origin}")

        # Validate rate limits
        if security_config.rate_limit_requests < 1:
            raise ValueError("Rate limit requests must be >= 1")

        if security_config.rate_limit_window_seconds < 1:
            raise ValueError("Rate limit window must be >= 1 second")

    async def _validate_network_config(self):
        """Validate network configuration."""
        if self.config.api_port < 1 or self.config.api_port > 65535:
            raise ValueError("API port must be between 1 and 65535")

        # Validate service discovery config
        if self.config.service_discovery.health_check_interval < 5:
            raise ValueError("Health check interval must be >= 5 seconds")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.

        Args:
            key: Dot-separated key (e.g., "database.url")
            default: Default value if not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        try:
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                else:
                    return default
            return value
        except Exception as e:
            return default

            logger.error(f"Error: {e}")
    def set(self, key: str, value: Any):
        """
        Set configuration value.

        Args:
            key: Dot-separated key
            value: Value to set
        """
        keys = key.split('.')
        obj = self.config

        for k in keys[:-1]:
            if not hasattr(obj, k):
                setattr(obj, k, type('', (), {})())  # Create empty object
            obj = getattr(obj, k)

        setattr(obj, keys[-1], value)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self.config)

    def save_to_file(self, file_path: str):
        """
        Save current configuration to file.

        Args:
            file_path: Path to save configuration
        """
        config_dict = self.to_dict()

        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)

        logger.info(f"Configuration saved to {file_path}")

    async def reload_config(self):
        """Reload configuration from sources."""
        old_config = self.config
        self.config = ApplicationConfig(service_name=self.service_name)

        try:
            await self.load_config()
            logger.info("Configuration reloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Configuration reload failed: {e}")
            self.config = old_config  # Rollback
            return False


# Global configuration instance
_config_manager: Optional[ConfigurationManager] = None

async def get_config_manager(service_name: str = "unknown") -> ConfigurationManager:
    """Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None or _config_manager.service_name != service_name:
        _config_manager = ConfigurationManager(service_name)
        await _config_manager.load_config()
    return _config_manager

async def get_config(service_name: str = "unknown") -> ApplicationConfig:
    """Get application configuration."""
    manager = await get_config_manager(service_name)
    return manager.config

async def config_get(key: str, default: Any = None, service_name: str = "unknown") -> Any:
    """Get configuration value."""
    manager = await get_config_manager(service_name)
    return manager.get(key, default)

async def config_set(key: str, value: Any, service_name: str = "unknown"):
    """Set configuration value."""
    manager = await get_config_manager(service_name)
    manager.set(key, value)