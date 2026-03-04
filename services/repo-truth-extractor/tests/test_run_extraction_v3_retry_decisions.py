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
    )


def test_parse_retry_reason_returns_generic_contract_reason_for_jsonish_parse_failures() -> None:
    runner = _load_runner_module()
    response_text = '{"artifacts":[{"artifact_name":"OUT.json","payload":"unterminated'
    exc = runner._strict_decode_error(response_text)
    reason = runner._parse_retry_reason(
        response_text,
        {
            "failure_type": None,
            "status_code": 200,
            "response_received": True,
            "response_summary": {"finish_reason": "STOP"},
        },
        exc,
    )
    assert reason == "json_contract_parse_failure"


def test_execute_step_emits_failed_sidecar_for_unparseable_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "A_repo_control_plane"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)

    prompt = tmp_path / "PROMPT_A0_TEST.md"
    prompt.write_text("Goal: OUT.json\n", encoding="utf-8")
    prompt_spec = runner.PromptSpec(step_id="A0", prompt_path=prompt, output_artifacts=("OUT.json",))
    partitions = [{"id": "A_P0001", "paths": ["/tmp/p1"]}]

    def fake_ctx(**_kwargs):  # type: ignore[no-untyped-def]
        return "PARTITION_PATH=/tmp/p1", {"files_included": 1, "files_skipped": 0, "context_bytes": 10, "redaction_hits": 0}

    def fake_call_llm(**_kwargs):  # type: ignore[no-untyped-def]
        return {
            "text": '{"artifacts":[{"artifact_name":"OUT.json","payload":"unterminated',
            "meta": {"failure_type": None, "status_code": 200, "response_received": True, "response_summary": {"finish_reason": "STOP"}},
        }

    monkeypatch.setattr(runner, "build_partition_context", fake_ctx)
    monkeypatch.setattr(runner, "call_llm", fake_call_llm)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner),
    )

    assert stats["ok"] == 0
    assert stats["failed"] == 1
    failed_json = json.loads((phase_dir / "raw" / "A0__A_P0001.FAILED.json").read_text(encoding="utf-8"))
    assert failed_json["failure_type"] == "parse"
