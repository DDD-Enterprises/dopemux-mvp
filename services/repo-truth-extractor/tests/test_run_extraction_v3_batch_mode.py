from __future__ import annotations

import importlib.util
import json
from pathlib import Path


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
        routing_policy="cost",
        batch_mode=True,
        batch_provider="openai",
        batch_poll_seconds=1,
        batch_wait_timeout_seconds=60,
        batch_max_requests_per_job=2000,
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


class _FakeBatchClient:
    def submit(self, requests, route, step_context):  # type: ignore[no-untyped-def]
        return "job-123"

    def poll(self, job_id):  # type: ignore[no-untyped-def]
        return "completed"

    def fetch_results(self, job_id):  # type: ignore[no-untyped-def]
        return [
            _BatchResultShim(
                custom_id="A_P0001",
                output_text=json.dumps({"artifacts": [{"artifact_name": "OUT.json", "payload": {"items": []}}]}),
                error=None,
            )
        ]

    def cancel(self, job_id):  # type: ignore[no-untyped-def]
        return None


class _BatchResultShim:
    def __init__(self, custom_id: str, output_text: str, error: str | None) -> None:
        self.custom_id = custom_id
        self.output_text = output_text
        self.error = error


def test_batch_mode_writes_batch_artifacts_and_request_meta(monkeypatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    phase_dir, prompt_spec, partitions = _prepare_step(runner, tmp_path)
    monkeypatch.setattr(runner, "build_partition_context", _fake_context)
    monkeypatch.setattr(
        runner,
        "resolve_step_ladder",
        lambda routing_policy, phase, step_id: [("openai", "gpt-5-nano", "OPENAI_API_KEY")],
    )
    monkeypatch.setattr(runner, "resolve_api_key", lambda provider, api_key_env: ("fake-key", api_key_env))
    monkeypatch.setattr(runner, "build_batch_client", lambda provider, api_key, cfg: _FakeBatchClient())

    stats = runner.execute_step_for_partitions(
        phase="A",
        prompt_spec=prompt_spec,
        partitions=partitions,
        phase_dir=phase_dir,
        cfg=_make_cfg(runner),
    )

    assert stats["ok"] == 1
    payload = json.loads((phase_dir / "raw" / "A1__A_P0001.json").read_text(encoding="utf-8"))
    assert payload["request_meta"]["execution_mode"] == "batch"
    assert payload["request_meta"]["batch_provider"] == "openai"
    assert payload["request_meta"]["batch_job_id"] == "job-123"

    batch_dir = phase_dir / "batch"
    assert (batch_dir / "A1.requests.jsonl").exists()
    assert (batch_dir / "A1.job.json").exists()
    assert (batch_dir / "A1.results.jsonl").exists()
    assert (batch_dir / "A1.summary.json").exists()
