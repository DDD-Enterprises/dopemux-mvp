from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
SERVICE_ROOT = HERE.parents[2]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.cli.benchmark_scoring_smoke import run_scoring_smoke
from benchmarking.storage.hashing import stable_json_dumps
from benchmarking.storage.paths import benchmark_paths
from benchmarking.synthesis.governance_pipeline import GovernanceSynthesisPipeline


def _pick_state(recommendations: list[dict[str, object]], state: str) -> dict[str, object]:
    for recommendation in recommendations:
        if recommendation.get("recommendation_state") == state:
            return recommendation
    return {}


def run_governance_smoke(root: Path | None = None, proof_dir: Path | None = None) -> dict[str, object]:
    scoring_payload = run_scoring_smoke(root=root, proof_dir=None)
    benchmark_run_id = str(scoring_payload["benchmark_run_id"])
    pipeline = GovernanceSynthesisPipeline(root)
    report = pipeline.synthesize_run(benchmark_run_id)
    recommendations = report["recommendations"]
    payload = {
        "benchmark_run_id": benchmark_run_id,
        "baseline_run_id": scoring_payload["baseline_run_id"],
        "db_row_counts": pipeline.repo.count_rows(),
        "sample_recommendation": _pick_state(recommendations, "recommended_for_review") or report["sample_recommendation"],
        "sample_experimental_recommendation": _pick_state(recommendations, "experimental_only"),
        "sample_governance_packet": report["sample_governance_packet"],
        "sample_governance_decision": report["sample_governance_decision"],
        "sample_portfolio_view": report["portfolio_view"],
    }
    if proof_dir is not None:
        proof_dir.mkdir(parents=True, exist_ok=True)
        benchmark_root = benchmark_paths(root).root
        (proof_dir / "RUN_MANIFEST.json").write_text(stable_json_dumps(payload) + "\n", encoding="utf-8")
        (proof_dir / "db_row_counts.json").write_text(stable_json_dumps(payload["db_row_counts"]) + "\n", encoding="utf-8")
        (proof_dir / "sample_recommendation.json").write_text(
            stable_json_dumps(payload["sample_recommendation"]) + "\n",
            encoding="utf-8",
        )
        (proof_dir / "sample_governance_packet.json").write_text(
            stable_json_dumps(payload["sample_governance_packet"]) + "\n",
            encoding="utf-8",
        )
        (proof_dir / "sample_governance_decision.json").write_text(
            stable_json_dumps(payload["sample_governance_decision"]) + "\n",
            encoding="utf-8",
        )
        (proof_dir / "sample_portfolio_view.json").write_text(
            stable_json_dumps(payload["sample_portfolio_view"]) + "\n",
            encoding="utf-8",
        )
        experimental = payload["sample_experimental_recommendation"]
        if experimental:
            (proof_dir / "sample_experimental_recommendation.json").write_text(
                stable_json_dumps(experimental) + "\n",
                encoding="utf-8",
            )
        tree_lines = sorted(str(path.relative_to(benchmark_root)) for path in benchmark_root.rglob("*"))
        (proof_dir / "benchmark_tree.txt").write_text("\n".join(tree_lines) + "\n", encoding="utf-8")
        (proof_dir / "smoke_output.txt").write_text(
            "\n".join(
                [
                    f"benchmark_run_id={benchmark_run_id}",
                    f"baseline_run_id={scoring_payload['baseline_run_id']}",
                    f"recommendation_total={len(recommendations)}",
                    f"decision_total={len(report['governance_decisions'])}",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="M4 governance smoke for benchmark recommendations and decisions.")
    parser.add_argument("--benchmark-root", type=Path, default=None)
    parser.add_argument("--proof-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = run_governance_smoke(root=args.benchmark_root, proof_dir=args.proof_dir)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
