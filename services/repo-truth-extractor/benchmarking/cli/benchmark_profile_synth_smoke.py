from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve()
SERVICE_ROOT = HERE.parents[2]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.storage.hashing import stable_json_dumps
from benchmarking.synthesis.profile_synth import (
    synthesize_profile_proposals,
    write_profile_synthesis_artifacts,
)


def run_profile_synth_smoke(
    *,
    repo_root: Path,
    benchmark_root: Path | None = None,
    proof_dir: Path | None = None,
) -> dict[str, object]:
    payload = synthesize_profile_proposals(repo_root=repo_root, benchmark_root=benchmark_root)
    if proof_dir is not None:
        proof_dir.mkdir(parents=True, exist_ok=True)
        run_manifest = {
            "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            "packet_id": "TP-RTE-BENCH-PROFILE-SYNTH-001",
            "feedback_loop_exists_in_reviewable_form": True,
            "synthesis_inputs": payload["synthesis_input_refs"],
            "proposal_count": len(payload["proposals"]),
            "routing_diff_count": len(payload["routing_diffs"]),
            "blocked_lane_count": len(payload["blocked_lanes"]),
        }
        (proof_dir / "RUN_MANIFEST.json").write_text(stable_json_dumps(run_manifest) + "\n", encoding="utf-8")
        write_profile_synthesis_artifacts(proof_dir, payload)
        if payload["proposals"]:
            (proof_dir / "sample_profile_proposal.json").write_text(
                stable_json_dumps(payload["proposals"][0]) + "\n",
                encoding="utf-8",
            )
        if payload["routing_diffs"]:
            (proof_dir / "sample_routing_diff_proposal.json").write_text(
                stable_json_dumps(payload["routing_diffs"][0]) + "\n",
                encoding="utf-8",
            )
        if payload["review_packets"]:
            (proof_dir / "sample_review_packet.json").write_text(
                stable_json_dumps(payload["review_packets"][0]) + "\n",
                encoding="utf-8",
            )
        (proof_dir / "sample_blocked_lanes.json").write_text(
            stable_json_dumps(payload["blocked_lanes"]) + "\n",
            encoding="utf-8",
        )
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Profile synthesis smoke for review-first benchmark proposals.")
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[4])
    parser.add_argument("--benchmark-root", type=Path, default=None)
    parser.add_argument("--proof-dir", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = run_profile_synth_smoke(repo_root=args.repo_root.resolve(), benchmark_root=args.benchmark_root, proof_dir=args.proof_dir)
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
