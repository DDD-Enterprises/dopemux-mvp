"""
Claude Code Launcher Module.

Handles detection, configuration, and launching of Claude Code with
ADHD-optimized settings and MCP server integration.
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

from ..config import ConfigManager

console = Console()


class ClaudeNotFoundError(Exception):
    """Raised when Claude Code executable is not found."""


class ClaudeLauncher:
    """
    Launches Claude Code with ADHD-optimized configuration.

    Handles:
    - Claude Code detection and validation
    - MCP server configuration generation
    - Environment variable setup
    - Process launching and monitoring
    """

    def __init__(self, config_manager: ConfigManager):
        """Initialize launcher with configuration manager."""
        self.config_manager = config_manager
        self.claude_path: Optional[Path] = None
        self._detect_claude()

    def _detect_claude(self) -> None:
        """Detect Claude Code installation."""
        # Check configuration first
        config = self.config_manager.load_config()
        if config.claude_path:
            claude_path = Path(config.claude_path)
            if claude_path.exists() and claude_path.is_file():
                self.claude_path = claude_path
                return

        # Common installation paths
        search_paths = [
            Path.home() / ".local" / "bin" / "claude",
            Path("/usr/local/bin/claude"),
            Path("/opt/homebrew/bin/claude"),
            Path("/usr/bin/claude"),
        ]

        # Check PATH
        claude_in_path = shutil.which("claude")
        if claude_in_path:
            search_paths.insert(0, Path(claude_in_path))

        for path in search_paths:
            if path.exists() and path.is_file():
                try:
                    # Verify it's actually Claude Code
                    result = subprocess.run(
                        [str(path), "--version"],
                        capture_output=True,
                        text=True,
                        timeout=5,
                    )
                    if result.returncode == 0 and "claude" in result.stdout.lower():
                        self.claude_path = path
                        console.print(f"[green]✓ Found Claude Code at {path}[/green]")
                        return
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    continue

        # Not found
        console.print("[yellow]⚠️ Claude Code not found in standard locations[/yellow]")

    def is_available(self) -> bool:
        """Check if Claude Code is available."""
        return self.claude_path is not None

    def get_installation_instructions(self) -> str:
        """Get Claude Code installation instructions."""
        return """
Claude Code not found. To install:

1. Visit: https://claude.ai/code
2. Download for your platform
3. Follow installation instructions
4. Or specify path with: dopemux config set claude_path /path/to/claude

Alternative: Set CLAUDE_PATH environment variable
"""

    def launch(
        self,
        project_path: Path,
        background: bool = False,
        debug: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ) -> subprocess.Popen:
        """
        Launch Claude Code with ADHD-optimized configuration.

        Args:
            project_path: Project directory path
            background: Run in background
            debug: Enable debug output
            context: Restored context information

        Returns:
            Claude Code process

        Raises:
            ClaudeNotFoundError: If Claude Code is not available
        """
        if not self.is_available():
            raise ClaudeNotFoundError(self.get_installation_instructions())

        # Generate Claude configuration
        claude_config = self._generate_claude_config(project_path, context)

        # Create temporary settings file
        settings_file = self._create_settings_file(claude_config)

        # Prepare environment
        env = self._prepare_environment()

        # Build command
        cmd = [str(self.claude_path)]

        # Add settings file
        cmd.extend(["--settings", str(settings_file)])

        # Add project path
        cmd.append(str(project_path))

        # Debug mode
        if debug:
            cmd.append("--debug")

        # Dangerous mode - check environment variables
        if (
            os.environ.get("CLAUDE_CODE_SKIP_PERMISSIONS") == "true"
            or os.environ.get("DOPEMUX_DANGEROUS_MODE") == "true"
        ):
            cmd.append("--dangerously-skip-permissions")
            console.print(
                "[red]⚠️  Added --dangerously-skip-permissions flag to Claude Code[/red]"
            )

        # Launch process
        console.print(
            f"[blue]🚀 Launching Claude Code with ADHD optimizations...[/blue]"
        )

        if background:
            # Detached background process
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        else:
            # Interactive process
            process = subprocess.Popen(cmd, env=env)

        return process

    def _generate_claude_config(
        self, project_path: Path, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate Claude Code configuration."""
        config = self.config_manager.load_config()

        # Base Claude settings
        claude_config = {
            "env": {
                "MCP_TOOL_TIMEOUT": "40000",
                "MAX_MCP_OUTPUT_TOKENS": "10000",
                "DOPEMUX_PROJECT": str(project_path),
                "DOPEMUX_ENABLED": "true",
            },
            "mcpServers": {},
        }

        # Add ADHD-specific environment variables
        adhd_profile = config.adhd_profile
        claude_config["env"].update(
            {
                "ADHD_FOCUS_DURATION": str(adhd_profile.focus_duration_avg),
                "ADHD_BREAK_INTERVAL": str(adhd_profile.break_interval),
                "ADHD_DISTRACTION_SENSITIVITY": str(
                    adhd_profile.distraction_sensitivity
                ),
                "ADHD_HYPERFOCUS_TENDENCY": str(
                    adhd_profile.hyperfocus_tendency
                ).lower(),
                "ADHD_NOTIFICATION_STYLE": adhd_profile.notification_style,
                "ADHD_VISUAL_COMPLEXITY": adhd_profile.visual_complexity,
            }
        )

        # Add context information if available
        if context:
            claude_config["env"].update(
                {
                    "DOPEMUX_CONTEXT_AVAILABLE": "true",
                    "DOPEMUX_LAST_GOAL": context.get("current_goal", ""),
                    "DOPEMUX_SESSION_ID": context.get("session_id", ""),
                }
            )

        # Configure MCP servers
        for name, server_config in config.mcp_servers.items():
            if server_config.enabled:
                mcp_config = {
                    "type": "stdio",
                    "command": server_config.command,
                    "args": server_config.args,
                    "env": self._resolve_env_vars(server_config.env),
                }

                # Add timeout if specified
                if server_config.timeout != 30:  # default
                    mcp_config["timeout"] = server_config.timeout

                claude_config["mcpServers"][name] = mcp_config

        return claude_config

    def _create_settings_file(self, config: Dict[str, Any]) -> Path:
        """Create temporary settings file for Claude Code."""
        # Create temporary file
        fd, temp_path = tempfile.mkstemp(suffix=".json", prefix="dopemux-claude-")

        try:
            with os.fdopen(fd, "w") as f:
                json.dump(config, f, indent=2)
        except Exception:
            os.unlink(temp_path)
            raise

        return Path(temp_path)

    def _prepare_environment(self) -> Dict[str, str]:
        """Prepare environment variables for Claude Code."""
        env = os.environ.copy()

        # Add Dopemux-specific variables
        env.update({"DOPEMUX_VERSION": "0.1.0", "DOPEMUX_ACTIVE": "true"})

        # Ensure required API keys are available
        required_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "EXA_API_KEY"]

        missing_keys = []
        for key in required_keys:
            if key not in env or not env[key]:
                missing_keys.append(key)

        if missing_keys:
            console.print(
                f"[yellow]⚠️ Missing API keys: {', '.join(missing_keys)}[/yellow]"
            )
            console.print("[dim]Some MCP servers may not function correctly[/dim]")

        return env

    def _resolve_env_vars(self, env_dict: Dict[str, str]) -> Dict[str, str]:
        """Resolve environment variables in MCP server config."""
        import re

        resolved = {}

        for key, value in env_dict.items():
            # Handle multiple variable substitutions in a single string
            def replace_var(match):
                var_part = match.group(1)
                if ":" in var_part:
                    var_name, default = var_part.split(":", 1)
                else:
                    var_name, default = var_part, ""
                return os.getenv(var_name, default)

            # Find all ${VAR} or ${VAR:default} patterns
            resolved_value = re.sub(r"\$\{([^}]+)\}", replace_var, value)
            resolved[key] = resolved_value

        return resolved

    def get_status(self) -> Dict[str, Any]:
        """Get Claude Code launcher status."""
        return {
            "claude_available": self.is_available(),
            "claude_path": str(self.claude_path) if self.claude_path else None,
            "mcp_servers_configured": len(self.config_manager.get_mcp_servers()),
            "adhd_optimizations": True,
        }

    def validate_mcp_servers(self) -> List[Dict[str, Any]]:
        """Validate MCP server configurations."""
        results = []
        config = self.config_manager.load_config()

        for name, server_config in config.mcp_servers.items():
            result = {
                "name": name,
                "enabled": server_config.enabled,
                "command_available": False,
                "env_vars_set": True,
                "issues": [],
            }

            # Check if command is available
            try:
                if server_config.command in ["python", "node", "npx", "uv", "uvx"]:
                    # Check if interpreter is available
                    cmd_path = shutil.which(server_config.command)
                    result["command_available"] = cmd_path is not None
                    if not cmd_path:
                        result["issues"].append(
                            f"Command '{server_config.command}' not found in PATH"
                        )
                else:
                    # Check if specific command exists
                    if Path(server_config.command).exists():
                        result["command_available"] = True
                    else:
                        cmd_path = shutil.which(server_config.command)
                        result["command_available"] = cmd_path is not None
                        if not cmd_path:
                            result["issues"].append(
                                f"Command '{server_config.command}' not found"
                            )
            except Exception as e:
                result["issues"].append(f"Error checking command: {e}")

            # Check environment variables
            for env_key, env_value in server_config.env.items():
                if env_value.startswith("${") and env_value.endswith("}"):
                    var_name = env_value[2:-1]
                    if ":" in var_name:
                        var_name = var_name.split(":", 1)[0]

                    if not os.getenv(var_name):
                        result["env_vars_set"] = False
                        result["issues"].append(
                            f"Environment variable '{var_name}' not set"
                        )

            results.append(result)

        return results

    def install_mcp_dependencies(self) -> bool:
        """Install missing MCP server dependencies."""
        try:
            # Install Node.js packages
            node_packages = [
                "@zilliz/claude-context-mcp",
                "context7-mcp",
                "morphllm-fast-apply-mcp",
                "exa-mcp",
            ]

            for package in node_packages:
                console.print(f"[blue]Installing {package}...[/blue]")
                result = subprocess.run(
                    ["npm", "install", "-g", package], capture_output=True, text=True
                )
                if result.returncode != 0:
                    console.print(
                        f"[yellow]Warning: Failed to install {package}[/yellow]"
                    )

            # Install Python packages
            python_packages = ["task-master-ai", "context-portal-mcp"]

            for package in python_packages:
                console.print(f"[blue]Installing {package}...[/blue]")
                result = subprocess.run(
                    ["pip", "install", package], capture_output=True, text=True
                )
                if result.returncode != 0:
                    console.print(
                        f"[yellow]Warning: Failed to install {package}[/yellow]"
                    )

            return True

        except Exception as e:
            console.print(f"[red]Error installing dependencies: {e}[/red]")
            return False
