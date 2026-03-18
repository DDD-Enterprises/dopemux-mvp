from typing import Dict, Any, List, Optional
from .schema import PRState


class ScoringEngine:
    """Calculates priority scores for PRs to determine enqueue order."""

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self.weights = weights or {
            "urgency": 10.0,
            "age_bonus": 0.5, # points per day
            "ci_cost_negative": -1.0, # points per minute of expected CI
            "risk_negative": -5.0, # points per high-risk label
            "hotfix_boost": 50.0
        }

    def calculate_score(self, pr_state: PRState) -> float:
        """Calculate total score for a PR."""
        score = 0.0
        
        # 1. Hotfix boost
        if any(l.lower() in ["hotfix", "emergency", "security"] for l in pr_state.labels):
            score += self.weights.get("hotfix_boost", 0.0)
            
        # 2. Age Bonus (mocked based on updatedAt for now)
        # In real impl, would parse updatedAt and calc days
        score += self.weights.get("age_bonus", 0.0) * 1.0 # Placeholder
        
        # 3. Risk (based on labels or diffstat)
        if pr_state.mergeable is False:
             score += self.weights.get("risk_negative", 0.0)
             
        # 4. Urgency Label
        if "urgency:high" in pr_state.labels:
            score += self.weights.get("urgency", 0.0)
            
        return score

    def rank_prs(self, pr_states: List[PRState]) -> List[PRState]:
        """Return PRs sorted by score descending."""
        return sorted(pr_states, key=self.calculate_score, reverse=True)
