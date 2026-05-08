"""Artifact tests for TP-DMX-COCKPIT-MERGE-STACK-CONSOLIDATE-001."""

from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[5]
PACKET_ID = "TP-DMX-COCKPIT-MERGE-STACK-CONSOLIDATE-001"
ARTIFACT_DIR = REPO_ROOT / "out" / "cockpit-merge-stack" / PACKET_ID
PROOF_DIR = REPO_ROOT / "proof" / "cockpit-merge-stack" / PACKET_ID


def _load_json(name: str) -> dict[str, object]:
    return json.loads((ARTIFACT_DIR / name).read_text(encoding="utf-8"))


def _joined(*parts: str) -> str:
    return "".join(parts)


def _artifact_text() -> str:
    return "\n".join(
        path.read_text(encoding="utf-8")
        for root in (ARTIFACT_DIR, PROOF_DIR)
        for path in sorted(root.glob("**/*"))
        if path.is_file()
    )


def test_merge_stack_json_artifacts_parse_and_match_packet_id():
    for name in (
        "STACK_STATE_REPORT.json",
        "STACK_ANCESTRY_REPORT.json",
        "CONSOLIDATION_READINESS_MATRIX.json",
        "STACK_VALIDATION_REPORT.json",
        "PROOF.json",
    ):
        payload = _load_json(name)
        assert payload["packet_id"] == PACKET_ID


def test_stack_pr_order_is_preserved():
    state = _load_json("STACK_STATE_REPORT.json")
    ancestry = _load_json("STACK_ANCESTRY_REPORT.json")
    readiness = _load_json("CONSOLIDATION_READINESS_MATRIX.json")

    covered = [568, 569, 570, 571, 573]
    assert state["covered_pr_set"] == covered
    assert ancestry["covered_pr_set"] == covered
    assert readiness["covered_pr_set"] == covered
    assert [item["pr_number"] for item in state["stack_prs"]] == covered
    assert ancestry["declared_order"] == [568, 569, 570, 571]
    assert readiness["merge_order_recommendation"] == [568, 569, 570, 571]
    assert readiness["merge_candidate_prs"] == [568, 569, 570, 571]
    assert readiness["reviewed_merged_evidence_prs"] == [573]
    assert readiness["sequential_merge_required"] is True


def test_merge_execution_handoff_is_not_authorization():
    handoff = (ARTIFACT_DIR / "MERGE_EXECUTION_HANDOFF.md").read_text(encoding="utf-8")
    assert "This handoff is not authorization." in handoff
    assert "Ledger decision" in handoff
    assert "This packet does not authorize it." in handoff


def test_readiness_matrix_does_not_claim_remote_mutation_happened():
    readiness_text = (ARTIFACT_DIR / "CONSOLIDATION_READINESS_MATRIX.md").read_text(
        encoding="utf-8"
    )
    readiness = _load_json("CONSOLIDATION_READINESS_MATRIX.json")

    assert _joined("PRs ", "merged") not in readiness_text
    assert _joined("merged ", "successfully") not in readiness_text
    assert readiness["mutation_statement"].startswith("No pull request")
    assert readiness["operator_command_candidates_are_handoff_only"] is True


def test_proof_records_no_remote_stack_mutation_and_preserves_governance():
    proof = _load_json("PROOF.json")
    boundary = proof["boundary_preservation"]
    statement = proof["mutation_statement"]

    assert proof["covered_pr_set"] == [568, 569, 570, 571, 573]
    assert proof["merge_candidate_prs"] == [568, 569, 570, 571]
    assert proof["reviewed_merged_evidence_prs"] == [573]
    assert "No pull request" in statement
    assert "base retarget" in statement
    assert "force-push" in statement
    assert boundary["safe_for_claude_design"] == "NO"
    assert boundary["READY_FOR_CLAUDE_DESIGN"] == "not approved"
    assert boundary["claude_design_upload"] == "not_authorized"
    assert boundary["final_screen_generation"] == "not_authorized"
    assert boundary["runtime_action_execution"] == "not_authorized"
    assert boundary["t4_remote_mutation"] == "not_authorized"
    assert boundary["canonical_writes"] == "not_authorized"
    assert boundary["unknown_drift_runtime_reclassification"] == "disabled"
    assert boundary["tx_tu_execution"] == "disabled"
    assert boundary["no_final_screens"] is True
    assert boundary["no_claude_design_upload"] is True
    assert boundary["no_runtime_action_execution"] is True
    assert boundary["no_t4_remote_mutation"] is True
    assert boundary["no_canonical_writes"] is True
    assert boundary["no_runtime_reclassification"] is True


def test_next_step_does_not_unlock_final_screens_or_remote_policy_first():
    next_step = (ARTIFACT_DIR / "POST_CONSOLIDATION_NEXT_STEP.md").read_text(
        encoding="utf-8"
    )
    assert "Ledger-authorized merge execution or blocker-cleanup packet" in next_step
    assert "PR 572's current GitHub conflict state" in next_step
    assert "Remote-mutation policy packet should not start" in next_step
    assert "Claude Design primitive/final-screen unlock packet is not recommended" in next_step
    assert _joined("final screens ", "approved") not in next_step


def test_expected_stack_heads_and_ancestry_are_verified():
    state = _load_json("STACK_STATE_REPORT.json")
    ancestry = _load_json("STACK_ANCESTRY_REPORT.json")

    expected_heads = {
        568: "9ad522df341375b7fede75eaa8e43e1f44097b41",
        569: "d27c4995f22ceba646763759fa4a8f53d547ac67",
        570: "b6b89fae076a669952ef1178d7d7d17a3e01eb7b",
        571: "93702834fbb05963685ed4919c6d099040399426",
        573: "1236757c15b1bfdf0926ee476908d56ed71b0dc6",
    }
    for item in state["stack_prs"]:
        assert item["expected_audited_head"] == expected_heads[item["pr_number"]]
        assert item["expected_head_matches_current_remote"] is True
        assert item["is_draft"] is False
        if item["pr_number"] == 573:
            assert item["pr_state"] == "MERGED"
            assert item["merge_commit"] == "c0c32c1639e675d3415257f2444437ae1fa2ea3c"
            assert item["coverage_role"] == "reviewed_merged_evidence_not_merge_candidate"
        else:
            assert item["pr_state"] == "OPEN"
    assert ancestry["all_declared_ancestry_checks_passed"] is True
    assert ancestry["unexpected_divergence_detected"] is False
    assert ancestry["required_packet_skip_detected"] is False


def test_pr573_audit_evidence_is_recorded_without_unlocking_runtime():
    proof = _load_json("PROOF.json")
    state = _load_json("STACK_STATE_REPORT.json")
    readiness = _load_json("CONSOLIDATION_READINESS_MATRIX.json")

    evidence = proof["pr_573_audit_evidence"]
    pr573_state = next(item for item in state["stack_prs"] if item["pr_number"] == 573)
    pr573_readiness = next(
        item for item in readiness["entries"] if item["pr_number"] == 573
    )

    assert evidence["audit_verdict"] == "PASS_WITH_RISKS"
    assert evidence["audit_qualifier"] == (
        "auditor-side/process risks only; no PR-side runtime-contract defect"
    )
    assert evidence["merge_commit"] == "c0c32c1639e675d3415257f2444437ae1fa2ea3c"
    assert evidence["proof_bundle_path"] == (
        "out/cockpit-runtime-contract-fidelity/"
        "TP-DMX-COCKPIT-RUNTIME-CONTRACT-FIDELITY-001/PROOF.json"
    )
    assert evidence["validation_summary"] == "58 cockpit tests passed"
    assert pr573_state["boundary_preservation_status"]["palette_broker_only"] is True
    assert pr573_state["boundary_preservation_status"]["t4_blocked"] is True
    assert pr573_state["boundary_preservation_status"]["tx_tu_non_executable"] is True
    assert (
        pr573_state["boundary_preservation_status"][
            "unknown_drift_runtime_reclassification_disabled"
        ]
        is True
    )
    assert pr573_readiness["classification"] == "REVIEWED_MERGED_EVIDENCE"
    assert pr573_readiness["coverage_role"] == "covered evidence; not a merge candidate"


def test_forbidden_positive_governance_claims_absent_from_generated_artifacts():
    text = _artifact_text()
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
        _joined("PRs ", "merged"),
        _joined("merged ", "successfully"),
    )
    for phrase in forbidden:
        assert phrase not in text


def test_forbidden_mutation_command_tokens_absent_from_generated_artifacts():
    text = _artifact_text()
    forbidden = (
        _joined("gh pr ", "merge"),
        _joined("git ", "merge"),
        _joined("git ", "rebase"),
        _joined("git ", "push ", "--force"),
        _joined("git branch ", "-d"),
        _joined("git branch ", "-D"),
        _joined("gh pr ", "edit"),
        _joined("gh pr ", "close"),
    )
    for phrase in forbidden:
        assert phrase not in text
