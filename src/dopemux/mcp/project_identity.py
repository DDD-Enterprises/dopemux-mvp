"""Project identity helpers for MCP state scoping."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


class ProjectIdentityError(RuntimeError):
    """Raised when a repo-scoped project identity cannot be resolved."""


@dataclass(frozen=True)
class ProjectIdentity:
    """Resolved worktree and repo identity used by MCP launchers."""

    worktree_root: Path
    project_root: Path
    git_common_dir: Path | None

    @property
    def project_hash(self) -> str:
        return hashlib.sha256(str(self.project_root).encode("utf-8")).hexdigest()[:16]

    @property
    def project_slug(self) -> str:
        slug = re.sub(r"[^a-z0-9._-]+", "-", self.project_root.name.lower()).strip("-")
        return slug or "workspace"

    @property
    def project_id(self) -> str:
        return f"{self.project_slug}-{self.project_hash}"


def _require_dir(path_value: str, *, env_name: str) -> Path:
    path = Path(path_value).expanduser().resolve()
    if not path.is_dir():
        raise ProjectIdentityError(f"{env_name} does not point to a directory: {path}")
    return path


def _git_output(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode != 0:
        raise ProjectIdentityError(result.stderr.strip() or "git identity lookup failed")
    return result.stdout.strip()


def _resolve_common_dir(worktree_root: Path) -> Path:
    common_dir_text = _git_output(["rev-parse", "--git-common-dir"], worktree_root)
    common_dir = Path(common_dir_text)
    if not common_dir.is_absolute():
        common_dir = worktree_root / common_dir
    return common_dir.resolve()


def _project_root_from_common_dir(common_dir: Path) -> Path:
    if common_dir.name == ".git":
        return common_dir.parent.resolve()
    return common_dir.resolve()


def resolve_project_identity(
    cwd: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> ProjectIdentity:
    """Resolve a stable local-git-repo identity and current worktree root.

    ``TASK_ORCHESTRATOR_PROJECT_ROOT`` and ``DOPEMUX_PROJECT_ROOT`` are explicit
    overrides for repo-scoped state and may point at non-git directories. Without
    those overrides this fails closed outside git instead of inventing identity.
    """

    env_map = os.environ if env is None else env
    base_cwd = Path(cwd or env_map.get("DOPEMUX_WORKSPACE_ROOT") or Path.cwd()).resolve()

    workspace_override = env_map.get("DOPEMUX_WORKSPACE_ROOT")
    if workspace_override:
        worktree_root = _require_dir(workspace_override, env_name="DOPEMUX_WORKSPACE_ROOT")
    else:
        try:
            worktree_root = Path(_git_output(["rev-parse", "--show-toplevel"], base_cwd)).resolve()
        except ProjectIdentityError:
            worktree_root = base_cwd

    for env_name in ("TASK_ORCHESTRATOR_PROJECT_ROOT", "DOPEMUX_PROJECT_ROOT"):
        override = env_map.get(env_name)
        if override:
            project_root = _require_dir(override, env_name=env_name)
            return ProjectIdentity(
                worktree_root=worktree_root,
                project_root=project_root,
                git_common_dir=None,
            )

    common_dir = _resolve_common_dir(worktree_root)
    project_root = _project_root_from_common_dir(common_dir)
    return ProjectIdentity(
        worktree_root=worktree_root,
        project_root=project_root,
        git_common_dir=common_dir,
    )
