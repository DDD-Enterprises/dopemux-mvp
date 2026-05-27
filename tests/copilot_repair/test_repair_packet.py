"""Tests for the Copilot repair packet schema and template.

Governance checks:
- copilot_authority const = "implementer-only"
- mutation_performed const = false
- RepairItem.category restricted to implementer-role only
- RepairItem.id pattern ^repair-[0-9]{4}$
- Template prohibitions present individually
"""
import json
import pathlib
import re

import jsonschema
import pytest

_SCHEMA_PATH = pathlib.Path(__file__).parents[2] / "schemas" / "copilot" / "repair_packet.schema.json"
_TEMPLATE_PATH = pathlib.Path(__file__).parents[2] / "docs" / "03-reference" / "templates" / "copilot" / "pr-repair-packet.md"

_SCHEMA = json.loads(_SCHEMA_PATH.read_text())

_VALIDATOR = jsonschema.Draft202012Validator(_SCHEMA)


def _validate(packet: dict) -> None:
    _VALIDATOR.validate(packet)


def _minimal_valid_packet(**overrides) -> dict:
    base = {
        "schema_version": "1.0.0",
        "generated_at": "2026-05-26T00:00:00Z",
        "pr_number": 42,
        "repo": "acme/widget",
        "copilot_authority": "implementer-only",
        "mutation_performed": False,
        "items": [],
    }
    base.update(overrides)
    return base


def _minimal_valid_item(**overrides) -> dict:
    base = {
        "id": "repair-0001",
        "category": "unresolved-thread",
        "source_blocker": "UNRESOLVED_REVIEW_THREAD",
        "source_item_id": None,
        "rationale": "Review thread is unresolved.",
        "suggested_action": "Address and resolve the thread.",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Schema file integrity
# ---------------------------------------------------------------------------

class TestSchemaFile:
    def test_valid_json(self):
        assert isinstance(_SCHEMA, dict)

    def test_required_properties_present(self):
        required = _SCHEMA.get("required", [])
        for field in ("schema_version", "generated_at", "pr_number", "repo",
                      "copilot_authority", "mutation_performed", "items"):
            assert field in required, f"{field!r} not in required"

    def test_additional_properties_false_top_level(self):
        assert _SCHEMA.get("additionalProperties") is False

    def test_additional_properties_false_repair_item(self):
        item_def = _SCHEMA["$defs"]["RepairItem"]
        assert item_def.get("additionalProperties") is False

    def test_repair_item_required_fields(self):
        required = _SCHEMA["$defs"]["RepairItem"].get("required", [])
        for field in ("id", "category", "source_blocker", "rationale", "suggested_action"):
            assert field in required, f"RepairItem.{field!r} not in required"

    def test_schema_version_const_is_pinned(self):
        assert _SCHEMA["properties"]["schema_version"].get("const") == "1.0.0"

    def test_generated_at_has_pattern(self):
        assert "pattern" in _SCHEMA["properties"]["generated_at"]

    def test_repo_has_pattern(self):
        assert "pattern" in _SCHEMA["properties"]["repo"]


# ---------------------------------------------------------------------------
# Governance pin checks
# ---------------------------------------------------------------------------

class TestSchemaGovernancePins:
    def test_copilot_authority_const(self):
        prop = _SCHEMA["properties"]["copilot_authority"]
        assert prop.get("const") == "implementer-only"

    def test_mutation_performed_const_false(self):
        prop = _SCHEMA["properties"]["mutation_performed"]
        assert prop.get("const") is False

    def test_category_enum_excludes_supervisor_harvest_incomplete(self):
        enum = _SCHEMA["$defs"]["RepairItem"]["properties"]["category"]["enum"]
        assert "harvest-incomplete" not in enum

    def test_category_enum_excludes_supervisor_pr_is_draft(self):
        enum = _SCHEMA["$defs"]["RepairItem"]["properties"]["category"]["enum"]
        assert "pr-is-draft" not in enum

    def test_category_enum_excludes_supervisor_pr_closed(self):
        enum = _SCHEMA["$defs"]["RepairItem"]["properties"]["category"]["enum"]
        assert "pr-closed" not in enum

    def test_category_enum_excludes_supervisor_mixed_sha(self):
        enum = _SCHEMA["$defs"]["RepairItem"]["properties"]["category"]["enum"]
        assert "mixed-sha" not in enum

    def test_category_enum_excludes_supervisor_unknown_reviewer(self):
        enum = _SCHEMA["$defs"]["RepairItem"]["properties"]["category"]["enum"]
        assert "unknown-reviewer" not in enum

    def test_category_enum_excludes_supervisor_proof_stale(self):
        enum = _SCHEMA["$defs"]["RepairItem"]["properties"]["category"]["enum"]
        assert "proof-stale" not in enum

    def test_category_enum_excludes_supervisor_unknown_check(self):
        enum = _SCHEMA["$defs"]["RepairItem"]["properties"]["category"]["enum"]
        assert "unknown-check" not in enum

    def test_category_enum_excludes_supervisor_needs_supervisor(self):
        enum = _SCHEMA["$defs"]["RepairItem"]["properties"]["category"]["enum"]
        assert "needs-supervisor" not in enum

    def test_category_enum_excludes_supervisor_embedded_audit_failed(self):
        enum = _SCHEMA["$defs"]["RepairItem"]["properties"]["category"]["enum"]
        assert "embedded-audit-failed" not in enum

    def test_category_enum_excludes_ci_pending_check(self):
        enum = _SCHEMA["$defs"]["RepairItem"]["properties"]["category"]["enum"]
        assert "pending-check" not in enum

    def test_category_enum_contains_implementer_categories(self):
        enum = _SCHEMA["$defs"]["RepairItem"]["properties"]["category"]["enum"]
        for cat in ("unresolved-thread", "failed-check", "request-changes", "must-fix"):
            assert cat in enum, f"implementer category {cat!r} missing from enum"

    def test_id_pattern_is_repair_prefix(self):
        prop = _SCHEMA["$defs"]["RepairItem"]["properties"]["id"]
        assert prop.get("pattern") == "^repair-[0-9]{4}$"


# ---------------------------------------------------------------------------
# Template file checks
# ---------------------------------------------------------------------------

class TestTemplateFile:
    @pytest.fixture(scope="class")
    def content(self):
        return _TEMPLATE_PATH.read_text()

    def test_file_exists(self):
        assert _TEMPLATE_PATH.exists(), f"Template not found: {_TEMPLATE_PATH}"

    def test_prohibition_must_not_post(self, content):
        lower = content.lower()
        assert "must not post" in lower, "Template must state 'must not post'"

    def test_prohibition_must_not_approve(self, content):
        lower = content.lower()
        assert "must not approve" in lower, "Template must state 'must not approve'"

    def test_prohibition_must_not_merge(self, content):
        lower = content.lower()
        has_merge = "must not merge" in lower or ("must not" in lower and "merge queue" in lower)
        assert has_merge, "Template must state 'must not merge' or 'must not ... merge queue'"

    def test_prohibition_must_not_readiness(self, content):
        lower = content.lower()
        assert "must not" in lower and "readiness" in lower, (
            "Template must state a prohibition involving 'readiness'"
        )

    def test_prohibition_tools_pr_merge(self, content):
        assert "tools/pr_merge" in content, "Template must mention tools/pr_merge prohibition"

    def test_prohibition_supervisor_role(self, content):
        lower = content.lower()
        has_super = "must not act on supervisor" in lower or "supervisor-role" in lower
        assert has_super, "Template must reference prohibition on supervisor-role items"

    def test_prohibition_ci_role(self, content):
        lower = content.lower()
        has_ci = "must not act on ci" in lower or "ci-role" in lower
        assert has_ci, "Template must reference prohibition on ci-role items"

    def test_no_trailing_whitespace(self, content):
        for i, line in enumerate(content.splitlines(), 1):
            assert line == line.rstrip(), f"Trailing whitespace on line {i}: {line!r}"


# ---------------------------------------------------------------------------
# Positive validation
# ---------------------------------------------------------------------------

class TestPacketValidation:
    def test_valid_minimal_packet(self):
        _validate(_minimal_valid_packet())

    def test_valid_packet_with_items(self):
        packet = _minimal_valid_packet(items=[
            _minimal_valid_item(),
            _minimal_valid_item(
                id="repair-0002",
                category="failed-check",
                source_blocker="FAILED_CHECK",
                suggested_action="Fix the failing CI check.",
            ),
        ])
        _validate(packet)

    def test_valid_packet_with_source_action_plan_id(self):
        packet = _minimal_valid_packet(source_action_plan_id="action-plan-abc123")
        _validate(packet)

    def test_valid_packet_source_action_plan_id_null(self):
        packet = _minimal_valid_packet(source_action_plan_id=None)
        _validate(packet)

    def test_valid_all_implementer_categories(self):
        for cat, blocker in [
            ("unresolved-thread", "UNRESOLVED_REVIEW_THREAD"),
            ("failed-check", "FAILED_CHECK"),
            ("request-changes", "REQUEST_CHANGES"),
            ("must-fix", "REVIEW_ITEM_MUST_FIX"),
        ]:
            packet = _minimal_valid_packet(items=[
                _minimal_valid_item(id="repair-0001", category=cat, source_blocker=blocker)
            ])
            _validate(packet)

    def test_valid_repair_item_without_source_item_id(self):
        packet = _minimal_valid_packet(items=[
            {
                "id": "repair-0001",
                "category": "must-fix",
                "source_blocker": "REVIEW_ITEM_MUST_FIX",
                "rationale": "Must fix.",
                "suggested_action": "Fix it.",
            }
        ])
        _validate(packet)


# ---------------------------------------------------------------------------
# Negative validation
# ---------------------------------------------------------------------------

class TestNegativeValidation:
    def _assert_invalid(self, packet: dict) -> None:
        with pytest.raises(jsonschema.ValidationError):
            _validate(packet)

    def test_copilot_authority_supervisor_fails(self):
        self._assert_invalid(_minimal_valid_packet(copilot_authority="supervisor"))

    def test_copilot_authority_empty_fails(self):
        self._assert_invalid(_minimal_valid_packet(copilot_authority=""))

    def test_mutation_performed_true_fails(self):
        self._assert_invalid(_minimal_valid_packet(mutation_performed=True))

    def test_category_supervisor_pr_is_draft_fails(self):
        self._assert_invalid(_minimal_valid_packet(items=[
            _minimal_valid_item(category="pr-is-draft", source_blocker="PR_IS_DRAFT")
        ]))

    def test_category_supervisor_harvest_incomplete_fails(self):
        self._assert_invalid(_minimal_valid_packet(items=[
            _minimal_valid_item(category="harvest-incomplete", source_blocker="HARVEST_INCOMPLETE")
        ]))

    def test_category_supervisor_pr_closed_fails(self):
        self._assert_invalid(_minimal_valid_packet(items=[
            _minimal_valid_item(category="pr-closed", source_blocker="PR_CLOSED")
        ]))

    def test_category_supervisor_embedded_audit_failed_fails(self):
        self._assert_invalid(_minimal_valid_packet(items=[
            _minimal_valid_item(category="embedded-audit-failed", source_blocker="EMBEDDED_AUDIT_FAILED")
        ]))

    def test_category_ci_pending_check_fails(self):
        self._assert_invalid(_minimal_valid_packet(items=[
            _minimal_valid_item(category="pending-check", source_blocker="PENDING_CHECK")
        ]))

    def test_id_wrong_prefix_action_fails(self):
        self._assert_invalid(_minimal_valid_packet(items=[
            _minimal_valid_item(id="action-0001")
        ]))

    def test_id_no_prefix_fails(self):
        self._assert_invalid(_minimal_valid_packet(items=[
            _minimal_valid_item(id="0001")
        ]))

    def test_id_too_few_digits_fails(self):
        self._assert_invalid(_minimal_valid_packet(items=[
            _minimal_valid_item(id="repair-001")
        ]))

    def test_extra_top_level_field_fails(self):
        packet = _minimal_valid_packet()
        packet["extra_field"] = "not allowed"
        self._assert_invalid(packet)

    def test_extra_repair_item_field_fails(self):
        item = _minimal_valid_item()
        item["extra_field"] = "not allowed"
        self._assert_invalid(_minimal_valid_packet(items=[item]))

    def test_missing_pr_number_fails(self):
        packet = _minimal_valid_packet()
        del packet["pr_number"]
        self._assert_invalid(packet)

    def test_missing_repo_fails(self):
        packet = _minimal_valid_packet()
        del packet["repo"]
        self._assert_invalid(packet)

    def test_missing_copilot_authority_fails(self):
        packet = _minimal_valid_packet()
        del packet["copilot_authority"]
        self._assert_invalid(packet)

    def test_pr_number_zero_fails(self):
        self._assert_invalid(_minimal_valid_packet(pr_number=0))

    def test_pr_number_string_fails(self):
        self._assert_invalid(_minimal_valid_packet(pr_number="42"))

    def test_missing_rationale_fails(self):
        item = _minimal_valid_item()
        del item["rationale"]
        self._assert_invalid(_minimal_valid_packet(items=[item]))

    def test_missing_suggested_action_fails(self):
        item = _minimal_valid_item()
        del item["suggested_action"]
        self._assert_invalid(_minimal_valid_packet(items=[item]))

    def test_generated_at_non_iso_fails(self):
        self._assert_invalid(_minimal_valid_packet(generated_at="banana"))

    def test_generated_at_date_only_fails(self):
        self._assert_invalid(_minimal_valid_packet(generated_at="2026-05-26"))

    def test_generated_at_with_offset_fails(self):
        self._assert_invalid(_minimal_valid_packet(generated_at="2026-05-26T00:00:00+00:00"))

    def test_repo_no_slash_fails(self):
        self._assert_invalid(_minimal_valid_packet(repo="noslash"))

    def test_repo_empty_fails(self):
        self._assert_invalid(_minimal_valid_packet(repo=""))

    def test_source_action_plan_id_empty_string_fails(self):
        self._assert_invalid(_minimal_valid_packet(source_action_plan_id=""))

    def test_source_item_id_empty_string_fails(self):
        self._assert_invalid(_minimal_valid_packet(items=[
            _minimal_valid_item(source_item_id="")
        ]))
