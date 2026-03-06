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
        line = line.strip()
        if not line:
            continue
        parsed = json.loads(line)
        assert isinstance(parsed, dict)
        rows.append(parsed)
    return rows


def test_soft_gate_events_include_denominator_math_and_states(tmp_path: Path) -> None:
    runner = _load_runner_module()
    ui = runner.UI(
        runner.UiConfig(mode="plain", quiet=True, jsonl_events=True),
        run_root=tmp_path,
        run_id="run_soft_gate",
    )

    common = {
        "phase": "D",
        "step_id": "D2",
        "attempted_llm_partitions": 40,
        "resume_success_skips": 5,
        "deterministic_input_skips": 3,
        "n_total": 32,
        "fail_rate": 0.21875,
        "failed_partitions": 7,
    }
    ui.soft_gate_event(
        status="triggered",
        action="strict_fallback_route_resolution",
        fallback_route=None,
        **common,
    )
    ui.soft_gate_event(
        status="fallback_started",
        action="strict_fallback_batch",
        fallback_route="openrouter/openai/gpt-5.2",
        **common,
    )
    ui.soft_gate_event(
        status="fallback_done",
        action="strict_fallback_batch_done",
        fallback_route="openrouter/openai/gpt-5.2",
        remaining_failed=2,
        **common,
    )

    rows = _read_jsonl(tmp_path / "events.jsonl")
    types = [str(row.get("type")) for row in rows]
    assert "soft_gate_triggered" in types
    assert "strict_fallback_batch_started" in types
    assert "strict_fallback_batch_done" in types

    triggered = next(row for row in rows if row.get("type") == "soft_gate_triggered")
    assert triggered["attempted_llm_partitions"] == 40
    assert triggered["resume_success_skips"] == 5
    assert triggered["deterministic_input_skips"] == 3
    assert triggered["n_total"] == 32
    assert abs(float(triggered["fail_rate"]) - 0.21875) < 1e-9
