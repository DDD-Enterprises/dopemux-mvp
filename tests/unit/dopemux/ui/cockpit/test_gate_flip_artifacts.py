"""Artifact tests for TP-DMX-COCKPIT-GATE-FLIP-001."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
PACKET_ID = "TP-DMX-COCKPIT-GATE-FLIP-001"
ARTIFACT_DIR = REPO_ROOT / "out" / "cockpit-gate-flip" / PACKET_ID
PROOF_DIR = REPO_ROOT / "proof" / "cockpit-gate-flip" / PACKET_ID
EXPECTED_CONDITIONS = {
    "COMMAND_PALETTE",
    "SAFE_ACTIONS",
    "SETTINGS_RUNTIME",
    "UNKNOWN_DRIFT",
    "PACK_REMEDIATE_IA",
    "RUNTIME_RENDER",
    "INVENTORY_REGEN",
    "EVIDENCE_LEDGER",
}


def _load_json(name: str) -> dict[str, object]:
    return json.loads((ARTIFACT_DIR / name).read_text(encoding="utf-8"))


def _joined(*parts: str) -> str:
    return "".join(parts)


def test_gate_flip_json_artifacts_parse_and_match_packet_id():
    for name in ("GATE_FLIP_STATUS.json", "PROOF.json"):
        payload = _load_json(name)
        assert payload["packet_id"] == PACKET_ID


def test_gate_flip_status_approves_only_after_all_eight_conditions_pass():
    status = _load_json("GATE_FLIP_STATUS.json")
    conditions = status["conditions"]

    assert status["safe_for_claude_design"] == "YES"
    assert status["READY_FOR_CLAUDE_DESIGN"] == "approved"
    assert status["claude_design_blocked"] is False
    assert {condition["id"] for condition in conditions} == EXPECTED_CONDITIONS
    assert all(condition["passed"] is True for condition in conditions)


def test_gate_flip_conditions_reference_required_proof_paths():
    status = _load_json("GATE_FLIP_STATUS.json")

    for condition in status["conditions"]:
        proof_path = condition["proof_path"]
        proof = json.loads((REPO_ROOT / proof_path).read_text(encoding="utf-8"))
        assert proof["packet_id"] == condition["packet_id"]


def test_gate_flip_preserves_non_execution_boundaries():
    status = _load_json("GATE_FLIP_STATUS.json")
    proof = _load_json("PROOF.json")

    assert status["upload_action_implemented"] is False
    assert status["runtime_action_execution_enabled"] is False
    assert status["runtime_reclassification_enabled"] is False
    assert status["t4_remote_mutation_authorized"] is False
    assert proof["boundary_preservation"]["no_runtime_action_execution"] is True
    assert proof["boundary_preservation"]["no_runtime_reclassification"] is True
    assert proof["boundary_preservation"]["no_claude_design_upload"] is True
    assert proof["boundary_preservation"]["no_t4_remote_mutation_authorization"] is True


def test_proof_records_gate_flip_pass_without_failed_conditions():
    proof = _load_json("PROOF.json")
    status = proof["gate_flip_status"]

    assert status["status"] == "PASS"
    assert status["condition_count"] == 8
    assert status["failed_conditions"] == []
    assert status["safe_for_claude_design"] == "YES"
    assert status["READY_FOR_CLAUDE_DESIGN"] == "approved"


def test_generated_artifacts_do_not_claim_execution_or_upload_authority():
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for root in (ARTIFACT_DIR, PROOF_DIR)
        for path in sorted(root.glob("**/*"))
        if path.is_file()
    )
    forbidden = (
        _joined("Claude Design upload ", "allowed"),
        _joined("T4 ", "authorized"),
        _joined("runtime execution ", "implemented"),
        _joined("Unknown / Drift ", "execution"),
        _joined("runtime reclassification ", "allowed"),
        _joined("execute ", "anyway"),
        _joined("approve ", "anyway"),
        _joined("final screens ", "approved"),
    )
    for phrase in forbidden:
        assert phrase not in text
