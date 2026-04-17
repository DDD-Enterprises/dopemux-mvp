from __future__ import annotations

import argparse
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


def _load_runner_module() -> types.ModuleType:
    module_path = _repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5_operator_safety", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _make_cfg(runner: types.ModuleType):
    cfg = runner.RunnerConfig.__new__(runner.RunnerConfig)
    defaults = {
        "dry_run": True,
        "max_files_docs": 35,
        "max_files_code": 20,
        "max_chars": 650000,
        "max_request_bytes": 200000,
        "file_truncate_chars": 70000,
        "home_scan_mode": "safe",
        "resume": False,
        "fail_fast_auth": False,
        "gemini_auth_mode": "auto",
        "gemini_transport": "sdk",
        "openai_transport": "openai_sdk",
        "xai_transport": "openai_sdk",
        "retry_policy": "default",
        "retry_max_attempts": 4,
        "retry_base_seconds": 2.0,
        "retry_max_seconds": 30.0,
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
        "batch_wait_timeout_seconds": 1800,
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
    }
    for key, value in defaults.items():
        object.__setattr__(cfg, key, value)
    return cfg


def test_apply_first_live_preset_applies_conservative_defaults() -> None:
    runner = _load_runner_module()
    args = argparse.Namespace(
        preset_stage="initial",
        routing_policy="balanced_openrouter",
        max_cost_usd=None,
        partition_workers=8,
        batch_mode=True,
        batch_wait_timeout_seconds=86400,
        compare_mode=None,
        output_root=None,
    )
    phases, preview = runner.apply_first_live_preset(args, [])
    assert phases == ["A", "H", "D", "C"]
    assert args.routing_policy == "cost"
    assert args.max_cost_usd == runner.FIRST_LIVE_PRESET_DEFAULT_CAP_USD
    assert args.partition_workers == 1
    assert args.batch_mode is False
    assert args.batch_wait_timeout_seconds == runner.INTERACTIVE_SAFE_BATCH_WAIT_SECONDS
    assert preview["full_recommended_sequence"][4] == "CHECKPOINT_REVIEW"


def test_apply_staged_safe_preset_enables_batch_defaults() -> None:
    runner = _load_runner_module()
    args = argparse.Namespace(
        preset_stage="initial",
        routing_policy="balanced_openrouter",
        max_cost_usd=None,
        partition_workers=8,
        batch_mode=False,
        batch_wait_timeout_seconds=86400,
        compare_mode=None,
        output_root=None,
    )
    phases, preview = runner.apply_staged_safe_preset(args, [])
    assert phases == ["A", "H", "D", "C"]
    assert args.routing_policy == "cost"
    assert args.max_cost_usd == runner.STAGED_SAFE_PRESET_DEFAULT_CAP_USD
    assert args.partition_workers == 1
    assert args.batch_mode is True
    assert args.batch_wait_timeout_seconds == runner.INTERACTIVE_SAFE_BATCH_WAIT_SECONDS
    assert preview["preset"] == runner.STAGED_SAFE_PRESET_NAME


def test_help_output_omits_contract_scope_warning() -> None:
    result = subprocess.run(
        [sys.executable, str(_repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py"), "--help"],
        cwd=str(_repo_root()),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    assert "model_map.yaml steps outside repo_truth_map JSON scope" not in result.stderr


def test_dry_run_output_omits_unknown_failure_spotlight(tmp_path: Path) -> None:
    output_root = tmp_path / "dry-run-output"
    result = subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py"),
            "--phase",
            "A",
            "--step",
            "A0",
            "--dry-run",
            "--ui",
            "plain",
            "--run-id",
            "tp5_dry_run_noise_probe",
            "--output-root",
            str(output_root),
        ],
        cwd=str(_repo_root()),
        text=True,
        capture_output=True,
        check=False,
    )
    combined_output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0
    assert "STEP_FAILURE" not in combined_output
    assert "unknown_failure" not in combined_output


def test_output_root_layout_redirects_run_and_doctor_paths(tmp_path: Path) -> None:
    runner = _load_runner_module()
    artifact_root = tmp_path / "artifact-root"
    runner.configure_output_layout(tmp_path, str(artifact_root))
    try:
        (artifact_root / "runs" / "operator_probe").mkdir(parents=True, exist_ok=True)
        dirs = runner.get_run_dirs(tmp_path, "operator_probe")
        assert dirs["root"] == artifact_root / "runs" / "operator_probe"
        assert runner.current_doctor_root(tmp_path) == artifact_root / "doctor"
        assert runner.latest_run_id_path(tmp_path) == artifact_root / "latest_run_id.txt"
    finally:
        runner.configure_output_layout(tmp_path, None)


def test_build_phase_cost_preview_marks_override_risk() -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    prompts = runner.get_phase_prompts("A")[:2]
    partitions = [
        {"id": "A_P0001", "char_count_estimate": 4000},
        {"id": "A_P0002", "char_count_estimate": 8000},
    ]
    preview = runner.build_phase_cost_preview("A", cfg, prompts, partitions)
    assert preview["phase"] == "A"
    assert preview["estimated_cost_usd"] > 0
    assert preview["confidence"] == "low"
    assert preview["route_override_steps"]
    assert any("top-level policy alone" in warning for warning in preview["warnings"])
    assert preview["preview_authority"] == "heuristic_non_authoritative"
    assert preview["ledger_authority"] == "runtime_provider_usage_when_available"


def test_build_phase_cost_preview_reuses_runtime_like_prompt_projection(
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    source_file = tmp_path / "config.yaml"
    source_file.write_text("alpha: 1\nbeta: 2\n", encoding="utf-8")
    prompt_file = tmp_path / "PROMPT_TEST.md"
    prompt_file.write_text("Return one JSON artifact.", encoding="utf-8")
    contract = {
        "scope": {"json_managed": True},
        "expected_artifacts": ["OUT.json"],
        "artifact_order": ["OUT.json"],
        "lane": {
            "primary_routes": [
                {
                    "provider": "xai",
                    "model_id": "grok-4.20-beta-0309-reasoning",
                    "api_key_env": "XAI_API_KEY",
                    "strict_json_schema": False,
                    "strict_passthrough_verified": False,
                }
            ]
        },
        "artifacts": {
            "OUT.json": {
                "canonical_schema_id": "OUT@v1",
                "schema_aliases": ["itemlist@v1"],
                "required_fields": ["id", "path", "line_range"],
                "prompt_required_item_fields": [],
            }
        },
    }
    prompt = runner.PromptSpec(
        step_id="A2",
        prompt_path=prompt_file,
        output_artifacts=("OUT.json",),
        contract=contract,
    )
    partition = {"id": "A_P0001", "paths": [str(source_file)], "char_count_estimate": 16}
    route = runner.resolve_effective_step_route(
        "A",
        prompt.step_id,
        cfg,
        step_contract=prompt.contract,
    )
    usage = runner._preview_partition_usage(
        phase="A",
        step_id=prompt.step_id,
        prompt_text=prompt_file.read_text(encoding="utf-8"),
        output_artifacts=prompt.output_artifacts,
        provider=str(route.get("provider") or ""),
        model_id=str(route.get("model_id") or ""),
        partition=partition,
        cfg=cfg,
        max_files=runner.max_files_for_phase("A", cfg),
    )
    preview = runner.build_phase_cost_preview("A", cfg, [prompt], [partition])
    assert preview["input_estimation_mode"] == "runtime_prompt_projection_v1"
    assert preview["steps"][0]["estimated_input_tokens"] == usage["input_tokens"]
    assert preview["steps"][0]["estimated_output_tokens"] == max(
        64, int(usage["input_tokens"] * 0.02)
    )
    assert preview["max_preview_request_payload_bytes"] >= usage["payload_bytes"]


def test_write_phase_dry_run_checklist_records_blindspots(tmp_path: Path) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    phase_dir = tmp_path / "A_repo_control_plane"
    (phase_dir / "inputs").mkdir(parents=True, exist_ok=True)
    payload = runner.write_phase_dry_run_checklist(
        phase_dir=phase_dir,
        phase="A",
        cfg=cfg,
        prompts=runner.get_phase_prompts("A")[:1],
        inventory=[
            {"path": str(tmp_path / "manual.pdf")},
            {"path": str(tmp_path / "service.java")},
        ],
        partitions=[{"id": "A_P0001"}],
        cost_preview={"estimated_cost_usd": 0.123, "confidence": "low"},
    )
    saved = json.loads(
        (phase_dir / "inputs" / "DRY_RUN_CHECKLIST.json").read_text(encoding="utf-8")
    )
    assert payload["estimated_cost"]["estimated_cost_usd"] == 0.123
    assert saved["input_blindspots"]["unsupported_inputs"][0]["suffix"] == ".pdf"
    assert any(
        row["suffix"] == ".java"
        for row in saved["input_blindspots"]["weak_language_inputs"]
    )


def test_write_retry_cost_report_snapshot_is_deterministic(tmp_path: Path) -> None:
    runner = _load_runner_module()
    runner.write_retry_cost_report_snapshot(
        tmp_path,
        phase="A",
        step_id="A0",
        report={
            "retry_count": 2,
            "estimated_extra_cost_usd": 0.015,
            "abnormal_partitions": [
                {
                    "partition_id": "A_P0002",
                    "estimated_retry_extra_cost_usd": 0.015,
                }
            ],
        },
    )
    runner.write_retry_cost_report_snapshot(
        tmp_path,
        phase="A",
        step_id="A1",
        report={
            "retry_count": 1,
            "estimated_extra_cost_usd": 0.005,
            "abnormal_partitions": [],
        },
    )
    payload = json.loads(
        (tmp_path / "telemetry" / runner.RETRY_COST_REPORT_FILENAME).read_text(
            encoding="utf-8"
        )
    )
    assert list(payload["steps"].keys()) == ["A:A0", "A:A1"]
    assert payload["summary"]["retry_count"] == 3
    assert payload["summary"]["estimated_extra_cost_usd"] == 0.02


def test_prompt_hash_report_for_selected_step_does_not_require_full_phase() -> None:
    runner = _load_runner_module()
    selected = [spec for spec in runner.get_phase_prompts("A") if spec.step_id == "A2"]
    report = runner._prompt_hash_report_for_phase(
        "A",
        selected,
        required_step_ids={"A2"},
    )
    assert report["blocked_promptset"] is False
    assert report["prompt_failures_count"] == 0


def test_run_pre_live_validator_records_artifact(monkeypatch, tmp_path: Path) -> None:
    runner = _load_runner_module()
    called = {}

    def _fake_run(*args, **kwargs):
        called["args"] = list(args[0])
        return subprocess.CompletedProcess(
            args=["python", "validate_pre_live_gate_v25.py"],
            returncode=0,
            stdout="validator ok\n",
            stderr="",
        )

    monkeypatch.setattr(runner.subprocess, "run", _fake_run)
    ok, payload = runner.run_pre_live_validator(
        tmp_path,
        tmp_path,
        target_policy="cost",
        target_phases=["A", "H", "D", "C"],
        allow_online_preflight=True,
    )
    assert ok is True
    assert payload["status"] == "pass"
    assert called["args"][2:] == [
        "--target-policy",
        "cost",
        "--target-phases",
        "A",
        "H",
        "D",
        "C",
        "--allow-online-preflight",
    ]
    saved = json.loads((tmp_path / "PRELIVE_VALIDATOR_RESULT.json").read_text(encoding="utf-8"))
    assert saved["exit_code"] == 0
    assert saved["status"] == "pass"


def test_run_provider_preflight_records_openrouter_specific_remediation(
    monkeypatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)

    monkeypatch.setattr(
        runner,
        "collect_provider_routes",
        lambda phases, routing_policy, selected_step_ids_by_phase=None: {
            "openrouter:openai/gpt-5.3-codex:OPENROUTER_API_KEY": {
                "provider": "openrouter",
                "model_id": "openai/gpt-5.3-codex",
                "api_key_env": "OPENROUTER_API_KEY",
            }
        },
    )
    monkeypatch.setattr(
        runner,
        "run_provider_doctor_probe",
        lambda **kwargs: {
            "provider": "openrouter",
            "model_id": "openai/gpt-5.3-codex",
            "api_key_env_name": "OPENROUTER_API_KEY",
            "api_key_env_resolved": "OPENROUTER_API_KEY",
            "failure_type": "auth_rejected",
            "status_code": 401,
            "provider_signature": "provider=openrouter;model=openai/gpt-5.3-codex",
        },
    )
    ok, payload = runner.run_provider_preflight(
        tmp_path,
        "run_openrouter_blocked",
        cfg,
        ["A", "H", "D", "C"],
    )
    assert ok is False
    assert payload["failure_summary"][0]["api_key_env"] == "OPENROUTER_API_KEY"
    assert "A/H/D/C routes still require this OpenRouter model" in str(
        payload["failure_summary"][0]["remediation"]
    )
    run_local = json.loads(
        (
            runner.current_runs_root(tmp_path)
            / "run_openrouter_blocked"
            / "PROVIDER_PREFLIGHT.json"
        ).read_text(encoding="utf-8")
    )
    assert run_local["status"] == "FAIL"
    assert run_local["phase_scope"] == ["A", "H", "D", "C"]
    assert run_local["step_scope"] == {}
    assert run_local["scope_kind"] == "launch"
    assert run_local["scope_complete_for_launch"] is True


def test_prepare_phase_provider_preflight_writes_partial_scope_file_without_canonical_run_root(
    monkeypatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    object.__setattr__(cfg, "dry_run", False)

    monkeypatch.setattr(
        runner,
        "collect_provider_routes",
        lambda phases, routing_policy, selected_step_ids_by_phase=None: {
            "openrouter:openai/gpt-5.3-codex:OPENROUTER_API_KEY": {
                "provider": "openrouter",
                "model_id": "openai/gpt-5.3-codex",
                "api_key_env": "OPENROUTER_API_KEY",
            }
        },
    )
    monkeypatch.setattr(
        runner,
        "run_provider_doctor_probe",
        lambda **kwargs: {
            "provider": "openrouter",
            "model_id": "openai/gpt-5.3-codex",
            "api_key_env_name": "OPENROUTER_API_KEY",
            "api_key_env_resolved": "OPENROUTER_API_KEY",
            "failure_type": None,
            "status_code": 200,
            "provider_signature": "provider=openrouter;model=openai/gpt-5.3-codex",
            "ready": True,
            "readiness_blocker": {"ready": True},
        },
    )

    run_root = runner.current_runs_root(tmp_path) / "run_d_partial_scope"
    run_root.mkdir(parents=True, exist_ok=True)

    updated_cfg = runner.prepare_phase_provider_preflight(
        tmp_path,
        "run_d_partial_scope",
        "D",
        cfg,
    )

    assert tuple(updated_cfg.provider_denylist) == ()
    assert (run_root / "PROVIDER_PREFLIGHT.json").exists() is False
    partial = json.loads((run_root / "PROVIDER_PREFLIGHT__D.json").read_text(encoding="utf-8"))
    assert partial["status"] == "PASS"
    assert partial["phase_scope"] == ["D"]
    assert partial["scope_kind"] == "phase"
    assert partial["scope_complete_for_launch"] is False


def test_prepare_phase_provider_preflight_skips_redundant_probe_when_launch_scope_exists(
    monkeypatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)
    object.__setattr__(cfg, "dry_run", False)

    run_root = runner.current_runs_root(tmp_path) / "run_d_skip_preflight"
    run_root.mkdir(parents=True, exist_ok=True)
    canonical = run_root / "PROVIDER_PREFLIGHT.json"
    canonical.write_text(
        json.dumps(
            {
                "status": "PASS",
                "phase_scope": ["A", "H", "D", "C"],
                "step_scope": {},
                "scope_kind": "launch",
                "scope_complete_for_launch": True,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        runner,
        "collect_provider_routes",
        lambda phases, routing_policy, selected_step_ids_by_phase=None: {
            "openrouter:openai/gpt-5.3-codex:OPENROUTER_API_KEY": {
                "provider": "openrouter",
                "model_id": "openai/gpt-5.3-codex",
                "api_key_env": "OPENROUTER_API_KEY",
            }
        },
    )

    def fail_probe(**kwargs):  # type: ignore[no-untyped-def]
        raise AssertionError("phase preflight should be skipped when launch scope already covers D")

    monkeypatch.setattr(runner, "run_provider_doctor_probe", fail_probe)

    updated_cfg = runner.prepare_phase_provider_preflight(
        tmp_path,
        "run_d_skip_preflight",
        "D",
        cfg,
    )

    assert tuple(updated_cfg.provider_denylist) == ()
    assert canonical.exists() is True
    assert (run_root / "PROVIDER_PREFLIGHT__D.json").exists() is False


def test_route_readiness_summary_distinguishes_required_fallback_and_configured(monkeypatch) -> None:
    runner = _load_runner_module()
    monkeypatch.delenv("DPMX_EXPLICIT_STEP_ROUTES", raising=False)
    summary = runner.derive_route_readiness_summary(["A", "H", "D"], "cost")

    assert "OPENROUTER_API_KEY" in summary["api_key_env_categories"]["required_active_route"]
    assert "GEMINI_API_KEY" in summary["api_key_env_categories"]["required_active_route"]
    assert "XAI_API_KEY" in summary["api_key_env_categories"]["optional_fallback"]
    assert "OPENAI_API_KEY" in summary["api_key_env_categories"]["configured_not_required"]

    openrouter_required = [
        row
        for row in summary["routes"]
        if row["provider"] == "openrouter"
        and row["model_id"] == "openai/gpt-5.3-codex"
    ]
    assert openrouter_required
    assert openrouter_required[0]["requirement_level"] == "required_active_route"
    assert openrouter_required[0]["configured_not_required"] is False


def test_route_readiness_summary_honors_explicit_step_routes(monkeypatch) -> None:
    runner = _load_runner_module()
    monkeypatch.setenv(
        "DPMX_EXPLICIT_STEP_ROUTES",
        json.dumps(
            {
                "enabled": True,
                "steps": {"H:H3": "openrouter/openai/gpt-5.4"},
                "phases": {"H": "openrouter/openai/gpt-5.4"},
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
    )

    summary = runner.derive_route_readiness_summary(["H"], "cost")
    required_routes = {
        f"{row['provider']}/{row['model_id']}"
        for row in summary["routes"]
        if row["requirement_level"] == "required_active_route"
    }

    assert required_routes == {"openrouter/openai/gpt-5.4"}


def test_print_config_includes_route_readiness_summary() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py"),
            "--preset",
            "first-live",
            "--dry-run",
            "--print-config",
            "--run-id",
            "tp6_print_config_test",
            "--no-write-latest",
        ],
        cwd=str(_repo_root()),
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    summary = payload["route_readiness_summary"]

    assert summary["target_policy"] == "cost"
    assert summary["target_phases"] == ["A", "H", "D", "C"]
    assert "OPENROUTER_API_KEY" in summary["api_key_env_categories"]["required_active_route"]
    assert "XAI_API_KEY" in summary["api_key_env_categories"]["required_active_route"]
    assert "OPENAI_API_KEY" in summary["api_key_env_categories"]["required_active_route"]
    assert summary["api_key_env_categories"]["configured_not_required"] == []
    assert payload["effective_model_routing"]["A"]["scope"] == "representative_phase_default_not_step_authoritative"


def test_print_config_reports_batch_mode_disabled_by_default() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py"),
            "--phase",
            "A",
            "--dry-run",
            "--print-config",
            "--run-id",
            "tp6_batch_default_probe",
            "--no-write-latest",
        ],
        cwd=str(_repo_root()),
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["cli"]["batch_mode"] is False


def test_print_phase_routing_handles_two_tuple_ladder_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)

    monkeypatch.setattr(
        runner,
        "get_phase_prompts",
        lambda phase: [
            runner.PromptSpec(
                step_id="A0",
                prompt_path=Path("/tmp/PROMPT_A0_TEST.md"),
                output_artifacts=("OUT.json",),
            )
        ],
    )
    monkeypatch.setattr(
        runner,
        "resolve_effective_step_route",
        lambda *args, **kwargs: {
            "step_type": "extract",
            "step_tier": "extract",
            "provider": "openrouter",
            "model_id": "openai/gpt-5.3-codex",
            "reason": "test_override",
            "ladder": [
                ("openrouter", "openai/gpt-5.3-codex"),
                ("openrouter", "openai/gpt-5.4", "OPENROUTER_API_KEY"),
            ],
        },
    )

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        exit_code = runner.print_phase_routing(["A"], cfg)

    payload = json.loads(buffer.getvalue())
    assert exit_code == 0
    assert payload["phases"]["A"][0]["ladder"] == [
        {
            "provider": "openrouter",
            "model_id": "openai/gpt-5.3-codex",
            "api_key_env": "",
        },
        {
            "provider": "openrouter",
            "model_id": "openai/gpt-5.4",
            "api_key_env": "OPENROUTER_API_KEY",
        },
    ]


def test_staged_safe_print_config_writes_confidence_ramp_artifacts(
    tmp_path: Path,
) -> None:
    output_root = tmp_path / "artifact-root"
    run_id = "tp6_staged_safe_artifact_probe"
    result = subprocess.run(
        [
            sys.executable,
            str(_repo_root() / "services" / "repo-truth-extractor" / "run_extraction_v5.py"),
            "--preset",
            "staged-safe",
            "--dry-run",
            "--print-config",
            "--run-id",
            run_id,
            "--no-write-latest",
            "--output-root",
            str(output_root),
        ],
        cwd=str(_repo_root()),
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    run_root = output_root / "runs" / run_id
    batch_pilot = json.loads((run_root / "BATCH_PILOT.json").read_text(encoding="utf-8"))
    phase_slice = json.loads((run_root / "PHASE_SLICE.json").read_text(encoding="utf-8"))
    breaker_state = json.loads((run_root / "BREAKER_STATE.json").read_text(encoding="utf-8"))
    gate_decision = json.loads((run_root / "PHASE_GATE_DECISION.json").read_text(encoding="utf-8"))
    certification_result = json.loads((run_root / "CERTIFICATION_RESULT.json").read_text(encoding="utf-8"))

    assert payload["cli"]["preset"] == "staged-safe"
    assert payload["cli"]["batch_mode"] is True
    assert batch_pilot["preset"] == "staged-safe"
    assert batch_pilot["batch_mode"] is True
    assert phase_slice["selected_phases"] == ["A", "H", "D", "C"]
    assert breaker_state["preset"] == "staged-safe"
    assert gate_decision["preset"] == "staged-safe"
    assert gate_decision["decision"] == "PREVIEW_ONLY"
    assert certification_result["artifact_version"] == "RTE_CERTIFICATION_V1"
    assert certification_result["overall_status"] == "UNKNOWN"
    assert set(certification_result["gate_classification"]) == {
        "artifact_contract_stability",
        "canonical_runner_correctness",
        "live_provider_readiness",
        "operator_topology_resilience",
    }


def test_run_phase_s_blocks_on_empty_r_outputs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    root = tmp_path / "run"
    dirs = {"root": root}
    for phase in runner.PHASES:
        phase_dir = root / runner.PHASE_DIR_NAMES[phase]
        dirs[phase] = phase_dir
        (phase_dir / "norm").mkdir(parents=True, exist_ok=True)
        (phase_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (dirs["R"] / "norm" / "R0_CONTROL_PLANE_TRUTH_MAP.md").write_text("", encoding="utf-8")
    monkeypatch.setattr(runner, "_run_phase_inner", lambda *args, **kwargs: None)
    with pytest.raises(RuntimeError, match="minimum-quality R outputs"):
        runner.run_phase_S(dirs, _make_cfg(runner))


def test_run_phase_s_blocks_on_invalid_r_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    root = tmp_path / "run"
    dirs = {"root": root}
    for phase in runner.PHASES:
        phase_dir = root / runner.PHASE_DIR_NAMES[phase]
        dirs[phase] = phase_dir
        (phase_dir / "norm").mkdir(parents=True, exist_ok=True)
        (phase_dir / "inputs").mkdir(parents=True, exist_ok=True)
    (dirs["R"] / "norm" / "R_ARBITRATION.json").write_text("{not-json", encoding="utf-8")
    monkeypatch.setattr(runner, "_run_phase_inner", lambda *args, **kwargs: None)
    with pytest.raises(RuntimeError, match="minimum-quality R outputs"):
        runner.run_phase_S(dirs, _make_cfg(runner))


def test_classify_provider_readiness_blocker_distinguishes_env_auth_and_quota() -> None:
    runner = _load_runner_module()

    missing = runner.classify_provider_readiness_blocker(
        provider="openrouter",
        model_id="openai/gpt-5.4",
        api_key_env="OPENROUTER_API_KEY",
        api_key_present=False,
        status_code=None,
        failure_type="auth_missing",
        provider_error_reason=None,
    )
    auth = runner.classify_provider_readiness_blocker(
        provider="openrouter",
        model_id="openai/gpt-5.4",
        api_key_env="OPENROUTER_API_KEY",
        api_key_present=True,
        status_code=401,
        failure_type="auth_rejected",
        provider_error_reason="user not found",
    )
    quota = runner.classify_provider_readiness_blocker(
        provider="openai",
        model_id="gpt-5.4",
        api_key_env="OPENAI_API_KEY",
        api_key_present=True,
        status_code=429,
        failure_type="quota_or_billing",
        provider_error_reason="insufficient_quota",
    )

    assert missing["blocker_code"] == "API_KEY_MISSING"
    assert missing["rerun_worthiness"] == "rerun_after_env_fix"
    assert auth["blocker_code"] == "PROVIDER_AUTH_REJECTED"
    assert auth["remediation_class"] == "fix_provider_credentials_or_permissions"
    assert quota["blocker_code"] == "QUOTA_OR_BILLING_BLOCK"
    assert quota["rerun_worthiness"] == "rerun_after_billing_fix"


def test_run_provider_preflight_emits_machine_readable_readiness_blockers(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    runner = _load_runner_module()
    cfg = _make_cfg(runner)

    monkeypatch.setattr(
        runner,
        "collect_provider_routes",
        lambda phases, routing_policy, selected_step_ids_by_phase=None: {
            "openrouter:openai/gpt-5.4:OPENROUTER_API_KEY": {
                "provider": "openrouter",
                "model_id": "openai/gpt-5.4",
                "api_key_env": "OPENROUTER_API_KEY",
            },
            "openai:gpt-5.4:OPENAI_API_KEY": {
                "provider": "openai",
                "model_id": "gpt-5.4",
                "api_key_env": "OPENAI_API_KEY",
            },
        },
    )

    def _fake_probe(provider, model_id, api_key_env, cfg):  # type: ignore[no-untyped-def]
        if provider == "openrouter":
            return {
                "provider": provider,
                "model_id": model_id,
                "api_key_env_name": api_key_env,
                "api_key_env_resolved": api_key_env,
                "status_code": 401,
                "failure_type": "auth_rejected",
                "provider_signature": f"{provider}:{model_id}",
                "ready": False,
                "readiness_blocker": {
                    "ready": False,
                    "blocker_code": "PROVIDER_AUTH_REJECTED",
                    "blocker_class": "auth",
                    "remediation_class": "fix_provider_credentials_or_permissions",
                    "rerun_worthiness": "rerun_after_auth_fix",
                    "human_summary": "blocked",
                },
            }
        return {
            "provider": provider,
            "model_id": model_id,
            "api_key_env_name": api_key_env,
            "api_key_env_resolved": api_key_env,
            "status_code": 429,
            "failure_type": "quota_or_billing",
            "provider_signature": f"{provider}:{model_id}",
            "ready": False,
            "readiness_blocker": {
                "ready": False,
                "blocker_code": "QUOTA_OR_BILLING_BLOCK",
                "blocker_class": "quota_billing",
                "remediation_class": "restore_quota_or_billing",
                "rerun_worthiness": "rerun_after_billing_fix",
                "human_summary": "blocked",
            },
        }

    monkeypatch.setattr(runner, "run_provider_doctor_probe", _fake_probe)

    ok, payload = runner.run_provider_preflight(tmp_path, "ops_readiness_probe", cfg, ["A"])

    assert ok is False
    assert payload["status"] == "FAIL"
    assert payload["failed_blocker_codes"] == ["PROVIDER_AUTH_REJECTED", "QUOTA_OR_BILLING_BLOCK"]
    assert payload["rerun_worthiness"] == "worth_rerunning_after_fixes"
    assert payload["failure_summary"][0]["readiness_blocker"]["blocker_code"] in {
        "PROVIDER_AUTH_REJECTED",
        "QUOTA_OR_BILLING_BLOCK",
    }
