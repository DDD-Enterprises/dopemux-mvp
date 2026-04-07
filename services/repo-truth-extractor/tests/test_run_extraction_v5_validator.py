from __future__ import annotations

import importlib.util
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
        ["run_extraction_v5.py", "--phase", "A"],
    )
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
        ["run_extraction_v5.py", "--phase", "A"],
    )

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

