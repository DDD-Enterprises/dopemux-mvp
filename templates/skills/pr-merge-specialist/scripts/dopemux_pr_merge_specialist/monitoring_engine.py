import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class OperationsMonitor:
    """Aggregates operational logs to monitor health and scale-gate compliance."""

    def __init__(self, ops_path: Path):
        self.ops_path = ops_path
        self.case_log = self.ops_path / "SUPERVISED_CASE_LOG.jsonl"
        self.signoff_log = self.ops_path / "OPERATOR_SIGNOFF_LOG.jsonl"

    def get_health_snapshot(self, window_size: int = 10) -> Dict[str, Any]:
        """Generate a health report over the last N runs."""
        cases = self._load_recent(self.case_log, window_size)
        signoffs = self._load_recent(
            self.signoff_log, window_size * 2
        )  # More buffer for signoffs

        if not cases:
            return {"status": "INSUFFICIENT_DATA", "count": 0}

        total = len(cases)
        # Check compliance: every case should have a matching signoff if it was a mutation
        # (Simplified: check if signoff count matches case count for now)
        compliance = len(signoffs) / total if total > 0 else 0.0

        successes = len(
            [c for c in cases if c.get("outcome") in ["merged", "merge_ready"]]
        )

        return {
            "window_size": window_size,
            "total_runs": total,
            "signoff_compliance": round(compliance, 2),
            "acceptance_rate": round(successes / total, 2),
            "status": "HEALTHY" if compliance >= 1.0 else "DRIFT_DETECTED",
        }

    def evaluate_scale_gate(self, health: Dict[str, Any]) -> Dict[str, Any]:
        """Apply scale-gate policy based on health metrics."""
        if health.get("status") == "INSUFFICIENT_DATA":
            return {
                "decision": "CONTINUE_SUPERVISED",
                "reason": "Insufficient data for evaluation.",
            }

        decision = "CONTINUE_SUPERVISED"
        reason = "All health metrics within normal range."

        if health["signoff_compliance"] < 1.0:
            decision = "PAUSE_AND_REVIEW"
            reason = f"Signoff compliance ({health['signoff_compliance']}) below mandatory threshold."

        return {"decision": decision, "reason": reason, "timestamp": time.time()}

    def _load_recent(self, path: Path, count: int) -> List[Dict[str, Any]]:
        if not path.exists():
            return []
        lines = path.read_text().splitlines()
        return [json.loads(l) for l in lines[-count:]]
