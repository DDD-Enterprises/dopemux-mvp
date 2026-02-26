from __future__ import annotations

from dataclasses import replace
import importlib.util
import json
from pathlib import Path
from typing import Any, Dict, List


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


class _WebhookResponse:
    def __init__(self, status: int = 204) -> None:
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


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


def test_send_webhook_success_includes_signature(monkeypatch) -> None:
    runner = _load_runner_module()
    captured = {}

    def _fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        captured["request"] = request
        captured["timeout"] = timeout
        return _WebhookResponse(status=204)

    monkeypatch.setattr(runner.urllib_request, "urlopen", _fake_urlopen)
    payload = {"schema": "DPMX_WEBHOOK_V1", "event": "batch.completed", "event_id": "evt_test"}
    ok, status_code, err = runner.send_webhook(
        payload,
        webhook_url="https://example.com/webhook",
        webhook_secret="topsecret",
        timeout_seconds=7,
    )

    assert ok is True
    assert status_code == 204
    assert err is None
    assert captured["timeout"] == 7
    request = captured["request"]
    headers = {k.lower(): v for k, v in request.header_items()}
    assert "x-dopemux-signature" in headers
    assert headers["x-dopemux-event"] == "batch.completed"


def test_send_webhook_http_error(monkeypatch) -> None:
    runner = _load_runner_module()

    def _fake_urlopen(request, timeout):  # type: ignore[no-untyped-def]
        raise runner.urllib_error.HTTPError(request.full_url, 502, "bad gateway", None, None)

    monkeypatch.setattr(runner.urllib_request, "urlopen", _fake_urlopen)
    ok, status_code, err = runner.send_webhook(
        {"schema": "DPMX_WEBHOOK_V1", "event": "batch.completed", "event_id": "evt_http_error"},
        webhook_url="https://example.com/webhook",
        webhook_secret="",
        timeout_seconds=5,
    )

    assert ok is False
    assert status_code == 502
    assert err == "http_error:502"


def test_run_batch_watch_marks_missing_api_key(monkeypatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "Q_quality_assurance"
    batch_dir = phase_dir / "batch"
    batch_dir.mkdir(parents=True, exist_ok=True)
    runner.write_json(
        batch_dir / "BATCH_JOB_INDEX.json",
        {
            "run_id": "rid",
            "phase_id": "Q",
            "jobs": [
                {
                    "run_id": "rid",
                    "phase_id": "Q",
                    "step_id": "Q0",
                    "partition_id": "Q_P0001",
                    "provider_id": "openai",
                    "model_id": "gpt-5-nano",
                    "api_key_env": "OPENAI_API_KEY",
                    "job_id": "job-1",
                    "state": "submitted",
                    "submitted_at_utc": "2026-02-21T00:00:00Z",
                }
            ],
        },
    )
    monkeypatch.setattr(runner, "resolve_api_key", lambda provider, api_key_env: ("", api_key_env))
    monkeypatch.setattr(runner, "normalize_step", lambda **kwargs: None)

    cfg = _make_cfg(runner)
    result = runner.run_batch_watch(
        root=tmp_path,
        run_id="rid",
        phase="Q",
        dirs={"Q": phase_dir},
        cfg=cfg,
    )

    assert result.exit_code == 0
    payload = json.loads((batch_dir / "BATCH_JOB_INDEX.json").read_text(encoding="utf-8"))
    job = payload["jobs"][0]
    assert job["state"] == "failed"
    assert str(job["error"]).startswith("missing_api_key")


def test_run_batch_watch_auto_continue_blocked_without_live_guard(tmp_path: Path) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "Q_quality_assurance"
    batch_dir = phase_dir / "batch"
    batch_dir.mkdir(parents=True, exist_ok=True)
    runner.write_json(
        batch_dir / "BATCH_JOB_INDEX.json",
        {
            "run_id": "rid",
            "phase_id": "Q",
            "jobs": [
                {
                    "run_id": "rid",
                    "phase_id": "Q",
                    "step_id": "Q0",
                    "partition_id": "Q_P0001",
                    "provider_id": "openai",
                    "model_id": "gpt-5-nano",
                    "api_key_env": "OPENAI_API_KEY",
                    "job_id": "job-2",
                    "state": "completed",
                    "results_applied": True,
                }
            ],
        },
    )

    cfg = replace(
        _make_cfg(runner),
        webhook_auto_continue=True,
        live_ok=False,
    )
    result = runner.run_batch_watch(
        root=tmp_path,
        run_id="rid",
        phase="Q",
        dirs={"Q": phase_dir},
        cfg=cfg,
    )

    assert result.exit_code == 0
    assert result.auto_continue_blocked is True
    assert result.next_phase is None


class _FakeFinalizeStore:
    def __init__(
        self,
        *,
        pending_jobs: List[Dict[str, Any]],
        completed_refs: List[str],
        latest_attempt: int | None = 1,
    ) -> None:
        self._pending_jobs = pending_jobs
        self._completed_refs = completed_refs
        self._latest_attempt = latest_attempt
        self.status_updates: List[Dict[str, Any]] = []

    def list_pending_jobs(self, provider: str, run_id: str, phase: str) -> List[Dict[str, Any]]:
        return list(self._pending_jobs)

    def list_completed_provider_refs(self, provider: str, run_id: str, phase: str) -> List[str]:
        return list(self._completed_refs)

    def latest_attempt_for_tuple(
        self, run_id: str, phase: str, step_id: str, partition_id: str
    ) -> int | None:
        return self._latest_attempt

    def update_async_job_status(
        self, provider: str, external_job_id: str, attempt: int, status: str, last_error: str | None
    ) -> None:
        self.status_updates.append(
            {
                "provider": provider,
                "external_job_id": external_job_id,
                "attempt": attempt,
                "status": status,
                "last_error": last_error,
            }
        )


def test_run_phase_r_finalize_no_pending_jobs_returns_zero(monkeypatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "R_arbitration"
    phase_dir.mkdir(parents=True, exist_ok=True)

    fake_store = _FakeFinalizeStore(pending_jobs=[], completed_refs=[])
    monkeypatch.setattr(runner, "_build_event_store_for_runner", lambda: fake_store)

    finalized = runner.run_phase_R_finalize(
        run_id="rid-finalize-empty",
        dirs={"R": phase_dir},
        cfg=_make_cfg(runner),
    )

    assert finalized == 0
    assert fake_store.status_updates == []


def test_run_phase_r_finalize_writes_output_and_marks_completed(monkeypatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "R_arbitration"
    raw_dir = phase_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    pending = {
        "step_id": "R1",
        "partition_id": "R_P0001",
        "attempt": 1,
        "external_job_id": "resp_1",
    }
    pending_placeholder = raw_dir / "R1__R_P0001.PENDING.json"
    pending_placeholder.write_text("{\"status\":\"pending\"}\n", encoding="utf-8")

    fake_store = _FakeFinalizeStore(
        pending_jobs=[pending],
        completed_refs=["resp_1"],
        latest_attempt=1,
    )
    monkeypatch.setattr(runner, "_build_event_store_for_runner", lambda: fake_store)

    prompt_path = tmp_path / "PROMPT_R1_TEST.md"
    prompt_path.write_text("Goal: R1_OUT.json\n", encoding="utf-8")
    monkeypatch.setattr(
        runner,
        "get_phase_prompts",
        lambda phase: [runner.PromptSpec(step_id="R1", prompt_path=prompt_path, output_artifacts=("R1_OUT.json",))]
        if phase == "R"
        else [],
    )
    monkeypatch.setattr(runner, "_fetch_webhook_payload_for_job", lambda event_store, run_id, provider_ref: {})
    monkeypatch.setattr(
        runner,
        "_extract_openai_response_text",
        lambda payload: json.dumps(
            {"artifacts": [{"artifact_name": "R1_OUT.json", "payload": {"value": 1}}]}
        ),
    )

    finalized = runner.run_phase_R_finalize(
        run_id="rid-finalize-write",
        dirs={"R": phase_dir},
        cfg=_make_cfg(runner),
    )

    assert finalized == 1
    out_json = raw_dir / "R1__R_P0001.json"
    assert out_json.exists()
    payload = json.loads(out_json.read_text(encoding="utf-8"))
    assert payload["phase"] == "R"
    assert payload["step_id"] == "R1"
    assert payload["request_meta"]["execution_mode"] == "async"
    assert payload["request_meta"]["external_job_id"] == "resp_1"
    assert not pending_placeholder.exists()
    assert any(update["status"] == "completed" for update in fake_store.status_updates)


def test_run_phase_r_finalize_orphans_stale_attempt(monkeypatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "R_arbitration"
    raw_dir = phase_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    pending = {
        "step_id": "R1",
        "partition_id": "R_P0001",
        "attempt": 1,
        "external_job_id": "resp_old",
    }
    fake_store = _FakeFinalizeStore(
        pending_jobs=[pending],
        completed_refs=["resp_old"],
        latest_attempt=2,
    )
    monkeypatch.setattr(runner, "_build_event_store_for_runner", lambda: fake_store)
    monkeypatch.setattr(runner, "get_phase_prompts", lambda phase: [])

    finalized = runner.run_phase_R_finalize(
        run_id="rid-finalize-stale",
        dirs={"R": phase_dir},
        cfg=_make_cfg(runner),
    )

    assert finalized == 0
    out_json = raw_dir / "R1__R_P0001.json"
    assert not out_json.exists()
    assert any(
        update["status"] == "orphaned" and update["last_error"] == "stale_attempt"
        for update in fake_store.status_updates
    )
