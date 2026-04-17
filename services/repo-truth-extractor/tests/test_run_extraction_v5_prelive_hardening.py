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


def _load_phase_contract_map_module() -> types.ModuleType:
    module_path = _repo_root() / "services" / "repo-truth-extractor" / "lib" / "phase_contract_map.py"
    spec = importlib.util.spec_from_file_location("phase_contract_map_prelive", module_path)
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


def test_classify_request_failure_marks_batch_submit_as_pre_model_execution() -> None:
    runner = _load_runner_module()
    failure = runner.classify_request_failure(
        {
            "failure_type": "provider",
            "provider_error_reason": "batch_submit_error:UnprocessableEntityError",
            "execution_mode": "batch",
            "batch_provider": "xai",
            "batch_job_id": None,
        }
    )
    assert failure["failure_class"] == "batch_submission_unprocessable"
    assert failure["failure_stage"] == "pre_model_execution"
    assert "rerun with --no-batch" in str(failure["remediation_hint"])


def test_normalize_step_reports_pre_model_execution_blocker_not_missing_artifacts(
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "A_repo_control_plane"
    raw_dir = phase_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = tmp_path / "PROMPT_A2_TEST.md"
    prompt_path.write_text("Return OUT.json", encoding="utf-8")
    partition_id = "A_P0001"
    raw_payload = {
        "phase": "A",
        "step_id": "A2",
        "partition_id": partition_id,
        "generated_at": "2026-04-02T00:00:00+00:00",
        "artifacts": [],
        "request_meta": {
            "failure_type": "provider",
            "provider_error_reason": "batch_submit_error:UnprocessableEntityError",
            "execution_mode": "batch",
            "batch_provider": "xai",
            "batch_job_id": None,
        },
    }
    (raw_dir / f"A2__{partition_id}.json").write_text(
        json.dumps(raw_payload), encoding="utf-8"
    )
    prompt = runner.PromptSpec(
        step_id="A2",
        prompt_path=prompt_path,
        output_artifacts=("OUT.json",),
    )

    qa = runner.normalize_step(
        "A",
        prompt,
        phase_dir,
        [{"id": partition_id}],
        step_exec_stats={"failed": 1},
    )

    assert qa["missing_expected_artifacts"] == []
    assert qa["artifact_blocked_by_failure_stage"] == {
        "pre_model_execution": ["OUT.json"]
    }
    assert qa["failure_stage_histogram"] == {"pre_model_execution": 1}
    assert qa["parse_failures"] == [
        {
            "partition_id": partition_id,
            "reason": "batch_submission_unprocessable",
            "file": str(raw_dir / f"A2__{partition_id}.json"),
        }
    ]


def test_classify_request_failure_distinguishes_batch_terminal_and_parse_failures() -> None:
    runner = _load_runner_module()

    provider_failure = runner.classify_request_failure(
        {
            "failure_type": "provider",
            "provider_error_reason": "batch_terminal_state:failed",
            "execution_mode": "batch_watch",
        }
    )
    assert provider_failure["failure_class"] == "batch_provider_execution_failed"
    assert provider_failure["failure_stage"] == "model_execution"
    assert "Check provider auth/quota/status" in str(
        provider_failure["remediation_hint"]
    )

    parse_failure = runner.classify_request_failure(
        {
            "failure_type": "parse",
            "provider_error_reason": None,
            "execution_mode": "batch_watch",
        }
    )
    assert parse_failure["failure_class"] == "batch_output_parse_failed"
    assert parse_failure["failure_stage"] == "post_model_output"
    assert "Inspect parser/contract artifacts" in str(
        parse_failure["remediation_hint"]
    )


def test_classify_failure_type_maps_openrouter_402_credit_failure_to_quota() -> None:
    runner = _load_runner_module()

    failure_type = runner.classify_failure_type(
        402,
        '{"error":{"message":"This request requires more credits, or fewer max_tokens."}}',
        "Provider can only afford 56151 completion tokens on this account.",
    )

    assert failure_type == "quota_or_billing"


def test_build_chat_payload_applies_h3_max_completion_tokens_budget() -> None:
    runner = _load_runner_module()

    assert runner._step_max_completion_tokens("H", "H3") == 8192
    payload = runner.build_chat_payload(
        "openrouter",
        "openai/gpt-5.4",
        "system",
        "user",
        max_completion_tokens=runner._step_max_completion_tokens("H", "H3"),
    )

    assert payload["max_tokens"] == 8192


def test_classify_request_failure_preserves_upstream_payload_failure_when_schema_gate_masks_it() -> None:
    runner = _load_runner_module()

    failure = runner.classify_request_failure(
        {
            "failure_type": "payload",
            "provider_error_reason": "",
            "status_code": 402,
            "response_received": False,
            "schema_gate_passed": False,
            "schema_gate_reason": "missing_expected_artifacts:HOME_ROUTER_SURFACE.json,HOME_PROVIDER_LADDER_HINTS.json",
            "schema_gate_context": {"artifact_name": "HOME_ROUTER_SURFACE.json"},
            "execution_mode": "sync",
        }
    )

    assert failure["failure_class"] == "payload"
    assert failure["reason"] == "payload"
    assert failure["failure_stage"] == "model_execution"
    assert failure["artifact_name"] is None


def test_normalize_step_keeps_parse_failures_at_threshold(tmp_path: Path) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "A_repo_control_plane"
    raw_dir = phase_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = tmp_path / "PROMPT_A2_TEST.md"
    prompt_path.write_text("Return OUT.json", encoding="utf-8")
    prompt = runner.PromptSpec(
        step_id="A2",
        prompt_path=prompt_path,
        output_artifacts=("OUT.json",),
    )
    partitions = []
    for idx in range(20):
        partition_id = f"A_P{idx + 1:04d}"
        partitions.append({"id": partition_id})
        if idx == 0:
            continue
        (raw_dir / f"A2__{partition_id}.json").write_text(
            json.dumps(
                {
                    "phase": "A",
                    "step_id": "A2",
                    "partition_id": partition_id,
                    "generated_at": "2026-04-11T00:00:00+00:00",
                    "artifacts": [
                        {
                            "artifact_name": "OUT.json",
                            "payload": {"schema": "itemlist@v1", "items": []},
                        }
                    ],
                    "request_meta": {},
                }
            ),
            encoding="utf-8",
        )

    qa = runner.normalize_step("A", prompt, phase_dir, partitions, step_exec_stats={})
    assert qa["raw_failed"] == 1
    assert qa["raw_ok"] == 19
    assert qa["parse_failure_rate"] == 0.05


def test_normalize_step_aborts_when_parse_failures_exceed_threshold(
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "A_repo_control_plane"
    raw_dir = phase_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = tmp_path / "PROMPT_A2_TEST.md"
    prompt_path.write_text("Return OUT.json", encoding="utf-8")
    prompt = runner.PromptSpec(
        step_id="A2",
        prompt_path=prompt_path,
        output_artifacts=("OUT.json",),
    )
    partitions = [{"id": "A_P0001"}, {"id": "A_P0002"}]
    (raw_dir / "A2__A_P0001.json").write_text(
        json.dumps(
            {
                "phase": "A",
                "step_id": "A2",
                "partition_id": "A_P0001",
                "generated_at": "2026-04-11T00:00:00+00:00",
                "artifacts": [
                    {
                        "artifact_name": "OUT.json",
                        "payload": {"schema": "itemlist@v1", "items": []},
                    }
                ],
                "request_meta": {},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError, match="Parse failure threshold exceeded"):
        runner.normalize_step("A", prompt, phase_dir, partitions, step_exec_stats={})

    qa = json.loads((phase_dir / "qa" / "A2_QA.json").read_text(encoding="utf-8"))
    assert qa["raw_failed"] == 1
    assert qa["raw_ok"] == 1
    assert qa["parse_failure_rate"] == 0.5


def test_coerce_artifacts_accepts_top_level_single_artifact_object() -> None:
    runner = _load_runner_module()
    parsed = {
        "artifact_name": "REPO_MCP_SERVER_DEFS.json",
        "payload": {"schema": "itemlist@v1", "items": []},
        "unknowns": ["kept"],
    }
    artifacts = runner.coerce_artifacts_from_response(
        parsed,
        json.dumps(parsed),
        ("REPO_MCP_SERVER_DEFS.json",),
    )
    assert artifacts == [
        {
            "artifact_name": "REPO_MCP_SERVER_DEFS.json",
            "payload": {"schema": "itemlist@v1", "items": []},
        }
    ]


def test_canonicalize_artifacts_normalizes_schema_alias_and_line_range() -> None:
    contracts = _load_structured_contracts_module()
    step_contract = {
        "expected_artifacts": ["REPO_MCP_SERVER_DEFS.json"],
        "artifact_order": ["REPO_MCP_SERVER_DEFS.json"],
        "artifacts": {
            "REPO_MCP_SERVER_DEFS.json": {
                "canonical_schema_id": "REPO_MCP_SERVER_DEFS@v1",
                "schema_aliases": [
                    "itemlist@v1",
                    "json_item_list@v1",
                    "ItemList@REPO_MCP_SERVER_DEFS@v1",
                ],
                "required_fields": ["id", "path", "line_range"],
                "prompt_required_item_fields": [],
            }
        },
    }
    artifacts = [
        {
            "artifact_name": "REPO_MCP_SERVER_DEFS.json",
            "payload": {
                "schema": "json_item_list@v1",
                "items": [
                    {
                        "id": "mcp:1",
                        "path": "config/profiles/adhd-default.yaml",
                        "line_range": "8-25",
                    }
                ],
            },
        }
    ]
    normalized, schema_normalizations = contracts.canonicalize_artifacts(
        artifacts,
        step_contract,
    )
    assert schema_normalizations == [
        {
            "artifact_name": "REPO_MCP_SERVER_DEFS.json",
            "from": "json_item_list@v1",
            "to": "REPO_MCP_SERVER_DEFS@v1",
        }
    ]
    payload = normalized[0]["payload"]
    assert payload["schema"] == "REPO_MCP_SERVER_DEFS@v1"
    assert payload["items"][0]["line_range"] == [8, 25]
    ok, reason, _context = contracts.artifacts_pass_contract_gate(
        normalized,
        step_contract,
    )
    assert ok is True
    assert reason is None


def test_schema_aliases_for_json_item_list_include_observed_generic_aliases() -> None:
    phase_contracts = _load_phase_contract_map_module()
    aliases = phase_contracts.schema_aliases_for_artifact(
        "REPO_MCP_SERVER_DEFS.json",
        kind="json_item_list",
    )
    assert "itemlist@v1" in aliases
    assert "json_item_list@v1" in aliases
    assert "REPO_MCP_SERVER_DEFS@v1" in aliases


def test_canonicalize_artifacts_keeps_unrelated_schema_ids_failing() -> None:
    contracts = _load_structured_contracts_module()
    step_contract = {
        "expected_artifacts": ["OUT.json"],
        "artifact_order": ["OUT.json"],
        "artifacts": {
            "OUT.json": {
                "canonical_schema_id": "OUT@v1",
                "schema_aliases": ["itemlist@v1"],
                "required_fields": ["id", "path", "line_range"],
                "prompt_required_item_fields": [],
            }
        },
    }
    normalized, _ = contracts.canonicalize_artifacts(
        [
            {
                "artifact_name": "OUT.json",
                "payload": {
                    "schema": "totally_wrong@v7",
                    "items": [{"id": "x", "path": "docs/a.md", "line_range": [1, 2]}],
                },
            }
        ],
        step_contract,
    )
    ok, reason, context = contracts.artifacts_pass_contract_gate(
        normalized,
        step_contract,
    )
    assert ok is False
    assert reason == "contract_schema_id_mismatch"
    assert context["constraint"] == "OUT@v1"


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
