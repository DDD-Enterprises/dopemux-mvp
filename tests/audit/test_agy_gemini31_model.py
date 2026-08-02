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
