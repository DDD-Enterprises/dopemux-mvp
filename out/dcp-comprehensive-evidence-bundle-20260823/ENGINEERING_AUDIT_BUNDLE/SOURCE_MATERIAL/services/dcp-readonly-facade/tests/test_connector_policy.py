"""Connector policy schema/loader tests (TP-DCP-MCP-RO-0013)."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest
import yaml
from jsonschema import Draft202012Validator

from dcp_facade import connector_policy as CP

_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema" / "connector_policy.schema.json"
_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "connector_policy"
_DOC_EXAMPLE = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "03-reference"
    / "dcp"
    / "chatgpt-mcp-readonly"
    / "CONNECTOR_POLICY_EXAMPLE.yaml"
)


def _schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


def _load(name: str):
    return yaml.safe_load((_FIXTURES / name).read_text(encoding="utf-8"))


def test_schema_is_self_valid():
    Draft202012Validator.check_schema(_schema())


def test_schema_accepts_valid_fixture():
    Draft202012Validator(_schema()).validate(_load("valid_enabled.yaml"))


def test_doc_example_records_validate():
    doc = yaml.safe_load(_DOC_EXAMPLE.read_text(encoding="utf-8"))
    validator = Draft202012Validator(_schema())
    assert doc.get("examples_only") is True
    for record in doc["records"]:
        validator.validate(record)


def test_loader_accepts_valid_record():
    store = CP.parse_connector_policy_document(_load("valid_enabled.yaml"))
    assert "chatgpt-dopemux-main" in store.policies
    policy = store.get("chatgpt-dopemux-main")
    assert policy is not None
    assert policy.enabled is True
    assert policy.default_target_id == "dopemux-main"
    assert "list_targets" in policy.allowed_tools


def test_loader_rejects_secret_like_credential_reference():
    raw = _load("valid_enabled.yaml")
    raw["credential_ref"]["reference"] = "[CREDENTIAL_SHAPED_VALUE_REDACTED]"
    store = CP.parse_connector_policy_document(raw)
    assert store.policies == {}
    assert any(
        "secret material" in warning or "locator" in warning or "env:VAR" in warning
        for warning in store.warnings
    )


def test_loader_rejects_bare_short_password_as_reference():
    raw = _load("valid_enabled.yaml")
    raw["credential_ref"]["reference"] = "ShortPassw0rd!!!!"
    store = CP.parse_connector_policy_document(raw)
    assert store.policies == {}


def test_loader_rejects_default_target_not_in_allowlist():
    raw = _load("valid_enabled.yaml")
    raw["default_target_id"] = "other-target"
    store = CP.parse_connector_policy_document(raw)
    assert store.policies == {}
    assert any("default_target_id" in warning for warning in store.warnings)


def test_loader_rejects_non_block_fail_closed():
    raw = _load("valid_enabled.yaml")
    raw["fail_closed"]["auth_failure"] = "ALLOW"
    store = CP.parse_connector_policy_document(raw)
    assert store.policies == {}


def test_multi_record_store_loads_independent_identities():
    store = CP.parse_connector_policy_document(_load("multi_record_store.yaml"))
    assert set(store.policies) == {"chatgpt-dopemux-main", "grok-feature-review-a7"}
    assert store.get("chatgpt-dopemux-main").provider == "chatgpt"
    assert store.get("grok-feature-review-a7").provider == "grok"


def test_duplicate_connector_id_drops_ambiguous_identity():
    raw = _load("multi_record_store.yaml")
    duplicate = deepcopy(raw["records"][0])
    duplicate["audit_label"] = "provider.chatgpt.duplicate"
    raw["records"].append(duplicate)
    store = CP.parse_connector_policy_document(raw)
    assert "chatgpt-dopemux-main" not in store.policies
    assert "grok-feature-review-a7" in store.policies
    assert any("duplicate connector_id" in warning for warning in store.warnings)


def test_public_receipt_has_no_raw_secret_material():
    store = CP.parse_connector_policy_document(_load("valid_enabled.yaml"))
    policy = store.get("chatgpt-dopemux-main")
    assert policy is not None
    receipt = CP.public_policy_receipt(policy)
    rendered = repr(receipt)
    assert "sk-" not in rendered
    assert receipt["credential_reference"] == "env:DCP_TEST_CONNECTOR_TOKEN"
    assert receipt["credential_fingerprint"].startswith("fp:")


def test_expired_helper():
    store = CP.parse_connector_policy_document(_load("expired.yaml"))
    policy = store.get("chatgpt-expired")
    assert policy is not None
    assert policy.is_expired() is True
