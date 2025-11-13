"""
Base Pattern Class for Event Pattern Detection
All pattern detectors inherit from this base
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class PatternInsight:
    """
    Insight generated from pattern detection

    These insights are automatically logged to ConPort as decisions or patterns
    """
    pattern_name: str
    severity: str  # "low", "medium", "high", "critical"
    summary: str
    details: str
    event_count: int
    first_occurrence: str
    last_occurrence: str
    affected_resources: List[str]  # Files, agents, workspaces affected
    recommended_actions: List[str]
    metadata: Dict[str, Any]

    def to_conport_decision(self, workspace_id: str) -> Dict[str, Any]:
        """
        Convert insight to ConPort decision format

        Args:
            workspace_id: Workspace ID for ConPort

        Returns:
            Dictionary suitable for ConPort log_decision
        """
        return {
            "workspace_id": workspace_id,
            "summary": f"[Pattern: {self.pattern_name}] {self.summary}",
            "rationale": self.details,
            "implementation_details": "\n".join([
                f"**Event Count**: {self.event_count}",
                f"**First Occurrence**: {self.first_occurrence}",
                f"**Last Occurrence**: {self.last_occurrence}",
                f"**Severity**: {self.severity}",
                "",
                "**Affected Resources**:",
                *[f"- {resource}" for resource in self.affected_resources],
                "",
                "**Recommended Actions**:",
                *[f"- {action}" for action in self.recommended_actions],
            ]),
            "tags": [
                f"pattern-detected",
                f"pattern-{self.pattern_name}",
                f"severity-{self.severity}",
                "auto-generated"
            ]
        }


class BasePattern(ABC):
    """
    Base class for all pattern detectors

    Subclasses must implement:
    - detect(): Analyze events and return insights
    - get_pattern_name(): Return unique pattern name
    """

    def __init__(self, threshold: Optional[int] = None):
        """
        Initialize pattern detector

        Args:
            threshold: Optional threshold for pattern triggering
        """
        self.threshold = threshold or self.get_default_threshold()
        self.detections = 0
        self.last_detection: Optional[str] = None

    @abstractmethod
    def detect(self, events: List[Dict[str, Any]]) -> List[PatternInsight]:
        """
        Analyze events and detect patterns

        Args:
            events: List of event dictionaries with type, data, source, timestamp

        Returns:
            List of PatternInsight objects if pattern detected, empty list otherwise
        """
        pass

    @abstractmethod
    def get_pattern_name(self) -> str:
        """
        Return unique pattern name

        Returns:
            Pattern name (e.g., "high_complexity_cluster")
        """
        pass

    @abstractmethod
    def get_default_threshold(self) -> int:
        """
        Return default threshold for pattern triggering

        Returns:
            Default threshold value
        """
        pass

    def get_description(self) -> str:
        """
        Return human-readable pattern description

        Returns:
            Pattern description
        """
        return f"Pattern detector: {self.get_pattern_name()}"

    def record_detection(self):
        """Record that pattern was detected"""
        self.detections += 1
        self.last_detection = datetime.utcnow().isoformat()

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get pattern detection metrics

        Returns:
            Dictionary with detections count and last_detection timestamp
        """
        return {
            "pattern_name": self.get_pattern_name(),
            "detections": self.detections,
            "last_detection": self.last_detection,
            "threshold": self.threshold
        }
