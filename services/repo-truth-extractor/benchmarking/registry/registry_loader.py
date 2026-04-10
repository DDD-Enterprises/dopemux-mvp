from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..models.entities import (
    Archetype,
    BenchmarkCase,
    BenchmarkCaseSet,
    ControlAnchorGroup,
    ModelRecord,
    Profile,
    ProviderSurface,
    RetryPolicy,
    RouteRecord,
)
from ..storage.hashing import hash_json
from ..storage.sqlite_repo import BenchmarkCatalogRepo
from .snapshot_capture import SERVICE_ROOT, build_contract_snapshot, build_validator_suite


@dataclass(frozen=True)
class RegistryBundle:
    contract_snapshot: object
    validator_suites: list[object]
    provider_surfaces: list[ProviderSurface]
    models: list[ModelRecord]
    routes: list[RouteRecord]
    archetypes: list[Archetype]
    profiles: list[Profile]
    retry_policies: list[RetryPolicy]
    control_anchor_groups: list[ControlAnchorGroup]
    benchmark_cases: list[BenchmarkCase]
    benchmark_case_sets: list[BenchmarkCaseSet]


def _core_surface_records() -> tuple[list[ProviderSurface], list[ModelRecord], list[RouteRecord]]:
    surfaces = [
        ProviderSurface(
            surface_id="surface_local_fixture_v1",
            surface_class="local_or_open_weight",
            provider_name="local-fixture",
            transport_kind="filesystem_process",
            endpoint_ref="local://benchmark-fixture",
            logging_posture="operator_visible",
            residency_posture="local_only",
            surface_hash=hash_json({"surface_id": "surface_local_fixture_v1"}),
            source_ref="m1_registry_seed",
        ),
        ProviderSurface(
            surface_id="surface_openrouter_api_v1",
            surface_class="openrouter_routed",
            provider_name="openrouter",
            transport_kind="https_json",
            endpoint_ref="https://openrouter.ai/api/v1",
            logging_posture="operator_visible",
            residency_posture="unknown",
            surface_hash=hash_json({"surface_id": "surface_openrouter_api_v1"}),
            source_ref="m1_registry_seed",
        ),
        ProviderSurface(
            surface_id="surface_openai_api_v1",
            surface_class="direct_provider_api",
            provider_name="openai",
            transport_kind="openai_sdk",
            endpoint_ref="https://api.openai.com/v1",
            logging_posture="operator_visible",
            residency_posture="unknown",
            surface_hash=hash_json({"surface_id": "surface_openai_api_v1"}),
            source_ref="m1_registry_seed",
        ),
    ]
    models = [
        ModelRecord(
            model_key="local/benchmark-fixture",
            display_name="Local Benchmark Fixture",
            family="fixture",
            source_registry_ref="benchmark_fixture_registry",
            registry_class="fixture_authority",
            lifecycle_status="candidate",
            content_hash=hash_json({"model_key": "local/benchmark-fixture"}),
            source_ref="m1_registry_seed",
        ),
        ModelRecord(
            model_key="openai/gpt-5.4",
            display_name="GPT-5.4",
            family="gpt-5",
            source_registry_ref="runtime_candidate_registry",
            registry_class="current_state_authority",
            lifecycle_status="candidate",
            content_hash=hash_json({"model_key": "openai/gpt-5.4"}),
            source_ref="m1_registry_seed",
        ),
        ModelRecord(
            model_key="openai/gpt-5.4-mini",
            display_name="GPT-5.4 Mini",
            family="gpt-5",
            source_registry_ref="runtime_candidate_registry",
            registry_class="current_state_authority",
            lifecycle_status="candidate",
            content_hash=hash_json({"model_key": "openai/gpt-5.4-mini"}),
            source_ref="m1_registry_seed",
        ),
    ]
    routes = [
        RouteRecord(
            route_id="route_local_fixture_v1",
            surface_id="surface_local_fixture_v1",
            model_key="local/benchmark-fixture",
            provider_model_id="local/benchmark-fixture",
            api_key_ref="",
            route_pin="local/benchmark-fixture",
            strict_json_schema_declared=True,
            strict_passthrough_verified=True,
            route_hash=hash_json({"route_id": "route_local_fixture_v1"}),
            content_hash=hash_json({"route_id": "route_local_fixture_v1"}),
            source_ref="m1_registry_seed",
        ),
        RouteRecord(
            route_id="route_openrouter_openai_gpt_5_4_v1",
            surface_id="surface_openrouter_api_v1",
            model_key="openai/gpt-5.4",
            provider_model_id="openai/gpt-5.4",
            api_key_ref="OPENROUTER_API_KEY",
            route_pin="openai/gpt-5.4",
            strict_json_schema_declared=True,
            strict_passthrough_verified=False,
            route_hash=hash_json({"route_id": "route_openrouter_openai_gpt_5_4_v1"}),
            content_hash=hash_json({"route_id": "route_openrouter_openai_gpt_5_4_v1"}),
            source_ref="m1_registry_seed",
        ),
        RouteRecord(
            route_id="route_openai_gpt_5_4_v1",
            surface_id="surface_openai_api_v1",
            model_key="openai/gpt-5.4",
            provider_model_id="gpt-5.4",
            api_key_ref="OPENAI_API_KEY",
            route_pin="gpt-5.4",
            strict_json_schema_declared=True,
            strict_passthrough_verified=True,
            route_hash=hash_json({"route_id": "route_openai_gpt_5_4_v1"}),
            content_hash=hash_json({"route_id": "route_openai_gpt_5_4_v1"}),
            source_ref="m1_registry_seed",
        ),
    ]
    return surfaces, models, routes


def build_registry_bundle() -> RegistryBundle:
    contract_snapshot = build_contract_snapshot()
    validator_runtime = build_validator_suite(
        validator_suite_id="validators_runtime_strict_json_v1",
        surface_scope=["direct_provider_api", "openrouter_routed", "local_or_open_weight"],
        validators=["json_schema_shape", "artifact_presence", "strict_contract_gate"],
        strength_class="strong",
        contract_rigor="strict_runtime_v5_with_promptset_v4_split",
        source_paths=[
            SERVICE_ROOT / "run_extraction_v5.py",
            SERVICE_ROOT / "lib" / "structured_output_contracts.py",
            SERVICE_ROOT / "promptsets" / "v4" / "promptset.yaml",
        ],
        notes=["Runtime authority is v5; contract authority may still live under promptsets/v4."],
    )
    validator_phase_s = build_validator_suite(
        validator_suite_id="validators_phase_s_advisory_v1",
        surface_scope=["direct_provider_api", "openrouter_routed", "local_or_open_weight"],
        validators=["phase_s_registry_presence", "synthesis_contract_lint"],
        strength_class="moderate",
        contract_rigor="phase_s_weaker_contract_caveat",
        source_paths=[
            SERVICE_ROOT / "prompts" / "phase_s" / "registry.json",
            SERVICE_ROOT / "prompts" / "phase_s" / "PROMPT_S11_CONTRACT_LINTER.md",
        ],
        notes=["phase_s may require weaker contract rigor than FL_INT."],
    )
    validator_fl_int = build_validator_suite(
        validator_suite_id="validators_fl_int_schema_v1",
        surface_scope=["direct_provider_api", "openrouter_routed", "local_or_open_weight"],
        validators=["fl_int_input_schema", "artifact_presence"],
        strength_class="strong",
        contract_rigor="schema_driven_fl_int",
        source_paths=[
            SERVICE_ROOT / "fl_int" / "schema_input.json",
            SERVICE_ROOT / "run_fl_int.py",
        ],
        notes=["FL_INT snapshot is schema-driven rather than prompt-only."],
    )
    validator_prescan = build_validator_suite(
        validator_suite_id="validators_prescan_repo_reasoning_v1",
        surface_scope=["direct_provider_api", "openrouter_routed", "local_or_open_weight"],
        validators=["prescan_inventory_shape", "repo_reasoning_contract"],
        strength_class="moderate",
        contract_rigor="mixed_code_and_schema_driven",
        source_paths=[
            SERVICE_ROOT / "run_prescan.py",
            SERVICE_ROOT / "lib" / "prescan" / "models.py",
        ],
        notes=["Prescan is partly code/schema-driven rather than prompt-only."],
    )

    surfaces, models, routes = _core_surface_records()
    archetypes = [
        Archetype(
            archetype_id="prescan_routing_assessment",
            description="Prescan and routing classification",
            phase_families=["prescan"],
            success_rubric_id="rubric_prescan_v1",
            promotion_policy_id="policy_manual_review_only",
            content_hash=hash_json({"archetype_id": "prescan_routing_assessment"}),
            source_ref="m1_registry_seed",
        ),
        Archetype(
            archetype_id="strict_evidence_extraction",
            description="Strict extraction and contract conformance",
            phase_families=["D_C_G_X"],
            success_rubric_id="rubric_strict_v1",
            promotion_policy_id="policy_manual_review_only",
            content_hash=hash_json({"archetype_id": "strict_evidence_extraction"}),
            source_ref="m1_registry_seed",
        ),
        Archetype(
            archetype_id="repair_merge_normalization",
            description="Repair and merge normalization path",
            phase_families=["H_Q"],
            success_rubric_id="rubric_repair_v1",
            promotion_policy_id="policy_manual_review_only",
            content_hash=hash_json({"archetype_id": "repair_merge_normalization"}),
            source_ref="m1_registry_seed",
        ),
        Archetype(
            archetype_id="adjudication_governance",
            description="Adjudication and conflict ruling",
            phase_families=["R_G"],
            success_rubric_id="rubric_adjudication_v1",
            promotion_policy_id="policy_manual_review_only",
            content_hash=hash_json({"archetype_id": "adjudication_governance"}),
            source_ref="m1_registry_seed",
        ),
        Archetype(
            archetype_id="output_shaping_contract",
            description="Output shaping and contract formatting",
            phase_families=["FL_INT"],
            success_rubric_id="rubric_output_v1",
            promotion_policy_id="policy_manual_review_only",
            content_hash=hash_json({"archetype_id": "output_shaping_contract"}),
            source_ref="m1_registry_seed",
        ),
        Archetype(
            archetype_id="tool_aware_repo_reasoning",
            description="Tool-aware repository reasoning",
            phase_families=["prescan_phase_s"],
            success_rubric_id="rubric_tool_repo_v1",
            promotion_policy_id="policy_manual_review_only",
            content_hash=hash_json({"archetype_id": "tool_aware_repo_reasoning"}),
            source_ref="m1_registry_seed",
        ),
    ]
    profiles = [
        Profile(
            profile_id="balanced_production",
            allowed_surfaces=["direct_provider_api", "openrouter_routed"],
            allowed_archetypes=[item.archetype_id for item in archetypes],
            policy_bounds={"local_or_open_weight": "not_production_eligible"},
            is_production_profile=True,
            content_hash=hash_json({"profile_id": "balanced_production"}),
            source_ref="m1_registry_seed",
        ),
        Profile(
            profile_id="governance_pending_review",
            allowed_surfaces=["direct_provider_api", "openrouter_routed"],
            allowed_archetypes=[
                "strict_evidence_extraction",
                "adjudication_governance",
                "tool_aware_repo_reasoning",
            ],
            policy_bounds={
                "governance_posture": "unresolved",
                "local_or_open_weight": "not_production_eligible",
            },
            is_production_profile=True,
            content_hash=hash_json({"profile_id": "governance_pending_review"}),
            source_ref="m1_registry_seed",
            notes=["Used by S1 hardening fixtures to exercise unresolved governance posture."],
        ),
        Profile(
            profile_id="benchmark_local_validation",
            allowed_surfaces=["local_or_open_weight"],
            allowed_archetypes=[item.archetype_id for item in archetypes],
            policy_bounds={"local_or_open_weight": "not_production_eligible"},
            is_production_profile=False,
            content_hash=hash_json({"profile_id": "benchmark_local_validation"}),
            source_ref="m1_registry_seed",
        ),
    ]
    retry_policies = [
        RetryPolicy(
            retry_policy_id="retry_ladder_structural_fail_closed_v1",
            same_route_rules=["same_surface_only", "fail_closed"],
            escalation_rules=["no_live_calls_in_m1"],
            max_hops=1,
            policy_hash=hash_json({"retry_policy_id": "retry_ladder_structural_fail_closed_v1"}),
            content_hash=hash_json({"retry_policy_id": "retry_ladder_structural_fail_closed_v1"}),
            source_ref="m1_registry_seed",
        ),
        RetryPolicy(
            retry_policy_id="retry_anchor_mismatch_v1",
            same_route_rules=["same_surface_only", "manual_fixture_override"],
            escalation_rules=["used_only_for_s1_control_anchor_mismatch"],
            max_hops=1,
            policy_hash=hash_json({"retry_policy_id": "retry_anchor_mismatch_v1"}),
            content_hash=hash_json({"retry_policy_id": "retry_anchor_mismatch_v1"}),
            source_ref="s1_hardening_seed",
            notes=["Used by S1 hardening fixtures to force comparable-control-anchor mismatch without bypassing foreign keys."],
        ),
    ]
    control_anchor_groups = [
        ControlAnchorGroup(
            anchor_group_id="anchor_openrouter_strict_v1",
            surface_class="openrouter_routed",
            archetype_id="strict_evidence_extraction",
            route_ids=["route_openrouter_openai_gpt_5_4_v1"],
            candidate_route_ids=[],
            required=True,
            content_hash=hash_json({"anchor_group_id": "anchor_openrouter_strict_v1"}),
            source_ref="m1_registry_seed",
            notes=["Control anchors remain separate from candidate routes."],
        ),
        ControlAnchorGroup(
            anchor_group_id="anchor_openai_general_v1",
            surface_class="direct_provider_api",
            archetype_id="tool_aware_repo_reasoning",
            route_ids=["route_openai_gpt_5_4_v1"],
            candidate_route_ids=[],
            required=True,
            content_hash=hash_json({"anchor_group_id": "anchor_openai_general_v1"}),
            source_ref="m1_registry_seed",
            notes=["Surface isolation is explicit at the anchor-group level."],
        ),
        ControlAnchorGroup(
            anchor_group_id="anchor_local_fixture_v1",
            surface_class="local_or_open_weight",
            archetype_id="tool_aware_repo_reasoning",
            route_ids=["route_local_fixture_v1"],
            candidate_route_ids=[],
            required=True,
            content_hash=hash_json({"anchor_group_id": "anchor_local_fixture_v1"}),
            source_ref="m1_registry_seed",
            notes=["Local/open-weight fixture routes are stored explicitly and are not production-eligible by default."],
        ),
    ]
    cases = [
        BenchmarkCase(
            case_id="prescan_route_inventory_v1",
            case_version=1,
            archetype_id="prescan_routing_assessment",
            phase_or_step_family="prescan",
            title="Prescan route inventory",
            description="Classify route/provider surfaces without collapsing surface boundaries.",
            prompt_inventory_refs=["services/repo-truth-extractor/run_prescan.py"],
            surface_scope=["local_or_open_weight"],
            executor_kind="prescan_adapter",
            validator_suite_id=validator_prescan.validator_suite_id,
            golden_evaluator_id="golden_prescan_inventory_v1",
            input_bundle_id="input_bundle_prescan_route_inventory_v1",
            contract_snapshot_id=contract_snapshot.contract_snapshot_id,
            case_tags=["prescan", "routing", "metadata_is_not_proof"],
            content_hash=hash_json({"case_id": "prescan_route_inventory_v1"}),
            source_ref="m1_registry_seed",
        ),
        BenchmarkCase(
            case_id="strict_extract_conflicting_evidence_v1",
            case_version=1,
            archetype_id="strict_evidence_extraction",
            phase_or_step_family="D_C_G_X",
            title="Strict extract conflicting evidence",
            description="Exercise strict extraction with runtime-v5 and contract-v4 kept separate.",
            prompt_inventory_refs=["services/repo-truth-extractor/promptsets/v4/promptset.yaml"],
            surface_scope=["openrouter_routed"],
            executor_kind="runtime_v5_adapter",
            validator_suite_id=validator_runtime.validator_suite_id,
            golden_evaluator_id="golden_strict_extract_v1",
            input_bundle_id="input_bundle_strict_extract_v1",
            contract_snapshot_id=contract_snapshot.contract_snapshot_id,
            case_tags=["strict", "evidence", "runtime_contract_split"],
            content_hash=hash_json({"case_id": "strict_extract_conflicting_evidence_v1"}),
            source_ref="m1_registry_seed",
        ),
        BenchmarkCase(
            case_id="repair_merge_conflict_normalization_v1",
            case_version=1,
            archetype_id="repair_merge_normalization",
            phase_or_step_family="H_Q",
            title="Repair merge conflict normalization",
            description="Exercise repair/merge style contract normalization without execution.",
            prompt_inventory_refs=["services/repo-truth-extractor/prompts/phase_s/PROMPT_S11_CONTRACT_LINTER.md"],
            surface_scope=["local_or_open_weight"],
            executor_kind="phase_s_adapter",
            validator_suite_id=validator_phase_s.validator_suite_id,
            golden_evaluator_id="golden_repair_merge_v1",
            input_bundle_id="input_bundle_repair_merge_v1",
            contract_snapshot_id=contract_snapshot.contract_snapshot_id,
            case_tags=["repair", "merge", "normalization"],
            content_hash=hash_json({"case_id": "repair_merge_conflict_normalization_v1"}),
            source_ref="m1_registry_seed",
        ),
        BenchmarkCase(
            case_id="adjudication_conflict_ruling_v1",
            case_version=1,
            archetype_id="adjudication_governance",
            phase_or_step_family="R_G",
            title="Adjudication conflict ruling",
            description="Exercise adjudication packet structure and ruling boundaries.",
            prompt_inventory_refs=["audit_prep/prompt4_benchmark_system_architecture.md"],
            surface_scope=["direct_provider_api", "openrouter_routed"],
            executor_kind="phase_s_adapter",
            validator_suite_id=validator_phase_s.validator_suite_id,
            golden_evaluator_id="golden_adjudication_v1",
            input_bundle_id="input_bundle_adjudication_v1",
            contract_snapshot_id=contract_snapshot.contract_snapshot_id,
            case_tags=["adjudication", "governance", "conflict"],
            content_hash=hash_json({"case_id": "adjudication_conflict_ruling_v1"}),
            source_ref="m1_registry_seed",
        ),
        BenchmarkCase(
            case_id="fl_int_output_shaping_v1",
            case_version=1,
            archetype_id="output_shaping_contract",
            phase_or_step_family="FL_INT",
            title="FL_INT output shaping",
            description="Exercise output shaping against FL_INT schema-driven contracts.",
            prompt_inventory_refs=["services/repo-truth-extractor/fl_int/schema_input.json"],
            surface_scope=["local_or_open_weight"],
            executor_kind="fl_int_adapter",
            validator_suite_id=validator_fl_int.validator_suite_id,
            golden_evaluator_id="golden_fl_int_output_v1",
            input_bundle_id="input_bundle_fl_int_output_v1",
            contract_snapshot_id=contract_snapshot.contract_snapshot_id,
            case_tags=["fl_int", "output", "schema_driven"],
            content_hash=hash_json({"case_id": "fl_int_output_shaping_v1"}),
            source_ref="m1_registry_seed",
        ),
        BenchmarkCase(
            case_id="tool_aware_repo_reasoning_v1",
            case_version=1,
            archetype_id="tool_aware_repo_reasoning",
            phase_or_step_family="prescan_phase_s",
            title="Tool-aware repo reasoning",
            description="Exercise repo reasoning with explicit tool-aware and phase_s caveat handling.",
            prompt_inventory_refs=[
                "services/repo-truth-extractor/run_prescan.py",
                "services/repo-truth-extractor/prompts/phase_s/registry.json",
            ],
            surface_scope=["direct_provider_api"],
            executor_kind="prescan_adapter",
            validator_suite_id=validator_prescan.validator_suite_id,
            golden_evaluator_id="golden_tool_repo_v1",
            input_bundle_id="input_bundle_tool_repo_v1",
            contract_snapshot_id=contract_snapshot.contract_snapshot_id,
            case_tags=["tool_aware", "repo_reasoning", "phase_s_caveat"],
            content_hash=hash_json({"case_id": "tool_aware_repo_reasoning_v1"}),
            source_ref="m1_registry_seed",
        ),
    ]
    case_sets = [
        BenchmarkCaseSet(
            case_set_id="benchmark_registry_starter_v1",
            case_set_version=1,
            archetype_id="tool_aware_repo_reasoning",
            benchmark_stage="registry_seed",
            title="Benchmark registry starter set",
            case_ids=[case.case_id for case in cases],
            control_anchor_group_id="anchor_openai_general_v1",
            schedule_class="manual_seed",
            content_hash=hash_json({"case_set_id": "benchmark_registry_starter_v1"}),
            source_ref="m1_registry_seed",
        ),
        BenchmarkCaseSet(
            case_set_id="strict_extract_weekly_v1",
            case_set_version=1,
            archetype_id="strict_evidence_extraction",
            benchmark_stage="admission_smoke",
            title="Strict extract weekly",
            case_ids=["strict_extract_conflicting_evidence_v1"],
            control_anchor_group_id="anchor_openrouter_strict_v1",
            schedule_class="manual_smoke",
            content_hash=hash_json({"case_set_id": "strict_extract_weekly_v1"}),
            source_ref="m1_registry_seed",
        ),
    ]
    return RegistryBundle(
        contract_snapshot=contract_snapshot,
        validator_suites=[validator_runtime, validator_phase_s, validator_fl_int, validator_prescan],
        provider_surfaces=surfaces,
        models=models,
        routes=routes,
        archetypes=archetypes,
        profiles=profiles,
        retry_policies=retry_policies,
        control_anchor_groups=control_anchor_groups,
        benchmark_cases=cases,
        benchmark_case_sets=case_sets,
    )


def seed_registry(repo: BenchmarkCatalogRepo) -> RegistryBundle:
    bundle = build_registry_bundle()
    repo.insert_contract_snapshot(bundle.contract_snapshot)
    for validator_suite in bundle.validator_suites:
        repo.insert_validator_suite(validator_suite)
    for surface in bundle.provider_surfaces:
        repo.insert_provider_surface(surface)
    for model in bundle.models:
        repo.insert_model(model)
    for route in bundle.routes:
        repo.insert_route(route)
    for archetype in bundle.archetypes:
        repo.insert_archetype(archetype)
    for profile in bundle.profiles:
        repo.insert_profile(profile)
    for retry_policy in bundle.retry_policies:
        repo.insert_retry_policy(retry_policy)
    for anchor_group in bundle.control_anchor_groups:
        repo.insert_control_anchor_group(anchor_group)
    for case in bundle.benchmark_cases:
        repo.insert_benchmark_case(case)
    for case_set in bundle.benchmark_case_sets:
        repo.insert_benchmark_case_set(case_set)
    return bundle
