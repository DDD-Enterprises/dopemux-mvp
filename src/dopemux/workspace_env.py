"""Helpers for generating per-workspace artifacts under ~/.dopemux."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, Optional

from .global_config import (
    WORKSPACES_DIR,
    WorkspaceEntry,
    get_default_workspace,
    get_workspace_entry,
    register_workspace,
    set_default_workspace,
)


@dataclass
class WorkspaceArtifacts:
    entry: WorkspaceEntry
    env_path: Path
    metadata_path: Path


def _write_env_file(workspace_dir: Path, workspace_path: Path, entry: WorkspaceEntry) -> Path:
    env_path = workspace_dir / "env"
    lines = [
        f"DOPEMUX_WORKSPACE_ROOT={workspace_path}",
        f"DOPEMUX_WORKSPACE_ID={workspace_path}",
        f"DOPEMUX_WORKSPACE_SLUG={entry.slug}",
        f"DOPEMUX_WORKSPACE_HASH={entry.workspace_hash}",
        f"DOPEMUX_INSTANCE_ID=${{DOPEMUX_INSTANCE_ID:-{entry.slug}}}",
        f"DOPEMUX_STACK_PREFIX=${{DOPEMUX_STACK_PREFIX:-{entry.slug}}}",
    ]
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return env_path


def _write_metadata_file(workspace_dir: Path, entry: WorkspaceEntry, is_default: bool) -> Path:
    meta_path = workspace_dir / "metadata.json"
    metadata: Dict[str, Optional[str | bool]] = {
        "slug": entry.slug,
        "path": str(entry.path),
        "workspace_hash": entry.workspace_hash,
        "created_at": entry.created_at,
        "last_used": entry.last_used,
        "is_default": is_default,
    }
    meta_path.write_text(json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8")
    return meta_path


def ensure_workspace_artifacts(workspace_path: Path, *, set_default: bool = False) -> WorkspaceArtifacts:
    """Ensure env + metadata files exist for the workspace and return their paths."""

    workspace_path = workspace_path.expanduser().resolve()
    entry = register_workspace(workspace_path)
    if set_default:
        set_default_workspace(workspace_path)
        entry = get_workspace_entry(workspace_path) or entry

    workspace_dir = WORKSPACES_DIR / entry.slug
    workspace_dir.mkdir(parents=True, exist_ok=True)

    env_path = _write_env_file(workspace_dir, workspace_path, entry)
    default_ws = get_default_workspace()
    metadata_path = _write_metadata_file(workspace_dir, entry, default_ws == workspace_path)

    return WorkspaceArtifacts(entry=entry, env_path=env_path, metadata_path=metadata_path)

