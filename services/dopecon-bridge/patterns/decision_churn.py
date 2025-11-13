"""
Decision Churn Pattern Detector

Detects when multiple consensus/decision events occur on the same topic,
suggesting unclear requirements or unstable architecture.
"""

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from .base_pattern import BasePattern, PatternInsight


class DecisionChurnPattern(BasePattern):
    """
    Detects decision churn from frequent consensus events.

    Triggers when:
    - Multiple consensus/decision events on same topic
    - Threshold: 3+ decisions on similar topics within window

    Generates:
    - Requirements clarification recommendation
    - Lists all related decisions
    - Suggests architectural review or requirements refinement
    """

    def get_pattern_name(self) -> str:
        return "decision_churn"

    def get_default_threshold(self) -> int:
        return 3  # 3+ decisions on similar topics

    def detect(self, events: List[Dict[str, Any]]) -> List[PatternInsight]:
        """
        Detect decision churn from events.

        Args:
            events: List of events (looking for decision.* events)

        Returns:
            List of insights for detected churn
        """
        insights = []

        # Collect decision-related events
        decision_events = []

        for event in events:
            event_type = event.get("type", "")

            if "decision" in event_type.lower() or "consensus" in event_type.lower():
                data = event.get("data", {})
                summary = data.get("summary", data.get("decision", ""))

                if summary:
                    decision_events.append({
                        "summary": summary,
                        "event_type": event_type,
                        "source": event.get("source", "unknown"),
                        "timestamp": event.get("timestamp"),
                        "data": data
                    })

        # Group by topic similarity
        topic_groups = self._group_by_topic_similarity(decision_events)

        # Check each group for churn
        for topic_keywords, decisions in topic_groups.items():
            if len(decisions) >= self.threshold:
                # Pattern detected!
                self.record_detection()

                # Get unique sources
                sources = list(set(d["source"] for d in decisions))

                # Determine severity
                if len(decisions) >= 6:
                    severity = "high"
                elif len(decisions) >= 4:
                    severity = "medium"
                else:
                    severity = "low"

                insight = PatternInsight(
                    pattern_name=self.get_pattern_name(),
                    severity=severity,
                    summary=f"Decision churn detected: {len(decisions)} decisions on '{topic_keywords}'",
                    details=(
                        f"Detected {len(decisions)} decision/consensus events "
                        f"related to: {topic_keywords}\n\n"
                        f"This suggests one of the following:\n"
                        f"1. Requirements are unclear or changing frequently\n"
                        f"2. Architectural direction is unstable\n"
                        f"3. Multiple valid approaches exist (need clear choice)\n"
                        f"4. Team needs alignment on technical direction\n\n"
                        f"Agents involved: {', '.join(sources)}"
                    ),
                    event_count=len(decisions),
                    first_occurrence=decisions[0]["timestamp"],
                    last_occurrence=decisions[-1]["timestamp"],
                    affected_resources=[d["summary"][:80] for d in decisions[:5]],
                    recommended_actions=[
                        f"Schedule requirements review for: {topic_keywords}",
                        "Clarify architectural direction and document decision",
                        "Create ADR (Architecture Decision Record)",
                        "Align team on chosen approach",
                        "Consider if churn indicates need for spike/prototype"
                    ],
                    metadata={
                        "topic_keywords": topic_keywords,
                        "decision_count": len(decisions),
                        "agents_involved": sources,
                        "decisions": [
                            {
                                "summary": d["summary"][:100],
                                "source": d["source"],
                                "timestamp": d["timestamp"]
                            }
                            for d in decisions[:5]  # First 5 examples
                        ]
                    }
                )

                insights.append(insight)

        return insights

    def _group_by_topic_similarity(
        self,
        decisions: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group decisions by topic similarity using shared keywords.

        Items are grouped together if they share at least one significant keyword.
        Uses primary keyword (most frequent) as group key.

        Args:
            decisions: List of decision dictionaries

        Returns:
            Dictionary mapping topic keywords to decisions
        """
        # Build keyword index: keyword -> list of decision indices
        keyword_to_decisions = defaultdict(list)

        stop_words = {
            "the", "and", "for", "with", "from", "this", "that",
            "should", "will", "can", "use", "using", "add", "update", "to"
        }

        for idx, decision in enumerate(decisions):
            summary = decision["summary"].lower()

            # Extract significant keywords
            words = [
                w for w in summary.split()
                if len(w) > 3 and w not in stop_words
            ]

            # Index this decision under all its keywords
            for word in words:
                keyword_to_decisions[word].append(idx)

        # Find keyword with most decisions (primary topic)
        if not keyword_to_decisions:
            return {}

        primary_keyword = max(keyword_to_decisions.items(), key=lambda x: len(x[1]))[0]

        # Group all decisions that share the primary keyword
        topic_groups = {
            primary_keyword: [decisions[idx] for idx in keyword_to_decisions[primary_keyword]]
        }

        return topic_groups
