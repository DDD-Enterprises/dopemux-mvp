from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

# Direct imports to avoid sys.modules string resolution issues
from dopemux.commands import extractor_validation
from dopemux.commands.extractor_validation import (
    LiveValidationRunner,
    ValidationConfig,
    _compare_prompt_step_sets,
    _estimate_upper_bound_spend,
    _normalize_payload,
    _phase_missing_required_artifacts,
)


def test_estimate_upper_bound_spend_uses_route_counts_and_reports_missing_routes() -> None:
    payload = {
        "step_done_route_counts": {
            "xai/grok-code-fast-1": 3,
            "gemini/gemini-2.5-pro": 2,
            "openrouter/openai/gpt-5.2-chat": 1,
        }
    }
    pricing = {
        "xai/grok-code-fast-1": 0.4,
        "gemini/gemini-2.5-pro": 0.75,
    }

    result = _estimate_upper_bound_spend(payload, pricing)

    assert result["estimated_upper_bound_usd"] == 2.7
    assert result["missing_routes"] == ["openrouter/openai/gpt-5.2-chat"]
    assert result["matched_routes"]["xai/grok-code-fast-1"]["count"] == 3


def test_normalize_payload_strips_ephemeral_keys() -> None:
    payload = {
        "generated_at": "2026-03-26T12:00:00Z",
        "run_id": "abc",
        "stable": {"value": 1, "updated_at": "2026-03-26T12:00:01Z"},
        "rows": [{"ts": "2026-03-26T12:00:02Z", "status": "PASS"}],
    }

    normalized = _normalize_payload(payload)

    assert "generated_at" not in normalized
    assert "run_id" not in normalized
    assert "updated_at" not in normalized["stable"]
    assert normalized["rows"][0] == {"status": "PASS"}


def test_phase_missing_required_artifacts_uses_phase_status() -> None:
    coverage_rollup = {"phases": {"D": {"status": "PASS"}, "C": {"status": "FAIL"}}}

    assert _phase_missing_required_artifacts(coverage_rollup, "D") == []
    assert _phase_missing_required_artifacts(coverage_rollup, "C") == ["C:status=FAIL"]
    assert _phase_missing_required_artifacts(coverage_rollup, "R") == ["R:missing_phase_row"]


def test_compare_prompt_step_sets_reports_missing_and_extra_steps() -> None:
    result = _compare_prompt_step_sets(
        required_steps=["C0", "C1", "C2"],
        observed_steps=["c0", "C2", "C3"],
    )

    assert result["required_steps"] == ["C0", "C1", "C2"]
    assert result["observed_steps"] == ["C0", "C2", "C3"]
    assert result["missing_steps"] == ["C1"]
    assert result["extra_steps"] == ["C3"]
    assert result["matches"] is False


def test_run_command_records_timeout_as_failed_step(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "services" / "repo-truth-extractor").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        extractor_validation, "_resolve_extractor_root",
        lambda _cwd: repo_root,
    )

    runner = LiveValidationRunner(
        ValidationConfig(
            promptset_root=repo_root,
            report_root=Path("reports/repo-truth-extractor/validation"),
        )
    )

    def fake_run(*args, **kwargs):  # type: ignore[no-untyped-def]
        raise subprocess.TimeoutExpired(cmd=kwargs.get("args", args[0]), timeout=3.0, output="partial", stderr="late")

    monkeypatch.setattr(extractor_validation.subprocess, "run", fake_run)

    record = runner._run_command(
        "timeout_case",
        ["fake", "command"],
        timeout_seconds=3.0,
    )

    assert record.status == "fail"
    assert record.exit_code is None
    assert record.detail == "timed out after 3.0s"
    assert Path(record.stdout_path).read_text(encoding="utf-8") == "partial"
    assert Path(record.stderr_path).read_text(encoding="utf-8") == "late"


def test_repo_local_cli_origin_guard_fails_for_site_packages(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "services" / "repo-truth-extractor").mkdir(parents=True, exist_ok=True)
    (repo_root / "src" / "dopemux").mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(
        extractor_validation, "_resolve_extractor_root",
        lambda _cwd: repo_root,
    )
    
    # Use a dummy module for dopemux to simulate site-packages load
    dummy_dopemux = SimpleNamespace(__file__="/tmp/site-packages/dopemux/__init__.py")
    monkeypatch.setitem(
        __import__("sys").modules,
        "dopemux",
        dummy_dopemux,
    )

    runner = LiveValidationRunner(
        ValidationConfig(
            promptset_root=repo_root,
            report_root=Path("reports/repo-truth-extractor/validation"),
        )
    )

    with pytest.raises(Exception, match="pip install -e"):
        runner._ensure_repo_local_cli_origin()


def test_record_pal_apilookup_writes_machine_readable_artifact(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo_root = tmp_path / "repo"
    service_root = repo_root / "services" / "repo-truth-extractor"
    promptset_root = tmp_path / "promptset"
    service_root.mkdir(parents=True, exist_ok=True)
    promptset_root.mkdir(parents=True, exist_ok=True)
    (promptset_root / "model_map.yaml").write_text("version: '2.0'\nsteps: []\n", encoding="utf-8")

    monkeypatch.setattr(
        extractor_validation, "_resolve_extractor_root",
        lambda _cwd: repo_root,
    )

    runner = LiveValidationRunner(
        ValidationConfig(
            promptset_root=promptset_root,
            report_root=Path("reports/repo-truth-extractor/validation"),
        )
    )

    async def fake_pal(tool_name: str, prompt: str):  # type: ignore[no-untyped-def]
        return {"status": "ok", "tool": tool_name, "prompt": prompt}

    monkeypatch.setattr(runner, "_call_pal_tool", fake_pal)

    runner._record_pal_apilookup()

    artifact = runner.report_dir / "PAL_API_LOOKUP.json"
    audit = runner.report_dir / "PROVIDER_MODEL_AUDIT.json"
    assert artifact.exists()
    assert audit.exists()
    payload = __import__("json").loads(artifact.read_text(encoding="utf-8"))
    assert payload["result"]["status"] == "ok"
    assert any(step.name == "pal_apilookup" and step.status == "pass" for step in runner.steps)


def test_optional_pal_failure_is_recorded_but_not_raised(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo_root = tmp_path / "repo"
    service_root = repo_root / "services" / "repo-truth-extractor"
    promptset_root = tmp_path / "promptset"
    service_root.mkdir(parents=True, exist_ok=True)
    promptset_root.mkdir(parents=True, exist_ok=True)
    (promptset_root / "model_map.yaml").write_text("version: '2.0'\nsteps: []\n", encoding="utf-8")
    
    monkeypatch.setattr(
        extractor_validation, "_resolve_extractor_root",
        lambda _cwd: repo_root,
    )
    
    runner = LiveValidationRunner(
        ValidationConfig(
            promptset_root=promptset_root,
            report_root=Path("reports/repo-truth-extractor/validation"),
        )
    )

    async def failing_pal(tool_name: str, prompt: str):  # type: ignore[no-untyped-def]
        raise RuntimeError("pal down")

    monkeypatch.setattr(runner, "_call_pal_tool", failing_pal)

    runner._record_pal_apilookup(required=False)

    assert any(step.name == "pal_apilookup" and step.status == "fail" and step.blocking is False for step in runner.steps)


def test_phase_slice_stage_runs_preflight_then_probe_then_pilot_then_slice(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    repo_root = tmp_path / "repo"
    (repo_root / "services" / "repo-truth-extractor").mkdir(parents=True, exist_ok=True)
    (repo_root / "src" / "dopemux").mkdir(parents=True, exist_ok=True)
    promptset_root = tmp_path / "promptset"
    promptset_root.mkdir(parents=True, exist_ok=True)
    pricing_manifest = tmp_path / "pricing.json"
    pricing_manifest.write_text('{"route_call_upper_bounds":{"openai/gpt-5-mini":0.1}}\n', encoding="utf-8")
    
    monkeypatch.setattr(
        extractor_validation, "_resolve_extractor_root",
        lambda _cwd: repo_root,
    )
    
    # Set up a clean dopemux module for the origin check
    dummy_dopemux = SimpleNamespace(__file__=str((repo_root / "src" / "dopemux" / "__init__.py").resolve()))
    monkeypatch.setitem(
        __import__("sys").modules,
        "dopemux",
        dummy_dopemux,
    )

    runner = LiveValidationRunner(
        ValidationConfig(
            promptset_root=promptset_root,
            report_root=Path("reports/repo-truth-extractor/validation"),
            pricing_manifest=pricing_manifest,
            stage="phase_slice",
        )
    )

    calls: list[str] = []
    monkeypatch.setattr(runner, "_record_baseline", lambda: calls.append("baseline"))
    monkeypatch.setattr(runner, "_ensure_repo_local_cli_origin", lambda: calls.append("origin"))
    monkeypatch.setattr(runner, "_run_preflight_stages", lambda: calls.append("preflight"))
    monkeypatch.setattr(runner, "_run_provider_probe_stage", lambda: calls.append("provider_probe"))
    monkeypatch.setattr(runner, "_run_batch_pilot_stage", lambda: calls.append("batch_pilot"))
    monkeypatch.setattr(runner, "_ensure_pricing_manifest_for_paid_stage", lambda: calls.append("pricing"))
    monkeypatch.setattr(runner, "_ensure_required_pal_evidence", lambda: calls.append("pal_required"))
    monkeypatch.setattr(runner, "_run_phase_slice_stage", lambda: calls.append("phase_slice"))
    monkeypatch.setattr(runner, "_record_pal_consensus", lambda stage_label: calls.append(f"consensus:{stage_label}"))

    payload = runner.run()

    assert payload["status"] == "pass"
    assert calls == [
        "baseline",
        "origin",
        "preflight",
        "provider_probe",
        "batch_pilot",
        "pricing",
        "pal_required",
        "phase_slice",
        "consensus:phase_slice",
    ]


def test_validation_toolchain_report_includes_install_guidance(monkeypatch: pytest.MonkeyPatch) -> None:
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "check_validation_toolchain.py"
    spec = importlib.util.spec_from_file_location("check_validation_toolchain", script_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    monkeypatch.setattr(module.shutil, "which", lambda binary: None)

    report = module.build_report()

    assert report["status"] == "fail"
    assert "gitleaks" in report["missing_tools"]
    assert "brew install gitleaks" in report["tools"]["gitleaks"]["install_guidance"]
