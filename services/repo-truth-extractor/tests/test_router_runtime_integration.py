from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _v5_smoke_helpers import load_runner_module


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _make_router_from_dir(tmp_path: Path):
    runner = load_runner_module()
    prescan_dir = tmp_path / "prescan"
    _write_json(
        prescan_dir / "prescan_intelligence.json",
        {
            "version": "2.0.0",
            "generated_at": "2026-04-13T00:00:00Z",
            "repo_root": str(tmp_path),
            "corpus_summary": {
                "total_files_scanned": 4,
                "included_files": 4,
                "excluded_files": 0,
                "ghost_files": 0,
                "total_included_size_bytes": 1000,
                "by_authority_class": {"canonical": 4},
                "by_extension": {".py": 4},
                "corpus_health_score": 95,
            },
            "lifecycle_distribution": {"active": 4},
            "duplicate_groups": {},
            "version_chains": {},
            "version_chain_count": 0,
            "compression_potential_files": 0,
            "ghost_files": [],
            "planned_features": {
                "proposed_adrs": [],
                "stub_files": [],
                "todo_files": [],
                "draft_docs": [],
            },
            "extraction_hints": {
                "skip_duplicates": ["src/skipped.py"],
                "high_churn_files": [],
                "compress_candidates": [],
            },
            "code_intelligence": {
                "topological_order": [
                    "src/high.py",
                    "src/medium.py",
                    "src/low.py",
                ],
                "dependency_clusters": [["src/high.py", "src/medium.py"]],
                "api_surfaces": ["fastapi"],
            },
            "grok_passes": {},
        },
    )
    _write_json(
        prescan_dir / "code_intelligence_report.json",
        {
            "processing_order": [
                {"rel_path": "src/medium.py", "score": 0.50},
                {"rel_path": "src/high.py", "score": 0.95},
                {"rel_path": "src/low.py", "score": 0.10},
            ],
            "orphans": [],
            "hotspots": [{"rel_path": "src/high.py", "hotspot_score": 0.90}],
            "pagerank_scores": {
                "src/high.py": 0.90,
                "src/medium.py": 0.50,
                "src/low.py": 0.10,
            },
            "signature_index": {
                "src/high.py": [
                    {
                        "name": "high_priority",
                        "kind": "function",
                        "signature": "def high_priority() -> None",
                        "decorators": ["@app.get('/health')"],
                    }
                ],
            },
            "entry_points": ["src/high.py"],
            "hub_files": [{"rel_path": "src/high.py"}],
            "test_mappings": [],
        },
    )
    router = runner.IntelligenceRouter.from_dir(prescan_dir)
    assert router is not None
    return runner, router


def test_build_partitions_keeps_prescan_skip_candidates_without_explicit_opt_in(
    tmp_path: Path,
) -> None:
    runner, router = _make_router_from_dir(tmp_path)
    inventory = [
        {"path": "src/low.py", "char_count_estimate": 10},
        {"path": "src/skipped.py", "char_count_estimate": 10},
        {"path": "src/high.py", "char_count_estimate": 10},
        {"path": "src/medium.py", "char_count_estimate": 10},
    ]

    partitions = runner.build_partitions(
        "A",
        inventory,
        max_files=2,
        max_chars=1000,
        router=router,
    )

    assert [row["path"] for row in inventory] == [
        "src/low.py",
        "src/skipped.py",
        "src/high.py",
        "src/medium.py",
    ]
    assert partitions[0]["paths"] == ["src/high.py", "src/medium.py"]
    assert partitions[1]["paths"] == ["src/low.py", "src/skipped.py"]
    assert "src/skipped.py" in {
        path for partition in partitions for path in partition["paths"]
    }


def test_build_partitions_allows_prescan_skip_candidates_only_with_opt_in(
    tmp_path: Path,
) -> None:
    runner, router = _make_router_from_dir(tmp_path)
    inventory = [
        {"path": "src/low.py", "char_count_estimate": 10},
        {"path": "src/skipped.py", "char_count_estimate": 10},
        {"path": "src/high.py", "char_count_estimate": 10},
        {"path": "src/medium.py", "char_count_estimate": 10},
    ]

    partitions = runner.build_partitions(
        "A",
        inventory,
        max_files=2,
        max_chars=1000,
        router=router,
        allow_prescan_scope_reduction=True,
    )

    assert partitions[0]["paths"] == ["src/high.py", "src/medium.py"]
    assert partitions[1]["paths"] == ["src/low.py"]
    assert "src/skipped.py" not in {
        path for partition in partitions for path in partition["paths"]
    }


def test_apply_router_partition_hints_reorders_paths_and_adds_brief(
    tmp_path: Path,
) -> None:
    runner, router = _make_router_from_dir(tmp_path)
    partitions = [
        {
            "id": "A_P0001",
            "paths": ["src/medium.py", "src/high.py", "src/low.py"],
            "file_count": 3,
            "char_count_estimate": 60,
        }
    ]

    updated = runner._apply_router_partition_hints("A", partitions, router=router)

    assert updated is partitions
    assert updated[0]["paths"] == ["src/high.py", "src/medium.py", "src/low.py"]
    assert updated[0]["context_brief"]
    assert "high_priority" in updated[0]["context_brief"]
