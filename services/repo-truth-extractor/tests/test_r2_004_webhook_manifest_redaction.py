"""TP-RTE-TRUTH-R2-004 / F-19d -- RUN_MANIFEST must not embed the raw
dpmx_webhook_url (a bearer-equivalent capability URL). Only presence
(dpmx_webhook_url_set) may be recorded, matching the treatment already
applied to dpmx_webhook_secret_set.

Exercises reporting.write_run_manifest directly (the function this packet
fixes) with a real argparse.Namespace built from the actual v5 CLI parser
(so every args.* attribute the function reads is populated with real
defaults) and lightweight stub ReportingDeps for everything unrelated to
the webhook fields, so the test stays fast and offline.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = REPO_ROOT / "services" / "repo-truth-extractor"

for path in (str(SERVICE_ROOT),):
    if path not in sys.path:
        sys.path.insert(0, path)


def _load_module(name: str, relative_path: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, SERVICE_ROOT / relative_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _load_runner():
    return _load_module("run_extraction_v5_r2_004_manifest", "run_extraction_v5.py")


def _build_deps(reporting, *, captured: dict, tmp_path: Path):
    def _write_json(path: Path, payload: Any) -> None:
        captured["path"] = path
        captured["payload"] = payload
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def _current_output_layout(root: Path):
        return SimpleNamespace(
            extraction_root=root,
            runs_root=root / "runs",
            latest_run_file=root / "latest_run_id.txt",
            doctor_root=root / "doctor",
        )

    return reporting.ReportingDeps(
        write_json=_write_json,
        now_iso=lambda: "2026-07-27T00:00:00+00:00",
        get_git_sha=lambda root: "deadbeef",
        sha256_text=lambda p: "sha",
        promptset_fingerprint=lambda phases: {
            "blocked_promptset": False,
            "prompt_hashes": [],
            "prompt_missing": [],
            "prompt_unreadable": [],
            "prompt_hash_errors": [],
            "prompt_failures": [],
            "prompt_failures_count": 0,
            "promptset_sha256": "sha256:stub",
        },
        refresh_run_manifest_artifacts=lambda root, dirs: None,
        compute_run_status=lambda *a, **k: "OK",
        update_run_manifest_status=lambda *a, **k: "OK",
        read_step_qa_payloads=lambda root: [],
        coverage_for_phase=lambda phase, root: {},
        write_strict_passthrough_attestations=lambda dirs, run_id, phases: {},
        current_output_layout=_current_output_layout,
        current_doctor_root=lambda root: root / "doctor",
        load_json=lambda p: {},
        read_repair_counters=lambda: {},
        get_phase_prompts=lambda phase: [],
        resolve_effective_step_tier=lambda *a, **k: "default",
        routing_ladders_payload=lambda: {},
        effective_model_routing_payload=lambda: {},
        benchmark_route_ownership_payload=lambda **k: {},
        blocked_promptset_payload=lambda report, at: {},
        resume_blocked_payload=lambda report: {},
        expected_artifact_present=lambda root, name: True,
        is_cost_abort_triggered=lambda: False,
        promptset_blocked_reason="promptset_blocked",
        prompt_hash_mode="sha256",
        phases=("A",),
        runner_script=SERVICE_ROOT / "run_extraction_v5.py",
        default_routing_policy="cost",
        routing_policy_version="v1",
        s_prompts_legacy="legacy",
        dpmx_webhook_url_env="DPMX_WEBHOOK_URL",
        dpmx_webhook_secret_env="DPMX_WEBHOOK_SECRET",
        dpmx_webhook_timeout_seconds_env="DPMX_WEBHOOK_TIMEOUT_SECONDS",
        dpmx_webhook_required_env="DPMX_WEBHOOK_REQUIRED",
        dpmx_webhook_auto_continue_env="DPMX_WEBHOOK_AUTO_CONTINUE",
        dpmx_live_ok_env="DPMX_LIVE_OK",
    )


def test_write_run_manifest_stores_webhook_presence_flag_not_raw_url(
    monkeypatch, tmp_path: Path
) -> None:
    runner = _load_runner()
    import reporting  # noqa: E402  (SERVICE_ROOT is on sys.path above)

    secret_url = "https://hooks.example.test/services/T000/B000/verysecrettoken12345"
    monkeypatch.setenv("DPMX_WEBHOOK_URL", secret_url)
    monkeypatch.setenv("DPMX_WEBHOOK_SECRET", "shhh-its-a-secret")

    parser = runner.build_parser()
    args = parser.parse_args(["--phase", "A", "--dry-run", "--run-id", "webhook_flag_test"])

    run_context = SimpleNamespace(
        source="explicit",
        latest_written=False,
        latest_file=tmp_path / "latest_run_id.txt",
    )
    dirs = {"root": tmp_path / "runs" / "webhook_flag_test"}
    dirs["root"].mkdir(parents=True, exist_ok=True)

    captured: dict = {}
    deps = _build_deps(reporting, captured=captured, tmp_path=tmp_path)

    reporting.write_run_manifest(
        deps,
        tmp_path,
        dirs,
        "webhook_flag_test",
        args,
        run_context,
        ["A"],
    )

    assert captured, "write_json was never called -- write_run_manifest did not run"
    cli = captured["payload"]["cli"]

    # The old, leaky key must be gone entirely.
    assert "dpmx_webhook_url" not in cli
    # The new presence-only flag must be True (env var was set).
    assert cli["dpmx_webhook_url_set"] is True
    # Matches the pre-existing treatment of the adjacent secret.
    assert cli["dpmx_webhook_secret_set"] is True

    # Belt-and-suspenders: the raw secret value must not appear anywhere in
    # the serialized manifest that gets written to disk.
    manifest_path = dirs["root"] / "RUN_MANIFEST.json"
    assert manifest_path.exists()
    raw_text = manifest_path.read_text(encoding="utf-8")
    assert secret_url not in raw_text
    assert "verysecrettoken12345" not in raw_text


def test_write_run_manifest_webhook_flag_is_false_when_unset(
    monkeypatch, tmp_path: Path
) -> None:
    runner = _load_runner()
    import reporting  # noqa: E402

    monkeypatch.delenv("DPMX_WEBHOOK_URL", raising=False)
    monkeypatch.delenv("DPMX_WEBHOOK_SECRET", raising=False)

    parser = runner.build_parser()
    args = parser.parse_args(["--phase", "A", "--dry-run", "--run-id", "webhook_flag_unset"])

    run_context = SimpleNamespace(
        source="explicit",
        latest_written=False,
        latest_file=tmp_path / "latest_run_id.txt",
    )
    dirs = {"root": tmp_path / "runs" / "webhook_flag_unset"}
    dirs["root"].mkdir(parents=True, exist_ok=True)

    captured: dict = {}
    deps = _build_deps(reporting, captured=captured, tmp_path=tmp_path)

    reporting.write_run_manifest(
        deps,
        tmp_path,
        dirs,
        "webhook_flag_unset",
        args,
        run_context,
        ["A"],
    )

    cli = captured["payload"]["cli"]
    assert "dpmx_webhook_url" not in cli
    assert cli["dpmx_webhook_url_set"] is False
    assert cli["dpmx_webhook_secret_set"] is False
