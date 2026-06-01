"""Tests for the independent embedded-audit CI entrypoint."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from scripts.audit.run_embedded_audit import build_embedded_audit_proof, run_cli


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "proof" / "embedded_audit.schema.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "embedded-audit.yml"


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
    assert (out_dir / proof["embedded_audit"]["report_path"]).is_file()
    assert "secret-value" not in (out_dir / "PROOF.json").read_text(encoding="utf-8")


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
    assert "auditor route JSON" in proof["embedded_audit"]["skip_reason"]
    assert (out_dir / proof["embedded_audit"]["report_path"]).is_file()


def test_embedded_audit_workflow_is_read_only_and_not_pull_request_target() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    permissions = text.split("permissions:\n", 1)[1].split("\njobs:", 1)[0]

    assert "pull_request_target" not in text
    assert "EMBEDDED_AUDIT_TOKEN: ${{ secrets.EMBEDDED_AUDIT_TOKEN }}" not in text
    assert "contents: read" in text
    assert "pull-requests: read" in text
    assert "checks: read" in text
    assert "statuses: read" in text
    assert "continue-on-error: true" in text
    assert ": write" not in permissions
    assert "scripts/audit/run_embedded_audit.py" in text


def test_embedded_audit_workflow_runs_emitter_from_trusted_source() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "Checkout trusted audit source" in text
    assert "path: trusted-source" in text
    assert "ref: ${{ steps.pr.outputs.trusted_ref }}" in text
    assert "working-directory: trusted-source" in text
    assert "git -C trusted-source fetch --no-tags --depth=1 origin" in text
    assert "ref: ${{ steps.pr.outputs.head_sha }}" not in text
    assert "github.event.pull_request.head.sha || github.sha" not in text
    assert "Verify requested head SHA" in text
    assert 'test "$actual_head_sha" = "$EXPECTED_HEAD_SHA"' in text
