import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from .schema import (
    ArbitrationRoleTrace, 
    ConsensusDecision, 
    MergeExecutionPlan, 
    RequiredVerificationPlan, 
    AutonomyGateReport
)


class ConsensusAdjudicator:
    """Unifies arbitration roles into a governed consensus decision and execution plan."""

    def adjudicate(self, trace: ArbitrationRoleTrace) -> tuple[ConsensusDecision, MergeExecutionPlan, RequiredVerificationPlan, AutonomyGateReport]:
        """Process role trace and apply autonomy policy."""
        
        analyzer = trace.analyzer
        challenger = trace.challenger
        arbiter = trace.arbiter
        
        # 1. Decision Logic
        preferred = arbiter.preferred_candidate if arbiter else None
        defer = arbiter.defer_to_human if arbiter else True
        confidence = arbiter.confidence if arbiter else "LOW"
        
        decision = ConsensusDecision(
            case_id="CONSENSUS_001",
            preferred_candidate=preferred,
            merge_strategy="SYNTHESIZE_BOTH" if preferred else "HUMAN_DEFER",
            rationale=arbiter.why_preferred if preferred else arbiter.why_rejected,
            confidence=confidence,
            defer_to_human=defer,
            blocking_risks=challenger.hidden_risks if challenger else [],
            evidence_refs=arbiter.evidence_refs if arbiter else []
        )
        
        # 2. Autonomy Gate Logic
        autonomy_decision = "DEFER_TO_HUMAN"
        gate_reason = "Default defer for high-risk arbitration."
        
        if not defer and confidence == "HIGH":
            autonomy_decision = "PATCH_PLAN_ALLOWED_HUMAN_REVIEW_REQUIRED"
            gate_reason = "High confidence consensus reached; human must review the resulting patch."
        elif defer:
            autonomy_decision = "DEFER_TO_HUMAN"
            gate_reason = arbiter.why_rejected if arbiter else "Arbitration incomplete."
            
        gate_report = AutonomyGateReport(
            decision=autonomy_decision,
            reason=gate_reason,
            confidence_score=0.8 if confidence == "HIGH" else 0.5
        )
        
        # 3. Execution and Verification Planning
        plan = MergeExecutionPlan(
            strategy=decision.merge_strategy,
            ordered_steps=["Apply patches", "Run verification"],
            autonomy_level=autonomy_decision,
            human_review_required=True
        )
        
        verif = RequiredVerificationPlan(
            required_checks=["build", "lint"],
            targeted_tests=challenger.verification_gaps if challenger else []
        )
        
        return decision, plan, verif, gate_report

    def emit_artifacts(self, report: Any, out_dir: Path):
        """Emit consensus artifacts."""
        if report.consensus_decision:
            (out_dir / "CONSENSUS_DECISION.json").write_text(json.dumps(report.consensus_decision.__dict__, indent=2, default=str))
        if report.merge_execution_plan:
            (out_dir / "MERGE_EXECUTION_PLAN.json").write_text(json.dumps(report.merge_execution_plan.__dict__, indent=2, default=str))
        if report.verification_requirement:
            (out_dir / "REQUIRED_VERIFICATION_PLAN.json").write_text(json.dumps(report.verification_requirement.__dict__, indent=2, default=str))
        if report.autonomy_report:
            (out_dir / "AUTONOMY_GATE_REPORT.json").write_text(json.dumps(report.autonomy_report.__dict__, indent=2, default=str))
