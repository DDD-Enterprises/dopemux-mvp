"""UAG semantic-core identity stages.

Identity resolution for a logical request is a strict, ordered set of distinct
stages. UNKNOWN and CONFLICTING are first-class values, never silently coerced
into a resolved identity. Provider attestation is a distinct stage that cannot
be inferred from gateway/proxy/provider self-report.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from dopemux.uag.enums import (
    AttestationClass,
    Confidence,
    EvidenceStatus,
    IdentityStageName,
)


@dataclass(frozen=True)
class IdentityStage:
    """A single observed identity stage (C0-R2 ``identityStage``).

    Frozen: a stage record, once created, cannot be mutated in place. Distinct
    stage names are never collapsed; the caller must carry them separately.
    """

    stage: IdentityStageName
    value: str | None
    source: str
    evidence_status: EvidenceStatus
    confidence: Confidence
    timestamp: str | None = None
    request_correlation_ref: str | None = None
    notes: str | None = None
    attestation_class: AttestationClass | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.stage, IdentityStageName):
            raise ValueError("stage must be an IdentityStageName")
        if not isinstance(self.source, str) or not self.source:
            raise ValueError("source must be a non-empty string")
        if self.stage is IdentityStageName.PROVIDER_ATTESTED:
            if self.attestation_class not in (AttestationClass.ABSENT, AttestationClass.UNKNOWN):
                raise ValueError(
                    "provider_attested requires attestation_class ABSENT or UNKNOWN; "
                    "cryptographic attestation is deferred in V1"
                )
        else:
            # Only the provider_attested stage carries an attestation class.
            if self.attestation_class is not None:
                raise ValueError("attestation_class is only valid on provider_attested")


@dataclass(frozen=True)
class UnknownItem:
    """First-class UNKNOWN marker (C0-R2 ``unknownItem``)."""

    code: str
    description: str
    evidence_status: EvidenceStatus = EvidenceStatus.UNKNOWN

    def __post_init__(self) -> None:
        if not isinstance(self.code, str) or not self.code:
            raise ValueError("UnknownItem.code must be non-empty")
        if not isinstance(self.description, str) or not self.description:
            raise ValueError("UnknownItem.description must be non-empty")
        if not isinstance(self.evidence_status, EvidenceStatus):
            raise ValueError("evidence_status must be an EvidenceStatus")


@dataclass(frozen=True)
class ConflictItem:
    """First-class CONFLICTING marker (C0-R2 ``conflictItem``)."""

    code: str
    left: str
    right: str
    description: str

    def __post_init__(self) -> None:
        for name in ("code", "left", "right", "description"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"ConflictItem.{name} must be non-empty")


@dataclass(frozen=True)
class IdentityChain:
    """Ordered collection of identity-stage records.

    Append-only: ``record`` returns a new chain; the receiver is never mutated.
    Stages are kept distinct; a chain may carry at most one record per stage
    name (the earliest wins, later duplicates are refused rather than rewritten).
    """

    stages: tuple[IdentityStage, ...] = field(default_factory=tuple)

    def record(self, stage: IdentityStage) -> "IdentityChain":
        if not isinstance(stage, IdentityStage):
            raise ValueError("record() expects an IdentityStage")
        for existing in self.stages:
            if existing.stage is stage.stage:
                raise ValueError(
                    f"stage {stage.stage.value} already recorded; identity collapse forbidden"
                )
        return IdentityChain(stages=self.stages + (stage,))

    def get(self, stage: IdentityStageName) -> IdentityStage | None:
        for record in self.stages:
            if record.stage is stage:
                return record
        return None

    @property
    def resolved_identity(self) -> str | None:
        """Return the latest distinct resolution, never a collapsed value.

        Falls back through reported stages only when a true resolution exists;
        returns None (UNKNOWN) when no stage carries a value.
        """
        for stage in (
            IdentityStageName.PROVIDER_ATTESTED,
            IdentityStageName.UAG_RESOLVED,
            IdentityStageName.POLICY_RESOLVED,
            IdentityStageName.CONFIGURED,
            IdentityStageName.REQUESTED,
        ):
            record = self.get(stage)
            if record is not None and record.value is not None:
                return record.value
        return None
