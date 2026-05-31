from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_module():
    root = Path(__file__).resolve().parents[3]
    module_path = (
        root
        / "services"
        / "repo-truth-extractor"
        / "benchmarking"
        / "cli"
        / "benchmark_live_route_readiness_smoke.py"
    )
    spec = importlib.util.spec_from_file_location("benchmark_live_route_readiness_smoke_test", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_strict_live_route_ids_include_gemini_attestation_candidates() -> None:
    module = _load_module()

    assert "route_gemini_direct_gemini_3_1_pro_preview_v1" in module.STRICT_LIVE_ROUTE_IDS
    assert "route_openrouter_gemini_3_1_pro_preview_v1" in module.STRICT_LIVE_ROUTE_IDS


def test_provider_readiness_aggregates_blocker_codes_and_rerun_worthiness(monkeypatch) -> None:
    module = _load_module()

    class FakeRepo:
        def fetch_route(self, route_id):  # type: ignore[no-untyped-def]
            return {"api_key_ref": "OPENROUTER_API_KEY", "route_pin": "x", "strict_passthrough_verified": True}

    class FakeCandidate:
        def __init__(self, route_id, cohort, provider_name, provider_model_id):
            self.route_id = route_id
            self.cohort = cohort
            self.provider_name = provider_name
            self.provider_model_id = provider_model_id
            self.surface_id = "surface"
            self.surface_class = "openrouter_routed"
            self.model_key = provider_model_id

    class FakeAssignment:
        def __init__(self, route_id, cohort, provider_name, provider_model_id):
            self.candidate = FakeCandidate(route_id, cohort, provider_name, provider_model_id)
            self.benchmark_route_ownership_mode = "strict_extraction_lane_owned_v1"
            self.benchmark_route_ownership_scope = "phase_a_json_managed"
            self.phase = "A"
            self.case_id = "strict_extract_conflicting_evidence_v1"

    class FakeRunner:
        @staticmethod
        def derive_route_readiness_summary(phases, routing_policy):  # type: ignore[no-untyped-def]
            return {"target_phases": phases, "target_policy": routing_policy, "routes": []}

        @staticmethod
        def run_provider_doctor_probe(provider, model_id, api_key_env, cfg):  # type: ignore[no-untyped-def]
            if provider == "openrouter":
                return {
                    "ready": False,
                    "status_code": 401,
                    "failure_type": "auth_rejected",
                    "provider_error_reason": None,
                    "readiness_blocker": {
                        "blocker_code": "PROVIDER_AUTH_REJECTED",
                        "blocker_class": "auth",
                        "remediation_class": "fix_provider_credentials_or_permissions",
                        "rerun_worthiness": "rerun_after_auth_fix",
                    },
                }
            return {
                "ready": False,
                "status_code": 429,
                "failure_type": "quota_or_billing",
                "provider_error_reason": "insufficient_quota",
                "readiness_blocker": {
                    "blocker_code": "QUOTA_OR_BILLING_BLOCK",
                    "blocker_class": "quota_billing",
                    "remediation_class": "restore_quota_or_billing",
                    "rerun_worthiness": "rerun_after_billing_fix",
                },
            }

    monkeypatch.setattr(module, "_load_runner_module", lambda: FakeRunner)
    monkeypatch.setattr(module, "_make_cfg", lambda runner: object())

    readiness = module._provider_readiness(
        FakeRepo(),
        [
            FakeAssignment("route_openrouter_openai_gpt_5_4_v1", "control", "openrouter", "openai/gpt-5.4"),
            FakeAssignment("route_openai_gpt_5_4_v1", "control", "openai", "gpt-5.4"),
        ],
    )

    assert readiness["status"] == "blocked"
    assert readiness["required_control_pair_ready"] is False
    assert readiness["blocker_codes"] == ["PROVIDER_AUTH_REJECTED", "QUOTA_OR_BILLING_BLOCK"]
    assert readiness["rerun_worthiness"] == "worth_rerunning_after_fixes"


def test_live_cohort_excludes_quota_blocked_openai_and_keeps_openrouter_replacement(monkeypatch) -> None:
    module = _load_module()

    class FakeRepo:
        def fetch_route(self, route_id):  # type: ignore[no-untyped-def]
            api_key = "OPENROUTER_API_KEY" if "openrouter" in route_id else "OPENAI_API_KEY"
            return {"api_key_ref": api_key, "route_pin": "x", "strict_passthrough_verified": True}

    class FakeCandidate:
        def __init__(self, route_id, cohort, provider_name, provider_model_id):
            self.route_id = route_id
            self.cohort = cohort
            self.provider_name = provider_name
            self.provider_model_id = provider_model_id
            self.surface_id = "surface"
            self.surface_class = "openrouter_routed" if provider_name == "openrouter" else "direct_provider_api"
            self.model_key = provider_model_id

    class FakeAssignment:
        def __init__(self, route_id, cohort, provider_name, provider_model_id):
            self.candidate = FakeCandidate(route_id, cohort, provider_name, provider_model_id)
            self.benchmark_route_ownership_mode = "strict_extraction_lane_owned_v1"
            self.benchmark_route_ownership_scope = "phase_a_json_managed"
            self.phase = "A"
            self.case_id = "strict_extract_conflicting_evidence_v1"
            self.live_execution = True

    class FakeRunner:
        @staticmethod
        def derive_route_readiness_summary(phases, routing_policy):  # type: ignore[no-untyped-def]
            return {"target_phases": phases, "target_policy": routing_policy, "routes": []}

        @staticmethod
        def run_provider_doctor_probe(provider, model_id, api_key_env, cfg):  # type: ignore[no-untyped-def]
            if provider == "openrouter":
                return {"ready": True, "readiness_blocker": {}}
            return {
                "ready": False,
                "status_code": 429,
                "failure_type": "quota_or_billing",
                "provider_error_reason": "insufficient_quota",
                "readiness_blocker": {"blocker_code": "QUOTA_OR_BILLING_BLOCK"},
            }

    monkeypatch.setattr(module, "_load_runner_module", lambda: FakeRunner)
    monkeypatch.setattr(module, "_make_cfg", lambda runner: object())

    readiness = module._provider_readiness(
        FakeRepo(),
        [
            FakeAssignment("route_openrouter_openai_gpt_5_4_v1", "control", "openrouter", "openai/gpt-5.4"),
            FakeAssignment("route_openrouter_openai_gpt_5_3_codex_v1", "premium", "openrouter", "openai/gpt-5.3-codex"),
            FakeAssignment("route_openai_gpt_5_4_v1", "control", "openai", "gpt-5.4"),
        ],
    )
    decision = module.decide_r1_live_cohort(
        [
            FakeAssignment("route_openrouter_openai_gpt_5_4_v1", "control", "openrouter", "openai/gpt-5.4"),
            FakeAssignment("route_openrouter_openai_gpt_5_3_codex_v1", "premium", "openrouter", "openai/gpt-5.3-codex"),
            FakeAssignment("route_openai_gpt_5_4_v1", "control", "openai", "gpt-5.4"),
        ],
        readiness,
    )

    assert decision["admitted_live_route_ids"] == [
        "route_openrouter_openai_gpt_5_3_codex_v1",
        "route_openrouter_openai_gpt_5_4_v1",
    ]
    assert decision["quota_blocked_openai_route_ids"] == ["route_openai_gpt_5_4_v1"]
