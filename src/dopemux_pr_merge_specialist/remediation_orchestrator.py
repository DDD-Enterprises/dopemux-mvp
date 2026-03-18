import json
from typing import Any, Dict, List, Optional

from .schema import PRMergeReport, RemediationFlowTrace, RemediationStageResult


class RemediationOrchestrator:
    """Orchestrates the end-to-end staged remediation workflow."""

    def __init__(self, manager: Any):
        self.manager = manager

    def run_flow(self, pr_id: str, run_id: str) -> PRMergeReport:
        """Execute the staged remediation flow."""
        trace = RemediationFlowTrace(run_id=run_id)

        # 1. Fetch current PR state
        # In this project, GitHubClient is the manager in many contexts.
        # We need to adapt to the fact that it doesn't have process_pr.
        # If the manager is a GitHubClient, we'll use plan_builder/classification helpers.
        
        from .github_api import GitHubClient
        if isinstance(self.manager, GitHubClient):
            from .plan_builder import build_plan_result
            from .classification import build_pr_state
            from .github_api import thread_counters
            from .policy import load_effective_policy
            from pathlib import Path
            
            client = self.manager
            policy = client.policy
            raw = client.fetch_pr(int(pr_id))
            threads = client.fetch_review_threads(int(pr_id))
            unresolved_total, active_threads, outdated_threads = thread_counters(threads)
            pr_state_obj = build_pr_state(raw, unresolved_total, active_threads, outdated_threads)
            check_payload = client.query_checks(int(pr_id))
            
            from .schema import ValidationReport, ValidationStatus
            validation = ValidationReport(
                status=ValidationStatus.NOT_EXECUTED,
                required_for_merge_ready=bool(policy.get("validation", {}).get("require_local_validation_for_merge_ready", True)),
                steps=[],
                attempts=0,
                remediation_applied=False,
            )
            
            result = build_plan_result(active_run_id=run_id, pr=pr_state_obj, threads=threads, check_payload=check_payload, validation_report=validation, policy=policy)
            
            # Map PRResult to PRMergeReport for compatibility with the Wizard's expectations
            from .schema import Blocker
            blockers = []
            for f in result.findings:
                if str(f.kind) == "blocker":
                    blockers.append(f.as_blocker())
            
            report = PRMergeReport(
                pr_id=pr_id,
                status="blocked" if blockers else "merge_ready",
                blockers=blockers,
                initial_state=pr_state_obj,
                telemetry={"lifecycle_state": result.lifecycle_state},
                remediation_flow_trace=trace
            )
            return report

        # Fallback to original logic if it's not a GitHubClient
        if hasattr(self.manager, "process_pr"):
            report = self.manager.process_pr(pr_id, run_id)
            return report
            
        raise AttributeError(f"Manager {type(self.manager)} does not support PR processing.")
