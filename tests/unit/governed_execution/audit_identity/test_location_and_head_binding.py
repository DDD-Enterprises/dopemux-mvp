"""Tests for EvidenceLocation classification and exact_head_binding()."""
from __future__ import annotations

import pytest

from dopemux.governed_execution.audit_identity.location import (
    EvidenceKind,
    classify_location,
    exact_head_binding,
    split,
)

_OID_A = "a" * 40
_OID_B = "b" * 40


@pytest.mark.parametrize(
    "path",
    [
        "proof/W07/AUDITOR_REPORT.md",
        "proofs/summary.json",
        "out/build/artifact.txt",
        "reports/coverage.html",
        "some/module.proof.json",
        "docs/section/PROOF.json",
        "some/dir/AUDITOR_REPORT.md",
    ],
)
def test_classify_location_evidence_store(path: str) -> None:
    assert classify_location(path) is EvidenceKind.EVIDENCE_STORE


@pytest.mark.parametrize(
    "path",
    [
        "src/dopemux/governed_execution/audit_identity/identity.py",
        "tests/unit/governed_execution/audit_identity/test_identity_layers.py",
        "docs/03-reference/governance/governed-execution-contract-v2.md",
        "task-packets/TP-DMX-GEC-V2-W07-AUDIT-IDENTITY-001.json",
        "not-proof/x.json",
        "docs/reports-on-things/x.md",
    ],
)
def test_classify_location_candidate_branch(path: str) -> None:
    assert classify_location(path) is EvidenceKind.CANDIDATE_BRANCH


def test_classify_location_is_top_level_prefix_only() -> None:
    """`not-proof/x.json` does not start with `proof/`, so it is a candidate
    path -- the classifier must not match a mid-path segment.
    """
    assert classify_location("services/proof/x.json") is EvidenceKind.CANDIDATE_BRANCH


def test_split_partitions_changed_paths() -> None:
    paths = [
        "src/dopemux/governed_execution/audit_identity/identity.py",
        "proof/W07/AUDITOR_REPORT.md",
        "docs/03-reference/governance/governed-execution-contract-v2.md",
        "out/logs/run.txt",
    ]
    candidate, evidence = split(paths)
    assert candidate == (
        "src/dopemux/governed_execution/audit_identity/identity.py",
        "docs/03-reference/governance/governed-execution-contract-v2.md",
    )
    assert evidence == (
        "proof/W07/AUDITOR_REPORT.md",
        "out/logs/run.txt",
    )


def test_split_empty_input() -> None:
    assert split([]) == ((), ())


def test_exact_head_binding_bound_true_on_triple_equality() -> None:
    result = exact_head_binding(_OID_A, _OID_A, _OID_A)
    assert result.bound is True
    assert result.reasons == ()
    assert result.authority == "NONE"


def test_exact_head_binding_false_on_audited_mismatch() -> None:
    result = exact_head_binding(_OID_B, _OID_A, _OID_A)
    assert result.bound is False
    assert any("audited_head" in reason for reason in result.reasons)


def test_exact_head_binding_false_on_finality_mismatch() -> None:
    result = exact_head_binding(_OID_A, _OID_B, _OID_A)
    assert result.bound is False
    assert any("finality_head" in reason for reason in result.reasons)


def test_exact_head_binding_false_on_freeze_mismatch() -> None:
    result = exact_head_binding(_OID_A, _OID_A, _OID_B)
    assert result.bound is False
    assert any("freeze_head" in reason for reason in result.reasons)


@pytest.mark.parametrize(
    "malformed",
    [
        "A" * 40,  # uppercase hex not legal per git_oid pattern
        "a" * 39,  # too short
        "a" * 41,  # too long
        "g" * 40,  # non-hex character
        "",
        "not-a-sha",
    ],
)
def test_exact_head_binding_malformed_oid_yields_false(malformed: str) -> None:
    result = exact_head_binding(malformed, _OID_A, _OID_A)
    assert result.bound is False
    assert any("malformed oid" in reason for reason in result.reasons)


def test_exact_head_binding_all_three_malformed() -> None:
    result = exact_head_binding("bad1", "bad2", "bad3")
    assert result.bound is False
    reason_text = " ".join(result.reasons)
    assert "audited_head" in reason_text
    assert "finality_head" in reason_text
    assert "freeze_head" in reason_text


def test_no_other_path_produces_bound_true() -> None:
    """Fuzz a handful of near-miss cases to confirm bound is False whenever
    the triple is not exactly equal.
    """
    cases = [
        (_OID_A, _OID_A, _OID_B),
        (_OID_A, _OID_B, _OID_B),
        (_OID_B, _OID_A, _OID_B),
        (_OID_A[:-1] + "c", _OID_A, _OID_A),
    ]
    for audited, finality, freeze in cases:
        assert exact_head_binding(audited, finality, freeze).bound is False
