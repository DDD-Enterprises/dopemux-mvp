import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .schema import PRMergeReport, PRState


class LiveTrialHarness:
    """Manages supervised live trial execution and feedback capture."""

    def __init__(self, manager: "QueueManager"):
        self.manager = manager
        self.live_path = Path("proof/pr_merge/arbitration/live")
        self.live_path.mkdir(parents=True, exist_ok=True)

    def build_live_index(
        self, shadow_shortlist: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Map shadow candidates to live trial assignments."""
        index = []
        for i, case in enumerate(shadow_shortlist):
            # Assign modes based on blast radius logic
            mode = "LIVE_ADVISORY"
            if i == 0:  # First one is always safest
                mode = "LIVE_DEFER_ONLY"

            index.append(
                {
                    "pr_id": case["pr_id"],
                    "trial_mode": mode,
                    "operator_owner": "human_integrator",
                    "status": "PENDING",
                }
            )

        (self.live_path / "LIVE_TRIAL_CASE_INDEX.json").write_text(
            json.dumps(index, indent=2)
        )
        return index

    def record_feedback(
        self, pr_id: str, run_id: str, action: str, note: str, was_useful: bool
    ):
        """Capture structured operator feedback for a live trial run."""
        feedback = {
            "timestamp": time.time(),
            "pr_id": pr_id,
            "run_id": run_id,
            "operator_action": action,  # GUIDANCE_ACCEPTED, GUIDANCE_REJECTED, etc.
            "was_useful": was_useful,
            "operator_note": note,
        }

        # Append to feedback ledger
        ledger = self.live_path / "OPERATOR_ACCEPTANCE_REPORT.jsonl"
        with open(ledger, "a", encoding="utf-8") as f:
            f.write(json.dumps(feedback) + "\n")

    def emit_incident(
        self, pr_id: str, run_id: str, incident_type: str, severity: str, desc: str
    ):
        """Log a live trial incident."""
        incident = {
            "timestamp": time.time(),
            "pr_id": pr_id,
            "run_id": run_id,
            "type": incident_type,
            "severity": severity,
            "description": desc,
        }

        # Append to incident ledger
        ledger = self.live_path / "LIVE_TRIAL_INCIDENTS.jsonl"
        with open(ledger, "a", encoding="utf-8") as f:
            f.write(json.dumps(incident) + "\n")
