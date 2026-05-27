"""Tests for tools/pr_action_bridge/compiler.py."""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from tools.pr_action_bridge.compiler import compile_action_plan as compile

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "pr_action_bridge" / "action_plan.schema.json"
COMPILER_SRC = ROOT / "tools" / "pr_action_bridge" / "compiler.py"

FIXED_TS = "2026-01-01T00:00:00Z"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def _ready_readiness(pr_number: int = 42, repo: str = "owner/repo") -> dict:
    return {
        "pr": {
            "number": pr_number,
            "url": f"https://github.com/{repo}/pull/{pr_number}",
            "base_ref": "main",
            "head_ref": "test-branch",
            "head_sha": "abc1234",
            "changed_files": [],
            "commits": [],
        },
        "readiness": "READY",
        "blockers": [],
    }


def _readiness_with_blockers(blockers: list[str], tier: str = "BLOCKED") -> dict:
    return {
        "pr": {
            "number": 99,
            "url": "https://github.com/owner/repo/pull/99",
            "base_ref": "main",
            "head_ref": "test-branch",
            "head_sha": "abc1234",
            "changed_files": [],
            "commits": [],
        },
        "readiness": tier,
        "blockers": blockers,
    }


_EMPTY_LEDGER: dict = {"items": []}
_EMPTY_THREADS: dict = {"threads": []}
_EMPTY_CI: dict = {"checks": []}


# ---------------------------------------------------------------------------
# Static safety check: no forbidden imports in compiler.py
# ---------------------------------------------------------------------------


class TestStaticSafety:
    def test_no_pr_merge_import(self) -> None:
        """compiler.py must never import tools.pr_merge or tools/pr_merge."""
        import re
        source = COMPILER_SRC.read_text()
        import_lines = [
            line for line in source.splitlines()
            if re.match(r"^\s*(import|from)\s+", line)
        ]
        for line in import_lines:
            assert "pr_merge" not in line, (
                f"compiler.py imports tools.pr_merge — forbidden by governance: {line!r}"
            )

    def test_no_gh_mutation_calls(self) -> None:
        """compiler.py must not contain gh pr merge/approve/ready/comment."""
        source = COMPILER_SRC.read_text()
        for forbidden in ("gh pr merge", "gh pr approve", "gh pr ready", "gh pr comment"):
            assert forbidden not in source, f"compiler.py contains forbidden call: {forbidden!r}"

    def test_mutation_performed_is_false_literal(self) -> None:
        """mutation_performed must be hardcoded False in the compiled output."""
        plan, _ = compile(
            _ready_readiness(), _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI,
            generated_at=FIXED_TS,
        )
        assert plan["mutation_performed"] is False
        assert type(plan["mutation_performed"]) is bool


# ---------------------------------------------------------------------------
# compile() — READY tier
# ---------------------------------------------------------------------------


class TestCompileReady:
    def test_ready_returns_empty_actions(self) -> None:
        plan, _ = compile(
            _ready_readiness(), _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI,
            generated_at=FIXED_TS,
        )
        assert plan["actions"] == []

    def test_ready_mutation_performed_false(self) -> None:
        plan, _ = compile(
            _ready_readiness(), _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI,
            generated_at=FIXED_TS,
        )
        assert plan["mutation_performed"] is False

    def test_ready_readiness_preserved(self) -> None:
        plan, _ = compile(
            _ready_readiness(), _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI,
            generated_at=FIXED_TS,
        )
        assert plan["readiness"] == "READY"

    def test_ready_pr_number_preserved(self) -> None:
        plan, _ = compile(
            _ready_readiness(pr_number=77), _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI,
            generated_at=FIXED_TS,
        )
        assert plan["pr_number"] == 77

    def test_ready_schema_version(self) -> None:
        plan, _ = compile(
            _ready_readiness(), _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI,
            generated_at=FIXED_TS,
        )
        assert plan["schema_version"] == "1.0.0"

    def test_ready_repair_packet_says_no_actions(self) -> None:
        _, repair = compile(
            _ready_readiness(), _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI,
            generated_at=FIXED_TS,
        )
        assert "No actions required" in repair
        assert "READY" in repair

    def test_ready_validates_against_schema(self) -> None:
        plan, _ = compile(
            _ready_readiness(), _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI,
            generated_at=FIXED_TS,
        )
        jsonschema.validate(plan, _schema())


# ---------------------------------------------------------------------------
# compile() — BLOCKED tier
# ---------------------------------------------------------------------------


class TestCompileBlocked:
    def test_harvest_incomplete_produces_supervisor_action(self) -> None:
        mr = _readiness_with_blockers(["HARVEST_INCOMPLETE"], "BLOCKED")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert len(plan["actions"]) == 1
        assert plan["actions"][0]["category"] == "harvest-incomplete"
        assert plan["actions"][0]["target_role"] == "supervisor"

    def test_pr_is_draft_produces_supervisor_action(self) -> None:
        mr = _readiness_with_blockers(["PR_IS_DRAFT"], "BLOCKED")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["category"] == "pr-is-draft"
        assert plan["actions"][0]["target_role"] == "supervisor"

    def test_pr_closed_produces_supervisor_action(self) -> None:
        mr = _readiness_with_blockers(["PR_CLOSED"], "BLOCKED")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["category"] == "pr-closed"

    def test_mixed_sha_produces_supervisor_action(self) -> None:
        mr = _readiness_with_blockers(["MIXED_SHA_ARTIFACT_SET"], "BLOCKED")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["category"] == "mixed-sha"

    def test_blocked_mutation_performed_false(self) -> None:
        mr = _readiness_with_blockers(["PR_IS_DRAFT"], "BLOCKED")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["mutation_performed"] is False

    def test_blocked_validates_against_schema(self) -> None:
        mr = _readiness_with_blockers(["PR_IS_DRAFT"], "BLOCKED")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        jsonschema.validate(plan, _schema())


# ---------------------------------------------------------------------------
# compile() — NEEDS_SUPERVISOR tier
# ---------------------------------------------------------------------------


class TestCompileNeedsSupervisor:
    def test_unknown_reviewer_produces_supervisor_action(self) -> None:
        mr = _readiness_with_blockers(["UNKNOWN_REVIEWER_NEEDS_CLASSIFICATION"], "NEEDS_SUPERVISOR")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["category"] == "unknown-reviewer"
        assert plan["actions"][0]["target_role"] == "supervisor"

    def test_proof_stale_produces_supervisor_action(self) -> None:
        mr = _readiness_with_blockers(["PROOF_STALE"], "NEEDS_SUPERVISOR")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["category"] == "proof-stale"

    def test_proof_missing_produces_supervisor_action(self) -> None:
        mr = _readiness_with_blockers(["PROOF_MISSING"], "NEEDS_SUPERVISOR")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["category"] == "proof-missing"

    def test_unknown_check_produces_supervisor_action(self) -> None:
        mr = _readiness_with_blockers(["UNKNOWN_CHECK"], "NEEDS_SUPERVISOR")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["category"] == "unknown-check"

    def test_review_item_needs_supervisor_action(self) -> None:
        mr = _readiness_with_blockers(["REVIEW_ITEM_NEEDS_SUPERVISOR"], "NEEDS_SUPERVISOR")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["category"] == "needs-supervisor"

    def test_embedded_audit_prefix_produces_embedded_audit_failed(self) -> None:
        mr = _readiness_with_blockers(["EMBEDDED_AUDIT_FAIL"], "NEEDS_SUPERVISOR")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["category"] == "embedded-audit-failed"
        assert plan["actions"][0]["target_role"] == "supervisor"

    def test_embedded_audit_any_suffix_handled(self) -> None:
        mr = _readiness_with_blockers(["EMBEDDED_AUDIT_NEEDS_SUPERVISOR"], "NEEDS_SUPERVISOR")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["category"] == "embedded-audit-failed"

    def test_unknown_pr_author_produces_supervisor_action(self) -> None:
        mr = _readiness_with_blockers(["UNKNOWN_PR_AUTHOR"], "NEEDS_SUPERVISOR")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["category"] == "unknown-pr-author"
        assert plan["actions"][0]["target_role"] == "supervisor"

    def test_needs_supervisor_validates_against_schema(self) -> None:
        mr = _readiness_with_blockers(["PROOF_STALE"], "NEEDS_SUPERVISOR")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        jsonschema.validate(plan, _schema())

    def test_proof_missing_validates_against_schema(self) -> None:
        mr = _readiness_with_blockers(["PROOF_MISSING"], "NEEDS_SUPERVISOR")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        jsonschema.validate(plan, _schema())

    def test_unknown_pr_author_validates_against_schema(self) -> None:
        mr = _readiness_with_blockers(["UNKNOWN_PR_AUTHOR"], "NEEDS_SUPERVISOR")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        jsonschema.validate(plan, _schema())


# ---------------------------------------------------------------------------
# compile() — NEEDS_IMPLEMENTER tier
# ---------------------------------------------------------------------------


class TestCompileNeedsImplementer:
    def test_unresolved_thread_produces_implementer_action(self) -> None:
        mr = _readiness_with_blockers(["UNRESOLVED_REVIEW_THREAD"], "NEEDS_IMPLEMENTER")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["category"] == "unresolved-thread"
        assert plan["actions"][0]["target_role"] == "implementer"

    def test_failed_check_produces_implementer_action(self) -> None:
        mr = _readiness_with_blockers(["FAILED_CHECK"], "NEEDS_IMPLEMENTER")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["category"] == "failed-check"
        assert plan["actions"][0]["target_role"] == "implementer"

    def test_request_changes_produces_implementer_action(self) -> None:
        mr = _readiness_with_blockers(["REQUEST_CHANGES"], "NEEDS_IMPLEMENTER")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["category"] == "request-changes"

    def test_review_item_must_fix_produces_implementer_action(self) -> None:
        mr = _readiness_with_blockers(["REVIEW_ITEM_MUST_FIX"], "NEEDS_IMPLEMENTER")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["category"] == "must-fix"

    def test_needs_implementer_validates_against_schema(self) -> None:
        mr = _readiness_with_blockers(["FAILED_CHECK"], "NEEDS_IMPLEMENTER")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        jsonschema.validate(plan, _schema())


# ---------------------------------------------------------------------------
# compile() — NOT_READY tier
# ---------------------------------------------------------------------------


class TestCompileNotReady:
    def test_pending_check_produces_ci_action(self) -> None:
        mr = _readiness_with_blockers(["PENDING_CHECK"], "NOT_READY")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["category"] == "pending-check"
        assert plan["actions"][0]["target_role"] == "ci"

    def test_not_ready_validates_against_schema(self) -> None:
        mr = _readiness_with_blockers(["PENDING_CHECK"], "NOT_READY")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        jsonschema.validate(plan, _schema())


# ---------------------------------------------------------------------------
# source_item_id cross-referencing
# ---------------------------------------------------------------------------


class TestSourceItemId:
    def test_unresolved_thread_cross_refs_thread(self) -> None:
        mr = _readiness_with_blockers(["UNRESOLVED_REVIEW_THREAD"], "NEEDS_IMPLEMENTER")
        threads = {
            "threads": [
                {"id": "T_abc123", "resolved": False},
            ]
        }
        plan, _ = compile(mr, _EMPTY_LEDGER, threads, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["source_item_id"] == "T_abc123"

    def test_failed_check_cross_refs_ci(self) -> None:
        mr = _readiness_with_blockers(["FAILED_CHECK"], "NEEDS_IMPLEMENTER")
        ci = {
            "checks": [
                {"id": "CI_001", "name": "test-suite", "blockers": ["FAILED_CHECK"]},
            ]
        }
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, ci, generated_at=FIXED_TS)
        assert plan["actions"][0]["source_item_id"] == "CI_001"

    def test_review_item_must_fix_cross_refs_ledger(self) -> None:
        mr = _readiness_with_blockers(["REVIEW_ITEM_MUST_FIX"], "NEEDS_IMPLEMENTER")
        ledger = {
            "items": [
                {"id": "R_xyz", "blockers": ["REVIEW_ITEM_MUST_FIX"]},
            ]
        }
        plan, _ = compile(mr, ledger, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["source_item_id"] == "R_xyz"

    def test_no_matching_item_gives_null(self) -> None:
        mr = _readiness_with_blockers(["HARVEST_INCOMPLETE"], "BLOCKED")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["source_item_id"] is None


# ---------------------------------------------------------------------------
# REPAIR_PACKET.md rendering
# ---------------------------------------------------------------------------


class TestRepairPacketRender:
    def test_repair_packet_has_header(self) -> None:
        _, repair = compile(
            _ready_readiness(), _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI,
            generated_at=FIXED_TS,
        )
        assert "# REPAIR_PACKET" in repair

    def test_repair_packet_groups_by_role_supervisor_first(self) -> None:
        mr = _readiness_with_blockers(
            ["UNRESOLVED_REVIEW_THREAD", "PROOF_STALE"],
            "NEEDS_SUPERVISOR",
        )
        _, repair = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        sup_pos = repair.index("## Supervisor Actions")
        impl_pos = repair.index("## Implementer Actions")
        assert sup_pos < impl_pos

    def test_repair_packet_implementer_before_ci(self) -> None:
        mr = _readiness_with_blockers(
            ["FAILED_CHECK", "PENDING_CHECK"],
            "NEEDS_IMPLEMENTER",
        )
        _, repair = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        impl_pos = repair.index("## Implementer Actions")
        ci_pos = repair.index("## CI / Wait Actions")
        assert impl_pos < ci_pos

    def test_repair_packet_includes_action_ids(self) -> None:
        mr = _readiness_with_blockers(["PR_IS_DRAFT"], "BLOCKED")
        _, repair = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert "action-0001" in repair

    def test_repair_packet_no_trailing_whitespace_on_any_line(self) -> None:
        mr = _readiness_with_blockers(
            ["PR_IS_DRAFT", "UNRESOLVED_REVIEW_THREAD", "PENDING_CHECK"],
            "BLOCKED",
        )
        _, repair = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        for i, line in enumerate(repair.splitlines(), 1):
            assert line == line.rstrip(), f"Trailing whitespace on line {i}: {line!r}"

    def test_repair_packet_ends_with_newline(self) -> None:
        _, repair = compile(
            _ready_readiness(), _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI,
            generated_at=FIXED_TS,
        )
        assert repair.endswith("\n")

    def test_repair_packet_omits_empty_role_sections(self) -> None:
        mr = _readiness_with_blockers(["PENDING_CHECK"], "NOT_READY")
        _, repair = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert "## Supervisor Actions" not in repair
        assert "## Implementer Actions" not in repair
        assert "## CI / Wait Actions" in repair


# ---------------------------------------------------------------------------
# Multiple blockers
# ---------------------------------------------------------------------------


class TestMultipleBlockers:
    def test_multiple_blockers_produce_multiple_actions(self) -> None:
        mr = _readiness_with_blockers(
            ["PR_IS_DRAFT", "PROOF_STALE"], "BLOCKED"
        )
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert len(plan["actions"]) == 2

    def test_action_ids_are_sequential(self) -> None:
        mr = _readiness_with_blockers(
            ["PR_IS_DRAFT", "FAILED_CHECK", "PENDING_CHECK"], "BLOCKED"
        )
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        ids = [a["id"] for a in plan["actions"]]
        assert ids == ["action-0001", "action-0002", "action-0003"]

    def test_schema_validates_multiple_actions(self) -> None:
        mr = _readiness_with_blockers(
            ["PR_IS_DRAFT", "FAILED_CHECK", "PENDING_CHECK"], "BLOCKED"
        )
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        jsonschema.validate(plan, _schema())


# ---------------------------------------------------------------------------
# generated_at passthrough
# ---------------------------------------------------------------------------


class TestGeneratedAt:
    def test_generated_at_passthrough(self) -> None:
        ts = "2025-12-31T23:59:59Z"
        plan, _ = compile(
            _ready_readiness(), _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI,
            generated_at=ts,
        )
        assert plan["generated_at"] == ts

    def test_generated_at_defaults_to_utc_now(self) -> None:
        plan, _ = compile(_ready_readiness(), _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI)
        assert plan["generated_at"].endswith("Z")


# ---------------------------------------------------------------------------
# Unknown blockers and sequential IDs
# ---------------------------------------------------------------------------


class TestUnknownBlockerAndSequentialIds:
    def test_unknown_blocker_is_silently_skipped(self) -> None:
        mr = _readiness_with_blockers(["COMPLETELY_UNKNOWN_BLOCKER"], "BLOCKED")
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"] == []

    def test_ids_stay_sequential_when_unknown_blocker_between_known(self) -> None:
        mr = _readiness_with_blockers(
            ["PR_IS_DRAFT", "COMPLETELY_UNKNOWN_BLOCKER", "FAILED_CHECK"],
            "BLOCKED",
        )
        plan, _ = compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert len(plan["actions"]) == 2
        assert plan["actions"][0]["id"] == "action-0001"
        assert plan["actions"][1]["id"] == "action-0002"

    def test_empty_string_item_id_collapses_to_none(self) -> None:
        mr = _readiness_with_blockers(["REVIEW_ITEM_MUST_FIX"], "NEEDS_IMPLEMENTER")
        ledger = {
            "items": [
                {"id": "", "node_id": "", "blockers": ["REVIEW_ITEM_MUST_FIX"]},
            ]
        }
        plan, _ = compile(mr, ledger, _EMPTY_THREADS, _EMPTY_CI, generated_at=FIXED_TS)
        assert plan["actions"][0]["source_item_id"] is None


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


class TestInputValidation:
    def test_missing_pr_number_raises(self) -> None:
        # Neither nested 'pr' nor flat 'pr_number'/'repo' present — should raise KeyError
        mr = {"readiness": "READY", "blockers": []}
        with pytest.raises(KeyError, match="pr.*nested classifier shape.*flat shape"):
            compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI)

    def test_missing_repo_raises(self) -> None:
        # Neither nested 'pr' nor both flat keys present — should raise KeyError
        mr = {"pr_number": 1, "readiness": "READY", "blockers": []}
        with pytest.raises(KeyError, match="pr.*nested classifier shape.*flat shape"):
            compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI)

    def test_missing_readiness_raises(self) -> None:
        mr = {"pr_number": 1, "repo": "owner/repo", "blockers": []}
        with pytest.raises(KeyError, match="readiness"):
            compile(mr, _EMPTY_LEDGER, _EMPTY_THREADS, _EMPTY_CI)
