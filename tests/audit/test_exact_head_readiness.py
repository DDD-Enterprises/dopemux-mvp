"""Negative/positive fixtures for exact-head readiness (TP-0018)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dopemux.audit.exact_head_readiness import evaluate_exact_head_readiness


HEAD = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def _ok_proof(**over):
    base = {
        "implementation_commit": HEAD,
        "embedded_audit": {"status": "PASS", "report_path": "proof/x/AUDITOR_REPORT.md"},
        "pr": {"head_at_creation": HEAD},
    }
    base.update(over)
    return base


def _ok_checks():
    return [
        {
            "name": "Unit Tests",
            "status": "completed",
            "conclusion": "success",
            "head_sha": HEAD,
            "matches_head_sha": True,
        }
    ]


def test_ready_when_all_gates_green():
    result = evaluate_exact_head_readiness(
        head_sha=HEAD,
        proof=_ok_proof(),
        checks=_ok_checks(),
        review_threads=[{"isResolved": True}],
        reviewers=["hu3mann"],
        changed_files=["services/dcp-readonly-facade/src/dcp_facade/acceptance.py"],
        allowlist=["services/dcp-readonly-facade/src/dcp_facade/**"],
    )
    assert result["status"] == "READY"
    assert result["ready_for_merge"] is True
    assert result["unresolved_blockers"] == []


def test_stale_proof_blocks():
    result = evaluate_exact_head_readiness(
        head_sha=HEAD,
        proof=_ok_proof(implementation_commit="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
        checks=_ok_checks(),
    )
    assert result["status"] == "BLOCKED"
    assert "proof_stale_to_head" in result["unresolved_blockers"]


def test_skipped_audit_blocks():
    result = evaluate_exact_head_readiness(
        head_sha=HEAD,
        proof=_ok_proof(embedded_audit={"status": "SKIPPED"}),
        checks=_ok_checks(),
    )
    assert result["status"] == "BLOCKED"
    assert any("embedded_audit_skipped" == b for b in result["unresolved_blockers"])


def test_failed_and_pending_checks_block():
    checks = [
        {
            "name": "Unit Tests",
            "status": "completed",
            "conclusion": "failure",
            "head_sha": HEAD,
            "matches_head_sha": True,
        },
        {
            "name": "preflight",
            "status": "in_progress",
            "conclusion": "pending",
            "head_sha": HEAD,
            "matches_head_sha": True,
        },
    ]
    result = evaluate_exact_head_readiness(head_sha=HEAD, proof=_ok_proof(), checks=checks)
    assert result["status"] == "BLOCKED"
    assert "failed_checks" in result["unresolved_blockers"]
    assert "pending_checks" in result["unresolved_blockers"]


def test_stale_checks_block():
    checks = [
        {
            "name": "Unit Tests",
            "status": "completed",
            "conclusion": "success",
            "head_sha": "cccccccccccccccccccccccccccccccccccccccc",
            "matches_head_sha": False,
        }
    ]
    result = evaluate_exact_head_readiness(head_sha=HEAD, proof=_ok_proof(), checks=checks)
    assert result["status"] == "BLOCKED"
    assert "checks_stale_to_head" in result["unresolved_blockers"]


def test_unknown_reviewer_and_unresolved_thread_block():
    result = evaluate_exact_head_readiness(
        head_sha=HEAD,
        proof=_ok_proof(),
        checks=_ok_checks(),
        reviewers=["mystery-bot"],
        review_threads=[{"isResolved": False, "path": "x.py"}],
    )
    assert result["status"] == "BLOCKED"
    assert "unknown_reviewers_or_bots" in result["unresolved_blockers"]
    assert "blocking_thread_unresolved" in result["unresolved_blockers"]


def test_allowlist_escape_blocks():
    result = evaluate_exact_head_readiness(
        head_sha=HEAD,
        proof=_ok_proof(),
        checks=_ok_checks(),
        changed_files=["secrets/prod.env", "services/dcp-readonly-facade/src/dcp_facade/x.py"],
        allowlist=["services/dcp-readonly-facade/src/dcp_facade/**"],
    )
    assert result["status"] == "BLOCKED"
    assert "diff_escapes_packet_allowlist" in result["unresolved_blockers"]


def test_acceptance_not_ready_blocks_when_required():
    result = evaluate_exact_head_readiness(
        head_sha=HEAD,
        proof=_ok_proof(),
        checks=_ok_checks(),
        acceptance_report={"release_ready": False},
        require_acceptance_ready=True,
    )
    assert result["status"] == "BLOCKED"
    assert "acceptance_release_not_ready" in result["unresolved_blockers"]


def test_cli_writes_blocked_artifact(tmp_path: Path):
    from dopemux.audit.exact_head_readiness import main

    proof = tmp_path / "PROOF.json"
    proof.write_text(json.dumps(_ok_proof(embedded_audit={"status": "SKIPPED"})))
    checks = tmp_path / "checks.json"
    checks.write_text(json.dumps({"checks": _ok_checks()}))
    out = tmp_path / "MERGE_READINESS.json"
    code = main(
        [
            "--head-sha",
            HEAD,
            "--proof-json",
            str(proof),
            "--checks-json",
            str(checks),
            "--out",
            str(out),
        ]
    )
    assert code == 1
    payload = json.loads(out.read_text())
    assert payload["status"] == "BLOCKED"
