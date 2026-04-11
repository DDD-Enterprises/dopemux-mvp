from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.cli.benchmark_profile_synth_smoke import run_profile_synth_smoke


def test_profile_synth_smoke_generates_reviewable_outputs(tmp_path: Path) -> None:
    payload = run_profile_synth_smoke(
        repo_root=ROOT,
        benchmark_root=tmp_path / "benchmarks",
        proof_dir=tmp_path / "proof",
    )

    proposal_classes = {item["proposal_class"] for item in payload["proposals"]}
    assert "admit_to_runtime_route_testing" in proposal_classes
    assert "candidate_for_low_cost_profile" in proposal_classes
    assert "insufficient_evidence" in proposal_classes or "experimental_only" in proposal_classes
    assert "blocked_lane" in proposal_classes
    assert payload["summary"]["feedback_loop_exists_in_reviewable_form"] is True
    assert (tmp_path / "proof" / "PROFILE_SYNTHESIS_SUMMARY.json").exists()
    assert (tmp_path / "proof" / "sample_profile_proposal.json").exists()
