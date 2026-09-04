from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[2]
R2_TOPOLOGY_SHA256 = "df8636983e23c273eeb8eb517ea4019653b4c6bcb50cae344cde2e847214d4c2"
R2_FALSIFICATION_SHA256 = "84b6e68f929e5b3f3ad37e9c2843755cc38a3a119fc87b5af057505d8ed83bcb"

def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def test_ratified_r2_references_are_byte_exact():
    topology = REPO_ROOT / "docs/03-reference/mcp/multiproject-service-topology.json"
    falsification = REPO_ROOT / "docs/03-reference/mcp/multiproject-falsification-contract.md"
    assert _sha256(topology) == R2_TOPOLOGY_SHA256
    assert _sha256(falsification) == R2_FALSIFICATION_SHA256

def test_service_topology_has_exact_contract_shape():
    topology = json.loads(
        (REPO_ROOT / "docs/03-reference/mcp/multiproject-service-topology.json").read_text()
    )
    assert len(topology["services"]) == 26
    assert set(topology["sharing_classes"]) == {
        "HOST_SINGLETON",
        "PROJECT_SCOPED",
        "WORKTREE_SCOPED",
        "RETIRED",
    }


def _load_schema(name: str) -> dict:
    return json.loads((REPO_ROOT / "schemas/mcp" / name).read_text())

def _verified_identity() -> dict:
    return {
        "schema_version": "dopemux.mcp.resolved-execution-identity.v1",
        "resolution_status": "VERIFIED",
        "project_id": "project-registry-id",
        "workspace_id": "workspace-registry-id",
        "instance_id": "instance-registry-id",
        "actor_id": "operator",
        "client_id": "codex-cli",
        "registry_generation": 7,
        "mutable_routing_allowed": True,
        "aliases": [
            {
                "kind": "git_common_dir",
                "value": "/Users/example/repo/.git",
                "role": "EVIDENCE_ONLY",
            }
        ],
    }

def test_verified_identity_requires_registry_ids():
    schema = _load_schema("resolved-execution-identity.schema.json")
    jsonschema.validate(_verified_identity(), schema)

def test_unknown_identity_cannot_allow_mutation():
    schema = _load_schema("resolved-execution-identity.schema.json")
    bad = _verified_identity()
    bad["resolution_status"] = "UNKNOWN"
    bad["mutable_routing_allowed"] = True
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)

def test_alias_never_becomes_authority():
    schema = _load_schema("resolved-execution-identity.schema.json")
    bad = _verified_identity()
    bad["aliases"][0]["role"] = "AUTHORITY"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def _v2_catalog() -> dict:
    return {
        "version": 2,
        "defaults": {"worktree": ["serena"]},
        "servers": {
            "serena": {
                "sharing_class": "WORKTREE_SCOPED",
                "target_class": "WORKTREE_SCOPED",
                "transport": "http",
                "plane": "code-intelligence",
                "authority_role": "code-intelligence",
                "lifecycle": "active",
                "management_model": "compose-service",
                "identity_scope": "per-instance",
                "state_authority": "derived",
                "mutation_class": "scoped",
                "endpoint_policy": "leased",
                "probe": "mcp",
                "idle_policy": "instance_idle",
                "flip_gate": ["concurrency-safe per-request workspace implementation"],
            }
        },
    }

def test_topology_matches_schema():
    schema = _load_schema("service-topology.schema.json")
    topology = json.loads((REPO_ROOT / "docs/03-reference/mcp/multiproject-service-topology.json").read_text())
    jsonschema.validate(topology, schema)

def test_v2_catalog_matches_schema():
    schema = _load_schema("fleet-catalog-v2.schema.json")
    jsonschema.validate(_v2_catalog(), schema)

def test_legacy_fields_rejected_by_v2_schema():
    schema = _load_schema("fleet-catalog-v2.schema.json")
    bad = _v2_catalog()
    bad["servers"]["serena"]["scope"] = "worktree"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)

def test_multi_project_singleton_rejected():
    schema = _load_schema("fleet-catalog-v2.schema.json")
    bad = _v2_catalog()
    bad["servers"]["serena"]["multi_project_singleton"] = True
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


def _owned_evidence() -> dict:
    return {
        "schema_version": "dopemux.mcp.ownership-evidence.v1",
        "classification": "OWNED",
        "mutation_eligible": True,
        "registry": {"verified": True, "project_id": "p", "registry_generation": 3},
        "lease": {"verified": True, "lease_id": "lease-1"},
        "probe": {"verified": True, "service_family": "conport"},
        "storage": {"verified": True, "evidence": "project-bound mount"},
    }

def test_valid_project_scoped_lease():
    schema = _load_schema("service-lease-v2.schema.json")
    lease = {"sharing_class": "PROJECT_SCOPED", "status": "active", "project_id": "proj-1"}
    jsonschema.validate(lease, schema)

def test_valid_worktree_scoped_lease():
    schema = _load_schema("service-lease-v2.schema.json")
    lease = {"sharing_class": "WORKTREE_SCOPED", "status": "active", "project_id": "proj-1", "instance_id": "inst-1"}
    jsonschema.validate(lease, schema)

def test_invalid_worktree_lease_missing_instance_id():
    schema = _load_schema("service-lease-v2.schema.json")
    lease = {"sharing_class": "WORKTREE_SCOPED", "status": "active", "project_id": "proj-1"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(lease, schema)

def test_invalid_retired_lease():
    schema = _load_schema("service-lease-v2.schema.json")
    lease = {"sharing_class": "RETIRED", "status": "active"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(lease, schema)

def test_stale_lease_mutation_attempt():
    schema = _load_schema("ownership-evidence.schema.json")
    evidence = _owned_evidence()
    evidence["lease"]["verified"] = False
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(evidence, schema)

@pytest.mark.parametrize("missing_block", ["registry", "lease", "probe", "storage"])
def test_owned_evidence_requires_all_blocks(missing_block):
    schema = _load_schema("ownership-evidence.schema.json")
    evidence = _owned_evidence()
    del evidence[missing_block]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(evidence, schema)

def test_non_owned_classification_forces_mutation_eligible_false():
    schema = _load_schema("ownership-evidence.schema.json")
    evidence = _owned_evidence()
    evidence["classification"] = "FOREIGN"
    evidence["mutation_eligible"] = True
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(evidence, schema)



def _valid_receipt() -> dict:
    return {
        "schema_version": "dopemux.mcp.runner-materialization-receipt.v1",
        "digest": "a" * 64,
        "shared_global_config_mutated": False,
        "authority": "PROVENANCE_ONLY",
        "project_id": "proj",
        "workspace_id": "workspace",
        "instance_id": "inst",
        "inherited_surface_status": "KNOWN"
    }

def test_valid_receipt():
    schema = _load_schema("runner-materialization-receipt.schema.json")
    jsonschema.validate(_valid_receipt(), schema)

def test_receipt_rejects_global_mutation():
    schema = _load_schema("runner-materialization-receipt.schema.json")
    receipt = _valid_receipt()
    receipt["shared_global_config_mutated"] = True
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(receipt, schema)

def test_strict_receipt_rejects_unknown_surface_status():
    schema = _load_schema("runner-materialization-receipt.schema.json")
    receipt = _valid_receipt()
    receipt["mode"] = "strict"
    receipt["inherited_surface_status"] = "UNKNOWN"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(receipt, schema)

def test_receipt_authority_must_be_provenance_only():
    schema = _load_schema("runner-materialization-receipt.schema.json")
    receipt = _valid_receipt()
    receipt["authority"] = "CANONICAL"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(receipt, schema)

def _valid_event() -> dict:
    return {
        "schema_version": "dopemux.mcp.project-event-envelope.v1",
        "project_id": "proj",
        "workspace_id": "workspace",
        "instance_id": "inst",
        "registry_generation": 4,
        "source_service": "srv",
        "event_identity": "evt123",
        "payload_digest": "a" * 64,
        "stream_namespace": "ns"
    }

def test_valid_event():
    schema = _load_schema("project-event-envelope.schema.json")
    jsonschema.validate(_valid_event(), schema)

@pytest.mark.parametrize("missing_field", ["project_id", "workspace_id", "instance_id", "registry_generation", "payload_digest", "stream_namespace"])
def test_event_requires_fields(missing_field):
    schema = _load_schema("project-event-envelope.schema.json")
    event = _valid_event()
    del event[missing_field]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(event, schema)
