"""Resolver: fail-closed eligibility + identity (the §5 flow)."""

from __future__ import annotations

import os

from dcp_facade.resolver import resolve


def test_unknown_project_blocked(build_registry):
    reg = build_registry([])
    res, reason = resolve(reg, "ghost")
    assert res is None
    assert "unknown project" in reason


def test_non_string_project_id_blocked(build_registry):
    reg = build_registry([])
    res, reason = resolve(reg, None)
    assert res is None
    assert "required" in reason


def test_disabled_project_blocked(make_workspace, build_registry, project_entry):
    ws = make_workspace()["path"]
    reg = build_registry([project_entry(ws, project_id="p", enabled=False)])
    res, reason = resolve(reg, "p")
    assert res is None
    assert "disabled" in reason


def test_missing_dopemux_blocked(make_workspace, build_registry, project_entry):
    ws = make_workspace(with_dopemux=False)["path"]
    reg = build_registry([project_entry(ws, project_id="p")], approved_roots=[str(ws.parent)])
    res, reason = resolve(reg, "p")
    assert res is None
    assert ".dopemux" in reason


def test_identity_project_mismatch_blocked(make_workspace, build_registry, project_entry):
    ws = make_workspace(project="actual")["path"]
    reg = build_registry(
        [project_entry(ws, project_id="p", identity_project="expected")],
        approved_roots=[str(ws.parent)],
    )
    res, reason = resolve(reg, "p")
    assert res is None
    assert "project does not match" in reason


def test_identity_owner_mismatch_blocked_when_declared(make_workspace, build_registry, project_entry):
    ws = make_workspace(project="proj", owner="real")["path"]
    reg = build_registry(
        [project_entry(ws, project_id="p", identity_project="proj", identity_owner="wrong")],
        approved_roots=[str(ws.parent)],
    )
    res, reason = resolve(reg, "p")
    assert res is None
    assert "owner does not match" in reason


def test_owner_check_skipped_when_not_declared(make_workspace, build_registry, project_entry):
    # workspace has owner=someone, but registry declares no identity.owner → matched on project alone
    ws = make_workspace(project="proj", owner="someone")["path"]
    reg = build_registry(
        [project_entry(ws, project_id="p", identity_project="proj", identity_owner=None)],
        approved_roots=[str(ws.parent)],
    )
    res, reason = resolve(reg, "p")
    assert reason is None
    assert res is not None


def test_escapes_approved_roots_blocked(make_workspace, build_registry, project_entry):
    ws = make_workspace()["path"]
    reg = build_registry(
        [project_entry(ws, project_id="p")],
        approved_roots=["/some/unrelated/root"],
    )
    res, reason = resolve(reg, "p")
    assert res is None
    assert "approved roots" in reason


def test_symlink_workspace_escape_blocked(make_workspace, build_registry, project_entry, tmp_path):
    ws = make_workspace()["path"]
    # a symlink that lives under an approved root but points at ws outside it
    approved = tmp_path / "approved"
    approved.mkdir()
    link = approved / "linked_ws"
    os.symlink(ws, link)
    reg = build_registry(
        [project_entry(link, project_id="p")],
        approved_roots=[str(approved)],
    )
    res, reason = resolve(reg, "p")
    # realpath of the symlink resolves to ws which is outside `approved` → blocked
    assert res is None
    assert "approved roots" in reason


def test_happy_path_resolves(make_workspace, build_registry, project_entry):
    info = make_workspace(project="proj", owner="tester")
    ws = info["path"]
    reg = build_registry(
        [project_entry(ws, project_id="p", identity_project="proj", identity_owner="tester")],
        approved_roots=[str(ws.parent)],
    )
    res, reason = resolve(reg, "p")
    assert reason is None
    assert res is not None
    assert res.project.project_id == "p"
    assert res.workspace == ws.resolve()
