from __future__ import annotations

import math
from datetime import datetime
from typing import Any, Dict, List, Optional

from .schema import PullRequestState


class AdvancedQueueScorer:
    """
    Implements the Weighted Shortest Expected Merge Time (WSEMT) scoring model.
    
    Formula: Score = (Base_Priority + (Age_Factor)) / Expected_CI_Duration
    
    Higher score = Higher priority.
    """

    def __init__(self, policy: Optional[Dict[str, Any]] = None):
        self.policy = policy or {}
        config = self.policy.get("scoring", {})
        
        self.weights = {
            "hotfix": config.get("hotfix_weight", 100.0),
            "feature": config.get("feature_weight", 20.0),
            "chore": config.get("chore_weight", 5.0),
            "aging_multiplier": config.get("aging_multiplier", 0.1), # Points per minute
            "base_ci_minutes": config.get("base_ci_minutes", 10.0),
            "ci_per_file_factor": config.get("ci_per_file_factor", 0.5),
        }

    def calculate_wsemt_score(self, pr: PullRequestState) -> float:
        """Calculate the risk-adjusted WSEMT score."""
        
        # 1. Base Priority Weight
        base_priority = 10.0
        labels = [l.lower() for l in pr.labels]
        
        if any(kw in labels for kw in ["hotfix", "emergency", "security", "p0"]):
            base_priority += self.weights["hotfix"]
        elif any(kw in labels for kw in ["feature", "enhancement"]):
            base_priority += self.weights["feature"]
        elif any(kw in labels for kw in ["chore", "refactor", "docs"]):
            base_priority += self.weights["chore"]

        # 2. Queue Age Factor (Anti-starvation)
        # We use updated_at as a proxy for 'time in queue' if created_at is missing
        # Format is usually ISO 8601: 2026-03-17T22:45:46Z
        age_minutes = 0.0
        try:
            if pr.updated_at:
                # Simple parse, ignoring TZ for relative diff if same day
                ts = datetime.fromisoformat(pr.updated_at.replace("Z", "+00:00"))
                delta = datetime.now(ts.tzinfo) - ts
                age_minutes = max(0.0, delta.total_seconds() / 60.0)
        except Exception:
            pass
            
        age_contribution = age_minutes * self.weights["aging_multiplier"]

        # 3. Expected CI Duration (Denominator)
        # Heuristic: base time + penalty for number of files changed
        expected_duration = self.weights["base_ci_minutes"] + (pr.changed_files * self.weights["ci_per_file_factor"])
        
        # Ensure we don't divide by zero
        expected_duration = max(1.0, expected_duration)

        score = (base_priority + age_contribution) / expected_duration
        return score

    def rank_prs(self, prs: List[PullRequestState]) -> List[PullRequestState]:
        """Rank PRs by WSEMT score descending."""
        return sorted(prs, key=self.calculate_wsemt_score, reverse=True)
