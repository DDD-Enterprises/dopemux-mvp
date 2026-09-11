"""Tests for project_legacy_embedded_audit() against a real embedded_audit
proof record shape, read from schemas/proof/embedded_audit.schema.json.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft7Validator

from dopemux.governed_execution.audit_identity.legacy import (
    PROVIDER_TABLE,
    project_legacy_embedded_audit,
)

REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = REPO_ROOT / "schemas" / "proof" / "embedded_audit.schema.json"


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _required_fields() -> list[str]:
    return list(_schema()["required"])


def _pass_record() -> dict[str, Any]:
    """A real, schema-valid PASS record built from the field names read out
    of embedded_audit.schema.json.
    """
    return {
        "required": True,
        "status": "PASS",
        "auditor_tool": "agy",
        "auditor_model": "gemini-3.1-pro-high",
        "invocation": "agy review --scope W07",
        "exit_code": 0,
        "report_path": "proof/TP-DMX-GEC-V2-W07-AUDIT-IDENTITY-001/AUDITOR_REPORT.md",
        "findings": [],
        "fixes_applied": [],
        "remaining_risks": [],
        "skip_reason": None,
    }


def _skipped_record() -> dict[str, Any]:
    return {
        "required": False,
        "status": "SKIPPED",
        "auditor_tool": "none",
        "auditor_model": "unknown",
        "invocation": None,
        "exit_code": None,
        "report_path": "proof/TP-EXAMPLE/AUDITOR_REPORT.md",
        "findings": [],
        "fixes_applied": [],
        "remaining_risks": [],
        "skip_reason": "no audit required for this path",
    }


def test_pass_record_matches_required_fields_from_schema() -> None:
    record = _pass_record()
    assert set(_required_fields()) <= set(record)


def test_pass_record_validates_against_embedded_audit_schema() -> None:
    Draft7Validator(_schema()).validate(_pass_record())


def test_skipped_record_validates_against_embedded_audit_schema() -> None:
    Draft7Validator(_schema()).validate(_skipped_record())


def test_project_pass_record_provider_table_exact() -> None:
    record = _pass_record()
    projection = project_legacy_embedded_audit(record)
    identity = projection.identity
    assert identity.runner == "agy"
    assert identity.provider == "google"
    assert identity.requested_model == "gemini-3.1-pro-high"
    assert identity.configured_model == "gemini-3.1-pro-high"
    assert projection.legacy_invocation == "agy review --scope W07"


def test_project_skipped_record_maps_none_provider_and_unknown_model() -> None:
    record = _skipped_record()
    projection = project_legacy_embedded_audit(record)
    identity = projection.identity
    assert identity.runner == "none"
    assert identity.provider == "NONE"
    assert identity.requested_model == "UNKNOWN"
    assert identity.configured_model == "UNKNOWN"
    assert projection.legacy_invocation is None


@pytest.mark.parametrize(
    ("auditor_tool", "expected_provider"),
    [
        ("agy", "google"),
        ("antigravity", "google"),
        ("gemini-cli", "google"),
        ("claude-code-cli", "anthropic"),
        ("copilot-cli", "github"),
        ("grok-cli", "xai"),
        ("opencode-cli", "UNKNOWN"),
        ("pal-mcp-clink", "UNKNOWN"),
        ("none", "NONE"),
    ],
)
def test_provider_table_exact_for_every_closed_key(auditor_tool: str, expected_provider: str) -> None:
    assert PROVIDER_TABLE[auditor_tool] == expected_provider


def test_provider_table_has_exactly_the_closed_keys() -> None:
    assert set(PROVIDER_TABLE) == {
        "agy",
        "antigravity",
        "gemini-cli",
        "claude-code-cli",
        "copilot-cli",
        "grok-cli",
        "opencode-cli",
        "pal-mcp-clink",
        "none",
    }


def test_unknown_auditor_tool_outside_table_yields_unknown_provider() -> None:
    record = _pass_record()
    record["auditor_tool"] = "some-future-auditor-cli"
    projection = project_legacy_embedded_audit(record)
    assert projection.identity.provider == "UNKNOWN"


def test_provider_never_derived_from_model_branding() -> None:
    """A future/unknown auditor_tool with a Google-branded model name must
    still yield provider UNKNOWN -- never inferred from the model string.
    """
    record = _pass_record()
    record["auditor_tool"] = "some-future-auditor-cli"
    record["auditor_model"] = "gemini-9-ultra"
    projection = project_legacy_embedded_audit(record)
    assert projection.identity.provider == "UNKNOWN"


def test_fields_absent_from_legacy_schema_become_unknown() -> None:
    projection = project_legacy_embedded_audit(_pass_record())
    identity = projection.identity
    assert identity.runner_version == "UNKNOWN"
    assert identity.response_claimed_model == "UNKNOWN"
    assert identity.provider_attested_model == "UNKNOWN"
    assert identity.effort_requested == "UNKNOWN"
    assert identity.effort_observed == "UNKNOWN"
    assert identity.auth_profile_ref == "UNKNOWN"
    assert identity.containment == "UNKNOWN"
    assert identity.network_posture == "UNKNOWN"
    assert identity.independence_class == "UNKNOWN"
    assert identity.qualification_receipt == "UNKNOWN"


def test_projected_identity_validates() -> None:
    projection = project_legacy_embedded_audit(_pass_record())
    assert projection.identity.validate() is True


def test_projection_authority_is_none() -> None:
    projection = project_legacy_embedded_audit(_pass_record())
    assert projection.authority == "NONE"


def test_source_record_is_never_modified() -> None:
    record = _pass_record()
    before = copy.deepcopy(record)
    project_legacy_embedded_audit(record)
    assert record == before


def test_source_record_is_never_modified_for_skipped() -> None:
    record = _skipped_record()
    before = copy.deepcopy(record)
    project_legacy_embedded_audit(record)
    assert record == before
