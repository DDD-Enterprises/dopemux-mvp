"""Imported prescan identity validation and receipt safety tests."""

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


def _write_file(root: Path, rel_path: str, text: str = "fixture\n") -> None:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _make_runner_config(import_dir: Path | None = None) -> runner.RunnerConfig:
    return runner.RunnerConfig(
        dry_run=True,
        max_files_docs=35,
        max_files_code=20,
        max_chars=650000,
        max_request_bytes=200000,
        file_truncate_chars=70000,
        home_scan_mode="safe",
        resume=False,
        fail_fast_auth=True,
        gemini_auth_mode="auto",
        gemini_transport="sdk",
        openai_transport="openai_sdk",
        xai_transport="openai_sdk",
        retry_policy="default",
        retry_max_attempts=1,
        retry_base_seconds=0.0,
        retry_max_seconds=0.0,
        phase_auth_fail_threshold=1,
        partition_workers=1,
        debug_phase_inputs=False,
        fail_fast_missing_inputs=False,
        routing_policy="cost",
        batch_mode=False,
        live_ok=False,
        prescan_skip=False,
        prescan_online=False,
        allow_online_llm=False,
        prescan_import_dir=str(import_dir) if import_dir else None,
        prescan_allow_scope_reduction=True,
    )


def _write_import(
    import_dir: Path,
    repo_root: Path,
    *,
    overrides: dict | None = None,
    include_identity: bool = True,
    git_sha: str = "git-current",
) -> dict:
    import_dir.mkdir(parents=True, exist_ok=True)
    identity = build_prescan_source_identity(
        repo_root,
        repo_root,
        git_sha=git_sha,
        artifact_root=import_dir,
        prescan_mode="local_prescan",
    )
    payload = {
        "code_intelligence": {},
        "corpus_manifest_hash": identity["corpus_manifest_hash"],
        "corpus_summary": {"total_included_size_bytes": 0},
        "extraction_hints": {
            "compress_candidates": [],
            "skip_duplicates": ["src/stale_skip.py"],
        },
        "generated_at": "2026-05-14T00:00:00+00:00",
        "git_sha": git_sha,
        "prescan_artifact_version": PRESCAN_ARTIFACT_VERSION,
        "repo_root": identity["repo_root"],
        "source_root": identity["source_root"],
        "version": "1.0",
    }
    if include_identity:
        payload["source_identity"] = identity
    if overrides:
        payload.update(overrides)
    (import_dir / "prescan_intelligence.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def test_imported_prescan_with_matching_source_identity_is_accepted(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_file(repo_root, "src/app.py", "def app():\n    return 1\n")
    import_dir = tmp_path / "import"
    _write_import(import_dir, repo_root)

    router_obj, validation = IntelligenceRouter.load_imported(
        import_dir,
        current_repo_root=repo_root,
        current_source_root=repo_root,
        current_git_sha="git-current",
    )

    assert router_obj is not None
    assert validation.verdict == "accepted"
    assert validation.can_influence_execution is True
    assert validation.advisory_only is False
    assert router_obj.should_skip("src/stale_skip.py") is True


def test_imported_prescan_with_mismatched_repo_root_is_rejected(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_file(repo_root, "src/app.py", "def app():\n    return 1\n")
    import_dir = tmp_path / "import"
    _write_import(import_dir, repo_root, overrides={"repo_root": str(tmp_path / "other")})

    router_obj, validation = IntelligenceRouter.load_imported(
        import_dir,
        current_repo_root=repo_root,
        current_source_root=repo_root,
        current_git_sha="git-current",
    )

    assert router_obj is None
    assert validation.verdict == "rejected_stale"
    assert "repo_root_mismatch" in validation.reason_codes
    assert validation.can_influence_execution is False


def test_imported_prescan_with_mismatched_corpus_manifest_hash_is_rejected(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    _write_file(repo_root, "src/app.py", "def app():\n    return 1\n")
    import_dir = tmp_path / "import"
    _write_import(import_dir, repo_root, overrides={"corpus_manifest_hash": "stale"})

    router_obj, validation = IntelligenceRouter.load_imported(
        import_dir,
        current_repo_root=repo_root,
        current_source_root=repo_root,
        current_git_sha="git-current",
    )

    assert router_obj is None
    assert validation.verdict == "rejected_stale"
    assert "corpus_manifest_hash_mismatch" in validation.reason_codes
    assert validation.can_influence_execution is False


def test_imported_prescan_missing_required_identity_is_non_authoritative(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    _write_file(repo_root, "src/app.py", "def app():\n    return 1\n")
    import_dir = tmp_path / "import"
    import_dir.mkdir(parents=True)
    (import_dir / "prescan_intelligence.json").write_text(
        json.dumps({"extraction_hints": {"skip_duplicates": ["src/app.py"]}}),
        encoding="utf-8",
    )

    router_obj, validation = IntelligenceRouter.load_imported(
        import_dir,
        current_repo_root=repo_root,
        current_source_root=repo_root,
        current_git_sha="git-current",
    )

    assert router_obj is None
    assert validation.mode == "imported_prescan_missing_metadata"
    assert validation.verdict == "missing_metadata"
    assert "missing_repo_root" in validation.reason_codes
    assert "missing_corpus_manifest_hash" in validation.reason_codes
    assert validation.can_influence_execution is False


def test_invalid_prescan_artifact_is_rejected(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    _write_file(repo_root, "src/app.py", "def app():\n    return 1\n")
    import_dir = tmp_path / "import"
    import_dir.mkdir(parents=True)
    (import_dir / "prescan_intelligence.json").write_text("{not-json", encoding="utf-8")

    validation = IntelligenceRouter.validate_import_dir(
        import_dir,
        current_repo_root=repo_root,
        current_source_root=repo_root,
        current_git_sha="git-current",
    )

    assert validation.verdict == "rejected_stale"
    assert "prescan_intelligence_parse_failed" in validation.reason_codes
    assert validation.can_influence_execution is False


def test_accepted_import_receipt_records_identity_and_influence(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    run_root = tmp_path / "run"
    _write_file(repo_root, "src/app.py", "def app():\n    return 1\n")
    import_dir = tmp_path / "import"
    _write_import(import_dir, repo_root)
    cfg = _make_runner_config(import_dir)

    with patch("run_extraction_v5.get_git_sha", return_value="git-current"):
        router_obj = runner.run_integrated_prescan_stage(repo_root, run_root, cfg)

    receipt = json.loads((run_root / "prescan" / "prescan_stage_receipt.json").read_text())
    assert router_obj is not None
    assert receipt["mode"] == "imported_prescan_accepted"
    assert receipt["verdict"] == "accepted"
    assert receipt["can_influence_execution"] is True
    assert receipt["advisory_only"] is False
    assert receipt["repo_root_current"] == receipt["repo_root_imported_if_present"]
    assert receipt["source_root_current"] == receipt["source_root_imported_if_present"]
    assert receipt["corpus_manifest_hash_current_if_available"] == receipt[
        "corpus_manifest_hash_imported_if_present"
    ]


def test_rejected_import_receipt_blocks_scope_reduction_and_router(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    run_root = tmp_path / "run"
    _write_file(repo_root, "src/app.py", "def app():\n    return 1\n")
    import_dir = tmp_path / "import"
    _write_import(import_dir, repo_root, overrides={"corpus_manifest_hash": "stale"})
    cfg = _make_runner_config(import_dir)

    with patch("run_extraction_v5.get_git_sha", return_value="git-current"):
        router_obj = runner.run_integrated_prescan_stage(repo_root, run_root, cfg)

    receipt = json.loads((run_root / "prescan" / "prescan_stage_receipt.json").read_text())
    assert router_obj is None
    assert receipt["mode"] == "imported_prescan_rejected_stale"
    assert receipt["verdict"] == "rejected_stale"
    assert receipt["can_influence_execution"] is False
    assert receipt["advisory_only"] is True
    assert receipt["scope_reduction_applied"] is False
    assert "corpus_manifest_hash_mismatch" in receipt["reason_codes"]


def test_import_validation_is_local_only(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    run_root = tmp_path / "run"
    _write_file(repo_root, "src/app.py", "def app():\n    return 1\n")
    import_dir = tmp_path / "import"
    _write_import(import_dir, repo_root)
    cfg = _make_runner_config(import_dir)

    with patch("run_extraction_v5.get_git_sha", return_value="git-current"), patch(
        "lib.prescan.engine.PrescanEngine.run",
        side_effect=AssertionError("local prescan should not run for import validation"),
    ):
        router_obj = runner.run_integrated_prescan_stage(repo_root, run_root, cfg)

    assert router_obj is not None

