"""
Abandoned Work Revival Suggester - Enhancement E3

Analyzes top abandoned projects and suggests which ones might be worth
reviving. Uses recency, relevance to current work, and branch context
to make intelligent suggestions.

Part of F001 Enhancement E3: Abandoned Work Revival
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class RevivalSuggester:
    """
    Suggest revival of abandoned work when relevant.

    ADHD benefit: Prevents duplicating abandoned work. Surfaces
    forgotten projects that align with current goals. Gentle nudge
    to finish vs. start new.
    """

    def __init__(self, workspace_id: str):
        """
        Initialize revival suggester.

        Args:
            workspace_id: Workspace ID for ConPort queries
        """
        self.workspace_id = workspace_id

    def suggest_revivals(
        self,
        top_abandoned: List[Dict],
        current_work: Dict,
        max_suggestions: int = 3
    ) -> Dict:
        """
        Suggest abandoned work to revive based on relevance to current work.

        Args:
            top_abandoned: Top abandoned projects from FalseStartsAggregator
            current_work: Current git detection result
            max_suggestions: Maximum suggestions to return

        Returns:
            {
                "has_suggestions": bool,
                "suggestion_count": int,
                "suggestions": [
                    {
                        "work_name": str,
                        "relevance_score": float (0.0-1.0),
                        "revival_reason": str,
                        "days_idle": int,
                        "file_overlap": int,
                        "files": List[str],
                        "branch": str | None,
                        "action": "resume" | "review" | "learn_from"
                    }
                ]
            }
        """
        try:
            if not top_abandoned:
                return self._no_suggestions()

            current_files = set(current_work.get("files", []))
            current_dirs = set(str(Path(f).parent) for f in current_files)

            # Score each abandoned work for revival relevance
            scored_revivals = []
            for abandoned in top_abandoned:
                score_result = self._calculate_revival_score(
                    abandoned,
                    current_files,
                    current_dirs
                )

                if score_result["relevance_score"] >= 0.3:  # Threshold for suggestion
                    scored_revivals.append(score_result)

            # Sort by relevance score (highest first)
            scored_revivals.sort(key=lambda x: x["relevance_score"], reverse=True)

            # Take top N suggestions
            suggestions = scored_revivals[:max_suggestions]

            if suggestions:
                logger.info(
                    f"🔄 {len(suggestions)} revival suggestions for current work "
                    f"(relevance: {suggestions[0]['relevance_score']:.0%})"
                )

            return {
                "has_suggestions": len(suggestions) > 0,
                "suggestion_count": len(suggestions),
                "suggestions": suggestions
            }

        except Exception as e:
            logger.error(f"Failed to generate revival suggestions: {e}")
            return self._no_suggestions()

    def _calculate_revival_score(
        self,
        abandoned: Dict,
        current_files: set,
        current_dirs: set
    ) -> Dict:
        """
        Calculate relevance score for reviving abandoned work.

        Scoring factors:
        - File overlap (same files touched)
        - Directory overlap (same areas of codebase)
        - Recency (more recent = more relevant)
        - Branch name similarity
        """
        abandoned_files = set(abandoned.get("files", []))
        abandoned_dirs = set(str(Path(f).parent) for f in abandoned_files)

        # Factor 1: File overlap (0-40 points)
        file_overlap = len(current_files & abandoned_files)
        file_overlap_score = min(file_overlap / max(len(current_files), 1) * 0.4, 0.4)

        # Factor 2: Directory overlap (0-30 points)
        dir_overlap = len(current_dirs & abandoned_dirs)
        dir_overlap_score = min(dir_overlap / max(len(current_dirs), 1) * 0.3, 0.3)

        # Factor 3: Recency (0-20 points) - more recent = more relevant
        days_idle = abandoned.get("days_idle", 999)
        if days_idle <= 7:
            recency_score = 0.2
        elif days_idle <= 30:
            recency_score = 0.15
        elif days_idle <= 90:
            recency_score = 0.1
        else:
            recency_score = 0.05

        # Factor 4: Branch name similarity (0-10 points)
        # Simple heuristic: shared words in branch names
        branch_score = 0.0
        # TODO: Implement branch name similarity if current work has branch context

        # Total score
        relevance_score = file_overlap_score + dir_overlap_score + recency_score + branch_score

        # Determine suggested action based on score
        if relevance_score >= 0.7:
            action = "resume"  # Highly relevant - resume directly
        elif relevance_score >= 0.5:
            action = "review"  # Moderately relevant - review first
        else:
            action = "learn_from"  # Lower relevance - might have useful patterns

        # Format revival reason
        revival_reason = self._format_revival_reason(
            file_overlap,
            dir_overlap,
            days_idle
        )

        return {
            "work_name": abandoned.get("name", "Unknown work"),
            "relevance_score": round(relevance_score, 2),
            "revival_reason": revival_reason,
            "days_idle": days_idle,
            "file_overlap": file_overlap,
            "files": list(abandoned_files),
            "branch": abandoned.get("branch"),
            "action": action
        }

    def _format_revival_reason(
        self,
        file_overlap: int,
        dir_overlap: int,
        days_idle: int
    ) -> str:
        """Format human-readable revival reason."""
        reasons = []

        if file_overlap > 0:
            reasons.append(f"{file_overlap} overlapping file{'s' if file_overlap != 1 else ''}")

        if dir_overlap > 0:
            reasons.append(f"same {dir_overlap} director{'ies' if dir_overlap != 1 else 'y'}")

        if days_idle <= 7:
            reasons.append("recent work")
        elif days_idle <= 30:
            reasons.append("from this month")

        return ", ".join(reasons) if reasons else "related to current work"

    def _no_suggestions(self) -> Dict:
        """Return result with no suggestions."""
        return {
            "has_suggestions": False,
            "suggestion_count": 0,
            "suggestions": []
        }

    def format_revival_message(self, suggestions: List[Dict]) -> str:
        """
        Format revival suggestions message.

        ADHD-optimized: Progressive disclosure, clear actions, gentle nudging.

        Args:
            suggestions: Revival suggestions from suggest_revivals

        Returns:
            Formatted message string
        """
        if not suggestions:
            return ""

        lines = ["🔄 ABANDONED WORK REVIVAL"]
        lines.append("─" * 45)
        lines.append("")
        lines.append(f"Found {len(suggestions)} abandoned project{'s' if len(suggestions) != 1 else ''}")
        lines.append("that might be worth reviving:")
        lines.append("")

        for i, suggestion in enumerate(suggestions, 1):
            name = suggestion["work_name"]
            relevance = suggestion["relevance_score"]
            reason = suggestion["revival_reason"]
            action = suggestion["action"]
            days = suggestion["days_idle"]

            # Action emoji
            action_emoji = {
                "resume": "▶️",
                "review": "👀",
                "learn_from": "📚"
            }.get(action, "💡")

            lines.append(f"{i}. {action_emoji} {name}")
            lines.append(f"   Relevance: {relevance:.0%} ({reason})")
            lines.append(f"   Idle: {days} days")

            # Action suggestion
            if action == "resume":
                lines.append("   → Highly relevant - consider resuming this instead?")
            elif action == "review":
                lines.append("   → Review first - might save work")
            else:
                lines.append("   → Lower priority - check for useful patterns")

            if i < len(suggestions):
                lines.append("")

        lines.append("")
        lines.append("💡 Finishing existing work > starting new work")

        return "\n".join(lines)
