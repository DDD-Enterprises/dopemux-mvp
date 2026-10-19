from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_docs_filename_hygiene.py"
POLICY_PATH = (
    Path(__file__).resolve().parents[2]
    / "config"
    / "docs_hygiene"
    / "docs_placement_policy.yaml"
)

SPEC = importlib.util.spec_from_file_location("check_docs_filename_hygiene", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _policy():
    return MODULE._load_policy(POLICY_PATH)


def test_slugify_stem_basic_cases():
    assert MODULE._slugify_stem("My File_Name") == "my-file-name"
    assert MODULE._slugify_stem("ADR-207-PHASE-1-IMPLEMENTATION-PLAN") == "adr-207-phase-1-implementation-plan"
    assert MODULE._slugify_stem("døpemux-brand-system") == "dopemux-brand-system"


def test_quarantine_and_keeper_are_exempt_from_rename():
    policy = _policy()
    quarantine = MODULE.classify_filename(
        rel_path="docs/04-explanation/history/sourceFiles/legacy.md",
        policy=policy,
    )
    keeper = MODULE.classify_filename(
        rel_path="docs/00-MASTER-INDEX.md",
        policy=policy,
    )
    assert quarantine.status == "quarantine"
    assert keeper.status == "exempt"


def test_needs_rename_detected_for_non_kebab_name():
    record = MODULE.classify_filename(
        rel_path="docs/03-reference/services/Server Registry.md",
        policy=_policy(),
    )
    assert record.status == "needs_rename"
    assert record.target_path == "docs/03-reference/services/server-registry.md"


def test_kebab_filename_is_ok():
    record = MODULE.classify_filename(
        rel_path="docs/03-reference/services/task-orchestrator.md",
        policy=_policy(),
    )
    assert record.status == "ok"
    assert record.target_path is None


import pytest

# Supervisor-reviewed fixture: symlink creation confined to this test's tmp_path.
# Generated tests receive this capability instead of importing os/importlib/sys.
@pytest.fixture
def mp023_symlink(tmp_path):
    root = tmp_path.resolve()

    def create(target, link):
        target = Path(target)
        link = Path(link)
        target.resolve().relative_to(root)
        link.parent.resolve().relative_to(root)
        if link.name in ("", ".", ".."):
            raise ValueError("invalid fixture link name")
        link.symlink_to(target)

    return create


def test_mp023_symlink_fixture_rejects_external_target(tmp_path, mp023_symlink):
    with pytest.raises(ValueError):
        mp023_symlink(tmp_path.parent / "outside-fixture.md", tmp_path / "alias.md")


def test_mp023_symlink_fixture_rejects_external_link(tmp_path, mp023_symlink):
    target = tmp_path / "target.md"
    target.write_text("public fixture\n")
    with pytest.raises(ValueError):
        mp023_symlink(target, tmp_path.parent / "outside-fixture.md")

def _hygiene_module():
    return MODULE


import pytest




def _minimal_policy():
    return {
        "docs_root": "docs",
        "quarantine_prefixes": [],
        "keep_docs_root_files": [],
        "filename_exemptions": [],
    }


def _make_repo(tmp_path):
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)
    (docs / "good-doc.md").write_text("# good\n", encoding="utf-8")
    outside = tmp_path / "outside"
    outside.mkdir()
    secret = outside / "Secret Notes.md"
    secret.write_text("# secret\n", encoding="utf-8")
    return repo, docs, secret




def test_iter_docs_rejects_parent_traversal_request(tmp_path):
    mod = _hygiene_module()
    repo, _docs, secret = _make_repo(tmp_path)
    assert secret.exists()

    result = list(mod.iter_docs(repo_root=repo, docs_root="docs", requested_paths=["../outside/Secret Notes.md"]))

    assert result == []
    records = mod.build_records(repo_root=repo, policy=_minimal_policy(), requested_paths=["../outside/Secret Notes.md"])
    assert records == []


def test_iter_docs_rejects_absolute_path_request(tmp_path):
    mod = _hygiene_module()
    repo, _docs, secret = _make_repo(tmp_path)

    result = list(mod.iter_docs(repo_root=repo, docs_root="docs", requested_paths=[str(secret)]))

    assert result == []


def test_iter_docs_skips_symlink_escaping_repo(tmp_path, mp023_symlink):
    mod = _hygiene_module()
    repo, docs, secret = _make_repo(tmp_path)
    escape = docs / "escape.md"
    mp023_symlink(secret, escape)
    assert escape.is_file()

    result = list(mod.iter_docs(repo_root=repo, docs_root="docs", requested_paths=["docs/escape.md"]))

    assert result == []


def test_iter_docs_keeps_legitimate_docs_request_and_default_walk(tmp_path, mp023_symlink):
    mod = _hygiene_module()
    repo, docs, _secret = _make_repo(tmp_path)
    alias = docs / "alias-doc.md"
    mp023_symlink(docs / "good-doc.md", alias)

    explicit = list(mod.iter_docs(repo_root=repo, docs_root="docs", requested_paths=["docs/good-doc.md", "docs/alias-doc.md"]))
    assert explicit == sorted([docs / "alias-doc.md", docs / "good-doc.md"])

    records = mod.build_records(repo_root=repo, policy=_minimal_policy(), requested_paths=["docs/good-doc.md"])
    assert [r.path for r in records] == ["docs/good-doc.md"]
    assert records[0].status == "ok"

    default_walk = list(mod.iter_docs(repo_root=repo, docs_root="docs"))
    assert docs / "good-doc.md" in default_walk
    assert (repo / "docs" / "missing.md") not in default_walk
    assert all(p.suffix == ".md" for p in default_walk)
