"""
FA-4-HIGH-1 — _SECRET_ASSIGN_RE \b boundary fails for _SURROUNDED_ env names.

The output_safety._SECRET_ASSIGN_RE regex uses \b word boundaries around
keywords like 'secret', 'password', 'token', 'api_key'. Python's \b does
NOT match adjacent to underscore (because _ is a word char), so any
env-var name where the keyword is surrounded by underscores fails to
match — and the value leaks through redaction.

Documented in:
  rte_audit_findings_FA4_security.md / FA-4-HIGH-1
  rte_audit_findings_FA8_liverun.md / "FA-4-HIGH-1 RUNTIME-CONFIRMED"

The test asserts the BROKEN behavior currently exists (xfail), so when
the regex is fixed, the test passes automatically.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Locate the extractor service
_SERVICE_ROOT = Path(__file__).resolve().parents[3]
if str(_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SERVICE_ROOT))

from output_safety import sanitize_text_for_output  # noqa: E402


# --- Patterns that ARE currently caught (positive regression — must stay green) ---
KNOWN_CAUGHT = [
    ("OpenAI sk- token", "sk-test-1234567890abcdefghij"),
    ("OpenAI sk-proj-", "sk-proj-abcd1234567890ABCDEFGHIJKLMNOP"),
    ("XAI xai-", "xai-FAKEXAITESTKEY1234567890"),
    ("Google AIza", "AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxx"),
    ("GitHub ghp_", "ghp_aAbBcCdDeEfFgGhHiIjJkKlLmMnN1234"),
    ("AWS AKIA", "AKIAIOSFODNN7EXAMPLE"),
    ("Bearer inline", "Authorization: Bearer 1234567890abcdefghijklmnop"),
    ("api_key query param", "https://api.example.com/v1?api_key=secret123"),
    (
        "Private key block",
        "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----",
    ),
    # ASSIGN-style — these work because keyword is on word-boundary
    ("SECRET=value", 'SECRET="hunter2"'),
    ("API_KEY trailing", "API_KEY=foo"),
    ("WEBHOOK_SECRET trailing", "WEBHOOK_SECRET=value"),
]


@pytest.mark.parametrize("label,raw", KNOWN_CAUGHT)
def test_known_secret_patterns_are_redacted(label: str, raw: str) -> None:
    """Positive regression: currently-caught patterns must stay caught."""
    out = sanitize_text_for_output(raw)
    assert "REDACTED" in out, f"{label}: expected REDACTED in {out!r}"


# --- Patterns fixed by FA-4-HIGH-1 ---
# These are env-var-style names where the keyword is surrounded by underscores.
SURROUNDED_LEAKS = [
    "AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    "aws_secret_access_key=abc-leak-value",
    "DATABASE_PASSWORD=hunter2-prod-secret-xyz",
    "INTERNAL_TOKEN=abcdefghij1234567890",
    "CUSTOMER_SECRET_KEY=leaked-value-here",
]


@pytest.mark.parametrize("raw", SURROUNDED_LEAKS)
def test_underscored_env_names_should_be_redacted(raw: str) -> None:
    """FA-4-HIGH-1 regression: underscored env-name secrets must redact."""
    out = sanitize_text_for_output(raw)
    assert "REDACTED" in out, (
        f"Expected redaction of underscored env-name secret: input={raw!r} output={out!r}"
    )
