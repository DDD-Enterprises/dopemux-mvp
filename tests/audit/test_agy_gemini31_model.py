"""Regression tests for the exact AGY Gemini 3.1 embedded-audit model id."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft7Validator


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas" / "proof" / "embedded_audit.schema.json"


def _audit(model: str) -> dict:
    return {
        "required": True,
        "status": "PASS_WITH_RISKS",
        "auditor_tool": "agy",
        "auditor_model": model,
        "invocation": (
            "agy --model gemini-3.1-pro-preview --print "
            "'<bounded read-only embedded-audit prompt>'"
        ),
        "exit_code": 0,
        "report_path": "proof/TP-AGY-GEMINI31-TEST/AUDITOR_REPORT.md",
        "findings": [],
        "fixes_applied": [],
        "remaining_risks": ["Preview model availability remains account-dependent."],
        "skip_reason": None,
    }


def _errors(model: str) -> list:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return sorted(Draft7Validator(schema).iter_errors(_audit(model)), key=lambda err: list(err.path))


def test_agy_gemini_31_pro_preview_exact_id_is_approved() -> None:
    assert _errors("gemini-3.1-pro-preview") == []


def test_agy_gemini_31_near_match_remains_rejected() -> None:
    assert _errors("gemini-3.1-pro")


def test_existing_generic_gemini_value_remains_backward_compatible() -> None:
    assert _errors("gemini") == []
