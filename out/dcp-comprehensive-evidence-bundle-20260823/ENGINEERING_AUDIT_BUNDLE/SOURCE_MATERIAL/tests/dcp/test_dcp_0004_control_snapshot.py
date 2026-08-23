"""TP-DCP-0004 local control snapshot tests."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft7Validator
import pytest

from dopemux.dcp.control_snapshot import (
    SnapshotBlocked,
    generate_control_snapshot,
    write_control_snapshot,
)


_THIS_DIR = Path(__file__).resolve().parent
_FIXTURES_DIR = _THIS_DIR / "fixtures"
_REPO_ROOT = _THIS_DIR.parents[1]
_EXPECTED_HEAD_SHA = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
_GENERATED_AT = "2026-06-04T12:00:00Z"


def _fixture(name: str) -> Path:
    return _FIXTURES_DIR / name


def _snapshot(root: Path) -> dict:
    return generate_control_snapshot(
        root,
        generated_at=_GENERATED_AT,
        expected_head_sha=_EXPECTED_HEAD_SHA,
    )


def _packet_state(snapshot: dict, packet_id: str) -> dict:
    return next(
        state for state in snapshot["packet_states"] if state["packet_id"] == packet_id
    )


def test_1_valid_local_snapshot_generation_preserves_core_contract():
    snapshot = _snapshot(_fixture("tp_dcp_0004_valid_snapshot_inputs"))

    assert snapshot["snapshot_family"] == "DCP_CONTROL_SNAPSHOT"
    assert snapshot["schema_version"] == "dcp-control-snapshot.v0"
    assert snapshot["snapshot_contract_version"] == "0.1.0"
    assert snapshot["generated_at"] == _GENERATED_AT
    assert snapshot["created_at_utc"] == _GENERATED_AT
    assert snapshot["generator"] == {
        "packet_id": "TP-DCP-0004",
        "implementation": "local",
        "live_adapters_used": False,
        "external_writes_used": False,
    }
    assert snapshot["derived"] is True
    assert snapshot["authoritative"] is False
    assert snapshot["readiness"]["snapshot_status"] == "READY"


def test_2_missing_tp_dcp_0003_dependency_blocks_snapshot():
    with pytest.raises(SnapshotBlocked) as exc:
        _snapshot(_fixture("tp_dcp_0004_missing_tp0003"))

    assert "TP-DCP-0003" in str(exc.value)


def test_3_missing_optional_artifact_becomes_unknown():
    snapshot = _snapshot(_fixture("tp_dcp_0004_valid_snapshot_inputs"))

    state = _packet_state(snapshot, "TP-DCP-0004")
    assert state["state"] == "UNKNOWN"
    assert state["proof_path"] is None
    assert state["freshness"] == "UNKNOWN"


def test_4_malformed_proof_becomes_conflicting(tmp_path):
    root = tmp_path / "malformed"
    proof_dir = root / "proof" / "TP-DCP-0003"
    packet_dir = root / "task-packets"
    proof_dir.mkdir(parents=True)
    packet_dir.mkdir(parents=True)
    (packet_dir / "TP-DCP-0003.md").write_text("# TP-DCP-0003", encoding="utf-8")
    (proof_dir / "PROOF.json").write_text('{"packet_id": "TP-DCP-0003",', encoding="utf-8")

    snapshot = _snapshot(root)

    assert _packet_state(snapshot, "TP-DCP-0003")["state"] == "CONFLICTING"
    assert snapshot["readiness"]["snapshot_status"] == "CONFLICTING"


def test_5_stale_proof_remains_stale_and_blocks_readiness():
    snapshot = _snapshot(_fixture("tp_dcp_0004_stale_proof"))

    assert _packet_state(snapshot, "TP-DCP-0003")["freshness"] == "STALE"
    assert snapshot["readiness"]["snapshot_status"] == "BLOCKED"
    assert "stale proof artifact detected" in snapshot["readiness"]["blocking_reasons"]


def test_6_conflicting_packet_proof_ids_become_conflicting():
    snapshot = _snapshot(_fixture("tp_dcp_0004_conflicting_proof"))

    assert _packet_state(snapshot, "TP-DCP-0003")["state"] == "CONFLICTING"
    assert snapshot["readiness"]["snapshot_status"] == "CONFLICTING"


def test_7_snapshot_includes_source_artifact_inventory():
    snapshot = _snapshot(_fixture("tp_dcp_0004_valid_snapshot_inputs"))
    paths = {item["path"] for item in snapshot["source_artifacts"]}

    assert "task-packets/TP-DCP-0001.json" in paths
    assert "proof/TP-DCP-0003/PROOF.json" in paths
    assert "schemas/dcp/dcp_control_snapshot.schema.json" in paths
    assert "tests/dcp/test_placeholder.py" in paths
    assert "schemas/dcp/dcp_control_snapshot.v0.schema.json" not in paths


def test_8_snapshot_includes_packet_states_for_dcp_0001_through_0004():
    snapshot = _snapshot(_fixture("tp_dcp_0004_valid_snapshot_inputs"))

    assert [state["packet_id"] for state in snapshot["packet_states"]] == [
        "TP-DCP-0001",
        "TP-DCP-0002",
        "TP-DCP-0003",
        "TP-DCP-0004",
    ]
    assert _packet_state(snapshot, "TP-DCP-0001")["state"] == "OBSERVED"
    assert _packet_state(snapshot, "TP-DCP-0003")["state"] == "OBSERVED"


def test_9_snapshot_preserves_residual_risks_from_local_proof():
    snapshot = _snapshot(_fixture("tp_dcp_0004_valid_snapshot_inputs"))

    assert "tp1 risk" in snapshot["packet_states"][0]["residual_risks"]
    assert "tp3 risk" in snapshot["residual_risks"]


def test_10_snapshot_preserves_stop_conditions_from_local_proof():
    snapshot = _snapshot(_fixture("tp_dcp_0004_valid_snapshot_inputs"))

    assert "tp1 stop" in snapshot["stop_conditions"]
    assert "tp3 stop" in snapshot["stop_condition_summary"]


def test_11_snapshot_is_derived_and_non_authoritative():
    snapshot = _snapshot(_fixture("tp_dcp_0004_valid_snapshot_inputs"))

    assert snapshot["derived"] is True
    assert snapshot["authoritative"] is False
    assert snapshot["authority_label_summary"]["snapshot"] == "INFERRED"
    assert "Source artifacts remain authoritative" in snapshot["surfaces"]["note"]


def test_12_live_write_ready_absent_returns_undefined_and_blocking():
    snapshot = _snapshot(_fixture("tp_dcp_0004_valid_snapshot_inputs"))

    assert snapshot["guards"]["live_write_ready_status"] == "UNDEFINED_AND_BLOCKING"
    assert snapshot["guards"]["live_write_status"] == "NONE"


def test_13_operational_live_write_ready_is_detected_and_blocks_readiness():
    snapshot = _snapshot(_fixture("tp_dcp_0004_live_write_detected"))

    assert snapshot["guards"]["live_write_ready_status"] == "OPERATIONAL"
    assert snapshot["guards"]["live_write_status"] == "DETECTED"
    assert snapshot["readiness"]["snapshot_status"] == "BLOCKED"
    assert "live write readiness detected" in snapshot["readiness"]["blocking_reasons"]


def test_14_merge_seam_status_is_preserved():
    snapshot = _snapshot(_fixture("tp_dcp_0004_valid_snapshot_inputs"))

    assert snapshot["guards"]["merge_seam_status"] == "PRESERVED"


def test_15_forbidden_merge_paths_are_not_imported_called_or_wrapped():
    dcp_root = _REPO_ROOT / "src" / "dopemux" / "dcp"
    text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(dcp_root.glob("*.py")))

    forbidden_fragments = [
        "queue" + "_drain",
        "batch" + "_resolve" + "_and" + "_merge",
        "dopemux" + "_pr" + "_merge" + "_specialist",
        "gh pr merge",
    ]
    assert all(fragment not in text for fragment in forbidden_fragments)


def test_16_no_url_following():
    snapshot = _snapshot(_fixture("tp_dcp_0004_valid_snapshot_inputs"))
    serialized = json.dumps(snapshot, sort_keys=True)

    assert "https://" not in serialized
    assert "http://" not in serialized


def test_17_no_dopetask_execution_path():
    dcp_root = _REPO_ROOT / "src" / "dopemux" / "dcp"
    text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(dcp_root.glob("*.py")))

    assert "scripts/" + "dopetask" not in text
    assert "scripts/" + "taskx" not in text
    assert "dopetask tp" not in text


def test_18_no_bridge_memory_context_or_task_orchestrator_call_path():
    dcp_root = _REPO_ROOT / "src" / "dopemux" / "dcp"
    text = "\n".join(path.read_text(encoding="utf-8") for path in sorted(dcp_root.glob("*.py")))

    forbidden_fragments = [
        "mem." + "upsert",
        "memory" + "_store",
        "/tools/" + "memory" + "_store",
        "/api/" + "decisions",
        "/api/" + "progress",
        "/api/" + "custom_data",
        "/api/" + "workflow",
        "/api/" + "pm",
        "requests.",
        "httpx.",
        "urllib.request",
        "subprocess",
    ]
    assert all(fragment not in text for fragment in forbidden_fragments)


def test_19_deterministic_output_for_stable_input_except_timestamp():
    root = _fixture("tp_dcp_0004_valid_snapshot_inputs")
    first = generate_control_snapshot(root, generated_at="2026-06-04T12:00:00Z", expected_head_sha=_EXPECTED_HEAD_SHA)
    second = generate_control_snapshot(root, generated_at="2026-06-04T13:00:00Z", expected_head_sha=_EXPECTED_HEAD_SHA)

    first_without_time = copy.deepcopy(first)
    second_without_time = copy.deepcopy(second)
    for snapshot in (first_without_time, second_without_time):
        snapshot.pop("generated_at")
        snapshot.pop("created_at_utc")

    assert first_without_time == second_without_time


def test_20_json_schema_validates_generated_snapshot():
    snapshot = _snapshot(_fixture("tp_dcp_0004_valid_snapshot_inputs"))
    schema = json.loads((_REPO_ROOT / "schemas" / "dcp" / "dcp_control_snapshot.schema.json").read_text(encoding="utf-8"))

    errors = list(Draft7Validator(schema).iter_errors(snapshot))
    assert not errors, [error.message for error in errors]


def test_22_missing_prerequisite_packet_evidence_blocks_readiness():
    """DMX-W1-04-F002: TP-DCP-0002 entirely absent must not be silently READY."""
    snapshot = _snapshot(_fixture("tp_dcp_0004_missing_tp0002_evidence"))

    state = _packet_state(snapshot, "TP-DCP-0002")
    assert state["state"] == "UNKNOWN"
    assert snapshot["readiness"]["snapshot_status"] != "READY"
    assert any(
        "TP-DCP-0002" in reason
        for reason in snapshot["readiness"]["blocking_reasons"]
    )


def test_21_write_snapshot_is_explicit_and_local(tmp_path):
    output = tmp_path / "DCP_CONTROL_SNAPSHOT.json"
    snapshot = write_control_snapshot(
        _fixture("tp_dcp_0004_valid_snapshot_inputs"),
        output,
        generated_at=_GENERATED_AT,
        expected_head_sha=_EXPECTED_HEAD_SHA,
    )

    written = json.loads(output.read_text(encoding="utf-8"))
    assert written == snapshot
    assert written["snapshot_family"] == "DCP_CONTROL_SNAPSHOT"
