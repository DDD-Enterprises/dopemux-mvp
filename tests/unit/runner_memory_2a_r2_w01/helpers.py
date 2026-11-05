"""Pure helpers shared by the W01 tests (no service imports)."""

from __future__ import annotations

import functools
import hashlib
import importlib.util
import json
import secrets
import sys
from pathlib import Path
from types import ModuleType

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICE_DIR = REPO_ROOT / "services" / "working-memory-assistant"
HASH_FILE_NAME = "memory-token-hashes.json"
AUTH_IDENTITY_IMPORTERS = ("dope_memory_main", "mcp_http")


@functools.lru_cache(maxsize=1)
def load_dope_memory_auth_identity() -> ModuleType:
    """Load dope-memory's ``auth_identity`` by path, once.

    ConPort ships a top-level ``auth_identity`` too, and older tests leave ConPort's
    directory ahead of this one on ``sys.path``, so a bare import can find the wrong
    file.
    """
    spec = importlib.util.spec_from_file_location(
        "auth_identity", SERVICE_DIR / "auth_identity.py"
    )
    module = importlib.util.module_from_spec(spec)
    saved = sys.modules.get("auth_identity")
    # dataclasses look their module up while it executes
    sys.modules["auth_identity"] = module
    try:
        spec.loader.exec_module(module)
    finally:
        if saved is not None:
            sys.modules["auth_identity"] = saved
        else:
            del sys.modules["auth_identity"]
    return module


def pin_dope_memory_modules(monkeypatch) -> None:
    """For one test, resolve ``auth_identity`` and its importers to dope-memory."""
    monkeypatch.setitem(sys.modules, "auth_identity", load_dope_memory_auth_identity())
    for name in AUTH_IDENTITY_IMPORTERS:
        monkeypatch.delitem(sys.modules, name, raising=False)


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
