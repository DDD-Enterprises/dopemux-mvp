"""
ADHD State Patterns Detector

Detects recurring cognitive load spikes or attention state patterns,
suggesting schedule adjustments or workflow optimizations.
"""

from collections import defaultdict
from datetime import datetime, time
from typing import Any, Dict, List

from .base_pattern import BasePattern, PatternInsight


class ADHDStatePattern(BasePattern):
    """
    Detects ADHD state patterns and cognitive load cycles.

    Triggers when:
    - Cognitive load spikes occur at specific times of day
    - Attention state patterns repeat across days
    - Threshold: 3+ occurrences of same pattern

    Generates:
    - Schedule optimization recommendations
    - Identifies problematic time windows
    - Suggests workflow adjustments
    """

    def get_pattern_name(self) -> str:
        return "adhd_state_patterns"

    def get_default_threshold(self) -> int:
        return 3  # 3+ occurrences of same pattern

    def detect(self, events: List[Dict[str, Any]]) -> List[PatternInsight]:
        """
        Detect ADHD state patterns from events.

        Args:
            events: List of events (looking for cognitive.state.changed, adhd.overload.detected)

        Returns:
            List of insights for detected patterns
        """
        insights = []

        # Collect ADHD state events
        cognitive_events = []
        overload_events = []

        for event in events:
            event_type = event.get("type", "")
            data = event.get("data", {})

            if event_type == "cognitive.state.changed":
                cognitive_events.append({
                    "attention_state": data.get("attention_state"),
                    "energy_level": data.get("energy_level"),
                    "cognitive_load": data.get("cognitive_load", 0),
                    "timestamp": event.get("timestamp")
                })

            elif event_type == "adhd.overload.detected":
                overload_events.append({
                    "cognitive_load": data.get("cognitive_load", 0),
                    "timestamp": event.get("timestamp"),
                    "trigger": data.get("trigger", "unknown")
                })

        # Pattern 1: Cognitive load spikes at specific times
        time_based_insights = self._detect_time_based_patterns(cognitive_events)
        insights.extend(time_based_insights)

        # Pattern 2: Frequent overload events
        overload_insights = self._detect_overload_patterns(overload_events)
        insights.extend(overload_insights)

        return insights

    def _detect_time_based_patterns(
        self,
        events: List[Dict[str, Any]]
    ) -> List[PatternInsight]:
        """Detect time-of-day cognitive load patterns"""
        insights = []

        # Group by hour of day
        hour_loads = defaultdict(list)

        for event in events:
            timestamp_str = event.get("timestamp", "")
            cognitive_load = event.get("cognitive_load", 0)

            try:
                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                hour = dt.hour
                hour_loads[hour].append(cognitive_load)
            except Exception as e:
                continue

                logger.error(f"Error: {e}")
        # Find hours with consistently high cognitive load
        high_load_hours = []

        for hour, loads in hour_loads.items():
            if len(loads) >= self.threshold:
                avg_load = sum(loads) / len(loads)
                if avg_load > 0.7:  # High cognitive load threshold
                    high_load_hours.append({
                        "hour": hour,
                        "avg_load": avg_load,
                        "occurrences": len(loads)
                    })

        if high_load_hours:
            # Sort by hour
            high_load_hours.sort(key=lambda x: x["hour"])

            self.record_detection()

            # Format time ranges
            time_ranges = [
                f"{h['hour']:02d}:00-{h['hour']:02d}:59 (avg load: {h['avg_load']:.2f})"
                for h in high_load_hours
            ]

            insight = PatternInsight(
                pattern_name=self.get_pattern_name(),
                severity="medium",
                summary=f"Recurring cognitive load spikes detected at {len(high_load_hours)} time windows",
                details=(
                    f"Detected recurring high cognitive load (>0.7) at specific times:\n\n"
                    + "\n".join(f"- {tr}" for tr in time_ranges) + "\n\n"
                    f"This suggests scheduling adjustments could improve productivity:\n"
                    f"- Avoid complex tasks during high-load windows\n"
                    f"- Schedule breaks before high-load periods\n"
                    f"- Move demanding work to lower-load times"
                ),
                event_count=sum(h["occurrences"] for h in high_load_hours),
                first_occurrence=events[0]["timestamp"],
                last_occurrence=events[-1]["timestamp"],
                affected_resources=time_ranges,
                recommended_actions=[
                    "Review task scheduling for high-load time windows",
                    "Schedule breaks before cognitive load spikes",
                    "Move complex tasks to optimal energy windows",
                    "Consider external factors (meetings, notifications)",
                    "Track improvements after schedule adjustments"
                ],
                metadata={
                    "high_load_hours": high_load_hours,
                    "pattern_type": "time_based_cognitive_load"
                }
            )

            insights.append(insight)

        return insights

    def _detect_overload_patterns(
        self,
        events: List[Dict[str, Any]]
    ) -> List[PatternInsight]:
        """Detect frequent cognitive overload events"""
        insights = []

        if len(events) >= self.threshold:
            # Pattern detected - frequent overload!
            self.record_detection()

            # Group by trigger
            triggers = defaultdict(int)
            for event in events:
                trigger = event.get("trigger", "unknown")
                triggers[trigger] += 1

            # Find most common trigger
            most_common_trigger = max(triggers.items(), key=lambda x: x[1])[0]

            severity = "high" if len(events) >= 6 else "medium"

            insight = PatternInsight(
                pattern_name=self.get_pattern_name(),
                severity=severity,
                summary=f"Frequent cognitive overload detected ({len(events)} events)",
                details=(
                    f"Detected {len(events)} cognitive overload events.\n\n"
                    f"Most common trigger: {most_common_trigger} "
                    f"({triggers[most_common_trigger]} occurrences)\n\n"
                    f"This indicates:\n"
                    f"- Workload may be too high\n"
                    f"- Tasks may be too complex\n"
                    f"- Need more frequent breaks\n"
                    f"- Better task chunking required"
                ),
                event_count=len(events),
                first_occurrence=events[0]["timestamp"],
                last_occurrence=events[-1]["timestamp"],
                affected_resources=[most_common_trigger],
                recommended_actions=[
                    "Reduce concurrent task complexity",
                    "Implement mandatory break enforcement",
                    "Review task complexity estimation",
                    "Consider breaking large tasks into smaller chunks",
                    "Enable ADHD Engine focus mode"
                ],
                metadata={
                    "overload_count": len(events),
                    "triggers": dict(triggers),
                    "most_common_trigger": most_common_trigger,
                    "pattern_type": "frequent_overload"
                }
            )

            insights.append(insight)

        return insights
