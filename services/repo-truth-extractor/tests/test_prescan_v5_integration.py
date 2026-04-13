"""Integration tests: Prescan output → Run_Extraction_V5 consumption."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from lib.intelligence_router import IntelligenceRouter
from lib.prescan.engine import PrescanEngine
from lib.prescan.models import FileEntry, PrescanConfig


def _make_sample_prescan_output(tmp_path: Path) -> dict:
    """Generate a minimal but complete prescan_intelligence.json."""
    return {
        "version": "2.0.0",
        "generated_at": "2026-04-11T12:00:00+00:00",
        "repo_root": str(tmp_path),
        "corpus_summary": {
            "total_files_scanned": 10,
            "included_files": 8,
            "excluded_files": 1,
            "ghost_files": 1,
            "total_included_size_bytes": 50000,
            "by_authority_class": {"canonical": 8, "ghost": 1, "support": 1},
            "by_extension": {".py": 5, ".md": 3},
            "corpus_health_score": 85,
        },
        "lifecycle_distribution": {
            "active": 5,
            "stale": 2,
            "frozen": 1,
            "unknown": 2,
        },
        "duplicate_groups": {
            "dup-001": ["src/old_impl.py", "src/legacy_impl.py"],
        },
        "version_chains": {
            "chain-v1": [
                {"path": "docs/guide-v1.md", "ordinal": 1, "is_latest": False},
                {"path": "docs/guide-v2.md", "ordinal": 2, "is_latest": True},
            ]
        },
        "version_chain_count": 1,
        "compression_potential_files": 1,
        "ghost_files": [
            {
                "path": "removed-feature.py",
                "deleted_at_sha": "abc123",
                "deleted_date": "2026-03-01",
                "recovery_source": "git_history",
            }
        ],
        "planned_features": {
            "proposed_adrs": ["docs/90-adr/ADR-001.md"],
            "stub_files": ["src/feature_stub.py"],
            "todo_files": ["src/feature_wip.py"],
            "draft_docs": ["docs/draft-feature.md"],
        },
        "extraction_hints": {
            "skip_duplicates": ["src/old_impl.py"],
            "high_churn_files": ["src/frequently_changed.py"],
            "compress_candidates": [],
        },
        "code_intelligence": {
            "analyzed_files": 5,
            "api_surfaces": ["api.main", "api.v2", "db.session"],
            "dependency_clusters": [
                ["src/auth.py", "src/session.py"],
                ["src/db.py", "src/models.py"],
            ],
            "topological_order": ["src/db.py", "src/models.py", "src/auth.py", "src/session.py", "src/api.py"],
        },
        "grok_passes": {
            "dedup": {
                "skipped_files": ["src/old_impl.py"],
                "summary": "Identified 1 duplicate file",
            },
            "discover": {
                "new_features": ["feature_auth_v2"],
                "summary": "Discovered 1 new feature",
            },
        },
        "cost_estimate": {
            "total_tokens_estimated": 150000,
            "estimated_cost_usd": 2.50,
        },
    }


def test_intelligence_router_loads_prescan_output(tmp_path: Path) -> None:
    """Verify IntelligenceRouter can load and parse prescan output."""
    intel = _make_sample_prescan_output(tmp_path)

    router = IntelligenceRouter(intel)

    assert router.intel is intel
    assert router.skip_list == {"src/old_impl.py"}
    assert len(router.topological_order) == 5
    assert router._grok_skip_list == set()  # No optimize pass result yet


def test_intelligence_router_from_dir(tmp_path: Path) -> None:
    """Verify IntelligenceRouter.from_dir() loads from a prescan output directory."""
    intel_data = _make_sample_prescan_output(tmp_path)
    intel_path = tmp_path / "prescan_intelligence.json"
    intel_path.write_text(json.dumps(intel_data))

    router = IntelligenceRouter.from_dir(tmp_path)

    assert router is not None
    assert router.intel["version"] == "2.0.0"
    assert router.skip_list == {"src/old_impl.py"}


def test_prescan_engine_output_keys_required_by_v5(tmp_path: Path) -> None:
    """Verify PrescanEngine._build_intelligence_base() outputs all keys IntelligenceRouter expects."""
    config = PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        enable_code_prescan=False,
        enable_git_enrichment=False,
        batch_mode=False,
    )
    engine = PrescanEngine(config)

    entries = [
        FileEntry(rel_path="src/main.py", size_bytes=100, extension=".py", authority_class="canonical"),
        FileEntry(rel_path="docs/README.md", size_bytes=50, extension=".md", authority_class="canonical"),
        FileEntry(
            rel_path="removed.py",
            size_bytes=0,
            extension=".py",
            authority_class="ghost",
            is_ghost=True,
            deleted_at_sha="abc",
            deleted_date="2026-03-01",
            recovery_source="git_history",
        ),
    ]

    intelligence = engine._build_intelligence_base(entries)

    # Verify keys that IntelligenceRouter expects (and v5 may use)
    required_keys = {
        "version",
        "generated_at",
        "repo_root",
        "corpus_summary",
        "lifecycle_distribution",
        "ghost_files",
        "planned_features",
        "version_chain_count",
        "compression_potential_files",
        "extraction_hints",
    }

    missing = required_keys - set(intelligence.keys())
    assert not missing, f"Missing keys in intelligence output: {missing}"

    # Verify structure
    assert intelligence["corpus_summary"]["ghost_files"] == 1
    assert len(intelligence["ghost_files"]) == 1
    assert intelligence["ghost_files"][0]["path"] == "removed.py"
    assert intelligence["lifecycle_distribution"] is not None
    assert intelligence["planned_features"]["proposed_adrs"] == []


def test_grok_passes_result_structure_compatible_with_router(tmp_path: Path) -> None:
    """Verify grok pass results can be loaded by IntelligenceRouter."""
    intel = _make_sample_prescan_output(tmp_path)

    # Simulate optimize pass result (which may be added by grok_passes)
    intel["grok_passes"]["optimize"] = {
        "skip_list": ["src/generated.py"],
        "compress_chains": [
            {
                "chain_id": "chain-v1",
                "send_summary_instead": True,
                "summary": "See v2",
            }
        ],
        "phase_routing_overrides": [
            {
                "path": "src/api.py",
                "recommended_phase": "phase2",
            }
        ],
        "model_routing_hints": [
            {
                "file_class": "api",
                "suggested_model": "gpt-5-codex",
            }
        ],
    }

    router = IntelligenceRouter(intel)

    # Router should have loaded optimize results
    assert "src/generated.py" in router.skip_list
    assert "src/old_impl.py" in router.skip_list  # Original skip list
    assert router._phase_routing.get("src/api.py") == "phase2"
    assert len(router._model_routing) == 1


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
