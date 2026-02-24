"""
Claude Code Launcher Module.

Handles detection, configuration, and launching of Claude Code with
ADHD-optimized settings and MCP server integration.
"""

import atexit

import logging

logger = logging.getLogger(__name__)

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..config import ConfigManager
from ..console import console

# Import RoutingConfig for mode-based environment preparation
try:
    from ..routing_config import RoutingConfig
except ImportError:
    RoutingConfig = None


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

        # Process tracking for cleanup
        self._spawned_processes: List[subprocess.Popen] = []
        self._temp_files: List[Path] = []
        self._cleanup_registered = False

        self._detect_claude()

        # Register cleanup handlers (only once per instance)
        if not self._cleanup_registered:
            atexit.register(self._cleanup)
            # Note: Signal handlers are global, so we check if already registered
            try:
                signal.signal(signal.SIGTERM, self._signal_handler)
                signal.signal(signal.SIGINT, self._signal_handler)
                self._cleanup_registered = True
            except (ValueError, OSError):
                # Signal handlers can only be registered in main thread
                # This is fine - atexit will still work
                pass

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
                        console.logger.info(f"[green]✓ Found Claude Code at {path}[/green]")
                        return
                except (subprocess.TimeoutExpired, subprocess.SubprocessError):
                    continue

        # Not found
        console.logger.info("[yellow]⚠️ Claude Code not found in standard locations[/yellow]")

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

        # In API-key proxy mode, rely on env to suppress browser/login prompts
        # (CLAUDE_NO_BROWSER and CLAUDE_CODE_SKIP_PERMISSIONS). The CLI
        # does not accept a --no-browser flag in some versions.

        # Launch process with sexy output
        from rich.panel import Panel
        
        launch_msg = Panel(
            "🚀 [bold cyan]Launching Claude Code[/bold cyan]\n"
            "[dim]ADHD optimizations • Context awareness • MCP tools enabled[/dim]",
            border_style="cyan",
            padding=(0, 2)
        )
        console.print(launch_msg)

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

        # Track process and temp file for cleanup
        self._spawned_processes.append(process)
        self._temp_files.append(settings_file)

        return process

    def _generate_claude_config(
        self, project_path: Path, context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate Claude Code configuration."""
        config = self.config_manager.load_config()

        # Base Claude settings
        # NOTE: env section is for MCP servers only - Claude Pro Max doesn't need API key
        claude_config = {
            "env": {
                "MCP_TOOL_TIMEOUT": "40000",
                "MAX_MCP_OUTPUT_TOKENS": "10000",
                "DOPEMUX_PROJECT": str(project_path),
                "DOPEMUX_ENABLED": "true",
            },
            "mcpServers": {},
        }

        # Do NOT add ANTHROPIC_API_KEY to Claude settings - Pro Max users authenticate through the app
        # MCP servers will get API keys from subprocess environment instead

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
        except Exception as e:
            os.unlink(temp_path)
            raise

            logger.error(f"Error: {e}")
        return Path(temp_path)

    def _prepare_environment(self) -> Dict[str, str]:
        """Prepare environment variables for Claude Code."""
        env = os.environ.copy()

        # Add Dopemux-specific variables
        env.update({"DOPEMUX_VERSION": "0.1.0", "DOPEMUX_ACTIVE": "true"})

        # Determine routing mode from config (replaces legacy DOPEMUX_CLAUDE_VIA_LITELLM)
        routing_mode = None
        if RoutingConfig is not None:
            try:
                routing_config = RoutingConfig.load_default()
                routing_mode = routing_config.get_mode()
                console.logger.info(f"[blue]📋 Claude Launcher: Routing mode {routing_mode}[/blue]")
            except Exception as e:
                console.logger.warning(f"[yellow]⚠️  Could not load routing config: {e}[/yellow]")
                console.logger.info("[dim]Falling back to legacy environment behavior[/dim]")
        
        # If routing mode is api, configure for proxy routing
        if routing_mode == "api":
            # Use CCR as proxy - keep ANTHROPIC_API_KEY and ANTHROPIC_BASE_URL
            via_litellm = True
            console.logger.info("[blue]🔄 Routing mode 'api': Configuring Claude for CCR proxy[/blue]")
        # If routing mode is subscription, use direct OAuth
        elif routing_mode == "subscription":
            via_litellm = False
            console.logger.info("[blue]📋 Routing mode 'subscription': Configuring Claude for direct OAuth[/blue]")
        # Fallback to legacy behavior
        else:
            via_litellm = env.get("DOPEMUX_CLAUDE_VIA_LITELLM") in ("1", "true", "True")
            if via_litellm:
                console.logger.info("[dim]Using legacy DOPEMUX_CLAUDE_VIA_LITELLM flag[/dim]")
        if via_litellm:
            # If ANTHROPIC_BASE_URL is already set (e.g., by CCR), keep it
            # Otherwise, fall back to LITELLM_PROXY_URL
            if not env.get("ANTHROPIC_BASE_URL"):
                proxy_url = env.get("LITELLM_PROXY_URL") or env.get("OPENAI_API_BASE")
                if proxy_url:
                    env.setdefault("ANTHROPIC_API_BASE", proxy_url)
                    env.setdefault("ANTHROPIC_BASE_URL", proxy_url)
            # Suppress browser/OAuth prompts in API-key proxy mode
            env.setdefault("CLAUDE_CODE_SKIP_PERMISSIONS", "true")
            env.setdefault("CLAUDE_NO_BROWSER", "1")
            # Isolate Claude platform home per instance to avoid picking up saved OAuth tokens
            try:
                from pathlib import Path as _Path
                inst = env.get("DOPEMUX_INSTANCE_ID", "A") or "A"
                ws = env.get("DOPEMUX_WORKSPACE_ID") or os.getcwd()
                claude_home = _Path(ws) / ".dopemux" / "claude-platform" / inst
                claude_home.mkdir(parents=True, exist_ok=True)
                env["CLAUDE_PLATFORM_HOME"] = str(claude_home)
            except Exception as e:
                pass
                logger.error(f"Error: {e}")
            # Remove any residual OAuth-related env to prevent mixed auth modes
            for k in list(env.keys()):
                if k.upper().startswith("ANTHROPIC_OAUTH") or k.upper() in {"ANTHROPIC_TOKEN", "CLAUDE_TOKEN"}:
                    env.pop(k, None)
            console.print(
                "[dim]✓ Routing Claude via LiteLLM proxy (API key mode enabled)[/dim]"
            )
        else:
            # CRITICAL: Do NOT pass ANTHROPIC_API_KEY to Claude Code subprocess
            # Claude Pro Max users authenticate through OAuth in the app, not via API key
            # If ANTHROPIC_API_KEY is in the environment, Claude Code switches to API key mode
            # and fails with 401 errors when the key is invalid/expired
            if "ANTHROPIC_API_KEY" in env:
                del env["ANTHROPIC_API_KEY"]
                console.print(
                    "[dim]✓ Using Claude Pro Max OAuth (ANTHROPIC_API_KEY excluded from Claude Code)[/dim]"
                )

        # MCP servers will still get ANTHROPIC_API_KEY through their individual env configs
        # via ${ANTHROPIC_API_KEY} substitution in _resolve_env_vars()
        # This allows MCP servers to use the key while Claude Code uses OAuth

        if not via_litellm:
            console.logger.info("[dim]ℹ️  Claude Pro Max: Authenticate through the app[/dim]")

        # Add other API keys for MCP server fallback
        # These are needed by MCP servers for fallback when Claude Pro Max hits rate limits
        other_keys = ["OPENAI_API_KEY", "EXA_API_KEY", "XAI_API_KEY", "GROQ_API_KEY"]

        available_keys = []
        for key in other_keys:
            key_value = os.getenv(key)
            if key_value:
                env[key] = key_value
                available_keys.append(key)

        if available_keys:
            console.print(
                f"[dim]✓ MCP fallback ready with: {', '.join(available_keys)}[/dim]"
            )
        else:
            console.print(
                "[dim]ℹ️  No fallback API keys set - MCP servers will use Claude Pro Max only[/dim]"
            )

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

                logger.error(f"Error: {e}")
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
                "pal",
                "morphllm-fast-apply-mcp",
                "exa-mcp",
            ]

            for package in node_packages:
                console.logger.info(f"[blue]Installing {package}...[/blue]")
                result = subprocess.run(
                    ["npm", "install", "-g", package], capture_output=True, text=True
                )
                if result.returncode != 0:
                    console.print(
                        f"[yellow]Warning: Failed to install {package}[/yellow]"
                    )

            # Install Python packages
            python_packages = ["context-portal-mcp"]  # Removed task-master-ai (crashes)

            for package in python_packages:
                console.logger.info(f"[blue]Installing {package}...[/blue]")
                result = subprocess.run(
                    ["pip", "install", package], capture_output=True, text=True
                )
                if result.returncode != 0:
                    console.print(
                        f"[yellow]Warning: Failed to install {package}[/yellow]"
                    )

            return True

        except Exception as e:
            console.logger.error(f"[red]Error installing dependencies: {e}[/red]")
            return False

    def _cleanup(self) -> None:
        """Clean up spawned Claude Code processes and temporary files."""
        # Clean up processes (Claude Code will clean up its MCP servers)
        for process in self._spawned_processes:
            try:
                if process.poll() is None:  # Still running
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        # Force kill if doesn't terminate gracefully
                        process.kill()
                        process.wait(timeout=2)
            except Exception as e:
                # Silent cleanup - don't spam errors on exit
                pass

                logger.error(f"Error: {e}")
        # Clean up temporary settings files
        for temp_file in self._temp_files:
            try:
                temp_file.unlink(missing_ok=True)
            except Exception as e:
                pass

                logger.error(f"Error: {e}")
        # Clear tracking lists
        self._spawned_processes.clear()
        self._temp_files.clear()

    def _signal_handler(self, signum: int, frame) -> None:
        """Handle termination signals gracefully."""
        self._cleanup()
        sys.exit(0)
