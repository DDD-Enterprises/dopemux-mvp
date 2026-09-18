"""Pure environment planner.

plan_environment(spec) -> EnvironmentPlan derives a deterministic execution
environment description from a caller-supplied EnvironmentSpec. It performs
no filesystem access, no process invocation and reads no clock: every
output field is a pure function of the input spec.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

_SLUG_INVALID = re.compile(r"[^a-z0-9]+")


class PlanRejected(Exception):
    """Raised when an EnvironmentSpec cannot be planned as given.

    reason is a short, human-readable explanation of which input was
    rejected and why.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class RepoIdentity:
    origin_url: str
    toplevel: str


@dataclass(frozen=True)
class RollbackLocality:
    strategy: str
    boundary: str


@dataclass(frozen=True)
class EnvironmentSpec:
    """Caller-supplied inputs to plan_environment.

    allowed_paths are relative, repo-rooted path strings (no leading '/'
    and no '..' segment); each is validated by plan_environment before the
    plan is produced.
    """

    repo_origin_url: str
    repo_toplevel: str
    packet_id: str
    base_sha: str
    branch: str
    worktree_root: str
    allowed_paths: tuple[str, ...]


@dataclass(frozen=True)
class EnvironmentPlan:
    """Deterministic output of plan_environment.

    worktree_path is worktree_root joined with a packet-derived slug;
    filesystem_root always equals worktree_path. allowed_paths is sorted
    and deduplicated. No field describes readiness, dispatch eligibility
    or any other authority predicate.
    """

    repo_identity: RepoIdentity
    packet_id: str
    base_sha: str
    branch: str
    worktree_root: str
    worktree_path: str
    filesystem_root: str
    allowed_paths: tuple[str, ...]
    rollback_locality: RollbackLocality


def _slugify(packet_id: str) -> str:
    lowered = packet_id.strip().lower()
    slug = _SLUG_INVALID.sub("-", lowered).strip("-")
    if not slug:
        raise PlanRejected(reason=f"packet_id yields an empty slug: {packet_id!r}")
    return slug


def _validate_allowed_path(path: str) -> str:
    if not isinstance(path, str) or not path.strip():
        raise PlanRejected(reason=f"allowed path is empty or not a string: {path!r}")
    if path.startswith("/"):
        raise PlanRejected(reason=f"allowed path is absolute: {path!r}")
    parts = PurePosixPath(path).parts
    if ".." in parts:
        raise PlanRejected(reason=f"allowed path escapes its root via '..': {path!r}")
    return path


def plan_environment(spec: EnvironmentSpec) -> EnvironmentPlan:
    """Derive an EnvironmentPlan from spec. Pure: no side effects.

    Raises PlanRejected when spec.allowed_paths is empty, contains an
    absolute path, contains a '..' segment, or when spec.packet_id cannot
    be turned into a non-empty slug.
    """
    if not spec.allowed_paths:
        raise PlanRejected(reason="allowed_paths is empty")

    validated = sorted({_validate_allowed_path(p) for p in spec.allowed_paths})
    slug = _slugify(spec.packet_id)
    worktree_path = f"{spec.worktree_root.rstrip('/')}/{slug}"

    return EnvironmentPlan(
        repo_identity=RepoIdentity(
            origin_url=spec.repo_origin_url,
            toplevel=spec.repo_toplevel,
        ),
        packet_id=spec.packet_id,
        base_sha=spec.base_sha,
        branch=spec.branch,
        worktree_root=spec.worktree_root,
        worktree_path=worktree_path,
        filesystem_root=worktree_path,
        allowed_paths=tuple(validated),
        rollback_locality=RollbackLocality(
            strategy="RESET_TO_BASE",
            boundary=f"branch:{spec.branch}",
        ),
    )
