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

    with pytest.raises(ValueError, match="unsafe output directory"):
        builder.validate_output_dir(repo_root, repo_root)

    with pytest.raises(ValueError, match="unsafe output directory"):
        builder.validate_output_dir(repo_root, tmp_path)

    with pytest.raises(ValueError, match="unsafe output directory"):
        builder.validate_output_dir(Path("/Users/hue/example-repo"), Path("/private/var"))

    with pytest.raises(ValueError, match="unsafe output directory"):
        builder.validate_output_dir(Path("/Users/hue/example-repo"), Path("/private/var/folders"))


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
        }
    ]


def test_classification_enum_includes_unknown_requires_review() -> None:
    builder = load_script("build_chatgpt_project_sources")

    assert "UNKNOWN_REQUIRES_REVIEW" in builder.VALID_PR_CLASSIFICATIONS
