"""
Context Switch Frequency Pattern Detector

Detects excessive workspace switching that degrades productivity,
suggesting focus mode or task batching.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List

from .base_pattern import BasePattern, PatternInsight


class ContextSwitchFrequencyPattern(BasePattern):
    """
    Detects excessive context switching from workspace events.

    Triggers when:
    - Workspace switches exceed healthy threshold (>10/hour)
    - Threshold: 10+ switches within 60 minutes

    Generates:
    - Focus mode recommendation
    - Task batching suggestions
    - Context switch cost analysis
    """

    def get_pattern_name(self) -> str:
        return "context_switch_frequency"

    def get_default_threshold(self) -> int:
        return 10  # 10+ switches per hour

    def detect(self, events: List[Dict[str, Any]]) -> List[PatternInsight]:
        """
        Detect excessive context switching from events.

        Args:
            events: List of events (looking for workspace.switched events)

        Returns:
            List of insights for detected patterns
        """
        insights = []

        # Collect workspace switch events
        switch_events = []

        for event in events:
            if event.get("type") == "workspace.switched":
                data = event.get("data", {})
                switch_events.append({
                    "from_workspace": data.get("from_workspace"),
                    "to_workspace": data.get("to_workspace"),
                    "timestamp": event.get("timestamp"),
                    "source": event.get("source", "desktop-commander")
                })

        if len(switch_events) < self.threshold:
            return insights  # Not enough switches to analyze

        # Calculate switch frequency (switches per hour)
        if len(switch_events) >= 2:
            try:
                first_time = datetime.fromisoformat(switch_events[0]["timestamp"].replace('Z', '+00:00'))
                last_time = datetime.fromisoformat(switch_events[-1]["timestamp"].replace('Z', '+00:00'))

                duration_hours = (last_time - first_time).total_seconds() / 3600

                if duration_hours > 0:
                    switches_per_hour = len(switch_events) / duration_hours

                    if switches_per_hour >= 10:
                        # Pattern detected!
                        self.record_detection()

                        # Calculate context switch cost (ADHD: 15-25 min recovery per switch)
                        avg_recovery_minutes = 20  # Conservative ADHD estimate
                        total_recovery_minutes = len(switch_events) * avg_recovery_minutes
                        productivity_loss_percent = min(
                            (total_recovery_minutes / (duration_hours * 60)) * 100,
                            80  # Cap at 80%
                        )

                        # Identify most frequently switched workspaces
                        workspace_counts = defaultdict(int)
                        for switch in switch_events:
                            workspace_counts[switch["to_workspace"]] += 1

                        top_workspaces = sorted(
                            workspace_counts.items(),
                            key=lambda x: x[1],
                            reverse=True
                        )[:5]

                        # Determine severity
                        if switches_per_hour >= 20:
                            severity = "critical"
                        elif switches_per_hour >= 15:
                            severity = "high"
                        else:
                            severity = "medium"

                        insight = PatternInsight(
                            pattern_name=self.get_pattern_name(),
                            severity=severity,
                            summary=f"Excessive context switching detected: {switches_per_hour:.1f} switches/hour ({len(switch_events)} switches)",
                            details=(
                                f"Detected {len(switch_events)} workspace switches "
                                f"over {duration_hours:.1f} hours ({switches_per_hour:.1f} switches/hour)\n\n"
                                f"**ADHD Impact**:\n"
                                f"- Estimated recovery time: {total_recovery_minutes:.0f} minutes total\n"
                                f"- Productivity loss: ~{productivity_loss_percent:.0f}%\n"
                                f"- Each switch costs 15-25 minutes of recovery time\n\n"
                                f"**Most Switched Workspaces**:\n"
                                + "\n".join(f"- {ws}: {count} times" for ws, count in top_workspaces) + "\n\n"
                                f"This indicates fragmented focus and high context-switching overhead."
                            ),
                            event_count=len(switch_events),
                            first_occurrence=switch_events[0]["timestamp"],
                            last_occurrence=switch_events[-1]["timestamp"],
                            affected_resources=[ws for ws, _ in top_workspaces],
                            recommended_actions=[
                                "Enable focus mode (disable notifications for 25-minute blocks)",
                                "Batch related tasks within same workspace",
                                "Schedule workspace-specific focus sessions",
                                "Use task lists to reduce reactive switching",
                                f"Target: <6 switches/hour (current: {switches_per_hour:.1f}/hour)"
                            ],
                            metadata={
                                "switches_per_hour": switches_per_hour,
                                "total_switches": len(switch_events),
                                "duration_hours": duration_hours,
                                "estimated_recovery_minutes": total_recovery_minutes,
                                "productivity_loss_percent": productivity_loss_percent,
                                "top_workspaces": dict(top_workspaces)
                            }
                        )

                        insights.append(insight)

            except Exception as e:
                # Skip malformed timestamps
                pass

                logger.error(f"Error: {e}")
        return insights

    def _detect_overload_patterns(
        self,
        events: List[Dict[str, Any]]
    ) -> List[PatternInsight]:
        """Detect frequent cognitive overload events"""
        # This is handled by ADHDStatePattern, skip here to avoid duplication
        return []
