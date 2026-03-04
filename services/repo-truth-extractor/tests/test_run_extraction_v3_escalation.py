from __future__ import annotations

import importlib.util
import json
from dataclasses import replace
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


def _make_cfg(runner, *, disable_escalation: bool = False):
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
        routing_policy="cost",
        disable_escalation=disable_escalation,
        escalation_max_hops=2,
    )


def _prepare_step(runner, tmp_path: Path):
    phase_dir = tmp_path / "A_repo_control_plane"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
    prompt = tmp_path / "PROMPT_A1_TEST.md"
    prompt.write_text("Goal: OUT.json\n", encoding="utf-8")
    prompt_spec = runner.PromptSpec(step_id="A1", prompt_path=prompt, output_artifacts=("OUT.json",))
    partitions = [{"id": "A_P0001", "paths": ["/tmp/p1"]}]
    return phase_dir, prompt_spec, partitions


def _fake_context(**kwargs):  # type: ignore[no-untyped-def]
    return (
        "PARTITION_PATH=/tmp/p1",
        {"files_included": 1, "files_skipped": 0, "context_bytes": 20, "redaction_hits": 0},
    )


def test_parse_failure_escalates_to_next_hop(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    phase_dir, prompt_spec, partitions = _prepare_step(runner, tmp_path)
    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(
        runner,
        "resolve_step_ladder",
        lambda routing_policy, phase, step_id: [
            ("openai", "model-hop1", "OPENAI_API_KEY"),
            ("openai", "model-hop2", "OPENAI_API_KEY"),
        ],
    )

    def fake_call_llm(**kwargs):  # type: ignore[no-untyped-def]
        model_id = kwargs["model_id"]
        if model_id == "model-hop1":
            return {
                "text": '{"artifacts":[{"artifact_name":"OUT.json","payload":"',
                "meta": {"failure_type": None, "status_code": 200, "response_summary": {"finish_reason": "STOP"}},
            }
        return {
            "text": json.dumps({"artifacts": [{"artifact_name": "OUT.json", "payload": {"items": []}}]}),
            "meta": {"failure_type": None, "status_code": 200, "response_summary": {"finish_reason": "STOP"}},
        }

    monkeypatch.setattr(runner, "call_llm", fake_call_llm)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner),
    )
    assert stats["ok"] == 1
    assert stats["failed"] == 0
    assert stats["escalated_partitions"] == 1
    payload = json.loads((phase_dir / "raw" / "A1__A_P0001.json").read_text(encoding="utf-8"))
    assert payload["request_meta"]["route_hop_total"] == 2
    assert len(payload["request_meta"]["route_attempts"]) == 2


def test_schema_failure_escalates_to_next_hop(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    phase_dir, prompt_spec, partitions = _prepare_step(runner, tmp_path)
    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(
        runner,
        "resolve_step_ladder",
        lambda routing_policy, phase, step_id: [
            ("openai", "model-hop1", "OPENAI_API_KEY"),
            ("openai", "model-hop2", "OPENAI_API_KEY"),
        ],
    )

    def fake_call_llm(**kwargs):  # type: ignore[no-untyped-def]
        model_id = kwargs["model_id"]
        if model_id == "model-hop1":
            return {
                "text": json.dumps(
                    {
                        "artifacts": [
                            {"artifact_name": "OUT.json", "payload": {"items": [{"path": "x.py", "line_range": [1, 1]}]}}
                        ]
                    }
                ),
                "meta": {"failure_type": None, "status_code": 200},
            }
        return {
            "text": json.dumps(
                {
                    "artifacts": [
                        {
                            "artifact_name": "OUT.json",
                            "payload": {"items": [{"id": "A", "path": "x.py", "line_range": [1, 1]}]},
                        }
                    ]
                }
            ),
            "meta": {"failure_type": None, "status_code": 200},
        }

    monkeypatch.setattr(runner, "call_llm", fake_call_llm)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner),
    )
    assert stats["ok"] == 1
    assert stats["escalated_partitions"] == 1
    payload = json.loads((phase_dir / "raw" / "A1__A_P0001.json").read_text(encoding="utf-8"))
    assert payload["request_meta"]["route_hop_total"] == 2


def test_disable_escalation_forces_single_hop(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    phase_dir, prompt_spec, partitions = _prepare_step(runner, tmp_path)
    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(
        runner,
        "resolve_step_ladder",
        lambda routing_policy, phase, step_id: [
            ("openai", "model-hop1", "OPENAI_API_KEY"),
            ("openai", "model-hop2", "OPENAI_API_KEY"),
        ],
    )

    def fake_call_llm(**kwargs):  # type: ignore[no-untyped-def]
        return {
            "text": '{"artifacts":[{"artifact_name":"OUT.json","payload":"',
            "meta": {"failure_type": None, "status_code": 200},
        }

    monkeypatch.setattr(runner, "call_llm", fake_call_llm)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner, disable_escalation=True),
    )
    assert stats["ok"] == 0
    assert stats["failed"] == 1
    payload = json.loads((phase_dir / "raw" / "A1__A_P0001.FAILED.json").read_text(encoding="utf-8"))
    assert payload["request_meta"]["route_hop_total"] == 1


def _premium_synthesis_ladder():
    return [
        ("openrouter", "openai/gpt-5.3-codex", "OPENROUTER_API_KEY"),
        ("openrouter", "openai/gpt-5.2", "OPENROUTER_API_KEY"),
        ("openrouter", "anthropic/claude-opus-4-6", "OPENROUTER_API_KEY"),
    ]


def test_synthesis_schema_failure_blocks_opus() -> None:
    runner = _load_runner_module()
    cfg = replace(_make_cfg(runner), routing_policy="balanced_grok_openrouter")

    def execute_attempt(route, hop_index):  # type: ignore[no-untyped-def]
        return {
            "response_text": "",
            "request_meta": {
                "failure_type": None,
                "status_code": 200,
                "schema_gate_reason": "schema_missing_key:id",
            },
            "artifacts": [],
            "route": route,
            "artifacts_ok": False,
            "escalation_trigger": "schema_missing_key:id",
        }

    payload = runner.call_llm_with_ladder(
        phase="R",
        step_id="R1",
        partition_id="R_P0001",
        routing_policy="balanced_grok_openrouter",
        routing_tier="synthesis",
        ladder=_premium_synthesis_ladder(),
        cfg=cfg,
        execute_attempt=execute_attempt,
    )

    meta = payload["request_meta"]
    assert meta["route_hop_total"] == 2
    assert meta["provider"] == "openrouter"
    assert meta["model_id"] == "openai/gpt-5.2"
    assert meta["escalation_class"] == "schema_repair"
    assert meta["opus_eligible"] is False
    assert meta["opus_block_reason"] == "blocked_for_escalation_class:schema_repair"


def test_synthesis_invalid_json_blocks_opus() -> None:
    runner = _load_runner_module()
    cfg = replace(_make_cfg(runner), routing_policy="balanced_grok_openrouter")

    def execute_attempt(route, hop_index):  # type: ignore[no-untyped-def]
        return {
            "response_text": "",
            "request_meta": {
                "failure_type": None,
                "status_code": 200,
                "provider_error_reason": "invalid_json",
            },
            "artifacts": [],
            "route": route,
            "artifacts_ok": False,
            "escalation_trigger": "parse_failure",
        }

    payload = runner.call_llm_with_ladder(
        phase="S",
        step_id="S1",
        partition_id="S_P0001",
        routing_policy="balanced_grok_openrouter",
        routing_tier="synthesis",
        ladder=_premium_synthesis_ladder(),
        cfg=cfg,
        execute_attempt=execute_attempt,
    )

    meta = payload["request_meta"]
    assert meta["route_hop_total"] == 2
    assert meta["model_id"] == "openai/gpt-5.2"
    assert meta["escalation_class"] == "schema_repair"
    assert meta["opus_eligible"] is False


def test_synthesis_provider_transport_failure_blocks_opus() -> None:
    runner = _load_runner_module()
    cfg = replace(_make_cfg(runner), routing_policy="balanced_grok_openrouter")

    def execute_attempt(route, hop_index):  # type: ignore[no-untyped-def]
        return {
            "response_text": "",
            "request_meta": {
                "failure_type": "rate_limit",
                "status_code": 429,
            },
            "artifacts": [],
            "route": route,
            "artifacts_ok": False,
            "escalation_trigger": "provider_failure",
        }

    payload = runner.call_llm_with_ladder(
        phase="T",
        step_id="T1",
        partition_id="T_P0001",
        routing_policy="balanced_grok_openrouter",
        routing_tier="synthesis",
        ladder=_premium_synthesis_ladder(),
        cfg=cfg,
        execute_attempt=execute_attempt,
    )

    meta = payload["request_meta"]
    assert meta["route_hop_total"] == 2
    assert meta["model_id"] == "openai/gpt-5.2"
    assert meta["escalation_class"] == "provider_transport"
    assert meta["opus_eligible"] is False


def test_synthesis_hard_reconciliation_unlocks_opus() -> None:
    runner = _load_runner_module()
    cfg = replace(_make_cfg(runner), routing_policy="balanced_grok_openrouter")

    def execute_attempt(route, hop_index):  # type: ignore[no-untyped-def]
        if hop_index < 2:
            return {
                "response_text": "",
                "request_meta": {
                    "failure_type": "provider",
                    "status_code": 500,
                    "provider_error_reason": "merge_conflict",
                },
                "artifacts": [],
                "route": route,
                "artifacts_ok": False,
                "escalation_trigger": "provider_failure",
            }
        return {
            "response_text": json.dumps({"artifacts": [{"artifact_name": "OUT.json", "payload": {"items": []}}]}),
            "request_meta": {
                "failure_type": None,
                "status_code": 200,
            },
            "artifacts": [{"artifact_name": "OUT.json", "payload": {"items": []}}],
            "route": route,
            "artifacts_ok": True,
            "escalation_trigger": None,
        }

    payload = runner.call_llm_with_ladder(
        phase="R",
        step_id="R1",
        partition_id="R_P0001",
        routing_policy="balanced_grok_openrouter",
        routing_tier="synthesis",
        ladder=_premium_synthesis_ladder(),
        cfg=cfg,
        execute_attempt=execute_attempt,
    )

    meta = payload["request_meta"]
    assert meta["route_hop_total"] == 3
    assert meta["provider"] == "openrouter"
    assert meta["model_id"] == "anthropic/claude-opus-4-6"
    assert meta["opus_eligible"] is True
    assert meta["opus_block_reason"] is None
    assert meta["route_attempts"][1]["escalation_class"] == "hard_reconciliation"
