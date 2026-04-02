from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "docs_sweep.py"

SPEC = importlib.util.spec_from_file_location("docs_sweep", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def _seed_config(tmp_path: Path) -> None:
    (tmp_path / "config" / "docs_hygiene").mkdir(parents=True)
    (tmp_path / "config" / "repo_hygiene").mkdir(parents=True)
    shutil.copy(REPO_ROOT / "config" / "docs_hygiene" / "docs_placement_policy.yaml", tmp_path / "config" / "docs_hygiene" / "docs_placement_policy.yaml")
    shutil.copy(REPO_ROOT / "config" / "repo_hygiene" / "root_hygiene_policy.json", tmp_path / "config" / "repo_hygiene" / "root_hygiene_policy.json")


def test_docs_sweep_apply_chains_filename_frontmatter_duplicates_and_placement(tmp_path: Path):
    _seed_config(tmp_path)
    source = tmp_path / "docs" / "rollout"
    source.mkdir(parents=True)
    (source / "Agent Guide-2.md").write_text("# Agent Guide\n", encoding="utf-8")

    exit_code = MODULE.run_sweep(mode="apply", repo_root=tmp_path)

    assert exit_code == 0
    final_path = tmp_path / "docs" / "02-how-to" / "rollout" / "agent-guide.md"
    assert final_path.exists()
    content = final_path.read_text(encoding="utf-8")
    assert content.startswith("---\n")
    assert "type: how-to" in content
    assert not (source / "Agent Guide-2.md").exists()
    assert not (source / "agent-guide-2.md").exists()

    check_exit = MODULE.run_sweep(mode="check", repo_root=tmp_path)
    assert check_exit == 0


def test_docs_sweep_apply_with_explicit_paths_propagates_renamed_paths_between_steps(tmp_path: Path):
    _seed_config(tmp_path)
    canonical_dir = tmp_path / "docs" / "02-how-to" / "mobile"
    canonical_dir.mkdir(parents=True)
    (canonical_dir / "implementation.md").write_text(
        "---\n"
        "id: implementation\n"
        "title: Implementation\n"
        "type: how-to\n"
        "owner: '@hu3mann'\n"
        "author: '@hu3mann'\n"
        "date: 2026-04-02\n"
        "last_review: 2026-04-02\n"
        "next_review: 2026-07-01\n"
        "prelude: Implementation (how-to) for dopemux documentation and developer workflows.\n"
        "---\n"
        "# impl\n",
        encoding="utf-8",
    )
    source_dir = tmp_path / "docs" / "mobile"
    source_dir.mkdir(parents=True)
    (source_dir / "implementation-2.md").write_text("# impl\n", encoding="utf-8")

    exit_code = MODULE.run_sweep(
        mode="apply",
        repo_root=tmp_path,
        requested_paths=["docs/mobile/implementation-2.md"],
    )

    assert exit_code == 0
    assert not (source_dir / "implementation-2.md").exists()
    assert not (source_dir / "implementation.md").exists()
    assert (canonical_dir / "implementation.md").exists()


def test_docs_sweep_audit_writes_combined_summary(tmp_path: Path):
    _seed_config(tmp_path)
    docs_dir = tmp_path / "docs" / "03-reference"
    docs_dir.mkdir(parents=True)
    (docs_dir / "reference-note.md").write_text(
        "---\nid: reference-note\ntitle: Reference Note\ntype: reference\nowner: '@hu3mann'\nauthor: '@hu3mann'\ndate: 2026-04-02\nlast_review: 2026-04-02\nnext_review: 2026-07-01\nprelude: reference note.\n---\n# Reference Note\n",
        encoding="utf-8",
    )

    audit_path = "reports/docs-hygiene/custom-sweep.json"
    exit_code = MODULE.run_sweep(mode="audit", repo_root=tmp_path, audit_out=audit_path)

    assert exit_code == 0
    payload = json.loads((tmp_path / audit_path).read_text(encoding="utf-8"))
    assert payload["mode"] == "audit"
    assert [step["step"] for step in payload["steps"]] == [
        "filename",
        "frontmatter",
        "duplicates",
        "placement",
        "schema-validation",
        "root-hygiene",
    ]


def test_docs_sweep_main_without_filenames_defaults_to_full_docs(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    _seed_config(tmp_path)
    docs_dir = tmp_path / "docs" / "03-reference"
    docs_dir.mkdir(parents=True)
    (docs_dir / "reference-note.md").write_text(
        "---\nid: reference-note\ntitle: Reference Note\ntype: reference\nowner: '@hu3mann'\nauthor: '@hu3mann'\ndate: 2026-04-02\nlast_review: 2026-04-02\nnext_review: 2026-07-01\nprelude: reference note.\n---\n# Reference Note\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(MODULE._PLACEMENT, "_repo_root", lambda: tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["docs_sweep.py", "--audit", "--audit-out", "reports/docs-hygiene/cli-audit.json"],
    )

    exit_code = MODULE.main()
    payload = json.loads((tmp_path / "reports/docs-hygiene/cli-audit.json").read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["scope"] == "all-docs"
    assert payload["steps"][0]["details"]["records"] == 1
