"""
Tests for F4: Auto-Branch Suggestions

Tests git_detector.py:suggest_branch_organization() functionality:
- File clustering by directory
- Branch name generation
- ADHD-optimized output formatting
"""

import pytest
from pathlib import Path
from datetime import datetime

# Mock git_detector module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "services" / "serena" / "v2"))

from git_detector import GitWorkDetector


class TestF4BranchSuggestions:
    """F4: Auto-Branch Suggestions - Test Suite"""

    @pytest.fixture
    def detector(self, tmp_path):
        """Create GitWorkDetector instance"""
        return GitWorkDetector(tmp_path)

    @pytest.fixture
    def detection_mixed_work(self):
        """Simulated detection with mixed uncommitted work"""
        return {
            "has_uncommitted": True,
            "branch": "main",
            "files": [
                "services/auth/jwt.py",
                "services/auth/session.py",
                "services/auth/middleware.py",
                "tests/auth/test_jwt.py",
                "docs/auth.md",
                "docs/api.md",
                "README.md"
            ],
            "file_statuses": [
                {"path": "services/auth/jwt.py", "status": "M", "status_name": "modified"},
                {"path": "services/auth/session.py", "status": "M", "status_name": "modified"},
                {"path": "services/auth/middleware.py", "status": "??", "status_name": "new"},
                {"path": "tests/auth/test_jwt.py", "status": "??", "status_name": "new"},
                {"path": "docs/auth.md", "status": "M", "status_name": "modified"},
                {"path": "docs/api.md", "status": "M", "status_name": "modified"},
                {"path": "README.md", "status": "M", "status_name": "modified"}
            ],
            "stats": {"new": 2, "modified": 5, "deleted": 0},
            "common_directory": ".",
            "first_change_time": datetime.now(),
            "is_feature_branch": False
        }

    @pytest.fixture
    def detection_focused_work(self):
        """Simulated detection with focused work (single directory)"""
        return {
            "has_uncommitted": True,
            "branch": "feature/auth",
            "files": [
                "services/auth/jwt.py",
                "services/auth/session.py"
            ],
            "file_statuses": [
                {"path": "services/auth/jwt.py", "status": "M", "status_name": "modified"},
                {"path": "services/auth/session.py", "status": "M", "status_name": "modified"}
            ],
            "stats": {"new": 0, "modified": 2, "deleted": 0},
            "common_directory": "services/auth",
            "first_change_time": datetime.now(),
            "is_feature_branch": True
        }

    @pytest.fixture
    def detection_too_few_files(self):
        """Simulated detection with too few files to suggest splitting"""
        return {
            "has_uncommitted": True,
            "branch": "main",
            "files": ["README.md", "docs/guide.md"],
            "file_statuses": [
                {"path": "README.md", "status": "M", "status_name": "modified"},
                {"path": "docs/guide.md", "status": "M", "status_name": "modified"}
            ],
            "stats": {"new": 0, "modified": 2, "deleted": 0},
            "common_directory": ".",
            "first_change_time": datetime.now(),
            "is_feature_branch": False
        }

    # === Core Functionality Tests ===

    @pytest.mark.asyncio
    async def test_f4_split_recommended_mixed_work(self, detector, detection_mixed_work):
        """Test F4 detects mixed work and recommends splitting"""
        result = await detector.suggest_branch_organization(
            detection=detection_mixed_work,
            min_cluster_size=2
        )

        assert result["should_split"] is True
        assert len(result["clusters"]) >= 2
        assert result["current_branch"] == "main"
        assert "suggestion" in result
        assert result["reason"] == "multiple_clusters_detected"

    @pytest.mark.asyncio
    async def test_f4_no_split_focused_work(self, detector, detection_focused_work):
        """Test F4 doesn't suggest split for focused work"""
        result = await detector.suggest_branch_organization(
            detection=detection_focused_work,
            min_cluster_size=2
        )

        assert result["should_split"] is False
        assert result["reason"] in ["single_cluster", "too_few_files"]
        assert result["current_branch"] == "feature/auth"

    @pytest.mark.asyncio
    async def test_f4_too_few_files(self, detector, detection_too_few_files):
        """Test F4 doesn't suggest split for < 3 files"""
        result = await detector.suggest_branch_organization(
            detection=detection_too_few_files,
            min_cluster_size=2
        )

        assert result["should_split"] is False
        assert result["reason"] == "too_few_files"

    # === Clustering Algorithm Tests ===

    def test_cluster_files_by_directory_basic(self, detector):
        """Test directory-based clustering"""
        files = [
            "services/auth/jwt.py",
            "services/auth/session.py",
            "docs/auth.md",
            "docs/api.md"
        ]

        clusters = detector._cluster_files_by_directory(files, min_size=2)

        assert len(clusters) == 2
        # Should have services/auth and docs clusters
        directories = [c["directory"] for c in clusters]
        assert "services/auth" in directories
        assert "docs" in directories

    def test_cluster_files_by_directory_min_size_filter(self, detector):
        """Test min_size filtering removes small clusters"""
        files = [
            "services/auth/jwt.py",
            "services/auth/session.py",
            "services/auth/middleware.py",
            "docs/api.md",  # Only 1 file in docs - below min_size
        ]

        clusters = detector._cluster_files_by_directory(files, min_size=2)

        # Only services/auth cluster should pass (3 files >= 2)
        assert len(clusters) == 1
        assert clusters[0]["directory"] == "services/auth"
        assert clusters[0]["size"] == 3

    def test_cluster_files_sorted_by_size(self, detector):
        """Test clusters are sorted by size (largest first)"""
        files = [
            "docs/api.md",
            "docs/guide.md",
            "services/auth/jwt.py",
            "services/auth/session.py",
            "services/auth/middleware.py",
            "services/auth/tokens.py"
        ]

        clusters = detector._cluster_files_by_directory(files, min_size=2)

        # services/auth (4 files) should come before docs (2 files)
        assert clusters[0]["size"] >= clusters[1]["size"]

    # === Branch Name Generation Tests ===

    def test_generate_branch_name_from_directory(self, detector):
        """Test branch name generation from directory name"""
        cluster = {
            "files": ["services/auth/jwt.py", "services/auth/session.py"],
            "directory": "services/auth",
            "size": 2
        }

        branch_name = detector._generate_branch_name(cluster)

        assert branch_name == "feature/auth"

    def test_generate_branch_name_for_docs(self, detector):
        """Test branch name generation for documentation files"""
        cluster = {
            "files": ["docs/api.md", "docs/guide.md", "README.md"],
            "directory": "docs",
            "size": 3
        }

        branch_name = detector._generate_branch_name(cluster)

        # Should use directory name for docs
        assert branch_name == "feature/docs"

    def test_generate_branch_name_for_md_files_in_root(self, detector):
        """Test branch name generation for .md files in root"""
        cluster = {
            "files": ["README.md", "CONTRIBUTING.md", "LICENSE.md"],
            "directory": "root",
            "size": 3
        }

        branch_name = detector._generate_branch_name(cluster)

        # Should detect all .md files and suggest docs/update
        assert branch_name == "docs/update"

    def test_generate_branch_name_for_python_files_in_root(self, detector):
        """Test branch name generation for Python files in root"""
        cluster = {
            "files": ["test.py", "utils.py"],
            "directory": "root",
            "size": 2
        }

        branch_name = detector._generate_branch_name(cluster)

        assert branch_name == "refactor/python"

    def test_generate_branch_name_for_frontend_files(self, detector):
        """Test branch name generation for frontend files"""
        for ext in ["ts", "tsx", "js", "jsx"]:
            cluster = {
                "files": [f"App.{ext}", f"components.{ext}"],
                "directory": "root",
                "size": 2
            }

            branch_name = detector._generate_branch_name(cluster)
            assert branch_name == "feature/frontend"

    def test_generate_branch_name_fallback(self, detector):
        """Test fallback branch name for mixed file types"""
        cluster = {
            "files": ["file1.txt", "file2.csv", "file3.json"],
            "directory": "root",
            "size": 3
        }

        branch_name = detector._generate_branch_name(cluster)

        assert branch_name == "feature/changes-3-files"

    # === Output Formatting Tests ===

    def test_format_branch_suggestion(self, detector):
        """Test human-readable suggestion formatting"""
        clusters = [
            {
                "name": "feature/auth",
                "files": ["services/auth/jwt.py", "services/auth/session.py"],
                "size": 2,
                "directory": "services/auth"
            },
            {
                "name": "docs/update",
                "files": ["docs/api.md", "README.md"],
                "size": 2,
                "directory": "docs"
            }
        ]

        suggestion = detector._format_branch_suggestion(clusters, "main")

        # Check key elements in output
        assert "💡 Suggestion: Split work into 2 focused branches" in suggestion
        assert "Current: main (4 files mixed)" in suggestion
        assert "feature/auth (2 files)" in suggestion
        assert "docs/update (2 files)" in suggestion
        assert "✓ Clearer commit history" in suggestion
        assert "✓ Easier code review" in suggestion
        assert "✓ Reduced context switching" in suggestion

    def test_format_branch_suggestion_limits_file_display(self, detector):
        """Test suggestion only shows first 5 files per cluster"""
        cluster = {
            "name": "feature/large",
            "files": [f"file{i}.py" for i in range(10)],  # 10 files
            "size": 10,
            "directory": "services"
        }

        suggestion = detector._format_branch_suggestion([cluster], "main")

        # Should show first 5 files + "... and 5 more"
        assert "file0.py" in suggestion
        assert "file4.py" in suggestion
        assert "... and 5 more" in suggestion
        assert "file9.py" not in suggestion  # 10th file shouldn't be shown

    # === Edge Cases ===

    @pytest.mark.asyncio
    async def test_f4_empty_files_list(self, detector):
        """Test F4 with no uncommitted files"""
        detection = {
            "has_uncommitted": False,
            "branch": "main",
            "files": [],
            "file_statuses": [],
            "stats": {"new": 0, "modified": 0, "deleted": 0}
        }

        # This should be caught earlier in the flow, but test defensive handling
        result = await detector.suggest_branch_organization(detection)

        assert result["should_split"] is False
        assert result["reason"] == "too_few_files"

    @pytest.mark.asyncio
    async def test_f4_custom_min_cluster_size(self, detector, detection_mixed_work):
        """Test F4 with custom min_cluster_size"""
        # Increase min_cluster_size to 4 (only services/auth has 4 files)
        result = await detector.suggest_branch_organization(
            detection=detection_mixed_work,
            min_cluster_size=4
        )

        # With min_size=4, docs cluster (3 files) gets filtered out
        # This leaves only 1 cluster (services/auth), so should_split=False
        assert result["should_split"] is False
        assert result["reason"] == "single_cluster"
        # But the cluster info is still available
        assert len(result["clusters"]) in [0, 1]  # May be empty or have the one cluster

    def test_cluster_handles_nested_directories(self, detector):
        """Test clustering with deeply nested directories"""
        files = [
            "services/api/v1/auth/jwt.py",
            "services/api/v1/auth/session.py",
            "services/api/v2/users/profile.py",
            "services/api/v2/users/settings.py"
        ]

        clusters = detector._cluster_files_by_directory(files, min_size=2)

        # Should have 2 clusters (immediate parent directories)
        assert len(clusters) == 2
        directories = [c["directory"] for c in clusters]
        assert "services/api/v1/auth" in directories
        assert "services/api/v2/users" in directories


# === Integration Tests (require real git repo) ===

@pytest.mark.integration
class TestF4Integration:
    """Integration tests requiring real git setup"""

    @pytest.mark.asyncio
    async def test_f4_real_workspace(self, tmp_path):
        """Test F4 with real workspace setup"""
        # Create temporary git repo
        import subprocess
        subprocess.run(["git", "init"], cwd=tmp_path, check=True)

        # Create test files in distinct directories
        (tmp_path / "services").mkdir()
        (tmp_path / "services" / "auth").mkdir(parents=True)
        (tmp_path / "docs").mkdir()

        # Create multiple files in each directory (need min_cluster_size >= 2)
        (tmp_path / "services" / "auth" / "jwt.py").write_text("# JWT module")
        (tmp_path / "services" / "auth" / "session.py").write_text("# Session module")
        (tmp_path / "services" / "auth" / "middleware.py").write_text("# Middleware")
        (tmp_path / "docs" / "api.md").write_text("# API docs")
        (tmp_path / "docs" / "guide.md").write_text("# Guide")

        detector = GitWorkDetector(tmp_path)
        detection = await detector.detect_uncommitted_work()

        assert detection["has_uncommitted"] is True
        # Should have 5 files across 2 directories
        assert len(detection["files"]) == 5

        result = await detector.suggest_branch_organization(detection)

        # Should detect 2 clusters: services/auth (3 files) and docs (2 files)
        assert result["should_split"] is True
        assert len(result["clusters"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
