"""Tests for schema enforcement on embedded_audit in validate_change_contract.py.

Verifies:
- Canonical report_path patterns pass validation.
- Non-matching report_path patterns fail with proof_schema_fail.
- Canonical schema is strictly enforced without popping or weakening report_path.pattern.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.governance.validate_change_contract import evaluate

ROOT = Path(__file__).resolve().parents[2]


def _build_proof(report_path: str, *, status: str = "PASS") -> dict:
    return {
        "packet_id": "TP-DMX-TEST-001",
        "head_sha": "0123456789abcdef0123456789abcdef01234567",
        "embedded_audit": {
            "required": True,
            "status": status,
            "auditor_tool": "claude-code-cli",
            "auditor_model": "sonnet",
            "invocation": "claude-code",
            "exit_code": 0,
            "report_path": report_path,
            "findings": [],
            "fixes_applied": [],
            "remaining_risks": [],
            "skip_reason": None,
        },
    }


def test_canonical_report_path_passes_validation() -> None:
    proof_path = "proof/TP-DMX-TEST-001/PROOF.json"
    valid_paths = [
        "proof/TP-DMX-TEST-001/AUDITOR_REPORT.md",
        "proof/TP-DMX-TEST-001/AUDITOR_REPAIR_REPORT.md",
        "proof/TP-DMX-TEST-001/AUDITOR_REPAIR_1_REPORT.md",
    ]
    for rep in valid_paths:
        payload = _build_proof(rep)
        result = evaluate(
            paths=[proof_path],
            cwd=ROOT,
            file_text={proof_path: json.dumps(payload)},
        )
        failures = [f for f in result.findings if f.code == "proof_schema_fail"]
        assert not failures, f"Expected {rep} to pass schema validation, but got: {failures}"


def test_non_canonical_report_path_fails_validation() -> None:
    invalid_paths = [
        "proof/pr_merge/embedded-audit/pr-1181/AUDITOR_REPORT.md",
        "proof/TP-DMX-TEST-001/extra/AUDITOR_REPORT.md",
        "other/AUDITOR_REPORT.md",
        "proof/TP-DMX-TEST-001/report.md",
    ]
    for rep in invalid_paths:
        proof_path = "proof/TP-DMX-TEST-001/PROOF.json"
        payload = _build_proof(rep)
        result = evaluate(
            paths=[proof_path],
            cwd=ROOT,
            file_text={proof_path: json.dumps(payload)},
        )
        failures = [f for f in result.findings if f.code == "proof_schema_fail"]
        assert len(failures) == 1, f"Expected {rep} to fail schema validation, but got: {failures}"
        assert "report_path" in failures[0].message


def test_report_path_pattern_not_softened_for_pr_merge_path() -> None:
    """Verifies defect VSH-002: proof paths containing 'proof/pr_merge/' must not bypass pattern check."""
    pr_merge_proof = "proof/pr_merge/embedded-audit/pr-9999/PROOF.json"
    payload = _build_proof("proof/pr_merge/embedded-audit/pr-9999/AUDITOR_REPORT.md")
    result = evaluate(
        paths=[pr_merge_proof],
        cwd=ROOT,
        file_text={pr_merge_proof: json.dumps(payload)},
    )
    failures = [f for f in result.findings if f.code == "proof_schema_fail"]
    assert len(failures) == 1, "Must fail schema validation for non-canonical report_path in pr_merge proof"
    assert "report_path" in failures[0].message
