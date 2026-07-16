"""Live ownership verification for release-one adapters (TP-DCP-MCP-RO-0015).

Port presence alone is never ownership authority. This module corroborates
identity, labels/mounts, protocol evidence, and candidate uniqueness. It performs
no network, Docker, or backend I/O — callers supply evidence (including optional
live probe results) and receive a fail-closed verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

RELEASE_ONE_FAMILIES = frozenset({"conport", "dope_memory"})

# Required Docker/runtime labels for a verified candidate.
REQUIRED_LABEL_KEYS = (
    "dopemux.project_id",
    "dopemux.service",
    "dopemux.worktree_root",
)


@dataclass(frozen=True)
class OwnershipEvidence:
    """Corroborating evidence for one service-family candidate.

    ``has_listening_port`` is an operational hint only and cannot alone verify.
    ``protocol_ok`` must be an explicit True from a completed probe; None means
    not probed and fails closed.
    """

    family: str
    expected_project_id: str
    expected_project_root: str
    expected_worktree_root: str
    runtime_project_id: Optional[str] = None
    runtime_project_root: Optional[str] = None
    runtime_worktree_root: Optional[str] = None
    labels: Mapping[str, str] = field(default_factory=dict)
    mounts: Sequence[str] = field(default_factory=tuple)
    protocol_ok: Optional[bool] = None
    protocol_name: Optional[str] = None
    has_listening_port: bool = False
    candidate_count: int = 0
    stale: bool = False
    unlabeled: bool = False


@dataclass(frozen=True)
class OwnershipVerdict:
    family: str
    state: str  # VERIFIED | BLOCKED
    reason: str
    evidence_codes: tuple[str, ...] = ()

    @property
    def verified(self) -> bool:
        return self.state == "VERIFIED"

    @property
    def callable(self) -> bool:
        """Ownership verification never by itself makes a backend callable.

        Release-one adapters may proceed only when verified **and** the
        operation is on the release-one allowlist (see safe_adapters).
        """
        return False

    def to_public_dict(self) -> dict[str, Any]:
        return {
            "family": self.family,
            "state": self.state,
            "reason": self.reason,
            "callable": False,
            "evidence_codes": list(self.evidence_codes),
        }


def _canon(path: Optional[str]) -> Optional[str]:
    if not path or not isinstance(path, str):
        return None
    try:
        return str(Path(path).expanduser().resolve(strict=False))
    except (OSError, RuntimeError, ValueError):
        return None


def verify_ownership(evidence: OwnershipEvidence) -> OwnershipVerdict:
    """Fail-closed ownership adjudication from supplied evidence only."""
    family = (evidence.family or "").strip()
    if family not in RELEASE_ONE_FAMILIES:
        return OwnershipVerdict(
            family=family or "unknown",
            state="BLOCKED",
            reason="service family not in release-one set",
            evidence_codes=("family_blocked",),
        )

    if evidence.candidate_count <= 0:
        return OwnershipVerdict(
            family=family,
            state="BLOCKED",
            reason="no matching runtime candidate",
            evidence_codes=("no_candidate",),
        )

    if evidence.candidate_count > 1:
        return OwnershipVerdict(
            family=family,
            state="BLOCKED",
            reason="ambiguous runtime candidates",
            evidence_codes=("ambiguous",),
        )

    if evidence.stale:
        return OwnershipVerdict(
            family=family,
            state="BLOCKED",
            reason="stale runtime evidence",
            evidence_codes=("stale",),
        )

    # Port-only trust is explicitly forbidden even if a socket is listening.
    has_identity = bool(evidence.runtime_project_id and evidence.runtime_project_root)
    has_labels = bool(evidence.labels) and not evidence.unlabeled
    if evidence.has_listening_port and not has_identity and not has_labels:
        return OwnershipVerdict(
            family=family,
            state="BLOCKED",
            reason="port presence is not ownership authority",
            evidence_codes=("port_only",),
        )

    if evidence.unlabeled or not evidence.labels:
        return OwnershipVerdict(
            family=family,
            state="BLOCKED",
            reason="candidate unlabeled",
            evidence_codes=("unlabeled",),
        )

    missing_labels = [key for key in REQUIRED_LABEL_KEYS if key not in evidence.labels]
    if missing_labels:
        return OwnershipVerdict(
            family=family,
            state="BLOCKED",
            reason="required ownership labels missing",
            evidence_codes=("missing_labels",),
        )

    if evidence.runtime_project_id != evidence.expected_project_id:
        return OwnershipVerdict(
            family=family,
            state="BLOCKED",
            reason="wrong project identity",
            evidence_codes=("wrong_project",),
        )

    if evidence.labels.get("dopemux.project_id") != evidence.expected_project_id:
        return OwnershipVerdict(
            family=family,
            state="BLOCKED",
            reason="label project identity mismatch",
            evidence_codes=("label_project_mismatch",),
        )

    expected_service = "conport" if family == "conport" else "dope-memory"
    if evidence.labels.get("dopemux.service") not in {family, expected_service}:
        return OwnershipVerdict(
            family=family,
            state="BLOCKED",
            reason="label service mismatch",
            evidence_codes=("label_service_mismatch",),
        )

    exp_proj = _canon(evidence.expected_project_root)
    exp_wt = _canon(evidence.expected_worktree_root)
    got_proj = _canon(evidence.runtime_project_root)
    got_wt = _canon(evidence.runtime_worktree_root)
    label_wt = _canon(evidence.labels.get("dopemux.worktree_root"))

    if not exp_proj or not exp_wt or got_proj != exp_proj or got_wt != exp_wt:
        return OwnershipVerdict(
            family=family,
            state="BLOCKED",
            reason="project/worktree root mismatch",
            evidence_codes=("root_mismatch",),
        )

    if label_wt != exp_wt:
        return OwnershipVerdict(
            family=family,
            state="BLOCKED",
            reason="label worktree root mismatch",
            evidence_codes=("label_root_mismatch",),
        )

    if evidence.mounts:
        mount_canons = {_canon(m) for m in evidence.mounts}
        if exp_wt not in mount_canons and exp_proj not in mount_canons:
            return OwnershipVerdict(
                family=family,
                state="BLOCKED",
                reason="required mount missing",
                evidence_codes=("mount_missing",),
            )

    if evidence.protocol_ok is not True:
        return OwnershipVerdict(
            family=family,
            state="BLOCKED",
            reason="live protocol verification required or failed",
            evidence_codes=("protocol_required",),
        )

    codes = ["identity", "labels", "protocol"]
    if evidence.mounts:
        codes.append("mounts")
    if evidence.has_listening_port:
        codes.append("port_hint_only")
    return OwnershipVerdict(
        family=family,
        state="VERIFIED",
        reason="ownership corroborated",
        evidence_codes=tuple(codes),
    )
