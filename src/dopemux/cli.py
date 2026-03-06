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
        logger.error(f"Error launching Claude Code: {e}")
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
@click.option(
    "--no-routing-repair",
    is_flag=True,
    help="Disable automatic routing repair loop (health check only)",
)
@click.option(
    "--routing-repair-max",
    type=int,
    default=3,
    help="Maximum number of repair attempts (default: 3)",
)
@click.option(
    "--routing-repair-no-sync-keys",
    is_flag=True,
    help="Do not attempt API key syncing during repair (default: no sync)",
)
@click.option(
    "--routing-fallback-subscription",
    is_flag=True,
    help="Fall back to subscription mode if routing repair fails (opt-in)",
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
    no_routing_repair: bool,
    routing_repair_max: int,
    routing_repair_no_sync_keys: bool,
    routing_fallback_subscription: bool,
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
    global RoutingConfig
    provider = None
    
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
        
        # Run health check and repair if needed
        try:
            from .launchd_services import LaunchdServiceManager
            service_manager = LaunchdServiceManager.get_instance()
            
            # Check health first
            console.logger.info("[blue]🏥 Checking routing service health...[/blue]")
            health = service_manager.check_health()
            
            # Check if services are healthy
            litellm_healthy = health.get("litellm", {}).get("status") == "healthy"
            ccr_healthy = health.get("ccr", {}).get("status") == "healthy"
            
            if litellm_healthy and ccr_healthy:
                console.logger.info("[green]✅ Routing services healthy[/green]")
            else:
                # Services are unhealthy - attempt repair
                if no_routing_repair:
                    console.logger.info("[yellow]⚠️  Routing services unhealthy, repair disabled[/yellow]")
                    error_msg = []
                    if not litellm_healthy:
                        error_msg.append(f"LiteLLM: {health.get('litellm', {}).get('error', 'unhealthy')}")
                    if not ccr_healthy:
                        error_msg.append(f"CCR: {health.get('ccr', {}).get('error', 'unhealthy')}")
                    raise click.ClickException(f"Routing services unhealthy: {', '.join(error_msg)}")
                
                console.logger.info("[yellow]⚠️  Routing services unhealthy - attempting repair[/yellow]")
                
                # Run repair loop
                allow_sync_keys = not routing_repair_no_sync_keys
                repair_result = service_manager.repair(
                    max_passes=routing_repair_max,
                    allow_sync_keys=allow_sync_keys
                )
                
                # Check if repair was successful
                if repair_result.get("healthy", False):
                    console.logger.info("[green]✅ Routing services repaired successfully[/green]")
                    health = repair_result["health"]
                    litellm_healthy = True
                    ccr_healthy = True
                else:
                    # Repair failed - provide diagnostics
                    console.logger.error("[red]❌ Failed to repair routing services[/red]")
                    
                    # Show repair attempts
                    console.logger.info("[yellow]Repair attempts:[/yellow]")
                    for attempt in repair_result.get("attempts", []):
                        console.logger.info(f"  Pass {attempt['pass']}: {attempt['action']}")
                    
                    # Show log paths
                    log_paths = service_manager._get_log_paths()
                    console.logger.info("[yellow]Check logs for details:[/yellow]")
                    console.logger.info(f"  LiteLLM launchd: {log_paths['litellm_launchd']}")
                    console.logger.info(f"  CCR launchd: {log_paths['ccr_launchd']}")
                    console.logger.info(f"  LiteLLM latest: {log_paths['litellm_latest']}")
                    
                    # Show diagnostic commands
                    console.logger.info("[yellow]Diagnostic commands:[/yellow]")
                    console.logger.info("  dopemux routing health")
                    console.logger.info("  dopemux routing status")
                    console.logger.info("  tail -f ~/.dopemux/logs/litellm_launchd.log")
                    
                    # Determine if we should fall back to subscription mode
                    if routing_fallback_subscription:
                        console.logger.info("[yellow]🔄 Falling back to subscription mode as requested[/yellow]")
                        routing_mode = "subscription"
                        _ensure_env_consistent_with_mode(routing_mode)
                    else:
                        error_msg = []
                        if not litellm_healthy:
                            error_msg.append(f"LiteLLM: {health.get('litellm', {}).get('error', 'unhealthy')}")
                        if not ccr_healthy:
                            error_msg.append(f"CCR: {health.get('ccr', {}).get('error', 'unhealthy')}")
                        raise click.ClickException(f"Routing services unhealthy after repair: {', '.join(error_msg)}")
            
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
                from .routing_config import RoutingConfig
                routing_config = RoutingConfig.load_default()
                current_routing_mode = routing_config.get_mode()
            except Exception:
                pass

            if current_routing_mode != "api":
                console.logger.warning("[yellow]⚠️  --altp flag ignored in subscription mode[/yellow]")
                console.logger.info("[dim]   Use 'dopemux routing mode api' to enable proxy routing[/dim]")
                # Disable proxy usage for this branch
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

            if use_altp:
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
        elif provider:
            os.environ["CLAUDE_CODE_ROUTER_MODELS"] = provider["name"]

        use_litellm = True
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
            _start_mcp_servers_with_progress(project_path, instance_id=instance_id or "A", instance_env=instance_env_vars)
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


from .commands.instances_commands import instances
cli.add_command(instances, "instances")



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


from .commands.kernel_commands import kernel
cli.add_command(kernel)


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


from .commands.autoresponder_commands import autoresponder
cli.add_command(autoresponder)



from .commands.extract_commands import extract
cli.add_command(extract, "extract")



from .commands.update_commands import update
cli.add_command(update)


from .commands.profile_commands import profile
cli.add_command(profile)
try:
    from .profile_commands import use_profile as _use_profile
    cli.add_command(_use_profile, "switch")
except ImportError:
    pass


from .commands.decisions_commands import decisions
cli.add_command(decisions)


from .commands.dev_commands import dev
cli.add_command(dev)
cli.add_command(mobile_commands, "mobile")
cli.add_command(mobile_env_commands, "mobile-env")
if genetic_group:
    cli.add_command(genetic_group, "genetic")


from .commands.code_commands import code
cli.add_command(code)
cli.add_command(tmux_commands, "tmux")
from .claude_tools.cli import register_commands
register_commands(cli)


from .commands.memory_commands import memory
cli.add_command(memory)


from .commands.trigger_group_commands import trigger_group
cli.add_command(trigger_group, "trigger")


from .commands.capture_group_commands import capture_group
cli.add_command(capture_group, "capture")


from .commands.workflow_group_commands import workflow_group
cli.add_command(workflow_group, "workflow")


from .commands.upgrades_commands import upgrades
cli.add_command(upgrades)


from .commands.extractor_commands import extractor, _run_extractor_runner, _run_repscan_runner
cli.add_command(extractor)



# ============================================================
# Commands extracted back from submodules (use @cli.command)
# ============================================================

# from src/dopemux/commands/extract_commands.py
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


from .commands.mcp_commands import mcp, servers
cli.add_command(mcp)
cli.add_command(servers)



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
    Resolve MCP stack directory using MCPProvisioner.
    Auto-provisions if missing.
    """
    from .mcp.provision import MCPProvisioner
    
    provisioner = MCPProvisioner(project_path)
    try:
        return provisioner.ensure_stack_present()
    except Exception as e:
        console.logger.error(f"[red]❌ MCP Provisioning failed: {e}[/red]")
        return None


def _start_mcp_servers_with_progress(project_path: Path, instance_id: str = "A", instance_env: Optional[dict] = None):
    """
    Start MCP servers with auto-provisioning, instance-scoped overlays, and Phase 0 gate.
    """
    if os.getenv("DOPEMUX_SKIP_MCP_START", "0").lower() in {"1", "true", "yes"}:
        console.logger.info("[yellow]⏭️ Skipping MCP server startup (DOPEMUX_SKIP_MCP_START)[/yellow]")
        return

    # 1. Provision stack if missing
    mcp_dir = _resolve_mcp_dir(project_path)
    if not mcp_dir:
        raise click.ClickException("MCP stack provisioning failed.")

    # 2. Materialize instance overlay
    from .mcp.instance_overlay import InstanceOverlayManager
    overlay_manager = InstanceOverlayManager(project_path, instance_id)
    overlay = overlay_manager.materialize()
    
    # 3. Prepare environment
    env_for_subprocess = os.environ.copy()
    if instance_env:
        env_for_subprocess.update(instance_env)
    
    # Load mcp.env values into subprocess env
    try:
        import dotenv
        env_vars = dotenv.dotenv_values(overlay["env_path"])
        env_for_subprocess.update({k: v for k, v in env_vars.items() if v is not None})
    except ImportError:
        # Fallback if python-dotenv not installed (unlikely but safe)
        pass

    console.logger.info(f"\n[bold blue]🔌 Starting MCP Servers (Instance {instance_id})[/bold blue]")
    console.logger.info(f"[dim]Project: {overlay['compose_project_name']}[/dim]")
    console.logger.info(f"[dim]Ports: PAL={overlay['port_map']['PAL']}, ConPort={overlay['port_map']['ConPort']}[/dim]\n")

    # Start docker-compose with overlay
    status_text = Text()
    status_text.append("🚀 ", style="bold blue")
    status_text.append("Launching containers...")

    startup_successful = False
    output_lines = []

    try:
        with Live(status_text, console=console, refresh_per_second=4) as live:
            # We use docker-compose with the generated override
            compose_file = mcp_dir / "compose.yml"
            if not compose_file.exists():
                # Try legacy name
                compose_file = mcp_dir / "docker-compose.yml"

            cmd = [
                "docker", "compose",
                "-f", str(compose_file),
                "-f", overlay["compose_path"],
                "--project-name", overlay["compose_project_name"],
                "up", "-d", "--remove-orphans"
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                env=env_for_subprocess,
                cwd=str(mcp_dir)
            )

            for line in process.stdout:
                line = line.strip()
                if line:
                    output_lines.append(line)
                    if len(output_lines) > 5:
                        output_lines.pop(0)
                    
                    status_text = Text()
                    status_text.append("🚀 ", style="bold blue")
                    status_text.append("Launching containers...\n")
                    for out in output_lines:
                        status_text.append(f"  [dim]{out}[/dim]\n")
                    live.update(status_text)

            process.wait()
            if process.returncode == 0:
                startup_successful = True
                status_text.append("\n✅ Containers launched!", style="bold green")
                live.update(status_text)
            else:
                status_text.append(f"\n❌ Startup failed (exit {process.returncode})", style="bold red")
                live.update(status_text)
                raise RuntimeError(f"Docker compose failed with exit code {process.returncode}")

        # 4. Phase 0 Discovery Gate
        console.logger.info("[blue]🛡️ Running Phase 0 Discovery Gate...[/blue]")
        from .mcp.gate import DiscoveryGate
        
        # We need to wait a few seconds for servers to actually start listening
        time.sleep(3)
        
        # Point the gate to use the resolved ports for this instance
        for srv_name, port in overlay["port_map"].items():
            env_var = f"DOPMUX_{srv_name.upper().replace('-', '_')}_URL"
            os.environ[env_var] = f"http://127.0.0.1:{port}/mcp" if srv_name != "LiteLLM" else f"http://127.0.0.1:{port}"

        gate = DiscoveryGate(project_path, run_id=f"start-{instance_id}-{int(time.time())}")
        if not asyncio.run(gate.run()):
            gate.print_block_report()
            raise click.ClickException("MCP Phase 0 Discovery Gate failed. Mandatory tools not available.")
        
        console.logger.info("[green]✅ Phase 0 Discovery Gate passed![/green]")

    except Exception as e:
        console.logger.error(f"[red]❌ MCP Startup failed: {e}[/red]")
        if output_lines:
            console.print("[dim]Last output lines:[/dim]")
            for line in output_lines[-10:]:
                console.print(f"  [dim]{line}[/dim]")
        raise click.ClickException(f"Failed to start MCP stack: {e}")


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


# from src/dopemux/commands/extractor_commands.py
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


_PIPELINE_VERSION_CHOICES = ["v4", "v3"]


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

# from src/dopemux/commands/memory_commands.py
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



# from src/dopemux/commands/profile_commands.py
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


# from src/dopemux/commands/workflow_group_commands.py
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


