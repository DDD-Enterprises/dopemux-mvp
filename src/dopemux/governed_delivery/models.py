"""Pure typed models for the governed-delivery evidence spine.

Everything here is derived and non-authoritative. Construction and validation
perform no I/O, consult no clock, and open no network connection: any instant a
caller needs must be passed in explicitly as ``as_of``.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Sequence

SCHEMA_EVIDENCE_REFERENCE = "governed-delivery.evidence-reference.v1"
SCHEMA_ENVELOPE = "governed-delivery.envelope.v1"
SCHEMA_GATE_LEDGER = "governed-delivery.gate-ledger.v1"
SCHEMA_WORK_ITEM_PROJECTION = "governed-delivery.work-item-projection.v1"
SCHEMA_CONTENT_AUDIT_BINDING = "governed-delivery.content-audit-binding.v1"
SCHEMA_PROOF_ONLY_EQUIVALENCE = "governed-delivery.proof-only-successor-equivalence.v1"
SCHEMA_OPERATOR_DECISION_REQUEST = "governed-delivery.operator-decision-request.v1"


class NormalizedFailureClass(str, Enum):
    """The eleven normalized failure classes.

    The census enumerates 44 failure branches. They reduce to these eleven so
    that no global workflow mega-enum is created.
    """

    CONTROL_EVENT_NOT_FAILURE = "CONTROL_EVENT_NOT_FAILURE"
    INVALID_INPUT_OR_ARTIFACT = "INVALID_INPUT_OR_ARTIFACT"
    STALE_OR_MISMATCHED_EVIDENCE = "STALE_OR_MISMATCHED_EVIDENCE"
    VALIDATION_FAILURE = "VALIDATION_FAILURE"
    BLOCKING_FINDING = "BLOCKING_FINDING"
    AUTHORITY_OR_JUDGMENT_REQUIRED = "AUTHORITY_OR_JUDGMENT_REQUIRED"
    CAPABILITY_UNAVAILABLE = "CAPABILITY_UNAVAILABLE"
    EXTERNAL_SYSTEM_UNAVAILABLE = "EXTERNAL_SYSTEM_UNAVAILABLE"
    SCOPE_OR_CONTAINMENT_VIOLATION = "SCOPE_OR_CONTAINMENT_VIOLATION"
    SECURITY_OR_TRUST_INCIDENT = "SECURITY_OR_TRUST_INCIDENT"
    TERMINAL_REJECTION_OR_ROLLBACK = "TERMINAL_REJECTION_OR_ROLLBACK"


class EnvelopeKind(str, Enum):
    FACT = "FACT"
    REQUEST = "REQUEST"
    FINDING = "FINDING"
    DECISION = "DECISION"
    RECEIPT = "RECEIPT"


class GateState(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PENDING = "PENDING"
    SATISFIED = "SATISFIED"
    UNSATISFIED = "UNSATISFIED"
    STALE = "STALE"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"
    CONFLICTING = "CONFLICTING"


class Phase(str, Enum):
    REQUEST = "REQUEST"
    DESIGN = "DESIGN"
    AUTHORITY = "AUTHORITY"
    IMPLEMENT = "IMPLEMENT"
    VERIFY = "VERIFY"
    REVIEW = "REVIEW"
    MERGE = "MERGE"
    POST_MERGE = "POST_MERGE"
    ACTIVATE = "ACTIVATE"
    TERMINAL = "TERMINAL"


class Posture(str, Enum):
    ACTIVE = "ACTIVE"
    BLOCKED = "BLOCKED"
    DECISION_REQUIRED = "DECISION_REQUIRED"
    READY = "READY"
    TERMINAL = "TERMINAL"


class FreshnessState(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    EXPIRED = "EXPIRED"
    SUPERSEDED = "SUPERSEDED"
    TOMBSTONED = "TOMBSTONED"
    UNKNOWN = "UNKNOWN"


class AuthorityEffect(str, Enum):
    NONE = "NONE"
    ADVISORY = "ADVISORY"
    GATE_INPUT = "GATE_INPUT"
    CANONICAL_DECISION = "CANONICAL_DECISION"
    TRANSITION_RECEIPT = "TRANSITION_RECEIPT"


class Independence(str, Enum):
    PROVEN = "PROVEN"
    LIMITED = "LIMITED"
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"


class AuditVerdict(str, Enum):
    PASS = "PASS"
    PASS_WITH_RISKS = "PASS_WITH_RISKS"
    FAIL = "FAIL"
    NEEDS_SUPERVISOR = "NEEDS_SUPERVISOR"
    SKIPPED = "SKIPPED"
    MALFORMED = "MALFORMED"
    UNKNOWN = "UNKNOWN"


class DecisionType(str, Enum):
    ARCHITECTURE_DECISION_REQUIRED = "ARCHITECTURE_DECISION_REQUIRED"
    RED_LANE_AUTHORIZATION_REQUIRED = "RED_LANE_AUTHORIZATION_REQUIRED"
    SUPERVISOR_ESCALATION_REQUIRED = "SUPERVISOR_ESCALATION_REQUIRED"
    MERGE_DECISION_REQUIRED = "MERGE_DECISION_REQUIRED"
    ACTIVATION_DECISION_REQUIRED = "ACTIVATION_DECISION_REQUIRED"


EVIDENCE_CLASSES: tuple[str, ...] = (
    "TASK_PACKET",
    "REPO_IDENTITY_RECEIPT",
    "SCOPE_RECEIPT",
    "VALIDATION_RECEIPT",
    "CONTENT_FREEZE_RECEIPT",
    "AUDIT_REQUEST",
    "AUDIT_EXECUTION_RECEIPT",
    "AUDIT_RESULT",
    "PROOF_BUNDLE",
    "PROOF_ONLY_EQUIVALENCE_RECEIPT",
    "PR_REFERENCE",
    "CI_CHECK_RESULT",
    "REVIEW_FINDING",
    "REVIEW_DISPOSITION",
    "PR_STEWARD_RESULT",
    "OPERATOR_DECISION",
    "MERGE_RECEIPT",
    "POST_MERGE_RECEIPT",
    "ACTIVATION_RECEIPT",
    "WORKFLOW_TRANSITION_RECEIPT",
)

GATE_CLASSES: tuple[str, ...] = (
    "IDENTITY",
    "AUTHORITY",
    "PACKET",
    "SCOPE",
    "VALIDATION",
    "FREEZE",
    "AUDIT",
    "PROOF",
    "PR",
    "CI",
    "REVIEW",
    "PR_STEWARD",
    "MERGE_AUTHORITY",
    "POST_MERGE",
    "ACTIVATION",
)


# The 39 census message classes, mapped to the five envelope kinds.
# Transcribed from DMX-GOV-WORKFLOW-OPT-001 section 03; the reduction is the
# architecture's own, not this module's invention.
MESSAGE_CLASS_CENSUS: Mapping[str, EnvelopeKind] = {
    "WorkIntake": EnvelopeKind.REQUEST,
    "InvestigationRequest": EnvelopeKind.REQUEST,
    "ArchitectureDecisionRequest": EnvelopeKind.REQUEST,
    "ExecutionDispatch": EnvelopeKind.REQUEST,
    "RepairRequest": EnvelopeKind.REQUEST,
    "AuditRequest": EnvelopeKind.REQUEST,
    "SupervisorEscalation": EnvelopeKind.REQUEST,
    "MergeDecisionRequest": EnvelopeKind.REQUEST,
    "ActivationDecisionRequest": EnvelopeKind.REQUEST,
    "InvestigationResult": EnvelopeKind.FACT,
    "ArchitectureCandidate": EnvelopeKind.FACT,
    "ExecutionHandoff": EnvelopeKind.FACT,
    "ProofBundleRef": EnvelopeKind.FACT,
    "PRCreated": EnvelopeKind.FACT,
    "PRHeadMoved": EnvelopeKind.FACT,
    "FallbackTransitionClaim": EnvelopeKind.FACT,
    "ArchitectureDecision": EnvelopeKind.DECISION,
    "ReviewDisposition": EnvelopeKind.DECISION,
    "MergeDecision": EnvelopeKind.DECISION,
    "ActivationDecision": EnvelopeKind.DECISION,
    "TaskPacketIssued": EnvelopeKind.RECEIPT,
    "PacketValidationResult": EnvelopeKind.RECEIPT,
    "ExecutionResult": EnvelopeKind.RECEIPT,
    "ValidationResult": EnvelopeKind.RECEIPT,
    "RepairResult": EnvelopeKind.RECEIPT,
    "FreezeNotice": EnvelopeKind.RECEIPT,
    "CIResult": EnvelopeKind.RECEIPT,
    "MergeReceipt": EnvelopeKind.RECEIPT,
    "PostMergeValidationResult": EnvelopeKind.RECEIPT,
    "ActivationReceipt": EnvelopeKind.RECEIPT,
    "WorkflowTransitionReceipt": EnvelopeKind.RECEIPT,
    "LeantimeReflectionReceipt": EnvelopeKind.RECEIPT,
    "SecondBrainPromotionReceipt": EnvelopeKind.RECEIPT,
    "AuditResult": EnvelopeKind.FINDING,
    "DriftNotice": EnvelopeKind.FINDING,
    "StaleEvidenceNotice": EnvelopeKind.FINDING,
    "BlockerNotice": EnvelopeKind.FINDING,
    "ReviewFinding": EnvelopeKind.FINDING,
    "PRStewardResult": EnvelopeKind.FINDING,
}


# The 44 census failure branches, mapped to the eleven normalized classes.
# Transcribed from DMX-GOV-WORKFLOW-OPT-001 section 10.
FAILURE_BRANCH_CENSUS: Mapping[str, tuple[str, NormalizedFailureClass]] = {
    "F-01": ("scope conflict", NormalizedFailureClass.SCOPE_OR_CONTAINMENT_VIOLATION),
    "F-02": ("architecture uncertainty", NormalizedFailureClass.AUTHORITY_OR_JUDGMENT_REQUIRED),
    "F-03": ("authority missing", NormalizedFailureClass.AUTHORITY_OR_JUDGMENT_REQUIRED),
    "F-04": ("packet invalid", NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT),
    "F-05": ("wrong repo/worktree/branch", NormalizedFailureClass.SCOPE_OR_CONTAINMENT_VIOLATION),
    "F-06": ("main movement", NormalizedFailureClass.CONTROL_EVENT_NOT_FAILURE),
    "F-07": ("PR head movement", NormalizedFailureClass.STALE_OR_MISMATCHED_EVIDENCE),
    "F-08": ("allowlist violation", NormalizedFailureClass.SCOPE_OR_CONTAINMENT_VIOLATION),
    "F-09": ("pre-commit mutation", NormalizedFailureClass.STALE_OR_MISMATCHED_EVIDENCE),
    "F-10": ("focused test failure", NormalizedFailureClass.VALIDATION_FAILURE),
    "F-11": ("full-suite failure", NormalizedFailureClass.VALIDATION_FAILURE),
    "F-12": ("secret-scan failure", NormalizedFailureClass.SECURITY_OR_TRUST_INCIDENT),
    "F-13": ("implementer blocked", NormalizedFailureClass.CAPABILITY_UNAVAILABLE),
    "F-14": ("implementer overreach", NormalizedFailureClass.SCOPE_OR_CONTAINMENT_VIOLATION),
    "F-15": ("incomplete handoff", NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT),
    "F-16": ("auditor unavailable", NormalizedFailureClass.CAPABILITY_UNAVAILABLE),
    "F-17": ("audit transport failure", NormalizedFailureClass.EXTERNAL_SYSTEM_UNAVAILABLE),
    "F-18": ("malformed audit", NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT),
    "F-19": ("unknown auditor identity", NormalizedFailureClass.SECURITY_OR_TRUST_INCIDENT),
    "F-20": ("audit FAIL", NormalizedFailureClass.BLOCKING_FINDING),
    "F-21": ("audit NEEDS_SUPERVISOR", NormalizedFailureClass.AUTHORITY_OR_JUDGMENT_REQUIRED),
    "F-22": ("audit PASS_WITH_RISKS", NormalizedFailureClass.CONTROL_EVENT_NOT_FAILURE),
    "F-23": ("proof malformed", NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT),
    "F-24": ("proof stale", NormalizedFailureClass.STALE_OR_MISMATCHED_EVIDENCE),
    "F-25": ("proof/head mismatch", NormalizedFailureClass.STALE_OR_MISMATCHED_EVIDENCE),
    "F-26": ("push rejection", NormalizedFailureClass.EXTERNAL_SYSTEM_UNAVAILABLE),
    "F-27": ("CI pending", NormalizedFailureClass.CONTROL_EVENT_NOT_FAILURE),
    "F-28": ("CI stale", NormalizedFailureClass.STALE_OR_MISMATCHED_EVIDENCE),
    "F-29": ("CI cancelled", NormalizedFailureClass.EXTERNAL_SYSTEM_UNAVAILABLE),
    "F-30": ("CI failure", NormalizedFailureClass.VALIDATION_FAILURE),
    "F-31": ("review comment", NormalizedFailureClass.CONTROL_EVENT_NOT_FAILURE),
    "F-32": ("review thread", NormalizedFailureClass.BLOCKING_FINDING),
    "F-33": ("MUST_FIX", NormalizedFailureClass.BLOCKING_FINDING),
    "F-34": ("optional/deferred review", NormalizedFailureClass.CONTROL_EVENT_NOT_FAILURE),
    "F-35": ("PR Steward NOT_READY", NormalizedFailureClass.CONTROL_EVENT_NOT_FAILURE),
    "F-36": ("PR Steward NEEDS_IMPLEMENTER", NormalizedFailureClass.BLOCKING_FINDING),
    "F-37": ("PR Steward NEEDS_SUPERVISOR", NormalizedFailureClass.AUTHORITY_OR_JUDGMENT_REQUIRED),
    "F-38": ("PR Steward BLOCKED", NormalizedFailureClass.CONTROL_EVENT_NOT_FAILURE),
    "F-39": ("merge conflict", NormalizedFailureClass.STALE_OR_MISMATCHED_EVIDENCE),
    "F-40": ("missing merge gate", NormalizedFailureClass.SECURITY_OR_TRUST_INCIDENT),
    "F-41": ("operator rejects merge", NormalizedFailureClass.TERMINAL_REJECTION_OR_ROLLBACK),
    "F-42": ("post-merge validation failure", NormalizedFailureClass.VALIDATION_FAILURE),
    "F-43": ("activation benchmark failure", NormalizedFailureClass.VALIDATION_FAILURE),
    "F-44": ("rollback", NormalizedFailureClass.TERMINAL_REJECTION_OR_ROLLBACK),
}

# Branches the census explicitly reframes: they are routed, not treated as
# defects. F-32 additionally carries audit note GOV-AUD-N3 — an unresolved
# review thread is blocking only once an authoritative classification says so.
CONTROL_REFRAMED_BRANCHES: frozenset[str] = frozenset(
    {"F-06", "F-09", "F-22", "F-27", "F-31", "F-34", "F-35", "F-38", "F-44"}
)


class GovernedDeliveryError(Exception):
    """Base class for deterministic governed-delivery denials."""


@dataclass(frozen=True)
class Denial(GovernedDeliveryError):
    """A fail-closed denial carrying its normalized class and reason."""

    normalized_class: NormalizedFailureClass
    reason: str

    def __str__(self) -> str:
        return f"{self.normalized_class.value}: {self.reason}"


def canonical_json(value: Any) -> str:
    """Deterministic JSON encoding: sorted keys, no incidental whitespace."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest_of(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


_ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?$")


def parse_instant(raw: str, *, field_name: str) -> datetime:
    """Parse an ISO-8601 instant. Unparseable input is denied, never guessed."""
    if not isinstance(raw, str) or not _ISO_RE.match(raw):
        raise Denial(
            NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
            f"{field_name} is not a parseable ISO-8601 instant: {raw!r}",
        )
    text = raw.replace(" ", "T")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _require_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Denial(
            NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
            f"{field_name} must be a non-empty string",
        )
    return value


def _require_known_identity(value: Any, field_name: str) -> str:
    """Identity fields fail closed: absent, blank or UNKNOWN is a denial."""
    if not isinstance(value, str) or not value.strip():
        raise Denial(
            NormalizedFailureClass.SCOPE_OR_CONTAINMENT_VIOLATION,
            f"{field_name} is required and unknown identity fails closed",
        )
    if value.strip().upper() == "UNKNOWN":
        raise Denial(
            NormalizedFailureClass.SCOPE_OR_CONTAINMENT_VIOLATION,
            f"{field_name} is UNKNOWN; unknown identity fails closed",
        )
    return value


def _require_enum(value: Any, enum_cls: type[Enum], field_name: str) -> Any:
    try:
        return enum_cls(value)
    except ValueError as exc:
        raise Denial(
            NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
            f"{field_name} has unknown value {value!r}",
        ) from exc


def _require_schema_version(value: Any, expected: str) -> str:
    if value != expected:
        raise Denial(
            NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
            f"unknown schema_version {value!r}; expected {expected!r}",
        )
    return value


@dataclass(frozen=True)
class Identity:
    """The isolation dimensions every consequential reduction must bind."""

    project_id: str
    repository_id: str
    workspace_id: str | None = None
    worktree_id: str | None = None
    instance_id: str | None = None
    packet_id: str | None = None

    def __post_init__(self) -> None:
        _require_known_identity(self.project_id, "project_id")
        _require_known_identity(self.repository_id, "repository_id")

    def conflicts_with(self, other: "Identity") -> str | None:
        """Return the first conflicting dimension, or None when compatible.

        A dimension present on both sides must match exactly. A dimension known
        on one side and absent on the other is not itself a conflict; callers
        that require presence enforce it separately.
        """
        for name in (
            "project_id",
            "repository_id",
            "workspace_id",
            "worktree_id",
            "instance_id",
            "packet_id",
        ):
            mine = getattr(self, name)
            theirs = getattr(other, name)
            if mine is not None and theirs is not None and mine != theirs:
                return name
        return None

    def require_compatible(self, other: "Identity", *, context: str) -> None:
        conflict = self.conflicts_with(other)
        if conflict is not None:
            raise Denial(
                NormalizedFailureClass.SCOPE_OR_CONTAINMENT_VIOLATION,
                f"{context}: {conflict} mismatch "
                f"({getattr(self, conflict)!r} vs {getattr(other, conflict)!r})",
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "repository_id": self.repository_id,
            "workspace_id": self.workspace_id,
            "worktree_id": self.worktree_id,
            "instance_id": self.instance_id,
            "packet_id": self.packet_id,
        }


@dataclass(frozen=True)
class Subject:
    """Git subject binding. Preserved in full so head and tree never blur."""

    base_sha: str | None = None
    head_sha: str | None = None
    tree_sha: str | None = None
    content_digest: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
            "tree_sha": self.tree_sha,
            "content_digest": self.content_digest,
        }


@dataclass(frozen=True)
class EvidenceReference:
    """Points at evidence owned elsewhere; never copies or amplifies it."""

    evidence_id: str
    evidence_class: str
    owner_system: str
    producer_identity: str
    canonical_location: str
    digest_or_signature: str
    identity: Identity
    observed_at: str
    authority_effect: AuthorityEffect = AuthorityEffect.NONE
    freshness_state: FreshnessState = FreshnessState.UNKNOWN
    subject: Subject = field(default_factory=Subject)
    valid_until: str | None = None
    schema_version_used: str | None = None
    policy_version: str | None = None
    tool_version: str | None = None
    environment_digest: str | None = None
    supersedes: str | None = None
    tombstone: bool | None = None

    def __post_init__(self) -> None:
        _require_text(self.evidence_id, "evidence_id")
        _require_text(self.owner_system, "owner_system")
        _require_text(self.producer_identity, "producer_identity")
        _require_text(self.canonical_location, "canonical_location")
        _require_text(self.digest_or_signature, "digest_or_signature")
        if self.evidence_class not in EVIDENCE_CLASSES:
            raise Denial(
                NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
                f"unknown evidence_class {self.evidence_class!r}",
            )
        parse_instant(self.observed_at, field_name="observed_at")
        if self.valid_until is not None:
            parse_instant(self.valid_until, field_name="valid_until")

    @property
    def is_usable(self) -> bool:
        """Only CURRENT, non-tombstoned evidence may support a reduction."""
        return self.freshness_state is FreshnessState.CURRENT and not self.tombstone

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_EVIDENCE_REFERENCE,
            "evidence_id": self.evidence_id,
            "evidence_class": self.evidence_class,
            "owner_system": self.owner_system,
            "producer_identity": self.producer_identity,
            "canonical_location": self.canonical_location,
            "digest_or_signature": self.digest_or_signature,
            **self.identity.as_dict(),
            **self.subject.as_dict(),
            "schema_version_used": self.schema_version_used,
            "policy_version": self.policy_version,
            "tool_version": self.tool_version,
            "environment_digest": self.environment_digest,
            "observed_at": self.observed_at,
            "valid_until": self.valid_until,
            "freshness_state": self.freshness_state.value,
            "supersedes": self.supersedes,
            "tombstone": self.tombstone,
            "authority_effect": self.authority_effect.value,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "EvidenceReference":
        _require_schema_version(raw.get("schema_version"), SCHEMA_EVIDENCE_REFERENCE)
        return cls(
            evidence_id=raw.get("evidence_id", ""),
            evidence_class=raw.get("evidence_class", ""),
            owner_system=raw.get("owner_system", ""),
            producer_identity=raw.get("producer_identity", ""),
            canonical_location=raw.get("canonical_location", ""),
            digest_or_signature=raw.get("digest_or_signature", ""),
            identity=Identity(
                project_id=raw.get("project_id", ""),
                repository_id=raw.get("repository_id", ""),
                workspace_id=raw.get("workspace_id"),
                worktree_id=raw.get("worktree_id"),
                instance_id=raw.get("instance_id"),
                packet_id=raw.get("packet_id"),
            ),
            subject=Subject(
                base_sha=raw.get("base_sha"),
                head_sha=raw.get("head_sha"),
                tree_sha=raw.get("tree_sha"),
                content_digest=raw.get("content_digest"),
            ),
            observed_at=raw.get("observed_at", ""),
            valid_until=raw.get("valid_until"),
            freshness_state=_require_enum(
                raw.get("freshness_state", "UNKNOWN"), FreshnessState, "freshness_state"
            ),
            authority_effect=_require_enum(
                raw.get("authority_effect", "NONE"), AuthorityEffect, "authority_effect"
            ),
            schema_version_used=raw.get("schema_version_used"),
            policy_version=raw.get("policy_version"),
            tool_version=raw.get("tool_version"),
            environment_digest=raw.get("environment_digest"),
            supersedes=raw.get("supersedes"),
            tombstone=raw.get("tombstone"),
        )


@dataclass(frozen=True)
class GovernedDeliveryEnvelope:
    """Transport for the five payload kinds. Carries no authority of its own."""

    envelope_id: str
    kind: EnvelopeKind
    event_type: str
    identity: Identity
    producer: str
    consumer: str
    created_at: str
    subject_ref: str
    idempotency_key: str
    payload_schema: str
    payload: Mapping[str, Any]
    evidence_refs: Sequence[EvidenceReference] = ()
    work_item_id: str | None = None
    authority_effect: AuthorityEffect = AuthorityEffect.NONE

    # Structurally false: transport can never authorize mutation.
    mutation_authorized: bool = False

    def __post_init__(self) -> None:
        _require_text(self.envelope_id, "envelope_id")
        _require_text(self.event_type, "event_type")
        _require_text(self.producer, "producer")
        _require_text(self.consumer, "consumer")
        _require_text(self.subject_ref, "subject_ref")
        _require_text(self.idempotency_key, "idempotency_key")
        _require_text(self.payload_schema, "payload_schema")
        parse_instant(self.created_at, field_name="created_at")
        if self.mutation_authorized:
            raise Denial(
                NormalizedFailureClass.SECURITY_OR_TRUST_INCIDENT,
                "mutation_authorized must remain false: transport cannot grant mutation",
            )
        expected = MESSAGE_CLASS_CENSUS.get(self.event_type)
        if expected is not None and expected is not self.kind:
            raise Denial(
                NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
                f"event_type {self.event_type!r} is a {expected.value} class, not {self.kind.value}",
            )
        for ref in self.evidence_refs:
            self.identity.require_compatible(
                ref.identity, context=f"envelope {self.envelope_id} evidence {ref.evidence_id}"
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_ENVELOPE,
            "envelope_id": self.envelope_id,
            "kind": self.kind.value,
            "event_type": self.event_type,
            "project_id": self.identity.project_id,
            "repository_id": self.identity.repository_id,
            "work_item_id": self.work_item_id,
            "packet_id": self.identity.packet_id,
            "producer": self.producer,
            "consumer": self.consumer,
            "created_at": self.created_at,
            "subject_ref": self.subject_ref,
            "evidence_refs": [ref.as_dict() for ref in self.evidence_refs],
            "idempotency_key": self.idempotency_key,
            "payload_schema": self.payload_schema,
            "payload": dict(self.payload),
            "authority_effect": self.authority_effect.value,
            "mutation_authorized": False,
        }


@dataclass(frozen=True)
class GateEntry:
    gate_id: str
    gate_class: str
    state: GateState
    policy_owner: str
    policy_version: str
    subject_digest_or_head: str
    producer_identity: str
    observed_at: str
    reason: str
    evidence_refs: Sequence[EvidenceReference] = ()
    blocking_actions: Sequence[str] = ()
    valid_until: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.gate_id, "gate_id")
        _require_text(self.policy_owner, "policy_owner")
        _require_text(self.policy_version, "policy_version")
        _require_text(self.reason, "reason")
        if self.gate_class not in GATE_CLASSES:
            raise Denial(
                NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
                f"unknown gate_class {self.gate_class!r}",
            )

    @property
    def blocks_consequential_action(self) -> bool:
        """UNKNOWN and CONFLICTING fail closed alongside the overt blockers."""
        return self.state in {
            GateState.UNSATISFIED,
            GateState.STALE,
            GateState.BLOCKED,
            GateState.UNKNOWN,
            GateState.CONFLICTING,
            GateState.PENDING,
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "gate_class": self.gate_class,
            "state": self.state.value,
            "policy_owner": self.policy_owner,
            "policy_version": self.policy_version,
            "evidence_refs": [ref.as_dict() for ref in self.evidence_refs],
            "subject_digest_or_head": self.subject_digest_or_head,
            "producer_identity": self.producer_identity,
            "observed_at": self.observed_at,
            "valid_until": self.valid_until,
            "blocking_actions": list(self.blocking_actions),
            "reason": self.reason,
        }


@dataclass(frozen=True)
class GateLedger:
    ledger_id: str
    identity: Identity
    subject_digest_or_head: str
    gates: Sequence[GateEntry] = ()

    def blocking_gates(self) -> list[GateEntry]:
        return [gate for gate in self.gates if gate.blocks_consequential_action]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_GATE_LEDGER,
            "ledger_id": self.ledger_id,
            "project_id": self.identity.project_id,
            "repository_id": self.identity.repository_id,
            "subject_digest_or_head": self.subject_digest_or_head,
            "gates": [gate.as_dict() for gate in self.gates],
        }


@dataclass(frozen=True)
class Blocker:
    blocker_id: str
    normalized_class: NormalizedFailureClass
    statement: str
    evidence_ref: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "blocker_id": self.blocker_id,
            "normalized_class": self.normalized_class.value,
            "statement": self.statement,
            "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True)
class NativeStateRef:
    subsystem: str
    native_state: str
    evidence_ref: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "subsystem": self.subsystem,
            "native_state": self.native_state,
            "evidence_ref": self.evidence_ref,
        }


@dataclass(frozen=True)
class NextLegalAction:
    """A recommendation. Never an execution permission."""

    action_type: str
    actor_class: str
    authority_ref: str | None = None
    prerequisites: Sequence[str] = ()

    @property
    def dispatch_eligible(self) -> bool:
        # Structurally false for the whole of G0.
        return False

    def as_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "actor_class": self.actor_class,
            "authority_ref": self.authority_ref,
            "prerequisites": list(self.prerequisites),
            "dispatch_eligible": False,
        }


@dataclass(frozen=True)
class WorkItemProjection:
    projection_id: str
    work_item_id: str
    identity: Identity
    subject: Subject
    phase: Phase
    posture: Posture
    next_legal_action: NextLegalAction
    updated_at: str
    native_state_refs: Sequence[NativeStateRef] = ()
    evidence_refs: Sequence[EvidenceReference] = ()
    blockers: Sequence[Blocker] = ()
    gate_ledger_ref: str | None = None
    packet_ref: str | None = None

    def as_dict(self) -> dict[str, Any]:
        body = {
            "schema_version": SCHEMA_WORK_ITEM_PROJECTION,
            "projection_id": self.projection_id,
            "work_item_id": self.work_item_id,
            "project_id": self.identity.project_id,
            "repository_id": self.identity.repository_id,
            "workspace_id": self.identity.workspace_id,
            "worktree_id": self.identity.worktree_id,
            "instance_id": self.identity.instance_id,
            "packet_ref": self.packet_ref or self.identity.packet_id,
            "subject": self.subject.as_dict(),
            "phase": self.phase.value,
            "posture": self.posture.value,
            "native_state_refs": [ref.as_dict() for ref in self.native_state_refs],
            "gate_ledger_ref": self.gate_ledger_ref,
            "evidence_refs": [ref.as_dict() for ref in self.evidence_refs],
            "blockers": [blocker.as_dict() for blocker in self.blockers],
            "next_legal_action": self.next_legal_action.as_dict(),
            "updated_at": self.updated_at,
        }
        body["projection_digest"] = digest_of(body)
        return body


@dataclass(frozen=True)
class ContentAuditBinding:
    """Represents a supplied audit result. Never invokes an auditor."""

    audit_id: str
    packet_ref: str
    audited_head: str
    audited_tree: str
    audited_content_digest: str
    base_policy_ref: str
    auditor_requested_identity: str
    auditor_configured_identity: str
    auditor_response_claimed_identity: str
    auditor_proxy_reported_identity: str
    auditor_provider_attested_identity: str
    independence: Independence
    verdict: AuditVerdict
    audit_result_digest: str
    observed_at: str
    finding_refs: Sequence[str] = ()
    risk_refs: Sequence[str] = ()
    packet_digest: str | None = None
    policy_digest: str | None = None
    included_paths_digest: str | None = None
    excluded_proof_only_paths: Sequence[str] = ()

    def __post_init__(self) -> None:
        _require_text(self.audit_id, "audit_id")
        _require_text(self.audited_head, "audited_head")
        _require_text(self.audited_tree, "audited_tree")
        _require_text(self.audited_content_digest, "audited_content_digest")
        _require_text(self.audit_result_digest, "audit_result_digest")

    @property
    def is_acceptable(self) -> bool:
        return self.verdict in {AuditVerdict.PASS, AuditVerdict.PASS_WITH_RISKS}

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_CONTENT_AUDIT_BINDING,
            "audit_id": self.audit_id,
            "packet_ref": self.packet_ref,
            "packet_digest": self.packet_digest,
            "policy_digest": self.policy_digest,
            "audited_head": self.audited_head,
            "audited_tree": self.audited_tree,
            "audited_content_digest": self.audited_content_digest,
            "included_paths_digest": self.included_paths_digest,
            "excluded_proof_only_paths": list(self.excluded_proof_only_paths),
            "base_policy_ref": self.base_policy_ref,
            "auditor_requested_identity": self.auditor_requested_identity,
            "auditor_configured_identity": self.auditor_configured_identity,
            "auditor_response_claimed_identity": self.auditor_response_claimed_identity,
            "auditor_proxy_reported_identity": self.auditor_proxy_reported_identity,
            "auditor_provider_attested_identity": self.auditor_provider_attested_identity,
            "independence": self.independence.value,
            "verdict": self.verdict.value,
            "finding_refs": list(self.finding_refs),
            "risk_refs": list(self.risk_refs),
            "audit_result_digest": self.audit_result_digest,
            "observed_at": self.observed_at,
        }


@dataclass(frozen=True)
class OperatorDecisionRequest:
    """Requests authority. Creating one grants nothing."""

    decision_request_id: str
    decision_type: DecisionType
    identity: Identity
    work_item_id: str
    packet_ref: str
    exact_subject_ref: str
    decision_required_from: str
    current_state: str
    recommended_action: str
    evidence_refs: Sequence[EvidenceReference] = ()
    blockers: Sequence[str] = ()
    risks: Sequence[str] = ()
    unknowns: Sequence[str] = ()
    alternatives: Sequence[str] = ()
    consequences: Sequence[str] = ()
    stop_conditions: Sequence[str] = ()
    expires_at: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.decision_request_id, "decision_request_id")
        _require_text(self.decision_required_from, "decision_required_from")
        _require_text(self.recommended_action, "recommended_action")

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_OPERATOR_DECISION_REQUEST,
            "decision_request_id": self.decision_request_id,
            "decision_type": self.decision_type.value,
            "project_id": self.identity.project_id,
            "repository_id": self.identity.repository_id,
            "work_item_id": self.work_item_id,
            "packet_ref": self.packet_ref,
            "exact_subject_ref": self.exact_subject_ref,
            "decision_required_from": self.decision_required_from,
            "current_state": self.current_state,
            "evidence_refs": [ref.as_dict() for ref in self.evidence_refs],
            "blockers": list(self.blockers),
            "risks": list(self.risks),
            "unknowns": list(self.unknowns),
            "recommended_action": self.recommended_action,
            "alternatives": list(self.alternatives),
            "consequences": list(self.consequences),
            "expires_at": self.expires_at,
            "stop_conditions": list(self.stop_conditions),
        }


def normalized_class_for_branch(branch_id: str) -> NormalizedFailureClass:
    """Map a census failure branch id to its class. Unknown fails closed."""
    entry = FAILURE_BRANCH_CENSUS.get(branch_id)
    if entry is None:
        raise Denial(
            NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
            f"unknown failure branch {branch_id!r}",
        )
    return entry[1]


def envelope_kind_for_event(event_type: str) -> EnvelopeKind:
    """Map a census message class to its envelope kind. Unknown fails closed."""
    kind = MESSAGE_CLASS_CENSUS.get(event_type)
    if kind is None:
        raise Denial(
            NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
            f"unknown message class {event_type!r}",
        )
    return kind
