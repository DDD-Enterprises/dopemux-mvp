"""Workspace containment guard (MCP fleet W2-F08).

Every caller-supplied ``workspace_path`` must resolve (realpath) to an existing
directory inside an allowed root before any filesystem, embedding or network
work happens. Allowed roots, in order:

* ``/workspaces`` - the container mount target of ``HOST_CODE_PARENT_DIR``
  (compose.yml: ``${HOST_CODE_PARENT_DIR}:/workspaces:ro``);
* ``HOST_CODE_PARENT_DIR`` itself, when it exists in this process (host run);
* operator-set ``DOPE_CONTEXT_ALLOWED_ROOTS`` (``os.pathsep`` separated).

Only roots that exist as directories count. No usable root means fail closed.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Optional

CONTAINER_MOUNT_TARGET = "/workspaces"


class WorkspaceRejected(ValueError):
    """Raised when a workspace path or file pattern is not acceptable."""


def allowed_roots() -> List[Path]:
    raw: List[str] = [CONTAINER_MOUNT_TARGET]
    host_parent = os.getenv("HOST_CODE_PARENT_DIR")
    if host_parent:
        raw.append(host_parent)
    extra = os.getenv("DOPE_CONTEXT_ALLOWED_ROOTS")
    if extra:
        raw.extend(p for p in extra.split(os.pathsep) if p)

    roots: List[Path] = []
    for item in raw:
        try:
            resolved = Path(item).expanduser().resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if resolved.is_dir() and resolved not in roots:
            roots.append(resolved)
    return roots


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def validate_workspace_path(raw: object) -> Path:
    """Return the strictly resolved workspace, or raise WorkspaceRejected."""
    if raw is None or not isinstance(raw, (str, os.PathLike)) or not str(raw).strip():
        raise WorkspaceRejected("workspace_path must be a non-empty path")
    roots = allowed_roots()
    if not roots:
        raise WorkspaceRejected(
            "no allowed workspace root is available (mount HOST_CODE_PARENT_DIR "
            "at /workspaces or set DOPE_CONTEXT_ALLOWED_ROOTS); refusing to index"
        )
    try:
        resolved = Path(raw).expanduser().resolve(strict=True)
    except (OSError, RuntimeError):
        raise WorkspaceRejected(
            f"workspace_path does not exist or cannot be resolved: {raw}"
        ) from None
    if not resolved.is_dir():
        raise WorkspaceRejected(f"workspace_path is not a directory: {raw}")
    if not any(_is_within(resolved, root) for root in roots):
        raise WorkspaceRejected(
            f"workspace_path is outside the allowed workspace roots: {raw}"
        )
    return resolved


def resolve_workspace(raw: Optional[object], default_factory) -> Path:
    """Validate an explicit path; an absent one uses the server's own default."""
    if raw:
        return validate_workspace_path(raw)
    return default_factory()


def validate_patterns(patterns: Optional[Iterable[str]]) -> None:
    """Reject absolute patterns and any pattern with a ``..`` segment."""
    for pattern in patterns or []:
        text = str(pattern)
        normalized = text.replace("\\", "/")
        segments = normalized.split("/")
        if (
            normalized.startswith("/")
            or Path(text).is_absolute()
            or (len(text) > 1 and text[1] == ":")
            or normalized.startswith("~")
            or ".." in segments
        ):
            raise WorkspaceRejected(
                f"file pattern must be relative and contain no '..': {pattern!r}"
            )


def contained_in_workspace(path: Path, workspace: Path) -> bool:
    """True if ``path`` (symlinks followed) stays inside ``workspace``."""
    try:
        return _is_within(path.resolve(), workspace.resolve())
    except (OSError, RuntimeError):
        return False
