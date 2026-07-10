"""Resolver core v2: pure target_id -> ResolvedTarget resolution (TP-DCP-MCP-RO-0010).

Mirrors tests/test_resolver.py's fail-closed style for the v2 gate sequence
(lookup -> enabled -> realpath -> approved-roots containment -> eligibility
-> identity -> .git-derived project_root/worktree_root -> bind policies),
plus explicit coverage for primary-checkout vs linked-worktree .git shapes.

Fixtures here build REAL temporary git workspaces/worktrees (subprocess is
test-fixture setup only — the resolver_core module under test performs no
subprocess/network/socket calls; see test_purity_* below).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Optional

import pytest

from dcp_facade.registry_v2 import parse_registry_v2
from dcp_facade.resolver_core import resolve_target


def _git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


@pytest.fixture
def build_registry_v2():
    """Build an in-memory RegistryV2 from target dicts (no file IO)."""

    def _build(targets: list[dict], approved_roots: Optional[list[str]] = None):
        doc: dict = {"targets": targets}
        if approved_roots is not None:
            doc["approved_roots"] = approved_roots
        return parse_registry_v2(doc)

    return _build


@pytest.fixture
def target_entry():
    """Helper to construct a registry v2 target dict pointing at a workspace."""

    def _entry(
        ws_path: Path,
        *,
        target_id: str = "t",
        identity_project: str = "testproj",
        identity_owner: Optional[str] = "tester",
        enabled: bool = True,
        service_policies: Optional[dict] = None,
    ) -> dict:
        identity: dict = {"project": identity_project}
        if identity_owner is not None:
            identity["owner"] = identity_owner
        return {
            "target_id": target_id,
            "workspace_path": str(ws_path),
            "enabled": enabled,
            "identity": identity,
            "service_policies": service_policies or {},
        }

    return _entry


@pytest.fixture
def make_linked_worktree(make_workspace, tmp_path_factory):
    """Build a real linked git worktree off a make_workspace primary checkout.

    Returns {"primary": Path, "worktree": Path, "head_sha": str}. Git does not
    track empty directories, so the linked worktree gets its own untracked
    ``.dopemux/`` marker (mirroring what ``make_workspace`` does for a primary
    checkout); tracked files such as ``.repo_id`` are inherited via checkout.
    """

    def _make(**workspace_kwargs) -> dict:
        primary = make_workspace(**workspace_kwargs)
        primary_path = primary["path"]
        parent = tmp_path_factory.mktemp("linked-wt-parent")
        wt_path = parent / "worktree"
        _git(
            primary_path,
            "worktree",
            "add",
            "--detach",
            "-q",
            str(wt_path),
            primary["head_sha"],
        )
        (wt_path / ".dopemux").mkdir()
        return {"primary": primary_path, "worktree": wt_path, "head_sha": primary["head_sha"]}

    return _make


# ---------------------------------------------------------------------------
# Negative branches
# ---------------------------------------------------------------------------


def test_unknown_target_blocked(build_registry_v2):
    reg = build_registry_v2([])
    resolved, reason = resolve_target(reg, "ghost")
    assert resolved is None
    assert reason


def test_non_string_target_id_blocked(build_registry_v2):
    reg = build_registry_v2([])
    resolved, reason = resolve_target(reg, None)
    assert resolved is None
    assert "required" in reason


def test_empty_string_target_id_blocked(build_registry_v2):
    reg = build_registry_v2([])
    resolved, reason = resolve_target(reg, "")
    assert resolved is None
    assert "required" in reason


def test_disabled_target_blocked(make_workspace, build_registry_v2, target_entry):
    ws = make_workspace()["path"]
    reg = build_registry_v2([target_entry(ws, target_id="t", enabled=False)])
    resolved, reason = resolve_target(reg, "t")
    assert resolved is None
    assert "disabled" in reason


def test_missing_dopemux_blocked(make_workspace, build_registry_v2, target_entry):
    ws = make_workspace(with_dopemux=False)["path"]
    reg = build_registry_v2(
        [target_entry(ws, target_id="t")], approved_roots=[str(ws.parent)]
    )
    resolved, reason = resolve_target(reg, "t")
    assert resolved is None
    assert reason


def test_identity_project_mismatch_blocked(make_workspace, build_registry_v2, target_entry):
    ws = make_workspace(project="actual")["path"]
    reg = build_registry_v2(
        [target_entry(ws, target_id="t", identity_project="expected")],
        approved_roots=[str(ws.parent)],
    )
    resolved, reason = resolve_target(reg, "t")
    assert resolved is None
    assert "identity" in reason


def test_identity_owner_mismatch_blocked_when_declared(make_workspace, build_registry_v2, target_entry):
    ws = make_workspace(project="proj", owner="real")["path"]
    reg = build_registry_v2(
        [target_entry(ws, target_id="t", identity_project="proj", identity_owner="wrong")],
        approved_roots=[str(ws.parent)],
    )
    resolved, reason = resolve_target(reg, "t")
    assert resolved is None
    assert "identity" in reason


def test_owner_check_skipped_when_not_declared(make_workspace, build_registry_v2, target_entry):
    # workspace has owner=someone, but registry declares no identity.owner -> matched on project alone
    ws = make_workspace(project="proj", owner="someone")["path"]
    reg = build_registry_v2(
        [target_entry(ws, target_id="t", identity_project="proj", identity_owner=None)],
        approved_roots=[str(ws.parent)],
    )
    resolved, reason = resolve_target(reg, "t")
    assert reason is None
    assert resolved is not None


def test_escapes_approved_roots_blocked(make_workspace, build_registry_v2, target_entry):
    ws = make_workspace()["path"]
    reg = build_registry_v2(
        [target_entry(ws, target_id="t")],
        approved_roots=["/some/unrelated/root"],
    )
    resolved, reason = resolve_target(reg, "t")
    assert resolved is None
    assert "approved roots" in reason


def test_symlink_workspace_escape_blocked(make_workspace, build_registry_v2, target_entry, tmp_path):
    ws = make_workspace()["path"]
    approved = tmp_path / "approved"
    approved.mkdir()
    link = approved / "linked_ws"
    os.symlink(ws, link)
    reg = build_registry_v2(
        [target_entry(link, target_id="t")],
        approved_roots=[str(approved)],
    )
    resolved, reason = resolve_target(reg, "t")
    assert resolved is None
    assert "approved roots" in reason


def test_missing_git_metadata_blocked(tmp_path, build_registry_v2, target_entry):
    # Eligible workspace (passes .dopemux + validate_workspace via a
    # pyproject.toml marker) but with NO .git file or directory at all.
    ws = tmp_path / "no-git"
    ws.mkdir()
    (ws / ".dopemux").mkdir()
    (ws / "pyproject.toml").write_text("", encoding="utf-8")
    (ws / ".repo_id").write_text("project=proj\n", encoding="utf-8")
    reg = build_registry_v2(
        [target_entry(ws, target_id="t", identity_project="proj", identity_owner=None)],
        approved_roots=[str(tmp_path)],
    )
    resolved, reason = resolve_target(reg, "t")
    assert resolved is None
    assert reason


def test_dopemux_present_but_workspace_validation_fails_blocked(
    tmp_path, build_registry_v2, target_entry
):
    # .dopemux/ present (the FIRST half of the eligibility gate passes) but
    # no .git and no project marker at all -> validate_workspace() itself
    # returns False (the SECOND half of the eligibility gate). Distinct from
    # test_missing_git_metadata_blocked, which passes eligibility via a
    # pyproject.toml marker and instead exercises the later .git-derivation
    # failure.
    ws = tmp_path / "no-markers"
    ws.mkdir()
    (ws / ".dopemux").mkdir()
    (ws / ".repo_id").write_text("project=proj\n", encoding="utf-8")
    reg = build_registry_v2(
        [target_entry(ws, target_id="t", identity_project="proj", identity_owner=None)],
        approved_roots=[str(tmp_path)],
    )
    resolved, reason = resolve_target(reg, "t")
    assert resolved is None
    assert reason


# ---------------------------------------------------------------------------
# Positive: primary checkout (.git is a directory; project_root == worktree_root)
# ---------------------------------------------------------------------------


def test_primary_checkout_resolves(make_workspace, build_registry_v2, target_entry):
    info = make_workspace(project="proj", owner="tester")
    ws = info["path"]
    reg = build_registry_v2(
        [target_entry(ws, target_id="t", identity_project="proj", identity_owner="tester")],
        approved_roots=[str(ws.parent)],
    )
    resolved, reason = resolve_target(reg, "t")
    assert reason is None
    assert resolved is not None
    assert resolved.target.target_id == "t"
    assert resolved.workspace == ws.resolve()
    assert resolved.project_root == ws.resolve()
    assert resolved.worktree_root == ws.resolve()


def test_primary_checkout_git_is_a_directory(make_workspace):
    ws = make_workspace()["path"]
    assert (ws / ".git").is_dir()


def test_resolved_target_binds_service_policies(make_workspace, build_registry_v2, target_entry):
    ws = make_workspace(project="proj", owner="tester")["path"]
    reg = build_registry_v2(
        [
            target_entry(
                ws,
                target_id="t",
                identity_project="proj",
                identity_owner="tester",
                service_policies={"conport": {"enabled": True}, "pal": {"enabled": False}},
            )
        ],
        approved_roots=[str(ws.parent)],
    )
    resolved, reason = resolve_target(reg, "t")
    assert reason is None
    assert set(resolved.service_policies) == {"conport", "pal"}
    assert resolved.service_policies["conport"].configured is True
    assert resolved.service_policies["pal"].configured is False


# ---------------------------------------------------------------------------
# Positive: linked worktree (.git is a gitfile; project_root != worktree_root)
# ---------------------------------------------------------------------------


def test_linked_worktree_git_is_a_file(make_linked_worktree):
    info = make_linked_worktree(project="proj", owner="tester")
    assert (info["worktree"] / ".git").is_file()


def test_linked_worktree_resolves_with_split_roots(
    make_linked_worktree, build_registry_v2, target_entry
):
    info = make_linked_worktree(project="proj", owner="tester")
    wt = info["worktree"]
    primary = info["primary"]
    reg = build_registry_v2(
        [target_entry(wt, target_id="t", identity_project="proj", identity_owner="tester")],
        approved_roots=[str(wt.parent), str(primary.parent)],
    )
    resolved, reason = resolve_target(reg, "t")
    assert reason is None
    assert resolved is not None
    assert resolved.workspace == wt.resolve()
    assert resolved.worktree_root == wt.resolve()
    assert resolved.project_root == primary.resolve()
    assert resolved.project_root != resolved.worktree_root


# ---------------------------------------------------------------------------
# Block-reason opacity (no absolute paths / ports / URLs leaked)
# ---------------------------------------------------------------------------


def test_block_reasons_never_leak_absolute_paths_ports_or_urls(
    make_workspace, build_registry_v2, target_entry
):
    ws = make_workspace()["path"]
    reasons = []

    reg = build_registry_v2([])
    _, r = resolve_target(reg, "ghost")
    reasons.append(r)

    reg = build_registry_v2([target_entry(ws, target_id="t", enabled=False)])
    _, r = resolve_target(reg, "t")
    reasons.append(r)

    reg = build_registry_v2(
        [target_entry(ws, target_id="t")], approved_roots=["/some/unrelated/root"]
    )
    _, r = resolve_target(reg, "t")
    reasons.append(r)

    reg = build_registry_v2(
        [target_entry(ws, target_id="t", identity_project="expected")],
        approved_roots=[str(ws.parent)],
    )
    _, r = resolve_target(reg, "t")
    reasons.append(r)

    for reason in reasons:
        assert reason is not None
        assert str(ws) not in reason
        assert str(ws.resolve()) not in reason
        assert "http://" not in reason
        assert "https://" not in reason


# ---------------------------------------------------------------------------
# Purity — no network/socket/subprocess/docker primitives in resolver_core.py
# ---------------------------------------------------------------------------


def test_resolver_core_module_has_no_forbidden_primitives():
    # Mirrors the commit-verify purity grep (see COMMAND_LOG.md); "docker" is
    # intentionally excluded here because "docker_mcp_gateway" is an
    # ADR-DCP-MCP-RO-0009-mandated service-family string literal in
    # registry_v2.py, not a container-inspection call — resolver_core.py
    # itself never references that literal at all.
    src_path = (
        Path(__file__).resolve().parents[1] / "src" / "dcp_facade" / "resolver_core.py"
    )
    text = src_path.read_text(encoding="utf-8")
    for token in (
        "subprocess",
        "socket.",
        "requests.",
        "httpx.",
        "urllib",
        "os.system",
        "shell=True",
    ):
        assert token not in text, f"forbidden primitive {token!r} found in resolver_core.py"
    assert "docker" not in text, "unexpected 'docker' token in resolver_core.py"
