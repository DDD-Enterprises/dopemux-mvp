"""
Configuration Manager for Dopemux.

Handles loading, saving, and merging of YAML/TOML configuration files
with support for environment variable substitution and ADHD-specific defaults.
"""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import toml
import yaml
from pydantic import BaseModel, Field, field_validator


class ADHDProfile(BaseModel):
    """ADHD user profile configuration."""

    focus_duration_avg: int = Field(
        default=25, description="Average focus duration in minutes"
    )
    break_interval: int = Field(default=5, description="Break interval in minutes")
    distraction_sensitivity: float = Field(
        default=0.5, description="Sensitivity to distractions (0-1)"
    )
    hyperfocus_tendency: bool = Field(
        default=False, description="Tendency to hyperfocus"
    )
    notification_style: str = Field(default="gentle", description="Notification style")
    visual_complexity: str = Field(
        default="minimal", description="Preferred visual complexity"
    )

    @field_validator("distraction_sensitivity")
    def validate_sensitivity(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Distraction sensitivity must be between 0 and 1")
        return v


class MCPServerConfig(BaseModel):
    """MCP Server configuration."""

    enabled: bool = True
    command: str
    args: list[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    timeout: int = 30
    auto_restart: bool = True


class AttentionConfig(BaseModel):
    """Attention monitoring configuration."""

    enabled: bool = True
    sample_interval: int = Field(default=5, description="Sampling interval in seconds")
    keystroke_threshold: float = Field(
        default=2.0, description="Keystrokes per second threshold"
    )
    context_switch_threshold: int = Field(
        default=3, description="Context switches per minute threshold"
    )
    adaptation_enabled: bool = True


class ContextConfig(BaseModel):
    """Context preservation configuration."""

    enabled: bool = True
    auto_save_interval: int = Field(
        default=30, description="Auto-save interval in seconds"
    )
    max_sessions: int = Field(default=50, description="Maximum sessions to keep")
    compression: bool = True
    backup_enabled: bool = True


class ClaudeAutoResponderConfig(BaseModel):
    """Claude Auto Responder configuration."""

    enabled: bool = Field(
        default=False, description="Enable automatic Claude Code confirmation responses"
    )
    terminal_scope: str = Field(
        default="current", description="Terminal scope: 'current', 'all', or 'project'"
    )
    response_delay: float = Field(default=0.0, description="Response delay in seconds")
    timeout_minutes: int = Field(
        default=30, description="Auto-stop after X minutes of inactivity"
    )
    whitelist_tools: bool = Field(
        default=True, description="Only respond to whitelisted tools"
    )
    debug_mode: bool = Field(default=False, description="Enable debug logging")

    @field_validator("response_delay")
    def validate_delay(cls, v):
        if v < 0 or v > 10:
            raise ValueError("Response delay must be between 0 and 10 seconds")
        return v

    @field_validator("terminal_scope")
    def validate_scope(cls, v):
        if v not in ["current", "all", "project"]:
            raise ValueError('Terminal scope must be "current", "all", or "project"')
        return v


class DopemuxConfig(BaseModel):
    """Main Dopemux configuration."""

    version: str = "1.0"
    adhd_profile: ADHDProfile = Field(default_factory=ADHDProfile)
    mcp_servers: Dict[str, MCPServerConfig] = Field(default_factory=dict)
    attention: AttentionConfig = Field(default_factory=AttentionConfig)
    context: ContextConfig = Field(default_factory=ContextConfig)
    claude_autoresponder: ClaudeAutoResponderConfig = Field(
        default_factory=ClaudeAutoResponderConfig
    )
    claude_path: Optional[str] = None
    project_templates: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


@dataclass
class ConfigPaths:
    """Configuration file paths."""

    global_config: Path
    user_config: Path
    project_config: Path
    cache_dir: Path
    data_dir: Path


class ConfigManager:
    """
    Manages configuration loading, saving, and merging for Dopemux.

    Supports hierarchical configuration with:
    - Global defaults
    - User-specific settings
    - Project-specific overrides
    - Environment variable substitution
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager."""
        self.paths = self._init_paths(config_path)
        self._config: Optional[DopemuxConfig] = None
        self._env_cache: Dict[str, str] = {}

    def _init_paths(self, config_path: Optional[str] = None) -> ConfigPaths:
        """Initialize configuration paths."""
        home = Path.home()
        cwd = Path.cwd()

        if config_path:
            user_config = Path(config_path)
        else:
            user_config = home / ".config" / "dopemux" / "config.yaml"

        return ConfigPaths(
            global_config=Path(__file__).parent.parent / "data" / "default_config.yaml",
            user_config=user_config,
            project_config=cwd / ".dopemux" / "config.yaml",
            cache_dir=home / ".cache" / "dopemux",
            data_dir=home / ".local" / "share" / "dopemux",
        )

    def load_config(self) -> DopemuxConfig:
        """
        Load and merge configuration from all sources.

        Returns:
            Merged configuration with environment variable substitution
        """
        if self._config is not None:
            return self._config

        # Start with defaults
        config_dict = self._get_default_config()

        # Load and merge user config
        if self.paths.user_config.exists():
            user_config = self._load_file(self.paths.user_config)
            config_dict = self._deep_merge(config_dict, user_config)

        # Load and merge project config
        if self.paths.project_config.exists():
            project_config = self._load_file(self.paths.project_config)
            config_dict = self._deep_merge(config_dict, project_config)

        # Substitute environment variables
        config_dict = self._substitute_env_vars(config_dict)

        # Validate and create config object
        self._config = DopemuxConfig(**config_dict)
        return self._config

    def save_user_config(self, config: DopemuxConfig) -> None:
        """Save user configuration to file."""
        self.paths.user_config.parent.mkdir(parents=True, exist_ok=True)

        config_dict = config.dict(exclude_defaults=True)
        with open(self.paths.user_config, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)

    def save_project_config(self, config: DopemuxConfig) -> None:
        """Save project-specific configuration."""
        self.paths.project_config.parent.mkdir(parents=True, exist_ok=True)

        # Only save project-specific settings
        project_config = {
            "mcp_servers": config.mcp_servers,
            "project_templates": config.project_templates,
        }

        with open(self.paths.project_config, "w") as f:
            yaml.dump(project_config, f, default_flow_style=False, indent=2)

    def get_mcp_servers(self) -> Dict[str, MCPServerConfig]:
        """Get MCP server configurations."""
        config = self.load_config()
        return config.mcp_servers

    def add_mcp_server(self, name: str, server_config: MCPServerConfig) -> None:
        """Add or update MCP server configuration."""
        config = self.load_config()
        config.mcp_servers[name] = server_config
        self.save_user_config(config)

    def remove_mcp_server(self, name: str) -> bool:
        """Remove MCP server configuration."""
        config = self.load_config()
        if name in config.mcp_servers:
            del config.mcp_servers[name]
            self.save_user_config(config)
            return True
        return False

    def update_adhd_profile(self, **kwargs) -> None:
        """Update ADHD profile settings."""
        config = self.load_config()
        for key, value in kwargs.items():
            if hasattr(config.adhd_profile, key):
                setattr(config.adhd_profile, key, value)
        self.save_user_config(config)

    def get_claude_autoresponder_config(self) -> ClaudeAutoResponderConfig:
        """Get Claude Auto Responder configuration."""
        config = self.load_config()
        return config.claude_autoresponder

    def update_claude_autoresponder(self, **kwargs) -> None:
        """Update Claude Auto Responder settings."""
        config = self.load_config()
        for key, value in kwargs.items():
            if hasattr(config.claude_autoresponder, key):
                setattr(config.claude_autoresponder, key, value)
        self.save_user_config(config)

    def get_claude_settings(self) -> Dict[str, Any]:
        """Get Claude Code settings for MCP integration."""
        config = self.load_config()

        # Build MCP servers section for Claude settings.json
        mcp_servers = {}
        for name, server_config in config.mcp_servers.items():
            if server_config.enabled:
                mcp_servers[name] = {
                    "type": "stdio",
                    "command": server_config.command,
                    "args": server_config.args,
                    "env": server_config.env,
                }

        return {
            "mcpServers": mcp_servers,
            "env": {"MCP_TOOL_TIMEOUT": "40000", "MAX_MCP_OUTPUT_TOKENS": "10000"},
        }

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "version": "1.0",
            "adhd_profile": {
                "focus_duration_avg": 25,
                "break_interval": 5,
                "distraction_sensitivity": 0.5,
                "hyperfocus_tendency": False,
                "notification_style": "gentle",
                "visual_complexity": "minimal",
            },
            "mcp_servers": self._get_default_mcp_servers(),
            "attention": {
                "enabled": True,
                "sample_interval": 5,
                "keystroke_threshold": 2.0,
                "context_switch_threshold": 3,
                "adaptation_enabled": True,
            },
            "context": {
                "enabled": True,
                "auto_save_interval": 30,
                "max_sessions": 50,
                "compression": True,
                "backup_enabled": True,
            },
            "claude_autoresponder": {
                "enabled": False,
                "terminal_scope": "current",
                "response_delay": 0.0,
                "timeout_minutes": 30,
                "whitelist_tools": True,
                "debug_mode": False,
            },
            "project_templates": self._get_project_templates(),
        }

    def _get_default_mcp_servers(self) -> Dict[str, Dict[str, Any]]:
        """Get default MCP server configurations."""
        return {
            "mas-sequential-thinking": {
                "enabled": True,
                "command": "python",
                "args": ["/Users/hue/code/mcp-server-mas-sequential-thinking/main.py"],
                "env": {
                    "LLM_PROVIDER": "openai",
                    "OPENAI_API_KEY": "${OPENAI_API_KEY}",
                    "EXA_API_KEY": "${EXA_API_KEY}",
                },
                "timeout": 60,
                "auto_restart": True,
            },
            "context7": {
                "enabled": True,
                "command": "npx",
                "args": ["-y", "context7-mcp"],
                "env": {},
                "timeout": 30,
                "auto_restart": True,
            },
            "claude-context": {
                "enabled": True,
                "command": "npx",
                "args": ["-y", "@zilliz/claude-context-mcp@latest"],
                "env": {
                    "EMBEDDING_PROVIDER": "voyage",
                    "EMBEDDING_MODEL": "voyage-code-2",
                    "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}",
                    "MILVUS_ADDRESS": "localhost:19530",
                    "HYBRID_SEARCH": "true",
                    "BM25_WEIGHT": "0.3",
                    "VECTOR_WEIGHT": "0.7",
                },
                "timeout": 45,
                "auto_restart": True,
            },
            "morphllm-fast-apply": {
                "enabled": True,
                "command": "npx",
                "args": ["-y", "morphllm-fast-apply-mcp"],
                "env": {},
                "timeout": 30,
                "auto_restart": True,
            },
            "exa": {
                "enabled": True,
                "command": "npx",
                "args": ["-y", "exa-mcp"],
                "env": {"EXA_API_KEY": "${EXA_API_KEY}"},
                "timeout": 30,
                "auto_restart": True,
            },
            "zen": {
                "enabled": True,
                "command": "npx",
                "args": ["-y", "zen-mcp"],
                "env": {
                    "OPENAI_API_KEY": "${OPENAI_API_KEY}",
                    "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}",
                    "GEMINI_API_KEY": "${GEMINI_API_KEY}",
                    "GROQ_API_KEY": "${GROQ_API_KEY}",
                    "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}",
                    "ZEN_DISABLED_TOOLS": "chat,explain,translate,summarize",
                },
                "timeout": 60,
                "auto_restart": True,
            },
            "leantime": {
                "enabled": False,  # Disabled by default until package is fixed
                "command": "npx",
                "args": ["-y", "leantime-mcp"],
                "env": {
                    "LEANTIME_URL": "${LEANTIME_URL}",
                    "LEANTIME_API_KEY": "${LEANTIME_API_KEY}",
                },
                "timeout": 30,
                "auto_restart": True,
            },
        }

    def _get_project_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get project template configurations."""
        return {
            "python": {
                "files": [
                    ".claude/claude.md",
                    ".claude/session.md",
                    ".claude/context.md",
                    ".claude/llms.md",
                ],
                "mcp_servers": [
                    "mas-sequential-thinking",
                    "context7",
                    "claude-context",
                ],
                "adhd_adaptations": {
                    "focus_duration_avg": 30,
                    "notification_style": "gentle",
                },
            },
            "javascript": {
                "files": [
                    ".claude/claude.md",
                    ".claude/session.md",
                    ".claude/context.md",
                    ".claude/llms.md",
                ],
                "mcp_servers": ["context7", "claude-context", "morphllm-fast-apply"],
                "adhd_adaptations": {
                    "focus_duration_avg": 25,
                    "visual_complexity": "minimal",
                },
            },
            "rust": {
                "files": [
                    ".claude/claude.md",
                    ".claude/session.md",
                    ".claude/context.md",
                    ".claude/llms.md",
                ],
                "mcp_servers": [
                    "mas-sequential-thinking",
                    "context7",
                    "claude-context",
                ],
                "adhd_adaptations": {
                    "focus_duration_avg": 35,
                    "distraction_sensitivity": 0.3,
                },
            },
        }

    def _load_file(self, path: Path) -> Dict[str, Any]:
        """Load configuration file (YAML or TOML)."""
        try:
            with open(path, "r") as f:
                if path.suffix.lower() in [".yaml", ".yml"]:
                    return yaml.safe_load(f) or {}
                elif path.suffix.lower() == ".toml":
                    return toml.load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {path.suffix}")
        except Exception as e:
            print(f"Warning: Failed to load config file {path}: {e}", file=sys.stderr)
            return {}

    def _deep_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _substitute_env_vars(self, obj: Any) -> Any:
        """Recursively substitute environment variables in configuration."""
        if isinstance(obj, dict):
            return {k: self._substitute_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_env_vars(item) for item in obj]
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            var_name = obj[2:-1]
            # Check cache first
            if var_name in self._env_cache:
                return self._env_cache[var_name]

            # Get from environment with optional default
            if ":" in var_name:
                var_name, default = var_name.split(":", 1)
            else:
                default = ""

            value = os.getenv(var_name, default)
            self._env_cache[var_name] = value
            return value
        else:
            return obj

    def ensure_directories(self) -> None:
        """Ensure all required directories exist."""
        for path in [self.paths.cache_dir, self.paths.data_dir]:
            path.mkdir(parents=True, exist_ok=True)

        # Create user config directory if it doesn't exist
        self.paths.user_config.parent.mkdir(parents=True, exist_ok=True)

    def get_data_path(self, *parts: str) -> Path:
        """Get path within data directory."""
        return self.paths.data_dir.joinpath(*parts)

    def get_cache_path(self, *parts: str) -> Path:
        """Get path within cache directory."""
        return self.paths.cache_dir.joinpath(*parts)
