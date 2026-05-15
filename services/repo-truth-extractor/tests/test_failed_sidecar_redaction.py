from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path
from typing import Any

import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_runner_module() -> types.ModuleType:
    module_path = _repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5_failed_sidecars", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_cfg(runner: types.ModuleType) -> Any:
    cfg = runner.RunnerConfig.__new__(runner.RunnerConfig)
    defaults = {
        "dry_run": False,
        "max_files_docs": 10,
        "max_files_code": 10,
        "max_chars": 50000,
        "max_request_bytes": 100000,
        "file_truncate_chars": 10000,
        "home_scan_mode": "safe",
        "resume": False,
        "fail_fast_auth": False,
        "gemini_auth_mode": "auto",
        "gemini_transport": "sdk",
        "openai_transport": "openai_sdk",
        "xai_transport": "openai_sdk",
        "retry_policy": "none",
        "retry_max_attempts": 1,
        "retry_base_seconds": 0.0,
        "retry_max_seconds": 0.0,
        "phase_auth_fail_threshold": 5,
        "partition_workers": 1,
        "debug_phase_inputs": False,
        "fail_fast_missing_inputs": False,
        "executor": "thread",
        "routing_policy": "cost",
        "disable_escalation": True,
        "escalation_max_hops": 1,
        "batch_mode": False,
        "batch_provider": "auto",
        "batch_poll_seconds": 30,
        "batch_wait_timeout_seconds": 1,
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
        "fl_int_provider_timeout_seconds": 180,
        "fl_int_f0_batch_timeout_seconds": 210,
    }
    for key, value in defaults.items():
        object.__setattr__(cfg, key, value)
    return cfg


def _secret_value() -> str:
    return "sk-" + "RTEPKT15" + ("A" * 32)


def _prompt_spec(runner: types.ModuleType, tmp_path: Path, *, step_id: str = "A0") -> Any:
    prompt_path = tmp_path / f"PROMPT_{step_id}_TEST.md"
    prompt_path.write_text("Return OUT.json\n", encoding="utf-8")
    return runner.PromptSpec(
        step_id=step_id,
        prompt_path=prompt_path,
        output_artifacts=("OUT.json",),
        contract={},
    )


def _partition(tmp_path: Path) -> dict[str, Any]:
    source = tmp_path / "source.txt"
    source.write_text("fixture\n", encoding="utf-8")
    return {"id": "A_P0001", "paths": [str(source)]}


def _assert_secret_redacted(text: str, secret: str) -> None:
    assert secret not in text
    assert "[REDACTED]" in text


def test_worker_exception_failed_sidecars_redact_secret_text(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    secret = _secret_value()
    phase_dir = tmp_path / "A_repo_control_plane"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)

    def forbidden_call_llm(**kwargs: Any) -> dict[str, Any]:
        raise AssertionError("provider call path must not be reached")

    def raising_context(**kwargs: Any) -> tuple[str, dict[str, int]]:
        raise RuntimeError(f"worker failed with api_key={secret}")

    monkeypatch.setattr(runner, "call_llm", forbidden_call_llm)
    monkeypatch.setattr(runner, "build_partition_context", raising_context)

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=_prompt_spec(runner, tmp_path),
        partitions=[_partition(tmp_path)],
        phase_dir=phase_dir,
        cfg=_make_cfg(runner),
    )

    assert stats["failed"] == 1
    failed_text = (phase_dir / "raw" / "A0__A_P0001.FAILED.txt").read_text(encoding="utf-8")
    failed_json = json.loads(
        (phase_dir / "raw" / "A0__A_P0001.FAILED.json").read_text(encoding="utf-8")
    )
    _assert_secret_redacted(failed_text, secret)
    assert failed_json["failure_type"] == "worker_exception"
    assert failed_json["phase"] == "A"
    assert failed_json["step_id"] == "A0"
    assert failed_json["partition_id"] == "A_P0001"
    assert secret not in json.dumps(failed_json, sort_keys=True)


def test_parse_failure_failed_sidecars_redact_raw_response_text(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    secret = _secret_value()
    phase_dir = tmp_path / "A_repo_control_plane"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        runner,
        "build_partition_context",
        lambda **kwargs: (
            "PARTITION_PATH=source.txt",
            {"files_included": 1, "files_skipped": 0, "context_bytes": 10, "redaction_hits": 0},
        ),
    )
    monkeypatch.setattr(
        runner,
        "call_llm",
        lambda **kwargs: {
            "text": f"not json api_key={secret}",
            "meta": {"failure_type": None, "status_code": 200},
        },
    )

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=_prompt_spec(runner, tmp_path),
        partitions=[_partition(tmp_path)],
        phase_dir=phase_dir,
        cfg=_make_cfg(runner),
    )

    assert stats["failed"] == 1
    failed_text = (phase_dir / "raw" / "A0__A_P0001.FAILED.txt").read_text(encoding="utf-8")
    failed_json = json.loads(
        (phase_dir / "raw" / "A0__A_P0001.FAILED.json").read_text(encoding="utf-8")
    )
    _assert_secret_redacted(failed_text, secret)
    assert failed_json["failure_type"] == "parse"
    assert failed_json["status_code"] == 200
    assert failed_json["phase"] == "A"
    assert failed_json["step_id"] == "A0"
    assert failed_json["partition_id"] == "A_P0001"
    assert secret not in json.dumps(failed_json, sort_keys=True)


def test_schema_failure_failed_sidecars_redact_response_and_preserve_context(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    secret = _secret_value()
    phase_dir = tmp_path / "A_repo_control_plane"
    (phase_dir / "raw").mkdir(parents=True, exist_ok=True)
    response_payload = {
        "artifacts": [
            {
                "artifact_name": "OUT.json",
                "payload": {
                    "items": [
                        {
                            "id": "item-1",
                            "path": "services/demo.py",
                            "note": f"token={secret}",
                        }
                    ]
                },
            }
        ]
    }

    monkeypatch.setattr(
        runner,
        "build_partition_context",
        lambda **kwargs: (
            "PARTITION_PATH=source.txt",
            {"files_included": 1, "files_skipped": 0, "context_bytes": 10, "redaction_hits": 0},
        ),
    )
    monkeypatch.setattr(
        runner,
        "call_llm",
        lambda **kwargs: {
            "text": json.dumps(response_payload),
            "meta": {"failure_type": None, "status_code": 200},
        },
    )

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=_prompt_spec(runner, tmp_path),
        partitions=[_partition(tmp_path)],
        phase_dir=phase_dir,
        cfg=_make_cfg(runner),
    )

    assert stats["failed"] == 1
    failed_text = (phase_dir / "raw" / "A0__A_P0001.FAILED.txt").read_text(encoding="utf-8")
    failed_json = json.loads(
        (phase_dir / "raw" / "A0__A_P0001.FAILED.json").read_text(encoding="utf-8")
    )
    _assert_secret_redacted(failed_text, secret)
    assert failed_json["failure_type"] == "schema"
    assert failed_json["schema_gate_context"]["failure_reason"] == "schema_missing_key:line_range"
    assert failed_json["schema_gate_context"]["artifact_name"] == "OUT.json"
    assert failed_json["schema_gate_context"]["item_id"] == "item-1"
    assert failed_json["schema_gate_context"]["item_path"] == "services/demo.py"
    assert secret not in json.dumps(failed_json, sort_keys=True)


def test_batch_watch_failure_sidecars_redact_provider_error_text(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    secret = _secret_value()
    root = tmp_path / "repo"
    run_id = "run-rte-pkt-15"
    phase_dir = tmp_path / run_id / "A_repo_control_plane"
    batch_dir = phase_dir / "batch"
    inputs_dir = phase_dir / "inputs"
    raw_dir = phase_dir / "raw"
    batch_dir.mkdir(parents=True, exist_ok=True)
    inputs_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)
    index_payload = {
        "jobs": [
            {
                "phase_id": "A",
                "step_id": "A0",
                "partition_id": "A_P0001",
                "provider_id": "openai",
                "model_id": "gpt-test",
                "api_key_env": "OPENAI_API_KEY",
                "job_id": "batch-job-1",
                "state": "completed",
            }
        ]
    }
    (batch_dir / "BATCH_JOB_INDEX.json").write_text(
        json.dumps(index_payload), encoding="utf-8"
    )
    (inputs_dir / "PARTITIONS.json").write_text(
        json.dumps({"partitions": [{"id": "A_P0001", "paths": []}]}),
        encoding="utf-8",
    )

    class FakeBatchClient:
        def fetch_results(self, job_id: str) -> list[Any]:
            assert job_id == "batch-job-1"
            return [
                types.SimpleNamespace(
                    custom_id="A_P0001",
                    output_text="",
                    error=f"provider failed with Authorization: Bearer {secret}",
                    meta={},
                )
            ]

    monkeypatch.setattr(
        runner,
        "get_phase_prompts",
        lambda phase: [_prompt_spec(runner, tmp_path)],
    )
    monkeypatch.setattr(
        runner,
        "resolve_api_key",
        lambda provider, api_key_env: ("offline-test-key", api_key_env),
    )
    monkeypatch.setattr(runner, "build_batch_client", lambda provider, api_key, cfg: FakeBatchClient())
    monkeypatch.setattr(runner, "maybe_send_batch_webhook", lambda **kwargs: True)

    with pytest.raises(RuntimeError, match="Parse failure threshold exceeded"):
        runner.run_batch_watch(
            root=root,
            run_id=run_id,
            phase="A",
            dirs={"A": phase_dir},
            cfg=_make_cfg(runner),
        )

    failed_text = (raw_dir / "A0__A_P0001.FAILED.txt").read_text(encoding="utf-8")
    failed_json = json.loads((raw_dir / "A0__A_P0001.FAILED.json").read_text(encoding="utf-8"))
    _assert_secret_redacted(failed_text, secret)
    assert failed_json["failure_type"] == "provider"
    assert failed_json["request_meta"]["execution_mode"] == "batch_watch"
    assert failed_json["request_meta"]["provider"] == "openai"
    assert failed_json["request_meta"]["model_id"] == "gpt-test"
    assert failed_json["request_meta"]["batch_job_id"] == "batch-job-1"
    assert secret not in json.dumps(failed_json, sort_keys=True)


def test_failed_sidecar_text_writer_redacts_batch_terminal_text(tmp_path: Path) -> None:
    runner = _load_runner_module()
    secret = _secret_value()
    failed_path = tmp_path / "raw" / "A0__A_P0001.FAILED.txt"

    runner.write_failed_sidecar_text(
        failed_path,
        f"batch_terminal_state:failed Authorization: Bearer {secret}\n",
    )

    failed_text = failed_path.read_text(encoding="utf-8")
    _assert_secret_redacted(failed_text, secret)
    assert "batch_terminal_state:failed" in failed_text
