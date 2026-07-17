"""TP-0016: provider doc examples validate and stay free of secret material."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

_REPO = Path(__file__).resolve().parents[3]
_DOCS = _REPO / "docs" / "03-reference" / "dcp" / "chatgpt-mcp-readonly"
_SCHEMA = (
    Path(__file__).resolve().parents[1] / "schema" / "connector_policy.schema.json"
)

_SECRET_PATTERNS = [
    # OpenAI-style keys (sk- + long alphanumeric), not words like "task-orchestrator".
    re.compile(r"(?<![A-Za-z])sk-[A-Za-z0-9]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{16,}"),
    re.compile(r"(?i)\b(api[_-]?key|password|secret)\s*[=:]\s*[^\s<]{8,}"),
]

_REQUIRED_DOC_FILES = (
    "PROVIDER_SETUP.md",
    "DISABLE_AND_ROLLBACK.md",
    "PROVIDER_COMMAND_LEDGER.md",
    "SOURCE_DATE_LEDGER.md",
    "CONNECTOR_POLICY_EXAMPLE.yaml",
    "CONNECTOR_POLICY_CONTRACT.md",
)

_REQUIRED_PLACEHOLDERS = (
    "<REPO_ROOT>",
    "<FACADE_PORT>",
    "<EXTERNAL_CONNECTOR_POLICY_PATH>",
    "<OPENAI_TUNNEL_ID>",
)


def _schema() -> dict:
    return json.loads(_SCHEMA.read_text(encoding="utf-8"))


def test_required_provider_docs_exist():
    for name in _REQUIRED_DOC_FILES:
        path = _DOCS / name
        assert path.is_file(), name


def test_connector_policy_example_validates_and_is_disabled():
    doc = yaml.safe_load((_DOCS / "CONNECTOR_POLICY_EXAMPLE.yaml").read_text(encoding="utf-8"))
    assert doc.get("examples_only") is True
    validator = Draft202012Validator(_schema())
    for record in doc["records"]:
        validator.validate(record)
        assert record.get("enabled") is False
        ref = record["credential_ref"]["reference"]
        assert not any(p.search(ref) for p in _SECRET_PATTERNS)


def test_provider_docs_have_no_secret_like_material():
    for name in _REQUIRED_DOC_FILES:
        text = (_DOCS / name).read_text(encoding="utf-8")
        for pattern in _SECRET_PATTERNS:
            assert pattern.search(text) is None, f"{name} matched {pattern.pattern}"


def test_provider_setup_placeholder_completeness():
    text = (_DOCS / "PROVIDER_SETUP.md").read_text(encoding="utf-8")
    for token in _REQUIRED_PLACEHOLDERS:
        assert token in text, token
    # Real-looking private home paths must not appear.
    assert "/Users/" not in text
    assert re.search(r"(?<![A-Za-z])sk-[A-Za-z0-9]{20,}", text) is None


def test_command_ledger_records_local_cli_verification():
    text = (_DOCS / "PROVIDER_COMMAND_LEDGER.md").read_text(encoding="utf-8")
    assert "dopemux mcp start --help" in text
    assert "PASS" in text
    assert "NOT_RUN" in text  # vendor CLIs explicitly not executed
