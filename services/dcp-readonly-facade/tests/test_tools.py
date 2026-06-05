"""Tools: enveloped, fail-closed, redacted end-to-end behavior."""

from __future__ import annotations

from dcp_facade import envelope as E
from dcp_facade import tools


def test_list_projects_enabled_only_no_path_leak(make_workspace, build_registry, project_entry):
    on = make_workspace(name="on")["path"]
    off = make_workspace(name="off")["path"]
    reg = build_registry(
        [
            project_entry(on, project_id="on", enabled=True),
            project_entry(off, project_id="off", enabled=False),
        ],
        approved_roots=[str(on.parent), str(off.parent)],
    )
    env = tools.list_projects(reg)
    assert env["status"] == E.OK
    ids = {row["project_id"] for row in env["data"]}
    assert ids == {"on"}
    # no absolute workspace path leaks into the payload
    assert str(on) not in str(env["data"])


def test_unknown_project_blocked_envelope(build_registry):
    reg = build_registry([])
    env = tools.get_repo_state_snapshot(reg, "ghost")
    assert env["status"] == E.BLOCKED
    assert env["data"] is None
    assert any("unknown project" in r for r in env["blocked_reasons"])


def test_path_like_project_id_blocked(build_registry):
    reg = build_registry([])
    env = tools.get_project_capabilities(reg, "../../etc/passwd")
    assert env["status"] == E.BLOCKED


def test_repo_state_snapshot_dirty_warning(make_workspace, build_registry, project_entry):
    info = make_workspace(dirty=True)
    ws = info["path"]
    reg = build_registry([project_entry(ws, project_id="p")], approved_roots=[str(ws.parent)])
    env = tools.get_repo_state_snapshot(reg, "p")
    assert env["status"] == E.OK
    assert env["head_sha"] == info["head_sha"]
    assert env["dirty"] is True
    assert "dirty worktree" in env["warnings"]
    assert env["authority_label"] == E.AUTHORITY_GIT


def test_capabilities_reports_configured_profiles(make_workspace, build_registry, project_entry):
    ws = make_workspace()["path"]
    reg = build_registry(
        [project_entry(ws, project_id="p", service_profiles={"conport": {"workspace_id": "w"}})],
        approved_roots=[str(ws.parent)],
    )
    env = tools.get_project_capabilities(reg, "p")
    assert env["status"] == E.OK
    caps = env["data"]["capabilities"]
    assert caps["conport"] is True
    assert caps["task_orchestrator"] is False


def test_list_proof_bundles_substring_filter(make_workspace, build_registry, project_entry):
    ws = make_workspace(bundles={"TP-A-0001": {"head_sha": "h"}, "TP-B-0002": {"head_sha": "h"}})["path"]
    reg = build_registry([project_entry(ws, project_id="p")], approved_roots=[str(ws.parent)])
    env = tools.list_proof_bundles(reg, "p", packet_id_filter="TP-A")
    assert env["status"] == E.OK
    ids = {b["bundle_id"] for b in env["data"]["bundles"]}
    assert ids == {"TP-A-0001"}


def test_list_proof_bundles_overlong_filter_blocked(make_workspace, build_registry, project_entry):
    ws = make_workspace(bundles={"TP-A-0001": {"head_sha": "h"}})["path"]
    reg = build_registry([project_entry(ws, project_id="p")], approved_roots=[str(ws.parent)])
    env = tools.list_proof_bundles(reg, "p", packet_id_filter="x" * 200)
    assert env["status"] == E.BLOCKED
    assert any("invalid packet_id_filter" in r for r in env["blocked_reasons"])


def test_fetch_proof_bundle_bad_id_blocked(make_workspace, build_registry, project_entry):
    ws = make_workspace(bundles={"TP-A-0001": {"head_sha": "h"}})["path"]
    reg = build_registry([project_entry(ws, project_id="p")], approved_roots=[str(ws.parent)])
    env = tools.fetch_proof_bundle(reg, "p", "../../etc")
    assert env["status"] == E.BLOCKED


def test_fetch_proof_bundle_redacts_secret_in_contents(make_workspace, build_registry, project_entry):
    # a proof file containing a secret must come back redacted
    ws = make_workspace(
        bundles={"TP-A-0001": {"head_sha": "h"}},
        extra_proof_files={"TP-A-0001/COMMAND_LOG.md": "leak API_KEY=supersecret12345 here\n"},
    )["path"]
    reg = build_registry([project_entry(ws, project_id="p")], approved_roots=[str(ws.parent)])
    env = tools.fetch_proof_bundle(reg, "p", "TP-A-0001")
    assert env["status"] == E.OK
    blob = str(env["data"]["contents"])
    assert "supersecret12345" not in blob
    assert E_secrets_flag(env)


def E_secrets_flag(env) -> bool:
    from dcp_facade.redaction import SECRETS

    return SECRETS in env["redactions"]
