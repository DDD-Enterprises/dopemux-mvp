from __future__ import annotations

import json
from pathlib import Path

from dopemux_pr_merge_specialist.schema import PullRequestState
from dopemux_pr_merge_specialist import queue_drain


def _write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _pr_state() -> PullRequestState:
    return PullRequestState(
        pr_id=765,
        title="needs implementation",
        author="dev",
        state="OPEN",
        base_ref="main",
        head_ref="feature/steward",
        ci_status="FAILURE",
        mergeable="MERGEABLE",
        merge_state_status="CLEAN",
        review_decision="",
        head_sha="abc123",
        base_sha="base123",
    )


def _merge_readiness(*, blockers: list[str] | None = None) -> dict:
    return {
        "generated_at": "2026-05-31T12:00:00Z",
        "readiness": "NEEDS_IMPLEMENTER",
        "blockers": blockers or ["FAILED_CHECK"],
        "pr": {
            "number": 765,
            "head_sha": "abc123",
            "head_ref": "feature/steward",
        },
        "proof": {
            "proof_head_sha": "abc123",
            "proof_path": "proof/TP/PROOF.json",
        },
        "embedded_audit": {
            "status": "PASS",
            "source": "independent",
        },
    }


def _audit_proof() -> dict:
    return {
        "generated_at": "2026-05-31T12:00:00Z",
        "head_sha": "abc123",
        "embedded_audit": {
            "status": "PASS",
            "source": "independent",
        },
    }


def test_remediation_gate_allows_needs_implementer_with_implementer_blocker(tmp_path: Path):
    pr_dir = tmp_path / "pr" / "765"
    _write_json(pr_dir / "MERGE_READINESS.json", _merge_readiness(blockers=["UNRESOLVED_REVIEW_THREAD"]))
    _write_json(pr_dir / "PROOF.json", _audit_proof())

    result = queue_drain.require_steward_remediation_gate(
        pr=_pr_state(),
        policy={"steward_gate": {"artifact_ttl_seconds": 3600}},
        pr_dir=pr_dir,
        now="2026-05-31T12:30:00Z",
    )

    assert result.allowed is True
    assert result.reason_code == "ALLOW_REMEDIATION"
    assert result.evidence["implementer_blockers"] == ["UNRESOLVED_REVIEW_THREAD"]


def test_remediation_gate_denies_missing_implementer_blocker(tmp_path: Path):
    pr_dir = tmp_path / "pr" / "765"
    _write_json(pr_dir / "MERGE_READINESS.json", _merge_readiness(blockers=["PROOF_STALE"]))
    _write_json(pr_dir / "PROOF.json", _audit_proof())

    result = queue_drain.require_steward_remediation_gate(
        pr=_pr_state(),
        policy={"steward_gate": {"artifact_ttl_seconds": 3600}},
        pr_dir=pr_dir,
        now="2026-05-31T12:30:00Z",
    )

    assert result.allowed is False
    assert result.reason_code == "DENY_NO_IMPLEMENTER_BLOCKER"
    assert result.evidence["blockers"] == ["PROOF_STALE"]


def test_remediation_gate_denies_missing_artifacts(tmp_path: Path):
    result = queue_drain.require_steward_remediation_gate(
        pr=_pr_state(),
        policy={"steward_gate": {"artifact_ttl_seconds": 3600}},
        pr_dir=tmp_path / "missing",
        now="2026-05-31T12:30:00Z",
    )

    assert result.allowed is False
    assert result.reason_code == "DENY_ARTIFACT_UNREADABLE"


def test_global_fix_pr_creation_requires_explicit_policy_opt_in():
    assert queue_drain.global_fix_prs_allowed({}) is False
    assert queue_drain.global_fix_prs_allowed({"steward_gate": {}}) is False
    assert (
        queue_drain.global_fix_prs_allowed(
            {"steward_gate": {"allow_global_fix_prs": True}}
        )
        is True
    )
