from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location(
        "run_extraction_v5_validator_repair_provenance",
        module_path,
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_args(**overrides):
    defaults = {
        "dry_run": False,
        "doctor": False,
        "doctor_auth": False,
        "preflight_providers": False,
        "coverage_report": False,
        "status": False,
        "status_json": False,
        "tail_run_log": False,
        "show_provider_usage": False,
        "print_config": False,
        "print_run_order": False,
        "print_phase_routing": False,
        "print_phase_prompts": None,
        "print_promptpack": False,
        "promptgen_scan": False,
        "gemini_list_models": False,
        "verify_phase_output": None,
        "batch_watch": False,
        "batch_retrieve": False,
        "finalize": False,
        "async_provider": None,
        "routing_policy": "balanced_openrouter",
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_should_enforce_pre_live_validator_for_live_phase_execution() -> None:
    runner = _load_runner_module()

    assert (
        runner.should_enforce_pre_live_validator(_make_args(), ["A", "H"]) is True
    )
    assert (
        runner.should_enforce_pre_live_validator(_make_args(dry_run=True), ["A"])
        is False
    )
    assert (
        runner.should_enforce_pre_live_validator(
            _make_args(preflight_providers=True), ["A"]
        )
        is False
    )
    assert (
        runner.should_enforce_pre_live_validator(_make_args(async_provider="openai"), [])
        is True
    )
    assert (
        runner.should_enforce_pre_live_validator(_make_args(), ["S_INT"]) is False
    )


def test_main_blocks_live_phase_when_validator_returns_no_go(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner_module()
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_extraction_v5.py", "--phase", "A", "--execute"],
    )
    monkeypatch.setenv("DPMX_LIVE_OK", "1")
    monkeypatch.setattr(
        runner,
        "enforce_pre_live_validator_for_execution",
        lambda **kwargs: (_ for _ in ()).throw(RuntimeError("validator blocked")),
    )

    with pytest.raises(SystemExit) as excinfo:
        runner.main()

    assert excinfo.value.code == 1


def test_main_allows_live_phase_when_validator_returns_go(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner_module()
    calls = []

    monkeypatch.setattr(
        sys,
        "argv",
        ["run_extraction_v5.py", "--phase", "A", "--execute"],
    )
    monkeypatch.setenv("DPMX_LIVE_OK", "1")

    def _fake_gate(**kwargs):
        calls.append(kwargs)
        return {"verdict": "GO"}

    monkeypatch.setattr(runner, "enforce_pre_live_validator_for_execution", _fake_gate)
    monkeypatch.setattr(
        runner,
        "resolve_run_context",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("stop_after_gate")),
    )

    with pytest.raises(SystemExit) as excinfo:
        runner.main()

    assert excinfo.value.code == 1
    assert len(calls) == 1
    assert calls[0]["phase_sequence"] == ["A"]


def test_main_skips_validator_for_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = _load_runner_module()
    called = {"value": False}

    monkeypatch.setattr(
        sys,
        "argv",
        ["run_extraction_v5.py", "--phase", "A", "--dry-run"],
    )

    def _fake_gate(**kwargs):
        called["value"] = True
        return {"verdict": "GO"}

    monkeypatch.setattr(runner, "enforce_pre_live_validator_for_execution", _fake_gate)
    monkeypatch.setattr(
        runner,
        "resolve_run_context",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("stop_after_gate")),
    )

    with pytest.raises(SystemExit) as excinfo:
        runner.main()

    assert excinfo.value.code == 1
    assert called["value"] is False


# ---------------------------------------------------------------------------
# RTE-UX-PKT-PRELIVE-VALIDATOR-ERROR-SHAPE-001
# Failure-shape coverage for pre-live validator blocked runs. Each test exercises
# only message formatting / structured emission. No provider, network, or live
# extraction call is made; the validator subprocess is stubbed.
# ---------------------------------------------------------------------------


class _FakeCompletedProcess:
    def __init__(self, *, returncode: int, stdout: str = "", stderr: str = "") -> None:
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_format_pre_live_validator_block_includes_all_sections() -> None:
    runner = _load_runner_module()

    text = runner.format_pre_live_validator_block(
        verdict="NO_GO",
        reason_codes=["MISSING_KEY", "STALE_PRESCAN"],
        output_dir="/tmp/run_xyz",
        stderr_text="boom: provider unreachable",
        artifact_path="/tmp/run_xyz/PRELIVE_VALIDATOR_RESULT.json",
        next_step_hint="review and rerun",
    )

    assert text.splitlines()[0] == "Pre-live validator blocked live execution."
    assert "  verdict: NO_GO" in text
    assert "  reason_codes: MISSING_KEY, STALE_PRESCAN" in text
    assert "  output_dir: /tmp/run_xyz" in text
    assert "  artifact: /tmp/run_xyz/PRELIVE_VALIDATOR_RESULT.json" in text
    assert "    boom: provider unreachable" in text
    assert "  next_step: review and rerun" in text
    assert "🚦" not in text
    assert "🛑" not in text


def test_format_pre_live_validator_block_missing_reason_codes() -> None:
    runner = _load_runner_module()

    text = runner.format_pre_live_validator_block(verdict="NO_GO")

    assert "  reason_codes: none reported" in text
    assert "  output_dir: <unknown>" in text
    assert "  next_step:" in text


def test_format_pre_live_validator_block_parse_error_flag() -> None:
    runner = _load_runner_module()

    text = runner.format_pre_live_validator_block(
        verdict="NO_GO",
        parse_error=True,
        stderr_text="validator crashed",
    )

    assert (
        "  parse_status: validator stdout was not parseable as JSON; "
        "treating as block (fail-closed)."
    ) in text
    assert "    validator crashed" in text


def test_enforce_pre_live_validator_emits_block_on_structured_no_go(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = _load_runner_module()
    monkeypatch.setenv("DPMX_LIVE_OK", "1")

    payload = {
        "verdict": "NO_GO",
        "reason_codes": ["MISSING_KEY", "STALE_PRESCAN"],
        "output_dir": "/tmp/run_abc",
    }

    def _fake_subprocess_run(*args, **kwargs):
        return _FakeCompletedProcess(
            returncode=1,
            stdout=json.dumps(payload),
            stderr="upstream auth failed",
        )

    monkeypatch.setattr(runner.subprocess, "run", _fake_subprocess_run)

    with pytest.raises(RuntimeError) as excinfo:
        runner.enforce_pre_live_validator_for_execution(
            root=Path("."),
            args=_make_args(execute=True),
            phase_sequence=["A"],
        )

    captured = capsys.readouterr()
    assert "Pre-live validator blocked live execution." in captured.err
    assert "  verdict: NO_GO" in captured.err
    assert "  reason_codes: MISSING_KEY, STALE_PRESCAN" in captured.err
    assert "  output_dir: /tmp/run_abc" in captured.err
    assert "    upstream auth failed" in captured.err
    # Exception message stays single-line so log handlers do not mangle it.
    assert "\n" not in str(excinfo.value)
    assert "verdict=NO_GO" in str(excinfo.value)


def test_enforce_pre_live_validator_fails_closed_on_malformed_stdout(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = _load_runner_module()
    monkeypatch.setenv("DPMX_LIVE_OK", "1")

    def _fake_subprocess_run(*args, **kwargs):
        return _FakeCompletedProcess(
            returncode=0,
            stdout="this is not json at all",
            stderr="oops",
        )

    monkeypatch.setattr(runner.subprocess, "run", _fake_subprocess_run)

    with pytest.raises(RuntimeError) as excinfo:
        runner.enforce_pre_live_validator_for_execution(
            root=Path("."),
            args=_make_args(execute=True),
            phase_sequence=["A"],
        )

    captured = capsys.readouterr()
    assert "Pre-live validator blocked live execution." in captured.err
    assert (
        "  parse_status: validator stdout was not parseable as JSON; "
        "treating as block (fail-closed)."
    ) in captured.err
    assert "  reason_codes: none reported" in captured.err
    assert "  output_dir: <unknown>" in captured.err
    assert "    oops" in captured.err
    assert "verdict=NO_GO" in str(excinfo.value)


def test_enforce_pre_live_validator_returns_payload_on_go(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = _load_runner_module()
    monkeypatch.setenv("DPMX_LIVE_OK", "1")

    def _fake_subprocess_run(*args, **kwargs):
        return _FakeCompletedProcess(
            returncode=0,
            stdout=json.dumps({"verdict": "GO"}),
            stderr="",
        )

    monkeypatch.setattr(runner.subprocess, "run", _fake_subprocess_run)

    result = runner.enforce_pre_live_validator_for_execution(
        root=Path("."),
        args=_make_args(execute=True),
        phase_sequence=["A"],
    )

    captured = capsys.readouterr()
    assert "Pre-live validator blocked" not in captured.err
    assert result["verdict"] == "GO"
    assert result["returncode"] == 0


def test_enforce_pre_live_validator_short_circuits_without_consent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner_module()
    monkeypatch.delenv("DPMX_LIVE_OK", raising=False)

    def _fail_subprocess_run(*args, **kwargs):  # pragma: no cover - guard rail
        raise AssertionError("validator must not be invoked without DPMX_LIVE_OK")

    monkeypatch.setattr(runner.subprocess, "run", _fail_subprocess_run)

    result = runner.enforce_pre_live_validator_for_execution(
        root=Path("."),
        args=_make_args(execute=True),
        phase_sequence=["A"],
    )

    assert result["verdict"] == "SKIPPED_NO_CONSENT"


def test_emit_validator_first_preset_block_structured_payload(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = _load_runner_module()

    payload = {
        "exit_code": 1,
        "status": "fail",
        "stdout": json.dumps(
            {
                "verdict": "NO_GO",
                "reason_codes": ["PRESET_GUARD", "ROUTE_READINESS"],
                "output_dir": "/tmp/run_qrs",
            }
        ),
        "stderr": "auth token expired",
    }

    runner._emit_validator_first_preset_block(payload, Path("/tmp/run_qrs"))
    out = capsys.readouterr().err

    assert "Pre-live validator blocked live execution." in out
    assert "  verdict: NO_GO" in out
    assert "  reason_codes: PRESET_GUARD, ROUTE_READINESS" in out
    assert "  output_dir: /tmp/run_qrs" in out
    assert "  artifact: /tmp/run_qrs/PRELIVE_VALIDATOR_RESULT.json" in out
    assert "    auth token expired" in out
    assert "--skip-pre-live-validator" in out


def test_emit_validator_first_preset_block_malformed_stdout(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = _load_runner_module()

    payload = {
        "exit_code": 2,
        "status": "fail",
        "stdout": "<<not json>>",
        "stderr": "validator crashed mid-run",
    }

    runner._emit_validator_first_preset_block(payload, Path("/tmp/run_tuv"))
    out = capsys.readouterr().err

    assert (
        "  parse_status: validator stdout was not parseable as JSON; "
        "treating as block (fail-closed)."
    ) in out
    assert "  reason_codes: none reported" in out
    assert "  output_dir: <unknown>" in out
    assert "    validator crashed mid-run" in out
    assert "  artifact: /tmp/run_tuv/PRELIVE_VALIDATOR_RESULT.json" in out


def test_emit_validator_first_preset_block_empty_payload(
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = _load_runner_module()

    runner._emit_validator_first_preset_block({}, Path("/tmp/run_wxy"))
    out = capsys.readouterr().err

    assert "Pre-live validator blocked live execution." in out
    assert "  verdict: NO_GO" in out
    assert "  reason_codes: none reported" in out
    assert "  output_dir: <unknown>" in out
    assert "  artifact: /tmp/run_wxy/PRELIVE_VALIDATOR_RESULT.json" in out
    # No stderr line when payload stderr is empty.
    assert "  stderr:" not in out
