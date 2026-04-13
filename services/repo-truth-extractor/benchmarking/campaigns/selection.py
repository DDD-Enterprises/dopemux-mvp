from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..models.entities import BenchmarkCaseSet, ControlAnchorGroup, ModelRecord, ProviderSurface, RouteRecord
from ..registry.registry_loader import seed_registry
from ..storage.hashing import hash_json
from ..storage.sqlite_repo import BenchmarkCatalogRepo


SERVICE_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class CampaignCandidate:
    route_id: str
    cohort: str
    surface_id: str
    surface_class: str
    provider_name: str
    model_key: str
    provider_model_id: str
    admission_reason: str
    policy_note: str


@dataclass(frozen=True)
class CampaignAssignment:
    candidate: CampaignCandidate
    case_id: str
    archetype_id: str
    profile_id: str
    control_anchor_group_id: str
    live_execution: bool
    phase: str
    repo_root: Path
    routing_override_model: str | None = None
    operator_note: str = ""
    benchmark_route_ownership_mode: str | None = None
    benchmark_route_ownership_scope: str | None = None


@dataclass(frozen=True)
class CampaignPlan:
    campaign_id: str
    case_set_id: str
    contract_snapshot_id: str
    runtime_version: str
    control_candidates: list[CampaignCandidate]
    candidate_candidates: list[CampaignCandidate]
    baseline_assignments: list[CampaignAssignment]
    campaign_assignments: list[CampaignAssignment]
    case_ids: list[str]
    policy_pack_files: list[str]
    repo_root: Path
    notes: list[str]


def ensure_r1_campaign_records(repo: BenchmarkCatalogRepo) -> None:
    if repo.fetch_benchmark_case("strict_extract_conflicting_evidence_v1") is None:
        seed_registry(repo)
    surfaces = [
        ProviderSurface(
            surface_id="surface_gemini_api_v1",
            surface_class="direct_provider_api",
            provider_name="gemini",
            transport_kind="https_json",
            endpoint_ref="https://generativelanguage.googleapis.com",
            logging_posture="operator_visible",
            residency_posture="unknown",
            surface_hash=hash_json({"surface_id": "surface_gemini_api_v1"}),
            source_ref="r1_campaign_seed",
            notes=["R1 direct provider surface for bounded live campaign."],
        ),
        ProviderSurface(
            surface_id="surface_xai_api_v1",
            surface_class="direct_provider_api",
            provider_name="xai",
            transport_kind="openai_sdk",
            endpoint_ref="https://api.x.ai/v1",
            logging_posture="operator_visible",
            residency_posture="unknown",
            surface_hash=hash_json({"surface_id": "surface_xai_api_v1"}),
            source_ref="r1_campaign_seed",
            notes=["R1 direct provider surface for bounded live campaign."],
        ),
    ]
    for record in surfaces:
        repo.insert_provider_surface(record)

    models = [
        ModelRecord(
            model_key="openai/gpt-5.3-codex",
            display_name="GPT-5.3 Codex",
            family="gpt-5",
            source_registry_ref="runtime_candidate_registry",
            registry_class="current_state_authority",
            lifecycle_status="candidate",
            content_hash=hash_json({"model_key": "openai/gpt-5.3-codex"}),
            source_ref="r1_campaign_seed",
        ),
        ModelRecord(
            model_key="gemini/gemini-3.1-pro-preview",
            display_name="Gemini 3.1 Pro Preview",
            family="gemini-3",
            source_registry_ref="runtime_candidate_registry",
            registry_class="current_state_authority",
            lifecycle_status="candidate",
            content_hash=hash_json({"model_key": "gemini/gemini-3.1-pro-preview"}),
            source_ref="r1_campaign_seed",
        ),
        ModelRecord(
            model_key="xai/grok-4.20-beta-0309-reasoning",
            display_name="Grok 4.20 Reasoning",
            family="grok-4",
            source_registry_ref="runtime_candidate_registry",
            registry_class="current_state_authority",
            lifecycle_status="candidate",
            content_hash=hash_json({"model_key": "xai/grok-4.20-beta-0309-reasoning"}),
            source_ref="r1_campaign_seed",
        ),
        ModelRecord(
            model_key="xai/grok-code-fast-1",
            display_name="Grok Code Fast 1",
            family="grok-code",
            source_registry_ref="runtime_candidate_registry",
            registry_class="current_state_authority",
            lifecycle_status="candidate",
            content_hash=hash_json({"model_key": "xai/grok-code-fast-1"}),
            source_ref="r1_campaign_seed",
        ),
    ]
    for record in models:
        repo.insert_model(record)

    routes = [
        RouteRecord(
            route_id="route_openrouter_openai_gpt_5_3_codex_v1",
            surface_id="surface_openrouter_api_v1",
            model_key="openai/gpt-5.3-codex",
            provider_model_id="openai/gpt-5.3-codex",
            api_key_ref="OPENROUTER_API_KEY",
            route_pin="openrouter/openai/gpt-5.3-codex",
            strict_json_schema_declared=True,
            strict_passthrough_verified=False,
            route_hash=hash_json({"route_id": "route_openrouter_openai_gpt_5_3_codex_v1"}),
            content_hash=hash_json({"route_id": "route_openrouter_openai_gpt_5_3_codex_v1"}),
            source_ref="r1_campaign_seed",
        ),
        RouteRecord(
            route_id="route_openai_gpt_5_4_mini_v1",
            surface_id="surface_openai_api_v1",
            model_key="openai/gpt-5.4-mini",
            provider_model_id="gpt-5.4-mini",
            api_key_ref="OPENAI_API_KEY",
            route_pin="openai/gpt-5.4-mini",
            strict_json_schema_declared=True,
            strict_passthrough_verified=True,
            route_hash=hash_json({"route_id": "route_openai_gpt_5_4_mini_v1"}),
            content_hash=hash_json({"route_id": "route_openai_gpt_5_4_mini_v1"}),
            source_ref="r1_campaign_seed",
        ),
        RouteRecord(
            route_id="route_gemini_3_1_pro_preview_v1",
            surface_id="surface_gemini_api_v1",
            model_key="gemini/gemini-3.1-pro-preview",
            provider_model_id="gemini-3.1-pro-preview",
            api_key_ref="GEMINI_API_KEY",
            route_pin="gemini/gemini-3.1-pro-preview",
            strict_json_schema_declared=False,
            strict_passthrough_verified=False,
            route_hash=hash_json({"route_id": "route_gemini_3_1_pro_preview_v1"}),
            content_hash=hash_json({"route_id": "route_gemini_3_1_pro_preview_v1"}),
            source_ref="r1_campaign_seed",
        ),
        RouteRecord(
            route_id="route_xai_grok_4_20_reasoning_v1",
            surface_id="surface_xai_api_v1",
            model_key="xai/grok-4.20-beta-0309-reasoning",
            provider_model_id="grok-4.20-beta-0309-reasoning",
            api_key_ref="XAI_API_KEY",
            route_pin="xai/grok-4.20-beta-0309-reasoning",
            strict_json_schema_declared=False,
            strict_passthrough_verified=False,
            route_hash=hash_json({"route_id": "route_xai_grok_4_20_reasoning_v1"}),
            content_hash=hash_json({"route_id": "route_xai_grok_4_20_reasoning_v1"}),
            source_ref="r1_campaign_seed",
        ),
        RouteRecord(
            route_id="route_xai_grok_code_fast_1_v1",
            surface_id="surface_xai_api_v1",
            model_key="xai/grok-code-fast-1",
            provider_model_id="grok-code-fast-1",
            api_key_ref="XAI_API_KEY",
            route_pin="xai/grok-code-fast-1",
            strict_json_schema_declared=False,
            strict_passthrough_verified=False,
            route_hash=hash_json({"route_id": "route_xai_grok_code_fast_1_v1"}),
            content_hash=hash_json({"route_id": "route_xai_grok_code_fast_1_v1"}),
            source_ref="r1_campaign_seed",
        ),
    ]
    for record in routes:
        repo.insert_route(record)

    repo.insert_control_anchor_group(
        ControlAnchorGroup(
            anchor_group_id="anchor_direct_strict_v1",
            surface_class="direct_provider_api",
            archetype_id="strict_evidence_extraction",
            route_ids=["route_openai_gpt_5_4_v1"],
            candidate_route_ids=[
                "route_openai_gpt_5_4_mini_v1",
                "route_gemini_3_1_pro_preview_v1",
                "route_xai_grok_4_20_reasoning_v1",
                "route_xai_grok_code_fast_1_v1",
            ],
            required=True,
            content_hash=hash_json({"anchor_group_id": "anchor_direct_strict_v1"}),
            source_ref="r1_campaign_seed",
            notes=[
                "R1 direct-provider anchor for bounded strict extraction campaign.",
                "Comparability still requires runtime_version, contract_snapshot_id, validator_suite_id, retry_policy_id, and case_id to match.",
            ],
        )
    )

    repo.insert_benchmark_case_set(
        BenchmarkCaseSet(
            case_set_id="r1_first_campaign_v1",
            case_set_version=1,
            archetype_id="strict_evidence_extraction",
            benchmark_stage="first_real_campaign",
            title="R1 first real bounded candidate campaign",
            case_ids=[
                "strict_extract_conflicting_evidence_v1",
                "tool_aware_repo_reasoning_v1",
            ],
            control_anchor_group_id="anchor_openrouter_strict_v1",
            schedule_class="manual_campaign",
            content_hash=hash_json({"case_set_id": "r1_first_campaign_v1"}),
            source_ref="r1_campaign_seed",
            notes=[
                "R1 is intentionally bounded to the live-contestable runtime-v5 extraction path plus one local experimental lane.",
                "phase_s and FL_INT remain lab-validated in this campaign because their adapters are not yet provider-backed.",
            ],
        )
    )


def _candidate(
    route_id: str,
    cohort: str,
    surface_id: str,
    surface_class: str,
    provider_name: str,
    model_key: str,
    provider_model_id: str,
    admission_reason: str,
    policy_note: str,
) -> CampaignCandidate:
    return CampaignCandidate(
        route_id=route_id,
        cohort=cohort,
        surface_id=surface_id,
        surface_class=surface_class,
        provider_name=provider_name,
        model_key=model_key,
        provider_model_id=provider_model_id,
        admission_reason=admission_reason,
        policy_note=policy_note,
    )


def build_r1_campaign_plan(repo: BenchmarkCatalogRepo) -> CampaignPlan:
    ensure_r1_campaign_records(repo)
    case = repo.fetch_benchmark_case("strict_extract_conflicting_evidence_v1")
    if case is None:
        raise RuntimeError("missing strict_extract_conflicting_evidence_v1 benchmark case")

    repo_root = SERVICE_ROOT
    controls = [
        _candidate(
            route_id="route_openrouter_openai_gpt_5_4_v1",
            cohort="control",
            surface_id="surface_openrouter_api_v1",
            surface_class="openrouter_routed",
            provider_name="openrouter",
            model_key="openai/gpt-5.4",
            provider_model_id="openai/gpt-5.4",
            admission_reason="Existing routed control anchor for strict contract lanes.",
            policy_note="Production-eligible routed control.",
        ),
        _candidate(
            route_id="route_openai_gpt_5_4_v1",
            cohort="control",
            surface_id="surface_openai_api_v1",
            surface_class="direct_provider_api",
            provider_name="openai",
            model_key="openai/gpt-5.4",
            provider_model_id="gpt-5.4",
            admission_reason="Existing direct-provider control anchor for bounded direct lane comparisons.",
            policy_note="Production-eligible direct control.",
        ),
    ]
    candidates = [
        _candidate(
            route_id="route_openrouter_openai_gpt_5_3_codex_v1",
            cohort="premium",
            surface_id="surface_openrouter_api_v1",
            surface_class="openrouter_routed",
            provider_name="openrouter",
            model_key="openai/gpt-5.3-codex",
            provider_model_id="openai/gpt-5.3-codex",
            admission_reason="Premium routed candidate with the closest contract-critical affinity to current strict OpenRouter lanes.",
            policy_note="Contest strict extraction first; do not infer broad superiority from this bounded run.",
        ),
        _candidate(
            route_id="route_xai_grok_4_20_reasoning_v1",
            cohort="premium",
            surface_id="surface_xai_api_v1",
            surface_class="direct_provider_api",
            provider_name="xai",
            model_key="xai/grok-4.20-beta-0309-reasoning",
            provider_model_id="grok-4.20-beta-0309-reasoning",
            admission_reason="Premium reasoning candidate for direct-provider bounded contest on non-strict extraction and QA lanes.",
            policy_note="Direct-provider candidate; strict contract lanes remain pinned by promptset v4.",
        ),
        _candidate(
            route_id="route_gemini_3_1_pro_preview_v1",
            cohort="balanced",
            surface_id="surface_gemini_api_v1",
            surface_class="direct_provider_api",
            provider_name="gemini",
            model_key="gemini/gemini-3.1-pro-preview",
            provider_model_id="gemini-3.1-pro-preview",
            admission_reason="Balanced candidate for realistic default-production comparison on bounded direct lanes.",
            policy_note="Direct-provider candidate; contest scope is limited to runtime-v5 phase A non-strict lanes.",
        ),
        _candidate(
            route_id="route_openai_gpt_5_4_mini_v1",
            cohort="balanced",
            surface_id="surface_openai_api_v1",
            surface_class="direct_provider_api",
            provider_name="openai",
            model_key="openai/gpt-5.4-mini",
            provider_model_id="gpt-5.4-mini",
            admission_reason="Balanced lower-cost OpenAI candidate exists in registry but is intentionally held out of R1 to keep the first live cohort bounded after observing real runtime cost.",
            policy_note="Held out of the first bounded campaign; not admitted.",
        ),
        _candidate(
            route_id="route_local_fixture_v1",
            cohort="experimental",
            surface_id="surface_local_fixture_v1",
            surface_class="local_or_open_weight",
            provider_name="local-fixture",
            model_key="local/benchmark-fixture",
            provider_model_id="local/benchmark-fixture",
            admission_reason="Experimental local/open-weight containment check under current policy.",
            policy_note="Must remain experimental-only under current policy.",
        ),
    ]

    def live_assignment(candidate: CampaignCandidate, profile_id: str, anchor_group_id: str) -> CampaignAssignment:
        return CampaignAssignment(
            candidate=candidate,
            case_id="strict_extract_conflicting_evidence_v1",
            archetype_id="strict_evidence_extraction",
            profile_id=profile_id,
            control_anchor_group_id=anchor_group_id,
            live_execution=True,
            phase="A",
            repo_root=repo_root,
            routing_override_model=f"{candidate.provider_name}/{candidate.provider_model_id}",
            operator_note="Strict contract steps remain pinned by promptsets/v4 model_map.yaml; candidate route contests bounded non-strict A-lane steps only.",
        )

    baseline_assignments = [
        live_assignment(controls[0], "balanced_production", "anchor_openrouter_strict_v1"),
        live_assignment(controls[1], "balanced_production", "anchor_direct_strict_v1"),
    ]
    campaign_assignments = [
        baseline_assignments[0],
        baseline_assignments[1],
        live_assignment(candidates[0], "balanced_production", "anchor_openrouter_strict_v1"),
        live_assignment(candidates[2], "balanced_production", "anchor_direct_strict_v1"),
        CampaignAssignment(
            candidate=candidates[4],
            case_id="tool_aware_repo_reasoning_v1",
            archetype_id="tool_aware_repo_reasoning",
            profile_id="benchmark_local_validation",
            control_anchor_group_id="anchor_local_fixture_v1",
            live_execution=False,
            phase="prescan",
            repo_root=repo_root,
            routing_override_model=None,
            operator_note="Experimental local/open-weight containment check; provider-backed route contesting is not implied.",
        ),
    ]

    return CampaignPlan(
        campaign_id="TP-RTE-BENCH-R1",
        case_set_id="r1_first_campaign_v1",
        contract_snapshot_id=str(case["contract_snapshot_id"]),
        runtime_version="v5",
        control_candidates=controls,
        candidate_candidates=candidates,
        baseline_assignments=baseline_assignments,
        campaign_assignments=campaign_assignments,
        case_ids=["strict_extract_conflicting_evidence_v1", "tool_aware_repo_reasoning_v1"],
        policy_pack_files=[
            "archetype_scoring_v1.json",
            "recommendation_state_policy_v1.json",
            "freshness_policy_v1.json",
            "control_anchor_policy_v1.json",
        ],
        repo_root=repo_root,
        notes=[
            "R1 is a bounded real campaign against the repo-truth-extractor service root.",
            "Only the runtime-v5 extraction path is provider-backed today; other families remain deterministic lab adapters and are not treated as real provider contests here.",
            "Observed live runtime cost and the operator's explicit $5 budget justified admitting a reduced five-route cohort rather than the aspirational packet maximum.",
            "No universal leaderboard is produced; outputs remain route-by-archetype and profile-scoped.",
        ],
    )
