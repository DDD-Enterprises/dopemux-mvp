"""
F6: Abandonment Tracking

Detects uncommitted work that's been idle for extended periods.
Uses time-based scoring to identify potentially abandoned work.

Key Features:
- Time-based abandonment scoring (7+ days = potentially abandoned)
- Severity classification (stale, likely, definitely abandoned)
- GUILT-FREE messaging (gentle nudges, not blame)
- Integration with F5 pattern learning (risky pattern detection)

Part of Phase 2 Analytics (F5-F8)
"""

from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AbandonmentTracker:
    """
    F6: Abandonment Tracking Engine

    Identifies uncommitted work that's been sitting idle for extended periods.
    Provides gentle ADHD-friendly reminders to finish or archive work.
    """

    def __init__(self, workspace_id: str):
        """
        Initialize abandonment tracker

        Args:
            workspace_id: Workspace ID for ConPort integration
        """
        self.workspace_id = workspace_id

        # Abandonment thresholds (from planning)
        self.min_days_idle = 7  # Consider abandoned after 7 days
        self.score_divisor = 14  # Score = days_idle / 14 (reaches 1.0 at 14 days)

        # Severity thresholds
        self.severity_thresholds = {
            "stale": (0.3, 0.5),  # 4-7 days idle
            "likely_abandoned": (0.5, 0.7),  # 7-10 days idle
            "definitely_abandoned": (0.7, float('inf'))  # 10+ days idle
        }

    def calculate_abandonment_score(self, git_detection: Dict) -> Dict:
        """
        Calculate abandonment score based on time idle

        Formula: score = days_idle / 14 (capped at 1.0)

        Args:
            git_detection: Git detection result with first_change_time

        Returns:
            {
                "score": float (0.0-1.0),
                "days_idle": int,
                "severity": str,
                "message": str (ADHD-friendly),
                "is_abandoned": bool (score >= 0.5)
            }
        """
        first_change_time = git_detection.get("first_change_time")

        # Handle missing first_change_time
        if not first_change_time:
            return {
                "score": 0.0,
                "days_idle": 0,
                "severity": "none",
                "message": "⚪ No time data available",
                "is_abandoned": False
            }

        # Calculate days idle
        now = datetime.now()
        time_idle = now - first_change_time
        days_idle = time_idle.days

        # Calculate score (capped at 1.0)
        score = min(days_idle / self.score_divisor, 1.0)

        # Classify severity
        severity = self.classify_severity(score)

        # Generate ADHD-friendly message
        message = self.generate_message(severity, days_idle)

        # Determine if truly abandoned (score >= 0.5 = 7+ days)
        is_abandoned = score >= 0.5

        return {
            "score": score,
            "days_idle": days_idle,
            "severity": severity,
            "message": message,
            "is_abandoned": is_abandoned,
            "first_change_time": first_change_time.isoformat()
        }

    def classify_severity(self, score: float) -> str:
        """
        Classify abandonment severity

        Thresholds:
        - 0.0-0.3: none (< 4 days, within normal workflow)
        - 0.3-0.5: stale (4-7 days, getting old but okay)
        - 0.5-0.7: likely_abandoned (7-10 days, probably forgot)
        - 0.7+: definitely_abandoned (10+ days, definitely forgotten)

        Args:
            score: Abandonment score (0.0-1.0)

        Returns:
            Severity classification string
        """
        if score < 0.3:
            return "none"
        elif score < 0.5:
            return "stale"
        elif score < 0.7:
            return "likely_abandoned"
        else:
            return "definitely_abandoned"

    def generate_message(self, severity: str, days_idle: int) -> str:
        """
        Generate ADHD-friendly message

        CRITICAL: Messages should be GUILT-FREE, gentle nudges not blame.
        Use emoji indicators and supportive language.

        Args:
            severity: Severity classification
            days_idle: Number of days idle

        Returns:
            Human-readable message with emoji indicator
        """
        if severity == "none":
            return f"⚪ Recent work ({days_idle} day{'s' if days_idle != 1 else ''} old)"

        elif severity == "stale":
            return f"🟡 Getting a bit stale ({days_idle} days old) - might want to wrap this up soon!"

        elif severity == "likely_abandoned":
            return f"🟠 From {days_idle} days ago - want to finish this or archive it?"

        else:  # definitely_abandoned
            return f"🔴 This has been sitting for {days_idle} days - time to decide: commit, archive, or delete?"

    def suggest_action(self, abandonment_data: Dict, git_detection: Dict) -> Dict:
        """
        Suggest action based on abandonment data

        Actions:
        - commit: Has meaningful changes, should be committed
        - archive: Experimental work, save for later (git stash)
        - delete: Throwaway work, safe to discard

        Args:
            abandonment_data: Result from calculate_abandonment_score
            git_detection: Git detection with file stats

        Returns:
            {
                "action": "commit"|"archive"|"delete",
                "rationale": str,
                "urgency": "low"|"medium"|"high"
            }
        """
        severity = abandonment_data["severity"]
        days_idle = abandonment_data["days_idle"]
        stats = git_detection.get("stats", {})
        file_count = len(git_detection.get("files", []))

        # Determine action based on severity and file count
        if severity == "definitely_abandoned":
            if file_count > 5:
                # Substantial work, likely worth committing
                return {
                    "action": "commit",
                    "rationale": f"{file_count} files changed - looks like real work worth saving",
                    "urgency": "high"
                }
            else:
                # Small changes, might be experimental
                return {
                    "action": "archive",
                    "rationale": f"Small change ({file_count} files), might be experimental - stash for later?",
                    "urgency": "medium"
                }

        elif severity == "likely_abandoned":
            if stats.get("new", 0) > 0:
                # New files created, likely intentional work
                return {
                    "action": "commit",
                    "rationale": f"{stats['new']} new file(s) created - probably want to keep this",
                    "urgency": "medium"
                }
            else:
                return {
                    "action": "archive",
                    "rationale": "Modifications only - could be experimental, consider stashing",
                    "urgency": "low"
                }

        else:  # stale
            return {
                "action": "commit",
                "rationale": "Still relatively fresh - finish up and commit",
                "urgency": "low"
            }

    def get_abandonment_summary(self, all_detections: List[Dict]) -> Dict:
        """
        Get summary of all abandoned work

        Args:
            all_detections: List of detection results with abandonment_data

        Returns:
            {
                "total_abandoned": int,
                "by_severity": {severity: count},
                "avg_days_idle": float,
                "oldest_work": {work_name, days_idle},
                "suggested_actions": {action: count}
            }
        """
        abandoned = [
            d for d in all_detections
            if d.get("abandonment_data", {}).get("is_abandoned")
        ]

        if not abandoned:
            return {
                "total_abandoned": 0,
                "by_severity": {},
                "avg_days_idle": 0.0,
                "oldest_work": None,
                "suggested_actions": {}
            }

        # Count by severity
        by_severity = {}
        for detection in abandoned:
            severity = detection["abandonment_data"]["severity"]
            by_severity[severity] = by_severity.get(severity, 0) + 1

        # Calculate average days idle
        total_days = sum(d["abandonment_data"]["days_idle"] for d in abandoned)
        avg_days_idle = total_days / len(abandoned)

        # Find oldest work
        oldest = max(abandoned, key=lambda d: d["abandonment_data"]["days_idle"])

        # Count suggested actions
        suggested_actions = {}
        for detection in abandoned:
            action_data = self.suggest_action(
                detection["abandonment_data"],
                detection["git_detection"]
            )
            action = action_data["action"]
            suggested_actions[action] = suggested_actions.get(action, 0) + 1

        return {
            "total_abandoned": len(abandoned),
            "by_severity": by_severity,
            "avg_days_idle": round(avg_days_idle, 1),
            "oldest_work": {
                "work_name": oldest.get("work_name"),
                "days_idle": oldest["abandonment_data"]["days_idle"]
            },
            "suggested_actions": suggested_actions
        }
