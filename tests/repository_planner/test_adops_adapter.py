from __future__ import annotations

import json
import shutil
from pathlib import Path

from jsonschema import Draft202012Validator

from dopemux.repository_planner.extensions import load_extension_adapters
from dopemux.repository_planner.models import SourceSnapshot


ROOT = Path(__file__).parents[2]
FIXTURE_ROOT = ROOT / "reports/project-control-plane/fixtures/adops_fixture"
SCHEMA_ROOT = ROOT / "schemas/adops_extension"
PINNED_HEAD = "864915b9cc8ff254eaa877627df1e510dc49dbec"
LEGACY_LOCAL_ONLY = "4ce6b644afa72231c24b3cdac58f251e1ca03321"


def _load(path: Path) -> dict[str, object]:
    assert path.is_file(), f"required fixture is missing: {path.relative_to(ROOT)}"
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _assert_valid(instance: dict[str, object], schema_path: Path) -> None:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=str)
    assert not errors, [error.message for error in errors]


def _adapter():
    module_path = ROOT / "src/dopemux/repository_planner/adapters/adops.py"
    assert module_path.is_file(), "AdOps adapter module is missing"
    from dopemux.repository_planner.adapters.adops import AdOpsExtensionAdapter

    return AdOpsExtensionAdapter()


def test_frozen_fixture_validates_against_generic_pcp_contracts() -> None:
    profile = _load(FIXTURE_ROOT / "project_profile.json")
    export = _load(FIXTURE_ROOT / "evidence_export.json")

    _assert_valid(
        profile,
        ROOT / "schemas/project_control_plane/project_profile.schema.json",
    )
    _assert_valid(
        export,
        ROOT / "schemas/project_control_plane/project_evidence_export.schema.json",
    )
    assert export["repo_state"]["head_sha"] == PINNED_HEAD  # type: ignore[index]
    assert export["proof_manifest"] == {  # type: ignore[index]
        "state": "PRESENT",
        "path": "proof/TP-ADOPS-ELITELUXE24-MODE-V1/IMPLEMENTER_REPORT.md",
        "freshness": "STALE",
    }


def test_source_inventory_is_pinned_redacted_and_fail_closed() -> None:
    inventory = _load(FIXTURE_ROOT / "SOURCES.json")
    sources = inventory["sources"]
    assert isinstance(sources, list)
    assert inventory["pinned_head"] == PINNED_HEAD
    assert inventory["legacy_candidate"] == {
        "commit_sha": LEGACY_LOCAL_ONLY,
        "status": "REMOTE_COMMIT_ABSENT",
        "verification": "GitHub commits API returned no commit for the exact SHA",
    }

    required = {
        "PROJECT_INSTRUCTIONS.md",
        ".claude/PROJECT_INSTRUCTIONS.md",
        ".github/copilot-instructions.md",
        "task-packets/ACTIVE.md",
        "task-packets/TP-ADOPS-ELITELUXE24-MODE-V1.md",
        "proof/TP-ADOPS-ELITELUXE24-MODE-V1/01_head_binding.txt",
        "proof/TP-ADOPS-ELITELUXE24-MODE-V1/IMPLEMENTER_REPORT.md",
        "proof/TP-ADOPS-ELITELUXE24-MODE-V1/AUDITOR_REPORT.md",
        "acceptance/TP-ADOPS-ELITELUXE24-MODE-V1.json",
    }
    assert {source["path"] for source in sources} == required
    for source in sources:
        assert source["privacy_class"] == "PUBLIC_REPOSITORY"
        assert source["fetched_at"].endswith("Z")
        assert not source["path"].startswith("/")
        assert "Downloads" not in json.dumps(source)
        if source["state"] == "PRESENT":
            assert len(source["blob_sha"]) == 40
            assert len(source["sha256"]) == 64
            assert source["url"].startswith(
                f"https://github.com/DDD-Enterprises/adOps/blob/{PINNED_HEAD}/"
            )
        else:
            assert source["state"] == "ABSENT"
            assert source["blob_sha"] is None
            assert source["sha256"] is None

    pr = inventory["github_observations"][0]  # type: ignore[index]
    assert pr["locator"] == "https://github.com/DDD-Enterprises/adOps/pull/277"
    assert pr["classification"] == "DESIGN_EVIDENCE_ONLY"
    assert pr["implementation_acceptance"] is False
    assert pr["state"] == "open"
    assert pr["draft"] is True


def test_additive_extension_files_validate_and_preserve_authority_order() -> None:
    manifest = _load(SCHEMA_ROOT / "extension_manifest.adops.json")
    authority = _load(SCHEMA_ROOT / "authority_map.adops.json")
    red_lanes = _load(SCHEMA_ROOT / "red_lanes.adops.json")

    _assert_valid(
        manifest,
        ROOT / "schemas/project_control_plane/extension_manifest.schema.json",
    )
    _assert_valid(
        authority,
        ROOT / "schemas/project_control_plane/authority_map.schema.json",
    )
    _assert_valid(
        red_lanes,
        ROOT / "schemas/project_control_plane/project_red_lanes.schema.json",
    )
    assert manifest["status"] == "PROPOSED"
    assert manifest["extension_kind"] == "PROJECT"
    assert all(manifest["invariants"].values())  # type: ignore[union-attr]

    authority_refs = authority["entries"][0]["source_truth_refs"]  # type: ignore[index]
    assert authority_refs[:3] == [
        "PROJECT_INSTRUCTIONS.md",
        ".github/copilot-instructions.md",
        ".claude/PROJECT_INSTRUCTIONS.md",
    ]
    forbidden_owners = {"github", "task-orchestrator", "repository-planner"}
    for entry in authority["entries"]:  # type: ignore[union-attr]
        assert entry["canonical_authority_owner"] not in forbidden_owners
        assert entry["canonical_writer"] is None
        assert entry["live_write_allowed"] is False
        assert entry["unknown_behavior"] == "BLOCK_OR_ESCALATE"


def test_adapter_registration_and_identity_matching_are_closed() -> None:
    adapters = load_extension_adapters(
        [SCHEMA_ROOT / "extension_manifest.adops.json"]
    )
    assert len(adapters) == 1
    adapter = adapters[0]
    assert adapter.extension_id == "adops-project"
    assert adapter.matches({"project_id": "DDD-Enterprises/adOps"}) is True
    assert adapter.matches({"project_id": "adOps"}) is False
    assert adapter.matches({"project_id": "DDD-Enterprises/adops"}) is False
    assert adapter.matches({}) is False


def test_adapter_projects_stale_unknown_and_design_evidence_without_authority() -> None:
    generic_export = _load(FIXTURE_ROOT / "evidence_export.json")

    snapshot = _adapter().enrich(generic_export, ROOT)

    assert isinstance(snapshot, SourceSnapshot)
    assert snapshot.authority == "NONE"
    assert snapshot.surface_class == "PROJECTION"
    assert snapshot.is_proof is False
    assert snapshot.project_id == "DDD-Enterprises/adOps"
    assert snapshot.observed_head == PINNED_HEAD
    assert snapshot.freshness == "STALE"
    assert len(snapshot.lanes) == 1
    lane = snapshot.lanes[0]
    assert lane.lane_id == "TP-ADOPS-ELITELUXE24-MODE-V1"
    assert lane.candidate_sha == PINNED_HEAD
    assert lane.gate_status == "FAIL"
    assert lane.audit_status == "UNKNOWN"
    assert lane.lifecycle_state == "IMPLEMENTED_NOT_ACCEPTED"

    claims = {claim.field: claim for claim in snapshot.claims}
    assert {field: claim.value for field, claim in claims.items()} == {
        "active_packet": "TP-ADOPS-ELITELUXE24-MODE-V1",
        "proof_freshness": "STALE",
        "audit_status": "UNKNOWN",
        "acceptance_status": "UNKNOWN",
        "remote_candidate": "REMOTE_COMMIT_PRESENT",
        "legacy_candidate": "REMOTE_COMMIT_ABSENT",
        "governance_pr_277": "DESIGN_EVIDENCE_ONLY",
    }
    assert claims["governance_pr_277"].materiality == "NON_BLOCKING"
    assert all(claim.freshness == "STALE" for claim in snapshot.claims)


def test_non_adops_export_remains_byte_equivalent_after_adapter_discovery() -> None:
    fixture = (
        ROOT
        / "reports/project-control-plane/fixtures/minimal_fixture/evidence_export.json"
    )
    generic_export = _load(fixture)
    before = json.dumps(
        generic_export, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")

    adapter = load_extension_adapters(
        [SCHEMA_ROOT / "extension_manifest.adops.json"]
    )[0]

    assert adapter.matches(generic_export) is False
    after = json.dumps(
        generic_export, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    assert after == before


def test_adapter_rejects_head_drift_dirty_state_and_mutated_input() -> None:
    adapter = _adapter()
    original = _load(FIXTURE_ROOT / "evidence_export.json")

    head_drift = json.loads(json.dumps(original))
    head_drift["repo_state"]["head_sha"] = "0" * 40
    try:
        adapter.enrich(head_drift, ROOT)
    except ValueError as exc:
        assert "pinned head" in str(exc)
    else:
        raise AssertionError("head drift must fail closed")

    dirty = json.loads(json.dumps(original))
    dirty["repo_state"]["worktree_state"] = "DIRTY"
    dirty["dirty_state"] = {"state": "DIRTY", "paths": ["src/adops/runtime.py"]}
    try:
        adapter.enrich(dirty, ROOT)
    except ValueError as exc:
        assert "clean source state" in str(exc)
    else:
        raise AssertionError("dirty source must fail closed")

    assert original == _load(FIXTURE_ROOT / "evidence_export.json")


def test_adapter_rejects_conflicting_caller_active_packet_or_proof_manifest() -> None:
    adapter = _adapter()
    original = _load(FIXTURE_ROOT / "evidence_export.json")

    bad_packet = json.loads(json.dumps(original))
    bad_packet["active_packet"] = {
        "state": "PRESENT",
        "packet_id": "TP-OTHER-PACKET-V1",
        "path": "task-packets/TP-OTHER-PACKET-V1.md",
    }
    try:
        adapter.enrich(bad_packet, ROOT)
    except ValueError as exc:
        assert "active packet conflicts" in str(exc)
    else:
        raise AssertionError("conflicting active packet in generic export must fail closed")

    bad_proof = json.loads(json.dumps(original))
    bad_proof["proof_manifest"] = {
        "state": "PRESENT",
        "path": "proof/TP-OTHER-PACKET-V1/IMPLEMENTER_REPORT.md",
        "freshness": "CURRENT",
    }
    try:
        adapter.enrich(bad_proof, ROOT)
    except ValueError as exc:
        assert "proof manifest conflicts" in str(exc)
    else:
        raise AssertionError("conflicting proof manifest in generic export must fail closed")


def test_missing_or_conflicting_inventory_fails_closed(tmp_path: Path) -> None:
    source_root = tmp_path / "repo"
    copied_fixture = (
        source_root / "reports/project-control-plane/fixtures/adops_fixture"
    )
    copied_fixture.parent.mkdir(parents=True)
    shutil.copytree(FIXTURE_ROOT, copied_fixture)
    copied_schemas = source_root / "schemas/project_control_plane"
    copied_schemas.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "schemas/project_control_plane", copied_schemas)
    generic_export = _load(FIXTURE_ROOT / "evidence_export.json")
    adapter = _adapter()

    (copied_fixture / "SOURCES.json").unlink()
    try:
        adapter.enrich(generic_export, source_root)
    except ValueError as exc:
        assert "SOURCES.json" in str(exc)
    else:
        raise AssertionError("missing inventory must fail closed")

    shutil.copy2(FIXTURE_ROOT / "SOURCES.json", copied_fixture / "SOURCES.json")
    inventory = _load(copied_fixture / "SOURCES.json")
    inventory["legacy_candidate"]["status"] = "REMOTE_COMMIT_PRESENT"
    (copied_fixture / "SOURCES.json").write_text(
        json.dumps(inventory), encoding="utf-8"
    )
    try:
        adapter.enrich(generic_export, source_root)
    except ValueError as exc:
        assert "legacy candidate" in str(exc)
    else:
        raise AssertionError("conflicting candidate evidence must fail closed")


def test_conflicting_blob_or_pr_identity_fails_closed(tmp_path: Path) -> None:
    source_root = tmp_path / "repo"
    copied_fixture = (
        source_root / "reports/project-control-plane/fixtures/adops_fixture"
    )
    copied_fixture.parent.mkdir(parents=True)
    shutil.copytree(FIXTURE_ROOT, copied_fixture)
    copied_schemas = source_root / "schemas/project_control_plane"
    copied_schemas.parent.mkdir(parents=True)
    shutil.copytree(ROOT / "schemas/project_control_plane", copied_schemas)
    generic_export = _load(FIXTURE_ROOT / "evidence_export.json")
    adapter = _adapter()

    inventory = _load(copied_fixture / "SOURCES.json")
    inventory["sources"][0]["blob_sha"] = "0" * 40
    (copied_fixture / "SOURCES.json").write_text(
        json.dumps(inventory), encoding="utf-8"
    )
    try:
        adapter.enrich(generic_export, source_root)
    except ValueError as exc:
        assert "blob SHA" in str(exc)
    else:
        raise AssertionError("conflicting blob identity must fail closed")

    inventory = _load(FIXTURE_ROOT / "SOURCES.json")
    inventory["github_observations"][0]["head_sha"] = "0" * 40
    (copied_fixture / "SOURCES.json").write_text(
        json.dumps(inventory), encoding="utf-8"
    )
    try:
        adapter.enrich(generic_export, source_root)
    except ValueError as exc:
        assert "PR #277" in str(exc)
    else:
        raise AssertionError("conflicting PR identity must fail closed")
