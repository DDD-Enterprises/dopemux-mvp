from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_runner_module():
    root = Path(__file__).resolve().parents[3]
    module_path = root / "services" / "repo-truth-extractor" / "run_extraction_v3.py"
    spec = importlib.util.spec_from_file_location("run_extraction_v3", module_path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


runner = _load_runner_module()


def test_build_partition_context_numbers_lines_for_phase_d(tmp_path: Path) -> None:
    sample = tmp_path / "doc.md"
    sample.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")

    context, stats = runner.build_partition_context(
        phase="D",
        partition_paths=[str(sample)],
        file_truncate_chars=200,
        home_scan_mode="safe",
        max_files=5,
        max_chars=500,
    )

    assert stats["files_included"] == 1
    assert "--- FILE:" in context
    assert "1: alpha" in context
    assert "2: beta" in context
    assert "3: gamma" in context


def test_artifacts_schema_gate_rejects_missing_line_range() -> None:
    ok, reason = runner.artifacts_pass_schema_gate(
        artifacts=[{"artifact_name": "OUT.json", "payload": {"items": [{"id": "x", "path": "docs/a.md"}]}}],
        expected_artifact_names=("OUT.json",),
    )
    assert ok is False
    assert reason == "schema_missing_key:line_range"


def test_artifacts_schema_gate_rejects_invalid_line_range_shape() -> None:
    ok, reason = runner.artifacts_pass_schema_gate(
        artifacts=[
            {
                "artifact_name": "OUT.json",
                "payload": {"items": [{"id": "x", "path": "docs/a.md", "line_range": [3]}]},
            }
        ],
        expected_artifact_names=("OUT.json",),
    )
    assert ok is False
    assert reason == "schema_invalid_line_range"


def test_artifacts_schema_gate_accepts_valid_line_range_shape() -> None:
    ok, reason = runner.artifacts_pass_schema_gate(
        artifacts=[
            {
                "artifact_name": "OUT.json",
                "payload": {"items": [{"id": "x", "path": "docs/a.md", "line_range": [3, 5]}]},
            }
        ],
        expected_artifact_names=("OUT.json",),
    )
    assert ok is True
    assert reason is None
