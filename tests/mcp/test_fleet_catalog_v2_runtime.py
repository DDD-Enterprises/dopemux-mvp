"""P1 catalog-v2 compiler, join, and compatibility-projection fingerprint.

Covers Task 3 of TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-PLANE-001. The v1
catalog files (mcp_catalog.yaml, default_catalog.yaml) are never written by
this suite -- see the module docstring in fleet_catalog.py's catalog-v2
section for why cutover stays CATALOG_V2_CUTOVER=BLOCKED_NOT_APPLIED.
"""

from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import jsonschema
import pytest

from dopemux.mcp import fleet_catalog

REPO_ROOT = Path(__file__).resolve().parents[2]


def _real_v1_catalog() -> dict:
    return fleet_catalog.load_root_catalog(REPO_ROOT)


def _real_topology() -> dict:
    return json.loads((REPO_ROOT / "docs/03-reference/mcp/multiproject-service-topology.json").read_text())


def _v2_schema() -> dict:
    return fleet_catalog.load_json_schema(REPO_ROOT / "schemas/mcp/fleet-catalog-v2.schema.json")


# ---- join closure -----------------------------------------------------


def test_topology_join_is_closed_for_real_catalog():
    """All 26 topology rows are either catalog-mapped (via identity or the
    documented alias table) or explicit non-catalog infrastructure."""

    joined, unresolved, unexplained = fleet_catalog.join_catalog_topology(_real_v1_catalog(), _real_topology())
    assert unresolved == []
    assert unexplained == []
    assert len(joined) == 19


def test_join_flags_unresolved_catalog_server():
    v1 = {"servers": {"totally-unknown-server": {}}}
    joined, unresolved, unexplained = fleet_catalog.join_catalog_topology(v1, _real_topology())
    assert unresolved == ["totally-unknown-server"]
    assert joined == {}


def test_compile_raises_on_unresolved_join():
    v1 = {"servers": {"totally-unknown-server": {"transport": "http", "authority_role": "x"}}}
    with pytest.raises(fleet_catalog.CatalogTopologyJoinError):
        fleet_catalog.compile_catalog_v2(v1, _real_topology())


# ---- compiled v2 shape --------------------------------------------------


def test_compiled_v2_validates_against_schema():
    v2 = fleet_catalog.compile_catalog_v2(_real_v1_catalog(), _real_topology())
    jsonschema.validate(v2, _v2_schema())


def test_compiled_v2_drops_legacy_fields():
    v2 = fleet_catalog.compile_catalog_v2(_real_v1_catalog(), _real_topology())
    for spec in v2["servers"].values():
        assert "scope" not in spec
        assert "state_scope" not in spec
        assert "port_policy" not in spec
        assert "multi_project_singleton" not in spec
        assert "follow_on_decision" not in spec


def test_compiled_v2_sharing_class_and_flip_gate_come_from_topology():
    v2 = fleet_catalog.compile_catalog_v2(_real_v1_catalog(), _real_topology())
    conport = v2["servers"]["conport"]
    assert conport["sharing_class"] == "WORKTREE_SCOPED"
    assert conport["target_class"] == "PROJECT_SCOPED"
    assert isinstance(conport["flip_gate"], list) and len(conport["flip_gate"]) >= 1

    task_orch = v2["servers"]["task-orchestrator"]
    assert task_orch["sharing_class"] == "PROJECT_SCOPED"


def test_compiled_v2_reserved_port_passthrough():
    v2 = fleet_catalog.compile_catalog_v2(_real_v1_catalog(), _real_topology())
    assert v2["servers"]["task-orchestrator"]["reserved_port"] == 7890


def test_identity_scope_mapping_raises_on_unmapped_value():
    v1 = {
        "servers": {
            "conport": {
                "transport": "sse",
                "authority_role": "structured-context-authority",
                "identity_scope": "some-new-scope-nobody-mapped-yet",
            }
        }
    }
    with pytest.raises(fleet_catalog.MCPFleetCatalogError):
        fleet_catalog.compile_catalog_v2(v1, _real_topology())


# ---- legacy compatibility projection + fingerprint ----------------------


def test_legacy_projection_reconstructs_placement_from_defaults():
    v2 = fleet_catalog.compile_catalog_v2(_real_v1_catalog(), _real_topology())
    projected = fleet_catalog.legacy_client_projection(v2)
    assert projected["servers"]["conport"]["scope"] == "per-worktree"
    assert projected["servers"]["task-orchestrator"]["scope"] == "per-worktree"
    assert projected["servers"]["dope-memory"]["scope"] == "per-worktree"
    # serena is topology WORKTREE_SCOPED but wired today as a singleton client
    # entry -- placement must come from defaults.per_worktree, not sharing_class.
    assert projected["servers"]["serena"]["scope"] == "singleton"
    assert projected["servers"]["pal-stdio"]["scope"] == "singleton"


def test_fingerprint_equal_between_real_v1_and_legacy_projected_v2():
    """The compiler achieves zero semantic drift against the real, current
    catalog: this is the proof that would gate cutover if it were authorized
    in this packet (see CATALOG_V2_CUTOVER=BLOCKED_NOT_APPLIED reasoning)."""

    v1 = _real_v1_catalog()
    v2 = fleet_catalog.compile_catalog_v2(v1, _real_topology())
    projected = fleet_catalog.legacy_client_projection(v2)

    assert fleet_catalog.catalog_semantic_fingerprint(v1) == fleet_catalog.catalog_semantic_fingerprint(projected)


def test_default_catalog_yaml_also_achieves_zero_drift():
    """default_catalog.yaml is byte-identical to mcp_catalog.yaml today
    (asserted directly), so the same compiled v2 + projection is zero-drift
    for it too."""

    assert (REPO_ROOT / "src/dopemux/mcp/default_catalog.yaml").read_bytes() == (
        REPO_ROOT / "mcp_catalog.yaml"
    ).read_bytes()


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(lambda c: c["profiles"]["core-code"]["servers"].pop(), id="drop-profile-member"),
        pytest.param(lambda c: c["servers"]["github-official"].__setitem__("command", "docker-modified"), id="change-command"),
        pytest.param(
            lambda c: c["servers"]["task-orchestrator"].__setitem__(
                "requires_env", ["RENAMED_ENV_KEY"]
            ),
            id="rename-env-key",
        ),
        pytest.param(
            lambda c: c["servers"]["conport"].__setitem__("scope", "singleton"),
            id="flip-placement",
        ),
    ],
)
def test_fingerprint_detects_real_divergence(mutate):
    """The comparator is not a no-op: each mutation below must make the
    fingerprints diverge, proving it actually inspects the facets it claims to."""

    v1 = _real_v1_catalog()
    v2 = fleet_catalog.compile_catalog_v2(v1, _real_topology())
    projected = fleet_catalog.legacy_client_projection(v2)

    mutated = copy.deepcopy(projected)
    mutate(mutated)

    assert fleet_catalog.catalog_semantic_fingerprint(v1) != fleet_catalog.catalog_semantic_fingerprint(mutated)


def test_load_root_catalog_v2_rejects_current_v1_file():
    """The real mcp_catalog.yaml is still version 1 -- load_root_catalog_v2
    must refuse it, not silently accept or upgrade it."""

    with pytest.raises(fleet_catalog.MCPFleetCatalogError):
        fleet_catalog.load_root_catalog_v2(REPO_ROOT)


def test_load_root_catalog_v2_validates_a_v2_file(tmp_path: Path):
    import shutil

    v2 = fleet_catalog.compile_catalog_v2(_real_v1_catalog(), _real_topology())
    (tmp_path / "mcp_catalog.yaml").write_text(
        __import__("yaml").safe_dump(v2, sort_keys=False), encoding="utf-8"
    )
    schema_dir = tmp_path / "schemas/mcp"
    schema_dir.mkdir(parents=True)
    shutil.copy(
        REPO_ROOT / "schemas/mcp/fleet-catalog-v2.schema.json",
        schema_dir / "fleet-catalog-v2.schema.json",
    )
    loaded = fleet_catalog.load_root_catalog_v2(tmp_path)
    assert loaded["version"] == 2


def test_live_catalog_files_are_untouched_by_this_packet():
    """CATALOG_V2_CUTOVER=BLOCKED_NOT_APPLIED: this packet must never have
    modified the live catalog files, regardless of what the compiler proves."""

    try:
        diff = subprocess.check_output(
            ["git", "diff", "--name-only", "origin/main...HEAD"], cwd=REPO_ROOT
        ).decode()
    except subprocess.CalledProcessError:
        pytest.skip("no trusted base ref available for git diff")
    except (FileNotFoundError, OSError):
        pytest.skip("git binary not available in this environment")
    changed = set(diff.splitlines())
    assert "mcp_catalog.yaml" not in changed
    assert "src/dopemux/mcp/default_catalog.yaml" not in changed
