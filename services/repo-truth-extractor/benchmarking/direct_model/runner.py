from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from run_extraction_v5 import run_provider_doctor_probe, RunnerConfig
from ..campaigns.selection import ensure_r1_campaign_records
from ..models.entities import (
    BenchmarkCase,
    BenchmarkCaseAttempt,
    BenchmarkCaseSet,
    BenchmarkRun,
    ModelRecord,
    ProviderSurface,
    RetryPolicy,
    ValidatorResult,
)
from ..models.ids import synthetic_id, synthetic_run_id, utc_now_iso
from ..models.lane_contracts import build_direct_model_attempt_payload
from ..registry.registry_loader import build_registry_bundle, seed_registry
from ..registry.snapshot_capture import build_contract_snapshot, build_validator_suite
from ..storage.bundle_writer import EvidenceBundleWriter
from ..storage.hashing import hash_json, stable_json_dumps
from ..storage.paths import benchmark_paths
from ..storage.sqlite_repo import BenchmarkCatalogRepo
from .adapters.openrouter import OpenRouterDirectAdapter
from .adapters.xai import XaiDirectAdapter
from .comparisons import summarize_attempts
from .spend import HARD_SPEND_CAP_USD, SOFT_ATTEMPT_ALERT_USD, SpendGuard, estimate_tokens, projected_output_tokens


DIRECT_MODEL_CASE_SET_ID = "direct_model_mvp_fixed_v1"
DIRECT_MODEL_RETRY_POLICY_ID = "retry_direct_model_transport_once_v1"


@dataclass(frozen=True)
class DirectModelCandidate:
    model_key: str
    provider_name: str
    provider_model_id: str
    surface_id: str
    surface_class: str
    api_key_env: str
    display_name: str
    capability_flags: list[str]


@dataclass(frozen=True)
class DirectModelCaseSpec:
    case_id: str
    title: str
    archetype_id: str
    phase_or_step_family: str
    description: str
    prompt: str
    response_schema: dict[str, Any]
    expected: dict[str, Any]
    max_tokens: int


def _git_commit() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, cwd=Path(__file__).resolve().parents[4])
            .strip()
        )
    except Exception:
        return "UNKNOWN"


def _candidate_records() -> list[DirectModelCandidate]:
    return [
        DirectModelCandidate(
            model_key="openrouter/openai/gpt-5.4",
            provider_name="openrouter",
            provider_model_id="openai/gpt-5.4",
            surface_id="surface_openrouter_api_v1",
            surface_class="openrouter_routed",
            api_key_env="OPENROUTER_API_KEY",
            display_name="OpenRouter GPT-5.4",
            capability_flags=["json_mode_requested", "chat_completions", "provider_preflight_passed"],
        ),
        DirectModelCandidate(
            model_key="xai/grok-4.20",
            provider_name="xai",
            provider_model_id="grok-4.20",
            surface_id="surface_xai_api_v1",
            surface_class="direct_provider_api",
            api_key_env="XAI_API_KEY",
            display_name="xAI Grok 4.20",
            capability_flags=["json_mode_requested", "chat_completions", "provider_preflight_passed"],
        ),
        DirectModelCandidate(
            model_key="openrouter/x-ai/grok-4.1-fast",
            provider_name="openrouter",
            provider_model_id="x-ai/grok-4.1-fast",
            surface_id="surface_openrouter_api_v1",
            surface_class="openrouter_routed",
            api_key_env="OPENROUTER_API_KEY",
            display_name="OpenRouter Grok 4.1 Fast",
            capability_flags=["json_mode_requested", "chat_completions", "provider_preflight_passed"],
        ),
    ]


def _case_specs() -> list[DirectModelCaseSpec]:
    return [
        DirectModelCaseSpec(
            case_id="dm_strict_extract_clean_v1",
            title="Direct-model strict extract clean",
            archetype_id="strict_evidence_extraction",
            phase_or_step_family="DM_EXTRACT",
            description="Clean extraction with strict JSON envelope and no contradictions.",
            prompt=(
                "Source A: Repo name is atlas-api. Primary language is Python. CI system is GitHub Actions. "
                "Owner team is platform-eng. Default branch is main.\n"
                "Source B: atlas-api uses Python 3.12 and GitHub Actions workflow ci.yml. "
                "Owner team remains platform-eng.\n"
                "Return only JSON."
            ),
            response_schema={
                "type": "object",
                "required": ["repo_name", "primary_language", "ci_system", "owner_team", "default_branch", "unknowns"],
                "properties": {
                    "repo_name": {"type": "string"},
                    "primary_language": {"type": "string"},
                    "ci_system": {"type": "string"},
                    "owner_team": {"type": "string"},
                    "default_branch": {"type": "string"},
                    "unknowns": {"type": "array", "items": {"type": "string"}},
                },
                "additionalProperties": False,
            },
            expected={
                "repo_name": "atlas-api",
                "primary_language": "Python",
                "ci_system": "GitHub Actions",
                "owner_team": "platform-eng",
                "default_branch": "main",
                "unknowns": [],
            },
            max_tokens=220,
        ),
        DirectModelCaseSpec(
            case_id="dm_strict_extract_conflicting_v1",
            title="Direct-model strict extract conflicting",
            archetype_id="strict_evidence_extraction",
            phase_or_step_family="DM_EXTRACT",
            description="Conflicting evidence must remain explicit unknown instead of guessed.",
            prompt=(
                "Source A: Service mercury uses Rust. Owner is infra-core. Default branch is main.\n"
                "Source B: Service mercury uses Rust. Owner is delivery-systems. Default branch is trunk.\n"
                "Return only JSON. Conflicting fields must be marked unknown and listed in conflicts."
            ),
            response_schema={
                "type": "object",
                "required": ["service_name", "primary_language", "owner_team", "default_branch", "conflicts", "unknowns"],
                "properties": {
                    "service_name": {"type": "string"},
                    "primary_language": {"type": "string"},
                    "owner_team": {"type": "string"},
                    "default_branch": {"type": "string"},
                    "conflicts": {"type": "array", "items": {"type": "string"}},
                    "unknowns": {"type": "array", "items": {"type": "string"}},
                },
                "additionalProperties": False,
            },
            expected={
                "service_name": "mercury",
                "primary_language": "Rust",
                "owner_team": "unknown",
                "default_branch": "unknown",
                "conflicts": ["default_branch", "owner_team"],
                "unknowns": ["default_branch", "owner_team"],
            },
            max_tokens=220,
        ),
        DirectModelCaseSpec(
            case_id="dm_output_packaging_strict_v1",
            title="Direct-model output packaging strict",
            archetype_id="output_shaping_contract",
            phase_or_step_family="DM_OUTPUT",
            description="Output packaging must preserve exact envelope shape under schema pressure.",
            prompt=(
                "Evidence items:\n"
                "1. docs/api.md lines 10-18 say the public endpoint is /v1/tasks.\n"
                "2. docs/api.md lines 30-34 say auth is bearer-token.\n"
                "Return only JSON with a packaging envelope."
            ),
            response_schema={
                "type": "object",
                "required": ["document_id", "claims", "warnings"],
                "properties": {
                    "document_id": {"type": "string"},
                    "claims": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["claim_id", "value", "evidence_ref"],
                            "properties": {
                                "claim_id": {"type": "string"},
                                "value": {"type": "string"},
                                "evidence_ref": {"type": "string"},
                            },
                            "additionalProperties": False,
                        },
                    },
                    "warnings": {"type": "array", "items": {"type": "string"}},
                },
                "additionalProperties": False,
            },
            expected={
                "document_id": "api_contract_packet",
                "claims": [
                    {"claim_id": "public_endpoint", "value": "/v1/tasks", "evidence_ref": "docs/api.md#L10"},
                    {"claim_id": "auth_mode", "value": "bearer-token", "evidence_ref": "docs/api.md#L30"},
                ],
                "warnings": [],
            },
            max_tokens=260,
        ),
        DirectModelCaseSpec(
            case_id="dm_cross_source_adjudication_small_v1",
            title="Direct-model cross-source adjudication small",
            archetype_id="adjudication_governance",
            phase_or_step_family="DM_ADJUDICATION",
            description="Small adjudication case for bounded evidence arbitration.",
            prompt=(
                "Claim alpha: Supported by source_a and source_b, both dated 2026-03-01.\n"
                "Claim beta: Supported by source_c dated 2025-11-10 and explicitly superseded by source_b.\n"
                "Return only JSON selecting the supported claim and naming blocked claims."
            ),
            response_schema={
                "type": "object",
                "required": ["selected_claim_id", "confidence", "blocked_claim_ids", "reason"],
                "properties": {
                    "selected_claim_id": {"type": "string"},
                    "confidence": {"type": "string"},
                    "blocked_claim_ids": {"type": "array", "items": {"type": "string"}},
                    "reason": {"type": "string"},
                },
                "additionalProperties": False,
            },
            expected={
                "selected_claim_id": "claim_alpha",
                "confidence": "medium",
                "blocked_claim_ids": ["claim_beta"],
            },
            max_tokens=220,
        ),
    ]


def _matrix(candidates: list[DirectModelCandidate], cases: list[DirectModelCaseSpec]) -> list[tuple[DirectModelCandidate, DirectModelCaseSpec]]:
    selected: list[tuple[DirectModelCandidate, DirectModelCaseSpec]] = []
    for case in cases[:3]:
        for candidate in candidates:
            selected.append((candidate, case))
    hard_case = cases[3]
    for candidate in candidates[:2]:
        selected.append((candidate, hard_case))
    return selected


def _response_format(case: DirectModelCaseSpec) -> dict[str, Any]:
    return {
        "type": "json_object",
        "json_schema": {
            "name": case.case_id,
            "strict": True,
            "schema": case.response_schema,
        },
    }


def _parse_json(text: str) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(text)
    except Exception as exc:
        return None, f"json_parse_error:{type(exc).__name__}"
    if not isinstance(value, dict):
        return None, "json_payload_not_object"
    return value, None


def _validate_shape(payload: dict[str, Any], schema: dict[str, Any]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    required = list(schema.get("required") or [])
    properties = dict(schema.get("properties") or {})
    for key in required:
        if key not in payload:
            failures.append(f"missing:{key}")
    if bool(schema.get("additionalProperties") is False):
        extra = sorted(set(payload.keys()) - set(properties.keys()))
        failures.extend(f"extra:{key}" for key in extra)
    return (not failures), failures


def _validate_expected(payload: dict[str, Any], expected: dict[str, Any]) -> tuple[bool, list[str], float]:
    checks = 0
    matches = 0
    failures: list[str] = []
    for key, expected_value in expected.items():
        checks += 1
        if payload.get(key) == expected_value:
            matches += 1
        else:
            failures.append(f"mismatch:{key}")
    return (matches == checks), failures, round(matches / checks if checks else 0.0, 6)


def _validator_rows(
    *,
    case_attempt_id: str,
    validator_suite_id: str,
    parse_ok: bool,
    parse_error: str | None,
    shape_ok: bool,
    shape_failures: list[str],
    semantic_ok: bool,
    semantic_failures: list[str],
) -> list[ValidatorResult]:
    rows = [
        ValidatorResult(
            validator_result_id=synthetic_id("validator", f"{case_attempt_id}_json_parse"),
            case_attempt_id=case_attempt_id,
            validator_suite_id=validator_suite_id,
            validator_name="json_parse",
            passed=parse_ok,
            strength_class="strong",
            failure_reason=parse_error,
            details_ref="VALIDATOR_RESULTS.json",
            content_hash=hash_json({"case_attempt_id": case_attempt_id, "validator": "json_parse"}),
        ),
        ValidatorResult(
            validator_result_id=synthetic_id("validator", f"{case_attempt_id}_schema_shape"),
            case_attempt_id=case_attempt_id,
            validator_suite_id=validator_suite_id,
            validator_name="schema_shape",
            passed=shape_ok,
            strength_class="strong",
            failure_reason=",".join(shape_failures) if shape_failures else None,
            details_ref="VALIDATOR_RESULTS.json",
            content_hash=hash_json({"case_attempt_id": case_attempt_id, "validator": "schema_shape"}),
        ),
        ValidatorResult(
            validator_result_id=synthetic_id("validator", f"{case_attempt_id}_semantic_expectation"),
            case_attempt_id=case_attempt_id,
            validator_suite_id=validator_suite_id,
            validator_name="semantic_expectation",
            passed=semantic_ok,
            strength_class="strong",
            failure_reason=",".join(semantic_failures) if semantic_failures else None,
            details_ref="VALIDATOR_RESULTS.json",
            content_hash=hash_json({"case_attempt_id": case_attempt_id, "validator": "semantic_expectation"}),
        ),
    ]
    return rows


def _preflight_cfg() -> RunnerConfig:
    return RunnerConfig(
        dry_run=False,
        max_files_docs=1,
        max_files_code=1,
        max_chars=1000,
        max_request_bytes=10000,
        file_truncate_chars=500,
        home_scan_mode="safe",
        resume=False,
        fail_fast_auth=False,
        gemini_auth_mode="auto",
        gemini_transport="sdk",
        openai_transport="openai_sdk",
        xai_transport="openai_sdk",
        retry_policy="none",
        retry_max_attempts=1,
        retry_base_seconds=0.0,
        retry_max_seconds=0.0,
        phase_auth_fail_threshold=1,
        partition_workers=1,
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
        routing_policy="balanced_grok_openrouter",
    )


class DirectModelRunner:
    def __init__(self, root: Path | None = None) -> None:
        self.root = benchmark_paths(root).root
        self.repo = BenchmarkCatalogRepo.from_root(self.root)
        self.writer = EvidenceBundleWriter(self.root)
        self.spend_guard = SpendGuard()
        self.adapters = {
            "openrouter": OpenRouterDirectAdapter(),
            "xai": XaiDirectAdapter(),
        }

    def preflight(self, candidates: list[DirectModelCandidate]) -> list[dict[str, Any]]:
        cfg = _preflight_cfg()
        results: list[dict[str, Any]] = []
        for candidate in candidates:
            probe = run_provider_doctor_probe(
                candidate.provider_name,
                candidate.provider_model_id,
                candidate.api_key_env,
                cfg,
            )
            results.append(
                {
                    "model_key": candidate.model_key,
                    "provider_name": candidate.provider_name,
                    "provider_model_id": candidate.provider_model_id,
                    "api_key_env": candidate.api_key_env,
                    "status_code": probe.get("status_code"),
                    "failure_type": probe.get("failure_type"),
                    "provider_signature": probe.get("provider_signature"),
                    "api_key_present": probe.get("api_key_present"),
                    "provider_error_reason": probe.get("provider_error_reason"),
                }
            )
        return results

    def _seed(self, candidates: list[DirectModelCandidate], cases: list[DirectModelCaseSpec]) -> dict[str, Any]:
        seed_registry(self.repo)
        ensure_r1_campaign_records(self.repo)
        bundle = build_registry_bundle()
        contract_snapshot = build_contract_snapshot()
        validator_suite = build_validator_suite(
            validator_suite_id="validators_direct_model_strict_json_v1",
            surface_scope=["direct_provider_api", "openrouter_routed"],
            validators=["json_parse", "schema_shape", "semantic_expectation"],
            strength_class="strong",
            contract_rigor="direct_model_json_contract",
            source_paths=[
                Path(__file__).resolve(),
                (Path(__file__).parent / "spend.py").resolve(),
                (Path(__file__).parent / "comparisons.py").resolve(),
            ],
            notes=[
                "Direct-model lane validates JSON structure and bounded expectations only.",
                "Validator outcomes do not imply runtime route truth or profile truth.",
            ],
        )
        self.repo.insert_contract_snapshot(contract_snapshot)
        self.repo.insert_validator_suite(validator_suite)
        xai_surface = ProviderSurface(
            surface_id="surface_xai_api_v1",
            surface_class="direct_provider_api",
            provider_name="xai",
            transport_kind="openai_sdk",
            endpoint_ref="https://api.x.ai/v1",
            logging_posture="operator_visible",
            residency_posture="unknown",
            surface_hash=hash_json({"surface_id": "surface_xai_api_v1"}),
            source_ref="dmb_001_seed",
        )
        self.repo.insert_provider_surface(xai_surface)
        for candidate in candidates:
            self.repo.insert_model(
                ModelRecord(
                    model_key=candidate.model_key,
                    display_name=candidate.display_name,
                    family="direct_model_mvp",
                    source_registry_ref="dmb_001_fixed_candidates",
                    registry_class="direct_model_candidate_registry",
                    lifecycle_status="candidate",
                    content_hash=hash_json({"model_key": candidate.model_key}),
                    source_ref="dmb_001_seed",
                    notes=[
                        "Direct-model candidate only; not runtime-route truth.",
                        f"Capability flags from code/config truth: {','.join(candidate.capability_flags)}",
                    ],
                )
            )
        retry_policy = RetryPolicy(
            retry_policy_id=DIRECT_MODEL_RETRY_POLICY_ID,
            same_route_rules=["one_initial_attempt", "retry_only_for_transport_provider_failure"],
            escalation_rules=["no_semantic_retries", "fail_closed_on_spend_cap_projection"],
            max_hops=2,
            policy_hash=hash_json({"retry_policy_id": DIRECT_MODEL_RETRY_POLICY_ID}),
            content_hash=hash_json({"retry_policy_id": DIRECT_MODEL_RETRY_POLICY_ID}),
            source_ref="dmb_001_seed",
        )
        self.repo.insert_retry_policy(retry_policy)
        for case in cases:
            self.repo.insert_benchmark_case(
                BenchmarkCase(
                    case_id=case.case_id,
                    case_version=1,
                    benchmark_mode="direct_model",
                    candidate_type="model_candidate",
                    execution_family="direct_api_execution",
                    archetype_id=case.archetype_id,
                    phase_or_step_family=case.phase_or_step_family,
                    title=case.title,
                    description=case.description,
                    prompt_inventory_refs=["direct_model.runner.fixed_cases"],
                    surface_scope=["direct_provider_api", "openrouter_routed"],
                    executor_kind="direct_model_mvp",
                    validator_suite_id=validator_suite.validator_suite_id,
                    golden_evaluator_id="direct_model_expected_payload_v1",
                    input_bundle_id=f"direct_model_input::{case.case_id}",
                    contract_snapshot_id=contract_snapshot.contract_snapshot_id,
                    route_distinctness_required=False,
                    pricing_relevant=True,
                    governance_relevant=False,
                    governance_blockers_apply_directly=False,
                    case_tags=["direct_model", "mvp", "lane_honest"],
                    content_hash=hash_json({"case_id": case.case_id, "mode": "direct_model"}),
                    source_ref="dmb_001_seed",
                )
            )
        case_set = BenchmarkCaseSet(
            case_set_id=DIRECT_MODEL_CASE_SET_ID,
            case_set_version=1,
            archetype_id="strict_evidence_extraction",
            benchmark_stage="direct_model_mvp",
            title="Direct model MVP fixed matrix",
            case_ids=[case.case_id for case in cases],
            control_anchor_group_id=None,
            schedule_class="manual_campaign",
            content_hash=hash_json({"case_set_id": DIRECT_MODEL_CASE_SET_ID}),
            source_ref="dmb_001_seed",
            notes=["Fixed 11-attempt matrix from TP-RTE-BENCH-DMB-001-AMENDMENT-A."],
        )
        self.repo.insert_benchmark_case_set(case_set)
        return {
            "contract_snapshot": contract_snapshot,
            "validator_suite": validator_suite,
            "case_set": case_set,
            "bundle": bundle,
        }

    def run(self, proof_dir: Path | None = None) -> dict[str, Any]:
        candidates = _candidate_records()
        cases = _case_specs()
        matrix = _matrix(candidates, cases)
        preflight = self.preflight(candidates)
        blocked = [row for row in preflight if int(row.get("status_code") or 0) != 200]
        if blocked:
            raise RuntimeError(f"direct_model preflight blocked: {stable_json_dumps(blocked)}")
        seeded = self._seed(candidates, cases)
        run_id = synthetic_run_id("direct_model_mvp")
        now = utc_now_iso()
        benchmark_run = BenchmarkRun(
            benchmark_run_id=run_id,
            run_type="direct_model_benchmark_mvp",
            trigger_type="manual",
            trigger_ref="TP-RTE-BENCH-DMB-001",
            git_commit=_git_commit(),
            runtime_version="v5",
            contract_snapshot_ids=[seeded["contract_snapshot"].contract_snapshot_id],
            status="IN_PROGRESS",
            started_at=now,
            content_hash=hash_json({"benchmark_run_id": run_id}),
            source_ref="dmb_001_runner",
        )
        self.repo.insert_benchmark_run(benchmark_run)
        self.writer.write_run_layout(
            benchmark_run=benchmark_run,
            case_set_id=DIRECT_MODEL_CASE_SET_ID,
            contract_version="promptsets/v4",
            contract_snapshot_id=seeded["contract_snapshot"].contract_snapshot_id,
            registry_snapshot_files=["direct_model/registry_seed.json"],
        )
        self.writer.write_case_set_layout(
            benchmark_run_id=run_id,
            case_set_id=DIRECT_MODEL_CASE_SET_ID,
            case_ids=[case.case_id for case in cases],
            control_anchor_group_id=None,
        )

        attempts_report: list[dict[str, Any]] = []
        for index, (candidate, case) in enumerate(matrix, start=1):
            adapter = self.adapters[candidate.provider_name]
            request_tokens = estimate_tokens(case.prompt, stable_json_dumps(case.response_schema))
            preview = self.spend_guard.estimate(
                provider=candidate.provider_name,
                model_id=candidate.provider_model_id,
                input_tokens=request_tokens,
                output_tokens=projected_output_tokens(request_tokens, max_tokens=case.max_tokens),
            )
            self.spend_guard.assert_can_afford(preview)
            attempt_id = synthetic_id("bca", f"{run_id}_{index}_{case.case_id}_{candidate.model_key}")
            system_prompt = (
                "You are running inside a direct-model benchmark lane. "
                "Return one JSON object only. Do not add prose. "
                "This lane does not prove runtime route truth or profile truth."
            )
            invocation = adapter.invoke(
                model_id=candidate.provider_model_id,
                system_prompt=system_prompt,
                user_prompt=(
                    f"Case: {case.case_id}\n"
                    f"Schema: {stable_json_dumps(case.response_schema)}\n"
                    f"Instructions: {case.prompt}"
                ),
                response_format=_response_format(case),
                max_tokens=case.max_tokens,
                retry_max_attempts=2,
            )
            parse_payload, parse_error = _parse_json(invocation["response_text"])
            shape_ok = False
            shape_failures: list[str] = []
            semantic_ok = False
            semantic_failures: list[str] = []
            semantic_score = 0.0
            if parse_payload is not None:
                shape_ok, shape_failures = _validate_shape(parse_payload, case.response_schema)
                semantic_ok, semantic_failures, semantic_score = _validate_expected(parse_payload, case.expected)
            validator_rows = _validator_rows(
                case_attempt_id=attempt_id,
                validator_suite_id=seeded["validator_suite"].validator_suite_id,
                parse_ok=parse_error is None,
                parse_error=parse_error,
                shape_ok=shape_ok,
                shape_failures=shape_failures,
                semantic_ok=semantic_ok,
                semantic_failures=semantic_failures,
            )
            validator_pass = all(row.passed for row in validator_rows)
            spend_record = self.spend_guard.record_expected(preview)
            retry_trace = list(invocation["meta"].get("retry_trace") or [])
            transport_retries = max(0, len(retry_trace) - 1) if retry_trace else 0
            failure_type = invocation["meta"].get("failure_type")
            failure_reason = parse_error or ",".join(shape_failures + semantic_failures) or failure_type
            attempt = BenchmarkCaseAttempt(
                case_attempt_id=attempt_id,
                benchmark_run_id=run_id,
                case_id=case.case_id,
                case_version=1,
                case_set_id=DIRECT_MODEL_CASE_SET_ID,
                benchmark_mode="direct_model",
                candidate_type="model_candidate",
                execution_family="direct_api_execution",
                archetype_id=case.archetype_id,
                phase_or_step_family=case.phase_or_step_family,
                surface_class=candidate.surface_class,
                surface_id=candidate.surface_id,
                profile_id=None,
                route_id=None,
                control_anchor_group_id=None,
                runtime_version="v5",
                contract_version="promptsets/v4",
                contract_snapshot_id=seeded["contract_snapshot"].contract_snapshot_id,
                schema_id=f"{case.case_id}@v1",
                strict_schema_expected=True,
                validator_suite_id=seeded["validator_suite"].validator_suite_id,
                attempt_number=1,
                retry_policy_id=DIRECT_MODEL_RETRY_POLICY_ID,
                temperature_or_equivalent=0.1,
                max_tokens_or_budget=case.max_tokens,
                tool_mode="disabled",
                batch_mode="sync",
                route_distinctness_required=False,
                pricing_relevant=True,
                governance_relevant=False,
                governance_blockers_apply_directly=False,
                direct_model_attempt=build_direct_model_attempt_payload(
                    declared_provider_name=candidate.provider_name,
                    declared_model_key=candidate.model_key,
                    selected_provider_name=str(invocation["meta"].get("provider") or candidate.provider_name),
                    selected_model_key=str(invocation["meta"].get("model_id") or candidate.provider_model_id),
                    direct_request_ref="outputs/REQUEST.json",
                    direct_response_ref="outputs/RESPONSE.json",
                    pricing_metrics={
                        "estimated_cost_usd": spend_record["estimated_cost_usd"],
                        "pricing_unknown": spend_record["unknown_model"],
                        "prompt_tokens": int(invocation["meta"].get("response_summary", {}).get("prompt_tokens") or preview.input_tokens),
                        "completion_tokens": int(invocation["meta"].get("response_summary", {}).get("completion_tokens") or preview.output_tokens),
                    },
                    latency_metrics={
                        "latency_ms": float(invocation["latency_ms"]),
                        "request_payload_bytes_estimate": int(invocation["request_payload_bytes_estimate"]),
                    },
                    validator_results_ref="VALIDATOR_RESULTS.json",
                    retry_metadata={
                        "retry_trace": retry_trace,
                        "transport_retry_count": transport_retries,
                        "semantic_retries": 0,
                        "retry_policy_honest": True,
                    },
                ),
                contract_gate_pass=(parse_error is None and shape_ok),
                contract_gate_strength="strong",
                contract_fail_reason=parse_error or ",".join(shape_failures) or None,
                first_pass_valid=validator_pass,
                structural_failure_classification=failure_type or parse_error or (shape_failures[0] if shape_failures else None),
                validator_pass=validator_pass,
                task_success_score=semantic_score,
                task_score_breakdown={
                    "semantic_expectation": semantic_score,
                    "schema_shape": 1.0 if shape_ok else 0.0,
                    "json_parse": 1.0 if parse_error is None else 0.0,
                },
                scoring_policy_id="direct_model_mvp_score_v1",
                scoring_policy_version="1",
                operational_metrics={
                    "latency_ms": float(invocation["latency_ms"]),
                    "prompt_tokens": int(invocation["meta"].get("response_summary", {}).get("prompt_tokens") or preview.input_tokens),
                    "completion_tokens": int(invocation["meta"].get("response_summary", {}).get("completion_tokens") or preview.output_tokens),
                    "cost_estimate_usd": spend_record["estimated_cost_usd"],
                    "transport_retry_count": transport_retries,
                },
                repair_invocations=0,
                sidefill_invocations=0,
                route_hop_total=0,
                unknowns_open=["direct_model_not_route_truth"] + (["pricing_unknown"] if spend_record["unknown_model"] else []),
                output_artifact_ref="outputs/PARSED_OUTPUT.json",
                golden_eval_ref="TASK_EVAL.json",
                control_delta_ref="CONTROL_DELTA.json",
                evidence_bundle_id=synthetic_id("bundle", attempt_id),
                timestamp_utc=utc_now_iso(),
            )
            outputs = {
                "REQUEST.json": {
                    "case_id": case.case_id,
                    "candidate": candidate.model_key,
                    "provider_name": candidate.provider_name,
                    "provider_model_id": candidate.provider_model_id,
                    "request_payload": invocation["request_payload"],
                    "lane_boundary_note": "direct_model request only; not runtime_route truth",
                },
                "RESPONSE.json": {
                    "ok": invocation["ok"],
                    "meta": invocation["meta"],
                    "response_text": invocation["response_text"],
                },
                "PARSED_OUTPUT.json": parse_payload if parse_payload is not None else {"parse_error": parse_error},
            }
            validator_results_payload = {
                "case_id": case.case_id,
                "candidate": candidate.model_key,
                "results": [row.to_dict() for row in validator_rows],
                "validator_pass": validator_pass,
                "lane_boundary_note": "validator results are direct_model evidence only",
            }
            task_eval = {
                "case_id": case.case_id,
                "candidate": candidate.model_key,
                "expected": case.expected,
                "parsed_output": parse_payload,
                "semantic_score": semantic_score,
                "semantic_failures": semantic_failures,
                "no_route_profile_truth_claimed": True,
            }
            route_trace = {
                "benchmark_mode": "direct_model",
                "lane_boundary_note": "no runtime route selected; direct-model execution only",
                "selected_model_identity": {
                    "provider_name": str(invocation["meta"].get("provider") or candidate.provider_name),
                    "model_id": str(invocation["meta"].get("model_id") or candidate.provider_model_id),
                    "surface_id": candidate.surface_id,
                    "surface_class": candidate.surface_class,
                },
                "retry_trace": retry_trace,
            }
            executor_links = {
                "candidate": candidate.model_key,
                "case_id": case.case_id,
                "retry_policy_id": DIRECT_MODEL_RETRY_POLICY_ID,
                "pricing_truth_class": spend_record["spend_truth_class"],
                "pricing_source": spend_record["pricing_source"],
            }
            control_delta = {
                "applicable": False,
                "reason": "direct_model lane does not emit runtime-route control deltas",
            }
            written = self.writer.write_attempt_bundle(
                attempt=attempt,
                route_trace=route_trace,
                validator_results=validator_results_payload,
                task_eval=task_eval,
                control_delta=control_delta,
                executor_links=executor_links,
                output_payloads=outputs,
            )
            self.repo.insert_evidence_bundle(written.bundle)
            self.repo.insert_benchmark_case_attempt(attempt)
            for row in validator_rows:
                self.repo.insert_validator_result(row)
            attempts_report.append(
                {
                    "case_id": case.case_id,
                    "candidate": {
                        "model_key": candidate.model_key,
                        "provider_name": candidate.provider_name,
                        "provider_model_id": candidate.provider_model_id,
                    },
                    "case_attempt_id": attempt.case_attempt_id,
                    "bundle_id": attempt.evidence_bundle_id,
                    "validator_pass": validator_pass,
                    "task_success_score": semantic_score,
                    "latency_ms": invocation["latency_ms"],
                    "expected_spend_usd": spend_record["estimated_cost_usd"],
                    "pricing_unknown": spend_record["unknown_model"],
                    "pricing_source": spend_record["pricing_source"],
                    "failure_classification": attempt.structural_failure_classification,
                    "failure_reason": failure_reason,
                    "transport_retry_count": transport_retries,
                    "soft_alert_triggered": spend_record["soft_alert_triggered"],
                }
            )

        comparison = summarize_attempts(attempts_report)
        benchmark_run = BenchmarkRun(
            benchmark_run_id=run_id,
            run_type="direct_model_benchmark_mvp",
            trigger_type="manual",
            trigger_ref="TP-RTE-BENCH-DMB-001",
            git_commit=benchmark_run.git_commit,
            runtime_version="v5",
            contract_snapshot_ids=benchmark_run.contract_snapshot_ids,
            status="READY_FOR_REVIEW",
            started_at=benchmark_run.started_at,
            finished_at=utc_now_iso(),
            content_hash=benchmark_run.content_hash,
            source_ref="dmb_001_runner",
        )
        self.repo.insert_benchmark_run(benchmark_run)
        payload = {
            "benchmark_run_id": run_id,
            "intended_branch": "codex/rte-benchmark-dmb-001",
            "preflight": preflight,
            "attempts": attempts_report,
            "comparison": comparison["comparison_rows"],
            "spend_summary": self.spend_guard.summary(),
            "no_route_profile_truth_claimed": True,
        }
        if proof_dir is not None:
            proof_dir.mkdir(parents=True, exist_ok=True)
            (proof_dir / "RUN_MANIFEST.json").write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")
            (proof_dir / "DIRECT_MODEL_CAMPAIGN_MANIFEST.json").write_text(
                stable_json_dumps(
                    {
                        "benchmark_run_id": run_id,
                        "candidate_count": len(candidates),
                        "case_count": len(cases),
                        "attempt_count": len(matrix),
                        "preflight": preflight,
                        "lane_boundary_note": "direct_model lane remains distinct from runtime_route and profile synthesis",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (proof_dir / "DIRECT_MODEL_MATRIX.json").write_text(
                stable_json_dumps(
                    {
                        "attempt_count": len(matrix),
                        "rows": [
                            {"case_id": case.case_id, "model_key": candidate.model_key}
                            for candidate, case in matrix
                        ],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (proof_dir / "DIRECT_MODEL_RETRY_POLICY.json").write_text(
                stable_json_dumps(
                    {
                        "initial_attempts": 1,
                        "transport_provider_retries": 1,
                        "semantic_retries": 0,
                        "retryable_failure_classes": ["network", "provider", "rate_limit"],
                        "non_retryable_failure_classes": ["schema_failure", "semantic_failure", "validator_failure"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            (proof_dir / "DIRECT_MODEL_SPEND_GUARD.json").write_text(
                stable_json_dumps(self.spend_guard.summary()) + "\n",
                encoding="utf-8",
            )
            (proof_dir / "DIRECT_MODEL_COMPARISON.json").write_text(
                stable_json_dumps(
                    {
                        "comparison_rows": comparison["comparison_rows"],
                        "lane_boundary_note": comparison["lane_boundary_note"],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            for model_key, summary in comparison["per_model"].items():
                slug = model_key.replace("/", "__")
                (proof_dir / f"DIRECT_MODEL_SUMMARY__{slug}.json").write_text(
                    stable_json_dumps(summary) + "\n",
                    encoding="utf-8",
                )
            (proof_dir / "DIRECT_MODEL_FAILURES.json").write_text(
                stable_json_dumps(comparison["failures"]) + "\n",
                encoding="utf-8",
            )
            (proof_dir / "sample_direct_model_summary.json").write_text(
                stable_json_dumps(next(iter(comparison["per_model"].values()), {})) + "\n",
                encoding="utf-8",
            )
            (proof_dir / "sample_direct_model_comparison.json").write_text(
                stable_json_dumps({"comparison_rows": comparison["comparison_rows"]}) + "\n",
                encoding="utf-8",
            )
            (proof_dir / "sample_direct_model_failures.json").write_text(
                stable_json_dumps(comparison["failures"]) + "\n",
                encoding="utf-8",
            )
            (proof_dir / "spend_summary.json").write_text(
                stable_json_dumps(self.spend_guard.summary()) + "\n",
                encoding="utf-8",
            )
        return payload
