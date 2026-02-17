#!/usr/bin/env python3
"""
Master extraction runner (A/H/D/C/E/W/B/G/Q/R/X/T/Z) with deterministic:
inventory -> partitioning -> per-partition raw outputs -> norm merge -> QA.
"""

import argparse
import fnmatch
import hashlib
import json
import logging
import os
import re
import platform
import subprocess
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests

# --- Configuration & Constants ---

PHASES = ["A", "H", "D", "C", "E", "W", "B", "G", "Q", "R", "X", "T", "Z"]
VERIFY_PHASE_CHOICES = PHASES + ["ALL"]
PROOF_PACK_FILENAME = "PROOF_PACK.json"
RUNNER_SCRIPT = Path(__file__).resolve()
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
}
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

MODEL_ROUTING = {
    "A": ("gemini", "gemini-2.0-flash-001", "GEMINI_API_KEY"),
    "H": ("gemini", "gemini-2.0-flash-001", "GEMINI_API_KEY"),
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
    r"(?i)\b(api[_-]?key|authorization|bearer|token|secret|password|private[_-]?key)\b"
)
SECRET_ASSIGN_RE = re.compile(
    r"(?i)^(\s*['\"]?[^:=\n]*?(?:api[_-]?key|authorization|bearer|token|secret|password|private[_-]?key)"
    r"[^:=\n]*?['\"]?\s*[:=]\s*).*$"
)
LONG_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9+/=_-])[A-Za-z0-9+/=_-]{33,}(?![A-Za-z0-9+/=_-])")
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
    "T1": ("TP_BACKLOG_TOPN.json",),
}


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
    max_request_bytes: int
    file_truncate_chars: int
    home_scan_mode: str
    resume: bool
    fail_fast_auth: bool
    gemini_auth_mode: str
    retry_policy: str
    retry_max_attempts: int
    retry_base_seconds: float
    retry_max_seconds: float
    phase_auth_fail_threshold: int


@dataclass(frozen=True)
class PromptSpec:
    step_id: str
    prompt_path: Path
    output_artifacts: Tuple[str, ...]


# --- Helpers ---

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def determine_run_id(root: Path, override: Optional[str]) -> str:
    """Return the run_id from override or latest file, validating existence."""
    if override:
        candidate = root / "extraction" / "runs" / override
        if not candidate.exists():
            raise FileNotFoundError(f"Run directory {candidate} does not exist.")
        if not candidate.is_dir():
            raise NotADirectoryError(f"Path {candidate} is not a directory.")
        return override
    return load_run_id(root)


def get_run_dirs(root: Path, run_id: str) -> Dict[str, Path]:
    """Return dict of run paths and ensure required folders exist."""
    base = root / "extraction/runs" / run_id
    if not base.exists():
        raise FileNotFoundError(f"Run directory {base} does not exist.")

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
        rel_home = str(resolved.relative_to(home)).replace('\\', '/')
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
            "retry_policy": args.retry_policy,
            "retry_max_attempts": args.retry_max_attempts,
            "retry_base_seconds": args.retry_base_seconds,
            "retry_max_seconds": args.retry_max_seconds,
            "phase_auth_fail_threshold": args.phase_auth_fail_threshold,
            "run_id_override": args.run_id,
            "doctor": args.doctor,
            "doctor_auth": args.doctor_auth,
            "verify_phase_output": args.verify_phase_output,
            "print_config": args.print_config,
        },
    }
    write_json(dirs["root"] / "RUN_MANIFEST.json", manifest)


def write_runner_identity(root: Path, run_root: Path) -> None:
    payload = {
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


def write_run_routing_fingerprint(
    run_root: Path,
    run_id: str,
    cfg: RunnerConfig,
    phases: List[str],
) -> None:
    phase_entries: Dict[str, List[Dict[str, Any]]] = {}
    for phase in phases:
        prompts = get_phase_prompts(phase)
        entries: List[Dict[str, Any]] = []
        provider, model_id, _ = MODEL_ROUTING.get(phase, ("xai", "grok-code-fast-1", "XAI_API_KEY"))
        endpoint_base = llm_base_url(provider)
        default_sequence = (
            _gemini_auth_mode_sequence(cfg.gemini_auth_mode, endpoint_base)
            if provider == "gemini"
            else ["bearer"]
        )
        for prompt in prompts:
            entries.append(
                {
                    "step_id": prompt.step_id,
                    "prompt_file": prompt.prompt_path.name,
                    "declared_outputs": list(prompt.output_artifacts),
                    "provider": provider,
                    "model_id": model_id,
                    "endpoint_base_url": endpoint_base,
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
            "gemini_auth_mode_requested": cfg.gemini_auth_mode,
            "fail_fast_auth": cfg.fail_fast_auth,
        },
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
    prompt_paths = sorted(Path("UPGRADES").glob("PROMPT_*.md"))
    for prompt_path in prompt_paths:
        match = re.match(r"PROMPT_([A-Z][0-9]+)_", prompt_path.name)
        if not match:
            continue
        step_id = match.group(1)
        step_map[step_id].append(prompt_path)

    phase_map: Dict[str, Dict[str, List[Path]]] = defaultdict(dict)
    duplicates: Dict[str, List[str]] = {}
    for step_id in sorted(step_map.keys()):
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
            errors.append(f"No prompts found for phase {phase} (UPGRADES/PROMPT_{phase}*).")

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
) -> None:
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
    }

    write_json(qa_dir / f"{step_id}_QA.json", qa_payload)


# --- LLM Execution ---

def llm_base_url(provider: str) -> str:
    return PROVIDER_BASE_URL.get(provider, PROVIDER_BASE_URL["openai"])


def build_chat_payload(
    provider: str,
    model_id: str,
    system_prompt: str,
    user_content: str,
) -> Dict[str, Any]:
    _ = provider
    return {
        "model": model_id,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.1,
    }


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


def classify_failure_type(status_code: Optional[int], response_body: str, error_text: str) -> str:
    body = (response_body or "").lower()
    err = (error_text or "").lower()
    joined = f"{body}\n{err}"
    if "api key not found" in joined or "api_key_invalid" in joined:
        return "api_key_missing_or_invalid"
    if "missing authorization header" in joined:
        return "auth_missing"
    if "permission_denied" in joined:
        return "permission_denied"
    if "resource_exhausted" in joined or "billing" in joined or "quota" in joined:
        return "billing_or_quota"
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
        or failure_type in {"quota_or_billing", "billing_or_quota", "api_key_missing_or_invalid", "permission_denied"}
    ):
        return False
    if status_code in {408, 429, 500, 502, 503, 504}:
        return True
    if exc is not None and is_retryable_exception(exc):
        return True
    return False


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
) -> Dict[str, Any]:
    base_url = llm_base_url(provider)
    api_key = os.getenv(api_key_env)
    if not api_key:
        logger.error("Missing API key env var: %s", api_key_env)
        sent_headers = make_headers(provider, "", cfg, cfg.gemini_auth_mode if provider == "gemini" else None)
        return {
            "ok": False,
            "text": "",
            "meta": {
                "provider": provider,
                "model_id": model_id,
                "endpoint_base_url": base_url,
                "endpoint_effective": endpoint_effective(f"{base_url}/chat/completions"),
                **endpoint_fingerprint(f"{base_url}/chat/completions"),
                "status_code": None,
                "failure_type": "auth_missing",
                "sent_header_keys": sorted(list(sent_headers.keys())),
                "auth_present_flags": build_auth_present_flags(sent_headers, False),
                "gemini_auth_mode_requested": cfg.gemini_auth_mode if provider == "gemini" else None,
                "gemini_auth_mode_effective": None,
                "provider_signature": provider_signature(
                    provider,
                    model_id,
                    f"{base_url}/chat/completions",
                    None,
                ),
                "provider_error_reason": "MISSING_API_KEY_ENV",
                "gemini_endpoint_family": "openai_compat"
                if provider == "gemini" and _is_gemini_openai_compat_endpoint(base_url)
                else ("native" if provider == "gemini" else None),
                "gemini_auth_attempt_sequence": _gemini_auth_mode_sequence(cfg.gemini_auth_mode, base_url)
                if provider == "gemini"
                else None,
                "request_payload_bytes": None,
                "retry_trace": [],
            },
        }

    payload = build_chat_payload(provider, model_id, system_prompt, user_content)
    body = serialize_payload_body(payload)
    request_payload_bytes = measure_payload_bytes_from_body(body)
    gemini_mode_requested = cfg.gemini_auth_mode if provider == "gemini" else None
    gemini_family = (
        "openai_compat" if provider == "gemini" and _is_gemini_openai_compat_endpoint(base_url) else "native"
    ) if provider == "gemini" else None
    auth_mode_sequence = _gemini_auth_mode_sequence(cfg.gemini_auth_mode, base_url) if provider == "gemini" else ["bearer"]
    effective_mode = auth_mode_sequence[0]
    if provider == "gemini":
        url, headers, auth_flags = _gemini_build_endpoint_and_headers(base_url, api_key, effective_mode)
    else:
        url = make_url(provider, base_url, cfg, api_key, effective_mode)
        headers = make_headers(provider, api_key, cfg, effective_mode)
        auth_flags = build_auth_present_flags(headers, False)

    last_failure_meta: Dict[str, Any] = {
        "provider": provider,
        "model_id": model_id,
        "endpoint_base_url": base_url,
        "endpoint_effective": endpoint_effective(url),
        **endpoint_fingerprint(url),
        "status_code": None,
        "failure_type": "unknown",
        "request_payload_bytes": request_payload_bytes,
        "sent_header_keys": sorted(list(headers.keys())),
        "auth_present_flags": auth_flags,
        "gemini_auth_mode_requested": gemini_mode_requested,
        "gemini_auth_mode_effective": effective_mode if provider == "gemini" else None,
        "provider_signature": provider_signature(
            provider,
            model_id,
            url,
            effective_mode if provider == "gemini" else None,
        ),
        "provider_error_reason": None,
        "gemini_endpoint_family": gemini_family,
        "gemini_auth_attempt_sequence": auth_mode_sequence if provider == "gemini" else None,
        "retry_trace": [],
    }
    retry_trace: List[Dict[str, Any]] = []
    mode_index = 0

    attempt = 0
    while attempt < cfg.retry_max_attempts:
        attempt += 1
        response = None
        exc_obj: Optional[Exception] = None
        provider_error_reason = None
        try:
            response = requests.post(url, headers=headers, data=body, timeout=180)
            response.raise_for_status()
            data = response.json()
            retry_trace.append(
                {
                    "attempt": attempt,
                    "status_code": response.status_code,
                    "failure_type": None,
                    "delay_seconds": 0.0,
                    "gemini_auth_mode_effective": effective_mode if provider == "gemini" else None,
                    "provider_error_reason": None,
                }
            )
            return {
                "ok": True,
                "text": data["choices"][0]["message"]["content"],
                "meta": {
                    "provider": provider,
                    "model_id": model_id,
                    "endpoint_base_url": base_url,
                    "endpoint_effective": endpoint_effective(url),
                    **endpoint_fingerprint(url),
                    "status_code": response.status_code,
                    "failure_type": None,
                    "request_payload_bytes": request_payload_bytes,
                    "sent_header_keys": sorted(list(headers.keys())),
                    "auth_present_flags": auth_flags,
                    "gemini_auth_mode_requested": gemini_mode_requested,
                    "gemini_auth_mode_effective": effective_mode if provider == "gemini" else None,
                    "provider_signature": provider_signature(
                        provider,
                        model_id,
                        url,
                        effective_mode if provider == "gemini" else None,
                    ),
                    "provider_error_reason": None,
                    "gemini_endpoint_family": gemini_family,
                    "gemini_auth_attempt_sequence": auth_mode_sequence if provider == "gemini" else None,
                    "retry_trace": retry_trace,
                },
            }
        except Exception as exc:
            exc_obj = exc
            response_body = ""
            status_code: Optional[int] = None
            if response is not None:
                try:
                    response_body = response.text[:1200]
                    status_code = response.status_code
                except Exception:
                    response_body = ""
            failure_type = classify_failure_type(status_code, response_body, str(exc))
            provider_error_reason = extract_provider_error_reason(response_body)
            safe_exc = sanitize_error_text(str(exc))
            safe_body = sanitize_error_text(response_body)
            retry_trace.append(
                {
                    "attempt": attempt,
                    "status_code": status_code,
                    "failure_type": failure_type,
                    "delay_seconds": 0.0,
                    "gemini_auth_mode_effective": effective_mode if provider == "gemini" else None,
                    "provider_error_reason": provider_error_reason,
                }
            )
            last_failure_meta = {
                "provider": provider,
                "model_id": model_id,
                "endpoint_base_url": base_url,
                "endpoint_effective": endpoint_effective(url),
                **endpoint_fingerprint(url),
                "status_code": status_code,
                "failure_type": failure_type,
                "request_payload_bytes": request_payload_bytes,
                "sent_header_keys": sorted(list(headers.keys())),
                "auth_present_flags": auth_flags,
                "gemini_auth_mode_requested": gemini_mode_requested,
                "gemini_auth_mode_effective": effective_mode if provider == "gemini" else None,
                "provider_signature": provider_signature(
                    provider,
                    model_id,
                    url,
                    effective_mode if provider == "gemini" else None,
                ),
                "provider_error_reason": provider_error_reason,
                "gemini_endpoint_family": gemini_family,
                "gemini_auth_attempt_sequence": auth_mode_sequence if provider == "gemini" else None,
                "retry_trace": retry_trace,
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
                provider == "gemini"
                and cfg.gemini_auth_mode == "auto"
                and is_auth_classified_failure(failure_type)
                and mode_index + 1 < len(auth_mode_sequence)
            ):
                mode_index += 1
                effective_mode = auth_mode_sequence[mode_index]
                url, headers, auth_flags = _gemini_build_endpoint_and_headers(base_url, api_key, effective_mode)
                logger.warning(
                    "Gemini auto auth pivot after auth_missing: next_mode=%s endpoint=%s",
                    effective_mode,
                    _sanitize_url(url),
                )
                continue

            if not should_retry(status_code, failure_type, exc_obj, cfg.retry_policy):
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
        "billing_or_quota",
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
    return enriched


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


def run_auth_doctor(root: Path, args: argparse.Namespace, cfg: RunnerConfig) -> int:
    phase = args.phase if args.phase in PHASES else "A"
    provider, model_id, api_key_env = MODEL_ROUTING.get(phase, ("gemini", "gemini-2.0-flash-001", "GEMINI_API_KEY"))
    if provider != "gemini":
        provider, model_id, api_key_env = ("gemini", "gemini-2.0-flash-001", "GEMINI_API_KEY")
    endpoint_base = llm_base_url(provider)
    auth_sequence = _gemini_auth_mode_sequence(cfg.gemini_auth_mode, endpoint_base)
    effective_mode = auth_sequence[0]
    api_key = os.getenv(api_key_env, "")
    endpoint_url, headers, auth_flags = _gemini_build_endpoint_and_headers(endpoint_base, api_key, effective_mode)
    result = call_llm(
        provider=provider,
        model_id=model_id,
        api_key_env=api_key_env,
        system_prompt="Return exactly OK.",
        user_content="Return the single token OK.",
        cfg=cfg,
    )
    meta = result.get("meta", {})
    doctor_dir = root / "extraction" / "doctor"
    doctor_dir.mkdir(parents=True, exist_ok=True)
    doctor_json = doctor_dir / "AUTH_DOCTOR.json"
    doctor_txt = doctor_dir / "AUTH_DOCTOR.txt"
    payload = {
        "generated_at": now_iso(),
        "phase": phase,
        "provider": provider,
        "model_id": model_id,
        "api_key_env_name": api_key_env,
        "api_key_present": bool(api_key),
        "api_key_length": len(api_key),
        "gemini_auth_mode_requested": cfg.gemini_auth_mode,
        "gemini_auth_mode_effective": meta.get("gemini_auth_mode_effective") or effective_mode,
        "gemini_auth_attempt_sequence": auth_sequence,
        "endpoint_effective": meta.get("endpoint_effective") or _sanitize_url(endpoint_url),
        "sent_header_keys": meta.get("sent_header_keys") or sorted(list(headers.keys())),
        "used_query_key": bool((meta.get("auth_present_flags") or {}).get("used_query_key", auth_flags["used_query_key"])),
        "status_code": meta.get("status_code"),
        "failure_type": meta.get("failure_type"),
        "provider_error_reason": meta.get("provider_error_reason"),
        "provider_signature": meta.get("provider_signature")
        or provider_signature(provider, model_id, _sanitize_url(endpoint_url), effective_mode),
    }
    write_json(doctor_json, payload)
    lines = [
        f"generated_at={payload['generated_at']}",
        f"phase={payload['phase']}",
        f"provider={payload['provider']}",
        f"model_id={payload['model_id']}",
        f"api_key_env_name={payload['api_key_env_name']}",
        f"api_key_present={str(payload['api_key_present']).lower()}",
        f"api_key_length={payload['api_key_length']}",
        f"gemini_auth_mode_requested={payload['gemini_auth_mode_requested']}",
        f"gemini_auth_mode_effective={payload['gemini_auth_mode_effective']}",
        f"endpoint_effective={payload['endpoint_effective']}",
        f"sent_header_keys={','.join(payload['sent_header_keys'] or [])}",
        f"used_query_key={str(payload['used_query_key']).lower()}",
        f"status_code={payload['status_code']}",
        f"failure_type={payload['failure_type']}",
        f"provider_error_reason={payload['provider_error_reason']}",
        f"provider_signature={payload['provider_signature']}",
    ]
    doctor_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0


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
    phase_dir: Path,
    cfg: RunnerConfig,
) -> int:
    step_id = prompt_spec.step_id
    prompt_path = prompt_spec.prompt_path
    output_artifacts = prompt_spec.output_artifacts
    prompt_text = safe_read(prompt_path)
    if not prompt_text:
        logger.error("Could not read prompt: %s", prompt_path)
        return

    raw_dir = phase_dir / "raw"
    provider, model_id, api_key_env = MODEL_ROUTING.get(
        phase, ("xai", "grok-code-fast-1", "XAI_API_KEY")
    )
    max_files = max_files_for_phase(phase, cfg)
    run_id = phase_dir.parent.name
    logger.info(
        "Step %s using prompt %s outputs=%s",
        step_id,
        prompt_path.name,
        list(output_artifacts),
    )
    resume_skipped = 0
    step_success_count = 0
    step_auth_failures = 0

    for partition in partitions:
        partition_id = partition["id"]
        out_json = raw_dir / f"{step_id}__{partition_id}.json"
        out_failed = raw_dir / f"{step_id}__{partition_id}.FAILED.txt"
        out_failed_json = raw_dir / f"{step_id}__{partition_id}.FAILED.json"
        out_trace = raw_dir / f"{step_id}__{partition_id}.TRACE.md"

        if cfg.resume and out_json.exists():
            resume_skipped += 1
            continue

        output_instructions = build_output_envelope_instructions(output_artifacts)
        prompt_prefix = (
            "Extract from the files below.\n"
            f"{output_instructions}\n"
            "\nFILES:\n"
        )
        reserved_chars = len(prompt_prefix)
        context_budget = max(cfg.max_chars - reserved_chars, 2048)
        current_budget = context_budget
        payload_body = b""
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
            payload = build_chat_payload(provider, model_id, prompt_text, user_prompt)
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
            gemini_sequence = _gemini_auth_mode_sequence(cfg.gemini_auth_mode, llm_base_url(provider))
            failure_meta = {
                "provider": provider,
                "model_id": model_id,
                "endpoint_base_url": llm_base_url(provider),
                "endpoint_effective": endpoint_effective(f"{llm_base_url(provider)}/chat/completions"),
                **endpoint_fingerprint(f"{llm_base_url(provider)}/chat/completions"),
                "status_code": None,
                "failure_type": "payload_unshrinkable",
                "request_payload_bytes": payload_bytes,
                "max_request_bytes": cfg.max_request_bytes,
                "over_by_bytes": over_by,
                "gemini_auth_mode_requested": cfg.gemini_auth_mode if provider == "gemini" else None,
                "gemini_auth_mode_effective": gemini_sequence[0] if provider == "gemini" else None,
                "provider_signature": provider_signature(
                    provider,
                    model_id,
                    f"{llm_base_url(provider)}/chat/completions",
                    gemini_sequence[0] if provider == "gemini" else None,
                ),
                "provider_error_reason": None,
                "gemini_endpoint_family": "openai_compat"
                if provider == "gemini" and _is_gemini_openai_compat_endpoint(llm_base_url(provider))
                else ("native" if provider == "gemini" else None),
                "gemini_auth_attempt_sequence": _gemini_auth_mode_sequence(cfg.gemini_auth_mode, llm_base_url(provider))
                if provider == "gemini"
                else None,
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
            out_failed.write_text(
                f"payload_unshrinkable: payload_bytes={payload_bytes} max_request_bytes={cfg.max_request_bytes}\n",
                encoding="utf-8",
            )
            write_json(out_failed_json, failure_meta)
            write_json(
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
            logger.error(
                "Payload over hard cap for %s %s: payload_bytes=%s max_request_bytes=%s",
                step_id,
                partition_id,
                payload_bytes,
                cfg.max_request_bytes,
            )
            continue

        if cfg.dry_run:
            logger.info(
                "Dry-run %s %s files=%s request_payload_bytes=%s redaction_hits=%s max_request_bytes=%s",
                step_id,
                partition_id,
                context_stats["files_included"],
                payload_bytes,
                context_stats["redaction_hits"],
                cfg.max_request_bytes,
            )

        if cfg.dry_run:
            gemini_sequence = _gemini_auth_mode_sequence(cfg.gemini_auth_mode, llm_base_url(provider))
            dry_mode = gemini_sequence[0] if provider == "gemini" else None
            dry_headers = (
                make_headers(provider, "REDACTED", cfg, dry_mode) if provider != "gemini"
                else _gemini_build_endpoint_and_headers(llm_base_url(provider), "REDACTED", dry_mode or "api_key")[1]
            )
            trace_text = (
                f"# PROMPT_FILE\n{prompt_path}\n\n# SYSTEM_PROMPT\n{prompt_text}\n\n"
                f"# PARTITION_ID\n{partition_id}\n\n# USER_CONTEXT_PREVIEW\n{context[:2000]}"
            )
            out_trace.write_text(trace_text, encoding="utf-8")
            dry_meta = {
                "provider": provider,
                "model_id": model_id,
                "endpoint_base_url": llm_base_url(provider),
                "endpoint_effective": endpoint_effective(f"{llm_base_url(provider)}/chat/completions"),
                **endpoint_fingerprint(f"{llm_base_url(provider)}/chat/completions"),
                "status_code": None,
                "failure_type": None,
                "request_payload_bytes": payload_bytes,
                "gemini_auth_mode_requested": cfg.gemini_auth_mode if provider == "gemini" else None,
                "gemini_auth_mode_effective": dry_mode,
                "gemini_auth_attempt_sequence": gemini_sequence if provider == "gemini" else None,
                "provider_signature": provider_signature(
                    provider,
                    model_id,
                    f"{llm_base_url(provider)}/chat/completions",
                    dry_mode if provider == "gemini" else None,
                ),
                "provider_error_reason": None,
                "gemini_endpoint_family": "openai_compat"
                if provider == "gemini" and _is_gemini_openai_compat_endpoint(llm_base_url(provider))
                else ("native" if provider == "gemini" else None),
                "sent_header_keys": sorted(list(dry_headers.keys())),
                "auth_present_flags": build_auth_present_flags(dry_headers, provider == "gemini" and dry_mode == "query_key"),
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
                    "request_meta": dry_meta,
                },
            )
            if out_failed.exists():
                out_failed.unlink()
            if out_failed_json.exists():
                out_failed_json.unlink()
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
        llm_result = call_llm(
            provider=provider,
            model_id=model_id,
            api_key_env=api_key_env,
            system_prompt=prompt_text,
            user_content=user_prompt,
            cfg=cfg,
        )
        response_text = str(llm_result.get("text", ""))
        request_meta = enrich_request_meta(
            llm_result.get("meta", {}),
            run_id=run_id,
            phase=phase,
            step_id=step_id,
            partition_id=partition_id,
            provider=provider,
            model_id=model_id,
        )
        request_meta.setdefault("request_payload_bytes", payload_bytes)

        if is_auth_classified_failure(request_meta.get("failure_type")):
            step_auth_failures += 1
            if cfg.fail_fast_auth and step_success_count == 0:
                raise RuntimeError(
                    f"Fail-fast auth triggered for step {step_id} partition {partition_id}. "
                    f"failure_type={request_meta.get('failure_type')} provider={provider} "
                    f"model={model_id} auth_mode={cfg.gemini_auth_mode}. "
                    "Check credentials, endpoint mode, and gemini auth strategy."
                )

        parsed = parse_json_from_response(response_text)
        artifacts = coerce_artifacts_from_response(
            parsed=parsed,
            raw_text=response_text,
            expected_artifacts=output_artifacts,
        )
        if not artifacts:
            out_failed.write_text(response_text, encoding="utf-8")
            write_json(
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
            logger.error("Artifact parse failed for %s %s", step_id, partition_id)
            write_json(
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
            continue

        step_success_count += 1
        write_json(
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
        if out_failed.exists():
            out_failed.unlink()
        if out_failed_json.exists():
            out_failed_json.unlink()

    if resume_skipped:
        logger.info("Resume: skipped %s existing outputs for step %s", resume_skipped, step_id)
    return step_auth_failures


def _run_phase_inner(
    phase: str,
    dirs: Dict[str, Path],
    cfg: RunnerConfig,
    collector: Optional[Collector],
    targets: Optional[List[str]],
    precollected_items: Optional[List[Dict[str, Any]]] = None,
) -> None:
    logger.info("--- Phase %s ---", phase)
    phase_dir = dirs[phase]
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

    logger.info(
        "Phase %s inventory=%s partitions=%s max_files=%s max_chars=%s",
        phase,
        len(inventory),
        len(partitions),
        max_files,
        cfg.max_chars,
    )

    phase_auth_failures = 0
    for prompt_spec in prompts:
        provider, model_id, api_key_env = MODEL_ROUTING.get(
            phase, ("xai", "grok-code-fast-1", "XAI_API_KEY")
        )
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
                if cfg.fail_fast_auth:
                    raise RuntimeError(
                        f"Gemini auth probe failed for phase={phase} step={prompt_spec.step_id} "
                        f"failure_type={probe_failure} env=GEMINI_API_KEY "
                        f"endpoint={probe.get('endpoint_effective')} "
                        f"mode={probe.get('gemini_auth_mode_effective')}."
                    )
        step_auth_failures = execute_step_for_partitions(
            phase=phase,
            prompt_spec=prompt_spec,
            partitions=partitions,
            phase_dir=phase_dir,
            cfg=cfg,
        )
        phase_auth_failures += step_auth_failures
        if phase_auth_failures >= cfg.phase_auth_fail_threshold:
            raise RuntimeError(
                f"Phase {phase} auth circuit breaker triggered: auth_failures={phase_auth_failures} "
                f"threshold={cfg.phase_auth_fail_threshold}. "
                "Check auth config, provider routing, and endpoint mode."
            )
        normalize_step(
            phase=phase,
            prompt_spec=prompt_spec,
            phase_dir=phase_dir,
            partitions=partitions,
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


def _verify_single_phase(phase: str, dirs: Dict[str, Path]) -> Tuple[int, Dict[str, Any], List[str]]:
    phase_dir = dirs.get(phase)
    if not phase_dir or not phase_dir.exists():
        print(f"VERIFY PHASE {phase}: MISSING DIRECTORY")
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

    return (0 if status == "PASS" else 2), counts, reasons


def verify_phase_output(dirs: Dict[str, Path], phases: List[str]) -> int:
    return_code = 0
    for phase in phases:
        code, _, _ = _verify_single_phase(phase, dirs)
        return_code = max(return_code, code)
    return return_code


def print_config(
    args: argparse.Namespace,
    root: Path,
    run_id: str,
    dirs: Dict[str, Path],
    cfg: RunnerConfig,
    phases: List[str],
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
            "print_config": args.print_config,
            "run_id_override": args.run_id,
            "dry_run": args.dry_run,
            "resume": args.resume,
            "home_scan_mode": args.home_scan_mode,
            "max_files_docs": args.max_files_docs,
            "max_files_code": args.max_files_code,
            "max_chars": args.max_chars,
            "max_request_bytes": args.max_request_bytes,
            "file_truncate_chars": args.file_truncate_chars,
            "fail_fast_auth": args.fail_fast_auth,
            "gemini_auth_mode": args.gemini_auth_mode,
            "retry_policy": args.retry_policy,
            "retry_max_attempts": args.retry_max_attempts,
            "retry_base_seconds": args.retry_base_seconds,
            "retry_max_seconds": args.retry_max_seconds,
            "phase_auth_fail_threshold": args.phase_auth_fail_threshold,
        },
        "limits": {
            "max_files_docs": cfg.max_files_docs,
            "max_files_code": cfg.max_files_code,
            "max_chars": cfg.max_chars,
            "max_request_bytes": cfg.max_request_bytes,
            "file_truncate_chars": cfg.file_truncate_chars,
        },
        "dirs": {phase: str(dirs[phase]) for phase in phases},
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
    _run_phase_inner("A", dirs, cfg, collector, targets)


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
    if cfg.home_scan_mode == "safe":
        items = home_safe_filter(items, home)
    _run_phase_inner("H", dirs, cfg, None, None, precollected_items=items)


def run_phase_C(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    collector = Collector(Path.cwd(), [".git", "node_modules", "venv", ".venv", "docs", "test-results"])
    targets = ["src", "services", "shared", "plugins", "tools", "scripts", "tests"]
    _run_phase_inner("C", dirs, cfg, collector, targets)


def run_phase_D(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    collector = Collector(Path.cwd(), [".git"])
    _run_phase_inner("D", dirs, cfg, collector, ["docs"])


def run_phase_E(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    collector = Collector(Path.cwd(), [".git", "node_modules", "docs"])
    targets = ["scripts", "tools", "compose", ".github", "Makefile", "package.json"]
    _run_phase_inner("E", dirs, cfg, collector, targets)


def run_phase_W(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    collector = Collector(Path.cwd(), [".git", "node_modules"])
    _run_phase_inner("W", dirs, cfg, collector, ["docs", "scripts", "src", "services"])


def run_phase_B(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    collector = Collector(Path.cwd(), [".git", "node_modules"])
    _run_phase_inner("B", dirs, cfg, collector, ["src", "services", "docs"])


def run_phase_G(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    collector = Collector(Path.cwd(), [".git", "node_modules"])
    _run_phase_inner("G", dirs, cfg, collector, [".github", "docs", ".claude", "AGENTS.md"])


def run_phase_Q(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
    items = collect_phase_artifacts(dirs, ["A", "H", "D", "C", "E", "W", "B", "G"], ["raw", "norm", "qa"])
    _run_phase_inner("Q", dirs, cfg, None, None, precollected_items=items)


def run_phase_R(dirs: Dict[str, Path], cfg: RunnerConfig) -> None:
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
    parser.add_argument("--retry-policy", choices=["none", "default"], default="default")
    parser.add_argument("--retry-max-attempts", type=int, default=4)
    parser.add_argument("--retry-base-seconds", type=float, default=2.0)
    parser.add_argument("--retry-max-seconds", type=float, default=30.0)
    parser.add_argument("--phase-auth-fail-threshold", type=int, default=5)
    parser.add_argument("--run-id", type=str)
    parser.add_argument("--doctor", action="store_true")
    parser.add_argument("--doctor-auth", action="store_true")
    parser.add_argument("--verify-phase-output", choices=VERIFY_PHASE_CHOICES)
    parser.add_argument("--print-config", action="store_true")
    args = parser.parse_args()

    if args.doctor and not args.phase:
        parser.error("--phase is required when running in --doctor mode.")
    if not args.phase and not args.verify_phase_output and not args.print_config and not args.doctor_auth:
        parser.error("--phase is required unless --verify-phase-output or --print-config are used.")

    root = Path.cwd()
    try:
        run_id = determine_run_id(root, args.run_id)
        dirs = get_run_dirs(root, run_id)
    except Exception as exc:
        logger.error("Setup failed: %s", exc)
        sys.exit(1)

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
        retry_policy=args.retry_policy,
        retry_max_attempts=max(1, args.retry_max_attempts),
        retry_base_seconds=max(0.0, args.retry_base_seconds),
        retry_max_seconds=max(0.0, args.retry_max_seconds),
        phase_auth_fail_threshold=max(1, args.phase_auth_fail_threshold),
    )

    write_run_manifest(root, dirs, run_id, args)
    write_runner_identity(root, dirs["root"])
    phase_sequence = resolve_phase_list(args.phase)
    if phase_sequence:
        write_run_routing_fingerprint(dirs["root"], run_id, cfg, phase_sequence)
    if args.print_config:
        print_config(args, root, run_id, dirs, cfg, phase_sequence)
        sys.exit(0)
    if args.doctor_auth:
        sys.exit(run_auth_doctor(root, args, cfg))

    if args.verify_phase_output:
        verify_targets = PHASES if args.verify_phase_output == "ALL" else [args.verify_phase_output]
        sys.exit(verify_phase_output(dirs, verify_targets))

    if args.doctor:
        success = run_doctor_checks(root, dirs, run_id, args.phase)
        sys.exit(0 if success else 1)

    logger.info("Target Run ID: %s", run_id)
    logger.info("Home scan mode: %s", cfg.home_scan_mode)

    if not phase_sequence:
        parser.error("--phase is required when running extraction phases.")
    phases = phase_sequence

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
    }

    run_started_at = now_iso()
    for phase in phases:
        phase_started_at = now_iso()
        run_phase = runners.get(phase)
        if run_phase is None:
            logger.warning("Unknown phase: %s", phase)
            continue
        try:
            run_phase(dirs, cfg)
        except Exception as exc:
            logger.error("Phase %s failed: %s", phase, exc)
            sys.exit(1)
        phase_finished_at = now_iso()
        counts = gather_phase_counts(dirs[phase])
        update_proof_pack(root, dirs, run_id, run_started_at, phase, counts, phase_started_at, phase_finished_at)


if __name__ == "__main__":
    main()
