"""Tests for the independent embedded-audit CI entrypoint."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from scripts.audit.run_embedded_audit import (
    build_diagnostic_failure_proof,
    build_embedded_audit_proof,
    enforce_independent_audit_proof,
    independent_audit_errors,
    run_cli,
)
from tools.pr_steward.collector import _independent_audit_errors


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "proof" / "embedded_audit.schema.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "embedded-audit.yml"
STEWARD_WORKFLOW_PATH = ROOT / ".github" / "workflows" / "pr-steward.yml"


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _route() -> dict:
    return {
        "tool": "pal-mcp-clink",
        "underlying_cli": "claude",
        "clink_client_name": "claude-audit",
        "audit_safe_config_proven": True,
        "clink_mutation_flags_detected": [],
        "invocation_template": (
            "pal-clink --client claude-audit --role codereviewer "
            "--input PAL_CLINK_AUDIT_INPUT.md "
            "--output PAL_CLINK_AUDIT_OUTPUT.json"
        ),
    }


def _pal_output(verdict: str = "PASS") -> dict:
    return {
        "status": "success",
        "verdict": verdict,
        "findings": [],
        "risks": [],
    }


def test_build_embedded_audit_proof_normalizes_pass_with_redacted_provenance() -> None:
    proof = build_embedded_audit_proof(
        packet_id="TP-DMX-AUDIT-CI-PROVENANCE-104",
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=760,
        head_sha="a" * 40,
        route=_route(),
        pal_output=_pal_output(),
        token_present=True,
        token_source="EMBEDDED_AUDIT_TOKEN",
        generated_at="2026-01-01T00:00:00Z",
    )

    jsonschema.Draft7Validator(_schema()).validate(proof["embedded_audit"])
    assert proof["embedded_audit"]["status"] == "PASS"
    assert proof["executed"] is True
    assert proof["embedded_audit"]["auditor_tool"] == "pal-mcp-clink"
    assert proof["provenance"]["proof_author"] == "independent-embedded-audit"
    assert proof["provenance"]["trusted_token_status"] == "AVAILABLE"
    assert proof["provenance"]["token_source"] == "EMBEDDED_AUDIT_TOKEN"
    assert proof["provenance"]["token_value_recorded"] is False
    assert "secret-value" not in json.dumps(proof)


def test_build_embedded_audit_proof_skips_fail_closed_without_trusted_token() -> None:
    proof = build_embedded_audit_proof(
        packet_id="TP-DMX-AUDIT-CI-PROVENANCE-104",
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=760,
        head_sha="b" * 40,
        route=_route(),
        pal_output=_pal_output(),
        token_present=False,
        token_source="EMBEDDED_AUDIT_TOKEN",
        generated_at="2026-01-01T00:00:00Z",
    )

    jsonschema.Draft7Validator(_schema()).validate(proof["embedded_audit"])
    assert proof["embedded_audit"]["status"] == "SKIPPED"
    assert proof["executed"] is False
    assert proof["embedded_audit"]["auditor_tool"] == "none"
    assert proof["provenance"]["trusted_token_status"] == "UNKNOWN"
    assert "separate least-privilege token" in proof["embedded_audit"]["skip_reason"]


def test_run_cli_writes_proof_and_auditor_report(tmp_path: Path) -> None:
    route_path = tmp_path / "AUDITOR_ROUTE.json"
    pal_output_path = tmp_path / "PAL_CLINK_AUDIT_OUTPUT.json"
    out_dir = tmp_path / "proof"
    route_path.write_text(json.dumps(_route()), encoding="utf-8")
    pal_output_path.write_text(json.dumps(_pal_output()), encoding="utf-8")

    exit_code = run_cli(
        [
            "--packet-id",
            "TP-DMX-AUDIT-CI-PROVENANCE-104",
            "--repo",
            "DDD-Enterprises/dopemux-mvp",
            "--pr",
            "760",
            "--head-sha",
            "c" * 40,
            "--route-json",
            str(route_path),
            "--pal-output-json",
            str(pal_output_path),
            "--out",
            str(out_dir),
            "--generated-at",
            "2026-01-01T00:00:00Z",
        ],
        env={"EMBEDDED_AUDIT_TOKEN": "secret-value"},
    )

    assert exit_code == 0
    proof = json.loads((out_dir / "PROOF.json").read_text(encoding="utf-8"))
    jsonschema.Draft7Validator(_schema()).validate(proof["embedded_audit"])
    assert proof["embedded_audit"]["status"] == "PASS"
    assert proof["executed"] is True
    report_text = (out_dir / proof["embedded_audit"]["report_path"]).read_text(
        encoding="utf-8"
    )
    assert "secret-value" not in (out_dir / "PROOF.json").read_text(encoding="utf-8")
    assert "secret-value" not in report_text
    assert "PROOF.json" in report_text


def test_run_cli_skips_when_route_json_is_missing(tmp_path: Path) -> None:
    out_dir = tmp_path / "proof"

    exit_code = run_cli(
        [
            "--packet-id",
            "TP-DMX-AUDIT-CI-PROVENANCE-104",
            "--repo",
            "DDD-Enterprises/dopemux-mvp",
            "--pr",
            "760",
            "--head-sha",
            "d" * 40,
            "--route-json",
            str(tmp_path / "missing" / "AUDITOR_ROUTE.json"),
            "--out",
            str(out_dir),
            "--generated-at",
            "2026-01-01T00:00:00Z",
        ],
        env={},
    )

    assert exit_code == 0
    proof = json.loads((out_dir / "PROOF.json").read_text(encoding="utf-8"))
    jsonschema.Draft7Validator(_schema()).validate(proof["embedded_audit"])
    assert proof["embedded_audit"]["status"] == "SKIPPED"
    assert proof["executed"] is False
    assert "auditor route JSON" in proof["embedded_audit"]["skip_reason"]
    assert (out_dir / proof["embedded_audit"]["report_path"]).is_file()


def test_run_cli_skips_when_supplied_pal_output_json_is_missing(
    tmp_path: Path,
) -> None:
    route_path = tmp_path / "AUDITOR_ROUTE.json"
    out_dir = tmp_path / "proof"
    route_path.write_text(json.dumps(_route()), encoding="utf-8")

    exit_code = run_cli(
        [
            "--packet-id",
            "TP-DMX-AUDIT-CI-PROVENANCE-104",
            "--repo",
            "DDD-Enterprises/dopemux-mvp",
            "--pr",
            "760",
            "--head-sha",
            "e" * 40,
            "--route-json",
            str(route_path),
            "--pal-output-json",
            str(tmp_path / "missing" / "PAL_CLINK_AUDIT_OUTPUT.json"),
            "--out",
            str(out_dir),
            "--generated-at",
            "2026-01-01T00:00:00Z",
        ],
        env={"EMBEDDED_AUDIT_TOKEN": "secret-value"},
    )

    assert exit_code == 0
    proof = json.loads((out_dir / "PROOF.json").read_text(encoding="utf-8"))
    jsonschema.Draft7Validator(_schema()).validate(proof["embedded_audit"])
    assert proof["embedded_audit"]["status"] == "SKIPPED"
    assert proof["executed"] is False
    assert "PAL clink output JSON" in proof["embedded_audit"]["skip_reason"]
    assert (out_dir / proof["embedded_audit"]["report_path"]).is_file()


def test_embedded_audit_workflow_uses_trusted_source_and_least_privilege() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    permissions = text.split("permissions:\n", 1)[1].split("\njobs:", 1)[0]

    assert "pull_request_target:" in text
    # Trigger must not use untrusted pull_request alone; legacy name may appear
    # only inside metadata shell equality checks.
    assert "on:\n  pull_request_target:" in text or "on:\n  pull_request_target" in text
    assert "contents: read" in text
    assert "pull-requests: read" in text
    assert "checks: read" in text
    assert "statuses: read" in text
    assert ": write" not in permissions
    assert "scripts/audit/run_embedded_audit.py" in text
    assert "persist-credentials: false" in text


def test_embedded_audit_workflow_handles_pull_request_target_metadata() -> None:
    """Regression: trigger is pull_request_target; shell must not only match pull_request."""
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert 'EVENT_NAME" = "pull_request_target"' in text or \
        "\"$EVENT_NAME\" = \"pull_request_target\"" in text or \
        '[ "$EVENT_NAME" = "pull_request_target" ]' in text
    assert '[ "$EVENT_NAME" = "pull_request" ] || [ "$EVENT_NAME" = "pull_request_target" ]' in text
    assert '[ "$EVENT_NAME" = "workflow_dispatch" ]' in text
    assert "EVENT_PR_NUMBER" in text
    assert "EVENT_HEAD_SHA" in text
    assert "INPUT_PR_NUMBER" in text
    assert "INPUT_HEAD_SHA" in text


def test_embedded_audit_workflow_runs_emitter_from_trusted_source() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "Checkout trusted audit source" in text
    assert "path: trusted-source" in text
    assert "ref: ${{ steps.pr.outputs.trusted_ref }}" in text
    assert "TRUSTED_FALLBACK_REF: ${{ github.event.repository.default_branch }}" in text
    assert "TRUSTED_FALLBACK_SHA" not in text
    assert "working-directory: trusted-source" in text
    assert "id: head_integrity" in text
    assert "Emit independent embedded audit proof" in text
    assert "Enforce independent audit result" in text
    assert "enforce_independent_audit_proof" in text
    assert "EMBEDDED_AUDIT_TOKEN: ${{ secrets.EMBEDDED_AUDIT_TOKEN }}" in text
    assert "refs/pull/${PR_NUMBER}/head" in text
    assert 'pr_head_sha" = "$EXPECTED_HEAD_SHA"' in text
    assert "Requested PR head SHA could not be fetched or no longer matches the PR head." in text
    assert "Emit skipped embedded audit proof" not in text
    assert "NEEDS_SUPERVISOR" in text
    assert '"executed": False' in text or '"executed": false' in text
    assert "git -C trusted-source fetch --no-tags --depth=1 origin" in text
    assert "Checkout requested head" not in text
    assert "ref: ${{ steps.pr.outputs.head_sha }}" not in text
    assert "github.event.pull_request.head.sha || github.sha" not in text
    assert "Verify requested head SHA" in text
    assert "Run PAL clink audit" in text
    assert "scripts/audit/pal_clink_runner.py" in text
    assert "preflight_status=$?" in text
    assert "mkdir -p ../embedded-audit-artifacts" in text
    assert "base_sha=\"$(git rev-parse HEAD)\"" in text
    assert "head_sha='${{ steps.pr.outputs.head_sha }}'" in text
    assert "git cat-file -e \"${head_sha}^{commit}\"" in text
    assert "Changed files:" in text
    assert "git diff --find-renames --name-status \"$base_sha\" \"$head_sha\"" in text
    assert "Unified diff:" in text
    assert (
        "git diff --find-renames --no-ext-diff "
        "\"$base_sha\" \"$head_sha\""
    ) in text
    assert "--route-json ../embedded-audit-artifacts/AUDITOR_ROUTE.json" in text
    assert (
        "--pal-output-json "
        "../embedded-audit-artifacts/PAL_CLINK_AUDIT_OUTPUT.json"
    ) in text
    assert (
        'if [ "$actual_head_sha" = "$EXPECTED_HEAD_SHA" ] '
        '&& [ "$pr_head_sha" = "$EXPECTED_HEAD_SHA" ]; then'
    ) in text
    # Soft runner exit is intentional; hard enforcement is authoritative.
    assert "Soft exit is intentional" in text or "soft_runner_exit" in text
    assert "missing on the trusted ref" in text
    assert "embedded-audit-pr-${{ steps.pr.outputs.number }}-head-${{ steps.pr.outputs.head_sha }}-proof" in text
    # Candidate must not be checked out as working tree with secrets.
    assert "path: candidate" not in text
    assert "EMBEDDED_AUDIT_TOKEN" in text
    # Token only appears in emit step context (trusted scripts), not in candidate checkout.


def test_pr_steward_workflow_uses_completed_independent_audit_artifact() -> None:
    text = STEWARD_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "workflow_run:" in text
    assert "workflows: [embedded-audit]" in text
    assert "gh run download" in text
    assert "independent-audit/PROOF.json" in text
    assert "--proof-path independent-audit/PROOF.json" in text
    assert "scripts.audit.pr_audit_router" not in text
    assert "Validate audit workflow-run identity" in text
    assert "conclusion_ok=" in text
    assert "publish failure status" in text or "Publish readiness status" in text
    assert "repository_missing" in text
    assert 'name == "embedded-audit" and path.endswith("embedded-audit.yml")' in text
    assert "embedded-audit-pr-" in text
    assert "Exactly one expected proof artifact is required" in text
    # Artifact name must use validated proof identity, not stale steps.pr.
    assert "name: pr-steward-${{ steps.pr.outputs.number }}" not in text
    assert "pr-steward-pr-${{ steps.proof.outputs.pr_number }}-head-${{ steps.proof.outputs.head_sha }}-readiness" in text
    assert "final readiness" in text
    assert "advisory check-only intake" in text  # documented old name for migration
    assert "enforce_independent_audit_proof" in text
    assert "persist-credentials: false" in text
    # PR head for artifact selection comes from artifact name, not run.head_sha
    # (unreliable under pull_request_target).
    assert "EXPECTED_HEAD_SHA: ${{ steps.run_identity.outputs.head_sha }}" not in text
    assert r"^embedded-audit-pr-(\d+)-head-([0-9a-f]{40})-proof$" in text
    assert "jq -s" in text
    assert "live_head" in text
    assert "Publish readiness status on candidate PR head" in text
    assert 'context="PR Steward / final readiness"' in text
    assert "statuses: write" in text


def _passing_proof(**overrides: object) -> dict:
    proof: dict = {
        "packet_id": "TP-DMX-AUDIT-CI-PROVENANCE-104",
        "repo": "DDD-Enterprises/dopemux-mvp",
        "pr_number": 1042,
        "head_sha": "a" * 40,
        "executed": True,
        "dry_run": False,
        "embedded_audit": {
            "status": "PASS",
            "report_path": "proof/x/AUDITOR_REPORT.md",
        },
        "provenance": {
            "proof_author": "independent-embedded-audit",
            "workflow": "embedded-audit.yml",
        },
    }
    proof.update(overrides)
    return proof


def test_enforce_accepts_passing_independent_audit() -> None:
    proof = _passing_proof()
    enforce_independent_audit_proof(
        proof,
        expected_pr=1042,
        expected_head_sha="a" * 40,
        expected_repo="DDD-Enterprises/dopemux-mvp",
    )


@pytest.mark.parametrize(
    "overrides,expected_fragment",
    [
        ({"executed": False}, "audit_not_executed"),
        ({"provenance": None}, "audit_provenance_missing"),
        (
            {"provenance": {"proof_author": "self", "workflow": "embedded-audit.yml"}},
            "unexpected proof author",
        ),
        (
            {
                "provenance": {
                    "proof_author": "independent-embedded-audit",
                    "workflow": "other.yml",
                }
            },
            "unexpected workflow",
        ),
        ({"pr_number": 999}, "audit_pr_mismatch"),
        ({"head_sha": "b" * 40}, "audit_head_mismatch"),
        ({"dry_run": True}, "audit_proof_dry_run"),
        ({"dry_run": "true"}, "audit_proof_malformed_dry_run"),
    ],
)
def test_enforce_rejects_spoof_and_mismatch_shapes(
    overrides: dict, expected_fragment: str
) -> None:
    proof = _passing_proof(**overrides)
    with pytest.raises(SystemExit) as exc:
        enforce_independent_audit_proof(
            proof,
            expected_pr=1042,
            expected_head_sha="a" * 40,
            expected_repo="DDD-Enterprises/dopemux-mvp",
        )
    assert expected_fragment in str(exc.value)


def test_independent_audit_errors_rejects_missing_repo_when_expected() -> None:
    proof = _passing_proof()
    proof.pop("repo", None)
    errors = independent_audit_errors(
        proof, expected_repo="DDD-Enterprises/dopemux-mvp"
    )
    assert any("audit_repo_missing" in e for e in errors)
    proof["repo"] = ""
    errors = independent_audit_errors(
        proof, expected_repo="DDD-Enterprises/dopemux-mvp"
    )
    assert any("audit_repo_missing" in e for e in errors)


def test_enforce_rejects_status_pass_without_execution() -> None:
    """status=PASS alone must never green the gate."""
    proof = _passing_proof(executed=False)
    proof["embedded_audit"]["status"] = "PASS"
    with pytest.raises(SystemExit) as exc:
        enforce_independent_audit_proof(
            proof,
            expected_pr=1042,
            expected_head_sha="a" * 40,
        )
    assert "audit_not_executed" in str(exc.value)


def test_enforce_rejects_non_passing_status_even_when_executed() -> None:
    proof = _passing_proof()
    proof["embedded_audit"]["status"] = "NEEDS_SUPERVISOR"
    with pytest.raises(SystemExit) as exc:
        enforce_independent_audit_proof(
            proof,
            expected_pr=1042,
            expected_head_sha="a" * 40,
        )
    assert "did not pass" in str(exc.value)


def test_diagnostic_failure_proof_has_no_trusted_provenance() -> None:
    proof = build_diagnostic_failure_proof(
        packet_id="TP-DMX-AUDIT-CI-PROVENANCE-104",
        repo="DDD-Enterprises/dopemux-mvp",
        pr_number=1042,
        head_sha="c" * 40,
        reason="missing emitter",
    )
    assert proof["executed"] is False
    assert proof["embedded_audit"]["status"] == "SKIPPED"
    assert proof["embedded_audit"]["auditor_tool"] == "none"
    assert proof["embedded_audit"]["auditor_model"] == "unknown"
    assert proof["embedded_audit"]["invocation"] is None
    assert proof["embedded_audit"]["exit_code"] is None
    assert proof["embedded_audit"]["skip_reason"] == "missing emitter"
    assert "provenance" not in proof
    jsonschema.Draft7Validator(_schema()).validate(proof["embedded_audit"])
    errors = independent_audit_errors(proof)
    assert any("audit_not_executed" in e for e in errors)
    assert any("provenance" in e for e in errors)
    with pytest.raises(SystemExit):
        enforce_independent_audit_proof(
            proof, expected_pr=1042, expected_head_sha="c" * 40
        )


def test_diagnostic_missing_emitter_workflow_shape_is_schema_valid_skipped() -> None:
    """Missing-emitter branch must emit SKIPPED+none/unknown (schema), not NEEDS_SUPERVISOR."""
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    # Both diagnostic paths use schema-valid SKIPPED with none/unknown.
    assert "missing on the trusted ref" in text
    assert "could not be fetched or no longer matches the PR head" in text
    assert '"status": "SKIPPED"' in text
    assert '"auditor_tool": "none"' in text
    assert '"auditor_model": "unknown"' in text
    # Invalid combo must not appear in diagnostic emission blocks.
    # (PASS_WITH_RISKS / NEEDS_SUPERVISOR may still appear elsewhere for other reasons.)
    missing_emitter_block = text.split("is missing on the trusted ref.", 1)[1][:1200]
    assert '"status": "SKIPPED"' in missing_emitter_block
    assert '"status": "NEEDS_SUPERVISOR"' not in missing_emitter_block
    head_mismatch_block = text.split(
        "could not be fetched or no longer matches the PR head.", 1
    )[1][:1200]
    assert '"status": "SKIPPED"' in head_mismatch_block
    assert '"status": "NEEDS_SUPERVISOR"' not in head_mismatch_block


def test_diagnostic_head_mismatch_and_missing_emitter_proofs_schema_and_enforce() -> None:
    """Both diagnostic shapes: schema-valid SKIPPED; hard enforce still fails closed."""
    reasons = (
        "Trusted audit emitter scripts/audit/run_embedded_audit.py is missing on the trusted ref.",
        "Requested PR head SHA could not be fetched or no longer matches the PR head.",
    )
    for reason in reasons:
        proof = build_diagnostic_failure_proof(
            packet_id="TP-DMX-AUDIT-CI-PROVENANCE-104",
            repo="DDD-Enterprises/dopemux-mvp",
            pr_number=1042,
            head_sha="d" * 40,
            reason=reason,
        )
        jsonschema.Draft7Validator(_schema()).validate(proof["embedded_audit"])
        assert proof["executed"] is False
        assert proof["embedded_audit"]["status"] == "SKIPPED"
        with pytest.raises(SystemExit) as exc:
            enforce_independent_audit_proof(
                proof,
                expected_pr=1042,
                expected_head_sha="d" * 40,
                expected_repo="DDD-Enterprises/dopemux-mvp",
            )
        assert "audit_not_executed" in str(exc.value)


def test_collector_and_enforce_parity_matrix() -> None:
    """Both surfaces must accept/reject the same cases."""
    cases = [
        (_passing_proof(), True),
        (_passing_proof(executed=False), False),
        (_passing_proof(provenance=None), False),
        (
            _passing_proof(
                provenance={
                    "proof_author": "forged",
                    "workflow": "embedded-audit.yml",
                }
            ),
            False,
        ),
        (
            _passing_proof(
                provenance={
                    "proof_author": "independent-embedded-audit",
                    "workflow": "wrong.yml",
                }
            ),
            False,
        ),
        (_passing_proof(dry_run=True, executed=True), False),
        (_passing_proof(dry_run="true"), False),
        (_passing_proof(head_sha="d" * 40), True),  # no expected head in collector
    ]
    for proof, expect_ok in cases:
        collector_errors = _independent_audit_errors(proof)
        shared_errors = independent_audit_errors(proof)
        assert collector_errors == shared_errors
        assert (not shared_errors) is expect_ok
        if expect_ok and proof.get("head_sha") == "a" * 40:
            enforce_independent_audit_proof(
                proof, expected_pr=1042, expected_head_sha="a" * 40
            )
        if not expect_ok:
            # status may still be PASS; enforce must still fail on identity errors
            with pytest.raises(SystemExit):
                enforce_independent_audit_proof(
                    proof,
                    expected_pr=1042,
                    expected_head_sha="a" * 40,
                )


def test_synthetic_runner_error_payload_cannot_pass_enforcement() -> None:
    """PAL soft-exit error JSON must not green the workflow via status alone."""
    # Emulates workflow synthesizing {"status":"error",...} then building a
    # skipped/failed proof; enforcement must reject executed!=true / non-PASS.
    synthetic_pal = {"status": "error", "risks": ["runner failed"]}
    # Even if a bad actor rewrote status to PASS with executed false:
    forged = {
        "executed": False,
        "pr_number": 1042,
        "head_sha": "a" * 40,
        "embedded_audit": {"status": "PASS"},
        "provenance": {
            "proof_author": "independent-embedded-audit",
            "workflow": "embedded-audit.yml",
        },
        "pal_hint": synthetic_pal,
    }
    with pytest.raises(SystemExit) as exc:
        enforce_independent_audit_proof(
            forged, expected_pr=1042, expected_head_sha="a" * 40
        )
    assert "audit_not_executed" in str(exc.value)
