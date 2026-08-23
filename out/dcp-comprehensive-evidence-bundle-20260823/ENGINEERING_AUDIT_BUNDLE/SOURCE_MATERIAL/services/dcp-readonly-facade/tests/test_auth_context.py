"""Provider-neutral auth context tests (TP-DCP-MCP-RO-0013)."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

from dcp_facade import auth_context as AUTH
from dcp_facade import connector_policy as CP

_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "connector_policy"


def _store(name: str) -> CP.ConnectorPolicyStore:
    raw = yaml.safe_load((_FIXTURES / name).read_text(encoding="utf-8"))
    return CP.parse_connector_policy_document(raw)


def _resolver(token: [REDACTED] = "test-token-alpha", ref: str = "env:DCP_TEST_CONNECTOR_TOKEN"):
    return AUTH.MappingSecretResolver({("environment", ref): token})


def test_authenticate_bearer_success():
    store = _store("valid_enabled.yaml")
    context, decision = AUTH.authenticate_bearer(
        store,
        authorization_header="Bearer [REDACTED]",
        secret_resolver=_resolver(),
    )
    assert decision.allowed is True
    assert context is not None
    assert context.connector_id == "chatgpt-dopemux-main"
    assert "test-token-alpha" not in repr(context)
    assert AUTH.verify_context_seal(context) is True


def test_missing_token_is_generic_failure():
    store = _store("valid_enabled.yaml")
    context, decision = AUTH.authenticate_bearer(store, authorization_header=None)
    assert context is None
    assert decision.allowed is False
    assert decision.reason == AUTH.GENERIC_AUTH_FAILURE
    assert decision.connector_id is None


def test_wrong_token_is_generic_failure():
    store = _store("valid_enabled.yaml")
    context, decision = AUTH.authenticate_bearer(
        store,
        authorization_header="Bearer wrong-token",
        secret_resolver=_resolver(),
    )
    assert context is None
    assert decision.allowed is False
    assert decision.reason == AUTH.GENERIC_AUTH_FAILURE
    assert "wrong-token" not in repr(decision)


def test_disabled_connector_fails_closed(monkeypatch):
    store = _store("disabled.yaml")
    resolver = AUTH.MappingSecretResolver(
        {("environment", "env:DCP_TEST_DISABLED_TOKEN"): "disabled-token"}
    )
    context, decision = AUTH.authenticate_bearer(
        store,
        presented_token="disabled-token",
        secret_resolver=resolver,
    )
    assert context is None
    assert decision.allowed is False
    assert decision.reason == AUTH.GENERIC_AUTH_FAILURE


def test_expired_connector_fails_closed():
    store = _store("expired.yaml")
    resolver = AUTH.MappingSecretResolver(
        {("environment", "env:DCP_TEST_EXPIRED_TOKEN"): "expired-token"}
    )
    context, decision = AUTH.authenticate_bearer(
        store,
        presented_token="expired-token",
        secret_resolver=resolver,
        now=datetime(2021, 1, 1, tzinfo=timezone.utc),
    )
    assert context is None
    assert decision.allowed is False
    assert decision.reason == AUTH.GENERIC_AUTH_FAILURE


def test_missing_credential_resolution_fails_closed():
    store = _store("valid_enabled.yaml")
    # Default env resolver has no token set.
    context, decision = AUTH.authenticate_bearer(
        store,
        authorization_header="Bearer [REDACTED]",
    )
    assert context is None
    assert decision.allowed is False


def test_target_and_tool_authorization_matrix():
    store = _store("valid_enabled.yaml")
    context, decision = AUTH.authenticate_bearer(
        store,
        presented_token="test-token-alpha",
        secret_resolver=_resolver(),
    )
    assert decision.allowed and context is not None

    ok_target = AUTH.authorize_target(context, "dopemux-main")
    deny_target = AUTH.authorize_target(context, "other-target")
    ok_tool = AUTH.authorize_tool(context, "list_targets")
    deny_tool = AUTH.authorize_tool(context, "mutation-tool-denied")
    unknown_tool = AUTH.authorize_tool(context, "not-a-tool")

    assert ok_target.allowed is True
    assert deny_target.allowed is False and deny_target.reason == AUTH.GENERIC_TARGET_DENY
    assert ok_tool.allowed is True
    assert deny_tool.allowed is False and deny_tool.reason == AUTH.GENERIC_TOOL_DENY
    assert unknown_tool.allowed is False


def test_forged_context_cannot_authorize():
    forged = AUTH.forge_context_attempt(
        connector_id="chatgpt-dopemux-main",
        allowed_target_ids=("dopemux-main",),
        allowed_tools=("list_targets",),
        seal="not-a-real-seal",
    )
    assert AUTH.verify_context_seal(forged) is False
    assert AUTH.authorize_target(forged, "dopemux-main").allowed is False
    assert AUTH.authorize_tool(forged, "list_targets").allowed is False


def test_untrusted_headers_never_authenticate():
    decision = AUTH.context_from_untrusted_headers(
        {
            "X-DCP-Connector-Id": "chatgpt-dopemux-main",
            "X-DCP-Connector-Seal": "anything",
            "Authorization": "Bearer [REDACTED]",
        }
    )
    assert decision.allowed is False
    assert decision.reason == AUTH.GENERIC_AUTH_FAILURE


def test_header_redaction_strips_connector_claims_and_bearer():
    cleaned, redactions = AUTH.strip_untrusted_connector_headers(
        {
            "X-DCP-Connector-Id": "chatgpt-dopemux-main",
            "Authorization": "Bearer [REDACTED]",
            "Accept": "application/json",
        }
    )
    assert "X-DCP-Connector-Id" not in cleaned
    assert cleaned["Authorization"] == "Bearer <redacted>"
    assert cleaned["Accept"] == "application/json"
    assert "super-secret-token-value" not in repr(cleaned)
    assert any(item.startswith("stripped:") for item in redactions)
    assert "secrets" in redactions


def test_credential_rotation_revokes_old_token():
    store = _store("valid_enabled.yaml")
    old = AUTH.MappingSecretResolver(
        {("environment", "env:DCP_TEST_CONNECTOR_TOKEN"): "token-v1"}
    )
    new = AUTH.MappingSecretResolver(
        {("environment", "env:DCP_TEST_CONNECTOR_TOKEN"): "token-v2"}
    )

    ctx_old, decision_old = AUTH.authenticate_bearer(
        store, presented_token="token-v1", secret_resolver=old
    )
    assert decision_old.allowed and ctx_old is not None

    # After rotation, old token no longer resolves.
    ctx_stale, decision_stale = AUTH.authenticate_bearer(
        store, presented_token="token-v1", secret_resolver=new
    )
    assert ctx_stale is None and decision_stale.allowed is False

    ctx_new, decision_new = AUTH.authenticate_bearer(
        store, presented_token="token-v2", secret_resolver=new
    )
    assert decision_new.allowed and ctx_new is not None
    # Identity remains independently revocable by connector_id; fingerprint stable.
    assert ctx_new.connector_id == ctx_old.connector_id
    assert ctx_new.credential_fingerprint == ctx_old.credential_fingerprint


def test_independent_connectors_do_not_cross_authorize():
    store = _store("multi_record_store.yaml")
    resolver = AUTH.MappingSecretResolver(
        {
            ("environment", "env:DCP_TEST_CONNECTOR_TOKEN"): "chatgpt-token",
            ("environment", "env:DCP_TEST_GROK_TOKEN"): "grok-token",
        }
    )
    chatgpt, d1 = AUTH.authenticate_bearer(
        store, presented_token="chatgpt-token", secret_resolver=resolver
    )
    grok, d2 = AUTH.authenticate_bearer(
        store, presented_token="grok-token", secret_resolver=resolver
    )
    assert d1.allowed and d2.allowed
    assert chatgpt is not None and grok is not None
    assert AUTH.authorize_target(chatgpt, "feature-review-a7").allowed is False
    assert AUTH.authorize_target(grok, "dopemux-main").allowed is False
    assert AUTH.authorize_target(chatgpt, "dopemux-main").allowed is True
    assert AUTH.authorize_target(grok, "feature-review-a7").allowed is True


def test_resolve_request_target_default():
    store = _store("valid_enabled.yaml")
    context, _ = AUTH.authenticate_bearer(
        store, presented_token="test-token-alpha", secret_resolver=_resolver()
    )
    assert context is not None
    target, decision = AUTH.resolve_request_target(context, None)
    assert decision.allowed is True
    assert target == "dopemux-main"
