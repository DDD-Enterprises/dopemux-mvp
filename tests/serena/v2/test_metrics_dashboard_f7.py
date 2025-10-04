"""
Tests for F7: Metrics Dashboard

Tests metrics_dashboard.py functionality:
- Metrics aggregation (F1-F6)
- Progressive disclosure (Levels 1-3)
- ADHD presentation rules
- ConPort integration
- Dashboard formatting
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add Serena v2 to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "services" / "serena" / "v2"))

from metrics_dashboard import MetricsAggregator, MetricsDashboard


class TestMetricsAggregator:
    """Test suite for metrics aggregation logic"""

    @pytest.fixture
    def aggregator(self):
        """Create MetricsAggregator instance"""
        return MetricsAggregator()

    def test_aggregate_empty_detections(self, aggregator):
        """Test aggregation with no detections"""
        result = aggregator.aggregate_detections([])

        assert result["total_detections"] == 0
        assert result["f1_f4_metrics"]["pass_rate"] == 0.0
        assert result["f5_metrics"]["boost_rate"] == 0.0
        assert result["f6_metrics"]["total_abandoned"] == 0

    def test_aggregate_single_detection(self, aggregator):
        """Test aggregation with single detection"""
        detection = {
            "confidence_score": 0.75,
            "passes_threshold": True,
            "threshold_used": 0.65,
            "session_number": 1,
            "pattern_boost": 0.15,
            "pattern_boost_details": {
                "matching_patterns": [
                    {"type": "file_extension", "pattern": ".py"}
                ]
            },
            "abandonment_data": {
                "is_abandoned": False,
                "days_idle": 2
            },
            "git_detection": {"files": ["test.py"]}
        }

        result = aggregator.aggregate_detections([detection])

        assert result["total_detections"] == 1
        assert result["f1_f4_metrics"]["pass_rate"] == 1.0
        assert result["f1_f4_metrics"]["avg_confidence"] == 0.75
        assert result["f5_metrics"]["boost_rate"] == 1.0
        assert result["f6_metrics"]["total_abandoned"] == 0

    def test_aggregate_multiple_detections(self, aggregator):
        """Test aggregation with multiple detections (varying confidence/boost)"""
        detections = [
            {
                "confidence_score": 0.80,
                "passes_threshold": True,
                "threshold_used": 0.65,
                "session_number": 2,
                "pattern_boost": 0.15,
                "pattern_boost_details": {"matching_patterns": []},
                "abandonment_data": {"is_abandoned": False},
                "git_detection": {"files": []}
            },
            {
                "confidence_score": 0.60,
                "passes_threshold": False,
                "threshold_used": 0.65,
                "session_number": 1,
                "pattern_boost": 0.0,
                "pattern_boost_details": {"matching_patterns": []},
                "abandonment_data": {"is_abandoned": False},
                "git_detection": {"files": []}
            },
            {
                "confidence_score": 0.70,
                "passes_threshold": True,
                "threshold_used": 0.60,
                "session_number": 3,
                "pattern_boost": 0.10,
                "pattern_boost_details": {"matching_patterns": []},
                "abandonment_data": {"is_abandoned": False},
                "git_detection": {"files": []}
            }
        ]

        result = aggregator.aggregate_detections(detections)

        assert result["total_detections"] == 3
        assert result["f1_f4_metrics"]["passed"] == 2
        assert result["f1_f4_metrics"]["pass_rate"] == pytest.approx(0.667, rel=0.01)
        assert result["f1_f4_metrics"]["avg_confidence"] == 0.70  # (0.80 + 0.60 + 0.70) / 3
        assert result["f5_metrics"]["boosted_count"] == 2  # 2 detections with boost > 0

    def test_aggregate_with_abandonments(self, aggregator):
        """Test aggregation with abandoned work"""
        detections = [
            {
                "confidence_score": 0.75,
                "passes_threshold": True,
                "threshold_used": 0.65,
                "session_number": 2,
                "pattern_boost": 0.12,
                "pattern_boost_details": {"matching_patterns": []},
                "abandonment_data": {
                    "is_abandoned": True,
                    "days_idle": 10,
                    "severity": "likely_abandoned"
                },
                "git_detection": {"files": ["a.py", "b.py", "c.py"]}  # 3 files → archive
            },
            {
                "confidence_score": 0.68,
                "passes_threshold": True,
                "threshold_used": 0.65,
                "session_number": 2,
                "pattern_boost": 0.08,
                "pattern_boost_details": {"matching_patterns": []},
                "abandonment_data": {
                    "is_abandoned": True,
                    "days_idle": 15,
                    "severity": "definitely_abandoned"
                },
                "git_detection": {"files": [f"file{i}.py" for i in range(8)]}  # 8 files → commit
            }
        ]

        result = aggregator.aggregate_detections(detections)

        assert result["f6_metrics"]["total_abandoned"] == 2
        assert result["f6_metrics"]["avg_days_idle"] == 12.5  # (10 + 15) / 2
        assert result["f6_metrics"]["severity_distribution"]["likely_abandoned"] == 1
        assert result["f6_metrics"]["severity_distribution"]["definitely_abandoned"] == 1
        assert result["f6_metrics"]["action_suggestions"]["commit"] == 1  # 8 files
        assert result["f6_metrics"]["action_suggestions"]["archive"] == 1  # 3 files

    def test_calculate_f5_top_patterns_limit(self, aggregator):
        """Test F5 top patterns limited to 5 (ADHD rule)"""
        # Create 10 different patterns
        detections = []
        for i in range(10):
            detections.append({
                "confidence_score": 0.70,
                "passes_threshold": True,
                "threshold_used": 0.65,
                "session_number": 1,
                "pattern_boost": 0.10,
                "pattern_boost_details": {
                    "matching_patterns": [
                        {"type": "file_extension", "pattern": f".ext{i}"}
                    ]
                },
                "abandonment_data": {"is_abandoned": False},
                "git_detection": {"files": []}
            })

        result = aggregator.aggregate_detections(detections)

        # Should only return top 5 patterns
        assert len(result["f5_metrics"]["top_patterns"]) <= 5


class TestMetricsDashboard:
    """Test suite for dashboard formatting"""

    @pytest.fixture
    def dashboard(self):
        """Create MetricsDashboard instance"""
        return MetricsDashboard(workspace_id="/tmp/test_workspace")

    @pytest.fixture
    def sample_detections(self):
        """Sample detection results for testing"""
        return [
            {
                "confidence_score": 0.75,
                "passes_threshold": True,
                "threshold_used": 0.65,
                "session_number": 2,
                "pattern_boost": 0.12,
                "pattern_boost_details": {
                    "matching_patterns": [
                        {"type": "file_extension", "pattern": ".py"}
                    ]
                },
                "abandonment_data": {
                    "is_abandoned": True,
                    "days_idle": 10,
                    "severity": "likely_abandoned"
                },
                "git_detection": {"files": ["a.py", "b.py"]}
            },
            {
                "confidence_score": 0.68,
                "passes_threshold": True,
                "threshold_used": 0.65,
                "session_number": 2,
                "pattern_boost": 0.10,
                "pattern_boost_details": {
                    "matching_patterns": [
                        {"type": "directory", "pattern": "services/"}
                    ]
                },
                "abandonment_data": {
                    "is_abandoned": False,
                    "days_idle": 3
                },
                "git_detection": {"files": ["c.py"]}
            }
        ]

    def test_generate_summary_level1(self, dashboard, sample_detections):
        """Test Level 1: At-a-glance summary"""
        summary = dashboard.generate_summary(sample_detections, level=1)

        # Check for key components
        assert "Detection Summary" in summary
        assert "2 found" in summary  # Total detections
        assert "2 tracked" in summary  # Passed threshold
        assert "Avg Confidence" in summary
        assert "Pattern Boost" in summary
        assert "Abandonments: 1" in summary

    def test_generate_summary_level2(self, dashboard, sample_detections):
        """Test Level 2: Feature breakdown"""
        summary = dashboard.generate_summary(sample_detections, level=2)

        # Check for F1-F6 sections
        assert "F1-F4: Detection System" in summary
        assert "F5: Pattern Learning" in summary
        assert "F6: Abandonment Tracking" in summary

        # Check for specific metrics
        assert "Total detections: 2" in summary
        assert "Pass rate" in summary
        assert "Boost rate" in summary
        assert "Total abandoned: 1" in summary

    def test_generate_summary_level3_no_history(self, dashboard, sample_detections):
        """Test Level 3: Trends (without historical data)"""
        summary = dashboard.generate_summary(sample_detections, level=3)

        # Should show "no data" message
        assert "Trend Analysis" in summary
        assert "No historical data" in summary or "coming soon" in summary.lower()

    def test_level1_visual_indicators(self, dashboard, sample_detections):
        """Test Level 1 uses visual indicators (emojis)"""
        summary = dashboard.generate_summary(sample_detections, level=1)

        # Check for emoji indicators
        assert any(emoji in summary for emoji in ["📊", "✅", "🟢", "🟡", "🔴", "⚡"])

    def test_level1_no_abandonments(self, dashboard):
        """Test Level 1 with zero abandonments shows positive message"""
        detections = [{
            "confidence_score": 0.75,
            "passes_threshold": True,
            "threshold_used": 0.65,
            "session_number": 1,
            "pattern_boost": 0.10,
            "pattern_boost_details": {"matching_patterns": []},
            "abandonment_data": {"is_abandoned": False},
            "git_detection": {"files": []}
        }]

        summary = dashboard.generate_summary(detections, level=1)

        assert "Abandonments: 0" in summary

    def test_level2_max_5_patterns(self, dashboard):
        """Test Level 2 limits patterns to 5 (ADHD rule)"""
        # Create 10 detections with different patterns
        detections = []
        for i in range(10):
            detections.append({
                "confidence_score": 0.70,
                "passes_threshold": True,
                "threshold_used": 0.65,
                "session_number": 1,
                "pattern_boost": 0.10,
                "pattern_boost_details": {
                    "matching_patterns": [
                        {"type": "file_extension", "pattern": f".ext{i}"}
                    ]
                },
                "abandonment_data": {"is_abandoned": False},
                "git_detection": {"files": []}
            })

        summary = dashboard.generate_summary(detections, level=2)

        # Count pattern mentions in output
        pattern_count = summary.count(".ext")
        assert pattern_count <= 5  # Should not exceed 5


class TestADHDPresentation:
    """Test suite for ADHD presentation rules"""

    @pytest.fixture
    def dashboard(self):
        """Create MetricsDashboard instance"""
        return MetricsDashboard(workspace_id="/tmp/test_workspace")

    def test_progressive_disclosure_default_level1(self, dashboard):
        """Test default disclosure level is 1 (summary)"""
        detections = [{
            "confidence_score": 0.70,
            "passes_threshold": True,
            "threshold_used": 0.65,
            "session_number": 1,
            "pattern_boost": 0.0,
            "pattern_boost_details": {"matching_patterns": []},
            "abandonment_data": {"is_abandoned": False},
            "git_detection": {"files": []}
        }]

        # Default should be level 1
        summary_default = dashboard.generate_summary(detections)
        summary_level1 = dashboard.generate_summary(detections, level=1)

        assert summary_default == summary_level1

    def test_visual_scanning_with_emojis(self, dashboard):
        """Test dashboard uses emojis for quick visual scanning"""
        detections = [{
            "confidence_score": 0.85,  # High confidence → 🟢
            "passes_threshold": True,
            "threshold_used": 0.65,
            "session_number": 1,
            "pattern_boost": 0.12,
            "pattern_boost_details": {"matching_patterns": []},
            "abandonment_data": {"is_abandoned": False},
            "git_detection": {"files": []}
        }]

        summary = dashboard.generate_summary(detections, level=1)

        # High confidence should show green indicator
        assert "🟢" in summary


class TestIntegration:
    """Integration tests for full dashboard workflow"""

    def test_full_dashboard_workflow(self):
        """Test complete workflow: aggregate → format → display"""
        dashboard = MetricsDashboard(workspace_id="/tmp/test_workspace")

        # Realistic detection data
        detections = [
            {
                "confidence_score": 0.78,
                "passes_threshold": True,
                "threshold_used": 0.65,
                "session_number": 2,
                "pattern_boost": 0.15,
                "pattern_boost_details": {
                    "matching_patterns": [
                        {"type": "file_extension", "pattern": ".py"},
                        {"type": "directory", "pattern": "services/"}
                    ]
                },
                "abandonment_data": {
                    "is_abandoned": True,
                    "days_idle": 9,
                    "severity": "likely_abandoned"
                },
                "git_detection": {"files": ["auth.py", "session.py", "jwt.py"]}
            },
            {
                "confidence_score": 0.65,
                "passes_threshold": True,
                "threshold_used": 0.65,
                "session_number": 1,
                "pattern_boost": 0.0,
                "pattern_boost_details": {"matching_patterns": []},
                "abandonment_data": {
                    "is_abandoned": False,
                    "days_idle": 1
                },
                "git_detection": {"files": ["readme.md"]}
            }
        ]

        # Test all 3 levels
        level1 = dashboard.generate_summary(detections, level=1)
        level2 = dashboard.generate_summary(detections, level=2)
        level3 = dashboard.generate_summary(detections, level=3)

        # All should produce output
        assert len(level1) > 0
        assert len(level2) > 0
        assert len(level3) > 0

        # Level 2 should be longer than Level 1 (more detail)
        assert len(level2) > len(level1)

    def test_empty_detections_graceful(self):
        """Test dashboard handles empty detection list gracefully"""
        dashboard = MetricsDashboard(workspace_id="/tmp/test_workspace")

        summary = dashboard.generate_summary([], level=1)

        # Should not crash, should show "0" values
        assert "0 found" in summary or "No detections" in summary.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
