from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

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
        "dopemux.commands.extractor_validation._resolve_extractor_root",
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

    monkeypatch.setattr("dopemux.commands.extractor_validation.subprocess.run", fake_run)

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
