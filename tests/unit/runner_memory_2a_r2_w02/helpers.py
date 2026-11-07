"""Pure helpers for the Wave 2A R2 W02 (ConPort identity) tests."""

from __future__ import annotations

import hashlib
import json
import secrets
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CONPORT_DIR = REPO_ROOT / "docker" / "mcp-servers-source" / "conport"
MIGRATIONS_DIR = CONPORT_DIR / "migrations"
WMA_DIR = REPO_ROOT / "services" / "working-memory-assistant"
HASH_FILE_NAME = "memory-token-hashes.json"

BOUND_WORKSPACE = "/test/bound-workspace"
OTHER_WORKSPACE = "/test/some-other-workspace"
INSTANCE = "inst-a"

SSE_TOOL_NAMES = frozenset(
    {
        "get_progress",
        "update_progress",
        "get_decisions",
        "log_decision",
        "get_recent_activity",
        "get_active_work",
        "workspace_summary",
        "fork_instance",
        "promote",
        "promote_all",
        "get_context",
        "update_context",
        "log_progress",
        "get_custom_data",
        "save_custom_data",
        "delete_custom_data",
        "search_content",
    }
)


def fake_token(label: str = "codex") -> str:
    """An obviously fake bearer token, generated per call."""
    return f"FAKE-TEST-TOKEN-{label}-{secrets.token_hex(12)}"


def sha256_hex(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def write_hash_file(auth_dir: Path, mapping: dict[str, str]) -> Path:
    """Write ``{sha256(token): principal}`` the way the W03 helper will."""
    auth_dir.mkdir(parents=True, exist_ok=True)
    path = auth_dir / HASH_FILE_NAME
    payload = {sha256_hex(token): principal for token, principal in mapping.items()}
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path
