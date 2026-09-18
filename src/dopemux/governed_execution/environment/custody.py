"""Writer custody receipt authoring.

author_custody_receipt renders a WriterCustodyReceipt dict (validating
against schemas/governed_execution/writer_custody_receipt.v1.schema.json)
from an EnvironmentPlan, a writer identity, a writer lease and
caller-supplied observed facts. Pure and deterministic: no filesystem,
process or clock access. The caller supplies both the observed facts and
the current instant (now); this module never reads a clock itself.

custody_state is exactly one of HELD, RELEASED or AMBIGUOUS. Any fact that
cannot be proven true yields AMBIGUOUS, never HELD. authority is always
the literal string "NONE": this receipt records custody, not permission.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .plan import EnvironmentPlan


class CustodyRefused(Exception):
    """Raised instead of authoring a receipt when custody cannot be claimed.

    reason is a short, human-readable explanation. Refusal happens
    whenever facts.outside_root_writes is True (a proven out-of-scope
    write) or None (unprovable): a receipt is never authored describing a
    writer that may have written outside its filesystem scope.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass(frozen=True)
class WriterIdentity:
    runner: str
    session_ref: str
    agent_role: str


@dataclass(frozen=True)
class WriterLease:
    lease_id: str
    issued_at: str
    expires_at: str


@dataclass(frozen=True)
class ObservedFacts:
    """Caller-observed facts about the writer's environment at receipt time.

    Every field except head_sha may be unprovable (None); an unprovable
    fact narrows custody_state toward AMBIGUOUS rather than being assumed
    true or false.
    """

    head_sha: str
    patch_bytes: bytes | None
    outside_root_writes: bool | None
    worktree_exists: bool | None
    branch_matches: bool | None


def _parse_rfc3339(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _lease_expired(lease: WriterLease, now: str) -> bool:
    return _parse_rfc3339(lease.expires_at) <= _parse_rfc3339(now)


def _allowlist_digest(allowed_paths: tuple[str, ...]) -> str:
    joined = "\n".join(sorted(allowed_paths))
    return hashlib.sha256(joined.encode("ascii")).hexdigest()


def _patch_sha256(patch_bytes: bytes | None) -> str:
    return hashlib.sha256(patch_bytes or b"").hexdigest()


def _custody_state(facts: ObservedFacts, lease: WriterLease, now: str) -> str:
    if _lease_expired(lease, now):
        return "RELEASED"
    if facts.worktree_exists is True and facts.branch_matches is True:
        return "HELD"
    return "AMBIGUOUS"


def author_custody_receipt(
    plan: EnvironmentPlan,
    writer: WriterIdentity,
    lease: WriterLease,
    facts: ObservedFacts,
    now: str,
) -> dict[str, Any]:
    """Author a WriterCustodyReceipt dict from plan, writer, lease and facts.

    now is an RFC 3339 UTC timestamp supplied by the caller, used only to
    decide whether lease has expired. Raises CustodyRefused when
    facts.outside_root_writes is True or None.
    """
    if facts.outside_root_writes is not False:
        raise CustodyRefused(
            reason=(
                "facts.outside_root_writes is "
                f"{facts.outside_root_writes!r}; refusing to author a receipt"
            )
        )

    custody_state = _custody_state(facts, lease, now)

    return {
        "schema_version": "dopemux.governed_execution.writer_custody_receipt.v1",
        "packet_id": plan.packet_id,
        "repo_identity": {
            "origin_url": plan.repo_identity.origin_url,
            "toplevel": plan.repo_identity.toplevel,
        },
        "worktree_path": plan.worktree_path,
        "branch": plan.branch,
        "base_sha": plan.base_sha,
        "allowed_paths": list(plan.allowed_paths),
        "allowlist_digest": _allowlist_digest(plan.allowed_paths),
        "writer_identity": {
            "runner": writer.runner,
            "session_ref": writer.session_ref,
            "agent_role": writer.agent_role,
        },
        "writer_lease": {
            "issued_at": lease.issued_at,
            "expires_at": lease.expires_at,
            "lease_id": lease.lease_id,
        },
        "diff_provenance": {
            "base_sha": plan.base_sha,
            "head_sha": facts.head_sha,
            "patch_sha256": _patch_sha256(facts.patch_bytes),
        },
        "rollback_locality": {
            "strategy": plan.rollback_locality.strategy,
            "boundary": plan.rollback_locality.boundary,
        },
        "filesystem_scope": {
            "root": plan.filesystem_root,
            "outside_root_writes": False,
        },
        "custody_state": custody_state,
        "authority": "NONE",
    }
