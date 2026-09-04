"""P1 registry-backed identity: explicit registration, fail-closed resolution.

Covers Task 2 of TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001 and the
falsification-contract fixtures FX-IDENT-01..05 at unit-test granularity.
"""

from __future__ import annotations

from pathlib import Path

import jsonschema
import pytest

from dopemux.mcp.identity import (
    IdentityClaim,
    resolve_execution_identity,
)
from dopemux.mcp.identity_registry import (
    IdentityRegistry,
    IdentityRegistryError,
    default_registry_path,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
IDENTITY_SCHEMA = REPO_ROOT / "schemas/mcp/resolved-execution-identity.schema.json"


def _schema() -> dict:
    import json

    return json.loads(IDENTITY_SCHEMA.read_text())


def _validate(resolved) -> None:
    jsonschema.validate(resolved.to_schema_dict(), _schema())


# ---- registry persistence -------------------------------------------------


def test_load_missing_is_read_only(tmp_path: Path):
    reg = IdentityRegistry.load(tmp_path / "identity.json")
    assert reg.present is False
    assert reg.parse_status == "MISSING"
    assert reg.data["projects"] == {}
    assert not (tmp_path / "identity.json").exists()


def test_load_create_missing_persists_empty_registry(tmp_path: Path):
    path = tmp_path / "identity.json"
    reg = IdentityRegistry.load(path, create_missing=True)
    assert path.exists()
    assert reg.parse_status == "OK"
    assert reg.generation == 0


def test_register_project_workspace_instance_round_trip(tmp_path: Path):
    path = tmp_path / "identity.json"
    reg = IdentityRegistry.load(path, create_missing=True)
    project_id = reg.register_project(aliases=[{"kind": "project_root", "value": "/repo/a"}])
    workspace_id = reg.register_workspace(
        project_id=project_id, aliases=[{"kind": "worktree_root", "value": "/repo/a"}]
    )
    instance_id = reg.register_instance(
        project_id=project_id,
        workspace_id=workspace_id,
        aliases=[{"kind": "worktree_root", "value": "/repo/a"}],
    )
    assert project_id.startswith("prj_")
    assert workspace_id.startswith("ws_")
    assert instance_id.startswith("inst_")

    reloaded = IdentityRegistry.load(path)
    assert reloaded.parse_status == "OK"
    assert reloaded.get_instance(project_id, workspace_id, instance_id) is not None
    assert reloaded.generation == reg.generation


def test_generation_increments_monotonically(tmp_path: Path):
    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    g0 = reg.generation
    pid = reg.register_project(aliases=[])
    g1 = reg.generation
    wid = reg.register_workspace(project_id=pid, aliases=[])
    g2 = reg.generation
    reg.register_instance(project_id=pid, workspace_id=wid, aliases=[])
    g3 = reg.generation
    assert g0 < g1 < g2 < g3


def test_parse_error_blocks_mutation(tmp_path: Path):
    path = tmp_path / "identity.json"
    path.write_text("{not-json")
    reg = IdentityRegistry.load(path)
    assert reg.parse_status == "ERROR"
    with pytest.raises(IdentityRegistryError):
        reg.register_project(aliases=[])


def test_register_workspace_unknown_project_fails_closed(tmp_path: Path):
    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    with pytest.raises(IdentityRegistryError):
        reg.register_workspace(project_id="prj_does_not_exist", aliases=[])


def test_add_alias_after_relocation(tmp_path: Path):
    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid = reg.register_project(aliases=[])
    wid = reg.register_workspace(project_id=pid, aliases=[])
    iid = reg.register_instance(
        project_id=pid, workspace_id=wid, aliases=[{"kind": "worktree_root", "value": "/old/path"}]
    )
    reg.add_alias(kind="worktree_root", value="/new/path", project_id=pid, workspace_id=wid, instance_id=iid)
    instance = reg.get_instance(pid, wid, iid)
    values = {a["value"] for a in instance["aliases"]}
    assert values == {"/old/path", "/new/path"}


# ---- resolver: FX-IDENT fixtures ------------------------------------------


def test_resolver_output_always_validates_schema(tmp_path: Path):
    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    resolved = resolve_execution_identity(
        cwd=Path("/nowhere"), registry=reg, actor_id="operator", client_id="claude"
    )
    _validate(resolved)
    assert resolved.resolution_status == "UNKNOWN"
    assert resolved.mutable_routing_allowed is False


def test_unregistered_path_resolves_unknown(tmp_path: Path):
    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid = reg.register_project(aliases=[])
    wid = reg.register_workspace(project_id=pid, aliases=[])
    reg.register_instance(project_id=pid, workspace_id=wid, aliases=[{"kind": "worktree_root", "value": "/known"}])

    resolved = resolve_execution_identity(
        cwd=Path("/unregistered"), registry=reg, actor_id="operator", client_id="claude"
    )
    _validate(resolved)
    assert resolved.resolution_status == "UNKNOWN"
    assert resolved.project_id is None


def test_full_chain_alias_resolves_verified(tmp_path: Path):
    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid = reg.register_project(aliases=[])
    wid = reg.register_workspace(project_id=pid, aliases=[])
    iid = reg.register_instance(
        project_id=pid, workspace_id=wid, aliases=[{"kind": "worktree_root", "value": "/repo/a"}]
    )

    resolved = resolve_execution_identity(
        cwd=Path("/repo/a"), registry=reg, actor_id="operator", client_id="claude"
    )
    _validate(resolved)
    assert resolved.resolution_status == "VERIFIED"
    assert resolved.project_id == pid
    assert resolved.workspace_id == wid
    assert resolved.instance_id == iid
    assert resolved.mutable_routing_allowed is True
    assert resolved.registry_generation == reg.generation


def test_relative_cwd_resolves_registered_absolute_alias(tmp_path: Path, monkeypatch):
    real_dir = tmp_path / "repo"
    real_dir.mkdir()
    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid = reg.register_project(aliases=[])
    wid = reg.register_workspace(project_id=pid, aliases=[])
    iid = reg.register_instance(
        project_id=pid, workspace_id=wid, aliases=[{"kind": "worktree_root", "value": str(real_dir)}]
    )

    monkeypatch.chdir(tmp_path)
    resolved = resolve_execution_identity(
        cwd=Path("repo"), registry=reg, actor_id="operator", client_id="claude"
    )
    _validate(resolved)
    assert resolved.resolution_status == "VERIFIED"
    assert resolved.project_id == pid
    assert resolved.workspace_id == wid
    assert resolved.instance_id == iid


def test_symlinked_cwd_resolves_registered_real_path_alias(tmp_path: Path):
    real_dir = tmp_path / "real-repo"
    real_dir.mkdir()
    symlink_dir = tmp_path / "repo-link"
    symlink_dir.symlink_to(real_dir)

    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid = reg.register_project(aliases=[])
    wid = reg.register_workspace(project_id=pid, aliases=[])
    iid = reg.register_instance(
        project_id=pid, workspace_id=wid, aliases=[{"kind": "worktree_root", "value": str(real_dir)}]
    )

    resolved = resolve_execution_identity(
        cwd=symlink_dir, registry=reg, actor_id="operator", client_id="claude"
    )
    _validate(resolved)
    assert resolved.resolution_status == "VERIFIED"
    assert resolved.project_id == pid
    assert resolved.workspace_id == wid
    assert resolved.instance_id == iid


def test_fx_ident_01_identical_basenames_distinct_projects(tmp_path: Path):
    """FX-IDENT-01: identical directory basenames across two projects must
    resolve to distinct registry project_id/endpoints; no alias-based
    (basename) selection."""

    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)

    pid_a = reg.register_project(aliases=[])
    wid_a = reg.register_workspace(project_id=pid_a, aliases=[])
    reg.register_instance(
        project_id=pid_a, workspace_id=wid_a, aliases=[{"kind": "worktree_root", "value": "/proj-A/repo"}]
    )

    pid_b = reg.register_project(aliases=[])
    wid_b = reg.register_workspace(project_id=pid_b, aliases=[])
    reg.register_instance(
        project_id=pid_b, workspace_id=wid_b, aliases=[{"kind": "worktree_root", "value": "/proj-B/repo"}]
    )

    assert pid_a != pid_b

    resolved_a = resolve_execution_identity(
        cwd=Path("/proj-A/repo"), registry=reg, actor_id="operator", client_id="claude"
    )
    resolved_b = resolve_execution_identity(
        cwd=Path("/proj-B/repo"), registry=reg, actor_id="operator", client_id="claude"
    )
    _validate(resolved_a)
    _validate(resolved_b)
    assert resolved_a.project_id == pid_a
    assert resolved_b.project_id == pid_b
    assert resolved_a.project_id != resolved_b.project_id


def test_fx_ident_02_relocation_requires_new_alias(tmp_path: Path):
    """FX-IDENT-02: relocating a checkout must not change project_id/instance_id,
    but the new path only resolves after the same registry record gains an
    alias for it -- it is never re-derived."""

    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid = reg.register_project(aliases=[])
    wid = reg.register_workspace(project_id=pid, aliases=[])
    iid = reg.register_instance(
        project_id=pid, workspace_id=wid, aliases=[{"kind": "worktree_root", "value": "/old/checkout"}]
    )

    before_move = resolve_execution_identity(
        cwd=Path("/new/checkout"), registry=reg, actor_id="operator", client_id="claude"
    )
    assert before_move.resolution_status == "UNKNOWN"

    reg.add_alias(kind="worktree_root", value="/new/checkout", project_id=pid, workspace_id=wid, instance_id=iid)

    after_move = resolve_execution_identity(
        cwd=Path("/new/checkout"), registry=reg, actor_id="operator", client_id="claude"
    )
    _validate(after_move)
    assert after_move.resolution_status == "VERIFIED"
    assert after_move.project_id == pid
    assert after_move.instance_id == iid


def test_fx_ident_04_alias_collision_conflicting(tmp_path: Path):
    """FX-IDENT-04: two aliases/markers claiming one path for different
    project_ids must resolve CONFLICTING; no mutable endpoint is emitted."""

    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid_a = reg.register_project(aliases=[])
    wid_a = reg.register_workspace(project_id=pid_a, aliases=[])
    reg.register_instance(
        project_id=pid_a, workspace_id=wid_a, aliases=[{"kind": "worktree_root", "value": "/contested"}]
    )

    pid_b = reg.register_project(aliases=[])
    wid_b = reg.register_workspace(project_id=pid_b, aliases=[])
    reg.register_instance(
        project_id=pid_b, workspace_id=wid_b, aliases=[{"kind": "worktree_root", "value": "/contested"}]
    )

    resolved = resolve_execution_identity(
        cwd=Path("/contested"), registry=reg, actor_id="operator", client_id="claude"
    )
    _validate(resolved)
    assert resolved.resolution_status == "CONFLICTING"
    assert resolved.mutable_routing_allowed is False
    assert resolved.project_id is None


def test_fx_ident_05_env_claim_disagrees_with_evidence_denies(tmp_path: Path):
    """FX-IDENT-05: an ambient claim (e.g. from an env override) that
    disagrees with cwd-derived registry evidence must deny, never override
    storage selection."""

    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid_true = reg.register_project(aliases=[])
    wid_true = reg.register_workspace(project_id=pid_true, aliases=[])
    reg.register_instance(
        project_id=pid_true, workspace_id=wid_true, aliases=[{"kind": "worktree_root", "value": "/repo/real"}]
    )
    pid_other = reg.register_project(aliases=[])

    resolved = resolve_execution_identity(
        cwd=Path("/repo/real"),
        registry=reg,
        actor_id="operator",
        client_id="claude",
        claim=IdentityClaim(project_id=pid_other),
    )
    _validate(resolved)
    assert resolved.resolution_status == "CONFLICTING"
    assert resolved.mutable_routing_allowed is False


def test_wrong_workspace_claim_fails_closed(tmp_path: Path):
    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid = reg.register_project(aliases=[])
    reg.register_workspace(project_id=pid, aliases=[])

    resolved = resolve_execution_identity(
        cwd=Path("/anywhere"),
        registry=reg,
        actor_id="operator",
        client_id="claude",
        claim=IdentityClaim(project_id=pid, workspace_id="ws_does_not_exist"),
    )
    _validate(resolved)
    assert resolved.resolution_status == "CONFLICTING"


def test_unknown_project_claim_fails_closed(tmp_path: Path):
    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    resolved = resolve_execution_identity(
        cwd=Path("/anywhere"),
        registry=reg,
        actor_id="operator",
        client_id="claude",
        claim=IdentityClaim(project_id="prj_ghost"),
    )
    _validate(resolved)
    assert resolved.resolution_status == "CONFLICTING"


def test_verified_claim_without_cwd_evidence(tmp_path: Path):
    """A fully specified, registry-consistent claim can resolve VERIFIED even
    with no matching cwd evidence (e.g. a background job with a known claim)."""

    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid = reg.register_project(aliases=[])
    wid = reg.register_workspace(project_id=pid, aliases=[])
    iid = reg.register_instance(project_id=pid, workspace_id=wid, aliases=[])

    resolved = resolve_execution_identity(
        cwd=Path("/no/evidence/here"),
        registry=reg,
        actor_id="operator",
        client_id="claude",
        claim=IdentityClaim(project_id=pid, workspace_id=wid, instance_id=iid),
    )
    _validate(resolved)
    assert resolved.resolution_status == "VERIFIED"
    assert resolved.project_id == pid
    assert resolved.instance_id == iid


@pytest.mark.parametrize("missing", ["actor_id", "client_id"])
def test_missing_actor_or_client_denies(tmp_path: Path, missing: str):
    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    kwargs = {"actor_id": "operator", "client_id": "claude"}
    kwargs[missing] = ""
    resolved = resolve_execution_identity(cwd=Path("/x"), registry=reg, **kwargs)
    _validate(resolved)
    assert resolved.resolution_status == "UNKNOWN"
    assert resolved.mutable_routing_allowed is False


def test_partial_chain_match_without_instance_alias_is_unknown(tmp_path: Path):
    """A project/workspace-level alias match with no instance-level alias must
    not be promoted to VERIFIED -- instance_id is required for VERIFIED."""

    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid = reg.register_project(aliases=[{"kind": "project_root", "value": "/repo/root"}])
    reg.register_workspace(project_id=pid, aliases=[])

    resolved = resolve_execution_identity(
        cwd=Path("/repo/root"), registry=reg, actor_id="operator", client_id="claude"
    )
    _validate(resolved)
    assert resolved.resolution_status == "UNKNOWN"


def test_env_default_registry_path_override(monkeypatch, tmp_path: Path):
    path = tmp_path / "custom-identity.json"
    monkeypatch.setenv("DOPEMUX_MCP_IDENTITY_REGISTRY", str(path))
    assert default_registry_path() == path.resolve()


def test_default_registry_path_is_home_scoped_when_unset(monkeypatch):
    monkeypatch.delenv("DOPEMUX_MCP_IDENTITY_REGISTRY", raising=False)
    resolved = default_registry_path()
    assert str(resolved).endswith(".dopemux/mcp/registry/identity.json")
