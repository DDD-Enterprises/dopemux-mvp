from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_docs_duplicates.py"
POLICY_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "docs_hygiene"
    / "docs_placement_policy.yaml"
)

SPEC = importlib.util.spec_from_file_location("check_docs_duplicates", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _policy():
    return MODULE._load_policy(POLICY_PATH)


def test_classify_duplicate_for_archive_manual_review_and_orphan(tmp_path: Path):
    policy = _policy()
    docs_dir = tmp_path / "docs" / "03-reference" / "systems"
    docs_dir.mkdir(parents=True)

    (docs_dir / "alpha.md").write_text("# alpha\n", encoding="utf-8")
    (docs_dir / "alpha-2.md").write_text("# alpha\n", encoding="utf-8")
    (docs_dir / "beta.md").write_text("# beta\nbase\n", encoding="utf-8")
    (docs_dir / "beta-2.md").write_text("# beta\nchanged\n", encoding="utf-8")
    (docs_dir / "gamma-2.md").write_text("# gamma\n", encoding="utf-8")

    archived = MODULE.classify_duplicate("docs/03-reference/systems/alpha-2.md", tmp_path, policy)
    review = MODULE.classify_duplicate("docs/03-reference/systems/beta-2.md", tmp_path, policy)
    orphan = MODULE.classify_duplicate("docs/03-reference/systems/gamma-2.md", tmp_path, policy)

    assert archived.status == "archive_duplicate"
    assert archived.base_path == "docs/03-reference/systems/alpha.md"
    assert archived.target_path == "docs/archive/deduped-suffixes/03-reference/systems/alpha-2.md"
    assert review.status == "manual_review"
    assert review.base_path == "docs/03-reference/systems/beta.md"
    assert orphan.status == "rename_orphan"
    assert orphan.target_path == "docs/03-reference/systems/gamma.md"


def test_run_apply_archives_duplicates_renames_orphans_and_rewrites_links(tmp_path: Path):
    policy = _policy()
    docs_dir = tmp_path / "docs" / "03-reference" / "systems"
    docs_dir.mkdir(parents=True)

    (docs_dir / "alpha.md").write_text("# alpha\n", encoding="utf-8")
    (docs_dir / "alpha-2.md").write_text("# alpha\n", encoding="utf-8")
    (docs_dir / "gamma-2.md").write_text("# gamma\n", encoding="utf-8")
    (docs_dir / "index.md").write_text("[alpha duplicate](alpha-2.md)\n", encoding="utf-8")

    audit_path = tmp_path / "reports" / "duplicates.json"
    exit_code = MODULE.run_apply(repo_root=tmp_path, policy=policy, audit_path=audit_path)

    assert exit_code == 0
    assert (docs_dir / "alpha.md").exists()
    assert not (docs_dir / "alpha-2.md").exists()
    assert (tmp_path / "docs" / "archive" / "deduped-suffixes" / "03-reference" / "systems" / "alpha-2.md").exists()
    assert (docs_dir / "gamma.md").exists()
    assert not (docs_dir / "gamma-2.md").exists()
    assert "[alpha duplicate](alpha.md)" in (docs_dir / "index.md").read_text(encoding="utf-8")
    assert MODULE.run_check(repo_root=tmp_path, policy=policy) == 0
