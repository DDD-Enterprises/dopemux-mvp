import json
from typing import List, Dict, Any, Optional
from .schema import PRMergeReport, RemediationFlowTrace, RemediationStageResult


class RemediationOrchestrator:
    """Orchestrates the end-to-end staged remediation workflow."""

    def __init__(self, manager: 'QueueManager'):
        self.manager = manager

    def run_flow(self, pr_id: str, run_id: str) -> PRMergeReport:
        """Execute the staged remediation flow."""
        trace = RemediationFlowTrace(run_id=run_id)
        
        # Stage 1: Collect State
        # (This is currently inside process_pr, we'll refactor slightly to expose stages)
        
        # We'll use the existing process_pr as the core, 
        # but we'll augment it with trace logging.
        report = self.manager.process_pr(pr_id, run_id)
        
        # Convert internal state to stages for the trace
        # (Refactoring QueueManager to use this orchestrator would be ideal)
        
        stages = []
        
        # Feedback Stage
        stages.append(RemediationStageResult(
            stage_name="INTAKE",
            status="SUCCESS" if report.feedback_items else "SKIPPED",
            actions_taken=[f"Ingested {len(report.feedback_items)} feedback items"]
        ))
        
        # Triage Stage
        stages.append(RemediationStageResult(
            stage_name="TRIAGE",
            status="SUCCESS" if report.triage_results else "SKIPPED",
            actions_taken=[f"Classified {len(report.triage_results)} checks"]
        ))
        
        # Verification Stage
        stages.append(RemediationStageResult(
            stage_name="VERIFICATION",
            status="SUCCESS" if report.verification_results else "SKIPPED",
            actions_taken=[f"Executed {len(report.verification_results)} commands"]
        ))
        
        # Stop Condition Detection
        stop_reason = None
        if report.status == "blocked":
            stop_reason = report.status_reason
            
        final_trace = RemediationFlowTrace(
            run_id=run_id,
            stages=stages,
            final_readiness=report.status == "merge_ready",
            final_decision="ENQUEUE" if report.status == "merge_ready" else "ESCALATE"
        )
        
        # Inject trace into report
        # We need a way to create a new report or update the existing one
        # since they are frozen. We'll add a helper to schema later if needed.
        return report # For now, return the report from manager
