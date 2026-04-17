from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_runner_module() -> types.ModuleType:
    module_path = _repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5_route_ownership", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_cfg(runner: types.ModuleType):
    cfg = runner.RunnerConfig.__new__(runner.RunnerConfig)
    defaults = {
        "dry_run": True,
        "max_files_docs": 35,
        "max_files_code": 20,
        "max_chars": 650000,
        "max_request_bytes": 200000,
        "file_truncate_chars": 70000,
        "home_scan_mode": "safe",
        "resume": False,
        "fail_fast_auth": False,
        "gemini_auth_mode": "auto",
        "gemini_transport": "sdk",
        "openai_transport": "openai_sdk",
        "xai_transport": "openai_sdk",
        "retry_policy": "default",
        "retry_max_attempts": 4,
        "retry_base_seconds": 2.0,
        "retry_max_seconds": 30.0,
        "phase_auth_fail_threshold": 5,
        "partition_workers": 1,
        "debug_phase_inputs": False,
        "fail_fast_missing_inputs": False,
        "executor": "thread",
        "routing_policy": "cost",
        "disable_escalation": False,
        "escalation_max_hops": 2,
        "batch_mode": False,
        "batch_provider": "auto",
        "batch_poll_seconds": 30,
        "batch_wait_timeout_seconds": 1800,
        "batch_max_requests_per_job": 2000,
        "batch_submit_only": False,
        "webhook_url": "",
        "webhook_secret": "",
        "webhook_timeout_seconds": 5,
        "webhook_required": False,
        "webhook_auto_continue": False,
        "live_ok": False,
        "selected_s_steps": None,
        "selected_execution_step": None,
        "d0_max_files": None,
        "d1_max_files": None,
        "provider_denylist": (),
        "compare_mode": None,
        "compare_model": None,
        "compare_provider": None,
        "compare_steps": None,
        "prescan_dir": None,
        "router": None,
        "max_cost_usd": None,
        "ledger": None,
    }
    for key, value in defaults.items():
        object.__setattr__(cfg, key, value)
    return cfg


def _ownership_payload(provider_name: str, provider_model_id: str, api_key_env: str) -> str:
    return json.dumps(
        {
            "enabled": True,
            "mode": "strict_extraction_lane_owned_v1",
            "scope": "phase_a_json_managed",
            "target_phase": "A",
            "benchmark_case_id": "strict_extract_conflicting_evidence_v1",
            "route_id": f"route_{provider_name}_{provider_model_id}",
            "surface_id": f"surface_{provider_name}_api_v1",
            "surface_class": "direct_provider_api" if provider_name != "openrouter" else "openrouter_routed",
            "provider_name": provider_name,
            "model_key": f"{provider_name}/{provider_model_id}",
            "provider_model_id": provider_model_id,
            "route_pin": f"{provider_name}/{provider_model_id}",
            "api_key_env": api_key_env,
            "strict_json_schema": True,
            "strict_passthrough_verified": True,
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def _explicit_routes_payload(*, steps: dict[str, str] | None = None, phases: dict[str, str] | None = None) -> str:
    return json.dumps(
        {
            "enabled": True,
            "steps": steps or {},
            "phases": phases or {},
        },
        sort_keys=True,
        separators=(",", ":"),
    )


def test_resolve_effective_step_route_defaults_to_promptset_when_no_ownership(monkeypatch) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    monkeypatch.delenv("DPMX_BENCHMARK_ROUTE_OWNERSHIP", raising=False)
    contract = runner._step_contract_for("A", "A0")
    route = runner.resolve_effective_step_route("A", "A0", cfg, step_contract=contract)
    assert route["provider"] == "openrouter"
    assert route["model_id"] == "openai/gpt-5.3-codex"
    assert route["reason"] == "contract_lane_primary_strict"


def test_resolve_effective_step_route_honors_benchmark_owned_strict_route(monkeypatch) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    monkeypatch.setenv(
        "DPMX_BENCHMARK_ROUTE_OWNERSHIP",
        _ownership_payload("openai", "gpt-5.4", "OPENAI_API_KEY"),
    )
    contract = runner._step_contract_for("A", "A0")
    route = runner.resolve_effective_step_route("A", "A0", cfg, step_contract=contract)
    assert route["provider"] == "openai"
    assert route["model_id"] == "gpt-5.4"
    assert route["reason"] == "benchmark_route_ownership_primary"
    assert route["route_ownership"]["mode"] == "strict_extraction_lane_owned_v1"


def test_resolve_effective_step_route_honors_benchmark_owned_non_strict_route(monkeypatch) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    monkeypatch.setenv(
        "DPMX_BENCHMARK_ROUTE_OWNERSHIP",
        _ownership_payload("openai", "gpt-5.4", "OPENAI_API_KEY"),
    )
    contract = runner._step_contract_for("A", "A2")
    route = runner.resolve_effective_step_route("A", "A2", cfg, step_contract=contract)
    assert route["provider"] == "openai"
    assert route["model_id"] == "gpt-5.4"
    assert route["reason"] == "benchmark_route_ownership_primary"


def test_call_llm_with_ladder_promotes_strict_two_tuple_routes_to_canonical_triples() -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    observed_routes = []

    def execute_attempt(route, hop_index):  # type: ignore[no-untyped-def]
        observed_routes.append((route, hop_index))
        provider, model_id, api_key_env = route
        return {
            "response_text": "",
            "request_meta": {"failure_type": None, "status_code": 200},
            "artifacts": [],
            "route": (provider, model_id, api_key_env),
            "artifacts_ok": True,
            "escalation_trigger": None,
        }

    payload = runner.call_llm_with_ladder(
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        routing_policy="cost",
        routing_tier="extract",
        ladder=[("openrouter", "openai/gpt-5.3-codex")],
        cfg=cfg,
        execute_attempt=execute_attempt,
    )

    assert observed_routes == [(
        ("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY"),
        0,
    )]
    assert payload["route"] == (
        "openrouter",
        "openai/gpt-5.3-codex",
        "OPENROUTER_API_KEY",
    )
    assert payload["request_meta"]["provider"] == "openrouter"
    assert payload["request_meta"]["model_id"] == "openai/gpt-5.3-codex"
    assert payload["request_meta"]["route_attempts"][0]["api_key_env"] == "OPENROUTER_API_KEY"


def test_benchmark_route_ownership_payload_reports_enabled(monkeypatch) -> None:
    runner = _load_runner_module()
    monkeypatch.setenv(
        "DPMX_BENCHMARK_ROUTE_OWNERSHIP",
        _ownership_payload("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY"),
    )
    payload = runner.benchmark_route_ownership_payload(validate=True)
    assert payload["enabled"] is True
    assert payload["provider_name"] == "openrouter"


def test_resolve_effective_step_route_honors_explicit_step_override_for_later_phase(
    monkeypatch,
) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    monkeypatch.setenv(
        "DPMX_EXPLICIT_STEP_ROUTES",
        _explicit_routes_payload(steps={"H:H3": "openrouter/openai/gpt-5.4"}),
    )

    route = runner.resolve_effective_step_route("H", "H3", cfg)

    assert route["provider"] == "openrouter"
    assert route["model_id"] == "openai/gpt-5.4"
    assert route["reason"] == "explicit_step_route_override"
    assert route["route_control"]["selector"] == "step"


def test_resolve_effective_step_route_prefers_step_override_over_phase_override(
    monkeypatch,
) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    monkeypatch.setenv(
        "DPMX_EXPLICIT_STEP_ROUTES",
        _explicit_routes_payload(
            steps={"H:H3": "openrouter/openai/gpt-5.4"},
            phases={"H": "openrouter/openai/gpt-5.3-codex"},
        ),
    )

    route = runner.resolve_effective_step_route("H", "H3", cfg)

    assert route["provider"] == "openrouter"
    assert route["model_id"] == "openai/gpt-5.4"
    assert route["reason"] == "explicit_step_route_override"


def test_call_llm_with_ladder_blocks_same_account_quota_escalation() -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    observed_routes = []

    def execute_attempt(route, hop_index):  # type: ignore[no-untyped-def]
        observed_routes.append((route, hop_index))
        provider, model_id, api_key_env = route
        return {
            "response_text": "",
            "request_meta": {
                "failure_type": "quota_or_billing",
                "status_code": 402,
            },
            "artifacts": [],
            "route": (provider, model_id, api_key_env),
            "artifacts_ok": False,
            "escalation_trigger": "provider_failure",
        }

    payload = runner.call_llm_with_ladder(
        phase="H",
        step_id="H3",
        partition_id="H_P0001",
        routing_policy="cost",
        routing_tier="extract",
        ladder=[
            ("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY"),
            ("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY"),
        ],
        cfg=cfg,
        execute_attempt=execute_attempt,
    )

    assert observed_routes == [(
        ("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY"),
        0,
    )]
    assert payload["request_meta"]["route_guard_blocked"] is True
    assert (
        payload["request_meta"]["route_guard_reason"]
        == "quota_or_billing_same_api_key_env"
    )
    assert payload["request_meta"]["blocked_next_route"] == "openrouter/openai/gpt-5.4"
    assert payload["request_meta"]["route_hop_total"] == 1
