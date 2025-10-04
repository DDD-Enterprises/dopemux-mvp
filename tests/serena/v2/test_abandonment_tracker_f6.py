"""
Tests for F6: Abandonment Tracking

Tests abandonment_tracker.py functionality:
- Score calculation (days_idle / 14)
- Severity classification (stale/likely/definitely)
- Integration with git detection
- Action suggestions
- Statistics generation
"""

import pytest
from pathlib import Path
from datetime import datetime, timedelta
import sys

# Add Serena v2 to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "services" / "serena" / "v2"))

from abandonment_tracker import AbandonmentTracker


class TestAbandonmentScore:
    """Test suite for abandonment score calculation"""

    @pytest.fixture
    def tracker(self):
        """Create AbandonmentTracker instance"""
        return AbandonmentTracker(workspace_id="/tmp/test_workspace")

    def test_score_7_days(self, tracker):
        """Test abandonment score for 7 days idle (should be 0.5)"""
        git_detection = {
            "first_change_time": datetime.now() - timedelta(days=7),
            "files": ["test.py"]
        }

        result = tracker.calculate_abandonment_score(git_detection)

        assert result["days_idle"] == 7
        assert result["score"] == 0.5  # 7 / 14 = 0.5
        assert result["is_abandoned"] is True  # score >= 0.5

    def test_score_14_days(self, tracker):
        """Test abandonment score for 14 days idle (should be 1.0)"""
        git_detection = {
            "first_change_time": datetime.now() - timedelta(days=14),
            "files": ["test.py"]
        }

        result = tracker.calculate_abandonment_score(git_detection)

        assert result["days_idle"] == 14
        assert result["score"] == 1.0  # 14 / 14 = 1.0
        assert result["is_abandoned"] is True

    def test_score_28_days_capped(self, tracker):
        """Test abandonment score for 28 days idle (should cap at 1.0)"""
        git_detection = {
            "first_change_time": datetime.now() - timedelta(days=28),
            "files": ["test.py"]
        }

        result = tracker.calculate_abandonment_score(git_detection)

        assert result["days_idle"] == 28
        assert result["score"] == 1.0  # Capped at 1.0 (not 2.0)
        assert result["is_abandoned"] is True

    def test_score_no_first_change_time(self, tracker):
        """Test abandonment score when first_change_time is missing"""
        git_detection = {
            "first_change_time": None,
            "files": ["test.py"]
        }

        result = tracker.calculate_abandonment_score(git_detection)

        assert result["score"] == 0.0
        assert result["days_idle"] == 0
        assert result["severity"] == "none"
        assert result["is_abandoned"] is False


class TestSeverityClassification:
    """Test suite for severity classification"""

    @pytest.fixture
    def tracker(self):
        """Create AbandonmentTracker instance"""
        return AbandonmentTracker(workspace_id="/tmp/test_workspace")

    def test_severity_none(self, tracker):
        """Test severity classification for score < 0.3 (none)"""
        assert tracker.classify_severity(0.0) == "none"
        assert tracker.classify_severity(0.2) == "none"
        assert tracker.classify_severity(0.29) == "none"

    def test_severity_stale(self, tracker):
        """Test severity classification for 0.3 <= score < 0.5 (stale)"""
        assert tracker.classify_severity(0.3) == "stale"
        assert tracker.classify_severity(0.4) == "stale"
        assert tracker.classify_severity(0.49) == "stale"

    def test_severity_likely_abandoned(self, tracker):
        """Test severity classification for 0.5 <= score < 0.7 (likely)"""
        assert tracker.classify_severity(0.5) == "likely_abandoned"
        assert tracker.classify_severity(0.6) == "likely_abandoned"
        assert tracker.classify_severity(0.69) == "likely_abandoned"

    def test_severity_definitely_abandoned(self, tracker):
        """Test severity classification for score >= 0.7 (definitely)"""
        assert tracker.classify_severity(0.7) == "definitely_abandoned"
        assert tracker.classify_severity(0.85) == "definitely_abandoned"
        assert tracker.classify_severity(1.0) == "definitely_abandoned"


class TestMessaging:
    """Test suite for ADHD-friendly messaging"""

    @pytest.fixture
    def tracker(self):
        """Create AbandonmentTracker instance"""
        return AbandonmentTracker(workspace_id="/tmp/test_workspace")

    def test_message_none_severity(self, tracker):
        """Test message for 'none' severity (recent work)"""
        message = tracker.generate_message("none", 2)

        assert "⚪" in message
        assert "2 days" in message
        assert "guilt" not in message.lower()

    def test_message_stale_severity(self, tracker):
        """Test message for 'stale' severity (gentle nudge)"""
        message = tracker.generate_message("stale", 5)

        assert "🟡" in message
        assert "5 days" in message
        assert "stale" in message.lower()
        # Check it's a gentle suggestion, not blame
        assert any(word in message.lower() for word in ["might", "want", "soon"])

    def test_message_likely_abandoned(self, tracker):
        """Test message for 'likely_abandoned' severity"""
        message = tracker.generate_message("likely_abandoned", 8)

        assert "🟠" in message
        assert "8 days" in message
        # Check for choice-based language (not blame)
        assert any(word in message.lower() for word in ["want", "finish", "archive"])

    def test_message_definitely_abandoned(self, tracker):
        """Test message for 'definitely_abandoned' severity"""
        message = tracker.generate_message("definitely_abandoned", 15)

        assert "🔴" in message
        assert "15 days" in message
        # Check for action-oriented language (not guilt)
        assert any(word in message.lower() for word in ["decide", "commit", "archive", "delete"])


class TestActionSuggestions:
    """Test suite for action suggestions"""

    @pytest.fixture
    def tracker(self):
        """Create AbandonmentTracker instance"""
        return AbandonmentTracker(workspace_id="/tmp/test_workspace")

    def test_suggest_commit_for_substantial_work(self, tracker):
        """Test suggests 'commit' for substantial abandoned work (> 5 files)"""
        abandonment_data = {
            "severity": "definitely_abandoned",
            "days_idle": 15,
            "score": 1.0
        }

        git_detection = {
            "files": [f"file{i}.py" for i in range(8)],  # 8 files
            "stats": {"new": 2, "modified": 6, "deleted": 0}
        }

        result = tracker.suggest_action(abandonment_data, git_detection)

        assert result["action"] == "commit"
        assert "worth saving" in result["rationale"].lower() or "real work" in result["rationale"].lower()
        assert result["urgency"] == "high"

    def test_suggest_archive_for_small_experimental_work(self, tracker):
        """Test suggests 'archive' for small abandoned changes"""
        abandonment_data = {
            "severity": "definitely_abandoned",
            "days_idle": 12,
            "score": 0.85
        }

        git_detection = {
            "files": ["test1.py", "test2.py"],  # Only 2 files
            "stats": {"new": 0, "modified": 2, "deleted": 0}
        }

        result = tracker.suggest_action(abandonment_data, git_detection)

        assert result["action"] == "archive"
        assert "experimental" in result["rationale"].lower() or "stash" in result["rationale"].lower()

    def test_suggest_commit_for_new_files(self, tracker):
        """Test suggests 'commit' when new files created (intentional work)"""
        abandonment_data = {
            "severity": "likely_abandoned",
            "days_idle": 8,
            "score": 0.57
        }

        git_detection = {
            "files": ["new1.py", "new2.py", "new3.py"],
            "stats": {"new": 3, "modified": 0, "deleted": 0}
        }

        result = tracker.suggest_action(abandonment_data, git_detection)

        assert result["action"] == "commit"
        assert "new file" in result["rationale"].lower()


class TestIntegration:
    """Integration tests with git detection and pattern learning"""

    @pytest.fixture
    def tracker(self):
        """Create AbandonmentTracker instance"""
        return AbandonmentTracker(workspace_id="/tmp/test_workspace")

    def test_full_abandonment_flow(self, tracker):
        """Test complete abandonment detection flow"""
        # Simulate work from 10 days ago
        git_detection = {
            "first_change_time": datetime.now() - timedelta(days=10),
            "files": ["services/auth/jwt.py", "services/auth/session.py"],
            "stats": {"new": 1, "modified": 1, "deleted": 0}
        }

        # Calculate abandonment
        result = tracker.calculate_abandonment_score(git_detection)

        # Verify score
        assert result["days_idle"] == 10
        assert result["score"] == pytest.approx(0.71, rel=0.01)  # 10 / 14 ≈ 0.71
        assert result["severity"] == "definitely_abandoned"
        assert result["is_abandoned"] is True

        # Get action suggestion
        action = tracker.suggest_action(result, git_detection)
        assert action["action"] in ["commit", "archive", "delete"]
        assert action["urgency"] in ["low", "medium", "high"]


class TestStatistics:
    """Test suite for abandonment statistics"""

    @pytest.fixture
    def tracker(self):
        """Create AbandonmentTracker instance"""
        return AbandonmentTracker(workspace_id="/tmp/test_workspace")

    def test_summary_with_no_abandoned_work(self, tracker):
        """Test statistics with no abandoned work"""
        all_detections = []

        summary = tracker.get_abandonment_summary(all_detections)

        assert summary["total_abandoned"] == 0
        assert summary["by_severity"] == {}
        assert summary["avg_days_idle"] == 0.0
        assert summary["oldest_work"] is None

    def test_summary_with_abandoned_work(self, tracker):
        """Test statistics with abandoned work items"""
        all_detections = [
            {
                "work_name": "Feature A",
                "abandonment_data": {
                    "days_idle": 8,
                    "score": 0.57,
                    "severity": "likely_abandoned",
                    "is_abandoned": True
                },
                "git_detection": {
                    "files": ["a.py"],
                    "stats": {"new": 0, "modified": 1, "deleted": 0}
                }
            },
            {
                "work_name": "Feature B",
                "abandonment_data": {
                    "days_idle": 15,
                    "score": 1.0,
                    "severity": "definitely_abandoned",
                    "is_abandoned": True
                },
                "git_detection": {
                    "files": ["b.py", "c.py"],
                    "stats": {"new": 1, "modified": 1, "deleted": 0}
                }
            }
        ]

        summary = tracker.get_abandonment_summary(all_detections)

        assert summary["total_abandoned"] == 2
        assert summary["by_severity"]["likely_abandoned"] == 1
        assert summary["by_severity"]["definitely_abandoned"] == 1
        assert summary["avg_days_idle"] == 11.5  # (8 + 15) / 2
        assert summary["oldest_work"]["work_name"] == "Feature B"
        assert summary["oldest_work"]["days_idle"] == 15


# === Integration Tests ===

@pytest.mark.integration
class TestAbandonmentTrackerIntegration:
    """Full integration tests"""

    def test_realistic_abandonment_scenario(self):
        """Test realistic abandonment tracking scenario"""
        tracker = AbandonmentTracker(workspace_id="/tmp/test_workspace")

        # Scenario: User started working on auth feature 9 days ago
        git_detection = {
            "first_change_time": datetime.now() - timedelta(days=9),
            "files": [
                "services/auth/jwt.py",
                "services/auth/session.py",
                "services/auth/middleware.py",
                "tests/test_auth.py"
            ],
            "stats": {"new": 2, "modified": 2, "deleted": 0}
        }

        # Step 1: Calculate abandonment
        abandonment_data = tracker.calculate_abandonment_score(git_detection)

        assert abandonment_data["days_idle"] == 9
        assert 0.6 < abandonment_data["score"] < 0.7  # 9/14 ≈ 0.64
        assert abandonment_data["severity"] == "likely_abandoned"
        assert abandonment_data["is_abandoned"] is True
        assert "🟠" in abandonment_data["message"]  # Orange indicator

        # Step 2: Get action suggestion
        action = tracker.suggest_action(abandonment_data, git_detection)

        # Should suggest commit (new files + reasonable file count)
        assert action["action"] == "commit"
        assert "new file" in action["rationale"].lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
