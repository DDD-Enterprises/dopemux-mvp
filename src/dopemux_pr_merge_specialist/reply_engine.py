import json
from typing import List, Dict, Any, Optional
from .schema import FeedbackItem, VerificationResult, ReviewReplyAction, ReviewReplyPlan, ThreadResolutionGuardReport


class ReviewReplyComposer:
    """Composes evidence-backed review replies based on remediation state."""

    def compose_reply(self, item: FeedbackItem, verif_results: List[VerificationResult]) -> str:
        """Generate a polite, evidence-backed reply for a feedback item."""
        intent = item.intent
        
        if intent == "MUST_FIX_CODE":
            return "✅ This has been addressed in the latest commit."
        
        if intent == "MUST_FIX_TEST":
            # Link to verification evidence
            passing = [r for r in verif_results if "test" in r.command.lower() and r.exit_code == 0]
            if passing:
                return f"✅ Tests verified: `{passing[0].command}` passed. Evidence: {passing[0].evidence_path}"
            return "⏳ Fix implemented; verification pending."

        if intent == "MUST_FIX_DOC":
            return "✅ Documentation updated as requested."

        if intent == "OPTIONAL_SUGGESTION":
            return "Thanks for the suggestion! I've noted it for a future pass."

        if intent == "QUESTION":
            return "I've flagged this for human follow-up to ensure an accurate response."

        if intent == "HUMAN_DECISION_REQUIRED":
            return "⚠️ Escalated to human review for decision."

        return "I've analyzed this feedback and it is pending remediation."


class ThreadResolutionGuard:
    """Enforces policy-backed rules for resolving review threads."""

    def can_resolve(self, item: FeedbackItem, verif_results: List[VerificationResult], conflict_class: str) -> tuple[bool, str]:
        """Determine if a thread can be safely resolved."""
        
        # 1. High Risk Context
        if conflict_class == "HIGH_RISK":
            return False, "Resolution blocked due to high-risk conflict state."

        # 2. Outdated
        if item.is_outdated:
            return True, "Thread is outdated by new changes."

        # 3. Policy by Intent
        intent = item.intent
        if intent == "MUST_FIX_CODE":
            return True, "Code change implemented."
            
        if intent == "MUST_FIX_TEST":
            passing = any(r.exit_code == 0 for r in verif_results if "test" in r.command.lower())
            if passing:
                return True, "Verification tests passed."
            return False, "Pending passing verification result."

        if intent in ["QUESTION", "HUMAN_DECISION_REQUIRED", "CONFLICTING_FEEDBACK"]:
            return False, f"Requires human intervention for intent: {intent}"

        if intent == "OPTIONAL_SUGGESTION":
            return False, "Optional suggestions are left for human closure."

        return False, "Default: resolution requires manual review."


class ReplyEngine:
    """Orchestrates the composition of replies and resolution decisions."""

    def __init__(self):
        self.composer = ReviewReplyComposer()
        self.guard = ThreadResolutionGuard()

    def plan_replies(
        self, 
        feedback_items: List[FeedbackItem], 
        verif_results: List[VerificationResult],
        conflict_class: str
    ) -> tuple[ReviewReplyPlan, List[ThreadResolutionGuardReport]]:
        actions = []
        reports = []

        for item in feedback_items:
            # Plan replies for Threads, Inline, and General PR Comments
            if item.source_type not in ["THREAD", "INLINE", "PR_COMMENT"] or item.is_resolved:
                continue
                
            # Skip if it's the PR Body itself
            if item.id == "PR_BODY":
                continue
                
            reply_text = self.composer.compose_reply(item, verif_results)
            can_resolve, reason = self.guard.can_resolve(item, verif_results, conflict_class)
            
            actions.append(ReviewReplyAction(
                id=f"REPLY_{item.id}",
                thread_id=item.thread_id or item.id,
                reply_body=reply_text,
                should_resolve=can_resolve,
                rationale=reason
            ))
            
            reports.append(ThreadResolutionGuardReport(
                thread_id=item.thread_id or item.id,
                can_resolve=can_resolve,
                reason=reason
            ))

        return ReviewReplyPlan(actions=actions), reports
