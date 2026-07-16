"""Ownership verification matrix (TP-DCP-MCP-RO-0015)."""

from __future__ import annotations

from dcp_facade.ownership import OwnershipEvidence, verify_ownership


def _base(**overrides) -> OwnershipEvidence:
    data = dict(
        family="conport",
        expected_project_id="proj-a",
        expected_project_root="/tmp/proj-a",
        expected_worktree_root="/tmp/proj-a/wt",
        runtime_project_id="proj-a",
        runtime_project_root="/tmp/proj-a",
        runtime_worktree_root="/tmp/proj-a/wt",
        labels={
            "dopemux.project_id": "proj-a",
            "dopemux.service": "conport",
            "dopemux.worktree_root": "/tmp/proj-a/wt",
        },
        mounts=("/tmp/proj-a/wt",),
        protocol_ok=True,
        protocol_name="mcp",
        has_listening_port=True,
        candidate_count=1,
        stale=False,
        unlabeled=False,
    )
    data.update(overrides)
    return OwnershipEvidence(**data)


def test_verified_happy_path():
    verdict = verify_ownership(_base())
    assert verdict.verified is True
    assert verdict.callable is False
    assert "identity" in verdict.evidence_codes


def test_port_only_is_blocked():
    verdict = verify_ownership(
        OwnershipEvidence(
            family="conport",
            expected_project_id="proj-a",
            expected_project_root="/tmp/proj-a",
            expected_worktree_root="/tmp/proj-a/wt",
            has_listening_port=True,
            candidate_count=1,
        )
    )
    assert verdict.verified is False
    assert "port_only" in verdict.evidence_codes or "unlabeled" in verdict.evidence_codes


def test_wrong_project_blocked():
    verdict = verify_ownership(_base(runtime_project_id="other"))
    assert verdict.verified is False
    assert "wrong_project" in verdict.evidence_codes


def test_ambiguous_candidates_blocked():
    verdict = verify_ownership(_base(candidate_count=2))
    assert verdict.verified is False
    assert "ambiguous" in verdict.evidence_codes


def test_stale_blocked():
    verdict = verify_ownership(_base(stale=True))
    assert verdict.verified is False
    assert "stale" in verdict.evidence_codes


def test_unlabeled_blocked():
    verdict = verify_ownership(_base(labels={}, unlabeled=True))
    assert verdict.verified is False
    assert "unlabeled" in verdict.evidence_codes


def test_protocol_required():
    verdict = verify_ownership(_base(protocol_ok=None))
    assert verdict.verified is False
    assert "protocol_required" in verdict.evidence_codes


def test_protocol_failed():
    verdict = verify_ownership(_base(protocol_ok=False))
    assert verdict.verified is False


def test_root_mismatch_blocked():
    verdict = verify_ownership(_base(runtime_worktree_root="/tmp/other"))
    assert verdict.verified is False
    assert "root_mismatch" in verdict.evidence_codes


def test_mount_missing_blocked():
    verdict = verify_ownership(_base(mounts=("/tmp/unrelated",)))
    assert verdict.verified is False
    assert "mount_missing" in verdict.evidence_codes


def test_family_not_release_one():
    verdict = verify_ownership(_base(family="dope_context"))
    assert verdict.verified is False
    assert "family_blocked" in verdict.evidence_codes


def test_dope_memory_family_label_alias():
    verdict = verify_ownership(
        _base(
            family="dope_memory",
            labels={
                "dopemux.project_id": "proj-a",
                "dopemux.service": "dope-memory",
                "dopemux.worktree_root": "/tmp/proj-a/wt",
            },
        )
    )
    assert verdict.verified is True
