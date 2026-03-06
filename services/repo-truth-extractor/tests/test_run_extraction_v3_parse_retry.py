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


def _prepare_step(runner, tmp_path: Path):
    phase_dir = tmp_path / "A_repo_control_plane"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
    prompt = tmp_path / "PROMPT_A0_TEST.md"
    prompt.write_text("Goal: OUT.json\n", encoding="utf-8")
    prompt_spec = runner.PromptSpec(step_id="A0", prompt_path=prompt, output_artifacts=("OUT.json",))
    partitions = [{"id": "A_P0001", "paths": ["/tmp/p1"]}]
    return phase_dir, prompt_spec, partitions


def _fake_context(**kwargs):  # type: ignore[no-untyped-def]
    return (
        "PARTITION_PATH=/tmp/p1",
        {"files_included": 1, "files_skipped": 0, "context_bytes": 20, "redaction_hits": 0},
    )


def test_parse_retry_succeeds_on_second_attempt(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    phase_dir, prompt_spec, partitions = _prepare_step(runner, tmp_path)
    calls = {"count": 0}
    responses = [
        (
            '{"artifacts":[{"artifact_name":"OUT.json","payload":"',
            {
                "failure_type": None,
                "status_code": 200,
                "response_received": True,
                "response_summary": {"finish_reason": "MAX_TOKENS"},
            },
        ),
        (
            json.dumps({"artifacts": [{"artifact_name": "OUT.json", "payload": {"ok": True}}]}),
            {
                "failure_type": None,
                "status_code": 200,
                "response_received": True,
                "response_summary": {"finish_reason": "STOP"},
            },
        ),
    ]

    def fake_call_llm(**kwargs):  # type: ignore[no-untyped-def]
        calls["count"] += 1
        idx = min(calls["count"] - 1, len(responses) - 1)
        text, meta = responses[idx]
        return {"text": text, "meta": dict(meta)}

    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(runner, "call_llm", fake_call_llm)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner),
    )

    assert calls["count"] == 2
    assert stats["ok"] == 1
    assert stats["failed"] == 0
    payload = json.loads((phase_dir / "raw" / "A0__A_P0001.json").read_text(encoding="utf-8"))
    request_meta = payload["request_meta"]
    assert request_meta["parse_retry_attempted"] is True
    assert request_meta["parse_retry_attempts"] == 1
    assert request_meta["parse_retry_reason"] == "max_tokens_string_eof_parse_failure"
    assert len(request_meta["parse_retry_trace"]) == 2
    assert request_meta["parse_retry_trace"][0]["artifacts_ok"] is False
    assert request_meta["parse_retry_trace"][1]["artifacts_ok"] is True
    assert not (phase_dir / "raw" / "A0__A_P0001.FAILED.txt").exists()
    assert not (phase_dir / "raw" / "A0__A_P0001.FAILED.json").exists()


def test_parse_retry_used_for_json_contract_failures_even_without_max_tokens(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    phase_dir, prompt_spec, partitions = _prepare_step(runner, tmp_path)
    calls = {"count": 0}
    responses = [
        (
            '{"artifacts":[{"artifact_name":"OUT.json","payload":"',
            {
                "failure_type": None,
                "status_code": 200,
                "response_received": True,
                "response_summary": {"finish_reason": "STOP"},
            },
        ),
        (
            json.dumps({"artifacts": [{"artifact_name": "OUT.json", "payload": {"ok": True}}]}),
            {
                "failure_type": None,
                "status_code": 200,
                "response_received": True,
                "response_summary": {"finish_reason": "STOP"},
            },
        ),
    ]

    def fake_call_llm(**kwargs):  # type: ignore[no-untyped-def]
        calls["count"] += 1
        idx = min(calls["count"] - 1, len(responses) - 1)
        text, meta = responses[idx]
        return {"text": text, "meta": dict(meta)}

    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(runner, "call_llm", fake_call_llm)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner),
    )

    assert calls["count"] == 2
    assert stats["ok"] == 1
    assert stats["failed"] == 0
    payload = json.loads((phase_dir / "raw" / "A0__A_P0001.json").read_text(encoding="utf-8"))
    request_meta = payload["request_meta"]
    assert request_meta["parse_retry_attempted"] is True
    assert request_meta["parse_retry_attempts"] == 1
    assert request_meta["parse_retry_reason"] == "json_contract_parse_failure"
    assert len(request_meta["parse_retry_trace"]) == 2


def test_parse_retry_used_for_mid_body_corruption(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    phase_dir, prompt_spec, partitions = _prepare_step(runner, tmp_path)
    calls = {"count": 0}
    responses = [
        (
            '{"artifacts":[{"artifact_name":"OUT.json","payload":"bad\\q"}]}',
            {
                "failure_type": None,
                "status_code": 200,
                "response_received": True,
                "response_summary": {"finish_reason": "MAX_TOKENS"},
            },
        ),
        (
            json.dumps({"artifacts": [{"artifact_name": "OUT.json", "payload": {"ok": True}}]}),
            {
                "failure_type": None,
                "status_code": 200,
                "response_received": True,
                "response_summary": {"finish_reason": "STOP"},
            },
        ),
    ]

    def fake_call_llm(**kwargs):  # type: ignore[no-untyped-def]
        calls["count"] += 1
        idx = min(calls["count"] - 1, len(responses) - 1)
        text, meta = responses[idx]
        return {"text": text, "meta": dict(meta)}

    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(runner, "call_llm", fake_call_llm)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner),
    )

    assert calls["count"] == 2
    assert stats["ok"] == 1
    assert stats["failed"] == 0
    payload = json.loads((phase_dir / "raw" / "A0__A_P0001.json").read_text(encoding="utf-8"))
    request_meta = payload["request_meta"]
    assert request_meta["parse_retry_attempted"] is True
    assert request_meta["parse_retry_attempts"] == 1
    assert request_meta["parse_retry_reason"] == "json_contract_parse_failure"
    assert request_meta["parse_retry_trace"][0]["strict_string_literal_error"] is True
    assert request_meta["parse_retry_trace"][0]["strict_semantic_eof_eligible"] is False


def test_parse_retry_exhausted_after_single_extra_attempt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    phase_dir, prompt_spec, partitions = _prepare_step(runner, tmp_path)
    calls = {"count": 0}

    def fake_call_llm(**kwargs):  # type: ignore[no-untyped-def]
        calls["count"] += 1
        return {
            "text": '{"artifacts":[{"artifact_name":"OUT.json","payload":"',
            "meta": {
                "failure_type": None,
                "status_code": 200,
                "response_received": True,
                "response_summary": {"finish_reason": "MAX_TOKENS"},
            },
        }

    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(runner, "call_llm", fake_call_llm)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner),
    )

    assert calls["count"] == 2
    assert stats["ok"] == 0
    assert stats["failed"] == 1
    failed = json.loads((phase_dir / "raw" / "A0__A_P0001.FAILED.json").read_text(encoding="utf-8"))
    request_meta = failed["request_meta"]
    assert request_meta["parse_retry_attempted"] is True
    assert request_meta["parse_retry_attempts"] == 1
    assert request_meta["parse_retry_reason"] == "max_tokens_string_eof_parse_failure"
    assert len(request_meta["parse_retry_trace"]) == 2
    assert request_meta["parse_retry_trace"][0]["artifacts_ok"] is False
    assert request_meta["parse_retry_trace"][1]["artifacts_ok"] is False
