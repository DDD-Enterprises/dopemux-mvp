"""
file_repo_root / tool_edit_path(s) behaviour of .claude/hooks/dcp_surface_guard.py.

Fake checkouts are built under tmp_path: a directory holding a ``.git``
directory is a main checkout, a directory holding a ``.git`` file with a
``gitdir:`` line is a linked worktree. No real git command runs here.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_HOOKS_DIR = Path(__file__).resolve().parents[3] / ".claude" / "hooks"
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from dcp_surface_guard import (  # noqa: E402
    RED_LANE_ID,
    file_repo_root,
    surface_guard_block,
    surface_guard_warnings,
    tool_edit_path,
    tool_edit_paths,
)

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


def test_notebook_path_is_read_when_file_path_is_also_set(tmp_path: Path) -> None:
    # Amendment 02: a harmless file_path must not hide a red-lane notebook_path.
    session_root = _main_checkout(tmp_path)
    sibling = _linked_worktree(tmp_path)
    harmless = sibling / "docs" / "ok.ipynb"
    target = sibling / "services" / "task-orchestrator" / "nb.ipynb"

    result = surface_guard_block(
        "NotebookEdit",
        {"file_path": str(harmless), "notebook_path": str(target)},
        session_root,
    )

    assert result is not None
    assert RED_LANE_ID in result


def test_notebook_path_contract_surface_is_warned_when_file_path_is_also_set(
    tmp_path: Path,
) -> None:
    root = _main_checkout(tmp_path)

    warnings = surface_guard_warnings(
        "NotebookEdit",
        {
            "file_path": str(root / "docs" / "ok.ipynb"),
            "notebook_path": str(root / "schemas" / "dcp" / "x.ipynb"),
        },
        root,
        "sess-dual",
    )

    assert len(warnings) == 1
    assert "Contract-sensitive surface" in warnings[0]


def test_tool_edit_path_keeps_t03_and_tool_edit_paths_reads_both() -> None:
    # T01/T03 interface stays as issued; Amendment 02 adds tool_edit_paths.
    both = {"file_path": "a.ipynb", "notebook_path": "b.ipynb"}
    assert tool_edit_path(both) == "a.ipynb"
    assert tool_edit_path({"file_path": "", "notebook_path": "b.ipynb"}) == "b.ipynb"
    assert tool_edit_path({"file_path": 3}) == ""
    assert tool_edit_paths(both) == ["a.ipynb", "b.ipynb"]
    assert tool_edit_paths({"file_path": "a", "notebook_path": "a"}) == ["a"]
    assert tool_edit_paths({"file_path": None, "notebook_path": ""}) == []
    assert tool_edit_paths({}) == []


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


# ---------------------------------------------------------------------------
# Relative paths when the process cwd is not the project root
# ---------------------------------------------------------------------------


def _sibling_under_project(root: Path) -> Path:
    sibling = root / ".worktrees" / "sib"
    sibling.mkdir(parents=True)
    (sibling / ".git").write_text("gitdir: ../../.git/worktrees/sib\n")
    return sibling


def test_relative_sibling_path_is_blocked_when_cwd_is_elsewhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _main_checkout(tmp_path)
    _sibling_under_project(root)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    result = surface_guard_block("Write", {"file_path": f".worktrees/sib/{_RED}"}, root)

    assert result is not None
    assert RED_LANE_ID in result


def test_relative_sibling_contract_surface_is_warned_when_cwd_is_elsewhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _main_checkout(tmp_path)
    _sibling_under_project(root)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    warnings = surface_guard_warnings(
        "Edit", {"file_path": ".worktrees/sib/schemas/dcp/x.json"}, root, "sess-rel"
    )

    assert len(warnings) == 1
    assert "Contract-sensitive surface" in warnings[0]


# ---------------------------------------------------------------------------
# file_repo_root, directly
# ---------------------------------------------------------------------------


def test_file_repo_root_linked_worktree_returns_its_directory(tmp_path: Path) -> None:
    sibling = _linked_worktree(tmp_path)
    target = sibling / "pkg" / "mod.py"
    target.parent.mkdir()
    target.write_text("")

    assert file_repo_root(str(target), tmp_path / "fallback") == sibling.resolve()


def test_file_repo_root_missing_parents_returns_nearest_enclosing_repo(tmp_path: Path) -> None:
    root = _main_checkout(tmp_path)
    inner = root / "vendor" / "inner"
    inner.mkdir(parents=True)
    (inner / ".git").write_text("gitdir: elsewhere\n")
    target = inner / "a" / "b" / "c.py"
    assert not target.parent.exists()

    assert file_repo_root(str(target), tmp_path / "fallback") == inner.resolve()


def test_file_repo_root_reads_a_relative_path_against_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _main_checkout(tmp_path)
    sibling = _sibling_under_project(root)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    assert file_repo_root(".worktrees/sib/new/x.py", root) == sibling.resolve()
    assert file_repo_root("new/x.py", root) == root.resolve()


def test_file_repo_root_symlink_resolves_to_the_repo_holding_its_target(tmp_path: Path) -> None:
    sibling = _linked_worktree(tmp_path)
    real = sibling / "real.py"
    real.write_text("")
    plain = tmp_path / "plain"
    plain.mkdir()
    link = plain / "link.py"
    link.symlink_to(real)

    assert file_repo_root(str(link), tmp_path / "fallback") == sibling.resolve()


def test_file_repo_root_no_repository_returns_fallback(tmp_path: Path) -> None:
    fallback = tmp_path / "fallback"
    plain = tmp_path / "plain"
    plain.mkdir()

    assert file_repo_root(str(plain / "x" / "y.py"), fallback) == fallback


# ---------------------------------------------------------------------------
# Amendment 03: both relative readings, lexical roots, per-path warn cache
# ---------------------------------------------------------------------------


def test_cwd_relative_sibling_path_is_blocked_when_project_root_is_elsewhere(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _main_checkout(tmp_path)
    cwd = tmp_path / "cwd"
    sibling = cwd / "sibling"
    (sibling / ".git").mkdir(parents=True)
    monkeypatch.chdir(cwd)

    result = surface_guard_block("Write", {"file_path": f"sibling/{_RED}"}, root)

    assert result is not None
    assert RED_LANE_ID in result


def test_cwd_relative_sibling_contract_surface_is_warned(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = _main_checkout(tmp_path)
    cwd = tmp_path / "cwd"
    sibling = cwd / "sibling"
    (sibling / ".git").mkdir(parents=True)
    monkeypatch.chdir(cwd)

    warnings = surface_guard_warnings(
        "Edit", {"file_path": "sibling/schemas/dcp/x.json"}, root, "sess-cwd"
    )

    assert len(warnings) == 1
    assert "Contract-sensitive surface" in warnings[0]


def test_symlinked_red_lane_dir_in_sibling_checkout_is_blocked(tmp_path: Path) -> None:
    root = _main_checkout(tmp_path)
    sibling = _linked_worktree(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (sibling / "services").mkdir()
    (sibling / "services" / "task-orchestrator").symlink_to(outside)

    result = surface_guard_block("Write", {"file_path": str(sibling / _RED)}, root)

    assert result is not None
    assert RED_LANE_ID in result


def test_symlinked_file_in_sibling_red_lane_is_blocked(tmp_path: Path) -> None:
    root = _main_checkout(tmp_path)
    sibling = _linked_worktree(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "plain.py").write_text("x = 1\n")
    target = sibling / _RED
    target.parent.mkdir(parents=True)
    target.symlink_to(outside / "plain.py")

    result = surface_guard_block("Edit", {"file_path": str(target)}, root)

    assert result is not None
    assert RED_LANE_ID in result


def test_cached_first_path_does_not_hide_new_second_contract_surface(
    tmp_path: Path,
) -> None:
    root = _main_checkout(tmp_path)
    (root / ".claude").mkdir()
    catalog = str(root / "schemas" / "dcp" / "a.json")
    notebook = str(root / "schemas" / "dcp" / "x.ipynb")

    first = surface_guard_warnings("Write", {"file_path": catalog}, root, "sess-c")
    second = surface_guard_warnings(
        "NotebookEdit", {"file_path": catalog, "notebook_path": notebook}, root, "sess-c"
    )
    third = surface_guard_warnings(
        "NotebookEdit", {"file_path": catalog, "notebook_path": notebook}, root, "sess-c"
    )

    assert len(first) == 1
    assert len(second) == 1
    assert third == []


# Amendment 04: a ``..`` hop in front of a symlinked red-lane directory.


def _symlinked_red_dir(checkout: Path, outside: Path) -> None:
    outside.mkdir(exist_ok=True)
    (checkout / "services").mkdir()
    (checkout / "services" / "task-orchestrator").symlink_to(outside)


def test_traversal_prefix_to_symlinked_sibling_red_lane_is_blocked(
    tmp_path: Path,
) -> None:
    root = _main_checkout(tmp_path)
    sibling = _linked_worktree(tmp_path)
    (tmp_path / "transit").mkdir()
    _symlinked_red_dir(sibling, tmp_path / "outside")
    path = f"{tmp_path}/transit/../{sibling.name}/{_RED}"

    result = surface_guard_block("Write", {"file_path": path}, root)

    assert result is not None
    assert RED_LANE_ID in result


def test_traversal_prefix_to_symlinked_project_root_red_lane_is_blocked(
    tmp_path: Path,
) -> None:
    root = _main_checkout(tmp_path)
    (tmp_path / "transit").mkdir()
    _symlinked_red_dir(root, tmp_path / "outside")
    path = f"{tmp_path}/transit/../{root.name}/{_RED}"

    result = surface_guard_block("Write", {"file_path": path}, root)

    assert result is not None
    assert RED_LANE_ID in result


def test_traversal_prefix_to_symlinked_sibling_contract_surface_is_warned(
    tmp_path: Path,
) -> None:
    root = _main_checkout(tmp_path)
    sibling = _linked_worktree(tmp_path)
    (tmp_path / "transit").mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (sibling / "schemas").symlink_to(outside)
    path = f"{tmp_path}/transit/../{sibling.name}/schemas/dcp/x.json"

    warnings = surface_guard_warnings("Write", {"file_path": path}, root, "sess-t")

    assert len(warnings) == 1
    assert "Contract-sensitive surface" in warnings[0]


# Amendment 05: ``..`` after a symlink is resolved the way the filesystem does


def test_dotdot_after_symlink_to_ordinary_file_is_allowed(tmp_path: Path) -> None:
    root = _main_checkout(tmp_path)
    (root / "other" / "sub").mkdir(parents=True)
    (root / "other" / "services" / "task-orchestrator").mkdir(parents=True)
    (root / "link").symlink_to(root / "other" / "sub")
    # link/.. is other/, so this is other/services/..., an ordinary file
    path = f"{root}/link/../{_RED}"

    assert surface_guard_block("Write", {"file_path": path}, root) is None


def test_dotdot_after_symlink_to_ordinary_file_is_not_warned(
    tmp_path: Path,
) -> None:
    root = _main_checkout(tmp_path)
    (root / "other" / "sub").mkdir(parents=True)
    (root / "link").symlink_to(root / "other" / "sub")
    path = f"{root}/link/../schemas/dcp/x.json"

    warnings = surface_guard_warnings("Write", {"file_path": path}, root, "sess-u")

    assert warnings == []


def test_dotdot_after_symlink_into_red_lane_is_blocked(tmp_path: Path) -> None:
    root = _main_checkout(tmp_path)
    (root / "services" / "sub").mkdir(parents=True)
    (root / "link").symlink_to(root / "services" / "sub")
    # link/.. is services/, so this is the red-lane file itself
    path = f"{root}/link/../task-orchestrator/x.py"

    result = surface_guard_block("Write", {"file_path": path}, root)

    assert result is not None
    assert RED_LANE_ID in result
