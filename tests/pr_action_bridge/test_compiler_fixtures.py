"""Fixture-driven tests for the PR Action Bridge compiler.

Covers the 5 canonical scenarios introduced in TP-DMX-PR-FIXTURES-011:
  - ready_green: no actions produced
  - needs_supervisor_proof_stale: proof-stale supervisor action
  - needs_supervisor_proof_missing: proof-missing supervisor action
  - needs_supervisor_unknown_author: unknown-pr-author supervisor action
  - needs_implementer_failed_check: failed-check implementer action
"""
from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from tools.pr_action_bridge.compiler import compile_action_plan

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "pr_action_bridge"
ACTION_PLAN_SCHEMA_PATH = ROOT / "schemas" / "pr_action_bridge" / "action_plan.schema.json"

FIXED_TS = "2026-01-01T00:00:00Z"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _schema() -> dict:
    return json.loads(ACTION_PLAN_SCHEMA_PATH.read_text(encoding="utf-8"))


def _compile(name: str) -> tuple[dict, str]:
    fx = _load(name)
    return compile_action_plan(
        fx["merge_readiness"],
        fx["review_ledger"],
        fx["thread_dispositions"],
        fx["ci_triage"],
        generated_at=FIXED_TS,
    )


def _validate_schema(plan: dict) -> None:
    schema = _schema()
    jsonschema.Draft7Validator.check_schema(schema)
    errors = sorted(
        jsonschema.Draft7Validator(schema).iter_errors(plan),
        key=lambda e: list(e.path),
    )
    assert errors == [], f"schema errors: {[e.message for e in errors]}"


class TestReadyGreen:
    def test_no_actions_produced(self) -> None:
        plan, _ = _compile("ready_green.json")
        assert plan["actions"] == []

    def test_readiness_is_ready(self) -> None:
        plan, _ = _compile("ready_green.json")
        assert plan["readiness"] == "READY"

    def test_mutation_performed_false(self) -> None:
        plan, _ = _compile("ready_green.json")
        assert plan["mutation_performed"] is False

    def test_repair_packet_says_no_actions(self) -> None:
        _, repair = _compile("ready_green.json")
        assert "No actions required" in repair

    def test_validates_against_schema(self) -> None:
        plan, _ = _compile("ready_green.json")
        _validate_schema(plan)


class TestNeedsSupervisorProofStale:
    def test_produces_one_supervisor_action(self) -> None:
        plan, _ = _compile("needs_supervisor_proof_stale.json")
        assert len(plan["actions"]) == 1
        assert plan["actions"][0]["target_role"] == "supervisor"

    def test_category_is_proof_stale(self) -> None:
        plan, _ = _compile("needs_supervisor_proof_stale.json")
        assert plan["actions"][0]["category"] == "proof-stale"

    def test_source_blocker_is_proof_stale(self) -> None:
        plan, _ = _compile("needs_supervisor_proof_stale.json")
        assert plan["actions"][0]["source_blocker"] == "PROOF_STALE"

    def test_rationale_mentions_stale(self) -> None:
        plan, _ = _compile("needs_supervisor_proof_stale.json")
        assert "stale" in plan["actions"][0]["rationale"].lower()

    def test_rationale_does_not_say_or_missing(self) -> None:
        plan, _ = _compile("needs_supervisor_proof_stale.json")
        assert "or missing" not in plan["actions"][0]["rationale"].lower()

    def test_validates_against_schema(self) -> None:
        plan, _ = _compile("needs_supervisor_proof_stale.json")
        _validate_schema(plan)


class TestNeedsSupervisorProofMissing:
    def test_produces_one_supervisor_action(self) -> None:
        plan, _ = _compile("needs_supervisor_proof_missing.json")
        assert len(plan["actions"]) == 1
        assert plan["actions"][0]["target_role"] == "supervisor"

    def test_category_is_proof_missing(self) -> None:
        plan, _ = _compile("needs_supervisor_proof_missing.json")
        assert plan["actions"][0]["category"] == "proof-missing"

    def test_source_blocker_is_proof_missing(self) -> None:
        plan, _ = _compile("needs_supervisor_proof_missing.json")
        assert plan["actions"][0]["source_blocker"] == "PROOF_MISSING"

    def test_rationale_mentions_missing(self) -> None:
        plan, _ = _compile("needs_supervisor_proof_missing.json")
        assert "missing" in plan["actions"][0]["rationale"].lower()

    def test_validates_against_schema(self) -> None:
        plan, _ = _compile("needs_supervisor_proof_missing.json")
        _validate_schema(plan)


class TestNeedsSupervisorUnknownAuthor:
    def test_produces_one_supervisor_action(self) -> None:
        plan, _ = _compile("needs_supervisor_unknown_author.json")
        assert len(plan["actions"]) == 1
        assert plan["actions"][0]["target_role"] == "supervisor"

    def test_category_is_unknown_pr_author(self) -> None:
        plan, _ = _compile("needs_supervisor_unknown_author.json")
        assert plan["actions"][0]["category"] == "unknown-pr-author"

    def test_source_blocker_is_unknown_pr_author(self) -> None:
        plan, _ = _compile("needs_supervisor_unknown_author.json")
        assert plan["actions"][0]["source_blocker"] == "UNKNOWN_PR_AUTHOR"

    def test_rationale_mentions_known_reviewers(self) -> None:
        plan, _ = _compile("needs_supervisor_unknown_author.json")
        assert "known_reviewers" in plan["actions"][0]["rationale"]

    def test_validates_against_schema(self) -> None:
        plan, _ = _compile("needs_supervisor_unknown_author.json")
        _validate_schema(plan)


class TestNeedsImplementerFailedCheck:
    def test_produces_one_implementer_action(self) -> None:
        plan, _ = _compile("needs_implementer_failed_check.json")
        assert len(plan["actions"]) == 1
        assert plan["actions"][0]["target_role"] == "implementer"

    def test_category_is_failed_check(self) -> None:
        plan, _ = _compile("needs_implementer_failed_check.json")
        assert plan["actions"][0]["category"] == "failed-check"

    def test_source_blocker_is_failed_check(self) -> None:
        plan, _ = _compile("needs_implementer_failed_check.json")
        assert plan["actions"][0]["source_blocker"] == "FAILED_CHECK"

    def test_source_item_id_is_check_name(self) -> None:
        plan, _ = _compile("needs_implementer_failed_check.json")
        assert plan["actions"][0]["source_item_id"] == "unit"

    def test_repair_packet_has_implementer_section(self) -> None:
        _, repair = _compile("needs_implementer_failed_check.json")
        assert "Implementer Actions" in repair

    def test_validates_against_schema(self) -> None:
        plan, _ = _compile("needs_implementer_failed_check.json")
        _validate_schema(plan)
