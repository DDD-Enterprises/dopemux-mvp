"""
Prioritization Context Helper - Enhancement E4

Queries ConPort for active tasks to help user decide if new untracked work
is truly urgent or if they should finish existing tasks first. Provides
context on current commitments to reduce false-starts.

Part of F001 Enhancement E4: Prioritization Context Helper
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class PriorityContextBuilder:
    """
    Build prioritization context from active ConPort tasks.

    ADHD benefit: Decision support for "Is this new work urgent?"
    Shows current commitments to prevent overcommitment. Encourages
    finishing existing tasks before starting new work.
    """

    def __init__(self, workspace_id: str):
        """
        Initialize priority context builder.

        Args:
            workspace_id: Workspace ID for ConPort queries
        """
        self.workspace_id = workspace_id

    async def get_priority_context(
        self,
        conport_client=None
    ) -> Dict:
        """
        Get prioritization context from active tasks.

        Queries ConPort for IN_PROGRESS and TODO tasks to show
        current commitments.

        Args:
            conport_client: Optional ConPort MCP client

        Returns:
            {
                "has_active_tasks": bool,
                "in_progress_count": int,
                "todo_count": int,
                "blocked_count": int,
                "total_active": int,
                "in_progress_tasks": [
                    {
                        "description": str,
                        "status": str,
                        "created_at": str,
                        "linked_decision": str | None
                    }
                ],
                "urgent_recommendation": str,
                "overcommitment_risk": "low" | "medium" | "high"
            }
        """
        try:
            if not conport_client:
                logger.warning("No ConPort client - returning empty context")
                return self._empty_context()

            # Query active progress entries
            active_tasks = await self._query_active_tasks(conport_client)

            # Categorize by status
            in_progress = [t for t in active_tasks if t.get("status") == "IN_PROGRESS"]
            todo = [t for t in active_tasks if t.get("status") == "TODO"]
            blocked = [t for t in active_tasks if t.get("status") == "BLOCKED"]

            # Calculate overcommitment risk
            overcommitment_risk = self._assess_overcommitment_risk(
                len(in_progress),
                len(todo),
                len(blocked)
            )

            # Generate urgency recommendation
            urgent_recommendation = self._generate_urgency_recommendation(
                len(in_progress),
                len(todo),
                overcommitment_risk
            )

            # Format task summaries
            in_progress_summaries = [
                {
                    "description": t.get("description", "Unknown task"),
                    "status": t.get("status"),
                    "created_at": t.get("created_at"),
                    "linked_decision": t.get("linked_decision_id")
                }
                for t in in_progress[:5]  # Top 5 only (ADHD limit)
            ]

            result = {
                "has_active_tasks": len(active_tasks) > 0,
                "in_progress_count": len(in_progress),
                "todo_count": len(todo),
                "blocked_count": len(blocked),
                "total_active": len(active_tasks),
                "in_progress_tasks": in_progress_summaries,
                "urgent_recommendation": urgent_recommendation,
                "overcommitment_risk": overcommitment_risk
            }

            if len(in_progress) > 0:
                logger.info(
                    f"📋 Priority context: {len(in_progress)} in-progress, "
                    f"{len(todo)} TODO (risk: {overcommitment_risk})"
                )

            return result

        except Exception as e:
            logger.error(f"Failed to get priority context: {e}")
            return self._empty_context()

    async def _query_active_tasks(self, conport_client) -> List[Dict]:
        """Query active tasks from ConPort progress_entry."""
        try:
            # Query ConPort progress entries
            # Status filter: IN_PROGRESS, TODO, BLOCKED (not DONE)
            result = await conport_client.get_progress(
                workspace_id=self.workspace_id
                # TODO: Add status filter if ConPort API supports it
                # status_filter=["IN_PROGRESS", "TODO", "BLOCKED"]
            )

            # Filter to active statuses
            if isinstance(result, list):
                tasks = result
            elif isinstance(result, dict) and "items" in result:
                tasks = result["items"]
            else:
                logger.warning(f"Unexpected ConPort progress response: {type(result)}")
                return []

            # Filter to active tasks only
            active_statuses = {"IN_PROGRESS", "TODO", "BLOCKED"}
            active_tasks = [
                t for t in tasks
                if t.get("status") in active_statuses
            ]

            return active_tasks

        except Exception as e:
            logger.error(f"Failed to query active tasks: {e}")
            return []

    def _assess_overcommitment_risk(
        self,
        in_progress_count: int,
        todo_count: int,
        blocked_count: int
    ) -> str:
        """
        Assess overcommitment risk based on task counts.

        ADHD research shows 1-2 active tasks is optimal.
        3+ tasks = high context-switching overhead.

        Returns:
            "low" | "medium" | "high"
        """
        # ADHD-optimized thresholds
        total_active = in_progress_count + todo_count

        if in_progress_count == 0:
            return "low"  # No active work - safe to start
        elif in_progress_count <= 2 and total_active <= 5:
            return "low"  # Within ADHD capacity
        elif in_progress_count <= 3 and total_active <= 10:
            return "medium"  # Approaching overload
        else:
            return "high"  # Definitely overcommitted

    def _generate_urgency_recommendation(
        self,
        in_progress_count: int,
        todo_count: int,
        overcommitment_risk: str
    ) -> str:
        """
        Generate recommendation for new work urgency.

        Returns human-readable guidance.
        """
        if in_progress_count == 0:
            return "No active work - safe to start new work"

        if overcommitment_risk == "high":
            return "⚠️ Already overcommitted - finish something first unless truly urgent"

        if overcommitment_risk == "medium":
            return "⚠️ Several tasks active - is this new work more important?"

        # Low risk
        if in_progress_count == 1:
            return "1 task in progress - consider finishing it first"
        else:
            return f"{in_progress_count} tasks in progress - prioritize carefully"

    def _empty_context(self) -> Dict:
        """Return empty context structure."""
        return {
            "has_active_tasks": False,
            "in_progress_count": 0,
            "todo_count": 0,
            "blocked_count": 0,
            "total_active": 0,
            "in_progress_tasks": [],
            "urgent_recommendation": "No active tasks found",
            "overcommitment_risk": "low"
        }

    def format_priority_message(self, context: Dict) -> str:
        """
        Format prioritization context message.

        ADHD-optimized: Clear priorities, decision support, gentle nudging.

        Args:
            context: Result from get_priority_context

        Returns:
            Formatted message string
        """
        if not context["has_active_tasks"]:
            return "✨ No active tasks - safe to start new work"

        lines = ["📋 CURRENT COMMITMENTS"]
        lines.append("─" * 45)
        lines.append("")

        # Summary counts
        in_progress = context["in_progress_count"]
        todo = context["todo_count"]
        blocked = context["blocked_count"]

        lines.append(f"Active tasks: {context['total_active']}")
        lines.append(f"  ▶️  In Progress: {in_progress}")
        lines.append(f"  📝 TODO: {todo}")
        if blocked > 0:
            lines.append(f"  🚧 Blocked: {blocked}")
        lines.append("")

        # Overcommitment warning
        risk = context["overcommitment_risk"]
        if risk == "high":
            lines.append("🔴 OVERCOMMITMENT RISK: HIGH")
            lines.append("   You're juggling too much already!")
        elif risk == "medium":
            lines.append("🟡 OVERCOMMITMENT RISK: MEDIUM")
            lines.append("   Approaching cognitive capacity")
        else:
            lines.append("🟢 Manageable workload")

        lines.append("")

        # Show in-progress tasks
        if context["in_progress_tasks"]:
            lines.append("Currently working on:")
            for task in context["in_progress_tasks"]:
                desc = task["description"]
                # Truncate long descriptions
                if len(desc) > 60:
                    desc = desc[:57] + "..."
                lines.append(f"  • {desc}")
            lines.append("")

        # Recommendation
        lines.append("💡 " + context["urgent_recommendation"])
        lines.append("")
        lines.append("   Ask yourself: Is this new work truly urgent?")
        lines.append("   Or should you finish existing tasks first?")

        return "\n".join(lines)
