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

# The default ``policy.required_gate_set`` of architecture section 05: every
# gate class is required until policy says otherwise. Default-deny is the point
# — GOV-AUD-003 was that an omitted gate silently read as "not a problem", so a
# lane that genuinely does not need a gate must say so with an explicit
# NOT_APPLICABLE entry rather than by leaving the ledger short.
DEFAULT_REQUIRED_GATE_CLASSES: tuple[str, ...] = GATE_CLASSES

# The isolation dimensions, in the order they are reported.
IDENTITY_DIMENSIONS: tuple[str, ...] = (
    "project_id",
    "repository_id",
    "workspace_id",
    "worktree_id",
    "instance_id",
    "packet_id",
)

# Immutable G0 identity profile. Callers may not narrow it.
G0_REQUIRED_IDENTITY_DIMENSIONS: tuple[str, ...] = (
    "project_id",
    "repository_id",
    "worktree_id",
    "packet_id",
)


class FactBasis(str, Enum):
    """How a structural fact came to be believed.

    GOV-AUD-002: a caller-supplied boolean is an assertion, not evidence. Only
    ``OBSERVED_GIT`` — computed by the deterministic observer from git objects —
    may support a PASS. ``CLAIMED_INPUT`` is retained rather than rejected
    outright so that a claim is visible in the receipt as a claim.
    """

    OBSERVED_GIT = "OBSERVED_GIT"
    CLAIMED_INPUT = "CLAIMED_INPUT"
    UNKNOWN = "UNKNOWN"


# The six structural conjuncts of architecture section 08, verbatim. The seventh
# (no_new_finding_or_acceptance_criterion) is the semantic field comparison and
# the eighth (equivalence_validator_passes) is the conjunction itself, so
# neither is a separately observed fact.
STRUCTURAL_CONJUNCTS: tuple[str, ...] = (
    "current_head_descends_from_or_is_patch_equivalent_to_audited_head",
    "actual_changed_paths_subset_of_allowed_proof_only_paths",
    "raw_diff_contains_no_substantive_source_change",
    "audited_content_tree_equal_under_exclusion",
    "packet_and_policy_digests_unchanged",
    "audit_result_bytes_unchanged",
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


@dataclass
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


_GIT_OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_SHA256_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _require_git_oid(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not _GIT_OID_RE.fullmatch(value):
        raise Denial(
            NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
            f"{field_name} must be a complete 40- or 64-hex git object id",
        )
    return value


def _require_sha256_digest(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not _SHA256_DIGEST_RE.fullmatch(value):
        raise Denial(
            NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
            f"{field_name} must be a sha256 digest",
        )
    return value


def _require_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise Denial(
            NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
            f"{field_name} must be an object",
        )
    return value


def _require_sequence(value: Any, field_name: str) -> Sequence[Any]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise Denial(
            NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
            f"{field_name} must be an array",
        )
    return value


def _require_text_sequence(value: Any, field_name: str) -> list[str]:
    items = _require_sequence(value, field_name)
    result: list[str] = []
    for index, item in enumerate(items):
        if not isinstance(item, str):
            raise Denial(
                NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
                f"{field_name}[{index}] must be a string",
            )
        result.append(item)
    return result


def _require_keys(
    raw: Mapping[str, Any], *, required: Sequence[str], allowed: Sequence[str], contract: str
) -> None:
    missing = sorted(set(required) - set(raw))
    extra = sorted(set(raw) - set(allowed))
    if missing or extra:
        details = []
        if missing:
            details.append("missing=" + ",".join(missing))
        if extra:
            details.append("forbidden=" + ",".join(extra))
        raise Denial(
            NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
            f"{contract} key contract violated: {'; '.join(details)}",
        )


@dataclass(frozen=True)
class StructuralFacts:
    """The structural inputs to proof-only equivalence, each with its basis.

    Produced by ``snapshot.observe_proof_only_facts`` from read-only git, or —
    when a caller supplies raw values — carrying ``CLAIMED_INPUT`` bases that
    can never reach PASS. ``observation_digest`` lets a later auditor re-run the
    observer and compare rather than take the receipt's word.
    """

    ancestry_established: bool = False
    actual_changed_paths: Sequence[str] = ()
    raw_diff_digest: str = ""
    content_tree_equivalent_under_exclusion: bool = False
    audited_packet_digest: str | None = None
    successor_packet_digest: str | None = None
    audited_policy_digest: str | None = None
    successor_policy_digest: str | None = None
    audited_audit_result_digest: str | None = None
    successor_audit_result_digest: str | None = None
    basis: Mapping[str, FactBasis] = field(default_factory=dict, init=False, repr=False)
    merge_base: str | None = None
    observer_version: str | None = None
    observation_digest: str | None = None
    absent_named_paths: Sequence[str] = ()

    def __post_init__(self) -> None:
        for name in self.basis:
            if name not in STRUCTURAL_CONJUNCTS:
                raise Denial(
                    NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
                    f"{name!r} is not a declared structural conjunct",
                )

    def basis_for(self, conjunct: str) -> FactBasis:
        """An undeclared basis is UNKNOWN, never optimistically OBSERVED."""
        return self.basis.get(conjunct, FactBasis.UNKNOWN)

    @classmethod
    def claimed(cls, **values: Any) -> "StructuralFacts":
        """Caller-asserted facts. Every basis is CLAIMED_INPUT, so PASS is unreachable."""
        instance = cls(**values)
        object.__setattr__(
            instance,
            "basis",
            {name: FactBasis.CLAIMED_INPUT for name in STRUCTURAL_CONJUNCTS},
        )
        return instance

    @classmethod
    def _from_git_observer(cls, **values: Any) -> "StructuralFacts":
        """Internal observer/test constructor; audit reuse remains disabled in G0."""
        basis = values.pop("basis")
        instance = cls(**values)
        object.__setattr__(instance, "basis", dict(basis))
        instance.__post_init__()
        return instance


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
        for name in G0_REQUIRED_IDENTITY_DIMENSIONS:
            _require_known_identity(getattr(self, name), name)
        for name in ("workspace_id", "instance_id"):
            value = getattr(self, name)
            if value is not None:
                _require_known_identity(value, name)

    def conflicts_with(self, other: "Identity") -> str | None:
        """Return the first conflicting dimension, or None when compatible.

        A dimension present on both sides must match exactly. Absence is handled
        by ``missing_dimensions`` rather than here: silently treating an absent
        dimension as compatible is what GOV-AUD-004 identified as a wildcard, so
        presence is a separate, explicitly required check.
        """
        for name in IDENTITY_DIMENSIONS:
            mine = getattr(self, name)
            theirs = getattr(other, name)
            if mine is not None and theirs is not None and mine != theirs:
                return name
        return None

    def missing_dimensions(
        self, other: "Identity", required: Sequence[str]
    ) -> list[str]:
        """Return the required dimensions not bound on *both* sides.

        Absence is not compatibility. A reduction that declares a dimension
        applicable must see it bound on both the expected and the offered
        identity, otherwise the unbound side is an unconstrained wildcard.
        """
        missing: list[str] = []
        for name in required:
            if name not in IDENTITY_DIMENSIONS:
                raise Denial(
                    NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
                    f"{name!r} is not a known identity dimension",
                )
            if getattr(self, name) is None or getattr(other, name) is None:
                missing.append(name)
        return missing

    def require_compatible(
        self,
        other: "Identity",
        *,
        context: str,
        required_dimensions: Sequence[str] = (),
    ) -> None:
        """Deny on a conflicting dimension, or on an unbound required dimension."""
        conflict = self.conflicts_with(other)
        if conflict is not None:
            raise Denial(
                NormalizedFailureClass.SCOPE_OR_CONTAINMENT_VIOLATION,
                f"{context}: {conflict} mismatch "
                f"({getattr(self, conflict)!r} vs {getattr(other, conflict)!r})",
            )
        missing = self.missing_dimensions(other, required_dimensions)
        if missing:
            raise Denial(
                NormalizedFailureClass.SCOPE_OR_CONTAINMENT_VIOLATION,
                f"{context}: required identity dimension(s) {', '.join(missing)} "
                "are not bound on both sides; absence is not compatibility",
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


def applicable_dimensions(identity: Identity) -> tuple[str, ...]:
    """Immutable G0 required profile; optional dimensions never weaken it.

    ``workspace_id`` and ``instance_id`` remain optional. ``conflicts_with``
    still denies either when both sides provide different values.
    """
    return G0_REQUIRED_IDENTITY_DIMENSIONS


@dataclass(frozen=True)
class Subject:
    """Git subject binding. Preserved in full so head and tree never blur."""

    base_sha: str | None = None
    head_sha: str | None = None
    tree_sha: str | None = None
    content_digest: str | None = None

    def __post_init__(self) -> None:
        for name in ("base_sha", "head_sha", "tree_sha"):
            value = getattr(self, name)
            if value is not None:
                _require_git_oid(value, name)
        if self.content_digest is not None:
            _require_sha256_digest(self.content_digest, "content_digest")

    def as_dict(self) -> dict[str, Any]:
        return {
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
            "tree_sha": self.tree_sha,
            "content_digest": self.content_digest,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Subject":
        raw = _require_mapping(raw, "subject")
        _require_keys(
            raw,
            required=("base_sha", "head_sha", "tree_sha", "content_digest"),
            allowed=("base_sha", "head_sha", "tree_sha", "content_digest"),
            contract="Subject",
        )
        return cls(
            base_sha=raw["base_sha"],
            head_sha=raw["head_sha"],
            tree_sha=raw["tree_sha"],
            content_digest=raw["content_digest"],
        )


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
        if self.tombstone is not None and not isinstance(self.tombstone, bool):
            raise Denial(
                NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
                "tombstone must be boolean or null",
            )

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
        raw = _require_mapping(raw, "EvidenceReference")
        allowed = (
            "schema_version",
            "evidence_id",
            "evidence_class",
            "owner_system",
            "producer_identity",
            "canonical_location",
            "digest_or_signature",
            *IDENTITY_DIMENSIONS,
            "base_sha",
            "head_sha",
            "tree_sha",
            "content_digest",
            "schema_version_used",
            "policy_version",
            "tool_version",
            "environment_digest",
            "observed_at",
            "valid_until",
            "freshness_state",
            "supersedes",
            "tombstone",
            "authority_effect",
        )
        _require_keys(
            raw,
            required=(
                "schema_version",
                "evidence_id",
                "evidence_class",
                "owner_system",
                "producer_identity",
                "canonical_location",
                "digest_or_signature",
                *G0_REQUIRED_IDENTITY_DIMENSIONS,
                "observed_at",
                "freshness_state",
                "authority_effect",
            ),
            allowed=allowed,
            contract="EvidenceReference",
        )
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
        if not isinstance(self.mutation_authorized, bool) or self.mutation_authorized:
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
        required = applicable_dimensions(self.identity)
        for ref in self.evidence_refs:
            self.identity.require_compatible(
                ref.identity,
                context=f"envelope {self.envelope_id} evidence {ref.evidence_id}",
                required_dimensions=required,
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_ENVELOPE,
            "envelope_id": self.envelope_id,
            "kind": self.kind.value,
            "event_type": self.event_type,
            "project_id": self.identity.project_id,
            "repository_id": self.identity.repository_id,
            "workspace_id": self.identity.workspace_id,
            "worktree_id": self.identity.worktree_id,
            "instance_id": self.identity.instance_id,
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

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "GovernedDeliveryEnvelope":
        raw = _require_mapping(raw, "GovernedDeliveryEnvelope")
        allowed = (
            "schema_version",
            "envelope_id",
            "kind",
            "event_type",
            *IDENTITY_DIMENSIONS,
            "work_item_id",
            "producer",
            "consumer",
            "created_at",
            "subject_ref",
            "evidence_refs",
            "idempotency_key",
            "payload_schema",
            "payload",
            "authority_effect",
            "mutation_authorized",
        )
        _require_keys(
            raw,
            required=(
                "schema_version",
                "envelope_id",
                "kind",
                "event_type",
                *G0_REQUIRED_IDENTITY_DIMENSIONS,
                "producer",
                "consumer",
                "created_at",
                "subject_ref",
                "evidence_refs",
                "idempotency_key",
                "payload_schema",
                "payload",
            ),
            allowed=allowed,
            contract="GovernedDeliveryEnvelope",
        )
        _require_schema_version(raw["schema_version"], SCHEMA_ENVELOPE)
        evidence_items = _require_sequence(raw["evidence_refs"], "evidence_refs")
        payload = _require_mapping(raw["payload"], "payload")
        return cls(
            envelope_id=raw["envelope_id"],
            kind=_require_enum(raw["kind"], EnvelopeKind, "kind"),
            event_type=raw["event_type"],
            identity=Identity(
                project_id=raw["project_id"],
                repository_id=raw["repository_id"],
                workspace_id=raw.get("workspace_id"),
                worktree_id=raw["worktree_id"],
                instance_id=raw.get("instance_id"),
                packet_id=raw["packet_id"],
            ),
            work_item_id=raw.get("work_item_id"),
            producer=raw["producer"],
            consumer=raw["consumer"],
            created_at=raw["created_at"],
            subject_ref=raw["subject_ref"],
            evidence_refs=[EvidenceReference.from_dict(item) for item in evidence_items],
            idempotency_key=raw["idempotency_key"],
            payload_schema=raw["payload_schema"],
            payload=payload,
            authority_effect=_require_enum(
                raw.get("authority_effect", "NONE"), AuthorityEffect, "authority_effect"
            ),
            mutation_authorized=raw.get("mutation_authorized", False),
        )


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
        _require_text(self.subject_digest_or_head, "subject_digest_or_head")
        _require_text(self.producer_identity, "producer_identity")
        _require_text(self.reason, "reason")
        parse_instant(self.observed_at, field_name="observed_at")
        if self.valid_until is not None:
            parse_instant(self.valid_until, field_name="valid_until")
        if self.gate_class not in GATE_CLASSES:
            raise Denial(
                NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
                f"unknown gate_class {self.gate_class!r}",
            )

    @staticmethod
    def state_blocks(state: GateState) -> bool:
        """UNKNOWN and CONFLICTING fail closed alongside the overt blockers."""
        return state in {
            GateState.UNSATISFIED,
            GateState.STALE,
            GateState.BLOCKED,
            GateState.UNKNOWN,
            GateState.CONFLICTING,
            GateState.PENDING,
        }

    @property
    def blocks_consequential_action(self) -> bool:
        return self.state_blocks(self.state)

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

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "GateEntry":
        raw = _require_mapping(raw, "GateEntry")
        allowed = (
            "gate_id",
            "gate_class",
            "state",
            "policy_owner",
            "policy_version",
            "evidence_refs",
            "subject_digest_or_head",
            "producer_identity",
            "observed_at",
            "valid_until",
            "blocking_actions",
            "reason",
        )
        _require_keys(
            raw,
            required=(
                "gate_id",
                "gate_class",
                "state",
                "policy_owner",
                "policy_version",
                "evidence_refs",
                "subject_digest_or_head",
                "producer_identity",
                "observed_at",
                "blocking_actions",
                "reason",
            ),
            allowed=allowed,
            contract="GateEntry",
        )
        return cls(
            gate_id=raw["gate_id"],
            gate_class=raw["gate_class"],
            state=_require_enum(raw["state"], GateState, "state"),
            policy_owner=raw["policy_owner"],
            policy_version=raw["policy_version"],
            evidence_refs=[
                EvidenceReference.from_dict(item)
                for item in _require_sequence(raw["evidence_refs"], "evidence_refs")
            ],
            subject_digest_or_head=raw["subject_digest_or_head"],
            producer_identity=raw["producer_identity"],
            observed_at=raw["observed_at"],
            valid_until=raw.get("valid_until"),
            blocking_actions=_require_text_sequence(
                raw["blocking_actions"], "blocking_actions"
            ),
            reason=raw["reason"],
        )


@dataclass(frozen=True)
class GateLedger:
    ledger_id: str
    identity: Identity
    subject_digest_or_head: str
    gates: Sequence[GateEntry] = ()
    risk_lane: str | None = None
    policy_digest: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.ledger_id, "ledger_id")
        _require_text(self.subject_digest_or_head, "subject_digest_or_head")
        if self.policy_digest is not None:
            _require_sha256_digest(self.policy_digest, "policy_digest")

    def blocking_gates(self) -> list[GateEntry]:
        return [gate for gate in self.gates if gate.blocks_consequential_action]

    def states_by_class(self) -> dict[str, GateState]:
        """Most-blocking state per gate class.

        Two entries for one class must not let the satisfied one mask the other,
        so the ledger reports the blocking state when the class carries both.
        """
        states: dict[str, GateState] = {}
        for gate in self.gates:
            existing = states.get(gate.gate_class)
            if existing is None or (
                gate.blocks_consequential_action
                and not GateEntry.state_blocks(existing)
            ):
                states[gate.gate_class] = gate.state
        return states

    def missing_required_classes(self) -> list[str]:
        """Required gate classes with no entry at all. GOV-AUD-003."""
        present = {gate.gate_class for gate in self.gates}
        return [name for name in GATE_CLASSES if name not in present]

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_GATE_LEDGER,
            "ledger_id": self.ledger_id,
            "project_id": self.identity.project_id,
            "repository_id": self.identity.repository_id,
            "workspace_id": self.identity.workspace_id,
            "worktree_id": self.identity.worktree_id,
            "instance_id": self.identity.instance_id,
            "packet_id": self.identity.packet_id,
            "subject_digest_or_head": self.subject_digest_or_head,
            "policy": {
                "risk_lane": self.risk_lane,
                "policy_digest": self.policy_digest,
            },
            "missing_required_gate_classes": self.missing_required_classes(),
            "gates": [gate.as_dict() for gate in self.gates],
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "GateLedger":
        raw = _require_mapping(raw, "GateLedger")
        allowed = (
            "schema_version",
            "ledger_id",
            *IDENTITY_DIMENSIONS,
            "subject_digest_or_head",
            "policy",
            "missing_required_gate_classes",
            "gates",
        )
        _require_keys(
            raw,
            required=(
                "schema_version",
                "ledger_id",
                *G0_REQUIRED_IDENTITY_DIMENSIONS,
                "subject_digest_or_head",
                "policy",
                "missing_required_gate_classes",
                "gates",
            ),
            allowed=allowed,
            contract="GateLedger",
        )
        _require_schema_version(raw["schema_version"], SCHEMA_GATE_LEDGER)
        policy = _require_mapping(raw["policy"], "policy")
        _require_keys(
            policy,
            required=("risk_lane", "policy_digest"),
            allowed=("risk_lane", "policy_digest"),
            contract="GateLedger.policy",
        )
        ledger = cls(
            ledger_id=raw["ledger_id"],
            identity=Identity(
                project_id=raw["project_id"],
                repository_id=raw["repository_id"],
                workspace_id=raw.get("workspace_id"),
                worktree_id=raw["worktree_id"],
                instance_id=raw.get("instance_id"),
                packet_id=raw["packet_id"],
            ),
            subject_digest_or_head=raw["subject_digest_or_head"],
            gates=[
                GateEntry.from_dict(item)
                for item in _require_sequence(raw["gates"], "gates")
            ],
            risk_lane=policy.get("risk_lane"),
            policy_digest=policy.get("policy_digest"),
        )
        declared_missing = _require_text_sequence(
            raw["missing_required_gate_classes"], "missing_required_gate_classes"
        )
        if declared_missing != ledger.missing_required_classes():
            raise Denial(
                NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
                "missing_required_gate_classes does not match fixed G0 gate evaluation",
            )
        return ledger


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

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "Blocker":
        raw = _require_mapping(raw, "Blocker")
        _require_keys(
            raw,
            required=("blocker_id", "normalized_class", "statement"),
            allowed=("blocker_id", "normalized_class", "statement", "evidence_ref"),
            contract="Blocker",
        )
        return cls(
            blocker_id=_require_text(raw["blocker_id"], "blocker_id"),
            normalized_class=_require_enum(
                raw["normalized_class"], NormalizedFailureClass, "normalized_class"
            ),
            statement=_require_text(raw["statement"], "statement"),
            evidence_ref=raw.get("evidence_ref"),
        )


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

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "NativeStateRef":
        raw = _require_mapping(raw, "NativeStateRef")
        _require_keys(
            raw,
            required=("subsystem", "native_state"),
            allowed=("subsystem", "native_state", "evidence_ref"),
            contract="NativeStateRef",
        )
        return cls(
            subsystem=_require_text(raw["subsystem"], "subsystem"),
            native_state=_require_text(raw["native_state"], "native_state"),
            evidence_ref=raw.get("evidence_ref"),
        )


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

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "NextLegalAction":
        raw = _require_mapping(raw, "NextLegalAction")
        _require_keys(
            raw,
            required=(
                "action_type",
                "actor_class",
                "authority_ref",
                "prerequisites",
                "dispatch_eligible",
            ),
            allowed=(
                "action_type",
                "actor_class",
                "authority_ref",
                "prerequisites",
                "dispatch_eligible",
            ),
            contract="NextLegalAction",
        )
        if raw["dispatch_eligible"] is not False:
            raise Denial(
                NormalizedFailureClass.SECURITY_OR_TRUST_INCIDENT,
                "dispatch_eligible must remain false in G0",
            )
        return cls(
            action_type=_require_text(raw["action_type"], "action_type"),
            actor_class=_require_text(raw["actor_class"], "actor_class"),
            authority_ref=raw["authority_ref"],
            prerequisites=_require_text_sequence(raw["prerequisites"], "prerequisites"),
        )


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
    gate_profile_complete: bool = False
    audit_binding_acceptable: bool = False
    audit_binding_ref: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.projection_id, "projection_id")
        _require_text(self.work_item_id, "work_item_id")
        parse_instant(self.updated_at, field_name="updated_at")
        if not isinstance(self.gate_profile_complete, bool) or not isinstance(
            self.audit_binding_acceptable, bool
        ):
            raise Denial(
                NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
                "readiness evidence flags must be booleans",
            )
        if self.packet_ref != self.identity.packet_id:
            raise Denial(
                NormalizedFailureClass.SCOPE_OR_CONTAINMENT_VIOLATION,
                "packet_ref must match fixed G0 packet_id",
            )
        if self.posture is Posture.READY:
            if self.blockers:
                raise Denial(
                    NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
                    "READY projection cannot carry blockers",
                )
            if not self.gate_profile_complete or not self.audit_binding_acceptable:
                raise Denial(
                    NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
                    "READY requires complete fixed gates and exact audit binding",
                )
            _require_text(self.audit_binding_ref, "audit_binding_ref")

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
            "packet_id": self.identity.packet_id,
            "packet_ref": self.packet_ref,
            "subject": self.subject.as_dict(),
            "phase": self.phase.value,
            "posture": self.posture.value,
            "native_state_refs": [ref.as_dict() for ref in self.native_state_refs],
            "gate_ledger_ref": self.gate_ledger_ref,
            "evidence_refs": [ref.as_dict() for ref in self.evidence_refs],
            "blockers": [blocker.as_dict() for blocker in self.blockers],
            "next_legal_action": self.next_legal_action.as_dict(),
            "gate_profile_complete": self.gate_profile_complete,
            "audit_binding_acceptable": self.audit_binding_acceptable,
            "audit_binding_ref": self.audit_binding_ref,
            "updated_at": self.updated_at,
        }
        body["projection_digest"] = digest_of(body)
        return body

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "WorkItemProjection":
        raw = _require_mapping(raw, "WorkItemProjection")
        allowed = (
            "schema_version",
            "projection_id",
            "work_item_id",
            *IDENTITY_DIMENSIONS,
            "packet_ref",
            "subject",
            "phase",
            "posture",
            "native_state_refs",
            "gate_ledger_ref",
            "evidence_refs",
            "blockers",
            "next_legal_action",
            "gate_profile_complete",
            "audit_binding_acceptable",
            "audit_binding_ref",
            "updated_at",
            "projection_digest",
        )
        _require_keys(
            raw,
            required=(
                "schema_version",
                "projection_id",
                "work_item_id",
                *G0_REQUIRED_IDENTITY_DIMENSIONS,
                "packet_ref",
                "subject",
                "phase",
                "posture",
                "native_state_refs",
                "evidence_refs",
                "blockers",
                "next_legal_action",
                "gate_profile_complete",
                "audit_binding_acceptable",
                "audit_binding_ref",
                "updated_at",
                "projection_digest",
            ),
            allowed=allowed,
            contract="WorkItemProjection",
        )
        _require_schema_version(raw["schema_version"], SCHEMA_WORK_ITEM_PROJECTION)
        projection = cls(
            projection_id=raw["projection_id"],
            work_item_id=raw["work_item_id"],
            identity=Identity(
                project_id=raw["project_id"],
                repository_id=raw["repository_id"],
                workspace_id=raw.get("workspace_id"),
                worktree_id=raw["worktree_id"],
                instance_id=raw.get("instance_id"),
                packet_id=raw["packet_id"],
            ),
            subject=Subject.from_dict(raw["subject"]),
            phase=_require_enum(raw["phase"], Phase, "phase"),
            posture=_require_enum(raw["posture"], Posture, "posture"),
            next_legal_action=NextLegalAction.from_dict(raw["next_legal_action"]),
            updated_at=raw["updated_at"],
            native_state_refs=[
                NativeStateRef.from_dict(item)
                for item in _require_sequence(raw["native_state_refs"], "native_state_refs")
            ],
            evidence_refs=[
                EvidenceReference.from_dict(item)
                for item in _require_sequence(raw["evidence_refs"], "evidence_refs")
            ],
            blockers=[
                Blocker.from_dict(item)
                for item in _require_sequence(raw["blockers"], "blockers")
            ],
            gate_ledger_ref=raw.get("gate_ledger_ref"),
            packet_ref=raw["packet_ref"],
            gate_profile_complete=raw["gate_profile_complete"],
            audit_binding_acceptable=raw["audit_binding_acceptable"],
            audit_binding_ref=raw["audit_binding_ref"],
        )
        if raw["projection_digest"] != projection.as_dict()["projection_digest"]:
            raise Denial(
                NormalizedFailureClass.INVALID_INPUT_OR_ARTIFACT,
                "projection_digest does not match canonical projection bytes",
            )
        return projection


@dataclass(frozen=True)
class ContentAuditBinding:
    """Represents a supplied audit result. Never invokes an auditor."""

    audit_id: str
    packet_ref: str
    packet_digest: str
    policy_digest: str
    audited_head: str
    audited_tree: str
    audited_content_digest: str
    included_paths_digest: str
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
    excluded_proof_only_paths: Sequence[str] = ()

    def __post_init__(self) -> None:
        _require_text(self.audit_id, "audit_id")
        _require_text(self.packet_ref, "packet_ref")
        _require_git_oid(self.audited_head, "audited_head")
        _require_git_oid(self.audited_tree, "audited_tree")
        _require_sha256_digest(self.audited_content_digest, "audited_content_digest")
        _require_sha256_digest(self.packet_digest, "packet_digest")
        _require_sha256_digest(self.policy_digest, "policy_digest")
        _require_sha256_digest(self.included_paths_digest, "included_paths_digest")
        _require_sha256_digest(self.audit_result_digest, "audit_result_digest")
        _require_text(self.base_policy_ref, "base_policy_ref")
        for name in (
            "auditor_requested_identity",
            "auditor_configured_identity",
            "auditor_response_claimed_identity",
            "auditor_proxy_reported_identity",
            "auditor_provider_attested_identity",
        ):
            _require_text(getattr(self, name), name)
        parse_instant(self.observed_at, field_name="observed_at")

    def is_acceptable_for(
        self,
        *,
        subject: Subject,
        packet_ref: str,
        packet_digest: str | None,
        policy_digest: str | None,
    ) -> bool:
        """Exact-subject acceptance predicate; verdict alone carries no authority."""
        return all(
            (
                self.verdict in {AuditVerdict.PASS, AuditVerdict.PASS_WITH_RISKS},
                self.independence in {Independence.PROVEN, Independence.LIMITED},
                self.audited_head == subject.head_sha,
                self.audited_tree == subject.tree_sha,
                self.audited_content_digest == subject.content_digest,
                self.packet_ref == packet_ref,
                packet_digest is not None and self.packet_digest == packet_digest,
                policy_digest is not None and self.policy_digest == policy_digest,
                self.auditor_configured_identity.strip().upper() != "UNKNOWN",
                self.auditor_response_claimed_identity.strip().upper() != "UNKNOWN",
                bool(self.audit_result_digest),
            )
        )

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

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ContentAuditBinding":
        raw = _require_mapping(raw, "ContentAuditBinding")
        allowed = (
            "schema_version",
            "audit_id",
            "packet_ref",
            "packet_digest",
            "policy_digest",
            "audited_head",
            "audited_tree",
            "audited_content_digest",
            "included_paths_digest",
            "excluded_proof_only_paths",
            "base_policy_ref",
            "auditor_requested_identity",
            "auditor_configured_identity",
            "auditor_response_claimed_identity",
            "auditor_proxy_reported_identity",
            "auditor_provider_attested_identity",
            "independence",
            "verdict",
            "finding_refs",
            "risk_refs",
            "audit_result_digest",
            "observed_at",
        )
        _require_keys(
            raw,
            required=allowed,
            allowed=allowed,
            contract="ContentAuditBinding",
        )
        _require_schema_version(raw["schema_version"], SCHEMA_CONTENT_AUDIT_BINDING)
        return cls(
            audit_id=raw["audit_id"],
            packet_ref=raw["packet_ref"],
            packet_digest=raw["packet_digest"],
            policy_digest=raw["policy_digest"],
            audited_head=raw["audited_head"],
            audited_tree=raw["audited_tree"],
            audited_content_digest=raw["audited_content_digest"],
            included_paths_digest=raw["included_paths_digest"],
            excluded_proof_only_paths=_require_text_sequence(
                raw["excluded_proof_only_paths"], "excluded_proof_only_paths"
            ),
            base_policy_ref=raw["base_policy_ref"],
            auditor_requested_identity=raw["auditor_requested_identity"],
            auditor_configured_identity=raw["auditor_configured_identity"],
            auditor_response_claimed_identity=raw["auditor_response_claimed_identity"],
            auditor_proxy_reported_identity=raw["auditor_proxy_reported_identity"],
            auditor_provider_attested_identity=raw["auditor_provider_attested_identity"],
            independence=_require_enum(raw["independence"], Independence, "independence"),
            verdict=_require_enum(raw["verdict"], AuditVerdict, "verdict"),
            finding_refs=_require_text_sequence(raw["finding_refs"], "finding_refs"),
            risk_refs=_require_text_sequence(raw["risk_refs"], "risk_refs"),
            audit_result_digest=raw["audit_result_digest"],
            observed_at=raw["observed_at"],
        )


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
        for name in (
            "decision_request_id",
            "work_item_id",
            "packet_ref",
            "exact_subject_ref",
            "decision_required_from",
            "current_state",
            "recommended_action",
        ):
            _require_text(getattr(self, name), name)
        if self.packet_ref != self.identity.packet_id:
            raise Denial(
                NormalizedFailureClass.SCOPE_OR_CONTAINMENT_VIOLATION,
                "packet_ref must match fixed G0 packet_id",
            )
        if self.expires_at is not None:
            parse_instant(self.expires_at, field_name="expires_at")
        required = applicable_dimensions(self.identity)
        for ref in self.evidence_refs:
            self.identity.require_compatible(
                ref.identity,
                context=f"operator decision {self.decision_request_id} evidence {ref.evidence_id}",
                required_dimensions=required,
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_OPERATOR_DECISION_REQUEST,
            "decision_request_id": self.decision_request_id,
            "decision_type": self.decision_type.value,
            "project_id": self.identity.project_id,
            "repository_id": self.identity.repository_id,
            "workspace_id": self.identity.workspace_id,
            "worktree_id": self.identity.worktree_id,
            "instance_id": self.identity.instance_id,
            "packet_id": self.identity.packet_id,
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

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "OperatorDecisionRequest":
        raw = _require_mapping(raw, "OperatorDecisionRequest")
        allowed = (
            "schema_version",
            "decision_request_id",
            "decision_type",
            *IDENTITY_DIMENSIONS,
            "work_item_id",
            "packet_ref",
            "exact_subject_ref",
            "decision_required_from",
            "current_state",
            "evidence_refs",
            "blockers",
            "risks",
            "unknowns",
            "recommended_action",
            "alternatives",
            "consequences",
            "expires_at",
            "stop_conditions",
        )
        required = tuple(name for name in allowed if name not in {"workspace_id", "instance_id", "expires_at"})
        _require_keys(
            raw,
            required=required,
            allowed=allowed,
            contract="OperatorDecisionRequest",
        )
        _require_schema_version(raw["schema_version"], SCHEMA_OPERATOR_DECISION_REQUEST)
        return cls(
            decision_request_id=raw["decision_request_id"],
            decision_type=_require_enum(raw["decision_type"], DecisionType, "decision_type"),
            identity=Identity(
                project_id=raw["project_id"],
                repository_id=raw["repository_id"],
                workspace_id=raw.get("workspace_id"),
                worktree_id=raw["worktree_id"],
                instance_id=raw.get("instance_id"),
                packet_id=raw["packet_id"],
            ),
            work_item_id=raw["work_item_id"],
            packet_ref=raw["packet_ref"],
            exact_subject_ref=raw["exact_subject_ref"],
            decision_required_from=raw["decision_required_from"],
            current_state=raw["current_state"],
            evidence_refs=[
                EvidenceReference.from_dict(item)
                for item in _require_sequence(raw["evidence_refs"], "evidence_refs")
            ],
            blockers=_require_text_sequence(raw["blockers"], "blockers"),
            risks=_require_text_sequence(raw["risks"], "risks"),
            unknowns=_require_text_sequence(raw["unknowns"], "unknowns"),
            recommended_action=raw["recommended_action"],
            alternatives=_require_text_sequence(raw["alternatives"], "alternatives"),
            consequences=_require_text_sequence(raw["consequences"], "consequences"),
            expires_at=raw.get("expires_at"),
            stop_conditions=_require_text_sequence(raw["stop_conditions"], "stop_conditions"),
        )


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
