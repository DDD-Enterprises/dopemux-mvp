from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _make_cfg(runner):
    return runner.RunnerConfig(
        dry_run=False,
        max_files_docs=10,
        max_files_code=10,
        max_chars=10000,
        max_request_bytes=200000,
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
        phase_auth_fail_threshold=5,
        partition_workers=1,
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
        routing_policy="balanced_grok_openrouter",
    )


def _fake_context(**_kwargs):  # type: ignore[no-untyped-def]
    return (
        "--- FILE: docs/example.md ---\n0001: line one\n0002: line two\n",
        {"files_included": 1, "files_skipped": 0, "context_bytes": 60, "redaction_hits": 0},
    )


def _evidence(path: str, line_range: list[int]) -> list[dict]:
    return [{"path": path, "line_range": line_range, "excerpt": "0001: line one"}]


def _d1_valid_payload() -> dict:
    return {
        "artifacts": [
            {
                "artifact_name": "DOC_INDEX.partX.json",
                "payload": {
                    "schema": "DOC_INDEX@v1",
                    "items": [
                        {
                            "id": "DOC_INDEX:item",
                            "path": "docs/example.md",
                            "line_range": [1, 2],
                            "name": "Example",
                            "kind": "guide",
                            "evidence": _evidence("docs/example.md", [1, 2]),
                        }
                    ],
                },
            },
            {
                "artifact_name": "DOC_CONTRACT_CLAIMS.partX.json",
                "payload": {
                    "schema": "DOC_CONTRACT_CLAIMS@v1",
                    "items": [
                        {
                            "id": "DOC_CONTRACT_CLAIMS:item",
                            "path": "docs/example.md",
                            "line_range": [1, 2],
                            "evidence": _evidence("docs/example.md", [1, 2]),
                        }
                    ],
                },
            },
            {
                "artifact_name": "DOC_BOUNDARIES.partX.json",
                "payload": {
                    "schema": "DOC_BOUNDARIES@v1",
                    "items": [
                        {
                            "id": "DOC_BOUNDARIES:item",
                            "path": "docs/example.md",
                            "line_range": [1, 2],
                            "evidence": _evidence("docs/example.md", [1, 2]),
                        }
                    ],
                },
            },
            {
                "artifact_name": "DOC_SUPERSESSION.partX.json",
                "payload": {
                    "schema": "DOC_SUPERSESSION@v1",
                    "items": [
                        {
                            "id": "DOC_SUPERSESSION:item",
                            "path": "docs/example.md",
                            "line_range": [1, 2],
                            "evidence": _evidence("docs/example.md", [1, 2]),
                        }
                    ],
                },
            },
            {
                "artifact_name": "CAP_NOTICES.partX.json",
                "payload": {
                    "schema": "CAP_NOTICES@v1",
                    "items": [
                        {
                            "id": "CAP_NOTICES:item",
                            "path": "docs/example.md",
                            "line_range": [1, 2],
                            "evidence": _evidence("docs/example.md", [1, 2]),
                        }
                    ],
                },
            },
        ]
    }


def test_step_tier_classifier_is_deterministic() -> None:
    runner = _load_runner_module()
    assert runner.resolve_step_tier("A", "A0") == "bulk"
    assert runner.resolve_step_tier("A", "A1") == "extract"
    assert runner.resolve_step_tier("Q", "Q1") == "qa"
    assert runner.resolve_step_tier("C", "C9") == "qa"
    assert runner.resolve_step_tier("R", "R1") == "synthesis"
    assert runner.resolve_step_tier("Z", "Z2") == "synthesis"


def test_contract_lane_routes_override_policy_for_json_managed_steps() -> None:
    runner = _load_runner_module()
    expected_d0 = [
        ("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY"),
        ("openrouter", "openai/gpt-5.2", "OPENROUTER_API_KEY"),
    ]
    assert runner.resolve_step_ladder("cost", "D", "D0") == expected_d0
    assert runner.resolve_step_ladder("balanced_grok_openrouter", "D", "D0") == expected_d0
    assert runner.resolve_step_ladder("quality", "D", "D1") == expected_d0

    assert runner.resolve_step_ladder("balanced_grok_openrouter", "D", "D2") == [
        ("xai", "grok-4-1-fast-reasoning", "XAI_API_KEY"),
        ("xai", "grok-4-1-fast-non-reasoning", "XAI_API_KEY"),
    ]
    assert runner.resolve_step_ladder("balanced_grok_openrouter", "C", "C1") == [
        ("xai", "grok-code-fast-1", "XAI_API_KEY"),
        ("xai", "grok-4-1-fast-reasoning", "XAI_API_KEY"),
    ]
    assert runner.resolve_step_ladder("balanced_grok_openrouter", "D", "D4") == [
        ("openrouter", "openai/gpt-5-mini", "OPENROUTER_API_KEY"),
    ]


def test_resolve_effective_step_route_marks_strict_required_contract_lane() -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    contract = runner._step_contract_for("D", "D1")
    route_info = runner.resolve_effective_step_route("D", "D1", cfg, step_contract=contract)
    assert route_info["reason"] == "contract_lane_primary_strict"
    assert route_info["strict_required"] is True
    assert route_info["provider"] == "openrouter"
    assert route_info["model_id"] == "openai/gpt-5.3-codex"
    attempts = route_info.get("strict_route_attempts")
    assert isinstance(attempts, list) and attempts
    assert attempts[0]["strict_capable"] is True


def test_strict_route_requires_verified_passthrough_for_openrouter() -> None:
    runner = _load_runner_module()
    route, attempts = runner.resolve_stage_route(
        step_contract={
            "lane": {
                "primary_routes": [
                    {
                        "provider": "openrouter",
                        "model_id": "openai/gpt-5.2",
                        "api_key_env": "OPENROUTER_API_KEY",
                        "strict_json_schema": True,
                        "strict_passthrough_verified": False,
                    }
                ]
            }
        },
        stage="primary",
        transport_for_provider=lambda _provider: "openai_sdk",
        strict_required=True,
    )
    assert route is None
    assert attempts
    assert attempts[0]["strict_capable"] is False
    assert attempts[0]["reason"] == "openrouter_strict_passthrough_unverified"


def test_strict_required_stage_fails_closed_before_token_spend() -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    with pytest.raises(RuntimeError, match="no strict-capable route before token spend"):
        runner.resolve_effective_step_route(
            "D",
            "D1",
            cfg,
            step_contract={
                "phase": "D",
                "step_id": "D1",
                "scope": {"json_managed": True},
                "lane": {
                    "lane_class": "CE",
                    "strict_schema_required_primary": True,
                    "primary_routes": [
                        {
                            "provider": "openrouter",
                            "model_id": "openai/gpt-5.2",
                            "api_key_env": "OPENROUTER_API_KEY",
                            "strict_json_schema": True,
                            "strict_passthrough_verified": False,
                        }
                    ],
                },
            },
        )


def test_no_auto_transport_flip_across_retry_hops(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    phase_dir = tmp_path / "D_docs_pipeline"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
    prompt = tmp_path / "PROMPT_D1_TEST.md"
    prompt.write_text("Goal: D1 strict output\n", encoding="utf-8")
    contract = runner._step_contract_for("D", "D1")
    prompt_spec = runner.PromptSpec(
        step_id="D1",
        prompt_path=prompt,
        output_artifacts=tuple(contract["artifact_order"]),
        contract=contract,
    )
    partitions = [{"id": "D_P0001", "paths": ["docs/example.md"]}]

    calls = {"count": 0}

    def fake_call_llm(**_kwargs):  # type: ignore[no-untyped-def]
        calls["count"] += 1
        if calls["count"] == 1:
            return {
                "text": json.dumps(_d1_valid_payload()),
                "meta": {
                    "failure_type": "provider",
                    "status_code": 503,
                    "provider_error_reason": "temporary_upstream",
                    "response_received": True,
                    "response_summary": {"finish_reason": "STOP"},
                },
            }
        return {
            "text": json.dumps(_d1_valid_payload()),
            "meta": {
                "failure_type": None,
                "status_code": 200,
                "response_received": True,
                "response_summary": {"finish_reason": "STOP"},
            },
        }

    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(runner, "call_llm", fake_call_llm)

    stats = runner.execute_step_for_partitions(
        phase="D",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=cfg,
    )
    assert stats["ok"] == 1

    payload = json.loads((phase_dir / "raw" / "D1__D_P0001.json").read_text(encoding="utf-8"))
    request_meta = payload["request_meta"]
    assert request_meta["no_auto_transport_flips"] is True
    attempts = request_meta.get("route_attempts", [])
    assert len(attempts) == 2
    assert all(row["provider"] == "openrouter" for row in attempts)


def test_provider_preflight_fails_when_an_active_provider_probe_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)

    def fake_probe(provider, model_id, api_key_env, cfg):  # type: ignore[no-untyped-def]
        if provider == "xai":
            return {
                "provider": provider,
                "model_id": model_id,
                "status_code": 503,
                "failure_type": "provider",
            }
        return {
            "provider": provider,
            "model_id": model_id,
            "status_code": 200,
            "failure_type": None,
        }

    monkeypatch.setattr(runner, "run_provider_doctor_probe", fake_probe)
    ok, payload = runner.run_provider_preflight(
        root=tmp_path,
        run_id="test_preflight",
        cfg=cfg,
        phases=["A"],
    )
    assert ok is False
    assert payload["status"] == "FAIL"
    assert "xai" in payload["failed_providers"]


def test_print_config_reports_contract_lane_effective_model_routing(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[3]
    script = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
    run_id = "test_model_routing_print_config"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--print-config",
            "--run-id",
            run_id,
            "--no-write-latest",
            "--gemini-model-id",
            "models/gemini-2.5-flash",
            "--routing-policy",
            "cost",
            "--phase",
            "A",
        ],
        cwd=str(tmp_path),
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    assert payload["cli"]["gemini_model_id"] == "models/gemini-2.5-flash"
    assert payload["cli"]["routing_policy"] == "cost"
    assert payload["effective_model_routing"]["A"]["provider"] == "openrouter"
    assert payload["effective_model_routing"]["A"]["model_id"] == "openai/gpt-5.3-codex"
