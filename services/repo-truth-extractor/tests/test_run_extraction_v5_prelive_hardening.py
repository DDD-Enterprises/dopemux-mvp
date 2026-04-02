from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import types
from pathlib import Path

import pytest


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _runner_script() -> Path:
    return _repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py"


def _load_runner_module() -> types.ModuleType:
    module_path = _runner_script()
    spec = importlib.util.spec_from_file_location("run_extraction_v5_prelive", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_spend_ledger_module() -> types.ModuleType:
    module_path = _repo_root() / "services" / "repo-truth-extractor" / "lib" / "spend_ledger.py"
    spec = importlib.util.spec_from_file_location("spend_ledger_prelive", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_structured_contracts_module() -> types.ModuleType:
    module_path = _repo_root() / "services" / "repo-truth-extractor" / "lib" / "structured_output_contracts.py"
    spec = importlib.util.spec_from_file_location("structured_contracts_prelive", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_cfg(runner: types.ModuleType):
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
        "disable_escalation": False,
        "escalation_max_hops": 2,
        "batch_mode": False,
        "batch_provider": "auto",
        "batch_poll_seconds": 30,
        "batch_wait_timeout_seconds": 86400,
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


def test_parse_json_from_response_reports_lossy_truncation_salvage() -> None:
    runner = _load_runner_module()
    meta: dict[str, object] = {}
    parsed = runner.parse_json_from_response(
        '{"ok":true',
        metadata_out=meta,
    )
    assert parsed["ok"] is True
    assert meta["truncation_salvage"] is True
    assert meta["lossy"] is True


def test_phase_catalog_includes_dependencies_and_default_route() -> None:
    runner = _load_runner_module()
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        rc = runner.print_phase_catalog(["R", "S"])
    assert rc == 0
    payload = json.loads(buffer.getvalue())
    rows = {row["code"]: row for row in payload["phases"]}
    assert rows["R"]["dependencies"] == ["A", "H", "D", "C"]
    assert rows["S"]["dependencies"] == ["R"]
    assert rows["R"]["default_route"]["model"]


def test_cli_help_mentions_execute_live_ok_and_list_phases(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(_runner_script()), "--help"],
        cwd=str(tmp_path),
        text=True,
        capture_output=True,
        check=True,
    )
    assert "--execute" in result.stdout
    assert "DPMX_LIVE_OK" in result.stdout
    assert "--list-phases" in result.stdout


def test_cli_list_phases_outputs_json(tmp_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(_runner_script()), "--list-phases"],
        cwd=str(tmp_path),
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["phase_count"] == len(payload["phases"])
    assert any(row["code"] == "R" for row in payload["phases"])


def test_cli_live_execution_requires_explicit_consent(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(_runner_script()),
            "--phase",
            "A",
            "--run-id",
            "consent_guard_test",
        ],
        cwd=str(tmp_path),
        text=True,
        capture_output=True,
    )
    assert result.returncode != 0
    assert "DPMX_LIVE_OK=1" in result.stderr


def test_runtime_spend_prefers_provider_usage_and_enforces_cap(tmp_path: Path) -> None:
    runner = _load_runner_module()
    spend_ledger = _load_spend_ledger_module()
    cfg = _make_cfg(runner)
    ledger = spend_ledger.SpendLedger(tmp_path, "run_prelive", max_cost_usd=0.00001)
    object.__setattr__(cfg, "ledger", ledger)
    object.__setattr__(cfg, "max_cost_usd", 0.00001)

    with pytest.raises(RuntimeError, match="Runtime cost cap exceeded"):
        runner._accumulate_runtime_spend(
            cfg,
            phase="A",
            step_id="A0",
            partition_id="A_P0001",
            provider="openai",
            model_id="gpt-5-mini",
            execution_mode="sync",
            response_summary={"usage": {"prompt_tokens": 100, "completion_tokens": 100000}},
            response_text='{"ok": true}',
            fallback_input_tokens=999999,
        )

    saved = json.loads((tmp_path / "spend_ledger.json").read_text(encoding="utf-8"))
    assert saved["models"]["openai/gpt-5-mini"]["input_tokens"] == 100
    assert saved["models"]["openai/gpt-5-mini"]["output_tokens"] == 100000


def test_projected_cost_limit_blocks_before_submit(tmp_path: Path) -> None:
    runner = _load_runner_module()
    spend_ledger = _load_spend_ledger_module()
    cfg = _make_cfg(runner)
    ledger = spend_ledger.SpendLedger(tmp_path, "run_projected", max_cost_usd=0.0001)
    object.__setattr__(cfg, "ledger", ledger)
    object.__setattr__(cfg, "max_cost_usd", 0.0001)

    with pytest.raises(RuntimeError, match="Projected cost cap exceeded"):
        runner._check_projected_cost_limit(
            cfg,
            phase="R",
            step_id="R0",
            partition_id="R_P0001",
            provider="openrouter",
            model_id="openai/gpt-5-mini",
            input_tokens=1_000_000,
            output_tokens=500_000,
            execution_mode="batch_submit",
        )


def test_spend_ledger_tracks_provider_prefixed_and_unknown_models(tmp_path: Path) -> None:
    spend_ledger = _load_spend_ledger_module()
    ledger = spend_ledger.SpendLedger(tmp_path, "run_models")
    known = ledger.accumulate(
        "R",
        1000,
        500,
        provider="openrouter",
        model_id="openai/gpt-5-mini",
    )
    unknown = ledger.accumulate(
        "R",
        1000,
        500,
        provider="mystery",
        model_id="weird-model",
    )
    assert known["unknown_model"] is False
    assert unknown["unknown_model"] is True
    payload = json.loads((tmp_path / "spend_ledger.json").read_text(encoding="utf-8"))
    assert "openrouter/openai/gpt-5-mini" in payload["models"]
    assert payload["unknown_model_events"] == 1


def test_merge_artifacts_by_name_reports_scalar_sidefill_conflicts() -> None:
    contracts = _load_structured_contracts_module()
    merged, conflicts = contracts.merge_artifacts_by_name(
        [
            {
                "artifact_name": "OUT.json",
                "payload": {
                    "items": [
                        {"id": "item-1", "status": "before", "path": "a.py"},
                    ]
                },
            }
        ],
        [
            {
                "artifact_name": "OUT.json",
                "payload": {
                    "items": [
                        {"id": "item-1", "status": "after", "path": "a.py"},
                    ]
                },
            }
        ],
        {"artifact_order": ["OUT.json"]},
        return_conflicts=True,
    )
    assert merged[0]["artifact_name"] == "OUT.json"
    assert conflicts == [
        {
            "artifact_name": "OUT.json",
            "item_id": "item-1",
            "field": "status",
            "existing_value": "before",
            "updated_value": "after",
        }
    ]
