from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


THIS_FILE = Path(__file__).resolve()


def _find_repo_root(start: Path) -> Path | None:
    for candidate in [start, *start.parents]:
        if (candidate / "pyproject.toml").exists() and (candidate / "templates" / "skills").exists():
            return candidate
    return None


def _find_skill_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "SKILL.md").exists() and (candidate / "agents" / "openai.yaml").exists():
            return candidate
    repo_root = _find_repo_root(start)
    if repo_root is not None:
        return repo_root / "templates" / "skills" / "pr-merge-specialist"
    raise RuntimeError("Unable to locate installed skill root")


REPO_ROOT = _find_repo_root(THIS_FILE)
SKILL_ROOT = _find_skill_root(THIS_FILE)
MODULES = [
    "__init__.py",
    "cli.py",
    "engine.py",
    "github_api.py",
    "merge.py",
    "policy.py",
    "queue_drain.py",
    "runtime.py",
    "schema.py",
    "steward_gate.py",
    "validation.py",
]


def test_template_runtime_parity_for_runtime_modules():
    if REPO_ROOT is None:
        pytest.skip("Repo source tree is unavailable in installed-skill test mode.")
    runtime_root = REPO_ROOT / "src" / "dopemux_pr_merge_specialist"
    template_root = REPO_ROOT / "templates" / "skills" / "pr-merge-specialist" / "scripts" / "dopemux_pr_merge_specialist"
    for module_name in MODULES:
        assert (runtime_root / module_name).read_text(encoding="utf-8") == (template_root / module_name).read_text(encoding="utf-8")


def test_sync_repo_skills_family_includes_pr_merge_specialist():
    if REPO_ROOT is None:
        pytest.skip("Repo sync script is unavailable in installed-skill test mode.")
    module_path = REPO_ROOT / "scripts" / "skills" / "sync_repo_skills.py"
    spec = importlib.util.spec_from_file_location("sync_repo_skills", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load sync_repo_skills module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert "pr-merge-specialist" in module.FAMILIES
    assert module.FAMILIES["pr-merge-specialist"] == ["pr-merge-specialist"]


def test_template_skill_files_exist_and_exclude_junk():
    assert (SKILL_ROOT / "SKILL.md").exists()
    assert (SKILL_ROOT / "agents" / "openai.yaml").exists()
    assert (SKILL_ROOT / "config" / "policy.example.yaml").exists()
    assert (
        SKILL_ROOT
        / "scripts"
        / "dopemux_pr_merge_specialist"
        / "config"
        / "policy.example.yaml"
    ).exists()
    assert (SKILL_ROOT / "PACKAGE_MANIFEST.json").exists()
    assert (SKILL_ROOT / "tests").exists()
    manifest = json.loads((SKILL_ROOT / "PACKAGE_MANIFEST.json").read_text(encoding="utf-8"))
    excludes = set(manifest.get("excludes", []))
    assert "__pycache__/" in excludes
    assert "*.pyc" in excludes
    assert "__MACOSX/" in excludes
