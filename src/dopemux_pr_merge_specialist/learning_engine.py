import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import PRMergeReport


class LearningEngine:
    """Captures overrides and attributes outcomes for policy tuning."""

    def __init__(self, learning_path: Path):
        self.learning_path = learning_path
        self.learning_path.mkdir(parents=True, exist_ok=True)
        self.ledger_file = self.learning_path / "OVERRIDE_LEDGER.jsonl"

    def log_override(
        self,
        run_id: str,
        pr_id: str,
        action: str,
        recommendation: str,
        override: str,
        rationale: str,
    ):
        """Record an explicit operator override."""
        entry = {
            "timestamp": time.time(),
            "run_id": run_id,
            "pr_id": pr_id,
            "action": action,
            "engine_recommendation": recommendation,
            "operator_action": override,
            "rationale": rationale,
        }
        with open(self.ledger_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def attribute_outcome(
        self, report: PRMergeReport, actual_status: str
    ) -> Dict[str, Any]:
        """Compare engine decision with eventual outcome."""
        engine_ready = report.status in ["merged", "merge_ready"]
        actual_ready = actual_status in ["merged", "closed_success"]

        if engine_ready and actual_ready:
            classification = "ADVANCED_CORRECTLY"
        elif not engine_ready and not actual_ready:
            classification = "BLOCKED_CORRECTLY"
        elif not engine_ready and actual_ready:
            classification = "OVER_BLOCKED"
        elif engine_ready and not actual_ready:
            classification = "UNDER_BLOCKED"

        return {
            "pr_id": report.pr_id,
            "engine_status": report.status,
            "actual_outcome": actual_status,
            "classification": classification,
        }

    def generate_recommendations(
        self, outcomes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify patterns and suggest policy adjustments."""
        recommendations = []
        over_blocked = [o for o in outcomes if o["classification"] == "OVER_BLOCKED"]
        under_blocked = [o for o in outcomes if o["classification"] == "UNDER_BLOCKED"]

        if len(over_blocked) > 5:
            recommendations.append(
                {
                    "area": "READINESS_GATES",
                    "suggestion": "Relax resolution guards for non-critical intents.",
                    "confidence": "MEDIUM",
                    "evidence_count": len(over_blocked),
                }
            )

        if under_blocked:
            recommendations.append(
                {
                    "area": "SAFETY_POLICIES",
                    "suggestion": "Tighten conflict detection or triage rules immediately.",
                    "confidence": "HIGH",
                    "evidence_count": len(under_blocked),
                }
            )

        return recommendations
