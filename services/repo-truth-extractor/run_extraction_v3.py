#!/usr/bin/env python3
"""
Master extraction runner (A/H/D/C/E/W/B/G/Q/R/X/T/Z) with deterministic:
inventory -> partitioning -> per-partition raw outputs -> norm merge -> QA.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
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
import time
import importlib.util
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
from urllib import error as urllib_error
from urllib import request as urllib_request

import requests

# Ensure local service modules are importable when loaded via importlib in tests.
RUNNER_SERVICE_DIR = Path(__file__).resolve().parent
if str(RUNNER_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(RUNNER_SERVICE_DIR))

try:
    from lib.batch_clients import (
        BatchClient,
        BatchRequest,
        BatchResult,
        BatchRoute,
        GeminiBatchClient,
        OpenAIBatchClient,
        XAIBatchClient,
    )
except ModuleNotFoundError:
    batch_clients_path = RUNNER_SERVICE_DIR / "lib" / "batch_clients.py"
    batch_clients_spec = importlib.util.spec_from_file_location("repo_truth_batch_clients", batch_clients_path)
    if not batch_clients_spec or not batch_clients_spec.loader:
        raise
    batch_clients_module = importlib.util.module_from_spec(batch_clients_spec)
    batch_clients_spec.loader.exec_module(batch_clients_module)
    BatchClient = batch_clients_module.BatchClient
    BatchRequest = batch_clients_module.BatchRequest
    BatchResult = batch_clients_module.BatchResult
    BatchRoute = batch_clients_module.BatchRoute
    GeminiBatchClient = batch_clients_module.GeminiBatchClient
    OpenAIBatchClient = batch_clients_module.OpenAIBatchClient
    XAIBatchClient = batch_clients_module.XAIBatchClient
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
    )
    from rich.table import Table
    from rich.text import Text
except Exception:  # pragma: no cover - optional rich rendering
    Console = None  # type: ignore[assignment]
    Panel = None  # type: ignore[assignment]
    Progress = None  # type: ignore[assignment]
    SpinnerColumn = None  # type: ignore[assignment]
    BarColumn = None  # type: ignore[assignment]
    MofNCompleteColumn = None  # type: ignore[assignment]
    TimeElapsedColumn = None  # type: ignore[assignment]
    TextColumn = None  # type: ignore[assignment]
    Table = None  # type: ignore[assignment]
    Text = None  # type: ignore[assignment]

# --- Configuration & Constants ---

PHASES = ["A", "H", "D", "C", "E", "W", "B", "G", "Q", "R", "X", "T", "Z", "S"]
PROMPT_HASH_MODE = "strict"
PROMPT_ROOT_ENV_VAR = "REPO_TRUTH_EXTRACTOR_PROMPT_ROOT"
LEGACY_PROMPT_ROOT_ENV_VAR = "UPGRADES_PROMPT_ROOT"
VERIFY_PHASE_CHOICES = PHASES + ["ALL"]
PROOF_PACK_FILENAME = "PROOF_PACK.json"
COVERAGE_ROLLUP_FILENAME = "COVERAGE_ROLLUP.json"
RESUME_PROOF_FILENAME = "RESUME_PROOF.json"
RUN_LOG_FILENAME = "RUN.log"
PROMPTSET_BLOCKED_REASON = "PROMPTSET_INVALID"
PROMPTSET_BLOCKED_EXIT_CODE = 2
RUNNER_SCRIPT = Path(__file__).resolve()
PROMPTGEN_SCANNER_VERSION = "GX0_SCANNER_V1"
PROMPTGEN_INPUTS_FILENAME = "PROMPTGEN_INPUTS.json"
PROMPTGEN_FINGERPRINT_FILENAME = "PROJECT_FINGERPRINT.json"
PROMPTGEN_FAILED_FILENAME = "GX0_PROMPTGEN_SCAN.FAILED.json"
GEMINI_MODELS_FILENAME = "GEMINI_MODELS.json"
GEMINI_MODELS_FAILED_FILENAME = "GEMINI_MODELS.FAILED.json"
GEMINI_MODELS_SCHEMA_VERSION = "GEMINI_MODELS_V1"
GEMINI_MODELS_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models"
PARSE_RETRY_MAX_EXTRA_ATTEMPTS = 1
STRING_LITERAL_ERROR_SNIPPETS = (
    "unterminated string",
    "invalid \\escape",
    "invalid \\u",
    "invalid control character",
)
PROMPTGEN_DEFAULT_MAX_FILES = 600
PROMPTGEN_DEFAULT_MAX_BYTES = 300000
PROMPTGEN_DEFAULT_EXCERPT_BYTES = 4000
PROMPTGEN_DEFAULT_OUTPUT_DIR = "00_inputs"
PROMPTGEN_DEFAULT_INCLUDE_GLOBS = [
    "pyproject.toml",
    "dopemux.toml",
    "compose.yml",
    ".claude/**",
    ".dopemux/**",
    ".taskx/**",
    ".github/**",
    "config/**",
    "scripts/**",
    "tools/**",
    "compose/**",
    "docker/**",
    "AGENTS.md",
    "README.md",
    "QUICK_START.md",
    "INSTALL.md",
    "CHANGELOG.md",
]
PROMPTGEN_DEFAULT_EXCLUDE_GLOBS = [
    "**/.git/**",
    "**/.venv/**",
    "**/__pycache__/**",
    "**/node_modules/**",
    "**/dist/**",
    "**/build/**",
    "**/.DS_Store",
    "**/*.png",
    "**/*.jpg",
    "**/*.jpeg",
    "**/*.webp",
    "**/*.gif",
    "**/*.pdf",
    "**/*.zip",
]
# mapping from phase code to directory suffix
PHASE_DIR_NAMES: Dict[str, str] = {
    "A": "A_repo_control_plane",
    "H": "H_home_control_plane",
    "D": "D_docs_pipeline",
    "C": "C_code_surfaces",
    "E": "E_execution_plane",
    "W": "W_workflow_plane",
    "B": "B_boundary_plane",
    "G": "G_governance_plane",
    "Q": "Q_quality_assurance",
    "R": "R_arbitration",
    "X": "X_feature_index",
    "T": "T_task_packets",
    "Z": "Z_handoff_freeze",
    "S": "S_synthesis",
}
LEGACY_PHASE_DIR_ALIASES: Dict[str, str] = {
    "R2_synthesis": "R_arbitration",
}
EXTRACTOR_SERVICE_DIR = RUNNER_SERVICE_DIR
V3_EXTRACTION_ROOT = Path("extraction/repo-truth-extractor/v3")
V3_RUNS_ROOT = V3_EXTRACTION_ROOT / "runs"
V3_LATEST_RUN_FILE = V3_EXTRACTION_ROOT / "latest_run_id.txt"
V3_DOCTOR_ROOT = V3_EXTRACTION_ROOT / "doctor"
CODE_HEAVY_PHASES = {"C", "E", "Q"}
R_REQUIRED_INPUT_PHASES = ["A", "H", "D", "C"]
R_REQUIRED_ARTIFACT_GROUPS: Dict[str, List[Tuple[str, ...]]] = {
    "A": [
        ("REPO_INSTRUCTION_SURFACE.json",),
        ("REPO_INSTRUCTION_REFERENCES.json",),
        ("REPO_MCP_SERVER_DEFS.json",),
        ("REPO_MCP_PROXY_SURFACE.json",),
        ("REPO_ROUTER_SURFACE.json",),
        ("REPO_HOOKS_SURFACE.json",),
        ("REPO_IMPLICIT_BEHAVIOR_HINTS.json",),
        ("REPO_COMPOSE_SERVICE_GRAPH.json",),
        ("REPO_LITELLM_SURFACE.json",),
        ("REPO_TASKX_SURFACE.json",),
    ],
    "H": [
        ("HOME_MCP_SURFACE.json",),
        ("HOME_ROUTER_SURFACE.json",),
        ("HOME_PROVIDER_LADDER_HINTS.json",),
        ("HOME_LITELLM_SURFACE.json",),
        ("HOME_PROFILES_SURFACE.json",),
        ("HOME_TMUX_WORKFLOW_SURFACE.json",),
        ("HOME_SQLITE_SCHEMA.json",),
    ],
    "D": [
        ("DOC_TOPIC_CLUSTERS.json",),
        ("DOC_SUPERSESSION.json",),
        ("DOC_CONTRACT_CLAIMS.json",),
        ("DUPLICATE_DRIFT_REPORT.json", "DOC_RECENCY_DUPLICATE_REPORT.json"),
        ("DOC_INDEX.json",),
    ],
    "C": [
        ("SERVICE_ENTRYPOINTS.json",),
        ("EVENTBUS_SURFACE.json",),
        ("EVENT_PRODUCERS.json",),
        ("EVENT_CONSUMERS.json",),
        ("DOPE_MEMORY_CODE_SURFACE.json",),
        ("DOPE_MEMORY_SCHEMAS.json",),
        ("DOPE_MEMORY_DB_WRITES.json",),
        ("TRINITY_ENFORCEMENT_SURFACE.json",),
        ("REFUSAL_AND_GUARDRAILS_SURFACE.json",),
        ("TASKX_INTEGRATION_SURFACE.json",),
        ("WORKFLOW_RUNNER_SURFACE.json",),
        ("DETERMINISM_RISK_LOCATIONS.json",),
        ("IDEMPOTENCY_RISK_LOCATIONS.json",),
        ("CONCURRENCY_RISK_LOCATIONS.json",),
    ],
}

ROUTING_POLICY_VERSION = "RTE_ROUTING_V1"
DEFAULT_ROUTING_POLICY = "cost"
DEFAULT_GEMINI_MODEL_ID = "gemini-2.5-flash"
STEP_TIERS = ("bulk", "extract", "synthesis", "qa")

MAGIC_SUBTYPE_ORDER = {
    "instructions": 0,
    "mcp_router_provider": 1,
    "compose_bootstrap": 2,
    "hooks": 3,
    "ci": 4,
    "workflow_launchers": 5,
    "instruction_docs": 6,
    "other": 7,
}

# Route tuple: provider, model_id, api_key_env
ROUTING_LADDERS: Dict[str, Dict[str, List[Tuple[str, str, str]]]] = {
    "cost": {
        "bulk": [
            ("openai", "gpt-5-nano", "OPENAI_API_KEY"),
            ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"),
            ("xai", "grok-code-fast-1", "XAI_API_KEY"),
        ],
        "extract": [
            ("openai", "gpt-5-mini", "OPENAI_API_KEY"),
            ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"),
            ("xai", "grok-code-fast-1", "XAI_API_KEY"),
        ],
        "synthesis": [
            ("openai", "gpt-5.2", "OPENAI_API_KEY"),
            ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"),
            ("xai", "grok-code-fast-1", "XAI_API_KEY"),
        ],
        "qa": [
            ("openai", "gpt-5-nano", "OPENAI_API_KEY"),
            ("openai", "gpt-5-mini", "OPENAI_API_KEY"),
            ("openai", "gpt-5.2", "OPENAI_API_KEY"),
        ],
    },
    "balanced": {
        "bulk": [
            ("openai", "gpt-5-nano", "OPENAI_API_KEY"),
            ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"),
            ("openai", "gpt-5-mini", "OPENAI_API_KEY"),
        ],
        "extract": [
            ("openai", "gpt-5-mini", "OPENAI_API_KEY"),
            ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"),
            ("xai", "grok-code-fast-1", "XAI_API_KEY"),
        ],
        "synthesis": [
            ("openai", "gpt-5.2", "OPENAI_API_KEY"),
            ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"),
            ("xai", "grok-code-fast-1", "XAI_API_KEY"),
        ],
        "qa": [
            ("openai", "gpt-5-mini", "OPENAI_API_KEY"),
            ("openai", "gpt-5-nano", "OPENAI_API_KEY"),
            ("gemini", "gemini-2.5-flash", "GEMINI_API_KEY"),
        ],
    },
    "quality": {
        "bulk": [
            ("openai", "gpt-5-mini", "OPENAI_API_KEY"),
            ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"),
            ("xai", "grok-code-fast-1", "XAI_API_KEY"),
        ],
        "extract": [
            ("openai", "gpt-5.2-pro", "OPENAI_API_KEY"),
            ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"),
            ("xai", "grok-code-fast-1", "XAI_API_KEY"),
        ],
        "synthesis": [
            ("openai", "gpt-5.2-pro", "OPENAI_API_KEY"),
            ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"),
            ("xai", "grok-code-fast-1", "XAI_API_KEY"),
        ],
        "qa": [
            ("openai", "gpt-5-mini", "OPENAI_API_KEY"),
            ("openai", "gpt-5.2-pro", "OPENAI_API_KEY"),
            ("gemini", "gemini-2.5-pro", "GEMINI_API_KEY"),
        ],
    },
}

ACTIVE_ROUTING_POLICY = DEFAULT_ROUTING_POLICY
ACTIVE_ROUTING_LADDERS = {
    policy: {tier: list(routes) for tier, routes in tiers.items()}
    for policy, tiers in ROUTING_LADDERS.items()
}

# Phase-level summary route is retained for compatibility surfaces and manifests.
MODEL_ROUTING: Dict[str, Tuple[str, str, str]] = {}
DEFAULT_MODEL_ROUTING: Dict[str, Tuple[str, str, str]] = {}

PROVIDER_BASE_URL = {
    "xai": "https://api.x.ai/v1",
    "gemini": "https://generativelanguage.googleapis.com",
    "openai": "https://api.openai.com/v1",
}

GEMINI_OPENAI_COMPAT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai"

TEXT_SUFFIXES = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".css",
    ".scss",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".sh",
    ".bash",
    ".rb",
    ".go",
    ".rs",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".java",
    ".kt",
    ".swift",
    ".php",
    ".phtml",
    ".pl",
    ".pm",
    ".t",
    ".r",
    ".sql",
    ".ini",
    ".cfg",
    ".conf",
    ".env",
}


def prompt_root() -> Path:
    configured = os.getenv(PROMPT_ROOT_ENV_VAR, "").strip()
    if not configured:
        configured = os.getenv(LEGACY_PROMPT_ROOT_ENV_VAR, "").strip()
    if configured:
        return Path(configured)
    return EXTRACTOR_SERVICE_DIR / "prompts" / "v3"


def step_sort_key(step_id: str) -> Tuple[str, int]:
    match = re.match(r"^([A-Z])(\d+)$", step_id)
    if not match:
        return (step_id[:1], 999999)
    return (match.group(1), int(match.group(2)))

TEXT_NAMES = {
    "Dockerfile",
    "Makefile",
    "Justfile",
    "Rakefile",
    ".githooks",
    ".gitignore",
    "package.json",
    "package-lock.json",
}

HOME_SAFE_ROOTS = [
    ".dopemux",
    ".config/dopemux",
    ".config/taskx",
    ".config/litellm",
    ".config/mcp",
]

HOME_SAFE_ALLOW_SUFFIXES = {
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".md",
    ".txt",
    ".ini",
    ".cfg",
    ".conf",
}

HOME_SAFE_DENY_GLOBS = [
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "*.log",
    "*.cache",
    "*.tmp",
    "*.swp",
    "*cache*",
    "*logs*",
    "*.pem",
    "*.p12",
    "*.pfx",
    "*.der",
    "*.crt",
    "*key*",
    "*token*",
    "*secret*",
    "*pass*",
    "*credential*",
]

REQUIRED_ITEM_KEYS = ["path", "line_range", "id"]
SECRET_LINE_RE = re.compile(
    r"(?i)\b(api[_-]?key|authorization|bearer|token|secret|password|private[_-]?key)\b"
)
SECRET_ASSIGN_RE = re.compile(
    r"(?i)^(\s*['\"]?[^:=\n]*?(?:api[_-]?key|authorization|bearer|token|secret|password|private[_-]?key)"
    r"[^:=\n]*?['\"]?\s*[:=]\s*).*$"
)
LONG_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9+/=_-])[A-Za-z0-9+/=_-]{33,}(?![A-Za-z0-9+/=_-])")
OUTPUT_FILENAME_RE = re.compile(r"\b[A-Z][A-Z0-9_]+(?:\.partX)?\.(?:json|md)\b")
OUTPUT_SECTION_START_RE = re.compile(
    r"(?i)^(?:#+\s*)?(goal(?:s)?|output(?:s)?(?:\s+files?)?|phase\s+[A-Z0-9]+\s+deliverables?)\b[:\-]?\s*$"
)
OUTPUT_SECTION_STOP_PREFIXES = (
    "prompt",
    "inputs",
    "input",
    "rules",
    "rule",
    "task",
    "role",
    "must include",
    "format",
    "action",
    "checks",
    "qa",
    "run per",
    "using",
    "output format",
    "hard rule",
    "evidence hierarchy",
    "arbitration procedure",
)
DEFAULT_OUTPUT_BY_STEP = {
    "T1": ("TP_BACKLOG_TOPN.json",),
}
DPMX_ROUTING_ENABLE_ENV = "DPMX_ROUTING_ENABLE"
DPMX_MODEL_INVENTORY_ENV = "DPMX_MODEL_INVENTORY"
DPMX_MODEL_EXTRACT_ENV = "DPMX_MODEL_EXTRACT"
DPMX_MODEL_SYNTHESIS_ENV = "DPMX_MODEL_SYNTHESIS"
DPMX_MODEL_QA_ENV = "DPMX_MODEL_QA"
DPMX_WEBHOOK_URL_ENV = "DPMX_WEBHOOK_URL"
DPMX_WEBHOOK_SECRET_ENV = "DPMX_WEBHOOK_SECRET"
DPMX_WEBHOOK_TIMEOUT_SECONDS_ENV = "DPMX_WEBHOOK_TIMEOUT_SECONDS"
DPMX_WEBHOOK_REQUIRED_ENV = "DPMX_WEBHOOK_REQUIRED"
DPMX_WEBHOOK_AUTO_CONTINUE_ENV = "DPMX_WEBHOOK_AUTO_CONTINUE"
DPMX_LIVE_OK_ENV = "DPMX_LIVE_OK"
DPMX_WEBHOOK_SCHEMA = "DPMX_WEBHOOK_V1"
DPMX_WEBHOOK_EVENT = "batch.completed"
STEP_TYPE_MODEL_ENV_VARS: Dict[str, str] = {
    "inventory": DPMX_MODEL_INVENTORY_ENV,
    "extract": DPMX_MODEL_EXTRACT_ENV,
    "synthesis": DPMX_MODEL_SYNTHESIS_ENV,
    "qa": DPMX_MODEL_QA_ENV,
}
PROVIDER_API_KEY_ENV: Dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "xai": "XAI_API_KEY",
}
REQUIRED_PROMPT_STEP_IDS: Dict[str, Set[str]] = {
    "A": {"A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A99"},
    "H": {"H0", "H1", "H2", "H3", "H4", "H5", "H6", "H7", "H9"},
    "D": {"D0", "D1", "D2", "D3", "D4", "D5"},
    "C": {"C0", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8", "C9"},
    "E": {"E0", "E1", "E2", "E3", "E4", "E5", "E6", "E9"},
    "W": {"W0", "W1", "W2", "W3", "W4", "W5", "W9"},
    "B": {"B0", "B1", "B2", "B3", "B9"},
    "G": {"G0", "G1", "G2", "G3", "G4", "G9"},
    "Q": {"Q0", "Q1", "Q2", "Q3", "Q9", "Q11"},
    "R": {"R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7", "R8"},
    "X": {"X0", "X1", "X2", "X3", "X4", "X9"},
    "T": {"T0", "T1", "T2", "T3", "T4", "T5", "T9"},
    "Z": {"Z0", "Z1", "Z2", "Z9"},
    "S": {"S0", "S1", "S2", "S3", "S4", "S5"},
}


# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("extract_runner")
_RUN_FILE_HANDLER: Optional[logging.Handler] = None


def configure_run_file_logger(run_root: Path) -> Path:
    global _RUN_FILE_HANDLER
    run_log_path = run_root / RUN_LOG_FILENAME
    run_log_path.parent.mkdir(parents=True, exist_ok=True)
    if _RUN_FILE_HANDLER is not None:
        logger.removeHandler(_RUN_FILE_HANDLER)
        try:
            _RUN_FILE_HANDLER.close()
        except Exception:
            pass
        _RUN_FILE_HANDLER = None
    file_handler = logging.FileHandler(run_log_path, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
    )
    logger.addHandler(file_handler)
    _RUN_FILE_HANDLER = file_handler
    logger.info("RUN_LOG_ENABLED path=%s", run_log_path.resolve())
    return run_log_path


@dataclass(frozen=True)
class RunnerConfig:
    dry_run: bool
    max_files_docs: int
    max_files_code: int
    max_chars: int
    max_request_bytes: int
    file_truncate_chars: int
    home_scan_mode: str
    resume: bool
    fail_fast_auth: bool
    gemini_auth_mode: str
    gemini_transport: str
    openai_transport: str
    xai_transport: str
    retry_policy: str
    retry_max_attempts: int
    retry_base_seconds: float
    retry_max_seconds: float
    phase_auth_fail_threshold: int
    partition_workers: int
    debug_phase_inputs: bool
    fail_fast_missing_inputs: bool
    routing_policy: str = DEFAULT_ROUTING_POLICY
    disable_escalation: bool = False
    escalation_max_hops: int = 2
    batch_mode: bool = False
    batch_provider: str = "auto"
    batch_poll_seconds: int = 30
    batch_wait_timeout_seconds: int = 86400
    batch_max_requests_per_job: int = 2000
    batch_submit_only: bool = False
    webhook_url: str = ""
    webhook_secret: str = ""
    webhook_timeout_seconds: int = 5
    webhook_required: bool = False
    webhook_auto_continue: bool = False
    live_ok: bool = False


@dataclass(frozen=True)
class PromptSpec:
    step_id: str
    prompt_path: Path
    output_artifacts: Tuple[str, ...]


@dataclass(frozen=True)
class RunContext:
    run_id: str
    source: str
    latest_file: Path
    latest_written: bool


@dataclass(frozen=True)
class BatchWatchResult:
    exit_code: int
    next_phase: Optional[str] = None
    auto_continue_blocked: bool = False


@dataclass(frozen=True)
class UiConfig:
    mode: str = "auto"  # auto|rich|plain
    quiet: bool = False
    jsonl_events: bool = False


class UI:
    def __init__(self, cfg: UiConfig, run_root: Path, run_id: str):
        self.cfg = cfg
        self.run_root = run_root
        self.run_id = run_id
        self._stdout_is_tty = sys.stdout.isatty()
        self._console: Optional[Any] = None
        self._progress: Optional[Any] = None
        self._task_id: Optional[int] = None
        self._progress_total = 0
        self._rich = False

        requested = cfg.mode
        want_rich = requested == "rich" or (requested == "auto" and self._stdout_is_tty)
        if want_rich and Console is not None and Progress is not None:
            self._console = Console(force_terminal=(requested == "rich"))
            self._rich = True

        self._events_path: Optional[Path] = None
        if cfg.jsonl_events:
            self._events_path = run_root / "events.jsonl"

    def _emit_event(self, payload: Dict[str, Any]) -> None:
        if self._events_path is None:
            return
        row = dict(payload)
        row.setdefault("ts", now_iso())
        row.setdefault("run_id", self.run_id)
        row.setdefault("run_root", str(self.run_root.resolve()))
        try:
            self._events_path.parent.mkdir(parents=True, exist_ok=True)
            with self._events_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")
        except Exception:
            # UI event persistence must never alter execution flow.
            return

    def _print_plain(self, line: str) -> None:
        print(line, flush=True)

    def _summary_line(self, line: str) -> None:
        if self._rich and self._console is not None:
            self._console.print(line)
        else:
            self._print_plain(line)

    def step_progress_stop(self) -> None:
        if self._progress is not None:
            self._progress.stop()
            self._progress = None
            self._task_id = None
            self._progress_total = 0

    def phase_start(
        self,
        phase: str,
        phase_dir: Path,
        inventory: int,
        partitions: int,
        provider: str,
        model_id: str,
        workers: int,
        flags: str,
        routing_policy: str = DEFAULT_ROUTING_POLICY,
        tier_defaults: Optional[Dict[str, str]] = None,
    ) -> None:
        self._emit_event(
            {
                "type": "phase_start",
                "phase": phase,
                "phase_dir": str(phase_dir.resolve()),
                "inventory": inventory,
                "partitions": partitions,
                "provider": provider,
                "model_id": model_id,
                "workers": workers,
                "flags": flags,
                "routing_policy": routing_policy,
                "tier_defaults": dict(tier_defaults or {}),
            }
        )
        if self.cfg.quiet:
            return
        if self._rich and self._console is not None and Panel is not None and Text is not None:
            body = Text()
            body.append(f"run={self.run_id}\n")
            body.append(f"phase={phase}\n")
            body.append(f"phase_dir={phase_dir.resolve()}\n")
            body.append(f"inventory={inventory} partitions={partitions}\n")
            body.append(f"provider={provider} model={model_id} workers={workers}\n")
            body.append(f"routing_policy={routing_policy}\n")
            if tier_defaults:
                body.append(f"tier_defaults={json.dumps(tier_defaults, sort_keys=True)}\n")
            body.append(f"flags={flags}")
            self._console.print(Panel(body, title=f"Phase {phase}", expand=False))
            return
        self._print_plain(
            (
                f"PHASE_START phase={phase} run_id={self.run_id} phase_dir={phase_dir.resolve()} "
                f"inventory={inventory} partitions={partitions} provider={provider} model={model_id} "
                f"workers={workers} routing_policy={routing_policy} "
                f"tier_defaults={json.dumps(tier_defaults or {}, sort_keys=True)} flags={flags}"
            )
        )

    def phase_inputs_provenance(
        self,
        phase: str,
        inventory_meta: Dict[str, Any],
        partitions_meta: Dict[str, Any],
    ) -> None:
        self._emit_event(
            {
                "type": "phase_inputs_provenance",
                "phase": phase,
                "inventory": inventory_meta,
                "partitions": partitions_meta,
            }
        )
        if self.cfg.quiet:
            return
        inv_size = int(inventory_meta.get("size", 0))
        part_size = int(partitions_meta.get("size", 0))
        if self._rich and self._console is not None:
            self._console.print(
                f"inputs_written phase={phase} inventory_bytes={inv_size} partitions_bytes={part_size}"
            )
            return
        self._print_plain(
            f"PHASE_INPUTS phase={phase} inventory_bytes={inv_size} partitions_bytes={part_size}"
        )

    def step_start(
        self,
        phase: str,
        step_id: str,
        prompt_path: Path,
        outputs: Tuple[str, ...],
        partitions_total: int,
        provider: str,
        model_id: str,
        step_tier: str = "extract",
        routing_policy: str = DEFAULT_ROUTING_POLICY,
    ) -> None:
        self._emit_event(
            {
                "type": "step_start",
                "phase": phase,
                "step": step_id,
                "prompt": str(prompt_path.resolve()),
                "outputs": list(outputs),
                "partitions_total": partitions_total,
                "provider": provider,
                "model_id": model_id,
                "step_tier": step_tier,
                "routing_policy": routing_policy,
            }
        )
        if self.cfg.quiet:
            return
        if self._rich and self._console is not None and TextColumn is not None:
            self.step_progress_stop()
            self._progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                TextColumn("ok={task.fields[ok]} fail={task.fields[failed]} skip={task.fields[skipped]} retry={task.fields[retried]}"),
                console=self._console,
                transient=True,
            )
            self._progress.start()
            self._progress_total = max(0, int(partitions_total))
            total = max(1, self._progress_total)
            self._task_id = self._progress.add_task(
                f"{phase}:{step_id}",
                total=total,
                ok=0,
                failed=0,
                skipped=0,
                retried=0,
            )
            return
        self._print_plain(
            (
                f"STEP_START phase={phase} step={step_id} partitions={partitions_total} "
                f"prompt={prompt_path.name} outputs={list(outputs)} tier={step_tier} "
                f"provider={provider} model={model_id} routing_policy={routing_policy}"
            )
        )

    def escalation_event(
        self,
        phase: str,
        step_id: str,
        partition_id: str,
        reason: str,
        from_route: str,
        to_route: str,
        hop: int,
    ) -> None:
        self._emit_event(
            {
                "type": "escalation",
                "phase": phase,
                "step": step_id,
                "partition_id": partition_id,
                "reason": reason,
                "from_route": from_route,
                "to_route": to_route,
                "hop": hop,
            }
        )
        if self.cfg.quiet:
            return
        self._summary_line(
            (
                f"ESCALATE phase={phase} step={step_id} partition={partition_id} "
                f"reason={reason} from={from_route} to={to_route} hop={hop}"
            )
        )

    def batch_event(
        self,
        phase: str,
        step_id: str,
        status: str,
        provider: str,
        details: str = "",
    ) -> None:
        self._emit_event(
            {
                "type": "batch",
                "phase": phase,
                "step": step_id,
                "status": status,
                "provider": provider,
                "details": details,
            }
        )
        if self.cfg.quiet:
            return
        suffix = f" {details}" if details else ""
        self._summary_line(
            f"BATCH phase={phase} step={step_id} status={status} provider={provider}{suffix}"
        )

    def partition_result(
        self,
        phase: str,
        step_id: str,
        completed: int,
        total: int,
        ok: int,
        failed: int,
        skipped: int,
        retried: int,
    ) -> None:
        self._emit_event(
            {
                "type": "partition_result",
                "phase": phase,
                "step": step_id,
                "completed": completed,
                "total": total,
                "ok": ok,
                "failed": failed,
                "skipped": skipped,
                "retried": retried,
            }
        )
        if self.cfg.quiet:
            return
        if self._rich and self._progress is not None and self._task_id is not None:
            bounded_total = max(1, total)
            self._progress.update(self._task_id, total=bounded_total)
            self._progress.update(
                self._task_id,
                completed=min(completed, bounded_total),
                ok=ok,
                failed=failed,
                skipped=skipped,
                retried=retried,
            )

    def step_done(
        self,
        phase: str,
        step_id: str,
        partitions_total: int,
        ok: int,
        failed: int,
        retries: int,
        skipped: int,
        elapsed_ms: int,
        norm_written: int,
        qa_file: str,
        hop_distribution: Optional[Dict[str, int]] = None,
        escalated_partitions: int = 0,
        execution_mode_counts: Optional[Dict[str, int]] = None,
        final_route_counts: Optional[Dict[str, int]] = None,
    ) -> None:
        self.step_progress_stop()
        self._emit_event(
            {
                "type": "step_done",
                "phase": phase,
                "step": step_id,
                "partitions_total": partitions_total,
                "ok": ok,
                "failed": failed,
                "retries": retries,
                "skipped": skipped,
                "elapsed_ms": elapsed_ms,
                "norm_written": norm_written,
                "qa_file": qa_file,
                "hop_distribution": dict(hop_distribution or {}),
                "escalated_partitions": int(escalated_partitions),
                "execution_mode_counts": dict(execution_mode_counts or {}),
                "final_route_counts": dict(final_route_counts or {}),
            }
        )
        self._summary_line(
            (
                f"STEP_DONE phase={phase} step={step_id} ok={ok} failed={failed} "
                f"retries={retries} skipped={skipped} elapsed_ms={elapsed_ms} "
                f"norm_written={norm_written} qa_file={qa_file} "
                f"hops={json.dumps(hop_distribution or {}, sort_keys=True)} "
                f"escalated={escalated_partitions} "
                f"exec_mode={json.dumps(execution_mode_counts or {}, sort_keys=True)} "
                f"routes={json.dumps(final_route_counts or {}, sort_keys=True)}"
            )
        )

    def phase_done(
        self,
        phase: str,
        status: str,
        raw_ok: int,
        raw_failed: int,
        raw_total: int,
        norm_count: int,
        qa_count: int,
        phase_dir: Path,
    ) -> None:
        self.step_progress_stop()
        self._emit_event(
            {
                "type": "phase_done",
                "phase": phase,
                "status": status,
                "raw_ok": raw_ok,
                "raw_failed": raw_failed,
                "raw_total": raw_total,
                "norm_count": norm_count,
                "qa_count": qa_count,
                "phase_dir": str(phase_dir.resolve()),
            }
        )
        self._summary_line(
            (
                f"PHASE_DONE phase={phase} status={status} raw_ok={raw_ok} raw_failed={raw_failed} "
                f"raw_total={raw_total} norm={norm_count} qa={qa_count} phase_dir={phase_dir.resolve()}"
            )
        )

    def verify_result(
        self,
        phase: str,
        status: str,
        counts: Dict[str, Any],
        reasons: List[str],
        phase_dir: Path,
    ) -> None:
        self._emit_event(
            {
                "type": "verify_result",
                "phase": phase,
                "status": status,
                "counts": counts,
                "reasons": reasons,
                "phase_dir": str(phase_dir.resolve()),
            }
        )

    def status_table(self, payload: Dict[str, Any], clear: bool = False) -> None:
        self._emit_event({"type": "status_snapshot", "payload": payload})
        if self._rich and Table is not None and self._console is not None:
            if clear:
                self._console.clear()
            summary = payload.get("summary", {})
            self._console.print(
                (
                    f"run={payload.get('run_id')} run_dir={payload.get('run_dir')} "
                    f"PASS={summary.get('PASS', 0)} FAIL={summary.get('FAIL', 0)} "
                    f"IN_PROGRESS={summary.get('IN_PROGRESS', 0)} NOT_STARTED={summary.get('NOT_STARTED', 0)}"
                )
            )
            table = Table(show_header=True, header_style="bold")
            table.add_column("Phase")
            table.add_column("Status")
            table.add_column("Inputs")
            table.add_column("Raw (ok/failed/total)")
            table.add_column("Norm")
            table.add_column("QA")
            table.add_column("Last Modified (UTC)")
            table.add_column("Phase Dir")
            for phase in PHASES:
                row = payload.get("phases", {}).get(phase, {})
                table.add_row(
                    phase,
                    str(row.get("status", "UNKNOWN")),
                    str(row.get("inputs_count", 0)),
                    f"{row.get('raw_ok', 0)}/{row.get('raw_failed_sidecars', 0)}/{row.get('raw_total', 0)}",
                    str(row.get("norm_count", 0)),
                    str(row.get("qa_count", 0)),
                    str(row.get("last_modified") or "-"),
                    str(row.get("phase_dir") or "-"),
                )
            self._console.print(table)
            return

        if clear and self._stdout_is_tty:
            self._print_plain("\033[2J\033[H")
        summary = payload.get("summary", {})
        self._print_plain(
            (
                f"run={payload.get('run_id')} run_dir={payload.get('run_dir')} "
                f"PASS={summary.get('PASS', 0)} FAIL={summary.get('FAIL', 0)} "
                f"IN_PROGRESS={summary.get('IN_PROGRESS', 0)} NOT_STARTED={summary.get('NOT_STARTED', 0)}"
            )
        )
        self._print_plain(
            "phase status inputs raw_ok raw_failed raw_total norm qa last_modified_utc phase_dir"
        )
        for phase in PHASES:
            row = payload.get("phases", {}).get(phase, {})
            self._print_plain(
                (
                    f"{phase} {row.get('status', 'UNKNOWN')} {row.get('inputs_count', 0)} "
                    f"{row.get('raw_ok', 0)} {row.get('raw_failed_sidecars', 0)} {row.get('raw_total', 0)} "
                    f"{row.get('norm_count', 0)} {row.get('qa_count', 0)} {row.get('last_modified') or '-'} "
                    f"{row.get('phase_dir') or '-'}"
                )
            )


@dataclass
class PartitionExecResult:
    partition_id: str
    write_ops: List[Dict[str, Any]]
    logs: List[Tuple[str, str]]
    request_meta: Dict[str, Any]
    artifacts: List[Dict[str, Any]]
    success: bool
    resume_skipped: bool
    auth_failure: bool
    auth_expired: bool
    recomputed_delta: int
    dry_run_delta: int
    failed_delta: int


class PromptsetBlockedError(RuntimeError):
    """Raised when promptset validation fails in strict mode."""


# --- Helpers ---

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _phase_input_stat(path: Path) -> Dict[str, Any]:
    resolved = path.resolve()
    if not resolved.exists():
        return {
            "exists": False,
            "size": 0,
            "mtime": None,
            "path": str(resolved),
        }
    stats = resolved.stat()
    return {
        "exists": True,
        "size": int(stats.st_size),
        "mtime": datetime.fromtimestamp(stats.st_mtime, timezone.utc).isoformat().replace("+00:00", "Z"),
        "path": str(resolved),
    }


def load_run_id(root: Path) -> Optional[str]:
    """Load latest run_id from file; return None if unavailable."""
    id_file = root / V3_LATEST_RUN_FILE
    if not id_file.exists():
        return None
    run_id = id_file.read_text(encoding="utf-8").strip()
    if not run_id:
        return None
    return run_id


def _validate_existing_run_dir(root: Path, run_id: str, allow_create_if_missing: bool = False) -> None:
    candidate = root / V3_RUNS_ROOT / run_id
    if not candidate.exists():
        if allow_create_if_missing:
            candidate.mkdir(parents=True, exist_ok=True)
            return
        raise FileNotFoundError(f"Run directory {candidate} does not exist.")
    if not candidate.is_dir():
        raise NotADirectoryError(f"Path {candidate} is not a directory.")


def _generate_run_id(root: Path) -> str:
    base = datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%SZ")
    runs_root = root / V3_RUNS_ROOT
    runs_root.mkdir(parents=True, exist_ok=True)

    candidate = runs_root / base
    suffix = 1
    while candidate.exists():
        candidate = runs_root / f"{base}_{suffix:02d}"
        suffix += 1
    candidate.mkdir(parents=True, exist_ok=False)
    return candidate.name


def latest_run_id_path(root: Path) -> Path:
    return root / V3_LATEST_RUN_FILE


def persist_latest_run_id(root: Path, run_id: str) -> None:
    id_file = latest_run_id_path(root)
    id_file.parent.mkdir(parents=True, exist_ok=True)
    id_file.write_text(run_id + "\n", encoding="utf-8")


def resolve_run_context(
    root: Path,
    args: argparse.Namespace,
    allow_create_if_missing: bool = False,
) -> RunContext:
    latest_file = latest_run_id_path(root)
    run_id_source = "generated"

    if args.run_id:
        run_id = args.run_id
        _validate_existing_run_dir(root, run_id, allow_create_if_missing=allow_create_if_missing)
        run_id_source = "explicit"
    else:
        latest = load_run_id(root)
        if latest:
            latest_dir = root / V3_RUNS_ROOT / latest
            if latest_dir.exists() and latest_dir.is_dir():
                run_id = latest
                run_id_source = "latest_run_id"
            else:
                logger.warning(
                    "latest_run_id.txt points to missing run directory %s; generating new run_id.",
                    latest_dir,
                )
                run_id = _generate_run_id(root)
        else:
            run_id = _generate_run_id(root)

    write_latest = (
        not args.no_write_latest
        and (not args.dry_run or args.write_latest_even_on_dry_run)
    )
    if write_latest:
        persist_latest_run_id(root, run_id)

    return RunContext(
        run_id=run_id,
        source=run_id_source,
        latest_file=latest_file,
        latest_written=write_latest,
    )


def get_run_dirs(root: Path, run_id: str) -> Dict[str, Path]:
    """Return dict of run paths and ensure required folders exist."""
    base = root / V3_RUNS_ROOT / run_id
    if not base.exists():
        raise FileNotFoundError(f"Run directory {base} does not exist.")
    for legacy_name, canonical_name in LEGACY_PHASE_DIR_ALIASES.items():
        legacy_path = base / legacy_name
        canonical_path = base / canonical_name
        if legacy_path.exists():
            if canonical_path.exists():
                raise RuntimeError(
                    f"Run directory has both canonical and legacy phase folders: {canonical_path} and {legacy_path}. "
                    f"Keep only canonical {canonical_name}."
                )
            raise RuntimeError(
                f"Legacy phase folder detected: {legacy_path}. Rename it to canonical {canonical_path} before running."
            )

    dirs: Dict[str, Path] = {"root": base, "inputs": base / "00_inputs"}
    for phase, suffix in PHASE_DIR_NAMES.items():
        dirs[phase] = base / suffix

    (dirs["inputs"]).mkdir(parents=True, exist_ok=True)
    for phase in PHASES:
        phase_dir = dirs[phase]
        (phase_dir / "inputs").mkdir(parents=True, exist_ok=True)
        (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
        (phase_dir / "norm").mkdir(parents=True, exist_ok=True)
        (phase_dir / "qa").mkdir(parents=True, exist_ok=True)

    return dirs


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_json_with_sha256(path: Path, payload: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
    path.write_bytes(raw)
    digest = sha256_bytes(raw)
    sidecar = path.with_suffix(".sha256")
    sidecar.write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    return digest


def _promptgen_relpath(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _promptgen_generated_at(run_id: str) -> str:
    seed = int(hashlib.sha256(run_id.encode("utf-8")).hexdigest()[:8], 16)
    return datetime.fromtimestamp(seed, timezone.utc).replace(microsecond=0).isoformat()


def _matches_promptgen_exclude(relpath: str, name: str, excludes: List[str]) -> bool:
    for pattern in excludes:
        if fnmatch.fnmatch(relpath, pattern) or fnmatch.fnmatch(name, pattern):
            return True
    return False


def _select_promptgen_files(
    root: Path,
    include_globs: List[str],
    exclude_globs: List[str],
    max_files: int,
) -> List[Dict[str, Any]]:
    selected: Dict[str, Dict[str, Any]] = {}
    max_allowed = max(0, int(max_files))
    for include_glob in include_globs:
        for candidate in sorted(root.glob(include_glob), key=lambda p: p.as_posix()):
            if not candidate.is_file():
                continue
            if not is_within(candidate, root):
                continue
            relpath = _promptgen_relpath(candidate, root)
            if _matches_promptgen_exclude(relpath, candidate.name, exclude_globs):
                continue
            if relpath not in selected:
                selected[relpath] = {
                    "path": candidate.resolve(),
                    "relpath": relpath,
                    "reason": f"include:{include_glob}",
                }

    ordered = [selected[key] for key in sorted(selected)]
    if max_allowed and len(ordered) > max_allowed:
        ordered = ordered[:max_allowed]
    elif max_allowed == 0:
        ordered = []
    return ordered


def _read_excerpt_bytes(content: bytes, excerpt_limit: int) -> bytes:
    return content[: max(0, int(excerpt_limit))]


def _promptgen_excerpt_priority(relpath: str) -> int:
    root_name = relpath.split("/", 1)[0]
    if (
        relpath in {"pyproject.toml", "dopemux.toml", "AGENTS.md"}
        or relpath.startswith(".claude/")
        or relpath.startswith(".taskx/")
        or relpath.startswith(".github/")
        or relpath.startswith("config/")
        or relpath == "compose.yml"
        or relpath.startswith("compose.yml")
    ):
        return 0
    if relpath in {"README.md", "QUICK_START.md", "INSTALL.md", "CHANGELOG.md"} or relpath.startswith("docs/"):
        return 1
    if root_name in {"scripts", "tools", "docker", "compose"}:
        return 2
    return 3


def _apply_excerpt_pack_policy(
    rows: List[Dict[str, Any]],
    max_total_bytes: int,
) -> Dict[str, Any]:
    cap = max(0, int(max_total_bytes))
    working = sorted(
        [
            {
                "relpath": row["relpath"],
                "priority": _promptgen_excerpt_priority(row["relpath"]),
                "raw_excerpt": row["raw_excerpt"],
                "raw_excerpt_len": len(row["raw_excerpt"]),
            }
            for row in rows
        ],
        key=lambda item: item["relpath"],
    )
    assigned: Dict[str, bytes] = {item["relpath"]: b"" for item in working}
    policy = "full"
    dropped_count = 0
    reduced = False

    if cap <= 0:
        return {
            "policy": "omitted_due_to_limits",
            "assigned": assigned,
            "dropped_count": len(working),
            "reduced_per_file": False,
        }

    keep = list(working)
    total = sum(item["raw_excerpt_len"] for item in keep)
    if total > cap:
        drop_order = sorted(keep, key=lambda item: (-item["priority"], item["relpath"]))
        keep_set = {item["relpath"] for item in keep}
        for item in drop_order:
            if total <= cap:
                break
            if item["relpath"] not in keep_set:
                continue
            keep_set.remove(item["relpath"])
            dropped_count += 1
            total -= item["raw_excerpt_len"]
        keep = [item for item in keep if item["relpath"] in keep_set]
        policy = "dropped_low_priority_files"

    if not keep:
        return {
            "policy": "omitted_due_to_limits",
            "assigned": assigned,
            "dropped_count": dropped_count,
            "reduced_per_file": False,
        }

    if total > cap:
        reduced = True
        per_file = cap // len(keep)
        remainder = cap % len(keep)
        for index, item in enumerate(sorted(keep, key=lambda row: row["relpath"])):
            allowed = per_file + (1 if index < remainder else 0)
            assigned[item["relpath"]] = item["raw_excerpt"][:allowed]
        if sum(len(blob) for blob in assigned.values()) <= 0:
            return {
                "policy": "omitted_due_to_limits",
                "assigned": {key: b"" for key in assigned},
                "dropped_count": dropped_count,
                "reduced_per_file": True,
            }
        policy = "dropped_and_reduced_per_file" if dropped_count else "reduced_per_file"
    else:
        for item in keep:
            assigned[item["relpath"]] = item["raw_excerpt"]

    return {
        "policy": policy,
        "assigned": assigned,
        "dropped_count": dropped_count,
        "reduced_per_file": reduced,
    }


def _detect_tooling_from_pyproject(pyproject_bytes: Optional[bytes]) -> Dict[str, Any]:
    if not pyproject_bytes:
        return {"present": False, "build_backend": None, "tooling": []}

    text = pyproject_bytes.decode("utf-8", errors="ignore")
    build_backend: Optional[str] = None
    tooling: Set[str] = set()

    try:
        import tomllib

        parsed = tomllib.loads(text)
        if isinstance(parsed, dict):
            build_system = parsed.get("build-system")
            if isinstance(build_system, dict):
                backend = build_system.get("build-backend")
                if isinstance(backend, str):
                    build_backend = backend
            tool_section = parsed.get("tool")
            if isinstance(tool_section, dict):
                for key in tool_section:
                    if isinstance(key, str):
                        tooling.add(key)
    except Exception:
        backend_match = re.search(r'(?m)^\s*build-backend\s*=\s*"([^"]+)"\s*$', text)
        if backend_match:
            build_backend = backend_match.group(1).strip()
        for match in re.finditer(r"(?m)^\s*\[tool\.([A-Za-z0-9_.-]+)\]\s*$", text):
            tooling.add(match.group(1))

    return {
        "present": True,
        "build_backend": build_backend,
        "tooling": sorted(tooling),
    }


def _parse_compose_services(
    selected_files: List[Dict[str, Any]],
    file_bytes_map: Dict[str, bytes],
) -> Dict[str, Any]:
    compose_rows = [
        row
        for row in selected_files
        if row["relpath"] == "compose.yml"
        or row["relpath"].startswith("compose.yml")
        or (row["relpath"].startswith("compose/") and row["relpath"].endswith((".yml", ".yaml")))
    ]
    compose_rows = sorted(compose_rows, key=lambda row: row["relpath"])

    services: Set[str] = set()
    ports: Set[str] = set()
    volumes: Set[str] = set()
    parser = "regex"
    yaml_available = False
    yaml_mod = None
    try:
        import yaml as yaml_mod  # type: ignore

        yaml_available = True
    except Exception:
        yaml_available = False

    for row in compose_rows:
        raw = file_bytes_map.get(row["relpath"], b"")
        text = raw.decode("utf-8", errors="ignore")
        parsed_with_yaml = False
        if yaml_available and yaml_mod is not None:
            try:
                loaded = yaml_mod.safe_load(text)
                if isinstance(loaded, dict):
                    parser = "yaml"
                    svc = loaded.get("services")
                    if isinstance(svc, dict):
                        for svc_name, svc_cfg in svc.items():
                            if isinstance(svc_name, str):
                                services.add(svc_name)
                            if isinstance(svc_cfg, dict):
                                svc_ports = svc_cfg.get("ports")
                                if isinstance(svc_ports, list):
                                    for item in svc_ports:
                                        if isinstance(item, (str, int, float)):
                                            ports.add(str(item))
                                svc_volumes = svc_cfg.get("volumes")
                                if isinstance(svc_volumes, list):
                                    for item in svc_volumes:
                                        if isinstance(item, (str, int, float)):
                                            volumes.add(str(item))
                parsed_with_yaml = True
            except Exception:
                parsed_with_yaml = False
        if parsed_with_yaml:
            continue

        in_services = False
        for line in text.splitlines():
            if re.match(r"^\s*services\s*:\s*$", line):
                in_services = True
                continue
            if in_services and re.match(r"^[A-Za-z0-9_.-]+\s*:\s*$", line):
                in_services = False
            if in_services:
                svc_match = re.match(r"^\s{2}([A-Za-z0-9_.-]+)\s*:\s*$", line)
                if svc_match:
                    services.add(svc_match.group(1))
            port_match = re.search(r'"?(\d{2,5}:\d{2,5}(?:/\w+)?)"?', line)
            if port_match:
                ports.add(port_match.group(1))
            vol_match = re.search(r"([./A-Za-z0-9_-]+:[./A-Za-z0-9_-]+)", line)
            if vol_match and "/" in vol_match.group(1):
                volumes.add(vol_match.group(1))

    return {
        "compose_files": [row["relpath"] for row in compose_rows],
        "service_count": len(services),
        "services": sorted(services),
        "ports": sorted(ports),
        "volumes": sorted(volumes),
        "parser": parser,
    }


def scan_promptgen_inputs(
    root: Path,
    run_id: str,
    args: argparse.Namespace,
) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    generated_at = _promptgen_generated_at(run_id)
    include_globs = list(args.promptgen_include_globs or PROMPTGEN_DEFAULT_INCLUDE_GLOBS)
    exclude_globs = list(args.promptgen_exclude_globs or PROMPTGEN_DEFAULT_EXCLUDE_GLOBS)
    selected = _select_promptgen_files(
        root=root,
        include_globs=include_globs,
        exclude_globs=exclude_globs,
        max_files=args.promptgen_max_files,
    )

    rows: List[Dict[str, Any]] = []
    file_bytes_map: Dict[str, bytes] = {}
    for item in selected:
        raw = read_bytes_strict(item["path"])
        file_bytes_map[item["relpath"]] = raw
        raw_excerpt = _read_excerpt_bytes(raw, args.promptgen_excerpt_bytes)
        rows.append(
            {
                "path": item["path"],
                "relpath": item["relpath"],
                "reason": item["reason"],
                "size": len(raw),
                "sha256": sha256_bytes(raw),
                "raw_excerpt": raw_excerpt,
                "raw_excerpt_len": len(raw_excerpt),
            }
        )

    excerpt_policy = _apply_excerpt_pack_policy(rows, args.promptgen_max_bytes)
    excerpt_assigned: Dict[str, bytes] = excerpt_policy["assigned"]

    files_payload: List[Dict[str, Any]] = []
    total_size = 0
    total_excerpt = 0
    excerpt_pack_files: List[Dict[str, Any]] = []
    for row in sorted(rows, key=lambda item: item["relpath"]):
        assigned_excerpt = excerpt_assigned.get(row["relpath"], b"")
        total_size += int(row["size"])
        total_excerpt += len(assigned_excerpt)
        files_payload.append(
            {
                "relpath": row["relpath"],
                "sha256": row["sha256"],
                "size": row["size"],
                "reason": row["reason"],
                "excerpt_sha256": sha256_bytes(assigned_excerpt),
                "excerpt_bytes": len(assigned_excerpt),
            }
        )
        if len(assigned_excerpt) > 0:
            excerpt_pack_files.append(
                {
                    "relpath": row["relpath"],
                    "excerpt_text": assigned_excerpt.decode("utf-8", errors="ignore"),
                    "excerpt_truncated": bool(
                        row["raw_excerpt_len"] > len(assigned_excerpt) or row["size"] > len(assigned_excerpt)
                    ),
                    "excerpt_bytes": len(assigned_excerpt),
                    "excerpt_sha256": sha256_bytes(assigned_excerpt),
                }
            )

    relpaths = [row["relpath"] for row in files_payload]
    extensions = Counter(Path(rel).suffix.lower() for rel in relpaths if Path(rel).suffix)
    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".go": "go",
        ".rs": "rust",
        ".java": "java",
        ".kt": "kotlin",
        ".rb": "ruby",
        ".php": "php",
        ".sh": "shell",
        ".md": "markdown",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".json": "json",
        ".sql": "sql",
    }
    language_counts: Counter = Counter()
    for ext, count in extensions.items():
        language = language_map.get(ext)
        if language:
            language_counts[language] += count

    present = set(relpaths)
    package_managers: Set[str] = set()
    if "package-lock.json" in present:
        package_managers.add("npm")
    if "pnpm-lock.yaml" in present:
        package_managers.add("pnpm")
    if "yarn.lock" in present:
        package_managers.add("yarn")
    if "poetry.lock" in present:
        package_managers.add("poetry")
    if "Pipfile.lock" in present:
        package_managers.add("pipenv")
    if "requirements.txt" in present:
        package_managers.add("pip")

    pyproject_bytes = file_bytes_map.get("pyproject.toml")
    python_detection = _detect_tooling_from_pyproject(pyproject_bytes)
    compose_detection = _parse_compose_services(files_payload, file_bytes_map)

    control_surfaces = {
        "taskx": any(rel == ".taskxroot" or rel.startswith(".taskx/") for rel in relpaths),
        "litellm": any("litellm" in rel.lower() for rel in relpaths),
        "mcp": any("mcp" in rel.lower() for rel in relpaths),
        "conport": any("conport" in rel.lower() for rel in relpaths),
        "github_actions": any(rel.startswith(".github/workflows/") for rel in relpaths),
        "claude": any(rel == ".claude.json" or rel.startswith(".claude/") for rel in relpaths),
    }
    top_paths = sorted({rel.split("/", 1)[0] for rel in relpaths})
    file_hash_lines = "\n".join(f"{row['relpath']}:{row['sha256']}" for row in files_payload).encode("utf-8")
    selected_set_sha256 = sha256_bytes(file_hash_lines)

    promptgen_inputs = {
        "generated_at": generated_at,
        "generated_at_mode": "deterministic_from_run_id",
        "run_id": run_id,
        "repo_root": str(root.resolve()),
        "scanner_version": PROMPTGEN_SCANNER_VERSION,
        "limits": {
            "max_files": int(args.promptgen_max_files),
            "max_bytes": int(args.promptgen_max_bytes),
            "excerpt_bytes": int(args.promptgen_excerpt_bytes),
        },
        "include_globs": include_globs,
        "exclude_globs": exclude_globs,
        "files": files_payload,
        "totals": {
            "selected_files": len(files_payload),
            "total_file_bytes": total_size,
            "total_excerpt_bytes": total_excerpt,
        },
    }

    project_fingerprint = {
        "generated_at": generated_at,
        "generated_at_mode": "deterministic_from_run_id",
        "run_id": run_id,
        "repo_root": str(root.resolve()),
        "scanner_version": PROMPTGEN_SCANNER_VERSION,
        "detected": {
            "languages": dict(sorted(language_counts.items(), key=lambda item: item[0])),
            "package_managers": sorted(package_managers),
            "python": python_detection,
            "containers": compose_detection,
            "control_surfaces": control_surfaces,
            "paths": {
                "top_level": top_paths,
                "selected_files_count": len(files_payload),
            },
            "excerpt_pack": {
                "policy": excerpt_policy["policy"],
                "max_total_bytes": int(args.promptgen_max_bytes),
                "max_per_file_bytes": int(args.promptgen_excerpt_bytes),
                "files_considered": len(files_payload),
                "files_included": len(excerpt_pack_files),
                "dropped_count": int(excerpt_policy["dropped_count"]),
                "reduced_per_file": bool(excerpt_policy["reduced_per_file"]),
                "total_bytes": total_excerpt,
                "files": excerpt_pack_files,
            },
            "hashes": {
                "selected_files_set_sha256": selected_set_sha256,
            },
        },
    }

    return promptgen_inputs, project_fingerprint, {
        "selected_files": len(files_payload),
        "total_excerpt_bytes": total_excerpt,
        "excerpt_policy": excerpt_policy["policy"],
    }


def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def is_text_candidate(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name in TEXT_NAMES


def classify_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".go",
        ".rs",
        ".java",
        ".kt",
        ".php",
        ".rb",
        ".c",
        ".cpp",
        ".h",
        ".hpp",
        ".swift",
        ".sh",
    }:
        return "code"
    if suffix in {".md", ".txt", ".rst"}:
        return "doc"
    return "config"


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def normalized_rel_path(path: Path, repo_root: Optional[Path] = None) -> str:
    resolved = path.resolve()
    root = (repo_root or Path.cwd()).resolve()
    if is_within(resolved, root):
        return str(resolved.relative_to(root)).replace("\\", "/")
    home = Path.home().resolve()
    if is_within(resolved, home):
        rel_home = str(resolved.relative_to(home)).replace("\\", "/")
        return f"~/{rel_home}"
    return str(resolved).replace("\\", "/")


def classify_surface(path_str: str) -> Dict[str, Any]:
    path = Path(path_str).resolve()
    rel = normalized_rel_path(path)
    lower_rel = rel.lower()
    lower_abs = str(path).replace("\\", "/").lower()
    lower = lower_rel if lower_rel.startswith("~/") else lower_abs
    name = path.name.lower()

    def _result(tier: int, subtype: str, reason: str) -> Dict[str, Any]:
        return {
            "tier": tier,
            "subtype": subtype,
            "subtype_rank": MAGIC_SUBTYPE_ORDER.get(subtype, 99),
            "reason": reason,
            "rel_path": rel,
        }

    if (
        "/docs/archive/" in lower
        or "/system_archive/" in lower
        or name.endswith(".zip")
        or name.endswith(".log")
    ):
        return _result(3, "other", "archive_surface")

    if (
        "/.claude/" in lower
        or name in {"agents.md", "claude.md"}
        or name.startswith(".claude.json")
    ):
        return _result(0, "instructions", "instruction_surface")

    if (
        "/.dopemux/" in lower
        or name.startswith("dopemux.toml")
        or name.startswith("mcp-proxy-config")
        or name.startswith("litellm.config")
        or lower.endswith(".taskxroot")
        or lower.endswith("/.taskx-pin")
        or "/.taskx/" in lower
        or lower.startswith("~/.dopemux/")
        or lower.startswith("~/.config/dopemux/")
        or lower.startswith("~/.config/taskx/")
        or lower.startswith("~/.config/litellm/")
        or lower.startswith("~/.config/mcp/")
    ):
        return _result(0, "mcp_router_provider", "config_ladder_surface")

    if (
        name.startswith("compose")
        or name.startswith("compose.yml")
        or "/compose/" in lower
    ):
        return _result(0, "compose_bootstrap", "compose_bootstrap_surface")

    if "/.githooks/" in lower:
        return _result(0, "hooks", "hooks_surface")

    if "/.github/workflows/" in lower:
        return _result(0, "ci", "ci_surface")

    if (
        name in {"makefile", "justfile", ".tmux.conf"}
        or "/scripts/" in lower
        or "/tools/" in lower
        or name.startswith("start-")
        or name.startswith("tmux-")
    ):
        return _result(0, "workflow_launchers", "launcher_surface")

    if (
        "/docs/" in lower
        and (
            "/custom-instructions/" in lower
            or "/prompts/" in lower
            or "/llm/" in lower
            or "agents" in name
            or "claude" in name
        )
    ):
        return _result(1, "instruction_docs", "instruction_docs_surface")

    if (
        "/docs/" in lower
        and (
            "/spec" in lower
            or "/architecture/" in lower
            or "/planes/" in lower
            or "/systems/" in lower
            or "/90-adr/" in lower
            or "/91-rfc/" in lower
        )
    ):
        return _result(1, "other", "active_docs_surface")

    if "/docs/" in lower or name.endswith(".md"):
        return _result(1, "other", "docs_surface")

    return _result(2, "other", "code_or_runtime_surface")


def classify_tier(path_str: str) -> int:
    return int(classify_surface(path_str).get("tier", 2))
def sha256_text(path: Path) -> str:
    content = safe_read(path)
    return hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()


def read_bytes_strict(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except Exception as exc:  # pragma: no cover - exercised via integration paths
        raise RuntimeError(
            f"prompt_unreadable: {path} :: {type(exc).__name__}: {exc}"
        ) from exc


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file_strict(path: Path) -> str:
    return sha256_bytes(read_bytes_strict(path))


def get_git_sha(root: Path) -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
            )
            .strip()
        )
    except Exception:
        return "UNKNOWN"


def collect_manifest_artifacts(dirs: Dict[str, Path]) -> List[Dict[str, Any]]:
    artifacts: List[Dict[str, Any]] = []
    for phase in PHASES:
        phase_dir = dirs.get(phase)
        if not phase_dir:
            continue
        for bucket in ("inputs", "raw", "norm", "qa"):
            bucket_dir = phase_dir / bucket
            if not bucket_dir.exists():
                continue
            for entry in sorted(bucket_dir.iterdir()):
                if not entry.is_file():
                    continue
                try:
                    st = entry.stat()
                    size = st.st_size
                except Exception:
                    size = 0
                artifacts.append(
                    {
                        "name": entry.name,
                        "phase": phase,
                        "phase_dir": PHASE_DIR_NAMES.get(phase, phase),
                        "bucket": bucket,
                        "path": str(entry.resolve()),
                        "size_bytes": size,
                    }
                )
    artifacts.sort(key=lambda row: (row["phase"], row["bucket"], row["name"]))
    return artifacts


def refresh_run_manifest_artifacts(run_root: Path, dirs: Dict[str, Path]) -> None:
    manifest_path = run_root / "RUN_MANIFEST.json"
    payload: Dict[str, Any] = {}
    if manifest_path.exists():
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
    payload["artifacts"] = collect_manifest_artifacts(dirs)
    payload["artifacts_updated_at"] = now_iso()
    write_json(manifest_path, payload)


def resolve_step_tier(phase: str, step_id: str) -> str:
    phase_code = str(phase or "").upper()
    token = str(step_id or "").upper()
    if phase_code in {"R", "X", "T"} or (phase_code == "Z" and token in {"Z1", "Z2"}):
        return "synthesis"
    if phase_code == "Q" or token.endswith("9") or token.endswith("99"):
        return "qa"
    if token.endswith("0"):
        return "bulk"
    return "extract"


def classify_step_type(phase: str, step_id: str) -> str:
    phase_code = str(phase or "").upper()
    token = str(step_id or "").upper()
    if phase_code == "Q" or token.endswith("9"):
        return "qa"
    if phase_code in {"R", "S"}:
        return "synthesis"
    if token.endswith("0") and phase_code in {"A", "H", "D", "C", "E", "W", "B", "G", "X"}:
        return "inventory"
    return "extract"


def _env_is_truthy(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _int_env(name: str, default: int, minimum: int = 1) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return max(minimum, int(default))
    try:
        value = int(raw)
    except Exception as exc:
        raise RuntimeError(f"{name} must be an integer. Got: {raw}") from exc
    return max(minimum, value)


def _parse_provider_model_env(value: str, env_name: str) -> Tuple[str, str, str]:
    raw = str(value or "").strip()
    if not raw:
        raise RuntimeError(
            f"{env_name} is required when {DPMX_ROUTING_ENABLE_ENV}=1 and must be provider/model."
        )
    if raw.count("/") != 1:
        raise RuntimeError(
            f"{env_name} must be provider/model (example: openai/gpt-5-nano). Got: {raw}"
        )
    provider_raw, model_raw = raw.split("/", 1)
    provider = provider_raw.strip().lower()
    model_id = model_raw.strip()
    if provider not in PROVIDER_API_KEY_ENV:
        allowed = ",".join(sorted(PROVIDER_API_KEY_ENV.keys()))
        raise RuntimeError(f"{env_name} provider must be one of {allowed}. Got: {provider_raw}")
    if not model_id:
        raise RuntimeError(f"{env_name} model id is required in provider/model value. Got: {raw}")
    return (provider, model_id, PROVIDER_API_KEY_ENV[provider])


def _resolve_env_step_type_routes() -> Dict[str, Tuple[str, str, str]]:
    routes: Dict[str, Tuple[str, str, str]] = {}
    for step_type, env_name in STEP_TYPE_MODEL_ENV_VARS.items():
        routes[step_type] = _parse_provider_model_env(os.getenv(env_name, ""), env_name)
    return routes


def dpmx_env_routing_payload(validate: bool = False) -> Dict[str, Any]:
    enabled = _env_is_truthy(DPMX_ROUTING_ENABLE_ENV)
    payload: Dict[str, Any] = {
        "enabled": enabled,
        "models": {
            step_type: os.getenv(env_name, "")
            for step_type, env_name in STEP_TYPE_MODEL_ENV_VARS.items()
        },
    }
    if enabled:
        routes = _resolve_env_step_type_routes() if validate else {}
        if routes:
            payload["resolved_routes"] = {
                step_type: {
                    "provider": provider,
                    "model_id": model_id,
                    "api_key_env": api_key_env,
                }
                for step_type, (provider, model_id, api_key_env) in routes.items()
            }
    return payload


def choose_model_for_step(
    phase: str,
    step_id: str,
    cfg: RunnerConfig,
) -> Optional[Tuple[str, str, str, str, str]]:
    del cfg
    if not _env_is_truthy(DPMX_ROUTING_ENABLE_ENV):
        return None
    step_type = classify_step_type(phase, step_id)
    routes = _resolve_env_step_type_routes()
    provider, model_id, api_key_env = routes[step_type]
    return (provider, model_id, api_key_env, step_type, "env_step_type_override")


def resolve_effective_step_route(
    phase: str,
    step_id: str,
    cfg: RunnerConfig,
) -> Dict[str, Any]:
    step_tier = resolve_step_tier(phase, step_id)
    step_type = classify_step_type(phase, step_id)
    chosen = choose_model_for_step(phase, step_id, cfg)
    reason = "policy_ladder_default"
    if chosen is not None:
        provider, model_id, api_key_env, step_type, reason = chosen
        step_ladder: List[Tuple[str, str, str]] = [(provider, model_id, api_key_env)]
    else:
        step_ladder = resolve_step_ladder(cfg.routing_policy, phase, step_id)
        if not step_ladder:
            step_ladder = [("openai", "gpt-5-mini", "OPENAI_API_KEY")]
        provider, model_id, api_key_env = step_ladder[0]
    return {
        "step_tier": step_tier,
        "step_type": step_type,
        "ladder": [tuple(route) for route in step_ladder],
        "provider": provider,
        "model_id": model_id,
        "api_key_env": api_key_env,
        "reason": reason,
    }


def write_phase_routing_log(
    phase_dir: Path,
    *,
    phase: str,
    step_id: str,
    step_type: str,
    provider: str,
    model_id: str,
    reason: str,
) -> None:
    payload_path = phase_dir / "ROUTING_LOG.json"
    rows: List[Dict[str, Any]] = []
    if payload_path.exists():
        try:
            existing = json.loads(payload_path.read_text(encoding="utf-8"))
            if isinstance(existing, dict) and isinstance(existing.get("entries"), list):
                rows = [row for row in existing["entries"] if isinstance(row, dict)]
        except Exception:
            rows = []
    rows = [
        row
        for row in rows
        if not (str(row.get("phase")) == phase and str(row.get("step_id")) == step_id)
    ]
    rows.append(
        {
            "phase": phase,
            "step_id": step_id,
            "step_type": step_type,
            "model": f"{provider}/{model_id}",
            "provider": provider,
            "model_id": model_id,
            "reason": reason,
        }
    )
    rows.sort(
        key=lambda row: (
            str(row.get("phase", "")),
            step_sort_key(str(row.get("step_id", ""))),
            str(row.get("step_type", "")),
            str(row.get("model", "")),
        )
    )
    write_json(payload_path, {"entries": rows})


def _read_json_dict(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _batch_job_sort_key(row: Dict[str, Any]) -> Tuple[str, Tuple[int, str], str, str]:
    return (
        str(row.get("phase_id", "")),
        step_sort_key(str(row.get("step_id", ""))),
        str(row.get("partition_id", "")),
        str(row.get("job_id", "")),
    )


def _read_batch_job_rows(path: Path) -> List[Dict[str, Any]]:
    payload = _read_json_dict(path)
    rows = payload.get("jobs")
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _upsert_batch_job_rows(existing: List[Dict[str, Any]], updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    keyed: Dict[Tuple[str, str, str, str], Dict[str, Any]] = {}
    for row in existing + updates:
        key = (
            str(row.get("phase_id", "")),
            str(row.get("step_id", "")),
            str(row.get("partition_id", "")),
            str(row.get("job_id", "")),
        )
        if not all(key):
            continue
        keyed[key] = dict(row)
    return sorted(keyed.values(), key=_batch_job_sort_key)


def write_batch_job_manifests(
    phase_dir: Path,
    *,
    run_id: str,
    phase_id: str,
    step_id: str,
    jobs: List[Dict[str, Any]],
) -> None:
    if not jobs:
        return
    batch_dir = phase_dir / "batch"
    batch_dir.mkdir(parents=True, exist_ok=True)
    step_jobs = sorted([dict(row) for row in jobs if isinstance(row, dict)], key=_batch_job_sort_key)
    write_json(
        batch_dir / "BATCH_JOB.json",
        {
            "run_id": run_id,
            "phase_id": phase_id,
            "step_id": step_id,
            "updated_at_utc": now_iso(),
            "jobs": step_jobs,
        },
    )
    index_path = batch_dir / "BATCH_JOB_INDEX.json"
    existing_rows = _read_batch_job_rows(index_path)
    merged_rows = _upsert_batch_job_rows(existing_rows, step_jobs)
    write_json(
        index_path,
        {
            "run_id": run_id,
            "phase_id": phase_id,
            "updated_at_utc": now_iso(),
            "jobs": merged_rows,
        },
    )


def _append_webhook_receipt(batch_dir: Path, filename: str, receipt: Dict[str, Any]) -> None:
    path = batch_dir / filename
    payload = _read_json_dict(path)
    rows = payload.get("events")
    existing: List[Dict[str, Any]] = [row for row in rows if isinstance(row, dict)] if isinstance(rows, list) else []
    existing.append(dict(receipt))
    existing.sort(key=lambda row: (str(row.get("event_id", "")), str(row.get("job_id", ""))))
    write_json(path, {"events": existing})


def _webhook_event_id(run_id: str, phase_id: str, step_id: str, job_id: str, state: str) -> str:
    # Use microsecond precision to avoid collisions for multiple events within the same second.
    now_basic = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    token = f"{run_id}|{phase_id}|{step_id}|{job_id}|{state}"
    digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:8]
    return f"evt_{now_basic}_{digest}"


def _redacted_webhook_url(url: str) -> str:
    try:
        parsed = urlparse(url)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, "", ""))
    except Exception:
        return url


def build_webhook_payload(
    *,
    root: Path,
    run_id: str,
    phase_id: str,
    phase_dir: Path,
    step_id: str,
    provider_id: str,
    model_id: str,
    job_id: str,
    state: str,
    detail: str,
    artifacts_written: List[str],
    artifacts_missing: List[str],
) -> Dict[str, Any]:
    event_id = _webhook_event_id(run_id, phase_id, step_id, job_id, state)
    emitted_at = now_iso()
    return {
        "schema": DPMX_WEBHOOK_SCHEMA,
        "event": DPMX_WEBHOOK_EVENT,
        "event_id": event_id,
        "emitted_at_utc": emitted_at,
        "run": {
            "run_id": run_id,
            "run_root": str(root.resolve()),
            "git_sha": get_git_sha(root),
            "runner_sha256": sha256_text(RUNNER_SCRIPT),
        },
        "phase": {
            "phase_id": phase_id,
            "phase_dir": str(phase_dir.resolve()),
            "step_id": step_id,
            "exec_mode": "batch",
        },
        "provider": {
            "provider_id": provider_id,
            "model_id": model_id,
            "job_id": job_id,
        },
        "status": {
            "state": state,
            "detail": detail[:240],
        },
        "artifacts": {
            "written": sorted(set(artifacts_written)),
            "missing": sorted(set(artifacts_missing)),
        },
        "links": {
            "local_phase_dir": str(phase_dir.resolve()),
        },
    }


def send_webhook(
    payload: Dict[str, Any],
    *,
    webhook_url: str,
    webhook_secret: str,
    timeout_seconds: int,
) -> Tuple[bool, int, Optional[str]]:
    body = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-Dopemux-Event": DPMX_WEBHOOK_EVENT,
        "X-Dopemux-Schema": DPMX_WEBHOOK_SCHEMA,
    }
    if webhook_secret:
        signature = hmac.new(webhook_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        headers["X-Dopemux-Signature"] = f"sha256={signature}"
    request = urllib_request.Request(webhook_url, data=body, headers=headers, method="POST")
    try:
        with urllib_request.urlopen(request, timeout=max(1, int(timeout_seconds))) as response:
            status_code = int(getattr(response, "status", 200))
            return (200 <= status_code < 300, status_code, None)
    except urllib_error.HTTPError as exc:
        return (False, int(getattr(exc, "code", 0) or 0), f"http_error:{exc.code}")
    except urllib_error.URLError as exc:
        return (False, 0, f"url_error:{exc.reason}")
    except Exception as exc:  # pragma: no cover - defensive path
        return (False, 0, f"send_error:{type(exc).__name__}")


def maybe_send_batch_webhook(
    *,
    cfg: RunnerConfig,
    root: Path,
    run_id: str,
    phase_id: str,
    phase_dir: Path,
    step_id: str,
    provider_id: str,
    model_id: str,
    job_id: str,
    state: str,
    detail: str,
    artifacts_written: List[str],
    artifacts_missing: List[str],
) -> bool:
    if not cfg.webhook_url.strip():
        return True
    payload = build_webhook_payload(
        root=root,
        run_id=run_id,
        phase_id=phase_id,
        phase_dir=phase_dir,
        step_id=step_id,
        provider_id=provider_id,
        model_id=model_id,
        job_id=job_id,
        state=state,
        detail=detail,
        artifacts_written=artifacts_written,
        artifacts_missing=artifacts_missing,
    )
    ok, status_code, err = send_webhook(
        payload,
        webhook_url=cfg.webhook_url,
        webhook_secret=cfg.webhook_secret,
        timeout_seconds=cfg.webhook_timeout_seconds,
    )
    batch_dir = phase_dir / "batch"
    batch_dir.mkdir(parents=True, exist_ok=True)
    if ok:
        _append_webhook_receipt(
            batch_dir,
            "WEBHOOK_SENT.json",
            {
                "event_id": payload.get("event_id"),
                "job_id": job_id,
                "step_id": step_id,
                "status_code": status_code,
                "url": _redacted_webhook_url(cfg.webhook_url),
                "sent_at_utc": now_iso(),
            },
        )
        return True
    _append_webhook_receipt(
        batch_dir,
        "WEBHOOK_FAIL.json",
        {
            "event_id": payload.get("event_id"),
            "job_id": job_id,
            "step_id": step_id,
            "status_code": status_code,
            "error": err or "unknown",
            "url": _redacted_webhook_url(cfg.webhook_url),
            "failed_at_utc": now_iso(),
        },
    )
    return False


def next_phase_id(current_phase: str) -> Optional[str]:
    current = str(current_phase or "").upper()
    if current not in PHASES:
        return None
    idx = PHASES.index(current)
    if idx + 1 >= len(PHASES):
        return None
    return PHASES[idx + 1]


def _normalize_routing_policy(policy: str) -> str:
    if policy in ROUTING_LADDERS:
        return policy
    return DEFAULT_ROUTING_POLICY


def _phase_default_tier(phase: str) -> str:
    if phase in {"R", "X", "T"}:
        return "synthesis"
    if phase == "Q":
        return "qa"
    if phase in {"A", "H", "D", "W", "B", "G"}:
        return "bulk"
    return "extract"


def _clone_ladders(policy: str) -> Dict[str, List[Tuple[str, str, str]]]:
    selected = ROUTING_LADDERS[_normalize_routing_policy(policy)]
    return {tier: [tuple(route) for route in routes] for tier, routes in selected.items()}


def _refresh_phase_default_model_routing(policy: str) -> Dict[str, Tuple[str, str, str]]:
    ladders = _clone_ladders(policy)
    phase_routes: Dict[str, Tuple[str, str, str]] = {}
    for phase in PHASES:
        tier = _phase_default_tier(phase)
        candidates = ladders.get(tier, [])
        if not candidates:
            candidates = ladders.get("extract", [])
        if not candidates:
            phase_routes[phase] = ("openai", "gpt-5-mini", "OPENAI_API_KEY")
            continue
        phase_routes[phase] = tuple(candidates[0])
    return phase_routes


def apply_model_overrides(
    gemini_model_id: str,
    routing_policy: str = DEFAULT_ROUTING_POLICY,
) -> None:
    global MODEL_ROUTING
    global DEFAULT_MODEL_ROUTING
    global ACTIVE_ROUTING_POLICY
    global ACTIVE_ROUTING_LADDERS
    selected_policy = _normalize_routing_policy(routing_policy)
    ACTIVE_ROUTING_POLICY = selected_policy
    ACTIVE_ROUTING_LADDERS = {
        policy: _clone_ladders(policy)
        for policy in ROUTING_LADDERS.keys()
    }
    gemini_override = str(gemini_model_id or "").strip()
    if gemini_override:
        for policy_name, tiers in ACTIVE_ROUTING_LADDERS.items():
            for tier_name, routes in tiers.items():
                rewritten: List[Tuple[str, str, str]] = []
                for provider, model_id, api_key_env in routes:
                    if provider == "gemini":
                        rewritten.append((provider, gemini_override, api_key_env))
                    else:
                        rewritten.append((provider, model_id, api_key_env))
                ACTIVE_ROUTING_LADDERS[policy_name][tier_name] = rewritten
    MODEL_ROUTING = _refresh_phase_default_model_routing(selected_policy)
    DEFAULT_MODEL_ROUTING = dict(MODEL_ROUTING)


def resolve_step_ladder(
    routing_policy: str,
    phase: str,
    step_id: str,
) -> List[Tuple[str, str, str]]:
    selected_policy = _normalize_routing_policy(routing_policy)
    tiers = ACTIVE_ROUTING_LADDERS.get(selected_policy) or _clone_ladders(selected_policy)
    step_tier = resolve_step_tier(phase, step_id)
    routes = tiers.get(step_tier, [])
    if not routes:
        routes = tiers.get("extract", [])
    return [tuple(route) for route in routes]


def routing_ladders_payload() -> Dict[str, Dict[str, List[Dict[str, str]]]]:
    payload: Dict[str, Dict[str, List[Dict[str, str]]]] = {}
    for policy, tiers in ACTIVE_ROUTING_LADDERS.items():
        payload[policy] = {}
        for tier, routes in tiers.items():
            payload[policy][tier] = [
                {
                    "provider": provider,
                    "model_id": model_id,
                    "api_key_env": api_key_env,
                }
                for provider, model_id, api_key_env in routes
            ]
    return payload


def effective_model_routing_payload() -> Dict[str, Dict[str, str]]:
    payload: Dict[str, Dict[str, str]] = {}
    for phase in PHASES:
        provider, model_id, api_key_env = MODEL_ROUTING.get(phase, ("", "", ""))
        payload[phase] = {
            "provider": provider,
            "model_id": model_id,
            "api_key_env": api_key_env,
        }
    return payload


# Initialize routing state on module load.
apply_model_overrides(DEFAULT_GEMINI_MODEL_ID, DEFAULT_ROUTING_POLICY)


def write_run_manifest(
    root: Path,
    dirs: Dict[str, Path],
    run_id: str,
    args: argparse.Namespace,
    run_context: RunContext,
    phases: List[str],
) -> Dict[str, Any]:
    prompt_report = promptset_fingerprint(phases)
    run_blocked = bool(prompt_report.get("blocked_promptset"))
    routing_policy = str(getattr(args, "routing_policy", DEFAULT_ROUTING_POLICY))
    disable_escalation = bool(getattr(args, "disable_escalation", False))
    escalation_max_hops = int(getattr(args, "escalation_max_hops", 2))
    batch_mode = bool(getattr(args, "batch_mode", False))
    batch_submit_only = bool(getattr(args, "batch_submit_only", False))
    batch_watch = bool(getattr(args, "batch_watch", False))
    batch_provider = str(getattr(args, "batch_provider", "auto"))
    batch_poll_seconds = int(getattr(args, "batch_poll_seconds", 30))
    batch_wait_timeout_seconds = int(getattr(args, "batch_wait_timeout_seconds", 86400))
    batch_max_requests_per_job = int(getattr(args, "batch_max_requests_per_job", 2000))
    manifest = {
        "run_id": run_id,
        "generated_at": now_iso(),
        "repo_root": str(root.resolve()),
        "git_sha": get_git_sha(root),
        "cli": {
            "phase": args.phase if args.phase else args.verify_phase_output,
            "dry_run": args.dry_run,
            "resume": args.resume,
            "max_files_docs": args.max_files_docs,
            "max_files_code": args.max_files_code,
            "max_chars": args.max_chars,
            "max_request_bytes": args.max_request_bytes,
            "file_truncate_chars": args.file_truncate_chars,
            "home_scan_mode": args.home_scan_mode,
            "fail_fast_auth": args.fail_fast_auth,
            "gemini_auth_mode": args.gemini_auth_mode,
            "gemini_model_id": args.gemini_model_id,
            "gemini_transport": args.gemini_transport,
            "openai_transport": args.openai_transport,
            "xai_transport": args.xai_transport,
            "retry_policy": args.retry_policy,
            "retry_max_attempts": args.retry_max_attempts,
            "retry_base_seconds": args.retry_base_seconds,
            "retry_max_seconds": args.retry_max_seconds,
            "phase_auth_fail_threshold": args.phase_auth_fail_threshold,
            "partition_workers": args.partition_workers,
            "routing_policy": routing_policy,
            "disable_escalation": disable_escalation,
            "escalation_max_hops": escalation_max_hops,
            "batch_mode": batch_mode,
            "batch_submit_only": batch_submit_only,
            "batch_watch": batch_watch,
            "batch_provider": batch_provider,
            "batch_poll_seconds": batch_poll_seconds,
            "batch_wait_timeout_seconds": batch_wait_timeout_seconds,
            "batch_max_requests_per_job": batch_max_requests_per_job,
            "debug_phase_inputs": args.debug_phase_inputs,
            "fail_fast_missing_inputs": args.fail_fast_missing_inputs,
            "run_id_override": args.run_id,
            "run_id_source": run_context.source,
            "run_id_resolution_precedence": [
                "explicit(--run-id)",
                f"implicit({V3_LATEST_RUN_FILE.as_posix()})",
                "generated(new timestamp run id)",
            ],
            "no_write_latest": args.no_write_latest,
            "write_latest_even_on_dry_run": args.write_latest_even_on_dry_run,
            "latest_run_id_written": run_context.latest_written,
            "latest_run_id_file": str(run_context.latest_file.resolve()),
            "doctor": args.doctor,
            "doctor_auth": args.doctor_auth,
            "preflight_providers": args.preflight_providers,
            "coverage_report": args.coverage_report,
            "ui": args.ui,
            "quiet": args.quiet,
            "jsonl_events": args.jsonl_events,
            "pretty": args.pretty,
            "print_promptpack": args.print_promptpack,
            "print_run_order": bool(getattr(args, "print_run_order", False)),
            "print_phase_routing": bool(getattr(args, "print_phase_routing", False)),
            "print_phase_prompts": getattr(args, "print_phase_prompts", None),
            "verify_phase_output": args.verify_phase_output,
            "print_config": args.print_config,
            "dpmx_webhook_url": os.getenv(DPMX_WEBHOOK_URL_ENV, "").strip(),
            "dpmx_webhook_secret_set": bool(os.getenv(DPMX_WEBHOOK_SECRET_ENV, "").strip()),
            "dpmx_webhook_timeout_seconds": os.getenv(DPMX_WEBHOOK_TIMEOUT_SECONDS_ENV, "").strip(),
            "dpmx_webhook_required": os.getenv(DPMX_WEBHOOK_REQUIRED_ENV, "").strip(),
            "dpmx_webhook_auto_continue": os.getenv(DPMX_WEBHOOK_AUTO_CONTINUE_ENV, "").strip(),
            "dpmx_live_ok": os.getenv(DPMX_LIVE_OK_ENV, "").strip(),
        },
        "prompt_hash_mode": PROMPT_HASH_MODE,
        "prompt_files": [row["path"] for row in prompt_report["prompt_hashes"]],
        "prompt_missing": prompt_report["prompt_missing"],
        "prompt_unreadable": prompt_report["prompt_unreadable"],
        "prompt_hash_errors": prompt_report["prompt_hash_errors"],
        "prompt_failures": prompt_report.get("prompt_failures", []),
        "prompt_failures_count": int(prompt_report.get("prompt_failures_count", 0)),
        "promptset_sha256": prompt_report["promptset_sha256"],
        "run_status": "BLOCKED" if run_blocked else "OK",
        "phase_status": "blocked_promptset" if run_blocked else "ready",
        "blocked_promptset": run_blocked,
        "routing_policy": routing_policy,
        "routing_policy_version": ROUTING_POLICY_VERSION,
        "routing_step_tiers": {
            phase: {
                spec.step_id: resolve_step_tier(phase, spec.step_id)
                for spec in get_phase_prompts(phase)
            }
            for phase in phases
        },
        "routing_ladders": routing_ladders_payload(),
        "batch_config": {
            "enabled": batch_mode,
            "submit_only": batch_submit_only,
            "watch_mode": batch_watch,
            "provider": batch_provider,
            "poll_seconds": batch_poll_seconds,
            "wait_timeout_seconds": batch_wait_timeout_seconds,
            "max_requests_per_job": batch_max_requests_per_job,
        },
        "effective_model_routing": effective_model_routing_payload(),
    }
    if run_blocked:
        manifest["blocked_reason"] = PROMPTSET_BLOCKED_REASON
        manifest["blocked"] = _blocked_promptset_payload(prompt_report, at="preflight")
    write_json(dirs["root"] / "RUN_MANIFEST.json", manifest)
    refresh_run_manifest_artifacts(dirs["root"], dirs)
    return prompt_report


def write_runner_identity(root: Path, run_root: Path, run_id: str) -> None:
    payload = {
        "run_id": run_id,
        "generated_at": now_iso(),
        "git_sha": get_git_sha(root),
        "runner_script_path": str(RUNNER_SCRIPT.resolve()),
        "runner_sha256": sha256_text(RUNNER_SCRIPT),
        "python_executable": sys.executable,
        "python_version": platform.python_version(),
    }
    write_json(run_root / "RUNNER_IDENTITY.json", payload)


def update_run_manifest_probe(
    run_root: Path,
    phase: str,
    step_id: str,
    probe_payload: Dict[str, Any],
) -> None:
    manifest_path = run_root / "RUN_MANIFEST.json"
    payload: Dict[str, Any] = {}
    if manifest_path.exists():
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
    probes = payload.setdefault("auth_probes", {})
    phase_probes = probes.setdefault(phase, {})
    phase_probes[step_id] = probe_payload
    write_json(manifest_path, payload)


def update_run_manifest_promptset_block(
    run_root: Path,
    phase: str,
    prompt_report: Dict[str, Any],
) -> None:
    manifest_path = run_root / "RUN_MANIFEST.json"
    payload: Dict[str, Any] = {}
    if manifest_path.exists():
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception:
            payload = {}
    payload["run_status"] = "BLOCKED"
    payload["phase_status"] = "blocked_promptset"
    payload["blocked_promptset"] = True
    payload["blocked_reason"] = PROMPTSET_BLOCKED_REASON
    payload["blocked_phase"] = phase
    payload["blocked_prompts_missing"] = prompt_report.get("prompt_missing", [])
    payload["blocked_prompts_unreadable"] = prompt_report.get("prompt_unreadable", [])
    payload["blocked_prompt_hash_errors"] = prompt_report.get("prompt_hash_errors", [])
    payload["prompt_failures"] = prompt_report.get("prompt_failures", [])
    payload["prompt_failures_count"] = int(prompt_report.get("prompt_failures_count", 0))
    payload["blocked"] = _blocked_promptset_payload(prompt_report, at="phase_execution")
    payload["prompt_hash_mode"] = PROMPT_HASH_MODE
    payload["promptset_sha256"] = None
    payload["updated_at"] = now_iso()
    write_json(manifest_path, payload)


def write_promptset_blocked_marker(
    phase: str,
    phase_dir: Path,
    prompt_report: Dict[str, Any],
) -> None:
    payload = {
        "generated_at": now_iso(),
        "phase": phase,
        "status": "blocked_promptset",
        "blocked_reason": PROMPTSET_BLOCKED_REASON,
        "prompt_hash_mode": PROMPT_HASH_MODE,
        "promptset_sha256": None,
        "prompt_hashes": prompt_report.get("prompt_hashes", []),
        "prompt_missing": prompt_report.get("prompt_missing", []),
        "prompt_unreadable": prompt_report.get("prompt_unreadable", []),
        "prompt_hash_errors": prompt_report.get("prompt_hash_errors", []),
        "prompt_failures": prompt_report.get("prompt_failures", []),
        "missing_prompts_count": int(prompt_report.get("missing_prompts_count", 0)),
        "unreadable_prompts_count": int(prompt_report.get("unreadable_prompts_count", 0)),
        "prompt_failures_count": int(prompt_report.get("prompt_failures_count", 0)),
    }
    write_json(phase_dir / "qa" / f"PHASE_{phase}_BLOCKED_PROMPTSET.json", payload)


# --- Collector Logic ---

class Collector:
    def __init__(self, root: Path, excludes: List[str]):
        self.root = root.resolve()
        self.excludes = excludes

    def _is_excluded(self, path: Path) -> bool:
        name = path.name
        rel = name
        if is_within(path, self.root):
            rel = str(path.resolve().relative_to(self.root))
        for pat in self.excludes:
            if fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel, pat):
                return True
        return False

    def collect(self, subdirs: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        roots = [self.root / d for d in subdirs] if subdirs else [self.root]
        items: List[Dict[str, Any]] = []

        for root in roots:
            if not root.exists():
                logger.warning("Root not found: %s", root)
                continue

            if root.is_file():
                if not self._is_excluded(root) and is_text_candidate(root):
                    items.append(self._make_item(root))
                continue

            for walk_root, dirs, files in os.walk(root):
                base = Path(walk_root)
                dirs[:] = [d for d in dirs if not self._is_excluded(base / d)]
                for filename in files:
                    path = base / filename
                    if self._is_excluded(path):
                        continue
                    if filename.startswith(".") and filename not in {
                        ".env",
                        ".gitignore",
                        ".claude.json",
                        ".taskx-pin",
                        ".tmux.conf",
                    }:
                        continue
                    if not is_text_candidate(path):
                        continue
                    items.append(self._make_item(path))

        items.sort(key=lambda item: item["path"])
        return items

    @staticmethod
    def _make_item(path: Path) -> Dict[str, Any]:
        try:
            st = path.stat()
            size = st.st_size
            mtime = st.st_mtime
        except Exception:
            size = 0
            mtime = 0.0
        return {"path": str(path.resolve()), "size": size, "mtime": mtime, "name": path.name}


def extract_output_artifacts(prompt_text: str, step_id: str) -> Tuple[str, ...]:
    lines = prompt_text.splitlines()
    artifacts: List[str] = []
    idx = 0

    while idx < len(lines):
        stripped = lines[idx].strip()
        if not stripped:
            idx += 1
            continue

        if OUTPUT_SECTION_START_RE.match(stripped):
            artifacts.extend(OUTPUT_FILENAME_RE.findall(stripped))
            idx += 1

            while idx < len(lines):
                candidate = lines[idx].strip()
                lower = candidate.lower()

                if not candidate:
                    next_idx = idx + 1
                    if next_idx < len(lines) and lines[next_idx].strip().startswith(("-", "*", "•")):
                        idx += 1
                        continue
                    break

                if any(lower.startswith(prefix) for prefix in OUTPUT_SECTION_STOP_PREFIXES):
                    break

                if (
                    candidate.startswith(("-", "*", "•"))
                    or OUTPUT_FILENAME_RE.search(candidate)
                    or lines[idx].startswith((" ", "\t"))
                ):
                    artifacts.extend(OUTPUT_FILENAME_RE.findall(candidate))
                    idx += 1
                    continue

                break
            continue

        idx += 1

    filtered: List[str] = []
    seen = set()
    for artifact in artifacts:
        if "_" not in artifact:
            continue
        if re.match(r"^[A-Z][0-9]+\.partX\.json$", artifact):
            continue
        if artifact in seen:
            continue
        seen.add(artifact)
        filtered.append(artifact)

    if not filtered:
        fallback = DEFAULT_OUTPUT_BY_STEP.get(step_id)
        if fallback:
            return fallback
    return tuple(filtered)


def _resolve_prompt_root() -> Path:
    return prompt_root()


def get_phase_prompts(phase: str) -> List[PromptSpec]:
    root = prompt_root()
    prompts = sorted(root.glob(f"PROMPT_{phase}*_*.md"))
    grouped: Dict[str, List[Path]] = {}

    for prompt_path in prompts:
        match = re.match(r"PROMPT_([A-Z][0-9]+)_", prompt_path.name)
        if not match:
            continue
        step_id = match.group(1)
        grouped.setdefault(step_id, []).append(prompt_path)

    specs: List[PromptSpec] = []
    for step_id in sorted(grouped.keys(), key=step_sort_key):
        candidates = sorted(grouped[step_id], key=lambda p: p.name)
        if len(candidates) > 1:
            raise RuntimeError(
                f"Duplicate prompts for {step_id}: {[p.name for p in candidates]}. "
                "Resolve duplicates before running the pipeline."
            )

        prompt_path = candidates[0]
        prompt_text = safe_read(prompt_path)
        output_artifacts = extract_output_artifacts(prompt_text, step_id)
        if not output_artifacts:
            logger.warning(
                "Prompt %s (%s) does not declare explicit output artifacts. Falling back to %s.json.",
                prompt_path.name,
                step_id,
                step_id,
            )
            output_artifacts = (f"{step_id}.json",)

        specs.append(
            PromptSpec(
                step_id=step_id,
                prompt_path=prompt_path,
                output_artifacts=tuple(output_artifacts),
            )
        )

    return specs


def _missing_prompt_glob(step_id: str) -> str:
    return str((prompt_root() / f"PROMPT_{step_id}_*.md").resolve())


def _truncate_exception_message(message: str, limit: int = 500) -> str:
    return message[:limit]


def _prompt_failure_entry(
    *,
    kind: str,
    prompt_id: str,
    path: Path,
    exception_type: str,
    exception_message: str,
) -> Dict[str, str]:
    return {
        "kind": kind,
        "prompt_id": prompt_id,
        "path": str(path.resolve()),
        "exception_type": exception_type,
        "exception_message": _truncate_exception_message(exception_message),
    }


def _blocked_promptset_payload(prompt_report: Dict[str, Any], at: str) -> Dict[str, Any]:
    return {
        "reason": PROMPTSET_BLOCKED_REASON,
        "at": at,
        "promptset": {
            "status": "blocked",
            "failures": prompt_report.get("prompt_failures", []),
        },
    }


def _resume_blocked_payload(prompt_report: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "reason": PROMPTSET_BLOCKED_REASON,
        "promptset_hash": None,
        "promptset_status": "blocked",
        "prompt_failures": prompt_report.get("prompt_failures", []),
    }


def _prompt_hash_report_for_phase(phase: str, specs: List[PromptSpec]) -> Dict[str, Any]:
    prompt_hashes: List[Dict[str, str]] = []
    prompt_missing: List[str] = []
    prompt_unreadable: List[Dict[str, str]] = []
    prompt_hash_errors: List[str] = []
    prompt_failures: List[Dict[str, str]] = []

    expected_steps = REQUIRED_PROMPT_STEP_IDS.get(phase, set())
    observed_steps = {spec.step_id for spec in specs}
    for step_id in sorted(expected_steps - observed_steps):
        missing_pattern = _missing_prompt_glob(step_id)
        prompt_missing.append(missing_pattern)
        prompt_hash_errors.append(f"prompt_missing: {missing_pattern}")
        prompt_failures.append(
            _prompt_failure_entry(
                kind="MISSING_PROMPT",
                prompt_id=step_id,
                path=Path(missing_pattern),
                exception_type="FileNotFoundError",
                exception_message=f"No prompt file found for required step '{step_id}'.",
            )
        )

    for spec in sorted(specs, key=lambda row: (row.step_id, str(row.prompt_path))):
        path = spec.prompt_path.resolve()
        if not path.exists():
            prompt_missing.append(str(path))
            prompt_hash_errors.append(f"prompt_missing: {path}")
            prompt_failures.append(
                _prompt_failure_entry(
                    kind="MISSING_PROMPT",
                    prompt_id=spec.step_id,
                    path=path,
                    exception_type="FileNotFoundError",
                    exception_message=f"Prompt file does not exist: {path}",
                )
            )
            continue
        try:
            digest = sha256_bytes(path.read_bytes())
        except Exception as exc:
            error_message = _truncate_exception_message(str(exc))
            prompt_unreadable.append(
                {
                    "prompt_id": spec.step_id,
                    "path": str(path),
                    "error": f"{type(exc).__name__}: {error_message}",
                }
            )
            prompt_hash_errors.append(
                f"prompt_unreadable: {path} :: {type(exc).__name__}: {error_message}"
            )
            prompt_failures.append(
                _prompt_failure_entry(
                    kind="UNREADABLE_PROMPT",
                    prompt_id=spec.step_id,
                    path=path,
                    exception_type=type(exc).__name__,
                    exception_message=error_message,
                )
            )
            continue
        prompt_hashes.append({"prompt_id": spec.step_id, "path": str(path), "sha256": digest})

    prompt_failures = sorted(
        prompt_failures,
        key=lambda row: (row["prompt_id"], row["path"], row["kind"]),
    )
    blocked = bool(prompt_failures)
    promptset_sha256: Optional[str] = None
    if not blocked:
        normalized = json.dumps(
            sorted(prompt_hashes, key=lambda row: row["path"]),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        promptset_sha256 = sha256_bytes(normalized)

    return {
        "phase": phase,
        "prompt_hash_mode": PROMPT_HASH_MODE,
        "promptset_sha256": promptset_sha256,
        "prompt_hashes": sorted(prompt_hashes, key=lambda row: row["path"]),
        "prompt_missing": sorted(set(prompt_missing)),
        "prompt_unreadable": sorted(prompt_unreadable, key=lambda row: row["path"]),
        "prompt_hash_errors": prompt_hash_errors,
        "prompt_failures": prompt_failures,
        "blocked_promptset": blocked,
        "missing_prompts_count": len(set(prompt_missing)),
        "unreadable_prompts_count": len(prompt_unreadable),
        "prompt_failures_count": len(prompt_failures),
    }


def promptset_fingerprint(phases: Iterable[str]) -> Dict[str, Any]:
    active_phases = sorted(set(phases))
    prompt_hashes: List[Dict[str, str]] = []
    prompt_missing: List[str] = []
    prompt_unreadable: List[Dict[str, str]] = []
    prompt_hash_errors: List[str] = []
    prompt_failures: List[Dict[str, str]] = []

    for phase in active_phases:
        report = _prompt_hash_report_for_phase(phase, get_phase_prompts(phase))
        prompt_hashes.extend(report["prompt_hashes"])
        prompt_missing.extend(report["prompt_missing"])
        prompt_unreadable.extend(report["prompt_unreadable"])
        prompt_hash_errors.extend(report["prompt_hash_errors"])
        prompt_failures.extend(report.get("prompt_failures", []))

    prompt_failures = sorted(
        prompt_failures,
        key=lambda row: (row["prompt_id"], row["path"], row["kind"]),
    )
    blocked = bool(prompt_failures)
    promptset_sha256: Optional[str] = None
    if not blocked:
        normalized = json.dumps(
            sorted(prompt_hashes, key=lambda row: row["path"]),
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        promptset_sha256 = sha256_bytes(normalized)

    return {
        "active_phases": active_phases,
        "prompt_hash_mode": PROMPT_HASH_MODE,
        "promptset_sha256": promptset_sha256,
        "prompt_hashes": sorted(prompt_hashes, key=lambda row: row["path"]),
        "prompt_missing": sorted(set(prompt_missing)),
        "prompt_unreadable": sorted(prompt_unreadable, key=lambda row: row["path"]),
        "prompt_hash_errors": prompt_hash_errors,
        "prompt_failures": prompt_failures,
        "blocked_promptset": blocked,
        "missing_prompts_count": len(set(prompt_missing)),
        "unreadable_prompts_count": len(prompt_unreadable),
        "prompt_failures_count": len(prompt_failures),
    }


def write_run_routing_fingerprint(
    run_root: Path,
    run_id: str,
    cfg: RunnerConfig,
    phases: List[str],
) -> None:
    phase_entries: Dict[str, List[Dict[str, Any]]] = {}
    step_tier_map: Dict[str, Dict[str, str]] = {}
    for phase in phases:
        prompts = get_phase_prompts(phase)
        entries: List[Dict[str, Any]] = []
        step_tier_map[phase] = {}
        for prompt in prompts:
            tier = resolve_step_tier(phase, prompt.step_id)
            step_tier_map[phase][prompt.step_id] = tier
            ladder = resolve_step_ladder(cfg.routing_policy, phase, prompt.step_id)
            provider, model_id, api_key_env = ladder[0] if ladder else ("openai", "gpt-5-mini", "OPENAI_API_KEY")
            endpoint_base = llm_base_url(provider, cfg)
            default_sequence = (
                _gemini_auth_mode_sequence(cfg.gemini_auth_mode, endpoint_base)
                if provider == "gemini"
                else ["sdk_bearer"]
            )
            endpoint_url = transport_endpoint_url(provider, model_id, cfg, "REDACTED", default_sequence[0])
            entries.append(
                {
                    "step_id": prompt.step_id,
                    "prompt_file": prompt.prompt_path.name,
                    "declared_outputs": list(prompt.output_artifacts),
                    "step_tier": tier,
                    "provider": provider,
                    "model_id": model_id,
                    "api_key_env": api_key_env,
                    "ladder": [
                        {
                            "provider": route_provider,
                            "model_id": route_model,
                            "api_key_env": route_key_env,
                        }
                        for route_provider, route_model, route_key_env in ladder
                    ],
                    "transport": transport_for_provider(provider, cfg),
                    "endpoint_base_url": endpoint_base,
                    "endpoint_effective": endpoint_effective(endpoint_url),
                    "gemini_endpoint_family": "openai_compat"
                    if provider == "gemini" and _is_gemini_openai_compat_endpoint(endpoint_base)
                    else ("native" if provider == "gemini" else None),
                    "default_auth_sequence": default_sequence,
                    "routing_signature": routing_signature(
                        phase,
                        prompt.step_id,
                        provider,
                        model_id,
                        endpoint_base,
                        default_sequence[0] if provider == "gemini" else None,
                    ),
                }
            )
        phase_entries[phase] = entries

    payload = {
        "run_id": run_id,
        "created_at": now_iso(),
        "config": {
            "routing_policy": cfg.routing_policy,
            "routing_policy_version": ROUTING_POLICY_VERSION,
            "gemini_auth_mode_requested": cfg.gemini_auth_mode,
            "gemini_model_id_requested": next(
                (
                    model_id
                    for provider, model_id, _ in MODEL_ROUTING.values()
                    if provider == "gemini"
                ),
                DEFAULT_GEMINI_MODEL_ID,
            ),
            "gemini_transport": cfg.gemini_transport,
            "openai_transport": cfg.openai_transport,
            "xai_transport": cfg.xai_transport,
            "fail_fast_auth": cfg.fail_fast_auth,
            "debug_phase_inputs": cfg.debug_phase_inputs,
            "fail_fast_missing_inputs": cfg.fail_fast_missing_inputs,
            "disable_escalation": cfg.disable_escalation,
            "escalation_max_hops": cfg.escalation_max_hops,
            "batch_mode": cfg.batch_mode,
            "batch_provider": cfg.batch_provider,
            "batch_poll_seconds": cfg.batch_poll_seconds,
            "batch_wait_timeout_seconds": cfg.batch_wait_timeout_seconds,
            "batch_max_requests_per_job": cfg.batch_max_requests_per_job,
        },
        "selected_policy": cfg.routing_policy,
        "step_tier_map": step_tier_map,
        "routing_ladders": routing_ladders_payload(),
        "batch_settings": {
            "enabled": cfg.batch_mode,
            "provider": cfg.batch_provider,
            "poll_seconds": cfg.batch_poll_seconds,
            "wait_timeout_seconds": cfg.batch_wait_timeout_seconds,
            "max_requests_per_job": cfg.batch_max_requests_per_job,
        },
        "effective_model_routing": effective_model_routing_payload(),
        "phases": phase_entries,
    }
    write_json(run_root / "RUN_ROUTING_FINGERPRINT.json", payload)


def resolve_phase_list(phase_arg: Optional[str]) -> List[str]:
    if not phase_arg:
        return []
    if phase_arg == "ALL":
        return PHASES
    return [phase_arg]


def collect_prompt_index() -> Tuple[Dict[str, Dict[str, List[Path]]], Dict[str, List[str]]]:
    step_map: Dict[str, List[Path]] = defaultdict(list)
    prompt_paths = sorted(prompt_root().glob("PROMPT_*.md"))
    for prompt_path in prompt_paths:
        match = re.match(r"PROMPT_([A-Z][0-9]+)_", prompt_path.name)
        if not match:
            continue
        step_id = match.group(1)
        step_map[step_id].append(prompt_path)

    phase_map: Dict[str, Dict[str, List[Path]]] = defaultdict(dict)
    duplicates: Dict[str, List[str]] = {}
    for step_id in sorted(step_map.keys(), key=step_sort_key):
        paths = sorted(step_map[step_id], key=lambda p: p.name)
        phase = step_id[0]
        phase_map.setdefault(phase, {})
        phase_map[phase][step_id] = paths
        if len(paths) > 1:
            duplicates[step_id] = [p.name for p in paths]

    return phase_map, duplicates


# --- Home Safe Mode ---

def home_safe_filter(items: List[Dict[str, Any]], home_root: Path) -> List[Dict[str, Any]]:
    allow_roots = [(home_root / rel).resolve() for rel in HOME_SAFE_ROOTS]
    filtered: List[Dict[str, Any]] = []
    skipped_counts = Counter()

    for item in items:
        path = Path(item["path"]).resolve()
        if not any(is_within(path, allow_root) or path == allow_root for allow_root in allow_roots):
            skipped_counts["outside_allow_roots"] += 1
            continue

        suffix = path.suffix.lower()
        if suffix not in HOME_SAFE_ALLOW_SUFFIXES:
            skipped_counts["disallowed_extension"] += 1
            continue

        lower_path = str(path).lower()
        lower_name = path.name.lower()
        if any(
            fnmatch.fnmatch(lower_name, pat) or fnmatch.fnmatch(lower_path, pat)
            for pat in HOME_SAFE_DENY_GLOBS
        ):
            skipped_counts["denylist_match"] += 1
            continue

        filtered.append(item)

    filtered.sort(key=lambda item: item["path"])
    logger.info(
        "Home SAFE filter kept %s/%s files (skipped: %s)",
        len(filtered),
        len(items),
        dict(skipped_counts),
    )
    return filtered


def run_doctor_checks(root: Path, dirs: Dict[str, Path], run_id: str, phase_arg: Optional[str]) -> bool:
    phase_list = resolve_phase_list(phase_arg)
    if not phase_list:
        logger.error("Doctor mode requires --phase to specify which pipelines to check.")
        return False

    prompt_index, duplicates = collect_prompt_index()
    errors: List[str] = []
    warnings: List[str] = []

    if duplicates:
        for step_id, names in duplicates.items():
            errors.append(f"Duplicate prompt step {step_id}: {names}")

    for phase in phase_list:
        prompts = prompt_index.get(phase, {})
        if not prompts:
            errors.append(
                f"No prompts found for phase {phase} ({prompt_root()}/PROMPT_{phase}*)."
            )

    run_root = dirs["root"]
    if not run_root.exists():
        errors.append(f"Run root missing: {run_root}")
    for phase in phase_list:
        phase_dir = dirs.get(phase)
        if not phase_dir or not phase_dir.exists():
            warnings.append(
                f"Phase directory missing (can be created by runner): {phase} -> {run_root / PHASE_DIR_NAMES.get(phase, phase)}"
            )

    print("DOCTOR PRECHECK REPORT")
    status = "PASS" if not errors else "FAIL"
    print(f"DOCTOR STATUS: {status}")
    if warnings:
        print("  WARNINGS:")
        for warning in warnings:
            print(f"    {warning}")
    if errors:
        print("  ERRORS:")
        for error in errors:
            print(f"    {error}")
        return False

    print(f"  Run ID: {run_id}")
    print(f"  Phases scanned: {', '.join(phase_list)}")
    print("  Prompt steps are unique and present for selected phases.")
    return True


def _required_artifact_groups_for_phase(phase: str) -> List[Tuple[str, ...]]:
    return R_REQUIRED_ARTIFACT_GROUPS.get(phase, [])


def _match_required_group(norm_dir: Path, group: Tuple[str, ...]) -> Tuple[bool, Optional[str]]:
    for pattern in group:
        for matched in sorted(norm_dir.glob(pattern)):
            if matched.is_file():
                return True, matched.name
    return False, None


def get_required_artifact_status(dirs: Dict[str, Path], phases: List[str]) -> Dict[str, Any]:
    per_phase: Dict[str, Any] = {}
    total_groups = 0
    present_groups = 0
    for phase in phases:
        groups = _required_artifact_groups_for_phase(phase)
        norm_dir = dirs[phase] / "norm"
        phase_rows: List[Dict[str, Any]] = []
        for group in groups:
            total_groups += 1
            ok = False
            matched = None
            if norm_dir.exists():
                ok, matched = _match_required_group(norm_dir, group)
            if ok:
                present_groups += 1
            phase_rows.append(
                {
                    "group": list(group),
                    "present": ok,
                    "matched_file": matched,
                }
            )
        per_phase[phase] = {
            "norm_dir": str(norm_dir),
            "required_groups_total": len(groups),
            "required_groups_present": sum(1 for row in phase_rows if row["present"]),
            "required_groups": phase_rows,
        }
    pct = (100.0 * present_groups / total_groups) if total_groups else 100.0
    return {
        "total_required_groups": total_groups,
        "present_required_groups": present_groups,
        "required_groups_present_pct": round(pct, 2),
        "phases": per_phase,
    }


def collect_provider_routes(
    phases: List[str],
    routing_policy: str,
) -> Dict[str, Dict[str, str]]:
    routes: Dict[str, Dict[str, str]] = {}
    for phase in phases:
        for prompt in get_phase_prompts(phase):
            ladder = resolve_step_ladder(routing_policy, phase, prompt.step_id)
            for provider, model_id, api_key_env in ladder:
                key = f"{provider}:{model_id}:{api_key_env}"
                if key in routes:
                    continue
                routes[key] = {
                    "provider": provider,
                    "model_id": model_id,
                    "api_key_env": api_key_env,
                }
    return routes


def run_provider_doctor_probe(provider: str, model_id: str, api_key_env: str, cfg: RunnerConfig) -> Dict[str, Any]:
    endpoint_base = llm_base_url(provider, cfg)
    transport = transport_for_provider(provider, cfg)
    api_key, resolved_api_key_env = resolve_api_key(provider, api_key_env)
    effective_mode = None
    auth_sequence = None
    if provider == "gemini":
        auth_sequence = _gemini_auth_mode_sequence(cfg.gemini_auth_mode, endpoint_base)
        effective_mode = auth_sequence[0]
    endpoint_url = transport_endpoint_url(provider, model_id, cfg, api_key, effective_mode)
    result = call_llm(
        provider=provider,
        model_id=model_id,
        api_key_env=api_key_env,
        system_prompt="Return exactly OK.",
        user_content="Return the single token OK.",
        cfg=cfg,
    )
    meta = result.get("meta", {})
    return {
        "provider": provider,
        "model_id": model_id,
        "api_key_env_name": api_key_env,
        "api_key_env_resolved": resolved_api_key_env,
        "api_key_present": bool(api_key),
        "transport": transport,
        "endpoint_effective": meta.get("endpoint_effective") or _sanitize_url(endpoint_url),
        "status_code": meta.get("status_code"),
        "failure_type": meta.get("failure_type"),
        "provider_error_reason": meta.get("provider_error_reason"),
        "provider_signature": meta.get("provider_signature")
        or provider_signature(provider, model_id, _sanitize_url(endpoint_url), effective_mode),
        "gemini_auth_mode_requested": cfg.gemini_auth_mode if provider == "gemini" else None,
        "gemini_auth_mode_effective": meta.get("gemini_auth_mode_effective") if provider == "gemini" else None,
        "gemini_auth_attempt_sequence": auth_sequence if provider == "gemini" else None,
    }


def run_provider_preflight(root: Path, run_id: str, cfg: RunnerConfig, phases: List[str]) -> Tuple[bool, Dict[str, Any]]:
    provider_routes = collect_provider_routes(phases=phases, routing_policy=cfg.routing_policy)
    provider_probes = [
        run_provider_doctor_probe(
            provider=route["provider"],
            model_id=route["model_id"],
            api_key_env=route["api_key_env"],
            cfg=cfg,
        )
        for route in provider_routes.values()
    ]
    batch_capability: Dict[str, Any] = {
        "enabled": bool(cfg.batch_mode),
        "provider": cfg.batch_provider,
        "status": "SKIPPED",
        "checks": [],
    }
    if cfg.batch_mode:
        checks: List[Dict[str, Any]] = []
        providers_to_check: Set[str] = set()
        if cfg.batch_provider == "auto":
            providers_to_check = {str(route["provider"]) for route in provider_routes.values()}
        else:
            providers_to_check = {cfg.batch_provider}
        for provider in sorted(providers_to_check):
            api_key_env = "OPENAI_API_KEY"
            if provider == "gemini":
                api_key_env = "GEMINI_API_KEY"
            elif provider == "xai":
                api_key_env = "XAI_API_KEY"
            api_key, _ = resolve_api_key(provider, api_key_env)
            checks.append(
                {
                    "provider": provider,
                    "api_key_env": api_key_env,
                    "api_key_present": bool(api_key),
                }
            )
        batch_capability = {
            "enabled": True,
            "provider": cfg.batch_provider,
            "status": "PASS" if all(row["api_key_present"] for row in checks) else "FAIL",
            "checks": checks,
        }
    failures = [
        probe for probe in provider_probes
        if probe.get("status_code") != 200 or is_auth_classified_failure(probe.get("failure_type"))
    ]
    payload = {
        "generated_at": now_iso(),
        "run_id": run_id,
        "status": "PASS" if not failures else "FAIL",
        "routes": provider_routes,
        "probes": provider_probes,
        "failed_providers": [probe.get("provider") for probe in failures],
        "routing_policy": cfg.routing_policy,
        "routing_policy_version": ROUTING_POLICY_VERSION,
        "batch_capability": batch_capability,
    }
    doctor_dir = root / V3_DOCTOR_ROOT
    doctor_dir.mkdir(parents=True, exist_ok=True)
    write_json(doctor_dir / "PROVIDER_PREFLIGHT.json", payload)
    return (not failures), payload


def _normalize_gemini_model(row: Dict[str, Any]) -> Dict[str, Any]:
    methods = row.get("supportedGenerationMethods")
    methods_list = sorted(set(str(item) for item in methods)) if isinstance(methods, list) else []
    return {
        "model_id": str(row.get("name") or ""),
        "display_name": row.get("displayName"),
        "input_token_limit": row.get("inputTokenLimit"),
        "output_token_limit": row.get("outputTokenLimit"),
        "supported_generation_methods": methods_list,
        "lifecycle": row.get("lifecycle"),
    }


def run_gemini_list_models(root: Path, run_id: str, dirs: Dict[str, Path]) -> int:
    del root
    out_dir = dirs["root"] / "00_inputs"
    output_path = out_dir / GEMINI_MODELS_FILENAME
    failed_path = out_dir / GEMINI_MODELS_FAILED_FILENAME
    started = time.time()

    api_key, resolved_api_key_env = resolve_api_key("gemini", "GEMINI_API_KEY")
    if not api_key:
        payload = {
            "generated_at": now_iso(),
            "run_id": run_id,
            "status": "failed",
            "stage": "gemini_list_models",
            "error_type": "auth_missing",
            "error": "Missing API key env var: GEMINI_API_KEY",
            "api_key_env_name": "GEMINI_API_KEY",
            "api_key_env_resolved": resolved_api_key_env,
            "endpoint": GEMINI_MODELS_ENDPOINT,
        }
        write_json(failed_path, payload)
        logger.error("Gemini models listing failed: missing GEMINI_API_KEY.")
        return 1

    page_token = ""
    raw_pages: List[bytes] = []
    raw_page_hashes: List[str] = []
    raw_models: List[Dict[str, Any]] = []
    page_count = 0

    try:
        while True:
            params: Dict[str, str] = {"key": api_key}
            if page_token:
                params["pageToken"] = page_token
            response = requests.get(GEMINI_MODELS_ENDPOINT, params=params, timeout=60)
            response.raise_for_status()
            body = response.content
            parsed = response.json()
            if not isinstance(parsed, dict):
                raise RuntimeError("Gemini models endpoint returned non-object JSON.")
            models = parsed.get("models")
            if isinstance(models, list):
                for model in models:
                    if isinstance(model, dict):
                        raw_models.append(model)
            raw_pages.append(body)
            raw_page_hashes.append(sha256_bytes(body))
            page_count += 1
            next_token = parsed.get("nextPageToken")
            if not isinstance(next_token, str) or not next_token:
                break
            page_token = next_token

        raw_response_bytes = b"".join(raw_pages)
        raw_response_sha = sha256_bytes(raw_response_bytes)
        normalized = [_normalize_gemini_model(row) for row in raw_models]
        generation_capable = [
            row for row in normalized
            if "generateContent" in row.get("supported_generation_methods", [])
            and row.get("model_id")
        ]
        generation_capable.sort(key=lambda row: str(row.get("model_id")))
        payload = {
            "version": GEMINI_MODELS_SCHEMA_VERSION,
            "generated_at": _promptgen_generated_at(run_id),
            "generated_at_mode": "deterministic_from_run_id",
            "run_id": run_id,
            "provider": "gemini",
            "filters": {
                "generation_capable_only": True,
            },
            "provenance": {
                "endpoint": GEMINI_MODELS_ENDPOINT,
                "api_version": "v1beta",
                "raw_response_sha256": raw_response_sha,
                "raw_models_count": len(raw_models),
                "pages_fetched": page_count,
                "raw_page_sha256": raw_page_hashes,
            },
            "models": generation_capable,
        }

        previous_payload: Optional[Dict[str, Any]] = None
        if output_path.exists():
            try:
                previous_payload = json.loads(output_path.read_text(encoding="utf-8"))
            except Exception:
                previous_payload = None

        digest = _write_json_with_sha256(output_path, payload)
        if failed_path.exists():
            failed_path.unlink()

        prev_raw_sha = (
            ((previous_payload or {}).get("provenance") or {}).get("raw_response_sha256")
            if isinstance(previous_payload, dict)
            else None
        )
        if isinstance(prev_raw_sha, str) and prev_raw_sha and prev_raw_sha != raw_response_sha:
            old_ids = {
                str(row.get("model_id"))
                for row in ((previous_payload or {}).get("models") or [])
                if isinstance(row, dict) and row.get("model_id")
            }
            new_ids = {str(row.get("model_id")) for row in generation_capable if row.get("model_id")}
            logger.warning(
                "Gemini model list changed for run_id=%s: previous_raw_sha=%s new_raw_sha=%s added=%s removed=%s",
                run_id,
                prev_raw_sha,
                raw_response_sha,
                len(new_ids - old_ids),
                len(old_ids - new_ids),
            )

        elapsed_ms = int((time.time() - started) * 1000)
        logger.info(
            "Gemini models listing complete run_id=%s models=%s raw_models=%s raw_response_sha=%s output_sha=%s elapsed_ms=%s path=%s",
            run_id,
            len(generation_capable),
            len(raw_models),
            raw_response_sha,
            digest,
            elapsed_ms,
            output_path,
        )
        return 0
    except Exception as exc:
        error_body = sanitize_error_text(str(exc))
        payload = {
            "generated_at": now_iso(),
            "run_id": run_id,
            "status": "failed",
            "stage": "gemini_list_models",
            "error_type": type(exc).__name__,
            "error": error_body[:1600],
            "api_key_env_name": "GEMINI_API_KEY",
            "api_key_env_resolved": resolved_api_key_env,
            "endpoint": GEMINI_MODELS_ENDPOINT,
            "pages_fetched": page_count,
            "raw_page_sha256": raw_page_hashes,
        }
        write_json(failed_path, payload)
        logger.error("Gemini models listing failed: %s", error_body)
        return 1


def run_doctor_full(
    root: Path,
    dirs: Dict[str, Path],
    run_id: str,
    phases: List[str],
    cfg: RunnerConfig,
) -> int:
    prompt_index, duplicates = collect_prompt_index()
    missing_steps: Dict[str, List[str]] = {}
    promptpack: Dict[str, List[Dict[str, Any]]] = {}
    for phase in phases:
        specs = get_phase_prompts(phase)
        if not specs:
            missing_steps[phase] = [f"No prompts found for phase {phase}."]
            promptpack[phase] = []
            continue
        promptpack[phase] = [
            {
                "step_id": spec.step_id,
                "path": str(spec.prompt_path.resolve()),
                "sha256": sha256_file_strict(spec.prompt_path),
                "declared_outputs": list(spec.output_artifacts),
            }
            for spec in specs
        ]

    required_status = get_required_artifact_status(dirs, R_REQUIRED_INPUT_PHASES)
    provider_routes = collect_provider_routes()
    provider_probes = [
        run_provider_doctor_probe(
            provider=route["provider"],
            model_id=route["model_id"],
            api_key_env=route["api_key_env"],
            cfg=cfg,
        )
        for route in provider_routes.values()
    ]

    payload = {
        "generated_at": now_iso(),
        "run_id": run_id,
        "runner": {
            "script_path": str(RUNNER_SCRIPT.resolve()),
            "runner_sha256": sha256_text(RUNNER_SCRIPT),
            "git_sha": get_git_sha(root),
            "python_executable": sys.executable,
            "python_version": platform.python_version(),
        },
        "phases": phases,
        "prompt_set_integrity": {
            "duplicate_step_ids": duplicates,
            "missing_steps_by_phase": missing_steps,
            "promptpack": promptpack,
        },
        "required_artifact_groups": required_status,
        "provider_reachability": {
            "routes": provider_routes,
            "probes": provider_probes,
        },
    }

    doctor_dir = root / V3_DOCTOR_ROOT
    doctor_dir.mkdir(parents=True, exist_ok=True)
    write_json(doctor_dir / "DOCTOR_FULL.json", payload)
    print(json.dumps(payload, indent=2))

    has_missing = any(missing_steps.values())
    has_duplicates = bool(duplicates)
    has_provider_fail = any(
        probe.get("status_code") not in {200}
        for probe in provider_probes
    )
    return 0 if not (has_missing or has_duplicates or has_provider_fail) else 1


def redact_sensitive_lines(text: str) -> Tuple[str, int]:
    output_lines: List[str] = []
    had_trailing_newline = text.endswith("\n")
    redaction_hits = 0

    for line in text.splitlines():
        redacted = line
        if SECRET_LINE_RE.search(redacted):
            replaced = SECRET_ASSIGN_RE.sub(r"\1[REDACTED]", redacted)
            redacted = replaced if replaced != redacted else "[REDACTED_LINE]"
            redaction_hits += 1
        redacted, token_hits = LONG_TOKEN_RE.subn("[REDACTED_LONG_TOKEN]", redacted)
        redaction_hits += token_hits
        output_lines.append(redacted)

    out = "\n".join(output_lines)
    if had_trailing_newline:
        out += "\n"
    return out, redaction_hits


# --- Inventory / Partitioning ---

def build_inventory(items: List[Dict[str, Any]], file_truncate_chars: int) -> List[Dict[str, Any]]:
    unique_paths = sorted({str(Path(item["path"]).resolve()) for item in items if item.get("path")})
    inventory: List[Dict[str, Any]] = []

    for path_str in unique_paths:
        path = Path(path_str)
        if not path.exists() or not path.is_file():
            continue

        content = safe_read(path)
        char_count = len(content)
        est_chars = min(char_count, file_truncate_chars)
        try:
            st = path.stat()
            size = st.st_size
            mtime = st.st_mtime
        except Exception:
            size = 0
            mtime = 0.0

        inventory.append(
            {
                "path": str(path),
                "size": size,
                "mtime": mtime,
                "sha256": sha256_text(path),
                "kind": classify_kind(path),
                "char_count": char_count,
                "char_count_estimate": est_chars,
            }
        )

    inventory.sort(key=lambda item: item["path"])
    return inventory


def max_files_for_phase(phase: str, cfg: RunnerConfig) -> int:
    if phase in CODE_HEAVY_PHASES:
        return cfg.max_files_code
    return cfg.max_files_docs


def build_partitions(
    phase: str, inventory: List[Dict[str, Any]], max_files: int, max_chars: int
) -> List[Dict[str, Any]]:
    partitions: List[Dict[str, Any]] = []
    current_paths: List[str] = []
    current_chars = 0

    def flush_partition() -> None:
        nonlocal current_paths, current_chars
        if not current_paths:
            return
        partition_id = f"{phase}_P{len(partitions) + 1:04d}"
        partitions.append(
            {
                "id": partition_id,
                "paths": list(current_paths),
                "file_count": len(current_paths),
                "char_count_estimate": current_chars,
            }
        )
        current_paths = []
        current_chars = 0

    for item in inventory:
        path = item["path"]
        base_chars = int(item.get("char_count_estimate", 0))
        # Account for per-file headers in context payload construction.
        est_chars = base_chars + min(len(path) + 80, 2000)
        would_exceed_files = len(current_paths) >= max_files
        would_exceed_chars = current_paths and (current_chars + est_chars > max_chars)
        if would_exceed_files or would_exceed_chars:
            flush_partition()
        current_paths.append(path)
        current_chars += est_chars

    flush_partition()
    if not partitions:
        partitions.append(
            {
                "id": f"{phase}_P0001",
                "paths": [],
                "file_count": 0,
                "char_count_estimate": 0,
            }
        )
    return partitions


def sort_key_for_item(item: Dict[str, Any]) -> Tuple[str, int, str, str]:
    path = str(item.get("path", ""))
    line_start = 0
    line_range = item.get("line_range")
    if isinstance(line_range, list) and line_range:
        try:
            line_start = int(line_range[0])
        except Exception:
            line_start = 0
    elif isinstance(line_range, str):
        match = re.search(r"\d+", line_range)
        if match:
            line_start = int(match.group(0))
    item_id = str(item.get("id", ""))
    fallback = hashlib.sha256(
        json.dumps(item, sort_keys=True, ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    return (path, line_start, item_id, fallback)


def normalize_json_payload(payload: Any) -> Any:
    if isinstance(payload, str):
        parsed = parse_json_from_response(payload)
        if parsed is not None:
            return parsed
    return payload


def stable_sort_list(items: List[Any]) -> List[Any]:
    if not items:
        return items
    if all(isinstance(item, dict) for item in items):
        return sorted(items, key=sort_key_for_item)
    return sorted(
        items,
        key=lambda item: hashlib.sha256(
            json.dumps(item, sort_keys=True, ensure_ascii=True, default=str).encode("utf-8")
        ).hexdigest(),
    )


def merge_json_chunks(chunks: List[Dict[str, Any]]) -> Any:
    if not chunks:
        return {"items": []}

    normalized = [
        {"partition_id": chunk["partition_id"], "payload": normalize_json_payload(chunk["payload"])}
        for chunk in chunks
    ]
    payloads = [chunk["payload"] for chunk in normalized]

    if len(payloads) == 1:
        payload = payloads[0]
        if isinstance(payload, list):
            return stable_sort_list(payload)
        if isinstance(payload, dict) and isinstance(payload.get("items"), list):
            return {**payload, "items": stable_sort_list(payload["items"])}
        return payload

    if all(isinstance(payload, list) for payload in payloads):
        merged_list: List[Any] = []
        for payload in payloads:
            merged_list.extend(payload)
        return stable_sort_list(merged_list)

    if all(isinstance(payload, dict) and isinstance(payload.get("items"), list) for payload in payloads):
        merged_items: List[Any] = []
        for payload in payloads:
            merged_items.extend(payload["items"])
        return {"items": stable_sort_list(merged_items)}

    return {
        "chunks": [
            {"partition_id": chunk["partition_id"], "payload": chunk["payload"]}
            for chunk in normalized
        ]
    }


def merge_markdown_chunks(chunks: List[Dict[str, Any]]) -> str:
    if not chunks:
        return ""
    if len(chunks) == 1:
        payload = chunks[0]["payload"]
        return payload if isinstance(payload, str) else json.dumps(payload, indent=2, ensure_ascii=True)

    parts: List[str] = []
    for chunk in chunks:
        partition_id = chunk["partition_id"]
        payload = chunk["payload"]
        text = payload if isinstance(payload, str) else json.dumps(payload, indent=2, ensure_ascii=True)
        parts.append(f"## {partition_id}\n\n{text.strip()}")
    return "\n\n".join(parts).strip() + "\n"


def extract_artifacts_from_partition_payload(
    payload: Any,
    expected_artifacts: Tuple[str, ...],
) -> List[Dict[str, Any]]:
    extracted: List[Dict[str, Any]] = []

    if isinstance(payload, dict) and isinstance(payload.get("artifacts"), list):
        for candidate in payload["artifacts"]:
            if not isinstance(candidate, dict):
                continue
            artifact_name = str(candidate.get("artifact_name", "")).strip()
            if not artifact_name:
                continue
            extracted.append({"artifact_name": artifact_name, "payload": candidate.get("payload")})
        if extracted:
            return extracted

    if isinstance(payload, dict):
        for artifact_name in expected_artifacts:
            if artifact_name in payload:
                extracted.append({"artifact_name": artifact_name, "payload": payload[artifact_name]})
        if extracted:
            return extracted

    if len(expected_artifacts) == 1:
        extracted.append({"artifact_name": expected_artifacts[0], "payload": payload})

    return extracted


def normalize_step(
    phase: str,
    prompt_spec: PromptSpec,
    phase_dir: Path,
    partitions: List[Dict[str, Any]],
    step_exec_stats: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    step_id = prompt_spec.step_id
    expected_artifacts = prompt_spec.output_artifacts
    raw_dir = phase_dir / "raw"
    norm_dir = phase_dir / "norm"
    qa_dir = phase_dir / "qa"
    partition_ids = [partition["id"] for partition in partitions]
    partition_order = {partition_id: idx + 1 for idx, partition_id in enumerate(partition_ids)}

    artifacts_by_name: Dict[str, List[Dict[str, Any]]] = {name: [] for name in expected_artifacts}
    parse_failures: List[Dict[str, str]] = []
    raw_ok = 0
    raw_failed = 0
    unexpected_artifacts: Counter[str] = Counter()

    for partition_id in partition_ids:
        raw_file = raw_dir / f"{step_id}__{partition_id}.json"
        fail_file = raw_dir / f"{step_id}__{partition_id}.FAILED.txt"
        if raw_file.exists():
            payload_text = safe_read(raw_file)
            try:
                payload = json.loads(payload_text)
            except json.JSONDecodeError:
                raw_failed += 1
                parse_failures.append(
                    {
                        "partition_id": partition_id,
                        "reason": "invalid_json",
                        "file": str(raw_file),
                    }
                )
                continue

            raw_ok += 1
            artifacts = extract_artifacts_from_partition_payload(payload, expected_artifacts)
            if not artifacts:
                parse_failures.append(
                    {
                        "partition_id": partition_id,
                        "reason": "missing_artifacts",
                        "file": str(raw_file),
                    }
                )
                continue

            for artifact in artifacts:
                artifact_name = artifact["artifact_name"]
                if artifact_name not in artifacts_by_name:
                    unexpected_artifacts[artifact_name] += 1
                    continue
                artifacts_by_name[artifact_name].append(
                    {"partition_id": partition_id, "payload": artifact["payload"]}
                )
        else:
            raw_failed += 1
            reason = "missing_output"
            file_path = str(raw_file)
            if fail_file.exists():
                reason = "llm_output_parse_failed"
                file_path = str(fail_file)
            parse_failures.append(
                {"partition_id": partition_id, "reason": reason, "file": file_path}
            )

    written_files: List[str] = []
    missing_expected_artifacts: List[str] = []
    missing_counts: Counter[str] = Counter()
    duplicate_ids: List[Dict[str, Any]] = []

    for artifact_name in expected_artifacts:
        chunks = artifacts_by_name.get(artifact_name, [])
        if not chunks:
            missing_expected_artifacts.append(artifact_name)
            continue

        chunks = sorted(chunks, key=lambda chunk: chunk["partition_id"])
        if ".partX." in artifact_name:
            for chunk in chunks:
                part_num = partition_order.get(chunk["partition_id"], 0)
                part_file = artifact_name.replace(".partX.", f".part{part_num:04d}.")
                part_path = norm_dir / part_file
                if part_path.suffix == ".json":
                    write_json(part_path, normalize_json_payload(chunk["payload"]))
                else:
                    text_payload = chunk["payload"]
                    if not isinstance(text_payload, str):
                        text_payload = json.dumps(text_payload, indent=2, ensure_ascii=True)
                    part_path.write_text(text_payload if text_payload.endswith("\n") else text_payload + "\n", encoding="utf-8")
                written_files.append(part_file)
            continue

        out_path = norm_dir / artifact_name
        if artifact_name.endswith(".json"):
            merged_payload = merge_json_chunks(chunks)
            write_json(out_path, merged_payload)
            written_files.append(artifact_name)

            inspect_items: List[Dict[str, Any]] = []
            if isinstance(merged_payload, list):
                inspect_items = [item for item in merged_payload if isinstance(item, dict)]
            elif isinstance(merged_payload, dict):
                payload_items = merged_payload.get("items")
                if isinstance(payload_items, list):
                    inspect_items = [item for item in payload_items if isinstance(item, dict)]

            id_counter: Counter[str] = Counter()
            for item in inspect_items:
                for key in REQUIRED_ITEM_KEYS:
                    if key not in item or item.get(key) in (None, "", []):
                        missing_counts[key] += 1
                item_id = str(item.get("id", "")).strip()
                if item_id:
                    id_counter[item_id] += 1

            duplicate_ids.extend(
                {"artifact": artifact_name, "id": item_id, "count": count}
                for item_id, count in sorted(id_counter.items(), key=lambda pair: (-pair[1], pair[0]))
                if count > 1
            )
            continue

        merged_text = merge_markdown_chunks(chunks)
        out_path.write_text(merged_text, encoding="utf-8")
        written_files.append(artifact_name)

    qa_payload = {
        "phase": phase,
        "step_id": step_id,
        "generated_at": now_iso(),
        "partitions_total": len(partition_ids),
        "raw_ok": raw_ok,
        "raw_failed": raw_failed,
        "expected_artifacts": list(expected_artifacts),
        "written_files": written_files,
        "missing_expected_artifacts": missing_expected_artifacts,
        "unexpected_artifacts": dict(sorted(unexpected_artifacts.items())),
        "missing_required_keys_counts": dict(sorted(missing_counts.items())),
        "duplicate_ids": duplicate_ids[:200],
        "parse_failures": parse_failures,
        "required_item_keys": REQUIRED_ITEM_KEYS,
        "resume_skipped_partitions": int((step_exec_stats or {}).get("resume_skipped", 0)),
        "recomputed_partitions": int((step_exec_stats or {}).get("recomputed", 0)),
        "dry_run_partitions": int((step_exec_stats or {}).get("dry_run", 0)),
        "execution_failed_partitions": int((step_exec_stats or {}).get("failed", 0)),
    }

    write_json(qa_dir / f"{step_id}_QA.json", qa_payload)
    return qa_payload


# --- LLM Execution ---

def transport_for_provider(provider: str, cfg: RunnerConfig) -> str:
    if provider == "gemini":
        return cfg.gemini_transport
    if provider == "xai":
        return cfg.xai_transport
    return cfg.openai_transport


def resolve_temperature(provider: str, model_id: str, default_temp: float) -> Optional[float]:
    if provider == "openai" and model_id.startswith("gpt-5"):
        return None
    return default_temp


def llm_base_url(provider: str, cfg: Optional[RunnerConfig] = None) -> str:
    if provider == "gemini" and cfg is not None and transport_for_provider(provider, cfg) == "openai_compat_http":
        return GEMINI_OPENAI_COMPAT_BASE_URL
    return PROVIDER_BASE_URL.get(provider, PROVIDER_BASE_URL["openai"])


def build_chat_payload(
    provider: str,
    model_id: str,
    system_prompt: str,
    user_content: str,
    force_json_output: bool = False,
) -> Dict[str, Any]:
    temperature = resolve_temperature(provider, model_id, 0.1)
    payload: Dict[str, Any] = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if force_json_output:
        if provider == "gemini":
            payload["response_format"] = {"type": "json_object"}
        elif provider in {"openai", "xai"}:
            payload["response_format"] = {"type": "json_object"}
    return payload


def serialize_payload_body(payload: Dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def measure_payload_bytes_from_body(body: bytes) -> int:
    return len(body)


def endpoint_effective(url: str) -> str:
    return _sanitize_url(url)


def _sanitize_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.query:
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    redacted = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        if key.lower() == "key":
            redacted.append((key, "REDACTED"))
        else:
            redacted.append((key, value))
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", urlencode(redacted), ""))


def _is_gemini_openai_compat_endpoint(endpoint_base_url: str) -> bool:
    return "/v1beta/openai" in (endpoint_base_url or "")


def _gemini_auth_mode_sequence(cfg_mode: str, endpoint_base_url: str) -> List[str]:
    if not _is_gemini_openai_compat_endpoint(endpoint_base_url):
        return ["sdk_api_key"]
    if cfg_mode != "auto":
        return [cfg_mode]
    if _is_gemini_openai_compat_endpoint(endpoint_base_url):
        return ["query_key", "api_key", "both"]
    return ["api_key", "query_key", "both"]


def _gemini_build_endpoint_and_headers(
    endpoint_base_url: str,
    api_key: str,
    mode: str,
) -> Tuple[str, Dict[str, str], Dict[str, bool]]:
    endpoint = f"{endpoint_base_url}/chat/completions"
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if mode == "query_key":
        effective_url = f"{endpoint}?{urlencode({'key': api_key})}"
    else:
        effective_url = endpoint
    if mode == "api_key":
        headers["x-goog-api-key"] = api_key
    elif mode == "bearer":
        headers["Authorization"] = f"Bearer {api_key}"
    elif mode == "both":
        headers["Authorization"] = f"Bearer {api_key}"
        headers["x-goog-api-key"] = api_key
    auth_flags = build_auth_present_flags(headers, mode == "query_key")
    return effective_url, headers, auth_flags


def endpoint_fingerprint(url: str) -> Dict[str, str]:
    parsed = urlparse(url)
    return {
        "endpoint_host": parsed.netloc,
        "endpoint_path": parsed.path,
    }


def provider_signature(
    provider: str,
    model_id: str,
    endpoint_url: str,
    gemini_auth_mode_effective: Optional[str],
) -> str:
    fp = endpoint_fingerprint(endpoint_url)
    auth_mode = gemini_auth_mode_effective if provider == "gemini" else "bearer"
    return (
        f"provider={provider};model={model_id};host={fp['endpoint_host']};"
        f"path={fp['endpoint_path']};auth_mode={auth_mode}"
    )


def routing_signature(
    phase: str,
    step_id: str,
    provider: str,
    model_id: str,
    endpoint_base_url: str,
    gemini_auth_mode_effective: Optional[str],
) -> str:
    canonical = {
        "endpoint_base_url": endpoint_base_url,
        "gemini_auth_mode_effective": gemini_auth_mode_effective,
        "model_id": model_id,
        "phase": phase,
        "provider": provider,
        "step_id": step_id,
    }
    encoded = json.dumps(canonical, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_auth_present_flags(headers: Dict[str, str], used_query_key: bool) -> Dict[str, bool]:
    return {
        "has_auth": "Authorization" in headers,
        "has_xgoog": "x-goog-api-key" in headers,
        "used_query_key": used_query_key,
    }


def make_headers(provider: str, api_key: str, cfg: RunnerConfig, auth_mode: Optional[str] = None) -> Dict[str, str]:
    if transport_for_provider(provider, cfg) != "openai_compat_http":
        return {}
    mode = auth_mode or cfg.gemini_auth_mode
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if provider != "gemini":
        headers["Authorization"] = f"Bearer {api_key}"
        return headers
    if mode == "api_key":
        headers["x-goog-api-key"] = api_key
    elif mode == "bearer":
        headers["Authorization"] = f"Bearer {api_key}"
    elif mode == "both" or mode == "auto":
        headers["Authorization"] = f"Bearer {api_key}"
        headers["x-goog-api-key"] = api_key
    elif mode == "query_key":
        pass
    else:
        headers["Authorization"] = f"Bearer {api_key}"
        headers["x-goog-api-key"] = api_key
    return headers


def make_url(
    provider: str,
    base_url: str,
    cfg: RunnerConfig,
    api_key: str,
    auth_mode_override: Optional[str] = None,
) -> str:
    mode = auth_mode_override or cfg.gemini_auth_mode
    url = f"{base_url}/chat/completions"
    if provider == "gemini" and mode == "query_key":
        return f"{url}?{urlencode({'key': api_key})}"
    return url


def transport_endpoint_url(
    provider: str,
    model_id: str,
    cfg: RunnerConfig,
    api_key: str = "",
    gemini_auth_mode: Optional[str] = None,
) -> str:
    base_url = llm_base_url(provider, cfg)
    if transport_for_provider(provider, cfg) == "openai_compat_http":
        return make_url(provider, base_url, cfg, api_key, gemini_auth_mode)
    if provider == "gemini":
        return f"{base_url}/v1beta/models/{model_id}:generateContent"
    return f"{base_url}/chat/completions"


def resolve_api_key(
    provider: str,
    api_key_env: str,
) -> Tuple[str, str]:
    if provider == "gemini":
        key_value = os.getenv(api_key_env, "")
        legacy_google_key = os.getenv("GOOGLE_API_KEY", "")
        if key_value and legacy_google_key and key_value != legacy_google_key:
            logger.error(
                "Conflicting Gemini API keys detected. "
                "Use only GEMINI_API_KEY in repo-root .env and remove GOOGLE_API_KEY."
            )
            return "", api_key_env
        return key_value, api_key_env
    value = os.getenv(api_key_env, "")
    return value, api_key_env


def sdk_auth_present_flags(provider: str, api_key_present: bool) -> Dict[str, bool]:
    flags = {
        "has_auth": False,
        "has_xgoog": False,
        "used_query_key": False,
        "sdk_api_key_present": api_key_present,
    }
    if provider == "openai" and api_key_present:
        flags["has_auth"] = True
    if provider == "xai" and api_key_present:
        flags["has_auth"] = True
    if provider == "gemini" and api_key_present:
        flags["has_xgoog"] = True
    return flags


def get_gemini_client(api_key: str) -> Any:
    try:
        from google import genai
    except ImportError as exc:
        raise RuntimeError("google-genai is required for Gemini SDK transport.") from exc
    # Canonical key source is GEMINI_API_KEY. Clear GOOGLE_API_KEY to prevent
    # google-genai from preferring the legacy env var when both are present.
    os.environ.pop("GOOGLE_API_KEY", None)
    return genai.Client(api_key=api_key)


def get_openai_client(base_url: Optional[str], api_key: str) -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai package is required for OpenAI/xAI SDK transport.") from exc
    kwargs: Dict[str, Any] = {"api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return OpenAI(**kwargs)


def get_xai_client(api_key: str) -> Any:
    return get_openai_client(base_url=PROVIDER_BASE_URL["xai"], api_key=api_key)


def extract_text_from_chat_completion(response_obj: Any) -> str:
    choices = getattr(response_obj, "choices", None)
    if not choices:
        return ""
    message = getattr(choices[0], "message", None)
    if message is None:
        return ""
    content = getattr(message, "content", "")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: List[str] = []
        for item in content:
            text_value = getattr(item, "text", None)
            if isinstance(text_value, str):
                chunks.append(text_value)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                chunks.append(item["text"])
        return "".join(chunks)
    return str(content or "")


def extract_text_from_gemini_response(response_obj: Any) -> str:
    text_attr = getattr(response_obj, "text", None)
    if isinstance(text_attr, str) and text_attr:
        return text_attr
    candidates = getattr(response_obj, "candidates", None) or []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", None) or []
        chunks: List[str] = []
        for part in parts:
            text_piece = getattr(part, "text", None)
            if isinstance(text_piece, str):
                chunks.append(text_piece)
        if chunks:
            return "".join(chunks)
    return ""


def summarize_llm_response(
    provider: str,
    transport: str,
    response_obj: Any,
    response_json: Optional[Dict[str, Any]],
    response_text: str,
) -> Dict[str, Any]:
    summary: Dict[str, Any] = {"text_length": len(response_text)}
    finish_reason = None
    candidate_count: Optional[int] = None

    if provider == "gemini":
        candidates = getattr(response_obj, "candidates", None) or []
        candidate_count = len(candidates)
        if candidates:
            finish_reason = getattr(candidates[0], "finish_reason", None)
    else:
        choices = None
        if isinstance(response_json, dict):
            choices = response_json.get("choices")
        else:
            choices = getattr(response_obj, "choices", None)
        if isinstance(choices, list):
            candidate_count = len(choices)
            if choices:
                finish_reason = getattr(choices[0], "finish_reason", None)

    if candidate_count is not None:
        summary["candidate_count"] = candidate_count
    if finish_reason:
        summary["finish_reason"] = finish_reason
    return summary


def capture_exception_metadata(exc: Exception) -> Dict[str, str]:
    message = sanitize_error_text(str(exc))
    return {
        "exception_type": type(exc).__name__,
        "exception_message_excerpt": message[:800],
    }


def exception_status_code(exc: Exception) -> Optional[int]:
    status = getattr(exc, "status_code", None)
    if isinstance(status, int):
        return status
    response = getattr(exc, "response", None)
    status = getattr(response, "status_code", None)
    if isinstance(status, int):
        return status
    return None


def exception_response_text(exc: Exception) -> str:
    body = getattr(exc, "body", None)
    if isinstance(body, str):
        return body
    if isinstance(body, dict):
        return json.dumps(body, ensure_ascii=True)
    response = getattr(exc, "response", None)
    text_attr = getattr(response, "text", None)
    if isinstance(text_attr, str):
        return text_attr
    return ""


def classify_failure_type(status_code: Optional[int], response_body: str, error_text: str) -> str:
    body = (response_body or "").lower()
    err = (error_text or "").lower()
    joined = f"{body}\n{err}"
    if "api key expired" in joined:
        return "auth_expired"
    if "api key not found" in joined or "api_key_invalid" in joined:
        return "api_key_missing_or_invalid"
    if "missing authorization header" in joined:
        return "auth_missing"
    if "permission_denied" in joined:
        return "permission_denied"
    if "resource_exhausted" in joined or "billing" in joined or "quota" in joined:
        return "quota_or_billing"
    if (
        "api key not valid" in joined
        or status_code in {401, 403}
        or "unauthorized" in joined
        or "permission" in joined
    ):
        return "auth_rejected"
    if status_code == 408:
        return "network"
    if status_code == 429 or "rate limit" in joined or "too many requests" in joined:
        return "rate_limit"
    if status_code is not None and 400 <= status_code < 500:
        return "payload"
    if status_code is not None and status_code >= 500:
        return "provider"
    if "timeout" in joined or "connection" in joined or "network" in joined:
        return "network"
    return "unknown"


def extract_provider_error_reason(response_body: str) -> Optional[str]:
    if not response_body:
        return None
    try:
        parsed = json.loads(response_body)
        if isinstance(parsed, list) and parsed:
            parsed = parsed[0]
        if not isinstance(parsed, dict):
            return None
        error_obj = parsed.get("error")
        if not isinstance(error_obj, dict):
            return None
        details = error_obj.get("details")
        if isinstance(details, list):
            for detail in details:
                if isinstance(detail, dict):
                    reason = detail.get("reason")
                    if isinstance(reason, str) and reason.strip():
                        return reason.strip()
        reason = error_obj.get("status")
        if isinstance(reason, str) and reason.strip():
            return reason.strip()
    except Exception:
        return None
    return None


def sanitize_error_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"([?&]key=)[^&\\s]+", r"\1REDACTED", text)


def is_retryable_exception(exc: Exception) -> bool:
    text = str(exc).lower()
    return isinstance(exc, requests.exceptions.Timeout) or "timeout" in text or "connection reset" in text


def should_retry(
    status_code: Optional[int],
    failure_type: str,
    exc: Optional[Exception],
    retry_policy: str,
) -> bool:
    if retry_policy == "none":
        return False
    if (
        failure_type.startswith("auth_")
        or failure_type in {"quota_or_billing", "api_key_missing_or_invalid", "permission_denied"}
    ):
        return False
    if status_code in {408, 429, 500, 502, 503, 504}:
        return True
    if exc is not None and is_retryable_exception(exc):
        return True
    return False


def is_auth_expired_failure(failure_type: Optional[str]) -> bool:
    return str(failure_type or "") == "auth_expired"


def backoff_seconds(attempt: int, base_seconds: float, max_seconds: float) -> float:
    if attempt <= 1:
        return 0.0
    delay = base_seconds * (2 ** (attempt - 2))
    return min(delay, max_seconds)


def call_llm(
    provider: str,
    model_id: str,
    api_key_env: str,
    system_prompt: str,
    user_content: str,
    cfg: RunnerConfig,
    force_json_output: bool = False,
) -> Dict[str, Any]:
    base_url = llm_base_url(provider, cfg)
    transport = transport_for_provider(provider, cfg)
    api_key, resolved_api_key_env = resolve_api_key(provider, api_key_env)
    payload = build_chat_payload(
        provider,
        model_id,
        system_prompt,
        user_content,
        force_json_output=force_json_output,
    )
    body = serialize_payload_body(payload)
    request_payload_bytes = measure_payload_bytes_from_body(body)
    request_payload_bytes_mode = "exact_http" if transport == "openai_compat_http" else "sdk_estimate"
    gemini_mode_requested = cfg.gemini_auth_mode if provider == "gemini" else None
    gemini_family = (
        "openai_compat" if provider == "gemini" and transport == "openai_compat_http" else "native"
    ) if provider == "gemini" else None
    structured_output: Dict[str, Any] = {
        "enabled": bool(provider == "gemini" and force_json_output),
        "mime_type": "application/json" if provider == "gemini" and force_json_output else None,
        "schema": None,
        "transport_mode": (
            "response_format_json_object"
            if provider == "gemini" and transport == "openai_compat_http" and force_json_output
            else ("response_mime_type" if provider == "gemini" and force_json_output else None)
        ),
    }
    auth_mode_sequence = _gemini_auth_mode_sequence(cfg.gemini_auth_mode, base_url) if provider == "gemini" else ["sdk_bearer"]
    mode_index = 0
    effective_mode = auth_mode_sequence[mode_index]
    endpoint_url = (
        f"{base_url}/v1beta/models/{model_id}:generateContent"
        if provider == "gemini" and transport != "openai_compat_http"
        else f"{base_url}/chat/completions"
    )
    sent_header_keys: List[str] = []
    auth_flags = sdk_auth_present_flags(provider, bool(api_key))
    if transport == "openai_compat_http":
        endpoint_url = make_url(provider, base_url, cfg, api_key, effective_mode)
        headers = make_headers(provider, api_key, cfg, effective_mode)
        sent_header_keys = sorted(list(headers.keys()))
        auth_flags = build_auth_present_flags(headers, provider == "gemini" and effective_mode == "query_key")

    if not api_key:
        logger.error("Missing API key env var: %s", api_key_env)
        if provider == "gemini":
            logger.error(
                "Gemini requires GEMINI_API_KEY in repo-root .env (canonical). "
                "GOOGLE_API_KEY is deprecated for this runner."
            )
        return {
            "ok": False,
            "text": "",
            "meta": {
                "provider": provider,
                "model_id": model_id,
                "endpoint_base_url": base_url,
                "endpoint_effective": endpoint_effective(endpoint_url),
                **endpoint_fingerprint(endpoint_url),
                "status_code": None,
                "failure_type": "auth_missing",
                "sent_header_keys": sent_header_keys,
                "auth_present_flags": auth_flags,
                "gemini_auth_mode_requested": gemini_mode_requested,
                "gemini_auth_mode_effective": None,
                "provider_signature": provider_signature(provider, model_id, endpoint_url, None),
                "provider_error_reason": "MISSING_API_KEY_ENV",
                "api_key_env_requested": api_key_env,
                "api_key_env_resolved": resolved_api_key_env,
                "gemini_endpoint_family": gemini_family,
                "gemini_auth_attempt_sequence": auth_mode_sequence if provider == "gemini" else None,
                "request_payload_bytes": request_payload_bytes,
                "request_payload_bytes_mode": request_payload_bytes_mode,
                "transport": transport,
                "retry_trace": [],
                "structured_output": structured_output,
            },
        }

    last_failure_meta: Dict[str, Any] = {
        "provider": provider,
        "model_id": model_id,
        "endpoint_base_url": base_url,
        "endpoint_effective": endpoint_effective(endpoint_url),
        **endpoint_fingerprint(endpoint_url),
        "status_code": None,
        "failure_type": "unknown",
        "request_payload_bytes": request_payload_bytes,
        "request_payload_bytes_mode": request_payload_bytes_mode,
        "sent_header_keys": sent_header_keys,
        "auth_present_flags": auth_flags,
        "gemini_auth_mode_requested": gemini_mode_requested,
        "gemini_auth_mode_effective": effective_mode if provider == "gemini" else None,
        "provider_signature": provider_signature(
            provider,
            model_id,
            endpoint_url,
            effective_mode if provider == "gemini" else None,
        ),
        "provider_error_reason": None,
        "api_key_env_requested": api_key_env,
        "api_key_env_resolved": resolved_api_key_env,
        "gemini_endpoint_family": gemini_family,
        "gemini_auth_attempt_sequence": auth_mode_sequence if provider == "gemini" else None,
        "transport": transport,
        "retry_trace": [],
        "structured_output": structured_output,
    }
    retry_trace: List[Dict[str, Any]] = []

    attempt = 0
    while attempt < cfg.retry_max_attempts:
        attempt += 1
        status_code: Optional[int] = None
        response_body = ""
        failure_type = "unknown"
        provider_error_reason = None
        try:
            response_json: Optional[Dict[str, Any]] = None
            if transport == "openai_compat_http":
                headers = make_headers(provider, api_key, cfg, effective_mode)
                endpoint_url = make_url(provider, base_url, cfg, api_key, effective_mode)
                auth_flags = build_auth_present_flags(headers, provider == "gemini" and effective_mode == "query_key")
                sent_header_keys = sorted(list(headers.keys()))
                response = requests.post(endpoint_url, headers=headers, data=body, timeout=180)
                response.raise_for_status()
                status_code = response.status_code
                response_json = response.json()
                response_text = response_json["choices"][0]["message"]["content"]
            elif provider == "gemini":
                client = get_gemini_client(api_key)
                response = client.models.generate_content(
                    model=model_id,
                    contents=user_content,
                    config={
                        "temperature": 0.1,
                        "system_instruction": system_prompt,
                        **({"response_mime_type": "application/json"} if force_json_output else {}),
                    },
                )
                status_code = 200
                response_text = extract_text_from_gemini_response(response)
            else:
                client = get_xai_client(api_key) if provider == "xai" else get_openai_client(None, api_key)
                chat_kwargs: Dict[str, Any] = {
                    "model": model_id,
                    "messages": payload["messages"],
                }
                if "temperature" in payload:
                    chat_kwargs["temperature"] = payload["temperature"]
                if "response_format" in payload:
                    chat_kwargs["response_format"] = payload["response_format"]
                response = client.chat.completions.create(**chat_kwargs)
                status_code = 200
                response_text = extract_text_from_chat_completion(response)

            response_summary = summarize_llm_response(
                provider=provider,
                transport=transport,
                response_obj=response,
                response_json=response_json,
                response_text=response_text,
            )
            retry_trace.append(
                {
                    "attempt": attempt,
                    "status_code": status_code,
                    "failure_type": None,
                    "delay_seconds": 0.0,
                    "gemini_auth_mode_effective": effective_mode if provider == "gemini" else None,
                    "provider_error_reason": None,
                    "response_received": True,
                    "response_summary": response_summary,
                }
            )
            return {
                "ok": True,
                "text": response_text,
                "meta": {
                    "provider": provider,
                    "model_id": model_id,
                    "endpoint_base_url": base_url,
                    "endpoint_effective": endpoint_effective(endpoint_url),
                    **endpoint_fingerprint(endpoint_url),
                    "status_code": status_code,
                    "failure_type": None,
                    "request_payload_bytes": request_payload_bytes,
                    "request_payload_bytes_mode": request_payload_bytes_mode,
                    "sent_header_keys": sent_header_keys,
                    "auth_present_flags": auth_flags,
                    "gemini_auth_mode_requested": gemini_mode_requested,
                    "gemini_auth_mode_effective": effective_mode if provider == "gemini" else None,
                    "provider_signature": provider_signature(
                        provider,
                        model_id,
                        endpoint_url,
                        effective_mode if provider == "gemini" else None,
                    ),
                    "provider_error_reason": None,
                    "api_key_env_requested": api_key_env,
                    "api_key_env_resolved": resolved_api_key_env,
                    "gemini_endpoint_family": gemini_family,
                    "gemini_auth_attempt_sequence": auth_mode_sequence if provider == "gemini" else None,
                    "transport": transport,
                    "retry_trace": retry_trace,
                    "response_received": True,
                    "response_summary": response_summary,
                    "structured_output": structured_output,
                },
            }
        except Exception as exc:
            status_code = exception_status_code(exc)
            response_body = exception_response_text(exc)[:1200]
            failure_type = classify_failure_type(status_code, response_body, str(exc))
            provider_error_reason = extract_provider_error_reason(response_body)
            safe_exc = sanitize_error_text(str(exc))
            safe_body = sanitize_error_text(response_body)
            exception_info = capture_exception_metadata(exc)
            retry_trace.append(
                {
                    "attempt": attempt,
                    "status_code": status_code,
                    "failure_type": failure_type,
                    "delay_seconds": 0.0,
                    "gemini_auth_mode_effective": effective_mode if provider == "gemini" else None,
                    "provider_error_reason": provider_error_reason,
                    "response_received": False,
                    **exception_info,
                }
            )
            last_failure_meta = {
                "provider": provider,
                "model_id": model_id,
                "endpoint_base_url": base_url,
                "endpoint_effective": endpoint_effective(endpoint_url),
                **endpoint_fingerprint(endpoint_url),
                "status_code": status_code,
                "failure_type": failure_type,
                "request_payload_bytes": request_payload_bytes,
                "request_payload_bytes_mode": request_payload_bytes_mode,
                "sent_header_keys": sent_header_keys,
                "auth_present_flags": auth_flags,
                "gemini_auth_mode_requested": gemini_mode_requested,
                "gemini_auth_mode_effective": effective_mode if provider == "gemini" else None,
                "provider_signature": provider_signature(
                    provider,
                    model_id,
                    endpoint_url,
                    effective_mode if provider == "gemini" else None,
                ),
                "provider_error_reason": provider_error_reason,
                **exception_info,
                "api_key_env_requested": api_key_env,
                "api_key_env_resolved": resolved_api_key_env,
                "gemini_endpoint_family": gemini_family,
                "gemini_auth_attempt_sequence": auth_mode_sequence if provider == "gemini" else None,
                "transport": transport,
                "retry_trace": retry_trace,
                "response_received": False,
                "structured_output": structured_output,
            }
            if response_body:
                logger.warning(
                    "LLM call failed attempt %s/%s provider=%s model=%s status=%s failure_type=%s: %s | body=%s",
                    attempt,
                    cfg.retry_max_attempts,
                    provider,
                    model_id,
                    status_code,
                    failure_type,
                    safe_exc,
                    safe_body,
                )
            else:
                logger.warning(
                    "LLM call failed attempt %s/%s provider=%s model=%s status=%s failure_type=%s: %s",
                    attempt,
                    cfg.retry_max_attempts,
                    provider,
                    model_id,
                    status_code,
                    failure_type,
                    safe_exc,
                )

            if (
                transport == "openai_compat_http"
                and provider == "gemini"
                and cfg.gemini_auth_mode == "auto"
                and is_auth_classified_failure(failure_type)
                and mode_index + 1 < len(auth_mode_sequence)
            ):
                mode_index += 1
                effective_mode = auth_mode_sequence[mode_index]
                logger.warning(
                    "Gemini openai_compat auth pivot after auth failure: next_mode=%s endpoint=%s",
                    effective_mode,
                    _sanitize_url(endpoint_url),
                )
                continue

            if not should_retry(status_code, failure_type, exc, cfg.retry_policy):
                break

            delay_seconds = backoff_seconds(attempt + 1, cfg.retry_base_seconds, cfg.retry_max_seconds)
            retry_trace[-1]["delay_seconds"] = delay_seconds
            if delay_seconds > 0:
                time.sleep(delay_seconds)
    logger.error("LLM call failed after retries provider=%s model=%s.", provider, model_id)
    return {
        "ok": False,
        "text": "",
        "meta": last_failure_meta,
    }


def is_auth_classified_failure(failure_type: Optional[str]) -> bool:
    if not failure_type:
        return False
    return failure_type.startswith("auth_") or failure_type in {
        "api_key_missing_or_invalid",
        "permission_denied",
        "quota_or_billing",
        "auth_rejected",
    }


def enrich_request_meta(
    meta: Dict[str, Any],
    run_id: str,
    phase: str,
    step_id: str,
    partition_id: str,
    provider: str,
    model_id: str,
) -> Dict[str, Any]:
    enriched = dict(meta or {})
    endpoint_base = str(enriched.get("endpoint_base_url") or llm_base_url(provider))
    auth_effective = enriched.get("gemini_auth_mode_effective")
    enriched["run_id"] = run_id
    enriched["phase"] = phase
    enriched["step_id"] = step_id
    enriched["partition_id"] = partition_id
    enriched.setdefault("provider", provider)
    enriched.setdefault("model_id", model_id)
    enriched.setdefault("endpoint_base_url", endpoint_base)
    if "provider_signature" not in enriched:
        enriched["provider_signature"] = provider_signature(
            provider,
            model_id,
            str(enriched.get("endpoint_effective") or f"{endpoint_base}/chat/completions"),
            auth_effective if provider == "gemini" else None,
        )
    enriched["routing_signature"] = routing_signature(
        phase,
        step_id,
        provider,
        model_id,
        endpoint_base,
        str(auth_effective) if provider == "gemini" and auth_effective is not None else None,
    )
    enriched["runner_script_sha256"] = sha256_text(RUNNER_SCRIPT)
    enriched["runner_script_path"] = str(RUNNER_SCRIPT.resolve())
    endpoint_sig_src = {
        "endpoint_effective": enriched.get("endpoint_effective"),
        "transport": enriched.get("transport"),
        "provider": enriched.get("provider"),
        "model_id": enriched.get("model_id"),
        "gemini_auth_mode_effective": enriched.get("gemini_auth_mode_effective"),
    }
    endpoint_sig = json.dumps(endpoint_sig_src, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    enriched["endpoint_transport_signature"] = hashlib.sha256(endpoint_sig.encode("utf-8")).hexdigest()
    enriched.setdefault("routing_tier", None)
    enriched.setdefault("routing_policy", None)
    enriched.setdefault("route_hop_index", None)
    enriched.setdefault("route_hop_total", None)
    enriched.setdefault("route_attempts", [])
    enriched.setdefault("escalation_trigger", None)
    enriched.setdefault("execution_mode", "sync")
    enriched.setdefault("batch_provider", None)
    enriched.setdefault("batch_job_id", None)
    return enriched


def call_llm_with_ladder(
    *,
    phase: str,
    step_id: str,
    partition_id: str,
    routing_policy: str,
    routing_tier: str,
    ladder: Sequence[Tuple[str, str, str]],
    cfg: RunnerConfig,
    execute_attempt: Callable[[Tuple[str, str, str], int], Dict[str, Any]],
    ui: Optional[UI] = None,
) -> Dict[str, Any]:
    if not ladder:
        return {
            "response_text": "",
            "request_meta": {
                "failure_type": "routing_empty_ladder",
                "provider_error_reason": "No routes configured for tier.",
            },
            "artifacts": [],
            "route": ("", "", ""),
            "escalation_trigger": "routing_empty_ladder",
            "route_attempts": [],
        }

    max_hops = 1 if cfg.disable_escalation else max(1, int(cfg.escalation_max_hops) + 1)
    max_hops = min(max_hops, len(ladder))
    attempts: List[Dict[str, Any]] = []
    final_payload: Optional[Dict[str, Any]] = None
    for hop_index in range(max_hops):
        route = tuple(ladder[hop_index])
        provider, model_id, api_key_env = route
        payload = execute_attempt(route, hop_index)
        request_meta = payload.get("request_meta") if isinstance(payload.get("request_meta"), dict) else {}
        escalation_trigger = str(payload.get("escalation_trigger") or "").strip() or None
        attempts.append(
            {
                "hop_index": hop_index + 1,
                "provider": provider,
                "model_id": model_id,
                "api_key_env": api_key_env,
                "failure_type": request_meta.get("failure_type"),
                "status_code": request_meta.get("status_code"),
                "escalation_trigger": escalation_trigger,
                "ok": bool(payload.get("artifacts_ok", False)),
            }
        )
        final_payload = dict(payload)
        if not escalation_trigger or hop_index + 1 >= max_hops:
            break
        if ui is not None:
            next_provider, next_model, _ = tuple(ladder[hop_index + 1])
            ui.escalation_event(
                phase=phase,
                step_id=step_id,
                partition_id=partition_id,
                reason=escalation_trigger,
                from_route=f"{provider}/{model_id}",
                to_route=f"{next_provider}/{next_model}",
                hop=hop_index + 1,
            )

    if final_payload is None:
        final_payload = {
            "response_text": "",
            "request_meta": {"failure_type": "routing_unresolved"},
            "artifacts": [],
            "route": tuple(ladder[0]),
            "escalation_trigger": "routing_unresolved",
        }
    final_request_meta = (
        dict(final_payload.get("request_meta"))
        if isinstance(final_payload.get("request_meta"), dict)
        else {}
    )
    final_request_meta["routing_tier"] = routing_tier
    final_request_meta["routing_policy"] = routing_policy
    final_request_meta["route_hop_total"] = len(attempts)
    final_request_meta["route_attempts"] = attempts
    final_request_meta["route_hop_index"] = int(attempts[-1]["hop_index"]) if attempts else 1
    final_request_meta["escalation_trigger"] = final_payload.get("escalation_trigger")
    final_route = tuple(final_payload.get("route") or ("", "", ""))
    final_request_meta["provider"] = final_route[0] if len(final_route) > 0 else final_request_meta.get("provider")
    final_request_meta["model_id"] = final_route[1] if len(final_route) > 1 else final_request_meta.get("model_id")
    return {
        **final_payload,
        "request_meta": final_request_meta,
    }


def run_gemini_auth_probe(
    run_id: str,
    phase: str,
    step_id: str,
    phase_dir: Path,
    provider: str,
    model_id: str,
    api_key_env: str,
    cfg: RunnerConfig,
) -> Dict[str, Any]:
    raw_dir = phase_dir / "raw"
    probe_path = raw_dir / f"AUTH_PROBE__gemini__{step_id}.json"
    system_prompt = "Return exactly OK."
    user_content = "Return the single token OK."
    result = call_llm(
        provider=provider,
        model_id=model_id,
        api_key_env=api_key_env,
        system_prompt=system_prompt,
        user_content=user_content,
        cfg=cfg,
    )
    meta = enrich_request_meta(
        result.get("meta", {}),
        run_id=run_id,
        phase=phase,
        step_id=step_id,
        partition_id="AUTH_PROBE",
        provider=provider,
        model_id=model_id,
    )
    payload = {
        "run_id": run_id,
        "phase": phase,
        "step_id": step_id,
        "provider": provider,
        "model_id": model_id,
        "endpoint_base_url": meta.get("endpoint_base_url"),
        "endpoint_effective": meta.get("endpoint_effective"),
        "gemini_endpoint_family": meta.get("gemini_endpoint_family"),
        "gemini_auth_mode_requested": meta.get("gemini_auth_mode_requested"),
        "gemini_auth_mode_effective": meta.get("gemini_auth_mode_effective"),
        "gemini_auth_attempt_sequence": meta.get("gemini_auth_attempt_sequence"),
        "sent_header_keys": meta.get("sent_header_keys"),
        "auth_present_flags": meta.get("auth_present_flags"),
        "provider_signature": meta.get("provider_signature"),
        "routing_signature": meta.get("routing_signature"),
        "status_code": meta.get("status_code"),
        "failure_type": meta.get("failure_type"),
        "provider_error_reason": meta.get("provider_error_reason"),
        "ok": bool(result.get("ok")),
        "generated_at": now_iso(),
    }
    write_json(probe_path, payload)
    update_run_manifest_probe(
        phase_dir.parent,
        phase,
        step_id,
        {
            "ok": payload["ok"],
            "status_code": payload["status_code"],
            "failure_type": payload["failure_type"],
            "provider_error_reason": payload["provider_error_reason"],
            "endpoint_effective": payload["endpoint_effective"],
            "gemini_auth_mode_effective": payload["gemini_auth_mode_effective"],
            "probe_artifact": str(probe_path),
            "updated_at": now_iso(),
        },
    )
    return payload


def _auth_failure_bucket(failure_type: Optional[str], provider_error_reason: Optional[str]) -> str:
    if not failure_type:
        return "none"
    if failure_type == "auth_expired":
        return "expired"
    if failure_type in {"auth_missing", "api_key_missing_or_invalid"}:
        return "missing_or_invalid"
    if failure_type in {"auth_rejected", "permission_denied"}:
        return "rejected"
    if "expired" in str(provider_error_reason or "").lower():
        return "expired"
    return "other"


def run_auth_doctor(root: Path, args: argparse.Namespace, cfg: RunnerConfig) -> int:
    phase = args.phase if args.phase in PHASES else "A"
    provider, model_id, api_key_env = MODEL_ROUTING.get(phase, ("gemini", DEFAULT_GEMINI_MODEL_ID, "GEMINI_API_KEY"))
    if provider != "gemini":
        provider, model_id, api_key_env = ("gemini", DEFAULT_GEMINI_MODEL_ID, "GEMINI_API_KEY")
    transport = transport_for_provider(provider, cfg)
    api_key, resolved_api_key_env = resolve_api_key(provider, api_key_env)
    if provider == "gemini" and transport == "openai_compat_http":
        modes = ["query_key", "api_key", "bearer", "both"]
    elif provider == "gemini":
        modes = ["sdk_api_key"]
    else:
        modes = ["sdk_bearer"]

    checks: List[Dict[str, Any]] = []
    for mode in modes:
        probe_cfg = cfg
        if provider == "gemini" and transport == "openai_compat_http":
            probe_cfg = replace(cfg, gemini_auth_mode=mode)
        endpoint_url = transport_endpoint_url(
            provider, model_id, probe_cfg, api_key, mode if provider == "gemini" else None
        )
        headers = make_headers(provider, api_key, probe_cfg, mode if provider == "gemini" else None)
        auth_flags = (
            build_auth_present_flags(headers, provider == "gemini" and mode == "query_key")
            if transport == "openai_compat_http"
            else sdk_auth_present_flags(provider, bool(api_key))
        )
        result = call_llm(
            provider=provider,
            model_id=model_id,
            api_key_env=api_key_env,
            system_prompt="Return exactly OK.",
            user_content="Return the single token OK.",
            cfg=probe_cfg,
        )
        meta = result.get("meta", {})
        failure_type = meta.get("failure_type")
        checks.append(
            {
                "mode": mode,
                "ok": bool(result.get("ok")),
                "transport": transport,
                "endpoint_effective": meta.get("endpoint_effective") or _sanitize_url(endpoint_url),
                "sent_header_keys": meta.get("sent_header_keys") or sorted(list(headers.keys())),
                "auth_present_flags": meta.get("auth_present_flags") or auth_flags,
                "status_code": meta.get("status_code"),
                "failure_type": failure_type,
                "provider_error_reason": meta.get("provider_error_reason"),
                "failure_bucket": _auth_failure_bucket(failure_type, meta.get("provider_error_reason")),
                "provider_signature": meta.get("provider_signature")
                or provider_signature(
                    provider,
                    model_id,
                    _sanitize_url(endpoint_url),
                    mode if provider == "gemini" else None,
                ),
                "response_received": bool(meta.get("response_received") or result.get("ok")),
                "sdk_response_summary": meta.get("response_summary"),
                "exception_type": meta.get("exception_type"),
                "exception_message_excerpt": meta.get("exception_message_excerpt"),
            }
        )

    succeeded_modes = [row["mode"] for row in checks if row["ok"]]
    failed_modes = [row["mode"] for row in checks if not row["ok"]]
    responses_received = any(row.get("response_received") for row in checks)
    canonical_endpoint = transport_endpoint_url(
        provider,
        model_id,
        cfg,
        api_key,
        cfg.gemini_auth_mode if provider == "gemini" else None,
    )
    summary = (
        f"{'PASS' if succeeded_modes else 'FAIL'} "
        f"provider={provider} transport={transport} endpoint={endpoint_effective(canonical_endpoint)} "
        f"response_received={responses_received} "
        f"succeeded_modes={','.join(succeeded_modes) if succeeded_modes else '-'} "
        f"failed_modes={','.join(failed_modes) if failed_modes else '-'}"
    )
    doctor_dir = root / V3_DOCTOR_ROOT
    doctor_dir.mkdir(parents=True, exist_ok=True)
    doctor_json = doctor_dir / "AUTH_DOCTOR.json"
    doctor_txt = doctor_dir / "AUTH_DOCTOR.txt"
    payload = {
        "generated_at": now_iso(),
        "phase": phase,
        "provider": provider,
        "model_id": model_id,
        "api_key_env_name": api_key_env,
        "api_key_env_resolved": resolved_api_key_env,
        "api_key_present": bool(api_key),
        "api_key_length": len(api_key),
        "transport": transport,
        "gemini_auth_mode_requested": cfg.gemini_auth_mode if provider == "gemini" else None,
        "modes_tested": modes,
        "checks": checks,
        "succeeded_modes": succeeded_modes,
        "failed_modes": failed_modes,
        "summary": summary,
    }
    write_json(doctor_json, payload)
    lines = [summary]
    lines.extend(
        [
            f"generated_at={payload['generated_at']}",
            f"phase={payload['phase']}",
            f"provider={payload['provider']}",
            f"model_id={payload['model_id']}",
            f"api_key_env_name={payload['api_key_env_name']}",
            f"api_key_env_resolved={payload['api_key_env_resolved']}",
            f"api_key_present={str(payload['api_key_present']).lower()}",
            f"api_key_length={payload['api_key_length']}",
            f"transport={payload['transport']}",
            f"gemini_auth_mode_requested={payload['gemini_auth_mode_requested']}",
            f"modes_tested={','.join(payload['modes_tested'])}",
            f"succeeded_modes={','.join(payload['succeeded_modes'])}",
            f"failed_modes={','.join(payload['failed_modes'])}",
        ]
    )
    doctor_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if succeeded_modes else 1


def _strip_outer_json_fence(text: str) -> str:
    no_fence = re.sub(r"^\s*```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    no_fence = re.sub(r"\s*```\s*$", "", no_fence)
    return no_fence.strip()


def _extract_first_fenced_json_block(text: str) -> Optional[str]:
    # Deterministic: first fenced block wins when multiple are present.
    match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    block = str(match.group(1)).strip()
    return block or None


def _contains_json_anchor(text: str) -> bool:
    return ("{" in text) or ("[" in text)


def _starts_with_json_token(text: str) -> bool:
    stripped = text.lstrip()
    if not stripped:
        return False
    return stripped[0] in {"{", "["}


def _is_string_literal_decode_error(exc: json.JSONDecodeError) -> bool:
    message = str(exc).lower()
    return any(snippet in message for snippet in STRING_LITERAL_ERROR_SNIPPETS)


def _is_semantic_eof_eligible(exc: json.JSONDecodeError, text: str) -> bool:
    trimmed = text.rstrip()
    if not trimmed:
        return False
    pos = int(exc.pos)
    eof_index = len(trimmed)
    return (pos >= eof_index or pos == eof_index - 1) and not _is_string_literal_decode_error(exc)


def _strict_decode_error(candidate: str) -> Optional[json.JSONDecodeError]:
    try:
        json.loads(candidate)
    except json.JSONDecodeError as exc:
        return exc
    except Exception:
        return None
    return None


def _parse_retry_reason(
    response_text: str,
    request_meta: Dict[str, Any],
    strict_decode_error: Optional[json.JSONDecodeError],
) -> Optional[str]:
    if strict_decode_error is None:
        return None
    if not _is_string_literal_decode_error(strict_decode_error):
        return None

    failure_type = str(request_meta.get("failure_type") or "").strip()
    if failure_type:
        return None
    status_code = request_meta.get("status_code")
    if isinstance(status_code, int) and status_code >= 400:
        return None
    if request_meta.get("response_received") is False:
        return None

    response_summary = request_meta.get("response_summary")
    finish_reason = ""
    if isinstance(response_summary, dict):
        finish_reason = str(response_summary.get("finish_reason") or "").upper()
    if finish_reason != "MAX_TOKENS":
        return None

    strict_candidate = response_text.strip()
    if not strict_candidate:
        return None
    trimmed = strict_candidate.rstrip()
    if not trimmed:
        return None
    pos = int(strict_decode_error.pos)
    eof_index = len(trimmed)
    if not (pos >= eof_index or pos == eof_index - 1):
        return None
    return "max_tokens_string_eof_parse_failure"


def try_repair_json_truncation(text: str, exc: Optional[json.JSONDecodeError]) -> Optional[str]:
    if not text or exc is None:
        return None
    if not _contains_json_anchor(text):
        return None
    if not _starts_with_json_token(text):
        return None

    if not _is_semantic_eof_eligible(exc, text):
        return None
    opener_for_closer = {"}": "{", "]": "["}
    closer_for_opener = {"{": "}", "[": "]"}
    stack: List[str] = []
    repaired_chars: List[str] = []
    unmatched_closer_indices: List[int] = []
    in_string = False
    escape = False

    for char in text:
        if in_string:
            repaired_chars.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            repaired_chars.append(char)
            continue

        if char in {"{", "["}:
            stack.append(char)
            repaired_chars.append(char)
            continue

        if char in {"}", "]"}:
            if stack and stack[-1] == opener_for_closer[char]:
                stack.pop()
                repaired_chars.append(char)
            else:
                repaired_chars.append(char)
                unmatched_closer_indices.append(len(repaired_chars) - 1)
            continue

        repaired_chars.append(char)

    suffix_start = len(repaired_chars)
    while suffix_start > 0 and (
        repaired_chars[suffix_start - 1].isspace() or repaired_chars[suffix_start - 1] in {"]", "}"}
    ):
        suffix_start -= 1

    if any(index < suffix_start for index in unmatched_closer_indices):
        return None

    drop_indices = set(unmatched_closer_indices)
    balanced_chars = [char for idx, char in enumerate(repaired_chars) if idx not in drop_indices]

    while stack:
        opener = stack.pop()
        balanced_chars.append(closer_for_opener[opener])

    repaired = "".join(balanced_chars)
    if repaired == text:
        return None
    return repaired


def parse_json_from_response(text: str) -> Optional[Any]:
    if not text:
        return None

    stripped = text.strip()
    if not stripped:
        return None

    repair_candidates: List[Tuple[str, json.JSONDecodeError]] = []
    seen_candidates: Set[str] = set()

    # 1) strict parse
    try:
        return json.loads(stripped)
    except json.JSONDecodeError as exc:
        repair_candidates.append((stripped, exc))
        seen_candidates.add(stripped)
    except Exception:
        pass

    # 2) defenced parse
    defenced = _strip_outer_json_fence(stripped)
    if defenced and defenced not in seen_candidates:
        try:
            return json.loads(defenced)
        except json.JSONDecodeError as exc:
            repair_candidates.append((defenced, exc))
            seen_candidates.add(defenced)
        except Exception:
            pass

    # 3) first fenced block only
    fenced_block = _extract_first_fenced_json_block(stripped)
    if fenced_block and fenced_block not in seen_candidates:
        try:
            return json.loads(fenced_block)
        except json.JSONDecodeError as exc:
            repair_candidates.append((fenced_block, exc))
            seen_candidates.add(fenced_block)
        except Exception:
            pass

    # 4) balanced repair parse (semantic EOF eligible only)
    for candidate, decode_error in repair_candidates:
        if not _is_semantic_eof_eligible(decode_error, candidate):
            continue
        repaired = try_repair_json_truncation(candidate, decode_error)
        if not repaired:
            continue
        try:
            return json.loads(repaired)
        except Exception:
            continue

    # 5) fail closed
    return None


def build_partition_context(
    phase: str,
    partition_paths: List[str],
    file_truncate_chars: int,
    home_scan_mode: str,
    max_files: int,
    max_chars: int,
) -> Tuple[str, Dict[str, int]]:
    chunks: List[str] = []
    redaction_hits = 0
    skipped_files = 0
    context_bytes = 0

    for path_str in partition_paths:
        if len(chunks) >= max_files:
            skipped_files += 1
            continue

        path = Path(path_str)
        content = safe_read(path)
        if len(content) > file_truncate_chars:
            content = content[:file_truncate_chars] + "\n...[TRUNCATED]..."
        if phase == "H" and home_scan_mode == "safe":
            content, hits = redact_sensitive_lines(content)
            redaction_hits += hits
        chunk_text = f"--- FILE: {path} ---\n{content}\n"
        chunk_bytes = len(chunk_text.encode("utf-8"))

        if chunks and (context_bytes + chunk_bytes > max_chars):
            skipped_files += 1
            continue

        if not chunks and chunk_bytes > max_chars:
            chunk_text = chunk_text.encode("utf-8")[:max_chars].decode("utf-8", errors="ignore")
            chunk_text += "\n...[CONTEXT_TRUNCATED_FOR_LIMIT]...\n"
            chunk_bytes = len(chunk_text.encode("utf-8"))

        chunks.append(chunk_text)
        context_bytes += chunk_bytes

    context = "\n".join(chunks)
    stats = {
        "files_total": len(partition_paths),
        "files_included": len(chunks),
        "files_skipped": skipped_files,
        "context_bytes": len(context.encode("utf-8")),
        "redaction_hits": redaction_hits,
    }
    return context, stats


def build_output_envelope_instructions(output_artifacts: Tuple[str, ...]) -> str:
    expected = "\n".join(f"- {artifact}" for artifact in output_artifacts)
    return (
        "Hard rules:\n"
        "- Output MUST be a single JSON value (object or array) and nothing else.\n"
        "- No markdown, prose, code fences, comments, or trailing commentary.\n"
        "- The first non-whitespace character MUST be { or [.\n"
        "- The last non-whitespace character MUST be } or ].\n"
        "- Do not emit multiple JSON objects.\n"
        "- Do not emit trailing commas.\n"
        "- Keep output UTF-8 plain text; no null bytes and no emoji.\n"
        "- Escape internal string quotes and avoid unescaped control characters.\n"
        "- Do not include unescaped newlines inside string values.\n"
        "Return JSON only with this exact envelope:\n"
        '{"artifacts":[{"artifact_name":"<exact artifact name>","payload":<json object|json array|markdown string>}]}'
        "\nConstraints:\n"
        "- artifact_name must exactly match one expected artifact.\n"
        "- For *.json artifacts, payload must be valid JSON (object or array).\n"
        "- For *.md artifacts, payload must be markdown text.\n"
        "- For *.partX.json artifacts, keep .partX in artifact_name exactly.\n"
        "- Do not emit any extra artifact names.\n"
        "Self-validation before finishing:\n"
        "- Ensure output is valid JSON.\n"
        "- If unsure, shorten values but keep structure valid.\n"
        "- Never emit invalid JSON.\n"
        "Expected artifacts:\n"
        f"{expected}\n"
    )


def coerce_artifacts_from_response(
    parsed: Optional[Any],
    raw_text: str,
    expected_artifacts: Tuple[str, ...],
) -> List[Dict[str, Any]]:
    expected_set = set(expected_artifacts)

    if isinstance(parsed, list):
        list_artifacts: List[Dict[str, Any]] = []
        for entry in parsed:
            if not isinstance(entry, dict):
                continue
            artifact_name_value = entry.get("artifact_name")
            if not isinstance(artifact_name_value, str):
                continue
            artifact_name = artifact_name_value.strip()
            if artifact_name not in expected_set:
                continue
            if "payload" not in entry:
                continue
            list_artifacts.append({"artifact_name": artifact_name, "payload": entry.get("payload")})
        if list_artifacts:
            return list_artifacts

    if isinstance(parsed, dict) and isinstance(parsed.get("artifacts"), list):
        artifacts: List[Dict[str, Any]] = []
        for entry in parsed["artifacts"]:
            if not isinstance(entry, dict):
                continue
            artifact_name = str(entry.get("artifact_name", "")).strip()
            if artifact_name not in expected_set:
                continue
            artifacts.append({"artifact_name": artifact_name, "payload": entry.get("payload")})
        if artifacts:
            return artifacts

    if isinstance(parsed, dict):
        keyed_artifacts: List[Dict[str, Any]] = []
        for artifact_name in expected_artifacts:
            if artifact_name in parsed:
                keyed_artifacts.append({"artifact_name": artifact_name, "payload": parsed[artifact_name]})
        if keyed_artifacts:
            return keyed_artifacts

    if len(expected_artifacts) == 1:
        artifact_name = expected_artifacts[0]
        if parsed is not None:
            return [{"artifact_name": artifact_name, "payload": parsed}]
        if artifact_name.endswith(".md"):
            return [{"artifact_name": artifact_name, "payload": raw_text}]

    return []


def artifacts_pass_schema_gate(
    artifacts: List[Dict[str, Any]],
    expected_artifact_names: Tuple[str, ...],
) -> Tuple[bool, Optional[str]]:
    expected = set(expected_artifact_names)
    observed = {
        str(row.get("artifact_name", "")).strip()
        for row in artifacts
        if isinstance(row, dict) and str(row.get("artifact_name", "")).strip()
    }
    missing = sorted(expected - observed)
    if missing:
        return False, f"missing_expected_artifacts:{','.join(missing)}"

    for row in artifacts:
        if not isinstance(row, dict):
            continue
        payload = row.get("payload")
        if isinstance(payload, dict):
            items = payload.get("items")
            if isinstance(items, list):
                for item in items:
                    if not isinstance(item, dict):
                        return False, "schema_item_not_object"
                    for key in ("id", "path", "line_range"):
                        if key not in item:
                            return False, f"schema_missing_key:{key}"
                        value = item.get(key)
                        if value in (None, "", []):
                            return False, f"schema_empty_key:{key}"
    return True, None


def should_escalate_for_failure_type(failure_type: Optional[str]) -> bool:
    token = str(failure_type or "").strip()
    if not token:
        return False
    if token.startswith("auth_"):
        return True
    return token in {
        "api_key_missing_or_invalid",
        "permission_denied",
        "quota_or_billing",
        "provider",
        "network",
        "timeout",
        "payload_unshrinkable",
    }


def build_batch_client(
    provider: str,
    api_key: str,
    cfg: RunnerConfig,
) -> BatchClient:
    if provider == "openai":
        return OpenAIBatchClient(api_key=api_key)
    if provider == "gemini":
        return GeminiBatchClient(api_key=api_key)
    if provider == "xai":
        return XAIBatchClient(api_key=api_key, base_url=llm_base_url(provider, cfg))
    raise RuntimeError(f"Unsupported batch provider: {provider}")


def validate_success_partition_output(
    success_json_path: Path,
    phase: str,
    step_id: str,
    partition_id: str,
    expected_artifact_names: Tuple[str, ...],
) -> Tuple[bool, str]:
    if not success_json_path.exists():
        return False, "missing_success_json"
    try:
        if success_json_path.stat().st_size <= 0:
            return False, "empty_success_json"
    except Exception as exc:
        return False, f"success_stat_error:{type(exc).__name__}"

    raw_text = safe_read(success_json_path)
    if not raw_text.strip():
        return False, "empty_success_json"

    try:
        payload = json.loads(raw_text)
    except Exception:
        return False, "invalid_success_json"

    if not isinstance(payload, dict):
        return False, "success_not_object"

    def _identity_mismatch(obj: Dict[str, Any], prefix: str) -> Optional[str]:
        expected_identity = {
            "phase": phase,
            "step_id": step_id,
            "partition_id": partition_id,
        }
        for key, expected_value in expected_identity.items():
            if key not in obj:
                continue
            actual = obj.get(key)
            if actual in (None, "", []):
                continue
            if str(actual) != str(expected_value):
                return f"{prefix}_{key}_mismatch"
        return None

    if payload.get("failure_type"):
        return False, "failure_type_top_level"
    request_meta = payload.get("request_meta")
    if isinstance(request_meta, dict) and request_meta.get("failure_type"):
        return False, "failure_type_request_meta"

    top_level_mismatch = _identity_mismatch(payload, "top_level")
    if top_level_mismatch:
        return False, top_level_mismatch

    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, list):
        return False, "artifacts_missing_or_not_list"

    expected_set = set(expected_artifact_names)
    has_expected_artifact = False
    for idx, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            return False, f"artifact_{idx}_not_object"
        artifact_name = str(artifact.get("artifact_name", "")).strip()
        if not artifact_name:
            return False, f"artifact_{idx}_artifact_name_missing"
        if "payload" not in artifact:
            return False, f"artifact_{idx}_payload_missing"
        if artifact_name in expected_set:
            has_expected_artifact = True
        artifact_payload = artifact.get("payload")
        if isinstance(artifact_payload, dict):
            payload_mismatch = _identity_mismatch(artifact_payload, f"artifact_{idx}_payload")
            if payload_mismatch:
                return False, payload_mismatch

    if not has_expected_artifact:
        return False, "no_expected_artifacts"

    schema_ok, schema_reason = artifacts_pass_schema_gate(artifacts, expected_artifact_names)
    if not schema_ok:
        return False, f"invalid_schema:{schema_reason}"

    return True, "valid_success"


def list_failed_sidecars(raw_dir: Path, step_id: str, partition_id: str) -> List[Path]:
    pattern = f"{step_id}__{partition_id}.FAILED.*"
    failed_paths = [path for path in raw_dir.glob(pattern) if path.is_file()]
    return sorted(failed_paths, key=lambda path: path.name)


def schedule_prune_failed_sidecars(
    write_ops: List[Dict[str, Any]],
    paths: List[Path],
    reason: str,
) -> int:
    unique_paths = sorted({str(path) for path in paths})
    for path in unique_paths:
        write_ops.append({"kind": "unlink_if_exists", "path": path, "reason": reason})
    return len(unique_paths)


def compute_resume_decision(
    success_json_path: Path,
    raw_dir: Path,
    phase: str,
    step_id: str,
    partition_id: str,
    expected_artifact_names: Tuple[str, ...],
) -> Dict[str, Any]:
    failed_paths = list_failed_sidecars(raw_dir, step_id, partition_id)
    failed_mtimes: List[float] = []
    for path in failed_paths:
        try:
            failed_mtimes.append(float(path.stat().st_mtime))
        except Exception:
            continue
    newest_failed_mtime = max(failed_mtimes) if failed_mtimes else None

    is_valid_success, validation_reason = validate_success_partition_output(
        success_json_path=success_json_path,
        phase=phase,
        step_id=step_id,
        partition_id=partition_id,
        expected_artifact_names=expected_artifact_names,
    )
    if not is_valid_success:
        return {
            "action": "RERUN",
            "prune_failed": False,
            "reason": "missing_or_invalid_success",
            "validation_reason": validation_reason,
            "failed_paths": failed_paths,
            "success_mtime": None,
            "failed_mtime": newest_failed_mtime,
        }

    try:
        success_mtime = float(success_json_path.stat().st_mtime)
    except Exception as exc:
        return {
            "action": "RERUN",
            "prune_failed": False,
            "reason": "missing_or_invalid_success",
            "validation_reason": f"success_mtime_error:{type(exc).__name__}",
            "failed_paths": failed_paths,
            "success_mtime": None,
            "failed_mtime": newest_failed_mtime,
        }

    if newest_failed_mtime is None:
        return {
            "action": "SKIP",
            "prune_failed": False,
            "reason": "valid_success",
            "validation_reason": validation_reason,
            "failed_paths": failed_paths,
            "success_mtime": success_mtime,
            "failed_mtime": None,
        }

    if success_mtime >= newest_failed_mtime:
        return {
            "action": "SKIP",
            "prune_failed": True,
            "reason": "valid_success_stale_failed",
            "validation_reason": validation_reason,
            "failed_paths": failed_paths,
            "success_mtime": success_mtime,
            "failed_mtime": newest_failed_mtime,
        }

    return {
        "action": "RERUN",
        "prune_failed": False,
        "reason": "failed_newer_than_success",
        "validation_reason": validation_reason,
        "failed_paths": failed_paths,
        "success_mtime": success_mtime,
        "failed_mtime": newest_failed_mtime,
    }


def execute_step_for_partitions(
    phase: str,
    prompt_spec: PromptSpec,
    partitions: List[Dict[str, Any]],
    phase_dir: Path,
    cfg: RunnerConfig,
    ui: Optional[UI] = None,
) -> Dict[str, int]:
    step_id = prompt_spec.step_id
    prompt_path = prompt_spec.prompt_path
    output_artifacts = prompt_spec.output_artifacts
    prompt_text = safe_read(prompt_path)
    if not prompt_text:
        logger.error("Could not read prompt: %s", prompt_path)
        return {
            "partitions_total": len(partitions),
            "resume_skipped": 0,
            "recomputed": 0,
            "dry_run": 0,
            "ok": 0,
            "failed": len(partitions),
            "auth_failures": 0,
        }

    raw_dir = phase_dir / "raw"
    route_info = resolve_effective_step_route(phase, step_id, cfg)
    step_tier = str(route_info["step_tier"])
    step_type = str(route_info["step_type"])
    step_ladder = [tuple(route) for route in route_info["ladder"]]
    initial_provider = str(route_info["provider"])
    initial_model_id = str(route_info["model_id"])
    initial_api_key_env = str(route_info["api_key_env"])
    routing_reason = str(route_info["reason"])
    provider, model_id, _ = initial_provider, initial_model_id, initial_api_key_env
    endpoint_base = llm_base_url(initial_provider, cfg)
    transport = transport_for_provider(initial_provider, cfg)
    force_json_output = initial_provider == "gemini"
    max_files = max_files_for_phase(phase, cfg)
    run_id = phase_dir.parent.name
    if routing_reason == "env_step_type_override":
        logger.info(
            "ROUTE phase=%s step=%s type=%s model=%s/%s reason=%s",
            phase,
            step_id,
            step_type,
            initial_provider,
            initial_model_id,
            routing_reason,
        )
        write_phase_routing_log(
            phase_dir,
            phase=phase,
            step_id=step_id,
            step_type=step_type,
            provider=initial_provider,
            model_id=initial_model_id,
            reason=routing_reason,
        )
    logger.info(
        "Step %s using prompt %s outputs=%s",
        step_id,
        prompt_path.name,
        list(output_artifacts),
    )
    if ui is not None:
        ui.step_start(
            phase=phase,
            step_id=step_id,
            prompt_path=prompt_path,
            outputs=output_artifacts,
            partitions_total=len(partitions),
            provider=initial_provider,
            model_id=initial_model_id,
            step_tier=step_tier,
            routing_policy=cfg.routing_policy,
        )
    resume_skipped = 0
    step_success_count = 0
    step_auth_failures = 0
    step_failed_count = 0
    step_recomputed_count = 0
    step_dry_run_count = 0
    step_retry_count = 0
    step_escalated_partitions = 0
    step_hop_distribution: Counter[str] = Counter()
    step_execution_mode_counts: Counter[str] = Counter()
    step_final_route_counts: Counter[str] = Counter()
    batch_request_rows: List[Dict[str, Any]] = []
    batch_job_rows: List[Dict[str, Any]] = []
    batch_result_rows: List[Dict[str, Any]] = []
    started_at = time.time()
    workers = max(1, min(16, int(cfg.partition_workers)))
    ui_completed = 0
    ui_ok = 0
    ui_failed = 0
    ui_skipped = 0
    ui_retried = 0

    def _append_log(logs: List[Tuple[str, str]], level: str, message: str) -> None:
        logs.append((level, message))

    def _op_write_text(write_ops: List[Dict[str, Any]], path: Path, text: str) -> None:
        write_ops.append({"kind": "write_text", "path": str(path), "text": text})

    def _op_write_json(write_ops: List[Dict[str, Any]], path: Path, payload: Dict[str, Any]) -> None:
        write_ops.append({"kind": "write_json", "path": str(path), "payload": payload})

    def _op_unlink_if_exists(write_ops: List[Dict[str, Any]], path: Path) -> None:
        write_ops.append({"kind": "unlink_if_exists", "path": str(path)})

    def _apply_write_ops(write_ops: List[Dict[str, Any]]) -> None:
        for op in write_ops:
            op_path = Path(str(op["path"]))
            if op["kind"] == "write_text":
                op_path.write_text(str(op["text"]), encoding="utf-8")
            elif op["kind"] == "write_json":
                payload = op["payload"] if isinstance(op["payload"], dict) else {}
                write_json(op_path, payload)
            elif op["kind"] == "unlink_if_exists":
                if op_path.exists():
                    op_path.unlink()

    def _ui_record_result(result: PartitionExecResult) -> None:
        nonlocal ui_completed, ui_ok, ui_failed, ui_skipped, ui_retried
        if ui is None:
            return
        ui_completed += 1
        if result.success:
            ui_ok += 1
        ui_failed += int(result.failed_delta)
        if result.resume_skipped:
            ui_skipped += 1
        retry_trace = result.request_meta.get("retry_trace")
        if isinstance(retry_trace, list):
            ui_retried += max(0, len(retry_trace) - 1)
        ui.partition_result(
            phase=phase,
            step_id=step_id,
            completed=ui_completed,
            total=len(partitions),
            ok=ui_ok,
            failed=ui_failed,
            skipped=ui_skipped,
            retried=ui_retried,
        )

    def _worker_exception_result(
        partition_id: str,
        out_json: Path,
        out_failed: Path,
        out_failed_json: Path,
        exc: Exception,
    ) -> PartitionExecResult:
        logs: List[Tuple[str, str]] = []
        write_ops: List[Dict[str, Any]] = []
        error_message = sanitize_error_text(str(exc)) or type(exc).__name__
        failure_meta = enrich_request_meta(
            {
                "provider": provider,
                "model_id": model_id,
                "endpoint_base_url": endpoint_base,
                "status_code": None,
                "failure_type": "worker_exception",
                "provider_error_reason": error_message[:300],
                "transport": transport,
                **capture_exception_metadata(exc),
            },
            run_id=run_id,
            phase=phase,
            step_id=step_id,
            partition_id=partition_id,
            provider=provider,
            model_id=model_id,
        )
        failure_meta["routing_tier"] = step_tier
        failure_meta["routing_policy"] = cfg.routing_policy
        failure_meta["route_hop_index"] = 1
        failure_meta["route_hop_total"] = 1
        failure_meta["route_attempts"] = []
        failure_meta["escalation_trigger"] = None
        failure_meta["execution_mode"] = "sync"
        _append_log(logs, "error", f"Worker exception for {step_id} {partition_id}: {error_message[:300]}")
        _op_write_text(write_ops, out_failed, f"worker_exception: {error_message}\n")
        _op_write_json(
            write_ops,
            out_failed_json,
            {
                "phase": phase,
                "step_id": step_id,
                "partition_id": partition_id,
                "generated_at": now_iso(),
                "failure_type": "worker_exception",
                "status_code": None,
                "request_meta": failure_meta,
            },
        )
        _op_write_json(
            write_ops,
            out_json,
            {
                "phase": phase,
                "step_id": step_id,
                "partition_id": partition_id,
                "generated_at": now_iso(),
                "artifacts": [],
                "request_meta": failure_meta,
            },
        )
        return PartitionExecResult(
            partition_id=partition_id,
            write_ops=write_ops,
            logs=logs,
            request_meta=failure_meta,
            artifacts=[],
            success=False,
            resume_skipped=False,
            auth_failure=is_auth_classified_failure(failure_meta.get("failure_type")),
            auth_expired=is_auth_expired_failure(failure_meta.get("failure_type")),
            recomputed_delta=1,
            dry_run_delta=0,
            failed_delta=1,
        )

    def _run_one_partition(partition: Dict[str, Any]) -> PartitionExecResult:
        partition_id = str(partition["id"])
        out_json = raw_dir / f"{step_id}__{partition_id}.json"
        out_failed = raw_dir / f"{step_id}__{partition_id}.FAILED.txt"
        out_failed_json = raw_dir / f"{step_id}__{partition_id}.FAILED.json"
        out_trace = raw_dir / f"{step_id}__{partition_id}.TRACE.md"
        logs: List[Tuple[str, str]] = []
        write_ops: List[Dict[str, Any]] = []

        if cfg.resume:
            decision = compute_resume_decision(
                success_json_path=out_json,
                raw_dir=raw_dir,
                phase=phase,
                step_id=step_id,
                partition_id=partition_id,
                expected_artifact_names=output_artifacts,
            )
            if decision["action"] == "SKIP":
                _append_log(logs, "info", f"Resume: skip valid success for {step_id} {partition_id}")
                if decision.get("prune_failed"):
                    prune_count = schedule_prune_failed_sidecars(
                        write_ops=write_ops,
                        paths=[path for path in decision.get("failed_paths", []) if isinstance(path, Path)],
                        reason="skip",
                    )
                    if prune_count > 0:
                        _append_log(
                            logs,
                            "info",
                            (
                                f"Resume: prune stale FAILED on skip for {step_id} "
                                f"{partition_id} count={prune_count}"
                            ),
                        )
                return PartitionExecResult(
                    partition_id=partition_id,
                    write_ops=write_ops,
                    logs=logs,
                    request_meta={},
                    artifacts=[],
                    success=False,
                    resume_skipped=True,
                    auth_failure=False,
                    auth_expired=False,
                    recomputed_delta=0,
                    dry_run_delta=0,
                    failed_delta=0,
                )
            if decision["reason"] == "failed_newer_than_success":
                _append_log(
                    logs,
                    "info",
                    f"Resume: rerun failed_newer_than_success for {step_id} {partition_id}",
                )
            else:
                _append_log(
                    logs,
                    "info",
                    (
                        f"Resume: rerun missing_or_invalid_success for {step_id} {partition_id} "
                        f"reason={decision.get('validation_reason')}"
                    ),
                )

        output_instructions = build_output_envelope_instructions(output_artifacts)
        prompt_prefix = (
            "Extract from the files below.\n"
            f"{output_instructions}\n"
            "\nFILES:\n"
        )
        reserved_chars = len(prompt_prefix)
        context_budget = max(cfg.max_chars - reserved_chars, 2048)
        current_budget = context_budget
        payload_bytes = 0
        user_prompt = ""
        context = ""
        context_stats: Dict[str, int] = {}
        system_prompt_bytes = len(prompt_text.encode("utf-8"))

        while True:
            context, context_stats = build_partition_context(
                phase=phase,
                partition_paths=partition["paths"],
                file_truncate_chars=cfg.file_truncate_chars,
                home_scan_mode=cfg.home_scan_mode,
                max_files=max_files,
                max_chars=current_budget,
            )
            user_prompt = f"{prompt_prefix}{context}"
            payload = build_chat_payload(
                provider,
                model_id,
                prompt_text,
                user_prompt,
                force_json_output=force_json_output,
            )
            payload_body = serialize_payload_body(payload)
            payload_bytes = measure_payload_bytes_from_body(payload_body)
            if payload_bytes <= cfg.max_request_bytes:
                break
            if current_budget <= 1024:
                break
            next_budget = max(1024, int(current_budget * 0.7))
            if next_budget == current_budget:
                next_budget = current_budget - 1
            current_budget = max(next_budget, 1024)

        if payload_bytes > cfg.max_request_bytes:
            over_by = payload_bytes - cfg.max_request_bytes
            gemini_sequence = _gemini_auth_mode_sequence(cfg.gemini_auth_mode, endpoint_base)
            endpoint_url = transport_endpoint_url(provider, model_id, cfg, "REDACTED", gemini_sequence[0])
            failure_meta = {
                "provider": provider,
                "model_id": model_id,
                "endpoint_base_url": endpoint_base,
                "endpoint_effective": endpoint_effective(endpoint_url),
                **endpoint_fingerprint(endpoint_url),
                "status_code": None,
                "failure_type": "payload_unshrinkable",
                "request_payload_bytes": payload_bytes,
                "request_payload_bytes_mode": "sdk_estimate" if transport != "openai_compat_http" else "exact_http",
                "max_request_bytes": cfg.max_request_bytes,
                "over_by_bytes": over_by,
                "gemini_auth_mode_requested": cfg.gemini_auth_mode if provider == "gemini" else None,
                "gemini_auth_mode_effective": gemini_sequence[0] if provider == "gemini" else None,
                "provider_signature": provider_signature(
                    provider,
                    model_id,
                    endpoint_url,
                    gemini_sequence[0] if provider == "gemini" else None,
                ),
                "provider_error_reason": None,
                "gemini_endpoint_family": "openai_compat"
                if provider == "gemini" and _is_gemini_openai_compat_endpoint(endpoint_base)
                else ("native" if provider == "gemini" else None),
                "gemini_auth_attempt_sequence": _gemini_auth_mode_sequence(cfg.gemini_auth_mode, endpoint_base)
                if provider == "gemini"
                else None,
                "transport": transport,
                "structured_output": {
                    "enabled": bool(force_json_output),
                    "mime_type": "application/json" if force_json_output else None,
                    "schema": None,
                },
                "system_prompt_bytes": system_prompt_bytes,
                "user_content_bytes": len(user_prompt.encode("utf-8")),
                "context_bytes_estimate": context_stats.get("context_bytes", 0),
            }
            failure_meta = enrich_request_meta(
                failure_meta,
                run_id=run_id,
                phase=phase,
                step_id=step_id,
                partition_id=partition_id,
                provider=provider,
                model_id=model_id,
            )
            failure_meta["routing_tier"] = step_tier
            failure_meta["routing_policy"] = cfg.routing_policy
            failure_meta["route_hop_index"] = 1
            failure_meta["route_hop_total"] = 1
            failure_meta["route_attempts"] = []
            failure_meta["escalation_trigger"] = "payload_unshrinkable"
            failure_meta["execution_mode"] = "batch" if cfg.batch_mode else "sync"
            failure_meta["batch_provider"] = cfg.batch_provider if cfg.batch_mode else None
            failure_meta["batch_job_id"] = None
            _append_log(
                logs,
                "error",
                (
                    f"Payload over hard cap for {step_id} {partition_id}: "
                    f"payload_bytes={payload_bytes} max_request_bytes={cfg.max_request_bytes}"
                ),
            )
            _op_write_text(
                write_ops,
                out_failed,
                f"payload_unshrinkable: payload_bytes={payload_bytes} max_request_bytes={cfg.max_request_bytes}\n",
            )
            _op_write_json(write_ops, out_failed_json, failure_meta)
            _op_write_json(
                write_ops,
                out_json,
                {
                    "phase": phase,
                    "step_id": step_id,
                    "partition_id": partition_id,
                    "generated_at": now_iso(),
                    "artifacts": [],
                    "request_meta": failure_meta,
                },
            )
            return PartitionExecResult(
                partition_id=partition_id,
                write_ops=write_ops,
                logs=logs,
                request_meta=failure_meta,
                artifacts=[],
                success=False,
                resume_skipped=False,
                auth_failure=False,
                auth_expired=False,
                recomputed_delta=1,
                dry_run_delta=0,
                failed_delta=1,
            )

        if cfg.dry_run:
            _append_log(
                logs,
                "info",
                (
                    f"Dry-run {step_id} {partition_id} files={context_stats['files_included']} "
                    f"request_payload_bytes={payload_bytes} redaction_hits={context_stats['redaction_hits']} "
                    f"max_request_bytes={cfg.max_request_bytes}"
                ),
            )
            gemini_sequence = _gemini_auth_mode_sequence(cfg.gemini_auth_mode, endpoint_base)
            dry_mode = gemini_sequence[0] if provider == "gemini" else None
            endpoint_url = transport_endpoint_url(provider, model_id, cfg, "REDACTED", dry_mode)
            dry_headers = make_headers(provider, "REDACTED", cfg, dry_mode) if transport == "openai_compat_http" else {}
            dry_auth_flags = (
                build_auth_present_flags(dry_headers, provider == "gemini" and dry_mode == "query_key")
                if transport == "openai_compat_http"
                else sdk_auth_present_flags(provider, True)
            )
            trace_text = (
                f"# PROMPT_FILE\n{prompt_path}\n\n# SYSTEM_PROMPT\n{prompt_text}\n\n"
                f"# PARTITION_ID\n{partition_id}\n\n# USER_CONTEXT_PREVIEW\n{context[:2000]}"
            )
            dry_meta = {
                "provider": provider,
                "model_id": model_id,
                "endpoint_base_url": endpoint_base,
                "endpoint_effective": endpoint_effective(endpoint_url),
                **endpoint_fingerprint(endpoint_url),
                "status_code": None,
                "failure_type": None,
                "request_payload_bytes": payload_bytes,
                "request_payload_bytes_mode": "sdk_estimate" if transport != "openai_compat_http" else "exact_http",
                "gemini_auth_mode_requested": cfg.gemini_auth_mode if provider == "gemini" else None,
                "gemini_auth_mode_effective": dry_mode,
                "gemini_auth_attempt_sequence": gemini_sequence if provider == "gemini" else None,
                "provider_signature": provider_signature(
                    provider,
                    model_id,
                    endpoint_url,
                    dry_mode if provider == "gemini" else None,
                ),
                "provider_error_reason": None,
                "gemini_endpoint_family": "openai_compat"
                if provider == "gemini" and _is_gemini_openai_compat_endpoint(endpoint_base)
                else ("native" if provider == "gemini" else None),
                "sent_header_keys": sorted(list(dry_headers.keys())),
                "auth_present_flags": dry_auth_flags,
                "transport": transport,
                "structured_output": {
                    "enabled": bool(force_json_output),
                    "mime_type": "application/json" if force_json_output else None,
                    "schema": None,
                },
            }
            dry_meta = enrich_request_meta(
                dry_meta,
                run_id=run_id,
                phase=phase,
                step_id=step_id,
                partition_id=partition_id,
                provider=provider,
                model_id=model_id,
            )
            dry_meta["routing_tier"] = step_tier
            dry_meta["routing_policy"] = cfg.routing_policy
            dry_meta["route_hop_index"] = 1
            dry_meta["route_hop_total"] = 1
            dry_meta["route_attempts"] = []
            dry_meta["escalation_trigger"] = None
            dry_meta["execution_mode"] = "sync"
            dry_meta["batch_provider"] = None
            dry_meta["batch_job_id"] = None
            _op_write_text(write_ops, out_trace, trace_text)
            _op_write_json(
                write_ops,
                out_json,
                {
                    "phase": phase,
                    "step_id": step_id,
                    "partition_id": partition_id,
                    "generated_at": now_iso(),
                    "artifacts": [
                        {
                            "artifact_name": artifact_name,
                            "payload": ([] if artifact_name.endswith(".json") else ""),
                        }
                        for artifact_name in output_artifacts
                    ],
                    "dry_run": True,
                    "request_meta": dry_meta,
                },
            )
            _op_unlink_if_exists(write_ops, out_failed)
            _op_unlink_if_exists(write_ops, out_failed_json)
            return PartitionExecResult(
                partition_id=partition_id,
                write_ops=write_ops,
                logs=logs,
                request_meta=dry_meta,
                artifacts=[],
                success=False,
                resume_skipped=False,
                auth_failure=False,
                auth_expired=False,
                recomputed_delta=1,
                dry_run_delta=1,
                failed_delta=0,
            )

        _append_log(
            logs,
            "info",
            (
                f"Executing {step_id} partition {partition_id} using provider={provider} model={model_id} "
                f"files={context_stats['files_included']} skipped={context_stats['files_skipped']} "
                f"context_bytes={context_stats['context_bytes']}"
            ),
        )
        def _route_attempt(route: Tuple[str, str, str], hop_index: int) -> Dict[str, Any]:
            route_provider, route_model_id, route_api_key_env = route
            route_force_json = route_provider == "gemini"

            def _execute_llm_call() -> Tuple[str, Dict[str, Any]]:
                if cfg.batch_mode:
                    batch_provider = cfg.batch_provider if cfg.batch_provider != "auto" else route_provider
                    selected_route = (route_provider, route_model_id, route_api_key_env)
                    if batch_provider != route_provider:
                        for candidate in step_ladder:
                            if candidate[0] == batch_provider:
                                selected_route = candidate
                                break
                    batch_provider, batch_model_id, batch_api_key_env = selected_route
                    batch_api_key, _ = resolve_api_key(batch_provider, batch_api_key_env)
                    if not batch_api_key:
                        failed_meta = {
                            "provider": batch_provider,
                            "model_id": batch_model_id,
                            "failure_type": "auth_missing",
                            "provider_error_reason": f"missing_api_key:{batch_api_key_env}",
                            "execution_mode": "batch",
                            "batch_provider": batch_provider,
                            "batch_job_id": None,
                        }
                        return "", enrich_request_meta(
                            failed_meta,
                            run_id=run_id,
                            phase=phase,
                            step_id=step_id,
                            partition_id=partition_id,
                            provider=batch_provider,
                            model_id=batch_model_id,
                        )
                    batch_client = build_batch_client(batch_provider, batch_api_key, cfg)
                    batch_requests = [
                        BatchRequest(
                            custom_id=partition_id,
                            model_id=batch_model_id,
                            system_prompt=prompt_text,
                            user_content=user_prompt,
                            force_json_output=(batch_provider == "gemini"),
                            metadata={
                                "phase": phase,
                                "step_id": step_id,
                                "partition_id": partition_id,
                            },
                        )
                    ]
                    batch_request_rows.append(
                        {
                            "partition_id": partition_id,
                            "provider": batch_provider,
                            "model_id": batch_model_id,
                            "routing_policy": cfg.routing_policy,
                            "routing_tier": step_tier,
                        }
                    )
                    step_context = {
                        "run_id": run_id,
                        "phase": phase,
                        "step_id": step_id,
                        "partition_id": partition_id,
                    }
                    if ui is not None:
                        ui.batch_event(
                            phase=phase,
                            step_id=step_id,
                            status="submit",
                            provider=batch_provider,
                            details=f"partition={partition_id} requests=1",
                        )
                    try:
                        batch_job_id = batch_client.submit(batch_requests, BatchRoute(*selected_route), step_context)
                        job_row = {
                            "run_id": run_id,
                            "phase_id": phase,
                            "step_id": step_id,
                            "partition_id": partition_id,
                            "provider_id": batch_provider,
                            "model_id": batch_model_id,
                            "api_key_env": batch_api_key_env,
                            "job_id": batch_job_id,
                            "state": "submitted",
                            "submitted_at_utc": now_iso(),
                        }
                        batch_job_rows.append(job_row)
                    except Exception as exc:
                        failed_meta = {
                            "provider": batch_provider,
                            "model_id": batch_model_id,
                            "failure_type": "provider",
                            "provider_error_reason": f"batch_submit_error:{type(exc).__name__}",
                            "execution_mode": "batch",
                            "batch_provider": batch_provider,
                            "batch_job_id": None,
                            **capture_exception_metadata(exc),
                        }
                        return "", enrich_request_meta(
                            failed_meta,
                            run_id=run_id,
                            phase=phase,
                            step_id=step_id,
                            partition_id=partition_id,
                            provider=batch_provider,
                            model_id=batch_model_id,
                        )
                    if cfg.batch_submit_only:
                        submit_payload = {
                            "artifacts": [
                                {
                                    "artifact_name": artifact_name,
                                    "payload": {
                                        "batch_status": "submitted",
                                        "batch_job_id": batch_job_id,
                                        "partition_id": partition_id,
                                    },
                                }
                                for artifact_name in output_artifacts
                            ]
                        }
                        meta = {
                            "provider": batch_provider,
                            "model_id": batch_model_id,
                            "status_code": 202,
                            "failure_type": None,
                            "provider_error_reason": None,
                            "execution_mode": "batch_submit_only",
                            "batch_provider": batch_provider,
                            "batch_job_id": batch_job_id,
                            "response_summary": {"batch_status": "submitted"},
                            "batch_pending": True,
                        }
                        return json.dumps(submit_payload, ensure_ascii=True, sort_keys=True), enrich_request_meta(
                            meta,
                            run_id=run_id,
                            phase=phase,
                            step_id=step_id,
                            partition_id=partition_id,
                            provider=batch_provider,
                            model_id=batch_model_id,
                        )
                    started_poll = time.time()
                    terminal_states = {"completed", "succeeded", "done", "failed", "cancelled", "canceled"}
                    status = ""
                    while True:
                        status = str(batch_client.poll(batch_job_id) or "").lower()
                        if status in terminal_states:
                            break
                        if time.time() - started_poll >= float(cfg.batch_wait_timeout_seconds):
                            try:
                                batch_client.cancel(batch_job_id)
                            except Exception:
                                pass
                            failed_meta = {
                                "provider": batch_provider,
                                "model_id": batch_model_id,
                                "failure_type": "timeout",
                                "provider_error_reason": f"batch_timeout:{cfg.batch_wait_timeout_seconds}s",
                                "execution_mode": "batch",
                                "batch_provider": batch_provider,
                                "batch_job_id": batch_job_id,
                            }
                            return "", enrich_request_meta(
                                failed_meta,
                                run_id=run_id,
                                phase=phase,
                                step_id=step_id,
                                partition_id=partition_id,
                                provider=batch_provider,
                                model_id=batch_model_id,
                            )
                        for row in batch_job_rows:
                            if (
                                str(row.get("partition_id")) == partition_id
                                and str(row.get("job_id")) == batch_job_id
                            ):
                                row["state"] = status or "running"
                                row["last_polled_at_utc"] = now_iso()
                                break
                        if ui is not None:
                            ui.batch_event(
                                phase=phase,
                                step_id=step_id,
                                status="poll",
                                provider=batch_provider,
                                details=f"partition={partition_id} state={status}",
                            )
                        time.sleep(max(1, int(cfg.batch_poll_seconds)))
                    results = batch_client.fetch_results(batch_job_id)
                    result_map: Dict[str, BatchResult] = {
                        str(row.custom_id): row for row in results
                    }
                    row = result_map.get(partition_id)
                    if ui is not None:
                        ui.batch_event(
                            phase=phase,
                            step_id=step_id,
                            status="complete",
                            provider=batch_provider,
                            details=f"partition={partition_id} state={status} results={len(results)}",
                        )
                    if row is None:
                        for job_row in batch_job_rows:
                            if (
                                str(job_row.get("partition_id")) == partition_id
                                and str(job_row.get("job_id")) == batch_job_id
                            ):
                                job_row["state"] = "failed"
                                job_row["completed_at_utc"] = now_iso()
                                break
                        failed_meta = {
                            "provider": batch_provider,
                            "model_id": batch_model_id,
                            "failure_type": "provider",
                            "provider_error_reason": "batch_missing_result_for_partition",
                            "execution_mode": "batch",
                            "batch_provider": batch_provider,
                            "batch_job_id": batch_job_id,
                        }
                        return "", enrich_request_meta(
                            failed_meta,
                            run_id=run_id,
                            phase=phase,
                            step_id=step_id,
                            partition_id=partition_id,
                            provider=batch_provider,
                            model_id=batch_model_id,
                        )
                    meta = {
                        "provider": batch_provider,
                        "model_id": batch_model_id,
                        "status_code": 200 if not row.error else None,
                        "failure_type": None if not row.error else "provider",
                        "provider_error_reason": row.error,
                        "execution_mode": "batch",
                        "batch_provider": batch_provider,
                        "batch_job_id": batch_job_id,
                        "response_summary": {"batch_status": status},
                    }
                    for job_row in batch_job_rows:
                        if (
                            str(job_row.get("partition_id")) == partition_id
                            and str(job_row.get("job_id")) == batch_job_id
                        ):
                            job_row["state"] = "completed" if not row.error else "failed"
                            job_row["completed_at_utc"] = now_iso()
                            break
                    batch_result_rows.append(
                        {
                            "partition_id": partition_id,
                            "provider": batch_provider,
                            "model_id": batch_model_id,
                            "job_id": batch_job_id,
                            "status": status,
                            "error": row.error,
                        }
                    )
                    return str(row.output_text or ""), enrich_request_meta(
                        meta,
                        run_id=run_id,
                        phase=phase,
                        step_id=step_id,
                        partition_id=partition_id,
                        provider=batch_provider,
                        model_id=batch_model_id,
                    )
                llm_result = call_llm(
                    provider=route_provider,
                    model_id=route_model_id,
                    api_key_env=route_api_key_env,
                    system_prompt=prompt_text,
                    user_content=user_prompt,
                    cfg=cfg,
                    force_json_output=route_force_json,
                )
                response_text_local = str(llm_result.get("text", ""))
                request_meta_local = enrich_request_meta(
                    llm_result.get("meta", {}),
                    run_id=run_id,
                    phase=phase,
                    step_id=step_id,
                    partition_id=partition_id,
                    provider=route_provider,
                    model_id=route_model_id,
                )
                request_meta_local.setdefault("request_payload_bytes", payload_bytes)
                return response_text_local, request_meta_local

            parse_retry_attempted = False
            parse_retry_attempts = 0
            parse_retry_reason: Optional[str] = None
            parse_retry_trace: List[Dict[str, Any]] = []
            response_text_local, request_meta_local = _execute_llm_call()
            artifacts_local: List[Dict[str, Any]] = []
            while True:
                strict_candidate = response_text_local.strip()
                strict_error = _strict_decode_error(strict_candidate) if strict_candidate else None
                strict_string_literal_error = bool(
                    strict_error is not None and _is_string_literal_decode_error(strict_error)
                )
                strict_semantic_eof_eligible = bool(
                    strict_error is not None and _is_semantic_eof_eligible(strict_error, strict_candidate)
                )
                parsed = parse_json_from_response(response_text_local)
                artifacts_local = coerce_artifacts_from_response(
                    parsed=parsed,
                    raw_text=response_text_local,
                    expected_artifacts=output_artifacts,
                )
                parse_retry_trace.append(
                    {
                        "attempt": len(parse_retry_trace) + 1,
                        "failure_type": request_meta_local.get("failure_type"),
                        "finish_reason": (request_meta_local.get("response_summary") or {}).get("finish_reason")
                        if isinstance(request_meta_local.get("response_summary"), dict)
                        else None,
                        "strict_decode_error": str(strict_error) if strict_error else None,
                        "strict_decode_error_message": strict_error.msg if strict_error else None,
                        "strict_decode_error_pos": int(strict_error.pos) if strict_error else None,
                        "strict_string_literal_error": strict_string_literal_error,
                        "strict_semantic_eof_eligible": strict_semantic_eof_eligible,
                        "parsed_json": parsed is not None,
                        "artifacts_ok": bool(artifacts_local),
                        "response_text_length": len(response_text_local),
                    }
                )
                if artifacts_local:
                    break
                eligible_reason = _parse_retry_reason(response_text_local, request_meta_local, strict_error)
                if parse_retry_attempts >= PARSE_RETRY_MAX_EXTRA_ATTEMPTS or not eligible_reason:
                    break
                parse_retry_attempted = True
                parse_retry_attempts += 1
                parse_retry_reason = eligible_reason
                response_text_local, request_meta_local = _execute_llm_call()

            schema_ok, schema_reason = artifacts_pass_schema_gate(artifacts_local, output_artifacts)
            escalation_trigger: Optional[str] = None
            if not artifacts_local:
                if step_tier != "bulk":
                    escalation_trigger = "parse_failure" if parse_retry_attempts > 0 else "parse_failure_no_retry"
            elif not schema_ok:
                escalation_trigger = schema_reason or "schema_gate_failure"
            elif should_escalate_for_failure_type(request_meta_local.get("failure_type")):
                escalation_trigger = "provider_failure"
            if escalation_trigger and cfg.disable_escalation:
                escalation_trigger = None
            request_meta_local = {
                **request_meta_local,
                "parse_retry_attempted": parse_retry_attempted,
                "parse_retry_attempts": parse_retry_attempts,
                "parse_retry_reason": parse_retry_reason,
                "parse_retry_trace": parse_retry_trace,
                "schema_gate_passed": bool(schema_ok),
                "schema_gate_reason": schema_reason,
                "route_hop_index": hop_index + 1,
                "routing_tier": step_tier,
                "routing_policy": cfg.routing_policy,
                "execution_mode": str(request_meta_local.get("execution_mode") or "sync"),
                "batch_provider": request_meta_local.get("batch_provider"),
                "batch_job_id": request_meta_local.get("batch_job_id"),
            }
            return {
                "response_text": response_text_local,
                "request_meta": request_meta_local,
                "artifacts": artifacts_local,
                "route": route,
                "artifacts_ok": bool(artifacts_local and schema_ok),
                "escalation_trigger": escalation_trigger,
            }

        ladder_result = call_llm_with_ladder(
            phase=phase,
            step_id=step_id,
            partition_id=partition_id,
            routing_policy=cfg.routing_policy,
            routing_tier=step_tier,
            ladder=step_ladder,
            cfg=cfg,
            execute_attempt=_route_attempt,
            ui=ui,
        )
        response_text = str(ladder_result.get("response_text", ""))
        request_meta = (
            dict(ladder_result.get("request_meta"))
            if isinstance(ladder_result.get("request_meta"), dict)
            else {}
        )
        artifacts = (
            list(ladder_result.get("artifacts"))
            if isinstance(ladder_result.get("artifacts"), list)
            else []
        )
        final_route = tuple(ladder_result.get("route") or (initial_provider, initial_model_id, initial_api_key_env))
        final_provider = final_route[0] if len(final_route) > 0 else initial_provider
        final_model_id = final_route[1] if len(final_route) > 1 else initial_model_id
        request_meta["execution_mode"] = request_meta.get("execution_mode") or "sync"
        request_meta["batch_provider"] = request_meta.get("batch_provider") or None
        request_meta["batch_job_id"] = request_meta.get("batch_job_id") or None
        request_meta["route_attempts"] = request_meta.get("route_attempts") or []
        if len(request_meta.get("route_attempts", [])) > 1:
            request_meta["escalation_trigger"] = request_meta.get("escalation_trigger") or "gated_retry"
        else:
            request_meta["escalation_trigger"] = request_meta.get("escalation_trigger")
        request_meta["provider"] = request_meta.get("provider") or final_provider
        request_meta["model_id"] = request_meta.get("model_id") or final_model_id
        auth_failure = is_auth_classified_failure(request_meta.get("failure_type"))
        auth_expired = is_auth_expired_failure(request_meta.get("failure_type"))

        if not artifacts:
            if bool(request_meta.get("parse_retry_attempted")):
                _append_log(logs, "info", f"Artifact parse retry exhausted for {step_id} {partition_id}")
            _append_log(logs, "error", f"Artifact parse failed for {step_id} {partition_id}")
            _op_write_text(write_ops, out_failed, response_text)
            _op_write_json(
                write_ops,
                out_failed_json,
                {
                    "phase": phase,
                    "step_id": step_id,
                    "partition_id": partition_id,
                    "generated_at": now_iso(),
                    "failure_type": request_meta.get("failure_type") or "parse",
                    "status_code": request_meta.get("status_code"),
                    "request_meta": request_meta,
                },
            )
            _op_write_json(
                write_ops,
                out_json,
                {
                    "phase": phase,
                    "step_id": step_id,
                    "partition_id": partition_id,
                    "generated_at": now_iso(),
                    "artifacts": [],
                    "request_meta": {
                        **request_meta,
                        "failure_type": request_meta.get("failure_type") or "parse",
                    },
                },
            )
            return PartitionExecResult(
                partition_id=partition_id,
                write_ops=write_ops,
                logs=logs,
                request_meta=request_meta,
                artifacts=[],
                success=False,
                resume_skipped=False,
                auth_failure=auth_failure,
                auth_expired=auth_expired,
                recomputed_delta=1,
                dry_run_delta=0,
                failed_delta=1,
            )

        _op_write_json(
            write_ops,
            out_json,
            {
                "phase": phase,
                "step_id": step_id,
                "partition_id": partition_id,
                "generated_at": now_iso(),
                "artifacts": artifacts,
                "request_meta": request_meta,
            },
        )
        return PartitionExecResult(
            partition_id=partition_id,
            write_ops=write_ops,
            logs=logs,
            request_meta=request_meta,
            artifacts=artifacts,
            success=True,
            resume_skipped=False,
            auth_failure=auth_failure,
            auth_expired=auth_expired,
            recomputed_delta=1,
            dry_run_delta=0,
            failed_delta=0,
        )

    ordered_partitions = sorted(partitions, key=lambda row: str(row["id"]))
    results_by_partition: Dict[str, PartitionExecResult] = {}
    if workers == 1:
        for partition in ordered_partitions:
            partition_id = str(partition["id"])
            out_json = raw_dir / f"{step_id}__{partition_id}.json"
            out_failed = raw_dir / f"{step_id}__{partition_id}.FAILED.txt"
            out_failed_json = raw_dir / f"{step_id}__{partition_id}.FAILED.json"
            try:
                results_by_partition[partition_id] = _run_one_partition(partition)
            except Exception as exc:  # defensive: keep per-partition fail-open
                results_by_partition[partition_id] = _worker_exception_result(
                    partition_id=partition_id,
                    out_json=out_json,
                    out_failed=out_failed,
                    out_failed_json=out_failed_json,
                    exc=exc,
                )
            _ui_record_result(results_by_partition[partition_id])
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_map = {executor.submit(_run_one_partition, partition): partition for partition in ordered_partitions}
            for future in as_completed(future_map):
                partition = future_map[future]
                partition_id = str(partition["id"])
                out_json = raw_dir / f"{step_id}__{partition_id}.json"
                out_failed = raw_dir / f"{step_id}__{partition_id}.FAILED.txt"
                out_failed_json = raw_dir / f"{step_id}__{partition_id}.FAILED.json"
                try:
                    results_by_partition[partition_id] = future.result()
                except Exception as exc:
                    results_by_partition[partition_id] = _worker_exception_result(
                        partition_id=partition_id,
                        out_json=out_json,
                        out_failed=out_failed,
                        out_failed_json=out_failed_json,
                        exc=exc,
                    )
                _ui_record_result(results_by_partition[partition_id])

    for partition in ordered_partitions:
        partition_id = str(partition["id"])
        out_json = raw_dir / f"{step_id}__{partition_id}.json"
        out_failed = raw_dir / f"{step_id}__{partition_id}.FAILED.txt"
        out_failed_json = raw_dir / f"{step_id}__{partition_id}.FAILED.json"
        result = results_by_partition.get(partition_id)
        if result is None:
            result = _worker_exception_result(
                partition_id=partition_id,
                out_json=out_json,
                out_failed=out_failed,
                out_failed_json=out_failed_json,
                exc=RuntimeError("missing partition result"),
            )
            _ui_record_result(result)

        if result.resume_skipped:
            _apply_write_ops(result.write_ops)
            for level, message in result.logs:
                if level == "error":
                    logger.error("%s", message)
                else:
                    logger.info("%s", message)
            resume_skipped += 1
            continue

        retry_trace = result.request_meta.get("retry_trace")
        if isinstance(retry_trace, list):
            step_retry_count += max(0, len(retry_trace) - 1)
        hop_total = int(result.request_meta.get("route_hop_total", 1) or 1)
        step_hop_distribution[str(hop_total)] += 1
        if hop_total > 1:
            step_escalated_partitions += 1
        execution_mode = str(result.request_meta.get("execution_mode") or "sync")
        step_execution_mode_counts[execution_mode] += 1
        final_provider = str(result.request_meta.get("provider") or provider)
        final_model = str(result.request_meta.get("model_id") or model_id)
        step_final_route_counts[f"{final_provider}/{final_model}"] += 1

        if result.auth_failure:
            step_auth_failures += 1
            must_fail_fast = cfg.fail_fast_auth or result.auth_expired
            if must_fail_fast and step_success_count == 0:
                for level, message in result.logs:
                    if level == "error":
                        logger.error("%s", message)
                    else:
                        logger.info("%s", message)
                if ui is not None:
                    ui.step_progress_stop()
                raise RuntimeError(
                    f"Fail-fast auth triggered for step {step_id} partition {partition_id}. "
                    f"failure_type={result.request_meta.get('failure_type')} "
                    f"provider={result.request_meta.get('provider') or provider} "
                    f"model={result.request_meta.get('model_id') or model_id} auth_mode={cfg.gemini_auth_mode}. "
                    "Check credentials, endpoint mode, and gemini auth strategy."
                )

        _apply_write_ops(result.write_ops)
        for level, message in result.logs:
            if level == "error":
                logger.error("%s", message)
            else:
                logger.info("%s", message)

        if result.success:
            valid_success, _validation_reason = validate_success_partition_output(
                success_json_path=out_json,
                phase=phase,
                step_id=step_id,
                partition_id=partition_id,
                expected_artifact_names=output_artifacts,
            )
            if valid_success:
                prune_ops: List[Dict[str, Any]] = []
                prune_count = schedule_prune_failed_sidecars(
                    write_ops=prune_ops,
                    paths=list_failed_sidecars(raw_dir, step_id, partition_id),
                    reason="after_success",
                )
                if prune_count > 0:
                    logger.info(
                        "Resume: prune stale FAILED after success for %s %s count=%s",
                        step_id,
                        partition_id,
                        prune_count,
                    )
                    _apply_write_ops(prune_ops)

        step_recomputed_count += result.recomputed_delta
        step_dry_run_count += result.dry_run_delta
        step_failed_count += result.failed_delta
        if result.success:
            step_success_count += 1

    if resume_skipped:
        logger.info("Resume: skipped %s existing outputs for step %s", resume_skipped, step_id)
    if cfg.batch_mode:
        batch_dir = phase_dir / "batch"
        batch_dir.mkdir(parents=True, exist_ok=True)
        requests_path = batch_dir / f"{step_id}.requests.jsonl"
        job_path = batch_dir / f"{step_id}.job.json"
        results_path = batch_dir / f"{step_id}.results.jsonl"
        summary_path = batch_dir / f"{step_id}.summary.json"
        requests_text = "\n".join(json.dumps(row, sort_keys=True, ensure_ascii=True) for row in batch_request_rows)
        results_text = "\n".join(json.dumps(row, sort_keys=True, ensure_ascii=True) for row in batch_result_rows)
        requests_path.write_text((requests_text + "\n") if requests_text else "", encoding="utf-8")
        results_path.write_text((results_text + "\n") if results_text else "", encoding="utf-8")
        write_json(
            job_path,
            {
                "generated_at": now_iso(),
                "run_id": run_id,
                "phase": phase,
                "step_id": step_id,
                "routing_policy": cfg.routing_policy,
                "routing_tier": step_tier,
                "batch_submit_only": bool(cfg.batch_submit_only),
                "jobs": batch_job_rows,
            },
        )
        write_json(
            summary_path,
            {
                "generated_at": now_iso(),
                "phase": phase,
                "step_id": step_id,
                "request_count": len(batch_request_rows),
                "result_count": len(batch_result_rows),
                "job_count": len(batch_job_rows),
                "batch_submit_only": bool(cfg.batch_submit_only),
            },
        )
        write_batch_job_manifests(
            phase_dir,
            run_id=run_id,
            phase_id=phase,
            step_id=step_id,
            jobs=batch_job_rows,
        )
    elapsed_ms = int((time.time() - started_at) * 1000)
    logger.info(
        "Step summary %s partitions_total=%s ok=%s failed=%s retries=%s elapsed_ms=%s workers=%s",
        step_id,
        len(ordered_partitions),
        step_success_count,
        step_failed_count,
        step_retry_count,
        elapsed_ms,
        workers,
    )
    if ui is not None:
        ui.step_progress_stop()
    return {
        "partitions_total": len(ordered_partitions),
        "resume_skipped": resume_skipped,
        "recomputed": step_recomputed_count,
        "dry_run": step_dry_run_count,
        "ok": step_success_count,
        "failed": step_failed_count,
        "retries": step_retry_count,
        "elapsed_ms": elapsed_ms,
        "auth_failures": step_auth_failures,
        "hop_distribution": dict(step_hop_distribution),
        "escalated_partitions": step_escalated_partitions,
        "execution_mode_counts": dict(step_execution_mode_counts),
        "final_route_counts": dict(step_final_route_counts),
    }


def _run_phase_inner(
    phase: str,
    dirs: Dict[str, Path],
    cfg: RunnerConfig,
    collector: Optional[Collector],
    targets: Optional[List[str]],
    precollected_items: Optional[List[Dict[str, Any]]] = None,
    ui: Optional[UI] = None,
) -> None:
    phase_started_epoch = time.time()
    logger.info("--- Phase %s ---", phase)
    phase_dir = dirs[phase]
    prompts = get_phase_prompts(phase)
    if not prompts:
        raise RuntimeError(f"No prompts found for phase {phase} in {prompt_root()}/")
    prompt_report = _prompt_hash_report_for_phase(phase, prompts)
    if prompt_report["blocked_promptset"]:
        update_run_manifest_promptset_block(phase_dir.parent, phase, prompt_report)
        write_promptset_blocked_marker(phase, phase_dir, prompt_report)
        bad_paths = prompt_report["prompt_missing"] + [
            row.get("path", "") for row in prompt_report["prompt_unreadable"]
        ]
        preview = ", ".join(bad_paths[:3]) if bad_paths else f"phase={phase}"
        if len(bad_paths) > 3:
            preview += ", ..."
        raise PromptsetBlockedError(
            f"Promptset blocked for phase {phase}: invalid promptset ({preview})"
        )

    if precollected_items is not None:
        context_items = sorted(precollected_items, key=lambda item: item["path"])
        logger.info("Using %s pre-collected input artifacts.", len(context_items))
    else:
        if collector is None:
            context_items = []
        else:
            logger.info("Scanning targets for phase %s: %s", phase, targets)
            context_items = collector.collect(subdirs=targets)
            logger.info("Collected %s context files.", len(context_items))

    inventory = build_inventory(context_items, cfg.file_truncate_chars)
    max_files = max_files_for_phase(phase, cfg)
    partitions = build_partitions(phase, inventory, max_files=max_files, max_chars=cfg.max_chars)

    write_json(
        phase_dir / "inputs" / "INVENTORY.json",
        {"phase": phase, "generated_at": now_iso(), "items": inventory},
    )
    write_json(
        phase_dir / "inputs" / "PARTITIONS.json",
        {
            "phase": phase,
            "generated_at": now_iso(),
            "limits": {
                "max_files": max_files,
                "max_chars": cfg.max_chars,
                "file_truncate_chars": cfg.file_truncate_chars,
            },
            "partitions": partitions,
        },
    )
    inventory_path = phase_dir / "inputs" / "INVENTORY.json"
    partitions_path = phase_dir / "inputs" / "PARTITIONS.json"
    inventory_meta = _phase_input_stat(inventory_path)
    partitions_meta = _phase_input_stat(partitions_path)
    if cfg.debug_phase_inputs:
        logger.info(
            "PHASE_INPUTS_PROVENANCE phase=%s phase_dir=%s INVENTORY=%s PARTITIONS=%s",
            phase,
            str(phase_dir.resolve()),
            json.dumps(inventory_meta, sort_keys=True, separators=(",", ":")),
            json.dumps(partitions_meta, sort_keys=True, separators=(",", ":")),
        )
    if ui is not None:
        ui.phase_inputs_provenance(phase, inventory_meta, partitions_meta)
    if cfg.fail_fast_missing_inputs and (
        not inventory_meta["exists"] or not partitions_meta["exists"]
    ):
        raise RuntimeError(
            "Phase inputs missing after write. "
            f"phase={phase} run_id={phase_dir.parent.name} phase_dir={phase_dir.resolve()} "
            f"inventory={inventory_meta} partitions={partitions_meta}"
        )

    logger.info(
        "Phase %s inventory=%s partitions=%s max_files=%s max_chars=%s",
        phase,
        len(inventory),
        len(partitions),
        max_files,
        cfg.max_chars,
    )
    phase_tier_defaults: Dict[str, str] = {}
    for tier_name in STEP_TIERS:
        routes = (ACTIVE_ROUTING_LADDERS.get(cfg.routing_policy, {}) or {}).get(tier_name, [])
        if routes:
            phase_tier_defaults[tier_name] = f"{routes[0][0]}/{routes[0][1]}"
    first_step = prompts[0] if prompts else None
    if first_step is not None:
        first_ladder = resolve_effective_step_route(phase, first_step.step_id, cfg)["ladder"]
    else:
        first_ladder = []
    provider, model_id, _ = first_ladder[0] if first_ladder else MODEL_ROUTING.get(phase, ("openai", "gpt-5-mini", "OPENAI_API_KEY"))
    ui_flags = (
        f"resume:{cfg.resume},dry_run:{cfg.dry_run},debug_phase_inputs:{cfg.debug_phase_inputs},"
        f"fail_fast_auth:{cfg.fail_fast_auth},routing_policy:{cfg.routing_policy},"
        f"disable_escalation:{cfg.disable_escalation},batch_mode:{cfg.batch_mode}"
    )
    logger.info(
        "PHASE_HEADER phase=%s run_id=%s phase_dir=%s inventory=%s partitions=%s max_files=%s "
        "max_chars=%s max_request_bytes=%s provider=%s model=%s routing_policy=%s tier_defaults=%s "
        "flags=resume:%s,dry_run:%s,debug_phase_inputs:%s,fail_fast_auth:%s",
        phase,
        phase_dir.parent.name,
        str(phase_dir.resolve()),
        len(inventory),
        len(partitions),
        max_files,
        cfg.max_chars,
        cfg.max_request_bytes,
        provider,
        model_id,
        cfg.routing_policy,
        json.dumps(phase_tier_defaults, sort_keys=True),
        cfg.resume,
        cfg.dry_run,
        cfg.debug_phase_inputs,
        cfg.fail_fast_auth,
    )
    if ui is not None:
        ui.phase_start(
            phase=phase,
            phase_dir=phase_dir,
            inventory=len(inventory),
            partitions=len(partitions),
            provider=provider,
            model_id=model_id,
            workers=cfg.partition_workers,
            flags=ui_flags,
            routing_policy=cfg.routing_policy,
            tier_defaults=phase_tier_defaults,
        )

    phase_auth_failures = 0
    for prompt_spec in prompts:
        route_info = resolve_effective_step_route(phase, prompt_spec.step_id, cfg)
        provider = str(route_info["provider"])
        model_id = str(route_info["model_id"])
        api_key_env = str(route_info["api_key_env"])
        if provider == "gemini" and not cfg.dry_run:
            probe = run_gemini_auth_probe(
                run_id=phase_dir.parent.name,
                phase=phase,
                step_id=prompt_spec.step_id,
                phase_dir=phase_dir,
                provider=provider,
                model_id=model_id,
                api_key_env=api_key_env,
                cfg=cfg,
            )
            probe_failure = str(probe.get("failure_type") or "")
            if is_auth_classified_failure(probe_failure):
                phase_auth_failures += 1
                if cfg.fail_fast_auth or is_auth_expired_failure(probe_failure):
                    raise RuntimeError(
                        f"Gemini auth probe failed for phase={phase} step={prompt_spec.step_id} "
                        f"failure_type={probe_failure} env=GEMINI_API_KEY "
                        f"endpoint={probe.get('endpoint_effective')} "
                        f"mode={probe.get('gemini_auth_mode_effective')}."
                    )
        step_stats = execute_step_for_partitions(
            phase=phase,
            prompt_spec=prompt_spec,
            partitions=partitions,
            phase_dir=phase_dir,
            cfg=cfg,
            ui=ui,
        )
        phase_auth_failures += int(step_stats.get("auth_failures", 0))
        if phase_auth_failures >= cfg.phase_auth_fail_threshold:
            raise RuntimeError(
                f"Phase {phase} auth circuit breaker triggered: auth_failures={phase_auth_failures} "
                f"threshold={cfg.phase_auth_fail_threshold}. "
                "Check auth config, provider routing, and endpoint mode."
            )
        qa_payload = normalize_step(
            phase=phase,
            prompt_spec=prompt_spec,
            phase_dir=phase_dir,
            partitions=partitions,
            step_exec_stats=step_stats,
        )
        logger.info(
            "STEP_DONE phase=%s step=%s partitions_total=%s ok=%s failed=%s retries=%s elapsed_ms=%s norm_written=%s qa_file=%s",
            phase,
            prompt_spec.step_id,
            int(step_stats.get("partitions_total", 0)),
            int(step_stats.get("ok", 0)),
            int(step_stats.get("failed", 0)),
            int(step_stats.get("retries", 0)),
            int(step_stats.get("elapsed_ms", 0)),
            len(qa_payload.get("written_files", [])) if isinstance(qa_payload.get("written_files"), list) else 0,
            f"{prompt_spec.step_id}_QA.json",
        )
        if ui is not None:
            ui.step_done(
                phase=phase,
                step_id=prompt_spec.step_id,
                partitions_total=int(step_stats.get("partitions_total", 0)),
                ok=int(step_stats.get("ok", 0)),
                failed=int(step_stats.get("failed", 0)),
                retries=int(step_stats.get("retries", 0)),
                skipped=int(step_stats.get("resume_skipped", 0)),
                elapsed_ms=int(step_stats.get("elapsed_ms", 0)),
                norm_written=(
                    len(qa_payload.get("written_files", []))
                    if isinstance(qa_payload.get("written_files"), list)
                    else 0
                ),
                qa_file=f"{prompt_spec.step_id}_QA.json",
                hop_distribution=(
                    step_stats.get("hop_distribution")
                    if isinstance(step_stats.get("hop_distribution"), dict)
                    else {}
                ),
                escalated_partitions=int(step_stats.get("escalated_partitions", 0)),
                execution_mode_counts=(
                    step_stats.get("execution_mode_counts")
                    if isinstance(step_stats.get("execution_mode_counts"), dict)
                    else {}
                ),
                final_route_counts=(
                    step_stats.get("final_route_counts")
                    if isinstance(step_stats.get("final_route_counts"), dict)
                    else {}
                ),
            )
    logger.info(
        "PHASE_EXECUTION_DONE phase=%s elapsed_ms=%s auth_failures=%s",
        phase,
        int((time.time() - phase_started_epoch) * 1000),
        phase_auth_failures,
    )


def _count_files(directory: Path, suffixes: Optional[Set[str]] = None) -> int:
    if not directory.exists():
        return 0
    count = 0
    for entry in sorted(directory.iterdir()):
        if not entry.is_file():
            continue
        if suffixes and entry.suffix.lower() not in suffixes:
            continue
        count += 1
    return count


def gather_phase_counts(phase_dir: Path) -> Dict[str, Any]:
    inputs_dir = phase_dir / "inputs"
    raw_dir = phase_dir / "raw"
    norm_dir = phase_dir / "norm"
    qa_dir = phase_dir / "qa"

    inputs_count = _count_files(inputs_dir)

    raw_ok = 0
    raw_failed = 0
    raw_total = 0
    if raw_dir.exists():
        for entry in sorted(raw_dir.iterdir()):
            if not entry.is_file():
                continue
            raw_total += 1
            if ".FAILED" in entry.name:
                raw_failed += 1
            elif entry.suffix.lower() == ".json":
                raw_ok += 1

    norm_count = _count_files(norm_dir, suffixes={".json"})
    qa_count = _count_files(qa_dir, suffixes={".json", ".md", ".txt"})

    return {
        "inputs": inputs_count,
        "raw": {"total": raw_total, "ok": raw_ok, "failed": raw_failed},
        "norm": norm_count,
        "qa": qa_count,
    }


def _verify_single_phase(
    phase: str,
    dirs: Dict[str, Path],
    ui: Optional[UI] = None,
) -> Tuple[int, Dict[str, Any], List[str]]:
    phase_dir = dirs.get(phase)
    if not phase_dir or not phase_dir.exists():
        print(f"VERIFY PHASE {phase}: MISSING DIRECTORY")
        if ui is not None:
            ui.verify_result(
                phase=phase,
                status="MISSING",
                counts={},
                reasons=[f"Phase directory {phase} is missing."],
                phase_dir=dirs.get(phase, Path(".")),
            )
        return 3, {}, [f"Phase directory {phase} is missing."]

    counts = gather_phase_counts(phase_dir)
    reasons: List[str] = []
    if counts["inputs"] == 0:
        reasons.append("inputs directory is empty.")
    if counts["raw"]["total"] == 0:
        reasons.append("raw directory has no artifacts.")
    if counts["norm"] == 0:
        reasons.append("norm directory has no json artifacts.")
    if counts["qa"] == 0:
        reasons.append("qa directory has no artifacts.")

    status = "PASS" if not reasons else "FAIL"
    print(f"VERIFY PHASE {phase}: {status}")
    print(f"  inputs: {counts['inputs']} files")
    raw_stats = counts["raw"]
    print(f"  raw: {raw_stats['total']} files (ok={raw_stats['ok']} failed={raw_stats['failed']})")
    print(f"  norm: {counts['norm']} files")
    print(f"  qa: {counts['qa']} files")
    if reasons:
        print("  ISSUES:")
        for reason in reasons:
            print(f"    {reason}")

    if ui is not None:
        ui.verify_result(
            phase=phase,
            status=status,
            counts=counts,
            reasons=reasons,
            phase_dir=phase_dir,
        )

    return (0 if status == "PASS" else 2), counts, reasons


def verify_phase_output(dirs: Dict[str, Path], phases: List[str], ui: Optional[UI] = None) -> int:
    return_code = 0
    for phase in phases:
        code, _, _ = _verify_single_phase(phase, dirs, ui=ui)
        return_code = max(return_code, code)
    return return_code


def _phase_last_modified_iso(phase_dir: Path) -> Optional[str]:
    latest_mtime: Optional[float] = None
    for bucket in ("inputs", "raw", "norm", "qa"):
        bucket_dir = phase_dir / bucket
        if not bucket_dir.exists():
            continue
        for entry in bucket_dir.iterdir():
            if not entry.is_file():
                continue
            mtime = float(entry.stat().st_mtime)
            if latest_mtime is None or mtime > latest_mtime:
                latest_mtime = mtime
    if latest_mtime is None:
        return None
    return datetime.fromtimestamp(latest_mtime, timezone.utc).isoformat().replace("+00:00", "Z")


def _phase_status_badge(
    counts: Dict[str, Any],
    reasons: List[str],
    coverage_status: str,
    has_any_files: bool,
) -> str:
    if not has_any_files:
        return "NOT_STARTED"
    if coverage_status == "FAIL":
        return "FAIL"
    if reasons:
        return "IN_PROGRESS"
    if int(counts.get("raw", {}).get("failed", 0)) > 0:
        return "FAIL"
    return "PASS"


def phase_status_snapshot(run_id: str, dirs: Dict[str, Path], phases: List[str]) -> Dict[str, Any]:
    rollup_path = dirs["root"] / COVERAGE_ROLLUP_FILENAME
    rollup_payload = _load_json(rollup_path)
    rollup_phases = rollup_payload.get("phases", {}) if isinstance(rollup_payload.get("phases"), dict) else {}

    per_phase: Dict[str, Any] = {}
    summary = {"NOT_STARTED": 0, "IN_PROGRESS": 0, "PASS": 0, "FAIL": 0}
    for phase in phases:
        phase_dir = dirs[phase]
        phase_dir_exists = phase_dir.exists()
        counts = gather_phase_counts(phase_dir) if phase_dir_exists else {"inputs": 0, "raw": {"total": 0, "ok": 0, "failed": 0}, "norm": 0, "qa": 0}
        reasons: List[str] = []
        if counts["inputs"] == 0:
            reasons.append("inputs directory is empty.")
        if counts["raw"]["total"] == 0:
            reasons.append("raw directory has no artifacts.")
        if counts["norm"] == 0:
            reasons.append("norm directory has no json artifacts.")
        if counts["qa"] == 0:
            reasons.append("qa directory has no artifacts.")

        has_any_files = (
            counts["inputs"] > 0
            or counts["raw"]["total"] > 0
            or counts["norm"] > 0
            or counts["qa"] > 0
        )
        rollup_row = rollup_phases.get(phase, {}) if isinstance(rollup_phases, dict) else {}
        coverage_status = str(rollup_row.get("status", "UNKNOWN")) if isinstance(rollup_row, dict) else "UNKNOWN"
        badge = _phase_status_badge(counts, reasons, coverage_status, has_any_files)
        summary[badge] += 1

        per_phase[phase] = {
            "phase": phase,
            "phase_dir": str(phase_dir.resolve()),
            "phase_dir_exists": phase_dir_exists,
            "inputs_count": counts["inputs"],
            "raw_total": counts["raw"]["total"],
            "raw_ok": counts["raw"]["ok"],
            "raw_failed_sidecars": counts["raw"]["failed"],
            "norm_count": counts["norm"],
            "qa_count": counts["qa"],
            "last_modified": _phase_last_modified_iso(phase_dir),
            "coverage_status": coverage_status,
            "status": badge,
            "issues": reasons,
        }

    return {
        "generated_at": now_iso(),
        "run_id": run_id,
        "run_dir": str(dirs["root"].resolve()),
        "phases": per_phase,
        "summary": summary,
        "coverage_rollup": str(rollup_path.resolve()) if rollup_path.exists() else None,
    }


def _status_console(use_rich: bool) -> Optional[Any]:
    if not use_rich or Console is None:
        return None
    return Console()


def print_status_human(payload: Dict[str, Any], use_rich: bool, clear: bool = False) -> None:
    if use_rich and Table is not None:
        console = _status_console(use_rich)
        if console is None:
            print_status_human(payload, use_rich=False, clear=clear)
            return
        if clear:
            console.clear()
        summary = payload.get("summary", {})
        console.print(
            (
                f"Run {payload.get('run_id')}  "
                f"PASS={summary.get('PASS', 0)} FAIL={summary.get('FAIL', 0)} "
                f"IN_PROGRESS={summary.get('IN_PROGRESS', 0)} NOT_STARTED={summary.get('NOT_STARTED', 0)}"
            )
        )
        table = Table(show_header=True, header_style="bold")
        table.add_column("Phase")
        table.add_column("Status")
        table.add_column("Inputs")
        table.add_column("Raw (ok/failed/total)")
        table.add_column("Norm")
        table.add_column("QA")
        table.add_column("Last Modified (UTC)")
        for phase in PHASES:
            row = payload.get("phases", {}).get(phase, {})
            table.add_row(
                phase,
                str(row.get("status", "UNKNOWN")),
                str(row.get("inputs_count", 0)),
                f"{row.get('raw_ok', 0)}/{row.get('raw_failed_sidecars', 0)}/{row.get('raw_total', 0)}",
                str(row.get("norm_count", 0)),
                str(row.get("qa_count", 0)),
                str(row.get("last_modified") or "-"),
            )
        console.print(table)
        return

    if clear and sys.stdout.isatty():
        print("\033[2J\033[H", end="")
    summary = payload.get("summary", {})
    print(
        f"Run {payload.get('run_id')} PASS={summary.get('PASS', 0)} FAIL={summary.get('FAIL', 0)} "
        f"IN_PROGRESS={summary.get('IN_PROGRESS', 0)} NOT_STARTED={summary.get('NOT_STARTED', 0)}"
    )
    print("phase status inputs raw_ok raw_failed raw_total norm qa last_modified_utc")
    for phase in PHASES:
        row = payload.get("phases", {}).get(phase, {})
        print(
            f"{phase} {row.get('status', 'UNKNOWN')} {row.get('inputs_count', 0)} "
            f"{row.get('raw_ok', 0)} {row.get('raw_failed_sidecars', 0)} {row.get('raw_total', 0)} "
            f"{row.get('norm_count', 0)} {row.get('qa_count', 0)} {row.get('last_modified') or '-'}"
        )


def run_status_loop(
    run_id: str,
    dirs: Dict[str, Path],
    args: argparse.Namespace,
    ui: Optional[UI] = None,
) -> int:
    interval = float(args.watch) if args.watch is not None else 0.0
    status_ui = ui if ui is not None else UI(UiConfig(mode="auto"), dirs["root"], run_id)

    def _emit_once(clear: bool = False) -> None:
        payload = phase_status_snapshot(run_id, dirs, PHASES)
        try:
            if args.status_json:
                print(json.dumps(payload, indent=2, ensure_ascii=True))
            else:
                status_ui.status_table(payload, clear=clear)
        except BrokenPipeError:
            raise

    if interval > 0:
        try:
            while True:
                _emit_once(clear=True)
                time.sleep(interval)
        except BrokenPipeError:
            return 0
        except KeyboardInterrupt:
            return 130
    else:
        try:
            _emit_once(clear=False)
        except BrokenPipeError:
            return 0
    return 0


def print_promptpack(phases: List[str]) -> int:
    payload: Dict[str, Any] = {
        "generated_at": now_iso(),
        "runner_script_path": str(RUNNER_SCRIPT.resolve()),
        "phases": {},
    }
    for phase in phases:
        specs = get_phase_prompts(phase)
        payload["phases"][phase] = [
            {
                "step_id": spec.step_id,
                "path": str(spec.prompt_path.resolve()),
                "sha256": sha256_file_strict(spec.prompt_path),
                "declared_outputs": list(spec.output_artifacts),
            }
            for spec in specs
        ]
    print(json.dumps(payload, indent=2))
    return 0


def print_run_order(phases: List[str]) -> int:
    payload = {
        "generated_at": now_iso(),
        "runner_script_path": str(RUNNER_SCRIPT.resolve()),
        "phase_order": [
            {
                "phase_id": phase,
                "phase_dir": PHASE_DIR_NAMES.get(phase, phase),
            }
            for phase in phases
        ],
    }
    print(json.dumps(payload, indent=2))
    return 0


def print_phase_routing(phases: List[str], cfg: RunnerConfig) -> int:
    payload: Dict[str, Any] = {
        "generated_at": now_iso(),
        "runner_script_path": str(RUNNER_SCRIPT.resolve()),
        "routing_policy": cfg.routing_policy,
        "phases": {},
    }
    for phase in phases:
        entries: List[Dict[str, Any]] = []
        for spec in get_phase_prompts(phase):
            route = resolve_effective_step_route(phase, spec.step_id, cfg)
            entries.append(
                {
                    "step_id": spec.step_id,
                    "step_type": route.get("step_type"),
                    "step_tier": route.get("step_tier"),
                    "provider": route.get("provider"),
                    "model_id": route.get("model_id"),
                    "model": f"{route.get('provider')}/{route.get('model_id')}",
                    "reason": route.get("reason"),
                    "ladder": [
                        {
                            "provider": row[0],
                            "model_id": row[1],
                            "api_key_env": row[2],
                        }
                        for row in route.get("ladder", [])
                    ],
                }
            )
        entries.sort(key=lambda row: step_sort_key(str(row.get("step_id", ""))))
        payload["phases"][phase] = entries
    print(json.dumps(payload, indent=2))
    return 0


def print_phase_prompts(phases: List[str]) -> int:
    payload: Dict[str, Any] = {
        "generated_at": now_iso(),
        "runner_script_path": str(RUNNER_SCRIPT.resolve()),
        "phases": {},
    }
    for phase in phases:
        specs = get_phase_prompts(phase)
        payload["phases"][phase] = [
            {
                "step_id": spec.step_id,
                "prompt_file": spec.prompt_path.name,
                "prompt_path": str(spec.prompt_path.resolve()),
                "declared_outputs": list(spec.output_artifacts),
            }
            for spec in specs
        ]
    print(json.dumps(payload, indent=2))
    return 0


_RUN_LOG_HMS_RE = re.compile(r"^(\d{2}:\d{2}:\d{2})\s+\[[A-Z]+\]\s+")
_STEP_START_PROVIDER_RE = re.compile(r"STEP_START .* provider=([a-zA-Z0-9_-]+) model=([^\s]+)")
_STEP_DONE_ROUTES_RE = re.compile(r"STEP_DONE .* routes=(\{.*\})")


def _parse_since_epoch(since_token: str) -> Optional[float]:
    raw = str(since_token or "").strip()
    if not raw:
        return None
    suffix_map = {"s": 1, "m": 60, "h": 3600}
    if raw[-1:].lower() in suffix_map and raw[:-1].isdigit():
        seconds = int(raw[:-1]) * suffix_map[raw[-1:].lower()]
        return time.time() - max(0, seconds)
    if raw.isdigit():
        return float(int(raw))
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        return None


def _run_log_line_epoch(line: str) -> Optional[float]:
    match = _RUN_LOG_HMS_RE.match(line)
    if not match:
        return None
    try:
        now_dt = datetime.now(timezone.utc)
        parsed = datetime.strptime(match.group(1), "%H:%M:%S").time()
        with_date = datetime.combine(now_dt.date(), parsed, tzinfo=timezone.utc)
        return with_date.timestamp()
    except Exception:
        return None


def _filtered_run_log_lines(
    run_log_path: Path,
    *,
    phase: Optional[str] = None,
    step: Optional[str] = None,
    since: Optional[str] = None,
) -> List[str]:
    if not run_log_path.exists():
        raise FileNotFoundError(f"RUN log not found: {run_log_path}")
    lines = run_log_path.read_text(encoding="utf-8").splitlines()
    phase_token = str(phase or "").strip().upper()
    step_token = str(step or "").strip().upper()
    since_epoch = _parse_since_epoch(str(since or "").strip())
    filtered: List[str] = []
    for line in lines:
        if phase_token and f"phase={phase_token}" not in line:
            continue
        if step_token and f"step={step_token}" not in line:
            continue
        if since_epoch is not None:
            line_epoch = _run_log_line_epoch(line)
            if line_epoch is None or line_epoch < since_epoch:
                continue
        filtered.append(line)
    return filtered


def tail_run_log(
    run_id: str,
    dirs: Dict[str, Path],
    *,
    phase: Optional[str] = None,
    step: Optional[str] = None,
    since: Optional[str] = None,
    tail_lines: int = 200,
) -> int:
    del run_id
    run_log_path = dirs["root"] / RUN_LOG_FILENAME
    try:
        lines = _filtered_run_log_lines(run_log_path, phase=phase, step=step, since=since)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1
    limit = max(1, int(tail_lines))
    for line in lines[-limit:]:
        print(line)
    return 0


def show_provider_usage(
    run_id: str,
    dirs: Dict[str, Path],
    *,
    phase: Optional[str] = None,
    step: Optional[str] = None,
    since: Optional[str] = None,
) -> int:
    run_log_path = dirs["root"] / RUN_LOG_FILENAME
    try:
        lines = _filtered_run_log_lines(run_log_path, phase=phase, step=step, since=since)
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1

    starts: Counter[str] = Counter()
    routes: Counter[str] = Counter()
    for line in lines:
        start_match = _STEP_START_PROVIDER_RE.search(line)
        if start_match:
            starts[f"{start_match.group(1)}/{start_match.group(2)}"] += 1
            continue
        done_match = _STEP_DONE_ROUTES_RE.search(line)
        if done_match:
            try:
                payload = json.loads(done_match.group(1))
            except Exception:
                continue
            if isinstance(payload, dict):
                for key, value in payload.items():
                    try:
                        routes[str(key)] += int(value)
                    except Exception:
                        continue

    payload = {
        "generated_at": now_iso(),
        "run_id": run_id,
        "run_root": str(dirs["root"].resolve()),
        "filters": {
            "phase": str(phase or "").upper() or None,
            "step": str(step or "").upper() or None,
            "since": str(since or "").strip() or None,
        },
        "step_start_counts": dict(sorted(starts.items())),
        "step_done_route_counts": dict(sorted(routes.items())),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True))
    return 0


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _coverage_for_phase(phase: str, phase_dir: Path) -> Dict[str, Any]:
    partitions_payload = _load_json(phase_dir / "inputs" / "PARTITIONS.json")
    partitions = partitions_payload.get("partitions") if isinstance(partitions_payload.get("partitions"), list) else []
    partition_ids = [str(partition.get("id")) for partition in partitions if isinstance(partition, dict) and partition.get("id")]

    raw_dir = phase_dir / "raw"
    attempted: Set[str] = set()
    ok: Set[str] = set()
    failed: Set[str] = set()
    failure_hist = Counter()

    if raw_dir.exists():
        for raw_json in sorted(raw_dir.glob("*.json")):
            payload = _load_json(raw_json)
            partition_id = str(payload.get("partition_id") or "")
            if not partition_id:
                match = re.search(r"__([A-Z]_P\d+)\.json$", raw_json.name)
                partition_id = match.group(1) if match else ""
            if partition_id:
                attempted.add(partition_id)
            artifacts = payload.get("artifacts")
            if isinstance(artifacts, list) and artifacts:
                if partition_id:
                    ok.add(partition_id)
            else:
                if partition_id:
                    failed.add(partition_id)
                request_meta = payload.get("request_meta")
                failure_type = None
                if isinstance(request_meta, dict):
                    failure_type = request_meta.get("failure_type")
                if not failure_type:
                    failure_type = "parse_or_empty"
                failure_hist[str(failure_type)] += 1

        for failed_json in sorted(raw_dir.glob("*.FAILED.json")):
            payload = _load_json(failed_json)
            failure_type = payload.get("failure_type") or "failed_sidecar"
            failure_hist[str(failure_type)] += 1
            partition_id = str(payload.get("partition_id") or "")
            if partition_id:
                attempted.add(partition_id)
                failed.add(partition_id)

    attempted_count = len(attempted) if attempted else len(partition_ids)
    total_partitions = len(partition_ids)
    return {
        "phase": phase,
        "partitions_total": total_partitions,
        "partitions_attempted": attempted_count,
        "partitions_ok": len(ok),
        "partitions_failed": len(failed),
        "failure_type_histogram": dict(sorted(failure_hist.items())),
    }


def generate_coverage_report(root: Path, dirs: Dict[str, Path], run_id: str, phases: List[str]) -> int:
    phase_rows = [_coverage_for_phase(phase, dirs[phase]) for phase in phases]
    required_status = get_required_artifact_status(dirs, R_REQUIRED_INPUT_PHASES)
    payload = {
        "generated_at": now_iso(),
        "run_id": run_id,
        "runner_sha256": sha256_text(RUNNER_SCRIPT),
        "git_sha": get_git_sha(root),
        "phases": {row["phase"]: row for row in phase_rows},
        "required_artifact_coverage": required_status,
    }
    write_json(dirs["root"] / "COVERAGE_REPORT.json", payload)
    proof_path = dirs["root"] / PROOF_PACK_FILENAME
    proof = _load_json(proof_path)
    proof["coverage_report"] = payload
    proof["updated_at"] = now_iso()
    write_json(proof_path, proof)
    print(json.dumps(payload, indent=2))
    return 0


def _read_step_qa_payloads(phase_dir: Path) -> List[Dict[str, Any]]:
    qa_dir = phase_dir / "qa"
    rows: List[Dict[str, Any]] = []
    if not qa_dir.exists():
        return rows
    for path in sorted(qa_dir.glob("*_QA.json")):
        row = _load_json(path)
        if row:
            rows.append(row)
    return rows


def _expected_artifact_present(norm_dir: Path, artifact_name: str) -> bool:
    if ".partX." in artifact_name:
        pattern = artifact_name.replace(".partX.", ".part*.")
        return any(entry.is_file() for entry in norm_dir.glob(pattern))
    return (norm_dir / artifact_name).is_file()


def write_phase_coverage_manifest(phase: str, phase_dir: Path) -> Dict[str, Any]:
    prompts = get_phase_prompts(phase)
    expected_outputs = {
        spec.step_id: list(spec.output_artifacts)
        for spec in prompts
    }
    prompt_declared_outputs = sorted(
        {artifact for artifacts in expected_outputs.values() for artifact in artifacts}
    )
    raw_dir = phase_dir / "raw"
    norm_dir = phase_dir / "norm"
    blocked_path = phase_dir / "qa" / f"PHASE_{phase}_BLOCKED_PROMPTSET.json"
    blocked_payload = _load_json(blocked_path)
    blocked_promptset = (
        blocked_payload.get("status") == "blocked_promptset"
        if isinstance(blocked_payload, dict)
        else False
    )
    missing_prompts_count = int(blocked_payload.get("missing_prompts_count", 0)) if blocked_promptset else 0
    unreadable_prompts_count = int(blocked_payload.get("unreadable_prompts_count", 0)) if blocked_promptset else 0
    qa_rows = _read_step_qa_payloads(phase_dir)
    qa_by_step: Dict[str, Dict[str, Any]] = {
        str(row.get("step_id")): row
        for row in qa_rows
        if isinstance(row, dict) and row.get("step_id")
    }

    observed_raw = sorted(entry.name for entry in raw_dir.iterdir() if entry.is_file()) if raw_dir.exists() else []
    observed_norm = sorted(entry.name for entry in norm_dir.iterdir() if entry.is_file()) if norm_dir.exists() else []
    undeclared_observed_outputs = sorted(
        [name for name in observed_norm if name not in prompt_declared_outputs]
    )

    counts = {
        "ok": 0,
        "failed": 0,
        "skipped": 0,
        "dry_run": 0,
        "blocked_promptset": 1 if blocked_promptset else 0,
        "missing_prompts_count": missing_prompts_count,
        "unreadable_prompts_count": unreadable_prompts_count,
    }
    for row in qa_rows:
        row_recomputed = int(row.get("recomputed_partitions", 0))
        row_failed = int(row.get("execution_failed_partitions", row.get("raw_failed", 0)))
        row_skipped = int(row.get("resume_skipped_partitions", 0))
        row_dry_run = int(row.get("dry_run_partitions", 0))
        row_ok = max(0, row_recomputed - row_failed - row_dry_run)

        counts["ok"] += row_ok
        counts["failed"] += row_failed
        counts["skipped"] += row_skipped
        counts["dry_run"] += row_dry_run

    missing_required: List[Dict[str, str]] = []
    missing_reason_counts = {
        "failed": 0,
        "skipped_resume": 0,
        "dry_run": 0,
        "blocked_promptset": 1 if blocked_promptset else 0,
        "prompt_does_not_declare_it": 0,
        "unknown": 0,
    }
    for step_id, artifacts in expected_outputs.items():
        step_row = qa_by_step.get(step_id, {})
        step_expected = set(step_row.get("expected_artifacts", [])) if isinstance(step_row, dict) else set()
        step_failed = (
            int(step_row.get("execution_failed_partitions", step_row.get("raw_failed", 0)))
            if isinstance(step_row, dict)
            else 0
        )
        step_skipped = int(step_row.get("resume_skipped_partitions", 0)) if isinstance(step_row, dict) else 0
        step_dry_run = int(step_row.get("dry_run_partitions", 0)) if isinstance(step_row, dict) else 0

        for artifact_name in artifacts:
            if not _expected_artifact_present(norm_dir, artifact_name):
                reason = "unknown"
                if artifact_name not in step_expected and step_row:
                    reason = "prompt_does_not_declare_it"
                elif step_dry_run > 0:
                    reason = "dry_run"
                elif step_failed > 0:
                    reason = "failed"
                elif step_skipped > 0:
                    reason = "skipped_resume"
                missing_required.append({"step_id": step_id, "artifact": artifact_name, "reason": reason})
                missing_reason_counts[reason] += 1

    payload = {
        "generated_at": now_iso(),
        "phase": phase,
        "expected_outputs": expected_outputs,
        "prompt_declared_outputs": prompt_declared_outputs,
        "observed_outputs": {
            "raw": observed_raw,
            "norm": observed_norm,
            "undeclared_norm": undeclared_observed_outputs,
        },
        "counts": counts,
        "missing_required_artifacts": missing_required,
        "missing_required_artifacts_by_reason": missing_reason_counts,
        "blocked_promptset": {
            "status": "BLOCKED" if blocked_promptset else "CLEAR",
            "missing_prompts_count": missing_prompts_count,
            "unreadable_prompts_count": unreadable_prompts_count,
            "prompt_missing": blocked_payload.get("prompt_missing", []) if blocked_promptset else [],
            "prompt_unreadable": blocked_payload.get("prompt_unreadable", []) if blocked_promptset else [],
        },
        "status": "FAIL" if blocked_promptset or missing_required else "PASS",
    }
    write_json(phase_dir / "qa" / f"PHASE_{phase}_COVERAGE.json", payload)
    return payload


def write_coverage_rollup(
    root: Path,
    dirs: Dict[str, Path],
    run_id: str,
    promptset_report: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    del root
    blocked_promptset = bool((promptset_report or {}).get("blocked_promptset"))
    if blocked_promptset:
        payload = {
            "generated_at": now_iso(),
            "run_id": run_id,
            "phases": {},
            "missing_required_artifacts_total": 0,
            "run_status": "BLOCKED",
            "blocked_reason": PROMPTSET_BLOCKED_REASON,
            "blocked_promptset": True,
            "prompt_failures_count": int((promptset_report or {}).get("prompt_failures_count", 0)),
            "phases_executed_count": 0,
        }
        write_json(dirs["root"] / COVERAGE_ROLLUP_FILENAME, payload)
        return payload

    phase_rollup: Dict[str, Any] = {}
    missing_total = 0
    for phase in PHASES:
        coverage_path = dirs[phase] / "qa" / f"PHASE_{phase}_COVERAGE.json"
        if not coverage_path.exists():
            continue
        payload = _load_json(coverage_path)
        missing = payload.get("missing_required_artifacts")
        missing_count = len(missing) if isinstance(missing, list) else 0
        missing_total += missing_count
        phase_rollup[phase] = {
            "status": payload.get("status", "UNKNOWN"),
            "missing_required_artifacts_count": missing_count,
            "missing_required_artifacts": missing if isinstance(missing, list) else [],
            "counts": payload.get("counts", {}),
            "blocked_promptset": payload.get("blocked_promptset", {}),
            "coverage_file": str(coverage_path.resolve()),
        }

    payload = {
        "generated_at": now_iso(),
        "run_id": run_id,
        "phases": phase_rollup,
        "missing_required_artifacts_total": missing_total,
        "run_status": "BLOCKED" if blocked_promptset else "OK",
        "blocked_reason": PROMPTSET_BLOCKED_REASON if blocked_promptset else None,
        "blocked_promptset": blocked_promptset,
        "prompt_failures_count": int((promptset_report or {}).get("prompt_failures_count", 0)),
        "phases_executed_count": 0 if blocked_promptset else len(phase_rollup),
    }
    write_json(dirs["root"] / COVERAGE_ROLLUP_FILENAME, payload)
    return payload


def write_resume_proof(
    dirs: Dict[str, Path],
    run_id: str,
    phases: Iterable[str],
    promptset_report: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    active_phases = sorted(set(phases))
    per_phase: Dict[str, Any] = {}
    total_skipped = 0
    total_recomputed = 0
    for phase in PHASES:
        phase_dir = dirs[phase]
        inventory_path = phase_dir / "inputs" / "INVENTORY.json"
        partitions_path = phase_dir / "inputs" / "PARTITIONS.json"
        qa_rows = _read_step_qa_payloads(phase_dir)
        skipped = sum(int(row.get("resume_skipped_partitions", 0)) for row in qa_rows)
        recomputed = sum(int(row.get("recomputed_partitions", 0)) for row in qa_rows)
        if not qa_rows and not inventory_path.exists() and not partitions_path.exists():
            continue
        total_skipped += skipped
        total_recomputed += recomputed
        per_phase[phase] = {
            "resume_skipped_partitions": skipped,
            "recomputed_partitions": recomputed,
            "inventory_sha256": sha256_text(inventory_path) if inventory_path.exists() else None,
            "partitions_sha256": sha256_text(partitions_path) if partitions_path.exists() else None,
            "inventory_file": str(inventory_path.resolve()) if inventory_path.exists() else None,
            "partitions_file": str(partitions_path.resolve()) if partitions_path.exists() else None,
        }

    promptset = promptset_report if promptset_report is not None else promptset_fingerprint(active_phases)
    blocked_promptset = bool(promptset.get("blocked_promptset"))
    payload = {
        "generated_at": now_iso(),
        "run_id": run_id,
        "active_phases": active_phases,
        "totals": {
            "resume_skipped_partitions": total_skipped,
            "recomputed_partitions": total_recomputed,
        },
        "phases": per_phase,
        "prompt_hash_mode": promptset["prompt_hash_mode"],
        "promptset_sha256": promptset["promptset_sha256"],
        "prompt_hashes": promptset["prompt_hashes"],
        "prompt_missing": promptset["prompt_missing"],
        "prompt_unreadable": promptset["prompt_unreadable"],
        "prompt_hash_errors": promptset["prompt_hash_errors"],
        "prompt_failures": promptset.get("prompt_failures", []),
        "blocked_promptset": promptset["blocked_promptset"],
        "missing_prompts_count": promptset["missing_prompts_count"],
        "unreadable_prompts_count": promptset["unreadable_prompts_count"],
        "prompt_failures_count": promptset.get("prompt_failures_count", 0),
        "resume_status": "blocked" if blocked_promptset else "ready",
    }
    if blocked_promptset:
        payload["blocked_reason"] = PROMPTSET_BLOCKED_REASON
        payload["blocked"] = _resume_blocked_payload(promptset)
    write_json(dirs["root"] / RESUME_PROOF_FILENAME, payload)
    return payload


def apply_promptset_preflight_block(
    root: Path,
    dirs: Dict[str, Path],
    run_id: str,
    phases: List[str],
    prompt_report: Dict[str, Any],
    run_started_at: str,
) -> None:
    for phase in phases:
        phase_report = _prompt_hash_report_for_phase(phase, get_phase_prompts(phase))
        if phase_report.get("blocked_promptset"):
            write_promptset_blocked_marker(phase, dirs[phase], phase_report)
    write_coverage_rollup(root, dirs, run_id, prompt_report)
    write_resume_proof(dirs, run_id, phases, promptset_report=prompt_report)
    write_blocked_promptset_proof_pack(root, dirs, run_id, run_started_at, phases, prompt_report)


def print_config(
    args: argparse.Namespace,
    root: Path,
    run_id: str,
    dirs: Dict[str, Path],
    cfg: RunnerConfig,
    phases: List[str],
    run_context: RunContext,
) -> None:
    config_payload = {
        "run_id": run_id,
        "run_root": str(root.resolve()),
        "git_sha": get_git_sha(root),
        "runner_sha256": sha256_text(RUNNER_SCRIPT),
        "python_version": platform.python_version(),
        "cwd": str(Path.cwd().resolve()),
        "phases": phases,
        "cli": {
            "phase_argument": args.phase,
            "verify_phase_output": args.verify_phase_output,
            "doctor": args.doctor,
            "doctor_auth": args.doctor_auth,
            "preflight_providers": args.preflight_providers,
            "coverage_report": args.coverage_report,
            "ui": args.ui,
            "quiet": args.quiet,
            "jsonl_events": args.jsonl_events,
            "pretty": args.pretty,
            "print_promptpack": args.print_promptpack,
            "print_run_order": args.print_run_order,
            "print_phase_routing": args.print_phase_routing,
            "print_phase_prompts": args.print_phase_prompts,
            "print_config": args.print_config,
            "run_id_override": args.run_id,
            "run_id_source": run_context.source,
            "run_id_resolution_precedence": [
                "explicit(--run-id)",
                f"implicit({V3_LATEST_RUN_FILE.as_posix()})",
                "generated(new timestamp run id)",
            ],
            "dry_run": args.dry_run,
            "resume": args.resume,
            "no_write_latest": args.no_write_latest,
            "write_latest_even_on_dry_run": args.write_latest_even_on_dry_run,
            "latest_run_id_written": run_context.latest_written,
            "latest_run_id_file": str(run_context.latest_file.resolve()),
            "home_scan_mode": args.home_scan_mode,
            "max_files_docs": args.max_files_docs,
            "max_files_code": args.max_files_code,
            "max_chars": args.max_chars,
            "max_request_bytes": args.max_request_bytes,
            "file_truncate_chars": args.file_truncate_chars,
            "fail_fast_auth": args.fail_fast_auth,
            "gemini_auth_mode": args.gemini_auth_mode,
            "gemini_model_id": args.gemini_model_id,
            "gemini_transport": args.gemini_transport,
            "openai_transport": args.openai_transport,
            "xai_transport": args.xai_transport,
            "retry_policy": args.retry_policy,
            "retry_max_attempts": args.retry_max_attempts,
            "retry_base_seconds": args.retry_base_seconds,
            "retry_max_seconds": args.retry_max_seconds,
            "phase_auth_fail_threshold": args.phase_auth_fail_threshold,
            "partition_workers": args.partition_workers,
            "routing_policy": args.routing_policy,
            "dpmx_routing_enable": os.getenv(DPMX_ROUTING_ENABLE_ENV, ""),
            "dpmx_model_inventory": os.getenv(DPMX_MODEL_INVENTORY_ENV, ""),
            "dpmx_model_extract": os.getenv(DPMX_MODEL_EXTRACT_ENV, ""),
            "dpmx_model_synthesis": os.getenv(DPMX_MODEL_SYNTHESIS_ENV, ""),
            "dpmx_model_qa": os.getenv(DPMX_MODEL_QA_ENV, ""),
            "disable_escalation": args.disable_escalation,
            "escalation_max_hops": args.escalation_max_hops,
            "batch_mode": args.batch_mode,
            "batch_submit_only": args.batch_submit_only,
            "batch_watch": args.batch_watch,
            "batch_provider": args.batch_provider,
            "batch_poll_seconds": args.batch_poll_seconds,
            "batch_wait_timeout_seconds": args.batch_wait_timeout_seconds,
            "batch_max_requests_per_job": args.batch_max_requests_per_job,
            "dpmx_webhook_url": os.getenv(DPMX_WEBHOOK_URL_ENV, ""),
            "dpmx_webhook_secret_set": bool(os.getenv(DPMX_WEBHOOK_SECRET_ENV, "").strip()),
            "dpmx_webhook_timeout_seconds": os.getenv(DPMX_WEBHOOK_TIMEOUT_SECONDS_ENV, ""),
            "dpmx_webhook_required": os.getenv(DPMX_WEBHOOK_REQUIRED_ENV, ""),
            "dpmx_webhook_auto_continue": os.getenv(DPMX_WEBHOOK_AUTO_CONTINUE_ENV, ""),
            "dpmx_live_ok": os.getenv(DPMX_LIVE_OK_ENV, ""),
            "debug_phase_inputs": args.debug_phase_inputs,
            "fail_fast_missing_inputs": args.fail_fast_missing_inputs,
        },
        "limits": {
            "max_files_docs": cfg.max_files_docs,
            "max_files_code": cfg.max_files_code,
            "max_chars": cfg.max_chars,
            "max_request_bytes": cfg.max_request_bytes,
            "file_truncate_chars": cfg.file_truncate_chars,
        },
        "dirs": {phase: str(dirs[phase]) for phase in phases},
        "routing_policy_version": ROUTING_POLICY_VERSION,
        "routing_ladders": routing_ladders_payload(),
        "effective_model_routing": effective_model_routing_payload(),
        "dpmx_env_routing": dpmx_env_routing_payload(validate=True),
        "webhook_settings": {
            "schema": DPMX_WEBHOOK_SCHEMA,
            "event": DPMX_WEBHOOK_EVENT,
            "url": cfg.webhook_url,
            "secret_set": bool(cfg.webhook_secret),
            "timeout_seconds": cfg.webhook_timeout_seconds,
            "required": cfg.webhook_required,
            "auto_continue": cfg.webhook_auto_continue,
            "live_ok": cfg.live_ok,
        },
        "batch_settings": {
            "enabled": cfg.batch_mode,
            "submit_only": cfg.batch_submit_only,
            "provider": cfg.batch_provider,
            "poll_seconds": cfg.batch_poll_seconds,
            "wait_timeout_seconds": cfg.batch_wait_timeout_seconds,
            "max_requests_per_job": cfg.batch_max_requests_per_job,
        },
    }
    print(json.dumps(config_payload, indent=2))


def update_proof_pack(
    root: Path,
    dirs: Dict[str, Path],
    run_id: str,
    run_started_at: str,
    phase: str,
    phase_counts: Dict[str, Any],
    phase_started_at: str,
    phase_finished_at: str,
) -> None:
    refresh_run_manifest_artifacts(dirs["root"], dirs)
    proof_path = dirs["root"] / PROOF_PACK_FILENAME
    proof: Dict[str, Any] = {}
    if proof_path.exists():
        try:
            proof = json.loads(proof_path.read_text(encoding="utf-8") or "{}")
        except Exception:
            proof = {}

    proof["run_id"] = run_id
    proof["git_sha"] = get_git_sha(root)
    proof["runner_sha256"] = sha256_text(RUNNER_SCRIPT)
    proof["argv"] = sys.argv
    proof["python_version"] = platform.python_version()
    proof["cwd"] = str(root.resolve())
    proof["started_at"] = run_started_at
    proof.setdefault("phases", {})[phase] = {
        "started_at": phase_started_at,
        "finished_at": phase_finished_at,
        "counts": phase_counts,
    }
    proof["finished_at"] = phase_finished_at
    proof["updated_at"] = now_iso()
    doctor_dir = root / V3_DOCTOR_ROOT
    auth_doctor = doctor_dir / "AUTH_DOCTOR.json"
    full_doctor = doctor_dir / "DOCTOR_FULL.json"
    routing_fp = dirs["root"] / "RUN_ROUTING_FINGERPRINT.json"
    coverage_rollup = dirs["root"] / COVERAGE_ROLLUP_FILENAME
    resume_proof = dirs["root"] / RESUME_PROOF_FILENAME
    proof["linked_artifacts"] = {
        "coverage_rollup": str(coverage_rollup.resolve()) if coverage_rollup.exists() else None,
        "resume_proof": str(resume_proof.resolve()) if resume_proof.exists() else None,
        "run_routing_fingerprint": str(routing_fp.resolve()) if routing_fp.exists() else None,
        "doctor_auth": str(auth_doctor.resolve()) if auth_doctor.exists() else None,
        "doctor_full": str(full_doctor.resolve()) if full_doctor.exists() else None,
    }
    write_json(proof_path, proof)


def write_blocked_promptset_proof_pack(
    root: Path,
    dirs: Dict[str, Path],
    run_id: str,
    run_started_at: str,
    phases: List[str],
    prompt_report: Dict[str, Any],
) -> None:
    refresh_run_manifest_artifacts(dirs["root"], dirs)
    proof_path = dirs["root"] / PROOF_PACK_FILENAME
    proof: Dict[str, Any] = {}
    if proof_path.exists():
        try:
            proof = json.loads(proof_path.read_text(encoding="utf-8") or "{}")
        except Exception:
            proof = {}

    blocked_at = now_iso()
    coverage_rollup = dirs["root"] / COVERAGE_ROLLUP_FILENAME
    resume_proof = dirs["root"] / RESUME_PROOF_FILENAME
    routing_fp = dirs["root"] / "RUN_ROUTING_FINGERPRINT.json"
    proof["run_id"] = run_id
    proof["git_sha"] = get_git_sha(root)
    proof["runner_sha256"] = sha256_text(RUNNER_SCRIPT)
    proof["argv"] = sys.argv
    proof["python_version"] = platform.python_version()
    proof["cwd"] = str(root.resolve())
    proof["started_at"] = run_started_at
    proof["finished_at"] = blocked_at
    proof["updated_at"] = blocked_at
    proof["run_status"] = "BLOCKED"
    proof["blocked_reason"] = PROMPTSET_BLOCKED_REASON
    proof["blocked"] = _blocked_promptset_payload(prompt_report, at="preflight")
    proof["phases"] = {phase: {"status": "NOT_EXECUTED"} for phase in phases}
    proof["linked_artifacts"] = {
        "coverage_rollup": str(coverage_rollup.resolve()) if coverage_rollup.exists() else None,
        "resume_proof": str(resume_proof.resolve()) if resume_proof.exists() else None,
        "run_routing_fingerprint": str(routing_fp.resolve()) if routing_fp.exists() else None,
    }
    write_json(proof_path, proof)


# --- Phase Wrappers ---

def to_items(paths: Iterable[Path]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for path in sorted({p.resolve() for p in paths if p.exists()}):
        try:
            st = path.stat()
            size = st.st_size
            mtime = st.st_mtime
        except Exception:
            size = 0
            mtime = 0.0
        items.append({"path": str(path), "size": size, "mtime": mtime, "name": path.name})
    return items


def collect_phase_artifacts(dirs: Dict[str, Path], phases: List[str], buckets: List[str]) -> List[Dict[str, Any]]:
    files: List[Path] = []
    for phase in phases:
        for bucket in buckets:
            bucket_dir = dirs[phase] / bucket
            if bucket_dir.exists():
                files.extend(sorted(bucket_dir.glob("*.json")))
                files.extend(sorted(bucket_dir.glob("*.md")))
    return to_items(files)


def _has_matching_file(directory: Path, pattern: str) -> bool:
    return any(True for _ in directory.glob(pattern))


def _phase_partitions_from_inputs(phase_dir: Path) -> List[Dict[str, Any]]:
    payload = _read_json_dict(phase_dir / "inputs" / "PARTITIONS.json")
    rows = payload.get("partitions")
    if not isinstance(rows, list):
        return []
    partitions: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        partition_id = str(row.get("id") or "").strip()
        if not partition_id:
            continue
        paths = row.get("paths")
        safe_paths = [str(path) for path in paths] if isinstance(paths, list) else []
        partitions.append({"id": partition_id, "paths": safe_paths})
    partitions.sort(key=lambda row: str(row["id"]))
    return partitions


def _batch_terminal_state(status: str) -> bool:
    token = str(status or "").strip().lower()
    return token in {"completed", "succeeded", "done", "failed", "cancelled", "canceled", "timeout"}


def _write_q_promptpack_declared_outputs_manifest(dirs: Dict[str, Path]) -> Path:
    manifest_path = dirs["Q"] / "inputs" / "Q_PROMPTPACK_DECLARED_OUTPUTS.json"
    rows: List[Dict[str, Any]] = []
    for phase in PHASES:
        for spec in get_phase_prompts(phase):
            rows.append(
                {
                    "phase": phase,
                    "step_id": spec.step_id,
                    "prompt_file": spec.prompt_path.name,
                    "declared_outputs": list(spec.output_artifacts),
                }
            )
    rows.sort(key=lambda row: (str(row["phase"]), step_sort_key(str(row["step_id"])), str(row["prompt_file"])))
    write_json(manifest_path, {"promptpack_declared_outputs": rows})
    return manifest_path


def _write_s_truth_pack_provenance_manifest(
    dirs: Dict[str, Path],
    input_sources: Dict[Path, str],
) -> Path:
    manifest_path = dirs["S"] / "inputs" / "S_PHASE_TRUTH_PACK_PROVENANCE.json"
    rows: List[Dict[str, Any]] = []
    for path, source_phase in sorted(input_sources.items(), key=lambda row: (row[1], row[0].name, str(row[0]))):
        try:
            size = int(path.stat().st_size)
        except Exception:
            size = 0
        try:
            digest = sha256_file_strict(path)
            sha_value = digest
            sha_reason: Optional[str] = None
        except Exception:
            sha_value = "UNKNOWN"
            sha_reason = "hash_unavailable"
        item: Dict[str, Any] = {
            "source_phase": source_phase,
            "artifact_name": path.name,
            "path": str(path),
            "sha256": sha_value,
            "bytes": size,
        }
        if sha_reason:
            item["sha256_reason"] = sha_reason
        rows.append(item)

    expected_optional = {
        "X": ["FEATURE_INDEX_MERGED.json"],
        "T": ["TP_MERGED.json", "TP_SUMMARY.md"],
        "Z": ["FREEZE_MANIFEST.json", "FREEZE_README.md"],
    }
    seen: Dict[str, Set[str]] = defaultdict(set)
    for row in rows:
        seen[str(row.get("source_phase", ""))].add(str(row.get("artifact_name", "")))
    missing_expected_inputs: List[Dict[str, str]] = []
    for source_phase, names in expected_optional.items():
        for name in names:
            if name not in seen.get(source_phase, set()):
                missing_expected_inputs.append(
                    {
                        "artifact_name": name,
                        "reason": f"not present in {source_phase}/norm",
                    }
                )
    missing_expected_inputs.sort(key=lambda row: (row["artifact_name"], row["reason"]))
    write_json(
        manifest_path,
        {
            "truth_pack_inputs": rows,
            "missing_expected_inputs": missing_expected_inputs,
        },
    )
    return manifest_path


def run_batch_watch(
    *,
    root: Path,
    run_id: str,
    phase: str,
    dirs: Dict[str, Path],
    cfg: RunnerConfig,
    ui: Optional[UI] = None,
) -> BatchWatchResult:
    phase_id = str(phase or "").upper()
    if phase_id not in PHASES:
        logger.error("Batch watcher requires a concrete phase in PHASES. Got: %s", phase)
        return BatchWatchResult(exit_code=1)
    phase_dir = dirs[phase_id]
    batch_dir = phase_dir / "batch"
    index_path = batch_dir / "BATCH_JOB_INDEX.json"
    jobs = _read_batch_job_rows(index_path)
    if not jobs:
        logger.error("Batch watcher found no jobs at %s", index_path)
        return BatchWatchResult(exit_code=1)

    jobs = sorted(
        [row for row in jobs if str(row.get("phase_id", "")).upper() == phase_id],
        key=_batch_job_sort_key,
    )
    if not jobs:
        logger.error("Batch watcher found no jobs for phase %s in %s", phase_id, index_path)
        return BatchWatchResult(exit_code=1)

    prompts_by_step = {spec.step_id: spec for spec in get_phase_prompts(phase_id)}
    partitions = _phase_partitions_from_inputs(phase_dir)
    partition_ids = {str(row["id"]) for row in partitions}
    step_stats: Dict[str, Dict[str, int]] = defaultdict(lambda: {"recomputed": 0, "failed": 0})
    steps_touched: Set[str] = set()
    webhook_failures = 0

    for row in jobs:
        step_id = str(row.get("step_id", "")).strip()
        partition_id = str(row.get("partition_id", "")).strip()
        provider_id = str(row.get("provider_id", "")).strip().lower()
        model_id = str(row.get("model_id", "")).strip()
        api_key_env = str(row.get("api_key_env", "")).strip() or PROVIDER_API_KEY_ENV.get(provider_id, "")
        job_id = str(row.get("job_id", "")).strip()
        if not (step_id and partition_id and provider_id and model_id and job_id):
            row["state"] = "failed"
            row["error"] = "invalid_job_manifest_row"
            row["completed_at_utc"] = now_iso()
            continue

        prompt_spec = prompts_by_step.get(step_id)
        if prompt_spec is None:
            row["state"] = "failed"
            row["error"] = "missing_prompt_spec_for_step"
            row["completed_at_utc"] = now_iso()
            continue

        output_artifacts = prompt_spec.output_artifacts
        current_state = str(row.get("state", "submitted")).strip().lower() or "submitted"
        if _batch_terminal_state(current_state) and row.get("results_applied"):
            continue

        steps_touched.add(step_id)
        raw_dir = phase_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)
        out_json = raw_dir / f"{step_id}__{partition_id}.json"
        out_failed = raw_dir / f"{step_id}__{partition_id}.FAILED.txt"
        out_failed_json = raw_dir / f"{step_id}__{partition_id}.FAILED.json"

        api_key, _ = resolve_api_key(provider_id, api_key_env)
        if not api_key:
            row["state"] = "failed"
            row["error"] = f"missing_api_key:{api_key_env}"
            row["completed_at_utc"] = now_iso()
            step_stats[step_id]["recomputed"] += 1
            step_stats[step_id]["failed"] += 1
            continue

        batch_client = build_batch_client(provider_id, api_key, cfg)
        terminal_status = current_state
        if not _batch_terminal_state(current_state):
            poll_started = time.time()
            while True:
                terminal_status = str(batch_client.poll(job_id) or "").lower().strip()
                if _batch_terminal_state(terminal_status):
                    break
                if time.time() - poll_started >= float(cfg.batch_wait_timeout_seconds):
                    terminal_status = "timeout"
                    try:
                        batch_client.cancel(job_id)
                    except Exception as exc:
                        logger.debug("Failed to cancel batch job %s after timeout: %s", job_id, exc)
                    break
                if ui is not None:
                    ui.batch_event(
                        phase=phase_id,
                        step_id=step_id,
                        status="watch_poll",
                        provider=provider_id,
                        details=f"partition={partition_id} state={terminal_status or 'pending'}",
                    )
                time.sleep(max(1, int(cfg.batch_poll_seconds)))

        artifacts_written: List[str] = []
        artifacts_missing: List[str] = []
        event_detail = f"state={terminal_status}"
        row["state"] = terminal_status
        row["last_polled_at_utc"] = now_iso()

        if terminal_status in {"completed", "succeeded", "done"}:
            results = batch_client.fetch_results(job_id)
            results_by_partition = {str(result.custom_id): result for result in results}
            result = results_by_partition.get(partition_id)
            if result is None:
                row["state"] = "failed"
                row["error"] = "batch_missing_result_for_partition"
                row["completed_at_utc"] = now_iso()
                artifacts_missing = list(output_artifacts)
                step_stats[step_id]["recomputed"] += 1
                step_stats[step_id]["failed"] += 1
                out_failed.write_text("batch_missing_result_for_partition\n", encoding="utf-8")
                write_json(
                    out_failed_json,
                    {
                        "phase": phase_id,
                        "step_id": step_id,
                        "partition_id": partition_id,
                        "generated_at": now_iso(),
                        "failure_type": "provider",
                        "status_code": None,
                        "request_meta": {
                            "execution_mode": "batch_watch",
                            "provider": provider_id,
                            "model_id": model_id,
                            "batch_provider": provider_id,
                            "batch_job_id": job_id,
                        },
                    },
                )
            else:
                response_text = str(result.output_text or "")
                parsed = parse_json_from_response(response_text)
                artifacts = coerce_artifacts_from_response(
                    parsed=parsed,
                    raw_text=response_text,
                    expected_artifacts=output_artifacts,
                )
                schema_ok, schema_reason = artifacts_pass_schema_gate(artifacts, output_artifacts)
                step_stats[step_id]["recomputed"] += 1
                if not artifacts or not schema_ok or result.error:
                    row["state"] = "failed"
                    row["error"] = result.error or schema_reason or "batch_parse_failure"
                    row["completed_at_utc"] = now_iso()
                    artifacts_missing = list(output_artifacts)
                    step_stats[step_id]["failed"] += 1
                    out_failed.write_text(response_text or (result.error or "batch_parse_failure"), encoding="utf-8")
                    write_json(
                        out_failed_json,
                        {
                            "phase": phase_id,
                            "step_id": step_id,
                            "partition_id": partition_id,
                            "generated_at": now_iso(),
                            "failure_type": "parse" if not result.error else "provider",
                            "status_code": None,
                            "request_meta": {
                                "execution_mode": "batch_watch",
                                "provider": provider_id,
                                "model_id": model_id,
                                "batch_provider": provider_id,
                                "batch_job_id": job_id,
                                "provider_error_reason": result.error,
                                "schema_gate_reason": schema_reason,
                            },
                        },
                    )
                else:
                    row["state"] = "completed"
                    row["error"] = None
                    row["completed_at_utc"] = now_iso()
                    row["results_applied"] = True
                    artifacts_written = sorted(
                        {
                            str(artifact.get("artifact_name", "")).strip()
                            for artifact in artifacts
                            if isinstance(artifact, dict)
                        }
                    )
                    request_meta = enrich_request_meta(
                        {
                            "provider": provider_id,
                            "model_id": model_id,
                            "status_code": 200,
                            "failure_type": None,
                            "provider_error_reason": None,
                            "execution_mode": "batch_watch",
                            "batch_provider": provider_id,
                            "batch_job_id": job_id,
                            "response_summary": {
                                "batch_status": terminal_status,
                                "watch_mode": True,
                            },
                        },
                        run_id=run_id,
                        phase=phase_id,
                        step_id=step_id,
                        partition_id=partition_id,
                        provider=provider_id,
                        model_id=model_id,
                    )
                    write_json(
                        out_json,
                        {
                            "phase": phase_id,
                            "step_id": step_id,
                            "partition_id": partition_id,
                            "generated_at": now_iso(),
                            "artifacts": artifacts,
                            "request_meta": request_meta,
                        },
                    )
                    if out_failed.exists():
                        out_failed.unlink()
                    if out_failed_json.exists():
                        out_failed_json.unlink()
            event_detail = f"state={row.get('state')}"
        else:
            row["completed_at_utc"] = now_iso()
            artifacts_missing = list(output_artifacts)
            step_stats[step_id]["recomputed"] += 1
            step_stats[step_id]["failed"] += 1
            write_json(
                out_failed_json,
                {
                    "phase": phase_id,
                    "step_id": step_id,
                    "partition_id": partition_id,
                    "generated_at": now_iso(),
                    "failure_type": "timeout" if terminal_status == "timeout" else "provider",
                    "status_code": None,
                    "request_meta": {
                        "execution_mode": "batch_watch",
                        "provider": provider_id,
                        "model_id": model_id,
                        "batch_provider": provider_id,
                        "batch_job_id": job_id,
                        "provider_error_reason": f"batch_terminal_state:{terminal_status}",
                    },
                },
            )
            out_failed.write_text(f"batch_terminal_state:{terminal_status}\n", encoding="utf-8")

        row["updated_at_utc"] = now_iso()
        webhook_ok = maybe_send_batch_webhook(
            cfg=cfg,
            root=root,
            run_id=run_id,
            phase_id=phase_id,
            phase_dir=phase_dir,
            step_id=step_id,
            provider_id=provider_id,
            model_id=model_id,
            job_id=job_id,
            state=str(row.get("state", "unknown")),
            detail=event_detail,
            artifacts_written=artifacts_written,
            artifacts_missing=artifacts_missing,
        )
        if not webhook_ok:
            webhook_failures += 1

        if partition_id not in partition_ids:
            partitions.append({"id": partition_id, "paths": []})
            partition_ids.add(partition_id)

    jobs = sorted(jobs, key=_batch_job_sort_key)
    write_json(
        index_path,
        {
            "run_id": run_id,
            "phase_id": phase_id,
            "updated_at_utc": now_iso(),
            "jobs": jobs,
        },
    )
    write_json(
        batch_dir / "BATCH_JOB.json",
        {
            "run_id": run_id,
            "phase_id": phase_id,
            "updated_at_utc": now_iso(),
            "jobs": jobs,
        },
    )

    jobs_by_step: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for row in jobs:
        step_id = str(row.get("step_id", "")).strip()
        if not step_id:
            continue
        jobs_by_step[step_id].append(row)
    for step_id, step_jobs in jobs_by_step.items():
        write_json(
            batch_dir / f"{step_id}.job.json",
            {
                "generated_at": now_iso(),
                "run_id": run_id,
                "phase": phase_id,
                "step_id": step_id,
                "jobs": sorted(step_jobs, key=_batch_job_sort_key),
            },
        )

    if not partitions:
        partitions = [{"id": str(row.get("partition_id")), "paths": []} for row in jobs if row.get("partition_id")]

    for step_id in sorted(steps_touched, key=step_sort_key):
        prompt_spec = prompts_by_step.get(step_id)
        if prompt_spec is None:
            continue
        stats = step_stats.get(step_id, {"recomputed": 0, "failed": 0})
        normalize_step(
            phase=phase_id,
            prompt_spec=prompt_spec,
            phase_dir=phase_dir,
            partitions=partitions,
            step_exec_stats={
                "resume_skipped": 0,
                "recomputed": int(stats.get("recomputed", 0)),
                "dry_run": 0,
                "failed": int(stats.get("failed", 0)),
            },
        )

    auto_continue_blocked = False
    next_phase = None
    if cfg.webhook_auto_continue:
        if cfg.live_ok:
            next_phase = next_phase_id(phase_id)
        else:
            auto_continue_blocked = True
            logger.info(
                "AUTO_CONTINUE_BLOCKED phase=%s reason=live_guard env=%s",
                phase_id,
                DPMX_LIVE_OK_ENV,
            )
    exit_code = 1 if (cfg.webhook_required and webhook_failures > 0) else 0
    return BatchWatchResult(
        exit_code=exit_code,
        next_phase=next_phase,
        auto_continue_blocked=auto_continue_blocked,
    )


def _ensure_required_norm_artifact_groups(dirs: Dict[str, Path]) -> List[str]:
    missing: List[str] = []
    for phase, groups in R_REQUIRED_ARTIFACT_GROUPS.items():
        norm_dir = dirs[phase] / "norm"
        if not norm_dir.exists():
            missing.append(f"{phase}: missing norm directory {norm_dir}")
            continue
        for group in groups:
            if not any(_has_matching_file(norm_dir, pattern) for pattern in group):
                pattern_desc = " or ".join(group)
                missing.append(f"{phase}: no artifact matching {pattern_desc} under {norm_dir}")
    return missing


def run_phase_A(dirs: Dict[str, Path], cfg: RunnerConfig, ui: Optional[UI] = None) -> None:
    excludes = [
        ".git",
        "node_modules",
        "venv",
        ".venv",
        "src",
        "services",
        "tests",
        "docs",
        "extraction",
        "reports",
        "tmp",
        "_audit_out",
        "SYSTEM_ARCHIVE",
        "*.zip",
    ]
    collector = Collector(Path.cwd(), excludes)
    targets = [
        ".claude",
        ".dopemux",
        ".githooks",
        ".github",
        ".taskx",
        "config",
        "scripts",
        "tools",
        "compose",
        "docker",
        "AGENTS.md",
        "README.md",
        "QUICK_START.md",
        "INSTALL.md",
        "CHANGELOG.md",
        "pyproject.toml",
        "dopemux.toml",
        "compose.yml",
        "compose.yml",
        "Makefile",
        ".claude.json",
        ".taskxroot",
    ]
    _run_phase_inner("A", dirs, cfg, collector, targets, ui=ui)


def run_phase_H(dirs: Dict[str, Path], cfg: RunnerConfig, ui: Optional[UI] = None) -> None:
    home = Path.home()
    excludes = [
        "Downloads",
        "Library",
        "Documents",
        "Pictures",
        "Music",
        "Public",
        "Desktop",
        ".cache",
        ".npm",
        ".pip",
    ]
    collector = Collector(home, excludes)
    items = collector.collect(subdirs=HOME_SAFE_ROOTS)
    if cfg.home_scan_mode == "safe":
        items = home_safe_filter(items, home)
    _run_phase_inner("H", dirs, cfg, None, None, precollected_items=items, ui=ui)


def run_phase_C(dirs: Dict[str, Path], cfg: RunnerConfig, ui: Optional[UI] = None) -> None:
    collector = Collector(Path.cwd(), [".git", "node_modules", "venv", ".venv", "docs", "test-results"])
    targets = ["src", "services", "shared", "plugins", "tools", "scripts", "tests"]
    _run_phase_inner("C", dirs, cfg, collector, targets, ui=ui)


def run_phase_D(dirs: Dict[str, Path], cfg: RunnerConfig, ui: Optional[UI] = None) -> None:
    collector = Collector(Path.cwd(), [".git"])
    _run_phase_inner("D", dirs, cfg, collector, ["docs"], ui=ui)


def run_phase_E(dirs: Dict[str, Path], cfg: RunnerConfig, ui: Optional[UI] = None) -> None:
    collector = Collector(Path.cwd(), [".git", "node_modules", "docs"])
    targets = ["scripts", "tools", "compose", ".github", "Makefile", "package.json"]
    _run_phase_inner("E", dirs, cfg, collector, targets, ui=ui)


def run_phase_W(dirs: Dict[str, Path], cfg: RunnerConfig, ui: Optional[UI] = None) -> None:
    collector = Collector(Path.cwd(), [".git", "node_modules"])
    _run_phase_inner("W", dirs, cfg, collector, ["docs", "scripts", "src", "services"], ui=ui)


def run_phase_B(dirs: Dict[str, Path], cfg: RunnerConfig, ui: Optional[UI] = None) -> None:
    collector = Collector(Path.cwd(), [".git", "node_modules"])
    _run_phase_inner("B", dirs, cfg, collector, ["src", "services", "docs"], ui=ui)


def run_phase_G(dirs: Dict[str, Path], cfg: RunnerConfig, ui: Optional[UI] = None) -> None:
    collector = Collector(Path.cwd(), [".git", "node_modules"])
    _run_phase_inner("G", dirs, cfg, collector, [".github", "docs", ".claude", "AGENTS.md"], ui=ui)


def run_phase_Q(dirs: Dict[str, Path], cfg: RunnerConfig, ui: Optional[UI] = None) -> None:
    items = collect_phase_artifacts(dirs, ["A", "H", "D", "C", "E", "W", "B", "G"], ["raw", "norm", "qa"])
    promptpack_manifest = _write_q_promptpack_declared_outputs_manifest(dirs)
    items.extend(to_items([promptpack_manifest]))
    items.sort(key=lambda item: str(item.get("path", "")))
    _run_phase_inner("Q", dirs, cfg, None, None, precollected_items=items, ui=ui)


# --- TP-WEBHOOKS-0002: Phase R Async Pilot ---

WEBHOOK_DB_URL_ENV = "WEBHOOK_DB_URL"


def _build_event_store_for_runner() -> Any:
    """Lazily import the webhook receiver ledger package and return a ready EventStore.

    This helper ensures (on a best-effort basis) that any pending DB migrations for the
    webhook event store have been applied before constructing the EventStore, mirroring
    the migration behavior used by the main server where possible.
    """
    repo_root = RUNNER_SERVICE_DIR.parents[1]
    webhook_receiver_dir = RUNNER_SERVICE_DIR.parent / "webhook_receiver"
    if str(webhook_receiver_dir) not in sys.path:
        sys.path.insert(0, str(webhook_receiver_dir))
    import storage  # type: ignore[import]

    db_url = storage.resolve_webhook_db_url()

    # Best-effort: attempt to run migrations in the same way the main server does.
    # Prefer calling ensure_migrations() from server.py; if that is not available,
    # fall back to invoking webhook_migrate.py via subprocess. Any failures are
    # logged but do not prevent the runner from continuing.
    try:
        try:
            import server  # type: ignore[import]
        except Exception:
            server = None  # type: ignore[assignment]

        if server is not None and hasattr(server, "ensure_migrations"):
            try:
                server.ensure_migrations(db_url)  # type: ignore[call-arg]
            except Exception:
                logging.exception(
                    "Failed to apply webhook event store migrations via server.ensure_migrations(); proceeding without them."
                )

        if not (server is not None and hasattr(server, "ensure_migrations")):
            migrate_script = repo_root / "scripts" / "webhook_migrate.py"
            if migrate_script.is_file():
                try:
                    subprocess.run(
                        [sys.executable, str(migrate_script), "--db", db_url],
                        check=True,
                    )
                except Exception:
                    logging.exception(
                        "Failed to apply webhook event store migrations via webhook_migrate.py; proceeding without them."
                    )
    except Exception:
        # If migrations cannot be run in this context, fall back to the previous behavior
        # and let build_event_store handle any initialization.
        logging.debug("Migrations not available or failed in runner context; continuing without them.")

    return storage.build_event_store(db_url)


def _extract_openai_response_text(payload: Dict[str, Any]) -> str:
    """Extract plain text content from an OpenAI response.completed webhook payload."""
    data = payload.get("data")
    if not isinstance(data, dict):
        return ""
    for item in (data.get("output") or []):
        if not isinstance(item, dict):
            continue
        if item.get("type") == "message":
            for block in (item.get("content") or []):
                if isinstance(block, dict) and block.get("type") in ("output_text", "text"):
                    text = block.get("text")
                    if text:
                        return str(text)
    # Fallback: direct text field on data
    direct = data.get("text")
    return str(direct) if direct else ""


def _phase_r_async_dedupe_key(
    run_id: str, step_id: str, partition_id: str, attempt: int, event_type: str
) -> str:
    return hashlib.sha256(
        f"openai|{run_id}|R|{step_id}|{partition_id}|{attempt}|{event_type}".encode("utf-8")
    ).hexdigest()


def run_phase_R_async_submit(
    run_id: str,
    dirs: Dict[str, Path],
    cfg: RunnerConfig,
) -> int:
    """TP-WEBHOOKS-0002: Submit Phase R partitions asynchronously via OpenAI Responses API.

    Writes async_jobs + run_events(request.pending) rows and PENDING placeholder artifacts.
    Does NOT wait for completion.  Returns count of newly-submitted partitions.
    """
    missing = _ensure_required_norm_artifact_groups(dirs)
    if missing:
        raise RuntimeError(
            "Phase R async submit requires norm inputs from A/H/D/C. Missing: " + "; ".join(missing)
        )

    input_files: List[Path] = []
    for phase in R_REQUIRED_INPUT_PHASES:
        phase_norm = dirs[phase] / "norm"
        if phase_norm.exists():
            input_files.extend(sorted(phase_norm.glob("*.json")))
            input_files.extend(sorted(phase_norm.glob("*.md")))
    deduped_inputs = sorted(set(input_files), key=str)
    context_items = to_items(deduped_inputs)
    inventory = build_inventory(context_items, cfg.file_truncate_chars)
    max_files = max_files_for_phase("R", cfg)
    partitions = build_partitions("R", inventory, max_files=max_files, max_chars=cfg.max_chars)
    prompts = get_phase_prompts("R")
    if not prompts:
        raise RuntimeError("No prompts found for phase R")

    try:
        from openai import OpenAI  # type: ignore[import]
    except Exception as exc:
        raise RuntimeError("openai SDK required for --async-provider openai") from exc

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is required for --async-provider openai")

    # Determine model: prefer synthesis tier OpenAI route
    route_info = resolve_effective_step_route("R", prompts[0].step_id, cfg)
    model_id = str(route_info["model_id"]) if route_info.get("provider") == "openai" else "gpt-4o-mini"

    client = OpenAI(api_key=api_key)
    event_store = _build_event_store_for_runner()
    phase_dir = dirs["R"]
    raw_dir = phase_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    (phase_dir / "inputs").mkdir(parents=True, exist_ok=True)
    write_json(
        phase_dir / "inputs" / "INVENTORY.json",
        {"phase": "R", "generated_at": now_iso(), "items": inventory},
    )

    submitted = 0

    for prompt_spec in prompts:
        step_id = prompt_spec.step_id
        prompt_text = safe_read(prompt_spec.prompt_path)
        if not prompt_text:
            logger.warning("Async R: empty prompt for step %s, skipping", step_id)
            continue
        output_artifacts = prompt_spec.output_artifacts
        output_instructions = build_output_envelope_instructions(output_artifacts)
        prompt_prefix = "Extract from the files below.\n" + output_instructions + "\n\nFILES:\n"

        for partition in partitions:
            partition_id = str(partition["id"])

            latest_attempt = event_store.latest_attempt_for_tuple(
                run_id=run_id, phase="R", step_id=step_id, partition_id=partition_id
            )
            attempt = (latest_attempt or 0) + 1

            out_json = raw_dir / f"{step_id}__{partition_id}.json"
            pending_path = raw_dir / f"{step_id}__{partition_id}.PENDING.json"

            # Idempotency: skip if already finalized
            if out_json.exists():
                try:
                    _p = json.loads(out_json.read_text(encoding="utf-8"))
                    if _p.get("status") != "pending" and isinstance(_p.get("artifacts"), list):
                        logger.info("Async R: %s/%s already finalized, skipping", step_id, partition_id)
                        continue
                except Exception as exc:
                    logger.debug("Async R: failed to parse idempotency artifact %s: %s", out_json, exc)

            context_budget = max(cfg.max_chars - len(prompt_prefix), 2048)
            context, _ = build_partition_context(
                phase="R",
                partition_paths=partition["paths"],
                file_truncate_chars=cfg.file_truncate_chars,
                home_scan_mode=cfg.home_scan_mode,
                max_files=max_files,
                max_chars=context_budget,
            )
            user_prompt = f"{prompt_prefix}{context}"

            metadata_dict = {
                "run_id": run_id,
                "phase": "R",
                "step_id": step_id,
                "partition_id": partition_id,
                "attempt": str(attempt),
            }

            try:
                response = client.responses.create(
                    model=model_id,
                    instructions=prompt_text,
                    input=user_prompt,
                    metadata=metadata_dict,
                )
                external_job_id = str(response.id)
                logger.info(
                    "Async R submitted provider=openai step=%s partition=%s response_id=%s",
                    step_id,
                    partition_id,
                    external_job_id,
                )
            except Exception as exc:
                logger.error(
                    "Async R submit failed step=%s partition=%s error=%s",
                    step_id,
                    partition_id,
                    exc,
                )
                write_json(
                    raw_dir / f"{step_id}__{partition_id}.FAILED.json",
                    {
                        "phase": "R",
                        "step_id": step_id,
                        "partition_id": partition_id,
                        "generated_at": now_iso(),
                        "failure_type": "async_submit_error",
                        "request_meta": {
                            "failure_type": "async_submit_error",
                            "error": str(exc)[:500],
                        },
                    },
                )
                continue

            from ledger.interface import AsyncJobInsert, RunEventInsert  # type: ignore[import]

            event_store.register_async_job(
                AsyncJobInsert(
                    provider="openai",
                    job_kind="responses_async",
                    external_job_id=external_job_id,
                    run_id=run_id,
                    phase="R",
                    step_id=step_id,
                    partition_id=partition_id,
                    attempt=attempt,
                    status="submitted",
                )
            )
            event_store.append_run_event(
                RunEventInsert(
                    run_id=run_id,
                    phase="R",
                    step_id=step_id,
                    partition_id=partition_id,
                    provider="openai",
                    event_type="request.pending",
                    event_id=None,
                    provider_ref=external_job_id,
                    webhook_event_id=None,
                    dedupe_key=_phase_r_async_dedupe_key(run_id, step_id, partition_id, attempt, "request.pending"),
                    orphaned=False,
                )
            )
            write_json(
                pending_path,
                {
                    "phase": "R",
                    "step_id": step_id,
                    "partition_id": partition_id,
                    "generated_at": now_iso(),
                    "status": "pending",
                    "external_job_id": external_job_id,
                    "attempt": attempt,
                    "artifacts": [],
                    "request_meta": {
                        "provider": "openai",
                        "model_id": model_id,
                        "execution_mode": "async",
                        "external_job_id": external_job_id,
                    },
                },
            )
            submitted += 1

    logger.info("Async R submit complete: submitted=%s", submitted)
    return submitted


def _fetch_webhook_payload_for_job(event_store: Any, run_id: str, provider_ref: str) -> Dict[str, Any]:
    """Retrieve the raw webhook payload JSON for a given provider_ref from the ledger."""
    fetch_fn = getattr(event_store, "fetch_webhook_payload", None)
    if not callable(fetch_fn):
        return {}

    try:
        # The EventStore is responsible for any backend-specific querying.
        payload = fetch_fn(provider="openai", run_id=run_id, provider_ref=provider_ref)
    except Exception:
        return {}

    if isinstance(payload, dict):
        return payload

    if isinstance(payload, str):
        payload_json = payload
    else:
        # Unsupported payload type
        return {}

    if not payload_json:
        return {}
    try:
        return json.loads(payload_json)
    except Exception:
        return {}


def run_phase_R_finalize(
    run_id: str,
    dirs: Dict[str, Path],
    cfg: RunnerConfig,
) -> int:
    """TP-WEBHOOKS-0002: Finalize Phase R from ledger webhook completions.

    For each pending async_job (run_id, phase=R, provider=openai):
      - If webhook completion received and this is the latest attempt: write raw output.
      - If stale attempt (superseded by a newer one): mark orphaned, skip output.
    Idempotent: already-written outputs are not re-written.
    Returns count of newly-finalized partitions.
    """
    event_store = _build_event_store_for_runner()
    phase_dir = dirs["R"]
    raw_dir = phase_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    pending_jobs = event_store.list_pending_jobs(provider="openai", run_id=run_id, phase="R")
    if not pending_jobs:
        logger.info("Finalize R: no pending jobs for run_id=%s", run_id)
        return 0

    completed_refs = set(
        event_store.list_completed_provider_refs(provider="openai", run_id=run_id, phase="R")
    )
    prompts_list = get_phase_prompts("R")
    artifacts_by_step: Dict[str, Tuple[str, ...]] = {ps.step_id: ps.output_artifacts for ps in prompts_list}

    finalized = 0
    for job in pending_jobs:
        step_id = str(job.get("step_id") or "")
        partition_id = str(job.get("partition_id") or "")
        attempt = int(job.get("attempt") or 1)
        external_job_id = str(job.get("external_job_id") or "")
        if not (step_id and partition_id and external_job_id):
            logger.warning("Finalize R: malformed job row, skipping: %s", job)
            continue

        out_json = raw_dir / f"{step_id}__{partition_id}.json"

        # Idempotency: already finalized with non-pending output
        if out_json.exists():
            try:
                _p = json.loads(out_json.read_text(encoding="utf-8"))
                if _p.get("status") != "pending" and isinstance(_p.get("artifacts"), list):
                    logger.info("Finalize R: %s/%s already written, marking completed", step_id, partition_id)
                    event_store.update_async_job_status(
                        provider="openai",
                        external_job_id=external_job_id,
                        attempt=attempt,
                        status="completed",
                        last_error=None,
                    )
                    continue
            except Exception as exc:
                logger.debug("Finalize R: failed to parse idempotency artifact %s: %s", out_json, exc)

        # Not yet completed via webhook
        if external_job_id not in completed_refs:
            logger.info(
                "Finalize R: no completion event yet step=%s partition=%s response_id=%s",
                step_id,
                partition_id,
                external_job_id,
            )
            continue

        # Reconciliation: check latest attempt
        latest_attempt = event_store.latest_attempt_for_tuple(
            run_id=run_id,
            phase="R",
            step_id=step_id,
            partition_id=partition_id,
        )
        if latest_attempt is not None and attempt < latest_attempt:
            logger.info(
                "Finalize R: orphaning stale attempt=%s latest=%s step=%s partition=%s",
                attempt,
                latest_attempt,
                step_id,
                partition_id,
            )
            event_store.update_async_job_status(
                provider="openai",
                external_job_id=external_job_id,
                attempt=attempt,
                status="orphaned",
                last_error="stale_attempt",
            )
            continue

        # Fetch and parse webhook payload
        webhook_payload = _fetch_webhook_payload_for_job(event_store, run_id, external_job_id)
        response_text = _extract_openai_response_text(webhook_payload)
        parsed = parse_json_from_response(response_text) if response_text else None
        expected_artifacts = artifacts_by_step.get(step_id, ("R_ARBITRATION.json",))
        artifacts = coerce_artifacts_from_response(parsed, response_text or "", expected_artifacts)

        write_json(
            out_json,
            {
                "phase": "R",
                "step_id": step_id,
                "partition_id": partition_id,
                "generated_at": now_iso(),
                "artifacts": artifacts,
                "request_meta": {
                    "provider": "openai",
                    "execution_mode": "async",
                    "external_job_id": external_job_id,
                    "attempt": attempt,
                },
            },
        )

        # Remove pending placeholder
        pending_path = raw_dir / f"{step_id}__{partition_id}.PENDING.json"
        if pending_path.exists():
            try:
                pending_path.unlink()
            except Exception as exc:
                logger.warning("Failed to remove pending placeholder %s: %s", pending_path, exc)

        event_store.update_async_job_status(
            provider="openai",
            external_job_id=external_job_id,
            attempt=attempt,
            status="completed",
            last_error=None,
        )
        logger.info(
            "Finalize R: wrote output step=%s partition=%s artifacts=%s",
            step_id,
            partition_id,
            len(artifacts),
        )
        finalized += 1

    logger.info(
        "Finalize R complete: finalized=%s of %s pending", finalized, len(pending_jobs)
    )
    return finalized


def run_phase_R(dirs: Dict[str, Path], cfg: RunnerConfig, ui: Optional[UI] = None) -> None:
    missing = _ensure_required_norm_artifact_groups(dirs)
    if missing:
        raise RuntimeError(
            "Phase R requires normalized inputs from A/H/D/C. Missing norm artifacts: "
            + "; ".join(missing)
        )

    input_files: List[Path] = []
    for phase in R_REQUIRED_INPUT_PHASES:
        phase_norm = dirs[phase] / "norm"
        if phase_norm.exists():
            input_files.extend(sorted(phase_norm.glob("*.json")))
            input_files.extend(sorted(phase_norm.glob("*.md")))

    deduped_inputs = sorted(set(input_files), key=str)
    _run_phase_inner("R", dirs, cfg, None, None, precollected_items=to_items(deduped_inputs), ui=ui)


def run_phase_X(dirs: Dict[str, Path], cfg: RunnerConfig, ui: Optional[UI] = None) -> None:
    r_norm = dirs["R"] / "norm"
    r_inputs: List[Path] = []
    if r_norm.exists():
        r_inputs.extend(sorted(r_norm.glob("*.json")))
        r_inputs.extend(sorted(r_norm.glob("*.md")))
    if not r_inputs:
        raise RuntimeError(f"Phase X requires R norm outputs at {r_norm}")
    _run_phase_inner("X", dirs, cfg, None, None, precollected_items=to_items(r_inputs), ui=ui)


def run_phase_T(dirs: Dict[str, Path], cfg: RunnerConfig, ui: Optional[UI] = None) -> None:
    input_files: List[Path] = []
    for phase in ["R", "X"]:
        norm_dir = dirs[phase] / "norm"
        if norm_dir.exists():
            input_files.extend(sorted(norm_dir.glob("*.json")))
            input_files.extend(sorted(norm_dir.glob("*.md")))
    _run_phase_inner("T", dirs, cfg, None, None, precollected_items=to_items(input_files), ui=ui)


def run_phase_S(dirs: Dict[str, Path], cfg: RunnerConfig, ui: Optional[UI] = None) -> None:
    r_norm = dirs["R"] / "norm"
    input_sources: Dict[Path, str] = {}
    if r_norm.exists():
        for path in sorted(r_norm.glob("*.json")) + sorted(r_norm.glob("*.md")):
            input_sources[path.resolve()] = "R"
    if not input_sources:
        raise RuntimeError(f"Phase S requires R norm outputs at {r_norm}")

    for phase in ["X", "T", "Z"]:
        norm_dir = dirs[phase] / "norm"
        if norm_dir.exists():
            for path in sorted(norm_dir.glob("*.json")) + sorted(norm_dir.glob("*.md")):
                input_sources.setdefault(path.resolve(), phase)

    manual_rulings_dir = dirs["root"] / "manual_rulings"
    if manual_rulings_dir.exists():
        for path in sorted(manual_rulings_dir.glob("PRO_*.json")):
            input_sources.setdefault(path.resolve(), "MANUAL")

    deduped_inputs = sorted(input_sources.keys(), key=str)
    truth_pack_manifest = _write_s_truth_pack_provenance_manifest(dirs, input_sources)
    precollected_files = deduped_inputs + [truth_pack_manifest]
    _run_phase_inner("S", dirs, cfg, None, None, precollected_items=to_items(precollected_files), ui=ui)


def run_phase_Z(dirs: Dict[str, Path], cfg: RunnerConfig, ui: Optional[UI] = None) -> None:
    final_items = collect_phase_artifacts(dirs, ["R", "X", "T"], ["raw", "norm", "qa"])
    _run_phase_inner("Z", dirs, cfg, None, None, precollected_items=final_items, ui=ui)


# --- Master Orchestrator ---

def main() -> None:
    try:
        signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    except (AttributeError, ValueError):
        pass
    parser = argparse.ArgumentParser("Master Extraction Runner")
    parser.add_argument("--phase", choices=PHASES + ["ALL"], required=False)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-files-docs", type=int, default=35)
    parser.add_argument("--max-files-code", type=int, default=20)
    parser.add_argument("--max-chars", type=int, default=650000)
    parser.add_argument("--max-request-bytes", type=int, default=200000)
    parser.add_argument("--file-truncate-chars", type=int, default=70000)
    parser.add_argument("--home-scan-mode", choices=["safe", "full"], default="safe")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--fail-fast-auth", dest="fail_fast_auth", action="store_true", default=True)
    parser.add_argument("--no-fail-fast-auth", dest="fail_fast_auth", action="store_false")
    parser.add_argument(
        "--gemini-auth-mode",
        choices=["api_key", "bearer", "both", "query_key", "auto"],
        default="auto",
    )
    parser.add_argument(
        "--gemini-model-id",
        type=str,
        default=DEFAULT_GEMINI_MODEL_ID,
        help="Override Gemini model ID for all Gemini-routed phases.",
    )
    parser.add_argument(
        "--routing-policy",
        choices=["cost", "balanced", "quality"],
        default=DEFAULT_ROUTING_POLICY,
    )
    parser.add_argument("--disable-escalation", action="store_true")
    parser.add_argument("--escalation-max-hops", type=int, default=2)
    parser.add_argument("--batch-mode", action="store_true")
    parser.add_argument(
        "--batch-submit-only",
        action="store_true",
        help="Submit batch jobs and persist metadata without inline polling/fetch.",
    )
    parser.add_argument(
        "--batch-watch",
        action="store_true",
        help="Poll submitted batch jobs, fetch results, and emit webhook notifications.",
    )
    parser.add_argument(
        "--batch-provider",
        choices=["auto", "openai", "gemini", "xai"],
        default="auto",
    )
    parser.add_argument("--batch-poll-seconds", type=int, default=30)
    parser.add_argument("--batch-wait-timeout-seconds", type=int, default=86400)
    parser.add_argument("--batch-max-requests-per-job", type=int, default=2000)
    parser.add_argument(
        "--gemini-transport",
        choices=["sdk", "openai_compat_http"],
        default="sdk",
    )
    parser.add_argument(
        "--openai-transport",
        choices=["openai_sdk"],
        default="openai_sdk",
    )
    parser.add_argument(
        "--xai-transport",
        choices=["openai_sdk"],
        default="openai_sdk",
    )
    parser.add_argument("--retry-policy", choices=["none", "default"], default="default")
    parser.add_argument("--retry-max-attempts", type=int, default=4)
    parser.add_argument("--retry-base-seconds", type=float, default=2.0)
    parser.add_argument("--retry-max-seconds", type=float, default=30.0)
    parser.add_argument("--phase-auth-fail-threshold", type=int, default=5)
    parser.add_argument("--partition-workers", type=int, default=1)
    parser.add_argument("--debug-phase-inputs", action="store_true")
    parser.add_argument("--fail-fast-missing-inputs", action="store_true")
    parser.add_argument("--run-id", type=str)
    parser.add_argument("--no-write-latest", action="store_true")
    parser.add_argument("--write-latest-even-on-dry-run", action="store_true")
    parser.add_argument("--doctor", action="store_true")
    parser.add_argument("--doctor-auth", action="store_true")
    parser.add_argument("--preflight-providers", action="store_true")
    parser.add_argument("--coverage-report", action="store_true")
    parser.add_argument("--ui", choices=["auto", "rich", "plain"], default="auto")
    parser.add_argument("--status", action="store_true")
    parser.add_argument("--status-json", action="store_true")
    parser.add_argument("--watch", type=float)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--jsonl-events", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--print-promptpack", action="store_true")
    parser.add_argument("--print-run-order", action="store_true")
    parser.add_argument("--print-phase-routing", action="store_true")
    parser.add_argument("--tail-run-log", action="store_true")
    parser.add_argument("--tail-lines", type=int, default=200)
    parser.add_argument("--since", type=str, default="")
    parser.add_argument("--step", type=str)
    parser.add_argument("--show-provider-usage", action="store_true")
    parser.add_argument(
        "--print-phase-prompts",
        nargs="?",
        const="ALL",
        type=str,
        help="Print prompt files and declared outputs for PHASE or ALL.",
    )
    parser.add_argument("--verify-phase-output", choices=VERIFY_PHASE_CHOICES)
    parser.add_argument("--print-config", action="store_true")
    parser.add_argument("--gemini-list-models", action="store_true")
    # TP-WEBHOOKS-0002: async pilot flags
    parser.add_argument(
        "--async-provider",
        choices=["openai"],
        default=None,
        help="Submit Phase R partitions asynchronously via the given provider's API.",
    )
    parser.add_argument(
        "--finalize",
        action="store_true",
        help="Finalize Phase R by reading webhook completions from the ledger.",
    )
    promptgen_group = parser.add_argument_group("promptgen")
    promptgen_group.add_argument("--promptgen-scan", action="store_true")
    promptgen_group.add_argument("--promptgen-max-files", type=int, default=PROMPTGEN_DEFAULT_MAX_FILES)
    promptgen_group.add_argument("--promptgen-max-bytes", type=int, default=PROMPTGEN_DEFAULT_MAX_BYTES)
    promptgen_group.add_argument("--promptgen-excerpt-bytes", type=int, default=PROMPTGEN_DEFAULT_EXCERPT_BYTES)
    promptgen_group.add_argument("--promptgen-include-globs", action="append")
    promptgen_group.add_argument("--promptgen-exclude-globs", action="append")
    promptgen_group.add_argument("--promptgen-output-dir", type=str, default=PROMPTGEN_DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    args.partition_workers = max(1, min(16, int(args.partition_workers)))
    if args.pretty and args.ui == "auto":
        args.ui = "rich"
    args.escalation_max_hops = max(0, int(args.escalation_max_hops))
    args.batch_poll_seconds = max(1, int(args.batch_poll_seconds))
    args.batch_wait_timeout_seconds = max(60, int(args.batch_wait_timeout_seconds))
    args.batch_max_requests_per_job = max(1, int(args.batch_max_requests_per_job))
    if args.batch_submit_only:
        args.batch_mode = True
    apply_model_overrides(args.gemini_model_id, args.routing_policy)

    # TP-WEBHOOKS-0002 validation
    if args.async_provider and not args.phase:
        parser.error("--async-provider requires --phase R.")
    if args.async_provider and args.phase != "R":
        parser.error("--async-provider is only supported for --phase R.")
    if args.finalize and not args.phase:
        parser.error("--finalize requires --phase R.")
    if args.finalize and args.phase != "R":
        parser.error("--finalize is only supported for --phase R.")

    if not (
        args.phase
        or args.verify_phase_output
        or args.print_config
        or args.doctor_auth
        or args.preflight_providers
        or args.doctor
        or args.coverage_report
        or args.status
        or args.status_json
        or args.print_promptpack
        or args.print_run_order
        or args.print_phase_routing
        or args.tail_run_log
        or args.show_provider_usage
        or args.print_phase_prompts
        or args.promptgen_scan
        or args.gemini_list_models
    ):
        parser.error(
            "--phase is required unless using --verify-phase-output, --print-config, "
            "--promptgen-scan, --doctor, --doctor-auth, --preflight-providers, --coverage-report, "
            "--status, --status-json, --print-promptpack, --print-run-order, "
            "--print-phase-routing, --tail-run-log, --show-provider-usage, "
            "--print-phase-prompts, or --gemini-list-models."
        )
    if args.watch is not None and args.watch <= 0:
        parser.error("--watch must be > 0 when provided.")
    if args.watch is not None and not (args.status or args.status_json):
        parser.error("--watch requires --status or --status-json.")
    if args.batch_watch and not args.phase:
        parser.error("--batch-watch requires --phase.")
    if args.batch_watch and args.phase == "ALL":
        parser.error("--batch-watch requires a concrete phase, not ALL.")
    if args.batch_watch and args.batch_submit_only:
        parser.error("--batch-watch cannot be combined with --batch-submit-only.")

    root = Path.cwd()
    try:
        allow_create_if_missing = bool(args.promptgen_scan or args.run_id or args.gemini_list_models)
        run_context = resolve_run_context(root, args, allow_create_if_missing=allow_create_if_missing)
        run_id = run_context.run_id
        dirs = get_run_dirs(root, run_id)
    except Exception as exc:
        logger.error("Setup failed: %s", exc)
        sys.exit(1)

    ui = UI(
        UiConfig(
            mode=str(args.ui),
            quiet=bool(args.quiet),
            jsonl_events=bool(args.jsonl_events),
        ),
        dirs["root"],
        run_id,
    )

    if args.promptgen_scan:
        started = time.time()
        out_dir = dirs["root"] / args.promptgen_output_dir
        try:
            promptgen_inputs, project_fingerprint, stats = scan_promptgen_inputs(root, run_id, args)
            promptgen_inputs_path = out_dir / PROMPTGEN_INPUTS_FILENAME
            fingerprint_path = out_dir / PROMPTGEN_FINGERPRINT_FILENAME
            promptgen_inputs_sha = _write_json_with_sha256(promptgen_inputs_path, promptgen_inputs)
            fingerprint_sha = _write_json_with_sha256(fingerprint_path, project_fingerprint)
            elapsed_ms = int((time.time() - started) * 1000)
            logger.info(
                "GX0 promptgen scan complete selected=%s excerpt_bytes=%s excerpt_policy=%s promptgen_inputs_sha=%s fingerprint_sha=%s elapsed_ms=%s",
                stats["selected_files"],
                stats["total_excerpt_bytes"],
                stats["excerpt_policy"],
                promptgen_inputs_sha,
                fingerprint_sha,
                elapsed_ms,
            )
            sys.exit(0)
        except Exception as exc:
            out_dir.mkdir(parents=True, exist_ok=True)
            write_json(
                out_dir / PROMPTGEN_FAILED_FILENAME,
                {
                    "generated_at": now_iso(),
                    "run_id": run_id,
                    "repo_root": str(root.resolve()),
                    "status": "failed",
                    "stage": "promptgen_scan",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
            logger.error("GX0 promptgen scan failed: %s", exc)
            sys.exit(1)
    if args.gemini_list_models:
        sys.exit(run_gemini_list_models(root, run_id, dirs))
    if args.status or args.status_json:
        sys.exit(run_status_loop(run_id, dirs, args, ui=ui))
    if args.tail_run_log:
        sys.exit(
            tail_run_log(
                run_id,
                dirs,
                phase=args.phase,
                step=args.step,
                since=args.since,
                tail_lines=args.tail_lines,
            )
        )
    if args.show_provider_usage:
        sys.exit(show_provider_usage(run_id, dirs, phase=args.phase, step=args.step, since=args.since))

    cfg = RunnerConfig(
        dry_run=args.dry_run,
        max_files_docs=args.max_files_docs,
        max_files_code=args.max_files_code,
        max_chars=args.max_chars,
        max_request_bytes=args.max_request_bytes,
        file_truncate_chars=args.file_truncate_chars,
        home_scan_mode=args.home_scan_mode,
        resume=args.resume,
        fail_fast_auth=args.fail_fast_auth,
        gemini_auth_mode=args.gemini_auth_mode,
        gemini_transport=args.gemini_transport,
        openai_transport=args.openai_transport,
        xai_transport=args.xai_transport,
        retry_policy=args.retry_policy,
        retry_max_attempts=max(1, args.retry_max_attempts),
        retry_base_seconds=max(0.0, args.retry_base_seconds),
        retry_max_seconds=max(0.0, args.retry_max_seconds),
        phase_auth_fail_threshold=max(1, args.phase_auth_fail_threshold),
        partition_workers=args.partition_workers,
        debug_phase_inputs=args.debug_phase_inputs,
        fail_fast_missing_inputs=args.fail_fast_missing_inputs,
        routing_policy=args.routing_policy,
        disable_escalation=bool(args.disable_escalation),
        escalation_max_hops=args.escalation_max_hops,
        batch_mode=bool(args.batch_mode),
        batch_provider=args.batch_provider,
        batch_poll_seconds=args.batch_poll_seconds,
        batch_wait_timeout_seconds=args.batch_wait_timeout_seconds,
        batch_max_requests_per_job=args.batch_max_requests_per_job,
        batch_submit_only=bool(args.batch_submit_only),
        webhook_url=os.getenv(DPMX_WEBHOOK_URL_ENV, "").strip(),
        webhook_secret=os.getenv(DPMX_WEBHOOK_SECRET_ENV, "").strip(),
        webhook_timeout_seconds=_int_env(DPMX_WEBHOOK_TIMEOUT_SECONDS_ENV, 5, minimum=1),
        webhook_required=_env_is_truthy(DPMX_WEBHOOK_REQUIRED_ENV),
        webhook_auto_continue=_env_is_truthy(DPMX_WEBHOOK_AUTO_CONTINUE_ENV),
        live_ok=_env_is_truthy(DPMX_LIVE_OK_ENV),
    )

    phase_sequence = resolve_phase_list(args.phase)
    prompt_report = write_run_manifest(root, dirs, run_id, args, run_context, phase_sequence or PHASES)
    configure_run_file_logger(dirs["root"])
    write_runner_identity(root, dirs["root"], run_id)
    if phase_sequence:
        write_run_routing_fingerprint(dirs["root"], run_id, cfg, phase_sequence)
    run_started_at = now_iso()
    if args.print_config:
        print_config(args, root, run_id, dirs, cfg, phase_sequence, run_context)
        sys.exit(0)
    if args.print_run_order:
        targets = phase_sequence if phase_sequence else PHASES
        sys.exit(print_run_order(targets))
    if args.print_phase_routing:
        targets = phase_sequence if phase_sequence else PHASES
        sys.exit(print_phase_routing(targets, cfg))
    if args.print_phase_prompts is not None:
        token = str(args.print_phase_prompts).strip().upper() if args.print_phase_prompts else "ALL"
        if token == "ALL":
            targets = PHASES
        elif token in PHASES:
            targets = [token]
        else:
            parser.error("--print-phase-prompts expects ALL or a single phase letter.")
        sys.exit(print_phase_prompts(targets))
    should_gate_promptset = bool(phase_sequence) and (
        args.preflight_providers
        or args.doctor
        or not (
            args.doctor_auth
            or args.print_promptpack
            or args.print_run_order
            or args.print_phase_routing
            or args.print_phase_prompts is not None
            or args.coverage_report
            or args.verify_phase_output
        )
    )
    if should_gate_promptset and prompt_report.get("blocked_promptset"):
        apply_promptset_preflight_block(
            root=root,
            dirs=dirs,
            run_id=run_id,
            phases=phase_sequence,
            prompt_report=prompt_report,
            run_started_at=run_started_at,
        )
        logger.error(
            "Run blocked before execution: reason=%s prompt_failures=%s",
            PROMPTSET_BLOCKED_REASON,
            int(prompt_report.get("prompt_failures_count", 0)),
        )
        sys.exit(PROMPTSET_BLOCKED_EXIT_CODE)
    if args.doctor_auth:
        sys.exit(run_auth_doctor(root, args, cfg))
    if args.preflight_providers:
        targets = phase_sequence if phase_sequence else PHASES
        ok, payload = run_provider_preflight(root, run_id, cfg, targets)
        print(json.dumps(payload, indent=2))
        sys.exit(0 if ok else 1)
    if args.print_promptpack:
        targets = phase_sequence if phase_sequence else PHASES
        sys.exit(print_promptpack(targets))
    if args.coverage_report:
        targets = phase_sequence if phase_sequence else PHASES
        for phase in targets:
            write_phase_coverage_manifest(phase, dirs[phase])
        write_coverage_rollup(root, dirs, run_id)
        write_resume_proof(dirs, run_id, targets)
        sys.exit(generate_coverage_report(root, dirs, run_id, targets))

    if args.verify_phase_output:
        verify_targets = PHASES if args.verify_phase_output == "ALL" else [args.verify_phase_output]
        sys.exit(verify_phase_output(dirs, verify_targets, ui=ui))

    if args.doctor:
        targets = phase_sequence if phase_sequence else PHASES
        sys.exit(run_doctor_full(root, dirs, run_id, targets, cfg))

    # TP-WEBHOOKS-0002: async submit / finalize dispatch (Phase R only)
    if args.async_provider == "openai" and not args.finalize:
        try:
            n = run_phase_R_async_submit(run_id=run_id, dirs=dirs, cfg=cfg)
            logger.info("Async R submit complete: submitted=%s run_id=%s", n, run_id)
            sys.exit(0)
        except Exception as exc:
            logger.error("Async R submit failed: %s", exc)
            sys.exit(1)

    if args.finalize:
        try:
            n = run_phase_R_finalize(run_id=run_id, dirs=dirs, cfg=cfg)
            logger.info("Finalize R complete: finalized=%s run_id=%s", n, run_id)
            sys.exit(0)
        except Exception as exc:
            logger.error("Finalize R failed: %s", exc)
            sys.exit(1)

    if args.batch_watch:
        if not phase_sequence or len(phase_sequence) != 1:
            parser.error("--batch-watch requires exactly one phase via --phase.")
        watch_phase = phase_sequence[0]
        watch_result = run_batch_watch(
            root=root,
            run_id=run_id,
            phase=watch_phase,
            dirs=dirs,
            cfg=cfg,
            ui=ui,
        )
        if watch_result.exit_code != 0:
            sys.exit(watch_result.exit_code)
        if watch_result.next_phase:
            logger.info(
                "AUTO_CONTINUE phase=%s next_phase=%s",
                watch_phase,
                watch_result.next_phase,
            )
            phase_sequence = [watch_result.next_phase]
        else:
            sys.exit(watch_result.exit_code)

    logger.info("Target Run ID: %s", run_id)
    logger.info("Home scan mode: %s", cfg.home_scan_mode)

    if not phase_sequence:
        parser.error("--phase is required when running extraction phases.")
    phases = phase_sequence
    if args.phase == "ALL":
        ok, payload = run_provider_preflight(root, run_id, cfg, phases)
        if not ok:
            logger.error(
                "Provider preflight failed before phase ALL. failed_providers=%s. See "
                f"{(V3_DOCTOR_ROOT / 'PROVIDER_PREFLIGHT.json').as_posix()}",
                ",".join(payload.get("failed_providers", [])),
            )
            sys.exit(1)

    runners = {
        "A": run_phase_A,
        "H": run_phase_H,
        "D": run_phase_D,
        "C": run_phase_C,
        "E": run_phase_E,
        "W": run_phase_W,
        "B": run_phase_B,
        "G": run_phase_G,
        "Q": run_phase_Q,
        "R": run_phase_R,
        "X": run_phase_X,
        "T": run_phase_T,
        "Z": run_phase_Z,
        "S": run_phase_S,
    }

    for phase in phases:
        phase_started_at = now_iso()
        run_phase = runners.get(phase)
        if run_phase is None:
            logger.warning("Unknown phase: %s", phase)
            continue
        try:
            run_phase(dirs, cfg, ui=ui)
        except Exception as exc:
            logger.error("Phase %s failed: %s", phase, exc)
            failed_counts = gather_phase_counts(dirs[phase])
            failed_raw = failed_counts.get("raw", {})
            logger.info(
                "PHASE_DONE phase=%s status=FAIL raw_ok=%s raw_failed=%s raw_total=%s norm=%s qa=%s",
                phase,
                int(failed_raw.get("ok", 0)),
                int(failed_raw.get("failed", 0)),
                int(failed_raw.get("total", 0)),
                int(failed_counts.get("norm", 0)),
                int(failed_counts.get("qa", 0)),
            )
            ui.phase_done(
                phase=phase,
                status="FAIL",
                raw_ok=int(failed_raw.get("ok", 0)),
                raw_failed=int(failed_raw.get("failed", 0)),
                raw_total=int(failed_raw.get("total", 0)),
                norm_count=int(failed_counts.get("norm", 0)),
                qa_count=int(failed_counts.get("qa", 0)),
                phase_dir=dirs[phase],
            )
            write_phase_coverage_manifest(phase, dirs[phase])
            write_coverage_rollup(root, dirs, run_id)
            write_resume_proof(dirs, run_id, phases)
            sys.exit(1)
        phase_finished_at = now_iso()
        counts = gather_phase_counts(dirs[phase])
        raw_stats = counts.get("raw", {})
        phase_reasons: List[str] = []
        if counts["inputs"] == 0:
            phase_reasons.append("inputs directory is empty.")
        if counts["raw"]["total"] == 0:
            phase_reasons.append("raw directory has no artifacts.")
        if counts["norm"] == 0:
            phase_reasons.append("norm directory has no json artifacts.")
        if counts["qa"] == 0:
            phase_reasons.append("qa directory has no artifacts.")
        phase_has_any = (
            counts["inputs"] > 0
            or counts["raw"]["total"] > 0
            or counts["norm"] > 0
            or counts["qa"] > 0
        )
        phase_status = _phase_status_badge(counts, phase_reasons, "UNKNOWN", phase_has_any)
        logger.info(
            "PHASE_DONE phase=%s status=%s raw_ok=%s raw_failed=%s raw_total=%s norm=%s qa=%s",
            phase,
            phase_status,
            int(raw_stats.get("ok", 0)),
            int(raw_stats.get("failed", 0)),
            int(raw_stats.get("total", 0)),
            int(counts.get("norm", 0)),
            int(counts.get("qa", 0)),
        )
        ui.phase_done(
            phase=phase,
            status=phase_status,
            raw_ok=int(raw_stats.get("ok", 0)),
            raw_failed=int(raw_stats.get("failed", 0)),
            raw_total=int(raw_stats.get("total", 0)),
            norm_count=int(counts.get("norm", 0)),
            qa_count=int(counts.get("qa", 0)),
            phase_dir=dirs[phase],
        )
        write_phase_coverage_manifest(phase, dirs[phase])
        write_coverage_rollup(root, dirs, run_id)
        write_resume_proof(dirs, run_id, phases)
        update_proof_pack(root, dirs, run_id, run_started_at, phase, counts, phase_started_at, phase_finished_at)


if __name__ == "__main__":
    main()
