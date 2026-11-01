"""Pure helpers shared by the W01 tests (no service imports)."""

from __future__ import annotations

import hashlib
import json
import secrets
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICE_DIR = REPO_ROOT / "services" / "working-memory-assistant"
HASH_FILE_NAME = "memory-token-hashes.json"


def fake_token(label: str = "codex") -> str:
    """An obviously fake bearer token, generated per call."""
    return f"FAKE-TEST-TOKEN-{label}-{secrets.token_hex(12)}"


def write_hash_file(auth_dir: Path, mapping: dict[str, str]) -> Path:
    """Write ``{sha256(token): principal}`` the way the W03 helper will."""
    auth_dir.mkdir(parents=True, exist_ok=True)
    path = auth_dir / HASH_FILE_NAME
    payload = {
        hashlib.sha256(token.encode("utf-8")).hexdigest(): principal
        for token, principal in mapping.items()
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path
