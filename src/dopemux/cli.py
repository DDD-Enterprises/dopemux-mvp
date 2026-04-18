#!/usr/bin/env python3
"""
Dopemux CLI - ADHD-optimized development platform CLI.

Main entry point for all dopemux commands providing context preservation,
attention monitoring, and task decomposition for neurodivergent developers.
"""

import logging
import os

logger = logging.getLogger(__name__)

import shutil
import signal
import socket
import sys
import tempfile
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence

import click

from .utils.dotenv_loader import check_dotenv_support, load_dotenv

# Import RoutingConfig for mode-based behavior
try:
    from .routing_config import RoutingConfig
except ImportError:  # pragma: no cover
    RoutingConfig = None

from rich.live import Live
from dopemux.ui.progress import branded_progress
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.text import Text

from . import __version__
from .claude_tools.cli import register_commands
from .console import console
from .ui.output import emit
from .ui.theme import (
    Glyphs,
    RenderMode,
    StatusChip,
    get_render_mode,
    set_render_mode,
    styled_panel,
    styled_table,
)
from .ui.prompts import dopemux_prompt, dopemux_confirm
from .ui.voice import VoiceEngine

# Load environment variables from .env file
load_dotenv()
check_dotenv_support()
import subprocess
from subprocess import CalledProcessError
from urllib.parse import urlparse

import yaml

from .pm.writes import PMWriteConfig
from .adhd import AttentionMonitor, ContextManager, TaskDecomposer
from .claude import ClaudeConfigurator, ClaudeLauncher, InstructionManager
from .ux.launcher_wizard import start_wizard
from .claude_config import ClaudeConfig, ClaudeConfigError
from .config import ConfigManager
from .dope_brainz_router import (
    DopeBrainzRouterError,
    DopeBrainzRouterManager,
)
from .health import HealthChecker
from .instance_manager import (
    InstanceManager,
    detect_instances_sync,
    detect_orphaned_instances_sync,
)
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
from .mobile import mobile as mobile_commands
from .mobile.hooks import mobile_task_notification
from .mobile.main import main as mobile_env_commands
from .mobile.runtime import update_tmux_mobile_indicator
from .profile_manager import ProfileManager
from .profile_models import ProfileValidationError
from .profile_parser import ProfileParser
from .project_init import init_project
from .protection_interceptor import (
    check_and_protect_main,
    consume_last_created_worktree,
)
from .tmux import tmux as tmux_commands

# Import genetic agent CLI
try:
    # Ensure services directory is in Python path for production environments
    services_path = Path(__file__).resolve().parent.parent / "services"
    if str(services_path) not in sys.path:
        sys.path.insert(0, str(services_path))

    from services.genetic_agent.cli import cli as genetic_group
except ImportError:
    # Fallback if genetic agent service is not available
    genetic_group = None
from .memory.capture_client import CaptureError, emit_capture_event
from .roles.catalog import (
    RoleNotFoundError,
    activate_role,
    available_roles,
    resolve_role,
)

if "-litellm" in sys.argv:
    sys.argv = ["--litellm" if arg == "-litellm" else arg for arg in sys.argv]


from .commands._helpers import (
    ATTENTION_PROFILE_DEFAULTS,
    ROLE_SERVER_SERVICE_MAP,
    _build_router_overrides,
    _ensure_role_profile,
    _get_routing_allowlist,
    _invoke_switch_role_script,
    _load_litellm_models,
    _persist_instance_env_exports,
    _select_model_by_priority,
    _suggest_server_start,
    show_version,
)


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
        console.logger.info(
            "[success]✨ Claude Code is running (minimal mode)\n[/success]"
        )


@click.group()
@click.option(
    "--version", is_flag=True, expose_value=False, is_eager=True, callback=show_version
)
@click.option("--config", "-c", help="🔬 Path to the ritual configuration file (dopemux.toml). Defaults to searching project root or ~/.config/dopemux/.")
@click.option("--verbose", "-v", is_flag=True, help="📊 Increase verbosity of the ritual logs. Enables deep telemetry for troubleshooting the flight-deck.")
@click.option(
    "--debug-log",
    type=click.Path(path_type=Path, dir_okay=False),
    help="📜 Specify a direct telemetry line to a file for capturing all internal daemon signals.",
)
@click.option(
    "--render-mode",
    type=click.Choice(["rich", "plain", "compact", "audit"]),
    default=None,
    help="🎭 Select the HUD aesthetic. 'rich' for high-fidelity interactive feedback, 'plain' for CI/CD compatibility, 'compact' for minimal screen footprint, or 'audit' for security review.",
)
@click.option(
    "--compact",
    is_flag=True,
    help="⚡ Toggle compact HUD rendering. Minimize the visual footprint of the cockpit.",
)
@click.option(
    "--plain", is_flag=True, help="🧪 Disable ritual styling. Renders output as raw text for ingestion by other daemons."
)
@click.option(
    "--json", "json_output", is_flag=True, help="📊 Emit ritual state as JSON. Ideal for flight-data analysis or external HUD integration. Implies --plain."
)
@click.option("--no-hints", is_flag=True, help="💧 Silence the flight-deck startup tips. For experienced pilots who have mastered the ritual.")
@click.pass_context
def cli(
    ctx,
    config: Optional[str],
    verbose: bool,
    debug_log: Optional[Path],
    render_mode: Optional[str],
    compact: bool,
    plain: bool,
    json_output: bool,
    no_hints: bool,
):
    """
    🧠 DØPEMÜX - Ritual Daemon of Focused Development

    DØPEMÜX is a flight-deck for neurodivergent developers, engineered to automate
    context preservation, orchestrate attention monitoring, and decompose complex
    objectives into ritualistic tasks. This command-line interface acts as your 
    primary ritual circle, synchronizing daemon states across your workspace,
    tmux sessions, and mobile devices to ensure zero context decay.

    Invoking this daemon establishes a cockpit environment where focus is a service
    and distraction is mitigated by architectural design.
    """
    from .ui.errors import install_error_handlers
    from .ui.logging import setup_branded_logging
    import logging
    
    install_error_handlers()
    setup_branded_logging(level=logging.DEBUG if verbose else logging.INFO)
    
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config_manager"] = ConfigManager(config_path=config)
    ctx.obj["json_output"] = json_output

    # Resolve render mode from flags (priority: --json > --render-mode > --compact > --plain > env)
    if json_output:
        set_render_mode(RenderMode.PLAIN)
    elif render_mode:
        set_render_mode(RenderMode(render_mode))
    elif compact:
        set_render_mode(RenderMode.COMPACT)
    elif plain:
        set_render_mode(RenderMode.PLAIN)
    # else: auto-detect from env (default)

    # Brand banner (interactive terminals only)
    import atexit

    _voice = VoiceEngine()
    if not json_output and get_render_mode() == RenderMode.RICH and sys.stderr.isatty():
        console.print(f"[mint]{Glyphs.BRAND_MARK}[/mint]", justify="center")

        def _aftercare():
            if get_render_mode() == RenderMode.RICH:
                console.print(f"\n[violet]{_voice.get_aftercare()}[/violet]")

        atexit.register(_aftercare)

    # Startup hints (stderr, only for interactive terminals)
    if not no_hints and not json_output and sys.stderr.isatty():
        try:
            from .startup_hints import create_hint_banner

            console.print(create_hint_banner(), stderr=True)
        except Exception:
            pass  # hints are non-critical

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


from .commands.bootstrap_commands import init, wire_conport  # noqa: E402

cli.add_command(init)
cli.add_command(wire_conport, "wire-conport")



@cli.command()
@click.option("--session", "-s", help="🧪 Restore a specific temporal coordinate (Session ID) to reconstruct past context.")
@click.option("--background", "-b", is_flag=True, help="⚡ Launch the cockpit in the background as a detached ritual process.")
@click.option("--debug", is_flag=True, help="🔬 Enable high-fidelity debug output for troubleshooting the ignition sequence.")
@click.option(
    "--dangerous",
    is_flag=True,
    help="⚠️  UNRESTRICTED ACCESS: Disables all tool-use approval rituals. USE WITH EXTREME CAUTION.",
)
@click.option(
    "--dangerously-skip-permissions",
    is_flag=True,
    help="⚠️  Bypass all permission gates. Identical to --dangerous.",
)
@click.option(
    "--no-mcp",
    is_flag=True,
    help="💧 Disable MCP server synchronization. Reduces cockpit capabilities (not recommended).",
)
@click.option(
    "--no-recovery",
    is_flag=True,
    help="⚡ Skip the orphan worktree recovery ritual and continue at current coordinates.",
)
@click.option(
    "--litellm",
    "use_litellm",
    is_flag=True,
    help="🧠 Route all cognitive traffic through the LiteLLM proxy for enhanced routing control.",
)
@click.option(
    "--alt-routing",
    "use_alt_routing",
    is_flag=True,
    help="🚀 Engage automatic alternative provider routing (OpenRouter, xAI, Minimax).",
)
@click.option(
    "--claude-router/--no-claude-router",
    "use_claude_router",
    default=False,  # Changed to False - OAuth-first design (no routing needed)
    help="⚡ Synchronize with the Claude Code Router (CCR) for instance-local routing.",
)
@click.option(
    "--role",
    "-r",
    help="🎭 Assume a specific ritual persona (e.g., quickfix, plan, research, orchestrator) to tune cognitive output.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="📊 Preview the ritual sequence and profile effects without committing to ignition.",
)
@click.option(
    "--grok",
    "use_grok",
    is_flag=True,
    help="🎯 Direct all cognitive requests to xAI Grok Code Fast 1.",
)
@click.option(
    "--codex",
    "use_codex",
    is_flag=True,
    help="🎯 Direct all cognitive requests to OpenAI GPT-5 Codex via OpenRouter.",
)
@click.option(
    "--altp",
    "use_altp",
    is_flag=True,
    help="🎯 Engage tier-matched routing (Opus → Codex, Sonnet → GPT-5-Mini, Haiku → Grok).",
)
@click.option(
    "--no-routing-repair",
    is_flag=True,
    help="🔬 Disable automatic routing health checks and repair sequences.",
)
@click.option(
    "--routing-repair-max",
    type=int,
    default=3,
    help="⚡ Maximum number of repair ritual attempts before abandoning the uplink.",
)
@click.option(
    "--routing-repair-no-sync-keys",
    is_flag=True,
    help="💧 Skip API key synchronization during the routing repair ritual.",
)
@click.option(
    "--routing-fallback-subscription",
    is_flag=True,
    help="🔄 Fall back to direct Anthropic subscription if routing repair fails.",
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
    ⚡ Ignition: Launch the DØPEMÜX Cockpit

    Initiates the primary ritual sequence, launching the Claude Code cognitive 
    engine within an ADHD-optimized cockpit. This command synchronizes active 
    MCP servers, restores temporal context from previous sessions, and engages 
    the attention monitor daemon to shield your focus.

    Flight-Deck Capabilities:
    - Context Reconstruction: Automatically resumes where the last ritual ended.
    - Instance Multiplexing: Detects active cockpits and provisions isolated 
      worktrees for parallel feature execution.
    - Routing Logic: Manages uplinks through LiteLLM, Claude Code Router (CCR), 
      and alternative providers (Grok, Codex).
    """
    from .ui.splash import boot_sequence
    boot_sequence()
    
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

    from .agent_validator import validate_agents_in_workspace
    from .workspace_utils import get_workspace_root

    # Preflight: Validate and fix agents
    try:
        workspace_root = get_workspace_root()
        project_path = Path(workspace_root) if workspace_root else Path.cwd()
        if workspace_root:
            validate_agents_in_workspace(workspace_root)
    except Exception as e:
        console.logger.warning(f"Agent validation warning: {e}")
        project_path = Path.cwd()

    # ── Routing mode from config (replaces legacy flags) ───────────────
    routing_mode = None
    routing_ports = None
    routing_config = None

    if RoutingConfig is not None:
        try:
            routing_config = RoutingConfig.load_default()
            routing_mode = routing_config.get_mode()
            routing_ports = routing_config.get_ports()
            console.logger.info(f"[info]📋 Routing mode: {routing_mode}[/info]")
        except Exception as e:
            console.logger.warning(
                f"[warning]⚠️  Could not load routing config: {e}[/warning]"
            )
            console.logger.info(
                "[text.dim]Falling back to legacy flag behavior[/text.dim]"
            )

    # Warn about deprecated flags when routing mode is available
    deprecated_flags_used = any(
        [use_grok, use_codex, use_altp, use_alt_routing, use_claude_router]
    )
    if deprecated_flags_used and routing_mode is not None:
        console.logger.warning(
            "[warning]⚠️  Deprecated flags detected (--grok/--codex/--altp/--alt-routing/--claude-router)[/warning]"
        )
        console.logger.info(
            "[text.dim]Prefer: dopemux routing mode api|subscription[/text.dim]"
        )

    # Check if provider flags were disabled due to subscription mode
    if not (use_grok or use_codex or use_altp or use_litellm) and (
        original_grok or original_codex or original_altp or original_litellm
    ):
        console.logger.info(
            "[info]📋 Using direct Anthropic connection (subscription mode)[/info]"
        )

    # ── Handle routing mode: api (proxy through CCR/LiteLLM) ─────────
    if routing_mode == "api" and not deprecated_flags_used:
        console.logger.info(
            "[info]🔄 Routing mode 'api': Starting services and configuring proxy[/info]"
        )

        # Run health check and repair if needed
        try:
            from .launchd_services import LaunchdServiceManager

            service_manager = LaunchdServiceManager.get_instance()

            # Check health first
            console.logger.info("[info]🏥 Checking routing service health...[/info]")
            health = service_manager.check_health()

            # Check if services are healthy
            litellm_healthy = health.get("litellm", {}).get("status") == "healthy"
            ccr_healthy = health.get("ccr", {}).get("status") == "healthy"

            if litellm_healthy and ccr_healthy:
                console.logger.info("[success]✅ Routing services healthy[/success]")
            else:
                # Services are unhealthy - attempt repair
                if no_routing_repair:
                    console.logger.info(
                        "[warning]⚠️  Routing services unhealthy, repair disabled[/warning]"
                    )
                    error_msg = []
                    if not litellm_healthy:
                        error_msg.append(
                            f"LiteLLM: {health.get('litellm', {}).get('error', 'unhealthy')}"
                        )
                    if not ccr_healthy:
                        error_msg.append(
                            f"CCR: {health.get('ccr', {}).get('error', 'unhealthy')}"
                        )
                    raise click.ClickException(
                        f"Routing services unhealthy: {', '.join(error_msg)}"
                    )

                console.logger.info(
                    "[warning]⚠️  Routing services unhealthy - attempting repair[/warning]"
                )

                # Run repair loop
                allow_sync_keys = not routing_repair_no_sync_keys
                repair_result = service_manager.repair(
                    max_passes=routing_repair_max, allow_sync_keys=allow_sync_keys
                )

                # Check if repair was successful
                if repair_result.get("healthy", False):
                    console.logger.info(
                        "[success]✅ Routing services repaired successfully[/success]"
                    )
                    health = repair_result["health"]
                    litellm_healthy = True
                    ccr_healthy = True
                else:
                    # Repair failed - provide diagnostics
                    console.logger.error(
                        "[error]❌ Failed to repair routing services[/error]"
                    )

                    # Show repair attempts
                    console.logger.info("[warning]Repair attempts:[/warning]")
                    for attempt in repair_result.get("attempts", []):
                        console.logger.info(
                            f"  Pass {attempt['pass']}: {attempt['action']}"
                        )

                    # Show log paths
                    log_paths = service_manager._get_log_paths()
                    console.logger.info("[warning]Check logs for details:[/warning]")
                    console.logger.info(
                        f"  LiteLLM launchd: {log_paths['litellm_launchd']}"
                    )
                    console.logger.info(f"  CCR launchd: {log_paths['ccr_launchd']}")
                    console.logger.info(
                        f"  LiteLLM latest: {log_paths['litellm_latest']}"
                    )

                    # Show diagnostic commands
                    console.logger.info("[warning]Diagnostic commands:[/warning]")
                    console.logger.info("  dopemux routing health")
                    console.logger.info("  dopemux routing status")
                    console.logger.info("  tail -f ~/.dopemux/logs/litellm_launchd.log")

                    # Determine if we should fall back to subscription mode
                    if routing_fallback_subscription:
                        console.logger.info(
                            "[warning]🔄 Falling back to subscription mode as requested[/warning]"
                        )
                        routing_mode = "subscription"
                        _ensure_env_consistent_with_mode(routing_mode)
                    else:
                        error_msg = []
                        if not litellm_healthy:
                            error_msg.append(
                                f"LiteLLM: {health.get('litellm', {}).get('error', 'unhealthy')}"
                            )
                        if not ccr_healthy:
                            error_msg.append(
                                f"CCR: {health.get('ccr', {}).get('error', 'unhealthy')}"
                            )
                        raise click.ClickException(
                            f"Routing services unhealthy after repair: {', '.join(error_msg)}"
                        )

        except Exception as e:
            console.logger.error(
                f"[error]❌ Failed to start routing services: {e}[/error]"
            )
            console.logger.info(
                "[warning]Falling back to direct Anthropic connection[/warning]"
            )
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
                console.logger.info(f"[text.dim]✓ CCR API key configured[/text.dim]")
            else:
                console.logger.warning(
                    "[warning]⚠️  DOPEMUX_CCR_API_KEY not set in routing.env[/warning]"
                )

            console.logger.info(
                f"[text.dim]✓ Claude Code → CCR (127.0.0.1:{ccr_port}) → LiteLLM[/text.dim]"
            )

            # Mark that we're using routing
            os.environ["DOPEMUX_ROUTING_MODE"] = "api"

    # ── Handle routing mode: subscription (direct to Anthropic) ──────
    elif routing_mode == "subscription" and not deprecated_flags_used:
        console.logger.info(
            "[info]📋 Routing mode 'subscription': Direct Anthropic connection[/info]"
        )

        # Ensure env vars are consistent with subscription mode
        _ensure_env_consistent_with_mode(routing_mode)
        console.logger.info("[text.dim]✓ Claude Code → Anthropic (direct)[/text.dim]")

    # ── Handle --grok / --codex / --altp provider routing ───────────────
    provider_proxy_started = False
    _provider_flags = sum([use_grok, use_codex, use_altp])
    if _provider_flags > 0:
        if _provider_flags > 1:
            raise click.ClickException(
                "Cannot combine --grok, --codex, and --altp. Pick one."
            )
        if use_alt_routing:
            raise click.ClickException(
                "Cannot combine provider flags with --alt-routing."
            )

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
                f"[info]🎯 {flag_name}: Routing ALL requests → {provider['label']}[/info]"
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
                console.logger.warning(
                    "[warning]⚠️  --altp flag ignored in subscription mode[/warning]"
                )
                console.logger.info(
                    "[text.dim]   Use 'dopemux routing mode api' to enable proxy routing[/text.dim]"
                )
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
                console.logger.info(
                    "[info]🎯 --altp: Tier-matched alternative provider routing[/info]"
                )
                for t in ALTP_PROVIDER["targets"]:
                    tier = t["name"].replace("altp-", "")
                    console.logger.info(
                        f"[text.dim]   {tier:>6s} → {t['label']} ({t['model']})[/text.dim]"
                    )

                config_data = generate_multi_target_config(ALTP_PROVIDER["targets"])

                # Auto-enable Claude Code Router for API translation
                use_claude_router = True
                console.logger.info(
                    "[text.dim]   Enabling Claude Code Router for API translation (responses → completions)[/text.dim]"
                )

                _routing_summary = (
                    "Claude Code → CCR → LiteLLM → tier-matched providers"
                )

        console.logger.info(
            "[info]🔄 Starting LiteLLM proxy (no DB required)...[/info]"
        )
        try:
            litellm_port, litellm_master_key = start_simple_proxy(
                project_root=Path.cwd(),
                config_data=config_data,
            )
            provider_proxy_started = True
        except LiteLLMProxyError as exc:
            raise click.ClickException(str(exc))

        console.logger.info(
            f"[success]✅ LiteLLM proxy ready on port {litellm_port}[/success]"
        )

        # Wire Claude Code to use the proxy
        os.environ["DOPEMUX_CLAUDE_VIA_LITELLM"] = "true"
        os.environ["DOPEMUX_DEFAULT_LITELLM"] = "1"
        os.environ["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{litellm_port}"
        os.environ["LITELLM_MASTER_KEY"] = litellm_master_key
        os.environ["DOPEMUX_LITELLM_MASTER_KEY"] = litellm_master_key
        os.environ["ANTHROPIC_API_KEY"] = litellm_master_key

        # Export CCR upstream env vars so Claude Code Router uses the new proxy
        os.environ["CLAUDE_CODE_ROUTER_PROVIDER"] = "litellm"
        os.environ["CLAUDE_CODE_ROUTER_UPSTREAM_URL"] = (
            f"http://127.0.0.1:{litellm_port}/v1/chat/completions"
        )
        os.environ["CLAUDE_CODE_ROUTER_UPSTREAM_KEY_VAR"] = "DOPEMUX_LITELLM_MASTER_KEY"

        if use_altp:
            # For --altp, we map to the tier names defined in generate_multi_target_config
            # CCR will expose these exact model names to Claude Code
            os.environ["CLAUDE_CODE_ROUTER_MODELS"] = "altp-opus,altp-sonnet,altp-haiku"
        elif provider:
            os.environ["CLAUDE_CODE_ROUTER_MODELS"] = provider["name"]

        use_litellm = True
        use_alt_routing = False  # Skip the full alt-routing block below

        console.logger.info(
            f"[text.dim]✓ {_routing_summary} (:{litellm_port})[/text.dim]"
        )
        console.logger.info("")

    # Handle --alt-routing flag (automatic LiteLLM setup)
    if use_alt_routing:
        use_litellm = True
        console.logger.info(
            "[info]🚀 Alternative routing enabled - starting LiteLLM automatically...[/info]"
        )

        from pathlib import Path as EnvPath

        from dotenv import load_dotenv

        routing_env = EnvPath.cwd() / ".env.routing"
        if routing_env.exists():
            load_dotenv(routing_env)
            console.logger.info("[text.dim]✓ Loaded .env.routing[/text.dim]")
        else:
            console.logger.info(
                "[warning]⚠️  .env.routing not found - using defaults[/warning]"
            )

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
            console.logger.info(
                "[error]❌ LiteLLM metrics database is required for alternative routing.[/error]"
            )
            console.logger.info(
                "[warning]   Set DOPEMUX_LITELLM_DB_URL in .env.routing and ensure the database is reachable.[/warning]"
            )
            console.logger.info("\n[info]Example:[/info]")
            console.logger.info(
                "  DOPEMUX_LITELLM_DB_URL=postgresql://user:password@localhost:5432/litellm"
            )  # pragma: allowlist secret
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
                    s.bind(("127.0.0.1", port))
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
                    console.logger.info(
                        "[error]❌ Ports 4000-4002 are all in use.[/error]"
                    )
                    console.logger.info(
                        "[warning]   Free up a port or stop an existing LiteLLM instance.[/warning]"
                    )
                    raise click.ClickException("No available ports for LiteLLM proxy.")
            console.logger.info(
                f"[warning]⚠️  Port 4000 is in use, using port {litellm_port} instead[/warning]"
            )

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
                    "[warning]⚠️ LiteLLM health probe blocked by OS (operation not permitted); proceeding without inline check.[/warning]"
                )
        except Exception as e:
            pass

            logger.error(f"Error: {e}")
        if not litellm_master_key:
            base_candidate = env_master_key_raw or stored_master_key
            litellm_master_key, regenerated_master_key = ensure_master_key(
                base_candidate
            )
            if regenerated_master_key:
                console.logger.info(
                    "[warning]⚠️  Generated LiteLLM master key with sk- prefix for proxy auth[/warning]"
                )
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
                config_data = (
                    yaml.safe_load(config_source.read_text(encoding="utf-8")) or {}
                )
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
            console.print("[text.dim]⚡ Dry-run: Skipping LiteLLM DB sync[/text.dim]")
            db_status_msg = "Dry-run: DB sync skipped"
            db_enabled = True
        else:
            try:
                db_status_msg, db_enabled = sync_litellm_database(instance_dir, db_url)
            except LiteLLMProxyError as exc:
                console.logger.error(
                    f"[error]❌ LiteLLM database setup failed: {exc}[/error]"
                )
                console.logger.info(
                    "[warning]   Fix the database connection (is Postgres running? credentials valid?) and retry.[/warning]"
                )
                console.logger.info("\n[info]Troubleshooting:[/info]")
                console.logger.info(
                    "  1. Check if PostgreSQL is running: lsof -i :5432 (or your port)"
                )
                console.logger.info("  2. Verify database credentials in .env.routing")
                console.logger.info("  3. Ensure the 'litellm' database exists")
                console.logger.info("  4. Test connection: psql <your_database_url>")
                raise click.ClickException(str(exc))

        if not db_enabled:
            console.logger.info(f"[error]❌ {db_status_msg}[/error]")
            console.logger.info(
                "[warning]   LiteLLM metrics must be available. Resolve the database issue and retry."
            )
            raise click.ClickException("LiteLLM metrics database not ready.")

        console.logger.info(f"[text.dim]{db_status_msg}[/text.dim]")
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
            console.logger.info(
                f"[success]✓ LiteLLM proxy already running on port {litellm_port}[/success]"
            )
        else:
            console.logger.info("[info]🔄 Starting LiteLLM proxy...[/info]")
            kill_result = subprocess.run(
                ["pkill", "-f", "litellm"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if kill_result.returncode not in (0, 1):
                console.logger.info(
                    "[error]❌ Unable to manage existing LiteLLM processes automatically (permission denied)."
                )
                console.logger.info(
                    f"[warning]   Stop the existing LiteLLM proxy on port {litellm_port} manually and rerun the command."
                )
                raise click.ClickException("LiteLLM proxy still running.")

            time.sleep(1)
            litellm_log.parent.mkdir(parents=True, exist_ok=True)
            with open(litellm_log, "w", encoding="utf-8") as log_file:
                subprocess.Popen(
                    [
                        "litellm",
                        "--config",
                        str(config_path),
                        "--port",
                        str(litellm_port),
                        "--host",
                        "0.0.0.0",
                    ],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )

            console.logger.info(
                "[text.dim]⏳ Waiting for LiteLLM to start...[/text.dim]"
            )
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
                    if (
                        isinstance(cause, OSError)
                        and getattr(cause, "errno", None) == 1
                    ):
                        console.print(
                            "[warning]⚠️ LiteLLM health probe blocked by OS (operation not permitted); assuming proxy is running.[/warning]"
                        )
                        ready = True
                        break
                time.sleep(1)

            if not ready:
                console.logger.info(
                    "[error]❌ LiteLLM proxy did not become healthy.[/error]"
                )
                console.logger.info(
                    f"[warning]   Check logs: tail -f {litellm_log}[/warning]"
                )
                console.logger.info("\n[info]Common issues:[/info]")
                console.logger.error(
                    "  • Database connection failed (check PostgreSQL is running)"
                )
                console.logger.info(
                    f"  • Port {litellm_port} became busy during startup"
                )
                console.logger.error("  • Configuration error in litellm.config.yaml")
                raise click.ClickException("LiteLLM proxy failed to start.")

            console.logger.info(
                f"[success]✅ LiteLLM proxy ready on port {litellm_port}[/success]"
            )

        os.environ["DOPEMUX_CLAUDE_VIA_LITELLM"] = "true"
        os.environ["DOPEMUX_DEFAULT_LITELLM"] = "1"
        os.environ["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{litellm_port}"
        os.environ["LITELLM_MASTER_KEY"] = litellm_master_key
        os.environ["DOPEMUX_LITELLM_MASTER_KEY"] = litellm_master_key
        os.environ["ANTHROPIC_API_KEY"] = litellm_master_key

        # Configure Claude Code Router to use this LiteLLM instance
        os.environ["CLAUDE_CODE_ROUTER_UPSTREAM_URL"] = (
            f"http://127.0.0.1:{litellm_port}/v1/chat/completions"
        )
        os.environ["CLAUDE_CODE_ROUTER_UPSTREAM_KEY_VAR"] = "DOPEMUX_LITELLM_MASTER_KEY"
        os.environ["CLAUDE_CODE_ROUTER_PROVIDER"] = "litellm"

        # Extract models from litellm config
        litellm_config = instance_dir / "litellm.config.yaml"
        models_list = _load_litellm_models(litellm_config)

        if models_list:
            os.environ["CLAUDE_CODE_ROUTER_MODELS"] = ",".join(models_list)
        else:
            console.logger.info(
                "[warning]⚠️  No models found in litellm.config.yaml[/warning]"
            )

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
        console.logger.info(
            "[text.dim]ℹ️ LiteLLM metrics database synchronised[/text.dim]"
        )
        console.logger.info(
            "[text.dim]✓ Claude Code configured to use LiteLLM proxy[/text.dim]"
        )
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
    
    # Resolve role (interactive wizard fallback)
    requested_role = role or os.environ.get("DOPEMUX_AGENT_ROLE")
    
    wizard_instance = None
    
    if not requested_role and not dry_run and not background and sys.stdin.isatty():
        requested_role, wizard_instance = start_wizard()
        if not requested_role:
            console.print("[warning]Launch cancelled by user[/warning]")
            sys.exit(0)
    elif not dry_run and not background and sys.stdin.isatty():
        # Initialize wizard in boot-sequence mode if role was pre-selected
        from .ux.launcher_wizard import LauncherWizard, LauncherState
        try:
            wizard_instance = LauncherWizard(console)
            wizard_instance.state = LauncherState.BOOT_SEQUENCE
            # Find index of requested role
            for i, (k, _) in enumerate(wizard_instance.roles):
                if k == requested_role:
                    wizard_instance.selected_index = i
                    break
            wizard_instance.live.start()
        except Exception:
            wizard_instance = None
            
    # Final fallback to developer
    requested_role = requested_role or "developer"
    
    if requested_role:
        try:
            role_activation = activate_role(requested_role, config_manager, console)
        except RoleNotFoundError:
            available = ", ".join(available_roles())
            console.print(
                f"[error]❌ Unknown role: {requested_role}[/error]\n"
                f"[text.dim]Available roles: {available}[/text.dim]"
            )
            sys.exit(1)

        spec = role_activation.spec
        role_profile = _ensure_role_profile(spec)
        pending_profile_name = getattr(role_profile, "name", spec.profile_name)
        if role:
            console.print(
                f"[info]🎭 Role activated:[/info] {spec.label} "
                f"[text.dim]({spec.key})[/text.dim] — {spec.description}"
            )
            if role_activation.enabled_servers:
                console.print(
                    f"[text.dim]Enabled MCP servers: {', '.join(role_activation.enabled_servers)}[/text.dim]"
                )
            if role_activation.disabled_servers:
                console.print(
                    f"[text.dim]Disabled MCP servers: {', '.join(role_activation.disabled_servers)}[/text.dim]"
                )
        else:
            console.print(
                f"[text.dim]🎭 Active role:[/text.dim] {spec.label} "
                f"[text.dim]({spec.key})[/text.dim]"
            )
    else:
        pending_profile_name = None

    cwd_path = Path.cwd()
    project_path = cwd_path

    try:
        dopemux_exists = Path.exists(project_path / ".dopemux")
    except (TypeError, AttributeError):
        dopemux_exists = False

    if not dopemux_exists:
        project_path_candidate = get_workspace_root()
        if project_path_candidate:
            if hasattr(project_path_candidate, "__truediv__"):
                project_path = project_path_candidate
            else:
                project_path = Path(project_path_candidate)

            try:
                dopemux_exists = Path.exists(project_path / ".dopemux")
            except (TypeError, AttributeError):
                dopemux_exists = False

    if dry_run:
        console.logger.info(
            "[info]Dry run: no tmux or Claude Code processes will be started.[/info]"
        )
        if role_activation:
            spec = role_activation.spec
            console.print(
                f"[text.dim]Role:[/text.dim] {spec.label} ({spec.key}) — {spec.description}"
            )
            if role_activation.enabled_servers:
                console.print(
                    f"[text.dim]MCP servers that would remain enabled: {', '.join(role_activation.enabled_servers)}[/text.dim]"
                )
            if role_activation.disabled_servers:
                console.print(
                    f"[text.dim]MCP servers that would be disabled: {', '.join(role_activation.disabled_servers)}[/text.dim]"
                )
        else:
            current_config = config_manager.load_config()
            enabled_now = sorted(
                name
                for name, server in current_config.mcp_servers.items()
                if server.enabled
            )
            console.print(
                f"[text.dim]No role specified — current enabled MCP servers: {', '.join(enabled_now)}[/text.dim]"
            )

        if role_activation and role_activation.missing_required:
            _suggest_server_start(role_activation.missing_required)

        if pending_profile_name:
            profile = role_profile or ProfileManager().get_profile(pending_profile_name)
            if profile:
                try:
                    claude_config = ClaudeConfig(config_path=project_path / ".claude" / "claude_config.json")
                    preview = claude_config.apply_profile(
                        profile,
                        create_backup=False,
                        dry_run=True,
                    )
                    preview_servers = sorted(preview.get("mcpServers", {}).keys())
                    console.print(
                        f"[text.dim]Profile '{profile.name}' would mount MCP servers: {', '.join(preview_servers)}[/text.dim]"
                    )
                except ClaudeConfigError as err:
                    console.print(
                        f"[warning]⚠ Claude config preview failed: {err}[/warning]"
                    )
            else:
                console.print(
                    f"[warning]⚠ Profile '{pending_profile_name}' is not defined."
                )

        console.logger.info(
            "[success]Dry run complete. No changes were made.[/success]"
        )
        ctx.exit(0)

    if role_activation and role_activation.missing_required:
        _suggest_server_start(role_activation.missing_required)
    if role_activation and role_activation.missing_optional:
        console.print(
            f"[text.dim]Optional services currently offline: {', '.join(role_activation.missing_optional)}[/text.dim]"
        )

    # Kill all active tmux sessions at start (requested behavior)
    # Skip if running inside tmux to avoid killing the session created by `dopemux tmux start`.
    try:
        if shutil.which("tmux") and not os.environ.get("TMUX"):
            _res = subprocess.run(
                ["tmux", "kill-server"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logging.debug(
                "tmux kill-server executed: returncode=%s",
                getattr(_res, "returncode", None),
            )
        else:
            logging.debug(
                "Skipping tmux kill-server (inside tmux: %s)",
                bool(os.environ.get("TMUX")),
            )
    except Exception as e:
        pass

        logger.error(f"Error: {e}")
    # Check if project is initialized
    if not dopemux_exists:
        console.print(
            "[warning]Project not initialized. Run 'dopemux init' first.[/warning]"
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

            wire_script = (
                Path(__file__).resolve().parents[2]
                / "scripts"
                / "wire_conport_project.py"
            )
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
                    conport_port=3004,  # Default ConPort port for instance A
                )

            if selected_worktree:
                console.logger.info(
                    f"\n[info]🔄 Recovering worktree session: {selected_worktree}[/info]"
                )
                os.chdir(selected_worktree)
                project_path = Path(selected_worktree)
                console.logger.info(
                    f"[success]✅ Switched to worktree: {project_path.name}[/success]"
                )
                console.logger.info(f"[text.dim]   Path: {project_path}[/text.dim]\n")
        except Exception as e:
            console.print(f"[warning]⚠️ Recovery menu unavailable: {e}[/warning]")

        try:
            should_exit = False
            if os.environ.get("DOPEMUX_ALLOW_MAIN") != "1":
                should_exit = check_and_protect_main(
                    workspace_path=str(project_path), enforce=False
                )

            new_worktree = consume_last_created_worktree()
            if new_worktree:
                os.chdir(new_worktree)
                project_path = Path.cwd()
                console.logger.info(
                    f"[success]🔀 Switched to worktree: {project_path.name}[/success]"
                )
                console.logger.info(f"[text.dim]   Path: {project_path}[/text.dim]")

            if should_exit and not new_worktree:
                sys.exit(0)
        except Exception as e:
            console.print(f"[warning]⚠️ Protection check unavailable: {e}[/warning]")

    instance_id = None
    port_base = None
    worktree_path = None
    instance_env_vars = {}

    if project_path_real_exists:
        instance_manager = InstanceManager(project_path)
        running_instances = detect_instances_sync(project_path)

        if running_instances:
            console.logger.info(
                f"\n[warning]⚠️  Found {len(running_instances)} running instance(s):[/warning]"
            )

            table = styled_table(
                f"{Glyphs.SERVER} Running Instances",
                ("Instance", {"style": "mint"}),
                ("Port", {"style": "magenta"}),
                ("Branch", {"style": "mint.soft"}),
                ("Current Worktree", {"style": "violet"}),
            )

            for inst in running_instances:
                table.add_row(
                    inst.instance_id,
                    str(inst.port_base),
                    inst.git_branch or "unknown",
                    str(inst.worktree_path) if inst.worktree_path else "N/A",
                )

            console.logger.info(table)

            try:
                instance_id, port_base = instance_manager.get_next_available_instance(
                    running_instances
                )

                console.print(
                    f"\n[info]💡 Multi-instance mode: Creating new worktree for instance {instance_id}[/info]"
                )

                if dopemux_confirm(
                    f"Create new worktree on port {port_base}?", default=True
                ):
                    suggested_branch = f"feature/instance-{instance_id}"
                    branch_name = dopemux_prompt(
                        "Branch name", default=suggested_branch, show_default=True
                    )

                    console.logger.info(
                        f"[info]📁 Creating worktree for {branch_name}...[/info]"
                    )
                    worktree_path = instance_manager.create_worktree(
                        instance_id, branch_name
                    )

                    console.logger.info(
                        f"[success]✅ Worktree created at {worktree_path}[/success]"
                    )

                    instance_env_vars = instance_manager.get_instance_env_vars(
                        instance_id, port_base, worktree_path
                    )

                    console.print(
                        f"\n[success]🎯 Starting instance {instance_id} on port {port_base}[/success]"
                    )
                    console.logger.info(
                        f"[text.dim]   Environment: DOPEMUX_INSTANCE_ID={instance_id}[/text.dim]"
                    )
                    console.logger.info(
                        f"[text.dim]   Workspace: {project_path}[/text.dim]"
                    )
                    console.logger.info(
                        f"[text.dim]   Worktree: {worktree_path}[/text.dim]"
                    )

                else:
                    console.logger.info(
                        "[warning]Cancelled. Continuing with single instance.[/warning]"
                    )

            except RuntimeError as e:
                console.logger.info(f"[error]❌ {str(e)}[/error]")
                sys.exit(1)

        if instance_id is None:
            instance_id = "A"
            port_base = 3000
            worktree_path = project_path

            instance_env_vars = instance_manager.get_instance_env_vars(
                instance_id, port_base, worktree_path
            )

            console.logger.info(
                "[info]🆕 Starting first instance (A) on port 3000[/info]"
            )
    else:
        instance_id = "A"
        port_base = 3000
        worktree_path = project_path

    if not instance_id:
        instance_id = "A"
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
                    instance_id, port_base, worktree_path
                )
                console.logger.info(
                    f"[text.dim]⚙️  Forced instance id: {instance_id} (port {port_base})[/text.dim]"
                )
            else:
                console.logger.info(
                    f"[text.dim]⚠️  DOPEMUX_FORCE_INSTANCE_ID={force_id} already in use; ignoring[/text.dim]"
                )
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
        os.environ["CLAUDE_CODE_ROUTER_UPSTREAM_URL"] = (
            "http://127.0.0.1:4000/v1/chat/completions"
        )
        os.environ["CLAUDE_CODE_ROUTER_UPSTREAM_KEY_VAR"] = "DOPEMUX_LITELLM_MASTER_KEY"

        console.logger.info(
            "[success]✅ Forced Claude Code to use LiteLLM proxy[/success]"
        )

    # Inject instance environment variables
    if instance_env_vars:
        # Auto fast per-instance mode for instances beyond A
        if instance_id and instance_id != "A":
            instance_env_vars["DOPEMUX_FAST_ONLY"] = "1"
        for key, value in instance_env_vars.items():
            os.environ[key] = value

        console.logger.info(
            "[text.dim]✅ Instance environment variables configured[/text.dim]"
        )
        _persist_instance_env_exports(
            project_path, instance_id or "A", instance_env_vars
        )

    active_profile_applied = False
    if pending_profile_name:
        profile_manager = ProfileManager()
        profile = role_profile or profile_manager.get_profile(pending_profile_name)
        if profile:
            try:
                claude_config = ClaudeConfig(config_path=project_path / ".claude" / "claude_config.json")
                claude_config.apply_profile(profile, create_backup=True, dry_run=False)
                try:
                    profile_manager.set_active_profile(project_path, profile.name)
                except (OSError, IOError) as e:
                    logger.error(f"Set active profile failed: {e}")
                except Exception:
                    logger.error("Unexpected set active profile error", exc_info=True)
                console.print(
                    f"[text.dim]✓ Activated profile '{profile.name}' for Claude Code[/text.dim]"
                )
                active_profile_applied = True
            except ClaudeConfigError as err:
                console.print(
                    f"[warning]⚠ Could not apply profile '{profile.name}': {err}[/warning]"
                )
        else:
            console.print(
                f"[warning]⚠ Profile '{pending_profile_name}' is not defined."
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

    if (
        litellm_enabled
        and not use_alt_routing
        and not _direct_provider_routing
        and not provider_proxy_started
    ):
        # Require OpenRouter since LiteLLM proxy is configured to route through it
        if not os.environ.get("OPENROUTER_API_KEY"):
            console.logger.info("[error]❌ OPENROUTER_API_KEY is not set.[/error]")
            console.logger.info(
                "[text.dim]Set OPENROUTER_API_KEY before using --litellm[/text.dim]"
            )
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
                for var in (
                    "DOPEMUX_LITELLM_DB_URL",
                    "LITELLM_DATABASE_URL",
                    "DATABASE_URL",
                ):
                    os.environ.pop(var, None)
        except Exception as e:
            logger.exception("Failed to start LiteLLM proxy: %s", e)
            raise

            if litellm_proxy_info.already_running:
                console.print(
                    f"[success]✅ Reusing LiteLLM proxy at {litellm_proxy_info.base_url}[/success]"
                )
            else:
                console.print(
                    f"[success]✅ LiteLLM proxy ready at {litellm_proxy_info.base_url}[/success]"
                )
                console.print(
                    f"[text.dim]   Config: {litellm_proxy_info.config_path}[/text.dim]"
                )
                console.print(
                    f"[text.dim]   Logs: {litellm_proxy_info.log_path}[/text.dim]"
                )
            if litellm_proxy_info.db_status:
                prisma_log = litellm_proxy_info.log_path.parent / "prisma.log"
                color = "dim" if litellm_proxy_info.db_enabled else "yellow"
                console.logger.info(
                    f"[{color}]   {litellm_proxy_info.db_status}[/{color}]"
                )
                if prisma_log.exists():
                    console.logger.info(
                        f"[text.dim]   Prisma log: {prisma_log}[/text.dim]"
                    )

        except LiteLLMProxyError as exc:
            console.logger.error(f"[error]❌ LiteLLM proxy failed: {exc}[/error]")
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

                router_overrides = _build_router_overrides(
                    provider_name, provider_models
                )
        else:
            provider_url = os.environ.get("CLAUDE_CODE_ROUTER_UPSTREAM_URL")
            models_env = os.environ.get("CLAUDE_CODE_ROUTER_MODELS", "")
            provider_models = [m.strip() for m in models_env.split(",") if m.strip()]
            if not provider_name:
                provider_name = os.environ.get("CLAUDE_CODE_ROUTER_PROVIDER", "custom")
            provider_key = os.environ.get("CLAUDE_CODE_ROUTER_UPSTREAM_KEY")

        if not provider_url:
            console.print(
                "[error]❌ Claude Code Router upstream URL is not configured.[/error]"
            )
            console.print(
                "[text.dim]Set CLAUDE_CODE_ROUTER_UPSTREAM_URL or enable --litellm.[/text.dim]"
            )
            sys.exit(1)

        if not provider_models:
            console.print(
                "[error]❌ No models configured for Claude Code Router upstream.[/error]"
            )
            console.print(
                "[text.dim]Set CLAUDE_CODE_ROUTER_MODELS or rely on --litellm defaults.[/text.dim]"
            )
            sys.exit(1)

        # Print DopeBrainzRouterManager class info before usage.
        console.print(
            "   Enabling Claude Code Router for API translation (responses → completions)"
        )

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
            console.logger.error(f"[error]❌ DopeBrainz Router failed: {exc}[/error]")
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
                f"[success]✅ Reusing Claude Code Router at {router_info.base_url}[/success]"
            )
        else:
            console.print(
                f"[success]✅ Claude Code Router ready at {router_info.base_url}[/success]"
            )
            console.logger.info(
                f"[text.dim]   Config: {router_info.config_path}[/text.dim]"
            )
            console.logger.info(f"[text.dim]   Logs: {router_info.log_path}[/text.dim]")

    with branded_progress(console=console) as progress:
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
                f"[success]📍 Welcome back! You were working on: {context.get('current_goal', 'Unknown task')}[/success]"
            )
        else:
            progress.update(task, description="Starting fresh session")
            console.logger.info("[info]🆕 Starting new session[/info]")

        # Check if dangerous mode has expired
        _check_dangerous_mode_expiry()

        # Handle dangerous mode activation
        is_dangerous_mode = dangerous or dangerously_skip_permissions
        if is_dangerous_mode:
            progress.update(task, description="⚠️  Activating dangerous mode...")
            _activate_dangerous_mode()

        # Auto-configure MCP servers for current worktree (Phase 2: Zero manual steps)
        skip_auto_config = os.getenv("DOPEMUX_SKIP_MCP_AUTOCONFIG", "0").lower() in {
            "1",
            "true",
            "yes",
        }
        if skip_auto_config:
            progress.update(
                task,
                description="⏭️ Skipping MCP auto-configuration (DOPEMUX_SKIP_MCP_AUTOCONFIG)",
            )
        else:
            progress.update(task, description="Auto-configuring MCP servers...")
            from .auto_configurator import WorktreeAutoConfigurator

            auto_config = WorktreeAutoConfigurator()
            workspace_to_configure = worktree_path or project_path
            success, message = auto_config.configure_workspace(workspace_to_configure)

            if success:
                progress.update(task, description="✅ MCP auto-configuration complete")
            if wizard_instance:
                wizard_instance.update_boot_step("Configuring Worktree", "SUCCESS")
            else:
                progress.update(task, description="⚠️ MCP auto-configuration skipped")
                console.logger.info(f"[text.dim]{message}[/text.dim]")

        # Start MCP servers by default (ADHD-optimized experience)
        if not no_mcp:
            # CRITICAL FIX: Pass instance_env_vars so MCP servers get workspace isolation
            _start_mcp_servers_with_progress(
                project_path,
                instance_id=instance_id or "A",
                instance_env=instance_env_vars,
                wizard=wizard_instance,
            )
            startup_workspace = (worktree_path or project_path).resolve()
            autoindex_result = _trigger_dope_context_autoindex_startup(
                startup_workspace
            )
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
                        "[warning]⚠️  Autoindex startup trigger failed; continuing without blocking.[/warning]"
                    )
        else:
            console.logger.info(
                "[warning]⚠️  Skipping MCP servers (reduced ADHD experience)[/warning]"
            )

        # Configure role-based instructions
        if role:
            progress.update(task, description=f"Activating {role} persona...")
            configurator = ClaudeConfigurator(config_manager)
            # project_path is the base directory for .claude/
            configurator.setup_project_config(project_path, role=role)

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
        progress.update(task, description="Starting activity monitoring...")
        if wizard_instance:
            wizard_instance.update_boot_step("Starting Activity Monitor", "LOADING")
        
        from .hooks.claude_code_hooks import claude_hooks
        claude_hooks.start_monitoring(str(project_path))
        
        attention_monitor = AttentionMonitor(project_path)
        attention_monitor.start_monitoring()

        if wizard_instance:
            wizard_instance.update_boot_step("Starting Activity Monitor", "SUCCESS")
            wizard_instance.finish(success=True, final_message="Dopemux Cockpit: All systems nominal. Launching Claude Code...")

        progress.update(task, description="Ready! 🎯", completed=True)

    # Save instance state to ConPort for crash recovery
    if instance_id and port_base:
        from datetime import datetime, timezone

        from .instance_state import InstanceState, save_instance_state_sync

        # Get current git branch
        try:
            git_branch = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(worktree_path or project_path),
                capture_output=True,
                text=True,
                check=True,
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
            last_focus_context=(
                context.get("current_goal", "New session") if context else "New session"
            ),
        )

        save_instance_state_sync(
            state,
            workspace_id=str(project_path.resolve()),
            conport_port=3004,  # Always save via instance A's ConPort
        )
        console.logger.info(
            "[text.dim]✅ Instance state saved for crash recovery[/text.dim]"
        )

    if not background:
        console.print(
            "[success]✨ Claude Code is running with ADHD optimizations[/success]"
        )
        console.logger.info("Press Ctrl+C to stop monitoring and save context")

        try:
            claude_process.wait()
        except KeyboardInterrupt:
            console.logger.info(
                "\n[warning]⏸️ Saving context and stopping...[/warning]"
            )

            # Mark instance as stopped in ConPort
            if instance_id:
                from datetime import datetime, timezone

                from .instance_state import (
                    load_instance_state_sync,
                    save_instance_state_sync,
                )

                workspace_id = str(project_path.resolve())
                state = load_instance_state_sync(
                    instance_id, workspace_id, conport_port=3004
                )
                if state:
                    state.status = "stopped"
                    state.last_active = datetime.now(timezone.utc)
                    save_instance_state_sync(state, workspace_id, conport_port=3004)
                    console.logger.info(
                        "[text.dim]✅ Instance marked as stopped[/text.dim]"
                    )

            ctx.invoke(cli.commands["save"])
            attention_monitor.stop_monitoring()


def _trigger_dope_context_autoindex_startup(
    workspace_path: Path,
    *,
    force: bool = False,
) -> Optional[dict]:
    """
    Trigger dope-context startup autoindex bootstrap for the current workspace.
    """
    enabled = os.getenv("DOPEMUX_AUTO_INDEX_ON_STARTUP", "1").lower() not in {
        "0",
        "false",
        "no",
    }
    if not enabled:
        return None

    base_url = os.getenv("DOPE_CONTEXT_URL", "http://localhost:3010").rstrip("/")
    endpoint = f"{base_url}/autoindex/bootstrap"
    payload = {
        "workspace_path": str(workspace_path.resolve()),
        "force": force,
        "wait_for_completion": False,
        "debounce_seconds": float(
            os.getenv("DOPEMUX_AUTO_INDEX_DEBOUNCE_SECONDS", "5.0")
        ),
        "periodic_interval": int(
            os.getenv("DOPEMUX_AUTO_INDEX_PERIODIC_SECONDS", "600")
        ),
        "trigger": "dopemux_cli_startup",
    }

    try:
        import requests

        response = requests.post(endpoint, json=payload, timeout=5)
        if response.status_code >= 400:
            console.logger.info(
                f"[warning]⚠️  Autoindex bootstrap request failed ({response.status_code})[/warning]"
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


from .commands.instances_commands import instances
cli.add_command(instances, "instances")

from .commands.native_hooks_commands import native_hooks
cli.add_command(native_hooks, "native-hooks")

from .commands.pr_commands import pr_merge_group
cli.add_command(pr_merge_group, "pr-merge")


from .commands.session_commands import status
cli.add_command(status, "status")

from .commands.ops_commands import run_build, run_tests
cli.add_command(run_tests, "run-tests")
cli.add_command(run_build, "run-build")


from .commands.kernel_commands import kernel

cli.add_command(kernel)


from .commands.task_legacy_commands import task as _task_legacy
cli.add_command(_task_legacy, "task")


from .commands.agent_loop_commands import agent_loop_cmd

cli.add_command(agent_loop_cmd)

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
from .commands.personas_commands import personas

cli.add_command(trigger_group, "trigger")


from .commands.capture_group_commands import capture_group

cli.add_command(capture_group, "capture")


from .commands.workflow_group_commands import workflow_group

cli.add_command(workflow_group, "workflow")


from .commands.upgrades_commands import upgrades

cli.add_command(upgrades)


from .commands.extractor_commands import extractor, _run_extractor_runner, _run_repscan_runner
from .commands.extractor_validation import ValidationConfig, run_live_validation

cli.add_command(extractor)

from .commands.audit_commands import audit
from .commands.diagnostics_commands import analyze, health, theme

cli.add_command(theme)
cli.add_command(audit)


# ============================================================
# Commands extracted back from submodules (use @cli.command)
# ============================================================


cli.add_command(analyze)

from .commands.mcp_commands import mcp, servers

cli.add_command(mcp)
cli.add_command(servers)


cli.add_command(health)


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
    os.environ["ZEN_FALLBACK_MODELS"] = (
        "litellm/openrouter-xai-grok-code-fast,litellm/openrouter-google-gemini-2-flash"
    )

    # Set up LiteLLM proxy URL
    os.environ["LITELLM_PROXY_URL"] = "http://localhost:4000"

    # Configure Claude Code to use LiteLLM
    os.environ["CLAUDE_CODE_LLM_PROVIDER"] = "litellm"
    os.environ["CLAUDE_CODE_LLM_BASE_URL"] = "http://localhost:4000"
    os.environ["CLAUDE_CODE_LLM_API_KEY"] = os.getenv("DOPEMUX_LITELLM_MASTER_KEY", "")

    console.logger.info(
        "[success]✅ OpenRouter via LiteLLM configuration applied[/success]"
    )


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
        console.logger.error(f"[error]❌ MCP Provisioning failed: {e}[/error]")
        return None


def _start_mcp_servers_with_progress(
    project_path: Path, instance_id: str = "A", instance_env: Optional[dict] = None, wizard=None
):
    """
    Start MCP servers with auto-provisioning, instance-scoped overlays, and Phase 0 gate.
    """
    if os.getenv("DOPEMUX_SKIP_MCP_START", "0").lower() in {"1", "true", "yes"}:
        if wizard:
            wizard.add_log("⏭️ Skipping MCP server startup (DOPEMUX_SKIP_MCP_START)")
        else:
            console.logger.info("[warning]⏭️ Skipping MCP server startup[/warning]")
        return

    # 1. Provision stack if missing
    mcp_dir = _resolve_mcp_dir(project_path)
    if not mcp_dir:
        if wizard: wizard.add_log("❌ MCP stack provisioning failed", style="red")
        raise click.ClickException("MCP stack provisioning failed.")

    # 2. Materialize instance overlay
    from .mcp.instance_overlay import InstanceOverlayManager
    overlay_manager = InstanceOverlayManager(project_path, instance_id)
    overlay = overlay_manager.materialize()

    # 3. Prepare environment
    env_for_subprocess = os.environ.copy()
    if instance_env:
        env_for_subprocess.update(instance_env)

    try:
        import dotenv
        env_vars = dotenv.dotenv_values(overlay["env_path"])
        env_for_subprocess.update({k: v for k, v in env_vars.items() if v is not None})
    except ImportError:
        pass

    if wizard:
        wizard.add_log(f"🔌 Starting MCP Servers (Instance {instance_id})")
        wizard.add_log(f"Project: {overlay['compose_project_name']}")
        wizard.update_boot_step("Connecting to Docker", "LOADING")
    else:
        console.logger.info(f"\n[info]🔌 Starting MCP Servers (Instance {instance_id})[/info]")
        console.logger.info(f"[text.dim]Project: {overlay['compose_project_name']}[/text.dim]")

    # 4. Resolve the canonical compose files
    compose_files = []
    docker_dir = project_path / "docker"
    for compose_part in ["core", "routing", "research", "pm", "agents"]:
        part_file = docker_dir / f"compose.{compose_part}.yml"
        if part_file.exists():
            compose_files.append("-f")
            compose_files.append(str(part_file))
    
    if not compose_files:
        legacy_file = project_path / "compose.yml"
        if legacy_file.exists():
            compose_files.append("-f")
            compose_files.append(str(legacy_file))
        else:
            fallback = mcp_dir / "compose.yml"
            if not fallback.exists():
                fallback = mcp_dir / "docker-compose.yml"
            compose_files.append("-f")
            compose_files.append(str(fallback))

    compose_files.append("-f")
    compose_files.append(overlay["compose_path"])

    cmd = [
        "docker", "compose",
    ] + compose_files + [
        "--project-name", overlay["compose_project_name"],
        "up", "-d", "--remove-orphans",
    ]

    startup_successful = False
    output_lines = []

    def run_docker_logic():
        nonlocal startup_successful
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env_for_subprocess,
            cwd=str(project_path),
        )

        for line in process.stdout:
            line = line.strip()
            if line:
                output_lines.append(line)
                if wizard:
                    wizard.add_log(line)
                if len(output_lines) > 5:
                    output_lines.pop(0)
                
                if not wizard:
                    # Update local live display
                    pass # Handled by the 'with Live' block outside if needed

        process.wait()
        startup_successful = (process.returncode == 0)
        if not startup_successful:
            if wizard: wizard.update_boot_step("Connecting to Docker", "FAILURE")
            raise RuntimeError(f"Docker compose failed with exit code {process.returncode}")

    if wizard:
        run_docker_logic()
        wizard.update_boot_step("Connecting to Docker", "SUCCESS")
        wizard.update_boot_step("Booting MCP Services", "LOADING")
    else:
        status_text = Text("🚀 Launching containers...")
        from rich.live import Live
        with Live(status_text, console=console, refresh_per_second=4) as live:
            run_docker_logic()
            status_text.append("\n✅ Containers launched!", style="success")
            live.update(status_text)

    # 5. Phase 0 Discovery Gate
    if wizard: wizard.add_log("🛡️ Running Phase 0 Discovery Gate...")
    from .mcp.gate import DiscoveryGate
    time.sleep(2)

    for srv_name, port in overlay["port_map"].items():
        env_var = f"DOPMUX_{srv_name.upper().replace('-', '_')}_URL"
        os.environ[env_var] = f"http://127.0.0.1:{port}/mcp" if srv_name != "LiteLLM" else f"http://127.0.0.1:{port}"

    gate = DiscoveryGate(project_path, run_id=f"start-{instance_id}-{int(time.time())}")
    if not asyncio.run(gate.run()):
        if wizard: wizard.update_boot_step("Booting MCP Services", "FAILURE")
        raise RuntimeError("MCP Discovery Gate failed.")

    if wizard:
        wizard.update_boot_step("Booting MCP Services", "SUCCESS")
        wizard.add_log("✅ MCP Servers Online")


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


from .commands.state_commands import restore, save
cli.add_command(save, "backup")
cli.add_command(restore, "restore")


from .commands.instances_commands import instances
from .commands.personas_commands import personas

@cli.group("native-hooks")
def native_hooks():
    """
    🔗 Protocol Synchronization: Manage Claude Code internal hooks

    Orchestrates the registration and management of high-fidelity internal 
    hooks. These rituals ensure that Claude Code activity is seamlessly 
    synchronized with the DØPEMÜX cockpit telemetry.
    """
    pass

@native_hooks.command("register")
@click.option("--global", "is_global", is_flag=True, help="🌐 Global Calibration: Register ritual hooks in the global configuration ledger.")
def native_hooks_register(is_global: bool):
    """
    ⚡ Synchronize Protocol: Register DØPEMÜX hooks in Claude settings

    Automates the injection of ritual hook coordinates into the Claude 
    Code configuration ledger, enabling real-time signal detection.
    """
    import json
    from pathlib import Path
    
    # Path to this script's native hook entry point
    hook_script = Path(__file__).resolve().parent / "claude" / "native_hooks.py"
    cmd = f"python3 {hook_script}"
    
    # Define hook configuration
    hooks_config = {
        "hooks": {
            "command": [
                {
                    "events": [
                        "SessionStart", 
                        "UserPromptSubmit", 
                        "PreToolUse", 
                        "PermissionRequest", 
                        "PostToolUse", 
                        "PostToolUseFailure", 
                        "Stop", 
                        "SubagentStop", 
                        "PreCompact", 
                        "SessionEnd"
                    ],
                    "command": cmd
                }
            ]
        }
    }
    
    # Target settings file
    if is_global:
        settings_path = Path.home() / ".claude" / "settings.json"
    else:
        settings_path = Path.cwd() / ".claude" / "settings.json"
        
    # Read existing settings
    existing = {}
    if settings_path.exists():
        try:
            existing = json.loads(settings_path.read_text())
        except:
            pass
            
    # Simple merge (Dopemux hooks first)
    if "hooks" not in existing:
        existing["hooks"] = {}
    if "command" not in existing["hooks"]:
        existing["hooks"]["command"] = []
        
    # Check if already registered
    already_registered = any(h.get("command") == cmd for h in existing["hooks"]["command"])
    
    if not already_registered:
        existing["hooks"]["command"].insert(0, hooks_config["hooks"]["command"][0])
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(json.dumps(existing, indent=2))
        console.print(f"[success]✓ Registered Dopemux native hooks in {settings_path}[/success]")
    else:
        console.print(f"[info]Dopemux native hooks already registered in {settings_path}[/info]")


cli.add_command(instances, "instances")
cli.add_command(personas, "personas")
cli.add_command(native_hooks, "native-hooks")

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
        console.logger.info(
            "\n[text.dim]Tip: Adjust path and time as needed.[/text.dim]"
        )
        return

    try:
        current = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
        content = current.stdout if current.returncode == 0 else ""
        if "# dopemux-backup" in content:
            console.logger.info(
                "[warning]⚠️  A dopemux-backup entry already exists in your crontab[/warning]"
            )
            return
        new_content = (
            content
            + ("\n" if content and not content.endswith("\n") else "")
            + cron_entry
        )
        p = subprocess.run(["crontab", "-"], input=new_content, text=True)
        if p.returncode == 0:
            console.logger.info(
                "[success]✅ Installed dopemux backup cron job[/success]"
            )
        else:
            console.logger.info(
                "[warning]⚠️  Could not install cron job. Printing entry instead:[/warning]"
            )
            console.logger.info(cron_entry)
    except Exception as e:
        console.logger.error(f"[warning]⚠️  Failed to install cron job: {e}[/warning]")
        console.logger.info("\nAdd this entry manually via 'crontab -e':\n")
        console.logger.info(cron_entry)


@cli.command("extract-chatlog")
@click.argument("directory", default=".")
@click.option("--output", "-o", help="📂 Harvest Coordinate: Output directory for extraction results.")
@click.option(
    "--confidence",
    "-c",
    type=float,
    default=0.5,
    help="🎯 Confidence Gate: Minimum threshold for signal extraction (0.0-1.0).",
)
@click.option(
    "--batch-size",
    "-b",
    type=int,
    default=10,
    help="📊 Signal Density: Number of artifacts to process per batch.",
)
@click.option(
    "--max-workers", "-w", type=int, default=4, help="⚡ Extraction Workers: Maximum parallel ritual workers.",
)
@click.option("--archive", "-a", help="📦 Temporal Archive: Directory for processed artifact storage.")
@click.option("--workspace-id", help="🆔 Ritual Chamber: ConPort workspace ID for persistent synchronization.")
@click.pass_context
def extract_chatlog(
    ctx,
    directory: str,
    output: Optional[str],
    confidence: float,
    batch_size: int,
    max_workers: int,
    archive: Optional[str],
    workspace_id: Optional[str],
):
    """
    📥 Harvest Telemetry: Extract high-fidelity intelligence from chat logs

    Engages the semantic extraction engine to harvest decisions, patterns, 
    and ritual progress from local chat log artifacts. Synchronizes the 
    extracted intelligence with the persistent knowledge graph.
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

    backend_path = (
        Path(__file__).parent.parent.parent
        / "services"
        / "dopemux-gpt-researcher"
        / "backend"
    )
    sys.path.insert(0, str(backend_path))

    try:
        from extraction_pipeline import ExtractionPipeline, PipelineConfig
    except ImportError as e:
        console.logger.info(
            f"[error]❌ Could not import extraction pipeline: {e}[/error]"
        )
        console.logger.info(
            "[warning]💡 Make sure you're in the dopemux-mvp directory[/warning]"
        )
        sys.exit(1)

    source_path = Path(directory).resolve()
    if not source_path.exists():
        console.logger.info(
            f"[error]❌ Directory does not exist: {source_path}[/error]"
        )
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

    console.logger.info("[info]🚀 Starting Basic Chatlog Extraction Pipeline[/info]")
    console.logger.info(f"[info]📁 Source: {source_path}[/info]")
    console.logger.info(f"[info]📤 Output: {output_path}[/info]")
    console.logger.info(f"[info]🎯 Extractors: Decision, Feature, Research[/info]")

    with branded_progress(console=console) as progress:
        task = progress.add_task("Initializing extraction pipeline...", total=None)

        try:
            pipeline = ExtractionPipeline(config)

            progress.update(task, description="Discovering files...")
            files = pipeline.discover_files()

            if not files:
                progress.update(
                    task, description="No files found to process", completed=True
                )
                console.logger.info(
                    "[warning]⚠️ No unprocessed chatlog files found[/warning]"
                )
                return

            progress.update(task, description=f"Processing {len(files)} files...")
            result = pipeline.run_extraction()

            if result["success"]:
                progress.update(
                    task,
                    description="Extraction completed successfully! ✅",
                    completed=True,
                )

                stats = result["statistics"]
                console.print(
                    styled_panel(
                        f"🎯 Basic Extraction Results:\n\n"
                        f"• Files processed: {stats['files_processed']}/{stats['total_files']}\n"
                        f"• Total chunks: {stats['total_chunks']}\n"
                        f"• Fields extracted: {stats['total_fields']}\n"
                        f"• High confidence fields: {stats['high_confidence_fields']}\n"
                        f"• Documents generated: {stats['documents_generated']}\n"
                        f"• Processing time: {stats['processing_time']:.2f}s\n\n"
                        f"🔬 Field Types:\n"
                        + "\n".join(
                            [
                                f"• {field_type}: {count}"
                                for field_type, count in stats["fields_by_type"].items()
                            ]
                        ),
                        title=f"{Glyphs.SUCCESS} Basic Extraction Complete",
                    )
                )

                console.logger.info(
                    f"\n[success]📁 Results saved to: {output_path}[/success]"
                )
                console.logger.info(
                    f"[success]📦 Processed files archived to: {result['archive_directory']}[/success]"
                )

            else:
                progress.update(
                    task, description="Extraction failed ❌", completed=True
                )
                console.logger.error(f"[error]❌ Extraction failed[/error]")
                if result.get("errors"):
                    console.logger.error(
                        f"[error]Errors: {len(result['errors'])}[/error]"
                    )
                    for error in result["errors"][:3]:
                        console.logger.error(f"[error]  • {error}[/error]")
                sys.exit(1)

        except Exception as e:
            progress.update(task, description="Error occurred", completed=True)
            console.logger.error(f"[error]❌ Extraction pipeline failed: {e}[/error]")
            if ctx.obj.get("verbose"):
                import traceback

                traceback.print_exc()
            sys.exit(1)


@cli.command()
@click.argument("directory", default=".")
@click.option("--output", "-o", help="📂 Harvest Coordinate: Output directory for high-fidelity extraction results.")
@click.option(
    "--confidence",
    "-c",
    type=float,
    default=0.4,
    help="🎯 Confidence Gate: Minimum threshold for signal extraction (0.0-1.0).",
)
@click.option(
    "--batch-size",
    "-b",
    type=int,
    default=15,
    help="📊 Signal Density: Number of artifacts to process per batch.",
)
@click.option(
    "--max-workers", "-w", type=int, default=6, help="⚡ Extraction Workers: Maximum parallel ritual workers.",
)
@click.option("--archive", "-a", help="📦 Temporal Archive: Directory for processed artifact storage.")
@click.option("--workspace-id", help="🆔 Ritual Chamber: ConPort workspace ID for persistent synchronization.")
@click.option(
    "--max-documents", "-d", type=int, default=8, help="📜 Materialization Limit: Maximum documents to synthesize during the ritual."
)
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
    max_documents: int,
):
    """
    🔬 Deep Harvest: Extract high-fidelity repository intelligence (Pro Mode)

    Engages the full semantic extraction suite to harvest constraints, 
    dependencies, and architectural patterns from chat logs. Synthesizes a 
    comprehensive knowledge graph and materializes high-fidelity reports.
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
    backend_path = (
        Path(__file__).parent.parent.parent
        / "services"
        / "dopemux-gpt-researcher"
        / "backend"
    )
    sys.path.insert(0, str(backend_path))

    try:
        from extraction_pipeline import ExtractionPipeline, PipelineConfig
    except ImportError as e:
        console.logger.info(
            f"[error]❌ Could not import extraction pipeline: {e}[/error]"
        )
        console.logger.info(
            "[warning]💡 Make sure you're in the dopemux-mvp directory[/warning]"
        )
        sys.exit(1)

    source_path = Path(directory).resolve()
    if not source_path.exists():
        console.logger.info(
            f"[error]❌ Directory does not exist: {source_path}[/error]"
        )
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
        workspace_id=workspace_id,
    )

    console.logger.info("[info]🔬 Starting Pro Chatlog Extraction Pipeline[/info]")
    console.logger.info(f"[info]📁 Source: {source_path}[/info]")
    console.logger.info(f"[info]📤 Output: {output_path}[/info]")
    console.logger.info(
        f"[info]🎯 Extractors: All 7 (Decision, Feature, Research, Constraint, Stakeholder, Risk, Security)[/info]"
    )

    with branded_progress(console=console) as progress:
        task = progress.add_task("Initializing Pro extraction pipeline...", total=None)

        try:
            # Create and run pipeline
            pipeline = ExtractionPipeline(config)

            progress.update(task, description="Discovering files...")
            files = pipeline.discover_files()

            if not files:
                progress.update(
                    task, description="No files found to process", completed=True
                )
                console.logger.info(
                    "[warning]⚠️ No unprocessed chatlog files found[/warning]"
                )
                return

            progress.update(
                task,
                description=f"Processing {len(files)} files with ALL extractors...",
            )
            result = pipeline.run_extraction()

            if result["success"]:
                progress.update(
                    task,
                    description="Pro extraction completed successfully! ✅",
                    completed=True,
                )

                stats = result["statistics"]
                console.print(
                    styled_panel(
                        f"🔬 Pro Extraction Results:\n\n"
                        f"• Files processed: {stats['files_processed']}/{stats['total_files']}\n"
                        f"• Total chunks: {stats['total_chunks']}\n"
                        f"• Fields extracted: {stats['total_fields']}\n"
                        f"• High confidence fields: {stats['high_confidence_fields']}\n"
                        f"• Documents generated: {stats['documents_generated']}\n"
                        f"• Processing time: {stats['processing_time']:.2f}s\n\n"
                        f"🔬 Field Types:\n"
                        + "\n".join(
                            [
                                f"• {field_type}: {count}"
                                for field_type, count in stats["fields_by_type"].items()
                            ]
                        )
                        + f"\n\n⏱️ Phase Times:\n"
                        + "\n".join(
                            [
                                f"• {phase}: {time:.2f}s"
                                for phase, time in stats["phase_times"].items()
                            ]
                        ),
                        title=f"{Glyphs.SUCCESS} Pro Extraction Complete",
                    )
                )

                console.logger.info(
                    f"\n[success]📁 Results saved to: {output_path}[/success]"
                )
                console.logger.info(
                    f"[success]📦 Processed files archived to: {result['archive_directory']}[/success]"
                )
                console.logger.info(
                    f"[success]📊 Knowledge graph: {output_path}/knowledge_graph.json[/success]"
                )
                console.logger.info(
                    f"[success]📋 Comprehensive report: {output_path}/reports/[/success]"
                )

            else:
                progress.update(
                    task, description="Pro extraction failed ❌", completed=True
                )
                console.logger.error(f"[error]❌ Pro extraction failed[/error]")
                if result.get("errors"):
                    console.logger.error(
                        f"[error]Errors: {len(result['errors'])}[/error]"
                    )
                    for error in result["errors"][:3]:  # Show first 3 errors
                        console.logger.error(f"[error]  • {error}[/error]")
                sys.exit(1)

        except Exception as e:
            progress.update(task, description="Error occurred", completed=True)
            console.logger.error(
                f"[error]❌ Pro extraction pipeline failed: {e}[/error]"
            )
            if ctx.obj.get("verbose"):
                import traceback

                traceback.print_exc()
            sys.exit(1)


# from src/dopemux/commands/extractor_commands.py
@cli.command(
    "repscan",
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.option(
    "--phase",
    type=click.Choice(
        ["ALL", "A", "H", "D", "C", "E", "W", "B", "G", "Q", "R", "X", "T", "Z"]
    ),
    help="📊 Target Phase: Phase code or ALL for the repo scan ritual.",
)
@click.option("--run-id", type=str, help="🆔 Ritual Session: Unique identifier for the scan run.")
@click.option("--promptgen", type=click.Choice(["off", "v1", "v2", "auto"]), help="🧠 Prompt Synthesis: Mode for automated prompt generation.")
@click.option("--promptpack", type=str, help="📦 Prompt Package: Specific promptpack to use for the ritual.")
@click.option("--promptgen-only", is_flag=True, help="⚡ Synthesis Only: Execute only the prompt generation phase.")
@click.option("--prompt-root", type=str, help="🔬 Prompt Source: Root directory for ritual prompts.")
@click.option("--profiles-dir", type=str, help="📂 Profile Registry: Path to the ritual profiles directory.")
@click.option("--legacy-runner", type=str, help="⏪ Legacy Engine: Path to the legacy v3 runner.")
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
    """
    🔬 Repository Audit: Run deterministic repo scan and prompt synthesis

    Engages the deterministic repository scanner to audit the codebase and 
    synthesize high-fidelity prompts for extraction rituals.
    """
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


_PIPELINE_VERSION_CHOICES = ["v5", "v4", "v3"]
_ROUTING_POLICY_CHOICES = [
    "cost",
    "balanced",
    "balanced_openrouter",
    "balanced_grok_openrouter",
    "quality",
    "openrouter",
    "gemini_primary",
    "optimal",
]
_LEGACY_DEFAULT_ROUTING_POLICY = "cost"
_V5_DEFAULT_ROUTING_POLICY = "balanced_openrouter"


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
        default="v5",
        show_default=True,
    )(command_fn)
    return command_fn


def _resolved_pipeline_version(
    pipeline_version: str, engine_version_legacy: Optional[str]
) -> str:
    if engine_version_legacy:
        return engine_version_legacy
    return pipeline_version


def _run_truth_v5_alias(
    *,
    phase: str = "ALL",
    dry_run: bool,
    resume: bool,
    workers: int,
    routing_policy: str,
) -> None:
    args: List[str] = ["--phase", phase or "ALL"]
    if dry_run:
        args.append("--dry-run")
    if resume:
        args.append("--resume")
    args.extend(["--partition-workers", str(max(1, int(workers)))])
    args.extend(["--routing-policy", routing_policy])
    _run_extractor_runner(pipeline_version="v5", args=args)


@upgrades.command("list")
@_pipeline_version_options
@click.pass_context
def extractor_list(ctx, pipeline_version: str, engine_version_legacy: Optional[str]):
    """
    📋 Catalog Phases: List ritual phases and effective pipeline order

    Displays the full sequence of extraction phases, detailing the 
    prescribed order of operations for the active ritual pipeline.
    """
    effective_version = _resolved_pipeline_version(
        pipeline_version, engine_version_legacy
    )
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
@click.option("--step", default=None, help="Single concrete step to execute within the selected phase.")
@click.option("--s-steps", default=None, help="Comma-separated subset of Phase S steps.")
@click.option("--run-id", default=None, help="Run ID")
@click.option(
    "--promptset-root",
    type=click.Path(exists=True, file_okay=False),
    default=None,
    help="External generated promptset directory for v5 prompt resolution.",
)
@click.option("--dry-run/--execute", default=True, show_default=True)
@click.option("--resume/--no-resume", default=True, show_default=True)
@click.option("--partition-workers", type=int, default=1, show_default=True)
@click.option(
    "--max-partitions-per-step",
    type=int,
    default=None,
    help="Cap the number of partitions executed for each step.",
)
@click.option(
    "--routing-policy",
    type=click.Choice(_ROUTING_POLICY_CHOICES),
    default=None,
    show_default=False,
    help="🧠 Cognitive Routing: LLM policy for extraction (default: model-map balanced).",
)
@click.option("--disable-escalation", is_flag=True, default=False, show_default=True)
@click.option("--escalation-max-hops", type=int, default=2, show_default=True)
@click.option("--batch-mode", is_flag=True, default=False, show_default=True)
@click.option("--batch-submit-only", is_flag=True, default=False, show_default=True)
@click.option("--batch-watch", is_flag=True, default=False, show_default=True)
@click.option("--batch-retrieve", is_flag=True, default=False, show_default=True)
@click.option("--batch-ids", multiple=True, help="Batch IDs to retrieve when using --batch-retrieve.")
@click.option(
    "--batch-provider",
    type=click.Choice(["auto", "openai", "gemini", "xai"]),
    default="auto",
    show_default=True,
    help="🧪 Batch Alchemist: Specific provider for asynchronous processing (default: auto).",
)
@click.option(
    "--retrieve-provider",
    type=click.Choice(["openai", "gemini", "xai"]),
    default="openai",
    show_default=True,
)
@click.option("--batch-poll-seconds", type=int, default=30, show_default=True)
@click.option("--batch-wait-timeout-seconds", type=int, default=86400, show_default=True)
@click.option("--batch-max-requests-per-job", type=int, default=2000, show_default=True)
@click.option("--allow-multi-phase-live-batch", is_flag=True, default=False, show_default=True)
@click.option("--ui", type=click.Choice(["auto", "rich", "plain"]), default="auto", show_default=True)
@click.option("--pretty", is_flag=True, default=False, show_default=True)
@click.option("--quiet", is_flag=True, default=False, show_default=True)
@click.option("--jsonl-events", is_flag=True, default=False, show_default=True)
@click.option(
    "--sync/--no-sync",
    default=True,
    show_default=True,
    help="🔄 State Sync: Sync local artifacts before ignition (v4 only).",
)
@click.pass_context
def extractor_run(
    ctx,
    pipeline_version: str,
    engine_version_legacy: Optional[str],
    phase: str,
    step: Optional[str],
    s_steps: Optional[str],
    run_id: Optional[str],
    promptset_root: Optional[str],
    dry_run: bool,
    resume: bool,
    partition_workers: int,
    max_partitions_per_step: Optional[int],
    routing_policy: Optional[str],
    disable_escalation: bool,
    escalation_max_hops: int,
    batch_mode: bool,
    batch_submit_only: bool,
    batch_watch: bool,
    batch_retrieve: bool,
    batch_ids: tuple[str, ...],
    batch_provider: str,
    retrieve_provider: str,
    batch_poll_seconds: int,
    batch_wait_timeout_seconds: int,
    batch_max_requests_per_job: int,
    allow_multi_phase_live_batch: bool,
    ui: str,
    pretty: bool,
    quiet: bool,
    jsonl_events: bool,
    sync: bool,
):
    """
    🚀 Ignite Pipeline: Run the Repo Truth Extractor (resumable)

    Engages the high-fidelity extraction engines to process the codebase 
    according to the active ritual promptset and routing policies.
    """
    effective_version = _resolved_pipeline_version(
        pipeline_version, engine_version_legacy
    )
    effective_routing_policy = routing_policy or (
        _V5_DEFAULT_ROUTING_POLICY
        if effective_version == "v5"
        else _LEGACY_DEFAULT_ROUTING_POLICY
    )
    args: List[str] = []
    if phase:
        args.extend(["--phase", phase])
    if step:
        args.extend(["--step", step])
    if s_steps:
        args.extend(["--s-steps", s_steps])
    if run_id:
        args.extend(["--run-id", run_id])
    if promptset_root:
        args.extend(["--promptset-root", promptset_root])
    if dry_run:
        args.append("--dry-run")
    if resume:
        args.append("--resume")
    args.extend(["--partition-workers", str(partition_workers)])
    if max_partitions_per_step is not None:
        args.extend(["--max-partitions-per-step", str(max(0, int(max_partitions_per_step)))])
    args.extend(["--routing-policy", effective_routing_policy])
    if disable_escalation:
        args.append("--disable-escalation")
    args.extend(["--escalation-max-hops", str(max(0, int(escalation_max_hops)))])
    if batch_mode:
        args.append("--batch-mode")
    if batch_submit_only:
        args.append("--batch-submit-only")
    if batch_watch:
        args.append("--batch-watch")
    if batch_retrieve:
        args.append("--batch-retrieve")
    for batch_id in batch_ids:
        args.extend(["--batch-ids", batch_id])
    args.extend(["--batch-provider", batch_provider])
    args.extend(["--retrieve-provider", retrieve_provider])
    args.extend(["--batch-poll-seconds", str(max(1, int(batch_poll_seconds)))])
    args.extend(["--batch-wait-timeout-seconds", str(max(60, int(batch_wait_timeout_seconds)))])
    args.extend(["--batch-max-requests-per-job", str(max(1, int(batch_max_requests_per_job)))])
    if allow_multi_phase_live_batch:
        args.append("--allow-multi-phase-live-batch")
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
@click.option("--run-id", default=None, help="🆔 Ritual Session: Unique identifier for the extraction run to diagnose.")
@click.option("--auto-reprocess/--no-auto-reprocess", default=False, show_default=True, help="🔧 Auto-Remediation: Automatically re-process failed partitions identified during the audit.")
@click.option(
    "--reprocess-dry-run/--no-reprocess-dry-run", default=False, show_default=True, help="🔬 Ritual Preview: Simulate the re-processing sequence without committing to disk."
)
@click.option("--reprocess-phases", default="", help="📊 Targeted Phases: Comma-separated list of extraction phases to audit.")
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
    🏥 Extraction Apothecary: Run diagnostics and deterministic re-process planning

    Performs a high-fidelity audit of an extraction session, identifying 
    structural hazards and proposing a deterministic re-synchronization plan 
    for failed partitions.
    """
    effective_version = _resolved_pipeline_version(
        pipeline_version, engine_version_legacy
    )
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
@click.option("--run-id", default=None, help="🆔 Ritual Session: Unique identifier for the extraction run to query.")
@click.option("--json", "status_json", is_flag=True, help="📊 Emit JSON: Output the ritual status as raw machine-readable data.")
@click.pass_context
def extractor_status(
    ctx,
    pipeline_version: str,
    engine_version_legacy: Optional[str],
    run_id: Optional[str],
    status_json: bool,
):
    """
    📊 Ritual Status: Show status of an extraction run

    Retrieves current cockpit telemetry for a specific extraction session, 
    detailing phase progression and partition status.
    """
    effective_version = _resolved_pipeline_version(
        pipeline_version, engine_version_legacy
    )
    args: List[str] = ["--status-json" if status_json else "--status"]
    if run_id:
        args.extend(["--run-id", run_id])
    _run_extractor_runner(pipeline_version=effective_version, args=args)


@upgrades.command("preflight")
@_pipeline_version_options
@click.option("--run-id", default=None, help="Run ID")
@click.option(
    "--promptset-root",
    type=click.Path(exists=True, file_okay=False),
    default=None,
    help="External generated promptset directory for v5 prompt resolution.",
)
@click.option("--auth-doctor", is_flag=True, help="Also run auth diagnostics")
@click.pass_context
def extractor_preflight(
    ctx,
    pipeline_version: str,
    engine_version_legacy: Optional[str],
    run_id: Optional[str],
    promptset_root: Optional[str],
    auth_doctor: bool,
):
    """
    🛫 Pre-Ignition Check: Run pre-flight diagnostics for an extraction run

    Executes a comprehensive sensor audit before starting an extraction 
    ritual, ensuring all directories are mounted and providers are synchronized.
    """
    effective_version = _resolved_pipeline_version(
        pipeline_version, engine_version_legacy
    )
    args: List[str] = ["--preflight-providers"]
    if run_id:
        args.extend(["--run-id", run_id])
    if promptset_root:
        args.extend(["--promptset-root", promptset_root])
    _run_extractor_runner(pipeline_version=effective_version, args=args)
    if auth_doctor:
        auth_args = ["--doctor-auth"]
        if run_id:
            auth_args.extend(["--run-id", run_id])
        if promptset_root:
            auth_args.extend(["--promptset-root", promptset_root])
        _run_extractor_runner(pipeline_version=effective_version, args=auth_args)


@upgrades.command("validate-live")
@click.option(
    "--promptset-root",
    type=click.Path(exists=True, file_okay=False),
    required=True,
    help="External generated promptset directory to validate and use for paid stages.",
)
@click.option(
    "--stage",
    type=click.Choice(["preflight", "provider_probe", "batch_pilot", "phase_slice", "full_phased"]),
    default="preflight",
    show_default=True,
    help="Validation stage to run. Paid stages include all earlier gates automatically.",
)
@click.option("--run-id", default=None, help="Validation run ID.")
@click.option(
    "--report-root",
    type=click.Path(file_okay=False),
    default="reports/repo-truth-extractor/validation",
    show_default=True,
    help="Directory where validation ledgers, logs, and reports are written.",
)
@click.option(
    "--routing-policy",
    type=click.Choice(_ROUTING_POLICY_CHOICES),
    default=_V5_DEFAULT_ROUTING_POLICY,
    show_default=True,
    help="Routing policy used for v5 dry-runs, canary, and full execution.",
)
@click.option("--tp008-map", type=click.Path(exists=True, dir_okay=False), default=None, help="Optional canonical TP-008 mapping file.")
@click.option(
    "--pricing-manifest",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Required for paid slice/full stages. JSON file with route_call_upper_bounds for spend caps.",
)
@click.option("--provider", type=click.Choice(["openai", "gemini", "xai"]), default=None, help="Preferred provider for paid probe and batch stages.")
@click.option("--ui", "ui_mode", type=click.Choice(["auto", "rich", "plain"]), default="auto", show_default=True)
@click.option("--provider-probe-phase", type=click.Choice(["D", "C", "Q"]), default="D", show_default=True)
@click.option("--provider-probe-step", default=None, help="Optional concrete step for the provider probe stage.")
@click.option("--provider-probe-max-usd", type=float, default=0.10, show_default=True)
@click.option("--provider-probe-max-minutes", type=float, default=5.0, show_default=True)
@click.option("--batch-pilot-phase", type=click.Choice(["D", "C", "Q"]), default="D", show_default=True)
@click.option("--batch-pilot-step", default=None, help="Optional concrete step for the batch pilot stage.")
@click.option("--batch-pilot-max-usd", type=float, default=1.0, show_default=True)
@click.option("--batch-pilot-max-minutes", type=float, default=15.0, show_default=True)
@click.option("--phase-slice-docs-phase", type=click.Choice(["D"]), default="D", show_default=True)
@click.option("--phase-slice-code-phase", type=click.Choice(["C", "Q"]), default="C", show_default=True)
@click.option("--phase-slice-synth-phase", type=click.Choice(["R", "S"]), default="R", show_default=True)
@click.option("--phase-slice-max-usd", type=float, default=5.0, show_default=True)
@click.option("--phase-slice-max-minutes", type=float, default=45.0, show_default=True)
@click.option("--full-max-usd", type=float, default=75.0, show_default=True)
@click.option("--full-max-minutes", type=float, default=240.0, show_default=True)
@click.pass_context
def extractor_validate_live(
    ctx,
    promptset_root: str,
    stage: str,
    run_id: Optional[str],
    report_root: str,
    routing_policy: str,
    tp008_map: Optional[str],
    pricing_manifest: Optional[str],
    provider: Optional[str],
    ui_mode: str,
    provider_probe_phase: str,
    provider_probe_step: Optional[str],
    provider_probe_max_usd: float,
    provider_probe_max_minutes: float,
    batch_pilot_phase: str,
    batch_pilot_step: Optional[str],
    batch_pilot_max_usd: float,
    batch_pilot_max_minutes: float,
    phase_slice_docs_phase: str,
    phase_slice_code_phase: str,
    phase_slice_synth_phase: str,
    phase_slice_max_usd: float,
    phase_slice_max_minutes: float,
    full_max_usd: float,
    full_max_minutes: float,
):
    """
    Run the fail-closed v5 live validation workflow.

    \b
    Examples:
      dopemux upgrades validate-live --promptset-root /tmp/promptset
      dopemux upgrades validate-live --stage provider_probe --promptset-root /tmp/promptset
      dopemux upgrades validate-live --stage phase_slice --promptset-root /tmp/promptset --pricing-manifest pricing.json
      dopemux upgrades validate-live --stage full_phased --promptset-root /tmp/promptset --pricing-manifest pricing.json
    """
    payload = run_live_validation(
        ValidationConfig(
            promptset_root=Path(promptset_root),
            stage=stage,
            run_id=run_id,
            report_root=Path(report_root),
            ui_mode=ui_mode,
            routing_policy=routing_policy,
            provider_probe_phase=provider_probe_phase,
            provider_probe_step=provider_probe_step,
            provider_probe_max_usd=provider_probe_max_usd,
            provider_probe_max_minutes=provider_probe_max_minutes,
            batch_pilot_phase=batch_pilot_phase,
            batch_pilot_step=batch_pilot_step,
            batch_pilot_max_usd=batch_pilot_max_usd,
            batch_pilot_max_minutes=batch_pilot_max_minutes,
            canary_phases=(phase_slice_docs_phase, phase_slice_code_phase, phase_slice_synth_phase),
            phase_slice_max_usd=phase_slice_max_usd,
            phase_slice_max_minutes=phase_slice_max_minutes,
            full_max_usd=full_max_usd,
            full_max_minutes=full_max_minutes,
            tp008_map=Path(tp008_map) if tp008_map else None,
            pricing_manifest=Path(pricing_manifest) if pricing_manifest else None,
            selected_provider=provider,
        )
    )
    report_path = Path(report_root) / payload["run_id"] / "VALIDATION_REPORT.json"
    console.logger.info(f"validation_report={report_path}")
    if payload.get("status") != "pass":
        blockers = payload.get("blockers") or ["Live validation failed."]
        raise click.ClickException(f"{blockers[0]} See {report_path}.")


@upgrades.group("promptset")
def upgrades_promptset_group():
    """Promptset utilities."""
    pass


@upgrades_promptset_group.command("audit")
@_pipeline_version_options
@click.option("--strict/--no-strict", default=True, show_default=True, help="🛡️  Enforce Constraints: Perform a strict structural audit of the promptset artifacts.")
@click.pass_context
def extractor_promptset_audit(
    ctx,
    pipeline_version: str,
    engine_version_legacy: Optional[str],
    strict: bool,
):
    """
    ⚖️ Ritual Integrity: Audit promptset contract compliance

    Performs a deep-tissue audit of the promptset to ensure compliance with 
    ritual contracts, including required sections, schemas, and determinism.

    \b
    Example:
      dopemux upgrades promptset audit --pipeline-version v4 --strict
    """
    effective_version = _resolved_pipeline_version(
        pipeline_version, engine_version_legacy
    )
    if effective_version == "v4":
        args = [
            "--promptset-audit",
            "--strict-audit" if strict else "--no-strict-audit",
        ]
        _run_extractor_runner(pipeline_version="v4", args=args)
        return
    raise click.ClickException("Promptset audit is implemented for v4 only.")


@upgrades.command("trace")
@click.option(
    "--dry-run",
    is_flag=True,
    default=True,
    help="Run the canonical v5 extractor in dry-run mode (default).",
)
@click.option(
    "--execute", is_flag=True, help="Actually call LLM providers (if configured)."
)
@click.option("--phase", help="Run only a specific phase (A, H, D, C, R, S, or ALL).")
@click.pass_context
def extractor_trace(ctx, dry_run: bool, execute: bool, phase: Optional[str]):
    """Compatibility alias for canonical v5 dry-run extraction."""
    del ctx
    if execute:
        dry_run = False
    args: List[str] = ["--phase", phase or "ALL"]
    if dry_run:
        args.append("--dry-run")
    _run_extractor_runner(pipeline_version="v5", args=args)


@cli.command("truth")
@click.option(
    "--dry-run", is_flag=True, default=True, help="🔬 Ritual Preview: Simulate execution without committing to disk (default)."
)
@click.option("--execute", is_flag=True, help="⚡ Ignite Ritual: Actually call LLM providers for extraction.")
@click.option(
    "--deep", is_flag=True, help="🌊 Deep Harvest: Compatibility flag only; canonical v5 does not support legacy deep mode."
)
@click.option("--resume", is_flag=True, help="⏯️  Resume Sequence: Resume a previously suspended extraction run.")
@click.option(
    "--workers", type=int, default=1, help="⚡ Ritual Workers: Number of parallel extraction workers (default: 1)."
)
@click.option(
    "--routing-policy",
    type=click.Choice(["cost", "balanced", "quality", "optimal"]),
    default="cost",
    help="🧠 Cognitive Routing: Intelligence routing policy (default: cost).",
)
@click.pass_context
def truth_command(
    ctx,
    dry_run: bool,
    execute: bool,
    deep: bool,
    resume: bool,
    workers: int,
    routing_policy: str,
):
    """
    👁️  Truth Extraction: Compatibility alias for canonical v5 extraction

    Routes directly to the canonical v5 extractor with ``--phase ALL``.
    """
    del ctx
    if execute:
        dry_run = False
    if deep:
        raise click.ClickException(
            "`dopemux truth --deep` is not supported on the canonical v5 path. "
            "Use `dopemux upgrades run --pipeline-version v5` with explicit promptset and phase controls."
        )
    _run_truth_v5_alias(
        phase="ALL",
        dry_run=dry_run,
        resume=resume,
        workers=workers,
        routing_policy=routing_policy,
    )


def _add_extractor_alias_if_missing(command, name: str) -> None:
    if name not in extractor.commands:
        extractor.add_command(command, name)


_add_extractor_alias_if_missing(extractor_list, "list")
_add_extractor_alias_if_missing(extractor_run, "run")
_add_extractor_alias_if_missing(extractor_doctor, "doctor")
_add_extractor_alias_if_missing(extractor_status, "status")
_add_extractor_alias_if_missing(extractor_preflight, "preflight")
_add_extractor_alias_if_missing(extractor_trace, "trace")


@extractor.group("promptset")
def extractor_promptset_group():
    """Promptset utilities (legacy alias for upgrades promptset)."""
    pass


extractor_promptset_group.add_command(extractor_promptset_audit, "audit")


# from src/dopemux/commands/memory_commands.py
@cli.command("launch")
@click.option(
    "--preset",
    type=click.Choice(
        ["minimal", "standard", "full", "dope-muted", "dope-neon", "dope-house"]
    ),
    default="standard",
    help="🎭 HUD Preset: Select an opinionated cockpit configuration for ignition.",
)
@click.option(
    "--attach/--no-attach", default=True, help="⚡ Auto-Attach: Immediately engage the cockpit after materialization."
)
@click.pass_context
def launch(ctx, preset: str, attach: bool):
    """
    🚀 Ignite Cockpit: Quick launch with opinionated presets

    Materializes the DØPEMÜX cockpit using high-fidelity presets. 
    Synchronizes layout, themes, and daemon configurations to align 
    with the selected mission profile.
    """
    import subprocess
    import time

    from .tmux.controller import TmuxController
    from .ui.splash import boot_sequence
    
    boot_sequence()

    console.logger.info(
        f"[info]🚀 Launching Dopemux with '{preset}' preset...[/info]\n"
    )

    if preset == "minimal":
        # Just start Claude Code, no tmux
        console.logger.info("[text.dim]Starting Claude Code without tmux...[/text.dim]")
        ctx.invoke(cli.commands["start"])
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
    console.logger.info(f"[info]📐 Creating {layout} layout...[/info]")

    tmux_start_args = [
        "dopemux",
        "tmux",
        "start",
        "--layout",
        layout,
        "--bootstrap",
    ]

    if not attach:
        tmux_start_args.append("--no-attach")

    # Start the session
    subprocess.run(tmux_start_args, check=True)

    autoindex_result = _trigger_dope_context_autoindex_startup(Path.cwd())
    if autoindex_result and autoindex_result.get("status") in {
        "started",
        "already_running",
    }:
        console.logger.info(
            "[text.dim]✅ Dope-context autoindex bootstrap triggered[/text.dim]"
        )

    # Apply theme if specified
    if theme:
        console.logger.info(f"\n[magenta]🎨 Applying {theme} theme...[/magenta]")
        time.sleep(1)  # Give tmux time to initialize
        subprocess.run(["dopemux", "tmux", "theme", theme, "--apply"], check=True)
        console.logger.info(f"[success]✨ {preset} preset ready![/success]")
    else:
        console.logger.info(f"[success]✨ {preset} preset ready![/success]")


@cli.command("dope")
@click.option(
    "--theme",
    type=click.Choice(["muted", "neon", "house"]),
    default="muted",
    help="🎭 Ritual Aesthetic: Select the visual theme for the DOPE layout.",
)
@click.option("--attach/--no-attach", default=True, help="⚡ Auto-Attach: Immediately engage the cockpit after materialization.")
@click.pass_context
def dope(ctx, theme: str, attach: bool):
    """
    🔥 Engage DOPE Ritual: Launch full high-fidelity cockpit (Shortcut)

    Materializes the complete DØPEMÜX experience, including the full DOPE 
    layout, dual-agent orchestrators, and high-fidelity dashboard panels.
    """
    preset = f"dope-{theme}"
    ctx.invoke(launch, preset=preset, attach=attach)


@cli.command("quick")
@click.pass_context
def quick(ctx):
    """
    ⚡ Streamlined Ignition: Fastest cockpit launch (Shortcut)

    Engages the high-velocity startup sequence, materializing a medium 
    layout cockpit for rapid ritual execution without full monitoring overhead.
    """
    console.print("[info]⚡ Quick start - medium layout[/info]\n")
    import subprocess

    subprocess.run(
        [
            "dopemux",
            "tmux",
            "start",
            "--layout",
            "medium",
        ],
        check=True,
    )


# from src/dopemux/commands/profile_commands.py
@cli.command("shell-setup")
@click.argument("shell_type", type=click.Choice(["bash", "zsh"], case_sensitive=False))
@click.pass_context
def shell_setup_cmd(ctx, shell_type: str):
    """
    🐚 Engage Shell Uplink: Output integration code for worktree switching

    Materializes high-fidelity shell functions to enable seamless worktree 
    transitions. Since Python daemons cannot directly manipulate the 
    parent shell's coordinates, these rituals provide the necessary hooks 
    for contextual 'cd' operations.
    """
    import importlib.resources

    # Read the shell integration script
    script_path = (
        Path(__file__).parent.parent.parent / "scripts" / "shell_integration.sh"
    )

    if not script_path.exists():
        click.secho(
            f"❌ Shell integration script not found: {script_path}", fg="red", err=True
        )
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


# =============================================================================
# Dashboard TUI Command
# =============================================================================


@cli.command("dashboard")
@click.option(
    "--demo", is_flag=True, help="🧪 Simulation Ritual: Run with mock telemetry (no live daemons required)."
)
def dashboard_cmd(demo: bool):
    """
    📊 Cockpit HUD: Launch the high-fidelity TUI dashboard

    Engages the real-time monitoring HUD for ADHD state, ritual productivity 
    metrics, daemon health, and cognitive load trends. Synchronizes across 
    all active sensors to provide a unified telemetry stream.
    """
    from .ui.dashboard import run_dashboard

    run_dashboard(demo=demo)


# Worktree Diagnostics Command
# =============================================================================


def _activate_dangerous_mode() -> None:
    """Enable session-scoped dangerous mode environment flags."""
    expires = time.time() + 3600
    os.environ["DOPEMUX_DANGEROUS_MODE"] = "true"
    os.environ["DOPEMUX_DANGEROUS_EXPIRES"] = str(expires)
    os.environ["HOOKS_ENABLE_ADAPTIVE_SECURITY"] = "0"
    os.environ["CLAUDE_CODE_SKIP_PERMISSIONS"] = "true"
    os.environ["METAMCP_ROLE_ENFORCEMENT"] = "false"
    os.environ["METAMCP_APPROVAL_REQUIRED"] = "false"
    os.environ["METAMCP_BUDGET_ENFORCEMENT"] = "false"
    os.environ["CLAUDE_DANGEROUS"] = "1"
    os.environ["SKIP_PERMISSIONS"] = "1"


def _deactivate_dangerous_mode() -> None:
    """Clear dangerous mode environment flags when they expire."""
    for key in [
        "DOPEMUX_DANGEROUS_MODE",
        "DOPEMUX_DANGEROUS_EXPIRES",
        "HOOKS_ENABLE_ADAPTIVE_SECURITY",
        "CLAUDE_CODE_SKIP_PERMISSIONS",
        "METAMCP_ROLE_ENFORCEMENT",
        "METAMCP_APPROVAL_REQUIRED",
        "METAMCP_BUDGET_ENFORCEMENT",
        "CLAUDE_DANGEROUS",
        "SKIP_PERMISSIONS",
    ]:
        os.environ.pop(key, None)


def _check_dangerous_mode_expiry() -> bool:
    """Deactivate dangerous mode after its session TTL elapses."""
    if os.getenv("DOPEMUX_DANGEROUS_MODE") != "true":
        return False

    expires_raw = os.getenv("DOPEMUX_DANGEROUS_EXPIRES", "0")
    try:
        expires_at = float(expires_raw)
    except ValueError:
        expires_at = 0.0

    if time.time() >= expires_at:
        _deactivate_dangerous_mode()
        return True

    return False


@cli.command("doctor")
@click.option("--worktree", is_flag=True, help="🔬 Focus Chamber: Run worktree-specific diagnostics.")
@click.option("--verbose", "-v", is_flag=True, help="📊 Deep Telemetry: Show high-fidelity diagnostic information.")
@click.pass_context
def doctor_cmd(ctx, worktree: bool, verbose: bool):
    """
    🏥 System Apothecary: Run diagnostics and health checks

    Performs a comprehensive structural audit of the DØPEMÜX configuration, 
    workspace detection sensors, MCP server stability, and worktree 
    synchronization. Ensures the ritual chamber is primed for high-fidelity 
    execution.
    """
    if worktree:
        # Phase 1-3 worktree diagnostics
        from .worktree_diagnostics import run_diagnostics

        success = run_diagnostics(verbose=verbose)
        sys.exit(0 if success else 1)
    else:
        # General Dopemux health check
        console.logger.info("\n[mint]🏥 Dopemux System Diagnostics[/mint]\n")
        console.logger.info(
            "[warning]Use --worktree flag for worktree-specific checks[/warning]\n"
        )

        # Basic checks
        checks = []

        config_manager: ConfigManager = (
            ctx.obj.get("config_manager") if ctx.obj else ConfigManager()
        )
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
            subprocess.run(
                ["docker", "version"], capture_output=True, check=True, timeout=5
            )
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
            checks.append(
                (f"Happy relay reachable ({mobile_cfg.happy_server_url})", reachable)
            )

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

        passed = sum(1 for _, r in checks if r)

        def _rich_doctor():
            table = styled_table(
                f"{Glyphs.INFO} System Diagnostics",
                ("Check", {"style": "text"}),
                ("Status",),
            )
            for check_name, result in checks:
                status = (
                    "[success]✅ Pass[/success]" if result else "[error]❌ Fail[/error]"
                )
                table.add_row(check_name, status)
            console.logger.info(table)
            console.logger.info(
                f"\n[bold]Result:[/bold] {passed}/{len(checks)} checks passed"
            )
            if passed == len(checks):
                console.logger.info("[success]🎉 System healthy![/success]")
            else:
                console.logger.error(
                    "[warning]⚠️  Some checks failed. See above for details.[/warning]"
                )

        emit(
            ctx,
            data={
                "checks": [{"name": n, "passed": r} for n, r in checks],
                "passed": passed,
                "total": len(checks),
                "healthy": passed == len(checks),
            },
            rich_render=_rich_doctor,
        )

        sys.exit(0 if passed == len(checks) else 1)


# ============================================================================
# Decision Management Commands (ConPort Enhancement Quick Wins)
# ============================================================================


# from src/dopemux/commands/workflow_group_commands.py
@cli.command("layouts")
def layouts():
    """
    📐 Catalog Cockpit Architectures: Show available layouts and themes

    Displays the index of available cockpit layouts and visual themes. 
    Provides high-fidelity descriptions and usage guidelines for optimizing 
    the cockpit aesthetic and structural alignment.
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
        console.logger.info("\n[warning]⏸️ Interrupted by user[/warning]")
        sys.exit(1)
    except Exception as e:
        error_text = Text(f"{Glyphs.ERROR} Error: ", style="error") + Text(str(e))
        console.logger.error(error_text)
        if "--debug" in sys.argv:
            raise
        sys.exit(1)


@cli.command("hooks")
@click.option("--setup", is_flag=True, help="🚀 Ignite Sensors: Start monitoring Claude Code activity signals.")
@click.option("--teardown", is_flag=True, help="⏹️ Halt Sensors: Stop monitoring Claude Code activity.")
@click.option("--status", is_flag=True, help="📊 Sensor HUD: Show current hook operational status.")
@click.option(
    "--enable",
    help="⚡ Engage Sensor: Enable specific hook type (session-start, file-change, shell-command, git-commit).",
)
@click.option(
    "--disable",
    help="⏸️  Silence Sensor: Disable specific hook type.",
)
@click.option("--shell-scripts", is_flag=True, help="🐚 Generate Rituals: Generate shell hook scripts for manual uplink.")
@click.option(
    "--install-shell-hooks", is_flag=True, help="⚡ Commit Uplink: Install shell hooks into system shell configuration."
)
@click.option(
    "--uninstall-shell-hooks",
    is_flag=True,
    help="🔌 Sever Uplink: Uninstall shell hooks from shell configuration.",
)
@click.option(
    "--workspace",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help="🔬 Ritual Chamber: Target workspace for hook synchronization.",
)
@click.option("--force", is_flag=True, help="⚡ Force Extraction: Overwrite safety interlocks for hook operations.")
@click.pass_context
def hooks_cmd(
    ctx,
    setup,
    teardown,
    status,
    enable,
    disable,
    shell_scripts,
    install_shell_hooks,
    uninstall_shell_hooks,
    workspace,
    force,
):
    """
    🔗 Event Synchronization: Manage Claude Code integration hooks

    Orchestrates the high-fidelity monitoring of Claude Code activity signals. 
    This system synchronizes shell rituals, file system modifications, and 
    git telemetry into the per-project Chronicle ledger.
    """
    try:
        from .hooks.claude_code_hooks import claude_hooks, get_shell_hook_scripts

        if setup:
            claude_hooks.start_monitoring(workspace)
            console.logger.info("[success]✅ Claude Code hooks started[/success]")
            console.logger.info(
                f"   Monitoring paths: {[str(p) for p in claude_hooks.watched_paths]}"
            )

        elif teardown:
            claude_hooks.stop_monitoring()
            console.logger.info("[success]✅ Claude Code hooks stopped[/success]")

        elif status:
            hook_status = claude_hooks.get_status()
            console.logger.info("[bold]Claude Code Hook Status:[/bold]")
            console.logger.info(
                f"   Monitoring active: {hook_status['monitoring_active']}"
            )
            console.logger.info(f"   Quiet mode: {hook_status['quiet_mode']}")
            console.logger.info(f"   Watched paths: {hook_status['watched_paths']}")
            console.logger.info("\n[bold]Hook Types:[/bold]")
            for hook_type, enabled in hook_status["active_hooks"].items():
                status_icon = "[success]✓[/success]" if enabled else "[error]✗[/error]"
                console.logger.info(f"   {status_icon} {hook_type}")

        elif enable:
            claude_hooks.enable_hook(enable)
            console.logger.info(f"[success]✅ Hook enabled: {enable}[/success]")

        elif disable:
            claude_hooks.disable_hook(disable)
            console.logger.info(f"[success]✅ Hook disabled: {disable}[/success]")

        elif shell_scripts:
            scripts = get_shell_hook_scripts()
            console.logger.info("[bold]Shell Hook Scripts:[/bold]")
            console.logger.info(
                "\n[text.dim]Add these to your ~/.bashrc or ~/.zshrc:[/text.dim]\n"
            )

            console.logger.info("[mint]For Bash:[/mint]")
            console.logger.info(scripts["bash_preexec"])
            console.logger.info(scripts["bash_precmd"])

            console.logger.info("\n[mint]For Zsh:[/mint]")
            console.logger.info(scripts["zsh_hooks"])

        elif install_shell_hooks:
            from .hooks.shell_hook_installer import install_shell_hooks as installer

            success, message = installer(force=force)
            if success:
                console.logger.info(f"[success]{message}[/success]")
            else:
                console.logger.info(f"[error]{message}[/error]")
                sys.exit(1)

        elif uninstall_shell_hooks:
            from .hooks.shell_hook_installer import uninstall_shell_hooks as uninstaller

            success, message = uninstaller()
            if success:
                console.logger.info(f"[success]{message}[/success]")
            else:
                console.logger.info(f"[error]{message}[/error]")
                sys.exit(1)

        else:
            # Default: show help
            console.logger.info("[bold]Dopemux Hook System[/bold]")
            console.logger.info("Manage external hooks for Claude Code integration.\n")
            console.logger.info("[bold]Commands:[/bold]")
            console.logger.info(
                "   --setup               Start monitoring Claude Code activity"
            )
            console.logger.info("   --teardown            Stop monitoring")
            console.logger.info("   --status              Show current hook status")
            console.logger.info("   --enable HOOK         Enable specific hook type")
            console.logger.info("   --disable HOOK        Disable specific hook type")
            console.logger.info("   --shell-scripts       Generate shell hook scripts")
            console.logger.info(
                "   --install-shell-hooks Install shell hooks in shell config"
            )
            console.logger.info(
                "   --uninstall-shell-hooks Remove shell hooks from shell config"
            )
            console.logger.info("   --workspace PATH      Set workspace to monitor")
            console.logger.info(
                "   --force               Force operations (e.g., reinstall)\n"
            )
            console.logger.info("[bold]Hook Types:[/bold]")
            console.logger.info("   session-start    Monitor Claude Code process start")
            console.logger.info("   file-change      Monitor file modifications")
            console.logger.info("   shell-command    Monitor shell commands")
            console.logger.info(
                "   git-commit       Monitor git operations (disabled by default)"
            )

    except Exception as e:
        console.logger.error(f"[error]❌ Hook command failed: {e}[/error]")
        if ctx.obj.get("verbose"):
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
