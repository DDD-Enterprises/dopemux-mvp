"""Ownership evidence evaluation (P1 fleet control plane).

Combines registry, lease, service-family-probe, and storage/mount evidence
into one closed classification. Labels and probes never independently prove
ownership -- see
``docs/90-adr/adr-dmx-mcp-multiproject-identity-sharing-contract-001.md`` S6
and ``schemas/mcp/ownership-evidence.schema.json``.

``mutation_eligible=True`` requires all four evidence classes verified. Every
other combination denies, differentiated only for operator legibility:
FOREIGN (a definite negative signal -- wrong project/instance), AMBIGUOUS
(partial or circumstantial positive evidence), or UNKNOWN (no meaningful
evidence either way).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

SCHEMA_VERSION = "dopemux.mcp.ownership-evidence.v1"

CLASSIFICATIONS = ("OWNED", "FOREIGN", "AMBIGUOUS", "UNKNOWN")

# docker_inspect.classify_container_ownership() label_status values that
# count as a definite negative signal or circumstantial positive signal.
# Corroboration only -- never sufficient by themselves for OWNED.
_CIRCUMSTANTIAL_LABEL_STATUSES = frozenset({"COMPOSE_MATCH", "MATCH"})
_NEGATIVE_LABEL_STATUS = "WRONG_PROJECT"


@dataclass(frozen=True)
class RegistryEvidence:
    verified: bool
    project_id: Optional[str] = None
    registry_generation: Optional[int] = None

    def to_schema_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"verified": self.verified}
        if self.project_id is not None:
            out["project_id"] = self.project_id
        if self.registry_generation is not None:
            out["registry_generation"] = self.registry_generation
        return out


@dataclass(frozen=True)
class LeaseEvidence:
    verified: bool
    lease_id: Optional[str] = None

    def to_schema_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"verified": self.verified}
        if self.lease_id is not None:
            out["lease_id"] = self.lease_id
        return out


@dataclass(frozen=True)
class ProbeEvidence:
    verified: bool
    service_family: Optional[str] = None

    def to_schema_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"verified": self.verified}
        if self.service_family is not None:
            out["service_family"] = self.service_family
        return out


@dataclass(frozen=True)
class StorageEvidence:
    verified: bool
    evidence: Optional[str] = None

    def to_schema_dict(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {"verified": self.verified}
        if self.evidence is not None:
            out["evidence"] = self.evidence
        return out


@dataclass(frozen=True)
class OwnershipEvidence:
    classification: str
    mutation_eligible: bool
    registry: Optional[RegistryEvidence] = None
    lease: Optional[LeaseEvidence] = None
    probe: Optional[ProbeEvidence] = None
    storage: Optional[StorageEvidence] = None

    def to_schema_dict(self) -> Dict[str, Any]:
        """Render exactly the shape
        ``schemas/mcp/ownership-evidence.schema.json`` requires. Each
        sub-block's identifying field (``project_id``, ``lease_id``,
        ``service_family``, ``evidence``) is required by the schema whenever
        that block is present at all -- not only when verified=True -- so a
        block whose identifying field is unknown is omitted entirely rather
        than emitted with a placeholder."""

        out: Dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "classification": self.classification,
            "mutation_eligible": self.mutation_eligible,
        }
        if self.registry is not None and self.registry.project_id is not None and self.registry.registry_generation is not None:
            out["registry"] = self.registry.to_schema_dict()
        if self.lease is not None and self.lease.lease_id is not None:
            out["lease"] = self.lease.to_schema_dict()
        if self.probe is not None and self.probe.service_family is not None:
            out["probe"] = self.probe.to_schema_dict()
        if self.storage is not None and self.storage.evidence is not None:
            out["storage"] = self.storage.to_schema_dict()
        return out


def evaluate_ownership(
    *,
    registry: RegistryEvidence,
    lease: LeaseEvidence,
    probe: ProbeEvidence,
    storage: StorageEvidence,
    label_status: Optional[str] = None,
) -> OwnershipEvidence:
    """Fail-closed ownership classification.

    ``label_status`` is the corroborating output of
    ``docker_inspect.classify_container_ownership`` (or ``None`` if no
    container evidence was gathered). It can only push a classification
    toward FOREIGN (a definite negative) or AMBIGUOUS (a circumstantial
    positive); it can never make a candidate OWNED by itself.
    """

    verified_count = sum(
        (registry.verified, lease.verified, probe.verified, storage.verified)
    )

    if verified_count == 4:
        if (
            registry.project_id is None
            or registry.registry_generation is None
            or lease.lease_id is None
            or probe.service_family is None
            or storage.evidence is None
        ):
            raise ValueError(
                "OWNED requires every evidence class's identifying field populated "
                "(registry.project_id/registry_generation, lease.lease_id, "
                "probe.service_family, storage.evidence) -- schema requires them "
                "whenever the block is present"
            )
        return OwnershipEvidence(
            classification="OWNED",
            mutation_eligible=True,
            registry=registry,
            lease=lease,
            probe=probe,
            storage=storage,
        )

    if label_status == _NEGATIVE_LABEL_STATUS:
        return OwnershipEvidence(
            classification="FOREIGN",
            mutation_eligible=False,
            registry=registry,
            lease=lease,
            probe=probe,
            storage=storage,
        )

    circumstantial = label_status in _CIRCUMSTANTIAL_LABEL_STATUSES
    if verified_count >= 2 or circumstantial:
        return OwnershipEvidence(
            classification="AMBIGUOUS",
            mutation_eligible=False,
            registry=registry,
            lease=lease,
            probe=probe,
            storage=storage,
        )

    return OwnershipEvidence(
        classification="UNKNOWN",
        mutation_eligible=False,
        registry=registry,
        lease=lease,
        probe=probe,
        storage=storage,
    )
