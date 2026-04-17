from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v5", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_telemetry_snapshot_writers_are_deterministic(tmp_path: Path) -> None:
    runner = _load_runner_module()

    runner.write_step_metrics_snapshot(
        tmp_path,
        phase="D",
        step_id="D1",
        metrics={"ok": 10, "failed": 2, "repair_invocations": 4},
    )
    runner.write_step_metrics_snapshot(
        tmp_path,
        phase="C",
        step_id="C9",
        metrics={"ok": 5, "failed": 0, "repair_invocations": 0},
    )
    step_metrics = json.loads(
        (tmp_path / "telemetry" / "STEP_METRICS.json").read_text(encoding="utf-8")
    )
    assert list(step_metrics["steps"].keys()) == ["C:C9", "D:D1"]
    assert step_metrics["steps"]["D:D1"]["repair_invocations"] == 4

    runner.write_failure_index_snapshot(
        tmp_path,
        phase="D",
        step_id="D1",
        failure_histogram={"schema_missing_key": 3, "missing_expected_artifacts": 1},
        first_failure={"partition_id": "D_P0002", "failure_class": "schema_missing_key"},
    )
    runner.write_failure_index_snapshot(
        tmp_path,
        phase="C",
        step_id="C8",
        failure_histogram={"provider": 2},
        first_failure={
            "partition_id": "C_P0009",
            "failure_class": "provider",
            "remediation_hint": "Check provider auth/quota/status.",
        },
    )
    failure_index = json.loads(
        (tmp_path / "telemetry" / "FAILURE_INDEX.json").read_text(encoding="utf-8")
    )
    assert list(failure_index["steps"].keys()) == ["C:C8", "D:D1"]
    assert failure_index["global_failure_histogram"]["schema_missing_key"] == 3
    assert (
        failure_index["steps"]["C:C8"]["first_failure"]["remediation_hint"]
        == "Check provider auth/quota/status."
    )

    dashboard = runner.write_run_dashboard_snapshot(
        tmp_path,
        payload={
            "summary": {"PASS": 9, "FAIL": 1, "IN_PROGRESS": 0, "NOT_STARTED": 3},
            "phases": {"D": {"status": "PASS"}},
        },
        source="run_complete",
    )
    assert dashboard["source"] == "run_complete"
    dashboard_file = json.loads(
        (tmp_path / "telemetry" / "RUN_DASHBOARD.json").read_text(encoding="utf-8")
    )
    assert dashboard_file["summary"]["PASS"] == 9


def test_build_first_failure_context_preserves_requested_and_final_routes() -> None:
    runner = _load_runner_module()

    payload = runner.build_first_failure_context(
        partition_id="H_P0001",
        failure_class="payload",
        failure_stage="model_execution",
        reason="payload",
        artifact_name=None,
        item_key=None,
        item_id=None,
        item_path=None,
        remediation_hint="Check provider auth/quota/status.",
        request_meta={
            "failure_type": "payload",
            "status_code": 402,
            "route_attempts": [
                {
                    "provider": "openrouter",
                    "model_id": "openai/gpt-5.3-codex",
                },
                {
                    "provider": "openrouter",
                    "model_id": "openai/gpt-5.4",
                },
            ],
        },
        requested_provider="openrouter",
        requested_model_id="openai/gpt-5.3-codex",
        final_provider="openrouter",
        final_model_id="openai/gpt-5.4",
    )

    assert payload["route"] == "openrouter/openai/gpt-5.4"
    assert payload["requested_route"] == "openrouter/openai/gpt-5.3-codex"
    assert payload["route_attempts"] == [
        "openrouter/openai/gpt-5.3-codex",
        "openrouter/openai/gpt-5.4",
    ]
    assert payload["underlying_failure_type"] == "payload"
    assert payload["underlying_status_code"] == 402
