from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_docs_hygiene.py"
POLICY_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "docs_hygiene"
    / "docs_placement_policy.yaml"
)

SPEC = importlib.util.spec_from_file_location("check_docs_hygiene", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _policy():
    return MODULE._load_policy(POLICY_PATH)


def test_canonical_path_is_ok():
    record = MODULE.classify_path(
        rel_path="docs/03-reference/services/task-orchestrator.md",
        frontmatter_type=None,
        policy=_policy(),
    )
    assert record.zone == "active"
    assert record.status == "ok"
    assert record.target_path is None


def test_quarantine_path_is_quarantine_zone():
    record = MODULE.classify_path(
        rel_path="docs/04-explanation/history/sourceFiles/legacy.md",
        frontmatter_type=None,
        policy=_policy(),
    )
    assert record.zone == "quarantine"
    assert record.status == "quarantine"
    assert record.target_path is None


def test_noncanonical_spec_path_maps_to_reference_spec():
    record = MODULE.classify_path(
        rel_path="docs/spec/dope-memory/v1/00-overview.md",
        frontmatter_type=None,
        policy=_policy(),
    )
    assert record.status == "needs_relocation"
    assert record.rule_id == "map-spec"
    assert record.target_path == "docs/03-reference/spec/dope-memory/v1/00-overview.md"


def test_nested_drift_archive_and_audit_reports_map_deterministically():
    policy = _policy()
    archive_record = MODULE.classify_path(
        rel_path="docs/04-explanation/archive/session-notes/2025-10/note.md",
        frontmatter_type=None,
        policy=policy,
    )
    audit_record = MODULE.classify_path(
        rel_path="docs/04-explanation/audit-reports/phase-1.md",
        frontmatter_type=None,
        policy=policy,
    )
    assert archive_record.status == "needs_relocation"
    assert archive_record.rule_id == "map-explanation-archive"
    assert archive_record.target_path == "docs/archive/session-notes/2025-10/note.md"
    assert audit_record.status == "needs_relocation"
    assert audit_record.rule_id == "map-explanation-audit-reports"
    assert audit_record.target_path == "docs/05-audit-reports/phase-1.md"


def test_root_allowlist_keeps_master_index_and_relocates_other_root_docs():
    policy = _policy()
    keeper = MODULE.classify_path(
        rel_path="docs/00-MASTER-INDEX.md",
        frontmatter_type="explanation",
        policy=policy,
    )
    moved = MODULE.classify_path(
        rel_path="docs/checklist-2.md",
        frontmatter_type="explanation",
        policy=policy,
    )
    assert keeper.status == "ok"
    assert keeper.rule_id == "root-keeper"
    assert moved.status == "needs_relocation"
    assert moved.rule_id == "root-override"
    assert moved.target_path == "docs/02-how-to/root-relocated/checklist-2.md"


def test_root_token_rule_applies_when_no_override():
    record = MODULE.classify_path(
        rel_path="docs/DEPLOYMENT_STATUS_NOTE.md",
        frontmatter_type=None,
        policy=_policy(),
    )
    assert record.status == "needs_relocation"
    assert record.rule_id == "root-token-audit-report"
    assert record.target_path == "docs/05-audit-reports/root-relocated/DEPLOYMENT_STATUS_NOTE.md"


def _write(root: Path, rel: str, content: bytes) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def test_apply_moves_identical_destination_fails_closed_and_keeps_both_paths(tmp_path):
    repo_root = tmp_path
    payload = b"# Same document\n\nidentical bytes\n"
    src = _write(repo_root, "docs/old/note.md", payload)
    dst = _write(repo_root, "docs/new/note.md", payload)

    with pytest.raises(FileExistsError):
        MODULE.apply_moves(repo_root=repo_root, old_to_target={"docs/old/note.md": "docs/new/note.md"})

    assert src.exists(), "source must not be unlinked on identical-destination collision"
    assert dst.exists()
    assert src.read_bytes() == payload
    assert dst.read_bytes() == payload


def test_apply_moves_preflight_rejects_whole_batch_before_any_move(tmp_path):
    repo_root = tmp_path
    safe_src = _write(repo_root, "docs/a-safe.md", b"# safe\n")
    dup_payload = b"# duplicate\n"
    dup_src = _write(repo_root, "docs/z-dup.md", dup_payload)
    dup_dst = _write(repo_root, "docs/dst/dup.md", dup_payload)
    safe_dst = repo_root / "docs/dst/safe.md"
    assert not safe_dst.exists()

    old_to_target = {
        "docs/a-safe.md": "docs/dst/safe.md",  # sorts first; would move cleanly on its own
        "docs/z-dup.md": "docs/dst/dup.md",  # sorts later; identical-target collision
    }

    with pytest.raises(FileExistsError):
        MODULE.apply_moves(repo_root=repo_root, old_to_target=old_to_target)

    # Transactional preflight: zero moves, zero deletions.
    assert safe_src.exists()
    assert not safe_dst.exists(), "safe move must not execute when batch is rejected"
    assert dup_src.exists(), "colliding source must not be unlinked"
    assert dup_dst.exists()
    assert dup_src.read_bytes() == dup_payload


def _names(directory: Path) -> set[str]:
    # Lexical listing: deterministic on case-sensitive and case-insensitive
    # filesystems alike.
    if not directory.exists():
        return set()
    return {entry.name for entry in directory.iterdir()}


def test_apply_moves_rejects_case_alias_between_batch_destinations(tmp_path):
    repo_root = tmp_path
    payload = b"# shared bytes\n"
    _write(repo_root, "docs/a.md", payload)
    _write(repo_root, "docs/z.md", payload)
    old_to_target = {"docs/a.md": "docs/Out.md", "docs/z.md": "docs/out.md"}

    with pytest.raises(FileExistsError) as excinfo:
        MODULE.apply_moves(repo_root=repo_root, old_to_target=old_to_target)

    assert "docs/Out.md" in str(excinfo.value)
    assert "docs/out.md" in str(excinfo.value)
    assert _names(repo_root / "docs") == {"a.md", "z.md"}
    assert (repo_root / "docs/a.md").read_bytes() == payload
    assert (repo_root / "docs/z.md").read_bytes() == payload


def test_apply_moves_late_alias_keeps_earlier_entries_unmoved(tmp_path):
    repo_root = tmp_path
    _write(repo_root, "docs/a-safe.md", b"# safe\n")
    _write(repo_root, "docs/y.md", b"# y\n")
    _write(repo_root, "docs/z.md", b"# z\n")
    old_to_target = {
        "docs/a-safe.md": "docs/dst/safe.md",  # sorts first; clean on its own
        "docs/y.md": "docs/dst/Out.md",  # alias pair sorts late
        "docs/z.md": "docs/dst/out.md",
    }

    with pytest.raises(FileExistsError):
        MODULE.apply_moves(repo_root=repo_root, old_to_target=old_to_target)

    assert _names(repo_root / "docs") == {"a-safe.md", "y.md", "z.md"}
    assert not (repo_root / "docs/dst").exists(), "earlier entry must not move"


def test_apply_moves_rejects_case_alias_of_existing_tree_file(tmp_path):
    repo_root = tmp_path
    src = _write(repo_root, "docs/old/note.md", b"# new note\n")
    existing = _write(repo_root, "docs/dst/Note.md", b"# existing note\n")
    old_to_target = {"docs/old/note.md": "docs/dst/note.md"}

    with pytest.raises(FileExistsError) as excinfo:
        MODULE.apply_moves(repo_root=repo_root, old_to_target=old_to_target)

    assert "docs/dst/note.md" in str(excinfo.value)
    assert "docs/dst/Note.md" in str(excinfo.value)
    assert _names(repo_root / "docs/old") == {"note.md"}
    assert _names(repo_root / "docs/dst") == {"Note.md"}
    assert src.read_bytes() == b"# new note\n"
    assert existing.read_bytes() == b"# existing note\n"


def test_apply_moves_rejects_case_only_self_rename(tmp_path):
    repo_root = tmp_path
    src = _write(repo_root, "docs/readme.md", b"# readme\n")
    old_to_target = {"docs/readme.md": "docs/README.md"}

    with pytest.raises(FileExistsError) as excinfo:
        MODULE.apply_moves(repo_root=repo_root, old_to_target=old_to_target)

    assert "docs/readme.md" in str(excinfo.value)
    assert "docs/README.md" in str(excinfo.value)
    assert _names(repo_root / "docs") == {"readme.md"}
    assert src.read_bytes() == b"# readme\n"


def test_apply_moves_drops_absent_source_before_preflight_and_apply(tmp_path):
    repo_root = tmp_path
    payload = b"# identical\n"
    _write(repo_root, "docs/a.md", payload)
    _write(repo_root, "docs/c.md", payload)
    assert not (repo_root / "docs/b.md").exists()
    old_to_target = {"docs/a.md": "docs/b.md", "docs/b.md": "docs/c.md"}

    old_to_actual, moved_pairs = MODULE.apply_moves(
        repo_root=repo_root, old_to_target=old_to_target
    )

    # The absent b.md mapping is dropped once, so the file a.md becomes is
    # never re-processed into a collision with the identical c.md.
    assert old_to_actual == {"docs/a.md": "docs/b.md"}
    assert moved_pairs == {"docs/a.md": "docs/b.md"}
    assert _names(repo_root / "docs") == {"b.md", "c.md"}
    assert (repo_root / "docs/b.md").read_bytes() == payload
    assert (repo_root / "docs/c.md").read_bytes() == payload


def test_apply_moves_non_alias_batch_still_moves_with_numbering(tmp_path):
    repo_root = tmp_path
    _write(repo_root, "docs/a.md", b"# a\n")
    _write(repo_root, "docs/b.md", b"# b\n")
    _write(repo_root, "docs/dst/b.md", b"# other b\n")
    old_to_target = {
        "docs/a.md": "docs/dst/a.md",
        "docs/b.md": "docs/dst/b.md",
    }

    old_to_actual, moved_pairs = MODULE.apply_moves(
        repo_root=repo_root, old_to_target=old_to_target
    )

    assert old_to_actual == {
        "docs/a.md": "docs/dst/a.md",
        "docs/b.md": "docs/dst/b-moved-2.md",
    }
    assert moved_pairs == old_to_actual
    assert _names(repo_root / "docs") == {"dst"}
    assert _names(repo_root / "docs/dst") == {"a.md", "b.md", "b-moved-2.md"}
    assert (repo_root / "docs/dst/b-moved-2.md").read_bytes() == b"# b\n"
    assert (repo_root / "docs/dst/b.md").read_bytes() == b"# other b\n"
