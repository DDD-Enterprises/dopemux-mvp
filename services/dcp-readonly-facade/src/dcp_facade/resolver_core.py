"""Pure resolver core — target_id -> ResolvedTarget (TP-DCP-MCP-RO-0010).

Resolution order (mirrors ``resolver.py``'s §5 flow, extended per ADR-DCP-
MCP-RO-0009 for registry v2):

  lookup -> enabled -> realpath -> approved-roots containment
  -> eligibility (.dopemux/ present + validate_workspace)
  -> identity (.repo_id project + conditional owner)
  -> derive project_root/worktree_root from LOCAL .git metadata only
  -> bind per-family service policies (already resolved at registry parse)
  -> ResolvedTarget.

Every failure returns a short, opaque block reason — never a path, port,
URL, or partial result (ADR §"Public Response Rules"; TP-DCP-MCP-RO-0010
hard constraint). This module is pure: it makes no outbound network calls,
opens no ports, spawns no external processes, and inspects no container
runtime or backend service. project_root/worktree_root are derived by
reading ``.git`` (directory vs gitfile) and, for a linked worktree, its
``commondir`` file — local filesystem reads only.

Reuses ``dopemux.workspace_detection.validate_workspace`` when importable
(repo ``src`` is on pytest ``pythonpath``); a conservative fallback is used
only when dopemux is unavailable (e.g. a stripped container) — identical
fallback shape to ``resolver.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .registry_v2 import ExposureTarget, RegistryV2, ServicePolicy

try:  # prefer the canonical dopemux validator
    from dopemux.workspace_detection import validate_workspace as _validate_workspace
except Exception:  # pragma: no cover - exercised only without dopemux on path

    def _validate_workspace(workspace_path: Path) -> tuple[bool, Optional[str]]:
        p = Path(workspace_path)
        if not p.is_dir():
            return False, "not a directory"
        if (
            (p / ".git").exists()
            or (p / "pyproject.toml").exists()
            or (p / ".repo_id").exists()
        ):
            return True, None
        return False, "no workspace markers"


@dataclass(frozen=True)
class ResolvedTarget:
    target: ExposureTarget
    workspace: Path  # canonical (realpath) directory — the bound checkout
    project_root: Path  # repository-level root (common .git's parent)
    worktree_root: Path  # worktree-level root (== workspace)
    service_policies: dict[str, ServicePolicy]


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


def _derive_roots(workspace: Path) -> tuple[Optional[Path], Optional[Path]]:
    """Derive (project_root, worktree_root) from LOCAL ``.git`` metadata only.

    - ``.git`` is a directory: primary checkout. project_root == worktree_root
      == workspace.
    - ``.git`` is a file (``gitdir: <path>``): linked worktree. Follow
      ``<gitdir>/commondir`` to the common ``.git`` directory; project_root is
      its parent. worktree_root == workspace.
    - No ``.git`` at all: unresolvable — fail closed (returns (None, None)).

    No network calls and no external process is spawned — pure filesystem reads.
    """
    git_path = workspace / ".git"

    if git_path.is_dir():
        return workspace, workspace

    if not git_path.is_file():
        return None, None

    try:
        content = git_path.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None, None

    prefix = "gitdir:"
    if not content.startswith(prefix):
        return None, None
    gitdir_raw = content[len(prefix) :].strip()
    if not gitdir_raw:
        return None, None

    gitdir = Path(gitdir_raw)
    if not gitdir.is_absolute():
        gitdir = workspace / gitdir
    try:
        gitdir = gitdir.resolve()
    except OSError:
        return None, None

    commondir_file = gitdir / "commondir"
    if not commondir_file.is_file():
        return None, None
    try:
        common_raw = commondir_file.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None, None
    if not common_raw:
        return None, None

    common_dir = Path(common_raw)
    if not common_dir.is_absolute():
        common_dir = gitdir / common_dir
    try:
        common_dir = common_dir.resolve()
    except OSError:
        return None, None

    return common_dir.parent, workspace


def resolve_target(
    registry: RegistryV2, target_id: object
) -> tuple[Optional[ResolvedTarget], Optional[str]]:
    """Return (ResolvedTarget, None) on success or (None, reason) when blocked.

    ``reason`` is always a short, opaque string: no absolute path, port, or
    URL is ever included (target_id itself is caller-supplied and opaque, so
    it is safe to echo back).
    """
    if not isinstance(target_id, str) or not target_id:
        return None, "target_id is required"

    target = registry.get(target_id)
    if target is None:
        return None, f"unknown target: {target_id}"
    if not target.enabled:
        return None, f"target disabled: {target_id}"

    try:
        real = Path(target.workspace_path).resolve()
    except OSError:
        return None, "workspace could not be resolved"
    if not real.is_dir():
        return None, "workspace is not a directory"

    if registry.approved_roots:
        if not any(_within(real, Path(r)) for r in registry.approved_roots):
            return None, "workspace escapes approved roots"

    # Eligibility: the dopemux init marker + canonical workspace validation.
    if not (real / ".dopemux").is_dir():
        return None, "workspace missing .dopemux (not initialized)"
    # Note: validate_workspace's raw error is intentionally discarded — it can
    # embed absolute paths, which must never appear in a caller-facing reason.
    ok, _ = _validate_workspace(real)
    if not ok:
        return None, "workspace validation failed"

    # Identity: .repo_id project (always) + owner (only when registry declares it).
    repo_id = _read_repo_id(real)
    if repo_id.get("project") != target.identity_project:
        return None, "identity project mismatch"
    if target.identity_owner is not None and repo_id.get("owner") != target.identity_owner:
        return None, "identity owner mismatch"

    project_root, worktree_root = _derive_roots(real)
    if project_root is None or worktree_root is None:
        return None, "workspace has no resolvable git root"

    return (
        ResolvedTarget(
            target=target,
            workspace=real,
            project_root=project_root,
            worktree_root=worktree_root,
            service_policies=dict(target.service_policies),
        ),
        None,
    )
