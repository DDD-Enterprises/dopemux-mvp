"""
Configuration Manager for Dopemux.

Handles loading, saving, and merging of YAML/TOML configuration files
with support for environment variable substitution and ADHD-specific defaults.
"""

from __future__ import annotations
import logging
import os
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Literal

import toml
import yaml
from pydantic import BaseModel, Field, field_validator


from ..mcp.registry import MCPRegistry


logger = logging.getLogger(__name__)


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


class MobileConfig(BaseModel):
    """Mobile mode configuration for Happy client integration."""

    enabled: bool = Field(default=False, description="Enable Dopemux mobile integrations")
    happy_server_url: Optional[str] = Field(
        default=None, description="Custom Happy relay base URL"
    )
    happy_webapp_url: Optional[str] = Field(
        default=None, description="Custom Happy webapp URL"
    )
    default_panes: Union[str, List[str]] = Field(
        default="primary",
        description="Default Claude panes to mirror (primary, all, or explicit names)",
    )
    popup_mode: bool = Field(
        default=False,
        description="Use tmux popup for ephemeral Happy session instead of panes",
    )

    @field_validator("default_panes")
    @classmethod
    def validate_default_panes(cls, value: Union[str, List[str]]):
        if isinstance(value, str):
            allowed = {"primary", "all"}
            if value.lower() in allowed:
                return value.lower()
            if not value:
                raise ValueError("default_panes must not be empty")
            return value
        if isinstance(value, list):
            if not value:
                raise ValueError("default_panes list must not be empty")
            for item in value:
                if not isinstance(item, str) or not item.strip():
                    raise ValueError("default_panes list entries must be non-empty strings")
            return [item.strip() for item in value]
        raise ValueError("default_panes must be 'primary', 'all', or a list of pane names")


class TmuxPresetConfig(BaseModel):
    """Configuration describing how to launch a preset tmux pane."""

    command: str
    cwd: Optional[str] = None
    window: Optional[str] = None
    focus: bool = True
    environment: Dict[str, str] = Field(default_factory=dict)


class DopeLayoutTransientThresholds(BaseModel):
    """Threshold configuration for Dope layout transient messages."""

    untracked_warning_days: int = Field(default=1, ge=0)
    untracked_critical_days: int = Field(default=7, ge=1)
    break_reminder_minutes: List[int] = Field(default_factory=lambda: [25, 45, 90])


class DopeLayoutTransientConfig(BaseModel):
    """Transient message preferences for the Dope layout."""

    enabled: bool = True
    untracked_work: bool = True
    context_switches: bool = True
    task_drift: bool = True
    break_reminders: bool = False
    thresholds: DopeLayoutTransientThresholds = Field(default_factory=DopeLayoutTransientThresholds)


class DopeLayoutPMConfig(BaseModel):
    """PM mode configuration for the Dope layout."""

    leantime_url: str = "http://localhost:3007"
    conport_url: str = "http://localhost:3009"
    auto_switch: bool = False


class DopeLayoutServicesConfig(BaseModel):
    """External service endpoints used by the Dope layout."""

    adhd_engine_url: str = "http://localhost:3008"
    activity_capture_url: str = "http://localhost:3006"
    serena_url: str = "http://localhost:3010"
    litellm_url: str = "http://localhost:4000"
    docker_compose_bin: str = "docker compose"


class DopeLayoutConfig(BaseModel):
    """Dope layout configuration surface."""

    default_mode: Literal["implementation", "pm"] = "implementation"
    metrics_bar_enabled: bool = True
    transient_messages: DopeLayoutTransientConfig = Field(default_factory=DopeLayoutTransientConfig)
    pm_mode: DopeLayoutPMConfig = Field(default_factory=DopeLayoutPMConfig)
    services: DopeLayoutServicesConfig = Field(default_factory=DopeLayoutServicesConfig)
    state_file: Optional[str] = None


class TmuxControllerConfig(BaseModel):
    """Settings for the Dopemux tmux controller."""

    enabled: bool = True
    default_session: Optional[str] = None
    allowed_sessions: List[str] = Field(default_factory=list)
    presets: Dict[str, TmuxPresetConfig] = Field(default_factory=dict)
    send_rate_limit_seconds: float = Field(default=0.15, ge=0.0)
    capture_default_lines: int = Field(default=200, ge=1, le=2000)
    default_layout: Literal["low", "medium", "high", "orchestrator", "dope"] = "dope"
    monitor_commands: Dict[str, str] = Field(default_factory=dict)
    orchestrator_command: Optional[str] = None
    sandbox_command: Optional[str] = None
    dual_agent_default: bool = False
    secondary_agent_command: Optional[str] = None
    pane_styles: Dict[str, str] = Field(default_factory=dict)
    pane_border_styles: Dict[str, str] = Field(default_factory=dict)
    status_style: Optional[str] = None
    status_left: Optional[str] = None
    status_right: Optional[str] = None
    status_palette: Dict[str, str] = Field(default_factory=dict)
    theme: Optional[str] = None

    @field_validator("allowed_sessions")
    @classmethod
    def normalize_allowed_sessions(cls, value: List[str]) -> List[str]:
        return [item.strip() for item in value if item and item.strip()]


class DopemuxConfig(BaseModel):
    """Main Dopemux configuration."""

    version: str = "1.0"
    mcp_mode: Literal["auto", "docker", "local"] = "auto"
    adhd_profile: ADHDProfile = Field(default_factory=ADHDProfile)
    mcp_servers: Dict[str, MCPServerConfig] = Field(default_factory=dict)
    attention: AttentionConfig = Field(default_factory=AttentionConfig)
    context: ContextConfig = Field(default_factory=ContextConfig)
    claude_autoresponder: ClaudeAutoResponderConfig = Field(
        default_factory=ClaudeAutoResponderConfig
    )
    claude_path: Optional[str] = None
    project_templates: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    mobile: MobileConfig = Field(default_factory=MobileConfig)
    tmux: TmuxControllerConfig = Field(default_factory=TmuxControllerConfig)
    dope_layout: DopeLayoutConfig = Field(default_factory=DopeLayoutConfig)


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

        user_config: Dict[str, Any] = {}
        project_config: Dict[str, Any] = {}

        # Load and merge user config
        if self.paths.user_config.exists():
            user_config = self._load_file(self.paths.user_config)
            config_dict = self._deep_merge(config_dict, user_config)

        # Load and merge project config
        if self.paths.project_config.exists():
            project_config = self._load_file(self.paths.project_config)
            config_dict = self._deep_merge(config_dict, project_config)

        # If the user has not explicitly configured mcp_servers, regenerate from
        # the canonical registry using the effective mode after all merges.
        explicit_mcp_servers = ("mcp_servers" in user_config) or ("mcp_servers" in project_config)
        if not explicit_mcp_servers:
            mcp_mode = str(config_dict.get("mcp_mode", "auto"))
            dope_layout = config_dict.get("dope_layout", {}) or {}
            services = dope_layout.get("services", {}) or {}
            docker_compose_bin = str(services.get("docker_compose_bin", "docker compose"))
            config_dict["mcp_servers"] = self._get_default_mcp_servers(
                mcp_mode=mcp_mode,
                docker_compose_bin=docker_compose_bin,
            )

        # Substitute environment variables
        config_dict = self._substitute_env_vars(config_dict)

        # Validate and create config object
        self._config = DopemuxConfig(**config_dict)
        self._repair_legacy_mcp_servers(self._config)

        # Remove servers requested for deprecation
        for deprecated in ("repo_prompt", "trigger"):
            self._config.mcp_servers.pop(deprecated, None)

        return self._config

    def _repair_legacy_mcp_servers(self, config: DopemuxConfig) -> None:
        """Repair known-broken legacy MCP entries in existing user configs."""
        if not config.mcp_servers:
            return

        try:
            registry = MCPRegistry()
        except Exception:
            return

        compose_bin = config.dope_layout.services.docker_compose_bin
        configured_mode = config.mcp_mode

        def _generate(name: str) -> Optional[Dict[str, Any]]:
            generated = self._generate_server_config(
                registry,
                name,
                configured_mode,
                docker_compose_bin=compose_bin,
            )
            if generated:
                return generated
            return self._generate_server_config(
                registry,
                name,
                "local",
                docker_compose_bin=compose_bin,
            )

        # Repair legacy dope-context wrapper when referenced script is missing.
        dope_context = config.mcp_servers.get("dope-context")
        if dope_context:
            missing_wrapper = any(
                isinstance(arg, str) and "services/dope-context/run_mcp.sh" in arg
                for arg in dope_context.args
            ) and not Path("services/dope-context/run_mcp.sh").exists()
            if missing_wrapper:
                replacement = _generate("claude-context")
                if replacement:
                    repaired = MCPServerConfig(**replacement)
                    repaired.env.update(dope_context.env)
                    config.mcp_servers["claude-context"] = repaired
                config.mcp_servers.pop("dope-context", None)

        # Repair host-specific mas-sequential-thinking path.
        mas_server = config.mcp_servers.get("mas-sequential-thinking")
        if mas_server and any(isinstance(arg, str) and "/Users/" in arg for arg in mas_server.args):
            replacement = _generate("mas-sequential-thinking")
            if replacement:
                repaired = MCPServerConfig(**replacement)
                repaired.env.update(mas_server.env)
                config.mcp_servers["mas-sequential-thinking"] = repaired

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

    def get_mobile_config(self) -> MobileConfig:
        """Return mobile Happy integration settings."""
        config = self.load_config()
        return config.mobile

    def get_tmux_config(self) -> TmuxControllerConfig:
        """Return tmux controller settings."""
        config = self.load_config()
        return config.tmux

    def update_claude_autoresponder(self, **kwargs) -> None:
        """Update Claude Auto Responder settings."""
        config = self.load_config()
        current = config.claude_autoresponder.model_dump()
        updates = {key: value for key, value in kwargs.items() if key in current}
        config.claude_autoresponder = ClaudeAutoResponderConfig(**(current | updates))
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
            "mcp_mode": "auto",
            "adhd_profile": {
                "focus_duration_avg": 25,
                "break_interval": 5,
                "distraction_sensitivity": 0.5,
                "hyperfocus_tendency": False,
                "notification_style": "gentle",
                "visual_complexity": "minimal",
            },
            "mcp_servers": self._get_default_mcp_servers(
                mcp_mode="auto",
                docker_compose_bin="docker compose",
            ),
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
            "mobile": {
                "enabled": False,
                "happy_server_url": None,
                "happy_webapp_url": None,
                "default_panes": "primary",
                "popup_mode": False,
            },
            "tmux": {
                "enabled": True,
                "default_session": None,
                "allowed_sessions": [],
                "send_rate_limit_seconds": 0.15,
                "capture_default_lines": 200,
                "default_layout": "dope",
                "monitor_commands": {
                    "monitor:worktree": "dopemux status --attention --tasks",
                    "monitor:logs": "(touch logs/latest.log 2>/dev/null); tail -n 120 logs/latest.log",
                    "monitor:metrics": "dopemux health",
                },
                "orchestrator_command": "dopemux start --no-recovery",
                "sandbox_command": None,
                "dual_agent_default": False,
                "secondary_agent_command": None,
                "pane_styles": {
                    "monitor:worktree": "fg=#a6e3a1,bg=#1e1e2e",
                    "monitor:logs": "fg=#89dceb,bg=#1e1e2e",
                    "monitor:metrics": "fg=#f9e2af,bg=#1e1e2e",
                    "orchestrator:control": "fg=#f5f5f7,bg=#181825",
                    "sandbox:shell": "fg=#f5c2e7,bg=#302d41",
                    "agent:primary": "fg=#cdd6f4,bg=#1f1d2e",
                    "agent:secondary": "fg=#b4befe,bg=#262335",
                },
                "pane_border_styles": {
                    "monitor:worktree": "fg=#a6e3a1,bg=#181825",
                    "monitor:logs": "fg=#89dceb,bg=#181825",
                    "monitor:metrics": "fg=#f9e2af,bg=#181825",
                    "orchestrator:control": "fg=#f5f5f7,bg=#11111b",
                    "sandbox:shell": "fg=#f5c2e7,bg=#11111b",
                    "agent:primary": "fg=#cdd6f4,bg=#11111b",
                    "agent:secondary": "fg=#b4befe,bg=#11111b",
                },
                "status_style": "bg=#1e1e2e,fg=#cdd6f4",
                "status_left": (
                    "#[fg=#1e1e2e,bg=#89b4fa]"
                    "#[fg=#11111b,bg=#89b4fa,bold] DOPMUX "
                    "#[fg=#89b4fa,bg=#1e1e2e] "
                    "#[fg=#a6e3a1]#H #[default]"
                ),
                "status_right": (
                    "#[fg=#f5c2e7]  %R #[fg=#89dceb]%a %b %d "
                    "#[fg=#cdd6f4]#{window_index}:#{window_name} "
                    "#[fg=#f9e2af]#{pane_index}:#{pane_title}"
                ),
                "status_palette": {
                    "accent": "#89b4fa",
                    "background": "#1e1e2e",
                    "foreground": "#cdd6f4",
                    "warning": "#f9e2af",
                    "success": "#a6e3a1",
                    "info": "#89dceb",
                    "alert": "#f5c2e7",
                },
                "theme": "muted",
                "presets": {
                    "bash": {
                        "command": "${SHELL:/bin/bash}",
                        "focus": True,
                    },
                    "claude": {
                        "command": "dopemux start --background --no-recovery",
                        "focus": True,
                    },
                },
            },
            "dope_layout": {
                "default_mode": "implementation",
                "metrics_bar_enabled": True,
                "transient_messages": {
                    "enabled": True,
                    "untracked_work": True,
                    "context_switches": True,
                    "task_drift": True,
                    "break_reminders": False,
                    "thresholds": {
                        "untracked_warning_days": 1,
                        "untracked_critical_days": 7,
                        "break_reminder_minutes": [25, 45, 90],
                    },
                },
                "pm_mode": {
                    "leantime_url": "http://localhost:3007",
                    "conport_url": "http://localhost:3009",
                    "auto_switch": False,
                },
                "services": {
                    "adhd_engine_url": "http://localhost:3008",
                    "activity_capture_url": "http://localhost:3006",
                    "serena_url": "http://localhost:3010",
                    "litellm_url": "http://localhost:4000",
                    "docker_compose_bin": "docker compose",
                },
                "state_file": None,
            },
            "project_templates": self._get_project_templates(),
        }

    def _parse_docker_compose_bin(self, docker_compose_bin: Optional[str]) -> List[str]:
        """Parse docker compose launcher config into command tokens."""
        raw = (docker_compose_bin or "").strip()
        if not raw:
            return ["docker", "compose"]

        tokens = shlex.split(raw)
        if not tokens:
            return ["docker", "compose"]

        if tokens == ["docker"]:
            return ["docker", "compose"]

        return tokens

    def _detect_docker_mode(
        self,
        registry: Optional[MCPRegistry] = None,
        docker_compose_bin: str = "docker compose",
    ) -> bool:
        """Check whether required docker MCP services are running."""
        try:
            registry = registry or MCPRegistry()
            required_defs = [
                server
                for server in registry.default_servers()
                if server.required_for_auto and server.docker
            ]
            if not required_defs:
                return False

            compose_file = required_defs[0].docker.compose_file
            compose_cmd = self._parse_docker_compose_bin(docker_compose_bin)
            cmd = compose_cmd + [
                "-f",
                compose_file,
                "ps",
                "--services",
                "--filter",
                "status=running",
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,
                timeout=5,
            )
            if result.returncode != 0:
                return False

            running_services = set(line.strip() for line in result.stdout.splitlines() if line.strip())
            required_services = {
                server.docker.service
                for server in required_defs
                if server.docker
            }
            return required_services.issubset(running_services)
        except FileNotFoundError:
            return False
        except Exception as exc:
            logger.debug("Docker mode detection failed: %s", exc)
            return False

    def _generate_server_config(
        self,
        registry: MCPRegistry,
        name: str,
        mcp_mode: str,
        docker_compose_bin: str = "docker compose",
    ) -> Optional[Dict[str, Any]]:
        """Generate MCPServerConfig for a given server name based on mode."""
        server_def = registry.get_server(name)
        if not server_def:
            return None

        mode = mcp_mode
        if mode == "auto":
            mode = "docker" if self._detect_docker_mode(registry, docker_compose_bin) else "local"

        if mode == "docker":
            if server_def.transport in ("http", "http-sse"):
                if not server_def.docker or server_def.docker.port is None:
                    return None
                return {
                    "enabled": True,
                    "command": "python",
                    "args": [
                        "-m",
                        "dopemux.mcp.http_stdio_bridge",
                        "--base-url",
                        f"http://localhost:{server_def.docker.port}",
                    ],
                    "env": {},
                    "timeout": 30,
                    "auto_restart": True,
                }

            if server_def.transport == "stdio":
                if not server_def.docker:
                    return None
                compose_tokens = self._parse_docker_compose_bin(docker_compose_bin)
                full_tokens = compose_tokens + [
                    "-f",
                    server_def.docker.compose_file,
                    "exec",
                    "-T",
                    server_def.docker.service,
                ] + list(server_def.docker.exec)
                return {
                    "enabled": True,
                    "command": full_tokens[0],
                    "args": full_tokens[1:],
                    "env": {},
                    "timeout": 30,
                    "auto_restart": True,
                }

        if server_def.local and server_def.local.command:
            return {
                "enabled": True,
                "command": server_def.local.command,
                "args": server_def.local.args,
                "env": {},
                "timeout": 30,
                "auto_restart": True,
            }

        return None

    def _get_default_mcp_servers(
        self,
        mcp_mode: str = "auto",
        docker_compose_bin: str = "docker compose",
    ) -> Dict[str, Dict[str, Any]]:
        """Build default MCP servers from the canonical registry."""
        try:
            registry = MCPRegistry()
        except Exception as exc:
            logger.error("Failed to load MCP registry defaults: %s", exc)
            return {}

        effective_mode = mcp_mode
        if mcp_mode == "auto":
            effective_mode = "docker" if self._detect_docker_mode(registry, docker_compose_bin) else "local"

        defaults: Dict[str, Dict[str, Any]] = {}
        for server in registry.default_servers():
            generated = self._generate_server_config(
                registry,
                server.name,
                effective_mode,
                docker_compose_bin=docker_compose_bin,
            )
            if generated:
                defaults[server.name] = generated

        env_overrides: Dict[str, Dict[str, str]] = {
            "claude-context": {
                "VOYAGE_API_KEY": "${VOYAGE_API_KEY}",
                "OPENAI_API_KEY": "${OPENAI_API_KEY}",
                "QDRANT_URL": "localhost",
                "QDRANT_PORT": "6333",
            },
            "pal": {
                "DISABLED_TOOLS": "refactor,testgen,secaudit,docgen,tracer",
                "DEFAULT_MODEL": "auto",
                "PAL_DEFAULT_PROVIDER": "openrouter",
            },
            "mas-sequential-thinking": {
                "LLM_PROVIDER": "openai",
                "OPENAI_API_KEY": "${OPENAI_API_KEY}",
                "EXA_API_KEY": "${EXA_API_KEY}",
            },
            "exa": {
                "EXA_API_KEY": "${EXA_API_KEY}",
            },
            "zen": {
                "OPENAI_API_KEY": "${OPENAI_API_KEY}",
                "XAI_API_KEY": "${XAI_API_KEY}",
                "GEMINI_API_KEY": "${GEMINI_API_KEY}",
                "GROQ_API_KEY": "${GROQ_API_KEY}",
                "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}",
                "ZEN_DISABLED_TOOLS": "chat,explain,translate,summarize",
                "ZEN_DEFAULT_MODEL": os.getenv("ZEN_DEFAULT_MODEL", "openai/gpt-4o"),
                "ZEN_FALLBACK_MODELS": os.getenv(
                    "ZEN_FALLBACK_MODELS", "xai/grok-beta,groq/llama-3.1-70b"
                ),
                "LITELLM_PROXY": os.getenv("LITELLM_PROXY", "http://localhost:4000"),
                "LITELLM_MASTER_KEY": os.getenv("DOPEMUX_LITELLM_MASTER_KEY", ""),
            },
        }

        for server_name, env in env_overrides.items():
            if server_name not in defaults:
                continue
            merged_env = dict(defaults[server_name].get("env", {}))
            merged_env.update(env)
            defaults[server_name]["env"] = merged_env

        return defaults

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
                    "conport",
                    "serena",
                    "claude-context",
                    "pal",
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
                "mcp_servers": ["conport", "claude-context", "pal", "morphllm-fast-apply"],
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
                    "conport",
                    "serena",
                    "claude-context",
                    "pal",
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
            logger.error(f"Warning: Failed to load config file {path}: {e}")
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

            # Cache but don't cache sensitive values in plain text
            if self._is_sensitive_var(var_name):
                # Store a flag instead of the actual value for logging purposes
                self._env_cache[var_name] = "[REDACTED]" if value else ""
                return value  # Return actual value for use
            else:
                self._env_cache[var_name] = value
                return value
        else:
            return obj

    def _is_sensitive_var(self, var_name: str) -> bool:
        """Check if environment variable contains sensitive information."""
        sensitive_patterns = [
            "API_KEY", "SECRET", "TOKEN", "PASSWORD", "PRIVATE",
            "CREDENTIAL", "AUTH", "KEY", "PASS"
        ]
        var_upper = var_name.upper()
        return any(pattern in var_upper for pattern in sensitive_patterns)

    def _sanitize_config_for_logging(self, config_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Create a sanitized version of config safe for logging."""
        def sanitize_value(key: str, value: Any) -> Any:
            if isinstance(value, dict):
                return {k: sanitize_value(k, v) for k, v in value.items()}
            elif isinstance(value, list):
                return [sanitize_value(f"{key}[{i}]", item) for i, item in enumerate(value)]
            elif isinstance(value, str) and self._is_sensitive_var(key):
                return "[REDACTED]" if value else ""
            else:
                return value

        return {k: sanitize_value(k, v) for k, v in config_dict.items()}

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
