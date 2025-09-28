# Configuration Management Context

**Scope**: System configuration, environment management, and settings
**Inherits**: Two-Plane Architecture from project root
**Focus**: Clear, maintainable configuration with ADHD-friendly organization

## ⚙️ Configuration Philosophy

### ADHD-Optimized Configuration
- **Clear Structure**: Logical organization with intuitive naming conventions
- **Environment Separation**: Distinct configurations for development, staging, production
- **Validation**: Type-safe configuration with clear error messages
- **Documentation**: Well-documented settings with examples and purpose

### Configuration Principles
- **Single Source of Truth**: Centralized configuration management
- **Environment-Based**: Different settings for different deployment contexts
- **Secure by Default**: Sensitive data handled through secure channels
- **Fail-Fast**: Invalid configurations detected early with helpful errors

## 🎯 Configuration Standards

### Pydantic Settings Pattern
```python
# config/settings.py
"""
Application Settings
Purpose: Centralized configuration management with validation
ADHD-Friendly: Clear error messages and environment-based organization
"""

from typing import Optional, List
from pydantic import BaseSettings, Field, validator
from pydantic.networks import PostgresDsn, RedisDsn
import os

class DatabaseConfig(BaseSettings):
    """Database configuration with validation."""

    url: PostgresDsn = Field(
        ...,
        env="DATABASE_URL",
        description="PostgreSQL connection URL"
    )
    pool_size: int = Field(
        default=10,
        env="DATABASE_POOL_SIZE",
        description="Connection pool size"
    )
    echo_queries: bool = Field(
        default=False,
        env="DATABASE_ECHO_QUERIES",
        description="Log all SQL queries (development only)"
    )

    @validator("echo_queries")
    def validate_echo_queries(cls, v, values):
        """Only allow query echoing in development."""
        if v and os.getenv("ENVIRONMENT") == "production":
            raise ValueError("Query echoing not allowed in production")
        return v

class RedisConfig(BaseSettings):
    """Redis configuration with validation."""

    url: RedisDsn = Field(
        ...,
        env="REDIS_URL",
        description="Redis connection URL"
    )
    ttl_default: int = Field(
        default=3600,
        env="REDIS_TTL_DEFAULT",
        description="Default TTL for cached items (seconds)"
    )

class MCPConfig(BaseSettings):
    """MCP server configuration."""

    enabled_servers: List[str] = Field(
        default=["conport", "task-master", "serena"],
        env="MCP_ENABLED_SERVERS",
        description="List of enabled MCP servers"
    )
    base_port: int = Field(
        default=8080,
        env="MCP_BASE_PORT",
        description="Base port for MCP server allocation"
    )
    broker_url: str = Field(
        default="http://localhost:8090",
        env="MCP_BROKER_URL",
        description="MCP broker URL for server coordination"
    )

class ADHDConfig(BaseSettings):
    """ADHD-specific configuration."""

    attention_timeout: int = Field(
        default=1800,  # 30 minutes
        env="ADHD_ATTENTION_TIMEOUT",
        description="Attention timeout in seconds"
    )
    progress_update_interval: int = Field(
        default=10,
        env="ADHD_PROGRESS_INTERVAL",
        description="Progress update interval in seconds"
    )
    max_options_scattered: int = Field(
        default=1,
        env="ADHD_MAX_OPTIONS_SCATTERED",
        description="Maximum options when attention is scattered"
    )
    max_options_focused: int = Field(
        default=3,
        env="ADHD_MAX_OPTIONS_FOCUSED",
        description="Maximum options when attention is focused"
    )

class AppConfig(BaseSettings):
    """Main application configuration."""

    # Environment
    environment: str = Field(
        default="development",
        env="ENVIRONMENT",
        description="Deployment environment"
    )
    debug: bool = Field(
        default=False,
        env="DEBUG",
        description="Enable debug mode"
    )

    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        env="API_HOST",
        description="API server host"
    )
    api_port: int = Field(
        default=8000,
        env="API_PORT",
        description="API server port"
    )

    # Security
    secret_key: str = Field(
        ...,
        env="SECRET_KEY",
        description="Application secret key"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        env="JWT_ALGORITHM",
        description="JWT signing algorithm"
    )
    jwt_expiration: int = Field(
        default=3600,
        env="JWT_EXPIRATION",
        description="JWT token expiration in seconds"
    )

    # Component configurations
    database: DatabaseConfig = DatabaseConfig()
    redis: RedisConfig = RedisConfig()
    mcp: MCPConfig = MCPConfig()
    adhd: ADHDConfig = ADHDConfig()

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v

    @validator("debug")
    def validate_debug(cls, v, values):
        """Ensure debug is False in production."""
        if v and values.get("environment") == "production":
            raise ValueError("Debug mode not allowed in production")
        return v

# Global settings instance
settings = AppConfig()
```

### Environment Configuration Files
```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=postgresql://user:pass@localhost:5432/dopemux_dev
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=development-secret-key-change-in-production
MCP_ENABLED_SERVERS=["conport", "task-master", "serena", "zen-mcp"]
ADHD_ATTENTION_TIMEOUT=1800
ADHD_PROGRESS_INTERVAL=5

# .env.staging
ENVIRONMENT=staging
DEBUG=false
DATABASE_URL=postgresql://user:pass@staging-db:5432/dopemux_staging
REDIS_URL=redis://staging-redis:6379/0
SECRET_KEY=${STAGING_SECRET_KEY}
MCP_BROKER_URL=http://staging-mcp-broker:8090

# .env.production
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=${PRODUCTION_DATABASE_URL}
REDIS_URL=${PRODUCTION_REDIS_URL}
SECRET_KEY=${PRODUCTION_SECRET_KEY}
MCP_ENABLED_SERVERS=["conport", "task-master"]
ADHD_ATTENTION_TIMEOUT=3600
ADHD_PROGRESS_INTERVAL=30
```

## 🚀 Agent Coordination

### Developer Agent (Primary)
**For Configuration Development**:
- Implement type-safe configuration with proper validation
- Create environment-specific configuration files
- Ensure secure handling of sensitive configuration data
- Test configuration changes across different environments

### Architect Agent (Consultation)
**For Configuration Design**:
- Design configuration architecture and organization patterns
- Review security implications of configuration management
- Guide configuration versioning and deployment strategies
- Ensure configuration aligns with system architecture

### Configuration Quality Standards
- **Type Safety**: All configuration validated with clear error messages
- **Security**: Sensitive data never committed to version control
- **Environment Parity**: Consistent configuration structure across environments
- **Documentation**: Clear documentation for all configuration options

## 🔧 Configuration Patterns

### MCP Server Configuration
```yaml
# config/mcp/servers.yaml
servers:
  conport:
    enabled: true
    port: 8080
    path: "/Users/hue/code/dopemux-mvp/services/conport/venv/bin/conport-mcp"
    args: ["--mode", "stdio", "--workspace_id", "/Users/hue/code/dopemux-mvp"]
    description: "Context preservation and memory management"

  task-master:
    enabled: true
    port: 8081
    path: "/path/to/task-master/server"
    args: ["--mode", "stdio"]
    description: "AI-driven task decomposition"

  serena:
    enabled: false  # Enable when available
    port: 8082
    path: "/path/to/serena/lsp"
    args: ["--stdio"]
    description: "Enhanced code navigation and memory"

  zen-mcp:
    enabled: true
    port: 8083
    path: "/path/to/zen-mcp/server"
    args: ["--stdio"]
    description: "Multi-model coordination for complex tasks"

broker:
  url: "http://localhost:8090"
  enabled_servers: ["conport", "task-master", "zen-mcp"]
  health_check_interval: 30
```

### Logging Configuration
```yaml
# config/logging.yaml
version: 1
disable_existing_loggers: false

formatters:
  detailed:
    format: "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    datefmt: "%Y-%m-%d %H:%M:%S"

  simple:
    format: "%(levelname)s - %(message)s"

  json:
    class: "pythonjsonlogger.jsonlogger.JsonFormatter"
    format: "%(asctime)s %(name)s %(levelname)s %(filename)s %(lineno)d %(message)s"

handlers:
  console:
    class: "logging.StreamHandler"
    level: "INFO"
    formatter: "detailed"
    stream: "ext://sys.stdout"

  file:
    class: "logging.handlers.RotatingFileHandler"
    level: "DEBUG"
    formatter: "json"
    filename: "logs/dopemux.log"
    maxBytes: 10485760  # 10MB
    backupCount: 5

  error_file:
    class: "logging.handlers.RotatingFileHandler"
    level: "ERROR"
    formatter: "detailed"
    filename: "logs/dopemux_errors.log"
    maxBytes: 10485760  # 10MB
    backupCount: 5

loggers:
  dopemux:
    level: "DEBUG"
    handlers: ["console", "file"]
    propagate: false

  uvicorn:
    level: "INFO"
    handlers: ["console"]
    propagate: false

  sqlalchemy.engine:
    level: "WARN"
    handlers: ["console"]
    propagate: false

root:
  level: "INFO"
  handlers: ["console", "error_file"]
```

## 📁 Configuration Organization

### Directory Structure
```
config/
├── environments/         # Environment-specific configurations
│   ├── development.yml   # Development environment
│   ├── staging.yml      # Staging environment
│   └── production.yml   # Production environment
├── mcp/                 # MCP server configurations
│   ├── broker.yaml      # MCP broker configuration
│   ├── servers.yaml     # Individual server configurations
│   └── proxy-config.json # MCP proxy configuration
├── docker/              # Container-specific configurations
│   ├── compose-dev.yml  # Development Docker Compose
│   ├── compose-prod.yml # Production Docker Compose
│   └── env-templates/   # Environment file templates
├── logging/             # Logging configurations
│   ├── development.yaml # Development logging
│   ├── production.yaml  # Production logging
│   └── structured.yaml  # Structured logging format
└── docs/                # Configuration documentation
    ├── environment-setup.md
    ├── mcp-configuration.md
    └── deployment-guide.md
```

### Configuration Validation
```python
# config/validator.py
"""
Configuration Validation
Purpose: Validate configuration files and environment setup
ADHD-Friendly: Clear error messages with specific fix suggestions
"""

import yaml
import os
from pathlib import Path
from typing import List, Dict, Any

class ConfigValidator:
    """Validate configuration files with helpful error messages."""

    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self) -> bool:
        """Validate all configuration files."""
        print("🔍 Validating configuration files...")

        # Validate environment files
        self.validate_environment_files()

        # Validate MCP configuration
        self.validate_mcp_configuration()

        # Validate logging configuration
        self.validate_logging_configuration()

        # Report results
        self.report_results()

        return len(self.errors) == 0

    def validate_environment_files(self):
        """Validate environment-specific configuration files."""
        env_dir = self.config_dir / "environments"
        required_files = ["development.yml", "staging.yml", "production.yml"]

        for filename in required_files:
            file_path = env_dir / filename
            if not file_path.exists():
                self.errors.append(f"❌ Missing environment file: {file_path}")
                continue

            try:
                with open(file_path) as f:
                    config = yaml.safe_load(f)
                    self.validate_environment_config(config, filename)
            except yaml.YAMLError as e:
                self.errors.append(f"❌ Invalid YAML in {filename}: {e}")

    def validate_environment_config(self, config: Dict[str, Any], filename: str):
        """Validate individual environment configuration."""
        required_keys = ["database", "redis", "api", "security"]

        for key in required_keys:
            if key not in config:
                self.errors.append(f"❌ Missing '{key}' section in {filename}")

        # Validate security settings
        if "security" in config:
            security = config["security"]
            if not security.get("secret_key"):
                self.errors.append(f"❌ Missing secret_key in {filename}")

    def validate_mcp_configuration(self):
        """Validate MCP server configuration."""
        mcp_config_path = self.config_dir / "mcp" / "servers.yaml"

        if not mcp_config_path.exists():
            self.warnings.append("⚠️ MCP configuration not found")
            return

        try:
            with open(mcp_config_path) as f:
                config = yaml.safe_load(f)

            if "servers" not in config:
                self.errors.append("❌ Missing 'servers' section in MCP config")
                return

            for server_name, server_config in config["servers"].items():
                self.validate_mcp_server(server_name, server_config)

        except yaml.YAMLError as e:
            self.errors.append(f"❌ Invalid MCP configuration YAML: {e}")

    def validate_mcp_server(self, name: str, config: Dict[str, Any]):
        """Validate individual MCP server configuration."""
        required_keys = ["enabled", "path", "description"]

        for key in required_keys:
            if key not in config:
                self.errors.append(f"❌ Missing '{key}' in MCP server '{name}'")

        # Check if server path exists (when enabled)
        if config.get("enabled") and "path" in config:
            path = Path(config["path"])
            if not path.exists():
                self.warnings.append(f"⚠️ MCP server path not found: {path}")

    def report_results(self):
        """Report validation results with ADHD-friendly formatting."""
        print()
        print("📊 Configuration Validation Results")
        print("=" * 40)

        if self.errors:
            print(f"❌ {len(self.errors)} Error(s) Found:")
            for error in self.errors:
                print(f"  {error}")
            print()

        if self.warnings:
            print(f"⚠️  {len(self.warnings)} Warning(s):")
            for warning in self.warnings:
                print(f"  {warning}")
            print()

        if not self.errors and not self.warnings:
            print("✅ All configuration files are valid!")
        elif not self.errors:
            print("✅ Configuration is valid (warnings noted)")
        else:
            print("❌ Configuration validation failed")
            print("💡 Fix the errors above and run validation again")

# Usage script
if __name__ == "__main__":
    config_dir = Path(__file__).parent
    validator = ConfigValidator(config_dir)

    if validator.validate_all():
        exit(0)
    else:
        exit(1)
```

## 🎯 ADHD-Friendly Configuration Features

### Environment Detection
```python
# config/environment.py
"""
Environment Detection and Auto-Configuration
ADHD-Friendly: Automatic environment detection with clear feedback
"""

import os
from pathlib import Path
from typing import Optional

class EnvironmentDetector:
    """Detect and configure environment automatically."""

    @staticmethod
    def detect_environment() -> str:
        """Detect current environment with clear logic."""
        # Check explicit environment variable
        env = os.getenv("ENVIRONMENT")
        if env:
            print(f"🎯 Environment set explicitly: {env}")
            return env

        # Check for environment indicators
        if os.getenv("KUBERNETES_SERVICE_HOST"):
            print("🐳 Kubernetes environment detected: production")
            return "production"

        if os.getenv("CI"):
            print("🔧 CI environment detected: staging")
            return "staging"

        if Path(".env.development").exists():
            print("💻 Development files detected: development")
            return "development"

        print("❓ Unable to detect environment, defaulting to development")
        return "development"

    @staticmethod
    def load_environment_config(env: Optional[str] = None) -> dict:
        """Load configuration for detected or specified environment."""
        if not env:
            env = EnvironmentDetector.detect_environment()

        config_file = Path(f"config/environments/{env}.yml")

        if not config_file.exists():
            raise FileNotFoundError(
                f"❌ Configuration file not found: {config_file}\n"
                f"💡 Create the file or check the environment name"
            )

        print(f"📁 Loading configuration from: {config_file}")

        with open(config_file) as f:
            return yaml.safe_load(f)
```

---

**Configuration Excellence**: Type-safe, validated configuration with clear organization
**ADHD Integration**: Clear error messages, environment detection, and helpful validation
**Security First**: Secure handling of sensitive data with environment-based protection