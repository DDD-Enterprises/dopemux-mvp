"""Local DCP proof artifact readers and routing domain model."""

from dopemux.dcp.proof_family import (
    ArtifactInspection,
    AuthorityLabel,
    FieldObservation,
    FreshnessStatus,
    LiveWriteReadyStatus,
    LiveWriteStatus,
    MergeSeamStatus,
    ProofFamily,
    classify_artifact,
)
from dopemux.dcp.proof_pointer_reader import read_proof_pointer
from dopemux.dcp.control_snapshot import (
    SnapshotBlocked,
    generate_control_snapshot,
    write_control_snapshot,
)
from dopemux.dcp.routing_model import (
    AuditRequirement,
    AuthorityClass,
    BackendKind,
    ComplexityClass,
    ConnectorKind,
    EscalationRequirement,
    ProofRequirement,
    RedLaneState,
    RiskClass,
    RouteDecision,
    RouteStatus,
    RuntimeImpact,
    TaskSource,
    TaskType,
)
from dopemux.dcp.routing_classifier import (
    RoutingClassificationInput,
    classify_route,
)

__all__ = [
    # Proof artifact readers (pre-existing)
    "ArtifactInspection",
    "AuthorityLabel",
    "FieldObservation",
    "FreshnessStatus",
    "LiveWriteReadyStatus",
    "LiveWriteStatus",
    "MergeSeamStatus",
    "ProofFamily",
    "SnapshotBlocked",
    "classify_artifact",
    "generate_control_snapshot",
    "read_proof_pointer",
    "write_control_snapshot",
    # Routing domain model (DMX-DCP-MODEL-ROUTING-MVP-0001R)
    "AuditRequirement",
    "AuthorityClass",
    "BackendKind",
    "ComplexityClass",
    "ConnectorKind",
    "EscalationRequirement",
    "ProofRequirement",
    "RedLaneState",
    "RiskClass",
    "RouteDecision",
    "RouteStatus",
    "RuntimeImpact",
    "TaskSource",
    "TaskType",
    # Routing classification engine (DMX-DCP-MODEL-ROUTING-MVP-0002)
    "RoutingClassificationInput",
    "classify_route",
]
