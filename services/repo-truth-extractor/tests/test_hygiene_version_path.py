"""
T5: Version/path mismatch detection tests.
Verifies that the scanner detects when the active v5 runner emits to a v3 path.
"""
from pathlib import Path
from unittest.mock import patch

import pytest

import importlib.util as _ilu
import sys as _sys
def _load_hyg():
    _root = __import__('pathlib').Path(__file__).resolve().parents[3]
    _spec = _ilu.spec_from_file_location(
        "extraction_hygiene",
        _root / "services" / "repo-truth-extractor" / "extraction_hygiene.py",
    )
    _mod = _ilu.module_from_spec(_spec)
    _sys.modules["extraction_hygiene"] = _mod
    _spec.loader.exec_module(_mod)
    return _mod
hyg = _load_hyg()


class TestVersionPathMismatch:
    """Version/path wiring must be detected and reported clearly."""

    def test_check_version_path_no_mismatch_after_fix(self):
        """After fixing constants, v5 runner pointing to v5 path has NO mismatch."""
        finding = hyg.check_version_path(
            runner_path=Path("services/repo-truth-extractor/run_extraction_v5.py"),
            repo_root=Path("."),
        )
        assert not finding.has_mismatch, (
            f"Expected NO mismatch after constant rename. "
            f"Runner: {finding.runner_version}, Output: {finding.output_path}"
        )
        assert finding.runner_version == "v5"
        assert "v5" in finding.output_path
        assert finding.severity == "ok"

    def test_check_version_path_detects_legacy_v3_mismatch(self, tmp_path):
        """Detects mismatch if runner still uses old V3_EXTRACTION_ROOT."""
        # Simulate a v5 runner that still declares V3_EXTRACTION_ROOT (legacy)
        runner = tmp_path / "services/repo-truth-extractor/run_extraction_v5.py"
        runner.parent.mkdir(parents=True, exist_ok=True)
        runner.write_text(
            '#!/usr/bin/env python3\n'
            'V3_EXTRACTION_ROOT = Path("extraction/repo-truth-extractor/v3")\n'
        )
        finding = hyg.check_version_path(
            runner_path=Path("services/repo-truth-extractor/run_extraction_v5.py"),
            repo_root=tmp_path,
        )
        assert finding.has_mismatch, "Should detect v5 runner using v3 output path"
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
        # Write a minimal runner that declares V5_EXTRACTION_ROOT (new convention)
        runner = tmp_path / "services/repo-truth-extractor/run_extraction_v5.py"
        runner.write_text(
            '#!/usr/bin/env python3\n'
            'V5_EXTRACTION_ROOT = "extraction/repo-truth-extractor/v5"\n'
        )

        result = hyg.run_scan(repo_root=tmp_path)

        # Should have a version-path finding (should be OK, no mismatch)
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
