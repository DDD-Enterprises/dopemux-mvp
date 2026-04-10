from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.cli.benchmark_scoring_smoke import run_scoring_smoke


def test_rollups_generate_case_set_archetype_profile_and_portfolio_outputs(tmp_path: Path) -> None:
    proof_dir = tmp_path / "proof"
    payload = run_scoring_smoke(root=tmp_path / "benchmarks", proof_dir=proof_dir)
    assert payload["db_row_counts"]["benchmark_case_attempt"] == 12
    assert payload["db_row_counts"]["control_delta"] >= 30
    assert payload["sample_case_set_rollup"]["case_set_id"] == "benchmark_registry_starter_v1"
    assert payload["sample_profile_fit"]["profile_id"]
    assert payload["sample_portfolio_view"]["view_type"] == "portfolio_matrix"
    assert payload["sample_portfolio_view"]["ranking_present"] is False
    assert (proof_dir / "sample_regression_comparison.json").exists()
