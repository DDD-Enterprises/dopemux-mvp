from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

from extractor.ui import UI, UiConfig


def _load_runner_module(module_name: str = "run_extraction_v5"):
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v5.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
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


def test_extracted_ui_uses_injected_jsonl_writer(tmp_path: Path) -> None:
    writes: list[tuple[Path, dict]] = []

    def append_jsonl(path: Path, payload: dict) -> None:
        writes.append((path, payload))

    ui = UI(
        UiConfig(mode="plain", quiet=True, jsonl_events=True),
        run_root=tmp_path,
        run_id="run_injected_writer",
        append_jsonl=append_jsonl,
    )

    ui._emit_event({"type": "injected_writer_probe"})

    assert [path.relative_to(tmp_path).as_posix() for path, _ in writes] == [
        "telemetry/TERMINAL_TIMELINE.jsonl",
        "events.jsonl",
    ]
    assert all(payload["run_id"] == "run_injected_writer" for _, payload in writes)
    assert not (tmp_path / "events.jsonl").exists()


def test_v5_facade_reexports_extracted_ui_symbols() -> None:
    runner = _load_runner_module()

    assert issubclass(runner.UI, UI)
    assert runner.UiConfig is UiConfig


def test_v5_facade_keeps_each_dynamic_runner_bound_to_its_own_writer(
    tmp_path: Path,
) -> None:
    runner_a = _load_runner_module("run_extraction_v5_writer_a")
    runner_b = _load_runner_module("run_extraction_v5_writer_b")

    ui_a = runner_a.UI(
        runner_a.UiConfig(mode="plain", quiet=True),
        run_root=tmp_path / "a",
        run_id="run_a",
    )
    ui_b = runner_b.UI(
        runner_b.UiConfig(mode="plain", quiet=True),
        run_root=tmp_path / "b",
        run_id="run_b",
    )

    assert ui_a._append_jsonl.__module__ == runner_a.__name__
    assert ui_b._append_jsonl.__module__ == runner_b.__name__
    assert (
        ui_a._append_jsonl.__globals__["_JSONL_WRITE_LOCK"]
        is runner_a._JSONL_WRITE_LOCK
    )
    assert (
        ui_b._append_jsonl.__globals__["_JSONL_WRITE_LOCK"]
        is runner_b._JSONL_WRITE_LOCK
    )

    ui_a._emit_event({"type": "runner_a_probe"})
    ui_b._emit_event({"type": "runner_b_probe"})

    assert _read_jsonl(tmp_path / "a" / "telemetry" / "TERMINAL_TIMELINE.jsonl")[
        0
    ]["run_id"] == "run_a"
    assert _read_jsonl(tmp_path / "b" / "telemetry" / "TERMINAL_TIMELINE.jsonl")[
        0
    ]["run_id"] == "run_b"


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
        route="openrouter/openai/gpt-5.4",
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
