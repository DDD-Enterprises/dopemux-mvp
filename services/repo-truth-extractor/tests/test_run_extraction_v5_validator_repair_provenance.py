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


def test_parse_json_provenance_clean_output_not_degraded() -> None:
    runner = _load_runner_module()

    parsed, provenance = runner.parse_json_from_response_with_provenance('{"ok": true}')
    finalized = runner.finalize_response_parse_provenance(
        provenance,
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        provider="openai",
        model_id="gpt-5-mini",
        contract_lane="extract",
        accepted=True,
    )

    assert parsed == {"ok": True}
    assert finalized["repair_applied"] is False
    assert finalized["final_disposition"] == "accepted_clean"
    assert finalized["degraded_acceptance"] is False


def test_parse_json_provenance_repaired_output_marked_degraded() -> None:
    runner = _load_runner_module()

    parsed, provenance = runner.parse_json_from_response_with_provenance(
        'prefix {"ok": true}'
    )
    finalized = runner.finalize_response_parse_provenance(
        provenance,
        phase="A",
        step_id="A0",
        partition_id="A_P0002",
        provider="openai",
        model_id="gpt-5-mini",
        contract_lane="extract",
        accepted=True,
    )

    assert parsed == {"ok": True}
    assert finalized["repair_applied"] is True
    assert finalized["repair_type"] == "extract_first_json_object"
    assert finalized["final_disposition"] == "accepted_degraded"
    assert finalized["degraded_acceptance"] is True


def test_parse_json_provenance_surfaces_claimed_strict_route() -> None:
    runner = _load_runner_module()

    parsed, provenance = runner.parse_json_from_response_with_provenance(
        'prefix {"ok": true}',
        claimed_strict_route=True,
    )
    finalized = runner.finalize_response_parse_provenance(
        provenance,
        phase="A",
        step_id="A0",
        partition_id="A_P0002",
        provider="openai",
        model_id="gpt-5-mini",
        contract_lane="extract",
        accepted=True,
    )

    assert parsed == {"ok": True}
    assert finalized["repair_applied"] is True
    assert finalized["claimed_strict_route"] is True

    metadata: dict[str, object] = {}
    assert runner.parse_json_from_response(
        'prefix {"ok": true}',
        metadata_out=metadata,
        claimed_strict_route=True,
    ) == {"ok": True}
    assert metadata["claimed_strict_route"] is True


def test_parse_json_provenance_rejected_output_is_deterministic() -> None:
    runner = _load_runner_module()

    parsed, provenance = runner.parse_json_from_response_with_provenance('{"ok": ')
    finalized = runner.finalize_response_parse_provenance(
        provenance,
        phase="A",
        step_id="A0",
        partition_id="A_P0003",
        provider="openai",
        model_id="gpt-5-mini",
        contract_lane="extract",
        accepted=False,
    )

    assert parsed is None
    assert finalized["final_disposition"] == "rejected"
    assert finalized["degraded_acceptance"] is False


def test_log_response_parse_repair_warns_only_for_repaired_output(
    caplog: pytest.LogCaptureFixture,
) -> None:
    runner = _load_runner_module()

    clean = runner.finalize_response_parse_provenance(
        {
            "repair_applied": False,
            "repair_type": None,
            "original_response_length": 12,
            "repaired_response_length": 12,
            "chars_lost": 0,
            "chars_delta": 0,
        },
        phase="A",
        step_id="A0",
        partition_id="A_P0001",
        provider="openai",
        model_id="gpt-5-mini",
        contract_lane="extract",
        accepted=True,
    )
    repaired = runner.finalize_response_parse_provenance(
        {
            "repair_applied": True,
            "repair_type": "extract_first_json_object",
            "original_response_length": 20,
            "repaired_response_length": 12,
            "chars_lost": 8,
            "chars_delta": -8,
        },
        phase="A",
        step_id="A0",
        partition_id="A_P0002",
        provider="openai",
        model_id="gpt-5-mini",
        contract_lane="extract",
        accepted=True,
    )

    with caplog.at_level("WARNING"):
        runner.log_response_parse_repair(clean)
        runner.log_response_parse_repair(repaired)

    records = [record.message for record in caplog.records]
    assert len(records) == 1
    assert "RESPONSE_PARSE_REPAIRED" in records[0]


def test_write_phase_coverage_manifest_persists_repair_metadata(
    tmp_path: Path,
) -> None:
    runner = _load_runner_module()
    phase_dir = tmp_path / "A_repo_control_plane"
    raw_dir = phase_dir / "raw"
    qa_dir = phase_dir / "qa"
    norm_dir = phase_dir / "norm"
    raw_dir.mkdir(parents=True, exist_ok=True)
    qa_dir.mkdir(parents=True, exist_ok=True)
    norm_dir.mkdir(parents=True, exist_ok=True)

    raw_payload = {
        "phase": "A",
        "step_id": "A0",
        "partition_id": "A_P0002",
        "artifacts": [{"artifact_name": "A.json", "payload": {"ok": True}}],
        "request_meta": {
            "response_parse_provenance": {
                "phase": "A",
                "step_id": "A0",
                "partition_id": "A_P0002",
                "provider": "openai",
                "model_id": "gpt-5-mini",
                "contract_lane": "extract",
                "repair_applied": True,
                "repair_type": "extract_first_json_object",
                "original_response_length": 20,
                "repaired_response_length": 12,
                "chars_lost": 8,
                "chars_delta": -8,
                "final_disposition": "accepted_degraded",
                "degraded_acceptance": True,
            }
        },
    }
    (raw_dir / "A0__A_P0002.json").write_text(
        json.dumps(raw_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    payload = runner.write_phase_coverage_manifest("A", phase_dir)

    assert payload["response_parse_repairs"]["events_total"] == 1
    assert (
        payload["response_parse_repairs"]["final_disposition_histogram"][
            "accepted_degraded"
        ]
        == 1
    )
    coverage_path = qa_dir / "PHASE_A_COVERAGE.json"
    written = json.loads(coverage_path.read_text(encoding="utf-8"))
    assert written["response_parse_repairs"]["events"][0]["repair_type"] == (
        "extract_first_json_object"
    )
