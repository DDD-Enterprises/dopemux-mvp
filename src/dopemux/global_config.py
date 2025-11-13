"""Global Dopemux configuration helpers.

This module centralizes read/write access to the dopemux config that lives in
``~/.dopemux``. The new config keeps track of every workspace the user has
opened as well as the preferred default workspace so that CLI commands, MCP
proxies, and installers can share the same source of truth. Each workspace is
assigned a stable slug (name + hash) so multiple clones can coexist without
clobbering each other's generated artifacts.

Nothing in here is dopemux-command specific which lets shell scripts and other
tools import it without pulling in the heavier CLI stack.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Dict, Optional

CONFIG_DIR = Path.home() / ".dopemux"
GLOBAL_CONFIG_PATH = CONFIG_DIR / "config.json"
WORKSPACES_DIR = CONFIG_DIR / "workspaces"

CONFIG_VERSION = 1


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_config() -> Dict:
    return {
        "version": CONFIG_VERSION,
        "default_workspace": None,
        "workspaces": {},
    }


def load_config() -> Dict:
    """Load the global dopemux config (creating a default structure if needed)."""

    if not GLOBAL_CONFIG_PATH.exists():
        return _default_config()

    try:
        with GLOBAL_CONFIG_PATH.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
            if not isinstance(data, dict):
                raise ValueError("Invalid config contents")
            data.setdefault("version", CONFIG_VERSION)
            data.setdefault("workspaces", {})
            data.setdefault("default_workspace", None)
            return data
    except (json.JSONDecodeError, OSError, ValueError):
        return _default_config()


def save_config(config: Dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with GLOBAL_CONFIG_PATH.open("w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2, sort_keys=True)


def _workspace_hash(workspace_path: Path) -> str:
    return hashlib.sha256(str(workspace_path).encode("utf-8")).hexdigest()[:12]


def _workspace_slug(workspace_path: Path) -> str:
    name = workspace_path.name or "workspace"
    return f"{name}-{_workspace_hash(workspace_path)}"


def _find_workspace_key(config: Dict, workspace_path: Path) -> Optional[str]:
    target = str(workspace_path)
    for key, entry in config.get("workspaces", {}).items():
        if entry.get("path") == target:
            return key
    return None


@dataclass
class WorkspaceEntry:
    slug: str
    path: Path
    created_at: str
    last_used: str
    workspace_hash: str


def register_workspace(workspace_path: Path) -> WorkspaceEntry:
    """Ensure the workspace is tracked in the global config and return metadata."""

    workspace_path = workspace_path.expanduser().resolve()
    config = load_config()
    key = _find_workspace_key(config, workspace_path)
    now = _utc_now()

    if key is None:
        slug = _workspace_slug(workspace_path)
        while slug in config["workspaces"]:
            slug = f"{slug}-dup"
        entry = {
            "path": str(workspace_path),
            "created_at": now,
            "last_used": now,
            "workspace_hash": _workspace_hash(workspace_path),
        }
        config["workspaces"][slug] = entry
        key = slug
    else:
        entry = config["workspaces"][key]
        entry["last_used"] = now

    save_config(config)
    return WorkspaceEntry(
        slug=key,
        path=workspace_path,
        created_at=entry["created_at"],
        last_used=entry["last_used"],
        workspace_hash=entry["workspace_hash"],
    )


def set_default_workspace(workspace_path: Path) -> None:
    workspace_path = workspace_path.expanduser().resolve()
    config = load_config()
    config["default_workspace"] = str(workspace_path)
    register_workspace(workspace_path)
    save_config(config)


def get_default_workspace() -> Optional[Path]:
    config = load_config()
    value = config.get("default_workspace")
    if value:
        candidate = Path(value)
        if candidate.exists():
            return candidate
    return None


def get_workspace_entry(workspace_path: Path) -> Optional[WorkspaceEntry]:
    config = load_config()
    key = _find_workspace_key(config, workspace_path.expanduser().resolve())
    if key is None:
        return None
    entry = config["workspaces"][key]
    return WorkspaceEntry(
        slug=key,
        path=Path(entry["path"]),
        created_at=entry["created_at"],
        last_used=entry["last_used"],
        workspace_hash=entry["workspace_hash"],
    )


__all__ = [
    "CONFIG_DIR",
    "GLOBAL_CONFIG_PATH",
    "WORKSPACES_DIR",
    "load_config",
    "save_config",
    "register_workspace",
    "set_default_workspace",
    "get_default_workspace",
    "get_workspace_entry",
    "WorkspaceEntry",
]
