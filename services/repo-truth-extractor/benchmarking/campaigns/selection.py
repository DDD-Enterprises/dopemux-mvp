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
            surface_id="surface_gemini_direct_api_v1",
            surface_class="direct_provider_api",
            provider_name="gemini",
            transport_kind="openai_sdk",
            endpoint_ref="https://generativelanguage.googleapis.com",
            logging_posture="operator_visible",
            residency_posture="unknown",
            surface_hash=hash_json({"surface_id": "surface_gemini_direct_api_v1"}),
            source_ref="r1_campaign_seed",
            notes=["R1 direct provider surface for strict-output attestation candidates."],
        ),
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
            model_key="google/gemini-3.1-pro-preview",
            display_name="Gemini 3.1 Pro Preview via OpenRouter",
            family="gemini-3",
            source_registry_ref="runtime_candidate_registry",
            registry_class="current_state_authority",
            lifecycle_status="candidate",
            content_hash=hash_json({"model_key": "google/gemini-3.1-pro-preview"}),
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
            route_id="route_gemini_direct_gemini_3_1_pro_preview_v1",
            surface_id="surface_gemini_direct_api_v1",
            model_key="gemini/gemini-3.1-pro-preview",
            provider_model_id="gemini-3.1-pro-preview",
            api_key_ref="GEMINI_API_KEY",
            route_pin="gemini-3.1-pro-preview",
            strict_json_schema_declared=True,
            strict_passthrough_verified=False,
            route_hash=hash_json({"route_id": "route_gemini_direct_gemini_3_1_pro_preview_v1"}),
            content_hash=hash_json({"route_id": "route_gemini_direct_gemini_3_1_pro_preview_v1"}),
            source_ref="r1_campaign_seed",
        ),
        RouteRecord(
            route_id="route_openrouter_gemini_3_1_pro_preview_v1",
            surface_id="surface_openrouter_api_v1",
            model_key="google/gemini-3.1-pro-preview",
            provider_model_id="google/gemini-3.1-pro-preview",
            api_key_ref="OPENROUTER_API_KEY",
            route_pin="google/gemini-3.1-pro-preview",
            strict_json_schema_declared=True,
            strict_passthrough_verified=False,
            route_hash=hash_json({"route_id": "route_openrouter_gemini_3_1_pro_preview_v1"}),
            content_hash=hash_json({"route_id": "route_openrouter_gemini_3_1_pro_preview_v1"}),
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


def decide_r1_live_cohort(
    assignments: list[CampaignAssignment],
    provider_readiness: dict[str, object],
) -> dict[str, object]:
    readiness_rows = {
        str(item.get("route_id") or ""): item
        for item in provider_readiness.get("routes", [])
        if isinstance(item, dict)
    }
    live_assignments = sorted(
        (assignment for assignment in assignments if assignment.live_execution),
        key=lambda assignment: (
            assignment.case_id,
            assignment.candidate.cohort,
            assignment.candidate.route_id,
        ),
    )

    route_decisions: list[dict[str, object]] = []
    admitted_route_ids: list[str] = []
    blocked_route_ids: list[str] = []
    quota_blocked_openai_routes: list[str] = []
    admitted_openrouter_routes: list[str] = []

    for assignment in live_assignments:
        readiness_row = readiness_rows.get(assignment.candidate.route_id, {})
        provider_probe = (
            readiness_row.get("provider_probe", {})
            if isinstance(readiness_row, dict)
            else {}
        )
        readiness_blocker = (
            provider_probe.get("readiness_blocker", {})
            if isinstance(provider_probe, dict)
            else {}
        )
        blocker_code = str(readiness_blocker.get("blocker_code") or "")
        ready = bool(readiness_row.get("ready")) if isinstance(readiness_row, dict) else False
        state = "admitted"
        rationale = "provider_ready"
        replacement_route_ids: list[str] = []

        if ready:
            admitted_route_ids.append(assignment.candidate.route_id)
            if assignment.candidate.provider_name == "openrouter":
                admitted_openrouter_routes.append(assignment.candidate.route_id)
        else:
            blocked_route_ids.append(assignment.candidate.route_id)
            if assignment.candidate.provider_name == "openai" and blocker_code == "QUOTA_OR_BILLING_BLOCK":
                state = "excluded_openai_quota_or_billing_block"
                rationale = "openai_first_party_unexecutable"
                quota_blocked_openai_routes.append(assignment.candidate.route_id)
            elif blocker_code:
                state = "excluded_provider_blocked"
                rationale = blocker_code.lower()
            else:
                state = "excluded_without_probe_evidence"
                rationale = "missing_provider_probe"

        route_decisions.append(
            {
                "route_id": assignment.candidate.route_id,
                "case_id": assignment.case_id,
                "cohort": assignment.candidate.cohort,
                "provider_name": assignment.candidate.provider_name,
                "provider_model_id": assignment.candidate.provider_model_id,
                "surface_class": assignment.candidate.surface_class,
                "live_execution": assignment.live_execution,
                "ready": ready,
                "decision_state": state,
                "decision_reason": rationale,
                "replacement_route_ids": replacement_route_ids,
                "provider_probe": provider_probe if isinstance(provider_probe, dict) else {},
            }
        )

    admitted_openrouter_routes = sorted(set(admitted_openrouter_routes))
    if quota_blocked_openai_routes and admitted_openrouter_routes:
        for row in route_decisions:
            if row["route_id"] in quota_blocked_openai_routes:
                row["replacement_route_ids"] = admitted_openrouter_routes

    notes: list[str] = []
    if quota_blocked_openai_routes:
        notes.append(
            "OpenAI first-party quota or billing blockers exclude those routes from the executable live cohort."
        )
    if admitted_openrouter_routes and quota_blocked_openai_routes:
        notes.append(
            "OpenRouter remains admitted as the live evidence-producing replacement cohort where provider readiness is proven."
        )
    if not admitted_route_ids:
        notes.append("No live routes remain admitted after provider-readiness filtering.")

    return {
        "campaign_id": "TP-RTE-BENCH-R1",
        "planned_live_route_ids": [assignment.candidate.route_id for assignment in live_assignments],
        "admitted_live_route_ids": sorted(admitted_route_ids),
        "blocked_live_route_ids": sorted(blocked_route_ids),
        "quota_blocked_openai_route_ids": sorted(quota_blocked_openai_routes),
        "admitted_openrouter_route_ids": admitted_openrouter_routes,
        "status": "admitted" if admitted_route_ids else "blocked",
        "route_decisions": route_decisions,
        "notes": notes,
    }


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
        # [0] openrouter_openai_gpt_5_3_codex  → anchor_openrouter_strict_v1
        # [1] xai_grok_4_20_reasoning          (no live_assignment — not yet admitted)
        # [2] gemini_3_1_pro_preview            (no live_assignment — pending telemetry)
        # [3] gemini_direct_3_1_pro_preview     → anchor_direct_strict_v1
        # [4] openrouter_gemini_3_1_pro_preview → anchor_openrouter_strict_v1
        # [5] openai_gpt_5_4_mini               → anchor_direct_strict_v1
        # [6] local_fixture                     → tool_aware_repo_reasoning_v1 (non-live)
        # When inserting a new candidate, update live_assignment indices AND this table.
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
            admission_reason="Balanced candidate remains out of the first admitted cohort because current dry-run ownership telemetry for this route is not yet strong enough to satisfy route-identity admissibility.",
            policy_note="Do not admit until owned-lane telemetry becomes admissibility-grade.",
        ),
        _candidate(
            route_id="route_gemini_direct_gemini_3_1_pro_preview_v1",
            cohort="balanced",
            surface_id="surface_gemini_direct_api_v1",
            surface_class="direct_provider_api",
            provider_name="gemini",
            model_key="gemini/gemini-3.1-pro-preview",
            provider_model_id="gemini-3.1-pro-preview",
            admission_reason="Direct Gemini strict-output candidate for live passthrough attestation; verification flag remains false until campaign evidence exists.",
            policy_note="Attestation candidate only; do not promote without live strict passthrough proof.",
        ),
        _candidate(
            route_id="route_openrouter_gemini_3_1_pro_preview_v1",
            cohort="premium",
            surface_id="surface_openrouter_api_v1",
            surface_class="openrouter_routed",
            provider_name="openrouter",
            model_key="google/gemini-3.1-pro-preview",
            provider_model_id="google/gemini-3.1-pro-preview",
            admission_reason="OpenRouter Gemini strict-output candidate for routed passthrough attestation; verification flag remains false until campaign evidence exists.",
            policy_note="Attestation candidate only; do not promote without live strict passthrough proof.",
        ),
        _candidate(
            route_id="route_openai_gpt_5_4_mini_v1",
            cohort="balanced",
            surface_id="surface_openai_api_v1",
            surface_class="direct_provider_api",
            provider_name="openai",
            model_key="openai/gpt-5.4-mini",
            provider_model_id="gpt-5.4-mini",
            admission_reason="Balanced lower-cost OpenAI candidate shares the direct-provider control family and can be admitted without changing the owned-lane strict extraction contest shape.",
            policy_note="Direct-provider candidate; bounded to runtime-v5 strict extraction on the existing owned-lane control family.",
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
        live_assignment(candidates[3], "balanced_production", "anchor_direct_strict_v1"),
        live_assignment(candidates[4], "balanced_production", "anchor_openrouter_strict_v1"),
        live_assignment(candidates[5], "balanced_production", "anchor_direct_strict_v1"),
        CampaignAssignment(
            candidate=candidates[6],
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
            "The admitted cohort stays below the packet maximum because only routes with admissibility-grade owned-lane evidence are included in the live strict contest.",
            "No universal leaderboard is produced; outputs remain route-by-archetype and profile-scoped.",
        ],
    )
