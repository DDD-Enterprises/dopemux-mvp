"""
Lightweight metrics tracker for dope-context MCP usage.
Tracks search calls to measure LLM search behavior before/after enhancements.
"""

import json

import logging

logger = logging.getLogger(__name__)

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class SearchMetric:
    """Single search call metric."""
    timestamp: str
    tool_name: str  # search_code, docs_search, search_all
    query: str
    workspace: str
    top_k: int
    scenario: str  # classified scenario
    explicit_search: bool  # True if query contains "search", "find", etc.


class MetricsTracker:
    """Track dope-context search usage for benchmarking."""

    def __init__(self, metrics_file: Optional[str] = None):
        """
        Initialize metrics tracker.

        Args:
            metrics_file: Path to metrics JSON file (default: ~/.dope-context/metrics.json)
        """
        if metrics_file:
            self.metrics_file = Path(metrics_file)
        else:
            metrics_dir = Path.home() / ".dope-context"
            metrics_dir.mkdir(exist_ok=True)
            self.metrics_file = metrics_dir / "search_metrics.json"

    def classify_query(self, query: str) -> tuple[str, bool]:
        """
        Classify query into scenario and detect if explicit search.

        Returns:
            (scenario, is_explicit) tuple

        Scenarios:
            - understanding: Understanding existing code
            - making_changes: Before modifying code
            - debugging: Finding bugs or issues
            - review: Code review or pattern analysis
            - refactoring: Finding related code
            - feature_dev: Learning from existing features
            - questions: Answering code questions
            - impact_analysis: Finding dependencies
            - explicit_search: User said "find" or "search"
        """
        query_lower = query.lower()

        # Check if explicit search request
        explicit_keywords = [
            "find", "search", "locate", "look for", "show me",
            "get me", "where is", "which file"
        ]
        is_explicit = any(kw in query_lower for kw in explicit_keywords)

        # Classify scenario
        if is_explicit:
            return ("explicit_search", True)

        # Understanding code
        if any(kw in query_lower for kw in [
            "how does", "how is", "what does", "explain", "understand",
            "what is", "tell me about"
        ]):
            return ("understanding", False)

        # Making changes
        if any(kw in query_lower for kw in [
            "add", "modify", "change", "update", "implement", "create",
            "remove", "delete", "refactor"
        ]):
            return ("making_changes", False)

        # Debugging
        if any(kw in query_lower for kw in [
            "why", "debug", "fix", "error", "issue", "problem", "failing",
            "not working", "broken"
        ]):
            return ("debugging", False)

        # Review/patterns
        if any(kw in query_lower for kw in [
            "review", "pattern", "best practice", "similar", "like"
        ]):
            return ("review", False)

        # Impact analysis
        if any(kw in query_lower for kw in [
            "depends on", "uses", "calls", "references", "affected by"
        ]):
            return ("impact_analysis", False)

        # Default: questions
        return ("questions", False)

    def log_search(
        self,
        tool_name: str,
        query: str,
        workspace: str,
        top_k: int = 10
    ):
        """
        Log a search call.

        Args:
            tool_name: search_code, docs_search, or search_all
            query: Search query string
            workspace: Workspace path
            top_k: Number of results requested
        """
        scenario, is_explicit = self.classify_query(query)

        metric = SearchMetric(
            timestamp=datetime.now().isoformat(),
            tool_name=tool_name,
            query=query,
            workspace=workspace,
            top_k=top_k,
            scenario=scenario,
            explicit_search=is_explicit
        )

        # Load existing metrics
        metrics = self._load_metrics()

        # Append new metric
        metrics.append(asdict(metric))

        # Save back
        self._save_metrics(metrics)

        # Also log to console for immediate visibility
        logger.info(f"[METRICS] {tool_name} | scenario={scenario} | explicit={is_explicit} | query={query[:50]}...")

    def get_summary(self, since_timestamp: Optional[str] = None) -> Dict:
        """
        Get metrics summary.

        Args:
            since_timestamp: Only include metrics after this ISO timestamp

        Returns:
            Summary dict with counts, percentages, scenarios
        """
        metrics = self._load_metrics()

        # Filter by timestamp if provided
        if since_timestamp:
            metrics = [
                m for m in metrics
                if m["timestamp"] >= since_timestamp
            ]

        if not metrics:
            return {
                "total_searches": 0,
                "explicit_searches": 0,
                "implicit_searches": 0,
                "explicit_percentage": 0,
                "implicit_percentage": 0,
                "scenarios": {}
            }

        total = len(metrics)
        explicit = sum(1 for m in metrics if m["explicit_search"])
        implicit = total - explicit

        # Count by scenario
        scenarios = {}
        for m in metrics:
            scenario = m["scenario"]
            scenarios[scenario] = scenarios.get(scenario, 0) + 1

        # Count by tool
        tools = {}
        for m in metrics:
            tool = m["tool_name"]
            tools[tool] = tools.get(tool, 0) + 1

        return {
            "total_searches": total,
            "explicit_searches": explicit,
            "implicit_searches": implicit,
            "explicit_percentage": round(explicit / total * 100, 1),
            "implicit_percentage": round(implicit / total * 100, 1),
            "scenarios": scenarios,
            "tools": tools,
            "sample_queries": {
                scenario: [
                    m["query"] for m in metrics
                    if m["scenario"] == scenario
                ][:3]  # First 3 examples per scenario
                for scenario in scenarios.keys()
            }
        }

    def export_for_analysis(self, output_file: str):
        """
        Export metrics to CSV for detailed analysis.

        Args:
            output_file: Output CSV file path
        """
        import csv

        metrics = self._load_metrics()

        if not metrics:
            logger.info("[METRICS] No metrics to export")
            return

        with open(output_file, 'w', newline='') as f:
            if metrics:
                writer = csv.DictWriter(f, fieldnames=metrics[0].keys())
                writer.writeheader()
                writer.writerows(metrics)

        logger.info(f"[METRICS] Exported {len(metrics)} metrics to {output_file}")

    def clear_metrics(self):
        """Clear all metrics (for fresh baseline)."""
        self._save_metrics([])
        logger.info(f"[METRICS] Cleared all metrics from {self.metrics_file}")

    def _load_metrics(self) -> List[Dict]:
        """Load metrics from file."""
        if not self.metrics_file.exists():
            return []

        try:
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _save_metrics(self, metrics: List[Dict]):
        """Save metrics to file."""
        with open(self.metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)


# Global tracker instance
_tracker: Optional[MetricsTracker] = None


def get_tracker() -> MetricsTracker:
    """Get or create global metrics tracker."""
    global _tracker
    if _tracker is None:
        _tracker = MetricsTracker()
    return _tracker
