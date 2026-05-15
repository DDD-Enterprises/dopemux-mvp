"""Prescan influence labels for accepted and rejected router consumers."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

import run_extraction_v5 as runner
from lib.intelligence_router import (
    PRESCAN_ARTIFACT_VERSION,
    IntelligenceRouter,
    build_prescan_source_identity,
)


def _write_file(root: Path, rel_path: str, text: str = "fixture\n") -> Path:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _identity(repo_root: Path, artifact_root: Path) -> dict:
    return build_prescan_source_identity(
        repo_root,
        repo_root,
        git_sha="git-current",
        artifact_root=artifact_root,
        prescan_mode="local_prescan",
    )


def _router_payload(repo_root: Path, artifact_root: Path, *, include_secret_hint: bool = False) -> dict:
    identity = _identity(repo_root, artifact_root)
    summary_hint = (
        "Use the current public summary. SECRET_VALUE_SHOULD_NOT_APPEAR"
        if include_secret_hint
        else "Use the current public summary."
    )
    return {
        "version": "2.0.0",
        "generated_at": "2026-05-14T00:00:00+00:00",
        "repo_root": identity["repo_root"],
        "source_root": identity["source_root"],
        "git_sha": "git-current",
        "corpus_manifest_hash": identity["corpus_manifest_hash"],
        "prescan_artifact_version": PRESCAN_ARTIFACT_VERSION,
        "source_identity": identity,
        "corpus_summary": {"total_included_size_bytes": 100},
        "version_chains": {
            "chain-1": [
                {"path": "docs/old.md", "ordinal": 1, "is_latest": False},
                {"path": "docs/current.md", "ordinal": 2, "is_latest": True},
            ]
        },
        "extraction_hints": {
            "skip_duplicates": ["src/skipped.py"],
            "compress_candidates": [
                {
                    "chain_id": "chain-1",
                    "send_summary_instead": True,
                    "summary_hint": summary_hint,
                }
            ],
        },
        "code_intelligence": {
            "topological_order": ["src/high.py", "src/medium.py", "src/low.py"],
            "dependency_clusters": [["src/high.py", "src/medium.py"]],
        },
        "grok_passes": {
            "optimize": {
                "skip_list": [],
                "phase_routing_overrides": [
                    {"path": "src/high.py", "recommended_phase": "X"}
                ],
                "model_routing_hints": [
                    {
                        "partition_pattern": "src/high.py",
                        "recommended_model": "premium",
                    }
                ],
            }
        },
    }


def _write_router_dir(repo_root: Path, prescan_dir: Path, *, stale_hash: bool = False) -> None:
    payload = _router_payload(repo_root, prescan_dir)
    if stale_hash:
        payload["corpus_manifest_hash"] = "stale"
        payload["source_identity"]["corpus_manifest_hash"] = "stale"
    _write_json(prescan_dir / "prescan_intelligence.json", payload)
    _write_json(
        prescan_dir / "code_intelligence_report.json",
        {
            "processing_order": [
                {"rel_path": "src/high.py", "score": 0.95},
                {"rel_path": "src/medium.py", "score": 0.50},
                {"rel_path": "src/low.py", "score": 0.10},
            ],
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
                ]
            },
            "entry_points": ["src/high.py"],
            "hub_files": [{"rel_path": "src/high.py"}],
            "test_mappings": [],
        },
    )


def _inventory(repo_root: Path) -> list[dict]:
    return [
        {"path": str(repo_root / "src/low.py"), "char_count_estimate": 10},
        {"path": str(repo_root / "src/skipped.py"), "char_count_estimate": 10},
        {"path": str(repo_root / "src/high.py"), "char_count_estimate": 10},
        {"path": str(repo_root / "src/medium.py"), "char_count_estimate": 10},
    ]


def _setup_repo(tmp_path: Path) -> Path:
    repo_root = tmp_path / "repo"
    _write_file(repo_root, "src/low.py")
    _write_file(repo_root, "src/skipped.py")
    _write_file(repo_root, "src/high.py")
    _write_file(repo_root, "src/medium.py")
    _write_file(repo_root, "docs/old.md", "# old\n")
    _write_file(repo_root, "docs/current.md", "# current\n")
    return repo_root


def test_accepted_local_prescan_partition_influence_is_labeled(tmp_path: Path) -> None:
    repo_root = _setup_repo(tmp_path)
    router_obj = IntelligenceRouter(_router_payload(repo_root, tmp_path / "prescan"))
    router_obj.code_report = {
        "processing_order": [
            {"rel_path": "src/high.py", "score": 0.95},
            {"rel_path": "src/medium.py", "score": 0.50},
            {"rel_path": "src/low.py", "score": 0.10},
        ],
        "hotspots": [{"rel_path": "src/high.py", "hotspot_score": 0.90}],
        "pagerank_scores": {"src/high.py": 0.90},
        "signature_index": {},
        "entry_points": [],
        "hub_files": [],
    }

    influence: dict = {}
    partitions = runner.build_partitions(
        "A",
        _inventory(repo_root),
        max_files=4,
        max_chars=1000,
        router=router_obj,
        allow_prescan_scope_reduction=True,
        influence_sink=influence,
    )
    runner._apply_router_partition_hints(
        "A",
        partitions,
        router=router_obj,
        influence_sink=influence,
    )

    assert influence["prescan_mode"] == "local_prescan"
    assert influence["can_influence_execution"] is True
    assert "scope_reduction" in influence["influence_classes"]
    assert "partition_reorder" in influence["influence_classes"]
    assert "tier_override" in influence["influence_classes"]
    assert "routing_model_hint" in influence["influence_classes"]
    assert "phase_hint" in influence["not_applied_influence_classes"]
    assert all(
        "SECRET_VALUE_SHOULD_NOT_APPEAR" not in json.dumps(label, sort_keys=True)
        for label in influence["labels"]
    )


def test_accepted_imported_prescan_labels_imported_mode(tmp_path: Path) -> None:
    repo_root = _setup_repo(tmp_path)
    prescan_dir = tmp_path / "imported"
    _write_router_dir(repo_root, prescan_dir)

    with patch("lib.intelligence_router._git_sha_for_root", return_value="git-current"):
        router_obj, validation = IntelligenceRouter.load_imported(
            prescan_dir,
            current_repo_root=repo_root,
            current_source_root=repo_root,
            current_git_sha="git-current",
        )

    assert router_obj is not None
    assert validation.mode == "imported_prescan_accepted"
    influence: dict = {}
    runner.build_partitions(
        "A",
        _inventory(repo_root),
        max_files=4,
        max_chars=1000,
        router=router_obj,
        allow_prescan_scope_reduction=True,
        influence_sink=influence,
    )

    assert influence["prescan_mode"] == "imported_prescan_accepted"
    assert influence["prescan_verdict"] == "accepted"
    assert influence["can_influence_execution"] is True
    assert "scope_reduction" in influence["influence_classes"]


def test_rejected_stale_prescan_cannot_apply_influence(tmp_path: Path) -> None:
    repo_root = _setup_repo(tmp_path)
    prescan_dir = tmp_path / "stale"
    _write_router_dir(repo_root, prescan_dir, stale_hash=True)

    with patch("lib.intelligence_router._git_sha_for_root", return_value="git-current"):
        router_obj, validation = IntelligenceRouter.load_imported(
            prescan_dir,
            current_repo_root=repo_root,
            current_source_root=repo_root,
            current_git_sha="git-current",
        )

    assert router_obj is None
    assert validation.can_influence_execution is False
    influence: dict = {}
    partitions = runner.build_partitions(
        "A",
        _inventory(repo_root),
        max_files=4,
        max_chars=1000,
        router=router_obj,
        allow_prescan_scope_reduction=True,
        influence_sink=influence,
    )

    assert "scope_reduction" not in influence["influence_classes"]
    assert str(repo_root / "src/skipped.py") in {
        path for partition in partitions for path in partition["paths"]
    }


def test_scope_reduction_requires_explicit_allow_flag(tmp_path: Path) -> None:
    repo_root = _setup_repo(tmp_path)
    router_obj = IntelligenceRouter(_router_payload(repo_root, tmp_path / "prescan"))

    disabled_influence: dict = {}
    disabled = runner.build_partitions(
        "A",
        _inventory(repo_root),
        max_files=4,
        max_chars=1000,
        router=router_obj,
        allow_prescan_scope_reduction=False,
        influence_sink=disabled_influence,
    )
    enabled_influence: dict = {}
    enabled = runner.build_partitions(
        "A",
        _inventory(repo_root),
        max_files=4,
        max_chars=1000,
        router=router_obj,
        allow_prescan_scope_reduction=True,
        influence_sink=enabled_influence,
    )

    disabled_paths = {path for partition in disabled for path in partition["paths"]}
    enabled_paths = {path for partition in enabled for path in partition["paths"]}
    assert str(repo_root / "src/skipped.py") in disabled_paths
    assert str(repo_root / "src/skipped.py") not in enabled_paths
    assert "scope_reduction" in disabled_influence["not_applied_influence_classes"]
    assert "scope_reduction" in enabled_influence["influence_classes"]


def test_compression_hint_label_is_advisory_and_redacted_from_proof(
    tmp_path: Path,
) -> None:
    repo_root = _setup_repo(tmp_path)
    router_obj = IntelligenceRouter(
        _router_payload(repo_root, tmp_path / "prescan", include_secret_hint=True)
    )

    with patch("run_extraction_v5.call_llm", side_effect=AssertionError("provider call")):
        context, stats = runner.build_partition_context(
            phase="A",
            partition_paths=[str(repo_root / "docs/old.md")],
            file_truncate_chars=1000,
            home_scan_mode="safe",
            max_files=5,
            max_chars=10000,
            router=router_obj,
        )

    assert "[PRESCAN COMPRESSION]" in context
    assert stats["compressed_files"] == 1
    proof_text = json.dumps(stats["prescan_influence"], sort_keys=True)
    assert "compression_hint" in proof_text
    assert "SECRET_VALUE_SHOULD_NOT_APPEAR" not in proof_text
    assert stats["prescan_influence"]["labels"][0]["advisory_model_derived"] is True
