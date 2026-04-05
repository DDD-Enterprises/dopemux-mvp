import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .arbitration_engine import EvidencePackager
from .schema import PRMergeReport, PRState


class ShadowTrialHarness:
    """Orchestrates the arbitration lane shadow trial over real queued cases."""

    def __init__(self, manager: "QueueManager", packager: EvidencePackager):
        self.manager = manager
        self.packager = packager
        self.shadow_path = Path("proof/pr_merge/arbitration/shadow")
        self.shadow_path.mkdir(parents=True, exist_ok=True)

    def build_case_index(self, pr_numbers: List[str]) -> List[Dict[str, Any]]:
        """Index and bucket PRs for the shadow trial."""
        index = []
        for num in pr_numbers:
            print(f"🧐 Indexing PR {num} for shadow trial...")
            try:
                # Fetch minimal state to evaluate trigger
                state = self.manager._fetch_detailed_state(num)
                # Mock a report for trigger check
                mock_report = PRMergeReport(
                    run_id="index_probe",
                    pr_id=num,
                    initial_state=state,
                    status="blocked",
                )

                triggered, reason = self.packager.check_trigger(mock_report)

                bucket = "SHADOW_READY"
                if not triggered:
                    bucket = "NOT_ELIGIBLE"
                elif not state.merge_base_sha or state.merge_base_sha == "UNKNOWN":
                    bucket = "NEEDS_EVIDENCE_REPAIR"

                index.append(
                    {
                        "pr_id": num,
                        "title": state.title,
                        "bucket": bucket,
                        "trigger_reason": reason,
                        "conflict_class": (
                            state.conflict_class
                            if hasattr(state, "conflict_class")
                            else "UNKNOWN"
                        ),
                    }
                )
            except Exception as e:
                index.append({"pr_id": num, "bucket": "NOT_ELIGIBLE", "error": str(e)})

        (self.shadow_path / "SHADOW_CASE_INDEX.json").write_text(
            json.dumps(index, indent=2)
        )
        return index

    def run_shadow_batch(self, index: List[Dict[str, Any]], run_id: str):
        """Execute the full arbitration lane in advisory shadow mode."""
        results = []
        ready_cases = [c for c in index if c["bucket"] == "SHADOW_READY"]

        print(f"🚀 Starting shadow batch for {len(ready_cases)} cases...")

        for case in ready_cases:
            pr_id = case["pr_id"]
            # Advisory-only run: manager.process_pr already performs full lane in dry-run/advisory
            # if we don't call enqueuing mutations.
            report = self.manager.process_pr(pr_id, run_id)

            results.append(
                {
                    "pr_id": pr_id,
                    "status": report.status,
                    "confidence": (
                        report.consensus_decision.confidence
                        if report.consensus_decision
                        else "N/A"
                    ),
                    "defer_to_human": (
                        report.consensus_decision.defer_to_human
                        if report.consensus_decision
                        else True
                    ),
                    "autonomy_gate": (
                        report.autonomy_report.decision
                        if report.autonomy_report
                        else "NO_AUTONOMOUS_PROGRESS"
                    ),
                }
            )

        (self.shadow_path / "SHADOW_RUN_REPORT.json").write_text(
            json.dumps(results, indent=2)
        )
        return results
