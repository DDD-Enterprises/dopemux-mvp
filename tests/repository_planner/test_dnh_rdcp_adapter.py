from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from dopemux.repository_planner.adapters.dnh_rdcp import DnhRdcpExtensionAdapter
from dopemux.repository_planner.extensions import load_extension_adapters
from dopemux.repository_planner.models import SourceSnapshot
from dopemux.repository_planner.planner import build_portfolio

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_ROOT = ROOT / "reports/project-control-plane/fixtures/dnh_crm_fixture"
SCHEMA_ROOT = ROOT / "schemas/dnh_extension"
PINNED_HEAD = "92eb632bb07426ae5159c02bf9da549888e7caf1"
EXPECTED_STATES = {
    "CURRENT",
    "STALE",
    "MISSING",
    "UNREADABLE",
    "UNPARSEABLE",
    "MIXED_SHA",
    "UNKNOWN",
}


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def _adapter() -> DnhRdcpExtensionAdapter:
    return DnhRdcpExtensionAdapter()


def _copy_adapter_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    shutil.copytree(
        ROOT / "schemas/project_control_plane",
        root / "schemas/project_control_plane",
    )
    shutil.copytree(SCHEMA_ROOT, root / "schemas/dnh_extension")
    shutil.copytree(
        FIXTURE_ROOT,
        root / "reports/project-control-plane/fixtures/dnh_crm_fixture",
    )
    return root


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(
        (item for item in root.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(root).as_posix().encode("utf-8"),
    ):
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def test_fixture_is_source_backed_and_contains_no_local_or_placeholder_data() -> None:
    inventory = _load(FIXTURE_ROOT / "SOURCES.json")
    profile = _load(FIXTURE_ROOT / "project_profile.json")
    evidence = _load(FIXTURE_ROOT / "evidence_export.json")

    assert inventory["schema_version"] == "dnh.rdcp_source_inventory.v1"
    assert inventory["repository"] == "DDD-Enterprises/dnh-crm"
    assert inventory["pinned_head"] == PINNED_HEAD
    assert profile["project_id"] == "DDD-Enterprises/dnh-crm"
    assert evidence["project_id"] == "DDD-Enterprises/dnh-crm"
    assert evidence["repo_state"]["head_sha"] == PINNED_HEAD  # type: ignore[index]

    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            FIXTURE_ROOT / "SOURCES.json",
            FIXTURE_ROOT / "project_profile.json",
            FIXTURE_ROOT / "evidence_export.json",
        )
    )
    assert "PLACEHOLDER" not in text
    assert "/Users/" not in text
    assert "/private/" not in text
    assert "token=" not in text.lower()

    sources = {item["role"]: item for item in inventory["sources"]}  # type: ignore[index]
    assert {
        "authority",
        "active_packet",
        "rdcp_architecture",
        "proof_pointer_schema",
        "proof_pointer",
        "proof_pointer_manifest",
        "source_ledger_schema",
        "source_ledger",
        "review_item_schema",
        "thread_dispositions_schema",
        "review_sensor_receipt",
        "review_item_output",
        "thread_dispositions_output",
        "task_orchestrator_export_schema",
        "task_orchestrator_export",
    } <= set(sources)
    for role, source in sources.items():
        assert source["privacy_class"] == "PRIVATE_REPOSITORY_METADATA"
        assert source["redaction_notes"]
        if source["state"] == "PRESENT":
            assert len(source["blob_sha"]) == 40
            assert len(source["sha256"]) == 64
            assert f"/blob/{PINNED_HEAD}/" in source["url"]
        else:
            assert role in {"review_item_output", "thread_dispositions_output"}
            assert source["state"] == "MISSING"
            assert source["blob_sha"] is None
            assert source["sha256"] is None


def test_fixture_and_extension_schemas_validate() -> None:
    for instance_name, schema_name in (
        ("project_profile.json", "project_profile.schema.json"),
        ("evidence_export.json", "project_evidence_export.schema.json"),
    ):
        instance = _load(FIXTURE_ROOT / instance_name)
        schema = _load(ROOT / "schemas/project_control_plane" / schema_name)
        assert list(Draft202012Validator(schema).iter_errors(instance)) == []

    manifest = _load(SCHEMA_ROOT / "extension_manifest.dnh.json")
    manifest_schema = _load(
        ROOT / "schemas/project_control_plane/extension_manifest.schema.json"
    )
    assert list(Draft202012Validator(manifest_schema).iter_errors(manifest)) == []
    assert manifest["extension_kind"] == "DNH_CRM"
    assert all(manifest["invariants"].values())  # type: ignore[union-attr]
    assert manifest["capabilities"]["runtime_mappings"] == []  # type: ignore[index]
    assert manifest["capabilities"]["adapter_mappings"] == [  # type: ignore[index]
        "dopemux.repository_planner.adapters.dnh_rdcp:DnhRdcpExtensionAdapter"
    ]

    source_map = _load(SCHEMA_ROOT / "rdcp_source_map.dnh.json")
    assert source_map["schema_version"] == "dnh.rdcp_source_map.v1"
    assert set(source_map["freshness_states"]) == EXPECTED_STATES
    assert source_map["task_orchestrator"]["authority"] == "NONE"  # type: ignore[index]
    assert source_map["task_orchestrator"]["is_proof"] is False  # type: ignore[index]


def test_adapter_registration_and_identity_matching_are_closed() -> None:
    adapters = load_extension_adapters([SCHEMA_ROOT / "extension_manifest.dnh.json"])
    assert len(adapters) == 1
    adapter = adapters[0]
    assert adapter.extension_id == "dnh-crm-rdcp"
    assert adapter.matches({"project_id": "DDD-Enterprises/dnh-crm"}) is True
    assert adapter.matches({"project_id": "dnh-crm"}) is False
    assert adapter.matches({"project_id": "DDD-Enterprises/dNh-CRM"}) is False
    assert adapter.matches({}) is False


def test_adapter_exposes_four_inert_fail_closed_lanes() -> None:
    generic_export = _load(FIXTURE_ROOT / "evidence_export.json")

    snapshot = _adapter().enrich(generic_export, ROOT)

    assert isinstance(snapshot, SourceSnapshot)
    assert snapshot.project_id == "DDD-Enterprises/dnh-crm"
    assert snapshot.authority == "NONE"
    assert snapshot.surface_class == "PROJECTION"
    assert snapshot.is_proof is False
    assert snapshot.observed_head == PINNED_HEAD
    assert snapshot.freshness == "UNKNOWN"

    lanes = {lane.lane_id: lane for lane in snapshot.lanes}
    assert set(lanes) == {
        "rdcp-proof-pointer",
        "rdcp-source-ledger",
        "rdcp-review-sensor",
        "rdcp-task-orchestrator",
    }
    assert all(lane.gate_status == "FAIL" for lane in lanes.values())
    assert all(lane.audit_status == "UNKNOWN" for lane in lanes.values())
    assert lanes["rdcp-proof-pointer"].lifecycle_state == "STALE"
    assert lanes["rdcp-source-ledger"].lifecycle_state == "MIXED_SHA"
    assert lanes["rdcp-review-sensor"].lifecycle_state == "MISSING"
    assert lanes["rdcp-task-orchestrator"].lifecycle_state == "UNKNOWN"

    claims = {(claim.lane_id, claim.field): claim for claim in snapshot.claims}
    assert claims[("rdcp-review-sensor", "rdcp_status")].value == "MISSING"
    assert claims[("rdcp-task-orchestrator", "authority")].value == "NONE"
    assert claims[("rdcp-task-orchestrator", "is_proof")].value == "false"
    assert claims[("rdcp-task-orchestrator", "export_mode")].value == "ARTIFACT_ONLY"
    assert claims[("rdcp-proof-pointer", "auditor_identity")].value == "UNKNOWN"
    assert all(claim.freshness == "UNKNOWN" for claim in snapshot.claims)


def test_proof_and_source_head_disagreements_remain_explicit() -> None:
    snapshot = _adapter().enrich(_load(FIXTURE_ROOT / "evidence_export.json"), ROOT)
    claims = {(claim.claim_id, claim.value) for claim in snapshot.claims}

    assert ("dnh:proof-pointer:candidate-head", PINNED_HEAD) in claims
    assert (
        "dnh:proof-pointer:proof-head",
        "c0818fe8e29bdeb8d14986f2500592f3acdb5cc8",
    ) in claims
    assert ("dnh:source-ledger:candidate-head", PINNED_HEAD) in claims
    assert (
        "dnh:source-ledger:artifact-head",
        "300fae3bdf77124a7a0ed9e64feb9a65bc84f111",
    ) in claims
    assert all(
        claim.materiality == "BLOCKING"
        for claim in snapshot.claims
        if claim.field in {"proof_head", "source_head"}
    )


def test_planner_reconciles_head_disagreements_visibly_and_never_advances() -> None:
    snapshot = _adapter().enrich(_load(FIXTURE_ROOT / "evidence_export.json"), ROOT)

    portfolio = build_portfolio((snapshot,))

    conflicts = {
        (conflict.lane_id, conflict.field): conflict for conflict in portfolio.conflicts
    }
    assert set(conflicts) == {
        ("rdcp-proof-pointer", "proof_head"),
        ("rdcp-source-ledger", "source_head"),
    }
    assert all(
        conflict.materiality == "BLOCKING"
        and conflict.status == "OPEN"
        and conflict.resolution_authority == "SOURCE_REPOSITORY"
        for conflict in conflicts.values()
    )
    recommendations = {
        item.lane_id: item.disposition for item in portfolio.recommendations
    }
    assert recommendations["rdcp-proof-pointer"] == "DEFER_BLOCKING_CONFLICT"
    assert recommendations["rdcp-source-ledger"] == "DEFER_BLOCKING_CONFLICT"
    assert recommendations["rdcp-review-sensor"] == "UNKNOWN"
    assert recommendations["rdcp-task-orchestrator"] == "UNKNOWN"
    assert "READY_FOR_CONTROL_TOWER_REVIEW" not in recommendations.values()


@pytest.mark.parametrize(
    "rdcp_state", ["UNREADABLE", "UNPARSEABLE", "MIXED_SHA", "UNKNOWN"]
)
def test_rdcp_states_are_preserved_without_becoming_passes(
    tmp_path: Path, rdcp_state: str
) -> None:
    root = _copy_adapter_root(tmp_path)
    source_map_path = root / "schemas/dnh_extension/rdcp_source_map.dnh.json"
    source_map = _load(source_map_path)
    source_map["lanes"][0]["observed_state"] = rdcp_state  # type: ignore[index]
    source_map_path.write_text(json.dumps(source_map), encoding="utf-8")

    snapshot = _adapter().enrich(_load(FIXTURE_ROOT / "evidence_export.json"), root)
    lane = next(item for item in snapshot.lanes if item.lane_id == "rdcp-proof-pointer")
    status = next(
        claim
        for claim in snapshot.claims
        if claim.lane_id == lane.lane_id and claim.field == "rdcp_status"
    )
    assert status.value == rdcp_state
    assert lane.lifecycle_state == rdcp_state
    assert lane.gate_status == "FAIL"


def test_malformed_input_path_escape_and_inventory_conflict_fail_closed(
    tmp_path: Path,
) -> None:
    root = _copy_adapter_root(tmp_path)
    generic_export = _load(FIXTURE_ROOT / "evidence_export.json")

    malformed = json.loads(json.dumps(generic_export))
    del malformed["repo_state"]
    with pytest.raises(ValueError, match="schema validation"):
        _adapter().enrich(malformed, root)

    source_map_path = root / "schemas/dnh_extension/rdcp_source_map.dnh.json"
    source_map = _load(source_map_path)
    source_map["lanes"][0]["source_roles"].append("escape")  # type: ignore[index]
    source_map["sources"]["escape"] = {  # type: ignore[index]
        "path": "../outside.json",
        "expected_schema_version": "1.0.0",
    }
    source_map_path.write_text(json.dumps(source_map), encoding="utf-8")
    with pytest.raises(ValueError, match="path escape"):
        _adapter().enrich(generic_export, root)

    shutil.copy2(SCHEMA_ROOT / "rdcp_source_map.dnh.json", source_map_path)
    inventory_path = (
        root / "reports/project-control-plane/fixtures/dnh_crm_fixture/SOURCES.json"
    )
    inventory = _load(inventory_path)
    inventory["sources"][0]["blob_sha"] = "0" * 40  # type: ignore[index]
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")
    with pytest.raises(ValueError, match="frozen source inventory"):
        _adapter().enrich(generic_export, root)


def test_adapter_validates_normalized_proof_pointer_and_manifest_bytes(
    tmp_path: Path,
) -> None:
    root = _copy_adapter_root(tmp_path)
    inventory_path = (
        root / "reports/project-control-plane/fixtures/dnh_crm_fixture/SOURCES.json"
    )
    inventory = _load(inventory_path)
    inventory["normalized_artifacts"]["proof_pointer"]["content"]["proof"][  # type: ignore[index]
        "validation_status"
    ] = "FAIL"
    inventory_path.write_text(json.dumps(inventory), encoding="utf-8")

    with pytest.raises(ValueError, match="normalized proof_pointer bytes"):
        _adapter().enrich(_load(FIXTURE_ROOT / "evidence_export.json"), root)


def test_adapter_is_read_only_and_does_not_mutate_generic_export(
    tmp_path: Path,
) -> None:
    root = _copy_adapter_root(tmp_path)
    generic_export = _load(FIXTURE_ROOT / "evidence_export.json")
    original = json.loads(json.dumps(generic_export))
    before = _tree_digest(root)

    _adapter().enrich(generic_export, root)

    assert _tree_digest(root) == before
    assert generic_export == original
