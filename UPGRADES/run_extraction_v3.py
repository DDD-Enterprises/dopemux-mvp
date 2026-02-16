#!/usr/bin/env python3
"""
Master extraction runner (A/H/M/D/C/E/W/B/G/Q/R/X/T/Z) with deterministic:
inventory -> partitioning -> per-partition raw outputs -> norm merge -> QA.
"""

import argparse
import fnmatch
import hashlib
import json
import logging
import os
import re
import sqlite3
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
try:
    from lib.chunking import (
        build_file_manifest_hash,
        build_partition_context,
        estimate_tokens_from_text,
        plan_chunks_for_step,
    )
    from lib.retry import (
        is_retryable_exception,
        parse_retry_after_seconds,
        retry_delay_seconds,
        should_retry_status,
    )
    from lib.throttle import ProviderLimiter, ProviderRateConfig
except ImportError:
    from UPGRADES.lib.chunking import (
        build_file_manifest_hash,
        build_partition_context,
        estimate_tokens_from_text,
        plan_chunks_for_step,
    )
    from UPGRADES.lib.retry import (
        is_retryable_exception,
        parse_retry_after_seconds,
        retry_delay_seconds,
        should_retry_status,
    )
    from UPGRADES.lib.throttle import ProviderLimiter, ProviderRateConfig

# --- Configuration & Constants ---

PHASES = ["A", "H", "M", "D", "C", "E", "W", "B", "G", "Q", "R", "X", "T", "Z"]
CODE_HEAVY_PHASES = {"C", "E", "Q"}
R_BASE_REQUIRED_INPUT_PHASES = ["A", "H", "D", "C"]
R_FULL_STEP_IDS = tuple(f"R{i}" for i in range(9))
R_PROFILE_MANIFEST_FILES = {
    "base": Path("UPGRADES/R_REQUIRED_ARTIFACT_GROUPS_BASE.json"),
    "full": Path("UPGRADES/R_REQUIRED_ARTIFACT_GROUPS_FULL.json"),
}
DEFAULT_R_REQUIRED_ARTIFACT_GROUPS_BASE: Dict[str, List[Tuple[str, ...]]] = {
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
        ("DOC_INDEX.json",),
        ("DOC_BOUNDARIES.json",),
        ("DOC_INTERFACES.json",),
        ("DOC_WORKFLOWS.json",),
        ("DOC_DECISIONS.json",),
        ("DOC_CITATION_GRAPH.json",),
        ("DOC_COVERAGE_REPORT.json",),
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
DEFAULT_R_REQUIRED_ARTIFACT_GROUPS_FULL_ADDITIONAL: Dict[str, List[Tuple[str, ...]]] = {
    "M": [
        ("M0_RUNTIME_EXPORT_INVENTORY.json",),
        ("M1_SQLITE_SCHEMA_SNAPSHOTS.json",),
        ("M2_SQLITE_TABLE_COUNTS.json",),
        ("M3_CONPORT_EXPORT_SAFE.json",),
        ("M4_DOPE_CONTEXT_EXPORT_SAFE.json",),
        ("M5_MCP_HEALTH_EXPORT_SAFE.json",),
        ("M6_RUNTIME_EXPORT_INDEX.json",),
    ]
}

MODEL_ROUTING = {
    "A": ("gemini", "gemini-2.0-flash-001", "GEMINI_API_KEY"),
    "H": ("gemini", "gemini-2.0-flash-001", "GEMINI_API_KEY"),
    "M": ("gemini", "gemini-2.0-flash-001", "GEMINI_API_KEY"),
    "D": ("gemini", "gemini-2.0-flash-001", "GEMINI_API_KEY"),
    "W": ("gemini", "gemini-2.0-flash-001", "GEMINI_API_KEY"),
    "B": ("gemini", "gemini-2.0-flash-001", "GEMINI_API_KEY"),
    "G": ("gemini", "gemini-2.0-flash-001", "GEMINI_API_KEY"),
    "Z": ("gemini", "gemini-2.0-flash-001", "GEMINI_API_KEY"),
    "C": ("xai", "grok-code-fast-1", "XAI_API_KEY"),
    "E": ("xai", "grok-code-fast-1", "XAI_API_KEY"),
    "Q": ("xai", "grok-code-fast-1", "XAI_API_KEY"),
    "R": ("openai", "gpt-5.2-extended", "OPENAI_API_KEY"),
    "X": ("openai", "gpt-5.2-extended", "OPENAI_API_KEY"),
    "T": ("openai", "gpt-5.2-extended", "OPENAI_API_KEY"),
}

PROVIDER_BASE_URL = {
    "xai": "https://api.x.ai/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai",
    "openai": "https://api.openai.com/v1",
}

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
    r"(?i)\b(api[_-]?key|authorization|bearer|token|secret|password|private[_-]?key|cookie|set-cookie)\b"
)
SECRET_ASSIGN_RE = re.compile(
    r"(?i)^(\s*['\"]?[^:=\n]*?(?:api[_-]?key|authorization|bearer|token|secret|password|private[_-]?key|cookie|set-cookie)"
    r"[^:=\n]*?['\"]?\s*[:=]\s*).*$"
)
LONG_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9+/=_-])[A-Za-z0-9+/=_-]{33,}(?![A-Za-z0-9+/=_-])")
ENV_SECRET_NAME_RE = re.compile(r"\b[A-Z0-9_]*(?:SECRET|TOKEN|KEY)\b")
BEARER_TOKEN_RE = re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}")
PRIVATE_KEY_BEGIN_RE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
PRIVATE_KEY_END_RE = re.compile(r"-----END [A-Z0-9 ]*PRIVATE KEY-----")
CONFIG_KEY_RE = re.compile(r'^\s*["\']?([A-Za-z0-9_.-]{2,})["\']?\s*[:=]')
OUTPUT_FILENAME_RE = re.compile(r"\b[A-Z][A-Z0-9_]+(?:\.partX)?\.(?:json|md)\b")
OUTPUT_SECTION_START_RE = re.compile(
    r"(?i)^(goal(?:s)?|output(?:s)?(?:\s+files?)?|phase\s+[A-Z0-9]+\s+deliverables?)\b"
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
    "T0": ("TP_BACKLOG_TOPN.json", "TP_INDEX.json"),
    "T1": ("TP_PACKETS_TOP10.partX.md", "TP_PACKET_IMPLEMENTATION_INDEX.json"),
}

PRIORITY_TIERS = {
    0: "magic_surfaces",
    1: "active_docs",
    2: "code_surfaces",
    3: "archives",
}

MAGIC_SUBTYPE_ORDER = {
    "instructions": 0,
    "mcp_router_provider": 1,
    "compose_bootstrap": 2,
    "hooks": 3,
    "ci": 4,
    "workflow_launchers": 5,
    "other_magic": 6,
    "instruction_docs": 7,
    "other": 99,
}

TIER0_RESERVE_RATIO = 0.40

REPO_MAGIC_SUBDIRS = [
    ".claude",
    ".dopemux",
    ".taskx",
    ".githooks",
    ".github/workflows",
    "compose",
    "scripts",
    "tools",
]

REPO_MAGIC_EXPLICIT_FILES = [
    "AGENTS.md",
    "CLAUDE.md",
    "claude.md",
    ".claude.json",
    ".taskx-pin",
    ".taskxroot",
    "Makefile",
    "Justfile",
    ".tmux.conf",
]

REPO_MAGIC_GLOBS = [
    ".claude.json*",
    "dopemux.toml*",
    "mcp-proxy-config*.json",
    "mcp-proxy-config*.yaml",
    "mcp-proxy-config*.yml",
    "compose*.yml",
    "docker-compose*.yml",
    "litellm.config*",
    "start-*.sh",
    "tmux-*.yaml",
    "tmux-*.sh",
]

HOME_MAGIC_SUBDIRS = [
    ".dopemux",
    ".config/dopemux",
    ".config/taskx",
    ".config/litellm",
    ".config/mcp",
]

DOC_INSTRUCTION_GLOBS = [
    "docs/**/custom-instructions/**",
    "docs/**/prompts/**",
    "docs/**/llm/**",
    "docs/**/*AGENTS*",
    "docs/**/*agents*",
    "docs/**/*CLAUDE*",
    "docs/**/*claude*",
]


# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("extract_runner")


@dataclass(frozen=True)
class RunnerConfig:
    dry_run: bool
    max_files_docs: int
    max_files_code: int
    max_chars: int
    file_truncate_chars: int
    home_scan_mode: str
    r_profile: str
    resume: bool
    rpm_openai: int
    tpm_openai: int
    rpm_gemini: int
    tpm_gemini: int
    rpm_xai: int
    tpm_xai: int
    max_inflight: int


@dataclass(frozen=True)
class PromptSpec:
    step_id: str
    prompt_path: Path
    output_artifacts: Tuple[str, ...]


# --- Helpers ---

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalized_headers(headers: Any) -> Dict[str, str]:
    snapshot: Dict[str, str] = {}
    if headers is None:
        return snapshot
    for key in headers.keys():
        key_str = str(key).strip().lower()
        if not key_str:
            continue
        try:
            snapshot[key_str] = str(headers.get(key, "")).strip()
        except Exception:
            snapshot[key_str] = ""
    return snapshot


def is_valid_json_file(path: Path) -> bool:
    if not path.exists() or not path.is_file():
        return False
    try:
        json.loads(safe_read(path))
        return True
    except Exception:
        return False


def load_run_id(root: Path) -> str:
    """Load latest run_id from file or fail."""
    id_file = root / "extraction/latest_run_id.txt"
    if not id_file.exists():
        raise FileNotFoundError(
            f"Run ID file not found at {id_file}. Run 'make x-run-init' first."
        )
    run_id = id_file.read_text(encoding="utf-8").strip()
    if not run_id:
        raise RuntimeError(f"Run ID file {id_file} is empty.")
    return run_id


def get_run_dirs(root: Path, run_id: str) -> Dict[str, Path]:
    """Return dict of run paths and ensure required folders exist."""
    base = root / "extraction/runs" / run_id
    if not base.exists():
        raise FileNotFoundError(f"Run directory {base} does not exist.")

    dirs = {
        "root": base,
        "inputs": base / "00_inputs",
        "A": base / "A_repo_control_plane",
        "H": base / "H_home_control_plane",
        "M": base / "M_runtime_exports",
        "D": base / "D_docs_pipeline",
        "C": base / "C_code_surfaces",
        "E": base / "E_execution_plane",
        "W": base / "W_workflow_plane",
        "B": base / "B_boundary_plane",
        "G": base / "G_governance_plane",
        "Q": base / "Q_quality_assurance",
        "R": base / "R_arbitration",
        "X": base / "X_feature_index",
        "T": base / "T_task_packets",
        "Z": base / "Z_handoff_freeze",
    }

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


def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def sha256_string(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()


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
        return f"~/{str(resolved.relative_to(home)).replace('\\', '/')}"
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
        or name.startswith("docker-compose")
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


def write_run_manifest(root: Path, dirs: Dict[str, Path], run_id: str, args: argparse.Namespace) -> None:
    manifest = {
        "run_id": run_id,
        "generated_at": now_iso(),
        "repo_root": str(root.resolve()),
        "git_sha": get_git_sha(root),
        "cli": {
            "phase": args.phase,
            "dry_run": args.dry_run,
            "resume": args.resume,
            "max_files_docs": args.max_files_docs,
            "max_files_code": args.max_files_code,
            "max_chars": args.max_chars,
            "file_truncate_chars": args.file_truncate_chars,
            "home_scan_mode": args.home_scan_mode,
            "r_profile": args.r_profile,
            "rpm_openai": args.rpm_openai,
            "tpm_openai": args.tpm_openai,
            "rpm_gemini": args.rpm_gemini,
            "tpm_gemini": args.tpm_gemini,
            "rpm_xai": args.rpm_xai,
            "tpm_xai": args.tpm_xai,
            "max_inflight": args.max_inflight,
        },
    }
    write_json(dirs["root"] / "RUN_MANIFEST.json", manifest)


def _load_magic_surface_index(index_path: Path) -> Dict[str, Any]:
    if not index_path.exists():
        return {"generated_at": now_iso(), "file_count": 0, "files": []}
    try:
        payload = json.loads(index_path.read_text(encoding="utf-8"))
    except Exception:
        return {"generated_at": now_iso(), "file_count": 0, "files": []}
    if not isinstance(payload, dict):
        return {"generated_at": now_iso(), "file_count": 0, "files": []}
    files = payload.get("files")
    if not isinstance(files, list):
        payload["files"] = []
    return payload


def update_magic_surface_index(
    dirs: Dict[str, Path],
    phase: str,
    inventory: List[Dict[str, Any]],
    file_truncate_chars: int,
) -> None:
    index_path = dirs["inputs"] / "MAGIC_SURFACE_INDEX.json"
    payload = _load_magic_surface_index(index_path)
    existing_rows: Dict[str, Dict[str, Any]] = {}
    for row in payload.get("files", []):
        if not isinstance(row, dict):
            continue
        path = str(row.get("path", "")).strip()
        if not path:
            continue
        existing_rows[path] = row

    for item in inventory:
        if int(item.get("priority_tier", 2)) != 0:
            continue
        path = str(item.get("path", "")).strip()
        if not path:
            continue
        char_count = int(item.get("char_count", 0) or 0)
        row = existing_rows.get(path, {})
        phases = sorted(set(list(row.get("phases_seen", [])) + [phase]))
        reasons = sorted(set(list(row.get("inclusion_reasons", [])) + [str(item.get("inclusion_reason", "unclassified"))]))
        entry = {
            "path": path,
            "relative_path": str(item.get("relative_path", normalized_rel_path(Path(path)))),
            "tier": int(item.get("priority_tier", 0)),
            "subtype": str(item.get("magic_subtype", "other")),
            "size": int(item.get("size", 0) or 0),
            "mtime": float(item.get("mtime", 0.0) or 0.0),
            "inclusion_reason": reasons[0] if reasons else str(item.get("inclusion_reason", "unclassified")),
            "inclusion_reasons": reasons,
            "phases_seen": phases,
            "truncated": char_count > max(int(file_truncate_chars), 0),
            "truncate_limit_chars": int(file_truncate_chars),
            "char_count": char_count,
        }
        existing_rows[path] = entry

    files = sorted(
        existing_rows.values(),
        key=lambda row: (
            int(row.get("tier", 0)),
            int(MAGIC_SUBTYPE_ORDER.get(str(row.get("subtype", "other")), 99)),
            str(row.get("relative_path", row.get("path", ""))),
            -float(row.get("mtime", 0.0)),
        ),
    )
    payload = {
        "run_id": dirs["root"].name,
        "generated_at": now_iso(),
        "file_count": len(files),
        "files": files,
    }
    write_json(index_path, payload)


def clone_required_artifact_groups(
    groups: Dict[str, List[Tuple[str, ...]]]
) -> Dict[str, List[Tuple[str, ...]]]:
    return {phase: [tuple(group) for group in phase_groups] for phase, phase_groups in groups.items()}


def normalize_required_artifact_groups(raw: Any) -> Dict[str, List[Tuple[str, ...]]]:
    normalized: Dict[str, List[Tuple[str, ...]]] = {}
    if not isinstance(raw, dict):
        return normalized

    for phase, groups in raw.items():
        if not isinstance(phase, str):
            continue
        phase_key = phase.strip().upper()
        if not phase_key:
            continue
        if not isinstance(groups, list):
            continue

        normalized_groups: List[Tuple[str, ...]] = []
        for group in groups:
            if isinstance(group, str):
                pattern = group.strip()
                if pattern:
                    normalized_groups.append((pattern,))
                continue
            if isinstance(group, (list, tuple)):
                patterns = tuple(
                    str(pattern).strip()
                    for pattern in group
                    if isinstance(pattern, str) and str(pattern).strip()
                )
                if patterns:
                    normalized_groups.append(patterns)
        if normalized_groups:
            normalized[phase_key] = normalized_groups
    return normalized


def load_r_required_artifact_groups_by_profile() -> Dict[str, Dict[str, List[Tuple[str, ...]]]]:
    base_groups = clone_required_artifact_groups(DEFAULT_R_REQUIRED_ARTIFACT_GROUPS_BASE)
    full_additional = clone_required_artifact_groups(DEFAULT_R_REQUIRED_ARTIFACT_GROUPS_FULL_ADDITIONAL)

    base_file = R_PROFILE_MANIFEST_FILES["base"]
    if base_file.exists():
        try:
            base_payload = json.loads(safe_read(base_file))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON in {base_file}: {exc}") from exc
        parsed = normalize_required_artifact_groups(base_payload.get("requires"))
        if parsed:
            base_groups = parsed

    full_file = R_PROFILE_MANIFEST_FILES["full"]
    if full_file.exists():
        try:
            full_payload = json.loads(safe_read(full_file))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON in {full_file}: {exc}") from exc
        parsed = normalize_required_artifact_groups(full_payload.get("requires_additional"))
        if parsed:
            full_additional = parsed

    full_groups = clone_required_artifact_groups(base_groups)
    for phase, groups in full_additional.items():
        full_groups.setdefault(phase, [])
        full_groups[phase].extend(groups)

    return {"base": base_groups, "full": full_groups}


def required_input_phases_for_r_profile(profile: str) -> List[str]:
    phases = list(R_BASE_REQUIRED_INPUT_PHASES)
    if profile == "full":
        phases.append("M")
    return phases


def phase_home_scan_mode(phase: str, cfg: RunnerConfig) -> str:
    if phase == "M":
        return "safe"
    if phase == "H":
        return cfg.home_scan_mode
    return "n/a"


def phase_uses_safe_redaction(phase: str, cfg: RunnerConfig) -> bool:
    return phase == "M" or (phase == "H" and cfg.home_scan_mode == "safe")


def phase_output_files(phase_dir: Path) -> List[str]:
    output_files: List[str] = []
    for bucket in ("raw", "norm", "qa"):
        bucket_dir = phase_dir / bucket
        if not bucket_dir.exists():
            continue
        for path in sorted(bucket_dir.rglob("*")):
            if path.is_file():
                output_files.append(str(path.resolve()))
    return output_files


def serialize_manifest_inputs(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    serialized: List[Dict[str, Any]] = []
    for item in sorted(items, key=lambda candidate: str(candidate.get("path", ""))):
        path = str(item.get("path", "")).strip()
        if not path:
            continue
        try:
            size = int(item.get("size", 0))
        except Exception:
            size = 0
        try:
            mtime = float(item.get("mtime", 0.0))
        except Exception:
            mtime = 0.0
        serialized.append({"path": path, "size": size, "mtime": mtime})
    return serialized


def write_phase_manifest(
    phase: str,
    dirs: Dict[str, Path],
    cfg: RunnerConfig,
    prompts: List[PromptSpec],
    context_items: List[Dict[str, Any]],
    max_files: int,
    outputs_before: List[str],
    outputs_after: List[str],
) -> None:
    created_outputs = sorted(set(outputs_after) - set(outputs_before))
    manifest = {
        "phase": phase,
        "run_id": dirs["root"].name,
        "created_at": now_iso(),
        "home_scan_mode": phase_home_scan_mode(phase, cfg),
        "prompt_files": [str(prompt.prompt_path.resolve()) for prompt in prompts],
        "step_ids": [prompt.step_id for prompt in prompts],
        "input_files": serialize_manifest_inputs(context_items),
        "output_files": outputs_after,
        "new_output_files": created_outputs,
        "caps": {
            "max_files_docs": cfg.max_files_docs,
            "max_files_code": cfg.max_files_code,
            "max_files_phase_effective": max_files,
            "max_chars": cfg.max_chars,
            "file_truncate_chars": cfg.file_truncate_chars,
            "max_inflight": cfg.max_inflight,
            "rpm": {
                "openai": cfg.rpm_openai,
                "gemini": cfg.rpm_gemini,
                "xai": cfg.rpm_xai,
            },
            "tpm": {
                "openai": cfg.tpm_openai,
                "gemini": cfg.tpm_gemini,
                "xai": cfg.tpm_xai,
            },
            "truncate_markers": [
                "...[TRUNCATED]...",
                "...[CONTEXT_TRUNCATED_FOR_LIMIT]...",
            ],
        },
        "redactions": {
            "safe_mode_active": phase_uses_safe_redaction(phase, cfg),
            "line_patterns": [
                "api_key/token/secret/password/private_key/cookie",
                "Bearer <token>",
                "long_token_33_plus_chars",
            ],
            "field_patterns": [
                "content",
                "message",
                "prompt",
                "response",
                "body",
                "text",
                "log",
            ],
            "hash_policy": "sha256(value)[:12]",
        },
        "resume_mode": cfg.resume,
    }
    write_json(dirs[phase] / "qa" / f"PHASE_{phase}_MANIFEST.json", manifest)


def write_partition_manifest(
    phase: str,
    phase_dir: Path,
    run_id: str,
    partitions: List[Dict[str, Any]],
    inventory_by_path: Dict[str, Dict[str, Any]],
    file_truncate_chars: int,
    max_files: int,
    max_chars: int,
    step_chunk_manifests: Dict[str, List[Dict[str, Any]]],
) -> None:
    partition_rows: List[Dict[str, Any]] = []
    for partition in sorted(partitions, key=lambda item: str(item.get("id", ""))):
        ordered_paths = [str(path) for path in partition.get("ordered_paths", partition.get("paths", []))]
        files = [
            _partition_file_row(path, inventory_by_path, file_truncate_chars)
            for path in ordered_paths
        ]
        tier_counts = Counter(int(row.get("priority_tier", 2)) for row in files)
        payload_hash = build_partition_payload_hash(
            ordered_paths=ordered_paths,
            inventory_by_path=inventory_by_path,
            file_truncate_chars=file_truncate_chars,
        )
        partition_rows.append(
            {
                "partition_id": str(partition.get("id", "")),
                "reason": str(partition.get("reason", "")),
                "ordered_paths": ordered_paths,
                "file_count": len(ordered_paths),
                "char_count_estimate": int(partition.get("char_count_estimate", 0) or 0),
                "byte_count_estimate": int(partition.get("byte_count_estimate", 0) or 0),
                "token_count_estimate": int(partition.get("token_count_estimate", 0) or 0),
                "tier_counts": dict(sorted(tier_counts.items())),
                "tier0_reserved_chars": int(partition.get("tier0_reserved_chars", int(max_chars * TIER0_RESERVE_RATIO))),
                "tier0_reserved_tokens": int(partition.get("tier0_reserved_tokens", max(int(max_chars * TIER0_RESERVE_RATIO / 4), 1))),
                "partition_payload_hash": payload_hash,
                "files": files,
            }
        )

    payload = {
        "phase": phase,
        "run_id": run_id,
        "generated_at": now_iso(),
        "limits": {
            "max_files": max_files,
            "max_chars": max_chars,
            "max_tokens": max(int(max_chars / 4), 1024),
            "file_truncate_chars": file_truncate_chars,
        },
        "partition_order": [row["partition_id"] for row in partition_rows],
        "partitions": partition_rows,
        "step_chunk_manifests": {
            step_id: sorted(
                rows,
                key=lambda row: (
                    str(row.get("chunk_id", "")),
                    str(row.get("chunk_key", "")),
                ),
            )
            for step_id, rows in sorted(step_chunk_manifests.items())
        },
    }
    write_json(phase_dir / "inputs" / "PARTITION_MANIFEST.json", payload)


def write_resume_proof(
    phase: str,
    phase_dir: Path,
    run_id: str,
    prompts: List[PromptSpec],
    step_coverages: List[Dict[str, Any]],
    step_qas: List[Dict[str, Any]],
    request_controller: "RequestController",
) -> None:
    qa_by_step = {str(item.get("step_id", "")): item for item in step_qas}
    coverage_by_step = {str(item.get("step_id", "")): item for item in step_coverages}

    steps: List[Dict[str, Any]] = []
    for prompt in sorted(prompts, key=lambda item: item.step_id):
        step_id = prompt.step_id
        coverage = coverage_by_step.get(step_id, {})
        qa = qa_by_step.get(step_id, {})
        chunk_ids = [str(value) for value in coverage.get("chunk_ids", [])]
        failed_chunk_ids = sorted(set(str(value) for value in coverage.get("failed_chunk_ids", [])))
        skipped = int(coverage.get("skipped_chunks", 0) or 0)
        completed = int(coverage.get("completed_chunks", 0) or 0)
        total_done = completed + skipped
        hash_mismatch = sorted(set(str(value) for value in coverage.get("hash_mismatch_chunk_ids", [])))
        parse_failures = qa.get("parse_failures", []) if isinstance(qa.get("parse_failures"), list) else []
        missing_partitions = qa.get("missing_partitions", []) if isinstance(qa.get("missing_partitions"), list) else []
        missing_expected = qa.get("missing_expected_artifacts", []) if isinstance(qa.get("missing_expected_artifacts"), list) else []
        written_files = qa.get("written_files", []) if isinstance(qa.get("written_files"), list) else []
        output_presence = {
            str(filename): (phase_dir / "norm" / str(filename)).exists()
            for filename in written_files
        }
        steps.append(
            {
                "step_id": step_id,
                "chunk_ids": chunk_ids,
                "planned_chunks": int(coverage.get("planned_chunks", len(chunk_ids)) or len(chunk_ids)),
                "completed_chunks": completed,
                "skipped_chunks": skipped,
                "failed_chunks": int(coverage.get("failed_chunks", len(failed_chunk_ids)) or len(failed_chunk_ids)),
                "completed_or_skipped_chunks": total_done,
                "failed_chunk_ids": failed_chunk_ids,
                "hash_mismatch_chunk_ids": hash_mismatch,
                "missing_partitions": sorted(set(str(value) for value in missing_partitions)),
                "missing_expected_artifacts": sorted(set(str(value) for value in missing_expected)),
                "parse_failures": parse_failures,
                "written_files": [str(filename) for filename in written_files],
                "written_files_exist": output_presence,
            }
        )

    payload = {
        "phase": phase,
        "run_id": run_id,
        "generated_at": now_iso(),
        "steps": steps,
        "last_successful_provider_call": request_controller.last_successful_call,
    }
    write_json(phase_dir / "qa" / "RESUME_PROOF.json", payload)


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


def get_phase_prompts(phase: str) -> List[PromptSpec]:
    prompts = sorted(Path("UPGRADES").glob(f"PROMPT_{phase}*_*.md"))
    grouped: Dict[str, List[Path]] = {}

    for prompt_path in prompts:
        match = re.match(r"PROMPT_([A-Z][0-9]+)_", prompt_path.name)
        if not match:
            continue
        step_id = match.group(1)
        grouped.setdefault(step_id, []).append(prompt_path)

    specs: List[PromptSpec] = []
    for step_id in sorted(grouped.keys()):
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


# --- Home Safe Mode ---

def home_safe_allow_roots(home_root: Path) -> List[Path]:
    return [(home_root / rel).resolve() for rel in HOME_SAFE_ROOTS]


def home_safe_violation_reason(path: Path, home_root: Path) -> Optional[str]:
    allow_roots = home_safe_allow_roots(home_root)
    resolved = path.resolve()
    if not any(is_within(resolved, allow_root) or resolved == allow_root for allow_root in allow_roots):
        return "outside_allow_roots"

    suffix = resolved.suffix.lower()
    if suffix not in HOME_SAFE_ALLOW_SUFFIXES:
        return "disallowed_extension"

    lower_path = str(resolved).lower()
    lower_name = resolved.name.lower()
    if any(
        fnmatch.fnmatch(lower_name, pat) or fnmatch.fnmatch(lower_path, pat)
        for pat in HOME_SAFE_DENY_GLOBS
    ):
        return "denylist_match"

    return None


def home_safe_filter(items: List[Dict[str, Any]], home_root: Path) -> List[Dict[str, Any]]:
    filtered: List[Dict[str, Any]] = []
    skipped_counts = Counter()

    for item in items:
        path = Path(item["path"]).resolve()
        violation = home_safe_violation_reason(path, home_root)
        if violation:
            skipped_counts[violation] += 1
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


def redact_sensitive_lines(text: str) -> Tuple[str, int]:
    output_lines: List[str] = []
    had_trailing_newline = text.endswith("\n")
    redaction_hits = 0
    in_private_key_block = False

    for line in text.splitlines():
        if in_private_key_block:
            redaction_hits += 1
            if PRIVATE_KEY_END_RE.search(line):
                in_private_key_block = False
            continue

        if PRIVATE_KEY_BEGIN_RE.search(line):
            output_lines.append("[REDACTED_PRIVATE_KEY_BLOCK]")
            redaction_hits += 1
            if not PRIVATE_KEY_END_RE.search(line):
                in_private_key_block = True
            continue

        redacted = line
        if SECRET_LINE_RE.search(redacted) or ENV_SECRET_NAME_RE.search(redacted):
            replaced = SECRET_ASSIGN_RE.sub(r"\1[REDACTED]", redacted)
            redacted = replaced if replaced != redacted else "[REDACTED_LINE]"
            redaction_hits += 1
        redacted, bearer_hits = BEARER_TOKEN_RE.subn("Bearer [REDACTED_TOKEN]", redacted)
        redaction_hits += bearer_hits
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

        surface = classify_surface(str(path))
        tier = int(surface.get("tier", 2))
        subtype = str(surface.get("subtype", "other"))
        inventory.append(
            {
                "path": str(path),
                "size": size,
                "mtime": mtime,
                "sha256": sha256_text(path),
                "kind": classify_kind(path),
                "char_count": char_count,
                "char_count_estimate": est_chars,
                "token_count_estimate": max(int(est_chars / 4), 1),
                "priority_tier": tier,
                "priority_label": PRIORITY_TIERS.get(tier, "unknown"),
                "magic_subtype": subtype,
                "magic_subtype_rank": int(surface.get("subtype_rank", 99)),
                "inclusion_reason": str(surface.get("reason", "unclassified")),
                "relative_path": str(surface.get("rel_path", normalized_rel_path(path))),
            }
        )

    inventory.sort(
        key=lambda item: (
            int(item.get("priority_tier", 2)),
            int(item.get("magic_subtype_rank", 99)),
            str(item.get("relative_path", item.get("path", ""))),
            -float(item.get("mtime", 0.0)),
        )
    )
    return inventory


def classify_priority_tier(path_str: str) -> int:
    return classify_tier(path_str)


def _partition_file_row(
    path: str,
    inventory_by_path: Dict[str, Dict[str, Any]],
    file_truncate_chars: int,
) -> Dict[str, Any]:
    info = inventory_by_path.get(path, {})
    char_count = int(info.get("char_count", 0) or 0)
    est_chars = int(info.get("char_count_estimate", 0) or 0)
    est_tokens = int(info.get("token_count_estimate", max(int(est_chars / 4), 1)))
    priority_tier = int(info.get("priority_tier", classify_priority_tier(path)) or 2)
    magic_subtype = str(info.get("magic_subtype", classify_surface(path).get("subtype", "other")))
    magic_subtype_rank = int(
        info.get(
            "magic_subtype_rank",
            classify_surface(path).get("subtype_rank", MAGIC_SUBTYPE_ORDER.get("other", 99)),
        )
        or MAGIC_SUBTYPE_ORDER.get("other", 99)
    )
    inclusion_reason = str(info.get("inclusion_reason", classify_surface(path).get("reason", "unclassified")))
    relative_path = str(info.get("relative_path", classify_surface(path).get("rel_path", normalized_rel_path(Path(path)))))
    return {
        "path": path,
        "relative_path": relative_path,
        "size": int(info.get("size", 0) or 0),
        "mtime": float(info.get("mtime", 0.0) or 0.0),
        "sha256": str(info.get("sha256", "")),
        "char_count": char_count,
        "char_count_estimate": est_chars,
        "token_count_estimate": max(est_tokens, 1),
        "truncation_planned": char_count > max(int(file_truncate_chars), 0),
        "priority_tier": priority_tier,
        "priority_label": PRIORITY_TIERS.get(priority_tier, "unknown"),
        "magic_subtype": magic_subtype,
        "magic_subtype_rank": magic_subtype_rank,
        "inclusion_reason": inclusion_reason,
    }


def build_partition_payload_hash(
    ordered_paths: List[str],
    inventory_by_path: Dict[str, Dict[str, Any]],
    file_truncate_chars: int,
) -> str:
    rows = [
        _partition_file_row(path, inventory_by_path, file_truncate_chars)
        for path in ordered_paths
    ]
    digest_source = json.dumps(rows, sort_keys=True, ensure_ascii=True)
    return sha256_string(digest_source)


def max_files_for_phase(phase: str, cfg: RunnerConfig) -> int:
    if phase in CODE_HEAVY_PHASES:
        return cfg.max_files_code
    return cfg.max_files_docs


def build_partitions(
    phase: str,
    inventory: List[Dict[str, Any]],
    max_files: int,
    max_chars: int,
    file_truncate_chars: int,
) -> List[Dict[str, Any]]:
    partitions: List[Dict[str, Any]] = []
    current_paths: List[str] = []
    current_chars = 0
    current_bytes = 0
    current_tokens = 0
    current_tier0_chars = 0
    current_tier0_tokens = 0
    inventory_by_path = {str(item.get("path", "")): item for item in inventory}
    max_tokens = max(int(max_chars / 4), 1024)
    tier0_reserved_chars = int(max_chars * TIER0_RESERVE_RATIO)
    tier0_reserved_tokens = max(int(tier0_reserved_chars / 4), 1)
    tier0_remaining = sum(1 for item in inventory if int(item.get("priority_tier", 2)) == 0)

    def flush_partition(reason: str) -> None:
        nonlocal current_paths, current_chars, current_bytes, current_tokens
        nonlocal current_tier0_chars, current_tier0_tokens
        if not current_paths:
            return
        partition_id = f"{phase}_P{len(partitions) + 1:04d}"
        kinds = sorted(
            {
                str(inventory_by_path.get(path, {}).get("kind", "unknown"))
                for path in current_paths
            }
        )
        partitions.append(
            {
                "id": partition_id,
                "partition_id": partition_id,
                "paths": list(current_paths),
                "ordered_paths": list(current_paths),
                "file_count": len(current_paths),
                "char_count_estimate": current_chars,
                "byte_count_estimate": current_bytes,
                "token_count_estimate": current_tokens,
                "category": kinds[0] if len(kinds) == 1 else "mixed",
                "reason": reason,
                "tier_counts": dict(
                    sorted(
                        Counter(
                            int(inventory_by_path.get(path, {}).get("priority_tier", 2))
                            for path in current_paths
                        ).items()
                    )
                ),
                "tier0_reserved_chars": tier0_reserved_chars,
                "tier0_reserved_tokens": tier0_reserved_tokens,
                "partition_payload_hash": build_partition_payload_hash(
                    current_paths, inventory_by_path, file_truncate_chars
                ),
            }
        )
        current_paths = []
        current_chars = 0
        current_bytes = 0
        current_tokens = 0
        current_tier0_chars = 0
        current_tier0_tokens = 0

    for item in sorted(
        inventory,
        key=lambda candidate: (
            int(candidate.get("priority_tier", 2)),
            int(candidate.get("magic_subtype_rank", 99)),
            str(candidate.get("relative_path", candidate.get("path", ""))),
            -float(candidate.get("mtime", 0.0)),
        ),
    ):
        path = item["path"]
        tier = int(item.get("priority_tier", 2))
        base_chars = int(item.get("char_count_estimate", 0))
        # Account for per-file headers in context payload construction.
        est_chars = base_chars + min(len(path) + 80, 2000)
        est_bytes = len(path.encode("utf-8")) + int(item.get("size", 0))
        est_tokens = max(int(est_chars / 4), 1)

        if (
            current_paths
            and tier != 0
            and tier0_remaining > 0
            and (
                current_tier0_chars < tier0_reserved_chars
                or current_tier0_tokens < tier0_reserved_tokens
            )
        ):
            flush_partition("tier0_reserved_budget")

        if current_paths and tier in {2, 3} and tier0_remaining > 0:
            flush_partition("tier0_exhaustion_guard")

        would_exceed_files = len(current_paths) >= max_files
        would_exceed_chars = current_paths and (current_chars + est_chars > max_chars)
        would_exceed_tokens = current_paths and (current_tokens + est_tokens > max_tokens)
        if would_exceed_files or would_exceed_chars or would_exceed_tokens:
            if would_exceed_files:
                reason = "max_files"
            elif would_exceed_chars:
                reason = "max_chars"
            else:
                reason = "max_tokens"
            flush_partition(reason)
        current_paths.append(path)
        current_chars += est_chars
        current_bytes += est_bytes
        current_tokens += est_tokens
        if tier == 0:
            current_tier0_chars += est_chars
            current_tier0_tokens += est_tokens
            tier0_remaining = max(tier0_remaining - 1, 0)

    flush_partition("final")
    if not partitions:
        partitions.append(
            {
                "id": f"{phase}_P0001",
                "partition_id": f"{phase}_P0001",
                "paths": [],
                "ordered_paths": [],
                "file_count": 0,
                "char_count_estimate": 0,
                "byte_count_estimate": 0,
                "token_count_estimate": 0,
                "category": "empty",
                "reason": "empty",
                "tier_counts": {},
                "tier0_reserved_chars": tier0_reserved_chars,
                "tier0_reserved_tokens": tier0_reserved_tokens,
                "partition_payload_hash": build_partition_payload_hash(
                    [], inventory_by_path, file_truncate_chars
                ),
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
    successful_partition_ids = set()

    for partition_id in partition_ids:
        raw_file = raw_dir / f"{step_id}__{partition_id}.json"
        fail_json = raw_dir / f"{step_id}__{partition_id}.FAILED.json"
        fail_txt = raw_dir / f"{step_id}__{partition_id}.FAILED.txt"
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

            expected_artifact_seen = False
            for artifact in artifacts:
                artifact_name = artifact["artifact_name"]
                if artifact_name not in artifacts_by_name:
                    unexpected_artifacts[artifact_name] += 1
                    continue
                expected_artifact_seen = True
                artifacts_by_name[artifact_name].append(
                    {"partition_id": partition_id, "payload": artifact["payload"]}
                )
            if expected_artifact_seen:
                successful_partition_ids.add(partition_id)
            else:
                parse_failures.append(
                    {
                        "partition_id": partition_id,
                        "reason": "unexpected_artifacts_only",
                        "file": str(raw_file),
                    }
                )
        else:
            raw_failed += 1
            reason = "missing_output"
            file_path = str(raw_file)
            if fail_json.exists():
                reason = "llm_output_parse_failed"
                file_path = str(fail_json)
            elif fail_txt.exists():
                reason = "llm_output_parse_failed"
                file_path = str(fail_txt)
            parse_failures.append(
                {"partition_id": partition_id, "reason": reason, "file": file_path}
            )

    written_files: List[str] = []
    missing_expected_artifacts: List[str] = []
    missing_counts: Counter[str] = Counter()
    duplicate_ids: List[Dict[str, Any]] = []

    for artifact_name in expected_artifacts:
        chunks = artifacts_by_name.get(artifact_name, [])
        if not chunks or len(chunks) != len(partition_ids):
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
        "successful_partitions": sorted(successful_partition_ids),
        "missing_partitions": sorted(set(partition_ids) - successful_partition_ids),
        "unexpected_artifacts": dict(sorted(unexpected_artifacts.items())),
        "missing_required_keys_counts": dict(sorted(missing_counts.items())),
        "duplicate_ids": duplicate_ids[:200],
        "parse_failures": parse_failures,
        "required_item_keys": REQUIRED_ITEM_KEYS,
    }

    write_json(qa_dir / f"{step_id}_QA.json", qa_payload)
    return qa_payload


# --- LLM Execution ---

def llm_base_url(provider: str) -> str:
    return PROVIDER_BASE_URL.get(provider, PROVIDER_BASE_URL["openai"])


@dataclass
class RequestController:
    run_id: str
    cfg: RunnerConfig
    provider_limits: Dict[str, ProviderLimiter] = field(default_factory=dict)
    missing_api_env_emitted: set = field(default_factory=set)
    rate_limit_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    last_successful_call: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.provider_limits = {
            "openai": ProviderLimiter(
                ProviderRateConfig(
                    rpm=max(self.cfg.rpm_openai, 0),
                    tpm=max(self.cfg.tpm_openai, 0),
                    max_inflight=max(self.cfg.max_inflight, 1),
                )
            ),
            "gemini": ProviderLimiter(
                ProviderRateConfig(
                    rpm=max(self.cfg.rpm_gemini, 0),
                    tpm=max(self.cfg.tpm_gemini, 0),
                    max_inflight=max(self.cfg.max_inflight, 1),
                )
            ),
            "xai": ProviderLimiter(
                ProviderRateConfig(
                    rpm=max(self.cfg.rpm_xai, 0),
                    tpm=max(self.cfg.tpm_xai, 0),
                    max_inflight=max(self.cfg.max_inflight, 1),
                )
            ),
        }
        self.rate_limit_stats = {
            provider: {
                "provider": provider,
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "retry_events": 0,
                "status_429": 0,
                "status_503": 0,
                "retry_after_obeyed": 0,
                "total_backoff_seconds": 0.0,
                "max_backoff_seconds": 0.0,
                "request_ids": [],
            }
            for provider in ("openai", "gemini", "xai")
        }

    def _stats_for(self, provider: str) -> Dict[str, Any]:
        if provider not in self.rate_limit_stats:
            self.rate_limit_stats[provider] = {
                "provider": provider,
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "retry_events": 0,
                "status_429": 0,
                "status_503": 0,
                "retry_after_obeyed": 0,
                "total_backoff_seconds": 0.0,
                "max_backoff_seconds": 0.0,
                "request_ids": [],
            }
        return self.rate_limit_stats[provider]

    @staticmethod
    def _request_id_from_headers(headers: Dict[str, str]) -> str:
        for key in (
            "x-request-id",
            "request-id",
            "openai-request-id",
            "x-openai-request-id",
        ):
            value = str(headers.get(key, "")).strip()
            if value:
                return value
        return ""

    def _provider_retry_policy(self, provider: str) -> Dict[str, Any]:
        if provider == "gemini":
            return {
                "max_attempts": 7,
                "max_retry_seconds": 900.0,
                "obey_retry_after": True,
            }
        if provider == "xai":
            return {
                "max_attempts": 7,
                "max_retry_seconds": 900.0,
                "obey_retry_after": True,
            }
        return {
            "max_attempts": 6,
            "max_retry_seconds": 600.0,
            "obey_retry_after": True,
        }

    def _provider_retry_delay_seconds(
        self,
        provider: str,
        attempt: int,
        status_code: Optional[int],
        retry_after: Optional[float],
        retry_seed: str,
    ) -> Tuple[float, bool]:
        if provider == "gemini":
            if retry_after is not None:
                return max(float(retry_after), 0.0), True
            delay = min(float(2 ** max(attempt - 1, 0)), 60.0)
            return delay, False

        if provider == "xai":
            if retry_after is not None:
                return max(float(retry_after), 0.0), True
            if status_code == 429:
                return min(float(6 * (2 ** max(attempt - 1, 0))), 120.0), False
            if status_code == 503:
                return min(float(3 * (2 ** max(attempt - 1, 0))), 90.0), False
            return min(float(2 * (2 ** max(attempt - 1, 0))), 60.0), False

        delay = retry_delay_seconds(
            attempt=attempt,
            retry_after=retry_after,
            seed_material=f"{retry_seed}|provider={provider}",
        )
        return delay, retry_after is not None

    def export_rate_limit_report(self) -> Dict[str, Any]:
        per_provider = []
        for provider in sorted(self.rate_limit_stats.keys()):
            stats = self.rate_limit_stats[provider]
            per_provider.append(
                {
                    "provider": provider,
                    "total_calls": int(stats.get("total_calls", 0) or 0),
                    "successful_calls": int(stats.get("successful_calls", 0) or 0),
                    "failed_calls": int(stats.get("failed_calls", 0) or 0),
                    "retry_events": int(stats.get("retry_events", 0) or 0),
                    "status_429": int(stats.get("status_429", 0) or 0),
                    "status_503": int(stats.get("status_503", 0) or 0),
                    "retry_after_obeyed": int(stats.get("retry_after_obeyed", 0) or 0),
                    "total_backoff_seconds": round(float(stats.get("total_backoff_seconds", 0.0) or 0.0), 6),
                    "max_backoff_seconds": round(float(stats.get("max_backoff_seconds", 0.0) or 0.0), 6),
                    "request_ids": list(stats.get("request_ids", []))[:100],
                }
            )
        return {
            "run_id": self.run_id,
            "generated_at": now_iso(),
            "providers": per_provider,
        }

    def _require_api_key(self, provider: str, api_key_env: str) -> str:
        api_key = os.getenv(api_key_env, "").strip()
        if api_key:
            return api_key
        if api_key_env not in self.missing_api_env_emitted:
            self.missing_api_env_emitted.add(api_key_env)
            raise RuntimeError(
                f"Missing API key env var for provider '{provider}': {api_key_env}. "
                "Set it and rerun with --resume."
            )
        raise RuntimeError(f"Missing API key env var: {api_key_env}")

    def execute_chat_completion(
        self,
        provider: str,
        model_id: str,
        api_key_env: str,
        system_prompt: str,
        user_content: str,
        retry_seed: str,
        est_tokens: int,
    ) -> Tuple[str, Dict[str, Any]]:
        api_key = self._require_api_key(provider, api_key_env)
        limiter = self.provider_limits.get(provider)
        if limiter is None:
            limiter = ProviderLimiter(ProviderRateConfig(rpm=0, tpm=0))
            self.provider_limits[provider] = limiter

        provider_stats = self._stats_for(provider)
        provider_stats["total_calls"] = int(provider_stats.get("total_calls", 0) or 0) + 1

        payload = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        url = f"{llm_base_url(provider)}/chat/completions"
        policy = self._provider_retry_policy(provider)
        max_attempts = int(policy.get("max_attempts", 6))
        max_retry_seconds = float(policy.get("max_retry_seconds", 600.0))
        start_ts = time.time()
        retry_trace: List[Dict[str, Any]] = []

        for attempt in range(1, max_attempts + 1):
            scheduled_sleep = limiter.acquire(est_tokens)
            status_code: Optional[int] = None
            headers_snapshot: Dict[str, str] = {}
            retry_after_seconds: Optional[float] = None
            response_body = ""
            body_excerpt = ""

            try:
                response = requests.post(url, headers=headers, json=payload, timeout=180)
                status_code = response.status_code
                headers_snapshot = normalized_headers(response.headers)
                request_id = self._request_id_from_headers(headers_snapshot)
                if request_id:
                    request_ids = provider_stats.setdefault("request_ids", [])
                    if request_id not in request_ids:
                        request_ids.append(request_id)
                retry_after_seconds = parse_retry_after_seconds(
                    headers_snapshot.get("retry-after", "")
                )
                limiter.apply_server_feedback(provider, headers_snapshot)
                response.raise_for_status()
                data = response.json()
                content = str(data["choices"][0]["message"]["content"])
                meta = {
                    "attempts": attempt,
                    "status_code": status_code,
                    "headers": headers_snapshot,
                    "scheduled_sleep_seconds": scheduled_sleep,
                    "retry_trace": retry_trace,
                    "total_retry_seconds": max(time.time() - start_ts, 0.0),
                    "limiter_state": limiter.export_state(),
                    "request_id": request_id,
                }
                provider_stats["successful_calls"] = int(provider_stats.get("successful_calls", 0) or 0) + 1
                self.last_successful_call = {
                    "provider": provider,
                    "model_id": model_id,
                    "attempts": attempt,
                    "status_code": status_code,
                    "request_id": request_id,
                    "timestamp": now_iso(),
                }
                return content, meta
            except Exception as exc:
                if "response" in locals():
                    try:
                        response_body = response.text
                    except Exception:
                        response_body = ""
                if response_body:
                    body_excerpt = response_body[:1200]

                if status_code is None and isinstance(exc, requests.HTTPError):
                    try:
                        status_code = exc.response.status_code if exc.response is not None else None
                    except Exception:
                        status_code = None
                should_retry_flag = should_retry_status(status_code) or (
                    status_code is None and is_retryable_exception(exc)
                )
                if status_code == 429:
                    limiter.adapt_on_429()

                retry_event = {
                    "attempt": attempt,
                    "status_code": status_code,
                    "error": str(exc),
                    "scheduled_sleep_seconds": scheduled_sleep,
                    "retry_after_seconds": retry_after_seconds,
                    "limiter_state": limiter.export_state(),
                }
                retry_trace.append(retry_event)
                provider_stats["retry_events"] = int(provider_stats.get("retry_events", 0) or 0) + 1
                if status_code == 429:
                    provider_stats["status_429"] = int(provider_stats.get("status_429", 0) or 0) + 1
                if status_code == 503:
                    provider_stats["status_503"] = int(provider_stats.get("status_503", 0) or 0) + 1

                if not should_retry_flag or attempt >= max_attempts:
                    provider_stats["failed_calls"] = int(provider_stats.get("failed_calls", 0) or 0) + 1
                    extra = f" | body={body_excerpt}" if body_excerpt else ""
                    raise RuntimeError(
                        f"LLM call failed provider={provider} model={model_id} "
                        f"attempt={attempt}/{max_attempts} status={status_code} error={exc}{extra}"
                    ) from exc

                sleep_seconds, obeyed_retry_after = self._provider_retry_delay_seconds(
                    provider=provider,
                    attempt=attempt,
                    status_code=status_code,
                    retry_after=retry_after_seconds,
                    retry_seed=f"{retry_seed}|attempt={attempt}",
                )
                if obeyed_retry_after:
                    provider_stats["retry_after_obeyed"] = (
                        int(provider_stats.get("retry_after_obeyed", 0) or 0) + 1
                    )
                elapsed = time.time() - start_ts
                if elapsed + sleep_seconds > max_retry_seconds:
                    provider_stats["failed_calls"] = int(provider_stats.get("failed_calls", 0) or 0) + 1
                    raise RuntimeError(
                        f"Retry time budget exceeded provider={provider} model={model_id} "
                        f"elapsed={elapsed:.2f}s budget={max_retry_seconds:.2f}s "
                        f"status={status_code} last_error={exc}"
                    ) from exc
                retry_event["backoff_sleep_seconds"] = sleep_seconds
                provider_stats["total_backoff_seconds"] = float(
                    provider_stats.get("total_backoff_seconds", 0.0) or 0.0
                ) + float(sleep_seconds)
                provider_stats["max_backoff_seconds"] = max(
                    float(provider_stats.get("max_backoff_seconds", 0.0) or 0.0),
                    float(sleep_seconds),
                )
                logger.warning(
                    "LLM retry provider=%s model=%s attempt=%s/%s status=%s sleep=%.3fs",
                    provider,
                    model_id,
                    attempt,
                    max_attempts,
                    status_code,
                    sleep_seconds,
                )
                time.sleep(sleep_seconds)

        raise RuntimeError(f"Unreachable retry exit provider={provider} model={model_id}")


def parse_json_from_response(text: str) -> Optional[Any]:
    if not text:
        return None
    stripped = text.strip()

    candidates = [stripped]
    no_fence = re.sub(r"^\s*```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
    no_fence = re.sub(r"\s*```\s*$", "", no_fence)
    candidates.append(no_fence.strip())

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except Exception:
            continue

    match = re.search(r"(\{.*\}|\[.*\])", no_fence, flags=re.DOTALL)
    if match:
        snippet = match.group(1)
        try:
            return json.loads(snippet)
        except Exception:
            return None
    return None


def build_output_envelope_instructions(output_artifacts: Tuple[str, ...]) -> str:
    expected = "\n".join(f"- {artifact}" for artifact in output_artifacts)
    return (
        "Return JSON only with this exact envelope:\n"
        '{"artifacts":[{"artifact_name":"<exact artifact name>","payload":<json object|json array|markdown string>}]}'
        "\nConstraints:\n"
        "- artifact_name must exactly match one expected artifact.\n"
        "- For *.json artifacts, payload must be valid JSON (object or array).\n"
        "- For *.md artifacts, payload must be markdown text.\n"
        "- For *.partX.json artifacts, keep .partX in artifact_name exactly.\n"
        "- Do not emit any extra artifact names.\n"
        "Expected artifacts:\n"
        f"{expected}\n"
    )


def coerce_artifacts_from_response(
    parsed: Optional[Any],
    raw_text: str,
    expected_artifacts: Tuple[str, ...],
) -> List[Dict[str, Any]]:
    expected_set = set(expected_artifacts)

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


def execute_step_for_partitions(
    phase: str,
    prompt_spec: PromptSpec,
    partitions: List[Dict[str, Any]],
    inventory_by_path: Dict[str, Dict[str, Any]],
    phase_dir: Path,
    cfg: RunnerConfig,
    request_controller: RequestController,
) -> Dict[str, Any]:
    step_id = prompt_spec.step_id
    prompt_path = prompt_spec.prompt_path
    output_artifacts = prompt_spec.output_artifacts
    prompt_text = safe_read(prompt_path)
    if not prompt_text:
        logger.error("Could not read prompt: %s", prompt_path)
        return {
            "step_id": step_id,
            "planned_chunks": len(partitions),
            "completed_chunks": 0,
            "skipped_chunks": 0,
            "failed_chunks": len(partitions),
            "failed_chunk_ids": [str(partition.get("id", "")) for partition in partitions],
            "chunk_ids": [str(partition.get("id", "")) for partition in partitions],
        }

    raw_dir = phase_dir / "raw"
    inputs_dir = phase_dir / "inputs"
    payload_cache_dir = inputs_dir / "payload_cache"
    payload_cache_dir.mkdir(parents=True, exist_ok=True)
    provider, model_id, api_key_env = MODEL_ROUTING.get(
        phase, ("xai", "grok-code-fast-1", "XAI_API_KEY")
    )
    if not cfg.dry_run:
        request_controller._require_api_key(provider, api_key_env)
    max_files = max_files_for_phase(phase, cfg)
    prompt_hash = hashlib.sha256(prompt_text.encode("utf-8", errors="ignore")).hexdigest()
    prompt_version = sha256_text(prompt_path)
    logger.info(
        "Step %s using prompt %s outputs=%s",
        step_id,
        prompt_path.name,
        list(output_artifacts),
    )
    resume_skipped = 0
    completed_chunks = 0
    failed_chunks = 0
    failed_chunk_ids: List[str] = []
    hash_mismatch_chunk_ids: List[str] = []
    chunk_ids: List[str] = []

    chunk_manifest_rows: List[Dict[str, Any]] = []
    truncated_only_chunks = 0
    chunks_with_tail_snippets = 0
    home_root = Path.home()
    tail_chars = min(max(int(cfg.file_truncate_chars * 0.1), 256), 2048)

    for partition in partitions:
        partition_id = partition["id"]
        chunk_ids.append(partition_id)
        out_json = raw_dir / f"{step_id}__{partition_id}.json"
        out_failed = raw_dir / f"{step_id}__{partition_id}.FAILED.json"
        out_trace = raw_dir / f"{step_id}__{partition_id}.TRACE.md"
        out_meta = raw_dir / f"{step_id}__{partition_id}.request_meta.json"
        payload_cache = payload_cache_dir / f"{step_id}__{partition_id}.prompt.txt"

        file_manifest_hash = str(partition.get("file_manifest_hash", ""))
        if not file_manifest_hash:
            file_manifest_hash = build_file_manifest_hash(partition.get("paths", []), inventory_by_path)
        output_instructions = build_output_envelope_instructions(output_artifacts)
        prompt_prefix = (
            "Extract from the files below.\n"
            f"{output_instructions}\n"
            "\nFILES:\n"
        )
        reserved_bytes = len(prompt_prefix.encode("utf-8"))
        context_budget = max(cfg.max_chars - reserved_bytes, 2048)
        filtered_paths: List[str] = []
        safe_mode_blocked = 0
        for path_str in partition.get("paths", []):
            path = Path(path_str)
            enforce_home_allowlist = phase == "H" and cfg.home_scan_mode == "safe"
            if enforce_home_allowlist:
                violation = home_safe_violation_reason(path, home_root)
                if violation:
                    safe_mode_blocked += 1
                    logger.warning("Blocked unsafe home file in SAFE mode: %s (%s)", path, violation)
                    continue
            filtered_paths.append(path_str)

        redaction_hits_total = 0

        def _read_for_chunk(path_str: str) -> str:
            nonlocal redaction_hits_total
            content_local = safe_read(Path(path_str))
            safe_redaction_active = phase == "M" or (phase == "H" and cfg.home_scan_mode == "safe")
            if safe_redaction_active:
                content_local, hits = redact_sensitive_lines(content_local)
                redaction_hits_total += hits
            return content_local

        context, context_stats, file_entries = build_partition_context(
            partition_paths=filtered_paths,
            read_text_fn=_read_for_chunk,
            file_truncate_chars=cfg.file_truncate_chars,
            max_files=max_files,
            max_chars=context_budget,
            tail_chars=tail_chars,
        )
        context_stats["redaction_hits"] = redaction_hits_total
        context_stats["safe_mode_blocked"] = safe_mode_blocked
        if context_stats.get("files_included", 0) > 0 and context_stats.get("truncated_files", 0) == context_stats.get(
            "files_included", 0
        ):
            truncated_only_chunks += 1
        if context_stats.get("tail_snippet_files", 0) > 0:
            chunks_with_tail_snippets += 1

        if payload_cache.exists():
            cached_prompt = safe_read(payload_cache)
            user_prompt = cached_prompt if cached_prompt else f"{prompt_prefix}{context}"
        else:
            user_prompt = f"{prompt_prefix}{context}"
            payload_cache.write_text(user_prompt, encoding="utf-8")
        injected_text_sha256 = hashlib.sha256(
            user_prompt.encode("utf-8", errors="ignore")
        ).hexdigest()

        chunk_contract = {
            "prompt_version": prompt_version,
            "provider": provider,
            "model": model_id,
            "system_prompt_hash": prompt_hash,
            "file_manifest_hash": file_manifest_hash,
            "caps": {
                "max_chars": cfg.max_chars,
                "file_truncate_chars": cfg.file_truncate_chars,
                "max_files_phase_effective": max_files,
            },
            "home_scan_mode": cfg.home_scan_mode,
            "safe_redaction_active": phase_uses_safe_redaction(phase, cfg),
            "redaction_version": "safe-redaction-v1",
            "injected_text_sha256": injected_text_sha256,
        }
        chunk_key = hashlib.sha256(
            json.dumps(chunk_contract, sort_keys=True, ensure_ascii=True).encode("utf-8", errors="ignore")
        ).hexdigest()

        if cfg.resume and out_json.exists() and out_meta.exists():
            if is_valid_json_file(out_json):
                meta_payload = parse_json_from_response(safe_read(out_meta))
                if isinstance(meta_payload, dict) and str(meta_payload.get("chunk_key", "")) == chunk_key:
                    prior_hash = str(meta_payload.get("output_sha256", "")).strip()
                    current_hash = sha256_text(out_json)
                    if prior_hash and prior_hash == current_hash:
                        resume_skipped += 1
                        chunk_manifest_rows.append(
                            {
                                "chunk_id": partition_id,
                                "base_partition_id": str(partition.get("base_partition_id", "")),
                                "file_manifest_hash": file_manifest_hash,
                                "chunk_key": chunk_key,
                                "injected_text_sha256": injected_text_sha256,
                                "request_payload_bytes": len(user_prompt.encode("utf-8")),
                                "file_entries": file_entries,
                                "context_stats": context_stats,
                                "status": "resume_skipped",
                                "resume_output_sha256": current_hash,
                            }
                        )
                        continue
                    hash_mismatch_chunk_ids.append(partition_id)

        payload_bytes = len(user_prompt.encode("utf-8"))
        chunk_manifest_rows.append(
            {
                "chunk_id": partition_id,
                "base_partition_id": str(partition.get("base_partition_id", "")),
                "file_manifest_hash": file_manifest_hash,
                "chunk_key": chunk_key,
                "injected_text_sha256": injected_text_sha256,
                "request_payload_bytes": payload_bytes,
                "file_entries": file_entries,
                "context_stats": context_stats,
            }
        )
        if payload_bytes > cfg.max_chars:
            raise RuntimeError(
                f"Payload limit exceeded for {step_id} {partition_id}: "
                f"{payload_bytes} > {cfg.max_chars} bytes."
            )

        if cfg.dry_run:
            logger.info(
                "Dry-run %s %s files=%s payload_bytes=%s redaction_hits=%s safe_mode_blocked=%s",
                step_id,
                partition_id,
                context_stats["files_included"],
                payload_bytes,
                context_stats["redaction_hits"],
                context_stats["safe_mode_blocked"],
            )

        if cfg.dry_run:
            trace_text = (
                f"# PROMPT_FILE\n{prompt_path}\n\n# SYSTEM_PROMPT\n{prompt_text}\n\n"
                f"# PARTITION_ID\n{partition_id}\n\n# USER_CONTEXT_PREVIEW\n{context[:2000]}"
            )
            out_trace.write_text(trace_text, encoding="utf-8")
            write_json(
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
                },
            )
            write_json(
                out_meta,
                {
                    "phase": phase,
                    "step_id": step_id,
                    "partition_id": partition_id,
                    "provider": provider,
                    "model_id": model_id,
                    "chunk_key": chunk_key,
                    "file_manifest_hash": file_manifest_hash,
                    "request_payload_bytes": payload_bytes,
                    "context_stats": context_stats,
                    "injected_text_sha256": injected_text_sha256,
                    "output_sha256": sha256_text(out_json),
                    "status": "dry_run",
                    "generated_at": now_iso(),
                },
            )
            if out_failed.exists():
                out_failed.unlink()
            completed_chunks += 1
            continue

        logger.info(
            "Executing %s partition %s using provider=%s model=%s files=%s skipped=%s context_bytes=%s",
            step_id,
            partition_id,
            provider,
            model_id,
            context_stats["files_included"],
            context_stats["files_skipped"],
            context_stats["context_bytes"],
        )
        request_meta: Dict[str, Any] = {
            "phase": phase,
            "step_id": step_id,
            "partition_id": partition_id,
            "provider": provider,
            "model_id": model_id,
            "api_key_env": api_key_env,
            "chunk_key": chunk_key,
            "file_manifest_hash": file_manifest_hash,
            "request_payload_bytes": payload_bytes,
            "context_stats": context_stats,
            "started_at": now_iso(),
            "status": "in_progress",
        }
        write_json(out_meta, request_meta)
        try:
            response, call_meta = request_controller.execute_chat_completion(
                provider=provider,
                model_id=model_id,
                api_key_env=api_key_env,
                system_prompt=prompt_text,
                user_content=user_prompt,
                retry_seed=f"{request_controller.run_id}|{phase}|{step_id}|{partition_id}",
                est_tokens=estimate_tokens_from_text(user_prompt),
            )
            request_meta.update(call_meta)
        except Exception as exc:
            failed_chunks += 1
            failed_chunk_ids.append(partition_id)
            error_text = str(exc)
            write_json(
                out_failed,
                {
                    "phase": phase,
                    "step_id": step_id,
                    "partition_id": partition_id,
                    "status": "failed",
                    "error": error_text,
                    "retry_trace": request_meta.get("retry_trace", []),
                    "generated_at": now_iso(),
                },
            )
            request_meta.update(
                {
                    "status": "failed",
                    "finished_at": now_iso(),
                    "error": error_text,
                }
            )
            write_json(out_meta, request_meta)
            logger.error("LLM execution failed for %s %s: %s", step_id, partition_id, error_text)
            continue

        parsed = parse_json_from_response(response)
        artifacts = coerce_artifacts_from_response(
            parsed=parsed,
            raw_text=response,
            expected_artifacts=output_artifacts,
        )
        if not artifacts:
            write_json(
                out_failed,
                {
                    "phase": phase,
                    "step_id": step_id,
                    "partition_id": partition_id,
                    "status": "failed",
                    "error": "artifact_parse_failed",
                    "raw_response_excerpt": response[:4000],
                    "retry_trace": request_meta.get("retry_trace", []),
                    "generated_at": now_iso(),
                },
            )
            logger.error("Artifact parse failed for %s %s", step_id, partition_id)
            failed_chunks += 1
            failed_chunk_ids.append(partition_id)
            request_meta.update(
                {
                    "status": "failed",
                    "finished_at": now_iso(),
                    "error": "artifact_parse_failed",
                }
            )
            write_json(out_meta, request_meta)
            continue

        write_json(
            out_json,
            {
                "phase": phase,
                "step_id": step_id,
                "partition_id": partition_id,
                "generated_at": now_iso(),
                "artifacts": artifacts,
            },
        )
        request_meta.update(
            {
                "status": "ok",
                "finished_at": now_iso(),
                "output_sha256": sha256_text(out_json),
            }
        )
        write_json(out_meta, request_meta)
        if out_failed.exists():
            out_failed.unlink()
        completed_chunks += 1

    if resume_skipped:
        logger.info("Resume: skipped %s existing outputs for step %s", resume_skipped, step_id)
    return {
        "step_id": step_id,
        "planned_chunks": len(partitions),
        "completed_chunks": completed_chunks,
        "skipped_chunks": resume_skipped,
        "failed_chunks": failed_chunks,
        "failed_chunk_ids": sorted(set(failed_chunk_ids)),
        "hash_mismatch_chunk_ids": sorted(set(hash_mismatch_chunk_ids)),
        "chunk_ids": chunk_ids,
        "truncated_only_chunks": truncated_only_chunks,
        "chunks_with_tail_snippets": chunks_with_tail_snippets,
        "chunk_manifest_rows": chunk_manifest_rows,
    }


def write_phase_merge_report(
    phase: str,
    phase_dir: Path,
    partitions: List[Dict[str, Any]],
    step_qas: List[Dict[str, Any]],
) -> None:
    partition_ids = [partition["id"] for partition in partitions]
    step_reports: List[Dict[str, Any]] = []
    total_parse_failures = 0
    total_missing_expected_artifacts = 0

    for qa_payload in sorted(step_qas, key=lambda item: str(item.get("step_id", ""))):
        parse_failures = qa_payload.get("parse_failures", [])
        missing_expected = qa_payload.get("missing_expected_artifacts", [])
        successful = list(qa_payload.get("successful_partitions", []))
        missing_partitions = list(qa_payload.get("missing_partitions", []))
        step_reports.append(
            {
                "step_id": qa_payload.get("step_id"),
                "partitions_total": qa_payload.get("partitions_total", len(partition_ids)),
                "successful_partitions": successful,
                "missing_partitions": missing_partitions,
                "missing_expected_artifacts": missing_expected,
                "parse_failures": parse_failures,
            }
        )
        total_parse_failures += len(parse_failures)
        total_missing_expected_artifacts += len(missing_expected)

    phase_report = {
        "phase": phase,
        "generated_at": now_iso(),
        "partitions_total": len(partition_ids),
        "partition_ids": partition_ids,
        "steps_total": len(step_reports),
        "total_parse_failures": total_parse_failures,
        "total_missing_expected_artifacts": total_missing_expected_artifacts,
        "steps": step_reports,
    }
    write_json(phase_dir / "qa" / f"{phase}_MERGE_REPORT.json", phase_report)


def _run_phase_inner(
    phase: str,
    dirs: Dict[str, Path],
    cfg: RunnerConfig,
    collector: Optional[Collector],
    targets: Optional[List[str]],
    precollected_items: Optional[List[Dict[str, Any]]] = None,
    forced_items: Optional[List[Dict[str, Any]]] = None,
) -> None:
    logger.info("--- Phase %s ---", phase)
    phase_dir = dirs[phase]
    outputs_before = phase_output_files(phase_dir)
    prompts = get_phase_prompts(phase)
    if not prompts:
        raise RuntimeError(f"No prompts found for phase {phase} in UPGRADES/")

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

    if forced_items:
        context_items = merge_items(context_items, forced_items)
        logger.info("Phase %s merged %s forced tier-0 items.", phase, len(forced_items))

    inventory = build_inventory(context_items, cfg.file_truncate_chars)
    update_magic_surface_index(dirs, phase, inventory, cfg.file_truncate_chars)
    inventory_by_path = {str(item.get("path", "")): item for item in inventory}
    max_files = max_files_for_phase(phase, cfg)
    partitions = build_partitions(
        phase,
        inventory,
        max_files=max_files,
        max_chars=cfg.max_chars,
        file_truncate_chars=cfg.file_truncate_chars,
    )

    write_json(
        phase_dir / "inputs" / "INVENTORY.json",
        {"phase": phase, "generated_at": now_iso(), "items": inventory},
    )
    write_json(
        dirs["inputs"] / f"{phase}_INVENTORY.json",
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
                "max_tokens": max(int(cfg.max_chars / 4), 1024),
                "file_truncate_chars": cfg.file_truncate_chars,
            },
            "partitions": partitions,
        },
    )
    write_json(
        dirs["inputs"] / f"{phase}_PARTITIONS.json",
        {
            "phase": phase,
            "generated_at": now_iso(),
            "limits": {
                "max_files": max_files,
                "max_chars": cfg.max_chars,
                "max_tokens": max(int(cfg.max_chars / 4), 1024),
                "file_truncate_chars": cfg.file_truncate_chars,
            },
            "partitions": partitions,
        },
    )

    logger.info(
        "Phase %s inventory=%s partitions=%s max_files=%s max_chars=%s",
        phase,
        len(inventory),
        len(partitions),
        max_files,
        cfg.max_chars,
    )

    request_controller = RequestController(run_id=dirs["root"].name, cfg=cfg)
    step_qas: List[Dict[str, Any]] = []
    step_coverages: List[Dict[str, Any]] = []
    step_chunk_manifests: Dict[str, List[Dict[str, Any]]] = {}
    for prompt_spec in prompts:
        chunk_plan = plan_chunks_for_step(
            partitions=partitions,
            inventory_by_path=inventory_by_path,
            max_files=max_files,
            max_chars=cfg.max_chars,
        )
        coverage = execute_step_for_partitions(
            phase=phase,
            prompt_spec=prompt_spec,
            partitions=chunk_plan,
            inventory_by_path=inventory_by_path,
            phase_dir=phase_dir,
            cfg=cfg,
            request_controller=request_controller,
        )
        step_chunk_rows = list(coverage.get("chunk_manifest_rows", []))
        step_chunk_manifests[prompt_spec.step_id] = step_chunk_rows
        write_json(
            phase_dir / "inputs" / f"CHUNK_MANIFEST_{prompt_spec.step_id}.json",
            {
                "phase": phase,
                "step_id": prompt_spec.step_id,
                "generated_at": now_iso(),
                "max_files": max_files,
                "max_chars": cfg.max_chars,
                "soft_target_chars": max(int(cfg.max_chars * 0.7), 2048),
                "chunks": step_chunk_rows,
            },
        )
        if "chunk_manifest_rows" in coverage:
            del coverage["chunk_manifest_rows"]
        step_coverages.append(dict(coverage))
        write_json(phase_dir / "qa" / f"{prompt_spec.step_id}__chunk_coverage.json", coverage)
        write_json(phase_dir / "qa" / f"{prompt_spec.step_id}_COVERAGE.json", coverage)
        qa_payload = normalize_step(
            phase=phase,
            prompt_spec=prompt_spec,
            phase_dir=phase_dir,
            partitions=chunk_plan,
        )
        step_qas.append(qa_payload)

    write_partition_manifest(
        phase=phase,
        phase_dir=phase_dir,
        run_id=dirs["root"].name,
        partitions=partitions,
        inventory_by_path=inventory_by_path,
        file_truncate_chars=cfg.file_truncate_chars,
        max_files=max_files,
        max_chars=cfg.max_chars,
        step_chunk_manifests=step_chunk_manifests,
    )
    write_phase_merge_report(
        phase=phase,
        phase_dir=phase_dir,
        partitions=partitions,
        step_qas=step_qas,
    )
    write_json(phase_dir / "qa" / "RATE_LIMIT_REPORT.json", request_controller.export_rate_limit_report())
    write_resume_proof(
        phase=phase,
        phase_dir=phase_dir,
        run_id=dirs["root"].name,
        prompts=prompts,
        step_coverages=step_coverages,
        step_qas=step_qas,
        request_controller=request_controller,
    )
    outputs_after = phase_output_files(phase_dir)
    write_phase_manifest(
        phase=phase,
        dirs=dirs,
        cfg=cfg,
        prompts=prompts,
        context_items=context_items,
        max_files=max_files,
        outputs_before=outputs_before,
        outputs_after=outputs_after,
    )


# --- Phase M Runtime Export Helpers ---

SQLITE_SUFFIXES = {".db", ".sqlite", ".sqlite3"}
PHASE_M_MAX_DISCOVERED_FILES = 5000
PHASE_M_MAX_CONFIG_KEYS = 40


def hash_identifier(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()[:12]


def classify_runtime_store(path: Path) -> str:
    suffix = path.suffix.lower()
    lower = str(path).lower()
    if suffix in SQLITE_SUFFIXES:
        return "sqlite_db"
    if "/cache/" in lower or lower.endswith(".cache") or lower.endswith(".log") or lower.endswith(".tmp"):
        return "cache"
    if suffix in HOME_SAFE_ALLOW_SUFFIXES:
        return "config"
    return "unknown"


def runtime_exportability(path: Path, classification: str) -> str:
    if not path.exists():
        return "missing"
    if not os.access(path, os.R_OK):
        return "permission_denied"
    if classification in {"sqlite_db", "config"}:
        return "ok"
    if classification == "cache":
        return "unsafe"
    return "unsafe"


def collect_runtime_inventory(
    home_root: Path, max_files: int = PHASE_M_MAX_DISCOVERED_FILES
) -> Tuple[List[Dict[str, Any]], List[str], bool]:
    discovered: List[Dict[str, Any]] = []
    missing_roots: List[str] = []
    truncated = False

    for allow_root in home_safe_allow_roots(home_root):
        if not allow_root.exists():
            missing_roots.append(str(allow_root))
            continue

        for walk_root, dirs, files in os.walk(allow_root):
            dirs.sort()
            files.sort()
            for filename in files:
                path = Path(walk_root) / filename
                if len(discovered) >= max_files:
                    truncated = True
                    break
                try:
                    st = path.stat()
                    size = st.st_size
                    mtime = st.st_mtime
                except Exception:
                    size = 0
                    mtime = 0.0
                classification = classify_runtime_store(path)
                discovered.append(
                    {
                        "path": str(path.resolve()),
                        "path_id": hash_identifier(str(path.resolve())),
                        "size": size,
                        "mtime": mtime,
                        "classification": classification,
                        "exportability": runtime_exportability(path, classification),
                    }
                )
            if truncated:
                break
        if truncated:
            break

    discovered.sort(key=lambda item: item["path"])
    return discovered, missing_roots, truncated


def extract_config_key_names(path: Path, max_keys: int = PHASE_M_MAX_CONFIG_KEYS) -> List[str]:
    keys: List[str] = []
    seen = set()
    text = safe_read(path)
    for line in text.splitlines():
        if len(line) > 256:
            continue
        match = CONFIG_KEY_RE.match(line)
        if not match:
            continue
        key = match.group(1).strip()
        if not key or key in seen:
            continue
        seen.add(key)
        keys.append(key)
        if len(keys) >= max_keys:
            break
    return keys


def collect_env_keys(value: Any, env_keys: set) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if key_text.lower() == "env" and isinstance(item, dict):
                for env_key in item.keys():
                    env_keys.add(str(env_key))
            collect_env_keys(item, env_keys)
    elif isinstance(value, list):
        for item in value:
            collect_env_keys(item, env_keys)


def collect_mcp_server_summaries(path: Path) -> List[Dict[str, Any]]:
    summaries: List[Dict[str, Any]] = []
    if path.suffix.lower() not in {".json", ".yaml", ".yml", ".toml"}:
        return summaries

    text = safe_read(path)
    if not text.strip():
        return summaries

    try:
        payload = json.loads(text)
    except Exception:
        return summaries

    server_blocks: List[Tuple[str, Dict[str, Any]]] = []
    if isinstance(payload, dict):
        for key in ("mcpServers", "mcp_servers", "servers"):
            candidate = payload.get(key)
            if isinstance(candidate, dict):
                for name, definition in candidate.items():
                    if isinstance(definition, dict):
                        server_blocks.append((str(name), definition))

    for name, definition in server_blocks:
        env_keys = set()
        collect_env_keys(definition, env_keys)
        command = definition.get("command")
        args = definition.get("args")
        summaries.append(
            {
                "name": name,
                "name_id": hash_identifier(name),
                "config_path": str(path.resolve()),
                "command": str(command) if isinstance(command, str) else "",
                "args_count": len(args) if isinstance(args, list) else 0,
                "env_keys": sorted(env_keys),
            }
        )
    return summaries


def sqlite_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def collect_sqlite_schema_snapshot(db_path: Path) -> Dict[str, Any]:
    snapshot: Dict[str, Any] = {
        "db_path": str(db_path.resolve()),
        "db_path_id": hash_identifier(str(db_path.resolve())),
        "status": "ok",
        "tables": [],
        "indexes": [],
        "triggers": [],
        "pragma": {
            "user_version": None,
            "foreign_keys": None,
            "sqlite_version": None,
        },
    }
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
    except Exception as exc:
        snapshot["status"] = "error"
        snapshot["error"] = str(exc)
        return snapshot

    try:
        cur = conn.cursor()
        try:
            cur.execute("PRAGMA user_version;")
            row = cur.fetchone()
            snapshot["pragma"]["user_version"] = int(row[0]) if row else None
        except Exception as exc:
            snapshot["pragma"]["user_version_error"] = str(exc)
        try:
            cur.execute("PRAGMA foreign_keys;")
            row = cur.fetchone()
            snapshot["pragma"]["foreign_keys"] = int(row[0]) if row else None
        except Exception as exc:
            snapshot["pragma"]["foreign_keys_error"] = str(exc)
        try:
            cur.execute("SELECT sqlite_version();")
            row = cur.fetchone()
            snapshot["pragma"]["sqlite_version"] = str(row[0]) if row else None
        except Exception as exc:
            snapshot["pragma"]["sqlite_version_error"] = str(exc)

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        table_names = [str(row[0]) for row in cur.fetchall() if row and row[0]]
        for table_name in table_names:
            table_payload: Dict[str, Any] = {
                "name": table_name,
                "name_id": hash_identifier(table_name),
                "columns": [],
            }
            try:
                cur.execute(f"PRAGMA table_info({sqlite_identifier(table_name)});")
                table_payload["columns"] = [
                    {
                        "name": str(column_row["name"]),
                        "type": str(column_row["type"]),
                        "notnull": int(column_row["notnull"]),
                    }
                    for column_row in cur.fetchall()
                ]
            except Exception as exc:
                table_payload["error"] = str(exc)
            snapshot["tables"].append(table_payload)

        cur.execute("SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;")
        snapshot["indexes"] = [str(row[0]) for row in cur.fetchall() if row and row[0]]
        cur.execute("SELECT name FROM sqlite_master WHERE type='trigger' ORDER BY name;")
        snapshot["triggers"] = [str(row[0]) for row in cur.fetchall() if row and row[0]]
    except Exception as exc:
        snapshot["status"] = "error"
        snapshot["error"] = str(exc)
    finally:
        conn.close()
    return snapshot


def collect_sqlite_table_counts(db_path: Path) -> Dict[str, Any]:
    counts_payload: Dict[str, Any] = {
        "db_path": str(db_path.resolve()),
        "db_path_id": hash_identifier(str(db_path.resolve())),
        "status": "ok",
        "table_counts": [],
    }
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except Exception as exc:
        counts_payload["status"] = "error"
        counts_payload["error"] = str(exc)
        return counts_payload

    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        table_names = [str(row[0]) for row in cur.fetchall() if row and row[0]]
        for table_name in table_names:
            table_count: Dict[str, Any] = {"name": table_name, "name_id": hash_identifier(table_name)}
            try:
                cur.execute(f"SELECT COUNT(*) FROM {sqlite_identifier(table_name)};")
                row = cur.fetchone()
                table_count["row_count"] = int(row[0]) if row else 0
            except Exception as exc:
                table_count["row_count"] = None
                table_count["error"] = str(exc)
            counts_payload["table_counts"].append(table_count)
    except Exception as exc:
        counts_payload["status"] = "error"
        counts_payload["error"] = str(exc)
    finally:
        conn.close()
    return counts_payload


def build_phase_m_seed_inputs(phase_dir: Path) -> List[Path]:
    seed_dir = phase_dir / "inputs" / "runtime_seed"
    seed_dir.mkdir(parents=True, exist_ok=True)

    home_root = Path.home()
    allow_roots = [str(path) for path in home_safe_allow_roots(home_root)]
    discovered, missing_roots, truncated = collect_runtime_inventory(home_root)
    sqlite_paths = [
        Path(item["path"])
        for item in discovered
        if item.get("classification") == "sqlite_db" and item.get("exportability") == "ok"
    ]
    config_paths = [
        Path(item["path"])
        for item in discovered
        if item.get("classification") == "config" and item.get("exportability") == "ok"
    ]

    schema_snapshots = [collect_sqlite_schema_snapshot(path) for path in sqlite_paths]
    table_counts = [collect_sqlite_table_counts(path) for path in sqlite_paths]

    config_summaries: List[Dict[str, Any]] = []
    mcp_server_summaries: List[Dict[str, Any]] = []
    for path in config_paths:
        key_sample = extract_config_key_names(path)
        config_summaries.append(
            {
                "path": str(path.resolve()),
                "path_id": hash_identifier(str(path.resolve())),
                "key_names_sample": key_sample,
                "keys_total_sampled": len(key_sample),
                "values": "REDACTED",
            }
        )
        mcp_server_summaries.extend(collect_mcp_server_summaries(path))

    mcp_server_unique = sorted(
        {
            (
                server["name"],
                server["name_id"],
                server["config_path"],
                server["command"],
                server["args_count"],
                tuple(server["env_keys"]),
            )
            for server in mcp_server_summaries
        }
    )
    mcp_servers = [
        {
            "name": name,
            "name_id": name_id,
            "config_path": config_path,
            "command": command,
            "args_count": args_count,
            "env_keys": list(env_keys),
        }
        for (name, name_id, config_path, command, args_count, env_keys) in mcp_server_unique
    ]

    m0_inventory = {
        "generated_at": now_iso(),
        "allow_roots": allow_roots,
        "missing_roots": missing_roots,
        "detected_paths": discovered,
        "caps": {
            "max_detected_files": PHASE_M_MAX_DISCOVERED_FILES,
            "detected_files": len(discovered),
        },
        "markers": ["TRUNCATED"] if truncated else [],
    }

    m1_schema = {
        "generated_at": now_iso(),
        "sqlite_databases_discovered": len(sqlite_paths),
        "snapshots": schema_snapshots,
        "no_row_data_exported": True,
    }

    m2_counts = {
        "generated_at": now_iso(),
        "sqlite_databases_discovered": len(sqlite_paths),
        "table_counts": table_counts,
        "no_row_data_exported": True,
    }

    conport_keywords = ("conport", "context_portal")
    dope_context_keywords = ("dope", "context.db", "global_index.sqlite")

    def filter_refs(keywords: Tuple[str, ...]) -> Dict[str, Any]:
        keyword_set = tuple(keyword.lower() for keyword in keywords)
        db_refs = [
            item
            for item in discovered
            if item.get("classification") == "sqlite_db"
            and any(keyword in str(item.get("path", "")).lower() for keyword in keyword_set)
        ]
        config_refs = [
            item
            for item in config_summaries
            if any(keyword in str(item.get("path", "")).lower() for keyword in keyword_set)
        ]
        schema_refs = [
            snapshot
            for snapshot in schema_snapshots
            if any(keyword in str(snapshot.get("db_path", "")).lower() for keyword in keyword_set)
        ]
        counts_refs = [
            count_payload
            for count_payload in table_counts
            if any(keyword in str(count_payload.get("db_path", "")).lower() for keyword in keyword_set)
        ]
        return {
            "db_refs": db_refs,
            "config_refs": config_refs,
            "schema_refs": schema_refs,
            "table_count_refs": counts_refs,
        }

    m3_conport = {
        "generated_at": now_iso(),
        "service": "conport",
        "summary": filter_refs(conport_keywords),
        "redaction": {"values": "REDACTED", "identifier_hash": "sha256(value)[:12]"},
    }

    m4_dope_context = {
        "generated_at": now_iso(),
        "service": "dope_context",
        "summary": filter_refs(dope_context_keywords),
        "redaction": {"values": "REDACTED", "identifier_hash": "sha256(value)[:12]"},
    }

    m5_mcp_health = {
        "generated_at": now_iso(),
        "sqlite3_available": True,
        "mcp_config_files": [
            summary for summary in config_summaries if "/mcp/" in summary["path"] or "mcp" in summary["path"]
        ],
        "mcp_servers": mcp_servers,
        "network_calls_attempted": False,
    }

    seed_outputs = [
        seed_dir / "M0_RUNTIME_EXPORT_INVENTORY.seed.json",
        seed_dir / "M1_SQLITE_SCHEMA_SNAPSHOTS.seed.json",
        seed_dir / "M2_SQLITE_TABLE_COUNTS.seed.json",
        seed_dir / "M3_CONPORT_EXPORT_SAFE.seed.json",
        seed_dir / "M4_DOPE_CONTEXT_EXPORT_SAFE.seed.json",
        seed_dir / "M5_MCP_HEALTH_EXPORT_SAFE.seed.json",
        seed_dir / "M6_RUNTIME_EXPORT_INDEX.seed.json",
    ]

    m6_index = {
        "generated_at": now_iso(),
        "attempted_exports": [
            "inventory_allowlisted_home_paths",
            "sqlite_schema_snapshots",
            "sqlite_table_counts",
            "conport_safe_summary",
            "dope_context_safe_summary",
            "mcp_health_safe_summary",
        ],
        "suggested_sqlite_verification_commands": [
            'sqlite3 <db> ".schema"',
            'sqlite3 <db> "select name from sqlite_master where type=\'table\';"',
            'sqlite3 <db> "select count(*) from <table>;"',
            'sqlite3 <db> "pragma user_version;"',
        ],
        "outputs_produced": [str(path.resolve()) for path in seed_outputs[:-1]],
        "redaction_rules_applied": [
            "REDACTED values for config content",
            "sha256(value)[:12] for stable identifiers",
            "no sqlite row exports",
        ],
        "missing_prerequisites": missing_roots,
        "caps_hit": {"runtime_inventory_truncated": truncated},
    }

    payloads = [
        m0_inventory,
        m1_schema,
        m2_counts,
        m3_conport,
        m4_dope_context,
        m5_mcp_health,
        m6_index,
    ]
    for path, payload in zip(seed_outputs, payloads):
        write_json(path, payload)

    return seed_outputs


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


def merge_items(*groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    dedup: Dict[str, Dict[str, Any]] = {}
    for group in groups:
        for item in group:
            path = str(item.get("path", "")).strip()
            if not path:
                continue
            dedup[path] = item
    return sorted(dedup.values(), key=lambda item: str(item.get("path", "")))


def collect_repo_magic_items(repo_root: Path) -> List[Dict[str, Any]]:
    collector = Collector(repo_root, [".git", "node_modules", "venv", ".venv", "extraction"])
    collected = collector.collect(subdirs=REPO_MAGIC_SUBDIRS + REPO_MAGIC_EXPLICIT_FILES)
    glob_paths: List[Path] = []
    for pattern in REPO_MAGIC_GLOBS:
        glob_paths.extend(sorted(repo_root.glob(pattern)))
    return merge_items(collected, to_items(glob_paths))


def collect_home_magic_items(home_root: Path) -> List[Dict[str, Any]]:
    collector = Collector(home_root, ["Downloads", "Library", ".cache", ".npm", ".pip"])
    return collector.collect(subdirs=HOME_MAGIC_SUBDIRS)


def collect_docs_instruction_items(repo_root: Path) -> List[Dict[str, Any]]:
    paths: List[Path] = []
    for pattern in DOC_INSTRUCTION_GLOBS:
        for path in sorted(repo_root.glob(pattern)):
            if path.is_file() and is_text_candidate(path):
                paths.append(path.resolve())
    return to_items(paths)


def collect_phase_c_magic_callers(repo_root: Path) -> List[Dict[str, Any]]:
    caller_paths: List[Path] = []
    patterns = [
        "scripts/**/*call*.py",
        "scripts/**/*call*.sh",
        "scripts/**/*mcp*.py",
        "scripts/**/*mcp*.sh",
        "tools/**/*call*.py",
        "tools/**/*call*.sh",
        "tools/**/*mcp*.py",
        "tools/**/*mcp*.sh",
        "src/**/cli.py",
        "src/**/main.py",
    ]
    for pattern in patterns:
        for path in sorted(repo_root.glob(pattern)):
            if path.is_file() and is_text_candidate(path):
                caller_paths.append(path.resolve())
    return to_items(caller_paths)


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


def _ensure_required_norm_artifact_groups(
    dirs: Dict[str, Path], required_groups: Dict[str, List[Tuple[str, ...]]]
) -> List[str]:
    missing: List[str] = []
    for phase, groups in required_groups.items():
        norm_dir = dirs[phase] / "norm"
        if not norm_dir.exists():
            missing.append(f"{phase}: missing norm directory {norm_dir}")
            continue
        for group in groups:
            if not any(_has_matching_file(norm_dir, pattern) for pattern in group):
                pattern_desc = " or ".join(group)
                missing.append(f"{phase}: no artifact matching {pattern_desc} under {norm_dir}")
    return missing


def _ensure_r_full_prompt_set() -> None:
    prompts = get_phase_prompts("R")
    prompt_steps = sorted(spec.step_id for spec in prompts)
    expected = sorted(R_FULL_STEP_IDS)
    if prompt_steps != expected:
        missing = sorted(set(expected) - set(prompt_steps))
        extra = sorted(set(prompt_steps) - set(expected))
        details: List[str] = []
        if missing:
            details.append(f"missing steps: {', '.join(missing)}")
        if extra:
            details.append(f"unexpected steps: {', '.join(extra)}")
        detail_text = "; ".join(details) if details else f"found steps: {prompt_steps}"
        raise RuntimeError(
            "Phase R requires full prompt set R0-R8. "
            + detail_text
        )


def run_phase_A(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
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
        "docker-compose.dev.yml",
        "docker-compose.prod.yml",
        "docker-compose.smoke.yml",
        "Makefile",
        ".claude.json",
        ".taskxroot",
    ]
    forced_items = collect_repo_magic_items(Path.cwd())
    _run_phase_inner("A", dirs, cfg, collector, targets, forced_items=forced_items)


def run_phase_H(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
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
    items = merge_items(items, collect_home_magic_items(home))
    if cfg.home_scan_mode == "safe":
        items = home_safe_filter(items, home)
    _run_phase_inner("H", dirs, cfg, None, None, precollected_items=items)


def run_phase_M(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    seed_files = build_phase_m_seed_inputs(dirs["M"])
    _run_phase_inner("M", dirs, cfg, None, None, precollected_items=to_items(seed_files))


def run_phase_C(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    collector = Collector(Path.cwd(), [".git", "node_modules", "venv", ".venv", "docs", "test-results"])
    targets = ["src", "services", "shared", "plugins", "tools", "scripts", "tests"]
    forced_items = collect_phase_c_magic_callers(Path.cwd())
    _run_phase_inner("C", dirs, cfg, collector, targets, forced_items=forced_items)


def run_phase_D(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    collector = Collector(Path.cwd(), [".git"])
    forced_items = merge_items(
        collect_repo_magic_items(Path.cwd()),
        collect_docs_instruction_items(Path.cwd()),
    )
    _run_phase_inner("D", dirs, cfg, collector, ["docs"], forced_items=forced_items)


def run_phase_E(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    collector = Collector(Path.cwd(), [".git", "node_modules", "docs"])
    targets = ["scripts", "tools", "compose", ".github", "Makefile", "package.json"]
    _run_phase_inner("E", dirs, cfg, collector, targets)


def run_phase_W(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    collector = Collector(Path.cwd(), [".git", "node_modules"])
    forced_items = collect_repo_magic_items(Path.cwd())
    _run_phase_inner("W", dirs, cfg, collector, ["docs", "scripts", "src", "services"], forced_items=forced_items)


def run_phase_B(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    collector = Collector(Path.cwd(), [".git", "node_modules"])
    forced_items = collect_repo_magic_items(Path.cwd())
    _run_phase_inner("B", dirs, cfg, collector, ["src", "services", "docs"], forced_items=forced_items)


def run_phase_G(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    collector = Collector(Path.cwd(), [".git", "node_modules"])
    forced_items = collect_repo_magic_items(Path.cwd())
    _run_phase_inner("G", dirs, cfg, collector, [".github", "docs", ".claude", "AGENTS.md"], forced_items=forced_items)


def run_phase_Q(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    items = collect_phase_artifacts(
        dirs,
        ["A", "H", "M", "D", "C", "E", "W", "B", "G"],
        ["raw", "norm", "qa"],
    )
    _run_phase_inner("Q", dirs, cfg, None, None, precollected_items=items)


def run_phase_R(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    _ensure_r_full_prompt_set()
    required_groups_by_profile = load_r_required_artifact_groups_by_profile()
    required_groups = required_groups_by_profile.get(cfg.r_profile)
    if required_groups is None:
        raise RuntimeError(f"Unsupported r-profile '{cfg.r_profile}'. Expected base or full.")
    required_input_phases = required_input_phases_for_r_profile(cfg.r_profile)

    missing: List[str] = []
    input_files: List[Path] = []
    for phase in required_input_phases:
        phase_norm = dirs[phase] / "norm"
        if phase_norm.exists():
            phase_files: List[Path] = []
            phase_files.extend(sorted(phase_norm.glob("*.json")))
            if not phase_files:
                missing.append(f"{phase}: no json artifacts under {phase_norm}")
            else:
                input_files.extend(phase_files)
        else:
            missing.append(f"{phase}: missing norm directory {phase_norm}")

    missing.extend(_ensure_required_norm_artifact_groups(dirs, required_groups))

    if missing:
        python_cmd = Path(sys.executable).name or "python3"
        missing_sorted = sorted(set(missing))
        recovery_commands = [
            f"{python_cmd} UPGRADES/run_extraction_v3.py --phase A --resume",
            f"{python_cmd} UPGRADES/run_extraction_v3.py --phase H --resume --home-scan-mode safe",
            f"{python_cmd} UPGRADES/run_extraction_v3.py --phase D --resume",
            f"{python_cmd} UPGRADES/run_extraction_v3.py --phase C --resume",
            f"{python_cmd} UPGRADES/run_extraction_v3.py --phase R --resume --r-profile {cfg.r_profile}",
        ]
        if cfg.r_profile == "full":
            recovery_commands.insert(
                2, f"{python_cmd} UPGRADES/run_extraction_v3.py --phase M --resume"
            )
        required_phases_desc = "/".join(required_input_phases)
        raise RuntimeError(
            f"Phase R requires normalized inputs for profile '{cfg.r_profile}' from {required_phases_desc}.\n"
            + "Missing norm artifacts:\n- "
            + "\n- ".join(missing_sorted)
            + "\nRecovery order:\n- "
            + "\n- ".join(recovery_commands)
        )

    deduped_inputs = sorted(set(input_files), key=lambda path: str(path))
    _run_phase_inner("R", dirs, cfg, None, None, precollected_items=to_items(deduped_inputs))


def run_phase_X(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    r_norm = dirs["R"] / "norm"
    r_inputs: List[Path] = []
    if r_norm.exists():
        r_inputs.extend(sorted(r_norm.glob("*.json")))
        r_inputs.extend(sorted(r_norm.glob("*.md")))
    if not r_inputs:
        raise RuntimeError(f"Phase X requires R norm outputs at {r_norm}")
    _run_phase_inner("X", dirs, cfg, None, None, precollected_items=to_items(r_inputs))


def run_phase_T(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    input_files: List[Path] = []
    for phase in ["R", "X"]:
        norm_dir = dirs[phase] / "norm"
        if norm_dir.exists():
            input_files.extend(sorted(norm_dir.glob("*.json")))
            input_files.extend(sorted(norm_dir.glob("*.md")))
    _run_phase_inner("T", dirs, cfg, None, None, precollected_items=to_items(input_files))


def run_phase_Z(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    final_items = collect_phase_artifacts(dirs, ["R", "X", "T"], ["raw", "norm", "qa"])
    _run_phase_inner("Z", dirs, cfg, None, None, precollected_items=final_items)


# --- Master Orchestrator ---

def main() -> None:
    parser = argparse.ArgumentParser("Master Extraction Runner")
    parser.add_argument("--phase", choices=PHASES + ["ALL"], required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-files-docs", type=int, default=35)
    parser.add_argument("--max-files-code", type=int, default=20)
    parser.add_argument("--max-chars", type=int, default=650000)
    parser.add_argument("--file-truncate-chars", type=int, default=70000)
    parser.add_argument("--home-scan-mode", choices=["safe", "full"], default="safe")
    parser.add_argument("--r-profile", choices=["base", "full"], default="base")
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--rpm-openai", type=int, default=60)
    parser.add_argument("--tpm-openai", type=int, default=120000)
    parser.add_argument("--rpm-gemini", type=int, default=15)
    parser.add_argument("--tpm-gemini", type=int, default=64000)
    parser.add_argument("--rpm-xai", type=int, default=30)
    parser.add_argument("--tpm-xai", type=int, default=90000)
    parser.add_argument("--max-inflight", type=int, default=1)
    args = parser.parse_args()

    root = Path.cwd()
    try:
        run_id = load_run_id(root)
        dirs = get_run_dirs(root, run_id)
    except Exception as exc:
        logger.error("Setup failed: %s", exc)
        sys.exit(1)

    cfg = RunnerConfig(
        dry_run=args.dry_run,
        max_files_docs=args.max_files_docs,
        max_files_code=args.max_files_code,
        max_chars=args.max_chars,
        file_truncate_chars=args.file_truncate_chars,
        home_scan_mode=args.home_scan_mode,
        r_profile=args.r_profile,
        resume=args.resume,
        rpm_openai=args.rpm_openai,
        tpm_openai=args.tpm_openai,
        rpm_gemini=args.rpm_gemini,
        tpm_gemini=args.tpm_gemini,
        rpm_xai=args.rpm_xai,
        tpm_xai=args.tpm_xai,
        max_inflight=max(args.max_inflight, 1),
    )

    write_run_manifest(root, dirs, run_id, args)
    logger.info("Target Run ID: %s", run_id)
    logger.info("Home scan mode: %s", cfg.home_scan_mode)
    logger.info("Phase R profile: %s", cfg.r_profile)

    if args.phase == "ALL":
        phases = ["A", "H", "M", "D", "E", "C", "W", "B", "G", "Q", "R", "X", "T", "Z"]
    else:
        phases = [args.phase]

    runners = {
        "A": run_phase_A,
        "H": run_phase_H,
        "M": run_phase_M,
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
    }

    for phase in phases:
        run_phase = runners.get(phase)
        if run_phase is None:
            logger.warning("Unknown phase: %s", phase)
            continue
        try:
            run_phase(dirs, cfg)
        except Exception as exc:
            logger.error("Phase %s failed: %s", phase, exc)
            sys.exit(1)


if __name__ == "__main__":
    main()
