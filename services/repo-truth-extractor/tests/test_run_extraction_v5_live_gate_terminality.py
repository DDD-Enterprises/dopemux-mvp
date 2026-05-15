from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    module_name = "run_extraction_v5_live_gate_terminality"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_args(**overrides):
    defaults = {
        "dry_run": False,
        "execute": True,
        "preflight_providers": False,
        "doctor_auth": False,
        "doctor": False,
        "gemini_list_models": False,
        "batch_watch": False,
        "batch_retrieve": False,
        "async_provider": None,
        "finalize": False,
        "prescan_online": False,
        "allow_online_llm": False,
        "skip_prescan": False,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


@pytest.mark.parametrize(
    ("overrides", "phases", "expected_names"),
    [
        ({}, ["A"], ["sync phase execution"]),
        ({}, ["S_INT"], ["sync phase execution"]),
        ({"dry_run": True, "execute": False}, ["A"], []),
        (
            {"batch_watch": True, "dry_run": True, "execute": False},
            ["A"],
            ["batch watch"],
        ),
        (
            {"batch_retrieve": True, "dry_run": True, "execute": False},
            [],
            ["batch retrieve"],
        ),
        (
            {"async_provider": "openai", "dry_run": True, "execute": False},
            ["R"],
            ["async Phase R submit"],
        ),
        ({"finalize": True, "dry_run": True, "execute": False}, ["R"], []),
        (
            {"preflight_providers": True, "dry_run": True, "execute": False},
            ["A"],
            ["provider preflight"],
        ),
        (
            {"doctor_auth": True, "dry_run": True, "execute": False},
            [],
            ["auth doctor"],
        ),
        (
            {"doctor": True, "dry_run": True, "execute": False},
            ["A"],
            ["full doctor provider probes"],
        ),
        (
            {"gemini_list_models": True, "dry_run": True, "execute": False},
            [],
            ["Gemini model listing"],
        ),
        (
            {"prescan_online": True, "dry_run": True, "execute": False},
            ["A"],
            ["online prescan/Grok"],
        ),
        (
            {"allow_online_llm": True, "dry_run": True, "execute": False},
            ["A"],
            ["online prescan/Grok"],
        ),
        (
            {
                "prescan_online": True,
                "skip_prescan": True,
                "dry_run": True,
                "execute": False,
            },
            ["A"],
            [],
        ),
    ],
)
def test_live_capable_operation_classifier(overrides, phases, expected_names) -> None:
    runner = _load_runner_module()

    observed = runner.classify_live_capable_operations(
        _make_args(**overrides),
        phases,
    )

    assert [operation.name for operation in observed] == expected_names


@pytest.mark.parametrize(
    "read_only_flag",
    [
        "coverage_report",
        "status",
        "status_json",
        "tail_run_log",
        "show_provider_usage",
        "print_config",
        "print_run_order",
        "print_phase_routing",
        "print_promptpack",
        "promptgen_scan",
    ],
)
def test_online_prescan_flags_do_not_gate_read_only_introspection(read_only_flag) -> None:
    runner = _load_runner_module()

    observed = runner.classify_live_capable_operations(
        _make_args(
            **{
                read_only_flag: True,
                "prescan_online": True,
                "allow_online_llm": True,
                "dry_run": True,
                "execute": False,
            }
        ),
        ["A"],
    )

    assert observed == ()


@pytest.mark.parametrize(
    ("flag_name", "flag_value"),
    [
        ("print_phase_prompts", "A"),
        ("verify_phase_output", "A"),
    ],
)
def test_value_read_only_flags_do_not_gate_online_prescan(flag_name, flag_value) -> None:
    runner = _load_runner_module()

    observed = runner.classify_live_capable_operations(
        _make_args(
            **{
                flag_name: flag_value,
                "prescan_online": True,
                "allow_online_llm": True,
                "dry_run": True,
                "execute": False,
            }
        ),
        ["A"],
    )

    assert observed == ()


def test_sync_phase_requires_execute_flag_and_live_ok(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = _load_runner_module()
    parser = argparse.ArgumentParser(prog="run_extraction_v5.py")
    monkeypatch.delenv(runner.DPMX_LIVE_OK_ENV, raising=False)

    with pytest.raises(SystemExit) as excinfo:
        runner.enforce_live_operation_consent(
            parser,
            args=_make_args(),
            phase_sequence=["A"],
            raw_argv=["--phase", "A"],
        )

    assert excinfo.value.code == 2
    stderr = capsys.readouterr().err
    assert "--execute" in stderr
    assert "DPMX_LIVE_OK=1" in stderr
    assert "sync phase execution" in stderr


def test_sync_phase_with_live_ok_still_requires_execute_flag(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    runner = _load_runner_module()
    parser = argparse.ArgumentParser(prog="run_extraction_v5.py")
    monkeypatch.setenv(runner.DPMX_LIVE_OK_ENV, "1")

    with pytest.raises(SystemExit) as excinfo:
        runner.enforce_live_operation_consent(
            parser,
            args=_make_args(),
            phase_sequence=["A"],
            raw_argv=["--phase", "A"],
        )

    assert excinfo.value.code == 2
    stderr = capsys.readouterr().err
    assert "Missing consent: --execute" in stderr
    assert "DPMX_LIVE_OK=1" not in stderr


@pytest.mark.parametrize(
    ("argv", "dispatch_name"),
    [
        (["--preflight-providers", "--dry-run"], "run_provider_preflight"),
        (["--doctor-auth", "--dry-run"], "run_auth_doctor"),
        (["--doctor", "--dry-run"], "run_doctor_full"),
        (["--gemini-list-models", "--dry-run"], "run_gemini_list_models"),
        (
            ["--phase", "R", "--async-provider", "openai", "--dry-run"],
            "run_phase_R_async_submit",
        ),
        (["--batch-watch", "--phase", "A", "--dry-run"], "run_batch_watch"),
        (
            ["--batch-retrieve", "--batch-ids", "batch_123", "--dry-run"],
            "run_batch_retrieval_and_integration",
        ),
        (
            ["--phase", "A", "--prescan-online", "--dry-run"],
            "run_integrated_prescan_stage",
        ),
    ],
)
def test_live_capable_dispatch_refuses_before_target_function(
    monkeypatch: pytest.MonkeyPatch,
    argv,
    dispatch_name: str,
) -> None:
    runner = _load_runner_module()
    called = {"value": False}

    def _fail_if_called(*_args, **_kwargs):
        called["value"] = True
        raise AssertionError(f"{dispatch_name} should not be called without live consent")

    monkeypatch.delenv(runner.DPMX_LIVE_OK_ENV, raising=False)
    monkeypatch.setattr(sys, "argv", ["run_extraction_v5.py", *argv])
    monkeypatch.setattr(runner, dispatch_name, _fail_if_called)

    with pytest.raises(SystemExit) as excinfo:
        runner.main()

    assert excinfo.value.code == 2
    assert called["value"] is False


def test_phase_dry_run_remains_available_without_live_ok(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner_module()
    monkeypatch.delenv(runner.DPMX_LIVE_OK_ENV, raising=False)
    monkeypatch.setattr(sys, "argv", ["run_extraction_v5.py", "--phase", "A", "--dry-run"])
    monkeypatch.setattr(
        runner,
        "enforce_pre_live_validator_for_execution",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("pre-live validator should not run for dry-run")
        ),
    )
    monkeypatch.setattr(
        runner,
        "resolve_run_context",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("after_live_gate")),
    )

    with pytest.raises(SystemExit) as excinfo:
        runner.main()

    assert excinfo.value.code == 1


def test_execute_with_live_ok_passes_consent_gate_without_provider_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner_module()
    gate_calls = []
    monkeypatch.setenv(runner.DPMX_LIVE_OK_ENV, "1")
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_extraction_v5.py", "--phase", "A", "--execute"],
    )

    def _fake_pre_live_gate(**kwargs):
        gate_calls.append(kwargs)
        return {"verdict": "GO"}

    monkeypatch.setattr(runner, "enforce_pre_live_validator_for_execution", _fake_pre_live_gate)
    monkeypatch.setattr(
        runner,
        "resolve_run_context",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("after_live_gate")),
    )

    with pytest.raises(SystemExit) as excinfo:
        runner.main()

    assert excinfo.value.code == 1
    assert len(gate_calls) == 1
    assert gate_calls[0]["phase_sequence"] == ["A"]
