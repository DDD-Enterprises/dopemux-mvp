"""Artifact tests for TP-DMX-COCKPIT-INVENTORY-REGEN-001."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
PACKET_ID = "TP-DMX-COCKPIT-INVENTORY-REGEN-001"
ARTIFACT_DIR = REPO_ROOT / "out" / "cockpit-inventory-regen" / PACKET_ID
PROOF_DIR = REPO_ROOT / "proof" / "cockpit-inventory-regen" / PACKET_ID


def _load_json(name: str) -> dict[str, object]:
    path = ARTIFACT_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def _joined(*parts: str) -> str:
    return "".join(parts)


def test_inventory_json_artifacts_parse_and_match_packet_id():
    for name in (
        "COMMAND_SURFACE_INVENTORY.json",
        "INVENTORY_DRIFT_REPORT.json",
        "CURRENT_HEAD_COCKPIT_STATUS.json",
        "PROOF.json",
    ):
        payload = _load_json(name)
        assert payload["packet_id"] == PACKET_ID


def test_inventory_preserves_five_modes_and_four_global_surfaces():
    inventory = _load_json("COMMAND_SURFACE_INVENTORY.json")
    status = _load_json("CURRENT_HEAD_COCKPIT_STATUS.json")

    runtime = inventory["runtime_model_status"]
    assert runtime["top_level_modes"] == [
        "PM",
        "Implementer",
        "Overview",
        "Services",
        "Events",
    ]
    assert runtime["top_level_mode_count"] == 5
    assert runtime["global_surfaces"] == [
        "Command Palette",
        "Settings/Admin/Runtime",
        "Safe Actions / Proof Gate",
        "Unknown / Drift Queue",
    ]
    assert runtime["global_surface_count"] == 4
    assert status["runtime_model_status"]["five_top_level_modes"] == runtime["top_level_modes"]
    assert status["runtime_model_status"]["four_global_surfaces"] == runtime["global_surfaces"]


def test_settings_admin_and_unknown_drift_summaries_are_included():
    inventory = _load_json("COMMAND_SURFACE_INVENTORY.json")
    regenerated = inventory["regenerated_counts"]
    assert regenerated["settings_admin_row_count"] == 62
    assert regenerated["settings_admin_unknown_tier_count"] == 62
    assert regenerated["unknown_drift_total_queue_items_lower_bound"] == 487
    assert regenerated["unknown_drift_aggregated_item_count"] == 45


def test_t4_tx_tu_boundaries_remain_blocked_or_non_executable():
    inventory = _load_json("COMMAND_SURFACE_INVENTORY.json")
    status = _load_json("CURRENT_HEAD_COCKPIT_STATUS.json")
    runtime = inventory["runtime_model_status"]
    governance = status["governance"]
    assert runtime["t4_blocked"] is True
    assert runtime["tx_tu_never_executable"] is True
    assert governance["no_t4_remote_mutation"] is True
    assert governance["no_runtime_action_execution"] is True
    assert governance["no_runtime_reclassification"] is True


def test_unknown_and_drift_rows_are_not_silently_resolved():
    inventory = _load_json("COMMAND_SURFACE_INVENTORY.json")
    proof = _load_json("PROOF.json")
    records = inventory["records"]
    assert any(record["safety_class"] == "UNKNOWN" for record in records)
    assert any(record["gate_tier"] == "TU" for record in records)
    assert proof["boundary_preservation"]["unknown_drift_does_not_execute"] is True
    assert proof["boundary_preservation"]["runtime_reclassification_disabled"] is True
    assert "Complete per-row command inventory source" in proof["unknowns"]


def test_aggregate_records_are_used_when_per_row_evidence_is_unavailable():
    inventory = _load_json("COMMAND_SURFACE_INVENTORY.json")
    assert inventory["per_row_data_status"] == "UNAVAILABLE_IN_ACCEPTED_ARTIFACTS"
    assert inventory["regenerated_counts"]["per_row_record_count"] == 0
    assert inventory["regenerated_counts"]["aggregate_record_count"] == len(inventory["records"])
    assert {record["record_kind"] for record in inventory["records"]} >= {
        "aggregate_count",
        "aggregate_lower_bound",
        "aggregate_policy_block",
    }


def test_drift_report_classifies_stale_and_uncomparable_inputs():
    report = _load_json("INVENTORY_DRIFT_REPORT.json")
    classifications = {
        item["metric"]: item["classification"] for item in report["comparisons"]
    }
    assert classifications["tx_exact_row_count"] == "UNCOMPARABLE"
    assert classifications["tu_exact_row_count"] == "UNCOMPARABLE"
    assert classifications["accepted_unknown_drift_index_drift_count"] == "STALE_INPUT"
    assert classifications["settings_admin_per_row_tier_mapping"] == "NEEDS_PACKET_DECISION"


def test_next_packet_matrix_does_not_recommend_final_screen_unlock():
    matrix = (ARTIFACT_DIR / "NEXT_PACKET_DECISION_MATRIX.md").read_text(encoding="utf-8")
    assert "Claude Design primitive/final-screen unlock packet | Not recommended" in matrix
    assert _joined("final screens ", "approved") not in matrix
    assert _joined("Claude Design upload ", "allowed") not in matrix


def test_forbidden_positive_governance_claims_absent_from_generated_artifacts():
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for root in (ARTIFACT_DIR, PROOF_DIR)
        for path in sorted(root.glob("**/*"))
        if path.is_file()
    )
    forbidden = (
        _joined("READY_FOR_CLAUDE_DESIGN: ", "approved"),
        _joined("safe_for_claude_design: ", "YES"),
        _joined("Claude Design upload ", "allowed"),
        _joined("T4 ", "authorized"),
        _joined("runtime execution ", "implemented"),
        _joined("Unknown / Drift ", "execution"),
        _joined("runtime reclassification ", "allowed"),
        _joined("execute ", "anyway"),
        _joined("approve ", "anyway"),
        _joined("resolve ", "now"),
        _joined("final screens ", "approved"),
    )
    for phrase in forbidden:
        assert phrase not in text


def test_forbidden_runtime_call_tokens_absent_from_cockpit_sources_and_tests():
    roots = [
        REPO_ROOT / "src" / "dopemux" / "ui" / "cockpit",
        REPO_ROOT / "src" / "dopemux" / "commands" / "cockpit_commands.py",
        REPO_ROOT / "tests" / "unit" / "dopemux" / "ui" / "cockpit",
        REPO_ROOT / "tests" / "unit" / "test_cockpit_cli.py",
    ]
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for root in roots
        for path in ([root] if root.is_file() else sorted(root.glob("*.py")))
    )
    forbidden = (
        _joined("sub", "process"),
        _joined("shell", "=True"),
        _joined("os.", "system"),
        _joined("req", "uests"),
        _joined("ht", "tpx"),
        _joined("url", "lib"),
        _joined("soc", "ket"),
        _joined("doc", "ker"),
        _joined("kub", "ectl"),
        _joined("gh pr ", "create"),
        _joined("git ", "push"),
    )
    for token in forbidden:
        assert token not in text
