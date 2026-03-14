"""Tests for TP-RTX-V5-GROK-DOC-COMPARISON-STEP-0001: comparison summary generation.

Verifies:
- COMPARE_SUMMARY_{STEP}.json contains all required fields
- COMPARE_SUMMARY_{STEP}.md is also written
- Summary correctly aggregates canonical vs comparison pass/fail counts
- Summary records correct route info for both lanes
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any



# ---------------------------------------------------------------------------
# Module loader
# ---------------------------------------------------------------------------

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


def _build_canonical_results(step_id: str, n_partitions: int = 2) -> list:
    return [
        {
            "partition_id": f"{step_id[0]}_P{i:04d}",
            "success": True,
            "request_meta": {
                "lane": "canonical",
                "authoritative": True,
                "provider": "openai",
                "model_id": "gpt-5-mini",
                "elapsed_ms": 1200 + i * 100,
                "final_contract_status": "pass",
                "repair_invocations": 0,
                "repair_successes": 0,
            },
        }
        for i in range(n_partitions)
    ]


def _build_comparison_results(step_id: str, n_pass: int = 2, n_fail: int = 0) -> list:
    results = []
    for i in range(n_pass):
        results.append({
            "partition_id": f"{step_id[0]}_P{i:04d}",
            "success": True,
            "request_meta": {
                "lane": "comparison",
                "authoritative": False,
                "provider": "xai",
                "model_id": "grok-4.20-beta",
                "elapsed_ms": 980 + i * 80,
                "final_contract_status": "pass",
                "repair_invocations": 0,
                "repair_successes": 0,
            },
        })
    for j in range(n_fail):
        idx = n_pass + j
        results.append({
            "partition_id": f"{step_id[0]}_P{idx:04d}",
            "success": False,
            "request_meta": {
                "lane": "comparison",
                "authoritative": False,
                "provider": "xai",
                "model_id": "grok-4.20-beta",
                "elapsed_ms": 500,
                "final_contract_status": "fail",
                "repair_invocations": 1,
                "repair_successes": 0,
                "failure_type": "parse_error",
            },
        })
    return results


# ---------------------------------------------------------------------------
# T9 (from plan, also T_summary_1): Summary has all required fields
# ---------------------------------------------------------------------------

def test_comparison_summary_has_required_fields(tmp_path: Path) -> None:
    """generate_comparison_summary must produce a summary with all required fields."""
    runner = _load_runner_module()

    assert hasattr(runner, "generate_comparison_summary"), (
        "run_extraction_v5 must expose generate_comparison_summary()"
    )

    eligible = list(runner.COMPARISON_ELIGIBLE_STEPS)
    step_id = eligible[0]
    phase_dir = tmp_path / "A_phase_dir"
    phase_dir.mkdir(parents=True)

    canonical_results = _build_canonical_results(step_id, n_partitions=2)
    comparison_results = _build_comparison_results(step_id, n_pass=2, n_fail=0)

    summary = runner.generate_comparison_summary(
        phase_dir=phase_dir,
        step_id=step_id,
        canonical_results=canonical_results,
        comparison_results=comparison_results,
        compare_provider="xai",
        compare_model="grok-4.20-beta",
    )

    required_fields = {
        "step_id",
        "canonical_route",
        "comparison_route",
        "partitions_compared",
        "canonical_contract_pass_count",
        "canonical_contract_fail_count",
        "comparison_contract_pass_count",
        "comparison_contract_fail_count",
        "canonical_repair_count",
        "comparison_repair_count",
        "canonical_latency_ms_mean",
        "comparison_latency_ms_mean",
    }

    missing = required_fields - set(summary.keys())
    assert not missing, f"Summary missing required fields: {sorted(missing)}"


# ---------------------------------------------------------------------------
# Summary written to disk as JSON + MD
# ---------------------------------------------------------------------------

def test_comparison_summary_writes_json_and_md(tmp_path: Path) -> None:
    """generate_comparison_summary must write both .json and .md artifacts."""
    runner = _load_runner_module()

    assert hasattr(runner, "generate_comparison_summary"), (
        "run_extraction_v5 must expose generate_comparison_summary()"
    )

    eligible = list(runner.COMPARISON_ELIGIBLE_STEPS)
    step_id = eligible[0]
    phase_dir = tmp_path / "A_phase_dir"
    phase_dir.mkdir(parents=True)

    canonical_results = _build_canonical_results(step_id)
    comparison_results = _build_comparison_results(step_id, n_pass=2)

    runner.generate_comparison_summary(
        phase_dir=phase_dir,
        step_id=step_id,
        canonical_results=canonical_results,
        comparison_results=comparison_results,
        compare_provider="xai",
        compare_model="grok-4.20-beta",
    )

    json_path = phase_dir / f"COMPARE_SUMMARY_{step_id}.json"
    md_path = phase_dir / f"COMPARE_SUMMARY_{step_id}.md"

    assert json_path.exists(), f"COMPARE_SUMMARY_{step_id}.json must be written"
    assert md_path.exists(), f"COMPARE_SUMMARY_{step_id}.md must be written"

    # JSON must be valid
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["step_id"] == step_id

    # MD must contain step_id
    md_text = md_path.read_text(encoding="utf-8")
    assert step_id in md_text, f"Markdown summary must mention step_id {step_id}"


# ---------------------------------------------------------------------------
# Summary aggregates counts correctly
# ---------------------------------------------------------------------------

def test_comparison_summary_counts_correctly(tmp_path: Path) -> None:
    """Summary pass/fail counts must reflect actual results."""
    runner = _load_runner_module()

    assert hasattr(runner, "generate_comparison_summary"), (
        "run_extraction_v5 must expose generate_comparison_summary()"
    )

    eligible = list(runner.COMPARISON_ELIGIBLE_STEPS)
    step_id = eligible[0]
    phase_dir = tmp_path / "A_phase_dir"
    phase_dir.mkdir(parents=True)

    # 3 canonical passes, 2 comparison passes + 1 fail
    canonical_results = _build_canonical_results(step_id, n_partitions=3)
    comparison_results = _build_comparison_results(step_id, n_pass=2, n_fail=1)

    summary = runner.generate_comparison_summary(
        phase_dir=phase_dir,
        step_id=step_id,
        canonical_results=canonical_results,
        comparison_results=comparison_results,
        compare_provider="xai",
        compare_model="grok-4.20-beta",
    )

    assert summary["canonical_contract_pass_count"] == 3, (
        f"canonical pass count must be 3; got {summary['canonical_contract_pass_count']}"
    )
    assert summary["comparison_contract_pass_count"] == 2, (
        f"comparison pass count must be 2; got {summary['comparison_contract_pass_count']}"
    )
    assert summary["comparison_contract_fail_count"] == 1, (
        f"comparison fail count must be 1; got {summary['comparison_contract_fail_count']}"
    )
    assert summary["partitions_compared"] >= 1, (
        "partitions_compared must be >= 1"
    )


# ---------------------------------------------------------------------------
# Summary records route info for both lanes
# ---------------------------------------------------------------------------

def test_comparison_summary_records_route_info(tmp_path: Path) -> None:
    """Summary must record both canonical_route and comparison_route."""
    runner = _load_runner_module()

    assert hasattr(runner, "generate_comparison_summary"), (
        "run_extraction_v5 must expose generate_comparison_summary()"
    )

    eligible = list(runner.COMPARISON_ELIGIBLE_STEPS)
    step_id = eligible[0]
    phase_dir = tmp_path / "A_phase_dir"
    phase_dir.mkdir(parents=True)

    canonical_results = _build_canonical_results(step_id)
    comparison_results = _build_comparison_results(step_id)

    summary = runner.generate_comparison_summary(
        phase_dir=phase_dir,
        step_id=step_id,
        canonical_results=canonical_results,
        comparison_results=comparison_results,
        compare_provider="xai",
        compare_model="grok-4.20-beta",
    )

    canonical_route = summary.get("canonical_route", {})
    comparison_route = summary.get("comparison_route", {})

    assert isinstance(canonical_route, dict), "canonical_route must be a dict"
    assert isinstance(comparison_route, dict), "comparison_route must be a dict"

    # comparison_route must identify grok
    assert comparison_route.get("provider") == "xai" or comparison_route.get("model_id") == "grok-4.20-beta", (
        f"comparison_route must identify xai/grok-4.20-beta; got {comparison_route}"
    )
