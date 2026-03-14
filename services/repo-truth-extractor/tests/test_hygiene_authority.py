"""
T4: Authority classification tests.
Verifies that representative paths classify into correct authority tiers.
"""
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


class TestAuthorityClassification:
    """Paths must map to the correct authority tier."""

    # --- canonical tier ---
    @pytest.mark.parametrize("path", [
        "compose.yml",
        "pyproject.toml",
        "dopemux.toml",
        "src/dopemux/cli.py",
        "services/task-orchestrator/server.py",
        "services/registry.yaml",
        ".claude/CLAUDE.md",
        ".github/workflows/ci.yml",
        "config/extraction_hygiene/hygiene_policy.yaml",
        "AGENTS.md",
        "README.md",
        "INSTALL.md",
        "QUICK_START.md",
    ])
    def test_canonical_paths(self, path):
        tier = hyg.classify_authority(path)
        assert tier == "canonical", f"{path!r} should be canonical, got {tier!r}"

    # --- reference tier ---
    @pytest.mark.parametrize("path", [
        "docs/03-reference/repo_truth_extractor_pipeline_phases.md",
        "docs/02-how-to/deploy-stack.md",
        "docs/04-explanation/serena_v2.md",
        "services/task-orchestrator/README.md",
        "CHANGELOG.md",
        "docs/00-MASTER-INDEX.md",
        "docs/docs_index.yaml",
    ])
    def test_reference_paths(self, path):
        tier = hyg.classify_authority(path)
        assert tier == "reference", f"{path!r} should be reference, got {tier!r}"

    # --- status_audit tier ---
    @pytest.mark.parametrize("path", [
        "AUDIT_INITIAL_FINDINGS.md",
        "AUDIT_RESULTS.json",
        "docs/05-audit-reports/some-audit.md",
        "reports/CONCURRENCY_RISK_LOCATIONS.json",
        "reports/ENV_VARS.json",
        "repo-truth-pack/conport/surfaces.json",
        "review_artifacts/A0__A_P0001.json",
    ])
    def test_status_audit_paths(self, path):
        tier = hyg.classify_authority(path)
        assert tier == "status_audit", f"{path!r} should be status_audit, got {tier!r}"

    # --- roadmap_speculative tier ---
    @pytest.mark.parametrize("path", [
        "UPGRADES/FULL_PIPELINE_OVERVIEW.md",
        "docs/archive/session_notes/some-note.md",
        "task-packets/TP-HYGIENE-0001.md",
        "contracts/some-contract.yaml",
    ])
    def test_roadmap_speculative_paths(self, path):
        tier = hyg.classify_authority(path)
        assert tier == "roadmap_speculative", (
            f"{path!r} should be roadmap_speculative, got {tier!r}"
        )

    # --- generated tier ---
    @pytest.mark.parametrize("path", [
        "proof/TP5A-conport/COMPLETION_REPORT.md",
        "extraction/repo-truth-extractor/v3/runs/FULL_RUN/A_repo_control_plane/raw/A0__A_P0001.json",
        "extraction/repo-truth-extractor/v4/runs/v4_full_run_0504/RUN_MANIFEST.json",
        "extraction/repo-truth-extractor/v5/proofs/TP-GROK-0001/CHANGESET_MAP.md",
        "extraction/repo-truth-extractor/quarantine/20260314T050000Z/some.json",
        "htmlcov/index.html",
        "tmp/gate_v25_full/run/output.json",
        "out/request_0.txt",
        "SYSTEM_ARCHIVE/serena-legacy/server.py",
        "src/dopemux/__pycache__/cli.cpython-311.pyc",
        ".venv/lib/python3.11/site-packages/click/__init__.py",
        "node_modules/dep/README.md",
        "vendor/some-dep/README.md",
    ])
    def test_generated_paths(self, path):
        tier = hyg.classify_authority(path)
        assert tier == "generated", f"{path!r} should be generated, got {tier!r}"

    def test_authority_summary_in_scan_result(self, tmp_path):
        """Scan result includes an authority_summary dict with tier counts."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src/cli.py").write_text("# code")
        (tmp_path / "reports").mkdir()
        (tmp_path / "reports/output.json").write_text("{}")

        result = hyg.run_scan(repo_root=tmp_path)

        assert isinstance(result.authority_summary, dict)
        # At minimum the tiers should be keys
        for tier in ("canonical", "reference", "status_audit", "roadmap_speculative", "generated"):
            assert tier in result.authority_summary
