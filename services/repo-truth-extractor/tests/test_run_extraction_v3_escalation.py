from __future__ import annotations

import importlib.util
import json
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
