from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def load_script(name: str):
    path = REPO_ROOT / "scripts" / "project_sources" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_output_cleanup_rejects_repo_root_and_ancestor(tmp_path: Path) -> None:
    builder = load_script("build_chatgpt_project_sources")
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    expected_parent = repo_root / "out" / "chatgpt-project-upload-set"
    expected_parent.mkdir(parents=True)
    valid_output = expected_parent / builder.PACKET_ID

    with pytest.raises(ValueError, match="unsafe output directory"):
        builder.validate_output_dir(repo_root, tmp_path) # ancestor of repo root

    with pytest.raises(ValueError, match="unsafe output directory"):
        builder.validate_output_dir(repo_root, repo_root) # repo root

    with pytest.raises(ValueError, match="unsafe output directory"):
        builder.validate_output_dir(repo_root, Path("/"))

    with pytest.raises(ValueError, match="unsafe output directory"):
        builder.validate_output_dir(repo_root, Path.home())

    # output not beneath expected parent
    with pytest.raises(ValueError, match="unsafe output directory"):
        builder.validate_output_dir(repo_root, repo_root / "out" / "something-else")

    # expected parent itself
    with pytest.raises(ValueError, match="unsafe output directory"):
        builder.validate_output_dir(repo_root, expected_parent)

    # wrong basename
    with pytest.raises(ValueError, match="unsafe output directory"):
        builder.validate_output_dir(repo_root, expected_parent / "wrong-basename")

    # Symlink to repo root
    symlink_dir = tmp_path / "symlink-to-repo"
    symlink_dir.symlink_to(repo_root)
    with pytest.raises(ValueError, match="unsafe output directory"):
        builder.validate_output_dir(repo_root, symlink_dir)

    # Valid case shouldn't raise
    builder.validate_output_dir(repo_root, valid_output)


def test_secret_scan_includes_package_root_members(tmp_path: Path) -> None:
    validator = load_script("validate_chatgpt_project_sources")
    captured_metadata = tmp_path / "OPEN_PR_CAPTURE" / "open-pr-1.json"
    captured_metadata.parent.mkdir()
    captured_metadata.write_text("token=ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456")

    hits = validator.find_secret_hits([captured_metadata], tmp_path)

    assert hits == [
        {
            "file": "OPEN_PR_CAPTURE/open-pr-1.json",
            "pattern": "github_pat",
            "match_prefix": "ghp_ABCDEFGH",
            "blocking": True,
        }
    ]


def test_classification_enum_includes_unknown_requires_review() -> None:
    builder = load_script("build_chatgpt_project_sources")

    assert "UNKNOWN_REQUIRES_REVIEW" in builder.VALID_PR_CLASSIFICATIONS
