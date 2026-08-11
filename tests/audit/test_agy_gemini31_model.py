"""Regression tests for the exact AGY Gemini 3.1 embedded-audit model id."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "proof" / "embedded_audit.schema.json"

def _audit(model: str, auditor_tool: str = "agy") -> dict:
    return {
        "required": True, "status": "PASS_WITH_RISKS", "auditor_tool": auditor_tool,
        "auditor_model": model, "invocation": f"agy --model {model} --print '<bounded read-only embedded-audit prompt>'",
        "exit_code": 0, "report_path": "proof/TP-AGY-GEMINI31-TEST/AUDITOR_REPORT.md",
        "findings": [], "fixes_applied": [], "remaining_risks": ["High model availability remains account-dependent."],
        "skip_reason": None,
    }

def _errors(model: str, auditor_tool: str = "agy") -> list:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return sorted(Draft7Validator(schema).iter_errors(_audit(model, auditor_tool)), key=lambda err: list(err.path))

def test_agy_gemini_31_pro_high_is_approved() -> None:
    assert _errors("gemini-3.1-pro-high") == []

@pytest.mark.parametrize("auditor_tool", ["claude-code-cli", "gemini-cli", "pal-mcp-clink", "antigravity", "copilot-cli"])
def test_gemini_31_pro_high_rejected_for_wrong_tools(auditor_tool: str) -> None:
    assert _errors("gemini-3.1-pro-high", auditor_tool)

def test_gemini_31_pro_preview_rejected() -> None:
    assert _errors("gemini-3.1-pro-preview")

def test_gemini_31_pro_low_rejected() -> None:
    assert _errors("gemini-3.1-pro-low")

def test_gemini_31_pro_rejected() -> None:
    assert _errors("gemini-3.1-pro")

def test_generic_gemini_backward_compatible() -> None:
    assert _errors("gemini") == []

def test_exact_model_requires_auditor_tool_to_be_present() -> None:
    """The conditional must not pass vacuously when `auditor_tool` is absent.

    JSON Schema `properties` is vacuous for a missing key, so `then.required` makes the
    conditional self-contained rather than relying on the top-level `required` list.
    """
    audit = _audit("gemini-3.1-pro-high")
    del audit["auditor_tool"]
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    messages = [err.message for err in Draft7Validator(schema).iter_errors(audit)]
    assert any("auditor_tool" in message for message in messages)

def test_schema_does_not_constrain_invocation_string() -> None:
    """ACCEPTED_DESIGN_BOUNDARY: the schema binds the declared tool/model pair only.

    `invocation` is an opaque string. A proof that declares the exact model but whose
    invocation never mentions `--model` is still schema-valid, so schema validity must
    never be read as proof that AGY was executed with the exact selector. Runtime
    selector truth comes from execution evidence (recorded invocation, captured AGY
    version/model list, requested/observed selector, fail-closed rejection of an invalid
    selector, and the independent audit) — see docs/ops/embedded-audit-proof.md.

    If this test ever fails, someone added invocation parsing to the schema: update the
    documented boundary deliberately rather than deleting this test.
    """
    audit = _audit("gemini-3.1-pro-high")
    audit["invocation"] = "agy --print '<bounded read-only embedded-audit prompt>'"
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    assert list(Draft7Validator(schema).iter_errors(audit)) == []
