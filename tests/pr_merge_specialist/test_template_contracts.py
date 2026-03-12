from __future__ import annotations

import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_template_runtime_parity_cli_and_schema():
    runtime_cli = (REPO_ROOT / "src" / "dopemux_pr_merge_specialist" / "cli.py").read_text(encoding="utf-8")
    template_cli = (
        REPO_ROOT
        / "templates"
        / "skills"
        / "pr-merge-specialist"
        / "scripts"
        / "dopemux_pr_merge_specialist"
        / "cli.py"
    ).read_text(encoding="utf-8")
    runtime_schema = (REPO_ROOT / "src" / "dopemux_pr_merge_specialist" / "schema.py").read_text(encoding="utf-8")
    template_schema = (
        REPO_ROOT
        / "templates"
        / "skills"
        / "pr-merge-specialist"
        / "scripts"
        / "dopemux_pr_merge_specialist"
        / "schema.py"
    ).read_text(encoding="utf-8")

    assert runtime_cli == template_cli
    assert runtime_schema == template_schema


def test_sync_repo_skills_family_includes_pr_merge_specialist():
    module_path = REPO_ROOT / "scripts" / "skills" / "sync_repo_skills.py"
    spec = importlib.util.spec_from_file_location("sync_repo_skills", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load sync_repo_skills module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert "pr-merge-specialist" in module.FAMILIES
    assert module.FAMILIES["pr-merge-specialist"] == ["pr-merge-specialist"]


def test_template_skill_files_exist():
    skill_root = REPO_ROOT / "templates" / "skills" / "pr-merge-specialist"
    assert (skill_root / "SKILL.md").exists()
    assert (skill_root / "agents" / "openai.yaml").exists()
    assert (skill_root / "scripts" / "dopemux_pr_merge_specialist" / "cli.py").exists()
