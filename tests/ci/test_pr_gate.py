"""Tests for the ci-summary PR gate in ci-complete.yml.

Structural invariants:
- ci-summary needs all 9 upstream jobs
- ci-summary runs with if: always()
- Gate blocks on code-quality, tests, extractor-smoke failures
- Advisory jobs (extractor-full, installer-smoke, scoped-coverage, integration,
  security, docs) do NOT trigger exit 1
- Gate comment mentions branch-protection UNKNOWN caveat
"""
import pathlib
import re

import yaml
import pytest

_WORKFLOW_PATH = pathlib.Path(__file__).parents[2] / ".github" / "workflows" / "ci-complete.yml"
_WORKFLOW = yaml.safe_load(_WORKFLOW_PATH.read_text())
_CI_SUMMARY = _WORKFLOW["jobs"]["ci-summary"]
_GATE_STEP = next(
    s for s in _CI_SUMMARY["steps"]
    if "ADHD-Optimized Results Summary" in s.get("name", "")
)
_GATE_SCRIPT = _GATE_STEP["run"]

_REQUIRED_BLOCKING = ("code-quality", "tests", "extractor-smoke")
_ADVISORY = ("extractor-full", "installer-smoke", "scoped-coverage", "integration", "security", "docs")


class TestCiSummaryStructure:
    def test_ci_summary_job_exists(self):
        assert "ci-summary" in _WORKFLOW["jobs"]

    def test_ci_summary_if_always(self):
        assert str(_CI_SUMMARY.get("if", "")).strip() == "always()"

    def test_ci_summary_needs_all_blocking_jobs(self):
        needs = _CI_SUMMARY.get("needs", [])
        for job in _REQUIRED_BLOCKING:
            assert job in needs, f"ci-summary missing required blocking job: {job!r}"

    def test_ci_summary_needs_advisory_jobs(self):
        needs = _CI_SUMMARY.get("needs", [])
        for job in _ADVISORY:
            assert job in needs, f"ci-summary missing advisory job: {job!r}"

    def test_ci_summary_has_exactly_one_step(self):
        assert len(_CI_SUMMARY["steps"]) == 1


class TestGateLogic:
    def test_gate_step_exists(self):
        assert _GATE_STEP is not None

    def test_gate_blocks_on_code_quality(self):
        assert "needs.code-quality.result" in _GATE_SCRIPT

    def test_gate_blocks_on_tests(self):
        assert "needs.tests.result" in _GATE_SCRIPT

    def test_gate_blocks_on_extractor_smoke(self):
        assert "needs.extractor-smoke.result" in _GATE_SCRIPT

    def test_gate_exits_1_on_failure(self):
        assert "exit 1" in _GATE_SCRIPT

    def test_gate_checks_each_required_job_uses_success_comparison(self):
        # All three required blocking jobs must be referenced in the gate section
        # and each must be compared against "success" (skipped/cancelled also block).
        for job in _REQUIRED_BLOCKING:
            assert f"needs.{job}.result" in _GATE_SCRIPT, (
                f"Gate must reference needs.{job}.result"
            )
        # At least one != "success" comparison per required blocking job
        success_checks = re.findall(r'!=\s*["\']success["\']', _GATE_SCRIPT)
        assert len(success_checks) >= len(_REQUIRED_BLOCKING), (
            f"Gate must have >= {len(_REQUIRED_BLOCKING)} '!= success' comparisons "
            f"(one per required blocking job), found {len(success_checks)}"
        )

    def test_advisory_extractor_full_result_absent_from_gate(self):
        # extractor-full always exits 0 (set +e trap) — its .result is structurally
        # always "success" regardless of actual test outcomes.
        # Gate must not reference extractor-full.result at all.
        assert "needs.extractor-full.result" not in _GATE_SCRIPT, (
            "extractor-full.result must not appear in gate script; "
            "it is advisory-only (always exits 0); use outputs.suite_status for informational display"
        )

    def test_gate_has_branch_protection_unknown_caveat(self):
        assert "UNKNOWN" in _GATE_SCRIPT, (
            "Gate script must document that branch protection truth is UNKNOWN"
        )

    def test_gate_mentions_advisory_carve_out(self):
        lower = _GATE_SCRIPT.lower()
        assert "advisory" in lower, "Gate script must document advisory carve-out"

    def test_gate_summary_blocked_message(self):
        assert "PR Gate: BLOCKED" in _GATE_SCRIPT

    def test_gate_summary_clear_message(self):
        assert "PR Gate: CLEAR" in _GATE_SCRIPT


class TestWorkflowNoTrailingWhitespace:
    def test_no_trailing_whitespace_in_ci_summary_step(self):
        for i, line in enumerate(_GATE_SCRIPT.splitlines(), 1):
            assert line == line.rstrip(), (
                f"Trailing whitespace on line {i} of gate script: {line!r}"
            )
