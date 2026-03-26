import json
from pathlib import Path
from typing import Optional

from .arbitration_runtime import ArbitrationLLMClient
from .schema import (
    AnalyzerReport,
    ArbiterReport,
    ArbitrationEvidenceBundle,
    ArbitrationRoleTrace,
    ChallengeReport,
    RuntimeFailure,
)


class ArbitrationRoleEngine:
    """Orchestrates sequential, role-separated arbitration using the LLM Runtime."""

    def __init__(self, client: Optional[ArbitrationLLMClient] = None):
        self.client = client or ArbitrationLLMClient()

    def run_arbitration(
        self, run_id: str, bundle: ArbitrationEvidenceBundle
    ) -> ArbitrationRoleTrace:
        """Execute the Analyzer -> Challenger -> Arbiter sequence via Runtime."""

        # 1. Analyzer Phase
        res = self.client.run_role("analyzer", bundle.__dict__)
        if isinstance(res, RuntimeFailure):
            return self._fail_closed(run_id, res)
        analyzer_report = AnalyzerReport(**res["data"])

        # 2. Challenger Phase
        res = self.client.run_role(
            "challenger", bundle.__dict__, prior_reports=[analyzer_report]
        )
        if isinstance(res, RuntimeFailure):
            return self._fail_closed(run_id, res)
        challenge_report = ChallengeReport(**res["data"])

        # 3. Arbiter Phase
        res = self.client.run_role(
            "arbiter",
            bundle.__dict__,
            prior_reports=[analyzer_report, challenge_report],
        )
        if isinstance(res, RuntimeFailure):
            return self._fail_closed(run_id, res)
        arbiter_report = ArbiterReport(**res["data"])

        return ArbitrationRoleTrace(
            run_id=run_id,
            analyzer=analyzer_report,
            challenger=challenge_report,
            arbiter=arbiter_report,
        )

    def _fail_closed(
        self, run_id: str, failure: RuntimeFailure
    ) -> ArbitrationRoleTrace:
        """Produce a fail-closed trace that forces human deferral."""
        # Create a stub arbiter report that defers
        stub_arbiter = ArbiterReport(
            case_id=f"FAIL_{failure.role}",
            analyzer_ref="N/A",
            challenge_ref="N/A",
            defer_to_human=True,
            why_rejected=f"Runtime Failure ({failure.failure_class}): {failure.error_message}",
            confidence="INSUFFICIENT",
        )
        return ArbitrationRoleTrace(run_id=run_id, arbiter=stub_arbiter)

    def emit_reports(self, trace: ArbitrationRoleTrace, out_dir: Path):
        """Emit role-specific artifacts."""
        if trace.analyzer:
            (out_dir / "ANALYZER_REPORT.json").write_text(
                json.dumps(trace.analyzer.__dict__, indent=2, default=str)
            )
        if trace.challenger:
            (out_dir / "CHALLENGE_REPORT.json").write_text(
                json.dumps(trace.challenger.__dict__, indent=2, default=str)
            )
        if trace.arbiter:
            (out_dir / "ARBITER_REPORT.json").write_text(
                json.dumps(trace.arbiter.__dict__, indent=2, default=str)
            )

        # Role Confidence Summary
        confidence_summary = {
            "analyzer": trace.analyzer.confidence if trace.analyzer else "N/A",
            "challenger": trace.challenger.confidence if trace.challenger else "N/A",
            "arbiter": trace.arbiter.confidence if trace.arbiter else "N/A",
        }
        (out_dir / "ROLE_CONFIDENCE_SUMMARY.json").write_text(
            json.dumps(confidence_summary, indent=2)
        )

        # Defer Decision
        defer = {
            "defer_to_human": trace.arbiter.defer_to_human if trace.arbiter else True,
            "reason": (
                trace.arbiter.why_rejected
                if trace.arbiter
                else "Arbitration failed to complete."
            ),
        }
        (out_dir / "ROLE_DEFER_DECISIONS.json").write_text(json.dumps(defer, indent=2))
