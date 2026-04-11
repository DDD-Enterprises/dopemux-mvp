from __future__ import annotations

import sys
from pathlib import Path


SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.cli.benchmark_reporting_smoke import run_reporting_smoke


def test_reporting_views_render_and_preserve_matrix_structure(tmp_path: Path) -> None:
    proof_dir = tmp_path / "proof"
    payload = run_reporting_smoke(root=tmp_path / "benchmarks", proof_dir=proof_dir)
    portfolio = payload["sample_portfolio_summary"]
    profile = payload["sample_profile_summary"]
    assert portfolio["view_type"] == "portfolio_summary"
    assert portfolio["matrix_preserved"] is True
    assert portfolio["benchmark_modes"] == ["runtime_route"]
    assert portfolio["lane_isolation_preserved"] is True
    assert "recommended_for_review" in portfolio["recommendation_state_counts"]
    assert profile["profile_id"]
    assert profile["benchmark_modes"] == ["runtime_route"]
    assert (proof_dir / "sample_portfolio_summary.json").exists()
