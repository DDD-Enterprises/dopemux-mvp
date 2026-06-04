"""
DCP proof-family dispatch tests - TP-DCP-0003.

These tests are local-only. They do not call GitHub, Dopetask,
Task-Orchestrator, ConPort, dope-memory, dope-context, or dopecon-bridge.
"""
import json
from pathlib import Path

from dopemux.dcp.proof_family import (
    AuthorityLabel,
    FreshnessStatus,
    LiveWriteReadyStatus,
    LiveWriteStatus,
    MergeSeamStatus,
    ProofFamily,
    classify_artifact,
)
from dopemux.dcp.proof_pointer_reader import read_proof_pointer


_THIS_DIR = Path(__file__).resolve().parent
_FIXTURES_DIR = _THIS_DIR / "fixtures"
_EXPECTED_HEAD_SHA = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


def _fixture(name: str) -> Path:
    return _FIXTURES_DIR / name


def test_1_valid_proof_pointer_classifies_and_preserves_local_reference():
    result = classify_artifact(
        _fixture("tp_dcp_0003_valid_proof_pointer.json"),
        expected_head_sha=_EXPECTED_HEAD_SHA,
    )

    assert result.family is ProofFamily.DCP_PROOF_POINTER
    assert result.authority_label is AuthorityLabel.OBSERVED
    assert result.freshness is FreshnessStatus.FRESH
    assert result.referenced_paths == ["proof/TP-DCP-0002/PROOF.json"]
    assert result.fields["validation_state"].value == "REPO_CROSS_CHECKED"
    assert result.fields["auditor_verdict"].value == "PASS_WITH_RISKS"


def test_2_valid_proof_bundle_classifies_and_extracts_minimum_fields():
    result = classify_artifact(
        _fixture("tp_dcp_0003_valid_proof_bundle.json"),
        expected_head_sha=_EXPECTED_HEAD_SHA,
    )

    assert result.family is ProofFamily.DCP_PROOF_BUNDLE
    assert result.freshness is FreshnessStatus.FRESH
    assert result.fields["packet_id"].value == "TP-DCP-0003"
    assert result.fields["pr_url"].value is None
    assert result.fields["live_write_ready_status"].value == "UNDEFINED_AND_BLOCKING"
    assert result.fields["merge_seam_status"].value == "PRESERVED"
    assert result.fields["live_write_status"].value == "NONE"


def test_3_audit_report_markdown_is_detected_without_json_requirements(tmp_path):
    audit_path = tmp_path / "AUDIT.md"
    audit_path.write_text(
        "# Audit\n\nAudit Verdict: PASS_WITH_RISKS\nAuditor: independent-reviewer\n",
        encoding="utf-8",
    )

    result = classify_artifact(audit_path, expected_head_sha=_EXPECTED_HEAD_SHA)

    assert result.family is ProofFamily.DCP_AUDIT_REPORT
    assert result.authority_label is AuthorityLabel.OBSERVED
    assert result.freshness is FreshnessStatus.UNKNOWN
    assert result.fields["audit_verdict"].value == "PASS_WITH_RISKS"
    assert result.fields["head_sha"].value == "UNKNOWN"


def test_4_valid_merge_readiness_classifies_as_local_readiness_artifact():
    result = classify_artifact(
        _fixture("tp_dcp_0003_valid_merge_readiness.json"),
        expected_head_sha=_EXPECTED_HEAD_SHA,
    )

    assert result.family is ProofFamily.DCP_MERGE_READINESS
    assert result.freshness is FreshnessStatus.FRESH
    assert result.fields["pr_steward_readiness_result"].value == "READY"
    assert result.live_write_status is LiveWriteStatus.NONE
    assert result.live_write_ready_status is LiveWriteReadyStatus.UNDEFINED_AND_BLOCKING


def test_5_unknown_proof_family_fails_closed():
    result = classify_artifact(
        _fixture("tp_dcp_0003_unknown_family.json"),
        expected_head_sha=_EXPECTED_HEAD_SHA,
    )

    assert result.family is ProofFamily.UNKNOWN
    assert result.authority_label is AuthorityLabel.UNKNOWN
    assert result.freshness is FreshnessStatus.UNKNOWN
    assert result.errors


def test_6_malformed_json_fails_closed_as_conflicting(tmp_path):
    malformed = tmp_path / "PROOF.json"
    malformed.write_text('{"packet_id": "TP-DCP-0003",', encoding="utf-8")

    result = classify_artifact(malformed, expected_head_sha=_EXPECTED_HEAD_SHA)

    assert result.family is ProofFamily.CONFLICTING
    assert result.authority_label is AuthorityLabel.CONFLICTING
    assert result.freshness is FreshnessStatus.CONFLICTING
    assert any("malformed JSON" in error for error in result.errors)


def test_7_missing_artifact_returns_unknown():
    result = classify_artifact(_FIXTURES_DIR / "does-not-exist.json")

    assert result.family is ProofFamily.UNKNOWN
    assert result.authority_label is AuthorityLabel.UNKNOWN
    assert result.freshness is FreshnessStatus.UNKNOWN
    assert result.fields["packet_id"].value == "UNKNOWN"


def test_8_stale_sha_returns_stale_without_external_lookup():
    result = classify_artifact(
        _fixture("tp_dcp_0003_stale_sha.json"),
        expected_head_sha=_EXPECTED_HEAD_SHA,
    )

    assert result.family is ProofFamily.DCP_PROOF_BUNDLE
    assert result.freshness is FreshnessStatus.STALE
    assert result.fields["head_sha"].value == "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"


def test_9_conflicting_sha_and_audit_fields_return_conflicting():
    result = classify_artifact(
        _fixture("tp_dcp_0003_conflicting_artifacts.json"),
        expected_head_sha=_EXPECTED_HEAD_SHA,
    )

    assert result.family is ProofFamily.CONFLICTING
    assert result.authority_label is AuthorityLabel.CONFLICTING
    assert result.freshness is FreshnessStatus.CONFLICTING
    assert any("head_sha" in error for error in result.errors)
    assert any("audit_verdict" in error for error in result.errors)


def test_10_absent_live_write_ready_is_undefined_and_blocking():
    result = classify_artifact(
        _fixture("tp_dcp_0003_valid_proof_pointer.json"),
        expected_head_sha=_EXPECTED_HEAD_SHA,
    )

    assert result.live_write_ready_status is LiveWriteReadyStatus.UNDEFINED_AND_BLOCKING
    assert result.live_write_status is LiveWriteStatus.NONE


def test_11_operational_live_write_ready_is_flagged(tmp_path):
    live_ready = tmp_path / "PROOF.json"
    live_ready.write_text(
        json.dumps(
            {
                "packet_id": "TP-DCP-0003",
                "head_sha": _EXPECTED_HEAD_SHA,
                "LIVE_WRITE_READY": "OPERATIONAL",
            }
        ),
        encoding="utf-8",
    )

    result = classify_artifact(live_ready, expected_head_sha=_EXPECTED_HEAD_SHA)

    assert result.live_write_ready_status is LiveWriteReadyStatus.OPERATIONAL
    assert result.live_write_status is LiveWriteStatus.DETECTED
    assert result.family is ProofFamily.CONFLICTING


def test_12_merge_seam_red_line_status_is_preserved_for_known_safe_artifact():
    result = classify_artifact(
        _fixture("tp_dcp_0003_valid_proof_bundle.json"),
        expected_head_sha=_EXPECTED_HEAD_SHA,
    )

    assert result.merge_seam_status is MergeSeamStatus.PRESERVED


def test_13_remote_urls_are_preserved_but_not_followed(tmp_path):
    pointer = tmp_path / "pointer.json"
    pointer.write_text(
        json.dumps(
            {
                "schema_version": "dcp-proof-pointer.v0",
                "pointer_id": "ptr-remote",
                "source_artifact_ref": "https://example.invalid/proof/PROOF.json",
                "source_head_sha": {"value": _EXPECTED_HEAD_SHA},
                "validation_state": "REPO_CROSS_CHECKED",
                "auditor_verdict": "PASS",
            }
        ),
        encoding="utf-8",
    )

    result = read_proof_pointer(pointer, expected_head_sha=_EXPECTED_HEAD_SHA)

    assert result.family is ProofFamily.DCP_PROOF_POINTER
    assert result.referenced_paths == []
    assert result.raw_references == ["https://example.invalid/proof/PROOF.json"]
    assert any("remote reference not followed" in error for error in result.errors)


def test_14_unsupported_uri_schemes_are_rejected_not_referenced(tmp_path):
    pointer = tmp_path / "pointer.json"
    pointer.write_text(
        json.dumps(
            {
                "schema_version": "dcp-proof-pointer.v0",
                "pointer_id": "ptr-unsafe-scheme",
                "source_artifact_ref": "ssh://host/repo/proof/PROOF.json",
                "source_head_sha": {"value": _EXPECTED_HEAD_SHA},
                "validation_state": "REPO_CROSS_CHECKED",
                "auditor_verdict": "PASS",
            }
        ),
        encoding="utf-8",
    )

    result = read_proof_pointer(pointer, expected_head_sha=_EXPECTED_HEAD_SHA)

    assert result.family is ProofFamily.DCP_PROOF_POINTER
    assert result.raw_references == ["ssh://host/repo/proof/PROOF.json"]
    assert result.referenced_paths == []
    assert any("unsupported reference scheme not followed" in error for error in result.errors)


def test_15_dcp_modules_do_not_contain_forbidden_execution_paths():
    dcp_root = Path(__file__).resolve().parents[2] / "src" / "dopemux" / "dcp"
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(dcp_root.glob("*.py"))
    )
    forbidden_fragments = [
        "queue" + "_drain",
        "batch" + "_resolve" + "_and" + "_merge",
        "dopemux" + "_pr" + "_merge" + "_specialist",
        "scripts/" + "dopetask",
        "scripts/" + "taskx",
    ]

    assert all(fragment not in text for fragment in forbidden_fragments)


def test_16_dcp_modules_do_not_contain_external_endpoint_call_paths():
    dcp_root = Path(__file__).resolve().parents[2] / "src" / "dopemux" / "dcp"
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(dcp_root.glob("*.py"))
    )
    forbidden_fragments = [
        "mem." + "upsert",
        "memory" + "_store",
        "/tools/" + "memory" + "_store",
        "/api/" + "decisions",
        "/api/" + "progress",
        "/api/" + "custom_data",
        "/api/" + "workflow",
        "/api/" + "pm",
        "requests.",
        "urllib.request",
    ]

    assert all(fragment not in text for fragment in forbidden_fragments)
