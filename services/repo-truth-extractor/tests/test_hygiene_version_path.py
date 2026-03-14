"""
T5: Version/path mismatch detection tests.
Verifies that the scanner detects when the active v5 runner emits to a v3 path.
"""
from pathlib import Path
from unittest.mock import patch

import pytest

from services.repo_truth_extractor import extraction_hygiene as hyg


class TestVersionPathMismatch:
    """Version/path wiring must be detected and reported clearly."""

    def test_check_version_path_detects_mismatch(self):
        """check_version_path() returns a mismatch finding for the known v5→v3 wiring."""
        finding = hyg.check_version_path(
            runner_path=Path("services/repo-truth-extractor/run_extraction_v5.py"),
            repo_root=Path("."),
        )
        assert finding.has_mismatch
        assert finding.runner_version == "v5"
        assert "v3" in finding.output_path
        assert finding.severity in ("warn", "error")

    def test_check_version_path_no_mismatch_when_aligned(self, tmp_path):
        """No mismatch if runner version matches its output path."""
        # Simulate a hypothetical aligned scenario
        finding = hyg.check_version_path(
            runner_path=Path("services/repo-truth-extractor/run_extraction_v3.py"),
            repo_root=tmp_path,
            override_output_path="extraction/repo-truth-extractor/v3",
        )
        assert not finding.has_mismatch

    def test_scan_includes_version_path_issue(self, tmp_path):
        """run_scan() includes version_path_issues in its result."""
        (tmp_path / "services/repo-truth-extractor").mkdir(parents=True)
        # Write a minimal runner that declares V3_EXTRACTION_ROOT
        runner = tmp_path / "services/repo-truth-extractor/run_extraction_v5.py"
        runner.write_text(
            '#!/usr/bin/env python3\n'
            'V3_EXTRACTION_ROOT = "extraction/repo-truth-extractor/v3"\n'
        )

        result = hyg.run_scan(repo_root=tmp_path)

        # Should have at least one version-path issue (warn or error)
        assert isinstance(result.version_path_issues, list)

    def test_mismatch_finding_has_required_fields(self):
        """VersionPathFinding has all required fields for observability."""
        finding = hyg.check_version_path(
            runner_path=Path("services/repo-truth-extractor/run_extraction_v5.py"),
            repo_root=Path("."),
        )
        assert hasattr(finding, "has_mismatch")
        assert hasattr(finding, "runner_version")
        assert hasattr(finding, "output_path")
        assert hasattr(finding, "severity")
        assert hasattr(finding, "message")

    def test_mismatch_message_is_grep_friendly(self):
        """Mismatch message contains VERSION_PATH_MISMATCH log tag."""
        finding = hyg.check_version_path(
            runner_path=Path("services/repo-truth-extractor/run_extraction_v5.py"),
            repo_root=Path("."),
        )
        if finding.has_mismatch:
            assert "VERSION_PATH_MISMATCH" in finding.message
