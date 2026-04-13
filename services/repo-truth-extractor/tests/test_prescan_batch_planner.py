from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from lib.prescan.batch_planner import BatchPlanner
from lib.prescan.models import FileEntry, PrescanConfig


def _make_config(tmp_path: Path) -> PrescanConfig:
    return PrescanConfig(
        repo_root=tmp_path,
        output_dir=tmp_path / "out",
        enable_code_prescan=False,
        enable_git_enrichment=False,
        batch_mode=True,
        max_tokens_per_batch=100,
        chars_per_token=1.0,
    )


def test_batch_planner_splits_batches_by_authority_class_and_budget(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path,
) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "docs" / "a.md").write_text("a" * 30, encoding="utf-8")
    (tmp_path / "docs" / "b.md").write_text("b" * 30, encoding="utf-8")
    (tmp_path / "src" / "todo.py").write_text("c" * 30, encoding="utf-8")

    entries = [
        FileEntry(
            rel_path="docs/a.md",
            size_bytes=30,
            extension=".md",
            authority_class="canonical",
            lifecycle_stage="frozen",
        ),
        FileEntry(
            rel_path="docs/b.md",
            size_bytes=30,
            extension=".md",
            authority_class="canonical",
            lifecycle_stage="stale",
        ),
        FileEntry(
            rel_path="src/todo.py",
            size_bytes=30,
            extension=".py",
            authority_class="historical",
            lifecycle_stage="stale",
        ),
    ]
    manifest = [entry.to_dict() for entry in entries]
    monkeypatch.setattr(
        "lib.prescan.batch_planner.estimate_payload_overhead", lambda pass_id: 10
    )
    monkeypatch.setattr(
        "lib.prescan.batch_planner.estimate_file_tokens",
        lambda file_path, chars_per_token=4.0: 30,
    )
    planner = BatchPlanner(_make_config(tmp_path), entries, manifest)

    plan = planner.plan_batches(
        "discover",
        intelligence={},
    )

    assert [batch.authority_classes for batch in plan.batches] == [
        ["canonical"],
        ["historical"],
    ]
    assert plan.total_files == 3
    assert plan.total_estimated_tokens > 0
def test_batch_planner_excludes_oversized_files_from_batches(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "topic-v1.md").write_text("a" * 95, encoding="utf-8")
    (tmp_path / "docs" / "topic-v2.md").write_text("b" * 20, encoding="utf-8")

    entries = [
        FileEntry(
            rel_path="docs/topic-v1.md",
            size_bytes=95,
            extension=".md",
            authority_class="canonical",
        ),
        FileEntry(
            rel_path="docs/topic-v2.md",
            size_bytes=20,
            extension=".md",
            authority_class="canonical",
        ),
    ]
    manifest = [entry.to_dict() for entry in entries]
    monkeypatch.setattr(
        "lib.prescan.batch_planner.estimate_payload_overhead", lambda pass_id: 10
    )
    monkeypatch.setattr(
        "lib.prescan.batch_planner.estimate_file_tokens",
        lambda file_path, chars_per_token=4.0: (
            95 if file_path.name == "topic-v1.md" else 20
        ),
    )
    planner = BatchPlanner(_make_config(tmp_path), entries, manifest)

    plan = planner.plan_batches(
        "dedup",
        intelligence={
            "duplicate_groups": {"dup-1": ["docs/topic-v1.md", "docs/topic-v2.md"]},
            "version_chains": {},
        },
    )

    assert plan.total_files == 1
    assert plan.oversized_files == [
        {
            "path": "docs/topic-v1.md",
            "tokens": 95,
            "reason": "exceeds_batch_limit",
        }
    ]
    assert plan.batches[0].file_paths == ["docs/topic-v2.md"]
