"""Workspace resolver — the fail-closed §5 flow.

Maps a caller-supplied ``project_id`` to a canonical, validated workspace path.
Every failure mode returns a block reason (never a path or partial result).

Resolution order (MULTI_PROJECT_REGISTRY_CONTRACT.md §5):
  lookup → enabled → realpath → containment in approved roots
  → eligibility (.dopemux/ present + validate_workspace)
  → identity (.repo_id project, and owner iff registry declares it)
  → bind.

Reuses ``dopemux.workspace_detection.validate_workspace`` when importable
(repo ``src`` is on pytest ``pythonpath``); a conservative fallback is used
only when dopemux is unavailable (e.g. a stripped container).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .registry import Project, Registry

try:  # prefer the canonical dopemux validator
    from dopemux.workspace_detection import validate_workspace as _validate_workspace
except Exception:  # pragma: no cover - exercised only without dopemux on path
    def _validate_workspace(workspace_path: Path) -> tuple[bool, Optional[str]]:
        p = Path(workspace_path)
        if not p.is_dir():
            return False, "not a directory"
        if (p / ".git").exists() or (p / "pyproject.toml").exists() or (p / ".repo_id").exists():
            return True, None
        return False, "no workspace markers"


@dataclass(frozen=True)
class Resolved:
    project: Project
    workspace: Path  # canonical (realpath) directory


def _read_repo_id(workspace: Path) -> dict[str, str]:
    """Parse the git-tracked ``.repo_id`` identity file (``key=value`` lines)."""
    f = workspace / ".repo_id"
    out: dict[str, str] = {}
    if not f.is_file():
        return out
    for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, val = line.split("=", 1)
        out[key.strip()] = val.strip()
    return out


def _within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def resolve(registry: Registry, project_id: object) -> tuple[Optional[Resolved], Optional[str]]:
    """Return (Resolved, None) on success or (None, reason) when blocked."""
    if not isinstance(project_id, str) or not project_id:
        return None, "project_id is required"

    project = registry.get(project_id)
    if project is None:
        return None, f"unknown project: {project_id}"
    if not project.enabled:
        return None, f"project disabled: {project_id}"

    try:
        real = Path(project.workspace_path).resolve()
    except Exception:
        return None, "workspace_path could not be resolved"
    if not real.is_dir():
        return None, "workspace path is not a directory"

    if registry.approved_roots:
        if not any(_within(real, Path(r)) for r in registry.approved_roots):
            return None, "workspace escapes approved roots"

    # Eligibility: the dopemux init marker + canonical workspace validation.
    if not (real / ".dopemux").is_dir():
        return None, "workspace missing .dopemux (not initialized)"
    ok, err = _validate_workspace(real)
    if not ok:
        return None, f"workspace validation failed: {err}"

    # Identity: .repo_id project (always) + owner (only when registry declares it).
    repo_id = _read_repo_id(real)
    if repo_id.get("project") != project.identity_project:
        return None, "repo_id project does not match registry identity"
    if project.identity_owner is not None and repo_id.get("owner") != project.identity_owner:
        return None, "repo_id owner does not match registry identity"

    return Resolved(project=project, workspace=real), None
