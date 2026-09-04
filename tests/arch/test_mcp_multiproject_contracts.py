from __future__ import annotations

import fnmatch
import hashlib
import json
import subprocess
from pathlib import Path

import pytest
import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[2]
R2_TOPOLOGY_SHA256 = "df8636983e23c273eeb8eb517ea4019653b4c6bcb50cae344cde2e847214d4c2"
# R2 payload hash: sha256 of 04_FALSIFICATION_CONTRACT.md (bare doc, no repo frontmatter).
# REPO_DOC_FULL_FILE_HASH != R2_SUBJECT_HASH because repo requires YAML frontmatter.
# R2_PAYLOAD_AFTER_FRONTMATTER_SHA256 = 84b6e68...
# R2_ARCHITECTURE_SEMANTICS_CHANGED = NO
R2_FALSIFICATION_PAYLOAD_SHA256 = "84b6e68f929e5b3f3ad37e9c2843755cc38a3a119fc87b5af057505d8ed83bcb"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _strip_yaml_frontmatter(path: Path) -> bytes:
    """Return file bytes with YAML frontmatter stripped (everything after closing ---)."""
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    if not text.startswith("---"):
        return raw
    end = text.index("---", 3) + 3
    if text[end : end + 1] == "\n":
        end += 1
    return text[end:].encode("utf-8")


def test_ratified_r2_topology_is_byte_exact():
    """Service topology JSON must be a full-file exact copy of the R2 source."""
    topology = REPO_ROOT / "docs/03-reference/mcp/multiproject-service-topology.json"
    assert _sha256(topology) == R2_TOPOLOGY_SHA256


def test_ratified_r2_falsification_payload_is_byte_exact():
    """Falsification contract post-frontmatter payload must be byte-identical to R2 source.

    REPO_DOC_FULL_FILE_HASH != R2_SUBJECT_HASH because repo frontmatter is required.
    R2_PAYLOAD_AFTER_FRONTMATTER_SHA256 = 84b6e68...
    R2_ARCHITECTURE_SEMANTICS_CHANGED = NO
    """
    falsification = REPO_ROOT / "docs/03-reference/mcp/multiproject-falsification-contract.md"
    payload = _strip_yaml_frontmatter(falsification)
    assert hashlib.sha256(payload).hexdigest() == R2_FALSIFICATION_PAYLOAD_SHA256

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

def test_unknown_identity_requires_mutable_routing_allowed_false():
    schema = _load_schema("resolved-execution-identity.schema.json")
    bad = _verified_identity()
    bad["resolution_status"] = "UNKNOWN"
    bad["mutable_routing_allowed"] = False
    bad["project_id"] = None
    bad["workspace_id"] = None
    bad["instance_id"] = None
    bad["actor_id"] = None
    bad["client_id"] = None
    bad["registry_generation"] = None
    jsonschema.validate(bad, schema)

def test_identity_requires_mutable_routing_allowed_globally():
    schema = _load_schema("resolved-execution-identity.schema.json")
    bad = _verified_identity()
    del bad["mutable_routing_allowed"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)

def test_alias_never_becomes_authority():
    schema = _load_schema("resolved-execution-identity.schema.json")
    bad = _verified_identity()
    bad["aliases"][0]["role"] = "AUTHORITY"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)

def test_alias_rejects_nested_authority_shaped_fields():
    schema = _load_schema("resolved-execution-identity.schema.json")
    bad = _verified_identity()
    bad["aliases"][0]["project_id"] = "rogue"
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


# R1-03 negative fixtures: arbitrary / legacy vocab values must be rejected.
@pytest.mark.parametrize("field,value", [
    ("sharing_class", "GLOBAL_MAGIC"),
    ("sharing_class", "global-mutable"),
    ("target_class", "dynamic-rebind"),
    ("target_class", "GLOBAL_MAGIC"),
    ("identity_scope", "global"),
    ("identity_scope", "GLOBAL_MAGIC"),
    ("state_authority", "global-mutable"),
    ("state_authority", "GLOBAL_MAGIC"),
    ("mutation_class", "dynamic-rebind"),
    ("mutation_class", "GLOBAL_MAGIC"),
    ("endpoint_policy", "GLOBAL_MAGIC"),
    ("probe", "GLOBAL_MAGIC"),
    ("idle_policy", "GLOBAL_MAGIC"),
])
def test_arbitrary_vocab_rejected_by_v2_schema(field: str, value: str) -> None:
    schema = _load_schema("fleet-catalog-v2.schema.json")
    bad = _v2_catalog()
    bad["servers"]["serena"][field] = value
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(bad, schema)


@pytest.mark.parametrize("legacy_field", ["scope", "state_scope", "port_policy"])
def test_legacy_field_names_rejected_by_v2_schema(legacy_field: str) -> None:
    schema = _load_schema("fleet-catalog-v2.schema.json")
    bad = _v2_catalog()
    bad["servers"]["serena"][legacy_field] = "worktree"
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

def _valid_lease(sharing_class: str, **overrides) -> dict:
    base = {
        "schema_version": "dopemux.mcp.service-lease.v2",
        "lease_id": "lease-1",
        "service_id": "conport",
        "sharing_class": sharing_class,
        "registry_generation": 7,
        "owner_epoch": 1,
        "endpoint": {"transport": "http", "host": "127.0.0.1", "port": 7890},
        "owner_runtime_identity": {"runtime_kind": "conport", "runtime_id": "conport-1"},
        "status": "active",
        "created_at": "2026-09-03T00:00:00Z",
        "updated_at": "2026-09-03T00:00:00Z",
        "last_verified_at": "2026-09-03T00:00:00Z",
        "evidence_refs": ["evidence-1"],
    }
    if sharing_class in ("PROJECT_SCOPED", "WORKTREE_SCOPED"):
        base["project_id"] = "proj-1"
    if sharing_class == "WORKTREE_SCOPED":
        base["instance_id"] = "inst-1"
    base.update(overrides)
    return base

def test_valid_project_scoped_lease():
    schema = _load_schema("service-lease-v2.schema.json")
    jsonschema.validate(_valid_lease("PROJECT_SCOPED"), schema)

def test_valid_worktree_scoped_lease():
    schema = _load_schema("service-lease-v2.schema.json")
    jsonschema.validate(_valid_lease("WORKTREE_SCOPED"), schema)

def test_invalid_worktree_lease_missing_instance_id():
    schema = _load_schema("service-lease-v2.schema.json")
    lease = _valid_lease("WORKTREE_SCOPED")
    del lease["instance_id"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(lease, schema)

def test_invalid_project_lease_missing_project_id():
    schema = _load_schema("service-lease-v2.schema.json")
    lease = _valid_lease("PROJECT_SCOPED")
    del lease["project_id"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(lease, schema)

def test_invalid_retired_lease():
    schema = _load_schema("service-lease-v2.schema.json")
    lease = _valid_lease("RETIRED")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(lease, schema)

def test_lease_rejects_authority_shaped_endpoint_extra_fields():
    schema = _load_schema("service-lease-v2.schema.json")
    lease = _valid_lease("PROJECT_SCOPED")
    lease["endpoint"]["path_hash"] = "deadbeef"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(lease, schema)

def test_lease_requires_owner_runtime_identity_fields():
    schema = _load_schema("service-lease-v2.schema.json")
    lease = _valid_lease("PROJECT_SCOPED")
    del lease["owner_runtime_identity"]["runtime_id"]
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
        "authority": "PROVENANCE_ONLY",
        "materialization_id": "mat-1",
        "project_id": "proj",
        "workspace_id": "workspace",
        "instance_id": "inst",
        "registry_generation": 5,
        "runner_family": "codex",
        "profile": "default",
        "catalog_digest": "b" * 64,
        "rendered_config_digest": "c" * 64,
        "lease_refs": ["lease-1"],
        "generated_at": "2026-09-03T00:00:00Z",
        "shared_global_config_mutated": False,
        "strict_mode": False,
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
    receipt["strict_mode"] = True
    receipt["inherited_surface_status"] = "UNKNOWN"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(receipt, schema)

def test_receipt_authority_must_be_provenance_only():
    schema = _load_schema("runner-materialization-receipt.schema.json")
    receipt = _valid_receipt()
    receipt["authority"] = "CANONICAL"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(receipt, schema)

def test_receipt_rejects_bad_catalog_digest_format():
    schema = _load_schema("runner-materialization-receipt.schema.json")
    receipt = _valid_receipt()
    receipt["catalog_digest"] = "ZZ" * 32
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(receipt, schema)

def test_receipt_rejects_unknown_runner_family():
    schema = _load_schema("runner-materialization-receipt.schema.json")
    receipt = _valid_receipt()
    receipt["runner_family"] = "not-a-runner"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(receipt, schema)

def _valid_event() -> dict:
    return {
        "schema_version": "dopemux.mcp.project-event-envelope.v1",
        "event_id": "evt-1",
        "event_type": "status_changed",
        "emitted_at": "2026-09-03T00:00:00Z",
        "source_service_id": "task-orchestrator",
        "project_id": "proj",
        "workspace_id": "workspace",
        "instance_id": "inst",
        "registry_generation": 4,
        "payload_digest": "a" * 64,
        "stream_namespace": "ns",
        "sequence": 12,
        "replay_key": "replay-1"
    }

def test_valid_event():
    schema = _load_schema("project-event-envelope.schema.json")
    jsonschema.validate(_valid_event(), schema)

@pytest.mark.parametrize("missing_field", ["event_id", "event_type", "emitted_at", "source_service_id", "project_id", "workspace_id", "instance_id", "registry_generation", "payload_digest", "stream_namespace", "sequence", "replay_key"])
def test_event_requires_fields(missing_field):
    schema = _load_schema("project-event-envelope.schema.json")
    event = _valid_event()
    del event[missing_field]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(event, schema)

def test_event_rejects_negative_registry_generation():
    schema = _load_schema("project-event-envelope.schema.json")
    event = _valid_event()
    event["registry_generation"] = -1
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(event, schema)

def test_event_rejects_negative_sequence():
    schema = _load_schema("project-event-envelope.schema.json")
    event = _valid_event()
    event["sequence"] = -1
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(event, schema)

def test_event_rejects_bad_payload_digest():
    schema = _load_schema("project-event-envelope.schema.json")
    event = _valid_event()
    event["payload_digest"] = "not-a-hex-digest"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(event, schema)

def test_service_topology_targets_and_eligibility():
    topology = json.loads((REPO_ROOT / "docs/03-reference/mcp/multiproject-service-topology.json").read_text())
    services = {s["SERVICE_ID"]: s for s in topology["services"]}

    conport = services["conport"]
    assert conport["TARGET_CLASS"] == "PROJECT_SCOPED"
    assert conport["ELIGIBLE_FOR_TARGET_NOW"] is False

    dope_memory = services["dope-memory"]
    assert dope_memory["TARGET_CLASS"] == "PROJECT_SCOPED"
    assert "HOST_SINGLETON only after" in dope_memory["DEFERRED_OPTION"]

    serena = services["serena"]
    assert serena["TARGET_CLASS"] == "WORKTREE_SCOPED"

    redis_events = services["redis-events"]
    assert redis_events["TARGET_CLASS"] == "PROJECT_SCOPED"

    task_orch = services["task-orchestrator-kotlin"]
    assert "multi_project_singleton" not in str(task_orch)

def test_p5_before_p4_dag():
    adr = (REPO_ROOT / "docs/90-adr/adr-dmx-mcp-multiproject-identity-sharing-contract-001.md").read_text()
    assert "redis-events logical -> PROJECT_SCOPED before dope-memory consolidation" in adr

FORBIDDEN_P0_PREFIXES = [
    "mcp_catalog.yaml",
    "src/dopemux/mcp/",
    "src/dopemux/commands/mcp_commands.py",
    "services/",
    "docker/",
    ".mcp.json",
]

# Repository-root compose files (compose.yml/compose.yaml/compose.*.yml/compose.*.yaml)
# are runtime surfaces for the MCP fleet and must never be mutated by this packet series.
ROOT_COMPOSE_PATTERNS = [
    "compose.yml",
    "compose.yaml",
    "compose.*.yml",
    "compose.*.yaml",
]

def _is_forbidden_p0_path(fpath: str) -> bool:
    if any(fpath.startswith(prefix) for prefix in FORBIDDEN_P0_PREFIXES):
        return True
    if "/" in fpath:
        return False
    return any(fnmatch.fnmatch(fpath, pattern) for pattern in ROOT_COMPOSE_PATTERNS)

@pytest.mark.parametrize("fpath", [
    "compose.yml",
    "compose.yaml",
    "compose.override.yml",
    "compose.dev.yaml",
])
def test_root_compose_file_is_forbidden(fpath):
    assert _is_forbidden_p0_path(fpath)

@pytest.mark.parametrize("fpath", [
    "README.md",
    "docs/compose.yml",
    "composefile.yml",
    "compose.override",
    "task-packets/INDEX.md",
])
def test_non_root_or_non_compose_path_is_allowed(fpath):
    assert not _is_forbidden_p0_path(fpath)

# P0's own merge range (base parent -> merge commit of PR #1306, "freeze
# multiproject P0 identity and sharing contracts"). This asserts a permanent,
# historical fact about the P0 packet itself -- it must never have touched a
# forbidden runtime path -- rather than gating the live branch diff.
#
# The original version of this test compared origin/main...HEAD, which meant
# it would fail for every future MCP tranche (P1 through P8) the instant it
# touched src/dopemux/mcp/** -- exactly what those tranches are chartered to
# do. That made the test internally inconsistent with its own packet series:
# discovered while implementing TP-DMX-MCP-MULTIPROJECT-P1-FLEET-CONTROL-
# PLANE-001, whose verify command list includes this file. Operator-authorized
# fix, recorded in that packet's implementation-notes.md.
P0_MERGE_RANGE = ("2b00c648e", "a8a7514b4")


def test_no_runtime_effect_diff():
    try:
        diff_out = subprocess.check_output(
            ["git", "diff", "--name-only", *P0_MERGE_RANGE]
        ).decode()
        changed = diff_out.splitlines()
        for c in changed:
            if _is_forbidden_p0_path(c):
                pytest.fail(f"Forbidden path mutated in P0's own merge range: {c}")
    except subprocess.CalledProcessError:
        pytest.skip("P0 merge range not available in this checkout")
    except (FileNotFoundError, OSError):
        pytest.skip("git binary not available in this environment")
