"""Deterministic, read-only governed-delivery snapshot.

Answers the six workflow questions from referenced evidence:

    WHERE_IS_THIS_WORK        -> phase
    WHAT_GATES_ARE_SATISFIED  -> gate ledger
    WHAT_BLOCKS_IT            -> blockers, preserved individually
    WHAT_EVIDENCE_IS_CURRENT  -> per-reference freshness
    WHO_ACTS_NEXT             -> next_legal_action.actor_class
    WHAT_ACTION_IS_LEGAL      -> next_legal_action, never dispatchable in G0

This module contacts nothing. It reads local git identity through a fixed-argv,
non-shell subprocess and otherwise consumes only what the caller supplies. It
writes no workflow state, no proof and no cache.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Sequence

from .models import (
    Blocker,
    Denial,
    EvidenceReference,
    FreshnessState,
    GateLedger,
    GateState,
    Identity,
    NativeStateRef,
    NextLegalAction,
    NormalizedFailureClass,
    Phase,
    Posture,
    Subject,
    WorkItemProjection,
    digest_of,
)
from .receipts import assess_freshness

# Read-only git subcommands. Anything not listed here is refused rather than
# passed through, so this module cannot become a mutation path.
_ALLOWED_GIT_READS: frozenset[tuple[str, ...]] = frozenset(
    {
        ("rev-parse", "HEAD"),
        ("rev-parse", "--show-toplevel"),
        ("rev-parse", "--abbrev-ref", "HEAD"),
        ("config", "--get", "remote.origin.url"),
    }
)


def read_git_fact(repo_root: Path, args: Sequence[str]) -> str | None:
    """Run one allowlisted read-only git command. Returns None on failure.

    Fixed argv and ``shell=False``: no interpolation, no shell, no write verbs.
    """
    key = tuple(args)
    if key not in _ALLOWED_GIT_READS:
        raise Denial(
            NormalizedFailureClass.SCOPE_OR_CONTAINMENT_VIOLATION,
            f"git read {key!r} is not on the read-only allowlist",
        )
    try:
        completed = subprocess.run(
            ["git", *args],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            shell=False,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip() or None


@dataclass(frozen=True)
class SnapshotInput:
    """Everything the snapshot is allowed to consider, supplied explicitly."""

    identity: Identity
    work_item_id: str
    as_of: str
    subject: Subject = field(default_factory=Subject)
    gate_ledger: GateLedger | None = None
    evidence_refs: Sequence[EvidenceReference] = ()
    native_state_refs: Sequence[NativeStateRef] = ()
    packet_ref: str | None = None
    audit_acceptable: bool | None = None
    merge_decision_present: bool = False
    activation_decision_present: bool = False
    terminal: bool = False


# Gate classes whose satisfaction advances the coarse phase, in order. The
# projection is navigational: this ordering describes where work has reached,
# never what it is permitted to do next.
_PHASE_SEQUENCE: tuple[tuple[str, Phase], ...] = (
    ("IDENTITY", Phase.REQUEST),
    ("AUTHORITY", Phase.AUTHORITY),
    ("PACKET", Phase.AUTHORITY),
    ("SCOPE", Phase.IMPLEMENT),
    ("VALIDATION", Phase.VERIFY),
    ("FREEZE", Phase.VERIFY),
    ("AUDIT", Phase.REVIEW),
    ("PROOF", Phase.REVIEW),
    ("PR", Phase.REVIEW),
    ("CI", Phase.REVIEW),
    ("REVIEW", Phase.REVIEW),
    ("PR_STEWARD", Phase.MERGE),
    ("MERGE_AUTHORITY", Phase.MERGE),
    ("POST_MERGE", Phase.POST_MERGE),
    ("ACTIVATION", Phase.ACTIVATE),
)


def derive_phase(source: SnapshotInput) -> Phase:
    """Derive the coarse phase from satisfied gates and supplied decisions."""
    if source.terminal:
        return Phase.TERMINAL
    if source.activation_decision_present:
        return Phase.ACTIVATE
    if source.merge_decision_present:
        return Phase.POST_MERGE

    if source.gate_ledger is None:
        return Phase.REQUEST

    satisfied = {
        gate.gate_class
        for gate in source.gate_ledger.gates
        if gate.state is GateState.SATISFIED
    }
    reached = Phase.REQUEST
    for gate_class, phase in _PHASE_SEQUENCE:
        if gate_class in satisfied:
            reached = phase
    return reached


def collect_blockers(source: SnapshotInput) -> list[Blocker]:
    """Preserve every root blocker individually rather than aggregating."""
    blockers: list[Blocker] = []

    if source.gate_ledger is not None:
        for gate in source.gate_ledger.blocking_gates():
            if gate.state is GateState.UNKNOWN:
                normalized = NormalizedFailureClass.STALE_OR_MISMATCHED_EVIDENCE
            elif gate.state is GateState.CONFLICTING:
                normalized = NormalizedFailureClass.STALE_OR_MISMATCHED_EVIDENCE
            elif gate.state is GateState.STALE:
                normalized = NormalizedFailureClass.STALE_OR_MISMATCHED_EVIDENCE
            elif gate.state is GateState.BLOCKED:
                normalized = NormalizedFailureClass.BLOCKING_FINDING
            elif gate.state is GateState.PENDING:
                normalized = NormalizedFailureClass.CONTROL_EVENT_NOT_FAILURE
            else:
                normalized = NormalizedFailureClass.VALIDATION_FAILURE
            blockers.append(
                Blocker(
                    blocker_id=f"gate:{gate.gate_id}",
                    normalized_class=normalized,
                    statement=f"gate {gate.gate_id} is {gate.state.value}: {gate.reason}",
                )
            )

    for ref in source.evidence_refs:
        assessment = assess_freshness(ref, as_of=source.as_of)
        if assessment.state is not FreshnessState.CURRENT:
            blockers.append(
                Blocker(
                    blocker_id=f"evidence:{ref.evidence_id}",
                    normalized_class=NormalizedFailureClass.STALE_OR_MISMATCHED_EVIDENCE,
                    statement=f"evidence {ref.evidence_id} is {assessment.state.value}: {assessment.reason}",
                    evidence_ref=ref.evidence_id,
                )
            )

    if source.audit_acceptable is False:
        blockers.append(
            Blocker(
                blocker_id="audit:not-acceptable",
                normalized_class=NormalizedFailureClass.BLOCKING_FINDING,
                statement="supplied audit verdict is not PASS or PASS_WITH_RISKS",
            )
        )

    return blockers


# Blocker classes that make a work item BLOCKED rather than merely ACTIVE.
_HARD_BLOCK_CLASSES: frozenset[NormalizedFailureClass] = frozenset(
    {
        NormalizedFailureClass.BLOCKING_FINDING,
        NormalizedFailureClass.STALE_OR_MISMATCHED_EVIDENCE,
        NormalizedFailureClass.VALIDATION_FAILURE,
        NormalizedFailureClass.SCOPE_OR_CONTAINMENT_VIOLATION,
        NormalizedFailureClass.SECURITY_OR_TRUST_INCIDENT,
        NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
    }
)

# Blocker classes that require a human judgment rather than a repair.
_DECISION_CLASSES: frozenset[NormalizedFailureClass] = frozenset(
    {
        NormalizedFailureClass.AUTHORITY_OR_JUDGMENT_REQUIRED,
        NormalizedFailureClass.TERMINAL_REJECTION_OR_ROLLBACK,
    }
)


def derive_posture(source: SnapshotInput, blockers: Sequence[Blocker]) -> Posture:
    """Derive posture. A stale or unknown consequential source prevents READY.

    Precedence follows architecture section 02: terminal, then blocking gate or
    blocker, then human decision required, then ready, otherwise active. BLOCKED
    deliberately outranks DECISION_REQUIRED — an item that is both blocked and
    awaiting a decision is reported as blocked.
    """
    if source.terminal:
        return Posture.TERMINAL

    if any(b.normalized_class in _HARD_BLOCK_CLASSES for b in blockers):
        return Posture.BLOCKED

    if any(b.normalized_class in _DECISION_CLASSES for b in blockers):
        return Posture.DECISION_REQUIRED

    if blockers:
        return Posture.ACTIVE

    if source.audit_acceptable is None:
        # Audit outcome unknown: READY would overstate what the evidence shows.
        return Posture.ACTIVE

    return Posture.READY


def derive_next_legal_action(
    source: SnapshotInput, phase: Phase, posture: Posture, blockers: Sequence[Blocker]
) -> NextLegalAction:
    """Recommend the next action. Never dispatchable, never self-authorizing."""
    if posture is Posture.TERMINAL:
        return NextLegalAction("NONE", "NONE", authority_ref=None)

    if posture is Posture.DECISION_REQUIRED:
        return NextLegalAction(
            "OPERATOR_DECISION",
            "OPERATOR",
            authority_ref=None,
            prerequisites=[b.blocker_id for b in blockers],
        )

    if posture is Posture.BLOCKED:
        return NextLegalAction(
            "RESOLVE_BLOCKER",
            "IMPLEMENTER",
            authority_ref=source.packet_ref,
            prerequisites=[b.blocker_id for b in blockers],
        )

    if phase in {Phase.MERGE, Phase.POST_MERGE, Phase.ACTIVATE}:
        return NextLegalAction("OPERATOR_DECISION", "OPERATOR", authority_ref=None)

    return NextLegalAction("CONTINUE_IN_PACKET_SCOPE", "IMPLEMENTER", authority_ref=source.packet_ref)


def build_projection(source: SnapshotInput) -> WorkItemProjection:
    """Reduce supplied evidence to a deterministic projection."""
    blockers = collect_blockers(source)
    phase = derive_phase(source)
    posture = derive_posture(source, blockers)
    action = derive_next_legal_action(source, phase, posture, blockers)

    for ref in source.evidence_refs:
        source.identity.require_compatible(
            ref.identity, context=f"snapshot evidence {ref.evidence_id}"
        )

    projection_id = digest_of(
        {
            "work_item_id": source.work_item_id,
            "identity": source.identity.as_dict(),
            "subject": source.subject.as_dict(),
            "as_of": source.as_of,
        }
    )

    return WorkItemProjection(
        projection_id=projection_id,
        work_item_id=source.work_item_id,
        identity=source.identity,
        subject=source.subject,
        phase=phase,
        posture=posture,
        next_legal_action=action,
        updated_at=source.as_of,
        native_state_refs=list(source.native_state_refs),
        evidence_refs=list(source.evidence_refs),
        blockers=blockers,
        gate_ledger_ref=source.gate_ledger.ledger_id if source.gate_ledger else None,
        packet_ref=source.packet_ref,
    )


def build_snapshot(source: SnapshotInput) -> dict[str, Any]:
    """Answer the six required questions from referenced evidence."""
    projection = build_projection(source)
    freshness = [
        assess_freshness(ref, as_of=source.as_of).as_dict() for ref in source.evidence_refs
    ]

    return {
        "projection": projection.as_dict(),
        "gate_ledger": source.gate_ledger.as_dict() if source.gate_ledger else None,
        "answers": {
            "WHERE_IS_THIS_WORK": projection.phase.value,
            "WHAT_GATES_ARE_SATISFIED": sorted(
                gate.gate_id
                for gate in (source.gate_ledger.gates if source.gate_ledger else ())
                if gate.state is GateState.SATISFIED
            ),
            "WHAT_BLOCKS_IT": [b.as_dict() for b in projection.blockers],
            "WHAT_EVIDENCE_IS_CURRENT": freshness,
            "WHO_ACTS_NEXT": projection.next_legal_action.actor_class,
            "WHAT_ACTION_IS_LEGAL": projection.next_legal_action.as_dict(),
        },
    }
