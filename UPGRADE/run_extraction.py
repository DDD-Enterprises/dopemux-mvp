#!/usr/bin/env python3
"""
Production-grade Dopemux extraction runner with content injection,
chunking, retry, checkpointing, and cost tracking.

Features:
- File content injection (models receive actual file content from disk)
- Upstream output injection (transform phases get prior results)
- Smart chunking for content exceeding context limits
- Multi-model support (Gemini Flash + Grok) with bidirectional fallback
- Retry logic with exponential backoff
- Checkpoint/resume from failures
- Token budget validation
- Continue-on-failure (skips failed phases, keeps running)

Usage:
    python run_extraction.py --phases priority          # Run priority phases only
    python run_extraction.py --phases all               # Run everything
    python run_extraction.py --resume --phases priority  # Resume from checkpoint
    python run_extraction.py --dry-run                  # Test without API calls

Environment variables:
    GEMINI_API_KEY  - Required for Flash phases (H/I/W/Docs)
    XAI_API_KEY     - Required for Grok phases (Code A-F), fallback for Flash
"""

import argparse
import json
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("ERROR: 'requests' library required. Install: pip install requests")
    sys.exit(1)


# ─── Model Configuration ──────────────────────────────────────────────────

MODEL_LIMITS = {
    "gemini": {"input": 1_000_000, "output": 8_192,
               "input_price": 0.10, "output_price": 0.40},
    "grok":   {"input": 256_000,   "output": 10_000,
               "input_price": 0.50, "output_price": 1.50},
}

_FLASH = ("gemini", "gemini-2.0-flash-001", "GEMINI_API_KEY")
_GROK = ("grok", "grok-code-fast-1", "XAI_API_KEY")

MODEL_ROUTING = {
    "H1": _FLASH, "H2": _FLASH, "H3": _FLASH, "H4": _FLASH,
    "I1": _FLASH, "I2": _FLASH, "I3": _FLASH,
    "W1": _FLASH, "W2": _FLASH, "W3": _FLASH,
    "A": _GROK, "B": _GROK, "C": _GROK, "D": _GROK, "E": _GROK, "F": _GROK,
    "D0": _FLASH, "D3": _FLASH, "M1": _FLASH, "QA": _FLASH, "CL": _FLASH,
}

# ─── Phase Configuration ──────────────────────────────────────────────────
# Keys: prompt, outputs, deps, group,
#       scan_globs, scan_roots ("repo"|["~/path"]), scan_exts, scan_excludes,
#       max_file_kb, head_lines, inject_from, sqlite_schema

PHASES = {
    # ── Instruction Plane ─────────────────────────────────────────────
    "I1": {
        "prompt": "EXEC_I1_INSTRUCTION_INDEX.md",
        "outputs": ["LLM_INSTRUCTION_INDEX.json"],
        "deps": [], "group": "priority",
        "scan_globs": [
            ".claude/**/*", "AGENTS.md", "mcp-proxy-config*",
            "start-mcp-servers.sh", "compose.yml", "compose/**/*",
            "docker-compose*.yml", ".dopemux/**/*", ".taskx/**/*",
            ".githooks/**/*", "docs/**/custom-instructions/**/*",
            "docs/llm/**/*", "docs/prompts/**/*",
        ],
    },
    "I2": {
        "prompt": "EXEC_I2_TOOLING_REFERENCES.md",
        "outputs": ["LLM_TOOLING_REFERENCES.json", "LLM_SERVER_CALL_SURFACE.json"],
        "deps": ["I1"], "group": "priority",
        "inject_from": {"I1": ["LLM_INSTRUCTION_INDEX.json"]},
        "scan_globs": [
            ".claude/**/*", "AGENTS.md", "mcp-proxy-config*",
            "start-mcp-servers.sh", "compose.yml", "compose/**/*",
            ".dopemux/**/*", ".taskx/**/*", ".githooks/**/*",
        ],
    },
    "I3": {
        "prompt": "PROMPT_I3_POLICY_GATES.md",
        "outputs": ["LLM_POLICY_GATES.json"],
        "deps": ["I1"], "group": "priority",
        "inject_from": {"I1": ["LLM_INSTRUCTION_INDEX.json"]},
        "scan_globs": [
            ".claude/**/*", "AGENTS.md", "mcp-proxy-config*",
            ".dopemux/**/*", ".taskx/**/*",
        ],
    },
    # ── Workflow Plane ────────────────────────────────────────────────
    "W1": {
        "prompt": "EXEC_W1_OPS_WORKFLOWS.md",
        "outputs": ["WORKFLOW_SURFACE_OPS.json"],
        "deps": [], "group": "priority",
        "scan_globs": [
            "compose.yml", "compose/**/*", "docker-compose*.yml",
            "scripts/**/*", "start-mcp-servers.sh",
            "Makefile", "justfile", "package.json", "pyproject.toml",
        ],
    },
    "W2": {
        "prompt": "PROMPT_W2_LLM_WORKFLOW_CUES.md",
        "outputs": ["WORKFLOW_SURFACE_LLM.json"],
        "deps": ["I1", "I2"], "group": "priority",
        "inject_from": {
            "I1": ["LLM_INSTRUCTION_INDEX.json"],
            "I2": ["LLM_TOOLING_REFERENCES.json", "LLM_SERVER_CALL_SURFACE.json"],
        },
        "scan_globs": [".claude/**/*", "AGENTS.md"],
    },
    "W3": {
        "prompt": "PROMPT_W3_WORKFLOW_GRAPH.md",
        "outputs": ["WORKFLOW_GRAPH_GLOBAL.json"],
        "deps": ["W1", "W2", "A"], "group": "priority",
        "inject_from": {
            "W1": ["WORKFLOW_SURFACE_OPS.json"],
            "W2": ["WORKFLOW_SURFACE_LLM.json"],
            "I2": ["LLM_SERVER_CALL_SURFACE.json"],
            "A": ["SERVICE_MAP.json"],
            "D": ["DB_SURFACE.json"],
        },
    },
    # ── Home Config ───────────────────────────────────────────────────
    "H1": {
        "prompt": "EXEC_H1_INVENTORY.md",
        "outputs": ["HOME_CONFIG_INVENTORY.json", "HOME_CONFIG_KEYS.json"],
        "deps": [], "group": "priority",
        "scan_globs": ["**/*"],
        "scan_roots": ["~/.dopemux", "~/.config/dopemux"],
        "scan_exts": {".json", ".yaml", ".yml", ".toml", ".env", ".sh",
                      ".conf", ".cfg", ".md", ".txt"},
        "scan_excludes": ["sessions/**", "cache/**", "*.log", "*.db",
                          "*.sqlite", "*.pyc", "__pycache__/**"],
        "max_file_kb": 100,
    },
    "H2": {
        "prompt": "EXEC_H2_SURFACES.md",
        "outputs": ["HOME_MCP_SURFACE.json", "HOME_ROUTER_SURFACE.json",
                     "HOME_HOOKS_SURFACE.json", "HOME_LITELLM_SURFACE.json"],
        "deps": [], "group": "priority",
        "scan_globs": [
            "mcp_config.json", "mcp-tools/**/*", "claude-code-router/**/*",
            "dope-brainz-router/**/*", "litellm/**/*", "hook_status.json",
            "tmux-layout.sh",
        ],
        "scan_roots": ["~/.dopemux", "~/.config/dopemux"],
        "scan_exts": {".json", ".yaml", ".yml", ".toml", ".sh", ".conf"},
        "scan_excludes": ["sessions/**", "*.log", "*.db"],
        "max_file_kb": 100,
    },
    "H3": {
        "prompt": "EXEC_H3_DIFF_HINTS.md",
        "outputs": ["HOME_VS_REPO_DIFF_HINTS.json"],
        "deps": ["H2"], "group": "priority",
        "inject_from": {
            "H2": ["HOME_MCP_SURFACE.json", "HOME_ROUTER_SURFACE.json",
                    "HOME_HOOKS_SURFACE.json", "HOME_LITELLM_SURFACE.json"],
        },
    },
    "H4": {
        "prompt": "EXEC_H4_SQLITE_SCHEMA.md",
        "outputs": ["HOME_SQLITE_SCHEMA.json"],
        "deps": [], "group": "priority",
        "scan_globs": ["**/*.db", "**/*.sqlite"],
        "scan_roots": ["~/.dopemux", "~/.config/dopemux"],
        "sqlite_schema": True,
    },
    # ── Code Phases ───────────────────────────────────────────────────
    "A": {
        "prompt": "EXEC_A_STRUCTURE_SERVICES_ENTRYPOINTS.md",
        "outputs": ["STRUCTURE_MAP.json", "SERVICE_MAP.json", "ENTRYPOINTS.json"],
        "deps": [], "group": "code",
        "scan_globs": [
            "services/**/*.py", "src/**/*.py", "config/**/*",
            "scripts/**/*", "compose.yml", "docker-compose*.yml",
            "Dockerfile*", "pyproject.toml", "setup.cfg", "setup.py",
        ],
    },
    "B": {
        "prompt": "EXEC_B_INTERFACES.md",
        "outputs": ["CLI_SURFACE.json", "API_SURFACE.json",
                     "MCP_SURFACE.json", "HOOKS_SURFACE.json"],
        "deps": [], "group": "code",
        "scan_globs": ["services/**/*.py", "src/**/*.py",
                       ".githooks/**/*", ".pre-commit-config.yaml"],
    },
    "C": {
        "prompt": "EXEC_C_EVENTS.md",
        "outputs": ["EVENT_EMITTERS.json", "EVENT_CONSUMERS.json",
                     "EVENT_ENVELOPE_FIELDS.json"],
        "deps": [], "group": "code",
        "scan_globs": ["services/**/*.py", "src/**/*.py"],
    },
    "D": {
        "prompt": "EXEC_D_DB_SURFACE.md",
        "outputs": ["DB_SURFACE.json", "MIGRATIONS.json", "DAO_SURFACE.json"],
        "deps": [], "group": "code",
        "scan_globs": ["services/**/*.py", "src/**/*.py",
                       "services/**/migrations/**/*", "alembic/**/*",
                       "services/**/*.sql", "src/**/*.sql"],
    },
    "E": {
        "prompt": "EXEC_E_ENV_CONFIG_SECRETS.md",
        "outputs": ["ENV_VARS.json", "CONFIG_LOADERS.json",
                     "SECRETS_RISK_LOCATIONS.json"],
        "deps": [], "group": "code",
        "scan_globs": ["services/**/*.py", "src/**/*.py", "config/**/*",
                       ".env*", "pyproject.toml", "compose.yml"],
    },
    "F": {
        "prompt": "EXEC_F_RISK_SCAN.md",
        "outputs": ["DETERMINISM_RISKS.json"],
        "deps": [], "group": "code",
        "scan_globs": ["services/**/*.py", "src/**/*.py"],
    },
    # ── Docs Phases ───────────────────────────────────────────────────
    "D0": {
        "prompt": "PROMPT_D0_INDEX_PARTITION.md",
        "outputs": ["DOC_INVENTORY.json", "DOC_PARTITIONS.json",
                     "DOC_TODO_QUEUE.json"],
        "deps": [], "group": "docs",
        "scan_globs": [
            "docs/**/*.md", ".claude/docs/**/*.md",
            "services/*/docs/**/*.md", "docker/mcp-servers/docs/**/*.md",
            "_audit_out/**/*.md", "quarantine/**/*.md",
        ],
        "head_lines": 25,
    },
    "D3": {
        "prompt": "PROMPT_D3_CITATION_GRAPH.md",
        "outputs": ["DOC_CITATION_GRAPH.json"],
        "deps": ["D0"], "group": "docs",
        "inject_from": {"D0": ["DOC_INVENTORY.json"]},
        "scan_globs": ["docs/**/*.md", ".claude/docs/**/*.md",
                       "services/*/docs/**/*.md"],
        "head_lines": 50,
    },
    "M1": {
        "prompt": "PROMPT_M1_MERGE_NORMALIZE.md",
        "outputs": ["DOC_INDEX.json", "DOC_CLAIMS.json", "DOC_BOUNDARIES.json",
                     "DOC_SUPERSESSION.json", "DOC_INTERFACES.json",
                     "DOC_WORKFLOWS.json", "DOC_DECISIONS.json",
                     "DOC_GLOSSARY.json"],
        "deps": ["D1", "D2"], "group": "docs",
    },
    "QA": {
        "prompt": "PROMPT_QA_COVERAGE_REPORT.md",
        "outputs": ["DOC_COVERAGE_REPORT.json"],
        "deps": ["M1", "D3"], "group": "docs",
        "inject_from": {
            "M1": ["DOC_INDEX.json", "DOC_CLAIMS.json"],
            "D3": ["DOC_CITATION_GRAPH.json"],
        },
    },
    "CL": {
        "prompt": "PROMPT_CL_TOPIC_CLUSTERS.md",
        "outputs": ["DOC_TOPIC_CLUSTERS.json"],
        "deps": ["M1"], "group": "docs",
        "inject_from": {"M1": ["DOC_INDEX.json", "DOC_CLAIMS.json"]},
    },
}

PRIORITY_ORDER = ["I1", "I2", "I3", "W1", "W2", "W3", "H1", "H2", "H3", "H4"]
CODE_ORDER = ["A", "B", "C", "D", "E", "F"]
DOCS_ORDER = ["D0", "D3", "M1", "QA", "CL"]

# Dirs to always skip when scanning
SKIP_DIRS = frozenset({
    "node_modules", ".git", ".venv", ".taskx_venv", "__pycache__",
    "SYSTEM_ARCHIVE", ".mypy_cache", ".pytest_cache",
})


# ─── Helpers ───────────────────────────────────────────────────────────────

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()

def _estimate_tokens(text: str) -> int:
    return len(text) // 4


# ─── Content Collector ─────────────────────────────────────────────────────

class ContentCollector:
    """Reads files from disk and formats them for prompt injection."""

    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir
        self.home_dirs = [
            Path.home() / ".dopemux",
            Path.home() / ".config" / "dopemux",
        ]

    def collect(self, phase_config: dict) -> list:
        """Collect files for a phase. Returns [(display_path, content), ...]."""
        globs = phase_config.get("scan_globs", [])
        if not globs:
            return []

        roots = phase_config.get("scan_roots", "repo")
        if roots == "repo":
            base_dirs = [self.repo_dir]
        elif isinstance(roots, list):
            base_dirs = [Path(r).expanduser() for r in roots]
        else:
            base_dirs = [Path(roots).expanduser()]

        exts = phase_config.get("scan_exts")
        excludes = phase_config.get("scan_excludes", [])
        max_size = phase_config.get("max_file_kb", 200) * 1024
        head_n = phase_config.get("head_lines")

        files = []
        seen = set()

        for base_dir in base_dirs:
            if not base_dir.exists():
                continue
            for glob_pattern in globs:
                try:
                    for path in sorted(base_dir.glob(glob_pattern)):
                        if not path.is_file() or path in seen:
                            continue
                        if any(part in SKIP_DIRS for part in path.parts):
                            continue
                        rel = str(path.relative_to(base_dir))
                        if any(path.match(ex) for ex in excludes):
                            continue
                        if exts and path.suffix.lower() not in exts:
                            continue
                        try:
                            if path.stat().st_size > max_size:
                                continue
                        except OSError:
                            continue
                        seen.add(path)
                        try:
                            content = path.read_text(encoding="utf-8", errors="replace")
                            if head_n:
                                content = "\n".join(content.split("\n")[:head_n])
                            if str(base_dir).startswith(str(Path.home())):
                                display = "~/" + str(path.relative_to(Path.home()))
                            else:
                                display = rel
                            files.append((display, content))
                        except (OSError, UnicodeDecodeError):
                            continue
                except (OSError, ValueError):
                    continue
        return files

    def collect_sqlite_schemas(self, phase_config: dict) -> list:
        """Extract DDL from SQLite files via sqlite3 CLI."""
        if not phase_config.get("sqlite_schema"):
            return []
        globs = phase_config.get("scan_globs", [])
        roots = phase_config.get("scan_roots", "repo")
        base_dirs = ([self.repo_dir] if roots == "repo"
                     else [Path(r).expanduser() for r in roots])
        schemas = []
        for base_dir in base_dirs:
            if not base_dir.exists():
                continue
            for glob_pattern in globs:
                for path in sorted(base_dir.glob(glob_pattern)):
                    if not path.is_file():
                        continue
                    try:
                        result = subprocess.run(
                            ["sqlite3", str(path), ".schema"],
                            capture_output=True, text=True, timeout=10,
                        )
                        if result.returncode == 0 and result.stdout.strip():
                            display = ("~/" + str(path.relative_to(Path.home()))
                                       if str(path).startswith(str(Path.home()))
                                       else str(path))
                            schemas.append((display, f"-- DDL for {display}\n{result.stdout}"))
                    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
                        continue
        return schemas

    @staticmethod
    def format_context(files: list) -> str:
        """Format files as context block for prompt injection."""
        if not files:
            return ""
        blocks = []
        for path, content in files:
            blocks.append(f"### FILE: {path}\n```\n{content}\n```")
        total_tokens = sum(_estimate_tokens(c) for _, c in files)
        return (f"\n\n## CONTEXT: {len(files)} files injected "
                f"(~{total_tokens:,} tokens)\n\n" + "\n\n".join(blocks))

    @staticmethod
    def chunk_files(files: list, budget_tokens: int) -> list:
        """Split files into chunks fitting within token budget."""
        if not files:
            return [[]]
        chunks, current, current_tokens = [], [], 0
        for path, content in files:
            ft = _estimate_tokens(content) + 60
            if current_tokens + ft > budget_tokens and current:
                chunks.append(current)
                current, current_tokens = [], 0
            current.append((path, content))
            current_tokens += ft
        if current:
            chunks.append(current)
        return chunks if chunks else [[]]


# ─── Upstream Output Injection ─────────────────────────────────────────────

def inject_upstream(extraction_dir: Path, inject_spec: dict) -> str:
    """Read upstream phase outputs and format for injection."""
    if not inject_spec:
        return ""
    blocks = []
    for phase_id, filenames in inject_spec.items():
        phase_dir = extraction_dir / phase_id.lower()
        for filename in filenames:
            path = phase_dir / filename
            if not path.exists():
                path = phase_dir / "combined_output.json"
            if path.exists():
                content = path.read_text(encoding="utf-8", errors="replace")
                blocks.append(
                    f"## INPUT DATA FROM {phase_id}: {filename}\n"
                    f"```json\n{content}\n```"
                )
    return ("\n\n" + "\n\n".join(blocks) + "\n") if blocks else ""


# ─── Checkpoint ────────────────────────────────────────────────────────────

class ExtractionCheckpoint:
    _FRESH = {
        "completed_phases": [], "failed_phases": [], "skipped_phases": [],
        "total_tokens": {"input": 0, "output": 0},
        "total_cost": 0.0, "started_at": None, "last_updated": None,
    }

    def __init__(self, checkpoint_file: Path, load_existing: bool = True):
        self.checkpoint_file = checkpoint_file
        self.data = (self._load() if load_existing
                     else json.loads(json.dumps(self._FRESH)))

    def _load(self) -> dict:
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                print(f"  Warning: corrupt checkpoint, starting fresh: {exc}")
        return json.loads(json.dumps(self._FRESH))

    def save(self):
        self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
        self.data["last_updated"] = _utcnow()
        tmp = self.checkpoint_file.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(self.data, f, indent=2)
        tmp.replace(self.checkpoint_file)

    def mark_completed(self, phase_id, tokens, cost):
        if phase_id not in self.data["completed_phases"]:
            self.data["completed_phases"].append(phase_id)
        self.data["total_tokens"]["input"] += tokens.get("input", 0)
        self.data["total_tokens"]["output"] += tokens.get("output", 0)
        self.data["total_cost"] += cost
        self.save()

    def mark_failed(self, phase_id, error):
        self.data["failed_phases"].append(
            {"phase": phase_id, "error": str(error)[:500], "timestamp": _utcnow()})
        self.save()

    def mark_skipped(self, phase_id, reason):
        self.data["skipped_phases"].append(
            {"phase": phase_id, "reason": reason, "timestamp": _utcnow()})
        self.save()

    def is_completed(self, phase_id):
        return phase_id in self.data["completed_phases"]


class APIError(Exception):
    def __init__(self, status_code: int, body: str):
        self.status_code = status_code
        self.body = body[:500]
        super().__init__(f"HTTP {status_code}: {self.body}")


# ─── Extractor ─────────────────────────────────────────────────────────────

class ExtractionRunner:
    """Production-grade multi-model extraction runner with content injection."""

    GROK_URL = "https://api.x.ai/v1/chat/completions"
    GEMINI_URL = ("https://generativelanguage.googleapis.com"
                  "/v1beta/models/{model}:generateContent")

    def __init__(self, base_dir, dry_run=False, checkpoint=None,
                 max_retries=3, base_retry_delay=5, timeout=180, verbose=False):
        self.base_dir = base_dir
        self.dry_run = dry_run
        self.checkpoint = checkpoint
        self.completed_phases = set(
            checkpoint.data["completed_phases"] if checkpoint else [])
        self.failed_phases = set()
        self.verbose = verbose
        self.max_retries = max_retries
        self.base_retry_delay = base_retry_delay
        self.timeout = timeout
        self._api_keys = {
            "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
            "XAI_API_KEY": os.getenv("XAI_API_KEY", ""),
        }
        self.collector = ContentCollector(base_dir)

    # ── Model resolution ────────────────────────────────────────────

    def _resolve_model(self, phase_id):
        api_type, model, key_env = MODEL_ROUTING.get(phase_id, _GROK)
        api_key = self._api_keys.get(key_env, "")
        if not api_key:
            if api_type == "gemini" and self._api_keys["XAI_API_KEY"]:
                print(f"  Warning: {key_env} not set, falling back to Grok")
                return "grok", "grok-code-fast-1", self._api_keys["XAI_API_KEY"]
            elif api_type == "grok" and self._api_keys["GEMINI_API_KEY"]:
                print(f"  Warning: {key_env} not set, falling back to Gemini")
                return "gemini", "gemini-2.0-flash-001", self._api_keys["GEMINI_API_KEY"]
            raise RuntimeError(f"No API key for {phase_id}. Set {key_env}.")
        return api_type, model, api_key

    # ── API calls ───────────────────────────────────────────────────

    def call_api(self, prompt, phase_id):
        """Call API with retry. Returns (content, tokens_dict, api_type)."""
        api_type = MODEL_ROUTING.get(phase_id, _GROK)[0]
        if self.dry_run:
            est_in = _estimate_tokens(prompt)
            print("  [DRY RUN] Would call API")
            return '{"artifact_type":"dry_run"}', {"input": est_in, "output": 4000}, api_type

        api_type, model, api_key = self._resolve_model(phase_id)
        max_out = MODEL_LIMITS[api_type]["output"]
        print(f"  Model: {model} (max_out={max_out:,})")

        dispatch = self._call_gemini if api_type == "gemini" else self._call_grok
        last_err = None

        for attempt in range(1, self.max_retries + 1):
            try:
                print(f"  API call (attempt {attempt}/{self.max_retries})...")
                content, tokens = dispatch(prompt, max_out, model, api_key)
                return content, tokens, api_type
            except requests.exceptions.Timeout:
                last_err = "Timeout"
            except requests.exceptions.ConnectionError as e:
                last_err = f"Connection error: {e}"
            except APIError as e:
                if e.status_code == 429:
                    last_err = "Rate limited"
                elif e.status_code >= 500:
                    last_err = f"Server error {e.status_code}"
                else:
                    raise
            delay = self.base_retry_delay * (2 ** (attempt - 1))
            print(f"  Warning: {last_err}. Waiting {delay}s...")
            time.sleep(delay)

        raise RuntimeError(f"All {self.max_retries} attempts failed: {last_err}")

    def _call_grok(self, prompt, max_tokens, model, api_key):
        resp = requests.post(
            self.GROK_URL,
            headers={"Content-Type": "application/json",
                     "Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a mechanical extractor. "
                     "Follow instructions exactly. Output JSON only."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
                "max_tokens": max_tokens,
            },
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            raise APIError(resp.status_code, resp.text)
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})
        return content, {"input": usage.get("prompt_tokens", 0),
                         "output": usage.get("completion_tokens", 0)}

    def _call_gemini(self, prompt, max_tokens, model, api_key):
        url = self.GEMINI_URL.format(model=model)
        resp = requests.post(
            url,
            params={"key": api_key},
            headers={"Content-Type": "application/json"},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0,
                    "maxOutputTokens": max_tokens,
                    "responseMimeType": "application/json",
                },
            },
            timeout=self.timeout,
        )
        if resp.status_code != 200:
            raise APIError(resp.status_code, resp.text)
        data = resp.json()
        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(f"Gemini returned no candidates: "
                               f"{json.dumps(data)[:500]}")
        content = candidates[0]["content"]["parts"][0]["text"]
        usage = data.get("usageMetadata", {})
        return content, {"input": usage.get("promptTokenCount", 0),
                         "output": usage.get("candidatesTokenCount", 0)}

    # ── JSON handling ───────────────────────────────────────────────

    @staticmethod
    def extract_json(response):
        text = response.strip()
        if text.startswith("```"):
            nl = text.find("\n")
            if nl == -1:
                text = text.lstrip("`").rstrip("`").strip()
            else:
                text = text[nl + 1:]
                if text.rstrip().endswith("```"):
                    text = text.rstrip()[:-3].rstrip()
        return text

    @staticmethod
    def validate_json(content):
        try:
            json.loads(content)
            return True
        except json.JSONDecodeError:
            return False

    def save_output(self, out_dir, filename, content, phase_id):
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / filename
        valid = self.validate_json(content)
        if not valid:
            print(f"  Warning: invalid JSON for {phase_id}, saving raw")
        if valid:
            content = json.dumps(json.loads(content), indent=2, ensure_ascii=True)
        path.write_text(content, encoding="utf-8")
        size_kb = path.stat().st_size / 1024
        print(f"  Saved: {path.relative_to(self.base_dir)} ({size_kb:.1f} KB)")

    def _try_split_outputs(self, out_dir, output_files, content, phase_id):
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            return False
        if not isinstance(data, dict):
            return False
        stems = {Path(f).stem.upper(): f for f in output_files}
        matched = {}
        for key in data:
            norm = key.upper().replace(" ", "_").replace("-", "_")
            if norm in stems:
                matched[stems[norm]] = data[key]
            elif len(data) == len(output_files):
                break
        else:
            if len(matched) == len(output_files):
                for fn, val in matched.items():
                    self.save_output(out_dir, fn,
                                     json.dumps(val, indent=2, ensure_ascii=True),
                                     phase_id)
                return True
        keys = list(data.keys())
        if len(keys) == len(output_files):
            for key, fn in zip(keys, output_files):
                self.save_output(out_dir, fn,
                                 json.dumps(data[key], indent=2, ensure_ascii=True),
                                 phase_id)
            return True
        return False

    # ── Merge chunked results ───────────────────────────────────────

    @staticmethod
    def merge_chunked_results(results: list) -> str:
        """Merge multiple JSON responses from chunked calls."""
        if len(results) == 1:
            return results[0]
        merged_data = None
        for result in results:
            try:
                data = json.loads(result)
            except json.JSONDecodeError:
                continue
            if merged_data is None:
                merged_data = data
                continue
            if isinstance(data, dict) and isinstance(merged_data, dict):
                for key, val in data.items():
                    if key in ("artifact_type", "generated_at_utc", "source_artifact"):
                        continue
                    if isinstance(val, list) and isinstance(merged_data.get(key), list):
                        merged_data[key].extend(val)
                    elif key not in merged_data:
                        merged_data[key] = val
        if merged_data is None:
            return results[0]
        return json.dumps(merged_data, indent=2, ensure_ascii=True)

    # ── Phase execution ─────────────────────────────────────────────

    def run_phase(self, phase_id):
        """Run a single phase with content injection and chunking."""
        config = PHASES[phase_id]

        if self.checkpoint and self.checkpoint.is_completed(phase_id):
            print(f"\n  Skip {phase_id}: already completed")
            self.completed_phases.add(phase_id)
            return True

        print(f"\n{'='*60}")
        print(f"  Phase {phase_id}: {config['prompt']}")
        print(f"{'='*60}")

        try:
            prompt_template = self._read_prompt(config["prompt"])
            api_type = MODEL_ROUTING.get(phase_id, _GROK)[0]
            input_limit = MODEL_LIMITS[api_type]["input"]
            prompt_tokens = _estimate_tokens(prompt_template)

            # Collect file content if scan phase
            files = self.collector.collect(config)
            sqlite_schemas = self.collector.collect_sqlite_schemas(config)
            files.extend(sqlite_schemas)

            # Inject upstream outputs if transform phase
            upstream_text = inject_upstream(
                self.base_dir / "extraction",
                config.get("inject_from", {}))
            upstream_tokens = _estimate_tokens(upstream_text)

            # Token budget: input_limit - prompt - upstream - 10% safety
            safety = int(input_limit * 0.10)
            file_budget = input_limit - prompt_tokens - upstream_tokens - safety

            if files:
                total_file_tokens = sum(_estimate_tokens(c) for _, c in files)
                print(f"  Files: {len(files)} ({total_file_tokens:,} tokens)")
                print(f"  Budget: {file_budget:,} tokens "
                      f"(limit={input_limit:,} - prompt={prompt_tokens:,}"
                      f" - upstream={upstream_tokens:,} - safety={safety:,})")

                if total_file_tokens > file_budget:
                    chunks = self.collector.chunk_files(files, file_budget)
                    print(f"  Chunking: {len(chunks)} chunks needed")
                    return self._run_chunked(phase_id, config, prompt_template,
                                             upstream_text, chunks)
                else:
                    context = self.collector.format_context(files)
                    full_prompt = prompt_template + upstream_text + context
            elif upstream_text:
                full_prompt = prompt_template + upstream_text
                print(f"  Upstream data: ~{upstream_tokens:,} tokens injected")
            else:
                full_prompt = prompt_template

            total = _estimate_tokens(full_prompt)
            print(f"  Total input: ~{total:,} tokens")
            if total > input_limit:
                print(f"  WARNING: exceeds {api_type} limit of {input_limit:,}!")

            content, tokens, api_type = self.call_api(full_prompt, phase_id)
            json_content = self.extract_json(content)
            self._save_phase_output(phase_id, config, json_content, tokens, api_type)
            return True

        except APIError as e:
            print(f"  FAILED {phase_id}: {e}")
            if "API_KEY_INVALID" in str(e) or "API Key not found" in str(e):
                print("    -> HINT: Your API key appears invalid. Check your .env or environment variables.")
            self.failed_phases.add(phase_id)
            if self.checkpoint:
                self.checkpoint.mark_failed(phase_id, str(e))
            return False

        except Exception as exc:
            print(f"  FAILED {phase_id}: {exc}")
            traceback.print_exc()
            self.failed_phases.add(phase_id)
            if self.checkpoint:
                self.checkpoint.mark_failed(phase_id, str(exc))
            return False

    def _run_chunked(self, phase_id, config, prompt_template, upstream_text, chunks):
        """Run a phase across multiple chunks and merge results."""
        results = []
        total_tokens = {"input": 0, "output": 0}
        total_cost = 0.0
        api_type = MODEL_ROUTING.get(phase_id, _GROK)[0]

        for i, chunk in enumerate(chunks):
            print(f"\n  --- Chunk {i+1}/{len(chunks)} "
                  f"({len(chunk)} files) ---")
            context = self.collector.format_context(chunk)
            full_prompt = prompt_template + upstream_text + context

            content, tokens, at = self.call_api(full_prompt, phase_id)
            json_content = self.extract_json(content)
            results.append(json_content)

            total_tokens["input"] += tokens["input"]
            total_tokens["output"] += tokens["output"]
            cost = self._calc_cost(tokens["input"], tokens["output"], at)
            total_cost += cost
            print(f"  Chunk {i+1} tokens: {tokens['input']:,}in "
                  f"/ {tokens['output']:,}out (${cost:.4f})")

            if not self.dry_run and i < len(chunks) - 1:
                time.sleep(2)

        merged = self.merge_chunked_results(results)
        self._save_phase_output(phase_id, config, merged,
                                total_tokens, api_type, total_cost)
        return True

    def _save_phase_output(self, phase_id, config, json_content,
                           tokens, api_type, cost=None):
        out_dir = self.base_dir / "extraction" / phase_id.lower()
        outputs = config["outputs"]

        if len(outputs) == 1:
            self.save_output(out_dir, outputs[0], json_content, phase_id)
        else:
            if not self._try_split_outputs(out_dir, outputs, json_content, phase_id):
                self.save_output(out_dir, "combined_output.json", json_content, phase_id)
                print(f"  NOTE: expected {len(outputs)} files, saved combined")

        if cost is None:
            cost = self._calc_cost(tokens["input"], tokens["output"], api_type)
        print(f"  Tokens: {tokens['input']:,} in / {tokens['output']:,} out")
        print(f"  Cost: ${cost:.4f}")

        if self.checkpoint:
            self.checkpoint.mark_completed(phase_id, tokens, cost)
        self.completed_phases.add(phase_id)
        print(f"  Phase {phase_id} complete")

    def _read_prompt(self, prompt_file):
        path = self.base_dir / "UPGRADE" / prompt_file
        if not path.exists():
            raise FileNotFoundError(f"Prompt not found: {path}")
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _calc_cost(input_tokens, output_tokens, api_type):
        limits = MODEL_LIMITS.get(api_type, MODEL_LIMITS["grok"])
        return ((input_tokens / 1e6) * limits["input_price"] +
                (output_tokens / 1e6) * limits["output_price"])

    # ── Phase group runners ─────────────────────────────────────────

    def _dep_satisfied(self, dep_phase_id):
        """Check if a dependency is satisfied: completed in this run OR outputs exist on disk."""
        if dep_phase_id in self.completed_phases:
            return True
        # Check if output files from that phase already exist (>100B = not a stub)
        if dep_phase_id in PHASES:
            dep_dir = self.base_dir / "extraction" / dep_phase_id.lower()
            outputs = PHASES[dep_phase_id]["outputs"]
            if dep_dir.exists():
                for out_file in outputs:
                    p = dep_dir / out_file
                    if p.exists() and p.stat().st_size > 100:
                        return True
                p = dep_dir / "combined_output.json"
                if p.exists() and p.stat().st_size > 100:
                    return True
        return False

    def _run_group(self, title, order):
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
        for phase_id in order:
            if phase_id not in PHASES:
                continue
            config = PHASES[phase_id]
            missing = [d for d in config["deps"] if not self._dep_satisfied(d)]
            if missing:
                reason = f"missing deps: {missing}"
                print(f"\n  Skip {phase_id}: {reason}")
                if self.checkpoint:
                    self.checkpoint.mark_skipped(phase_id, reason)
                continue
            ok = self.run_phase(phase_id)
            if ok and not self.dry_run:
                time.sleep(2)

    def run_priority(self):
        self._run_group("PRIORITY PHASES (I/W/H)", PRIORITY_ORDER)

    def run_code(self):
        self._run_group("CODE PHASES (A-F) [Grok]", CODE_ORDER)

    def run_docs(self):
        print("\n  NOTE: D1/D2 require manual partition execution")
        self._run_group("DOCS PHASES (D0-CL) [Flash]", DOCS_ORDER)

    def run_all(self):
        print(f"{'='*60}")
        print("  COMPLETE DOPEMUX EXTRACTION")
        print(f"{'='*60}")
        if self.checkpoint:
            if self.checkpoint.data.get("started_at"):
                n = len(self.checkpoint.data["completed_phases"])
                print(f"\n  Resuming ({n} phases done)")
            else:
                self.checkpoint.data["started_at"] = _utcnow()
                self.checkpoint.save()
        start = time.time()
        try:
            self.run_priority()
            self.run_code()
            self.run_docs()
            self._run_deferred()
        except KeyboardInterrupt:
            print("\n\n  Interrupted")
        finally:
            self._summary(start)

    def _run_deferred(self):
        """Retry phases that were skipped due to cross-group dependencies."""
        all_order = PRIORITY_ORDER + CODE_ORDER + DOCS_ORDER
        deferred = [p for p in all_order
                    if p in PHASES
                    and p not in self.completed_phases
                    and p not in self.failed_phases]
        if not deferred:
            return
        runnable = [p for p in deferred
                    if all(self._dep_satisfied(d) for d in PHASES[p]["deps"])]
        if not runnable:
            return
        self._run_group("DEFERRED PHASES (cross-group deps)", runnable)

    def _summary(self, start_time):
        elapsed = time.time() - start_time
        print(f"\n{'='*60}")
        print("  EXTRACTION SUMMARY")
        print(f"{'='*60}")
        print(f"\n  Completed: {len(self.completed_phases)} phases")
        if self.completed_phases:
            print(f"    {sorted(self.completed_phases)}")
        if self.failed_phases:
            print(f"\n  Failed: {len(self.failed_phases)} phases")
            print(f"    {sorted(self.failed_phases)}")
        if self.checkpoint:
            t = self.checkpoint.data["total_tokens"]
            c = self.checkpoint.data["total_cost"]
            print(f"\n  Tokens:  {t['input']:,} in / {t['output']:,} out")
            print(f"  Cost:    ${c:.4f}")
        print(f"\n  Elapsed: {elapsed / 60:.1f} min")
        print(f"  Output:  {self.base_dir / 'extraction'}/")
        if self.failed_phases:
            print("\n  Re-run with --resume to retry failed phases")


# ─── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Dopemux extraction pipeline (Flash + Grok)",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--phases", choices=["priority", "code", "docs", "all"],
                        default="all", help="Phase group (default: all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Simulate without API calls")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from checkpoint (skip completed)")
    parser.add_argument("--verbose", action="store_true",
                        help="Show injected context details")
    parser.add_argument("--base-dir", type=Path,
                        default=Path("/Users/hue/code/dopemux-mvp"))
    parser.add_argument("--checkpoint-file", type=Path, default=None)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--max-retries", type=int, default=3)
    args = parser.parse_args()

    gemini_key = os.getenv("GEMINI_API_KEY", "")
    xai_key = os.getenv("XAI_API_KEY", "")

    if not args.dry_run and not gemini_key and not xai_key:
        print("ERROR: Set at least one API key:")
        print("  export GEMINI_API_KEY=...   (for Flash: H/I/W/Docs)")
        print("  export XAI_API_KEY=...      (for Grok: Code A-F)")
        sys.exit(1)

    if not args.dry_run:
        for name, key, label in [
            ("GEMINI_API_KEY", gemini_key, "Flash"),
            ("XAI_API_KEY", xai_key, "Grok"),
        ]:
            if key:
                print(f"  OK: {name} set ({label} phases ready)")
            else:
                print(f"  Warning: {name} not set ({label} phases will fallback)")

    if not args.base_dir.exists():
        print(f"ERROR: directory not found: {args.base_dir}")
        sys.exit(1)

    cp_file = args.checkpoint_file or (args.base_dir / "extraction" / ".checkpoint.json")
    checkpoint = ExtractionCheckpoint(cp_file)

    if not args.dry_run and checkpoint.data["completed_phases"]:
        n = len(checkpoint.data["completed_phases"])
        if args.resume:
            print(f"\n  Resuming: {n} phases completed, skipping those")
        else:
            print(f"\n  Warning: checkpoint has {n} done phases.")
            print(f"    Use --resume to skip them, or delete {cp_file}")
            print(f"    Running without --resume re-runs everything.\n")
            checkpoint = ExtractionCheckpoint(cp_file, load_existing=False)

    runner = ExtractionRunner(
        base_dir=args.base_dir,
        dry_run=args.dry_run,
        checkpoint=None if args.dry_run else checkpoint,
        max_retries=args.max_retries,
        base_retry_delay=5,
        timeout=args.timeout,
        verbose=args.verbose,
    )

    dispatch = {
        "all": runner.run_all,
        "priority": runner.run_priority,
        "code": runner.run_code,
        "docs": runner.run_docs,
    }

    start = time.time()
    try:
        dispatch[args.phases]()
    except KeyboardInterrupt:
        print("\n\n  Interrupted")
    finally:
        if args.phases != "all":
            runner._summary(start)


if __name__ == "__main__":
    main()
