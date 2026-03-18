import re
from typing import List, Dict, Any, Optional
from .schema import CITriageCategory


class TriageRule:
    def __init__(
        self,
        name: str,
        category: CITriageCategory,
        retryable: bool,
        reason: str,
        check_name_pattern: Optional[str] = None,
        conclusion: Optional[str] = None,
    ):
        self.name = name
        self.category = category
        self.retryable = retryable
        self.reason = reason
        self.check_name_pattern = check_name_pattern
        self.conclusion = conclusion

    def matches(self, check_run: Dict[str, Any]) -> bool:
        """Check if this rule matches a given check run dictionary."""
        if self.conclusion and check_run.get("conclusion") != self.conclusion:
            return False
        
        if self.check_name_pattern:
            if not re.search(self.check_name_pattern, check_run.get("name", "")):
                return False
                
        return True


class TriageEngine:
    """Classifies CI failures into actionable categories."""

    def __init__(self, rules: Optional[List[TriageRule]] = None):
        # Default rules if none provided
        self.rules = rules or [
            TriageRule(
                name="Infra Timeout",
                category="INFRA",
                retryable=True,
                reason="Job timed out, likely infrastructure congestion.",
                conclusion="TIMED_OUT"
            ),
            TriageRule(
                name="Action Required / Governance",
                category="GOVERNANCE",
                retryable=False,
                reason="Manual intervention or governance check required.",
                conclusion="ACTION_REQUIRED"
            ),
            TriageRule(
                name="Known Flaky Pattern",
                category="FLAKE",
                retryable=True,
                reason="Matches known flaky test pattern.",
                check_name_pattern=r"(e2e|integration|selenium)"
            ),
            TriageRule(
                name="Generic Code Failure",
                category="CODE",
                retryable=False,
                reason="Standard check failure, likely a bug or linter error.",
                conclusion="FAILURE"
            )
        ]

    def triage(self, check_runs: List[Dict[str, Any]]) -> Dict[str, CITriageCategory]:
        """Process a list of check runs and return a mapping of check name to category."""
        results = {}
        for run in check_runs:
            name = run.get("name", "unknown")
            conclusion = run.get("conclusion")
            
            if conclusion in ["SUCCESS", "NEUTRAL", "SKIPPED"]:
                continue
                
            matched = False
            for rule in self.rules:
                if rule.matches(run):
                    results[name] = rule.category
                    matched = True
                    break
            
            if not matched:
                results[name] = "UNKNOWN"
                
        return results

    def is_retryable(self, triage_results: Dict[str, CITriageCategory]) -> bool:
        """Determine if the overall PR state is retryable based on triage results."""
        if not triage_results:
            return False
            
        # If any failure is CODE or GOVERNANCE, it's NOT retryable automatically
        non_retryable = {"CODE", "GOVERNANCE", "UNKNOWN"}
        for cat in triage_results.values():
            if cat in non_retryable:
                return False
        
        return True
