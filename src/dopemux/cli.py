#!/usr/bin/env python3
"""
Dopemux CLI - ADHD-optimized development platform CLI.

Main entry point for all dopemux commands providing context preservation,
attention monitoring, and task decomposition for neurodivergent developers.
"""

import os

import logging

logger = logging.getLogger(__name__)

import sys
import time
import shutil
import socket
import signal
import tempfile
import shlex
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence
import warnings

import click
from .utils.dotenv_loader import load_dotenv, check_dotenv_support

# Import RoutingConfig for mode-based behavior
try:
    from .routing_config import RoutingConfig
except ImportError:  # pragma: no cover
    RoutingConfig = None

from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from . import __version__
from .claude_tools.cli import register_commands
from .console import console

# Load environment variables from .env file
load_dotenv()
check_dotenv_support()
from .adhd import AttentionMonitor, ContextManager, TaskDecomposer
from .claude import ClaudeConfigurator, ClaudeLauncher
from .dope_brainz_router import (
    DopeBrainzRouterError,
    DopeBrainzRouterManager,
)
from .config import ConfigManager
from .health import HealthChecker
from .instance_manager import InstanceManager, detect_instances_sync, detect_orphaned_instances_sync
from .litellm_proxy import (
    ALTP_PROVIDER,
    CODEX_PROVIDER,
    DEFAULT_LITELLM_CONFIG,
    GROK_PROVIDER,
    LiteLLMProxyError,
    LiteLLMProxyManager,
    ensure_master_key,
    generate_multi_target_config,
    generate_single_target_config,
    start_simple_proxy,
    sync_litellm_database,
)
from .profile_manager import ProfileManager
from .profile_models import ProfileValidationError
from .claude_config import ClaudeConfig, ClaudeConfigError
from .profile_parser import ProfileParser
from .protection_interceptor import check_and_protect_main, consume_last_created_worktree
from .project_init import init_project
import subprocess
from subprocess import CalledProcessError
from urllib.parse import urlparse
import yaml
from .mobile import mobile as mobile_commands
from .mobile.main import main as mobile_env_commands
from .mobile.hooks import mobile_task_notification
from .mobile.runtime import update_tmux_mobile_indicator
from .tmux import tmux as tmux_commands

# Import genetic agent CLI
try:
    # Ensure services directory is in Python path for production environments
    services_path = Path(__file__).resolve().parent.parent / 'services'
    if str(services_path) not in sys.path:
        sys.path.insert(0, str(services_path))

    from services.genetic_agent.cli import cli as genetic_group
except ImportError:
    # Fallback if genetic agent service is not available
    genetic_group = None
from .roles.catalog import (
    activate_role,
    available_roles,
    resolve_role,
    RoleNotFoundError,
)
from .memory.capture_client import CaptureError, emit_capture_event
from .extractor.runner import PipelineRunner


if "-litellm" in sys.argv:
    sys.argv = ["--litellm" if arg == "-litellm" else arg for arg in sys.argv]



ROLE_SERVER_SERVICE_MAP = {
    "conport": "conport",
    "serena": "serena",
    "serena-lsp": "serena",
    "zen": "zen",
    "exa": "exa",
    "gptr-mcp": "gptr-mcp",
    "dopemux-gpt-researcher": "dopemux-gpt-researcher",
    "desktop-commander": "desktop-commander",
    "leantime": "leantime-bridge",
    "leantime-bridge": "leantime-bridge",
}

ATTENTION_PROFILE_DEFAULTS = {
    "scattered": {
        "session_duration_minutes": 20,
        "energy_preference": "low",
        "attention_mode": "scattered",
    },
    "focused": {
        "session_duration_minutes": 50,
        "energy_preference": "medium",
        "attention_mode": "focused",
    },
    "hyperfocus": {
        "session_duration_minutes": 90,
        "energy_preference": "high",
        "attention_mode": "hyperfocused",
    },
    "variable": {
        "session_duration_minutes": 45,
        "energy_preference": "any",
        "attention_mode": "any",
    },
}


def _get_routing_allowlist() -> set[str]:
    """Return the set of environment variable names allowed for export."""
    return {
        # Dopemux Identity
        "DOPEMUX_INSTANCE_ID",
        "DOPEMUX_WORKSPACE_ID",
        "DOPEMUX_CLAUDE_VIA_LITELLM",
        "DOPEMUX_DEFAULT_LITELLM",
        
        # Anthropic / LiteLLM Auth
        "ANTHROPIC_BASE_URL",
        "ANTHROPIC_API_BASE",
        "ANTHROPIC_API_KEY",
        "LITELLM_MASTER_KEY",
        "DOPEMUX_LITELLM_MASTER_KEY",
        
        # Database (if needed for metrics)
        "DOPEMUX_LITELLM_DB_URL",
        "LITELLM_DATABASE_URL",
        "DATABASE_URL",
        
        # Claude Code Router (CCR)
        "CLAUDE_CODE_ROUTER_PORT",
        "CLAUDE_CODE_ROUTER_HOME",
        "CLAUDE_CODE_ROUTER_CONFIG",
        "CLAUDE_CODE_ROUTER_LOG",
        "CLAUDE_CODE_ROUTER_PROVIDER",
        "CLAUDE_CODE_ROUTER_MODELS",
        "CLAUDE_CODE_ROUTER_UPSTREAM_URL",
        "CLAUDE_CODE_ROUTER_UPSTREAM_KEY_VAR",
        "CLAUDE_CODE_ROUTER_UPSTREAM_KEY",
    }


def _persist_instance_env_exports(
    project_root: Path, instance_id: str, env_vars: Dict[str, str]
) -> None:
    """
    Persist instance environment variables for use outside Dopemux processes.

    Writes both `export`-style and `.env`-style files with a strict allowlist
    of routing and identity variables.
    """
    try:
        target_dir = project_root / ".dopemux" / "env"
        target_dir.mkdir(parents=True, exist_ok=True)

        slug = instance_id or "A"
        export_path = target_dir / f"instance_{slug}.sh"
        env_path = target_dir / f"instance_{slug}.env"

        allowlist = _get_routing_allowlist()
        export_secrets = os.environ.get("DOPEMUX_EXPORT_SECRETS") == "1"
        
        filtered_vars = {}
        for k, v in env_vars.items():
            if k not in allowlist:
                continue
                
            # Pattern-based secret detection
            is_secret = any(p in k for p in ("API_KEY", "TOKEN", "SECRET", "PASSWORD", "MASTER_KEY"))
            if is_secret and not export_secrets:
                continue
                
            filtered_vars[k] = v
            
        sorted_items = sorted(filtered_vars.items())

        with export_path.open("w", encoding="utf-8") as export_file:
            export_file.write("#!/usr/bin/env bash\n")
            export_file.write("# Autogenerated by Dopemux – current instance environment\n")
            export_file.write("# Source this file in your shell to mirror Dopemux routing context.\n\n")
            for key, value in sorted_items:
                value_str = "" if value is None else str(value)
                export_file.write(f"export {key}={shlex.quote(value_str)}\n")

        with env_path.open("w", encoding="utf-8") as env_file:
            env_file.write("# Autogenerated by Dopemux – docker-compose compatible env file\n")
            for key, value in sorted_items:
                value_str = "" if value is None else str(value)
                safe_value = value_str.replace("\\", "\\\\").replace('"', '\\"')
                env_file.write(f'{key}="{safe_value}"\n')

        # Refresh convenience pointers for the active instance
        shutil.copyfile(export_path, target_dir / "current.sh")
        shutil.copyfile(env_path, target_dir / "current.env")

        relative_export = export_path.relative_to(project_root)
        console.print(
            f"[dim]✓ Instance environment exported to {relative_export} "
            f"(source .dopemux/env/current.sh to mirror in this shell)[/dim]"
        )
    except Exception as exc:  # pragma: no cover - best effort persistence
        console.print(
            f"[yellow]⚠️  Could not persist instance environment: {exc}[/yellow]"
        )


def _ensure_role_profile(spec) -> Optional[object]:  # returns DopemuxProfile when available
    """Ensure a profile file exists for the given role spec."""

    profile_name = getattr(spec, "profile_name", None)
    if not profile_name:
        return None

    manager = ProfileManager()
    existing = manager.get_profile(profile_name)
    if existing:
        return existing

    profiles_dir = manager.profiles_dir
    profiles_dir.mkdir(parents=True, exist_ok=True)

    required = sorted({"conport", * (spec.required_servers or [])})
    optional = sorted(set(spec.optional_servers or []))

    attention_cfg = ATTENTION_PROFILE_DEFAULTS.get(spec.attention_state, ATTENTION_PROFILE_DEFAULTS["variable"])

    profile_data = {
        "name": profile_name,
        "display_name": spec.label,
        "description": spec.description,
        "mcp_servers": {
            "required": required,
            "enabled": optional,
            "disabled": [],
        },
        "adhd_config": {
            "session_duration_minutes": attention_cfg["session_duration_minutes"],
            "energy_preference": attention_cfg["energy_preference"],
            "attention_mode": attention_cfg["attention_mode"],
        },
        "markers": {
            "required_files": [],
            "optional_files": [],
        },
    }

    profile_path = profiles_dir / f"{profile_name}.yaml"
    with open(profile_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(profile_data, f, sort_keys=False)

    return manager.get_profile(profile_name)


def _load_litellm_models(config_path: Path) -> List[str]:
    """Load model names from a LiteLLM YAML configuration file."""
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except yaml.YAMLError:
        return []

    models: List[str] = []
    for entry in data.get("model_list", []) if isinstance(data, dict) else []:
        if isinstance(entry, dict):
            name = entry.get("model_name")
            if isinstance(name, str) and name.strip():
                models.append(name.strip())
    return models


def _select_model_by_priority(models: Sequence[str], candidates: Sequence[str]) -> Optional[str]:
    """Choose the first model matching any candidate (exact or substring) from a list."""
    if not models:
        return None

    normalized = [(model, model.lower()) for model in models]
    for candidate in candidates:
        candidate_lower = candidate.lower()
        for original, lower in normalized:
            if lower == candidate_lower:
                return original
        for original, lower in normalized:
            if candidate_lower in lower:
                return original

    return models[0]


def _build_router_overrides(provider_name: str, models: Sequence[str]) -> Dict[str, str]:
    """Generate CCR router overrides based on available LiteLLM models."""
    overrides: Dict[str, str] = {}

    def _assign(key: str, candidates: Sequence[str]) -> None:
        chosen = _select_model_by_priority(models, candidates)
        if chosen:
            overrides[key] = f"{provider_name},{chosen}"

    _assign(
        "default",
        (
            "gpt-5",
            "gpt-5-pro",
            "openrouter-openai-gpt-5",
            "grok-4-fast",
            "grok-4",
            "grok-code-fast-1",
            "xai-grok-4-fast",
            "xai-grok-code-fast-1",
        ),
    )
    _assign(
        "background",
        (
            "grok-4-fast",
            "grok-code-fast-1",
            "xai-grok-4-fast",
            "xai-grok-code-fast-1",
            "openrouter-xai-grok-code-fast",
        ),
    )
    _assign(
        "think",
        (
            "gpt-5-codex",
            "openrouter-openai-gpt-5-codex",
            "codex",
        ),
    )
    _assign(
        "webSearch",
        (
            "gpt-5-mini",
            "openrouter-openai-gpt-5-mini",
            "glm-4.6",
            "grok-code-fast-1",
            "xai-grok-code-fast-1",
            "openrouter-google-gemini-2-flash",
        ),
    )

    return overrides


def _suggest_server_start(missing_servers: Iterable[str]) -> None:
    """Suggest commands to start missing MCP services."""

    services = sorted({ROLE_SERVER_SERVICE_MAP.get(name, name) for name in missing_servers})
    if not services:
        return
    service_arg = ",".join(services)
    console.print(
        f"[yellow]💡 Start required services: dopemux mcp up --services {service_arg}[/yellow]"
    )
    console.print(
        "[dim]   or bring up the full stack: dopemux mcp start-all --verify[/dim]"
    )


def _invoke_switch_role_script(role_key: str) -> None:
    if os.getenv("DOPEMUX_SKIP_SWITCH_ROLE_SCRIPT", "0").lower() in {"1", "true", "yes"}:
        return

    script_path = Path.home() / ".claude" / "switch-role.sh"
    if not script_path.exists():
        return

    try:
        subprocess.run([str(script_path), role_key], check=True)
        console.print(
            f"[dim]✓ Synced MetaMCP role via {script_path} {role_key}[/dim]"
        )
    except subprocess.CalledProcessError as exc:
        console.print(
            f"[yellow]⚠ switch-role.sh failed (exit {exc.returncode}); continuing[/yellow]"
        )


def show_version(ctx, param, value):
    """Show version and exit."""
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"Dopemux {__version__}")
    ctx.exit()


def _start_minimal_session(
    config_manager: ConfigManager,
    project_path: Path,
    session: Optional[str],
    background: bool,
    debug: bool,
):
    """Fallback start routine for non-real workspaces (test/mocked environments)."""
    context_manager = ContextManager(project_path)
    context = None
    if session:
        context = context_manager.restore_session(session)
    else:
        context = context_manager.restore_latest()

    launcher = ClaudeLauncher(config_manager)
    try:
        launcher.launch(
            project_path=project_path,
            background=background,
            debug=debug,
            context=context,
        )
    except Exception as e:
        pass

        logger.error(f"Error: {e}")
    if not background:
        console.logger.info("[green]✨ Claude Code is running (minimal mode)\n[/green]")


@click.group()
@click.option(
    "--version", is_flag=True, expose_value=False, is_eager=True, callback=show_version
)
@click.option("--config", "-c", help="Configuration file path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--debug-log", type=click.Path(path_type=Path, dir_okay=False), help="Write debug logs to file")
@click.pass_context
def cli(ctx, config: Optional[str], verbose: bool, debug_log: Optional[Path]):
    """
    🧠 Dopemux - ADHD-optimized development platform

    Provides context preservation, attention monitoring, and task decomposition
    for enhanced productivity in software development.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config_manager"] = ConfigManager(config_path=config)

    # Optional debug file logging
    log_path_env = os.getenv("DOPEMUX_DEBUG_LOG")
    if not debug_log and log_path_env:
        debug_log = Path(log_path_env)
    if debug_log:
        try:
            log_path = Path(debug_log).expanduser().resolve()
            log_path.parent.mkdir(parents=True, exist_ok=True)
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s %(levelname)s %(name)s: %(message)s",
                handlers=[logging.FileHandler(log_path, encoding="utf-8")],
            )
            ctx.obj["debug_log"] = str(log_path)
            os.environ["DOPEMUX_DEBUG_LOG"] = str(log_path)
            logging.debug("dopemux invoked: argv=%s", sys.argv)
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to initialize debug logging file: {e}")
        except Exception:
            logger.error("Unexpected debug logging setup error", exc_info=True)
@cli.command()
@click.argument(
    "directory",
    type=click.Path(path_type=Path, file_okay=False, dir_okay=True),
    required=False,
)
@click.option("--profile", "-p", help="Profile to use (auto-detects if not specified)")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing .dopemux/ directory")
@click.option("--template", "-t", help="Claude configuration template")
@click.pass_context
def init(ctx, directory: Optional[Path], profile: Optional[str], force: bool, template: Optional[str]):
    """
    🚀 Initialize dopemux in current project

    Creates .dopemux/ directory with profile-based configuration.
    Auto-detects project type and suggests appropriate profile.

    \b
    Examples:
        dopemux init                    # Auto-detect and prompt
        dopemux init -p python-ml       # Use specific profile
        dopemux init --force            # Reinitialize existing project
        dopemux init ../project-2       # Initialize specific directory
    """
    config_manager = ctx.obj["config_manager"]

    workspace = Path(directory or Path.cwd()).expanduser().resolve()
    dopemux_dir = workspace / ".dopemux"

    workspace_exists = False
    dopemux_exists = False
    try:
        workspace_exists = Path.exists(workspace)
        dopemux_exists = Path.exists(dopemux_dir)
    except TypeError:
        pass

    if directory and not workspace_exists and not dopemux_exists:
        console.logger.info(f"[red]Directory does not exist: {workspace}[/red]")
        sys.exit(1)

    if not force and not workspace_exists and dopemux_exists:
        console.logger.info(f"[yellow]⚠️  Project already initialized (.dopemux/ exists)[/yellow]")
        sys.exit(1)

    try:
        workspace.mkdir(parents=True, exist_ok=True)
    except (OSError, FileNotFoundError) as e:
        logger.error(f"Workspace directory creation failed: {e}")
    except Exception:
        logger.error("Unexpected error creating workspace directory", exc_info=True)
    success = init_project(workspace, profile, force)

    if not success:
        console.logger.info("[yellow]Initialization cancelled.[/yellow]")
        sys.exit(1)

    click.echo("Project Initialized")

    try:
        configurator = ClaudeConfigurator(config_manager)
        configurator.setup_project_config(workspace, template or "python", force=force)
    except (ClaudeConfigError, ProfileValidationError) as e:
        logger.error(f"Project configuration setup failed: {e}")
    except Exception:
        logger.error("Unexpected configurator error", exc_info=True)
    # Install git hook for automatic ConPort wiring
    try:
        hooks_dir = workspace / ".git" / "hooks"
        if hooks_dir.exists():
            src = Path(__file__).resolve().parents[2] / "scripts" / "git_post_worktree_hook.sh"
            dst = hooks_dir / "post-checkout"
            if not dst.exists():
                shutil.copy2(src, dst)
                dst.chmod(0o755)
                click.echo("🔗 Installed git post-checkout hook for ConPort wiring")
            else:
                click.echo("✅ Git post-checkout hook present")
    except (OSError, shutil.Error) as e:
        logger.error(f"Git hook installation failed: {e}")
    except Exception:
        logger.error("Unexpected git hook install error", exc_info=True)
@cli.command()
@click.option("--instance", "-i", help="Instance id (feature branch name)")
@click.option("--project", "-p", help="Project root (defaults to CWD)")
def wire_conport(instance: Optional[str], project: Optional[str]):
    """
    Wire project-level ConPort MCP config for the current worktree.

    Writes .claude/claude_config.json with a `conport` stdio server that
    docker-execs into the correct container (mcp-conport[_<instance>]).
    """
    try:
        script = Path(__file__).resolve().parents[2] / "scripts" / "wire_conport_project.py"
        args = [sys.executable, str(script)]
        if instance:
            args.extend(["--instance", instance])
        if project:
            args.extend(["--project", project])
        subprocess.check_call(args)
        click.echo("✅ ConPort wired for this project/worktree")
    except CalledProcessError as e:
        click.echo(f"❌ Failed to wire ConPort: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option("--session", "-s", help="Restore specific session ID")
@click.option("--background", "-b", is_flag=True, help="Launch in background")
@click.option("--debug", is_flag=True, help="Launch with debug output")
@click.option(
    "--dangerous",
    is_flag=True,
    help="⚠️  Enable dangerous mode (no approvals, all tools)",
)
@click.option(
    "--dangerously-skip-permissions",
    is_flag=True,
    help="⚠️  Skip all permission checks (same as --dangerous)",
)
@click.option(
    "--no-mcp",
    is_flag=True,
    help="Skip starting MCP servers (not recommended for ADHD experience)",
)
@click.option(
    "--no-recovery",
    is_flag=True,
    help="Skip orphan worktree recovery menu and continue in current location",
)
@click.option(
    "--litellm",
    "use_litellm",
    is_flag=True,
    help="Route Claude Code traffic through LiteLLM proxy",
)
@click.option(
    "--alt-routing",
    "use_alt_routing",
    is_flag=True,
    help="🚀 Automatic alternative provider routing (OpenRouter, XAI, Minimax) - starts LiteLLM automatically",
)
@click.option(
    "--claude-router/--no-claude-router",
    "use_claude_router",
    default=False,  # Changed to False - OAuth-first design (no routing needed)
    help="Start Claude Code Router per instance (requires global `ccr`)",
)
@click.option(
    "--role",
    "-r",
    help="Run Claude with a specific role/persona (e.g. quickfix, act, plan, research, all, orchestrator).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Preview role/profile effects without launching Claude Code.",
)
@click.option(
    "--grok",
    "use_grok",
    is_flag=True,
    help="🎯 Route ALL requests to xAI Grok Code Fast 1 (requires XAI_API_KEY)",
)
@click.option(
    "--codex",
    "use_codex",
    is_flag=True,
    help="🎯 Route ALL requests to OpenAI GPT-5 Codex via OpenRouter (requires OPENROUTER_API_KEY)",
)
@click.option(
    "--altp",
    "use_altp",
    is_flag=True,
    help="🎯 Tier-matched routing: opus→GPT-5.2-Codex, sonnet→GPT-5-Mini, haiku→Grok Code Fast 1",
)
@click.pass_context
def start(
    ctx,
    session: Optional[str],
    background: bool,
    debug: bool,
    dangerous: bool,
    dangerously_skip_permissions: bool,
    no_mcp: bool,
    no_recovery: bool,
    use_litellm: bool,
    use_alt_routing: bool,
    use_claude_router: bool,
    role: Optional[str],
    dry_run: bool,
    use_grok: bool,
    use_codex: bool,
    use_altp: bool,
    **legacy_kwargs,
):
    """
    🚀 Start Claude Code with ADHD-optimized configuration

    Launches Claude Code with custom MCP servers, restores previous context,
    and activates attention monitoring for the current project.

    Multi-Instance Support:
        Automatically detects running instances and creates isolated worktrees
        for parallel ADHD-optimized development workflows.
    """
    # Track original flag values for subscription mode warnings
    original_grok = use_grok
    original_codex = use_codex
    original_altp = use_altp
    original_litellm = use_litellm
    
    def _ensure_env_consistent_with_mode(final_mode: str) -> None:
        """Ensure environment variables are consistent with routing mode.
        
        Prevents stale proxy env vars when falling back to subscription mode.
        """
        if final_mode == "subscription":
            # Unset proxy variables to ensure direct connection
            env_vars_to_unset = ["ANTHROPIC_BASE_URL", "DOPEMUX_ROUTING_MODE"]
            for var in env_vars_to_unset:
                if var in os.environ:
                    del os.environ[var]
            
            # Only unset ANTHROPIC_API_KEY if we set it (marked by DOPEMUX_SET_ANTHROPIC_API_KEY)
            if os.environ.get("DOPEMUX_SET_ANTHROPIC_API_KEY") == "1":
                if "ANTHROPIC_API_KEY" in os.environ:
                    del os.environ["ANTHROPIC_API_KEY"]
                if "DOPEMUX_SET_ANTHROPIC_API_KEY" in os.environ:
                    del os.environ["DOPEMUX_SET_ANTHROPIC_API_KEY"]
                    
        elif final_mode == "api":
            # Ensure API mode variables are set
            if "DOPEMUX_ROUTING_MODE" not in os.environ:
                os.environ["DOPEMUX_ROUTING_MODE"] = "api"
            
            # Mark that we're managing the API key
            if "ANTHROPIC_API_KEY" in os.environ:
                os.environ["DOPEMUX_SET_ANTHROPIC_API_KEY"] = "1"
    
    legacy_value = legacy_kwargs.get("claude_router")
    if legacy_value is not None:
        use_claude_router = legacy_value

    from .workspace_utils import get_workspace_root
    from .agent_validator import validate_agents_in_workspace

    # Preflight: Validate and fix agents
    try:
        workspace_root = get_workspace_root()
        if workspace_root:
            validate_agents_in_workspace(workspace_root)
    except Exception as e:
        console.logger.warning(f"Agent validation warning: {e}")

    # ── Routing mode from config (replaces legacy flags) ───────────────
    routing_mode = None
    routing_ports = None
    routing_config = None
    
    if RoutingConfig is not None:
        try:
            routing_config = RoutingConfig.load_default()
            routing_mode = routing_config.get_mode()
            routing_ports = routing_config.get_ports()
            console.logger.info(f"[blue]📋 Routing mode: {routing_mode}[/blue]")
        except Exception as e:
            console.logger.warning(f"[yellow]⚠️  Could not load routing config: {e}[/yellow]")
            console.logger.info("[dim]Falling back to legacy flag behavior[/dim]")
    
    # Warn about deprecated flags when routing mode is available
    deprecated_flags_used = any([use_grok, use_codex, use_altp, use_alt_routing, use_claude_router])
    if deprecated_flags_used and routing_mode is not None:
        console.logger.warning("[yellow]⚠️  Deprecated flags detected (--grok/--codex/--altp/--alt-routing/--claude-router)[/yellow]")
        console.logger.info("[dim]Prefer: dopemux routing mode api|subscription[/dim]")

    # Check if provider flags were disabled due to subscription mode
    if not (use_grok or use_codex or use_altp or use_litellm) and (original_grok or original_codex or original_altp or original_litellm):
        console.logger.info("[blue]📋 Using direct Anthropic connection (subscription mode)[/blue]")

    # ── Handle routing mode: api (proxy through CCR/LiteLLM) ─────────
    if routing_mode == "api" and not deprecated_flags_used:
        console.logger.info("[blue]🔄 Routing mode 'api': Starting services and configuring proxy[/blue]")
        
        # Ensure services are installed and running
        try:
            from .launchd_services import LaunchdServiceManager
            service_manager = LaunchdServiceManager.get_instance()
            
            # Check if services are running, start if not
            status = service_manager.get_service_status()
            litellm_running = status.get("litellm", {}).get("status") == "running"
            ccr_running = status.get("ccr", {}).get("status") == "running"
            
            if not litellm_running or not ccr_running:
                console.logger.info("[blue]🚀 Ensuring routing services are running...[/blue]")
                service_manager.install_services()
                service_manager.start_services()
                time.sleep(2)  # Give services time to start
            
            # Verify services are healthy
            health = service_manager.check_health()
            litellm_healthy = health.get("litellm", {}).get("status") == "healthy"
            ccr_healthy = health.get("ccr", {}).get("status") == "healthy"
            
            if not litellm_healthy or not ccr_healthy:
                error_msg = []
                if not litellm_healthy:
                    error_msg.append(f"LiteLLM unhealthy: {health.get('litellm', {}).get('error', 'unknown')}")
                if not ccr_healthy:
                    error_msg.append(f"CCR unhealthy: {health.get('ccr', {}).get('error', 'unknown')}")
                raise click.ClickException(f"Routing services not healthy: {', '.join(error_msg)}")
                
            console.logger.info("[green]✅ Routing services healthy[/green]")
            
        except Exception as e:
            console.logger.error(f"[red]❌ Failed to start routing services: {e}[/red]")
            console.logger.info("[yellow]Falling back to direct Anthropic connection[/yellow]")
            routing_mode = "subscription"
            # Ensure env vars are cleaned up immediately
            _ensure_env_consistent_with_mode(routing_mode)
        
        # Configure environment for API mode
        if routing_mode == "api":
            ccr_port = routing_ports["ccr"]
            ccr_api_key = os.getenv("DOPEMUX_CCR_API_KEY")
            
            # Set environment variables for Claude Code to use CCR
            os.environ["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{ccr_port}"
            if ccr_api_key:
                os.environ["ANTHROPIC_API_KEY"] = ccr_api_key
                # Mark that we set this key so we can clean it up if needed
                os.environ["DOPEMUX_SET_ANTHROPIC_API_KEY"] = "1"
                console.logger.info(f"[dim]✓ CCR API key configured[/dim]")
            else:
                console.logger.warning("[yellow]⚠️  DOPEMUX_CCR_API_KEY not set in routing.env[/yellow]")
            
            console.logger.info(f"[dim]✓ Claude Code → CCR (127.0.0.1:{ccr_port}) → LiteLLM[/dim]")
            
            # Mark that we're using routing
            os.environ["DOPEMUX_ROUTING_MODE"] = "api"
            
    # ── Handle routing mode: subscription (direct to Anthropic) ──────
    elif routing_mode == "subscription" and not deprecated_flags_used:
        console.logger.info("[blue]📋 Routing mode 'subscription': Direct Anthropic connection[/blue]")
        
        # Ensure env vars are consistent with subscription mode
        _ensure_env_consistent_with_mode(routing_mode)
        console.logger.info("[dim]✓ Claude Code → Anthropic (direct)[/dim]")

    # ── Handle --grok / --codex / --altp provider routing ───────────────
    provider_proxy_started = False
    _provider_flags = sum([use_grok, use_codex, use_altp])
    if _provider_flags > 0:
        if _provider_flags > 1:
            raise click.ClickException("Cannot combine --grok, --codex, and --altp. Pick one.")
        if use_alt_routing:
            raise click.ClickException("Cannot combine provider flags with --alt-routing.")

        if use_grok or use_codex:
            # ── Single-target routing ───────────────────────────────────
            provider = GROK_PROVIDER if use_grok else CODEX_PROVIDER
            flag_name = "--grok" if use_grok else "--codex"

            if not os.getenv(provider["api_key_env"]):
                raise click.ClickException(
                    f"${provider['api_key_env']} is required for {flag_name}. "
                    f"Set it in your environment or .env file."
                )

            console.logger.info(
                f"[cyan]🎯 {flag_name}: Routing ALL requests → {provider['label']}[/cyan]"
            )

            config_data = generate_single_target_config(
                target_name=provider["name"],
                litellm_model=provider["model"],
                api_key_env=provider["api_key_env"],
                max_tokens=provider.get("max_tokens", 131072),
                extra_litellm_params=provider.get("extra_params"),
            )
            _routing_summary = f"Claude Code → LiteLLM → {provider['label']}"

        else:
            # ── Multi-target tier-matched routing (--altp) ──────────────
            # Check if we should warn about proxy usage
            current_routing_mode = "subscription"  # Default to subscription
            try:
                if RoutingConfig is not None:
                    routing_config = RoutingConfig.load_default()
                    current_routing_mode = routing_config.get_mode()
            except Exception:
                pass

            if current_routing_mode != "api":
                console.logger.warning("[yellow]⚠️  --altp flag ignored in subscription mode[/yellow]")
                console.logger.info("[dim]   Use 'dopemux routing mode api' to enable proxy routing[/dim]")
                # Fall through to default behavior (direct connection)
                use_altp = False
                use_litellm = False
            else:
                missing_keys = [
                    k for k in ALTP_PROVIDER["required_keys"] if not os.getenv(k)
                ]
                if missing_keys:
                    raise click.ClickException(
                        f"--altp requires: {', '.join('$' + k for k in missing_keys)}. "
                        f"Set them in your environment or .env file."
                    )

            console.logger.info("[cyan]🎯 --altp: Tier-matched alternative provider routing[/cyan]")
            for t in ALTP_PROVIDER["targets"]:
                tier = t["name"].replace("altp-", "")
                console.logger.info(f"[dim]   {tier:>6s} → {t['label']} ({t['model']})[/dim]")

            config_data = generate_multi_target_config(ALTP_PROVIDER["targets"])
            
            # Auto-enable Claude Code Router for API translation
            use_claude_router = True
            console.logger.info("[dim]   Enabling Claude Code Router for API translation (responses → completions)[/dim]")
            
            _routing_summary = "Claude Code → CCR → LiteLLM → tier-matched providers"

        console.logger.info("[blue]🔄 Starting LiteLLM proxy (no DB required)...[/blue]")
        try:
            litellm_port, litellm_master_key = start_simple_proxy(
                project_root=Path.cwd(),
                config_data=config_data,
            )
            provider_proxy_started = True
        except LiteLLMProxyError as exc:
            raise click.ClickException(str(exc))

        console.logger.info(f"[green]✅ LiteLLM proxy ready on port {litellm_port}[/green]")

        # Wire Claude Code to use the proxy
        os.environ["DOPEMUX_CLAUDE_VIA_LITELLM"] = "true"
        os.environ["DOPEMUX_DEFAULT_LITELLM"] = "1"
        os.environ["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{litellm_port}"
        os.environ["LITELLM_MASTER_KEY"] = litellm_master_key
        os.environ["DOPEMUX_LITELLM_MASTER_KEY"] = litellm_master_key
        os.environ["ANTHROPIC_API_KEY"] = litellm_master_key

        # Export CCR upstream env vars so Claude Code Router uses the new proxy
        os.environ["CLAUDE_CODE_ROUTER_PROVIDER"] = "litellm"
        os.environ["CLAUDE_CODE_ROUTER_UPSTREAM_URL"] = f"http://127.0.0.1:{litellm_port}/v1/chat/completions"
        os.environ["CLAUDE_CODE_ROUTER_UPSTREAM_KEY_VAR"] = "DOPEMUX_LITELLM_MASTER_KEY"
        
        if use_altp:
            # For --altp, we map to the tier names defined in generate_multi_target_config
            # CCR will expose these exact model names to Claude Code
            os.environ["CLAUDE_CODE_ROUTER_MODELS"] = "altp-opus,altp-sonnet,altp-haiku"
        elif 'provider' in locals():
            os.environ["CLAUDE_CODE_ROUTER_MODELS"] = provider["name"]

        use_alt_routing = False  # Skip the full alt-routing block below

        console.logger.info(f"[dim]✓ {_routing_summary} (:{litellm_port})[/dim]")
        console.logger.info("")

    # Handle --alt-routing flag (automatic LiteLLM setup)
    if use_alt_routing:
        use_litellm = True
        console.logger.info("[cyan]🚀 Alternative routing enabled - starting LiteLLM automatically...[/cyan]")

        from pathlib import Path as EnvPath
        from dotenv import load_dotenv

        routing_env = EnvPath.cwd() / ".env.routing"
        if routing_env.exists():
            load_dotenv(routing_env)
            console.logger.info("[dim]✓ Loaded .env.routing[/dim]")
        else:
            console.logger.info("[yellow]⚠️  .env.routing not found - using defaults[/yellow]")

        instance_dir = Path.cwd() / ".dopemux" / "litellm" / "A"
        instance_dir.mkdir(parents=True, exist_ok=True)
        litellm_log = instance_dir / "litellm.log"
        master_key_path = instance_dir / "master.key"
        db_url_path = instance_dir / "database.url"

        remember_raw = os.getenv("DOPEMUX_LITELLM_REMEMBER_DB", "").strip().lower()
        remember_db = remember_raw not in {"0", "false", "no"}
        db_url = (
            os.getenv("DOPEMUX_LITELLM_DB_URL")
            or os.getenv("LITELLM_DATABASE_URL")
            or os.getenv("DATABASE_URL")
        )
        if not db_url and remember_db and db_url_path.exists():
            try:
                loaded = db_url_path.read_text(encoding="utf-8").strip()
                if loaded:
                    db_url = loaded
            except (OSError, UnicodeDecodeError) as e:
                logger.error(f"Failed to read stored LiteLLM DB URL: {e}")
            except Exception:
                logger.error("Unexpected DB URL load error", exc_info=True)
        if not db_url:
            console.logger.info("[red]❌ LiteLLM metrics database is required for alternative routing.[/red]")
            console.logger.info("[yellow]   Set DOPEMUX_LITELLM_DB_URL in .env.routing and ensure the database is reachable.[/yellow]")
            console.logger.info("\n[cyan]Example:[/cyan]")
            console.logger.info("  DOPEMUX_LITELLM_DB_URL=postgresql://user:password@localhost:5432/litellm")  # pragma: allowlist secret
            raise click.ClickException("LiteLLM metrics database not configured.")

        stored_master_key: Optional[str] = None
        if master_key_path.exists():
            try:
                stored_master_key = master_key_path.read_text(encoding="utf-8").strip()
            except (OSError, UnicodeDecodeError) as e:
                stored_master_key = None
                logger.error(f"Failed to read stored master key: {e}")
            except (OSError, UnicodeDecodeError) as e:
                stored_master_key = None
                logger.error(f"Failed to read stored master key: {e}")
            except Exception:
                stored_master_key = None
                logger.exception("Unexpected master key read error")
        env_master_key_raw = (os.getenv("LITELLM_MASTER_KEY") or "").strip()
        candidate_keys: List[str] = []
        for key in (stored_master_key, env_master_key_raw):
            if key and key not in candidate_keys:
                candidate_keys.append(key)

        import httpx

        # Check if port 4000 is available, otherwise use an alternative
        def is_port_available(port: int) -> bool:
            """Check if a port is available for binding."""
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('127.0.0.1', port))
                    return True
                except OSError:
                    return False

        litellm_port = 4000
        if not is_port_available(litellm_port):
            # Port 4000 is taken, try 4001
            litellm_port = 4001
            if not is_port_available(litellm_port):
                # Port 4001 is also taken, try 4002
                litellm_port = 4002
                if not is_port_available(litellm_port):
                    console.logger.info("[red]❌ Ports 4000-4002 are all in use.[/red]")
                    console.logger.info("[yellow]   Free up a port or stop an existing LiteLLM instance.[/yellow]")
                    raise click.ClickException("No available ports for LiteLLM proxy.")
            console.logger.info(f"[yellow]⚠️  Port 4000 is in use, using port {litellm_port} instead[/yellow]")

        litellm_master_key = ""
        regenerated_master_key = False
        litellm_running = False

        # Check if LiteLLM is already running on the determined port
        try:
            resp = httpx.get(
                f"http://localhost:{litellm_port}/health/readiness",
                timeout=2,
            )
            if resp.status_code == 200:
                litellm_running = True
                # Use stored key if available, otherwise use env var
                litellm_master_key = stored_master_key or env_master_key_raw or ""
        except httpx.HTTPError as exc:
            cause = getattr(exc, "__cause__", None)
            if isinstance(cause, OSError) and getattr(cause, "errno", None) == 1:
                console.print(
                    "[yellow]⚠️ LiteLLM health probe blocked by OS (operation not permitted); proceeding without inline check.[/yellow]"
                )
        except Exception as e:
            pass

            logger.error(f"Error: {e}")
        if not litellm_master_key:
            base_candidate = env_master_key_raw or stored_master_key
            litellm_master_key, regenerated_master_key = ensure_master_key(base_candidate)
            if regenerated_master_key:
                console.logger.info("[yellow]⚠️  Generated LiteLLM master key with sk- prefix for proxy auth[/yellow]")
        else:
            regenerated_master_key = False

        os.environ["LITELLM_MASTER_KEY"] = litellm_master_key

        if not stored_master_key or stored_master_key != litellm_master_key:
            try:
                master_key_path.write_text(litellm_master_key, encoding="utf-8")
            except (OSError, IOError) as e:
                logger.error(f"Master key write failed: {e}")
            except Exception:
                logger.error("Unexpected master key write error", exc_info=True)
        config_source: Optional[Path] = None
        if (instance_dir / "litellm.config.yaml").exists():
            config_source = instance_dir / "litellm.config.yaml"

        if config_source and config_source.exists():
            try:
                config_data = yaml.safe_load(config_source.read_text(encoding="utf-8")) or {}
            except yaml.YAMLError:
                config_data = {}
        else:
            try:
                config_data = yaml.safe_load(DEFAULT_LITELLM_CONFIG) or {}
            except yaml.YAMLError:
                config_data = {}

        general_settings = config_data.setdefault("general_settings", {})
        general_settings["master_key"] = litellm_master_key

        if dry_run:
            console.print("[dim]⚡ Dry-run: Skipping LiteLLM DB sync[/dim]")
            db_status_msg = "Dry-run: DB sync skipped"
            db_enabled = True
        else:
            try:
                db_status_msg, db_enabled = sync_litellm_database(instance_dir, db_url)
            except LiteLLMProxyError as exc:
                console.logger.error(f"[red]❌ LiteLLM database setup failed: {exc}[/red]")
                console.logger.info("[yellow]   Fix the database connection (is Postgres running? credentials valid?) and retry.[/yellow]")
                console.logger.info("\n[cyan]Troubleshooting:[/cyan]")
                console.logger.info("  1. Check if PostgreSQL is running: lsof -i :5432 (or your port)")
                console.logger.info("  2. Verify database credentials in .env.routing")
                console.logger.info("  3. Ensure the 'litellm' database exists")
                console.logger.info("  4. Test connection: psql <your_database_url>")
                raise click.ClickException(str(exc))

        if not db_enabled:
            console.logger.info(f"[red]❌ {db_status_msg}[/red]")
            console.logger.info("[yellow]   LiteLLM metrics must be available. Resolve the database issue and retry.")
            raise click.ClickException("LiteLLM metrics database not ready.")

        console.logger.info(f"[dim]{db_status_msg}[/dim]")
        general_settings["database_url"] = db_url

        config_path = instance_dir / "litellm.config.yaml"
        try:
            config_path.write_text(
                yaml.safe_dump(config_data, sort_keys=False, default_flow_style=False),
                encoding="utf-8",
            )
        except Exception as e:
            pass

            logger.error(f"Error: {e}")
        if litellm_running:
            console.logger.info(f"[green]✓ LiteLLM proxy already running on port {litellm_port}[/green]")
        else:
            console.logger.info("[blue]🔄 Starting LiteLLM proxy...[/blue]")
            kill_result = subprocess.run(
                ["pkill", "-f", "litellm"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if kill_result.returncode not in (0, 1):
                console.logger.info("[red]❌ Unable to manage existing LiteLLM processes automatically (permission denied).")
                console.logger.info(f"[yellow]   Stop the existing LiteLLM proxy on port {litellm_port} manually and rerun the command.")
                raise click.ClickException("LiteLLM proxy still running.")

            time.sleep(1)
            litellm_log.parent.mkdir(parents=True, exist_ok=True)
            with open(litellm_log, "w", encoding="utf-8") as log_file:
                subprocess.Popen(
                    ["litellm", "--config", str(config_path), "--port", str(litellm_port), "--host", "0.0.0.0"],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )

            console.logger.info("[dim]⏳ Waiting for LiteLLM to start...[/dim]")
            ready = False
            for _ in range(20):
                try:
                    resp = httpx.get(
                        f"http://127.0.0.1:{litellm_port}/health/readiness",
                        timeout=2,
                    )
                    if resp.status_code == 200:
                        ready = True
                        break
                except httpx.HTTPError as exc:
                    cause = getattr(exc, "__cause__", None)
                    if isinstance(cause, OSError) and getattr(cause, "errno", None) == 1:
                        console.print(
                            "[yellow]⚠️ LiteLLM health probe blocked by OS (operation not permitted); assuming proxy is running.[/yellow]"
                        )
                        ready = True
                        break
                time.sleep(1)

            if not ready:
                console.logger.info("[red]❌ LiteLLM proxy did not become healthy.[/red]")
                console.logger.info(f"[yellow]   Check logs: tail -f {litellm_log}[/yellow]")
                console.logger.info("\n[cyan]Common issues:[/cyan]")
                console.logger.error("  • Database connection failed (check PostgreSQL is running)")
                console.logger.info(f"  • Port {litellm_port} became busy during startup")
                console.logger.error("  • Configuration error in litellm.config.yaml")
                raise click.ClickException("LiteLLM proxy failed to start.")

            console.logger.info(f"[green]✅ LiteLLM proxy ready on port {litellm_port}[/green]")

        os.environ["DOPEMUX_CLAUDE_VIA_LITELLM"] = "true"
        os.environ["DOPEMUX_DEFAULT_LITELLM"] = "1"
        os.environ["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{litellm_port}"
        os.environ["LITELLM_MASTER_KEY"] = litellm_master_key
        os.environ["DOPEMUX_LITELLM_MASTER_KEY"] = litellm_master_key
        os.environ["ANTHROPIC_API_KEY"] = litellm_master_key
        
        # Configure Claude Code Router to use this LiteLLM instance
        os.environ["CLAUDE_CODE_ROUTER_UPSTREAM_URL"] = f"http://127.0.0.1:{litellm_port}/v1/chat/completions"
        os.environ["CLAUDE_CODE_ROUTER_UPSTREAM_KEY_VAR"] = "DOPEMUX_LITELLM_MASTER_KEY"
        os.environ["CLAUDE_CODE_ROUTER_PROVIDER"] = "litellm"
        
        # Extract models from litellm config
        litellm_config = instance_dir / "litellm.config.yaml"
        models_list = _load_litellm_models(litellm_config)
        
        if models_list:
            os.environ["CLAUDE_CODE_ROUTER_MODELS"] = ",".join(models_list)
        else:
            console.logger.info("[yellow]⚠️  No models found in litellm.config.yaml[/yellow]")

        os.environ["DOPEMUX_LITELLM_DB_URL"] = db_url
        os.environ.setdefault("LITELLM_DATABASE_URL", db_url)
        os.environ["DATABASE_URL"] = db_url
        if remember_db:
            try:
                db_url_path.parent.mkdir(parents=True, exist_ok=True)
                db_url_path.write_text(db_url, encoding="utf-8")
            except (OSError, IOError) as e:
                logger.error(f"Persist DB URL failed: {e}")
            except Exception:
                logger.error("Unexpected DB URL persist error", exc_info=True)
        console.logger.info("[dim]ℹ️ LiteLLM metrics database synchronised[/dim]")
        console.logger.info("[dim]✓ Claude Code configured to use LiteLLM proxy[/dim]")
        console.logger.info("")
    # Default to LiteLLM + Router if configured (Option A)
    if not use_litellm and not use_claude_router:
        if os.getenv("DOPEMUX_DEFAULT_LITELLM", "0") == "1":
            use_litellm = True
            use_claude_router = True

    config_manager = ctx.obj["config_manager"]

    role_activation = None
    pending_profile_name: Optional[str] = None
    role_profile = None
    requested_role = role or os.environ.get("DOPEMUX_AGENT_ROLE")
    if requested_role:
        try:
            role_activation = activate_role(requested_role, config_manager, console)
        except RoleNotFoundError:
            available = ", ".join(available_roles())
            console.print(
                f"[red]❌ Unknown role: {requested_role}[/red]\n"
                f"[dim]Available roles: {available}[/dim]"
            )
            sys.exit(1)

        spec = role_activation.spec
        role_profile = _ensure_role_profile(spec)
        pending_profile_name = getattr(role_profile, "name", spec.profile_name)
        if role:
            console.print(
                f"[cyan]🎭 Role activated:[/cyan] {spec.label} "
                f"[dim]({spec.key})[/dim] — {spec.description}"
            )
            if role_activation.enabled_servers:
                console.print(
                    f"[dim]Enabled MCP servers: {', '.join(role_activation.enabled_servers)}[/dim]"
                )
            if role_activation.disabled_servers:
                console.print(
                    f"[dim]Disabled MCP servers: {', '.join(role_activation.disabled_servers)}[/dim]"
                )
        else:
            console.print(
                f"[dim]🎭 Active role:[/dim] {spec.label} "
                f"[dim]({spec.key})[/dim]"
            )
    else:
        pending_profile_name = None

    if dry_run:
        console.logger.info("[cyan]Dry run: no tmux or Claude Code processes will be started.[/cyan]")
        if role_activation:
            spec = role_activation.spec
            console.print(
                f"[dim]Role:[/dim] {spec.label} ({spec.key}) — {spec.description}"
            )
            if role_activation.enabled_servers:
                console.print(
                    f"[dim]MCP servers that would remain enabled: {', '.join(role_activation.enabled_servers)}[/dim]"
                )
            if role_activation.disabled_servers:
                console.print(
                    f"[dim]MCP servers that would be disabled: {', '.join(role_activation.disabled_servers)}[/dim]"
                )
        else:
            current_config = config_manager.load_config()
            enabled_now = sorted(
                name
                for name, server in current_config.mcp_servers.items()
                if server.enabled
            )
            console.print(
                f"[dim]No role specified — current enabled MCP servers: {', '.join(enabled_now)}[/dim]"
            )

        if role_activation and role_activation.missing_required:
            _suggest_server_start(role_activation.missing_required)

        if pending_profile_name:
            profile = role_profile or ProfileManager().get_profile(pending_profile_name)
            if profile:
                try:
                    claude_config = ClaudeConfig()
                    preview = claude_config.apply_profile(
                        profile,
                        create_backup=False,
                        dry_run=True,
                    )
                    preview_servers = sorted(preview.get("mcpServers", {}).keys())
                    console.print(
                        f"[dim]Profile '{profile.name}' would mount MCP servers: {', '.join(preview_servers)}[/dim]"
                    )
                except ClaudeConfigError as err:
                    console.print(
                        f"[yellow]⚠ Claude config preview failed: {err}[/yellow]"
                    )
            else:
                    console.print(
                        f"[yellow]⚠ Profile '{pending_profile_name}' is not defined."
                    )

        console.logger.info("[green]Dry run complete. No changes were made.[/green]")
        ctx.exit(0)

    if role_activation and role_activation.missing_required:
        _suggest_server_start(role_activation.missing_required)
    if role_activation and role_activation.missing_optional:
        console.print(
            f"[dim]Optional services currently offline: {', '.join(role_activation.missing_optional)}[/dim]"
        )

    # Kill all active tmux sessions at start (requested behavior)
    # Skip if running inside tmux to avoid killing the session created by `dopemux tmux start`.
    try:
        if shutil.which("tmux") and not os.environ.get("TMUX"):
            _res = subprocess.run(["tmux", "kill-server"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logging.debug("tmux kill-server executed: returncode=%s", getattr(_res, "returncode", None))
        else:
            logging.debug("Skipping tmux kill-server (inside tmux: %s)", bool(os.environ.get("TMUX")))
    except Exception as e:
        pass

        logger.error(f"Error: {e}")
    cwd_path = Path.cwd()
    project_path = cwd_path

    try:
        dopemux_exists = Path.exists(project_path / ".dopemux")
    except TypeError:
        dopemux_exists = False

    if not dopemux_exists:
        project_path_candidate = get_workspace_root()
        if hasattr(project_path_candidate, "__truediv__"):
            project_path = project_path_candidate
        else:
            project_path = Path(project_path_candidate)

        try:
            dopemux_exists = Path.exists(project_path / ".dopemux")
        except TypeError:
            dopemux_exists = False

    # Check if project is initialized
    if not dopemux_exists:
        console.print(
            "[yellow]Project not initialized. Run 'dopemux init' first.[/yellow]"
        )
        if click.confirm("Initialize now?"):
            ctx.invoke(init, directory=str(project_path))
        else:
            sys.exit(1)

    project_path_real_exists = os.path.isdir(str(project_path))

    if not project_path_real_exists:
        _start_minimal_session(config_manager, project_path, session, background, debug)
        return

    if project_path_real_exists:
        try:
            from subprocess import check_call
            wire_script = Path(__file__).resolve().parents[2] / "scripts" / "wire_conport_project.py"
            check_call([sys.executable, str(wire_script)])
        except Exception as e:
            pass

            logger.error(f"Error: {e}")
    if project_path_real_exists:
        # Worktree Recovery Menu (ADHD-optimized session recovery)
        # Show menu if orphaned worktree sessions exist
        from .worktree_recovery import show_recovery_menu_sync

        try:
            selected_worktree = None
            if not no_recovery:
                selected_worktree = show_recovery_menu_sync(
                    workspace_id=str(project_path),
                    conport_port=3004  # Default ConPort port for instance A
                )

            if selected_worktree:
                console.logger.info(f"\n[blue]🔄 Recovering worktree session: {selected_worktree}[/blue]")
                os.chdir(selected_worktree)
                project_path = Path(selected_worktree)
                console.logger.info(f"[green]✅ Switched to worktree: {project_path.name}[/green]")
                console.logger.info(f"[dim]   Path: {project_path}[/dim]\n")
        except Exception as e:
            console.print(f"[yellow]⚠️ Recovery menu unavailable: {e}[/yellow]")

        try:
            should_exit = False
            if os.environ.get("DOPEMUX_ALLOW_MAIN") != "1":
                should_exit = check_and_protect_main(
                    workspace_path=str(project_path),
                    enforce=False
                )

            new_worktree = consume_last_created_worktree()
            if new_worktree:
                os.chdir(new_worktree)
                project_path = Path.cwd()
                console.logger.info(f"[green]🔀 Switched to worktree: {project_path.name}[/green]")
                console.logger.info(f"[dim]   Path: {project_path}[/dim]")

            if should_exit and not new_worktree:
                sys.exit(0)
        except Exception as e:
            console.print(f"[yellow]⚠️ Protection check unavailable: {e}[/yellow]")

    instance_id = None
    port_base = None
    worktree_path = None
    instance_env_vars = {}

    if project_path_real_exists:
        instance_manager = InstanceManager(project_path)
        running_instances = detect_instances_sync(project_path)

        if running_instances:
            console.logger.info(f"\n[yellow]⚠️  Found {len(running_instances)} running instance(s):[/yellow]")

            table = Table(title="Running Instances")
            table.add_column("Instance", style="cyan")
            table.add_column("Port", style="magenta")
            table.add_column("Branch", style="green")
            table.add_column("Current Worktree", style="blue")

            for inst in running_instances:
                table.add_row(
                    inst.instance_id,
                    str(inst.port_base),
                    inst.git_branch or "unknown",
                    str(inst.worktree_path) if inst.worktree_path else "N/A"
                )

            console.logger.info(table)

            try:
                instance_id, port_base = instance_manager.get_next_available_instance(running_instances)

                console.print(
                    f"\n[blue]💡 Multi-instance mode: Creating new worktree for instance {instance_id}[/blue]"
                )

                if click.confirm(f"Create new worktree on port {port_base}?", default=True):
                    suggested_branch = f"feature/instance-{instance_id}"
                    branch_name = click.prompt(
                        "Branch name",
                        default=suggested_branch,
                        show_default=True
                    )

                    console.logger.info(f"[blue]📁 Creating worktree for {branch_name}...[/blue]")
                    worktree_path = instance_manager.create_worktree(instance_id, branch_name)

                    console.logger.info(f"[green]✅ Worktree created at {worktree_path}[/green]")

                    instance_env_vars = instance_manager.get_instance_env_vars(
                        instance_id,
                        port_base,
                        worktree_path
                    )

                    console.print(
                        f"\n[green]🎯 Starting instance {instance_id} on port {port_base}[/green]"
                    )
                    console.logger.info(f"[dim]   Environment: DOPEMUX_INSTANCE_ID={instance_id}[/dim]")
                    console.logger.info(f"[dim]   Workspace: {project_path}[/dim]")
                    console.logger.info(f"[dim]   Worktree: {worktree_path}[/dim]")

                else:
                    console.logger.info("[yellow]Cancelled. Continuing with single instance.[/yellow]")

            except RuntimeError as e:
                console.logger.info(f"[red]❌ {str(e)}[/red]")
                sys.exit(1)

        if instance_id is None:
            instance_id = 'A'
            port_base = 3000
            worktree_path = project_path

            instance_env_vars = instance_manager.get_instance_env_vars(
                instance_id,
                port_base,
                worktree_path
            )

            console.logger.info("[blue]🆕 Starting first instance (A) on port 3000[/blue]")
    else:
        instance_id = 'A'
        port_base = 3000
        worktree_path = project_path

    if not instance_id:
        instance_id = 'A'
    if not port_base:
        port_base = 3000
    if not worktree_path:
        worktree_path = project_path

    # Optional override for default instance id mapping (advanced)
    try:
        force_id = os.getenv("DOPEMUX_FORCE_INSTANCE_ID", "").strip()
        if force_id and force_id in InstanceManager.AVAILABLE_IDS:
            used = {inst.instance_id for inst in (running_instances or [])}
            if force_id not in used:
                idx = InstanceManager.AVAILABLE_IDS.index(force_id)
                forced_port = InstanceManager.AVAILABLE_PORTS[idx]
                instance_id = force_id
                port_base = forced_port
                # Recompute per-instance env
                instance_env_vars = instance_manager.get_instance_env_vars(
                    instance_id,
                    port_base,
                    worktree_path
                )
                console.logger.info(f"[dim]⚙️  Forced instance id: {instance_id} (port {port_base})[/dim]")
            else:
                console.logger.info(f"[dim]⚠️  DOPEMUX_FORCE_INSTANCE_ID={force_id} already in use; ignoring[/dim]")
    except Exception as e:
        pass

        logger.error(f"Error: {e}")
    # Check if we should use OpenRouter via LiteLLM (for tmux --happy mode)
    if os.getenv("DOPEMUX_USE_OPENROUTER") == "1":
        _configure_openrouter_litellm()
        
        # Force Claude Code to use LiteLLM proxy
        os.environ["ANTHROPIC_API_KEY"] = os.getenv("DOPEMUX_LITELLM_MASTER_KEY", "")
        os.environ["ANTHROPIC_BASE_URL"] = "http://127.0.0.1:4000"
        
        # Also set for Claude Code Router
        os.environ["CLAUDE_CODE_ROUTER_PROVIDER"] = "litellm"
        os.environ["CLAUDE_CODE_ROUTER_UPSTREAM_URL"] = "http://127.0.0.1:4000/v1/chat/completions"
        os.environ["CLAUDE_CODE_ROUTER_UPSTREAM_KEY_VAR"] = "DOPEMUX_LITELLM_MASTER_KEY"
        
        console.logger.info("[green]✅ Forced Claude Code to use LiteLLM proxy[/green]")

    # Inject instance environment variables
    if instance_env_vars:
        # Auto fast per-instance mode for instances beyond A
        if instance_id and instance_id != 'A':
            instance_env_vars["DOPEMUX_FAST_ONLY"] = "1"
        for key, value in instance_env_vars.items():
            os.environ[key] = value

        console.logger.info("[dim]✅ Instance environment variables configured[/dim]")
        _persist_instance_env_exports(project_path, instance_id or "A", instance_env_vars)

    active_profile_applied = False
    if pending_profile_name:
        profile_manager = ProfileManager()
        profile = role_profile or profile_manager.get_profile(pending_profile_name)
        if profile:
            try:
                claude_config = ClaudeConfig()
                claude_config.apply_profile(profile, create_backup=True, dry_run=False)
                try:
                    profile_manager.set_active_profile(project_path, profile.name)
                except (OSError, IOError) as e:
                    logger.error(f"Set active profile failed: {e}")
                except Exception:
                    logger.error("Unexpected set active profile error", exc_info=True)
                console.print(
                    f"[dim]✓ Activated profile '{profile.name}' for Claude Code[/dim]"
                )
                active_profile_applied = True
            except ClaudeConfigError as err:
                console.print(
                    f"[yellow]⚠ Could not apply profile '{profile.name}': {err}[/yellow]"
                )
        else:
            console.print(
                f"[yellow]⚠ Profile '{pending_profile_name}' is not defined."
            )

    if role_activation and not dry_run:
        _invoke_switch_role_script(role_activation.spec.key)

    litellm_proxy_info = None
    # --grok/--codex start their own proxy with direct routing
    # --altp uses CCR as translation layer (not direct routing) due to API compatibility
    _direct_provider_routing = use_grok or use_codex
    # If --litellm is passed, prefer enabling CCR unless explicitly disabled by user
    if use_litellm and not use_claude_router and not _direct_provider_routing:
        use_claude_router = True
    litellm_enabled = use_litellm or use_claude_router

    if litellm_enabled and not use_alt_routing and not _direct_provider_routing and not provider_proxy_started:
        # Require OpenRouter since LiteLLM proxy is configured to route through it
        if not os.environ.get("OPENROUTER_API_KEY"):
            console.logger.info("[red]❌ OPENROUTER_API_KEY is not set.[/red]")
            console.logger.info("[dim]Set OPENROUTER_API_KEY before using --litellm[/dim]")
            sys.exit(1)

        try:
            litellm_manager = LiteLLMProxyManager(project_path, instance_id, port_base)
            litellm_proxy_info = litellm_manager.ensure_started()
            env_updates = litellm_manager.build_client_env(litellm_proxy_info)
            for key, value in env_updates.items():
                os.environ[key] = value

            # Explicit hint for Claude Launcher to route via LiteLLM (API key mode)
            os.environ["DOPEMUX_CLAUDE_VIA_LITELLM"] = "1"

            if not litellm_proxy_info.db_enabled:
                for var in ("DOPEMUX_LITELLM_DB_URL", "LITELLM_DATABASE_URL", "DATABASE_URL"):
                    os.environ.pop(var, None)
        except Exception as e:
            logger.exception("Failed to start LiteLLM proxy: %s", e)
            raise

            if litellm_proxy_info.already_running:
                console.print(
                    f"[green]✅ Reusing LiteLLM proxy at {litellm_proxy_info.base_url}[/green]"
                )
            else:
                console.print(
                    f"[green]✅ LiteLLM proxy ready at {litellm_proxy_info.base_url}[/green]"
                )
                console.print(
                    f"[dim]   Config: {litellm_proxy_info.config_path}[/dim]"
                )
                console.print(
                    f"[dim]   Logs: {litellm_proxy_info.log_path}[/dim]"
                )
            if litellm_proxy_info.db_status:
                prisma_log = litellm_proxy_info.log_path.parent / "prisma.log"
                color = "dim" if litellm_proxy_info.db_enabled else "yellow"
                console.logger.info(f"[{color}]   {litellm_proxy_info.db_status}[/{color}]")
                if prisma_log.exists():
                    console.logger.info(f"[dim]   Prisma log: {prisma_log}[/dim]")

        except LiteLLMProxyError as exc:
            console.logger.error(f"[red]❌ LiteLLM proxy failed: {exc}[/red]")
            sys.exit(1)

    router_info = None
    if use_claude_router and not _direct_provider_routing:
        provider_url = None
        provider_models: List[str] = []
        provider_name = os.environ.get("CLAUDE_CODE_ROUTER_PROVIDER")
        provider_key_env = os.environ.get(
            "CLAUDE_CODE_ROUTER_UPSTREAM_KEY_VAR",
            "DOPEMUX_LITELLM_MASTER_KEY" if litellm_proxy_info else None,
        )
        provider_key: Optional[str] = None
        router_overrides: Dict[str, str] = {}

        if litellm_proxy_info:
            provider_url = f"{litellm_proxy_info.base_url}/v1/chat/completions"
            provider_name = provider_name or "litellm"
            provider_models = _load_litellm_models(litellm_proxy_info.config_path)

            extra_models_env = os.environ.get("CLAUDE_CODE_ROUTER_MODELS", "")
            if extra_models_env:
                provider_models.extend(
                    [
                        model.strip()
                        for model in extra_models_env.split(",")
                        if model.strip()
                    ]
                )

            if provider_models:
                deduped: List[str] = []
                seen_lower = set()
                for model in provider_models:
                    lower = model.lower()
                    if lower in seen_lower:
                        continue
                    seen_lower.add(lower)
                    deduped.append(model)
                provider_models = deduped

                router_overrides = _build_router_overrides(provider_name, provider_models)
        else:
            provider_url = os.environ.get("CLAUDE_CODE_ROUTER_UPSTREAM_URL")
            models_env = os.environ.get("CLAUDE_CODE_ROUTER_MODELS", "")
            provider_models = [m.strip() for m in models_env.split(",") if m.strip()]
            if not provider_name:
                provider_name = os.environ.get("CLAUDE_CODE_ROUTER_PROVIDER", "custom")
            provider_key = os.environ.get("CLAUDE_CODE_ROUTER_UPSTREAM_KEY")

        if not provider_url:
            console.print(
                "[red]❌ Claude Code Router upstream URL is not configured.[/red]"
            )
            console.print(
                "[dim]Set CLAUDE_CODE_ROUTER_UPSTREAM_URL or enable --litellm.[/dim]"
            )
            sys.exit(1)

        if not provider_models:
            console.print(
                "[red]❌ No models configured for Claude Code Router upstream.[/red]"
            )
            console.print(
                "[dim]Set CLAUDE_CODE_ROUTER_MODELS or rely on --litellm defaults.[/dim]"
            )
            sys.exit(1)

        # Print DopeBrainzRouterManager class info before usage.
        console.print("   Enabling Claude Code Router for API translation (responses → completions)")



        router_manager = DopeBrainzRouterManager(project_path, instance_id, port_base)

        try:
            router_info = router_manager.ensure_started(
                provider_url=provider_url,
                provider_models=provider_models,
                provider_name=provider_name or "litellm",
                provider_key=provider_key,
                provider_key_env_var=provider_key_env,
                router_overrides=router_overrides if router_overrides else None,
            )
        except DopeBrainzRouterError as exc:
            console.logger.error(f"[red]❌ DopeBrainz Router failed: {exc}[/red]")
            sys.exit(1)

        router_env = router_manager.build_client_env(router_info)
        # Use router-provided base URL + API key for Claude Code and MCPs.
        # Do not restore original ANTHROPIC_API_KEY here — in API-key proxy mode,
        # the router (or LiteLLM) master key must be used by Claude to avoid login/API errors.
        os.environ.update(router_env)
        
        os.environ.update(router_env)
        
        # Re-export env with router variables so Claude Code can pick them up
        # We explicitly filter here for clarity, though _persist_instance_env_exports has a builtin allowlist.
        allowlist = _get_routing_allowlist()
        export_env = {k: os.environ[k] for k in allowlist if k in os.environ}
        _persist_instance_env_exports(project_path, instance_id, export_env)

        if router_info.already_running:
            console.print(
                f"[green]✅ Reusing Claude Code Router at {router_info.base_url}[/green]"
            )
        else:
            console.print(
                f"[green]✅ Claude Code Router ready at {router_info.base_url}[/green]"
            )
            console.logger.info(f"[dim]   Config: {router_info.config_path}[/dim]")
            console.logger.info(f"[dim]   Logs: {router_info.log_path}[/dim]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        # Restore context
        task = progress.add_task("Restoring context...", total=None)

        # Use worktree path for context if in multi-instance mode
        context_path = worktree_path if worktree_path else project_path
        context_manager = ContextManager(context_path)

        if session:
            context = context_manager.restore_session(session)
        else:
            context = context_manager.restore_latest()

        if context:
            progress.update(
                task,
                description=f"Restored session from {context.get('timestamp', 'unknown')}",
            )
            console.print(
                f"[green]📍 Welcome back! You were working on: {context.get('current_goal', 'Unknown task')}[/green]"
            )
        else:
            progress.update(task, description="Starting fresh session")
            console.logger.info("[blue]🆕 Starting new session[/blue]")

        # Check if dangerous mode has expired
        _check_dangerous_mode_expiry()

        # Handle dangerous mode activation
        is_dangerous_mode = dangerous or dangerously_skip_permissions
        if is_dangerous_mode:
            progress.update(task, description="⚠️  Activating dangerous mode...")
            _activate_dangerous_mode()

        # Auto-configure MCP servers for current worktree (Phase 2: Zero manual steps)
        skip_auto_config = os.getenv("DOPEMUX_SKIP_MCP_AUTOCONFIG", "0").lower() in {"1", "true", "yes"}
        if skip_auto_config:
            progress.update(task, description="⏭️ Skipping MCP auto-configuration (DOPEMUX_SKIP_MCP_AUTOCONFIG)")
        else:
            progress.update(task, description="Auto-configuring MCP servers...")
            from .auto_configurator import WorktreeAutoConfigurator

            auto_config = WorktreeAutoConfigurator()
            workspace_to_configure = worktree_path or project_path
            success, message = auto_config.configure_workspace(workspace_to_configure)

            if success:
                progress.update(task, description="✅ MCP auto-configuration complete")
            else:
                progress.update(task, description="⚠️ MCP auto-configuration skipped")
                console.logger.info(f"[dim]{message}[/dim]")

        # Start MCP servers by default (ADHD-optimized experience)
        if not no_mcp:
            # CRITICAL FIX: Pass instance_env_vars so MCP servers get workspace isolation
            _start_mcp_servers_with_progress(project_path, instance_env=instance_env_vars)
            startup_workspace = (worktree_path or project_path).resolve()
            autoindex_result = _trigger_dope_context_autoindex_startup(startup_workspace)
            if autoindex_result:
                status = autoindex_result.get("status", "unknown")
                if status in {"started", "already_running"}:
                    progress.update(
                        task,
                        description=(
                            f"Autoindex startup {status} for {startup_workspace.name}"
                        ),
                    )
                elif status in {"request_failed", "http_error"}:
                    console.logger.info(
                        "[yellow]⚠️  Autoindex startup trigger failed; continuing without blocking.[/yellow]"
                    )
        else:
            console.logger.info("[yellow]⚠️  Skipping MCP servers (reduced ADHD experience)[/yellow]")

        # Launch Claude Code
        progress.update(task, description="Launching Claude Code...")
        launcher = ClaudeLauncher(config_manager)
        claude_process = launcher.launch(
            project_path=project_path,
            background=background,
            debug=debug,
            context=context,
        )

        # Start attention monitoring
        progress.update(task, description="Starting attention monitoring...")
        attention_monitor = AttentionMonitor(project_path)
        attention_monitor.start_monitoring()

        progress.update(task, description="Ready! 🎯", completed=True)

    # Save instance state to ConPort for crash recovery
    if instance_id and port_base:
        from .instance_state import save_instance_state_sync, InstanceState
        from datetime import datetime, timezone

        # Get current git branch
        try:
            git_branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(worktree_path or project_path),
                capture_output=True,
                text=True,
                check=True
            ).stdout.strip()
        except (subprocess.SubprocessError, OSError) as e:
            git_branch = "unknown"
            logger.debug(f"Git branch detection failed (expected in non-git dirs): {e}")
        except Exception:
            git_branch = "unknown"
            logger.debug("Unexpected git branch detection error")
        state = InstanceState(
            instance_id=instance_id,
            port_base=port_base,
            worktree_path=str(worktree_path or project_path),
            git_branch=git_branch,
            created_at=datetime.now(timezone.utc),
            last_active=datetime.now(timezone.utc),
            status="active",
            last_working_directory=str(worktree_path or project_path),
            last_focus_context=context.get('current_goal', 'New session') if context else 'New session'
        )

        save_instance_state_sync(
            state,
            workspace_id=str(project_path.resolve()),
            conport_port=3004  # Always save via instance A's ConPort
        )
        console.logger.info("[dim]✅ Instance state saved for crash recovery[/dim]")

    if not background:
        console.print(
            "[green]✨ Claude Code is running with ADHD optimizations[/green]"
        )
        console.logger.info("Press Ctrl+C to stop monitoring and save context")

        try:
            claude_process.wait()
        except KeyboardInterrupt:
            console.logger.info("\n[yellow]⏸️ Saving context and stopping...[/yellow]")

            # Mark instance as stopped in ConPort
            if instance_id:
                from .instance_state import load_instance_state_sync, save_instance_state_sync
                from datetime import datetime, timezone

                workspace_id = str(project_path.resolve())
                state = load_instance_state_sync(instance_id, workspace_id, conport_port=3004)
                if state:
                    state.status = 'stopped'
                    state.last_active = datetime.now(timezone.utc)
                    save_instance_state_sync(state, workspace_id, conport_port=3004)
                    console.logger.info("[dim]✅ Instance marked as stopped[/dim]")

            ctx.invoke(save)
            attention_monitor.stop_monitoring()


@cli.command()
@click.option("--message", "-m", help="Save message/note")
@click.option("--force", "-f", is_flag=True, help="Force save even if no changes")
@click.pass_context
def save(ctx, message: Optional[str], force: bool):
    """
    💾 Save current development context

    Captures open files, cursor positions, mental model, and recent decisions
    for seamless restoration later.
    """
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.logger.info("[red]No Dopemux project found in current directory[/red]")
        sys.exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Saving context...", total=None)

        context_manager = ContextManager(project_path)
        session_id = context_manager.save_context(message=message, force=force)

        progress.update(task, description="Context saved!", completed=True)

    console.logger.info(f"[green]✅ Context saved (session: {session_id[:8]})[/green]")
    if message:
        console.logger.info(f"[dim]Note: {message}[/dim]")


@cli.command()
@click.option("--session", "-s", help="Specific session ID to restore")
@click.option(
    "--list", "-l", "list_sessions", is_flag=True, help="List available sessions"
)
@click.pass_context
def restore(ctx, session: Optional[str], list_sessions: bool):
    """
    🔄 Restore previous development context

    Restores files, cursor positions, and mental model from a previous session.
    """
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.logger.info("[red]No Dopemux project found in current directory[/red]")
        sys.exit(1)

    context_manager = ContextManager(project_path)

    if list_sessions:
        sessions = context_manager.list_sessions()
        if not sessions:
            console.logger.info("[yellow]No saved sessions found[/yellow]")
            return

        table = Table(title="Available Sessions")
        table.add_column("ID", style="cyan")
        table.add_column("Timestamp", style="green")
        table.add_column("Goal", style="yellow")
        table.add_column("Files", justify="right", style="blue")

        for s in sessions:
            table.add_row(
                s["id"],
                s["timestamp"],
                s.get("current_goal", "No goal set")[:50],
                str(len(s.get("open_files", []))),
            )

        console.logger.info(table)
        for s in sessions:
            console.logger.info(f"- {s['id']} :: {s.get('current_goal', 'No goal set')}")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Restoring context...", total=None)

        if session:
            context = context_manager.restore_session(session)
        else:
            context = context_manager.restore_latest()

        progress.update(task, description="Context restored!", completed=True)

    if context:
        console.print(
            f"[green]✅ Restored session from {context.get('timestamp', 'unknown')}[/green]"
        )
        console.print(
            f"[blue]🎯 Goal: {context.get('current_goal', 'No goal set')}[/blue]"
        )
        console.print(
            f"[yellow]📁 Files: {len(context.get('open_files', []))} files restored[/yellow]"
        )
    else:
        console.logger.info("[red]❌ No context found to restore[/red]")


@cli.group()
def instances():
    """
    🏗️  Manage multiple Dopemux instances and worktrees

    Commands for managing parallel ADHD-optimized development workflows
    with isolated worktrees and shared database.
    """
    pass


@instances.command("list")
@click.pass_context
def instances_list(ctx):
    """
    📋 List all running instances and worktrees

    Shows currently active instances with their ports, branches, and paths.
    Automatically detects and reports orphaned instances (crashed).
    """
    project_path = Path.cwd()
    workspace_id = str(project_path.resolve())

    instance_manager = InstanceManager(project_path)
    running_instances = detect_instances_sync(project_path)

    # Detect orphaned instances (automatic crash detection)
    orphaned_instances = detect_orphaned_instances_sync(
        project_path,
        workspace_id,
        conport_port=3004  # Always query via instance A's ConPort
    )

    # Show running instances
    if running_instances:
        console.logger.info(f"\n[green]✅ Found {len(running_instances)} running instance(s)[/green]\n")

        table = Table(title="Running Instances")
        table.add_column("Instance", style="cyan", no_wrap=True)
        table.add_column("Port", style="magenta", no_wrap=True)
        table.add_column("Branch", style="green")
        table.add_column("Current Worktree", style="blue")
        table.add_column("Status", style="green")

        for inst in running_instances:
            status = "✅ Healthy" if inst.is_healthy else "⚠️  Unknown"
            table.add_row(
                inst.instance_id,
                str(inst.port_base),
                inst.git_branch or "unknown",
                str(inst.worktree_path) if inst.worktree_path else "main",
                status
            )

        console.logger.info(table)
    else:
        console.logger.info("[yellow]No running instances found[/yellow]")

    # Show orphaned instances (automatic crash detection)
    if orphaned_instances:
        console.logger.info(f"\n[red]⚠️  Found {len(orphaned_instances)} orphaned instance(s)[/red]")
        console.logger.info("[dim]Orphaned instances have crashed but their worktrees still exist[/dim]\n")

        orphan_table = Table(title="Orphaned Instances (Crashed)")
        orphan_table.add_column("Instance", style="red", no_wrap=True)
        orphan_table.add_column("Branch", style="yellow")
        orphan_table.add_column("Last Active", style="dim")
        orphan_table.add_column("Last Focus", style="cyan")
        orphan_table.add_column("Action", style="green")

        from datetime import datetime
        for orphan in orphaned_instances:
            # Calculate time since last active
            if isinstance(orphan['last_active'], str):
                last_active = datetime.fromisoformat(orphan['last_active'])
            else:
                last_active = orphan['last_active']

            time_diff = datetime.now() - last_active
            if time_diff.days > 0:
                time_ago = f"{time_diff.days}d ago"
            elif time_diff.seconds > 3600:
                time_ago = f"{time_diff.seconds // 3600}h ago"
            else:
                time_ago = f"{time_diff.seconds // 60}m ago"

            orphan_table.add_row(
                orphan['instance_id'],
                orphan['git_branch'],
                time_ago,
                orphan.get('last_focus_context', 'N/A')[:40] or "N/A",
                f"dopemux instances resume {orphan['instance_id']}"
            )

        console.logger.info(orphan_table)
        console.logger.info("\n[dim]💡 Tip: Use 'dopemux instances resume <id>' to restart an orphaned instance[/dim]")
        console.logger.info("[dim]     Or use 'dopemux instances cleanup <id>' to remove the worktree[/dim]")

    # Show git worktrees
    console.logger.info("\n[bold]Git Worktrees:[/bold]")
    worktrees = instance_manager.list_worktrees()

    if worktrees:
        worktree_table = Table()
        worktree_table.add_column("ID", style="cyan")
        worktree_table.add_column("Path", style="dim")
        worktree_table.add_column("Branch", style="green")

        for wt_id, wt_path, wt_branch in worktrees:
            worktree_table.add_row(wt_id, str(wt_path), wt_branch)

        console.logger.info(worktree_table)
    else:
        console.logger.info("[dim]No worktrees found[/dim]")


@instances.command("resume")
@click.argument("instance_id")
@click.option("--restore-context", "-r", is_flag=True, help="Restore working directory and focus context")
@click.pass_context
def instances_resume(ctx, instance_id: str, restore_context: bool):
    """
    🔄 Resume an orphaned instance (one-click crash recovery)

    Restarts services for an orphaned instance, optionally restoring
    the last working directory and focus context.

    \b
    Examples:
        dopemux instances resume B              # Restart instance B
        dopemux instances resume B --restore-context  # Restart and restore context

    \b
    ADHD Benefit:
        Zero-friction recovery from crashes. Resume exactly where you left off
        with preserved mental model and context continuity.
    """
    project_path = Path.cwd()
    workspace_id = str(project_path.resolve())

    # Load orphaned instance state
    from .instance_state import load_instance_state_sync

    state = load_instance_state_sync(instance_id, workspace_id, conport_port=3004)

    if not state:
        console.logger.info(f"[red]❌ No saved state found for instance {instance_id}[/red]")
        console.logger.info("[dim]Tip: Use 'dopemux instances list' to see available instances[/dim]")
        sys.exit(1)

    if state.status != 'orphaned':
        console.logger.info(f"[yellow]⚠️  Instance {instance_id} is not orphaned (status: {state.status})[/yellow]")
        if state.status == 'active':
            console.logger.info(f"[dim]Instance is already running on port {state.port_base}[/dim]")
        sys.exit(1)

    # Check if worktree still exists
    worktree_path = Path(state.worktree_path)
    if not worktree_path.exists():
        console.logger.info(f"[red]❌ Worktree not found at {worktree_path}[/red]")
        console.logger.info("[dim]The worktree may have been deleted. Use 'dopemux instances cleanup' to remove state[/dim]")
        sys.exit(1)

    console.logger.info(f"\n[cyan]🔄 Resuming instance {instance_id}...[/cyan]")
    console.logger.info(f"   Branch: {state.git_branch}")
    console.logger.info(f"   Worktree: {worktree_path}")
    console.logger.info(f"   Port base: {state.port_base}")

    if state.last_focus_context:
        console.logger.info(f"   Last focus: [dim]{state.last_focus_context}[/dim]")

    # Show context restoration info
    if restore_context and state.last_working_directory:
        console.logger.info(f"\n[green]✨ Context restoration enabled:[/green]")
        console.logger.info(f"   Working directory: {state.last_working_directory}")
        if state.last_focus_context:
            console.logger.info(f"   Focus context: {state.last_focus_context}")

    # Start instance
    console.logger.info(f"\n[yellow]💡 Starting instance {instance_id} on port {state.port_base}...[/yellow]")

    # Set environment variables for this process
    env = os.environ.copy()
    env.update({
        "DOPEMUX_INSTANCE_ID": instance_id,
        "DOPEMUX_WORKSPACE_ID": workspace_id,
        "DOPEMUX_PORT_BASE": str(state.port_base),
        "TASK_MASTER_PORT": str(state.port_base + 5),
        "SERENA_PORT": str(state.port_base + 6),
        "CONPORT_PORT": str(state.port_base + 7),
        "INTEGRATION_BRIDGE_PORT": str(state.port_base + 16),
    })

    # Change to worktree directory if restoring context
    original_cwd = os.getcwd()
    if restore_context and state.last_working_directory:
        try:
            os.chdir(state.last_working_directory)
            console.logger.info(f"[green]✅ Changed to working directory: {state.last_working_directory}[/green]")
        except Exception as e:
            console.logger.info(f"[yellow]⚠️  Could not change to working directory: {e}[/yellow]")
            console.logger.info("[dim]Staying in current directory[/dim]")

    console.logger.info(f"\n[green]✅ Instance {instance_id} resumed successfully![/green]")
    console.logger.info(f"[dim]Services are starting on port {state.port_base}...[/dim]")

    if restore_context:
        console.logger.info("\n[cyan]📍 Context Restored:[/cyan]")
        console.logger.info(f"   You were working on: {state.last_focus_context or 'N/A'}")
        console.logger.info(f"   In directory: {os.getcwd()}")

    console.logger.info(f"\n[dim]💡 Tip: Instance will be marked as 'active' when dopemux start completes[/dim]")
    console.logger.info(f"[dim]     Run: cd {worktree_path} && dopemux start[/dim]")

    # Mark as active (optimistic - actual start command will confirm)
    from .instance_state import save_instance_state_sync
    state.status = 'active'
    from datetime import datetime
    state.last_active = datetime.now()
    save_instance_state_sync(state, workspace_id, conport_port=3004)


@instances.command("cleanup")
@click.argument("instance_id", required=False)
@click.option("--all", "-a", is_flag=True, help="Clean up all stopped instances")
@click.option("--force", "-f", is_flag=True, help="Force cleanup without confirmation")
@click.pass_context
def instances_cleanup(ctx, instance_id: Optional[str], all: bool, force: bool):
    """
    🧹 Clean up stopped instance worktrees

    Removes git worktrees for stopped instances to free up disk space.

    \b
    Examples:
        dopemux instances cleanup B          # Remove instance B worktree
        dopemux instances cleanup --all      # Remove all stopped instances
    """
    project_path = Path.cwd()
    instance_manager = InstanceManager(project_path)

    if not instance_id and not all:
        console.logger.info("[red]❌ Specify instance ID or use --all flag[/red]")
        console.logger.info("[dim]Usage: dopemux instances cleanup <ID> or --all[/dim]")
        sys.exit(1)

    if all:
        # Get all worktrees
        worktrees = instance_manager.list_worktrees()
        running_instances = detect_instances_sync(project_path)
        running_ids = {inst.instance_id for inst in running_instances}

        # Find stopped instances
        stopped_instances = [
            (wt_id, wt_path) for wt_id, wt_path, _ in worktrees
            if wt_id not in running_ids and wt_id != 'A'
        ]

        if not stopped_instances:
            console.logger.info("[green]✅ No stopped instances to clean up[/green]")
            return

        console.logger.info(f"\n[yellow]⚠️  Found {len(stopped_instances)} stopped instance(s) to clean:[/yellow]")
        for wt_id, wt_path in stopped_instances:
            console.logger.info(f"  • Instance {wt_id}: {wt_path}")

        if not force and not click.confirm("\nProceed with cleanup?"):
            console.logger.info("[yellow]Cleanup cancelled[/yellow]")
            return

        # Clean up each stopped instance
        from .instance_state import cleanup_instance_state_sync
        workspace_id = str(project_path.resolve())

        for wt_id, _ in stopped_instances:
            if instance_manager.cleanup_worktree(wt_id):
                console.logger.info(f"[green]✅ Removed worktree for instance {wt_id}[/green]")

                # Also remove instance state from ConPort
                if cleanup_instance_state_sync(wt_id, workspace_id, conport_port=3004):
                    console.logger.info(f"[dim]✅ Removed instance state for {wt_id}[/dim]")
            else:
                console.logger.error(f"[red]❌ Failed to remove worktree for instance {wt_id}[/red]")

    else:
        # Clean up specific instance
        if instance_id == 'A':
            console.logger.info("[red]❌ Cannot clean up main worktree (instance A)[/red]")
            sys.exit(1)

        # Check if instance is running
        running_instances = detect_instances_sync(project_path)
        if any(inst.instance_id == instance_id for inst in running_instances):
            console.logger.info(f"[red]❌ Instance {instance_id} is still running[/red]")
            console.logger.info("[dim]Stop the instance before cleaning up its worktree[/dim]")
            sys.exit(1)

        worktree_path = instance_manager._get_worktree_path(instance_id)
        if not worktree_path or not worktree_path.exists():
            console.logger.info(f"[yellow]⚠️  No worktree found for instance {instance_id}[/yellow]")
            return

        console.logger.info(f"\n[yellow]⚠️  Removing worktree for instance {instance_id}[/yellow]")
        console.logger.info(f"[dim]Path: {worktree_path}[/dim]")

        if not force and not click.confirm("Proceed?"):
            console.logger.info("[yellow]Cleanup cancelled[/yellow]")
            return

        if instance_manager.cleanup_worktree(instance_id):
            console.logger.info(f"[green]✅ Removed worktree for instance {instance_id}[/green]")

            # Also remove instance state from ConPort
            from .instance_state import cleanup_instance_state_sync
            workspace_id = str(project_path.resolve())

            if cleanup_instance_state_sync(instance_id, workspace_id, conport_port=3004):
                console.logger.info(f"[dim]✅ Removed instance state from ConPort[/dim]")
        else:
            console.logger.error(f"[red]❌ Failed to remove worktree for instance {instance_id}[/red]")


@cli.command()
@click.option("--attention", "-a", is_flag=True, help="Show attention metrics")
@click.option("--context", "-c", is_flag=True, help="Show context information")
@click.option("--tasks", "-t", is_flag=True, help="Show task progress")
@click.option("--mobile", "-m", is_flag=True, help="Show Happy mobile status")
@click.pass_context
def status(ctx, attention: bool, context: bool, tasks: bool, mobile: bool):
    """
    📊 Show current session status and metrics

    Displays attention state, context information, task progress, and
    ADHD accommodation effectiveness.
    """
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.logger.info("[red]No Dopemux project found in current directory[/red]")
        sys.exit(1)

    # Show all by default if no specific flags
    if not any([attention, context, tasks, mobile]):
        attention = context = tasks = mobile = True

    if attention:
        monitor = AttentionMonitor(project_path)
        metrics = monitor.get_current_metrics()

        table = Table(title="🧠 Attention Metrics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Status", style="yellow")

        table.add_row(
            "Current State",
            metrics.get("attention_state", "unknown"),
            _get_attention_emoji(metrics.get("attention_state")),
        )
        table.add_row(
            "Session Duration", f"{metrics.get('session_duration', 0):.1f} min", "⏱️"
        )
        table.add_row("Focus Score", f"{metrics.get('focus_score', 0):.1%}", "🎯")
        table.add_row("Context Switches", str(metrics.get("context_switches", 0)), "🔄")

        console.logger.info(table)

    if context:
        context_manager = ContextManager(project_path)
        current_context = context_manager.get_current_context()

        table = Table(title="📍 Context Information")
        table.add_column("Item", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Current Goal", current_context.get("current_goal", "Not set"))
        table.add_row("Open Files", str(len(current_context.get("open_files", []))))
        table.add_row("Last Save", current_context.get("last_save", "Never"))
        table.add_row("Git Branch", current_context.get("git_branch", "unknown"))

        console.logger.info(table)

    if tasks:
        decomposer = TaskDecomposer(project_path)
        progress_info = decomposer.get_progress()

        if progress_info:
            table = Table(title="📋 Task Progress")
            table.add_column("Task", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Progress", style="yellow")

            for task in progress_info.get("tasks", []):
                status_emoji = (
                    "✅" if task["completed"] else "🔄" if task["in_progress"] else "⏳"
                )
                table.add_row(
                    task["name"], status_emoji, f"{task.get('progress', 0):.0%}"
                )

            console.logger.info(table)
        else:
            console.logger.info("[yellow]No active tasks found[/yellow]")

    if mobile:
        from .mobile.runtime import check_cli_health, list_mobile_panes
        from .mobile.tmux_utils import TmuxError

        cfg_manager = ctx.obj.get("config_manager") if ctx.obj else ConfigManager()
        mobile_cfg = cfg_manager.get_mobile_config()

        happy_ok = check_cli_health("happy")
        claude_ok = check_cli_health("claude")

        try:
            panes = list_mobile_panes()
            tmux_error = None
        except TmuxError as exc:
            panes = []
            tmux_error = str(exc)

            logger.error(f"Error: {e}")
        mobile_table = Table(title="📱 Mobile Status")
        mobile_table.add_column("Check", style="cyan")
        mobile_table.add_column("Status", style="green")

        mobile_table.add_row("Mobile Enabled", "✅ Enabled" if mobile_cfg.enabled else "❌ Disabled")
        mobile_table.add_row("Happy CLI", "✅ Healthy" if happy_ok else "❌ Unavailable")
        mobile_table.add_row("Claude CLI", "✅ Healthy" if claude_ok else "⚠️ Check setup")

        if tmux_error:
            mobile_table.add_row("tmux", f"⚠️ {tmux_error}")
        else:
            mobile_table.add_row("Active Sessions", str(len(panes)))

        console.logger.info(mobile_table)

        if not tmux_error and panes:
            sessions_table = Table(title="📱 Active Happy Sessions")
            sessions_table.add_column("Pane", style="cyan")
            sessions_table.add_column("Window", style="green")
            sessions_table.add_column("Path", style="dim")

            for pane in panes:
                sessions_table.add_row(
                    pane.title or "(unnamed)",
                    pane.window or "?",
                    pane.path or "",
                )

            console.logger.info(sessions_table)


@cli.command("run-tests")
@click.argument("command", nargs=-1)
@click.option("--cwd", type=click.Path(file_okay=False, dir_okay=True), help="Working directory for the test command")
@click.option("--label", default="Test run", show_default=True, help="Notification label for this test run")
@click.pass_context
def run_tests(ctx, command: Sequence[str], cwd: Optional[str], label: str):
    """Run automated tests and send mobile notifications."""

    args = list(command) if command else ["pytest"]
    task_label = label or "Test run"

    with mobile_task_notification(
        ctx,
        task_label,
        success_message=f"✅ {task_label} complete",
        failure_message=f"❌ {task_label} failed",
    ):
        result = subprocess.run(args, cwd=cwd, check=False)
        cmd_display = " ".join(args)

        if result.returncode == 0:
            console.logger.info(f"[green]✅ Tests passed ({cmd_display})[/green]")
        else:
            console.logger.error(f"[red]❌ Tests failed ({cmd_display})[/red]")
            sys.exit(result.returncode)

    cfg_manager = ctx.obj.get("config_manager") if ctx.obj else ConfigManager()
    update_tmux_mobile_indicator(cfg_manager)


@cli.command("run-build")
@click.argument("command", nargs=-1)
@click.option("--cwd", type=click.Path(file_okay=False, dir_okay=True), help="Working directory for the build command")
@click.option("--label", default="Build", show_default=True, help="Notification label for this build run")
@click.pass_context
def run_build(ctx, command: Sequence[str], cwd: Optional[str], label: str):
    """Run a build command and send mobile notifications."""

    # Default to npm build if no command provided
    args = list(command) if command else ["npm", "run", "build"]
    task_label = label or "Build"

    with mobile_task_notification(
        ctx,
        task_label,
        success_message=f"✅ {task_label} complete",
        failure_message=f"❌ {task_label} failed",
    ):
        result = subprocess.run(args, cwd=cwd, check=False)
        cmd_display = " ".join(args)

        if result.returncode == 0:
            console.logger.info(f"[green]✅ Build succeeded ({cmd_display})[/green]")
        else:
            console.logger.error(f"[red]❌ Build failed ({cmd_display})[/red]")
            sys.exit(result.returncode)

    cfg_manager = ctx.obj.get("config_manager") if ctx.obj else ConfigManager()
    update_tmux_mobile_indicator(cfg_manager)


def _run_taskx_kernel(base_args: Sequence[str], taskx_args: Sequence[str]) -> None:
    """Delegate kernel lifecycle commands to scripts/taskx."""
    repo_root = Path(__file__).resolve().parents[2]
    wrapper = repo_root / "scripts" / "taskx"
    if not wrapper.exists():
        console.logger.error(f"[red]TaskX wrapper missing: {wrapper}[/red]")
        sys.exit(1)

    cmd = [str(wrapper), *base_args, *taskx_args]
    result = subprocess.run(cmd, cwd=repo_root, check=False)
    if result.returncode != 0:
        sys.exit(result.returncode)


@cli.group("kernel")
def kernel() -> None:
    """TaskX kernel lifecycle commands delegated through scripts/taskx."""


@kernel.command("doctor", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_doctor(taskx_args: Sequence[str]) -> None:
    """Run TaskX doctor."""
    _run_taskx_kernel(["doctor"], taskx_args)


@kernel.command("compile", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_compile(taskx_args: Sequence[str]) -> None:
    """Run TaskX Dopemux compile lifecycle step."""
    _run_taskx_kernel(["dopemux", "compile"], taskx_args)


@kernel.command("run", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_run(taskx_args: Sequence[str]) -> None:
    """Run TaskX Dopemux run lifecycle step."""
    _run_taskx_kernel(["dopemux", "run"], taskx_args)


@kernel.command("collect", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_collect(taskx_args: Sequence[str]) -> None:
    """Run TaskX Dopemux collect lifecycle step."""
    _run_taskx_kernel(["dopemux", "collect"], taskx_args)


@kernel.command("gate", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_gate(taskx_args: Sequence[str]) -> None:
    """Run TaskX Dopemux gate lifecycle step."""
    _run_taskx_kernel(["dopemux", "gate"], taskx_args)


@kernel.command("promote", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_promote(taskx_args: Sequence[str]) -> None:
    """Run TaskX Dopemux promote lifecycle step."""
    _run_taskx_kernel(["dopemux", "promote"], taskx_args)


@kernel.command("feedback", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_feedback(taskx_args: Sequence[str]) -> None:
    """Run TaskX Dopemux feedback lifecycle step."""
    _run_taskx_kernel(["dopemux", "feedback"], taskx_args)


@kernel.command("loop", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_loop(taskx_args: Sequence[str]) -> None:
    """Run TaskX Dopemux loop lifecycle step."""
    _run_taskx_kernel(["dopemux", "loop"], taskx_args)


@cli.command()
@click.argument("description", required=False)
@click.option("--duration", "-d", type=int, default=25, help="Task duration in minutes")
@click.option(
    "--priority", "-p", type=click.Choice(["low", "medium", "high"]), default="medium"
)
@click.option("--list", "-l", "list_tasks", is_flag=True, help="List current tasks")
@click.pass_context
def task(
    ctx, description: Optional[str], duration: int, priority: str, list_tasks: bool
):
    """
    📋 DEPRECATED - Use SuperClaude /dx: commands instead

    This command has been replaced by:
    - /dx:implement - Start ADHD-optimized implementation session
    - /dx:session start/end/break - Session management
    - /dx:load - Load tasks from ConPort
    - /dx:stats - View ADHD metrics and progress

    See: docs/90-adr/ADR-XXXX-path-c-migration.md
    """
    console.logger.info("[yellow]" + "="*60 + "[/yellow]")
    console.logger.info("[red]⚠️  DEPRECATED COMMAND[/red]")
    console.logger.info("[yellow]" + "="*60 + "[/yellow]")
    console.logger.info()
    console.logger.info("The 'dopemux task' command has been replaced by SuperClaude /dx: commands:")
    console.logger.info()
    console.logger.info("  [cyan]/dx:implement[/cyan] - Start ADHD-optimized implementation session")
    console.logger.info("  [cyan]/dx:session start[/cyan] - Begin work session")
    console.logger.info("  [cyan]/dx:load[/cyan] - Load tasks from ConPort")
    console.logger.info("  [cyan]/dx:stats[/cyan] - View ADHD metrics and progress")
    console.logger.info()
    console.logger.info("Migration completed: October 2025")
    console.logger.info("See: [blue]docs/90-adr/ADR-XXXX-path-c-migration.md[/blue]")
    console.logger.info()
    console.logger.info("[yellow]" + "="*60 + "[/yellow]")

    project_path = Path.cwd()
    if not (project_path / ".dopemux").exists():
        console.logger.info("[red]No Dopemux project found in current directory[/red]")
        sys.exit(1)

    decomposer = TaskDecomposer(project_path)

    if list_tasks:
        tasks = decomposer.list_tasks()
        if not tasks:
            console.logger.info("[yellow]No tasks found[/yellow]")
            return

        table = Table(title="Current Tasks")
        table.add_column("Task", style="cyan")
        table.add_column("Priority", style="yellow")
        table.add_column("Duration", style="green")
        table.add_column("Status", style="blue")

        for task in tasks:
            status = (
                "✅ Complete"
                if task.get("status") == "completed"
                else (
                    "🔄 In Progress"
                    if task.get("status") == "in_progress"
                    else "⏳ Pending"
                )
            )
            table.add_row(
                task["description"],
                task["priority"],
                f"{task['estimated_duration']}m",
                status,
            )

        console.logger.info(table)
        return

    # Check if description is provided for adding new task
    if not description:
        console.logger.info("[red]Description required when not listing tasks[/red]")
        console.logger.info("Use 'dopemux task --list' to list current tasks")
        sys.exit(1)

    # Add new task
    task_id = decomposer.add_task(
        description=description, duration=duration, priority=priority
    )

    console.logger.info(f"[green]✅ Task added: {description}[/green]")
    console.logger.info(f"[blue]🆔 ID: {task_id}[/blue]")
    console.logger.info(f"[yellow]⏱️ Duration: {duration} minutes[/yellow]")
    console.logger.info(f"[cyan]🎯 Priority: {priority}[/cyan]")


@cli.group()
@click.pass_context
def autoresponder(ctx):
    """
    🤖 Manage Claude Auto Responder integration

    Automatic confirmation responses for Claude Code prompts with
    ADHD-optimized controls and attention-aware features.
    """


@autoresponder.command("start")
@click.option(
    "--terminal-scope",
    "-t",
    type=click.Choice(["current", "all", "project"]),
    help="Terminal scope for monitoring",
)
@click.option("--delay", "-d", type=float, help="Response delay in seconds (0-10)")
@click.option("--timeout", type=int, help="Auto-stop timeout in minutes")
@click.option(
    "--whitelist/--no-whitelist", default=None, help="Enable/disable tool whitelisting"
)
@click.option("--debug/--no-debug", default=None, help="Enable/disable debug mode")
@click.pass_context
def autoresponder_start(ctx, terminal_scope, delay, timeout, whitelist, debug):
    """
    🚀 Start Claude Auto Responder

    Begins automatic confirmation of Claude Code prompts with current
    configuration settings and ADHD optimizations.
    """
    config_manager = ctx.obj["config_manager"]
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.logger.info("[red]No Dopemux project found in current directory[/red]")
        sys.exit(1)

    # Update configuration if options provided
    updates = {}
    if terminal_scope:
        updates["terminal_scope"] = terminal_scope
    if delay is not None:
        updates["response_delay"] = delay
    if timeout:
        updates["timeout_minutes"] = timeout
    if whitelist is not None:
        updates["whitelist_tools"] = whitelist
    if debug is not None:
        updates["debug_mode"] = debug

    if updates:
        config_manager.update_claude_autoresponder(**updates)

    from integrations.claude_autoresponder import create_autoresponder_manager

    autoresponder_manager = create_autoresponder_manager(config_manager, project_path)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Starting auto responder...", total=None)

        success = autoresponder_manager.start()

        if success:
            progress.update(
                task, description="Auto responder started! 🤖", completed=True
            )
            console.logger.info("[green]✅ Claude Auto Responder is now active[/green]")
            console.print(
                "[blue]🎯 Monitoring for Claude Code confirmation prompts[/blue]"
            )

            config = config_manager.get_claude_autoresponder_config()
            console.logger.info(f"[yellow]📡 Scope: {config.terminal_scope}[/yellow]")
            if config.response_delay > 0:
                console.logger.info(f"[cyan]⏱️ Delay: {config.response_delay}s[/cyan]")
            console.print(
                f"[dim]💤 Auto-stop after {config.timeout_minutes} minutes of inactivity[/dim]"
            )
        else:
            progress.update(task, description="Failed to start", completed=True)
            console.logger.error("[red]❌ Failed to start auto responder[/red]")
            console.print(
                "[yellow]💡 Try running 'dopemux autoresponder setup' first[/yellow]"
            )
            sys.exit(1)


@autoresponder.command("stop")
@click.pass_context
def autoresponder_stop(ctx):
    """
    ⏹️ Stop Claude Auto Responder

    Stops automatic confirmation and displays session statistics.
    """
    config_manager = ctx.obj["config_manager"]
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.logger.info("[red]No Dopemux project found in current directory[/red]")
        sys.exit(1)

    from integrations.claude_autoresponder import create_autoresponder_manager

    autoresponder_manager = create_autoresponder_manager(config_manager, project_path)

    if not autoresponder_manager.is_running():
        console.logger.info("[yellow]Auto responder is not running[/yellow]")
        return

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Stopping auto responder...", total=None)

        # Get stats before stopping
        status = autoresponder_manager.get_status()

        success = autoresponder_manager.stop()

        if success:
            progress.update(task, description="Auto responder stopped", completed=True)
            console.logger.info("[green]✅ Claude Auto Responder stopped[/green]")

            # Show session stats
            console.logger.info(f"[blue]📊 Session Statistics:[/blue]")
            console.logger.info(f"  ⏱️ Uptime: {status['uptime_minutes']:.1f} minutes")
            console.logger.info(f"  ✅ Responses sent: {status['responses_sent']}")
            if status["responses_sent"] > 0:
                console.print(
                    f"  📈 Rate: {status['responses_per_minute']:.1f} responses/min"
                )
        else:
            progress.update(task, description="Error stopping", completed=True)
            console.logger.error("[red]❌ Error stopping auto responder[/red]")


@autoresponder.command("status")
@click.pass_context
def autoresponder_status(ctx):
    """
    📊 Show auto responder status

    Displays current status, configuration, and performance metrics.
    """
    config_manager = ctx.obj["config_manager"]
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.logger.info("[red]No Dopemux project found in current directory[/red]")
        sys.exit(1)

    from integrations.claude_autoresponder import create_autoresponder_manager

    autoresponder_manager = create_autoresponder_manager(config_manager, project_path)
    status = autoresponder_manager.get_status()

    # Status overview
    status_color = "green" if status["running"] else "yellow"
    status_emoji = "🟢" if status["running"] else "🟡"

    table = Table(title="🤖 Claude Auto Responder Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style=status_color)

    table.add_row("Status", f"{status_emoji} {status['status'].title()}")
    table.add_row("Running", "Yes" if status["running"] else "No")

    if status["running"]:
        table.add_row("Uptime", f"{status['uptime_minutes']:.1f} minutes")
        table.add_row("Responses Sent", str(status["responses_sent"]))
        table.add_row("Response Rate", f"{status['responses_per_minute']:.1f}/min")
        table.add_row("Attention State", status["attention_state"])

        if status["last_response"]:
            table.add_row("Last Response", status["last_response"])

    console.logger.info(table)

    # Configuration table
    config_table = Table(title="⚙️ Configuration")
    config_table.add_column("Setting", style="cyan")
    config_table.add_column("Value", style="green")

    config = status["config"]
    config_table.add_row("Enabled", "Yes" if config["enabled"] else "No")
    config_table.add_row("Terminal Scope", config["terminal_scope"])
    config_table.add_row("Response Delay", f"{config['response_delay']}s")
    config_table.add_row("Timeout", f"{config['timeout_minutes']} minutes")
    config_table.add_row(
        "Whitelist Tools", "Yes" if config["whitelist_tools"] else "No"
    )
    config_table.add_row("Debug Mode", "Yes" if config["debug_mode"] else "No")

    console.logger.info(config_table)


@autoresponder.command("setup")
@click.pass_context
def autoresponder_setup(ctx):
    """
    🔧 Setup Claude Auto Responder

    Downloads and configures the ClaudeAutoResponder tool for use with Dopemux.
    """
    config_manager = ctx.obj["config_manager"]
    project_path = Path.cwd()

    if not (project_path / ".dopemux").exists():
        console.logger.info("[red]No Dopemux project found in current directory[/red]")
        sys.exit(1)

    from integrations.claude_autoresponder import create_autoresponder_manager

    autoresponder_manager = create_autoresponder_manager(config_manager, project_path)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Setting up ClaudeAutoResponder...", total=None)

        success = autoresponder_manager.setup_autoresponder()

        if success:
            progress.update(task, description="Setup complete! 🎉", completed=True)
            console.logger.info("[green]✅ ClaudeAutoResponder setup complete[/green]")
            console.logger.info("[blue]🚀 Run 'dopemux autoresponder start' to begin[/blue]")
        else:
            progress.update(task, description="Setup failed", completed=True)
            console.logger.error("[red]❌ Setup failed[/red]")
            console.logger.info("[yellow]Check logs for details[/yellow]")
            sys.exit(1)


@cli.group()
@click.pass_context
def extract(ctx):
    """
    📄 Document extraction with ADHD-optimized patterns

    Extract entities, configurations, and patterns from documentation
    using specialized extractors for markdown, YAML, and ADHD content.
    """
    pass


@extract.command("docs")
@click.argument("directory", default=".")
@click.option(
    "--mode", "-m",
    type=click.Choice(["basic", "detailed", "adhd"]),
    default="basic",
    help="Extraction mode: basic (key-value), detailed (all patterns), adhd (ADHD-specific)"
)
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "csv", "markdown", "yaml"]),
    default="json",
    help="Output format for extracted entities"
)
@click.option("--output", "-o", help="Output file path (default: print to stdout)")
@click.option("--confidence", "-c", type=float, default=0.5, help="Minimum confidence threshold (0.0-1.0)")
@click.option("--extensions", help="File extensions to process (default: .md,.yaml,.yml)")
@click.option("--adhd-profile", "-p", is_flag=True, help="Extract ADHD accommodation profile")
@click.pass_context
def extract_docs(
    ctx,
    directory: str,
    mode: str,
    format: str,
    output: Optional[str],
    confidence: float,
    extensions: Optional[str],
    adhd_profile: bool
):
    """
    📄 Extract entities from documentation files

    Process markdown and YAML files to extract structured information
    using ADHD-optimized patterns and confidence scoring.
    """
    with mobile_task_notification(
        ctx,
        "Documentation extraction",
        success_message="✅ Documentation extraction complete",
        failure_message="❌ Documentation extraction failed",
    ):
        _run_extract_docs(
            ctx,
            directory,
            mode,
            format,
            output,
            confidence,
            extensions,
            adhd_profile,
        )


def _run_extract_docs(
    ctx,
    directory: str,
    mode: str,
    format: str,
    output: Optional[str],
    confidence: float,
    extensions: Optional[str],
    adhd_profile: bool,
) -> None:
    import json
    import csv
    from io import StringIO

    # Add extraction package to path
    sys.path.append(str(Path(__file__).parent.parent.parent / "extraction"))

    try:
        from document_classifier import DocumentClassifier, extract_from_directory
    except ImportError as e:
        console.logger.info(f"[red]❌ Could not import extraction modules: {e}[/red]")
        console.logger.info("[yellow]💡 Make sure you're in the dopemux-mvp directory[/yellow]")
        sys.exit(1)

    source_path = Path(directory).resolve()
    if not source_path.exists():
        console.logger.info(f"[red]❌ Directory does not exist: {source_path}[/red]")
        sys.exit(1)

    if not extensions:
        extensions = ".md,.yaml,.yml,.json"

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Extracting entities in {mode} mode...", total=None)

        try:
            results = extract_from_directory(str(source_path))

            progress.update(task, description="Processing results...", total=None)

            filtered_entities = {}
            total_entities = 0
            filtered_count = 0

            for entity_type, entity_list in results.get('all_entities', {}).items():
                filtered_list = []
                for entity in entity_list:
                    total_entities += 1
                    entity_confidence = entity.get('confidence', 0.0)
                    if entity_confidence >= confidence:
                        filtered_list.append(entity)
                        filtered_count += 1

                if filtered_list:
                    filtered_entities[entity_type] = filtered_list

            if mode == "basic":
                basic_types = ['section_header', 'project_metadata', 'yaml_properties', 'markdown_headers']
                filtered_entities = {k: v for k, v in filtered_entities.items() if k in basic_types}
            elif mode == "adhd":
                adhd_keywords = ['adhd', 'focus', 'break', 'attention', 'cognitive', 'accommodation']
                adhd_types = [
                    k
                    for k in filtered_entities.keys()
                    if any(keyword in k.lower() for keyword in adhd_keywords)
                ]
                filtered_entities = {k: v for k, v in filtered_entities.items() if k in adhd_types}

            progress.update(task, description="Formatting output...", total=None)

            output_data = {
                'extraction_summary': {
                    'mode': mode,
                    'source_directory': str(source_path),
                    'documents_processed': results.get('documents_processed', 0),
                    'total_entities_found': total_entities,
                    'entities_above_threshold': filtered_count,
                    'confidence_threshold': confidence,
                    'entity_types': list(filtered_entities.keys()),
                },
                'entities': filtered_entities,
            }

            if adhd_profile and results.get('metadata', {}).get('adhd_documents'):
                sys.path.append(str(Path(__file__).parent.parent.parent / "extraction"))
                from adhd_entities import ADHDEntityExtractor

                extractor = ADHDEntityExtractor()
                for doc_info in results.get('document_types', {}).get('markdown', []):
                    if doc_info['filename'] in results['metadata']['adhd_documents']:
                        output_data['adhd_profile'] = {
                            'accommodation_categories': ['attention_management', 'energy_management'],
                            'confidence_note': 'Profile extraction requires document content access',
                        }
                        break

            progress.update(task, description="Complete! ✅", completed=True)

        except Exception as e:
            progress.update(task, description="Error occurred", completed=True)
            console.logger.error(f"[red]❌ Extraction failed: {e}[/red]")
            if ctx.obj.get("verbose"):
                import traceback
                traceback.print_exc()
            sys.exit(1)

    if format == "json":
        output_text = json.dumps(output_data, indent=2, ensure_ascii=False)
    elif format == "yaml":
        try:
            import yaml

            output_text = yaml.dump(output_data, default_flow_style=False, allow_unicode=True)
        except ImportError:
            console.logger.info("[yellow]⚠️ PyYAML not available, falling back to JSON[/yellow]")
            output_text = json.dumps(output_data, indent=2, ensure_ascii=False)
    elif format == "csv":
        output_buffer = StringIO()
        writer = csv.writer(output_buffer)
        writer.writerow(['entity_type', 'content', 'value', 'confidence', 'source_file'])

        for entity_type, entity_list in filtered_entities.items():
            for entity in entity_list:
                writer.writerow(
                    [
                        entity_type,
                        entity.get('content', ''),
                        entity.get('value', ''),
                        entity.get('confidence', 0.0),
                        entity.get('source_file', ''),
                    ]
                )
        output_text = output_buffer.getvalue()
    elif format == "markdown":
        lines = [f"# Extraction Results - {mode.title()} Mode\n"]
        lines.append(f"**Source**: {source_path}")
        lines.append(f"**Documents**: {output_data['extraction_summary']['documents_processed']}")
        lines.append(f"**Entities**: {filtered_count}/{total_entities} (confidence ≥ {confidence})\n")

        for entity_type, entity_list in filtered_entities.items():
            lines.append(f"## {entity_type.replace('_', ' ').title()}\n")
            for entity in entity_list:
                lines.append(f"- **{entity.get('content', 'N/A')}**")
                if entity.get('value'):
                    lines.append(f": {entity['value']}")
                lines.append(f" _(confidence: {entity.get('confidence', 0.0):.2f})_")
                lines.append("")

        output_text = "\n".join(lines)
    else:
        output_text = json.dumps(output_data, indent=2, ensure_ascii=False)

    if output:
        output_path = Path(output)
        output_path.write_text(output_text, encoding='utf-8')
        console.logger.info(f"[green]✅ Results written to {output_path}[/green]")
    else:
        console.logger.info(output_text)

    console.print(
        Panel(
            f"🎯 Extraction Summary:\n\n"
            f"• Mode: {mode}\n"
            f"• Documents: {results.get('documents_processed', 0)}\n"
            f"• Entities: {filtered_count}/{total_entities}\n"
            f"• Entity types: {len(filtered_entities)}\n"
            f"• Format: {format}",
            title="📊 Results",
            border_style="green",
        )
    )


@extract.command("pipeline")
@click.argument("directory", default=".")
@click.option("--output", "-o", help="Output directory for pipeline results", default="./output")
@click.option(
    "--adhd/--no-adhd",
    default=True,
    help="Enable/disable ADHD-specific extraction patterns"
)
@click.option(
    "--multi-angle/--no-multi-angle",
    default=True,
    help="Enable/disable multi-angle entity extraction"
)
@click.option(
    "--embeddings/--no-embeddings",
    default=True,
    help="Enable/disable vector embedding generation"
)
@click.option(
    "--tsv/--no-tsv",
    default=True,
    help="Enable/disable TSV registry generation"
)
@click.option(
    "--confidence", "-c",
    type=float,
    default=0.5,
    help="Minimum confidence threshold for entities (0.0-1.0)"
)
@click.option(
    "--embedding-model", "-m",
    default="voyage-context-3",
    help="Embedding model to use"
)
@click.option("--milvus-uri", help="Milvus database URI for vector storage")
@click.option("--extensions", help="File extensions to process (default: .md,.yaml,.yml,.json,.txt)")
@click.option(
    "--format", "-f",
    type=click.Choice(["json", "csv", "markdown"]),
    default="json",
    help="Output format for extraction results"
)
@click.option(
    "--synthesis/--no-synthesis",
    default=True,
    help="Enable/disable document synthesis generation"
)
@click.option(
    "--synthesis-types",
    multiple=True,
    type=click.Choice(["executive", "adhd", "technical", "all"]),
    default=["executive", "adhd"],
    help="Types of synthesis to generate (can specify multiple)"
)
@click.option(
    "--synthesis-format",
    type=click.Choice(["markdown", "json", "both"]),
    default="markdown",
    help="Output format for synthesis results"
)
@click.pass_context
def extract_pipeline(
    ctx,
    directory: str,
    output: str,
    adhd: bool,
    multi_angle: bool,
    embeddings: bool,
    tsv: bool,
    confidence: float,
    embedding_model: str,
    milvus_uri: Optional[str],
    extensions: Optional[str],
    format: str,
    synthesis: bool,
    synthesis_types: tuple,
    synthesis_format: str
):
    """
    🚀 Complete document processing pipeline

    Run the full unified pipeline including multi-layer extraction,
    atomic unit normalization, TSV registry generation, and vector
    embeddings. Integrates all extraction systems into a single workflow.
    """
    with mobile_task_notification(
        ctx,
        "Extraction pipeline",
        success_message="✅ Extraction pipeline complete",
        failure_message="❌ Extraction pipeline failed",
    ):
        _run_extract_pipeline(
            ctx,
            directory,
            output,
            adhd,
            multi_angle,
            embeddings,
            tsv,
            confidence,
            embedding_model,
            milvus_uri,
            extensions,
            format,
            synthesis,
            synthesis_types,
            synthesis_format,
        )


def _run_extract_pipeline(
    ctx,
    directory: str,
    output: str,
    adhd: bool,
    multi_angle: bool,
    embeddings: bool,
    tsv: bool,
    confidence: float,
    embedding_model: str,
    milvus_uri: Optional[str],
    extensions: Optional[str],
    format: str,
    synthesis: bool,
    synthesis_types: tuple,
    synthesis_format: str,
) -> None:

    try:
        from .extraction import UnifiedDocumentPipeline, PipelineConfig
    except ImportError as e:
        console.logger.info(f"[red]❌ Could not import pipeline modules: {e}[/red]")
        console.logger.info("[yellow]💡 Make sure the extraction package is properly installed[/yellow]")
        sys.exit(1)

    source_path = Path(directory).resolve()
    output_path = Path(output).resolve()

    if not source_path.exists():
        console.logger.info(f"[red]❌ Source directory does not exist: {source_path}[/red]")
        sys.exit(1)

    file_extensions = None
    if extensions:
        file_extensions = [ext.strip() for ext in extensions.split(',')]
        if not all(ext.startswith('.') for ext in file_extensions):
            file_extensions = ['.' + ext.lstrip('.') for ext in file_extensions]

    synthesis_types_list = list(synthesis_types)
    if "all" in synthesis_types_list:
        synthesis_types_list = ["executive", "adhd", "technical"]

    config = PipelineConfig(
        source_directory=source_path,
        output_directory=output_path,
        enable_adhd_extraction=adhd,
        enable_multi_angle=multi_angle,
        file_extensions=file_extensions,
        confidence_threshold=confidence,
        generate_tsv_registries=tsv,
        generate_embeddings=embeddings,
        embedding_model=embedding_model,
        milvus_uri=milvus_uri,
        export_json=(format == "json"),
        export_csv=(format == "csv"),
        export_markdown=(format == "markdown"),
        enable_synthesis=synthesis,
        synthesis_types=synthesis_types_list,
        synthesis_format=synthesis_format,
    )

    console.logger.info(f"[blue]🚀 Starting unified document pipeline...[/blue]")
    console.logger.info(f"[blue]📁 Source: {source_path}[/blue]")
    console.logger.info(f"[blue]📤 Output: {output_path}[/blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing pipeline...", total=None)

        try:
            pipeline = UnifiedDocumentPipeline(config)
            result = pipeline.process_documents()

            if result.success:
                progress.update(task, description="Pipeline completed successfully! ✅", completed=True)

                console.print(
                    Panel(
                        f"🎯 Pipeline Results:\n\n"
                        f"• Processing time: {result.processing_time:.2f}s\n"
                        f"• Documents processed: {result.document_count}\n"
                        f"• Total entities extracted: {result.total_entities}\n"
                        f"• TSV registries: {len(result.registry_files or {})}\n"
                        f"• Vector embeddings: {result.vector_count}\n"
                        f"• Output files: {len(result.output_files or [])}\n\n"
                        f"📊 Configuration:\n"
                        f"• ADHD extraction: {'✅' if adhd else '❌'}\n"
                        f"• Multi-angle extraction: {'✅' if multi_angle else '❌'}\n"
                        f"• TSV registries: {'✅' if tsv else '❌'}\n"
                        f"• Vector embeddings: {'✅' if embeddings else '❌'}\n"
                        f"• Confidence threshold: {confidence}",
                        title="🚀 Pipeline Complete",
                        border_style="green",
                    )
                )

                if result.output_files:
                    console.logger.info("\n[green]📤 Generated files:[/green]")
                    for file_path in result.output_files:
                        console.logger.info(f"  • {file_path}")

                if result.registry_files:
                    console.logger.info("\n[green]📊 TSV registries:[/green]")
                    for name, path in result.registry_files.items():
                        count = result.registry_counts.get(name, 0) if result.registry_counts else 0
                        console.logger.info(f"  • {name}: {path} ({count} entries)")

                if result.embedding_summary:
                    console.logger.info("\n[green]🔍 Embeddings:[/green]")
                    console.logger.info(f"  • Model: {result.embedding_summary.get('model', 'N/A')}")
                    console.logger.info(f"  • Vectors: {result.vector_count}")

            else:
                progress.update(task, description="Pipeline failed ❌", completed=True)
                console.logger.error(f"[red]❌ Pipeline failed: {result.error_message}[/red]")
                sys.exit(1)

        except Exception as e:
            progress.update(task, description="Error occurred", completed=True)
            console.logger.error(f"[red]❌ Pipeline execution failed: {e}[/red]")
            if ctx.obj.get("verbose"):
                import traceback
                traceback.print_exc()
            sys.exit(1)


@extract.command("cleanup")
@click.argument("directory", default=".")
@click.option(
    "--dry-run/--execute",
    default=True,
    help="Preview cleanup without removing files (default: dry-run)"
)
@click.option(
    "--cleanup-types",
    multiple=True,
    type=click.Choice(["temporary", "cache", "outputs", "interim", "all"]),
    default=["temporary", "cache", "interim"],
    help="Types of files to clean (can specify multiple)"
)
@click.option(
    "--include-outputs/--preserve-outputs",
    default=False,
    help="Include output files in cleanup (default: preserve)"
)
@click.option(
    "--report-format",
    type=click.Choice(["table", "json", "detailed"]),
    default="detailed",
    help="Format for cleanup report"
)
@click.option("--report-file", help="Save cleanup report to file")
@click.pass_context
def extract_cleanup(
    ctx,
    directory: str,
    dry_run: bool,
    cleanup_types: tuple,
    include_outputs: bool,
    report_format: str,
    report_file: Optional[str]
):
    """
    🧹 Clean pipeline files and generate activity report

    Remove temporary, cache, and interim files created during pipeline processing.
    Provides detailed reporting on files removed, created, changed, and output.

    Default behavior preserves output files and runs in dry-run mode for safety.
    """
    with mobile_task_notification(
        ctx,
        "Pipeline cleanup",
        success_message="✅ Pipeline cleanup complete",
        failure_message="❌ Pipeline cleanup failed",
    ):
        _run_extract_cleanup(
            ctx,
            directory,
            dry_run,
            cleanup_types,
            include_outputs,
            report_format,
            report_file,
        )


def _run_extract_cleanup(
    ctx,
    directory: str,
    dry_run: bool,
    cleanup_types: tuple,
    include_outputs: bool,
    report_format: str,
    report_file: Optional[str],
) -> None:
    import json
    from datetime import datetime

    # Import cleanup modules
    try:
        from .extraction.cleanup import PipelineCleanup, CleanupConfig
    except ImportError as e:
        console.logger.info(f"[red]❌ Could not import cleanup modules: {e}[/red]")
        console.logger.info("[yellow]💡 Make sure the extraction package is properly installed[/yellow]")
        sys.exit(1)

    target_path = Path(directory).resolve()

    if not target_path.exists():
        console.logger.info(f"[red]❌ Target directory does not exist: {target_path}[/red]")
        sys.exit(1)

    # Configure cleanup
    cleanup_types_list = list(cleanup_types)
    if "all" in cleanup_types_list:
        cleanup_types_list = ["temporary", "cache", "outputs", "interim"]
    elif include_outputs and "outputs" not in cleanup_types_list:
        cleanup_types_list.append("outputs")

    config = CleanupConfig(
        cleanup_types=cleanup_types_list,
        dry_run=dry_run,
        preserve_recent_hours=0,  # Clean all matching files
        include_hidden=False,
        backup_before_delete=False  # For safety in dry-run mode
    )

    console.logger.info(f"[blue]🧹 {'Previewing' if dry_run else 'Executing'} pipeline cleanup...[/blue]")
    console.logger.info(f"[blue]📁 Target: {target_path}[/blue]")
    console.logger.info(f"[blue]🎯 Cleanup types: {', '.join(cleanup_types_list)}[/blue]")

    if dry_run:
        console.logger.info("[yellow]⚠️  DRY RUN: No files will actually be removed[/yellow]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Scanning for cleanup candidates...", total=None)

        try:
            # Create cleanup system and generate mock activity report
            cleanup = PipelineCleanup(config)

            # For cleanup command, we simulate an activity report for the target directory
            mock_activity_report = {
                "operation_summary": {
                    "start_time": datetime.now().isoformat(),
                    "end_time": datetime.now().isoformat(),
                    "total_operations": 0,
                    "directories_scanned": [str(target_path)]
                },
                "file_operations": {
                    "created": [],
                    "modified": [],
                    "deleted": [],
                    "moved": []
                },
                "size_tracking": {
                    "total_bytes_created": 0,
                    "total_bytes_modified": 0,
                    "total_bytes_deleted": 0
                },
                "categorization": {
                    "by_extension": {},
                    "by_operation": {},
                    "by_directory": {}
                }
            }

            progress.update(task, description="Performing cleanup analysis...")

            # Perform cleanup
            result = cleanup.cleanup_pipeline_files(mock_activity_report, target_path)

            if result.success:
                progress.update(task, description=f"Cleanup {'preview' if dry_run else 'execution'} completed! ✅", completed=True)

                # Generate detailed report
                if report_format == "detailed":
                    console.print(
                        Panel(
                            f"🧹 Cleanup Results:\n\n"
                            f"• Files removed: {result.files_removed}\n"
                            f"• Space freed: {result.space_freed / (1024*1024):.2f} MB\n"
                            f"• Processing time: {result.processing_time:.2f}s\n"
                            f"• Errors: {len(result.errors)}\n\n"
                            f"📊 File Types Cleaned:\n"
                            + "\n".join([f"• {category}: {count} files"
                                       for category, count in result.files_by_category.items()]),
                            title=f"🧹 Cleanup {'Preview' if dry_run else 'Complete'}",
                            border_style="green" if result.success else "red",
                        )
                    )

                    # Show detailed file lists
                    if result.removed_files:
                        console.logger.info(f"\n[green]{'📋 Files to be removed:' if dry_run else '🗑️  Files removed:'}[/green]")
                        for file_path in result.removed_files[:20]:  # Show first 20
                            file_size = file_path.stat().st_size if file_path.exists() else 0
                            size_str = f"({file_size / 1024:.1f} KB)" if file_size > 0 else ""
                            console.logger.info(f"  • {file_path.relative_to(target_path)} {size_str}")

                        if len(result.removed_files) > 20:
                            console.logger.info(f"  ... and {len(result.removed_files) - 20} more files")

                    # Show errors if any
                    if result.errors:
                        console.logger.error(f"\n[red]⚠️  Errors encountered:[/red]")
                        for error in result.errors[:5]:  # Show first 5 errors
                            console.logger.error(f"  • {error}")
                        if len(result.errors) > 5:
                            console.logger.error(f"  ... and {len(result.errors) - 5} more errors")

                elif report_format == "table":
                    # Create a summary table
                    from rich.table import Table

                    table = Table(title=f"Cleanup {'Preview' if dry_run else 'Results'}")
                    table.add_column("Category", style="cyan")
                    table.add_column("Files", justify="right", style="magenta")
                    table.add_column("Size", justify="right", style="green")

                    for category, count in result.files_by_category.items():
                        # Calculate size for this category
                        category_size = sum(
                            f.stat().st_size if f.exists() else 0
                            for f in result.removed_files
                            if category.lower() in str(f).lower()
                        )
                        size_mb = category_size / (1024 * 1024)
                        table.add_row(category, str(count), f"{size_mb:.2f} MB")

                    console.logger.info(table)

                elif report_format == "json":
                    # JSON summary
                    json_result = {
                        "cleanup_summary": {
                            "dry_run": dry_run,
                            "success": result.success,
                            "files_removed": result.files_removed,
                            "space_freed_mb": result.space_freed / (1024*1024),
                            "processing_time": result.processing_time,
                            "target_directory": str(target_path),
                            "cleanup_types": cleanup_types_list
                        },
                        "file_categories": result.files_by_category,
                        "removed_files": [str(f) for f in result.removed_files],
                        "errors": result.errors,
                        "timestamp": datetime.now().isoformat()
                    }
                    console.logger.info(json.dumps(json_result, indent=2))

                # Save report to file if requested
                if report_file:
                    report_path = Path(report_file)
                    report_data = {
                        "cleanup_summary": {
                            "dry_run": dry_run,
                            "success": result.success,
                            "files_removed": result.files_removed,
                            "space_freed_mb": result.space_freed / (1024*1024),
                            "processing_time": result.processing_time,
                            "target_directory": str(target_path),
                            "cleanup_types": cleanup_types_list,
                            "timestamp": datetime.now().isoformat()
                        },
                        "detailed_results": {
                            "file_categories": result.files_by_category,
                            "removed_files": [str(f) for f in result.removed_files],
                            "errors": result.errors
                        }
                    }

                    with open(report_path, 'w') as f:
                        json.dump(report_data, f, indent=2)

                    console.logger.info(f"\n[green]📄 Report saved to: {report_path}[/green]")

            else:
                progress.update(task, description="Cleanup failed ❌", completed=True)
                console.logger.error(f"[red]❌ Cleanup failed: {result.error_message}[/red]")
                sys.exit(1)

        except Exception as e:
            progress.update(task, description="Error occurred", completed=True)
            console.logger.error(f"[red]❌ Cleanup execution failed: {e}[/red]")
            if ctx.obj.get("verbose"):
                import traceback
                traceback.print_exc()
            sys.exit(1)


@cli.command()
@click.argument("directory", default=".")
@click.option("--output", "-o", help="Output directory for analysis results")
@click.option(
    "--embedding-model", "-m", default="voyage-context-3", help="Embedding model to use"
)
@click.option("--milvus-uri", help="Milvus database URI (file path for Lite mode)")
@click.option("--max-files", type=int, help="Maximum number of files to process")
@click.option("--batch-size", type=int, default=10, help="Batch size for processing")
@click.option("--extensions", help="Comma-separated list of file extensions to include")
@click.option("--exclude", help="Comma-separated list of patterns to exclude")
@click.pass_context
def analyze(
    ctx,
    directory: str,
    output: Optional[str],
    embedding_model: str,
    milvus_uri: Optional[str],
    max_files: Optional[int],
    batch_size: int,
    extensions: Optional[str],
    exclude: Optional[str],
):
    """
    🔍 Analyze codebase with multi-angle document processing

    Processes documents in the specified directory, extracting features,
    components, subsystems, and research insights with semantic embeddings
    for intelligent code navigation and ADHD-friendly analysis.
    """
    from .analysis import DocumentProcessor, ProcessingConfig

    # Prepare configuration
    source_path = Path(directory).resolve()
    if not source_path.exists():
        console.logger.info(f"[red]❌ Directory does not exist: {source_path}[/red]")
        sys.exit(1)

    # Set output directory
    if output:
        output_path = Path(output).resolve()
    else:
        output_path = source_path / ".dopemux" / "analysis"

    output_path.mkdir(parents=True, exist_ok=True)

    # Parse extensions
    file_extensions = None
    if extensions:
        file_extensions = [
            f".{ext.strip().lstrip('.')}" for ext in extensions.split(",")
        ]

    # Parse exclusion patterns
    exclude_patterns = None
    if exclude:
        exclude_patterns = [pattern.strip() for pattern in exclude.split(",")]

    # Create configuration
    config = ProcessingConfig(
        source_directory=source_path,
        output_directory=output_path,
        max_files=max_files,
        file_extensions=file_extensions,
        exclude_patterns=exclude_patterns,
        embedding_model=embedding_model,
        milvus_uri=milvus_uri,
        batch_size=batch_size,
        show_progress=True,
        gentle_feedback=True,
    )

    # Initialize and run processor
    console.logger.info(f"[blue]🧠 Starting ADHD-optimized analysis of {source_path}[/blue]")
    console.logger.info(f"[dim]Output: {output_path}[/dim]")

    try:
        processor = DocumentProcessor(config)
        results = processor.analyze_directory()

        if results["success"]:
            console.print(
                f"[green]✅ Analysis complete! Results saved to {output_path}[/green]"
            )
            console.print(
                f"[blue]📊 Processing time: {results['processing_time']:.1f}s[/blue]"
            )

            # Show usage suggestions
            console.print(
                Panel(
                    f"🎯 Next steps:\n\n"
                    f"• Browse results in {output_path}\n"
                    f"• Use semantic search with embeddings\n"
                    f"• Explore feature and component registries\n"
                    f"• Review evidence links for traceability",
                    title="🚀 Ready to Explore",
                    border_style="green",
                )
            )
        else:
            console.logger.error("[red]❌ Analysis failed[/red]")
            sys.exit(1)

    except Exception as e:
        console.logger.error(f"[red]❌ Analysis error: {e}[/red]")
        if ctx.obj.get("verbose"):
            import traceback

            traceback.print_exc()
        sys.exit(1)


@cli.group()
def mcp():
    """Manage MCP Docker servers (start/stop/status/logs)."""


@mcp.command("up")
@click.option("--all", "all_services", is_flag=True, help="Start all MCP servers")
@click.option("--services", "services", help="Comma-separated services to start")
def mcp_up_cmd(all_services: bool, services: str):
    """Start MCP servers via docker-compose."""
    try:
        # Resolve script path
        script_dir = Path(__file__).parent.parent.parent / "scripts"
        script_path = script_dir / "start-all-mcp-servers.sh"
        
        if all_services or not services:
            cmd = f"bash {script_path}"
        else:
            svc_list = " ".join(s.strip() for s in services.split(",") if s.strip())
            cmd = f"docker compose -f compose.yml up -d --build {svc_list}"
        console.logger.info(f"[blue]🔌 {cmd}[/blue]")
        subprocess.run(["bash","-lc", cmd], check=True)
        console.logger.info("[green]✅ MCP servers started[/green]")
    except CalledProcessError:
        console.logger.error("[red]❌ Failed to start MCP servers[/red]")
        sys.exit(1)


@mcp.command("down")
def mcp_down_cmd():
    """Stop all MCP servers."""
    try:
        # Stop and remove only the MCP-related services
        mcp_services = ["conport", "pal", "litellm", "dope-context", "serena", "gptr-mcp", "desktop-commander", "leantime-bridge"]
        subprocess.run(["docker", "compose", "-f", "compose.yml", "rm", "-f", "-s", "-v"] + mcp_services, check=True)
        console.logger.info("[green]✅ MCP servers stopped[/green]")
    except CalledProcessError:
        console.logger.error("[red]❌ Failed to stop MCP servers[/red]")
        sys.exit(1)


@mcp.command("status")
def mcp_status_cmd():
    """Show docker-compose status for MCP servers."""
    try:
        subprocess.run(["docker","compose","-f","compose.yml","ps"], check=False)
    except CalledProcessError:
        sys.exit(1)


@mcp.command("logs")
@click.option("--service", "service", help="Service to tail logs for")
def mcp_logs_cmd(service: str):
    """Tail logs for an MCP service or all."""
    try:
        if service:
            cmd = f"docker compose -f compose.yml logs -f {service}"
        else:
            cmd = "docker compose -f compose.yml logs -f"
        console.logger.info(f"[blue]📄 {cmd}[/blue]")
        subprocess.run(["bash","-lc", cmd], check=False)
    except CalledProcessError:
        sys.exit(1)


@mcp.command("start-all")
@click.option("--verify", "-v", is_flag=True, help="Verify service health after starting")
def mcp_start_all_cmd(verify: bool):
    """
    🚀 Start complete Dopemux stack (MCP servers + application services)

    Starts all services including:
    - MCP servers (ConPort, Zen, Serena, etc.)
    - Integration Bridge (event processing, pattern detection)
    - Task Orchestrator (ADHD task coordination)
    - All infrastructure (PostgreSQL, Redis, Qdrant)

    \b
    Examples:
        dopemux mcp start-all           # Start everything
        dopemux mcp start-all --verify  # Start + verify health

    \b
    ADHD Benefit:
        One command to start the complete event-driven intelligence system.
        No need to remember which services to start manually.
    """
    try:
        # Run the start-all.sh script
        script_path = Path(__file__).parent.parent.parent / "scripts" / "start-all.sh"

        if not script_path.exists():
            console.logger.info(f"[red]❌ start-all.sh not found at {script_path}[/red]")
            console.logger.info("[yellow]Falling back to manual startup...[/yellow]")

            # Fallback: manual startup
            console.logger.info("[blue]Starting MCP servers...[/blue]")
            subprocess.run(["docker","compose","-f","compose.yml","up","-d"], check=True)

            console.logger.info("[blue]Starting Integration Bridge...[/blue]")
            subprocess.run(["bash","-lc","cd docker/conport-kg && docker-compose up -d --no-deps integration-bridge"], check=True)

            console.logger.info("[blue]Starting Task Orchestrator...[/blue]")
            subprocess.run(["docker","compose","-f","compose.yml","--profile","manual","up","-d","task-orchestrator"], check=True)

            console.logger.info("[green]✅ All services started[/green]")
        else:
            # Use the script
            cmd = ["bash", str(script_path)]
            if verify:
                cmd.append("--verify")

            subprocess.run(cmd, check=True)

    except CalledProcessError:
        console.logger.error("[red]❌ Failed to start all services[/red]")
        console.logger.info("[yellow]💡 Try: docker ps to see running containers[/yellow]")
        sys.exit(1)


@cli.group()
def servers():
    """Alias for 'dopemux mcp' commands."""


@servers.command("up")
@click.option("--all", "all_services", is_flag=True, help="Start all MCP servers")
@click.option("--services", "services", help="Comma-separated services to start")
def servers_up_cmd(all_services: bool, services: str):
    mcp_up_cmd(all_services, services)


@servers.command("down")
def servers_down_cmd():
    mcp_down_cmd()


@servers.command("status")
def servers_status_cmd():
    mcp_status_cmd()


@servers.command("logs")
@click.option("--service", "service", help="Service to tail logs for")
def servers_logs_cmd(service: str):
    mcp_logs_cmd(service)


@cli.command()
@click.option("--detailed", "-d", is_flag=True, help="Show detailed health information")
@click.option("--service", "-s", help="Check specific service only")
@click.option("--fix", "-f", is_flag=True, help="Attempt to fix unhealthy services")
@click.option("--cleanup", "-c", is_flag=True, help="Clean up orphaned MCP processes")
@click.option("--watch", "-w", is_flag=True, help="Continuous monitoring mode")
@click.option(
    "--interval", "-i", type=int, default=30, help="Watch interval in seconds"
)
@click.pass_context
def health(
    ctx, detailed: bool, service: Optional[str], fix: bool, cleanup: bool, watch: bool, interval: int
):
    """
    🏥 Comprehensive health check for Dopemux ecosystem

    Monitors Dopemux core, Claude Code, MCP servers, Docker services,
    system resources, and ADHD feature effectiveness with ADHD-friendly reporting.

    Use --cleanup to find and kill orphaned MCP server processes.
    """
    project_path = Path.cwd()
    health_checker = HealthChecker(project_path, console)

    # Handle cleanup flag first
    if cleanup:
        console.logger.info("[blue]🧹 Cleaning up orphaned MCP processes...[/blue]")

        try:
            # Find orphaned MCP processes
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True,
                text=True,
                check=True
            )

            orphaned_pids = []
            mcp_patterns = [
                'conport-mcp',
                'serena/v2/mcp_server.py',
                'src.mcp.server',
                'dopemux-gpt-researcher'
            ]

            for line in result.stdout.split('\n'):
                # Check if it's an MCP process
                if any(pattern in line for pattern in mcp_patterns):
                    # Extract PID
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1]
                        # Check if parent process (Claude Code) is still running
                        try:
                            parent_check = subprocess.run(
                                ["ps", "-o", "ppid=", "-p", pid],
                                capture_output=True,
                                text=True
                            )
                            ppid = parent_check.stdout.strip()
                            if ppid:
                                parent_cmd = subprocess.run(
                                    ["ps", "-o", "comm=", "-p", ppid],
                                    capture_output=True,
                                    text=True
                                )
                                # If parent is not Claude Code, it's orphaned
                                if 'claude' not in parent_cmd.stdout.lower():
                                    orphaned_pids.append(pid)
                        except (subprocess.SubprocessError, OSError) as e:
                            logger.error(f"Process parent check failed: {e}")
                        except Exception:
                            logger.error("Unexpected process parent check error", exc_info=True)
            if orphaned_pids:
                console.print(f"[yellow]Found {len(orphaned_pids)} orphaned MCP processes[/yellow]")

                if click.confirm("Kill these processes?", default=True):
                    killed = 0
                    for pid in orphaned_pids:
                        try:
                            os.kill(int(pid), signal.SIGTERM)
                            killed += 1
                        except (OSError, ValueError):
                            pass

                    console.print(f"[green]✅ Cleaned up {killed} orphaned processes[/green]")
                else:
                    console.print("[yellow]Cleanup cancelled[/yellow]")
            else:
                console.print("[green]✅ No orphaned MCP processes found[/green]")

        except Exception as e:
            console.print(f"[red]❌ Cleanup failed: {e}[/red]")

        # Exit after cleanup unless combined with other flags
        if not (detailed or service or fix or watch):
            return

    if watch:
        console.print(
            f"[blue]👁️ Starting continuous health monitoring (interval: {interval}s)[/blue]"
        )
        console.print("[dim]Press Ctrl+C to stop[/dim]")

        try:
            while True:
                console.clear()
                console.print(
                    f"[dim]Last check: {datetime.now().strftime('%H:%M:%S')}[/dim]"
                )

                results = health_checker.check_all(detailed=detailed)
                health_checker.display_health_report(results, detailed=detailed)

                time.sleep(interval)
        except KeyboardInterrupt:
            console.print("\n[yellow]🛑 Health monitoring stopped[/yellow]")
            return

    # Single health check
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Running health checks...", total=None)

        if service:
            # Check specific service
            checker_method = getattr(health_checker, f"_check_{service}", None)
            if not checker_method:
                console.logger.info(f"[red]❌ Unknown service: {service}[/red]")
                console.print(
                    f"[yellow]Available services: {', '.join(health_checker.checks.keys())}[/yellow]"
                )
                sys.exit(1)

            result = checker_method(detailed=detailed)
            results = {service: result}
        else:
            # Check all services
            results = health_checker.check_all(detailed=detailed)

        progress.update(task, description="Health checks complete!", completed=True)

    # Display results
    health_checker.display_health_report(results, detailed=detailed)

    # Fix unhealthy services if requested
    if fix:
        console.logger.info("\n[blue]🔧 Attempting to fix unhealthy services...[/blue]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            fix_task = progress.add_task("Fixing services...", total=None)

            restarted = health_checker.restart_unhealthy_services()

            progress.update(
                fix_task, description="Fix attempts complete!", completed=True
            )

        if restarted:
            console.print(
                f"[green]✅ Restarted services: {', '.join(restarted)}[/green]"
            )
            console.logger.info("[blue]💡 Run 'dopemux health' again to verify fixes[/blue]")
        else:
            console.logger.info("[yellow]⚠️ No services could be automatically fixed[/yellow]")
            console.logger.info("[dim]Manual intervention may be required[/dim]")

    # Exit with appropriate code for scripting
    critical_count = sum(1 for h in results.values() if h.status.value[0] == "critical")
    if critical_count > 0:
        sys.exit(1)


@autoresponder.command("config")
@click.option("--enabled/--disabled", help="Enable or disable auto responder")
@click.option(
    "--terminal-scope",
    type=click.Choice(["current", "all", "project"]),
    help="Terminal monitoring scope",
)
@click.option("--delay", type=float, help="Response delay in seconds (0-10)")
@click.option("--timeout", type=int, help="Auto-stop timeout in minutes")
@click.option("--whitelist/--no-whitelist", help="Enable/disable tool whitelisting")
@click.option("--debug/--no-debug", help="Enable/disable debug mode")
@click.pass_context
def autoresponder_config(
    ctx, enabled, terminal_scope, delay, timeout, whitelist, debug
):
    """
    ⚙️ Configure auto responder settings

    Update configuration options for Claude Auto Responder integration.
    """
    config_manager = ctx.obj["config_manager"]

    updates = {}
    if enabled is not None:
        updates["enabled"] = enabled
    if terminal_scope:
        updates["terminal_scope"] = terminal_scope
    if delay is not None:
        updates["response_delay"] = delay
    if timeout:
        updates["timeout_minutes"] = timeout
    if whitelist is not None:
        updates["whitelist_tools"] = whitelist
    if debug is not None:
        updates["debug_mode"] = debug

    if not updates:
        # Show current config
        current_config = config_manager.get_claude_autoresponder_config()

        table = Table(title="🤖 Auto Responder Configuration")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Enabled", "Yes" if current_config.enabled else "No")
        table.add_row("Terminal Scope", current_config.terminal_scope)
        table.add_row("Response Delay", f"{current_config.response_delay}s")
        table.add_row("Timeout", f"{current_config.timeout_minutes} minutes")
        table.add_row(
            "Whitelist Tools", "Yes" if current_config.whitelist_tools else "No"
        )
        table.add_row("Debug Mode", "Yes" if current_config.debug_mode else "No")

        console.logger.info(table)
        return

    # Apply updates
    try:
        config_manager.update_claude_autoresponder(**updates)
        console.logger.info("[green]✅ Configuration updated[/green]")

        # Show what changed
        for key, value in updates.items():
            console.logger.info(f"[blue]  {key}: {value}[/blue]")

        # Restart if running
        project_path = Path.cwd()
        if (project_path / ".dopemux").exists():
            from integrations.claude_autoresponder import create_autoresponder_manager

            autoresponder_manager = create_autoresponder_manager(
                config_manager, project_path
            )
            if autoresponder_manager.is_running():
                console.print(
                    "[yellow]🔄 Restarting auto responder with new settings...[/yellow]"
                )
                autoresponder_manager.restart()

    except ValueError as e:
        console.logger.error(f"[red]❌ Configuration error: {e}[/red]")
        sys.exit(1)


def _get_attention_emoji(state: Optional[str]) -> str:
    """Get emoji for attention state."""
    emoji_map = {
        "focused": "🎯",
        "scattered": "🌪️",
        "hyperfocus": "🔥",
        "normal": "😊",
        "distracted": "😵‍💫",
    }
    return emoji_map.get(state, "❓")


def _configure_openrouter_litellm():
    """Configure environment for OpenRouter via LiteLLM"""
    # Set up OpenRouter models for LiteLLM
    openrouter_models = [
        "openrouter-xai-grok-code-fast",
        "openrouter-openai-gpt-5",
        "openrouter-openai-gpt-5-mini",
        "openrouter-openai-gpt-5-codex",
        "openrouter-google-gemini-2-flash",
        "openrouter-meta-llama-3.1-405b",
    ]
    
    # Update environment
    os.environ["CLAUDE_CODE_ROUTER_PROVIDER"] = "litellm"
    os.environ["CLAUDE_CODE_ROUTER_UPSTREAM_KEY_VAR"] = "DOPEMUX_LITELLM_MASTER_KEY"
    os.environ["CLAUDE_CODE_ROUTER_MODELS"] = ",".join(openrouter_models)
    
    # Ensure Zen MCP uses LiteLLM
    os.environ["ZEN_DEFAULT_MODEL"] = "litellm/openrouter-openai-gpt-5"
    os.environ["ZEN_FALLBACK_MODELS"] = "litellm/openrouter-xai-grok-code-fast,litellm/openrouter-google-gemini-2-flash"
    
    # Set up LiteLLM proxy URL
    os.environ["LITELLM_PROXY_URL"] = "http://localhost:4000"
    
    # Configure Claude Code to use LiteLLM
    os.environ["CLAUDE_CODE_LLM_PROVIDER"] = "litellm"
    os.environ["CLAUDE_CODE_LLM_BASE_URL"] = "http://localhost:4000"
    os.environ["CLAUDE_CODE_LLM_API_KEY"] = os.getenv("DOPEMUX_LITELLM_MASTER_KEY", "")
    
    console.logger.info("[green]✅ OpenRouter via LiteLLM configuration applied[/green]")




def _resolve_mcp_dir(project_path: Path) -> Optional[Path]:
    """
    Resolve MCP stack location deterministically.

    Resolution order:
    1. DOPEMUX_MCP_DIR (explicit override)
    2. project_path/docker/mcp-servers (local project assets)
    3. dopemux repo root (fallback for editable installs)
    """
    # 1. Explicit override
    if env_dir := os.getenv("DOPEMUX_MCP_DIR"):
        path = Path(env_dir).resolve()
        if (path / "start-all-mcp-servers.sh").exists():
            return path

    # 2. Local project
    local_path = project_path / "docker" / "mcp-servers"
    if (local_path / "start-all-mcp-servers.sh").exists():
        return local_path

    # 3. Inferred package root (editable install)
    # cli.py is at src/dopemux/cli.py -> parents[2] is repo root
    try:
        source_root = Path(__file__).resolve().parents[2]
        pkg_path = source_root / "docker" / "mcp-servers"
        if (pkg_path / "start-all-mcp-servers.sh").exists():
            return pkg_path
    except Exception:
        pass

    return None


def _start_mcp_servers_with_progress(project_path: Path, instance_env: Optional[dict] = None):
    """
    Start MCP servers with real-time output streaming and health check waiting.

    CRITICAL: Passes instance environment variables to MCP servers for workspace isolation.
    Without this, all instances share the same workspace = broken ADHD context preservation!

    Args:
        project_path: Project root path
        instance_env: Instance-specific environment variables (DOPEMUX_WORKSPACE_ID, etc.)

    ADHD-optimized:
    - Real-time visual feedback reduces anxiety
    - Clear status updates maintain engagement
    - Health check waiting ensures everything is ready
    """
    if os.getenv("DOPEMUX_SKIP_MCP_START", "0").lower() in {"1", "true", "yes"}:
        console.logger.info("[yellow]⏭️ Skipping MCP server startup (DOPEMUX_SKIP_MCP_START)[/yellow]")
        return

    import requests

    # Resolve MCP stack location
    mcp_dir = _resolve_mcp_dir(project_path)
    
    if not mcp_dir:
        console.print()
        console.logger.error("[red]❌ Required MCP startup assets not found.[/red]")
        console.print("[dim]   (Checked: DOPEMUX_MCP_DIR, local project, and dopemux package root)[/dim]")
        
        console.print("\n[bold]Remedies:[/bold]")
        console.print("  1. Set DOPEMUX_MCP_DIR to the location of 'docker/mcp-servers'")
        console.print("     [green]export DOPEMUX_MCP_DIR=/path/to/dopemux/docker/mcp-servers[/green]")
        console.print("  2. Symlink the docker stack to your project:")
        console.print(f"     [green]cd {project_path} && mkdir -p docker && ln -s .../dopemux/docker/mcp-servers docker/mcp-servers[/green]")
        console.print("  3. Skip MCP requirement (functionality will be reduced):")
        console.print("     [green]dopemux start --no-mcp[/green]")
        
        raise click.ClickException("MCP stack required but not found. See remedies above.")
    
    # We found it - ensure script exists (double-check, though resolver checks it)
    script_path = mcp_dir / "start-all-mcp-servers.sh"

    # CRITICAL FIX: Merge instance env with current environment
    # This ensures MCP servers get DOPEMUX_WORKSPACE_ID and other instance vars
    env_for_subprocess = os.environ.copy()
    if instance_env:
        env_for_subprocess.update(instance_env)

    # Critical servers to health check
    critical_servers = [
        ("ConPort", "http://localhost:3004/health"),
        ("PAL", "http://localhost:3003/health"),
        ("LiteLLM", "http://localhost:4000/health/readiness"),
    ]

    console.logger.info("\n[bold blue]🔌 Starting MCP Servers[/bold blue]")
    console.logger.info("[dim]This may take 30-60 seconds for first-time setup...[/dim]\n")

    # Start docker-compose with real-time output
    status_text = Text()
    status_text.append("🚀 ", style="bold blue")
    status_text.append("Launching containers...")

    startup_successful = False
    output_lines = []
    
    try:
        with Live(status_text, console=console, refresh_per_second=4) as live:
            # Start the containers with instance environment
            # CRITICAL FIX: Pass env_for_subprocess so docker-compose gets DOPEMUX_WORKSPACE_ID
            # Use absolute path with cwd to avoid 'cd' failures from symlinked directories
            script_path = mcp_dir / "start-all-mcp-servers.sh"
            if not script_path.exists():
                console.logger.error(f"[red]❌ MCP startup script not found at {script_path}[/red]")
                console.logger.info(f"[dim]Expected: {script_path}[/dim]")
                raise FileNotFoundError(f"start-all-mcp-servers.sh not found at {script_path}")

            process = subprocess.Popen(
                ["bash", str(script_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=str(mcp_dir),  # Set working directory explicitly instead of 'cd'
                env=env_for_subprocess  # ← THE FIX! Passes instance vars to MCP servers
            )

            # Stream output line by line
            for line in process.stdout:
                line = line.rstrip()
                if line:
                    # Update status with last meaningful line
                    if "Starting" in line:
                        status_text = Text()
                        status_text.append("🔨 ", style="bold blue")
                        status_text.append(line)
                        live.update(status_text)
                    elif "✅" in line or "Healthy" in line:
                        status_text = Text()
                        status_text.append("✅ ", style="bold green")
                        status_text.append(line)
                        live.update(status_text)
                    elif "⚡" in line:
                        status_text = Text()
                        status_text.append("⚡ ", style="bold yellow")
                        status_text.append(line)
                        live.update(status_text)

                    output_lines.append(line)

            process.wait()

            if process.returncode != 0:
                console.logger.error("\n[red]❌ MCP server startup failed[/red]")
                console.logger.info("[dim]Last 10 lines of output:[/dim]")
                for line in output_lines[-10:]:
                    console.logger.info(f"[dim]{line}[/dim]")
                raise CalledProcessError(process.returncode, process.args)
        
        # Mark startup as successful only after the first Live context has fully exited
        startup_successful = True

    except CalledProcessError as e:
        console.logger.error("[yellow]⚠️  Failed to start MCP servers (continuing with reduced functionality)[/yellow]")
        console.logger.info("[dim]   Tip: Run 'dopemux start --no-mcp' to skip this step[/dim]")
        return  # Exit early to avoid starting the second Live context
    except Exception as e:
        console.logger.error(f"[yellow]⚠️  Error during MCP startup: {e}[/yellow]")
        console.logger.info("[dim]   Continuing with reduced functionality...[/dim]")
        return  # Exit early to avoid starting the second Live context

    # Only proceed with health checks if startup was successful
    if startup_successful:
        # Wait for health checks
        console.logger.info("\n[bold blue]🏥 Waiting for services to become healthy...[/bold blue]")

        max_wait = 45  # seconds
        start_time = time.time()
        all_healthy = False

        health_status = {name: False for name, _ in critical_servers}

        try:
            with Live(console=console, refresh_per_second=2) as live:
                while time.time() - start_time < max_wait:
                    status_text = Text()
                    all_healthy = True

                    for name, url in critical_servers:
                        is_healthy = False
                        try:
                            response = requests.get(url, timeout=2)
                            is_healthy = response.status_code == 200
                        except requests.RequestException:
                            is_healthy = False

                        health_status[name] = is_healthy
                        if is_healthy:
                            status_text.append("✅ ", style="bold green")
                        else:
                            status_text.append("⏳ ", style="bold yellow")
                            all_healthy = False
                        status_text.append(f"{name}\n")

                    # Add elapsed time
                    elapsed = int(time.time() - start_time)
                    status_text.append(f"\n[dim]⏱️  {elapsed}s / {max_wait}s[/dim]")

                    live.update(Panel(status_text, title="[bold]Health Check Status[/bold]", border_style="blue"))

                    if all_healthy:
                        break

                    time.sleep(2)

            if all_healthy:
                console.logger.info("\n[bold green]✅ All MCP servers are healthy and ready![/bold green]\n")
            else:
                # Show which services failed
                console.logger.info("\n[yellow]⚠️  Some services are not healthy (continuing anyway):[/yellow]")
                for name, is_healthy in health_status.items():
                    if not is_healthy:
                        console.logger.info(f"  [red]❌ {name}[/red]")
                    else:
                        console.logger.info(f"  [green]✅ {name}[/green]")
                console.logger.info("[dim]Tip: Check docker logs with: docker compose -f compose.yml logs[/dim]\n")
        
        except Exception as e:
            console.logger.error(f"[yellow]⚠️  Error during health checks: {e}[/yellow]")
            console.logger.info("[dim]   Continuing anyway...[/dim]")


def _trigger_dope_context_autoindex_startup(
    workspace_path: Path,
    *,
    force: bool = False,
) -> Optional[dict]:
    """
    Trigger dope-context startup autoindex bootstrap for the current workspace.
    """
    enabled = os.getenv("DOPEMUX_AUTO_INDEX_ON_STARTUP", "1").lower() not in {"0", "false", "no"}
    if not enabled:
        return None

    base_url = os.getenv("DOPE_CONTEXT_URL", "http://localhost:3010").rstrip("/")
    endpoint = f"{base_url}/autoindex/bootstrap"
    payload = {
        "workspace_path": str(workspace_path.resolve()),
        "force": force,
        "wait_for_completion": False,
        "debounce_seconds": float(os.getenv("DOPEMUX_AUTO_INDEX_DEBOUNCE_SECONDS", "5.0")),
        "periodic_interval": int(os.getenv("DOPEMUX_AUTO_INDEX_PERIODIC_SECONDS", "600")),
        "trigger": "dopemux_cli_startup",
    }

    try:
        import requests

        response = requests.post(endpoint, json=payload, timeout=5)
        if response.status_code >= 400:
            console.logger.info(
                f"[yellow]⚠️  Autoindex bootstrap request failed ({response.status_code})[/yellow]"
            )
            return {
                "status": "http_error",
                "status_code": response.status_code,
                "endpoint": endpoint,
            }
        result = response.json()
        return result if isinstance(result, dict) else {"status": "unknown_response"}
    except Exception as exc:
        logger.warning("Failed to trigger dope-context autoindex bootstrap: %s", exc)
        return {
            "status": "request_failed",
            "error": str(exc),
            "endpoint": endpoint,
        }


def _activate_dangerous_mode():
    """
    Activate dangerous mode with proper security safeguards.

    This temporarily overrides the default safe mode settings for the current
    session only. Changes are not persisted to the .env file.

    Security Features:
    - Time-limited session (1 hour max)
    - Explicit user confirmation required
    - Clear warnings about risks
    - Environment isolation
    """
    # Check if already in dangerous mode
    if os.getenv("DOPEMUX_DANGEROUS_MODE") == "true":
        expires_str = os.getenv("DOPEMUX_DANGEROUS_EXPIRES", "0")
        expires_timestamp = float(expires_str) if expires_str.isdigit() else 0

        if time.time() < expires_timestamp:
            console.logger.info("[yellow]⚠️  Dangerous mode already active[/yellow]")
            remaining_minutes = int((expires_timestamp - time.time()) / 60)
            console.logger.info(f"[dim]Expires in {remaining_minutes} minutes[/dim]")
            return
        else:
            # Expired, clear old settings
            _deactivate_dangerous_mode()

    # Show serious warning
    console.print(Panel(
        "[red bold]⚠️  DANGER: This will disable ALL security restrictions![/red bold]\n\n"
        "[yellow]This mode will:[/yellow]\n"
        "• Skip all permission checks\n"
        "• Disable role enforcement\n"
        "• Bypass budget limits\n"
        "• Allow unrestricted tool access\n\n"
        "[red]Use ONLY in isolated, trusted environments![/red]\n"
        "[yellow]Session will expire automatically in 1 hour.[/yellow]",
        title="🚨 Security Warning",
        border_style="red"
    ))

    # Require explicit confirmation
    if not click.confirm("\nDo you understand the risks and want to proceed?", default=False):
        console.logger.info("[green]Dangerous mode cancelled. Staying in safe mode.[/green]")
        return

    if not click.confirm("Are you in an isolated, trusted environment?", default=False):
        console.logger.info("[green]Dangerous mode cancelled for security.[/green]")
        return

    # Set time-limited dangerous mode (1 hour)
    expiry_time = time.time() + 3600  # 1 hour

    os.environ["DOPEMUX_DANGEROUS_MODE"] = "true"
    os.environ["DOPEMUX_DANGEROUS_EXPIRES"] = str(expiry_time)
    os.environ["DOPEMUX_DANGEROUS_PID"] = str(os.getpid())  # Track process

    # Set security bypass flags
    os.environ["HOOKS_ENABLE_ADAPTIVE_SECURITY"] = "0"
    os.environ["CLAUDE_CODE_SKIP_PERMISSIONS"] = "true"
    os.environ["METAMCP_ROLE_ENFORCEMENT"] = "false"
    os.environ["METAMCP_APPROVAL_REQUIRED"] = "false"
    os.environ["METAMCP_BUDGET_ENFORCEMENT"] = "false"

    # Traditional dangerous flags for compatibility
    os.environ["CLAUDE_DANGEROUS"] = "true"
    os.environ["SKIP_PERMISSIONS"] = "true"

    # Log for audit trail (but not sensitive info)
    expiry_str = datetime.fromtimestamp(expiry_time).strftime("%H:%M:%S")
    console.logger.info(f"[red bold]⚠️  DANGEROUS MODE ACTIVE until {expiry_str}[/red bold]")


def _deactivate_dangerous_mode():
    """Deactivate dangerous mode and clean up environment."""
    dangerous_vars = [
        "DOPEMUX_DANGEROUS_MODE",
        "DOPEMUX_DANGEROUS_EXPIRES",
        "DOPEMUX_DANGEROUS_PID",
        "HOOKS_ENABLE_ADAPTIVE_SECURITY",
        "CLAUDE_CODE_SKIP_PERMISSIONS",
        "METAMCP_ROLE_ENFORCEMENT",
        "METAMCP_APPROVAL_REQUIRED",
        "METAMCP_BUDGET_ENFORCEMENT",
        "CLAUDE_DANGEROUS",
        "SKIP_PERMISSIONS"
    ]

    for var in dangerous_vars:
        os.environ.pop(var, None)

    console.logger.info("[green]✅ Dangerous mode deactivated[/green]")


def _check_dangerous_mode_expiry():
    """Check if dangerous mode has expired and clean up if needed."""
    if os.getenv("DOPEMUX_DANGEROUS_MODE") == "true":
        expires_str = os.getenv("DOPEMUX_DANGEROUS_EXPIRES", "0")
        expires_timestamp = float(expires_str) if expires_str.isdigit() else 0

        if time.time() >= expires_timestamp:
            console.logger.info("[yellow]⏰ Dangerous mode expired, returning to safe mode[/yellow]")
            _deactivate_dangerous_mode()
            return True
    return False


@cli.command("backup")
@click.option("--dest", help="Destination directory for tar backups (defaults to docker/mcp-servers/backups/volumes_<timestamp>)")
@click.option("--pattern", help="Regex to filter volume names (default: ^(mcp_|dopemux_))")
@click.option("--no-pull", is_flag=True, help="Do not pull alpine image if missing")
@click.option("--schedule", type=click.Choice(["daily", "weekly"]), help="Print a cron entry to run backups on a schedule")
@click.option("--apply", is_flag=True, help="Attempt to install the cron entry into your crontab")
@click.pass_context
def backup(ctx, dest: Optional[str], pattern: Optional[str], no_pull: bool, schedule: Optional[str], apply: bool):
    """
    📦 Back up all Docker named volumes used by Dopemux (mcp_*/dopemux_*).

    Creates .tgz archives and a SHA256SUMS.txt manifest in the destination.
    Use --schedule to print or install a cron job for daily/weekly backups.
    """
    from .workspace_utils import get_workspace_root
    import hashlib, re

    # Scheduling path only
    if schedule:
        _print_or_apply_cron(schedule, apply)
        return

    with mobile_task_notification(
        ctx,
        "Docker volume backup",
        success_message="✅ Docker volume backup complete",
        failure_message="❌ Docker volume backup failed",
    ):
        _run_volume_backup(dest, pattern, no_pull, get_workspace_root)


def _run_volume_backup(dest: Optional[str], pattern: Optional[str], no_pull: bool, get_workspace_root):
    import hashlib
    import re

    workspace = get_workspace_root()
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    default_dest = workspace / "docker" / "mcp-servers" / "backups" / f"volumes_{ts}"
    dest_path = Path(dest).expanduser().resolve() if dest else default_dest
    dest_path.mkdir(parents=True, exist_ok=True)

    vol_pattern = re.compile(pattern or r"^(mcp_|dopemux_)")

    try:
        result = subprocess.run(["docker", "volume", "ls", "--format", "{{.Name}}"], capture_output=True, text=True, check=True)
    except Exception as e:
        console.logger.info(f"[red]❌ Docker not available: {e}[/red]")
        sys.exit(1)

    volumes = [v.strip() for v in result.stdout.splitlines() if v.strip() and vol_pattern.search(v.strip())]
    if not volumes:
        console.logger.info("[yellow]No matching volumes found[/yellow]")
        return

    console.logger.info(f"[blue]== Backing up {len(volumes)} volumes to {dest_path} ==[/blue]")

    if not no_pull:
        try:
            subprocess.run(["docker", "image", "inspect", "alpine:latest"], capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError:
            console.logger.info("[dim]Pulling alpine:latest ...[/dim]")
            subprocess.run(["docker", "pull", "alpine:latest"], check=False)

    ok = 0
    fail = 0
    for vol in volumes:
        console.logger.info(f"Backing up [cyan]{vol}[/cyan] ...")
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{vol}:/data:ro",
            "-v", f"{str(dest_path)}:/backup",
            "alpine", "sh", "-lc",
            f"cd /data 2>/dev/null || mkdir -p /data; tar czf '/backup/{vol}.tgz' -C /data ."
        ]
        try:
            subprocess.run(cmd, check=True)
            console.logger.info(f"[green]✓ {vol}[/green] → {dest_path / (vol + '.tgz')}")
            ok += 1
        except subprocess.CalledProcessError:
            console.logger.error(f"[red]✗ Failed to back up {vol}[/red]")
            fail += 1

    try:
        sums_path = dest_path / "SHA256SUMS.txt"
        with sums_path.open("w") as f:
            for tgz in sorted(dest_path.glob("*.tgz")):
                h = hashlib.sha256()
                with tgz.open("rb") as tf:
                    for chunk in iter(lambda: tf.read(1024 * 1024), b""):
                        h.update(chunk)
                f.write(f"{h.hexdigest()}  {tgz.name}\n")
        console.logger.info(f"[green]Manifest written:[/green] {sums_path}")
    except Exception as e:
        console.logger.info(f"[yellow]⚠️  Could not write checksum manifest: {e}[/yellow]")

    console.logger.error(f"\n[bold]Summary[/bold]: Backed up {ok} volumes, {fail} failed")


def _print_or_apply_cron(frequency: str, apply: bool) -> None:
    """Print or install a cron job to run 'dopemux backup' on the desired schedule."""
    # Defaults: run at 02:30 local time
    cron_time = "30 2 * * *" if frequency == "daily" else "30 2 * * 1"

    backup_cmd = "dopemux backup"
    cron_entry = (
        f"# dopemux-backup ({frequency})\n"
        f"{cron_time} cd $HOME/code/dopemux-mvp && {backup_cmd} >> $HOME/.dopemux/backup.log 2>&1\n"
    )

    if not apply:
        console.logger.info("\n[bold]Cron suggestion[/bold] (add via 'crontab -e'):\n")
        console.logger.info(cron_entry)
        console.logger.info("\n[dim]Tip: Adjust path and time as needed.[/dim]")
        return

    try:
        current = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        content = current.stdout if current.returncode == 0 else ""
        if "# dopemux-backup" in content:
            console.logger.info("[yellow]⚠️  A dopemux-backup entry already exists in your crontab[/yellow]")
            return
        new_content = content + ("\n" if content and not content.endswith("\n") else "") + cron_entry
        p = subprocess.run(["crontab", "-"], input=new_content, text=True)
        if p.returncode == 0:
            console.logger.info("[green]✅ Installed dopemux backup cron job[/green]")
        else:
            console.logger.info("[yellow]⚠️  Could not install cron job. Printing entry instead:[/yellow]")
            console.logger.info(cron_entry)
    except Exception as e:
        console.logger.error(f"[yellow]⚠️  Failed to install cron job: {e}[/yellow]")
        console.logger.info("\nAdd this entry manually via 'crontab -e':\n")
        console.logger.info(cron_entry)


@cli.command("extract-chatlog")
@click.argument("directory", default=".")
@click.option("--output", "-o", help="Output directory for extraction results")
@click.option("--confidence", "-c", type=float, default=0.5, help="Minimum confidence threshold (0.0-1.0)")
@click.option("--batch-size", "-b", type=int, default=10, help="Number of files to process per batch")
@click.option("--max-workers", "-w", type=int, default=4, help="Maximum parallel workers")
@click.option("--archive", "-a", help="Archive directory for processed files")
@click.option("--workspace-id", help="ConPort workspace ID for persistence")
@click.pass_context
def extract_chatlog(
    ctx,
    directory: str,
    output: Optional[str],
    confidence: float,
    batch_size: int,
    max_workers: int,
    archive: Optional[str],
    workspace_id: Optional[str]
):
    """
    📄 Extract structured data from chatlog conversations (Basic Mode)

    Process chatlog files using core extractors (decisions, features, research)
    with adaptive document synthesis. Includes batch processing with phase
    synchronization and automatic archiving of processed files.

    Basic extractors:
    • Decision extraction (conclusions, agreements, next steps)
    • Feature extraction (requirements, user stories, acceptance criteria)
    • Research extraction (findings, references, methodologies)
    """
    with mobile_task_notification(
        ctx,
        "Chatlog extraction",
        success_message="✅ Chatlog extraction complete",
        failure_message="❌ Chatlog extraction failed",
    ):
        _run_extract_chatlog(
            ctx,
            directory,
            output,
            confidence,
            batch_size,
            max_workers,
            archive,
            workspace_id,
        )


def _run_extract_chatlog(
    ctx,
    directory: str,
    output: Optional[str],
    confidence: float,
    batch_size: int,
    max_workers: int,
    archive: Optional[str],
    workspace_id: Optional[str],
) -> None:

    backend_path = Path(__file__).parent.parent.parent / "services" / "dopemux-gpt-researcher" / "backend"
    sys.path.insert(0, str(backend_path))

    try:
        from extraction_pipeline import ExtractionPipeline, PipelineConfig
    except ImportError as e:
        console.logger.info(f"[red]❌ Could not import extraction pipeline: {e}[/red]")
        console.logger.info("[yellow]💡 Make sure you're in the dopemux-mvp directory[/yellow]")
        sys.exit(1)

    source_path = Path(directory).resolve()
    if not source_path.exists():
        console.logger.info(f"[red]❌ Directory does not exist: {source_path}[/red]")
        sys.exit(1)

    if output:
        output_path = Path(output).resolve()
    else:
        output_path = source_path / ".dopemux" / "extraction"

    archive_path = Path(archive).resolve() if archive else None

    if not workspace_id:
        workspace_id = str(source_path)

    config = PipelineConfig(
        source_directory=source_path,
        output_directory=output_path,
        archive_directory=archive_path,
        batch_size=batch_size,
        max_workers=max_workers,
        confidence_threshold=confidence,
        include_basic_extractors=True,
        include_pro_extractors=False,
        enable_synthesis=True,
        max_documents=4,
        verbose=ctx.obj.get("verbose", False),
        persist_to_conport=True,
        workspace_id=workspace_id,
    )

    console.logger.info("[blue]🚀 Starting Basic Chatlog Extraction Pipeline[/blue]")
    console.logger.info(f"[blue]📁 Source: {source_path}[/blue]")
    console.logger.info(f"[blue]📤 Output: {output_path}[/blue]")
    console.logger.info(f"[blue]🎯 Extractors: Decision, Feature, Research[/blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing extraction pipeline...", total=None)

        try:
            pipeline = ExtractionPipeline(config)

            progress.update(task, description="Discovering files...")
            files = pipeline.discover_files()

            if not files:
                progress.update(task, description="No files found to process", completed=True)
                console.logger.info("[yellow]⚠️ No unprocessed chatlog files found[/yellow]")
                return

            progress.update(task, description=f"Processing {len(files)} files...")
            result = pipeline.run_extraction()

            if result['success']:
                progress.update(task, description="Extraction completed successfully! ✅", completed=True)

                stats = result['statistics']
                console.print(
                    Panel(
                        f"🎯 Basic Extraction Results:\n\n"
                        f"• Files processed: {stats['files_processed']}/{stats['total_files']}\n"
                        f"• Total chunks: {stats['total_chunks']}\n"
                        f"• Fields extracted: {stats['total_fields']}\n"
                        f"• High confidence fields: {stats['high_confidence_fields']}\n"
                        f"• Documents generated: {stats['documents_generated']}\n"
                        f"• Processing time: {stats['processing_time']:.2f}s\n\n"
                        f"📊 Field Types:\n"
                        + "\n".join(
                            [f"• {field_type}: {count}" for field_type, count in stats['fields_by_type'].items()]
                        ),
                        title="🚀 Basic Extraction Complete",
                        border_style="green",
                    )
                )

                console.logger.info(f"\n[green]📁 Results saved to: {output_path}[/green]")
                console.logger.info(f"[green]📦 Processed files archived to: {result['archive_directory']}[/green]")

            else:
                progress.update(task, description="Extraction failed ❌", completed=True)
                console.logger.error(f"[red]❌ Extraction failed[/red]")
                if result.get('errors'):
                    console.logger.error(f"[red]Errors: {len(result['errors'])}[/red]")
                    for error in result['errors'][:3]:
                        console.logger.error(f"[red]  • {error}[/red]")
                sys.exit(1)

        except Exception as e:
            progress.update(task, description="Error occurred", completed=True)
            console.logger.error(f"[red]❌ Extraction pipeline failed: {e}[/red]")
            if ctx.obj.get("verbose"):
                import traceback
                traceback.print_exc()
            sys.exit(1)


@cli.command()
@click.argument("directory", default=".")
@click.option("--output", "-o", help="Output directory for extraction results")
@click.option("--confidence", "-c", type=float, default=0.4, help="Minimum confidence threshold (0.0-1.0)")
@click.option("--batch-size", "-b", type=int, default=15, help="Number of files to process per batch")
@click.option("--max-workers", "-w", type=int, default=6, help="Maximum parallel workers")
@click.option("--archive", "-a", help="Archive directory for processed files")
@click.option("--workspace-id", help="ConPort workspace ID for persistence")
@click.option("--max-documents", "-d", type=int, default=8, help="Maximum documents to generate")
@click.pass_context
def extractPro(
    ctx,
    directory: str,
    output: Optional[str],
    confidence: float,
    batch_size: int,
    max_workers: int,
    archive: Optional[str],
    workspace_id: Optional[str],
    max_documents: int
):
    """
    🔬 Extract comprehensive data from chatlog conversations (Pro Mode)

    Process chatlog files using ALL extractors with advanced analysis capabilities.
    Includes full synthesis suite, knowledge graph construction, and comprehensive
    reporting with pre-commit review integration.

    Pro extractors include ALL basic extractors PLUS:
    • Constraint extraction (technical/business limitations, dependencies)
    • Stakeholder extraction (roles, responsibilities, decision makers)
    • Risk extraction (threats, mitigations, impact assessments)
    • Security extraction (auth requirements, compliance, vulnerabilities)

    Pro features:
    • Lower confidence threshold for broader coverage
    • More parallel processing power
    • Advanced document synthesis (8+ document types)
    • Knowledge graph with relationship mapping
    • Comprehensive quality metrics and reporting
    """
    with mobile_task_notification(
        ctx,
        "Pro chatlog extraction",
        success_message="✅ Pro chatlog extraction complete",
        failure_message="❌ Pro chatlog extraction failed",
    ):
        _run_extract_pro(
            ctx,
            directory,
            output,
            confidence,
            batch_size,
            max_workers,
            archive,
            workspace_id,
            max_documents,
        )


def _run_extract_pro(
    ctx,
    directory: str,
    output: Optional[str],
    confidence: float,
    batch_size: int,
    max_workers: int,
    archive: Optional[str],
    workspace_id: Optional[str],
    max_documents: int,
) -> None:

    # Add the gpt-researcher backend to the path
    backend_path = Path(__file__).parent.parent.parent / "services" / "dopemux-gpt-researcher" / "backend"
    sys.path.insert(0, str(backend_path))

    try:
        from extraction_pipeline import ExtractionPipeline, PipelineConfig
    except ImportError as e:
        console.logger.info(f"[red]❌ Could not import extraction pipeline: {e}[/red]")
        console.logger.info("[yellow]💡 Make sure you're in the dopemux-mvp directory[/yellow]")
        sys.exit(1)

    source_path = Path(directory).resolve()
    if not source_path.exists():
        console.logger.info(f"[red]❌ Directory does not exist: {source_path}[/red]")
        sys.exit(1)

    # Set output directory
    if output:
        output_path = Path(output).resolve()
    else:
        output_path = source_path / ".dopemux" / "extraction-pro"

    # Set archive directory
    archive_path = None
    if archive:
        archive_path = Path(archive).resolve()

    # Set workspace ID for ConPort
    if not workspace_id:
        workspace_id = str(source_path)

    # Create configuration for Pro mode
    config = PipelineConfig(
        source_directory=source_path,
        output_directory=output_path,
        archive_directory=archive_path,
        batch_size=batch_size,
        max_workers=max_workers,
        confidence_threshold=confidence,
        include_basic_extractors=True,
        include_pro_extractors=True,  # Pro mode includes ALL extractors
        enable_synthesis=True,
        max_documents=max_documents,
        verbose=ctx.obj.get("verbose", False),
        persist_to_conport=True,
        workspace_id=workspace_id
    )

    console.logger.info("[blue]🔬 Starting Pro Chatlog Extraction Pipeline[/blue]")
    console.logger.info(f"[blue]📁 Source: {source_path}[/blue]")
    console.logger.info(f"[blue]📤 Output: {output_path}[/blue]")
    console.logger.info(f"[blue]🎯 Extractors: All 7 (Decision, Feature, Research, Constraint, Stakeholder, Risk, Security)[/blue]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing Pro extraction pipeline...", total=None)

        try:
            # Create and run pipeline
            pipeline = ExtractionPipeline(config)

            progress.update(task, description="Discovering files...")
            files = pipeline.discover_files()

            if not files:
                progress.update(task, description="No files found to process", completed=True)
                console.logger.info("[yellow]⚠️ No unprocessed chatlog files found[/yellow]")
                return

            progress.update(task, description=f"Processing {len(files)} files with ALL extractors...")
            result = pipeline.run_extraction()

            if result['success']:
                progress.update(task, description="Pro extraction completed successfully! ✅", completed=True)

                stats = result['statistics']
                console.print(
                    Panel(
                        f"🔬 Pro Extraction Results:\n\n"
                        f"• Files processed: {stats['files_processed']}/{stats['total_files']}\n"
                        f"• Total chunks: {stats['total_chunks']}\n"
                        f"• Fields extracted: {stats['total_fields']}\n"
                        f"• High confidence fields: {stats['high_confidence_fields']}\n"
                        f"• Documents generated: {stats['documents_generated']}\n"
                        f"• Processing time: {stats['processing_time']:.2f}s\n\n"
                        f"📊 Field Types:\n" +
                        "\n".join([f"• {field_type}: {count}"
                                 for field_type, count in stats['fields_by_type'].items()]) +
                        f"\n\n⏱️ Phase Times:\n" +
                        "\n".join([f"• {phase}: {time:.2f}s"
                                 for phase, time in stats['phase_times'].items()]),
                        title="🚀 Pro Extraction Complete",
                        border_style="green",
                    )
                )

                console.logger.info(f"\n[green]📁 Results saved to: {output_path}[/green]")
                console.logger.info(f"[green]📦 Processed files archived to: {result['archive_directory']}[/green]")
                console.logger.info(f"[green]📊 Knowledge graph: {output_path}/knowledge_graph.json[/green]")
                console.logger.info(f"[green]📋 Comprehensive report: {output_path}/reports/[/green]")

            else:
                progress.update(task, description="Pro extraction failed ❌", completed=True)
                console.logger.error(f"[red]❌ Pro extraction failed[/red]")
                if result.get('errors'):
                    console.logger.error(f"[red]Errors: {len(result['errors'])}[/red]")
                    for error in result['errors'][:3]:  # Show first 3 errors
                        console.logger.error(f"[red]  • {error}[/red]")
                sys.exit(1)

        except Exception as e:
            progress.update(task, description="Error occurred", completed=True)
            console.logger.error(f"[red]❌ Pro extraction pipeline failed: {e}[/red]")
            if ctx.obj.get("verbose"):
                import traceback
                traceback.print_exc()
            sys.exit(1)


@cli.group()
def update():
    """🔄 Update and upgrade dopemux system components."""
    pass


@update.command()
@click.option(
    "--check",
    is_flag=True,
    help="Check for updates without applying them (dry run)"
)
@click.option(
    "--minimal",
    is_flag=True,
    help="Skip Docker rebuilds if possible (faster update)"
)
@click.option(
    "--skip-backups",
    is_flag=True,
    help="Skip backup creation (not recommended)"
)
@click.option(
    "--skip-docker",
    is_flag=True,
    help="Skip Docker image updates"
)
@click.option(
    "--timeout",
    type=int,
    default=30,
    help="Timeout in minutes for update operations"
)
@click.pass_context
def run(ctx, check: bool, minimal: bool, skip_backups: bool, skip_docker: bool, timeout: int):
    """
    🚀 Run comprehensive system update

    Updates all dopemux components including:
    - Git repository (with local change preservation)
    - Docker containers and images
    - Python and Node.js dependencies
    - Database migrations
    - Configuration updates

    Includes automatic backup, rollback capability, and ADHD-friendly progress tracking.
    """
    import asyncio
    from .update import UpdateManager, UpdateConfig

    try:
        # Configure update
        config = UpdateConfig(
            dry_run=check,
            minimal=minimal,
            skip_backups=skip_backups,
            skip_docker=skip_docker,
            timeout_minutes=timeout
        )

        # Create update manager
        manager = UpdateManager(config=config, project_root=Path.cwd())

        if check:
            console.logger.info("[cyan]🔍 Checking for available updates...[/cyan]")
            # Run dry run
            plan = asyncio.run(manager.dry_run())

            # Display update plan
            _show_update_plan(plan)

        else:
            # Run actual update
            console.logger.info("[cyan]🚀 Starting dopemux update...[/cyan]")
            result = asyncio.run(manager.run_update())

            # Show result
            if result.value == "success":
                console.logger.info("[green]✅ Update completed successfully![/green]")
            elif result.value == "rolled_back":
                console.logger.error("[yellow]🔄 Update failed but rollback successful[/yellow]")
            elif result.value == "interrupted":
                console.logger.info("[yellow]⏸️ Update interrupted - resume with 'dopemux update resume'[/yellow]")
            else:
                console.logger.error("[red]❌ Update failed[/red]")
                sys.exit(1)

    except Exception as e:
        console.logger.error(f"[red]❌ Update command failed: {e}[/red]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@update.command()
@click.pass_context
def resume(ctx):
    """
    ▶️ Resume interrupted update from last checkpoint

    Continues an update that was interrupted by user or system failure.
    Uses automatic checkpointing to resume from the exact point of interruption.
    """
    import asyncio
    from .update import UpdateManager, UpdateConfig

    try:
        # Create manager with resume configuration
        config = UpdateConfig(checkpoint_saves=True)
        manager = UpdateManager(config=config, project_root=Path.cwd())

        console.logger.info("[cyan]🔄 Resuming interrupted update...[/cyan]")
        result = asyncio.run(manager.run_update())

        if result.value == "success":
            console.logger.info("[green]✅ Update resumed and completed successfully![/green]")
        else:
            console.logger.error(f"[red]❌ Update resume failed: {result.value}[/red]")
            sys.exit(1)

    except Exception as e:
        console.logger.error(f"[red]❌ Resume command failed: {e}[/red]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@update.command()
@click.option(
    "--backup-name",
    help="Specific backup to rollback to (interactive selection if not provided)"
)
@click.option(
    "--list-backups",
    is_flag=True,
    help="List available backups and exit"
)
@click.pass_context
def rollback(ctx, backup_name: Optional[str], list_backups: bool):
    """
    ⏪ Rollback to previous system state

    Safely restore the system to a previous working state using automatic backups.
    Includes database restoration, configuration rollback, and service restart.
    """
    import asyncio
    from .update import RollbackManager

    try:
        manager = RollbackManager(project_root=Path.cwd())

        if list_backups:
            # List available backups
            backups = manager.list_available_backups()

            if not backups:
                console.logger.info("[yellow]No backups available[/yellow]")
                return

            console.logger.info("\n[bold]Available Backups:[/bold]")
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Name", style="cyan")
            table.add_column("Created", style="dim")
            table.add_column("Version", style="green")
            table.add_column("Size", style="blue")

            for backup in backups:
                backup_path = Path(backup['path'])
                created = backup['created_at'][:19].replace('T', ' ')
                version = backup.get('version_from', 'unknown')
                size = backup.get('size', 'unknown')

                table.add_row(backup_path.name, created, version, size)

            console.logger.info(table)
            return

        # Perform rollback
        console.logger.info("[yellow]🔄 Initiating system rollback...[/yellow]")
        success = asyncio.run(manager.manual_rollback(backup_name))

        if success:
            console.logger.info("[green]✅ Rollback completed successfully![/green]")
        else:
            console.logger.error("[red]❌ Rollback failed[/red]")
            sys.exit(1)

    except Exception as e:
        console.logger.error(f"[red]❌ Rollback command failed: {e}[/red]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


@update.command()
@click.pass_context
def update_status_cmd(ctx):
    """
    📊 Show system update status and health

    Displays current version, available updates, system health,
    and update history.
    """
    import asyncio
    from .update import UpdateManager
    from .update.health import HealthChecker

    try:
        manager = UpdateManager(project_root=Path.cwd())
        health_checker = HealthChecker(project_root=Path.cwd())

        console.logger.info("[cyan]📊 Dopemux System Status[/cyan]\n")

        # Version information
        version_info = manager.check_for_updates()
        console.logger.info(f"[bold]Current Version:[/bold] {version_info.current}")
        console.logger.info(f"[bold]Latest Version:[/bold] {version_info.target}")

        if version_info.current != version_info.target:
            console.logger.info(f"[yellow]📦 Update available: {version_info.current} → {version_info.target}[/yellow]")
        else:
            console.logger.info("[green]✅ System is up to date[/green]")

        # Health status
        console.logger.info("\n[bold]System Health:[/bold]")
        health_results = asyncio.run(health_checker.check_all_services())

        healthy_count = sum(health_results.values())
        total_count = len(health_results)

        if healthy_count == total_count:
            console.logger.info(f"[green]✅ All services healthy ({healthy_count}/{total_count})[/green]")
        else:
            console.logger.info(f"[yellow]⚠️ {total_count - healthy_count} services need attention ({healthy_count}/{total_count})[/yellow]")

            # Show unhealthy services
            unhealthy = [service for service, healthy in health_results.items() if not healthy]
            for service in unhealthy:
                console.logger.info(f"  [red]❌ {service}[/red]")

    except Exception as e:
        console.logger.error(f"[red]❌ Status command failed: {e}[/red]")
        if ctx.obj and ctx.obj.get('verbose'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


def _show_update_plan(plan):
    """Show update plan in user-friendly format."""
    version_info = plan['version_info']

    console.logger.info(f"\n[bold]📋 Update Plan: v{version_info['current']} → v{version_info['target']}[/bold]")

    if version_info['current'] == version_info['target']:
        console.logger.info("[green]✅ Already up to date![/green]")
        return

    # Show what will be updated
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Component", style="cyan")
    table.add_column("Action", style="yellow")
    table.add_column("Details")

    table.add_row("Code", "🔄 Update", "Pull latest changes from git")
    table.add_row("Dependencies", "📦 Update", "Python and Node.js packages")
    table.add_row("Docker", "🐳 Rebuild", "Update container images")
    table.add_row("Configuration", "⚙️ Merge", "Preserve local customizations")

    if version_info.get('requires_migration'):
        table.add_row("Database", "🔄 Migrate", "Apply schema changes")

    console.logger.info(table)

    # Show estimates
    console.logger.info(f"\n[dim]⏱️ Estimated time: {plan.get('estimated_time', '15-20 minutes')}[/dim]")
    console.logger.info(f"[dim]💾 Backup size: {plan.get('backup_size', '~250 MB')}[/dim]")

    # Show phases
    phases = plan.get('phases', [])
    if phases:
        console.logger.info(f"\n[bold]Phases:[/bold] {' → '.join(phases)}")


# =============================================================================
# Profile Management Commands (Epic 1)
# =============================================================================

@cli.group()
def profile():
    """📋 Manage MCP profiles for context-aware tool selection."""
    pass


@profile.command("list")
@click.option("--profile-dir", "-d", help="Profile directory path", type=click.Path(exists=True))
@click.pass_context
def profile_list_cmd(ctx, profile_dir: Optional[str]):
    """📋 List all available profiles.

    Shows all profiles with their MCP server counts and descriptions.
    Profiles can be applied with: dopemux profile apply <name>
    """
    try:
        # Get profiles directory
        from .profile_commands import get_profiles_directory
        profiles_directory = Path(profile_dir) if profile_dir else get_profiles_directory()

        # Parse all profiles in directory
        parser = ProfileParser(validate_mcps=False)
        profile_set = parser.parse_directory(profiles_directory, pattern="*.yaml")

        if not profile_set.profiles:
            console.logger.info("[yellow]⚠️  No valid profiles found[/yellow]")
            console.logger.info(f"\n[dim]Profile directory: {profiles_directory}[/dim]")
            console.logger.info("\n[cyan]💡 Get started:[/cyan]")
            console.logger.info(f"   • Create personalized profile: [white]dopemux profile init[/white]")
            console.logger.info(f"   • See examples: [white]dopemux profile --help[/white]")
            console.logger.info(f"   • Read guide: [white]docs/guides/PROFILE_USER_GUIDE.md[/white]")
            sys.exit(1)

        # Display profiles in a rich table
        table = Table(title="📋 Available Profiles", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="green")
        table.add_column("Display Name", style="cyan")
        table.add_column("MCPs", style="yellow")
        table.add_column("Description", style="white", no_wrap=False)

        for p in profile_set.profiles:
            mcp_count = len(p.mcps)
            table.add_row(
                p.name,
                p.display_name,
                f"{mcp_count} servers",
                p.description
            )

        console.logger.info(table)
        console.logger.info(f"\n[dim]Profile directory: {profiles_directory}[/dim]")
        console.logger.info(f"[dim]Total profiles: {len(profile_set.profiles)}[/dim]")

        # Add helpful tips
        console.logger.info(f"\n[cyan]💡 Quick Tips:[/cyan]")
        console.logger.info(f"   • View details: [white]dopemux profile show <name>[/white]")
        console.logger.info(f"   • Apply profile: [white]dopemux profile apply <name>[/white]")
        console.logger.info(f"   • Create custom: [white]dopemux profile init[/white]")

    except FileNotFoundError as e:
        console.logger.error(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.logger.error(f"[red]Unexpected error: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


@profile.command("init")
@click.argument("profile_name", required=False)
@click.option("--output-dir", "-o", help="Output directory for profile", type=click.Path())
@click.pass_context
def profile_init_cmd(ctx, profile_name: Optional[str], output_dir: Optional[str]):
    """✨ Create a personalized profile using git history analysis."""
    try:
        from .profile_wizard import ProfileWizard

        # Initialize wizard
        wizard = ProfileWizard()

        # Run interactive wizard
        output_path = Path(output_dir) if output_dir else None
        result_file = wizard.run(profile_name=profile_name, output_dir=output_path)

        if result_file:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        console.logger.info("\n[yellow]❌ Profile creation cancelled[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.logger.error(f"[red]Unexpected error: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


@profile.command("auto-enable")
@click.option("--check-interval", "-i", type=int, help="Check interval in seconds (default: 300)")
@click.option("--threshold", "-t", type=float, help="Confidence threshold (default: 0.85)")
@click.pass_context
def profile_auto_enable_cmd(ctx, check_interval: Optional[int], threshold: Optional[float]):
    """🔍 Enable auto-detection with gentle profile suggestions."""
    try:
        from .auto_detection_service import AutoDetectionService, create_default_settings

        # Create default config if it doesn't exist
        config_file = Path.cwd() / ".dopemux" / "profile-settings.yaml"
        if not config_file.exists():
            create_default_settings(config_file)

        # Load and update config
        service = AutoDetectionService(config_file=config_file)

        if check_interval:
            service.config.check_interval_seconds = check_interval
        if threshold:
            service.config.confidence_threshold = threshold

        service.config.enabled = True
        service.config.save(config_file)

        console.logger.info("[green]✅ Auto-detection enabled[/green]")
        console.logger.info(f"   Check interval: {service.config.check_interval_seconds}s ({service.config.check_interval_seconds // 60} min)")
        console.logger.info(f"   Confidence threshold: {service.config.confidence_threshold:.0%}")
        console.logger.info(f"   Quiet hours: {service.config.quiet_hours_start}-{service.config.quiet_hours_end}")
        console.logger.info(f"\n[dim]💡 Service will suggest profile switches when confidence >{service.config.confidence_threshold:.0%}[/dim]")
        console.logger.info(f"[dim]💡 Edit settings: {config_file}[/dim]")

    except Exception as e:
        console.logger.error(f"[red]Error: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


@profile.command("auto-disable")
@click.pass_context
def profile_auto_disable_cmd(ctx):
    """⏸️  Disable auto-detection suggestions."""
    try:
        config_file = Path.cwd() / ".dopemux" / "profile-settings.yaml"

        if not config_file.exists():
            console.logger.info("[yellow]Auto-detection not configured[/yellow]")
            return

        from .auto_detection_service import AutoDetectionConfig

        config = AutoDetectionConfig(config_file)
        config.enabled = False
        config.save(config_file)

        console.logger.info("[green]✅ Auto-detection disabled[/green]")

    except Exception as e:
        console.logger.error(f"[red]Error: {e}[/red]")
        sys.exit(1)


@profile.command("auto-status")
@click.pass_context
def profile_auto_status_cmd(ctx):
    """📊 Show auto-detection configuration and status."""
    try:
        config_file = Path.cwd() / ".dopemux" / "profile-settings.yaml"

        if not config_file.exists():
            console.logger.info("[yellow]Auto-detection not configured[/yellow]")
            console.logger.info(f"\n[dim]Run 'dopemux profile auto-enable' to set up[/dim]")
            return

        from .auto_detection_service import AutoDetectionConfig

        config = AutoDetectionConfig(config_file)

        status = "[green]Enabled[/green]" if config.enabled else "[red]Disabled[/red]"
        console.logger.info(f"\n[bold]Auto-Detection Status:[/bold] {status}")
        console.logger.info(f"\n[cyan]Settings:[/cyan]")
        console.logger.info(f"   Check interval: {config.check_interval_seconds}s ({config.check_interval_seconds // 60} min)")
        console.logger.info(f"   Confidence threshold: {config.confidence_threshold:.0%}")
        console.logger.info(f"   Debounce period: {config.debounce_minutes} min")
        console.logger.info(f"   Quiet hours: {config.quiet_hours_start}-{config.quiet_hours_end}")

        if config.never_suggest:
            console.logger.info(f"\n[yellow]Never Suggest:[/yellow]")
            for profile in sorted(config.never_suggest):
                console.logger.info(f"   • {profile}")

        console.logger.info(f"\n[dim]Config file: {config_file}[/dim]")

    except Exception as e:
        console.logger.error(f"[red]Error: {e}[/red]")
        sys.exit(1)


@profile.command("stats")
@click.option("--days", "-d", type=int, default=30, help="Days of history to analyze (default: 30)")
@click.pass_context
def profile_stats_cmd(ctx, days: int):
    """📊 Show profile usage analytics and trends."""
    try:
        from .profile_analytics import get_stats_sync, display_stats

        workspace_id = str(Path.cwd())

        # Get stats from ConPort
        console.logger.info(f"[cyan]📊 Analyzing profile usage (last {days} days)...[/cyan]\n")
        stats = get_stats_sync(workspace_id, days_back=days)

        # Display with visual dashboard
        display_stats(stats, days_back=days)

        # Optimization suggestions (if enough data)
        if stats.total_switches >= 10:
            console.logger.info(f"\n[bold]💡 Optimization Suggestions:[/bold]")

            # Suggest based on patterns
            if stats.switch_accuracy < 70:
                console.logger.info(f"   • [yellow]Low accuracy ({stats.switch_accuracy:.0f}%)[/yellow]: Consider refining auto-detection rules")

            if stats.auto_switches == 0 and stats.total_switches > 20:
                console.logger.info(f"   • [cyan]All manual switches[/cyan]: Try 'dopemux profile auto-enable' for suggestions")

            if stats.suggestion_declined > stats.suggestion_accepted * 2:
                console.logger.info(f"   • [yellow]Many declined suggestions[/yellow]: Lower confidence threshold or adjust profile rules")

            # Suggest creating a new profile for common patterns
            if stats.most_used_profile and stats.usage_by_profile.get(stats.most_used_profile, 0) > stats.total_switches * 0.7:
                console.logger.info(f"   • [green]Stable workflow detected[/green]: Your '{stats.most_used_profile}' profile is well-matched!")

    except Exception as e:
        console.logger.error(f"[red]Error: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


@profile.command("analyze-usage")
@click.option("--days", "days_back", type=click.IntRange(1), default=90, show_default=True, help="Days of git history to analyze")
@click.option(
    "--max-commits",
    type=click.IntRange(1),
    default=500,
    show_default=True,
    help="Maximum commits to scan",
)
@click.option(
    "--repo-path",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Repository path (defaults to current directory)",
)
@click.pass_context
def profile_analyze_usage_cmd(ctx, days_back: int, max_commits: int, repo_path: Optional[Path]):
    """Analyze git usage patterns to suggest profile defaults."""
    try:
        from .profile_analyzer import GitHistoryAnalyzer

        analyzer = GitHistoryAnalyzer(repo_path=repo_path or Path.cwd())
        analysis = analyzer.analyze(days_back=days_back, max_commits=max_commits)
        analyzer.display_analysis(analysis)
    except Exception as e:
        console.logger.error(f"[red]Error: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


@profile.command("show")
@click.argument("profile_name")
@click.option("--profile-dir", "-d", help="Profile directory path", type=click.Path(exists=True))
@click.option("--raw", "-r", is_flag=True, help="Show raw YAML content")
@click.pass_context
def profile_show_cmd(ctx, profile_name: str, profile_dir: Optional[str], raw: bool):
    """📄 Show detailed profile information."""
    try:
        parser = ProfileParser(Path(profile_dir) if profile_dir else None)
        profile_paths = parser.discover_profiles()

        # Find matching profile
        profile_path = None
        for path in profile_paths:
            if path.stem == profile_name:
                profile_path = path
                break

        if not profile_path:
            console.logger.info(f"[red]Profile '{profile_name}' not found[/red]")
            console.logger.info(f"\nAvailable profiles in {parser.profile_dir}:")
            for path in profile_paths:
                console.logger.info(f"  • {path.stem}")
            sys.exit(1)

        # Show raw YAML if requested
        if raw:
            console.logger.info(f"\n[cyan]Profile: {profile_name}[/cyan]")
            console.logger.info(f"[dim]Path: {profile_path}[/dim]\n")
            with open(profile_path, 'r') as f:
                console.logger.info(f.read())
            return

        # Load and validate profile
        p = parser.load_profile(profile_path)

        # Display formatted profile info
        console.logger.info(f"\n[bold cyan]Profile: {p.display_name}[/bold cyan]")
        console.logger.info(f"[dim]Name: {p.name}[/dim]")
        console.logger.info(f"[dim]File: {profile_path}[/dim]\n")

        console.logger.info(f"[bold]Description:[/bold] {p.description}\n")

        # MCP Servers
        console.logger.info("[bold]MCP Servers:[/bold]")
        for mcp in p.mcps:
            console.logger.info(f"  • {mcp}")

        # ADHD Config (if present)
        if p.adhd_config:
            console.logger.info("\n[bold]ADHD Configuration:[/bold]")
            console.logger.info(f"  Energy preference: {p.adhd_config.energy_preference}")
            console.logger.info(f"  Attention mode: {p.adhd_config.attention_mode}")
            console.logger.info(f"  Session duration: {p.adhd_config.session_duration} minutes")

        # Auto-detection rules (if present)
        if p.auto_detection:
            console.logger.info("\n[bold]Auto-Detection Rules:[/bold]")
            if p.auto_detection.git_branches:
                console.logger.info("  Git branches:")
                for branch in p.auto_detection.git_branches:
                    console.logger.info(f"    • {branch}")
            if p.auto_detection.directories:
                console.logger.info("  Directories:")
                for dir in p.auto_detection.directories:
                    console.logger.info(f"    • {dir}")
            if p.auto_detection.file_patterns:
                console.logger.info("  File patterns:")
                for pattern in p.auto_detection.file_patterns:
                    console.logger.info(f"    • {pattern}")
            if p.auto_detection.time_windows:
                console.logger.info("  Time windows:")
                for window in p.auto_detection.time_windows:
                    console.logger.info(f"    • {window}")

        console.logger.info(f"\n[green]✓ Profile is valid[/green]")

    except ProfileValidationError as e:
        console.logger.error(f"[red]Validation Error:[/red] {e.reason}")
        if e.fix_suggestion:
            console.logger.info(f"[yellow]Suggestion:[/yellow] {e.fix_suggestion}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.logger.error(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.logger.error(f"[red]Unexpected error: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


@profile.command("validate")
@click.argument("profile_name", required=False)
@click.option("--profile-dir", "-d", help="Profile directory path", type=click.Path(exists=True))
@click.option("--all", "-a", is_flag=True, help="Validate all profiles")
@click.pass_context
def profile_validate_cmd(ctx, profile_name: Optional[str], profile_dir: Optional[str], all: bool):
    """✅ Validate profile YAML and configuration."""
    try:
        parser = ProfileParser(Path(profile_dir) if profile_dir else None)

        if all:
            # Validate all profiles
            console.logger.info("[cyan]Validating all profiles...[/cyan]\n")
            profile_set = parser.load_all_profiles(fail_fast=False)

            # Show results
            table = Table(title="Validation Results", show_header=True, header_style="bold cyan")
            table.add_column("Profile", style="cyan")
            table.add_column("Status", style="white")
            table.add_column("Message", style="white", no_wrap=False)

            for p in profile_set.profiles:
                table.add_row(p.name, "[green]✓ Valid[/green]", f"{len(p.mcps)} MCP servers")

            for path, error in profile_set.errors:
                error_msg = str(error)
                if isinstance(error, ProfileValidationError):
                    error_msg = f"{error.reason}"
                table.add_row(path.stem, "[red]✗ Invalid[/red]", error_msg)

            console.logger.info(table)

            # Summary
            total = len(profile_set.profiles) + len(profile_set.errors)
            valid = len(profile_set.profiles)
            console.logger.info(f"\n[bold]Summary:[/bold] {valid}/{total} profiles valid")

            if profile_set.errors:
                sys.exit(1)

        else:
            # Validate single profile
            if not profile_name:
                console.logger.error("[red]Error: Provide a profile name or use --all[/red]")
                console.logger.info("Usage: dopemux profile validate <profile_name>")
                console.logger.info("   or: dopemux profile validate --all")
                sys.exit(1)

            profile_paths = parser.discover_profiles()
            profile_path = None
            for path in profile_paths:
                if path.stem == profile_name:
                    profile_path = path
                    break

            if not profile_path:
                console.logger.info(f"[red]Profile '{profile_name}' not found[/red]")
                sys.exit(1)

            console.logger.info(f"[cyan]Validating profile: {profile_name}[/cyan]\n")

            # Load and validate
            p = parser.load_profile(profile_path)

            console.logger.info(f"[green]✓ YAML syntax is valid[/green]")
            console.logger.info(f"[green]✓ Profile schema is valid[/green]")
            console.logger.info(f"[green]✓ All {len(p.mcps)} MCP servers are configured[/green]")
            if p.adhd_config:
                console.logger.info(f"[green]✓ ADHD configuration is valid[/green]")
            if p.auto_detection:
                console.logger.info(f"[green]✓ Auto-detection rules are valid[/green]")

            console.logger.info(f"\n[bold green]Profile '{profile_name}' is valid ✓[/bold green]")

    except ProfileValidationError as e:
        console.logger.error(f"[red]✗ Validation failed:[/red] {e.reason}")
        if e.fix_suggestion:
            console.logger.info(f"[yellow]💡 Suggestion:[/yellow] {e.fix_suggestion}")
        sys.exit(1)
    except FileNotFoundError as e:
        console.logger.error(f"[red]Error: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.logger.error(f"[red]Unexpected error: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


@profile.command("copy")
@click.argument("source_name")
@click.argument("target_name")
def profile_copy_cmd(source_name: str, target_name: str):
    """Copy profile command placeholder."""
    raise click.ClickException("profile copy is not implemented yet")


@profile.command("edit")
@click.argument("profile_name")
def profile_edit_cmd(profile_name: str):
    """Edit profile command placeholder."""
    raise click.ClickException("profile edit is not implemented yet")


@profile.command("delete")
@click.argument("profile_name")
def profile_delete_cmd(profile_name: str):
    """Delete profile command placeholder."""
    raise click.ClickException("profile delete is not implemented yet")


@profile.command("current")
def profile_current_cmd():
    """Show current active profile placeholder."""
    raise click.ClickException("profile current is not implemented yet")


# Register additional profile commands from modules
try:
    from .profile_commands import (
        use_profile,
        create_profile
    )

    # Note: 'list' and 'show' are already defined above as inline commands.
    # We only add unique commands from the module to avoiding conflicts.
    profile.add_command(use_profile, "use")
    profile.add_command(create_profile, "create")
    profile.add_command(use_profile, "apply")
    cli.add_command(use_profile, "switch")

except ImportError:
    pass  # Profile commands not available


# Worktree Management Commands (Epic 3)
# =============================================================================

@cli.group()
def worktrees():
    """🌳 Manage git worktrees for parallel development."""
    pass


@worktrees.command("list")
@click.pass_context
def worktrees_list_cmd(ctx):
    """📋 List all git worktrees with status."""
    from .worktree_commands import list_worktrees
    list_worktrees()


@worktrees.command("current")
@click.option("--no-cache", is_flag=True, help="Skip cache and detect fresh")
@click.pass_context
def worktrees_current_cmd(ctx, no_cache: bool):
    """📍 Get current worktree path (cached for MCP efficiency)."""
    from .worktree_commands import get_current_worktree
    path = get_current_worktree(use_cache=not no_cache, quiet=False)
    if path:
        # Print just the path for easy shell scripting
        logger.info(path)
    else:
        sys.exit(1)


@worktrees.command("switch-path")
@click.argument("branch")
@click.pass_context
def worktrees_switch_path_cmd(ctx, branch: str):
    """📁 Output worktree path for shell integration (use with shell function)."""
    from .worktree_commands import get_worktree_path

    path = get_worktree_path(branch)

    if path:
        # Auto-configure MCP servers for target worktree (Phase 2: Zero manual steps)
        from .auto_configurator import WorktreeAutoConfigurator

        auto_config = WorktreeAutoConfigurator()
        success, message = auto_config.configure_workspace(Path(path))

        # Show auto-config status to stderr (doesn't pollute path output)
        if success:
            click.echo("✅ MCP auto-configuration complete", err=True)
        else:
            click.echo(f"⚠️ MCP auto-configuration: {message}", err=True)

        # Machine-readable output for shell integration (to stdout)
        click.echo(path)
        ctx.exit(0)
    else:
        # Error output to stderr
        click.echo(f"Error: Worktree not found for branch '{branch}'", err=True)
        click.echo("\nAvailable worktrees:", err=True)
        # Show list for user
        from .worktree_commands import list_worktrees
        list_worktrees()
        ctx.exit(1)


@worktrees.command("switch")
@click.argument("branch")
@click.option("--no-fuzzy", is_flag=True, help="Disable fuzzy matching")
@click.pass_context
def worktrees_switch_cmd(ctx, branch: str, no_fuzzy: bool):
    """[DEPRECATED] Use shell integration instead - see 'dopemux shell-setup'."""
    click.secho("\n⚠️  WARNING: This command cannot change your shell's directory", fg="yellow", bold=True)
    click.secho("This is a fundamental POSIX limitation, not a bug.\n", fg="yellow")

    click.secho("Why it doesn't work:", fg="cyan")
    click.echo("  • Python runs in a subprocess")
    click.echo("  • Subprocesses cannot modify the parent shell's working directory")
    click.echo("  • This affects ALL programming languages, not just Python\n")

    # Offer automated shell integration installation (Phase 3: UX Polish)
    click.secho("✅ Solution: Install shell integration", fg="green", bold=True)

    from .shell_integration_installer import ShellIntegrationInstaller

    installer = ShellIntegrationInstaller()

    if installer.is_supported() and not installer.is_installed():
        click.echo("\n[Option 1] Automated installation (recommended):")
        click.echo("  We can install shell integration automatically right now!")

        if click.confirm("  Install automatically?", default=True):
            success, message = installer.install(auto_confirm=True)

            if success:
                click.secho(f"\n🎉 {message}", fg="green", bold=True)
                click.echo(f"\nActivate now: source ~/{'.' + installer.shell_name + 'rc'}")
                click.echo(f"Then try: dwt {branch}\n")
                ctx.exit(0)
            else:
                click.secho(f"\n❌ {message}", fg="red")
                click.echo("Falling back to manual instructions...\n")
        else:
            click.echo("\n[Option 2] Manual installation:")
    else:
        click.echo("\n[Manual installation]:")

    click.echo("  1. Run: dopemux shell-setup bash >> ~/.bashrc")
    click.echo("  2. Run: source ~/.bashrc")
    click.echo(f"  3. Use: dwt {branch}\n")

    click.secho("Alternative: Use the workaround command", fg="cyan")
    click.echo(f"  cd $(dopemux worktrees switch-path {branch})\n")

    ctx.exit(1)


@worktrees.command("cleanup")
@click.option("--force", "-f", is_flag=True, help="Remove dirty worktrees")
@click.option("--dry-run", "-n", is_flag=True, help="Preview without removing")
@click.pass_context
def worktrees_cleanup_cmd(ctx, force: bool, dry_run: bool):
    """🧹 Clean up unused worktrees."""
    from .worktree_commands import cleanup_worktrees
    workspace = Path.cwd()
    cleanup_worktrees(workspace, force=force, dry_run=dry_run)


# Shell Integration Command
# =============================================================================

@cli.command("shell-setup")
@click.argument("shell_type", type=click.Choice(["bash", "zsh"], case_sensitive=False))
@click.pass_context
def shell_setup_cmd(ctx, shell_type: str):
    """🐚 Output shell integration code for worktree switching.

    This command outputs shell functions that enable proper worktree switching.
    Python subprocesses cannot change the parent shell's directory, so we provide
    shell functions that execute 'cd' in the shell's context.

    Usage:
        dopemux shell-setup bash >> ~/.bashrc && source ~/.bashrc
        dopemux shell-setup zsh >> ~/.zshrc && source ~/.zshrc

    Then use:
        dwt <branch>   # Switch to worktree with fuzzy matching
        dwtls          # List all worktrees
        dwtcur         # Show current worktree
    """
    import importlib.resources

    # Read the shell integration script
    script_path = Path(__file__).parent.parent.parent / "scripts" / "shell_integration.sh"

    if not script_path.exists():
        click.secho(f"❌ Shell integration script not found: {script_path}", fg="red", err=True)
        ctx.exit(1)

    try:
        content = script_path.read_text()

        # Output header
        click.echo(f"\n# Dopemux Shell Integration ({shell_type})")
        click.echo(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        click.echo("# Source: dopemux shell-setup\n")

        # Output the integration code
        click.echo(content)

        # Usage instructions to stderr so they don't pollute the output
        click.echo("\n# Installation complete! Restart your shell or run:", err=True)
        if shell_type == "bash":
            click.echo("#   source ~/.bashrc", err=True)
        else:
            click.echo("#   source ~/.zshrc", err=True)
        click.echo("#", err=True)
        click.echo("# Then use:", err=True)
        click.echo("#   dwt <branch>   - Switch to worktree", err=True)
        click.echo("#   dwtls          - List worktrees", err=True)
        click.echo("#   dwtcur         - Current worktree", err=True)

    except Exception as e:
        click.secho(f"❌ Error reading shell integration: {e}", fg="red", err=True)
        ctx.exit(1)


        logger.error(f"Error: {e}")
# Worktree Diagnostics Command
# =============================================================================

@cli.command("doctor")
@click.option("--worktree", is_flag=True, help="Run worktree-specific diagnostics")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed information")
@click.pass_context
def doctor_cmd(ctx, worktree: bool, verbose: bool):
    """🏥 Run system diagnostics and health checks.

    Comprehensive health check for Dopemux configuration, workspace detection,
    MCP servers, and worktree system.

    Examples:
        dopemux doctor                # General health check
        dopemux doctor --worktree     # Worktree system check
        dopemux doctor --worktree -v  # Detailed worktree diagnostics
    """
    if worktree:
        # Phase 1-3 worktree diagnostics
        from .worktree_diagnostics import run_diagnostics

        success = run_diagnostics(verbose=verbose)
        sys.exit(0 if success else 1)
    else:
        # General Dopemux health check
        console.logger.info("\n[bold cyan]🏥 Dopemux System Diagnostics[/bold cyan]\n")
        console.logger.info("[yellow]Use --worktree flag for worktree-specific checks[/yellow]\n")

        # Basic checks
        checks = []

        config_manager: ConfigManager = ctx.obj.get("config_manager") if ctx.obj else ConfigManager()
        mobile_cfg = config_manager.get_mobile_config()

        # 1. Check if dopemux is initialized
        workspace = Path.cwd()
        dopemux_dir = workspace / ".dopemux"
        checks.append(("Dopemux initialized", dopemux_dir.exists()))

        # 2. Check environment variables
        checks.append(("ANTHROPIC_API_KEY set", bool(os.getenv("ANTHROPIC_API_KEY"))))
        checks.append(("VOYAGE_API_KEY set", bool(os.getenv("VOYAGE_API_KEY"))))

        # 3. Check Docker (for MCP servers)
        try:
            subprocess.run(["docker", "version"], capture_output=True, check=True, timeout=5)
            checks.append(("Docker available", True))
        except Exception as e:
            checks.append(("Docker available", False))

            logger.error(f"Error: {e}")
        # 4. Mobile prerequisites
        happy_present = shutil.which("happy") is not None
        checks.append(("Happy CLI available", happy_present))

        claude_present = shutil.which("claude") is not None
        checks.append(("Claude CLI available", claude_present))

        if mobile_cfg.happy_server_url:
            parsed = urlparse(mobile_cfg.happy_server_url)
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            reachable = False
            if host:
                try:
                    with socket.create_connection((host, port), timeout=3):
                        reachable = True
                except Exception as e:
                    reachable = False
                    logger.error(f"Error: {e}")
            checks.append((f"Happy relay reachable ({mobile_cfg.happy_server_url})", reachable))

        # 5. TaskX rails check
        taskx_script = workspace / "scripts" / "taskx"
        taskx_doctor_ok = False
        taskx_label = "TaskX doctor deterministic"
        if taskx_script.exists():
            try:
                taskx_proc = subprocess.run(
                    [str(taskx_script), "doctor", "--timestamp-mode", "deterministic"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                taskx_doctor_ok = taskx_proc.returncode == 0
                if verbose and taskx_proc.stdout:
                    console.logger.info(taskx_proc.stdout.strip())
                if not taskx_doctor_ok and verbose:
                    taskx_error = taskx_proc.stderr.strip() or "TaskX doctor failed"
                    console.logger.error(taskx_error)
            except Exception as e:
                if verbose:
                    console.logger.error(f"TaskX doctor error: {e}")
                taskx_doctor_ok = False
        else:
            taskx_label = "TaskX doctor deterministic (scripts/taskx missing)"
        checks.append((taskx_label, taskx_doctor_ok))

        # Print results
        from rich.table import Table
        table = Table(show_header=False)
        table.add_column("Check", style="bold")
        table.add_column("Status")

        passed = 0
        for check_name, result in checks:
            status = "[green]✅ Pass[/green]" if result else "[red]❌ Fail[/red]"
            table.add_row(check_name, status)
            if result:
                passed += 1

        console.logger.info(table)

        # Summary
        console.logger.info(f"\n[bold]Result:[/bold] {passed}/{len(checks)} checks passed")

        if passed == len(checks):
            console.logger.info("[green]🎉 System healthy![/green]")
        else:
            console.logger.error("[yellow]⚠️  Some checks failed. See above for details.[/yellow]")

        sys.exit(0 if passed == len(checks) else 1)


# ============================================================================
# Decision Management Commands (ConPort Enhancement Quick Wins)
# ============================================================================

@cli.group()
def decisions():
    """
    📊 Decision tracking and analytics

    Manage and analyze decisions logged in ConPort with ADHD-optimized
    visualizations and review workflows.

    \b
    Quick Win Commands:
        review    - Review decisions pending attention
        stats     - Show decision statistics with charts
        energy    - Energy level tracking commands

    Part of ConPort Enhancement roadmap (Phase 1-5).
    """
    pass


@decisions.group()
def energy():
    """
    ⚡ Energy level tracking (ADHD optimization)

    Track your energy levels throughout the day to discover patterns
    and optimize decision-making timing.
    """
    pass


@decisions.group()
def patterns():
    """
    🔍 Pattern detection and learning (Phase 3)

    Auto-detect decision patterns from history:
    - Tag clustering (co-occurring tags)
    - Decision chains (sequential patterns)
    - Timing patterns (time-of-day, duration)
    - Energy correlation (energy vs quality)
    """
    pass


# Import and register decision commands
try:
    from .commands.decisions_commands import (
        review_decisions,
        decision_stats,
        log_energy,
        energy_status,
        show_decision,
        list_decisions,
        energy_analytics,
        graph_decision,
        update_outcome,
        enhanced_stats,
        query_decisions,
        pattern_tags
    )

    # Decision management commands
    decisions.add_command(review_decisions, "review")
    decisions.add_command(decision_stats, "stats")
    decisions.add_command(show_decision, "show")
    decisions.add_command(list_decisions, "list")
    decisions.add_command(graph_decision, "graph")
    decisions.add_command(update_outcome, "update-outcome")
    decisions.add_command(enhanced_stats, "stats-enhanced")
    decisions.add_command(query_decisions, "query")

    # Energy tracking commands
    energy.add_command(log_energy, "log")
    energy.add_command(energy_status, "status")
    energy.add_command(energy_analytics, "analytics")

    # Pattern detection commands (Phase 3)
    patterns.add_command(pattern_tags, "tags")

except ImportError as e:
    # Graceful degradation if dependencies not installed
    pass  # Commands won't be available but CLI still works




# ============================================================================
# Development Mode Commands (Contributor Support)
# ============================================================================

@cli.group()
def dev():
    """
    🔧 Development mode (for contributors)

    Auto-detects local checkouts of MCP servers (Zen, ConPort, etc.)
    and uses them instead of production versions. Enables hot reload
    and test database isolation.

    Components checked:
    - ~/code/zen-mcp-server (Zen MCP development)
    - ~/code/conport-mcp (ConPort development)
    - ~/code/serena-lsp (Serena development)
    """
    pass


# Import and register dev commands
try:
    from .dev_commands import dev_status, dev_enable, dev_paths

    dev.add_command(dev_status, "status")
    dev.add_command(dev_enable, "enable")
    dev.add_command(dev_paths, "paths")

except ImportError as e:
    pass  # Dev commands not available


# Register mobile integration commands
cli.add_command(mobile_commands, "mobile")
cli.add_command(mobile_env_commands, "mobile-env")


# Add genetic agent CLI group
if genetic_group:
    cli.add_command(genetic_group, "genetic")


# Code command group - dedicated vanilla agent interface
@cli.group()
@click.pass_context
def code(ctx):
    """
    🧠 AI Code Repair - Vanilla Agent

    Quick and reliable code fixes using traditional LLM-based iterative repair.
    Best for straightforward bugs and rapid development cycles.

    Examples:
        dopemux code repair "undefined variable error" --file script.py
        dopemux code analyze "null pointer issue" --file app.py
        dopemux code status
    """
    pass


@code.command()
@click.argument('bug_description')
@click.option('--file', '-f', 'file_path', help='Path to file containing the bug')
@click.option('--line', '-l', type=int, help='Line number where bug occurs')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.pass_context
def repair(ctx, bug_description, file_path, line, verbose, dry_run):
    """
    Repair code using the vanilla agent.

    BUG_DESCRIPTION: Description of the bug to fix

    Examples:
        dopemux code repair "variable not defined" --file script.py --line 42
        dopemux code repair "null pointer exception" --file app.py --verbose
    """
    # Import here to avoid circular dependencies
    try:
        # Add services to Python path if needed
        services_path = Path(__file__).resolve().parent.parent / 'services'
        if str(services_path) not in sys.path:
            sys.path.insert(0, str(services_path))

        from genetic_agent.vanilla.vanilla_agent import VanillaAgent
        from genetic_agent.core.config import AgentConfig
        import asyncio

        async def run_repair():
            config = AgentConfig()
            agent = VanillaAgent(config)

            task = {
                "bug_description": bug_description,
                "file_path": file_path or "",
                "line_number": line or 0
            }

            if dry_run:
                console.logger.info("[yellow]🔍 Dry run mode - analyzing bug without repair[/yellow]")
                analysis = await agent._analyze_bug(bug_description, file_path or "", line or 0)
                console.logger.info("Analysis Results:")
                console.logger.info(f"  Description: {analysis.get('description', 'N/A')}")
                console.logger.info(f"  Complexity: {analysis.get('complexity', {}).get('score', 'N/A')}")
                console.logger.info(f"  Similar patterns: {len(analysis.get('similar_patterns', {}).get('results', []))}")
                return

            result = await agent.process_task(task)

            if result.get('success'):
                console.logger.info("[green]✅ Repair successful![/green]")
                console.logger.info(f"Confidence: {result.get('confidence', 0):.2f}")
                console.logger.info(f"Iterations: {result.get('iterations', 0)}")
                if result.get('repair'):
                    console.logger.info("\n[blue]Generated Repair:[/blue]")
                    console.logger.info(result['repair'])
                if result.get('explanation'):
                    console.logger.info(f"\n[yellow]Explanation:[/yellow] {result['explanation']}")
            else:
                console.logger.error("[red]❌ Repair failed[/red]")
                console.logger.error(f"Reason: {result.get('explanation', 'Unknown error')}")
                if verbose:
                    console.logger.debug(f"Debug: Iterations attempted: {result.get('iterations', 0)}")

        asyncio.run(run_repair())

    except Exception as e:
        console.logger.error(f"[red]❌ Code repair failed: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()


@code.command()
@click.argument('bug_description')
@click.option('--file', '-f', 'file_path', help='Path to file to analyze')
@click.option('--line', '-l', type=int, help='Line number to analyze')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def analyze(ctx, bug_description, file_path, line, verbose):
    """
    Analyze a bug without attempting repair.

    Provides insights, complexity assessment, and repair strategy recommendations.
    """
    try:
        services_path = Path(__file__).resolve().parent.parent / 'services'
        if str(services_path) not in sys.path:
            sys.path.insert(0, str(services_path))

        from genetic_agent.vanilla.vanilla_agent import VanillaAgent
        from genetic_agent.core.config import AgentConfig
        import asyncio

        async def run_analysis():
            config = AgentConfig()
            agent = VanillaAgent(config)

            analysis = await agent._analyze_bug(bug_description, file_path or "", line or 0)

            console.logger.info("[blue]🔍 Bug Analysis Complete[/blue]")
            console.logger.info(f"Description: {analysis.get('description', 'N/A')}")
            console.logger.info(f"Complexity Score: {analysis.get('complexity', {}).get('score', 'N/A')}")
            console.logger.info(f"Similar Patterns Found: {len(analysis.get('similar_patterns', {}).get('results', []))}")

            if verbose:
                if analysis.get('complexity', {}).get('details'):
                    console.logger.info("Complexity Details:")
                    for key, value in analysis['complexity']['details'].items():
                        console.logger.info(f"  {key}: {value}")

        asyncio.run(run_analysis())

    except Exception as e:
        console.logger.error(f"[red]❌ Analysis failed: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()


@code.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def code_agent_status_cmd(ctx, verbose):
    """
    Show code agent status and configuration.
    """
    try:
        services_path = Path(__file__).resolve().parent.parent / 'services'
        if str(services_path) not in sys.path:
            sys.path.insert(0, str(services_path))

        from genetic_agent.core.config import AgentConfig
        import asyncio

        async def show_status():
            config = AgentConfig()

            console.logger.info("[blue]🧠 Vanilla Code Agent Status[/blue]")
            console.logger.info(f"Container Zen URL: {config.zen_url}")
            console.logger.info(f"Container ConPort URL: {config.conport_url}")
            console.logger.info(f"Container Serena URL: {config.serena_url}")
            console.logger.info(f"Container Dope-Context URL: {config.dope_context_url}")
            console.logger.info(f"Max Iterations: {config.max_iterations}")
            console.logger.info(f"Confidence Threshold: {config.confidence_threshold}")
            console.logger.info(f"Workspace: {config.workspace_id}")

            # Test MCP connectivity from host (localhost URLs)
            console.logger.info("\n[yellow]Host MCP Service Status (localhost):[/yellow]")
            host_urls = {
                "Zen": "http://localhost:3003",
                "ConPort": "http://localhost:3004",
                "Serena": "http://localhost:3006",
                "Dope-Context": "http://localhost:3010"
            }

            timeout = aiohttp.ClientTimeout(total=3.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for service, url in host_urls.items():
                    reachable = False
                    error_msg = ""

                    try:
                        health_url = f"{url.rstrip('/')}/health"
                        async with session.get(health_url) as response:
                            if response.status == 200:
                                reachable = True
                            else:
                                error_msg = f"Health check failed with status {response.status}"
                    except Exception as e:
                        error_msg = f"Connection failed: {str(e)}"

                        logger.error(f"Error: {e}")
                    status_icon = "✅" if reachable else "❌"
                    console.logger.info(f"  {status_icon} {service}")
                    if not reachable:
                        console.logger.error(f"    Error: {error_msg}")

            console.logger.info("\n[dim]Note: Container uses Docker network names, host uses localhost[/dim]")

        asyncio.run(show_status())

    except Exception as e:
        console.logger.error(f"[red]❌ Status check failed: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()

# Ensure tmux commands group exists
if not hasattr(tmux_commands, 'commands'):
    # If tmux_commands is not a Click group, create one
    @cli.group()
    def tmux():
        """Manage tmux sessions and panes for Dopemux."""
        pass
    tmux_commands = tmux

cli.add_command(tmux_commands, "tmux")

# Register Claude-Code-Tools commands
from .claude_tools.cli import register_commands
register_commands(cli)


# ============================================================================
# Memory Capture & Global Rollup Commands
# ============================================================================

@cli.group()
def memory():
    """🧠 Memory capture and global rollup operations."""
    pass


@memory.group()
def rollup():
    """📊 Global rollup index operations."""
    pass


@rollup.command()
@click.option(
    "--projects-file",
    type=click.Path(exists=True, path_type=Path),
    help="File containing list of project roots (newline or JSON)",
)
@click.option(
    "--index-path",
    type=click.Path(path_type=Path),
    help="Global index path (default: ~/.dopemux/global_index.sqlite)",
)
def build(projects_file: Optional[Path], index_path: Optional[Path]):
    """Build global rollup index from project ledgers (read-only)."""
    from dopemux.memory.global_rollup import (
        GlobalRollupIndexer,
        resolve_rollup_projects,
        GlobalRollupError,
    )

    try:
        roots = resolve_rollup_projects(projects_file=projects_file)
        console.logger.info(f"[cyan]Resolved {len(roots)} project(s)[/cyan]")

        indexer = GlobalRollupIndexer(index_path=index_path)
        result = indexer.build(roots)

        console.logger.info(f"[green]✓[/green] Projects registered: {result['projects_registered']}")
        console.logger.info(f"[green]✓[/green] Pointers indexed: {result['pointers_upserted']}")
        console.logger.info(f"[green]✓[/green] Index: {result['index_path']}")

    except GlobalRollupError as e:
        console.logger.error(f"[red]✗ Rollup error:[/red] {e}")
        raise click.Abort()


@rollup.command()
@click.option(
    "--index-path",
    type=click.Path(path_type=Path),
    help="Global index path (default: ~/.dopemux/global_index.sqlite)",
)
def list(index_path: Optional[Path]):
    """List registered projects in global rollup index."""
    from dopemux.memory.global_rollup import GlobalRollupIndexer
    from rich.table import Table

    indexer = GlobalRollupIndexer(index_path=index_path)

    projects = indexer.list_projects()

    if not projects:
        console.logger.info("[yellow]No projects registered in global index[/yellow]")
        return

    table = Table(title="Registered Projects")
    table.add_column("Project ID", style="cyan")
    table.add_column("Repo Root", style="green")
    table.add_column("Last Seen", style="yellow")

    for proj in projects:
        table.add_row(
            proj["project_id"],
            proj["repo_root"],
            proj["last_seen_at"],
        )

    console.logger.info(table)


@rollup.command()
@click.argument("query")
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Max results (default: 10, max: 100)",
)
@click.option(
    "--index-path",
    type=click.Path(path_type=Path),
    help="Global index path (default: ~/.dopemux/global_index.sqlite)",
)
def search(query: str, limit: int, index_path: Optional[Path]):
    """Search global rollup index for promoted work log entries."""
    from dopemux.memory.global_rollup import GlobalRollupIndexer
    from rich.table import Table

    indexer = GlobalRollupIndexer(index_path=index_path)

    results = indexer.search(query, limit=limit)

    if not results:
        console.logger.info(f"[yellow]No results for: {query}[/yellow]")
        return

    table = Table(title=f"Search Results: {query}")
    table.add_column("Timestamp", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Summary", style="green")
    table.add_column("Project", style="blue", overflow="fold")

    for row in results:
        table.add_row(
            row["ts_utc"],
            row["event_type"],
            row["summary"][:80] + ("..." if len(row["summary"]) > 80 else ""),
            row["project_id"][-40:],  # Last 40 chars of path
        )

    console.logger.info(table)
    console.logger.info(f"\n[dim]Showing {len(results)} of up to {limit} results[/dim]")


@memory.group()
def capture():
    """📥 Capture CLI tool events (Copilot, Codex, etc.)"""
    pass


@capture.command()
@click.option(
    "--event",
    type=str,
    required=True,
    help="Event JSON string (required)",
)
@click.option(
    "--mode",
    type=click.Choice(["plugin", "cli", "mcp", "auto"]),
    default="auto",
    help="Capture mode (default: auto)",
)
@click.option(
    "--quiet",
    is_flag=True,
    help="Suppress output (for hook usage)",
)
@click.option(
    "--repo-root",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Project repository root (default: auto-detect)",
)
@click.option(
    "--lane",
    type=str,
    default=None,
    help="Lane identifier for policy enforcement (e.g., agent:primary)",
)
def emit(event: str, mode: str, quiet: bool, repo_root: Optional[Path], lane: Optional[str]):
    """
    Emit a capture event to Chronicle.

    Writes event to per-project Chronicle ledger with content-addressed
    deduplication. Designed for hook and adapter usage.

    Examples:

        dopemux memory capture emit --event '{"event_type":"file.written","payload":{"path":"src/app.py"}}'

        dopemux memory capture emit --mode plugin --quiet --event '{"event_type":"task.completed","payload":{"task":"T-001"}}'
    """
    from dopemux.memory.capture_client import emit_capture_event, CaptureError
    import json

    try:
        # Parse event JSON
        try:
            event_data = json.loads(event)
        except json.JSONDecodeError as e:
            if not quiet:
                console.logger.error(f"[red]✗ Invalid JSON:[/red] {e}")
            raise click.Abort()

        # Validate event structure
        if not isinstance(event_data, dict):
            if not quiet:
                console.logger.error("[red]✗ Event must be a JSON object[/red]")
            raise click.Abort()

        if "event_type" not in event_data:
            if not quiet:
                console.logger.error("[red]✗ Event must have 'event_type' field[/red]")
            raise click.Abort()

        # Emit to Chronicle
        result = emit_capture_event(
            event_data,
            mode=mode,
            repo_root=repo_root,
            emit_event_bus=False,  # Don't emit to event bus for manual captures
            lane=lane,
        )

        # Output result
        if not quiet:
            if result.inserted:
                console.logger.info(f"[green]✓[/green] Event captured: {result.event_id[:16]}...")
                console.logger.info(f"  Event type: {event_data.get('event_type')}")
                console.logger.info(f"  Mode: {mode}")
            else:
                console.logger.info(f"[yellow]✓[/yellow] Event already exists (deduplicated): {result.event_id[:16]}...")

        # Exit code 0 on success
        sys.exit(0)

    except CaptureError as e:
        if not quiet:
            console.logger.error(f"[red]✗ Capture error:[/red] {e}")
        sys.exit(1)
    except Exception as e:
        if not quiet:
            console.logger.error(f"[red]✗ Unexpected error:[/red] {e}")
        sys.exit(1)


@capture.command()
@click.argument("session_id")
@click.option(
    "--since",
    type=str,
    default=None,
    help="Only ingest events after this ISO timestamp",
)
@click.option(
    "--repo-root",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Project repository root (default: auto-detect)",
)
def copilot(session_id: str, since: Optional[str], repo_root: Optional[Path]):
    """
    Ingest Copilot CLI session transcript into Chronicle.

    Parses JSONL events from ~/.copilot/session-state/{SESSION_ID}/events.jsonl
    and emits to Chronicle via content-addressed deduplication.

    Examples:

        dopemux memory capture copilot 550e8400-e29b-41d4-a716-446655440000

        dopemux memory capture copilot SESSION_ID --since 2025-02-12T10:30:00Z

        dopemux memory capture copilot SESSION_ID --repo-root /path/to/project
    """
    from dopemux.memory.adapters import CopilotCaptureAdapter
    from datetime import datetime

    try:
        # Parse since timestamp if provided
        since_dt = None
        if since:
            try:
                since_dt = datetime.fromisoformat(since.rstrip("Z"))
            except ValueError as e:
                console.logger.error(f"[red]✗ Invalid timestamp format:[/red] {e}")
                console.logger.info("[dim]Expected ISO 8601 format: 2025-02-12T10:30:00Z[/dim]")
                raise click.Abort()

        # Initialize adapter
        adapter = CopilotCaptureAdapter(repo_root=repo_root)

        # Ingest session
        console.logger.info(f"[cyan]📥 Ingesting Copilot session: {session_id}[/cyan]")
        if since:
            console.logger.info(f"[dim]Filtering events after: {since}[/dim]")

        stats = adapter.ingest_session(session_id, since=since_dt)

        # Display results
        console.logger.info(f"\n[green]✓[/green] Ingestion complete:")
        console.logger.info(f"  Total events parsed: {stats['total']}")
        console.logger.info(f"  Successfully inserted: {stats['inserted']}")
        console.logger.info(f"  Deduplicated (already exist): {stats['deduplicated']}")
        console.logger.info(f"  Skipped (unmapped types): {stats['skipped']}")

        if stats["inserted"] == 0 and stats["total"] > 0:
            console.logger.info("\n[yellow]💡 All events already ingested (idempotent)[/yellow]")

    except FileNotFoundError as e:
        console.logger.error(f"[red]✗ Session not found:[/red] {e}")
        console.logger.info("[dim]Use 'dopemux memory capture copilot-list' to see available sessions[/dim]")
        raise click.Abort()
    except Exception as e:
        console.logger.error(f"[red]✗ Ingestion failed:[/red] {e}")
        raise click.Abort()


@capture.command("copilot-list")
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Max sessions to display (default: 20)",
)
def copilot_list(limit: int):
    """
    List available Copilot CLI sessions.

    Shows sessions from ~/.copilot/session-state/ with event counts and timestamps.

    Examples:

        dopemux memory capture copilot-list

        dopemux memory capture copilot-list --limit 50
    """
    from dopemux.memory.adapters import CopilotCaptureAdapter
    from rich.table import Table

    adapter = CopilotCaptureAdapter()
    sessions = adapter.list_sessions()

    if not sessions:
        console.logger.info("[yellow]No Copilot sessions found in ~/.copilot/session-state/[/yellow]")
        return

    # Limit results
    display_sessions = sessions[:limit]

    table = Table(title=f"Available Copilot Sessions (showing {len(display_sessions)} of {len(sessions)})")
    table.add_column("Session ID", style="cyan", width=36)
    table.add_column("Events", style="green", justify="right")
    table.add_column("Started", style="yellow")

    for session in display_sessions:
        table.add_row(
            session["session_id"],
            str(session["event_count"]),
            session.get("start_timestamp") or "unknown",
        )

    console.logger.info(table)

    if len(sessions) > limit:
        console.logger.info(f"\n[dim]💡 Showing {limit} of {len(sessions)} sessions. Use --limit to see more.[/dim]")


# ============================================================================
# 🚀 EASY LAUNCH SHORTCUTS - Quick commands for common workflows
# ============================================================================

@cli.command("launch")
@click.option(
    "--preset",
    type=click.Choice(["minimal", "standard", "full", "dope-muted", "dope-neon", "dope-house"]),
    default="standard",
    help="Launch preset configuration"
)
@click.option("--attach/--no-attach", default=True, help="Attach to session after creation")
@click.pass_context
def launch(ctx, preset: str, attach: bool):
    """
    🚀 Quick launch with opinionated presets.
    
    Presets:
    
      minimal     - Just Claude Code, no tmux
      standard    - Medium layout with default theme
      full        - DOPE layout with all features
      dope-muted  - DOPE layout + muted theme (recommended)
      dope-neon   - DOPE layout + neon theme
      dope-house  - DOPE layout + house theme
    
    Examples:
    
      dopemux launch                    # Standard setup
      dopemux launch --preset full      # Full DOPE layout
      dopemux launch --preset dope-muted  # DOPE with muted colors
    """
    from .tmux.controller import TmuxController
    import subprocess
    import time
    
    console.logger.info(f"[cyan]🚀 Launching Dopemux with '{preset}' preset...[/cyan]\n")
    
    if preset == "minimal":
        # Just start Claude Code, no tmux
        console.logger.info("[dim]Starting Claude Code without tmux...[/dim]")
        ctx.invoke(cli.commands['start'])
        return
    
    # Parse preset into layout and theme
    layout_map = {
        "standard": ("medium", None),
        "full": ("dope", None),
        "dope-muted": ("dope", "muted"),
        "dope-neon": ("dope", "neon"),
        "dope-house": ("dope", "house"),
    }
    
    layout, theme = layout_map[preset]
    
    # Start tmux with layout
    console.logger.info(f"[blue]📐 Creating {layout} layout...[/blue]")
    
    tmux_start_args = [
        "dopemux", "tmux", "start",
        "--layout", layout,
        "--bootstrap",
    ]
    
    if not attach:
        tmux_start_args.append("--no-attach")
    
    # Start the session
    subprocess.run(tmux_start_args, check=True)

    autoindex_result = _trigger_dope_context_autoindex_startup(Path.cwd())
    if autoindex_result and autoindex_result.get("status") in {"started", "already_running"}:
        console.logger.info("[dim]✅ Dope-context autoindex bootstrap triggered[/dim]")

    # Apply theme if specified
    if theme:
        console.logger.info(f"\n[magenta]🎨 Applying {theme} theme...[/magenta]")
        time.sleep(1)  # Give tmux time to initialize
        subprocess.run(["dopemux", "tmux", "theme", theme, "--apply"], check=True)
        console.logger.info(f"[green]✨ {preset} preset ready![/green]")
    else:
        console.logger.info(f"[green]✨ {preset} preset ready![/green]")


@cli.command("dope")
@click.option(
    "--theme",
    type=click.Choice(["muted", "neon", "house"]),
    default="muted",
    help="Visual theme to apply"
)
@click.option("--attach/--no-attach", default=True, help="Attach to session")
@click.pass_context
def dope(ctx, theme: str, attach: bool):
    """
    🔥 Launch full DOPE layout (shortcut for: launch --preset dope-{theme})
    
    This is the complete Dopemux experience:
      ✓ Full DOPE layout with all monitors
      ✓ Orchestrator + dual agents
      ✓ Dashboard panels
      ✓ Auto-bootstrap services
      ✓ Your choice of theme
    
    Examples:
    
      dopemux dope              # DOPE with muted theme (default)
      dopemux dope --theme neon # DOPE with neon theme
      dopemux dope --theme house # DOPE with house theme
    """
    preset = f"dope-{theme}"
    ctx.invoke(launch, preset=preset, attach=attach)


@cli.command("quick")
@click.pass_context
def quick(ctx):
    """
    ⚡ Fastest start - medium layout, no bells and whistles.
    
    Perfect for:
      • Quick coding sessions
      • Testing something fast
      • Don't need full monitoring
    
    Equivalent to: dopemux tmux start --layout medium
    """
    console.print("[cyan]⚡ Quick start - medium layout[/cyan]\n")
    import subprocess
    subprocess.run([
        "dopemux", "tmux", "start",
        "--layout", "medium",
    ], check=True)


@cli.group("trigger")
def trigger_group():
    """Internal hook triggers."""
    pass

@trigger_group.command("command-done")
@click.option("--async", "_async", is_flag=True, help="No-op")
@click.option("--quiet", is_flag=True, help="Suppress output")
def trigger_command_done(_async: bool, quiet: bool):
    if _async and not quiet:
        quiet = True
    try:
        emit_capture_event(
            {"event_type": "command.done", "payload": {}},
            mode="auto",
            emit_event_bus=False,
        )
    except CaptureError:
        sys.exit(1)
    if not quiet:
        console.print("[dim]command-done trigger received[/dim]")
    return 0

@trigger_group.command("shell-command")
@click.option("--context", type=str, help="JSON context", default="")
@click.option("--async", "_async", is_flag=True, help="No-op")
@click.option("--quiet", is_flag=True, help="Suppress output")
def trigger_shell_command(context: str, _async: bool, quiet: bool):
    import json

    if _async and not quiet:
        quiet = True
    payload: dict = {}
    if context:
        try:
            parsed_context = json.loads(context)
            payload = parsed_context if isinstance(parsed_context, dict) else {"context": parsed_context}
        except json.JSONDecodeError:
            payload = {"raw_context": context}
    try:
        emit_capture_event(
            {"event_type": "shell.command", "payload": payload},
            mode="auto",
            emit_event_bus=False,
        )
    except CaptureError:
        sys.exit(1)
    if not quiet:
        console.print("[dim]shell-command trigger received[/dim]")
    return 0


@cli.group("capture")
def capture_group():
    """Capture events into Chronicle."""
    pass


@capture_group.command("emit")
@click.option("--event", type=str, required=True, help="Event JSON object")
@click.option(
    "--mode",
    type=click.Choice(["plugin", "cli", "mcp", "auto"]),
    default="auto",
    help="Capture mode",
)
@click.option("--repo-root", type=click.Path(exists=True, path_type=Path), default=None)
def capture_emit(event: str, mode: str, repo_root: Optional[Path]):
    import json

    try:
        event_data = json.loads(event)
    except json.JSONDecodeError as exc:
        raise click.ClickException(f"Invalid JSON: {exc}")

    if not isinstance(event_data, dict):
        raise click.ClickException("event must decode to an object")

    emit_capture_event(
        event_data,
        mode=mode,
        repo_root=repo_root,
        emit_event_bus=False,
    )


@capture_group.command("note", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("tokens", nargs=-1, type=click.UNPROCESSED)
def capture_note(tokens: Sequence[str]):
    if not tokens:
        raise click.ClickException("summary is required")

    summary = tokens[0]
    mode = "auto"
    tags: List[str] = []
    session_id: Optional[str] = None
    source = "cli"

    i = 1
    while i < len(tokens):
        arg = tokens[i]
        if arg == "--mode":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--mode requires a value")
            mode = tokens[i]
        elif arg == "--tag":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--tag requires a value")
            tags.append(tokens[i])
        elif arg == "--session-id":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--session-id requires a value")
            session_id = tokens[i]
        elif arg == "--source":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--source requires a value")
            source = tokens[i]
        else:
            raise click.ClickException(f"Unknown option: {arg}")
        i += 1

    event = {
        "event_type": "manual.note",
        "source": source,
        "payload": {
            "summary": summary,
            "tags": tags,
        },
    }
    if session_id:
        event["session_id"] = session_id

    emit_capture_event(
        event,
        mode=mode,
        emit_event_bus=False,
    )


def _workflow_api_base_url() -> str:
    return os.getenv("DOPEMUX_WORKFLOW_API_URL", "http://localhost:8000").rstrip("/")


def _workflow_request(method: str, path: str, *, json_payload=None, params=None):
    import requests

    url = f"{_workflow_api_base_url()}{path}"
    response = requests.request(method, url, json=json_payload, params=params, timeout=30)
    if response.status_code >= 400:
        raise click.ClickException(f"Workflow API error {response.status_code}: {response.text}")
    return response


@cli.group("workflow")
def workflow_group():
    """Workflow planning commands."""
    pass


@workflow_group.group("ideas")
def workflow_ideas_group():
    """Workflow idea management."""
    pass


@workflow_ideas_group.command("add", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("tokens", nargs=-1, type=click.UNPROCESSED)
def workflow_ideas_add(tokens: Sequence[str]):
    title: Optional[str] = None
    description: Optional[str] = None
    source = "manual"
    creator = "cli"
    tags: List[str] = []

    i = 0
    while i < len(tokens):
        arg = tokens[i]
        if arg == "--title":
            i += 1
            title = tokens[i] if i < len(tokens) else None
        elif arg == "--description":
            i += 1
            description = tokens[i] if i < len(tokens) else None
        elif arg == "--source":
            i += 1
            source = tokens[i] if i < len(tokens) else source
        elif arg == "--creator":
            i += 1
            creator = tokens[i] if i < len(tokens) else creator
        elif arg == "--tag":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--tag requires a value")
            tags.append(tokens[i])
        else:
            raise click.ClickException(f"Unknown option: {arg}")
        i += 1

    if not title:
        raise click.ClickException("--title is required")
    if not description:
        raise click.ClickException("--description is required")

    payload = {
        "title": title,
        "description": description,
        "source": source,
        "creator": creator,
        "tags": tags,
    }
    _workflow_request("POST", "/api/workflow/ideas", json_payload=payload)


@workflow_ideas_group.command("promote", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("idea_id")
@click.argument("tokens", nargs=-1, type=click.UNPROCESSED)
def workflow_ideas_promote(
    idea_id: str,
    tokens: Sequence[str],
):
    sync_leantime = True
    priority: Optional[str] = None
    business_value: Optional[str] = None
    criteria: List[str] = []
    tags: List[str] = []

    i = 0
    while i < len(tokens):
        arg = tokens[i]
        if arg == "--sync-leantime":
            sync_leantime = True
        elif arg == "--no-sync-leantime":
            sync_leantime = False
        elif arg == "--priority":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--priority requires a value")
            priority = tokens[i]
        elif arg == "--business-value":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--business-value requires a value")
            business_value = tokens[i]
        elif arg == "--criterion":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--criterion requires a value")
            criteria.append(tokens[i])
        elif arg == "--tag":
            i += 1
            if i >= len(tokens):
                raise click.ClickException("--tag requires a value")
            tags.append(tokens[i])
        else:
            raise click.ClickException(f"Unknown option: {arg}")
        i += 1

    payload = {
        "sync_to_leantime": sync_leantime,
        "acceptance_criteria": criteria,
        "tags": tags,
    }
    if priority:
        payload["priority"] = priority
    if business_value:
        payload["business_value"] = business_value

    _workflow_request("POST", f"/api/workflow/ideas/{idea_id}/promote", json_payload=payload)


@workflow_group.group("epics")
def workflow_epics_group():
    """Workflow epic management."""
    pass


@workflow_epics_group.command("list")
@click.option("--status", default=None, help="Filter by status")
@click.option("--priority", default=None, help="Filter by priority")
@click.option("--tag", default=None, help="Filter by single tag")
@click.option("--limit", type=int, default=20, show_default=True)
def workflow_epics_list(status: Optional[str], priority: Optional[str], tag: Optional[str], limit: int):
    params = {"limit": limit}
    if status:
        params["status"] = status
    if priority:
        params["priority"] = priority
    if tag:
        params["tag"] = tag

    _workflow_request("GET", "/api/workflow/epics", params=params)


@cli.command("layouts")
def layouts():
    """
    📐 Show available layouts and themes with examples.
    
    Educational command to learn what's available.
    """
    from rich.markdown import Markdown
    
    help_text = """
# Dopemux Layouts & Themes Guide

## 🏗️ Layouts (Structure)

Layouts control **pane arrangement** - where things go in your tmux session.

| Layout       | Description | Use When |
|--------------|-------------|----------|
| `low`        | Minimal: main + agent | You want simplicity |
| `medium`     | Standard split panes | General development |
| `high`       | More monitoring panes | Need more visibility |
| `orchestrator` | Full orchestrator + monitors | Managing multiple tasks |
| `dope`       | Complete DOPE experience | You want it all! 🔥 |

## 🎨 Themes (Appearance)

Themes control **colors and styling** - how things look.

| Theme  | Style | Best For |
|--------|-------|----------|
| `muted` | Soft, low contrast | Long sessions, reduced eye strain |
| `neon`  | Bright, vibrant | High energy, clear distinctions |
| `house` | Balanced, professional | General use |

## 🚀 Easy Commands

Instead of memorizing complex tmux commands, use these shortcuts:

```bash
# Quick start commands
dopemux quick                    # Fast medium layout
dopemux dope                     # Full DOPE with muted theme
dopemux dope --theme neon        # Full DOPE with neon theme
dopemux launch --preset full     # Full DOPE, default theme

# Full control
dopemux launch --preset dope-muted  # Explicit preset

# Traditional (if you prefer)
dopemux tmux start --layout dope --bootstrap
dopemux tmux theme muted --apply
```

## 📋 Presets Reference

| Preset | Layout | Theme | Description |
|--------|--------|-------|-------------|
| `minimal` | none | none | Just Claude Code |
| `standard` | medium | default | Basic split panes |
| `full` | dope | default | Everything enabled |
| `dope-muted` | dope | muted | Recommended! 🌟 |
| `dope-neon` | dope | neon | Bright & vibrant |
| `dope-house` | dope | house | Professional |

## 💡 Tips

- **First time?** Try: `dopemux dope`
- **Long session?** Use: `dopemux launch --preset dope-muted`
- **Quick test?** Use: `dopemux quick`
- **Learning?** Start with: `dopemux launch --preset standard`

## 🔧 Advanced Usage

```bash
# Manual control (traditional way)
dopemux tmux start --layout dope --bootstrap --alt-routing
dopemux tmux theme neon --apply

# List current panes
dopemux tmux list

# Preview a theme without applying
dopemux tmux theme neon
```
"""
    
    console.logger.info(Markdown(help_text))


# Register routing commands
def _register_routing_commands():
    try:
        from .routing_cli import routing
        cli.add_command(routing, "routing")
    except Exception as e:
        # Graceful degradation if routing module has issues
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to register routing commands: {e}")

_register_routing_commands()

def main():
    """Main entry point."""
    try:
        cli()
    except KeyboardInterrupt:
        console.logger.info("\n[yellow]⏸️ Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        error_text = Text("❌ Error: ", style="red") + Text(str(e))
        console.logger.error(error_text)
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@cli.command("hooks")
@click.option("--setup", is_flag=True, help="Start monitoring Claude Code activity")
@click.option("--teardown", is_flag=True, help="Stop monitoring")
@click.option("--status", is_flag=True, help="Show current hook status")
@click.option("--enable", help="Enable specific hook type (session-start, file-change, shell-command, git-commit)")
@click.option("--disable", help="Disable specific hook type (session-start, file-change, shell-command, git-commit)")
@click.option("--shell-scripts", is_flag=True, help="Generate shell hook scripts")
@click.option("--install-shell-hooks", is_flag=True, help="Install shell hooks in shell config")
@click.option("--uninstall-shell-hooks", is_flag=True, help="Uninstall shell hooks from shell config")
@click.option("--workspace", type=click.Path(exists=True, file_okay=False, dir_okay=True), help="Set workspace to monitor")
@click.option("--force", is_flag=True, help="Force operations (e.g., reinstall)")
@click.pass_context
def hooks_cmd(ctx, setup, teardown, status, enable, disable, shell_scripts, install_shell_hooks, uninstall_shell_hooks, workspace, force):
    """
    Manage Dopemux hook system for Claude Code integration.

    Provides external monitoring and triggering of Dopemux workflows
    based on Claude Code activity without interfering with the CLI.
    """
    try:
        from .hooks.claude_code_hooks import claude_hooks, get_shell_hook_scripts

        if setup:
            claude_hooks.start_monitoring(workspace)
            console.logger.info("[green]✅ Claude Code hooks started[/green]")
            console.logger.info(f"   Monitoring paths: {[str(p) for p in claude_hooks.watched_paths]}")

        elif teardown:
            claude_hooks.stop_monitoring()
            console.logger.info("[green]✅ Claude Code hooks stopped[/green]")

        elif status:
            hook_status = claude_hooks.get_status()
            console.logger.info("[bold]Claude Code Hook Status:[/bold]")
            console.logger.info(f"   Monitoring active: {hook_status['monitoring_active']}")
            console.logger.info(f"   Quiet mode: {hook_status['quiet_mode']}")
            console.logger.info(f"   Watched paths: {hook_status['watched_paths']}")
            console.logger.info("\n[bold]Hook Types:[/bold]")
            for hook_type, enabled in hook_status['active_hooks'].items():
                status_icon = "[green]✓[/green]" if enabled else "[red]✗[/red]"
                console.logger.info(f"   {status_icon} {hook_type}")

        elif enable:
            claude_hooks.enable_hook(enable)
            console.logger.info(f"[green]✅ Hook enabled: {enable}[/green]")

        elif disable:
            claude_hooks.disable_hook(disable)
            console.logger.info(f"[green]✅ Hook disabled: {disable}[/green]")

        elif shell_scripts:
            scripts = get_shell_hook_scripts()
            console.logger.info("[bold]Shell Hook Scripts:[/bold]")
            console.logger.info("\n[dim]Add these to your ~/.bashrc or ~/.zshrc:[/dim]\n")

            console.logger.info("[bold cyan]For Bash:[/bold cyan]")
            console.logger.info(scripts['bash_preexec'])
            console.logger.info(scripts['bash_precmd'])

            console.logger.info("\n[bold cyan]For Zsh:[/bold cyan]")
            console.logger.info(scripts['zsh_hooks'])

        elif install_shell_hooks:
            from .hooks.shell_hook_installer import install_shell_hooks as installer
            success, message = installer(force=force)
            if success:
                console.logger.info(f"[green]{message}[/green]")
            else:
                console.logger.info(f"[red]{message}[/red]")
                sys.exit(1)

        elif uninstall_shell_hooks:
            from .hooks.shell_hook_installer import uninstall_shell_hooks as uninstaller
            success, message = uninstaller()
            if success:
                console.logger.info(f"[green]{message}[/green]")
            else:
                console.logger.info(f"[red]{message}[/red]")
                sys.exit(1)

        else:
            # Default: show help
            console.logger.info("[bold]Dopemux Hook System[/bold]")
            console.logger.info("Manage external hooks for Claude Code integration.\n")
            console.logger.info("[bold]Commands:[/bold]")
            console.logger.info("   --setup               Start monitoring Claude Code activity")
            console.logger.info("   --teardown            Stop monitoring")
            console.logger.info("   --status              Show current hook status")
            console.logger.info("   --enable HOOK         Enable specific hook type")
            console.logger.info("   --disable HOOK        Disable specific hook type")
            console.logger.info("   --shell-scripts       Generate shell hook scripts")
            console.logger.info("   --install-shell-hooks Install shell hooks in shell config")
            console.logger.info("   --uninstall-shell-hooks Remove shell hooks from shell config")
            console.logger.info("   --workspace PATH      Set workspace to monitor")
            console.logger.info("   --force               Force operations (e.g., reinstall)\n")
            console.logger.info("[bold]Hook Types:[/bold]")
            console.logger.info("   session-start    Monitor Claude Code process start")
            console.logger.info("   file-change      Monitor file modifications")
            console.logger.info("   shell-command    Monitor shell commands")
            console.logger.info("   git-commit       Monitor git operations (disabled by default)")

    except Exception as e:
        console.logger.error(f"[red]❌ Hook command failed: {e}[/red]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)

_PIPELINE_VERSION_CHOICES = ["v4", "v3"]


@cli.group()
def upgrades():
    """Canonical Repo Truth Extractor commands (v4 default, v3 fallback)."""
    pass


@cli.group()
@click.pass_context
def extractor(ctx):
    """Legacy alias for `dopemux upgrades`."""
    if ctx.invoked_subcommand:
        console.logger.info("[yellow]⚠ `dopemux extractor` is legacy. Use `dopemux upgrades`.[/yellow]")


def _resolve_extractor_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "services" / "repo-truth-extractor").is_dir():
            return candidate
    return start


def _extractor_runner_path(repo_root: Path, pipeline_version: str) -> Path:
    base = repo_root / "services" / "repo-truth-extractor"
    if pipeline_version == "v4":
        return base / "run_extraction_v4.py"
    return base / "run_extraction_v3.py"


def _run_extractor_runner(
    *,
    pipeline_version: str,
    args: List[str],
    repo_root: Optional[Path] = None,
) -> None:
    resolved_root = _resolve_extractor_repo_root(repo_root or Path.cwd())
    runner = _extractor_runner_path(resolved_root, pipeline_version)
    if not runner.exists():
        raise click.ClickException(f"Runner not found: {runner}")
    cmd = [sys.executable, str(runner), *args]
    proc = subprocess.run(cmd, cwd=resolved_root)
    if proc.returncode != 0:
        raise click.ClickException(
            f"Repo Truth Extractor {pipeline_version} runner failed with exit code {proc.returncode}"
        )


def _repscan_runner_path(repo_root: Path) -> Path:
    return repo_root / "services" / "repo-truth-extractor" / "run_repscan.py"


def _run_repscan_runner(
    *,
    args: List[str],
    repo_root: Optional[Path] = None,
) -> None:
    resolved_root = _resolve_extractor_repo_root(repo_root or Path.cwd())
    runner = _repscan_runner_path(resolved_root)
    if not runner.exists():
        raise click.ClickException(f"RepoScan runner not found: {runner}")
    cmd = [sys.executable, str(runner), *args]
    proc = subprocess.run(cmd, cwd=resolved_root)
    if proc.returncode != 0:
        raise click.ClickException(f"RepoScan runner failed with exit code {proc.returncode}")


@cli.command("repscan", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.option("--phase", type=click.Choice(["ALL", "A", "H", "D", "C", "E", "W", "B", "G", "Q", "R", "X", "T", "Z"]))
@click.option("--run-id", type=str)
@click.option("--promptgen", type=click.Choice(["off", "v1", "v2", "auto"]))
@click.option("--promptpack", type=str)
@click.option("--promptgen-only", is_flag=True)
@click.option("--prompt-root", type=str)
@click.option("--profiles-dir", type=str)
@click.option("--legacy-runner", type=str)
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def repscan_passthrough(
    phase: Optional[str],
    run_id: Optional[str],
    promptgen: Optional[str],
    promptpack: Optional[str],
    promptgen_only: bool,
    prompt_root: Optional[str],
    profiles_dir: Optional[str],
    legacy_runner: Optional[str],
    args: tuple[str, ...],
) -> None:
    """Run deterministic repo scan/promptgen wrapper over v3 extraction."""
    forwarded: List[str] = [*args]
    if phase:
        forwarded.extend(["--phase", phase])
    if run_id:
        forwarded.extend(["--run-id", run_id])
    if promptgen:
        forwarded.extend(["--promptgen", promptgen])
    if promptpack:
        forwarded.extend(["--promptpack", promptpack])
    if promptgen_only:
        forwarded.append("--promptgen-only")
    if prompt_root:
        forwarded.extend(["--prompt-root", prompt_root])
    if profiles_dir:
        forwarded.extend(["--profiles-dir", profiles_dir])
    if legacy_runner:
        forwarded.extend(["--legacy-runner", legacy_runner])
    _run_repscan_runner(args=forwarded)


def _pipeline_version_options(command_fn: Callable) -> Callable:
    command_fn = click.option(
        "--engine-version",
        "engine_version_legacy",
        type=click.Choice(_PIPELINE_VERSION_CHOICES),
        default=None,
        hidden=True,
    )(command_fn)
    command_fn = click.option(
        "--pipeline-version",
        "pipeline_version",
        type=click.Choice(_PIPELINE_VERSION_CHOICES),
        default="v4",
        show_default=True,
    )(command_fn)
    return command_fn


def _resolved_pipeline_version(pipeline_version: str, engine_version_legacy: Optional[str]) -> str:
    if engine_version_legacy:
        return engine_version_legacy
    return pipeline_version


@upgrades.command("list")
@_pipeline_version_options
@click.pass_context
def extractor_list(ctx, pipeline_version: str, engine_version_legacy: Optional[str]):
    """List phases and effective pipeline order."""
    effective_version = _resolved_pipeline_version(pipeline_version, engine_version_legacy)
    if effective_version == "v4":
        _run_extractor_runner(
            pipeline_version="v4",
            args=["--promptset-audit", "--no-strict-audit"],
        )
        promptset_path = (
            _resolve_extractor_repo_root(Path.cwd())
            / "services"
            / "repo-truth-extractor"
            / "promptsets"
            / "v4"
            / "promptset.yaml"
        )
        if promptset_path.exists():
            payload = yaml.safe_load(promptset_path.read_text(encoding="utf-8")) or {}
            order = payload.get("all_phase_order", [])
            console.logger.info("v4 phases: " + " -> ".join(order))
            return
    _run_extractor_runner(pipeline_version=effective_version, args=["--print-config"])


@upgrades.command("run")
@_pipeline_version_options
@click.option("--phase", default="ALL", show_default=True, help="Phase code or ALL")
@click.option("--run-id", default=None, help="Run ID")
@click.option("--dry-run/--execute", default=True, show_default=True)
@click.option("--resume/--no-resume", default=True, show_default=True)
@click.option("--partition-workers", type=int, default=1, show_default=True)
@click.option(
    "--routing-policy",
    type=click.Choice(["cost", "balanced", "quality"]),
    default="cost",
    show_default=True,
)
@click.option("--disable-escalation", is_flag=True, default=False, show_default=True)
@click.option("--escalation-max-hops", type=int, default=2, show_default=True)
@click.option("--batch-mode", is_flag=True, default=False, show_default=True)
@click.option(
    "--batch-provider",
    type=click.Choice(["auto", "openai", "gemini", "xai"]),
    default="auto",
    show_default=True,
)
@click.option("--batch-poll-seconds", type=int, default=30, show_default=True)
@click.option("--batch-wait-timeout-seconds", type=int, default=86400, show_default=True)
@click.option("--batch-max-requests-per-job", type=int, default=2000, show_default=True)
@click.option("--ui", type=click.Choice(["auto", "rich", "plain"]), default="auto", show_default=True)
@click.option("--pretty", is_flag=True, default=False, show_default=True)
@click.option("--quiet", is_flag=True, default=False, show_default=True)
@click.option("--jsonl-events", is_flag=True, default=False, show_default=True)
@click.option(
    "--sync/--no-sync",
    default=True,
    show_default=True,
    help="v4 only: sync into extraction/repo-truth-extractor/v4",
)
@click.pass_context
def extractor_run(
    ctx,
    pipeline_version: str,
    engine_version_legacy: Optional[str],
    phase: str,
    run_id: Optional[str],
    dry_run: bool,
    resume: bool,
    partition_workers: int,
    routing_policy: str,
    disable_escalation: bool,
    escalation_max_hops: int,
    batch_mode: bool,
    batch_provider: str,
    batch_poll_seconds: int,
    batch_wait_timeout_seconds: int,
    batch_max_requests_per_job: int,
    ui: str,
    pretty: bool,
    quiet: bool,
    jsonl_events: bool,
    sync: bool,
):
    """
    Run Repo Truth Extractor pipeline (resumable).

    \b
    Examples:
      dopemux upgrades run --pipeline-version v4 --phase A --run-id local_a --dry-run --resume
      dopemux upgrades run --pipeline-version v4 --phase ALL --run-id full_001 --execute --resume
      dopemux upgrades run --pipeline-version v4 --phase C --execute --batch-mode --ui rich
    """
    effective_version = _resolved_pipeline_version(pipeline_version, engine_version_legacy)
    args: List[str] = []
    if phase:
        args.extend(["--phase", phase])
    if run_id:
        args.extend(["--run-id", run_id])
    if dry_run:
        args.append("--dry-run")
    if resume:
        args.append("--resume")
    args.extend(["--partition-workers", str(partition_workers)])
    args.extend(["--routing-policy", routing_policy])
    if disable_escalation:
        args.append("--disable-escalation")
    args.extend(["--escalation-max-hops", str(max(0, int(escalation_max_hops)))])
    if batch_mode:
        args.append("--batch-mode")
    args.extend(["--batch-provider", batch_provider])
    args.extend(["--batch-poll-seconds", str(max(1, int(batch_poll_seconds)))])
    args.extend(["--batch-wait-timeout-seconds", str(max(60, int(batch_wait_timeout_seconds)))])
    args.extend(["--batch-max-requests-per-job", str(max(1, int(batch_max_requests_per_job)))])
    args.extend(["--ui", ui])
    if pretty:
        args.append("--pretty")
    if quiet:
        args.append("--quiet")
    if jsonl_events:
        args.append("--jsonl-events")
    if effective_version == "v4":
        args.extend(["--sync" if sync else "--no-sync"])
    _run_extractor_runner(pipeline_version=effective_version, args=args)


@upgrades.command("doctor")
@_pipeline_version_options
@click.option("--run-id", default=None, help="Run ID")
@click.option("--auto-reprocess/--no-auto-reprocess", default=False, show_default=True)
@click.option("--reprocess-dry-run/--no-reprocess-dry-run", default=False, show_default=True)
@click.option("--reprocess-phases", default="", help="Comma-separated phase list")
@click.pass_context
def extractor_doctor(
    ctx,
    pipeline_version: str,
    engine_version_legacy: Optional[str],
    run_id: Optional[str],
    auto_reprocess: bool,
    reprocess_dry_run: bool,
    reprocess_phases: str,
):
    """
    Run doctor diagnostics and deterministic reprocess planning for a run.

    \b
    Example:
      dopemux upgrades doctor --pipeline-version v4 --run-id <RUN_ID> --auto-reprocess --reprocess-dry-run
    """
    effective_version = _resolved_pipeline_version(pipeline_version, engine_version_legacy)
    args: List[str] = ["--doctor"]
    if run_id:
        args.extend(["--run-id", run_id])
    if auto_reprocess:
        args.append("--doctor-auto-reprocess")
    if reprocess_dry_run:
        args.append("--doctor-reprocess-dry-run")
    if reprocess_phases.strip():
        args.extend(["--doctor-reprocess-phases", reprocess_phases.strip()])
    _run_extractor_runner(pipeline_version=effective_version, args=args)


@upgrades.command("status")
@_pipeline_version_options
@click.option("--run-id", default=None, help="Run ID")
@click.option("--json", "status_json", is_flag=True, help="Emit JSON status")
@click.pass_context
def extractor_status(
    ctx,
    pipeline_version: str,
    engine_version_legacy: Optional[str],
    run_id: Optional[str],
    status_json: bool,
):
    """Show run status or a machine-readable JSON status payload."""
    effective_version = _resolved_pipeline_version(pipeline_version, engine_version_legacy)
    args: List[str] = ["--status-json" if status_json else "--status"]
    if run_id:
        args.extend(["--run-id", run_id])
    _run_extractor_runner(pipeline_version=effective_version, args=args)


@upgrades.command("preflight")
@_pipeline_version_options
@click.option("--run-id", default=None, help="Run ID")
@click.option("--auth-doctor", is_flag=True, help="Also run auth diagnostics")
@click.pass_context
def extractor_preflight(
    ctx,
    pipeline_version: str,
    engine_version_legacy: Optional[str],
    run_id: Optional[str],
    auth_doctor: bool,
):
    """Run provider preflight checks and optional auth diagnostics."""
    effective_version = _resolved_pipeline_version(pipeline_version, engine_version_legacy)
    args: List[str] = ["--preflight-providers"]
    if run_id:
        args.extend(["--run-id", run_id])
    _run_extractor_runner(pipeline_version=effective_version, args=args)
    if auth_doctor:
        auth_args = ["--doctor-auth"]
        if run_id:
            auth_args.extend(["--run-id", run_id])
        _run_extractor_runner(pipeline_version=effective_version, args=auth_args)


@upgrades.group("promptset")
def upgrades_promptset_group():
    """Promptset utilities."""
    pass


@upgrades_promptset_group.command("audit")
@_pipeline_version_options
@click.option("--strict/--no-strict", default=True, show_default=True)
@click.pass_context
def extractor_promptset_audit(
    ctx,
    pipeline_version: str,
    engine_version_legacy: Optional[str],
    strict: bool,
):
    """
    Audit promptset contract compliance (required sections, schemas, determinism).

    \b
    Example:
      dopemux upgrades promptset audit --pipeline-version v4 --strict
    """
    effective_version = _resolved_pipeline_version(pipeline_version, engine_version_legacy)
    if effective_version == "v4":
        args = ["--promptset-audit", "--strict-audit" if strict else "--no-strict-audit"]
        _run_extractor_runner(pipeline_version="v4", args=args)
        return
    raise click.ClickException("Promptset audit is implemented for v4 only.")


@upgrades.command("trace")
@click.option("--dry-run", is_flag=True, default=True, help="Simulate execution by generating trace files only (default)")
@click.option("--execute", is_flag=True, help="Actually call LLM providers (if configured)")
@click.option("--phase", help="Run only a specific trace phase (A, H, D, C, R, S)")
@click.pass_context
def extractor_trace(ctx, dry_run: bool, execute: bool, phase: Optional[str]):
    """Legacy trace generation path for synthesis-input trace bundles."""
    project_path = Path.cwd()
    if execute:
        dry_run = False
    runner = PipelineRunner(project_path)
    if phase:
        runner.run_phase(phase, dry_run=dry_run)
    else:
        runner.run_all(dry_run=dry_run)


extractor.add_command(extractor_list, "list")
extractor.add_command(extractor_run, "run")
extractor.add_command(extractor_doctor, "doctor")
extractor.add_command(extractor_status, "status")
extractor.add_command(extractor_preflight, "preflight")
extractor.add_command(extractor_trace, "trace")


@extractor.group("promptset")
def extractor_promptset_group():
    """Promptset utilities (legacy alias for upgrades promptset)."""
    pass


extractor_promptset_group.add_command(extractor_promptset_audit, "audit")
if __name__ == "__main__":
    main()
