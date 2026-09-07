from __future__ import annotations

import json
from pathlib import Path

from scripts.audit.run_embedded_audit import build_evidence_gate_proof
from tools.pr_steward import collector


_REPO = "DDD-Enterprises/dopemux-mvp"
_PR = 704
_HEAD = "a" * 40
_BASE = "b" * 40
_NOT_REQUIRED_REASON = "AUDIT_NOT_REQUIRED_BY_TRUSTED_CHANGE_CONTRACT"


def _not_required_proof() -> dict:
    return build_evidence_gate_proof(
        packet_id="TP-DMX-PR-STEWARD-001",
        repo=_REPO,
        pr_number=_PR,
        head_sha=_HEAD,
        base_sha=_BASE,
        change_contract={
            "status": "PASS",
            "max_lane": "L1",
            "model_audit_required": False,
        },
        local_attestation=None,
    )


def _write_proof(tmp_path: Path, proof: dict) -> Path:
    path = tmp_path / "PROOF.json"
    path.write_text(json.dumps(proof), encoding="utf-8")
    return path


def test_proof_state_preserves_validated_not_required_metadata(tmp_path: Path) -> None:
    state, errors = collector._proof_state(
        proof_path=_write_proof(tmp_path, _not_required_proof()),
        pr_head_sha=_HEAD,
        expected_pr=_PR,
        expected_repo=_REPO,
    )

    assert errors == []
    assert state["embedded_audit"]["status"] == "SKIPPED"
    assert state["embedded_audit"]["required"] is False
    assert state["embedded_audit"]["skip_reason"] == _NOT_REQUIRED_REASON
    assert state["proof"]["matches_pr_head"] is True


def test_proof_state_invalid_proof_forces_needs_supervisor(tmp_path: Path) -> None:
    proof = _not_required_proof()
    proof["provenance"]["proof_author"] = "self-attested"

    state, errors = collector._proof_state(
        proof_path=_write_proof(tmp_path, proof),
        pr_head_sha=_HEAD,
        expected_pr=_PR,
        expected_repo=_REPO,
    )

    assert errors
    assert state["embedded_audit"]["status"] == "NEEDS_SUPERVISOR"
    assert state["embedded_audit"]["required"] is False
    assert state["embedded_audit"]["skip_reason"] == _NOT_REQUIRED_REASON


def test_proof_state_preserves_malformed_required_without_coercion(
    tmp_path: Path,
) -> None:
    proof = _not_required_proof()
    proof["embedded_audit"]["required"] = "false"

    state, errors = collector._proof_state(
        proof_path=_write_proof(tmp_path, proof),
        pr_head_sha=_HEAD,
        expected_pr=_PR,
        expected_repo=_REPO,
    )

    assert errors
    assert state["embedded_audit"]["status"] == "NEEDS_SUPERVISOR"
    assert state["embedded_audit"]["required"] == "false"
    assert state["embedded_audit"]["skip_reason"] == _NOT_REQUIRED_REASON
