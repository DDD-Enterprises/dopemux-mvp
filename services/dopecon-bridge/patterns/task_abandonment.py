"""
Task Abandonment Pattern Detector

Detects tasks that were started but never progressed,
suggesting task complexity issues or motivation problems.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .base_pattern import BasePattern, PatternInsight


class TaskAbandonmentPattern(BasePattern):
    """
    Detects task abandonment from progress events.

    Triggers when:
    - Tasks marked IN_PROGRESS but no updates for >2 hours
    - Threshold: 3+ abandoned tasks

    Generates:
    - Task breakdown recommendations
    - Complexity analysis suggestions
    - Motivation/energy mismatch insights
    """

    def get_pattern_name(self) -> str:
        return "task_abandonment"

    def get_default_threshold(self) -> int:
        return 3  # 3+ abandoned tasks

    def detect(self, events: List[Dict[str, Any]]) -> List[PatternInsight]:
        """
        Detect task abandonment from events.

        Args:
            events: List of events (looking for task.progress.updated events)

        Returns:
            List of insights for detected patterns
        """
        insights = []

        # Track task status changes
        task_timeline = defaultdict(list)

        for event in events:
            event_type = event.get("type", "")

            if "progress" in event_type.lower() or "task" in event_type.lower():
                data = event.get("data", {})
                task_id = data.get("task_id", data.get("progress_id"))
                status = data.get("status", "")

                if task_id and status:
                    task_timeline[task_id].append({
                        "status": status.upper(),
                        "timestamp": event.get("timestamp"),
                        "description": data.get("description", ""),
                        "complexity": data.get("complexity"),
                        "energy_required": data.get("energy_required")
                    })

        # Identify abandoned tasks
        abandoned_tasks = []
        current_time = datetime.utcnow()

        for task_id, timeline in task_timeline.items():
            # Sort by timestamp
            timeline.sort(key=lambda x: x["timestamp"])

            # Check if task started but not completed
            statuses = [t["status"] for t in timeline]

            if "IN_PROGRESS" in statuses and "DONE" not in statuses and "COMPLETED" not in statuses:
                # Task started but not finished
                last_update = timeline[-1]

                try:
                    last_update_time = datetime.fromisoformat(
                        last_update["timestamp"].replace('Z', '+00:00')
                    )

                    # Check if abandoned (no updates for >2 hours)
                    hours_since_update = (current_time - last_update_time.replace(tzinfo=None)).total_seconds() / 3600

                    if hours_since_update >= 2:
                        abandoned_tasks.append({
                            "task_id": task_id,
                            "description": last_update["description"],
                            "hours_abandoned": hours_since_update,
                            "complexity": last_update.get("complexity"),
                            "energy_required": last_update.get("energy_required"),
                            "started_at": timeline[0]["timestamp"],
                            "last_update": last_update["timestamp"]
                        })

                except Exception as e:
                    # Skip malformed timestamps
                    continue

                    logger.error(f"Error: {e}")
        if len(abandoned_tasks) >= self.threshold:
            # Pattern detected!
            self.record_detection()

            # Sort by abandonment duration
            abandoned_tasks.sort(key=lambda x: x["hours_abandoned"], reverse=True)

            # Calculate average complexity (if available)
            complexities = [t["complexity"] for t in abandoned_tasks if t.get("complexity")]
            avg_complexity = sum(complexities) / len(complexities) if complexities else None

            # Determine severity
            if len(abandoned_tasks) >= 6:
                severity = "high"
            elif len(abandoned_tasks) >= 4:
                severity = "medium"
            else:
                severity = "low"

            # Build recommendations
            recommendations = [
                "Review abandoned tasks for complexity or clarity issues",
                "Break down complex tasks into smaller, manageable chunks"
            ]

            if avg_complexity and avg_complexity > 0.6:
                recommendations.append(
                    f"High average complexity ({avg_complexity:.2f}) - consider task decomposition"
                )

            recommendations.extend([
                "Match task energy requirements with current energy levels",
                "Consider if tasks align with current interests/motivation",
                "Use ADHD Engine recommendations for task selection"
            ])

            insight = PatternInsight(
                pattern_name=self.get_pattern_name(),
                severity=severity,
                summary=f"Task abandonment pattern: {len(abandoned_tasks)} tasks started but not progressed",
                details=(
                    f"Detected {len(abandoned_tasks)} tasks that were started (IN_PROGRESS) "
                    f"but have not been updated for 2+ hours.\n\n"
                    + (f"**Average Complexity**: {avg_complexity:.2f}\n\n" if avg_complexity else "")
                    + f"**Longest Abandoned**: {abandoned_tasks[0]['hours_abandoned']:.1f} hours\n\n"
                    f"This pattern suggests:\n"
                    f"- Tasks may be too complex or poorly defined\n"
                    f"- Energy/complexity mismatch\n"
                    f"- Lack of clear next steps\n"
                    f"- Motivation or interest misalignment"
                ),
                event_count=len(abandoned_tasks),
                first_occurrence=abandoned_tasks[-1]["started_at"],
                last_occurrence=abandoned_tasks[0]["last_update"],
                affected_resources=[t["description"][:60] for t in abandoned_tasks[:5]],
                recommended_actions=recommendations,
                metadata={
                    "abandoned_count": len(abandoned_tasks),
                    "average_complexity": avg_complexity,
                    "longest_abandoned_hours": abandoned_tasks[0]["hours_abandoned"],
                    "sample_tasks": [
                        {
                            "description": t["description"][:100],
                            "hours_abandoned": t["hours_abandoned"],
                            "complexity": t.get("complexity")
                        }
                        for t in abandoned_tasks[:5]
                    ]
                }
            )

            insights.append(insight)

        return insights
