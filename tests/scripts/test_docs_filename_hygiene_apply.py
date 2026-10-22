"""Data-safety tests for the --apply / --repair path of check_docs_filename_hygiene.

Every test runs inside ``tmp_path``; the tool is never pointed at the real repo.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Dict, Optional

import pytest

MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_docs_filename_hygiene.py"
POLICY_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "docs_hygiene"
    / "docs_placement_policy.yaml"
)

SPEC = importlib.util.spec_from_file_location("check_docs_filename_hygiene_apply_under_test", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

AUDIT_REL = "reports/docs-hygiene/filename_audit.json"


def _policy():
    return MODULE._load_policy(POLICY_PATH)


def _apply(repo_root: Path, requested: Optional[list] = None) -> int:
    return MODULE.run_apply(
        repo_root=repo_root,
        policy=_policy(),
        audit_path=repo_root / AUDIT_REL,
        requested_paths=requested,
    )


def _snapshot(repo_root: Path) -> Dict[str, bytes]:
    return {
        str(p.relative_to(repo_root)): p.read_bytes()
        for p in sorted(repo_root.rglob("*"))
        if p.is_file() and "reports" not in p.parts
    }


# --------------------------------------------------------------------------- F1


def test_apply_fails_and_does_not_rewrite_refs_when_a_source_vanishes(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "Foo_Bar.md").write_text("# foo\n", encoding="utf-8")
    (docs / "Other_Doc.md").write_text("# other\n", encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text("see docs/Foo_Bar.md and docs/Other_Doc.md\n", encoding="utf-8")

    real_build_records = MODULE.build_records

    def vanishing_build_records(**kwargs):
        records = real_build_records(**kwargs)
        # The source disappears between planning and apply.
        (docs / "Foo_Bar.md").unlink(missing_ok=True)
        return records

    monkeypatch.setattr(MODULE, "build_records", vanishing_build_records)

    rc = _apply(tmp_path)

    assert rc != 0, "planned/actual rename sets diverged but the run reported success"
    text = readme.read_text(encoding="utf-8")
    assert "docs/foo-bar.md" not in text, "reference rewritten to a target that was never created"
    assert "docs/Foo_Bar.md" in text
    # Fail-closed: nothing was renamed when the plan could not be executed in full.
    assert (docs / "Other_Doc.md").exists()
    assert not (docs / "other-doc.md").exists()


# --------------------------------------------------------------------------- F2


def test_apply_rewrites_only_whole_path_tokens(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "Foo_Bar.md").write_text("# foo\n", encoding="utf-8")
    archive = tmp_path / "archive" / "docs"
    archive.mkdir(parents=True)
    (archive / "Foo_Bar.md").write_text("# archived copy\n", encoding="utf-8")

    notes = tmp_path / "notes.md"
    notes.write_text(
        "archive/docs/Foo_Bar.md\n"
        "docs/Foo_Bar.md.bak\n"
        "see docs/Foo_Bar.md.\n"
        "`docs/Foo_Bar.md`\n"
        "- docs/Foo_Bar.md: entry\n",
        encoding="utf-8",
    )
    changelog = tmp_path / "CHANGELOG.md"
    changelog_text = "- moved old/docs/Foo_Bar.md to archive/docs/Foo_Bar.md\n"
    changelog.write_text(changelog_text, encoding="utf-8")

    rc = _apply(tmp_path)

    assert rc == 0
    assert (docs / "foo-bar.md").exists()
    assert (archive / "Foo_Bar.md").exists()
    assert notes.read_text(encoding="utf-8") == (
        "archive/docs/Foo_Bar.md\n"
        "docs/Foo_Bar.md.bak\n"
        "see docs/foo-bar.md.\n"
        "`docs/foo-bar.md`\n"
        "- docs/foo-bar.md: entry\n"
    )
    assert changelog.read_text(encoding="utf-8") == changelog_text


def test_plain_ref_rewrite_applies_chained_keys_exactly_once(tmp_path):
    target = tmp_path / "refs.txt"
    target.write_text("docs/A.md docs/C.md\n", encoding="utf-8")

    MODULE._rewrite_plain_path_refs(
        repo_root=tmp_path,
        path_map={"docs/A.md": "docs/C.md", "docs/C.md": "docs/D.md"},
    )

    assert target.read_text(encoding="utf-8") == "docs/C.md docs/D.md\n"


@pytest.mark.parametrize("worktree_root", [".worktrees/other", ".claude/worktrees/other"])
def test_plain_ref_rewrite_never_touches_sibling_worktrees(tmp_path, worktree_root):
    # Running --apply in the main checkout must not rewrite another session's
    # worktree checked out inside the repo.
    own = tmp_path / "refs.txt"
    own.write_text("see docs/A.md\n", encoding="utf-8")
    sibling = tmp_path / worktree_root / "refs.txt"
    sibling.parent.mkdir(parents=True)
    sibling.write_text("see docs/A.md\n", encoding="utf-8")

    MODULE._rewrite_plain_path_refs(repo_root=tmp_path, path_map={"docs/A.md": "docs/b.md"})

    assert own.read_text(encoding="utf-8") == "see docs/b.md\n"
    assert sibling.read_text(encoding="utf-8") == "see docs/A.md\n"


# --------------------------------------------------------------------------- F3


def test_apply_preserves_crlf_and_every_unreplaced_byte(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "Foo_Bar.md").write_bytes(b"# foo\r\n")
    notes = tmp_path / "notes.md"
    notes.write_bytes(b"\xef\xbb\xbffirst caf\xc3\xa9\r\nsee docs/Foo_Bar.md here\r\ntrailing\r\n")
    untouched = tmp_path / "untouched.md"
    untouched_bytes = b"no refs here\r\nat all\r\n"
    untouched.write_bytes(untouched_bytes)

    rc = _apply(tmp_path)

    assert rc == 0
    assert notes.read_bytes() == b"\xef\xbb\xbffirst caf\xc3\xa9\r\nsee docs/foo-bar.md here\r\ntrailing\r\n"
    assert untouched.read_bytes() == untouched_bytes


def test_apply_skips_non_utf8_file_with_warning_and_never_writes_replacement_char(tmp_path, capsys):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "Foo_Bar.md").write_text("# foo\n", encoding="utf-8")
    legacy = tmp_path / "legacy.txt"
    legacy_bytes = b"see docs/Foo_Bar.md \xff\xfe latin-1 caf\xe9\n"
    legacy.write_bytes(legacy_bytes)

    rc = _apply(tmp_path)
    captured = capsys.readouterr()

    assert rc == 0
    assert legacy.read_bytes() == legacy_bytes
    assert b"\xef\xbf\xbd" not in legacy.read_bytes()
    assert "legacy.txt" in captured.out + captured.err
    assert "WARNING" in captured.out + captured.err


# --------------------------------------------------------------------------- F4


def test_crash_in_phase_two_leaves_journal_and_repair_completes_idempotently(tmp_path, monkeypatch):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "Foo_Bar.md").write_text("# foo\n", encoding="utf-8")
    (docs / "Other_Doc.md").write_text("# other\n", encoding="utf-8")
    readme = tmp_path / "README.md"
    readme.write_text("see docs/Foo_Bar.md and docs/Other_Doc.md\n", encoding="utf-8")

    reports_dir = tmp_path / "reports" / "docs-hygiene"
    reports_dir.mkdir(parents=True)
    audit_path = tmp_path / AUDIT_REL
    prior_audit = '[{"prior": true}]'
    audit_path.write_text(prior_audit, encoding="utf-8")

    real_safe_move = MODULE._safe_move

    def exploding_safe_move(repo_root, src_rel, dst_rel):
        if ".tmp-filename-rename-" in src_rel:
            raise RuntimeError("boom: simulated crash in phase 2")
        return real_safe_move(repo_root=repo_root, src_rel=src_rel, dst_rel=dst_rel)

    monkeypatch.setattr(MODULE, "_safe_move", exploding_safe_move)
    with pytest.raises(RuntimeError, match="boom"):
        _apply(tmp_path)
    monkeypatch.undo()

    # Phase 1 happened, phase 2 did not: only temp-named files remain.
    temp_files = sorted(p.name for p in docs.glob(".tmp-filename-rename-*.md"))
    assert len(temp_files) == 2
    assert not (docs / "foo-bar.md").exists()

    journals = sorted(reports_dir.glob("*.jsonl"))
    assert len(journals) == 1, "a recovery journal must exist after a crash mid-rename"
    records = [json.loads(line) for line in journals[0].read_text(encoding="utf-8").splitlines() if line.strip()]
    for record in records:
        assert {"old", "temp", "final", "sha256", "phase", "timestamp"} <= set(record)
    pending = {(r["old"], r["final"]) for r in records if r["phase"] == "planned"}
    assert pending == {("docs/Foo_Bar.md", "docs/foo-bar.md"), ("docs/Other_Doc.md", "docs/other-doc.md")}
    assert {r["temp"] for r in records if r["phase"] == "temp"} == {f"docs/{name}" for name in temp_files}
    assert not [r for r in records if r["phase"] == "final"]

    rc = MODULE.run_repair(
        repo_root=tmp_path,
        journal_path=journals[0],
        policy=_policy(),
        audit_path=audit_path,
    )
    assert rc == 0
    assert (docs / "foo-bar.md").read_text(encoding="utf-8") == "# foo\n"
    assert (docs / "other-doc.md").read_text(encoding="utf-8") == "# other\n"
    assert not list(docs.glob(".tmp-filename-rename-*.md"))
    assert readme.read_text(encoding="utf-8") == "see docs/foo-bar.md and docs/other-doc.md\n"

    after_first_repair = _snapshot(tmp_path)
    rc_again = MODULE.run_repair(
        repo_root=tmp_path,
        journal_path=journals[0],
        policy=_policy(),
        audit_path=audit_path,
    )
    assert rc_again == 0
    assert _snapshot(tmp_path) == after_first_repair

    # The audit written by repair replaced the prior one, but the prior one is retained.
    assert audit_path.read_text(encoding="utf-8") != prior_audit
    retained = [p for p in reports_dir.glob("filename_audit-*.json") if p.read_text(encoding="utf-8") == prior_audit]
    assert retained, "previous audit must be copied to a timestamped sibling before overwrite"


def test_write_audit_retains_previous_audit(tmp_path):
    audit_path = tmp_path / AUDIT_REL
    first = [MODULE.FilenameRecord(path="docs/a.md", zone="active", status="ok", target_path=None, reason="kebab-ok")]
    second = [
        MODULE.FilenameRecord(
            path="docs/B.md", zone="active", status="needs_rename", target_path="docs/b.md", reason="kebab-required"
        )
    ]

    MODULE.write_audit(path=audit_path, records=first)
    first_text = audit_path.read_text(encoding="utf-8")
    MODULE.write_audit(path=audit_path, records=second, keep_previous=True)

    assert json.loads(audit_path.read_text(encoding="utf-8"))[0]["path"] == "docs/B.md"
    siblings = [p for p in audit_path.parent.glob("filename_audit-*.json")]
    assert siblings, "previous audit must be retained as a timestamped sibling"
    assert any(p.read_text(encoding="utf-8") == first_text for p in siblings)


def test_cli_accepts_repair_mode(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["check_docs_filename_hygiene.py", "--repair", "reports/docs-hygiene/j.jsonl"])
    try:
        args = MODULE.parse_args()
    except SystemExit:
        args = None
    assert args is not None, "--repair <journal> is not accepted by the CLI"
    assert args.repair == "reports/docs-hygiene/j.jsonl"
