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

import hashlib
import re
import subprocess
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Mapping, Sequence

from .models import (
    GATE_CLASSES,
    STRUCTURAL_CONJUNCTS,
    Blocker,
    ContentAuditBinding,
    Denial,
    EvidenceReference,
    FactBasis,
    FreshnessState,
    GateEntry,
    GateLedger,
    GateState,
    Identity,
    NativeStateRef,
    NextLegalAction,
    NormalizedFailureClass,
    Phase,
    Posture,
    StructuralFacts,
    Subject,
    WorkItemProjection,
    applicable_dimensions,
    digest_of,
)
from .receipts import assess_freshness

OBSERVER_VERSION = "governed-delivery.git-observer.1"

# Full object ids only. An abbreviated sha would let an ambiguous or
# short-form head into a receipt whose whole purpose is exact-head binding
# (architecture section 08: "valid for exact head pair and diff").
_SHA_RE = re.compile(r"^([0-9a-f]{40}|[0-9a-f]{64})$")

# Read-only git shapes. A shape is a fixed argv template; ``<sha>`` and
# ``<blobspec>`` are the only parameterised positions and each is validated
# before it reaches the process. Anything not matching a shape is refused, so
# this module cannot become a mutation path and cannot be steered into one by a
# crafted argument.
_GIT_READ_SHAPES: tuple[tuple[str, ...], ...] = (
    ("rev-parse", "HEAD"),
    ("rev-parse", "--show-toplevel"),
    ("rev-parse", "--abbrev-ref", "HEAD"),
    ("config", "--get", "remote.origin.url"),
    ("merge-base", "--is-ancestor", "<sha>", "<sha>"),
    ("merge-base", "<sha>", "<sha>"),
    ("diff", "--name-only", "<sha>", "<sha>"),
    ("diff", "--no-color", "<sha>", "<sha>"),
    ("ls-tree", "-r", "--full-tree", "<sha>"),
    ("show", "<blobspec>"),
)


def _valid_sha(value: str) -> bool:
    return bool(_SHA_RE.match(value))


def _valid_blobspec(value: str) -> bool:
    """``<sha>:<path>``, with the path constrained to stay inside the tree."""
    sha, separator, path = value.partition(":")
    if not separator or not _valid_sha(sha) or not path:
        return False
    if path.startswith("/") or "\0" in path:
        return False
    return ".." not in path.split("/")


def _matches_shape(args: Sequence[str], shape: Sequence[str]) -> bool:
    if len(args) != len(shape):
        return False
    for supplied, expected in zip(args, shape):
        if expected == "<sha>":
            if not _valid_sha(supplied):
                return False
        elif expected == "<blobspec>":
            if not _valid_blobspec(supplied):
                return False
        elif supplied != expected:
            return False
    return True


def run_git_read(
    repo_root: Path, args: Sequence[str], *, binary: bool = False
) -> tuple[int, Any]:
    """Run one shape-allowlisted read-only git command.

    Returns ``(returncode, output)``. Unlike :func:`read_git_fact` the return
    code is preserved, because ``merge-base --is-ancestor`` reports its answer
    that way and collapsing it to None would lose the distinction between "not
    an ancestor" and "the command could not run".
    """
    argv = list(args)
    if not any(_matches_shape(argv, shape) for shape in _GIT_READ_SHAPES):
        raise Denial(
            NormalizedFailureClass.SCOPE_OR_CONTAINMENT_VIOLATION,
            f"git read {tuple(argv)!r} does not match a read-only allowlisted shape",
        )
    try:
        completed = subprocess.run(
            ["git", *argv],
            cwd=str(repo_root),
            capture_output=True,
            text=not binary,
            shell=False,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return 128, b"" if binary else f"{exc}"
    return completed.returncode, completed.stdout


def read_git_fact(repo_root: Path, args: Sequence[str]) -> str | None:
    """Run one allowlisted read-only git command. Returns None on failure."""
    returncode, output = run_git_read(repo_root, args)
    if returncode != 0:
        return None
    return str(output).strip() or None


def _sha256_hex(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _tree_entries(repo_root: Path, head: str) -> dict[str, str] | None:
    """path -> ``mode type oid`` for every tracked entry at ``head``.

    Mode and type are kept, not just the object id. Two changes preserve the
    blob oid exactly while altering what the file *is*: a permission change
    (``100644`` to ``100755``, making a source file executable) and a type
    change (``100644`` to ``120000``, turning a file whose content reads
    ``/etc/passwd`` into a symlink pointing there). Digesting the oid alone
    would call both trees equivalent. The path-membership conjunct also catches
    them, but these are meant to be independent checks, and a conjunct that
    silently agrees with its neighbour is not one.
    """
    returncode, output = run_git_read(repo_root, ["ls-tree", "-r", "--full-tree", head])
    if returncode != 0:
        return None
    entries: dict[str, str] = {}
    for line in str(output).splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if not path or len(parts) < 3:
            continue
        mode, kind, oid = parts[0], parts[1], parts[2]
        entries[path] = f"{mode} {kind} {oid}"
    return entries


def _excluded_tree_digest(
    entries: Mapping[str, str], allowed_paths: Sequence[str]
) -> str:
    """Digest every tracked file NOT matching ``allowed_paths``.

    This is the concrete form of the receipt's
    ``content_digest_exclusion_definition``: a later auditor can recompute it
    from the same two heads and the same allowlist.
    """
    excluded = sorted(
        (path, blob)
        for path, blob in entries.items()
        if not any(fnmatch(path, pattern) for pattern in allowed_paths)
    )
    return digest_of(excluded)


def _blob_digest(repo_root: Path, head: str, path: str | None) -> str | None:
    """sha256 of one file's bytes at one head, or None when it is absent."""
    if not path:
        return None
    returncode, payload = run_git_read(repo_root, ["show", f"{head}:{path}"], binary=True)
    if returncode != 0:
        return None
    return _sha256_hex(payload)


def observe_proof_only_facts(
    repo_root: Path,
    *,
    audited_head: str,
    successor_head: str,
    allowed_paths: Sequence[str],
    packet_path: str | None = None,
    policy_path: str | None = None,
    audit_result_path: str | None = None,
) -> StructuralFacts:
    """Compute the structural conjuncts from git rather than accept them.

    GOV-AUD-002: every fact returned here carries ``OBSERVED_GIT`` only when
    this function actually established it from git objects. A step that could
    not run leaves its fact false with an ``UNKNOWN`` basis, so a partial
    observation degrades to a denial instead of a silent pass.
    """
    if not _valid_sha(audited_head) or not _valid_sha(successor_head):
        raise Denial(
            NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
            "both heads must be resolved git object ids before observation",
        )

    # Only the directly observed conjuncts are seeded here.
    # ``raw_diff_contains_no_substantive_source_change`` is deliberately absent:
    # the evaluator derives it from path membership and tree equality rather
    # than observing it, so claiming a basis for it here would be inventing one.
    basis: dict[str, FactBasis] = {
        name: FactBasis.UNKNOWN
        for name in STRUCTURAL_CONJUNCTS
        if name != "raw_diff_contains_no_substantive_source_change"
    }

    # 1. Ancestry. Only descent is tested; patch-equivalence is the architecture's
    #    permitted alternative but is not established here, so a non-descendant
    #    fails closed rather than being assumed equivalent.
    ancestry_code, _ = run_git_read(
        repo_root, ["merge-base", "--is-ancestor", audited_head, successor_head]
    )
    ancestry_established = ancestry_code == 0
    if ancestry_code in (0, 1):
        basis["current_head_descends_from_or_is_patch_equivalent_to_audited_head"] = (
            FactBasis.OBSERVED_GIT
        )

    # 2. Changed paths.
    paths_code, paths_out = run_git_read(
        repo_root, ["diff", "--name-only", audited_head, successor_head]
    )
    changed_paths: tuple[str, ...] = ()
    if paths_code == 0:
        changed_paths = tuple(
            line.strip() for line in str(paths_out).splitlines() if line.strip()
        )
        basis["actual_changed_paths_subset_of_allowed_proof_only_paths"] = (
            FactBasis.OBSERVED_GIT
        )

    # 3. Raw diff digest, retained so a laundered change stays detectable later.
    diff_code, diff_out = run_git_read(
        repo_root, ["diff", "--no-color", audited_head, successor_head], binary=True
    )
    raw_diff_digest = _sha256_hex(diff_out) if diff_code == 0 else ""

    # 4. Tree equality under exclusion.
    audited_entries = _tree_entries(repo_root, audited_head)
    successor_entries = _tree_entries(repo_root, successor_head)
    tree_equivalent = False
    if audited_entries is not None and successor_entries is not None:
        tree_equivalent = _excluded_tree_digest(
            audited_entries, allowed_paths
        ) == _excluded_tree_digest(successor_entries, allowed_paths)
        basis["audited_content_tree_equal_under_exclusion"] = FactBasis.OBSERVED_GIT

    # 5/6. Frozen digests, hashed from the named files' bytes at each head.
    absent: list[str] = []
    digests: dict[str, str | None] = {}
    for label, path in (
        ("packet", packet_path),
        ("policy", policy_path),
        ("audit_result", audit_result_path),
    ):
        for side, head in (("audited", audited_head), ("successor", successor_head)):
            value = _blob_digest(repo_root, head, path)
            digests[f"{side}_{label}"] = value
            if path and value is None:
                absent.append(f"{path}@{side}")

    if packet_path and policy_path:
        basis["packet_and_policy_digests_unchanged"] = FactBasis.OBSERVED_GIT
    if audit_result_path:
        basis["audit_result_bytes_unchanged"] = FactBasis.OBSERVED_GIT

    merge_base = read_git_fact(repo_root, ["merge-base", audited_head, successor_head])

    observation_digest = digest_of(
        {
            "audited_head": audited_head,
            "successor_head": successor_head,
            "allowed_paths": sorted(allowed_paths),
            "ancestry_established": ancestry_established,
            "actual_changed_paths": sorted(changed_paths),
            "raw_diff_digest": raw_diff_digest,
            "content_tree_equivalent_under_exclusion": tree_equivalent,
            "digests": {name: digests[name] for name in sorted(digests)},
            "merge_base": merge_base,
            "observer_version": OBSERVER_VERSION,
        }
    )

    return StructuralFacts._from_git_observer(
        ancestry_established=ancestry_established,
        actual_changed_paths=changed_paths,
        raw_diff_digest=raw_diff_digest,
        content_tree_equivalent_under_exclusion=tree_equivalent,
        audited_packet_digest=digests.get("audited_packet"),
        successor_packet_digest=digests.get("successor_packet"),
        audited_policy_digest=digests.get("audited_policy"),
        successor_policy_digest=digests.get("successor_policy"),
        audited_audit_result_digest=digests.get("audited_audit_result"),
        successor_audit_result_digest=digests.get("successor_audit_result"),
        basis=basis,
        merge_base=merge_base,
        observer_version=OBSERVER_VERSION,
        observation_digest=observation_digest,
        absent_named_paths=tuple(sorted(set(absent))),
    )


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
    audit_binding: ContentAuditBinding | None = None
    packet_digest: str | None = None
    policy_digest: str | None = None
    terminal: bool = False

    def __post_init__(self) -> None:
        if self.packet_ref != self.identity.packet_id:
            raise Denial(
                NormalizedFailureClass.SCOPE_OR_CONTAINMENT_VIOLATION,
                "snapshot packet_ref must match fixed G0 packet_id",
            )
        if self.gate_ledger is not None:
            self.identity.require_compatible(
                self.gate_ledger.identity,
                context="snapshot gate ledger",
                required_dimensions=applicable_dimensions(self.identity),
            )
            expected_subjects = {self.subject.head_sha, self.subject.content_digest}
            if self.gate_ledger.subject_digest_or_head not in expected_subjects:
                raise Denial(
                    NormalizedFailureClass.STALE_OR_MISMATCHED_EVIDENCE,
                    "gate ledger is not bound to snapshot head or content digest",
                )

    def identity_dimensions_required(self) -> tuple[str, ...]:
        return applicable_dimensions(self.identity)


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


def required_gate_classes(source: SnapshotInput) -> tuple[str, ...]:
    """Immutable G0 required gate set. No caller or JSON policy may narrow it."""
    return tuple(GATE_CLASSES)


def missing_required_gates(source: SnapshotInput) -> list[str]:
    """Required gate classes with no ledger entry at all."""
    present: set[str] = set()
    if source.gate_ledger is not None:
        present = {gate.gate_class for gate in source.gate_ledger.gates}
    return [name for name in required_gate_classes(source) if name not in present]


def gate_profile_complete(source: SnapshotInput) -> bool:
    if source.gate_ledger is None or missing_required_gates(source):
        return False
    states = source.gate_ledger.states_by_class()
    return all(
        states.get(name) in {GateState.SATISFIED, GateState.NOT_APPLICABLE}
        for name in GATE_CLASSES
    )


def audit_binding_acceptable(source: SnapshotInput) -> bool:
    if source.audit_binding is None:
        return False
    return source.audit_binding.is_acceptable_for(
        subject=source.subject,
        packet_ref=source.identity.packet_id or "",
        packet_digest=source.packet_digest,
        policy_digest=source.policy_digest,
    )


def _unknown_gate_for(source: SnapshotInput, gate_class: str) -> GateEntry:
    """Materialize a missing required gate as UNKNOWN.

    Architecture section 05 defines UNKNOWN as "required evidence is missing",
    which is precisely this case. GOV-AUD-003 was that an omitted gate was
    instead read as nothing at all, so an incomplete ledger could reach READY.
    """
    return GateEntry(
        gate_id=f"missing:{gate_class.lower()}",
        gate_class=gate_class,
        state=GateState.UNKNOWN,
        policy_owner="governed-delivery.required-gate-profile",
        policy_version="v1",
        subject_digest_or_head=(
            source.subject.head_sha
            or source.subject.content_digest
            or source.identity.packet_id
            or source.work_item_id
        ),
        producer_identity="governed-delivery.snapshot",
        observed_at=source.as_of,
        reason=(
            f"required gate class {gate_class} has no entry in the ledger; "
            "required evidence is missing"
        ),
    )


def derive_phase(source: SnapshotInput) -> Phase:
    """Derive the coarse phase from the longest satisfied prefix of the sequence.

    GOV-AUD-003: taking the highest phase reached by *any* satisfied gate let a
    ledger holding only a late gate claim a phase whose prerequisites were never
    evidenced. Advancement now stops at the first required gate that is not
    satisfied, so a phase implies everything before it.
    """
    if source.terminal:
        return Phase.TERMINAL

    if source.gate_ledger is None:
        return Phase.REQUEST

    states = source.gate_ledger.states_by_class()
    required = set(required_gate_classes(source))

    reached = Phase.REQUEST
    for gate_class, phase in _PHASE_SEQUENCE:
        state = states.get(gate_class)
        if state is GateState.SATISFIED:
            reached = phase
            continue
        if state is GateState.NOT_APPLICABLE:
            # Policy declared this gate inapplicable: not a barrier, but not
            # evidence of arrival either. Skip without advancing.
            continue
        if state is None and gate_class not in required:
            # Absent and not required: nothing to evidence, nothing to fail.
            continue
        # Anything else stops advancement — including a gate the policy does not
        # require but which is present and NOT satisfied. "Not required" excuses
        # an absence, never a visible failure: stepping over a present
        # UNSATISFIED or BLOCKED gate would let a later gate claim a phase whose
        # prerequisite demonstrably did not hold.
        break
    return reached


def collect_blockers(source: SnapshotInput) -> list[Blocker]:
    """Preserve every root blocker individually rather than aggregating."""
    blockers: list[Blocker] = []

    synthesized = [_unknown_gate_for(source, name) for name in missing_required_gates(source)]

    if source.gate_ledger is not None or synthesized:
        existing = source.gate_ledger.blocking_gates() if source.gate_ledger else []
        for gate in [*existing, *synthesized]:
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

    if source.audit_binding is None:
        blockers.append(
            Blocker(
                blocker_id="audit:no-binding",
                normalized_class=NormalizedFailureClass.STALE_OR_MISMATCHED_EVIDENCE,
                statement="no ContentAuditBinding supplied; AUDIT is UNKNOWN",
            )
        )
    elif not audit_binding_acceptable(source):
        blockers.append(
            Blocker(
                blocker_id="audit:binding-invalid",
                normalized_class=NormalizedFailureClass.BLOCKING_FINDING,
                statement=(
                    "ContentAuditBinding does not match exact head, tree, content, packet, "
                    "policy, verdict, identity, and independence requirements"
                ),
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

    required_dimensions = source.identity_dimensions_required()
    for ref in source.evidence_refs:
        source.identity.require_compatible(
            ref.identity,
            context=f"snapshot evidence {ref.evidence_id}",
            required_dimensions=required_dimensions,
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
        gate_profile_complete=gate_profile_complete(source),
        audit_binding_acceptable=audit_binding_acceptable(source),
        audit_binding_ref=source.audit_binding.audit_id if source.audit_binding else None,
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
        "required_gate_classes": list(required_gate_classes(source)),
        "missing_required_gate_classes": missing_required_gates(source),
        "required_identity_dimensions": list(source.identity_dimensions_required()),
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
