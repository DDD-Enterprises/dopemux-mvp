"""Tests for scripts/audit/validate_audit_proof.py.

Covers:
  - Valid PASS bundle (all required fields, non-SKIPPED)
  - Valid PASS_WITH_RISKS bundle
  - Valid SKIPPED bundle (tool=none, model=unknown, invocation/exit_code null, skip_reason present)
  - Invalid: enum violation in auditor_tool
  - Invalid: enum violation in auditor_model
  - Invalid: enum violation in status
  - Invalid: non-SKIPPED but exit_code is string (contract: must be integer)
  - Invalid: non-SKIPPED but invocation is null
  - Invalid: SKIPPED but skip_reason absent/null
  - Invalid: missing required field (findings)
  - Invalid: extra field (additionalProperties: false)
  - Missing embedded_audit key entirely
  - JSON parse error
  - Directory scan via --all
  - Quiet flag suppresses PASS output
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "audit" / "validate_audit_proof.py"
SCHEMA_PATH = ROOT / "schemas" / "proof" / "embedded_audit.schema.json"

# ---------------------------------------------------------------------------
# Minimal valid embedded_audit shapes
# ---------------------------------------------------------------------------

_VALID_PASS: dict = {
    "required": True,
    "status": "PASS",
    "auditor_tool": "claude-code-cli",
    "auditor_model": "claude-sonnet-4.6",
    "invocation": "mcp__pal__codereview expert_model=gpt-5.2 review_type=full",
    "exit_code": 0,
    "report_path": "proof/TP-EXAMPLE-001/AUDITOR_REPORT.md",
    "findings": [],
    "fixes_applied": [],
    "remaining_risks": [],
    "skip_reason": None,
}

_VALID_SKIPPED: dict = {
    "required": False,
    "status": "SKIPPED",
    "auditor_tool": "none",
    "auditor_model": "unknown",
    "invocation": None,
    "exit_code": None,
    "report_path": "proof/TP-EXAMPLE-001/AUDITOR_REPORT.md",
    "findings": [],
    "fixes_applied": [],
    "remaining_risks": [],
    "skip_reason": "No executable logic introduced; read-only evidence capture only.",
}


def _make_proof(embedded_audit: dict) -> dict:
    """Wrap embedded_audit in a minimal top-level PROOF.json shape."""
    return {
        "schema_version": "1.0.0",
        "tp_id": "TP-EXAMPLE-001",
        "embedded_audit": embedded_audit,
    }


def _write_proof(tmp_path: Path, embedded_audit: dict) -> Path:
    proof_path = tmp_path / "PROOF.json"
    proof_path.write_text(
        json.dumps(_make_proof(embedded_audit), indent=2), encoding="utf-8"
    )
    return proof_path


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
        timeout=10,
    )


# ---------------------------------------------------------------------------
# Valid cases
# ---------------------------------------------------------------------------


class TestValidPass:
    def test_exit_code_zero(self, tmp_path: Path) -> None:
        p = _write_proof(tmp_path, _VALID_PASS)
        result = _run([str(p)])
        assert result.returncode == 0

    def test_output_contains_pass(self, tmp_path: Path) -> None:
        p = _write_proof(tmp_path, _VALID_PASS)
        result = _run([str(p)])
        assert "PASS" in result.stdout

    def test_summary_shows_one_pass(self, tmp_path: Path) -> None:
        p = _write_proof(tmp_path, _VALID_PASS)
        result = _run([str(p)])
        assert "1/1 PASS" in result.stdout


class TestValidPassWithRisks:
    def test_exit_code_zero(self, tmp_path: Path) -> None:
        ea = {**_VALID_PASS, "status": "PASS_WITH_RISKS", "remaining_risks": ["mypy not run"]}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 0


class TestValidSkipped:
    def test_exit_code_zero(self, tmp_path: Path) -> None:
        p = _write_proof(tmp_path, _VALID_SKIPPED)
        result = _run([str(p)])
        assert result.returncode == 0

    def test_output_contains_pass(self, tmp_path: Path) -> None:
        p = _write_proof(tmp_path, _VALID_SKIPPED)
        result = _run([str(p)])
        assert "PASS" in result.stdout


class TestReportPathVariants:
    """Schema allows AUDITOR_REPORT.md, AUDITOR_REPAIR_REPORT.md, AUDITOR_REPAIR_N_REPORT.md."""

    def test_repair_report_path_accepted(self, tmp_path: Path) -> None:
        ea = {**_VALID_PASS, "report_path": "proof/TP-EXAMPLE-001/AUDITOR_REPAIR_REPORT.md"}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 0

    def test_repair_numbered_report_path_accepted(self, tmp_path: Path) -> None:
        ea = {**_VALID_PASS, "report_path": "proof/TP-EXAMPLE-001/AUDITOR_REPAIR_1_REPORT.md"}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 0

    def test_non_matching_report_path_rejected(self, tmp_path: Path) -> None:
        ea = {**_VALID_PASS, "report_path": "proof/TP-EXAMPLE-001/PROOF.json"}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1


class TestValidWithFindings:
    def test_pass_with_finding(self, tmp_path: Path) -> None:
        ea = {
            **_VALID_PASS,
            "status": "PASS_WITH_RISKS",
            "findings": [
                {
                    "id": "F-001-LOW-1",
                    "severity": "LOW",
                    "title": "Minor naming inconsistency",
                    "status": "ACCEPTED_RISK",
                    "body": "Pre-existing, not introduced here.",
                }
            ],
        }
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# Enum violations
# ---------------------------------------------------------------------------


class TestEnumViolations:
    def test_bad_auditor_tool(self, tmp_path: Path) -> None:
        ea = {**_VALID_PASS, "auditor_tool": "PAL MCP codereview (mcp__pal__codereview)"}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1
        assert "FAIL" in result.stdout

    def test_bad_auditor_model(self, tmp_path: Path) -> None:
        ea = {**_VALID_PASS, "auditor_model": "gemini-2.5-pro"}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1

    def test_bad_status(self, tmp_path: Path) -> None:
        ea = {**_VALID_PASS, "status": "NOT_RUN"}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1

    def test_bad_finding_severity(self, tmp_path: Path) -> None:
        ea = {
            **_VALID_PASS,
            "findings": [
                {
                    "id": "F-001",
                    "severity": "CRITICAL",  # not in enum: BLOCKING/HIGH/MEDIUM/LOW/INFO
                    "title": "Something",
                    "status": "OPEN",
                    "body": "Details.",
                }
            ],
        }
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# Contract violations: SKIPPED shape
# ---------------------------------------------------------------------------


class TestSkippedConstraints:
    def test_skipped_with_real_tool_fails(self, tmp_path: Path) -> None:
        """SKIPPED requires auditor_tool=none."""
        ea = {**_VALID_SKIPPED, "auditor_tool": "claude-code-cli"}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1

    def test_skipped_with_real_model_fails(self, tmp_path: Path) -> None:
        """SKIPPED requires auditor_model=unknown."""
        ea = {**_VALID_SKIPPED, "auditor_model": "claude-sonnet-4.6"}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1

    def test_skipped_with_nonnull_invocation_fails(self, tmp_path: Path) -> None:
        ea = {**_VALID_SKIPPED, "invocation": "some-command"}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1

    def test_skipped_with_nonnull_exit_code_fails(self, tmp_path: Path) -> None:
        ea = {**_VALID_SKIPPED, "exit_code": 0}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1

    def test_skipped_without_skip_reason_fails(self, tmp_path: Path) -> None:
        ea = {**_VALID_SKIPPED, "skip_reason": None}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# Contract violations: non-SKIPPED shape
# ---------------------------------------------------------------------------


class TestNonSkippedConstraints:
    def test_string_exit_code_fails(self, tmp_path: Path) -> None:
        """Non-SKIPPED: exit_code must be integer, not string."""
        ea = {**_VALID_PASS, "exit_code": "code_review_complete: true"}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1

    def test_null_invocation_fails(self, tmp_path: Path) -> None:
        """Non-SKIPPED: invocation must be a non-empty string."""
        ea = {**_VALID_PASS, "invocation": None}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1

    def test_tool_none_in_non_skipped_fails(self, tmp_path: Path) -> None:
        """Non-SKIPPED: auditor_tool must not be 'none'."""
        ea = {**_VALID_PASS, "auditor_tool": "none"}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1

    def test_model_unknown_in_non_skipped_fails(self, tmp_path: Path) -> None:
        """Non-SKIPPED: auditor_model must not be 'unknown'."""
        ea = {**_VALID_PASS, "auditor_model": "unknown"}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1

    def test_nonnull_skip_reason_in_non_skipped_fails(self, tmp_path: Path) -> None:
        """Non-SKIPPED: skip_reason must be null."""
        ea = {**_VALID_PASS, "skip_reason": "Some reason"}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1


# ---------------------------------------------------------------------------
# Missing / extra fields
# ---------------------------------------------------------------------------


class TestFieldErrors:
    def test_missing_findings_fails(self, tmp_path: Path) -> None:
        ea = {k: v for k, v in _VALID_PASS.items() if k != "findings"}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1

    def test_missing_fixes_applied_fails(self, tmp_path: Path) -> None:
        ea = {k: v for k, v in _VALID_PASS.items() if k != "fixes_applied"}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1

    def test_extra_field_fails(self, tmp_path: Path) -> None:
        """additionalProperties: false — extra fields are rejected."""
        ea = {**_VALID_PASS, "fallback_used": False}
        p = _write_proof(tmp_path, ea)
        result = _run([str(p)])
        assert result.returncode == 1

    def test_missing_embedded_audit_key_fails(self, tmp_path: Path) -> None:
        proof_path = tmp_path / "PROOF.json"
        proof_path.write_text(
            json.dumps({"schema_version": "1.0.0", "tp_id": "TP-EXAMPLE-001"}, indent=2),
            encoding="utf-8",
        )
        result = _run([str(proof_path)])
        assert result.returncode == 1
        assert "missing top-level field" in result.stdout


# ---------------------------------------------------------------------------
# File / parse errors
# ---------------------------------------------------------------------------


class TestFileErrors:
    def test_json_parse_error_fails(self, tmp_path: Path) -> None:
        proof_path = tmp_path / "PROOF.json"
        proof_path.write_text("{invalid json", encoding="utf-8")
        result = _run([str(proof_path)])
        assert result.returncode == 1

    def test_nonexistent_file_exits_2(self, tmp_path: Path) -> None:
        result = _run([str(tmp_path / "nonexistent_PROOF.json")])
        assert result.returncode == 2


# ---------------------------------------------------------------------------
# Directory scan (--all)
# ---------------------------------------------------------------------------


class TestDirectoryScan:
    def test_scan_finds_all_proof_files(self, tmp_path: Path) -> None:
        # Create two valid bundles in subdirectories
        for name in ("TP-001", "TP-002"):
            d = tmp_path / name
            d.mkdir()
            _write_proof(d, _VALID_PASS)
        result = _run(["--all", str(tmp_path)])
        assert result.returncode == 0
        assert "2/2 PASS" in result.stdout

    def test_scan_reports_failure_when_any_invalid(self, tmp_path: Path) -> None:
        d1 = tmp_path / "TP-001"
        d1.mkdir()
        _write_proof(d1, _VALID_PASS)

        d2 = tmp_path / "TP-002"
        d2.mkdir()
        _write_proof(d2, {**_VALID_PASS, "auditor_tool": "bad-tool-not-in-enum"})

        result = _run(["--all", str(tmp_path)])
        assert result.returncode == 1
        assert "FAIL" in result.stdout

    def test_scan_empty_dir_exits_2(self, tmp_path: Path) -> None:
        result = _run(["--all", str(tmp_path)])
        assert result.returncode == 2

    def test_scan_nonexistent_dir_exits_2(self, tmp_path: Path) -> None:
        result = _run(["--all", str(tmp_path / "no-such-dir")])
        assert result.returncode == 2

    def test_dedup_when_all_and_positional_overlap(self, tmp_path: Path) -> None:
        """Same PROOF.json via --all and as positional arg is validated once, not twice."""
        d = tmp_path / "TP-001"
        d.mkdir()
        p = _write_proof(d, _VALID_PASS)
        result = _run(["--all", str(tmp_path), str(p)])
        assert result.returncode == 0
        assert "1/1 PASS" in result.stdout


# ---------------------------------------------------------------------------
# Quiet flag
# ---------------------------------------------------------------------------


class TestQuietFlag:
    def test_quiet_suppresses_pass_lines(self, tmp_path: Path) -> None:
        p = _write_proof(tmp_path, _VALID_PASS)
        result = _run(["--quiet", str(p)])
        assert result.returncode == 0
        # PASS lines should be absent; summary should still be present
        lines = [ln for ln in result.stdout.splitlines() if ln.startswith("PASS")]
        assert lines == []
        assert "1/1 PASS" in result.stdout

    def test_quiet_still_shows_fail_lines(self, tmp_path: Path) -> None:
        ea = {**_VALID_PASS, "auditor_tool": "bad-tool"}
        p = _write_proof(tmp_path, ea)
        result = _run(["--quiet", str(p)])
        assert result.returncode == 1
        assert "FAIL" in result.stdout


# ---------------------------------------------------------------------------
# No-args usage: exit 2
# ---------------------------------------------------------------------------


class TestUsage:
    def test_no_args_exits_2(self) -> None:
        result = _run([])
        assert result.returncode == 2
