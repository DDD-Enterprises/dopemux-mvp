"""Gitstate: read-only branch/head/dirty over a real repo + fixed allowlist."""

from __future__ import annotations

from pathlib import Path

from dcp_facade import gitstate


def test_clean_repo_state(make_workspace):
    info = make_workspace()
    st = gitstate.repo_state(info["path"])
    assert st["head_sha"] == info["head_sha"]
    assert st["branch"] is not None
    assert st["dirty"] is False


def test_dirty_repo_state(make_workspace):
    info = make_workspace(dirty=True)
    st = gitstate.repo_state(info["path"])
    assert st["dirty"] is True


def test_non_git_dir_returns_none_fields(tmp_path: Path):
    st = gitstate.repo_state(tmp_path)
    assert st["head_sha"] is None
    assert st["dirty"] is None


def test_allowlist_is_fixed_and_readonly():
    # Only read-only verbs; no mutating git subcommands present.
    for argv in gitstate._ALLOWED.values():
        assert argv[0] == "git"
        assert argv[1] in {"rev-parse", "status"}
