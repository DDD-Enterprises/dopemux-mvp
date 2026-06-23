import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class OperationalizationEngine:
    """Manages supervised production operations and sign-offs."""

    def __init__(self, ops_path: Path):
        self.ops_path = ops_path
        self.ops_path.mkdir(parents=True, exist_ok=True)
        self.signoff_file = self.ops_path / "OPERATOR_SIGNOFF_LOG.jsonl"
        self.case_log = self.ops_path / "SUPERVISED_CASE_LOG.jsonl"

    def log_signoff(
        self,
        pr_id: str,
        run_id: str,
        action: str,
        rationale: str,
        operator: str = "human_integrator",
    ):
        """Record a formal operator sign-off for a high-risk action."""
        entry = {
            "timestamp": time.time(),
            "pr_id": pr_id,
            "run_id": run_id,
            "action": action,
            "operator": operator,
            "rationale": rationale,
            "status": "APPROVED",
        }
        with open(self.signoff_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def log_case_usage(self, pr_id: str, run_id: str, mode: str, outcome: str):
        """Record the start and outcome of a supervised arbitration case."""
        entry = {
            "timestamp": time.time(),
            "pr_id": pr_id,
            "run_id": run_id,
            "operational_mode": mode,
            "outcome": outcome,
        }
        with open(self.case_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def check_authorization(self, action: str, mode: str) -> bool:
        """Enforce the Allowed Actions Matrix."""
        # Hardcoded constraints for v0.1.0 GO_SUPERVISED_ONLY posture
        if mode == "ADVISORY":
            return action in [
                "EVIDENCE_PACK",
                "ARBITRATION",
                "CONSENSUS",
                "DEFER_PACKET",
            ]

        if mode == "LIVE_SAFE":
            # These require sign-off (checked externally, but gated here)
            return action in [
                "PATCH_PROPOSAL",
                "VERIFICATION",
                "METADATA_HYGIENE",
                "REPLY_COMPOSITION",
            ]

        return False


class FlightDeckOpsEngine:
    """Specialized engine for flight deck operational logging and safety."""

    def __init__(self, ops_path: Path):
        self.ops_path = ops_path
        self.ops_path.mkdir(parents=True, exist_ok=True)
        self.case_log = self.ops_path / "FLIGHT_DECK_CASE_LOG.jsonl"
        self.signoff_log = self.ops_path / "OPERATOR_SIGNOFF_LOG.jsonl"
        self.safety_log = self.ops_path / "ONGOING_AUTO_APPLY_SAFETY.jsonl"

    def log_case(self, pr_id: str, run_id: str, status: str, strategy: str):
        entry = {
            "timestamp": time.time(),
            "pr_id": pr_id,
            "run_id": run_id,
            "status": status,
            "strategy": strategy,
        }
        with open(self.case_log, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_signoff(self, pr_id: str, run_id: str, action: str, rationale: str):
        entry = {
            "timestamp": time.time(),
            "pr_id": pr_id,
            "run_id": run_id,
            "action": action,
            "rationale": rationale,
        }
        with open(self.signoff_log, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def log_auto_apply(self, pr_id: str, file: str, risk: str, status: str):
        entry = {
            "timestamp": time.time(),
            "pr_id": pr_id,
            "file": file,
            "risk": risk,
            "status": status,
        }
        with open(self.safety_log, "a") as f:
            f.write(json.dumps(entry) + "\n")
