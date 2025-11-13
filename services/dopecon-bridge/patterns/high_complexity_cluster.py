"""
High Complexity Cluster Pattern Detector

Detects when multiple high-complexity code events occur in the same directory,
suggesting a refactoring opportunity.
"""

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List
from pathlib import Path

from .base_pattern import BasePattern, PatternInsight


class HighComplexityClusterPattern(BasePattern):
    """
    Detects clusters of high-complexity code in the same directory.

    Triggers when:
    - Multiple files in same directory have complexity > 0.6
    - Threshold: 3+ files within event window

    Generates:
    - Refactoring recommendation for directory
    - Lists all high-complexity files
    - Suggests architectural review
    """

    def get_pattern_name(self) -> str:
        return "high_complexity_cluster"

    def get_default_threshold(self) -> int:
        return 3  # 3+ high-complexity files in same directory

    def detect(self, events: List[Dict[str, Any]]) -> List[PatternInsight]:
        """
        Detect high-complexity clusters from events.

        Args:
            events: List of events (looking for code.complexity.high)

        Returns:
            List of insights for detected clusters
        """
        insights = []

        # Group complexity events by directory
        directory_complexity = defaultdict(list)

        for event in events:
            if event.get("type") == "code.complexity.high":
                data = event.get("data", {})
                file_path = data.get("file")
                complexity = data.get("complexity", 0)

                if file_path and complexity > 0.6:
                    directory = str(Path(file_path).parent)
                    directory_complexity[directory].append({
                        "file": file_path,
                        "complexity": complexity,
                        "timestamp": event.get("timestamp")
                    })

        # Check each directory for clusters
        for directory, files in directory_complexity.items():
            if len(files) >= self.threshold:
                # Pattern detected!
                self.record_detection()

                # Calculate average complexity
                avg_complexity = sum(f["complexity"] for f in files) / len(files)

                # Sort by complexity (highest first)
                files_sorted = sorted(files, key=lambda x: x["complexity"], reverse=True)

                # Determine severity based on average complexity and file count
                if avg_complexity > 0.8 and len(files) >= 5:
                    severity = "critical"
                elif avg_complexity > 0.7 or len(files) >= 4:
                    severity = "high"
                else:
                    severity = "medium"

                insight = PatternInsight(
                    pattern_name=self.get_pattern_name(),
                    severity=severity,
                    summary=f"High complexity cluster detected in {Path(directory).name}/ ({len(files)} files, avg: {avg_complexity:.2f})",
                    details=(
                        f"Detected {len(files)} files with high complexity (>0.6) "
                        f"in directory: {directory}\n\n"
                        f"Average complexity: {avg_complexity:.2f}\n"
                        f"This suggests the directory may benefit from refactoring "
                        f"to reduce cognitive load and improve maintainability."
                    ),
                    event_count=len(files),
                    first_occurrence=files_sorted[-1]["timestamp"],
                    last_occurrence=files_sorted[0]["timestamp"],
                    affected_resources=[f["file"] for f in files_sorted],
                    recommended_actions=[
                        f"Review {directory} for refactoring opportunities",
                        "Consider extracting common logic into helper functions",
                        "Break down complex functions into smaller, focused units",
                        "Add documentation for high-complexity areas",
                        f"Schedule focused time for refactoring (complexity: {avg_complexity:.2f})"
                    ],
                    metadata={
                        "directory": directory,
                        "file_count": len(files),
                        "average_complexity": avg_complexity,
                        "highest_complexity": files_sorted[0]["complexity"],
                        "files_by_complexity": [
                            {"file": f["file"], "complexity": f["complexity"]}
                            for f in files_sorted
                        ]
                    }
                )

                insights.append(insight)

        return insights
