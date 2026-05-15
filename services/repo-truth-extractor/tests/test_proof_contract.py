from __future__ import annotations

from lib import proof_contract
from lib.proof_contract import (
    build_conformance_report,
    classify_artifact,
    classify_artifact_authority_order,
)


def _partial_proof_pack() -> dict:
    return {
        "run_id": "run-static-001",
        "git_sha": "abc123",
        "runner_sha256": "runner-digest",
        "argv": ["run_extraction_v5.py", "--phase", "D", "--dry-run"],
        "cwd": "/repo",
        "updated_at": "2026-05-15T00:00:00Z",
        "phases": {"D": {"counts": {"raw": 1}}},
        "linked_artifacts": {"coverage_rollup": "/repo/COVERAGE_ROLLUP.json"},
    }


def _full_bundle() -> dict:
    return {
        "bundle_id": "RTE-PKT-10-BUNDLE",
        "run_id": "rte-pkt-10-local",
        "source_version": "proof-contract-helper-v1",
        "repo_root": "/repo",
        "git_sha": "abc123",
        "runner_sha": "runner-digest",
        "command_argv": ["pytest", "test_proof_contract.py"],
        "cwd": "/repo",
        "status": "READY_FOR_REVIEW",
        "validation_state": "PASSED",
        "run_posture": "STATIC_ONLY",
        "generated_at": "2026-05-15T00:00:00Z",
        "phase_list": ["proof-contract"],
        "generated_artifact_list": ["RTE-PKT-10_MANIFEST.json"],
        "authoritative_artifacts": ["RTE-PKT-10_MANIFEST.json"],
        "supporting_artifacts": ["RTE-PKT-10_TEST_REPORT.md"],
        "runtime_authority_artifacts": [
            "services/repo-truth-extractor/run_extraction_v5.py"
        ],
        "generated_evidence_artifacts": ["PROOF_PACK.json"],
        "proof_governance_artifacts": [
            "out/rte-pkt-10-proof-contract/RTE-PKT-10_MANIFEST.json"
        ],
        "external_advisory_artifacts": ["external-report-redacted"],
        "sample_or_uncertain_lineage_artifacts": ["sample-proof-pack"],
        "chain_of_custody": {
            "documented": True,
            "source_version": "proof-contract-helper-v1",
        },
        "warnings": [],
        "blockers": [],
        "handoff_refs": [],
        "parent_bundle_refs": [],
        "review_order_hint": 10,
        "live_validation_status": "NOT_RUN",
        "provider_call_status": "NOT_RUN",
        "batch_operation_status": "NOT_RUN",
        "redaction_status": "REDACTED",
        "artifact_hashes": {"RTE-PKT-10_MANIFEST.json": "sha256:abc"},
    }


def test_partial_proof_pack_is_run_proof_not_full_contract_bundle() -> None:
    report = build_conformance_report(
        _partial_proof_pack(),
        artifact_path=(
            "services/repo-truth-extractor/extraction/repo-truth-extractor/"
            "v5/runs/run/PROOF_PACK.json"
        ),
    )

    assert report["overall_status"] == "PARTIAL"
    assert report["is_full_proof_contract_bundle"] is False
    assert report["proof_posture"] == "run_proof_or_packet_evidence_not_full_bundle"
    assert report["artifact"]["classification"] == "runtime_generated_evidence"
    assert report["fields"]["authoritative_artifacts"]["status"] == "MISSING"
    assert report["fields"]["supporting_artifacts"]["status"] == "MISSING"


def test_missing_authoritative_and_supporting_declarations_do_not_pass() -> None:
    payload = _full_bundle()
    payload.pop("authoritative_artifacts")
    payload.pop("supporting_artifacts")

    report = build_conformance_report(
        payload,
        artifact_path="out/rte-pkt-10-proof-contract/RTE-PKT-10_MANIFEST.json",
    )

    assert report["overall_status"] == "PARTIAL"
    assert report["fields"]["authoritative_artifacts"]["status"] == "MISSING"
    assert report["fields"]["supporting_artifacts"]["status"] == "MISSING"
    assert report["is_full_proof_contract_bundle"] is False


def test_static_batch_proof_remains_live_unvalidated() -> None:
    payload = {
        "packet_id": "RTE-PKT-08-XAI-BATCH-STATIC",
        "status": "READY_FOR_REVIEW",
        "live_validation_status": "NOT_LIVE_VALIDATED",
        "provider_call_status": "NOT_RUN",
        "batch_operation_status": "NOT_RUN",
        "warnings": ["LIVE_VALIDATION_REQUIRED"],
    }

    report = build_conformance_report(
        payload,
        artifact_path="proof/TP-RTE-BATCH-E2E-006/PROOF.json",
    )

    assert report["artifact"]["classification"] == "proof_governance_artifact"
    assert report["artifact"]["static_only"] is True
    assert (
        report["fields"]["live_validation_status"]["observed_value"]
        == "NOT_LIVE_VALIDATED"
    )
    assert report["fields"]["provider_call_status"]["observed_value"] == "NOT_RUN"


def test_generated_artifacts_do_not_outrank_runtime_source_authority() -> None:
    ordered = classify_artifact_authority_order(
        [
            "out/rte-pkt-10-proof-contract/RTE-PKT-10_MANIFEST.json",
            "services/repo-truth-extractor/run_extraction_v5.py",
        ]
    )

    assert ordered[0]["classification"] == "runtime_authority"
    assert ordered[1]["classification"] == "proof_governance_artifact"
    assert ordered[1]["authority_rank"] < ordered[0]["authority_rank"]


def test_exact_pass1_identity_stays_unknown_without_run_id_and_hashes() -> None:
    report = build_conformance_report(
        {"status": "READY_FOR_REVIEW"},
        artifact_path=(
            "services/repo-truth-extractor/tests/fixtures/proof_pack_sample.json"
        ),
    )

    assert report["artifact"]["classification"] == "sample_artifact_uncertain_lineage"
    assert report["exact_pass1_identity"]["status"] == "UNKNOWN"
    assert "run_id" in report["missing_fields"]
    assert "artifact_hashes" in report["missing_fields"]


def test_packet_proof_manifest_is_not_runtime_source_authority() -> None:
    artifact = classify_artifact(
        "out/rte-pkt-02-payload-redaction/RTE-PKT-02_MANIFEST.json"
    )

    assert artifact["classification"] == "proof_governance_artifact"
    assert artifact["is_runtime_source_authority"] is False
    assert (
        artifact["authority_boundary"]
        == "runtime source authority outranks generated proof evidence"
    )


def test_no_provider_and_redaction_status_are_carried_into_report() -> None:
    payload = {
        "status": "READY_FOR_REVIEW",
        "provider_calls": {
            "live_provider_calls_run": False,
            "batch_submit_poll_retrieve_cancel_run": False,
        },
        "live_validation_run": False,
        "redaction_status": "REDACTED",
    }

    report = build_conformance_report(
        payload,
        artifact_path="out/rte-pkt-02-payload-redaction/RTE-PKT-02_MANIFEST.json",
    )

    assert report["fields"]["provider_call_status"]["observed_value"] == "NOT_RUN"
    assert report["fields"]["batch_operation_status"]["observed_value"] == "NOT_RUN"
    assert report["fields"]["live_validation_status"]["observed_value"] == "NOT_RUN"
    assert report["fields"]["redaction_status"]["observed_value"] == "REDACTED"


def test_proof_contract_helper_requires_no_provider_client() -> None:
    assert not hasattr(proof_contract, "requests")
    assert not hasattr(proof_contract, "OpenAI")

    report = build_conformance_report(
        _full_bundle(),
        artifact_path="out/rte-pkt-10-proof-contract/RTE-PKT-10_MANIFEST.json",
    )

    assert report["overall_status"] == "SATISFIED"
    assert report["fields"]["provider_call_status"]["observed_value"] == "NOT_RUN"
    assert report["fields"]["batch_operation_status"]["observed_value"] == "NOT_RUN"


def test_not_applicable_fields_require_explicit_caller_declaration() -> None:
    payload = _full_bundle()
    payload.pop("handoff_refs")

    report = build_conformance_report(
        payload,
        artifact_path="out/rte-pkt-10-proof-contract/RTE-PKT-10_MANIFEST.json",
        not_applicable_fields={"handoff_refs"},
    )

    assert report["overall_status"] == "SATISFIED"
    assert report["fields"]["handoff_refs"]["status"] == "NOT_APPLICABLE"
