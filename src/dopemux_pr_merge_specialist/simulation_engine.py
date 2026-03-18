import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from .schema import PRMergeReport, PRState, SimulationResult, PolicySnapshot
from .queue_manager import QueueManager


class SimulationEngine:
    """Replays historical proof bundles under alternate policy configurations."""

    def __init__(self, manager: QueueManager):
        self.manager = manager

    def simulate_run(self, proof_bundle_path: Path, candidate_policy: Dict[str, Any]) -> SimulationResult:
        """Re-run logic against a historical snapshot."""
        
        # 1. Load Baseline
        snapshot_path = proof_bundle_path / "QUEUE_STATE_SNAPSHOT.json"
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot not found at {snapshot_path}")
            
        baseline_data = json.loads(snapshot_path.read_text())
        baseline_status = baseline_data.get("status", "UNKNOWN")
        
        # 2. Apply Candidate Policy (Mocked injection for now)
        # In real impl, we'd override manager.scoring_engine.weights etc.
        original_weights = self.manager.scoring_engine.weights.copy()
        if "scoring_weights" in candidate_policy:
            self.manager.scoring_engine.weights.update(candidate_policy["scoring_weights"])
            
        # 3. Recompute (Mocked bypass of GraphQL via direct process_pr injection or internal method)
        # For simulation, we'll implement a 'dry_run_from_state' in QueueManager
        
        # 4. Generate Result (Placeholder for logic)
        simulated_status = baseline_status # No-op for first pass
        
        # Reset policy
        self.manager.scoring_engine.weights = original_weights
        
        return SimulationResult(
            original_run_id=baseline_data.get("run_id", "UNKNOWN"),
            baseline_status=baseline_status,
            simulated_status=simulated_status,
            status_changed=baseline_status != simulated_status,
            score_delta=0.0
        )

    def emit_summary(self, results: List[SimulationResult], out_path: Path):
        """Emit advisory simulation artifacts."""
        summary = {
            "total_simulations": len(results),
            "decision_changes": len([r for r in results if r.status_changed]),
            "results": [r.__dict__ for r in results]
        }
        out_path.write_text(json.dumps(summary, indent=2))
