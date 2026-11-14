"""
file_repo_root / tool_edit_path behaviour of .claude/hooks/dcp_surface_guard.py.

Fake checkouts are built under tmp_path: a directory holding a ``.git``
directory is a main checkout, a directory holding a ``.git`` file with a
``gitdir:`` line is a linked worktree. No real git command runs here.
"""
from __future__ import annotations

import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parents[3] / ".claude" / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from dcp_surface_guard import RED_LANE_ID, surface_guard_block  # noqa: E402

_RED = "services/task-orchestrator/x.py"
_EXEMPT = "services/dopecon-bridge/ddg_mcp_stdio.py"


def _main_checkout(base: Path) -> Path:
    root = base / "main-checkout"
    (root / ".git").mkdir(parents=True)
    return root


def _linked_worktree(base: Path) -> Path:
    root = base / "sibling-worktree"
    root.mkdir(parents=True)
    (root / ".git").write_text("gitdir: ../main-checkout/.git/worktrees/sibling\n")
    return root


def test_sibling_worktree_red_lane_path_is_blocked(tmp_path: Path) -> None:
    session_root = _main_checkout(tmp_path)
    sibling = _linked_worktree(tmp_path)
    target = sibling / _RED
    target.parent.mkdir(parents=True)
    target.write_text("x = 1\n")

    result = surface_guard_block("Edit", {"file_path": str(target)}, session_root)

    assert result is not None
    assert RED_LANE_ID in result


def test_new_file_in_missing_directory_is_blocked(tmp_path: Path) -> None:
    session_root = _main_checkout(tmp_path)
    sibling = _linked_worktree(tmp_path)
    target = sibling / "services" / "task-orchestrator" / "new" / "deep" / "x.py"
    assert not target.parent.exists()

    result = surface_guard_block("Write", {"file_path": str(target)}, session_root)

    assert result is not None
    assert RED_LANE_ID in result


def test_notebook_path_is_read(tmp_path: Path) -> None:
    session_root = _main_checkout(tmp_path)
    sibling = _linked_worktree(tmp_path)
    target = sibling / "services" / "task-orchestrator" / "nb.ipynb"

    result = surface_guard_block("NotebookEdit", {"notebook_path": str(target)}, session_root)

    assert result is not None
    assert RED_LANE_ID in result


def test_symlink_into_red_lane_is_blocked(tmp_path: Path) -> None:
    session_root = _main_checkout(tmp_path)
    sibling = _linked_worktree(tmp_path)
    real = sibling / _RED
    real.parent.mkdir(parents=True)
    real.write_text("x = 1\n")
    (sibling / "docs").mkdir()
    link = sibling / "docs" / "innocent.py"
    link.symlink_to(real)

    result = surface_guard_block("Edit", {"file_path": str(link)}, session_root)

    assert result is not None
    assert RED_LANE_ID in result


def test_exempt_file_in_sibling_worktree_stays_allowed(tmp_path: Path) -> None:
    session_root = _main_checkout(tmp_path)
    sibling = _linked_worktree(tmp_path)
    target = sibling / _EXEMPT
    target.parent.mkdir(parents=True)
    target.write_text("x = 1\n")

    assert surface_guard_block("Edit", {"file_path": str(target)}, session_root) is None


def test_planted_git_file_does_not_hide_a_red_lane_path(tmp_path: Path) -> None:
    root = _main_checkout(tmp_path)
    target = root / _RED
    target.parent.mkdir(parents=True)
    target.write_text("x = 1\n")
    assert surface_guard_block("Edit", {"file_path": str(target)}, root) is not None

    for planted in (root / "services" / ".git", root / "services" / "task-orchestrator" / ".git"):
        planted.write_text("gitdir: elsewhere\n")
        result = surface_guard_block("Edit", {"file_path": str(target)}, root)
        assert result is not None, planted
        assert RED_LANE_ID in result


def test_planted_git_file_in_sibling_worktree_does_not_hide_it(tmp_path: Path) -> None:
    root = _main_checkout(tmp_path)
    sibling = root / ".worktrees" / "sibling"
    sibling.mkdir(parents=True)
    (sibling / ".git").write_text("gitdir: ../../.git/worktrees/sibling\n")
    (sibling / "services").mkdir()
    (sibling / "services" / ".git").write_text("gitdir: elsewhere\n")
    target = sibling / _RED

    result = surface_guard_block("Write", {"file_path": str(target)}, root)

    assert result is not None
    assert RED_LANE_ID in result


def test_path_outside_any_repo_is_allowed(tmp_path: Path) -> None:
    session_root = _main_checkout(tmp_path)
    plain = tmp_path / "not-a-repo"
    target = plain / _RED
    target.parent.mkdir(parents=True)
    target.write_text("x = 1\n")

    assert surface_guard_block("Edit", {"file_path": str(target)}, session_root) is None
