"""canonical_identity_summary must stay schema-complete for
schemas/mcp/resolved-execution-identity.schema.json -- a consumer trusting
its schema_version as authoritative must be able to validate the result.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from dopemux.mcp.identity import IdentityClaim, resolve_execution_identity
from dopemux.mcp.identity_registry import IdentityRegistry
from dopemux.mcp.runtime_state import canonical_identity_summary

REPO_ROOT = Path(__file__).resolve().parents[2]
IDENTITY_SCHEMA = REPO_ROOT / "schemas/mcp/resolved-execution-identity.schema.json"


def _schema() -> dict:
    return json.loads(IDENTITY_SCHEMA.read_text())


def test_summary_keys_are_superset_of_schema_dict_keys(tmp_path: Path):
    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    resolved = resolve_execution_identity(
        cwd=Path("/nowhere"), registry=reg, actor_id="operator", client_id="claude"
    )
    assert set(canonical_identity_summary(resolved).keys()) == set(resolved.to_schema_dict().keys())


@pytest.mark.parametrize(
    "claim",
    [
        None,
        IdentityClaim(project_id="prj_x", workspace_id="ws_x", instance_id="inst_x"),
    ],
)
def test_summary_validates_against_schema_for_unknown_and_conflicting(tmp_path: Path, claim):
    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    resolved = resolve_execution_identity(
        cwd=Path("/nowhere"), registry=reg, actor_id="operator", client_id="claude", claim=claim
    )
    jsonschema.validate(canonical_identity_summary(resolved), _schema())


def test_summary_validates_against_schema_for_verified(tmp_path: Path):
    reg = IdentityRegistry.load(tmp_path / "identity.json", create_missing=True)
    pid = reg.register_project(aliases=[])
    wid = reg.register_workspace(project_id=pid, aliases=[])
    reg.register_instance(
        project_id=pid, workspace_id=wid, aliases=[{"kind": "worktree_root", "value": "/repo/a"}]
    )
    resolved = resolve_execution_identity(
        cwd=Path("/repo/a"), registry=reg, actor_id="operator", client_id="claude"
    )
    assert resolved.resolution_status == "VERIFIED"
    jsonschema.validate(canonical_identity_summary(resolved), _schema())
