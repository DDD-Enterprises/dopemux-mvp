## pyproject.toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "dopemux"
version = "0.1.0"
description = "ADHD-optimized development platform that wraps Claude Code with custom configurations"
readme = "README.md"
requires-python = ">=3.11,<3.14"
license = {text = "MIT"}
authors = [
    {name = "Dopemux Team", email = "team@dopemux.dev"},
]
keywords = ["adhd", "development", "ai", "claude", "productivity"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
    "Topic :: Software Development :: Tools",
    "Topic :: Scientific/Engineering :: Human Machine Interfaces",
]

dependencies = [
    "click>=8.0.0",
    "pyyaml>=6.0",
    "questionary>=2.0.1",
    "rich>=13.0.0",
    "textual>=0.54.0",
    "readchar>=4.2.1",
    "requests>=2.28.0",
    "openai>=1.50.0",
    "google-genai>=1.0.0",
    "aiohttp>=3.14.0",
    "watchdog>=3.0.0",
    "python-dateutil>=2.8.2",
    "python-dotenv>=1.2.2",
    "filelock>=3.12.0",
    "jinja2>=3.1.0",
    "sqlite-utils>=3.30.0",
    "psutil>=5.9.0",
    "pydantic>=2.7.0",
    "toml>=0.10.0",
    "docker>=7.0.0",
    "litellm>=1.83.7",
    "fastapi>=0.115.12",
    "uvicorn[standard]>=0.32.0",
    "redis>=5.0.1",
    # Document processing dependencies
    "chardet>=5.0.0",
    "pymilvus>=2.3.0",
    "voyageai>=0.2.0",
    "numpy>=1.24.0",
    "scipy>=1.10.0",
    "scikit-learn>=1.3.0",
    "pandas>=2.0.0",
    "markdown>=3.4.0",
    "python-docx>=0.8.11",
    "pdfplumber>=0.9.0",
]

[project.optional-dependencies]
test = [
    "pytest>=9.0.3",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.12.0",
    "pytest-xdist>=3.6.1",
]
dev = [
    "pytest>=9.0.3",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.12.0",
    "pytest-xdist>=3.6.1",
    "black>=23.0.0",
    "isort>=5.12.0",
    "flake8>=6.0.0",
    "mypy>=1.0.0",
    "pre-commit>=3.0.0",
    "pip-audit>=2.7.0",
    "bandit>=1.7.0",
    "semgrep>=1.90.0",
    "dopetask==0.5.1",
]
services = [
    "asyncpg>=0.29.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "tree-sitter>=0.25.2",
    "tree-sitter-python==0.23.0",
    "tree-sitter-javascript==0.23.0",
    "tree-sitter-typescript==0.23.0",
    "tree-sitter-go==0.23.0",
    "tree-sitter-rust==0.23.0",
    "fastmcp",
    "httpx>=0.28.1",
    "pydantic-settings>=2.1.0",
    "python-jose[cryptography]>=3.5.0",
    "mcp>=1.23.3",
    "tenacity>=8.2.3",
    "structlog>=24.1.0",
    "prometheus-client>=0.19.0",
    "pyjwt>=2.8.0",
    "cryptography>=41.0.0",
    "passlib[bcrypt]>=1.7.4",
    "celery[redis]>=5.3.0",
    "kombu>=5.3.0",
    "qdrant-client>=1.15.0",
    "pymupdf>=1.23.0",
    "beautifulsoup4>=4.12.0",
    "lxml>=6.1.0",
    "rank_bm25",
    "python-multipart>=0.0.27",
    "aioredis>=2.0.1",
    "asyncio-mqtt>=0.16.0",
    "aiofiles>=23.2.1",
    "psycopg2-binary>=2.9.7",
    "alembic>=1.12.0",
    "pytz>=2023.3",
    "orjson>=3.9.0",
    "msgpack>=1.0.7",
    "anthropic>=0.18.0",
]
all = [
    "dopemux[dev,services]",
]

[project.urls]
Homepage = "https://github.com/dopemux/dopemux-mvp"
Repository = "https://github.com/dopemux/dopemux-mvp"
Issues = "https://github.com/dopemux/dopemux-mvp/issues"
Documentation = "https://docs.dopemux.dev"

[project.scripts]
dopemux = "dopemux.cli:main"
dopemux-mobile = "dopemux.mobile.main:main"
dopemux-github = "dopemux_github_specialist.cli:main"
dopemux-pr-merge = "dopemux_pr_merge_specialist.cli:main"
dopemux-pr-steward = "dopemux_pr_steward.cli:main"

[tool.setuptools]
packages = [
    "conport",
    "core",
    "core.config",
    "dopemux",
    "dopemux.adhd",
    "dopemux.agent",
    "dopemux.analysis",
    "dopemux.claude",
    "dopemux.claude_tools",
    "dopemux.commands",
    "dopemux.config",
    "dopemux.conport",
    "dopemux.core_logging",
    "dopemux.embeddings",
    "dopemux.embeddings.core",
    "dopemux.embeddings.enhancers",
    "dopemux.embeddings.integrations",
    "dopemux.embeddings.pipelines",
    "dopemux.embeddings.providers",
    "dopemux.embeddings.storage",
    "dopemux.events",
    "dopemux.execution",
    "dopemux.extraction",
    "dopemux.extractor",
    "dopemux.hooks",
    "dopemux.logging",
    "dopemux.mcp",
    "dopemux.memory",
    "dopemux.memory.adapters",
    "dopemux.mobile",
    "dopemux.orchestrator",
    "dopemux.orchestrator.automation",
    "dopemux.orchestrator.ui",
    "dopemux.orchestrator.validation",
    "dopemux.pm",
    "dopemux.pm.adapters",
    "dopemux.roles",
    "dopemux.service_base",
    "dopemux.system_data",
    "dopemux.templates",
    "dopemux.tools",
    "dopemux.tmux",
    "dopemux.tui",
    "dopemux.tui.widgets",
    "dopemux.ui",
    "dopemux.ui.cockpit",
    "dopemux.update",
    "dopemux.upgrades",
    "dopemux.utils",
    "dopemux.ux",
    "dopemux.ux.wizard",
    "dopemux.voice",
    "dopemux.workflow",
    "dopemux_github_specialist",
    "dopemux_github_specialist.gemini",
    "dopemux_github_specialist.github",
    "dopemux_pr_merge_specialist",
    "dopemux_pr_steward",
    "integrations",
    "tools",
    "tools.auditor_router",
    "tools.copilot_repair",
    "tools.prompt_rewrite_v4",
    "tools.prompt_rewrite_v4.benchmark",
    "tools.pr_action_bridge",
    "tools.pr_steward",
    "utils",
]

[tool.setuptools.package-dir]
"" = "src"
"tools" = "tools"
"tools.copilot_repair" = "tools/copilot_repair"
"tools.pr_action_bridge" = "tools/pr_action_bridge"
"tools.pr_steward" = "tools/pr_steward"

[tool.setuptools.package-data]
"dopemux.templates" = [
    "init/.claude/PRIMER.md",
    "init/.claude/PROJECT_INSTRUCTIONS.MD",
    "init/.claude/README.md",
    "init/.claude/claude.md",
    "init/.github/workflows/embedded-audit.yml",
    "init/.github/workflows/pr-steward.yml",
    "init/config/pr_merge_specialist/policy.yaml",
    "init/config/pr_steward/policy.json",
    "init/docs/90-adr/TEMPLATE_ADR.md",
    "init/docs/90-adr/TEMPLATE_ADR_LIGHT.md",
    "init/docs/90-adr/TEMPLATE_ADR_RECORD.md",
    "init/docs/task-packets/CHECKLIST.md",
    "init/docs/task-packets/INDEX.md",
    "init/docs/task-packets/README.md",
    "init/docs/task-packets/STATUS.md",
    "init/docs/task-packets/TEMPLATE_TASK_PACKET.md",
    "init/task-packets/CHECKLIST.md",
    "init/task-packets/INDEX.md",
    "init/task-packets/README.md",
    "init/task-packets/STATUS.md",
    "init/task-packets/TEMPLATE_TASK_PACKET.md",
]
"dopemux_pr_steward" = ["config.schema.json"]
"tools.pr_steward" = ["known_reviewers.json"]

[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache

## src/dopemux/cli.py
#!/usr/bin/env python3
"""
Dopemux CLI - ADHD-optimized development platform CLI.

Main entry point for all dopemux commands providing context preservation,
attention monitoring, and task decomposition for neurodivergent developers.
"""

import logging
import os

logger = logging.getLogger(__name__)

import shlex
import shutil
import signal
import socket
import sys
import tempfile
import time
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence
from contextlib import contextmanager

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
from .ux.confidence_band import ConfidenceBandState, render_confidence_band

# Load environment variables from .env file
load_dotenv()
check_dotenv_support()
import subprocess
from subprocess import CalledProcessError
from urllib.parse import urlparse

import yaml


class LegacyReplacementCommand(click.Command):
    """Click command that reports a canonical replacement surface."""

    def __init__(
        self,
        *args: Any,
        replacement_command: str,
        replacement_by_arg: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> None:
        self.replacement_command = replacement_command
        self.replacement_by_arg = replacement_by_arg or {}
        super().__init__(*args, **kwargs)

    def format_help(self, ctx: click.Context, formatter: click.HelpFormatter) -> None:
        formatter.write_text(
            f"Legacy command disabled. Use `{self.replacement_command}` instead."
        )

    def parse_args(self, ctx: click.Context, args: List[str]) -> List[str]:
        if any(arg in ("--help", "-h") for arg in args):
            click.echo(ctx.get_help(), color=ctx.color)
            ctx.exit()
        if args and args[0] in self.replacement_by_arg:
            ctx.meta["legacy_replacement_command"] = self.replacement_by_arg[args[0]]
        ctx.args = []
        return []

    def invoke(self, ctx: click.Context) -> Any:
        replacement = ctx.meta.get("legacy_replacement_command", self.replacement_command)
        raise click.ClickException(
            f"Legacy command disabled. Use `{replacement}` instead."
        )


def _unavailable_group(message: str) -> click.Group:
    @click.group()
    def _group() -> None:
        raise click.ClickException(message)

    return _group


_LITELLM_IMPORT_ERROR: Optional[BaseException] = None

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
try:
    from .health import HealthChecker
except ModuleNotFoundError as exc:
    if exc.name != "psutil":
        raise

    class HealthChecker:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            raise click.ClickException(
                "Health checks are unavailable because the psutil package is "
                "not importable. Install project dependencies before invoking "
                "health commands."
            )
from .instance_manager import (
    InstanceManager,
    detect_instances_sync,
    detect_orphaned_instances_sync,
)
try:
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
except ModuleNotFoundError as exc:
    if exc.name != "litellm":
        raise
    _LITELLM_IMPORT_ERROR = exc

    class LiteLLMProxyError(RuntimeError):
        """Raised when LiteLLM proxy helpers are unavailable."""

    def _raise_litellm_unavailable(*args: Any, **kwargs: Any) -> Any:
        raise LiteLLMProxyError(
            "LiteLLM proxy support is unavailable because the litellm package "
            "is not importable. Install project dependencies before invoking "
            "LiteLLM-backed commands."
        ) from _LITELLM_IMPORT_ERROR

    ALTP_PROVIDER = {"required_keys": (), "targets": ()}
    CODEX_PROVIDER = {}
    DEFAULT_LITELLM_CONFIG = ""
    GROK_PROVIDER = {}
    LiteLLMProxyManager = _raise_litellm_unavailable
    ensure_master_key = _raise_litellm_unavailable
    generate_multi_target_config = _raise_litellm_unavailable
    generate_single_target_config = _raise_litellm_unavailable
    start_simple_proxy = _raise_litellm_unavailable
    sync_litellm_database = _raise_litellm_unavailable
try:
    from .mobile import mobile as mobile_commands
    from .mobile.hooks import mobile_task_notification
    from .mobile.main import main as mobile_env_commands
    from .mobile.runtime import update_tmux_mobile_indicator
except ModuleNotFoundError as exc:
    if exc.name != "litellm":
        raise
    _mobile_unavailable_message = (
        "Mobile commands are unavailable because the LiteLLM-backed tmux "
        "command stack is not importable in this environment."
    )
    mobile_commands = _unavailable_group(_mobile_unavailable_message)
    mobile_env_commands = _unavailable_group(_mobile_unavailable_message)

    @contextmanager
    def mobile_task_notification(*args: Any, **kwargs: Any) -> Any:
        yield

    def update_tmux_mobile_indicator(*args: Any, **kwargs: Any) -> None:
        return None
from .profile_manager import ProfileManager
from .profile_models import ProfileValidationError
from .profile_parser import ProfileParser
from .project_init import init_project
from .protection_interceptor import (
    check_and_protect_main,
    consume_last_created_worktree,
)
try:
    from .tmux import tmux as tmux_commands
except ModuleNotFoundError as exc:
    if exc.name != "litellm":
        raise
    tmux_commands = _unavailable_group(
        "Tmux commands are unavailable because the litellm package is not importable."
    )

from .memory.capture_client import CaptureError, emit_capture_event
from .roles.catalog import (
    RoleNotFoundError,
    activate_role,
    available_roles,
    resolve_role,
)

if "-litellm" in sys.argv:
    sys.argv = ["--litellm" if arg == "-litellm" else arg for arg in sys.argv]


ROLE_SERVER_SERVICE_MAP = {
    "dopemux-conport": "dopemux-conport",
    "dopemux-serena": "dopemux-serena",
    "dopemux-zen": "dopemux-zen",
    "dopemux-pal": "dopemux-pal",
    "dopemux-gpt-researcher": "dopemux-gpt-researcher",
    "dopemux-desktop-commander": "dopemux-desktop-commander",
    "dopemux-leantime-bridge": "dopemux-leantime-bridge",
    "dopemux-claude-context": "dopemux-claude-context",
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

## src/dopemux/commands/kernel_commands.py
"""
TaskX Kernel Lifecycle Commands

Delegates kernel lifecycle commands to the scripts/taskx wrapper.
"""

import sys
import subprocess
from pathlib import Path
from typing import Sequence

import click

from ..console import console


def _run_taskx_kernel(base_args: Sequence[str], taskx_args: Sequence[str]) -> None:
    """Delegate kernel lifecycle commands to scripts/taskx."""
    repo_root = Path(__file__).resolve().parents[3]
    wrapper = repo_root / "scripts" / "taskx"
    if not wrapper.exists():
        console.logger.error(f"[error]TaskX wrapper missing: {wrapper}[/error]")
        sys.exit(1)

    cmd = [str(wrapper), *base_args, *taskx_args]
    result = subprocess.run(cmd, cwd=repo_root, check=False)
    if result.returncode != 0:
        sys.exit(result.returncode)


@click.group("kernel")
def kernel() -> None:
    """
    🔬 TaskX Kernel Lifecycle: Orchestrate Ritual Steps

    Manages the primary execution kernel of the TaskX subsystem. These commands
    delegate to the TaskX ritual wrapper (scripts/taskx), synchronizing the
    core state and lifecycle of the active daemon.

    Capabilities:
    - Diagnostic Scans: Run the doctor ritual to verify kernel health.
    - Lifecycle Stages: Compile, Run, Collect, Gate, Promote, Feedback, and Loop.
    """


@kernel.command("doctor", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_doctor(taskx_args: Sequence[str]) -> None:
    """
    🔬 Run diagnostic scan on the active kernel (TaskX doctor).

    Verifies the integrity of the ritual chamber and daemon synchronization.
    """
    _run_taskx_kernel(["doctor"], taskx_args)


@kernel.command("compile", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_compile(taskx_args: Sequence[str]) -> None:
    """
    🧪 Synchronize and compile the TaskX ritual logic.

    Transforms raw intent into executable kernel patterns.
    """
    _run_taskx_kernel(["dopemux", "compile"], taskx_args)


@kernel.command("run", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_run(taskx_args: Sequence[str]) -> None:
    """
    ⚡ Execute the current TaskX ritual cycle.

    Launches the active kernel within the provisioned cockpit.
    """
    _run_taskx_kernel(["dopemux", "run"], taskx_args)


@kernel.command("collect", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_collect(taskx_args: Sequence[str]) -> None:
    """
    📊 Harvest ritual artifacts and state updates from the active kernel.

    Consolidates mission telemetry and stores it in the central archive.
    """
    _run_taskx_kernel(["dopemux", "collect"], taskx_args)


@kernel.command("gate", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_gate(taskx_args: Sequence[str]) -> None:
    """
    💧 Verify ritual exit conditions and quality gates.

    Ensures mission success criteria are satisfied before promotion.
    """
    _run_taskx_kernel(["dopemux", "gate"], taskx_args)


@kernel.command("promote", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_promote(taskx_args: Sequence[str]) -> None:
    """
    ⚡ Advance the ritual state to the next temporal coordinate.

    Commits verified artifacts to the shared repository.
    """
    _run_taskx_kernel(["dopemux", "promote"], taskx_args)


@kernel.command("feedback", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_feedback(taskx_args: Sequence[str]) -> None:
    """
    🧠 Process mission feedback and update ritual heuristics.

    Refines the daemon's cognitive patterns based on execution data.
    """
    _run_taskx_kernel(["dopemux", "feedback"], taskx_args)


@kernel.command("loop", context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("taskx_args", nargs=-1, type=click.UNPROCESSED)
def kernel_loop(taskx_args: Sequence[str]) -> None:
    """
    ⚡ Initiate a persistent ritual loop.

    Automates sequential execution of the TaskX kernel lifecycle.
    """
    _run_taskx_kernel(["dopemux", "loop"], taskx_args)

## scripts/taskx
#!/usr/bin/env bash
set -euo pipefail

# Compatibility shim during taskx -> dopetask transition.
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/dopetask" "$@"

## scripts/dopetask
#!/usr/bin/env bash
set -euo pipefail

# --- Configuration ---
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EXPECTED_PROJECT_ID="dopemux-mvp"
VENV="$REPO_ROOT/.dopetask_venv"
VERSION_MARKER="$VENV/.dopetask_version"
PIN_FILE="$REPO_ROOT/.dopetask-pin"

# --- Authority Rails ---
if [[ ! -f "$REPO_ROOT/.dopetaskroot" ]]; then
  echo "ERROR: .dopetaskroot missing in repo root: $REPO_ROOT" >&2
  exit 2
fi

if [[ ! -f "$PIN_FILE" ]]; then
  echo "ERROR: .dopetask-pin missing in repo root" >&2
  exit 2
fi

# Parse pin
INSTALL_METHOD=""
DEP_NAME=""
TARGET_VERSION=""
while IFS='=' read -r key value; do
  case "$key" in
    install) INSTALL_METHOD="$value" ;;
    dep) DEP_NAME="$value" ;;
    version) TARGET_VERSION="$value" ;;
  esac
done < "$PIN_FILE"

if [[ "$INSTALL_METHOD" != "pip" && "$INSTALL_METHOD" != "uv" ]]; then
  echo "ERROR: Invalid install method in .dopetask-pin: $INSTALL_METHOD" >&2
  exit 2
fi

if [[ -z "$DEP_NAME" || -z "$TARGET_VERSION" ]]; then
  echo "ERROR: Malformed .dopetask-pin (missing dep or version)" >&2
  exit 2
fi

# --- Venv & Install Management ---
mkdir -p "$VENV"
if [[ ! -d "$VENV/bin" ]]; then
  python3 -m venv "$VENV"
fi

CURRENT_INSTALLED=""
if [[ -f "$VERSION_MARKER" ]]; then
  CURRENT_INSTALLED="$(cat "$VERSION_MARKER" | tr -d '[:space:]')"
fi

install_dopetask() {
  echo "INFO: Installing $DEP_NAME==$TARGET_VERSION via $INSTALL_METHOD..."
  source "$VENV/bin/activate"

  if [[ "$INSTALL_METHOD" == "uv" ]] && command -v uv &> /dev/null; then
    uv pip install "$DEP_NAME==$TARGET_VERSION"
  else
    if [[ "$INSTALL_METHOD" == "uv" ]]; then
      echo "WARN: uv requested but not found, falling back to pip" >&2
    fi
    pip install --quiet --upgrade pip
    pip install --quiet "$DEP_NAME==$TARGET_VERSION"
  fi

  echo "$TARGET_VERSION" > "$VERSION_MARKER"
}

# Re-install on drift
if [[ "$CURRENT_INSTALLED" != "$TARGET_VERSION" ]]; then
  install_dopetask
fi

# Ensure executable exists
if [[ ! -x "$VENV/bin/dopetask" ]]; then
  install_dopetask
fi

# --- Execution ---
source "$VENV/bin/activate"

# Special handling for 'doctor' (known branch enforcement in 0.5.x)
if [[ "${1:-}" == "doctor" ]]; then
  set +e
  "$VENV/bin/dopetask" "$@"
  EXIT_CODE=$?
  set -e
  if [[ $EXIT_CODE -ne 0 ]]; then
    echo "HINT: dopetask doctor may fail on non-main branches in 0.5.x." >&2
  fi
  exit $EXIT_CODE
fi

exec "$VENV/bin/dopetask" "$@"

## services/task-orchestrator/app/main.py
"""
Coordination API Service - REST API for Two-Plane Coordination

Provides RESTful endpoints for cross-plane operations and event handling.
"""

import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager

# Add repo root to path before importing shared dopemux modules.
repo_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
src_path = os.path.join(repo_root, "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from dopemux.workspace_detection import get_workspace_root

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Response
from fastapi.middleware.cors import CORSMiddleware
import json
try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover - optional MCP transport in slim test envs
    class FastMCP:  # type: ignore[override]
        """Minimal fallback used when the MCP server package is unavailable."""

        def __init__(self, name: str):
            self.name = name
            self.tools: Dict[str, Dict[str, Any]] = {}

        def tool(self, *, name: str, description: str):
            def decorator(func):
                self.tools[name] = {"description": description, "handler": func}
                return func

            return decorator

try:
    from dopemux.logging import configure_logging, RequestIDMiddleware
except Exception:
    RequestIDMiddleware = None
    def configure_logging(service_name, *, level=None, **_):
        resolved_level = getattr(logging, str(level or "INFO").upper(), logging.INFO)
        logging.basicConfig(
            level=resolved_level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        return logging.getLogger(service_name)
coordinator_import_error = None
try:
    from .core.coordinator import create_plane_coordinator
except Exception as relative_import_error:  # pragma: no cover - direct module loading in tests
    coordinator_import_error = relative_import_error
    try:
        from app.core.coordinator import create_plane_coordinator
    except Exception as absolute_import_error:  # pragma: no cover - slim test env fallback
        coordinator_import_error = absolute_import_error
        async def create_plane_coordinator(*_args, **_kwargs):
            raise RuntimeError(
                "task-orchestrator coordinator is unavailable in this environment: "
                f"{coordinator_import_error}"
            )

# Configure structured logging
configure_logging("task-orchestrator")
logger = logging.getLogger(__name__)
SERVICE_NAME = os.getenv("SERVICE_NAME", "task-orchestrator")
HEALTH_CHECK_PATH = os.getenv("HEALTH_CHECK_PATH", "/health")
DEFAULT_PORT = 8000

# Initialize MCP server
mcp = FastMCP("Task-Orchestrator")

# Register MCP tools
try:
    from task_orchestrator.mcp import MCP_TOOLS, handle_tool_call
    for tool_def in MCP_TOOLS:
        @mcp.tool(name=tool_def["name"], description=tool_def["description"])
        async def mcp_tool_wrapper(tool_name=tool_def["name"], **kwargs):
            return await handle_tool_call(tool_name, kwargs)
except ImportError:
    # Fallback for direct module loading in tests or different structure
    try:
        from .mcp import MCP_TOOLS, handle_tool_call
        for tool_def in MCP_TOOLS:
            @mcp.tool(name=tool_def["name"], description=tool_def["description"])
            async def mcp_tool_wrapper(tool_name=tool_def["name"], **kwargs):
                return await handle_tool_call(tool_name, kwargs)
    except ImportError:
        logger = logging.getLogger(__name__)
        logger.warning("MCP tools could not be loaded - server will be empty")

# Import shared models from local models
try:
    from .models.coordination import (
        PlaneType,
        CoordinationEventType,
        ConflictResolutionStrategy,
        CoordinationOperationRequest,
        CoordinationOperationResponse,
        PlaneHealthResponse,
        CoordinationMetricsResponse,
        EmitEventRequest,
        ConflictResolutionRequest,
        HealthResponse
    )
except ImportError:  # pragma: no cover - direct module loading in tests
    from app.models.coordination import (
        PlaneType,
        CoordinationEventType,
        ConflictResolutionStrategy,
        CoordinationOperationRequest,
        CoordinationOperationResponse,
        PlaneHealthResponse,
        CoordinationMetricsResponse,
        EmitEventRequest,
        ConflictResolutionRequest,
        HealthResponse
    )

try:
    from .models.workflow import (
        CreateIdeaRequest,
        UpdateIdeaRequest,
        PromoteIdeaRequest,
        CreateEpicRequest,
        UpdateEpicRequest,
    )
    from .services.workflow_service import (
        WorkflowConflictError,
        WorkflowNotFoundError,
        WorkflowUnavailableError,
    )
    from .api.project_workflow import router as project_workflow_router
except ImportError:  # pragma: no cover - direct module loading in tests
    from app.models.workflow import (
        CreateIdeaRequest,
        UpdateIdeaRequest,
        PromoteIdeaRequest,
        CreateEpicRequest,
        UpdateEpicRequest,
    )
    from app.services.workflow_service import (
        WorkflowConflictError,
        WorkflowNotFoundError,
        WorkflowUnavailableError,
    )
    from app.api.project_workflow import router as project_workflow_router

try:
    from .api.project_workflow import router as project_workflow_router
except ImportError:  # pragma: no cover - direct module loading in tests
    from app.api.project_workflow import router as project_workflow_router

logger = logging.getLogger(__name__)

# ============================================================================
# FastAPI Application
# ============================================================================

async def init_coordinator():
    """Initialize plane coordinator"""
    logger.info("Initializing plane coordinator...")
    coordinator = await create_plane_coordinator(get_workspace_root())
    logger.info("Plane coordinator initialized")
    return {"coordinator": coordinator}


async def shutdown_coordinator():
    """Shutdown plane coordinator"""
    # Coordinator shutdown handled by lifespan_context
    pass


@asynccontextmanager
async def lifespan_context(name: str, startup_func, shutdown_func):
    """Helper to manage service lifespan with startup and shutdown hooks"""
    logger.info(f"Starting {name} lifespan context...")
    state = await startup_func()
    try:
        yield state
    finally:
        logger.info(f"Shutting down {name} lifespan context...")
        await shutdown_func()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    async with lifespan_context("task-orchestrator", init_coordinator, shutdown_coordinator) as state:
        app.state.coordinator = state.get("coordinator")
        yield


app = FastAPI(
    title="Dopemux Plane Coordination API",
    description="REST API for two-plane architecture coordination",
    version="1.0.0",
    lifespan=lifespan
)
app.include_router(project_workflow_router)

# CORS middleware for web integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8097"],  # ADHD Dashboard, etc.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request ID middleware
if RequestIDMiddleware is not None:
    app.add_middleware(RequestIDMiddleware)

# ============================================================================
# WebSocket Connection Manager
# ============================================================================


class ConnectionManager:
    """WebSocket connection manager for real-time coordination events."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, client_info: Dict[str, Any] = None):
        """Connect a new WebSocket client."""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_metadata[websocket] = client_info or {}
        logger.info(f"🔗 WebSocket client connected: {len(self.active_connections)} total")

    def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            del self.connection_metadata[websocket]
            logger.info(f"🔌 WebSocket client disconnected: {len(self.active_connections)} remaining")

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to client: {e}")
                disconnected.append(connection)

        # Clean up disconnected clients
        for connection in disconnected:

## services/task-orchestrator/mcp_stdio.py
from app.main import mcp

if __name__ == "__main__":
    mcp.run(transport="stdio")

## services/dope-context/src/mcp/server.py
"""
FastMCP Server - Task 8
Exposes code index as MCP tools for Claude Code integration.

MCP Tools:
1. index_workspace - Index code files
2. search_code - Hybrid search (dense + sparse + rerank)
3. get_index_status - Collection info
4. clear_index - Delete collection
"""

import ast
import asyncio
import json
import logging
import os
import pickle
import subprocess
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, List, Optional, Set, Tuple

import aiohttp

FASTMCP_AVAILABLE = True
try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover - exercised in constrained envs
    from .fastmcp_stub import FastMCP

    FASTMCP_AVAILABLE = False
try:
    from starlette.requests import Request
    from starlette.responses import JSONResponse
except ImportError:  # pragma: no cover - for constrained test envs

    class Request:  # type: ignore
        """Fallback request stub."""

        def __init__(self, *args, **kwargs):
            self._starlette_unavailable = True

    class JSONResponse(dict):  # type: ignore
        """Fallback JSON response stub."""

        def __init__(self, content=None, **kwargs):
            super().__init__(content or {})


from ..autonomous.autonomous_controller import AutonomousConfig, AutonomousController
from ..context.openai_generator import OpenAIContextGenerator
from ..embeddings.contextualized_embedder import ContextualizedEmbedder
from ..embeddings.voyage_embedder import VoyageEmbedder
from ..pipeline.docs_pipeline import DocIndexingPipeline
from ..pipeline.indexing_pipeline import (
    IndexingConfig,
    IndexingPipeline,
    IndexingProgress,
)
from ..preprocessing.code_chunker import ChunkingConfig, CodeChunker
from ..rerank.voyage_reranker import VoyageReranker
from ..search.dense_search import MultiVectorSearch, SearchProfile
from ..search.docs_search import DocumentSearch
from ..search.hybrid_search import BM25Index, HybridSearch
from ..sync.file_synchronizer import ChangeSet, FileSynchronizer
from ..utils.metrics_tracker import get_tracker
from ..utils.token_budget import truncate_code_results, truncate_docs_results
from ..utils.workspace import (
    get_collection_names,
    get_snapshot_dir,
    get_workspace_root,
    workspace_to_hash,
)

# ConPort-KG Integration (optional)
try:
    from dopecon_bridge_connector import emit_search_completed

    CONPORT_INTEGRATION_AVAILABLE = True
except ImportError:
    CONPORT_INTEGRATION_AVAILABLE = False


logger = logging.getLogger(__name__)

if not FASTMCP_AVAILABLE:
    logger.warning(
        "fastmcp package not installed; falling back to stub FastMCP. "
        "MCP tools remain importable but server.run() is a no-op."
    )

TRINITY_DECISION_DEFAULT_LIMIT = 3
TRINITY_DECISION_MAX_LIMIT = 10
TRINITY_BOUNDARY_MARKER = "search-memory-authority-boundary-v1"


# Initialize FastMCP server
mcp = FastMCP("dope-context")


def _resolve_transport_runtime() -> Tuple[str, str, int]:
    """Resolve active MCP transport/host/port deterministically."""
    transport_env = os.getenv("MCP_TRANSPORT") or os.getenv("FASTMCP_TRANSPORT")
    if transport_env:
        transport = transport_env.strip().lower()
    elif os.getenv("MCP_SERVER_PORT"):
        transport = "http"
    else:
        transport = "stdio"

    valid_transports = {"stdio", "http", "sse", "streamable-http"}
    if transport not in valid_transports:
        logger.warning("Unknown MCP transport '%s'; defaulting to 'stdio'", transport)
        transport = "stdio"

    host = os.getenv("MCP_SERVER_HOST") or os.getenv("FASTMCP_HOST") or "127.0.0.1"
    port_str = (
        os.getenv("MCP_SERVER_PORT") or os.getenv("FASTMCP_PORT") or os.getenv("PORT")
    )
    try:
        port = int(port_str) if port_str else 3010
    except (TypeError, ValueError):
        logger.warning("Invalid MCP_SERVER_PORT '%s'; defaulting to 3010", port_str)
        port = 3010

    if transport == "stdio":
        return transport, "stdio", 0
    return transport, host, port


def _transport_connection_url(transport: str, host: str, port: int) -> str:
    """Build user-facing MCP connection URL from runtime transport."""
    if transport == "stdio":
        return "stdio://mcp"
    return f"http://localhost:{port}/mcp"


def _normalize_decision_limit(limit_value: Any) -> int:
    """Clamp cross-plane decision retrieval limits to Trinity boundary rails."""
    try:
        parsed = int(limit_value)
    except (TypeError, ValueError):
        parsed = TRINITY_DECISION_DEFAULT_LIMIT
    return max(1, min(parsed, TRINITY_DECISION_MAX_LIMIT))


# # @mcp.custom_route("/health", methods=["GET"])
async def health_check(_: Request) -> JSONResponse:
    """Basic health endpoint for container probes."""
    return JSONResponse({"status": "ok"})


# # @mcp.custom_route("/info", methods=["GET"])
async def service_info(_: Request) -> JSONResponse:
    """Service discovery endpoint - auto-config support (ADR-208)"""
    transport, host, port = _resolve_transport_runtime()
    connection_url = _transport_connection_url(transport, host, port)
    warning = (
        "fastmcp package not installed; stub server active and MCP run loop is a no-op."
        if not FASTMCP_AVAILABLE
        else None
    )
    return JSONResponse(
        {
            "name": "dope-context",
            "version": "1.0.0",
            "fastmcp_available": FASTMCP_AVAILABLE,
            "canonical_entrypoint": "python -m src.mcp.server",
            "mcp": {
                "protocol": "stdio" if transport == "stdio" else "sse",
                "connection": {
                    "type": "stdio" if transport == "stdio" else "sse",
                    "url": connection_url,
                },
                "env": {
                    "VOYAGE_API_KEY": "${VOYAGEAI_API_KEY:-}",
                    "OPENAI_API_KEY": "${OPENAI_API_KEY:-}",
                    "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY:-}",
                },
            },
            "runtime": {
                "transport": transport,
                "host": host,
                "port": port,
                "fastmcp_available": FASTMCP_AVAILABLE,
                "canonical_entrypoint": "python -m src.mcp.server",
            },
            "health": "/health",
            "description": "Semantic code search and autonomous indexing",
            "metadata": {
                "role": "workflow",
                "priority": "high",
                "adhd_integration": True,
                "autonomous_indexing": True,
                "conport_integration": CONPORT_INTEGRATION_AVAILABLE,
                "warning": warning,
            },
        }
    )


# # @mcp.custom_route("/autoindex/bootstrap", methods=["POST"])
async def autoindex_bootstrap(request: Request) -> JSONResponse:
    """Trigger startup bootstrap indexing then autonomous watchers."""
    payload: Dict[str, Any] = {}
    try:
        if hasattr(request, "json"):
            maybe_payload = await request.json()
            if isinstance(maybe_payload, dict):
                payload = maybe_payload
    except Exception:
        payload = {}

    workspace_path = payload.get("workspace_path")
    force = bool(payload.get("force", False))
    wait_for_completion = bool(payload.get("wait_for_completion", False))
    debounce_seconds = float(payload.get("debounce_seconds", 5.0))
    periodic_interval = int(payload.get("periodic_interval", 600))

    workspace = (
        Path(workspace_path).resolve() if workspace_path else get_workspace_root()
    )
    key = str(workspace)
    running_task = _autoindex_bootstrap_tasks.get(key)

    if running_task and not running_task.done():
        return JSONResponse(
            {
                "status": "already_running",
                "workspace": key,
                "details": _autoindex_bootstrap_status.get(key, {}),
            }
        )

    task = asyncio.create_task(
        _run_workspace_autoindex_bootstrap(
            workspace,
            force=force,
            debounce_seconds=debounce_seconds,
            periodic_interval=periodic_interval,
        )
    )
    _autoindex_bootstrap_tasks[key] = task

    if wait_for_completion:
        result = await task
        return JSONResponse(result)

    return JSONResponse(
        {
            "status": "started",
            "workspace": key,
            "wait_for_completion": False,
            "message": "Bootstrap started in background; use /autoindex/status for progress.",
        }
    )



## services/working-memory-assistant/dope_memory_main.py
#!/usr/bin/env python3
"""
Dope-Memory HTTP Server - FastAPI wrapper for MCP tools.

Exposes Dope-Memory MCP tools over HTTP on port 3020.
This is the canonical entry point for the Dope-Memory service.

Per registry.yaml:
- Port: 3020
- Health: /health
- Category: mcp
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import sys
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

# Add parent dir to path for package imports when run directly
_THIS_DIR = Path(__file__).parent.resolve()
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Use absolute imports now that we've fixed the path
from canonical_ledger import CanonicalLedgerError, resolve_canonical_ledger
from chronicle.store import ChronicleStore
from promotion.redactor import Redactor
from promotion.promotion import PromotionEngine
from reflection.reflection import ReflectionGenerator
from trajectory.manager import TrajectoryManager

# Logging setup
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Configuration
PORT = int(os.getenv("PORT", os.getenv("DOPE_MEMORY_PORT", "3020")))
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", str(PORT)))
SERVICE_NAME = os.getenv("SERVICE_NAME", "dope-memory")
HEALTH_CHECK_PATH = os.getenv("HEALTH_CHECK_PATH", "/health")
DATA_DIR = Path(os.getenv("DOPE_MEMORY_DATA_DIR", str(Path.home() / ".dope-memory")))
DEFAULT_WORKSPACE_ID = os.getenv("DOPE_MEMORY_WORKSPACE_ID", "default")
DEFAULT_INSTANCE_ID = os.getenv("DOPE_MEMORY_INSTANCE_ID", "A")

# CORS configuration
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8097,http://adhd-dashboard:8097"
    ).split(",") if o.strip()
]


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Server (Inline to avoid import issues)
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class ToolResponse:
    """Standard tool response wrapper."""

    success: bool
    data: dict[str, Any]
    error: Optional[str] = None


class DopeMemoryMCPServer:
    """MCP server for Dope-Memory tools.

    All tools enforce ADHD Top-3 boundary with pagination support.
    """

    def __init__(
        self,
        workspace_id: str,
        instance_id: str = "A",
    ):
        self.default_workspace_id = workspace_id
        self.default_instance_id = instance_id
        self.redactor = Redactor()
        self.promotion_engine = PromotionEngine()
        # Keyed by resolved canonical ledger path
        self._stores: dict[str, ChronicleStore] = {}

    def _get_store(self, workspace_id: str) -> ChronicleStore:
        """Get or create a ChronicleStore for the canonical ledger.

        Resolves workspace_id to the single canonical ledger per ADR-213.
        """
        db_path = resolve_canonical_ledger(workspace_id)
        path_key = str(db_path)
        if path_key not in self._stores:
            store = ChronicleStore(db_path)
            store.initialize_schema()
            self._stores[path_key] = store
        return self._stores[path_key]

    def _encode_cursor(
        self, importance_score: int, ts_utc: str, entry_id: str, scope_hash: str
    ) -> str:
        """Encode a pagination cursor."""
        data = {"i": importance_score, "t": ts_utc, "id": entry_id, "h": scope_hash}
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()

    def _decode_cursor(
        self, cursor: str, expected_scope_hash: str
    ) -> Optional[tuple[int, str, str]]:
        """Decode and validate a pagination cursor."""
        try:
            data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
            if data.get("h") != expected_scope_hash:
                return None
            return (data["i"], data["t"], data["id"])
        except Exception:
            return None

    def _compute_scope_hash(self, **filters: Any) -> str:
        """Compute hash of search scope for cursor validation."""
        normalized = json.dumps(filters, sort_keys=True)
        return hashlib.sha256(normalized.encode()).hexdigest()[:8]

    def memory_search(
        self,
        query: str,
        workspace_id: str,
        instance_id: str,
        session_id: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
        top_k: int = 3,
        cursor: Optional[str] = None,
        include_superseded: bool = False,
    ) -> ToolResponse:
        """Search work log entries with trajectory boost applied to ranking."""
        try:
            top_k = min(max(1, top_k), 10)
            store = self._get_store(workspace_id)

            f = filters or {}
            search_filters = {
                "query": query.strip().lower(),
                "session_id": session_id,
                "category": f.get("category"),
                "entry_type": f.get("entry_type"),
                "workflow_phase": f.get("workflow_phase"),
                "tags_any": f.get("tags_any"),
                "time_range": f.get("time_range", "all"),
            }

            scope_hash = self._compute_scope_hash(
                workspace_id=workspace_id, instance_id=instance_id, **search_filters
            )
            decoded_cursor = None
            if cursor:
                decoded_cursor = self._decode_cursor(cursor, scope_hash)

            # Fetch extra rows to account for boost re-ranking
            # Fetch 2x top_k to have candidates for boost re-ranking
            fetch_limit = min(top_k * 2, 20)

            rows = store.search_work_log(
                workspace_id=workspace_id,
                instance_id=instance_id,
                query=query.strip().lower() if query.strip() else None,
                session_id=session_id,
                category=f.get("category"),
                entry_type=f.get("entry_type"),
                workflow_phase=f.get("workflow_phase"),
                tags_any=f.get("tags_any"),
                time_range=f.get("time_range"),
                limit=fetch_limit + 1,
                cursor=decoded_cursor,
                include_superseded=include_superseded,
            )

            # Apply trajectory boost to ranking
            trajectory_mgr = TrajectoryManager(store)
            trajectory = trajectory_mgr.get_trajectory(workspace_id, instance_id)

            # Calculate boosted scores
            boosted_rows = []
            for row in rows:
                base_score = row["importance_score"]
                boost = trajectory_mgr.get_boost_factor(row, trajectory)
                boosted_score = base_score + boost

                boosted_rows.append({
                    **row,
                    "_boosted_score": boosted_score,
                    "_boost_applied": boost,
                })

            # Re-sort by boosted score (desc), then ts_utc (desc), then id (asc)
            boosted_rows.sort(
                key=lambda r: (-r["_boosted_score"], -datetime.fromisoformat(r["ts_utc"]).timestamp(), r["id"])
            )

            # Apply Top-K after boost
            has_more = len(boosted_rows) > top_k
            items = boosted_rows[:top_k]

            next_token = None
            if has_more and items:
                last = items[-1]
                next_token = self._encode_cursor(
                    last["importance_score"], last["ts_utc"], last["id"], scope_hash
                )

            response_items = []
            for row in items:
                item = {
                    "id": row["id"],
                    "ts_utc": row["ts_utc"],
                    "summary": row["summary"],
                    "category": row["category"],
                    "entry_type": row["entry_type"],
                    "workflow_phase": row.get("workflow_phase"),
                    "outcome": row["outcome"],
                    "importance_score": row["importance_score"],
                    "tags": json.loads(row.get("tags_json", "[]")),
                    # Include boost metadata for debugging (optional)
                    "_boost_applied": row.get("_boost_applied", 0.0),
                }
                # Include chain annotations when superseded entries are shown (Packet F §5.2)
                if include_superseded:
                    item["is_head"] = row.get("is_head", True)
                    item["superseded_by"] = row.get("superseded_by")
                    item["supersedes"] = row.get("supersedes")
                    item["chain_position"] = row.get("chain_position")
                response_items.append(item)

            return ToolResponse(
                success=True,
                data={
                    "items": response_items,
                    "more_count": max(0, len(boosted_rows) - top_k - 1) if has_more else 0,
                    "next_token": next_token,
                },
            )
        except Exception as e:
            logger.error(f"memory_search error: {e}")
            return ToolResponse(success=False, data={}, error=str(e))

    def memory_store(
        self,
        workspace_id: str,

## services/dopecon-bridge/dopecon_bridge/routes.py
"""
DopeconBridge API routes for the active runtime.

The active bridge is an adapter and proxy layer only. It must not act as
canonical task, workflow, decision, or progress authority.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from .auth import authenticate_user, create_access_token, get_current_user, security
from .clients import conport_client, mcp_client, update_context_delta
from .config import settings
from .core import cache_manager
from .leantime_contract import (
    build_leantime_tool_request,
    normalize_leantime_route_response,
)


logger = logging.getLogger(__name__)


WORKFLOW_SIGNIFICANT_OPERATIONS = {
    "update_task_status",
    "leantime.update_task_status",
    "update_sprint",
    "leantime.update_sprint",
    "transition_work_item",
    "pm_transition_work_item",
    "next_action",
    "get_next_action",
}
SAFE_PM_ROUTE_OPERATIONS = {
    "get_tasks",
    "list_tasks",
    "create_task",
    "update_task",
    "create_project",
    "get_project_status",
    "allocate_resource",
    "leantime.get_tasks",
    "leantime.list_tasks",
    "leantime.create_task",
    "leantime.update_task",
    "leantime.create_project",
    "leantime.get_project_status",
    "leantime.allocate_resource",
}


class PRDParseRequest(BaseModel):
    """Legacy task-creation request that now fails closed."""

    content: str = Field(..., description="PRD content to parse")
    project_id: str = Field(..., description="Project ID for task creation")


class PublishEventRequest(BaseModel):
    """Request to publish an event."""

    stream: str = Field(default="dopemux:events", description="Redis Stream name")
    event_type: str = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Event data payload")
    source: Optional[str] = Field(None, description="Event source identifier")


class TaskUpdateRequest(BaseModel):
    """Legacy task update request that now fails closed."""

    status: str = Field(..., description="New task status")
    assigned_to: Optional[str] = Field(None, description="User assignment")


class PMRouteRequest(BaseModel):
    """Normalized PM-plane request body."""

    source: str = Field(default="cognitive", description="Source plane label")
    operation: str = Field(..., description="Normalized PM operation")
    data: Dict[str, Any] = Field(default_factory=dict, description="Operation payload")
    requester: str = Field(..., description="Calling client or service")


class CustomDataRequest(BaseModel):
    workspace_id: Optional[str] = None
    category: str
    key: str
    value: Dict[str, Any]


class DecisionRequest(BaseModel):
    workspace_id: Optional[str] = None
    summary: Optional[str] = None
    rationale: str
    implementation_details: Optional[str] = None
    alternatives: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    confidence_level: str = "medium"
    decision_type: str = "implementation"


class ProgressRequest(BaseModel):
    workspace_id: Optional[str] = None
    description: str
    status: str = "IN_PROGRESS"
    percentage: int = 0
    priority: str = "medium"
    linked_decision_id: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


auth_router = APIRouter(prefix="/auth", tags=["Authentication"])
events_router = APIRouter(prefix="/events", tags=["EventBus"])
tasks_router = APIRouter(prefix="/tasks", tags=["Tasks"])
ddg_router = APIRouter(prefix="/ddg", tags=["Decision Graph"])
pm_router = APIRouter(prefix="/route", tags=["PM Routing"])
kg_router = APIRouter(prefix="/kg", tags=["ConPort Proxy"])
health_router = APIRouter(tags=["Health"])


def _default_workspace_id(workspace_id: Optional[str]) -> str:
    return workspace_id or settings.default_workspace_id


def _correlation_id(request: Request) -> str:
    return request.headers.get("X-Request-ID") or str(uuid4())


def _reject_policy_blocked(detail: str) -> None:
    raise HTTPException(status_code=409, detail=detail)


def _is_workflow_significant_pm_mutation(operation: str, payload: Dict[str, Any]) -> bool:
    normalized = (operation or "").strip().lower()
    if normalized in WORKFLOW_SIGNIFICANT_OPERATIONS:
        return True
    return "status" in payload or "transition" in normalized or "workflow" in normalized


def _normalize_decision_list(payload: Dict[str, Any], query: Optional[str] = None) -> Dict[str, Any]:
    items = list(payload.get("decisions", []))
    return {
        "count": int(payload.get("count", len(items))),
        "items": items,
        "decisions": items,
        "query": query,
        "source": "conport",
    }


def _normalize_search_results(payload: Dict[str, Any], query: str) -> Dict[str, Any]:
    results = payload.get("results", {})
    items = list(results.get("decisions", []))
    return {
        "count": int(payload.get("total_count", len(items))),
        "items": items,
        "decisions": items,
        "query": query,
        "source": "conport",
    }


def _normalize_progress_list(payload: Dict[str, Any]) -> Dict[str, Any]:
    entries = list(payload.get("progress", []))
    return {
        "count": int(payload.get("count", len(entries))),
        "entries": entries,
        "progress": entries,
        "source": "conport",
    }


def _normalize_custom_data_read(payload: Dict[str, Any]) -> Dict[str, Any]:
    if "items" in payload and isinstance(payload["items"], list):
        items = list(payload["items"])
    elif "value" in payload:
        items = [payload]
    else:
        items = []
    return {
        "success": True,
        "count": int(payload.get("count", len(items))),
        "data": items,
        "source": "conport",
    }


async def _publish_event_internal(request: PublishEventRequest) -> Dict[str, Any]:
    from .event_bus import Event, EventBus

    event_bus = EventBus()
    await event_bus.initialize()
    try:
        event = Event(
            type=request.event_type,
            data=request.data,
            source=request.source or settings.service_name,
        )
        msg_id = await event_bus.publish(request.stream, event)
        return {
            "status": "published",
            "message_id": msg_id,
            "stream": request.stream,
            "event_type": request.event_type,
            "timestamp": datetime.utcnow().isoformat(),
        }
    finally:
        await event_bus.close()


@auth_router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate and return access token."""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/refresh")
async def refresh_token(current_token: str = Depends(security)):
    """Refresh access token."""
    access_token = create_access_token(
        data={"sub": "admin"},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@health_router.get("/health")
async def health_check():
    """Health check with service status."""
    try:
        services_health = await mcp_client.health_check_all()
        services_health["conport"] = await conport_client.health_check()
        return {
            "status": "healthy",
            "instance": settings.instance_name,
            "port": settings.port,
            "services": services_health,

## services/adhd_engine/main.py
"""
ADHD Accommodation Engine - FastAPI Application

Standalone microservice extracted from task-orchestrator (Decision #140).

Features:
- 6 API endpoints (/api/v1/*) + 2 utility endpoints for ADHD assessments
- 6 background async monitors (energy, attention, cognitive load, breaks, hyperfocus, context switching)
- Redis persistence for user profiles and state
- DopeconBridge connection for ConPort data (✅ COMPLETE as of 2025-10-16)
- API key authentication (X-API-Key header)
- Environment-based CORS configuration
"""

import os
import asyncio
import importlib.util
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
PROMETHEUS_AVAILABLE = importlib.util.find_spec("prometheus_client") is not None

try:
    from dopemux.logging import configure_logging, RequestIDMiddleware
except Exception:  # pragma: no cover - fallback path for isolated service images
    RequestIDMiddleware = None

    def configure_logging(service_name, *, level=None, **_):
        resolved_level = getattr(logging, str(level or "INFO").upper(), logging.INFO)
        logging.basicConfig(
            level=resolved_level,
            format="%(asctime)s %(levelname)s %(name)s %(message)s",
        )
        return logging.getLogger(service_name)

# Use relative imports for module execution (python -m services.adhd_engine.main)
from .core.engine import ADHDAccommodationEngine
from .api import routes
from .config import settings
from .operator_identity import resolve_operator_user_id
from .middleware.rate_limit import RateLimitMiddleware
from .core.error_handling import with_error_handling
try:
    from fastmcp import FastMCP
except ImportError:  # pragma: no cover - optional dependency for local test envs
    class FastMCP:  # type: ignore[override]
        """Minimal FastMCP fallback so API can boot without MCP extras."""

        def __init__(self, name: str):
            self.name = name
            self.http_app = FastAPI(title=f"{name} MCP Fallback")

        def tool(self):
            def decorator(func):
                return func

            return decorator

# Initialize FastMCP
mcp = FastMCP("ADHD-Engine")

@mcp.tool()
async def get_cognitive_state(user_id: str | None = None) -> dict:
    """Get current cognitive state (energy, attention, load)."""
    if not engine:
        return {"error": "Engine not initialized"}

    user_id = user_id or resolve_operator_user_id()

    # We call the engine directly for speed
    energy = await engine.get_energy_level(user_id)
    attention = await engine.get_attention_state(user_id)
    load = await engine.get_cognitive_load(user_id)

    return {
        "energy_level": energy.level,
        "energy_score": energy.score,
        "attention_state": attention.state,
        "cognitive_load": load
    }

@mcp.tool()
async def assess_task_complexity(title: str, description: str = "") -> dict:
    """Assess task complexity and ADHD impact."""
    if not engine:
        return {"error": "Engine not initialized"}

    assessment = await engine.assess_task(title, description)
    return assessment.dict()

# Import shared Redis pool and cache for performance optimization
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'docker', 'mcp-servers', 'shared'))
from redis_pool import get_redis_pool
from cache import get_cache

# Import shared monitoring (optional - from repo root shared/, not services/shared)
try:
    import sys
    import os
    # Add repo root to path to find shared/monitoring
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    from shared.monitoring.base import DopemuxMonitoring
except ImportError:
    DopemuxMonitoring = None
    logger = logging.getLogger(__name__)
    logger.warning("DopemuxMonitoring not available - metrics disabled")

# Use relative imports for module execution
from .core.error_handling import (
    GlobalErrorHandler,
    CircuitBreaker,
    CircuitBreakerConfig,
    ErrorType,
    ErrorSeverity
)

# Configure logging
configure_logging("adhd-engine", level=str(settings.log_level))
logger = logging.getLogger(__name__)

# Global instances
engine: ADHDAccommodationEngine = None
error_handler: GlobalErrorHandler = None
circuit_breakers = {}
monitoring: DopemuxMonitoring = None

# Phase 7: Full I/O Wiring globals
workspace_watcher = None
output_dispatcher = None


class _FallbackADHDEngine:
    """Lightweight engine used when test-mode startup must proceed without infra."""

    def __init__(self, startup_error: str):
        self.startup_error = startup_error
        self.user_profiles = {}
        self.current_energy_levels = {}
        self.current_attention_states = {}
        self.predictive_engine = None
        self.is_fallback_engine = True

    async def close(self) -> None:
        return None

    async def _calculate_system_cognitive_load(self) -> float:
        return 0.35

    async def get_energy_level(self, user_id: str):
        class _EnergyState:
            def __init__(self, level: str = "medium", score: float = 0.5):
                self.level = level
                self.score = score

        energy = self.current_energy_levels.get(user_id, "medium")
        energy_text = energy.value if hasattr(energy, "value") else str(energy)
        return _EnergyState(level=energy_text, score=0.5)

    async def get_attention_state(self, user_id: str):
        class _AttentionSnapshot:
            def __init__(self, state: str = "focused"):
                self.state = state

        state = self.current_attention_states.get(user_id, "focused")
        state_text = state.value if hasattr(state, "value") else str(state)
        return _AttentionSnapshot(state=state_text)

    async def get_cognitive_load(self, user_id: str) -> float:
        return await self._calculate_system_cognitive_load()

    async def get_accommodation_health(self) -> dict:
        return {
            "overall_status": "🟡 Degraded",
            "service": "adhd-engine",
            "mode": "fallback",
            "startup_error": self.startup_error,
        }

    async def assess_task_suitability(self, user_id: str, task_data: dict) -> dict:
        complexity = float(task_data.get("complexity_score", 0.5))
        estimated_minutes = int(task_data.get("estimated_minutes", 30))
        suitability_score = max(0.0, min(1.0, 1.0 - (complexity * 0.5)))
        cognitive_load = max(0.0, min(1.0, complexity * 0.8 + (estimated_minutes / 180.0)))

        if cognitive_load < 0.2:
            load_level = "minimal"
        elif cognitive_load < 0.4:
            load_level = "low"
        elif cognitive_load < 0.6:
            load_level = "moderate"
        elif cognitive_load < 0.8:
            load_level = "high"
        else:
            load_level = "extreme"

        return {
            "suitability_score": suitability_score,
            "energy_match": max(0.0, min(1.0, 1.0 - complexity)),
            "attention_compatibility": max(0.0, min(1.0, 1.0 - (complexity * 0.7))),
            "cognitive_load": cognitive_load,
            "cognitive_load_level": load_level,
            "recommendations": [
                {
                    "accommodation_type": "task_chunking",
                    "urgency": "soon",
                    "message": "Break this task into smaller steps",
                    "action_required": False,
                    "suggested_actions": ["Split into 15-minute chunks"],
                    "cognitive_benefit": "Reduces overwhelm",
                    "implementation_effort": "low",
                }
            ],
            "accommodations_needed": ["task_chunking"],
            "optimal_timing": {"recommended_window": "now", "reason": "fallback_engine"},
            "adhd_insights": {
                "hyperfocus_risk": "low",
                "distraction_risk": "medium",
                "context_switch_impact": "medium",
            },
        }

    async def assess_task(self, title: str, description: str = ""):
        class _Assessment:
            def __init__(self, payload: dict):
                self._payload = payload

            def dict(self) -> dict:
                return self._payload

        payload = await self.assess_task_suitability(
            user_id="default",
            task_data={
                "title": title,
                "description": description,
                "complexity_score": 0.5,
                "estimated_minutes": 30,
            },
        )
        return _Assessment(payload)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management.

    Startup:
    - Initialize ADHD accommodation engine
    - Connect to Redis
    - Start 6 background monitoring tasks
    - Start ADHD Event Listener for implicit triggers

    Shutdown:
    - Stop background monitors gracefully
    - Stop ADHD Event Listener

## services/repo-truth-extractor/run_extraction_v5.py
#!/usr/bin/env python3
"""
Master extraction runner (A/H/D/C/E/W/B/G/Q/R/X/T/Z) with deterministic:
inventory -> partitioning -> per-partition raw outputs -> norm merge -> QA.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
import copy
from decimal import Decimal, ROUND_HALF_UP
import fnmatch
import hashlib
import hmac
import json
import logging
import os
import re
import signal
import platform
import subprocess
import sys
import threading
import tempfile
import time
import textwrap
import importlib.util
import random
import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib import error as urllib_error
from urllib import request as urllib_request

import requests
import yaml

# Ensure local service modules are importable when loaded via importlib in tests.
RUNNER_SERVICE_DIR = Path(__file__).resolve().parent
if str(RUNNER_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(RUNNER_SERVICE_DIR))

from output_safety import (
    sanitize_failed_sidecar_text,
    sanitize_payload_for_failed_sidecar,
    sanitize_payload_for_output,
    sanitize_text_for_output,
    sanitize_text_for_provider_payload,
    sanitized_json_bytes,
    sanitized_json_text,
)
from phases import (
    CODE_HEAVY_PHASES,
    LEGACY_PHASE_DIR_ALIASES,
    PHASES,
    PHASE_DIR_NAMES,
    PHASE_DISPLAY_NAMES,
    PHASE_OPTIONAL_DEPENDENCIES,
    PHASE_PURPOSES,
    PHASE_REQUIRED_DEPENDENCIES,
    PHASE_S_BASE_STEPS,
    PHASE_S_BASE_STEP_SET,
    PHASE_SP_BASE_STEPS,
    PHASE_SP_BASE_STEP_SET,
    REQUIRED_PROMPT_STEP_IDS,
    R_OPTIONAL_INPUT_PHASES,
    R_REQUIRED_INPUT_PHASES,
    VERIFY_PHASE_CHOICES,
)
from rte_output_layout import (
    OutputLayout,
    RunContext,
    configure_output_layout as _configure_output_layout_impl,
    current_doctor_root as _current_doctor_root_impl,
    current_extraction_root as _current_extraction_root_impl,
    current_output_layout as _current_output_layout_impl,
    current_runs_root as _current_runs_root_impl,
    generate_run_id as _generate_run_id_impl,
    get_run_dirs as _get_run_dirs_impl,
    latest_run_id_path as _latest_run_id_path_impl,
    load_run_id as _load_run_id_impl,
    persist_latest_run_id as _persist_latest_run_id_impl,
    resolve_run_context as _resolve_run_context_impl,
    validate_existing_run_dir as _validate_existing_run_dir_impl,
)
from rte_ops_surfaces import (
    apply_first_live_preset as _apply_first_live_preset_impl,
    apply_staged_safe_preset as _apply_staged_safe_preset_impl,
    argv_has_flag as _argv_has_flag_impl,
    build_phase_cost_preview as _build_phase_cost_preview_impl,
    collect_provider_routes as _collect_provider_routes_impl,
    derive_route_readiness_summary as _derive_route_readiness_summary_impl,
    first_live_phase_sequence as _first_live_phase_sequence_impl,
    max_files_for_phase as _max_files_for_phase_impl,
    preview_partition_usage as _preview_partition_usage_impl,
    run_pre_live_validator as _run_pre_live_validator_impl,
    run_provider_preflight as _run_provider_preflight_impl,
)
from rte_phase_wrappers import (
    plan_home_phase as _plan_home_phase_impl,
    plan_q_phase as _plan_q_phase_impl,
    plan_r_phase as _plan_r_phase_impl,
    plan_repo_scan_phase as _plan_repo_scan_phase_impl,
    plan_s_phase as _plan_s_phase_impl,
    plan_sp_phase as _plan_sp_phase_impl,
    plan_t_phase as _plan_t_phase_impl,
    plan_x_phase as _plan_x_phase_impl,
)
from rte_promptset import (
    blocked_promptset_payload as _blocked_promptset_payload_impl,
    get_active_s_prompts_mode as _get_active_s_prompts_mode_impl,
    get_s_step_controls as _get_s_step_controls_impl,
    legacy_phase_prompt_specs as _legacy_phase_prompt_specs_impl,
    load_phase_s_registry as _load_phase_s_registry_impl,
    phase_s_registry_dir as _phase_s_registry_dir_impl,
    phase_s_registry_path as _phase_s_registry_path_impl,
    prompt_hash_report_for_phase as _prompt_hash_report_for_phase_impl,
    prompt_root as _prompt_root_impl,
    promptset_fingerprint as _promptset_fingerprint_impl,
    resolve_phase_s_prompts as _resolve_phase_s_prompts_impl,
    resolve_phase_sp_prompts as _resolve_phase_sp_prompts_impl,
    resume_blocked_payload as _resume_blocked_payload_impl,
    set_active_s_prompts_mode as _set_active_s_prompts_mode_impl,
    step_sort_key as _step_sort_key_impl,
    validate_phase_s_registry as _validate_phase_s_registry_impl,
)
from rte_config import (
    BENCHMARK_ROUTE_OWNERSHIP_MODE,
    COST_ABORT_FILENAME,
    COST_ABORT_REASON,
    COVERAGE_ROLLUP_FILENAME,
    D0_MAX_FILES_ENV_VAR,
    D1_MAX_FILES_ENV_VAR,
    DPMX_BENCHMARK_ROUTE_OWNERSHIP_ENV,
    DPMX_EXPLICIT_STEP_ROUTES_ENV,
    DPMX_LIVE_OK_ENV,
    DPMX_MODEL_EXTRACT_ENV,
    DPMX_MODEL_INVENTORY_ENV,
    DPMX_MODEL_QA_ENV,
    DPMX_MODEL_SYNTHESIS_ENV,
    DPMX_ROUTING_ENABLE_ENV,
    DPMX_WEBHOOK_AUTO_CONTINUE_ENV,
    DPMX_WEBHOOK_EVENT,
    DPMX_WEBHOOK_REQUIRED_ENV,
    DPMX_WEBHOOK_SCHEMA,
    DPMX_WEBHOOK_SECRET_ENV,
    DPMX_WEBHOOK_TIMEOUT_SECONDS_ENV,
    DPMX_WEBHOOK_URL_ENV,
    FAILURE_INDEX_FILENAME,
    FIRST_LIVE_INITIAL_PHASES,
    FIRST_LIVE_POST_REVIEW_PHASES,
    FIRST_LIVE_PRESET_DEFAULT_CAP_USD,
    FIRST_LIVE_PRESET_NAME,
    GEMINI_MODELS_ENDPOINT,
    GEMINI_MODELS_FAILED_FILENAME,
    GEMINI_MODELS_FILENAME,
    GEMINI_MODELS_SCHEMA_VERSION,
    INTERACTIVE_SAFE_BATCH_WAIT_SECONDS,
    LEGACY_PROMPT_ROOT_ENV_VAR,
    PARSE_FAILURE_ABORT_THRESHOLD,
    PARSE_RETRY_MAX_EXTRA_ATTEMPTS,
    PRICING_CONFIG_PATH,
    PROOF_PACK_FILENAME,
    PROMPTGEN_DEFAULT_EXCERPT_BYTES,
    PROMPTGEN_DEFAULT_EXCLUDE_GLOBS,
    PROMPTGEN_DEFAULT_INCLUDE_GLOBS,
    PROMPTGEN_DEFAULT_MAX_BYTES,
    PROMPTGEN_DEFAULT_MAX_FILES,
    PROMPTGEN_DEFAULT_OUTPUT_DIR,
    PROMPTGEN_FAILED_FILENAME,
    PROMPTGEN_FINGERPRINT_FILENAME,
    PROMPTGEN_INPUTS_FILENAME,
    PROMPTGEN_SCANNER_VERSION,
    PROMPT_HASH_MODE,
    PROMPT_ROOT_ENV_VAR,
    PROMPTSET_BLOCKED_EXIT_CODE,
    PROMPTSET_BLOCKED_REASON,
    REPO_ROOT,
    RESUME_PROOF_FILENAME,
    RETRY_COST_REPORT_FILENAME,
    RUN_DASHBOARD_FILENAME,
    RUN_LOG_FILENAME,
    RUNNER_SCRIPT,
    SPEND_LEDGER_FILENAME,
    STEP_METRICS_FILENAME,
    STRICT_PASSTHROUGH_ATTESTATIONS_FILENAME,
    STAGED_SAFE_PRESET_DEFAULT_CAP_USD,
    STAGED_SAFE_PRESET_NAME,
    STRING_LITERAL_ERROR_SNIPPETS,
    S_PROMPTS_AUTO,
    S_PROMPTS_LEGACY,
    S_PROMPTS_MODE_ENV_VAR,
    S_PROMPTS_MODES,
    S_PROMPTS_REGISTRY,
    S_STEPS_ENV_VAR,
    TELEMETRY_DIRNAME,
    TERMINAL_TIMELINE_FILENAME,
    V5_DOCTOR_ROOT,
    V5_EXTRACTION_ROOT,
    V5_LATEST_RUN_FILE,
    V5_RUNS_ROOT,
)
from rte_reports import (
    ReportingDeps,
    TelemetryWriterDeps,
    gather_phase_counts as rte_gather_phase_counts,
    refresh_run_manifest_artifacts as rte_refresh_run_manifest_artifacts,
    update_proof_pack as rte_update_proof_pack,
    update_run_manifest_contract_map as rte_update_run_manifest_contract_map,
    update_run_manifest_promptset_block as rte_update_run_manifest_promptset_block,
    write_blocked_promptset_proof_pack as rte_write_blocked_promptset_proof_pack,
    write_certification_result as rte_write_certification_result,
    write_coverage_rollup as rte_write_coverage_rollup,
    write_failure_index_snapshot as rte_write_failure_index_snapshot,
    write_phase_coverage_manifest as rte_write_phase_coverage_manifest,
    write_promptset_blocked_marker as rte_write_promptset_blocked_marker,
    write_resume_proof as rte_write_resume_proof,
    write_run_dashboard_snapshot as rte_write_run_dashboard_snapshot,
    write_run_manifest as rte_write_run_manifest,
    write_runner_identity as rte_write_runner_identity,
    write_step_metrics_snapshot as rte_write_step_metrics_snapshot,
)
from reporting import build_run_id_resolution_precedence
from rte_constants import (
    RUN_STATUS_BLOCKED,
    RUN_STATUS_COST_ABORTED,
    RUN_STATUS_OK,
)
from llm_runtime import (
    LLMRuntimeDeps,
    _RESPONSE_SUMMARY_PASSTHROUGH_KEYS,
    _provider_route_kind,
    backoff_seconds as llm_runtime_backoff_seconds,
    call_llm as llm_runtime_call_llm,
    call_llm_with_ladder as llm_runtime_call_llm_with_ladder,
    classify_route_identity as llm_runtime_classify_route_identity,
    coerce_artifacts_from_response as llm_runtime_coerce_artifacts_from_response,
    comparison_artifact_dir as llm_runtime_comparison_artifact_dir,
    classify_route_identity as llm_runtime_classify_route_identity,
    compute_comparison_resume_decision as llm_runtime_compute_comparison_resume_decision,
    is_auth_classified_failure as llm_runtime_is_auth_classified_failure,
    is_retryable_exception as llm_runtime_is_retryable_exception,
    normalize_response_artifacts as llm_runtime_normalize_response_artifacts,
    parse_json_from_response as llm_runtime_parse_json_from_response,
    parse_json_from_response_with_provenance as llm_runtime_parse_json_from_response_with_provenance,
    run_comparison_lane as llm_runtime_run_comparison_lane,
    should_retry as llm_runtime_should_retry,
)
from lib.pricing_surface import pricing_surface_metadata
from lib.risk_dashboard import (
    build_rte_risk_dashboard,
    collect_rte_risk_dashboard_inputs,
    write_rte_risk_dashboard_artifacts,
)
from lib.route_options import (
    ROUTE_REQUEST_OPTION_KEYS,
    normalize_route_request_options as _shared_normalize_route_request_options,
