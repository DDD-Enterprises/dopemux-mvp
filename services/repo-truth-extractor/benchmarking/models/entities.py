from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from .enums import (
    BundleType,
    ContractGateStrength,
    DecisionOutcome,
    DecisionType,
    RecommendationState,
    SurfaceClass,
)
from .ids import utc_now_iso


def _normalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return {key: _normalize(val) for key, val in asdict(value).items() if val is not None}
    if isinstance(value, dict):
        return {str(key): _normalize(val) for key, val in value.items() if val is not None}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    return value


@dataclass(frozen=True)
class BenchmarkModel:
    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        return {key: _normalize(value) for key, value in payload.items() if value is not None}


@dataclass(frozen=True)
class VersionedRecord(BenchmarkModel):
    created_at_utc: str = field(default_factory=utc_now_iso)
    created_by: str = "codex"
    source_ref: str = "synthetic_smoke"
    notes: list[str] = field(default_factory=list)
    supersedes_id: str | None = None


@dataclass(frozen=True)
class ProviderSurface(VersionedRecord):
    surface_id: str = ""
    surface_class: SurfaceClass = SurfaceClass.DIRECT_PROVIDER_API
    provider_name: str = ""
    transport_kind: str = ""
    endpoint_ref: str = ""
    logging_posture: str = ""
    residency_posture: str = ""
    surface_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "surface_class", SurfaceClass.coerce(self.surface_class))


@dataclass(frozen=True)
class ModelRecord(VersionedRecord):
    model_key: str = ""
    display_name: str = ""
    family: str = ""
    source_registry_ref: str = ""
    registry_class: str = ""
    lifecycle_status: str = ""
    content_hash: str = ""


@dataclass(frozen=True)
class RouteRecord(VersionedRecord):
    route_id: str = ""
    surface_id: str = ""
    model_key: str = ""
    provider_model_id: str = ""
    api_key_ref: str = ""
    route_pin: str = ""
    strict_json_schema_declared: bool = False
    strict_passthrough_verified: bool = False
    route_hash: str = ""
    content_hash: str = ""


@dataclass(frozen=True)
class ContractSnapshot(VersionedRecord):
    contract_snapshot_id: str = ""
    runtime_version: str = ""
    contract_version: str = ""
    source_files: list[str] = field(default_factory=list)
    content_hashes: dict[str, str] = field(default_factory=dict)
    strict_schema_expected: bool = True
    snapshot_hash: str = ""
    content_hash: str = ""


@dataclass(frozen=True)
class ValidatorSuite(VersionedRecord):
    validator_suite_id: str = ""
    surface_scope: list[str] = field(default_factory=list)
    validators: list[str] = field(default_factory=list)
    strength_class: str = ""
    contract_rigor: str = ""
    source_files: list[str] = field(default_factory=list)
    content_hashes: dict[str, str] = field(default_factory=dict)
    version_hash: str = ""
    content_hash: str = ""


@dataclass(frozen=True)
class ControlAnchorGroup(VersionedRecord):
    anchor_group_id: str = ""
    surface_class: SurfaceClass = SurfaceClass.DIRECT_PROVIDER_API
    archetype_id: str = ""
    route_ids: list[str] = field(default_factory=list)
    candidate_route_ids: list[str] = field(default_factory=list)
    required: bool = True
    content_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "surface_class", SurfaceClass.coerce(self.surface_class))


@dataclass(frozen=True)
class Archetype(VersionedRecord):
    archetype_id: str = ""
    description: str = ""
    phase_families: list[str] = field(default_factory=list)
    success_rubric_id: str = ""
    promotion_policy_id: str = ""
    content_hash: str = ""


@dataclass(frozen=True)
class Profile(VersionedRecord):
    profile_id: str = ""
    allowed_surfaces: list[str] = field(default_factory=list)
    allowed_archetypes: list[str] = field(default_factory=list)
    policy_bounds: dict[str, Any] = field(default_factory=dict)
    is_production_profile: bool = False
    content_hash: str = ""


@dataclass(frozen=True)
class RetryPolicy(VersionedRecord):
    retry_policy_id: str = ""
    same_route_rules: list[str] = field(default_factory=list)
    escalation_rules: list[str] = field(default_factory=list)
    max_hops: int = 0
    policy_hash: str = ""
    content_hash: str = ""


@dataclass(frozen=True)
class BenchmarkCase(VersionedRecord):
    case_id: str = ""
    case_version: int = 1
    archetype_id: str = ""
    phase_or_step_family: str = ""
    title: str = ""
    description: str = ""
    prompt_inventory_refs: list[str] = field(default_factory=list)
    surface_scope: list[str] = field(default_factory=list)
    executor_kind: str = ""
    validator_suite_id: str = ""
    golden_evaluator_id: str = ""
    input_bundle_id: str = ""
    contract_snapshot_id: str = ""
    case_tags: list[str] = field(default_factory=list)
    content_hash: str = ""


@dataclass(frozen=True)
class BenchmarkCaseSet(VersionedRecord):
    case_set_id: str = ""
    case_set_version: int = 1
    archetype_id: str = ""
    benchmark_stage: str = ""
    title: str = ""
    case_ids: list[str] = field(default_factory=list)
    control_anchor_group_id: str = ""
    schedule_class: str = ""
    content_hash: str = ""


@dataclass(frozen=True)
class BenchmarkRun(VersionedRecord):
    benchmark_run_id: str = ""
    run_type: str = ""
    trigger_type: str = ""
    trigger_ref: str = ""
    git_commit: str = ""
    runtime_version: str = ""
    contract_snapshot_ids: list[str] = field(default_factory=list)
    status: str = ""
    started_at: str = field(default_factory=utc_now_iso)
    finished_at: str | None = None
    content_hash: str = ""


@dataclass(frozen=True)
class BenchmarkCaseAttempt(VersionedRecord):
    case_attempt_id: str = ""
    benchmark_run_id: str = ""
    case_id: str = ""
    case_version: int = 1
    case_set_id: str = ""
    archetype_id: str = ""
    phase_or_step_family: str = ""
    surface_class: SurfaceClass = SurfaceClass.DIRECT_PROVIDER_API
    surface_id: str = ""
    profile_id: str = ""
    route_id: str = ""
    control_anchor_group_id: str = ""
    runtime_version: str = ""
    contract_version: str = ""
    contract_snapshot_id: str = ""
    schema_id: str = ""
    strict_schema_expected: bool = True
    validator_suite_id: str = ""
    attempt_number: int = 1
    retry_policy_id: str = ""
    temperature_or_equivalent: float = 0.0
    max_tokens_or_budget: int = 0
    tool_mode: str = ""
    batch_mode: str = ""
    contract_gate_pass: bool = False
    contract_gate_strength: ContractGateStrength = ContractGateStrength.STRONG
    contract_fail_reason: str | None = None
    first_pass_valid: bool = False
    structural_failure_classification: str | None = None
    validator_pass: bool = False
    task_success_score: float = 0.0
    task_score_breakdown: dict[str, float] = field(default_factory=dict)
    scoring_policy_id: str | None = None
    scoring_policy_version: str | None = None
    operational_metrics: dict[str, float | int] = field(default_factory=dict)
    repair_invocations: int = 0
    sidefill_invocations: int = 0
    route_hop_total: int = 0
    unknowns_open: list[str] = field(default_factory=list)
    output_artifact_ref: str = ""
    golden_eval_ref: str = ""
    control_delta_ref: str = ""
    evidence_bundle_id: str = ""
    timestamp_utc: str = field(default_factory=utc_now_iso)

    def __post_init__(self) -> None:
        object.__setattr__(self, "surface_class", SurfaceClass.coerce(self.surface_class))
        object.__setattr__(
            self,
            "contract_gate_strength",
            ContractGateStrength.coerce(self.contract_gate_strength),
        )


@dataclass(frozen=True)
class ValidatorResult(VersionedRecord):
    validator_result_id: str = ""
    case_attempt_id: str = ""
    validator_suite_id: str = ""
    validator_name: str = ""
    passed: bool = False
    strength_class: str = ""
    failure_reason: str | None = None
    details_ref: str = ""
    content_hash: str = ""


@dataclass(frozen=True)
class ControlDelta(VersionedRecord):
    control_delta_id: str = ""
    candidate_attempt_id: str = ""
    anchor_attempt_id: str = ""
    metric_name: str = ""
    candidate_value: float = 0.0
    anchor_value: float = 0.0
    delta_value: float = 0.0
    delta_state: str = ""
    content_hash: str = ""


@dataclass(frozen=True)
class EvidenceBundle(VersionedRecord):
    bundle_id: str = ""
    bundle_type: BundleType = BundleType.BENCHMARK_CASE_ATTEMPT
    benchmark_run_id: str = ""
    root_path: str = ""
    manifest_hash: str = ""
    artifact_hashes: dict[str, str] = field(default_factory=dict)
    retention_class: str = ""
    content_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "bundle_type", BundleType.coerce(self.bundle_type))


@dataclass(frozen=True)
class PromotionRecommendation(VersionedRecord):
    recommendation_id: str = ""
    benchmark_run_id: str = ""
    route_id: str = ""
    surface_id: str = ""
    archetype_id: str = ""
    profile_id: str = ""
    runtime_version: str = ""
    contract_version: str = ""
    contract_snapshot_id: str = ""
    freshness_state: str = ""
    dispute_state: str = ""
    recommendation_state: RecommendationState = RecommendationState.NOT_EVALUATED
    failed_gates: list[str] = field(default_factory=list)
    evidence_bundle_ids: list[str] = field(default_factory=list)
    relevant_rollup_ids: list[str] = field(default_factory=list)
    control_delta_summary: dict[str, float | str | int] = field(default_factory=dict)
    required_action: str = ""
    requires_review: bool = True
    content_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "recommendation_state",
            RecommendationState.coerce(self.recommendation_state),
        )


@dataclass(frozen=True)
class GovernanceDecision(VersionedRecord):
    decision_id: str = ""
    recommendation_id: str = ""
    decision_type: DecisionType = DecisionType.DEFER
    decision_outcome: DecisionOutcome = DecisionOutcome.RECORDED
    actor: str = ""
    timestamp: str = field(default_factory=utc_now_iso)
    reason: str = ""
    evidence_bundle_ids: list[str] = field(default_factory=list)
    governance_packet_ref: str | None = None
    required_action: str | None = None
    supersedes_decision_id: str | None = None
    content_hash: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_type", DecisionType.coerce(self.decision_type))
        object.__setattr__(self, "decision_outcome", DecisionOutcome.coerce(self.decision_outcome))


def validate_required_strings(record: BenchmarkModel, names: list[str]) -> None:
    for name in names:
        value = getattr(record, name)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{type(record).__name__}.{name} must be a non-empty string")


def field_names(model_type: type[BenchmarkModel]) -> list[str]:
    return [item.name for item in fields(model_type)]
