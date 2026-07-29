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
from dopemux.dcp.routing_backend_policy import (
    BackendPolicyRecommendation,
    BackendPolicyRule,
    explain_backend_policy,
    select_backend_policy,
)
from dopemux.dcp.lane_model import (
    LaneDecision,
    LaneKind,
)
from dopemux.dcp.lane_engine import (
    decide_lane,
)
from dopemux.dcp.runner_capability_registry import (
    CapabilityRegistryError,
    RunnerCapability,
    RunnerCapabilityRegistry,
    assert_no_invocation_authorized,
    load_runner_capabilities,
)
from dopemux.dcp.runner_contract import (
    RunnerContractDocument,
    RunnerContractError,
    RunnerInvocationPlan,
    RunnerPlanStatus,
    RunnerProofEnvelope,
    RunnerResult,
    build_blocked_plan,
    document_plan,
    execute_runner_plan,
)
from dopemux.dcp.trusted_adapter_registry import (
    AdapterRecord,
    RegistryError,
    TrustedAdapterRegistry,
    assert_no_mutation_adapters,
    listed_adapter_ids,
    load_registry,
)
from dopemux.dcp.input_adapters import (
    TrustedInputCapability,
    TrustedInputError,
    active_trusted_adapters,
    capability_from_any,
    is_execution_eligible,
    refuse_serialized_trust,
    untrusted_classify_source,
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
    # Backend policy recommendations (DMX-DCP-MODEL-ROUTING-MVP-0003)
    "BackendPolicyRecommendation",
    "BackendPolicyRule",
    "explain_backend_policy",
    "select_backend_policy",
    # Lane model + engine (DMX-DCP-MODEL-ROUTING-MVP-0005)
    "LaneDecision",
    "LaneKind",
    "decide_lane",
    # Trusted-input capability boundary (DMX-DCP-MODEL-ROUTING-MVP-0007I)
    "TrustedInputCapability",
    "TrustedInputError",
    "active_trusted_adapters",
    "capability_from_any",
    "is_execution_eligible",
    "refuse_serialized_trust",
    "untrusted_classify_source",
    # Trusted adapter registry (0007A)
    "AdapterRecord",
    "RegistryError",
    "TrustedAdapterRegistry",
    "assert_no_mutation_adapters",
    "listed_adapter_ids",
    "load_registry",
    # Runner contract (0008)
    "RunnerContractDocument",
    "RunnerContractError",
    "RunnerInvocationPlan",
    "RunnerPlanStatus",
    "RunnerProofEnvelope",
    "RunnerResult",
    "build_blocked_plan",
    "document_plan",
    "execute_runner_plan",
    # Runner capability registry (0009)
    "CapabilityRegistryError",
    "RunnerCapability",
    "RunnerCapabilityRegistry",
    "assert_no_invocation_authorized",
    "load_runner_capabilities",
]
