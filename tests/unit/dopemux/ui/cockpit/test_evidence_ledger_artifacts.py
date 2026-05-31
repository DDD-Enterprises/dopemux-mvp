"""Artifact tests for TP-DMX-COCKPIT-EVIDENCE-LEDGER-001."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
PACKET_ID = "TP-DMX-COCKPIT-EVIDENCE-LEDGER-001"
ARTIFACT_DIR = REPO_ROOT / "out" / "cockpit-evidence-ledger" / PACKET_ID
PROOF_DIR = REPO_ROOT / "proof" / "cockpit-evidence-ledger" / PACKET_ID


def _load_json(name: str) -> dict[str, object]:
    return json.loads((ARTIFACT_DIR / name).read_text(encoding="utf-8"))


def _joined(*parts: str) -> str:
    return "".join(parts)


def test_evidence_ledger_json_artifacts_parse_and_match_packet_id():
    for name in ("EVIDENCE_LEDGER_REDUCTION.json", "PROOF.json"):
        payload = _load_json(name)
        assert payload["packet_id"] == PACKET_ID


def test_condition_8_has_no_unresolved_items():
    reduction = _load_json("EVIDENCE_LEDGER_REDUCTION.json")
    proof = _load_json("PROOF.json")

    assert reduction["condition"]["status"] == "SATISFIED_FOR_CONDITION_8"
    assert reduction["condition_8_unresolved_items"] == []
    assert proof["condition_8_status"]["status"] == "PASS"
    assert proof["condition_8_status"]["condition_8_unresolved_items"] == 0


def test_every_condition_8_reduction_is_resolved_or_explicitly_rejected():
    reduction = _load_json("EVIDENCE_LEDGER_REDUCTION.json")
    statuses = {item["current_status"] for item in reduction["reductions"]}
    assert statuses <= {"RESOLVED", "EXPLICITLY_REJECTED"}
    assert statuses == {"RESOLVED", "EXPLICITLY_REJECTED"}
    assert len(reduction["reductions"]) == 7


def test_root_authority_absences_are_resolved_by_repo_authority_fallbacks():
    reduction = _load_json("EVIDENCE_LEDGER_REDUCTION.json")
    authority = reduction["authority_evidence"]

    assert authority["root_rules_md_present"] is False
    assert authority["root_truth_md_count"] == 0
    assert "docs/03-reference/governance/rules.md" in authority["docs_reference_rules"]
    assert len(authority["docs_reference_truth_files"]) == 7


def test_runtime_registration_rejects_genetic_worktree_and_vault_surfaces():
    reduction = _load_json("EVIDENCE_LEDGER_REDUCTION.json")
    registered = reduction["runtime_cli_evidence"]["registered_top_level"]

    assert registered["decisions"] is True
    assert registered["genetic"] is False
    assert registered["worktree"] is False
    assert registered["worktrees"] is False
    assert registered["vault"] is False
    assert registered["env"] is True
    assert registered["session"] is True
    assert registered["safe"] is True


def test_decisions_surface_has_no_claimed_hidden_leaf_callbacks():
    reduction = _load_json("EVIDENCE_LEDGER_REDUCTION.json")
    subcommands = reduction["runtime_cli_evidence"]["registered_subcommands"]
    source = reduction["source_evidence"]

    assert subcommands["decisions"] == ["energy", "patterns"]
    assert source["decisions_leaf_callback_status"] == "NO_CONCRETE_LEAF_CALLBACKS"


def test_boundary_preserves_design_gate_and_non_execution():
    reduction = _load_json("EVIDENCE_LEDGER_REDUCTION.json")
    proof = _load_json("PROOF.json")

    assert reduction["boundary_preservation"]["safe_for_claude_design"] == "NO"
    assert reduction["boundary_preservation"]["does_not_modify_runtime"] is True
    assert reduction["boundary_preservation"]["does_not_register_commands"] is True
    assert reduction["boundary_preservation"]["does_not_execute_actions"] is True
    assert proof["boundary_preservation"]["no_runtime_change"] is True
    assert proof["boundary_preservation"]["no_command_registration_change"] is True


def test_generated_artifacts_do_not_claim_positive_governance_state():
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
