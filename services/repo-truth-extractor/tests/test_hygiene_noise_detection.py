"""
T1: Noise-path detection tests.
Verifies that known junk roots are flagged by the hygiene scanner.
"""
import fnmatch
from pathlib import Path

import pytest

# Import the module under test (will fail until extraction_hygiene.py exists)
from services.repo_truth_extractor import extraction_hygiene as hyg


REPO_ROOT = Path(__file__).parents[3]


class TestNoisyPathDetection:
    """Verify scanner correctly flags paths that must not enter extraction."""

    def test_node_modules_readme_is_flagged(self):
        result = hyg.classify_path(
            "services/dopecon-bridge/node_modules/prebuild-install/README.md"
        )
        assert result.is_excluded, "node_modules README must be excluded"
        assert result.category == "vendored_deps"

    def test_pycache_is_flagged(self):
        result = hyg.classify_path("src/dopemux/__pycache__/cli.cpython-311.pyc")
        assert result.is_excluded
        assert result.category == "build_cache"

    def test_venv_is_flagged(self):
        result = hyg.classify_path(".venv/lib/python3.11/site-packages/anyio/__init__.py")
        assert result.is_excluded
        assert result.category == "virtualenv"

    def test_dist_artifact_is_flagged(self):
        result = hyg.classify_path("services/some-service/dist/index.js")
        assert result.is_excluded
        assert result.category == "build_artifact"

    def test_build_artifact_is_flagged(self):
        result = hyg.classify_path("ui-dashboard/build/static/main.js")
        assert result.is_excluded
        assert result.category == "build_artifact"

    def test_v3_run_output_is_flagged(self):
        result = hyg.classify_path(
            "extraction/repo-truth-extractor/v3/runs/FULL_RUN/A_repo_control_plane/raw/A0__A_P0001.json"
        )
        assert result.is_excluded
        assert result.category == "run_output"

    def test_v4_run_output_is_flagged(self):
        result = hyg.classify_path(
            "extraction/repo-truth-extractor/v4/runs/v4_full_run_0504/A_repo_control_plane/raw/A0__A_P0001.json"
        )
        assert result.is_excluded
        assert result.category == "run_output"

    def test_proof_bundle_is_flagged(self):
        result = hyg.classify_path(
            "extraction/repo-truth-extractor/v5/proofs/TP-RTX-GROK-0001/CHANGESET_MAP.md"
        )
        assert result.is_excluded
        assert result.category == "proof_bundle"

    def test_quarantine_is_flagged(self):
        result = hyg.classify_path(
            "extraction/repo-truth-extractor/quarantine/20260314T050000Z/some_file.json"
        )
        assert result.is_excluded
        assert result.category == "quarantine"

    def test_htmlcov_is_flagged(self):
        result = hyg.classify_path("htmlcov/index.html")
        assert result.is_excluded

    def test_canonical_source_not_flagged(self):
        result = hyg.classify_path("src/dopemux/cli.py")
        assert not result.is_excluded

    def test_compose_yml_not_flagged(self):
        result = hyg.classify_path("compose.yml")
        assert not result.is_excluded

    def test_scan_returns_warnings_for_noise_dirs(self, tmp_path):
        """Integration: scan a tree with known junk dirs and expect WARN entries."""
        # Build a minimal fake repo tree
        (tmp_path / "src/dopemux").mkdir(parents=True)
        (tmp_path / "src/dopemux/cli.py").write_text("# code")
        (tmp_path / "node_modules/dep/README.md").mkdir(parents=True, exist_ok=True) or None
        (tmp_path / "node_modules/dep").mkdir(parents=True, exist_ok=True)
        (tmp_path / "node_modules/dep/README.md").write_text("# dep")
        (tmp_path / ".venv/lib").mkdir(parents=True)
        (tmp_path / ".venv/lib/module.py").write_text("# venv")

        result = hyg.run_scan(repo_root=tmp_path)

        warn_paths = [w.path for w in result.warnings]
        assert any("node_modules" in str(p) for p in warn_paths), (
            "node_modules should generate a HYGIENE_WARN"
        )
