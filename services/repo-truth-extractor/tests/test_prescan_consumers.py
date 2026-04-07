from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from lib.intelligence_router import IntelligenceRouter
from lib.promptgen.feature_detector import detect_features


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_intelligence_router_from_dir_accepts_expanded_prescan_contract(tmp_path: Path) -> None:
    prescan_dir = tmp_path / "prescan"
    _write_json(
        prescan_dir / "prescan_intelligence.json",
        {
            "version": "2.0.0",
            "generated_at": "2026-04-07T00:00:00Z",
            "repo_root": str(tmp_path),
            "corpus_summary": {
                "total_files_scanned": 4,
                "included_files": 3,
                "excluded_files": 1,
                "ghost_files": 1,
                "total_included_size_bytes": 123,
                "by_authority_class": {"canonical": 3},
                "by_extension": {".py": 2, ".md": 1},
                "corpus_health_score": 90,
            },
            "lifecycle_distribution": {"fresh": 1, "active": 2, "unknown": 1},
            "duplicate_groups": {},
            "version_chains": {
                "chain-1": [
                    {"path": "docs/v1.md", "ordinal": 1, "is_latest": False},
                    {"path": "docs/v2.md", "ordinal": 2, "is_latest": True},
                ]
            },
            "version_chain_count": 1,
            "compression_potential_files": 1,
            "ghost_files": [
                {
                    "path": "docs/deleted.md",
                    "deleted_at_sha": "deadbeef",
                    "deleted_date": "2026-04-01",
                    "recovery_source": "git_history",
                }
            ],
            "planned_features": {
                "proposed_adrs": ["docs/90-adr/ADR-001.md"],
                "stub_files": ["src/stub.py"],
                "todo_files": ["src/todo.py"],
                "draft_docs": ["docs/draft.md"],
            },
            "extraction_hints": {
                "skip_duplicates": ["docs/v1.md"],
                "high_churn_files": ["src/hot.py"],
                "compress_candidates": [
                    {
                        "chain_id": "chain-1",
                        "send_summary_instead": True,
                        "summary_hint": "Use latest version summary.",
                    }
                ],
            },
            "code_intelligence": {
                "topological_order": ["src/core.py", "src/app.py"],
                "dependency_clusters": [["src/core.py", "src/app.py"]],
                "api_surfaces": ["fastapi", "mcp"],
            },
            "grok_passes": {
                "optimize": {
                    "skip_list": ["src/generated.py"],
                    "compress_chains": [
                        {
                            "chain_id": "chain-1",
                            "send_summary_instead": True,
                            "summary_hint": "Use latest version summary.",
                        }
                    ],
                    "phase_routing_overrides": [
                        {"path": "docs/90-adr/ADR-001.md", "recommended_phase": "X"}
                    ],
                    "model_routing_hints": [
                        {
                            "partition_pattern": "src/*.py",
                            "recommended_model": "premium",
                        }
                    ],
                }
            },
        },
    )
    _write_json(
        prescan_dir / "code_intelligence_report.json",
        {
            "processing_order": [
                {"rel_path": "src/core.py", "score": 0.9},
                {"rel_path": "src/app.py", "score": 0.8},
            ],
            "orphans": [
                {"rel_path": "src/dead.py", "confidence": 0.8},
                {"rel_path": "src/maybe.py", "confidence": 0.5},
            ],
            "hotspots": [{"rel_path": "src/core.py", "hotspot_score": 0.95}],
            "pagerank_scores": {"src/core.py": 0.9, "src/app.py": 0.2},
            "test_mappings": [
                {"source_path": "src/core.py", "test_path": "tests/test_core.py"}
            ],
        },
    )

    router = IntelligenceRouter.from_dir(prescan_dir)

    assert router is not None
    assert router.should_skip("docs/v1.md") is True
    assert router.should_skip("src/generated.py") is True
    assert router.get_compression_hint("docs/v1.md") == "Use latest version summary."
    assert router.get_phase_routing_override("docs/90-adr/ADR-001.md") == "X"
    assert router.get_model_tier("src/core.py") == "premium"
    assert router.should_skip_code("src/dead.py") is True
    assert router.should_skip_code("src/maybe.py") is False
    assert router.get_test_file("src/core.py") == "tests/test_core.py"
    assert router.get_bundling_group("src/app.py") == "cluster_0"


def test_feature_detector_consumes_prescan_api_surfaces_for_confidence_boost(tmp_path: Path) -> None:
    (tmp_path / "api_server.py").write_text("def placeholder():\n    return None\n", encoding="utf-8")
    (tmp_path / "mcp_tool.py").write_text("def placeholder_tool():\n    return None\n", encoding="utf-8")

    payload = detect_features(
        root=tmp_path,
        run_id="prescan-consumer-test",
        prescan_intelligence={
            "code_intelligence": {
                "api_surfaces": ["http_api_route", "mcp"],
            }
        },
    )

    feature_index = {item["feature_id"]: item for item in payload["detected_features"]}

    assert feature_index["http_api_python"]["confidence"] == "high"
    assert "prescan:api_surface_detected" in feature_index["http_api_python"]["content_evidence"]
    assert feature_index["mcp_tools"]["confidence"] == "high"
    assert "prescan:mcp_surface_detected" in feature_index["mcp_tools"]["content_evidence"]
