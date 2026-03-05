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


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parsed = json.loads(line)
        assert isinstance(parsed, dict)
        rows.append(parsed)
    return rows


def test_ui_events_emit_schema_to_events_and_timeline(tmp_path: Path) -> None:
    runner = _load_runner_module()
    ui = runner.UI(
        runner.UiConfig(mode="plain", quiet=False, jsonl_events=True),
        run_root=tmp_path,
        run_id="run_ui_events",
    )

    ui.step_heartbeat(
        phase="D",
        step_id="D1",
        completed=10,
        total=25,
        ok=8,
        failed=2,
        skipped=0,
        retried=1,
        escalated=2,
        repair=3,
        sidefill=1,
        soft_gate=0,
    )
    ui.failure_spotlight(
        phase="D",
        step_id="D1",
        partition_id="D_P0001",
        failure_class="schema_missing_key",
        reason="schema_missing_key:line_range",
        route="openrouter/openai/gpt-5.2",
        artifact_name="DOC_INDEX.partX.json",
        item_key="line_range",
        item_id="DOC_INDEX:item_1",
        item_path="docs/example.md",
        mode="full",
    )
    ui.step_top_failures(
        phase="D",
        step_id="D1",
        failure_histogram={
            "schema_missing_key": 2,
            "missing_expected_artifacts": 1,
        },
    )
    ui.run_dashboard_snapshot(
        {
            "summary": {
                "PASS": 2,
                "FAIL": 1,
                "IN_PROGRESS": 0,
                "NOT_STARTED": 0,
            }
        },
        source="phase:D:pass",
    )

    events_path = tmp_path / "events.jsonl"
    timeline_path = tmp_path / "telemetry" / "TERMINAL_TIMELINE.jsonl"
    assert events_path.exists()
    assert timeline_path.exists()

    events_rows = _read_jsonl(events_path)
    timeline_rows = _read_jsonl(timeline_path)
    assert len(events_rows) == len(timeline_rows)

    event_types = {str(row.get("type")) for row in events_rows}
    assert "step_heartbeat" in event_types
    assert "step_failure_spotlight" in event_types
    assert "step_top_failures" in event_types
    assert "run_dashboard_snapshot" in event_types

    for row in events_rows:
        assert row.get("run_id") == "run_ui_events"
        assert isinstance(row.get("run_root"), str)
        assert isinstance(row.get("ts"), str)
