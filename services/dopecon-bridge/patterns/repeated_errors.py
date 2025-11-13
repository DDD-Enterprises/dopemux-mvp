"""
Repeated Errors Pattern Detector

Detects when the same error occurs multiple times across different agents,
suggesting a systemic issue.
"""

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List

from .base_pattern import BasePattern, PatternInsight


class RepeatedErrorPattern(BasePattern):
    """
    Detects repeated error patterns across agents.

    Triggers when:
    - Same error message/type occurs from multiple agents
    - Threshold: 3+ occurrences within event window

    Generates:
    - Systemic error investigation recommendation
    - Lists all agents experiencing error
    - Suggests root cause analysis
    """

    def get_pattern_name(self) -> str:
        return "repeated_errors"

    def get_default_threshold(self) -> int:
        return 3  # 3+ occurrences of same error

    def detect(self, events: List[Dict[str, Any]]) -> List[PatternInsight]:
        """
        Detect repeated error patterns from events.

        Args:
            events: List of events (looking for *.error, *.failed events)

        Returns:
            List of insights for detected patterns
        """
        insights = []

        # Group error events by error signature
        error_groups = defaultdict(list)

        for event in events:
            event_type = event.get("type", "")

            # Look for error-related events
            if "error" in event_type.lower() or "failed" in event_type.lower():
                data = event.get("data", {})
                error_message = data.get("error", data.get("message", ""))

                if error_message:
                    # Create error signature (normalize for grouping)
                    signature = self._normalize_error_message(error_message)

                    error_groups[signature].append({
                        "event_type": event_type,
                        "error_message": error_message,
                        "source": event.get("source", "unknown"),
                        "timestamp": event.get("timestamp"),
                        "data": data
                    })

        # Check each error group for patterns
        for signature, occurrences in error_groups.items():
            if len(occurrences) >= self.threshold:
                # Pattern detected!
                self.record_detection()

                # Get unique agents experiencing this error
                agents = list(set(occ["source"] for occ in occurrences))

                # Determine severity
                if len(occurrences) >= 10:
                    severity = "critical"
                elif len(occurrences) >= 6:
                    severity = "high"
                else:
                    severity = "medium"

                insight = PatternInsight(
                    pattern_name=self.get_pattern_name(),
                    severity=severity,
                    summary=f"Repeated error across {len(agents)} agents ({len(occurrences)} occurrences): {signature[:50]}...",
                    details=(
                        f"Detected repeated error pattern across multiple agents:\n\n"
                        f"Error: {signature}\n"
                        f"Occurrences: {len(occurrences)}\n"
                        f"Agents affected: {', '.join(agents)}\n\n"
                        f"This suggests a systemic issue that requires investigation. "
                        f"The error is impacting multiple parts of the system."
                    ),
                    event_count=len(occurrences),
                    first_occurrence=occurrences[0]["timestamp"],
                    last_occurrence=occurrences[-1]["timestamp"],
                    affected_resources=agents,
                    recommended_actions=[
                        "Investigate root cause of error",
                        f"Check logs from agents: {', '.join(agents)}",
                        "Review recent code changes that may have introduced issue",
                        "Add error handling or validation to prevent recurrence",
                        "Consider adding monitoring alert for this error pattern"
                    ],
                    metadata={
                        "error_signature": signature,
                        "occurrence_count": len(occurrences),
                        "agents_affected": agents,
                        "sample_errors": [
                            {
                                "source": occ["source"],
                                "message": occ["error_message"][:100],
                                "timestamp": occ["timestamp"]
                            }
                            for occ in occurrences[:5]  # First 5 examples
                        ]
                    }
                )

                insights.append(insight)

        return insights

    def _normalize_error_message(self, error: str) -> str:
        """
        Normalize error message for grouping.

        Removes variable parts (line numbers, IDs, timestamps) to create
        a stable error signature.

        Args:
            error: Raw error message

        Returns:
            Normalized error signature
        """
        import re

        # Remove line numbers (e.g., "line 123")
        normalized = re.sub(r'\bline\s+\d+\b', 'line N', error, flags=re.IGNORECASE)

        # Remove file paths (keep just filename)
        normalized = re.sub(r'/[^\s]+/([^\s/]+)', r'\1', normalized)

        # Remove timestamps
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}', 'TIMESTAMP', normalized)

        # Remove UUIDs
        normalized = re.sub(
            r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            'UUID',
            normalized,
            flags=re.IGNORECASE
        )

        # Remove numeric IDs
        normalized = re.sub(r'\bid[:\s=]+\d+\b', 'id N', normalized, flags=re.IGNORECASE)

        return normalized.strip()
