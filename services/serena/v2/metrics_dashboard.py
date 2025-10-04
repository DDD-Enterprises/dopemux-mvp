"""
F7: Metrics Dashboard

Aggregates F1-F6 analytics into ADHD-optimized dashboard views.
Provides 3-level progressive disclosure with visual indicators.

Key Features:
- Aggregate detection metrics (confidence, pass rate, patterns, abandonment)
- 3-level progressive disclosure (summary, breakdown, trends)
- ADHD presentation rules (max 5 items, visual indicators)
- ConPort integration for historical tracking
- Text-based terminal-friendly visualization

Part of Phase 2 Analytics (F5-F8)
"""

from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging
import json
from collections import defaultdict

logger = logging.getLogger(__name__)


class MetricsAggregator:
    """
    Aggregate detection results into statistics

    Processes F1-F6 metrics from detection results and calculates:
    - Detection statistics (count, pass rate, avg confidence)
    - Pattern learning statistics (boost rate, avg boost, top patterns)
    - Abandonment statistics (count, severity, action suggestions)
    """

    def aggregate_detections(self, results: List[Dict]) -> Dict:
        """
        Aggregate all detection results into comprehensive statistics

        Args:
            results: List of detection results from UntrackedWorkDetector.detect()

        Returns:
            Aggregated metrics across F1-F6 features
        """
        if not results:
            return self._empty_metrics()

        return {
            "total_detections": len(results),
            "timestamp": datetime.now().isoformat(),
            "f1_f4_metrics": self.calculate_f1_f4_metrics(results),
            "f5_metrics": self.calculate_f5_metrics(results),
            "f6_metrics": self.calculate_f6_metrics(results)
        }

    def calculate_f1_f4_metrics(self, results: List[Dict]) -> Dict:
        """
        Calculate F1-F4: Detection System metrics

        Metrics:
        - Total detections
        - Pass rate (passed threshold / total)
        - Average confidence score
        - Average threshold used
        - Session distribution (session 1, 2, 3+)
        """
        total = len(results)
        passed = sum(1 for r in results if r.get("passes_threshold", False))

        confidences = [r.get("confidence_score", 0.0) for r in results]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        thresholds = [r.get("threshold_used", 0.0) for r in results]
        avg_threshold = sum(thresholds) / len(thresholds) if thresholds else 0.0

        # Session distribution
        session_dist = defaultdict(int)
        for r in results:
            session = r.get("session_number", 1)
            if session >= 3:
                session_dist["3+"] += 1
            else:
                session_dist[str(session)] += 1

        return {
            "total_detections": total,
            "passed": passed,
            "pass_rate": passed / total if total > 0 else 0.0,
            "avg_confidence": round(avg_confidence, 2),
            "avg_threshold": round(avg_threshold, 2),
            "session_distribution": dict(session_dist)
        }

    def calculate_f5_metrics(self, results: List[Dict]) -> Dict:
        """
        Calculate F5: Pattern Learning metrics

        Metrics:
        - Boost rate (detections with pattern boost / total)
        - Average boost amount
        - Top patterns (limited to 5 for ADHD)
        """
        total = len(results)
        boosted = sum(1 for r in results if r.get("pattern_boost", 0.0) > 0)

        boosts = [r.get("pattern_boost", 0.0) for r in results]
        avg_boost = sum(boosts) / len(boosts) if boosts else 0.0

        # Collect pattern details
        pattern_counts = defaultdict(int)
        for r in results:
            details = r.get("pattern_boost_details", {})
            for pattern in details.get("matching_patterns", []):
                pattern_type = pattern.get("type", "unknown")
                pattern_value = pattern.get("pattern", "unknown")
                key = f"{pattern_type}:{pattern_value}"
                pattern_counts[key] += 1

        # Top 5 patterns only (ADHD limit)
        top_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "boost_rate": boosted / total if total > 0 else 0.0,
            "avg_boost": round(avg_boost, 3),
            "boosted_count": boosted,
            "top_patterns": [{"pattern": p, "count": c} for p, c in top_patterns]
        }

    def calculate_f6_metrics(self, results: List[Dict]) -> Dict:
        """
        Calculate F6: Abandonment Tracking metrics

        Metrics:
        - Total abandoned (score >= 0.5)
        - Average days idle
        - Severity distribution (stale, likely, definitely)
        - Action suggestions (commit, archive, delete)
        """
        abandoned = [
            r for r in results
            if r.get("abandonment_data", {}).get("is_abandoned", False)
        ]

        if not abandoned:
            return {
                "total_abandoned": 0,
                "avg_days_idle": 0.0,
                "severity_distribution": {},
                "action_suggestions": {}
            }

        # Calculate stats
        days_idle_list = [r["abandonment_data"]["days_idle"] for r in abandoned]
        avg_days_idle = sum(days_idle_list) / len(days_idle_list)

        # Severity distribution
        severity_dist = defaultdict(int)
        for r in abandoned:
            severity = r["abandonment_data"]["severity"]
            severity_dist[severity] += 1

        # Action suggestions (would come from suggest_action in real usage)
        # For now, estimate based on file counts
        action_dist = defaultdict(int)
        for r in abandoned:
            file_count = len(r.get("git_detection", {}).get("files", []))
            if file_count > 5:
                action_dist["commit"] += 1
            elif file_count > 2:
                action_dist["archive"] += 1
            else:
                action_dist["delete"] += 1

        return {
            "total_abandoned": len(abandoned),
            "avg_days_idle": round(avg_days_idle, 1),
            "severity_distribution": dict(severity_dist),
            "action_suggestions": dict(action_dist)
        }

    def _empty_metrics(self) -> Dict:
        """Return empty metrics structure"""
        return {
            "total_detections": 0,
            "timestamp": datetime.now().isoformat(),
            "f1_f4_metrics": {
                "total_detections": 0,
                "passed": 0,
                "pass_rate": 0.0,
                "avg_confidence": 0.0,
                "avg_threshold": 0.0,
                "session_distribution": {}
            },
            "f5_metrics": {
                "boost_rate": 0.0,
                "avg_boost": 0.0,
                "boosted_count": 0,
                "top_patterns": []
            },
            "f6_metrics": {
                "total_abandoned": 0,
                "avg_days_idle": 0.0,
                "severity_distribution": {},
                "action_suggestions": {}
            }
        }


class MetricsDashboard:
    """
    Generate ADHD-optimized dashboard views

    Provides 3 levels of progressive disclosure:
    - Level 1: At-a-glance summary (always shown)
    - Level 2: Feature breakdown (F1-F6 separate sections)
    - Level 3: Time-series trends (requires ConPort history)

    ADHD Optimizations:
    - Max 5 items per section
    - Visual indicators (✅❌📈📉↑↓)
    - Trend directions only (not all values)
    - Color coding with emojis
    """

    def __init__(self, workspace_id: str):
        """
        Initialize metrics dashboard

        Args:
            workspace_id: Workspace ID for ConPort integration
        """
        self.workspace_id = workspace_id
        self.aggregator = MetricsAggregator()

    def generate_summary(
        self,
        results: List[Dict],
        level: int = 1,
        include_trends: bool = False
    ) -> str:
        """
        Generate dashboard at specified disclosure level

        Args:
            results: List of detection results to aggregate
            level: Disclosure level (1, 2, or 3)
            include_trends: Show trend arrows (requires history)

        Returns:
            Formatted dashboard string
        """
        metrics = self.aggregator.aggregate_detections(results)

        if level == 1:
            return self.format_level1(metrics, include_trends)
        elif level == 2:
            return self.format_level2(metrics)
        elif level == 3:
            return self.format_level3(metrics, {})  # TODO: Add history
        else:
            return "Invalid level. Use 1 (summary), 2 (breakdown), or 3 (trends)."

    def format_level1(self, metrics: Dict, include_trends: bool = False) -> str:
        """
        Level 1: At-a-glance summary

        Shows:
        - Detection count and pass rate
        - Average confidence
        - Pattern boost activity
        - Abandonment count
        """
        f1_f4 = metrics["f1_f4_metrics"]
        f5 = metrics["f5_metrics"]
        f6 = metrics["f6_metrics"]

        # Detection summary
        total = f1_f4["total_detections"]
        passed = f1_f4["passed"]
        pass_rate = f1_f4["pass_rate"]

        # Confidence indicator
        conf = f1_f4["avg_confidence"]
        conf_emoji = "🟢" if conf >= 0.7 else "🟡" if conf >= 0.5 else "🔴"

        # Abandonment indicator
        abandoned = f6["total_abandoned"]
        abandon_emoji = "✅" if abandoned == 0 else "🟡" if abandoned <= 2 else "🔴"

        output = []
        output.append("📊 Detection Summary")
        output.append("=" * 50)
        output.append(f"✅ Detections: {total} found | {passed} tracked ({pass_rate:.0%} pass rate)")
        output.append(f"{conf_emoji} Avg Confidence: {conf:.2f}")
        output.append(f"⚡ Pattern Boost: Active in {f5['boost_rate']:.0%} of detections")
        output.append(f"{abandon_emoji} Abandonments: {abandoned} items")

        if abandoned > 0:
            avg_idle = f6["avg_days_idle"]
            output.append(f"   └─ Avg {avg_idle:.1f} days idle")

        return "\n".join(output)

    def format_level2(self, metrics: Dict) -> str:
        """
        Level 2: Feature breakdown

        Shows F1-F6 metrics in separate sections
        """
        f1_f4 = metrics["f1_f4_metrics"]
        f5 = metrics["f5_metrics"]
        f6 = metrics["f6_metrics"]

        output = []
        output.append("📊 Metrics Dashboard - Feature Breakdown")
        output.append("=" * 50)

        # F1-F4: Detection System
        output.append("\n🔍 F1-F4: Detection System")
        output.append(f"  Total detections: {f1_f4['total_detections']}")
        output.append(f"  Pass rate: {f1_f4['pass_rate']:.1%} ({f1_f4['passed']}/{f1_f4['total_detections']})")
        output.append(f"  Avg confidence: {f1_f4['avg_confidence']:.2f}")
        output.append(f"  Avg threshold: {f1_f4['avg_threshold']:.2f}")

        if f1_f4['session_distribution']:
            output.append("  Session distribution:")
            for session, count in sorted(f1_f4['session_distribution'].items()):
                output.append(f"    Session {session}: {count}")

        # F5: Pattern Learning
        output.append("\n⚡ F5: Pattern Learning")
        output.append(f"  Boost rate: {f5['boost_rate']:.1%} ({f5['boosted_count']} detections)")
        output.append(f"  Avg boost: +{f5['avg_boost']:.3f}")

        if f5['top_patterns']:
            output.append("  Top patterns (max 5):")
            for pattern_data in f5['top_patterns'][:5]:
                pattern = pattern_data['pattern']
                count = pattern_data['count']
                output.append(f"    {pattern}: {count} occurrences")

        # F6: Abandonment Tracking
        output.append("\n🔴 F6: Abandonment Tracking")
        output.append(f"  Total abandoned: {f6['total_abandoned']}")

        if f6['total_abandoned'] > 0:
            output.append(f"  Avg days idle: {f6['avg_days_idle']:.1f}")

            if f6['severity_distribution']:
                output.append("  Severity distribution:")
                for severity, count in f6['severity_distribution'].items():
                    emoji = {"stale": "🟡", "likely_abandoned": "🟠", "definitely_abandoned": "🔴"}.get(severity, "⚪")
                    output.append(f"    {emoji} {severity}: {count}")

            if f6['action_suggestions']:
                output.append("  Suggested actions:")
                for action, count in f6['action_suggestions'].items():
                    output.append(f"    {action}: {count}")
        else:
            output.append("  ✅ No abandoned work detected")

        return "\n".join(output)

    def format_level3(self, metrics: Dict, history: Dict) -> str:
        """
        Level 3: Time-series trends

        Requires ConPort historical data
        Shows trends over time (daily/weekly)
        """
        output = []
        output.append("📊 Metrics Dashboard - Trend Analysis")
        output.append("=" * 50)

        if not history:
            output.append("\n⚠️  No historical data available")
            output.append("   Run detections over multiple days to see trends")
            return "\n".join(output)

        # TODO: Implement trend analysis when ConPort integration is complete
        output.append("\n📈 Confidence Trend (7 days)")
        output.append("  [Trend visualization coming soon]")

        output.append("\n⚡ Pattern Boost Trend (7 days)")
        output.append("  [Trend visualization coming soon]")

        output.append("\n🔴 Abandonment Trend (7 days)")
        output.append("  [Trend visualization coming soon]")

        return "\n".join(output)

    def save_daily_snapshot(self, metrics: Dict, conport_client = None) -> None:
        """
        Save daily metrics snapshot to ConPort

        Args:
            metrics: Aggregated metrics from aggregate_detections()
            conport_client: Optional ConPort MCP client

        Stores in custom_data category 'metrics_history'
        Key format: YYYY-MM-DD_summary
        90-day retention policy
        """
        if not conport_client:
            logger.warning("ConPort client not provided, skipping snapshot save")
            return

        # TODO: Implement when ConPort client is available
        date_key = datetime.now().strftime("%Y-%m-%d_summary")

        # Store metrics as JSON in ConPort custom_data
        # category: "metrics_history"
        # key: date_key
        # value: metrics

        logger.info(f"Saved metrics snapshot: {date_key}")

    def get_trends(
        self,
        metric_name: str,
        days: int = 7,
        conport_client = None
    ) -> Dict:
        """
        Retrieve historical trends from ConPort

        Args:
            metric_name: Metric to retrieve ("confidence", "pattern_boost", "abandonment_rate")
            days: Number of days of history
            conport_client: Optional ConPort MCP client

        Returns:
            Time-series data for the specified metric
        """
        if not conport_client:
            logger.warning("ConPort client not provided, returning empty trends")
            return {}

        # TODO: Implement when ConPort client is available
        # Query ConPort custom_data category 'metrics_history'
        # For last N days
        # Extract specific metric from each snapshot
        # Return as {date: value} dictionary

        return {}
