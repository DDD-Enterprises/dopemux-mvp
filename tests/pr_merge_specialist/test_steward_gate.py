from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from dopemux_pr_merge_specialist.steward_gate import steward_gate


HEAD_SHA = "abc123def456"
NOW = datetime(2026, 5, 31, 12, 0, tzinfo=timezone.utc)
FRESH = "2026-05-31T11:45:00Z"


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


def _merge_readiness(
    *,
    head_sha: str = HEAD_SHA,
    proof_head_sha: str = HEAD_SHA,
    readiness: str = "NEEDS_IMPLEMENTER",
    audit_status: str = "PASS",
    generated_at: str = FRESH,
) -> dict:
    return {
        "schema_version": "1.1.0",
        "generated_at": generated_at,
        "pr": {
            "number": 123,
            "url": "https://github.example/pr/123",
            "base_ref": "main",
            "head_ref": "feature",
            "head_sha": head_sha,
        },
        "readiness": readiness,
        "risk_tier": "MEDIUM",
        "embedded_audit": {
            "status": audit_status,
            "report_path": "proof/TP/AUDITOR_REPORT.md",
        },
        "proof": {
            "proof_path": "proof/TP/PROOF.json",
            "proof_head_sha": proof_head_sha,
            "matches_pr_head": proof_head_sha == head_sha,
            "proof_freshness": "FRESH",
        },
        "blockers": ["FAILED_CHECK"],
        "unknowns": [],
        "mutation_performed": False,
    }


def _audit_proof(
    *,
    head_sha: str = HEAD_SHA,
    embedded_status: str = "PASS",
    generated_at: str = FRESH,
) -> dict:
    return {
        "packet_id": "TP-DMX-AUDIT-CI-PROVENANCE-104",
        "head_sha": head_sha,
        "generated_at": generated_at,
        "embedded_audit": {
            "required": True,
            "status": embedded_status,
            "auditor_tool": "pal-mcp-clink",
            "auditor_model": "opus",
            "invocation": "pal clink audit",
            "exit_code": 0,
            "report_path": "proof/TP-DMX-AUDIT-CI-PROVENANCE-104/AUDITOR_REPORT.md",
            "findings": [],
            "fixes_applied": [],
            "remaining_risks": [],
            "skip_reason": None,
        },
    }


def test_remediation_gate_allows_fresh_matching_needs_implementer_artifacts(tmp_path: Path):
    readiness_path = _write_json(tmp_path / "MERGE_READINESS.json", _merge_readiness())
    proof_path = _write_json(tmp_path / "PROOF.json", _audit_proof())

    result = steward_gate(
        head_sha=HEAD_SHA,
        required_class="REMEDIATION",
        merge_readiness_path=readiness_path,
        audit_proof_path=proof_path,
        now=NOW,
        ttl_seconds=3600,
    )

    assert result.allowed is True
    assert result.reason_code == "ALLOW_REMEDIATION"
    assert result.required_class == "REMEDIATION"
    assert result.evidence["merge_readiness"] == "NEEDS_IMPLEMENTER"


def test_remediation_gate_denies_sha_mismatch(tmp_path: Path):
    readiness_path = _write_json(
        tmp_path / "MERGE_READINESS.json",
        _merge_readiness(proof_head_sha="different"),
    )
    proof_path = _write_json(tmp_path / "PROOF.json", _audit_proof())

    result = steward_gate(
        head_sha=HEAD_SHA,
        required_class="REMEDIATION",
        merge_readiness_path=readiness_path,
        audit_proof_path=proof_path,
        now=NOW,
        ttl_seconds=3600,
    )

    assert result.allowed is False
    assert result.reason_code == "DENY_SHA_MISMATCH"


def test_remediation_gate_denies_skipped_independent_audit(tmp_path: Path):
    readiness_path = _write_json(tmp_path / "MERGE_READINESS.json", _merge_readiness())
    proof_path = _write_json(
        tmp_path / "PROOF.json",
        _audit_proof(embedded_status="SKIPPED"),
    )

    result = steward_gate(
        head_sha=HEAD_SHA,
        required_class="REMEDIATION",
        merge_readiness_path=readiness_path,
        audit_proof_path=proof_path,
        now=NOW,
        ttl_seconds=3600,
    )

    assert result.allowed is False
    assert result.reason_code == "DENY_AUDIT_NOT_PASSING"


def test_remediation_gate_denies_stale_artifact(tmp_path: Path):
    readiness_path = _write_json(
        tmp_path / "MERGE_READINESS.json",
        _merge_readiness(generated_at="2026-05-30T11:00:00Z"),
    )
    proof_path = _write_json(tmp_path / "PROOF.json", _audit_proof())

    result = steward_gate(
        head_sha=HEAD_SHA,
        required_class="REMEDIATION",
        merge_readiness_path=readiness_path,
        audit_proof_path=proof_path,
        now=NOW,
        ttl_seconds=3600,
    )

    assert result.allowed is False
    assert result.reason_code == "DENY_STALE_ARTIFACT"


def test_finalization_gate_requires_ready_readiness(tmp_path: Path):
    readiness_path = _write_json(tmp_path / "MERGE_READINESS.json", _merge_readiness())
    proof_path = _write_json(tmp_path / "PROOF.json", _audit_proof())

    result = steward_gate(
        head_sha=HEAD_SHA,
        required_class="FINALIZATION",
        merge_readiness_path=readiness_path,
        audit_proof_path=proof_path,
        now=NOW,
        ttl_seconds=3600,
    )

    assert result.allowed is False
    assert result.reason_code == "DENY_READINESS_CLASS_MISMATCH"
