"""UAG semantic-core enumerations.

Pure value enums for the provider-neutral Universal Agent Gateway semantic core.
Mirrors the ratified C0-R2 `common_defs.schema.json` value spaces. No I/O, no
execution authority, no provider coupling.
"""

from __future__ import annotations

from enum import Enum


class IdentityStageName(str, Enum):
    """Ordered identity-resolution stages for a logical request.

    Stages must remain distinct; identity collapse across stages is forbidden
    by design (see ``identity.py``). The reported stages carry no authority.
    """

    REQUESTED = "requested"
    CONFIGURED = "configured"
    POLICY_RESOLVED = "policy_resolved"
    UAG_RESOLVED = "uag_resolved"
    ATTEMPTED = "attempted"
    GATEWAY_REPORTED = "gateway_reported"
    PROXY_REPORTED = "proxy_reported"
    PROVIDER_REPORTED = "provider_reported"
    PROVIDER_ATTESTED = "provider_attested"


class EvidenceStatus(str, Enum):
    """Provenance quality of an identity-stage or unknown-item record."""

    OBSERVED = "OBSERVED"
    HISTORICALLY_RECORDED = "HISTORICALLY_RECORDED"
    CLAIMED = "CLAIMED"
    INFERRED = "INFERRED"
    CONFLICTING = "CONFLICTING"
    UNKNOWN = "UNKNOWN"
    NOT_RUN = "NOT_RUN"


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class AttemptSemanticState(str, Enum):
    """Semantic attempt state space (C0-R2 ``attemptSemanticState``).

    ``SENT_ACCEPTANCE_UNKNOWN`` is NOT retry-safe; the core never invents
    retry or fallback semantics from it.
    """

    NOT_SENT = "NOT_SENT"
    NON_ACCEPTANCE_PROVEN = "NON_ACCEPTANCE_PROVEN"
    SENT_ACCEPTANCE_UNKNOWN = "SENT_ACCEPTANCE_UNKNOWN"
    ACCEPTED_NO_OUTPUT = "ACCEPTED_NO_OUTPUT"
    OUTPUT_STARTED = "OUTPUT_STARTED"
    PRIVATE_STATE_EMITTED = "PRIVATE_STATE_EMITTED"
    TOOL_INTENT_EMITTED = "TOOL_INTENT_EMITTED"
    EXTERNAL_SIDE_EFFECT_POSSIBLE = "EXTERNAL_SIDE_EFFECT_POSSIBLE"
    EXTERNAL_SIDE_EFFECT_CONFIRMED = "EXTERNAL_SIDE_EFFECT_CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCEL_REQUESTED_TERMINATION_UNKNOWN = "CANCEL_REQUESTED_TERMINATION_UNKNOWN"


class OutputContractClass(str, Enum):
    """Requested output contract class (three-lane IR selector)."""

    PUBLIC_TEXT = "PUBLIC_TEXT"
    TYPED_FAMILY_ENVELOPE = "TYPED_FAMILY_ENVELOPE"
    TOOL_INTENT_ONLY = "TOOL_INTENT_ONLY"
    MIXED = "MIXED"


class CompatibilityStatus(str, Enum):
    """Compatibility-registry status. Runtime UAG may not self-promote to VERIFIED."""

    VERIFIED = "VERIFIED"
    VERIFIED_WITH_TRANSFORMATION = "VERIFIED_WITH_TRANSFORMATION"
    DEGRADED = "DEGRADED"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class SemanticLossClass(str, Enum):
    EXACT = "EXACT"
    EQUIVALENT_BY_PROFILE = "EQUIVALENT_BY_PROFILE"
    NARROWING = "NARROWING"
    MODEL_ONLY_SUPERSET_REQUIRES_CANONICAL_REVALIDATION = (
        "MODEL_ONLY_SUPERSET_REQUIRES_CANONICAL_REVALIDATION"
    )
    LOSSY = "LOSSY"
    UNREPRESENTABLE = "UNREPRESENTABLE"
    UNKNOWN = "UNKNOWN"


class AttestationClass(str, Enum):
    """Provider attestation class. V1 permits only ABSENT or UNKNOWN.

    CRYPTOGRAPHIC_PROVIDER_ATTESTATION is deferred and rejected in V1.
    """

    ABSENT = "ABSENT"
    UNKNOWN = "UNKNOWN"


class PrivateStateReplayScope(str, Enum):
    """Private-state replay scope. V1 has no cross-restart read path."""

    PROCESS_LIFETIME_ONLY = "PROCESS_LIFETIME_ONLY"
    NONE = "NONE"


class ExecutionAuthority(str, Enum):
    """Authority value. The semantic core only ever carries NONE."""

    NONE = "NONE"
