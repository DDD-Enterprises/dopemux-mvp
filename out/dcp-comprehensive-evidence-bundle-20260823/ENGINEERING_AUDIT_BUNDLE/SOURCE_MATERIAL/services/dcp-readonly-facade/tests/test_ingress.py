"""Authenticated loopback ingress tests (TP-DCP-MCP-RO-0014)."""

from __future__ import annotations

import json
from typing import Any

import pytest
from starlette.testclient import TestClient

from dcp_facade.auth_context import MappingSecretResolver
from dcp_facade.connector_policy import parse_connector_policy_document
from dcp_facade.ingress import AuthIngressMiddleware, build_protected_mcp_placeholder_app
from dcp_facade.ingress_audit import IngressAuditLog
from dcp_facade.loopback_server import NonLoopbackBindError, assert_loopback_host, probe_loopback_bind
from dcp_facade.rate_limit import ConnectorRateLimiter, RateLimitConfig


def _policy(enabled: bool = True, rpm: int = 60, burst: int = 10, concurrent: int = 2) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "connector_id": "chatgpt-dopemux-main",
        "provider": "chatgpt",
        "transport_class": "local_streamable_http",
        "credential_ref": {
            "kind": "environment",
            "reference": "env:DCP_TEST_CONNECTOR_TOKEN",
            "verification_fingerprint": "fp:chatgpt:testdigest01",
            "rotation_group": "dcp-chatgpt",
        },
        "default_target_id": "dopemux-main",
        "allowed_target_ids": ["dopemux-main"],
        "multi_target_authorized": False,
        "allowed_tools": [
            "list_targets",
            "get_target_capabilities",
            "get_target_repo_state_snapshot",
            "list_target_proof_bundles",
            "fetch_target_proof_bundle",
            "get_target_runtime_receipt",
        ],
        "denied_tools": ["mutation-tool-denied"],
        "enabled": enabled,
        "rate_limit": {
            "requests_per_minute": rpm,
            "burst": burst,
            "max_concurrent": concurrent,
            "deny_on_backend_unavailable": True,
        },
        "audit_label": "provider.chatgpt.dopemux-main",
        "created_by": "operator-test",
        "created_at": "2099-01-01T00:00:00Z",
        "expires_at": "2099-02-01T00:00:00Z",
        "last_verified_at": None,
        "source_documentation_date": "2026-07-15",
        "provider_account_class": "business",
        "fail_closed": {
            "unknown_target": "BLOCK",
            "disabled_target": "BLOCK",
            "unauthorized_target": "BLOCK",
            "denied_tool": "BLOCK",
            "expired_credential": "BLOCK",
            "ambiguous_owner": "BLOCK",
            "stale_runtime": "BLOCK",
            "auth_failure": "BLOCK",
            "missing_rate_policy": "BLOCK",
            "provider_drift": "BLOCK",
        },
    }


def _client(
    *,
    token: [REDACTED] = "test-token-alpha",
    rpm: int = 60,
    burst: int = 10,
    concurrent: int = 2,
    enabled: bool = True,
) -> tuple[TestClient, IngressAuditLog]:
    store = parse_connector_policy_document(_policy(enabled=enabled, rpm=rpm, burst=burst, concurrent=concurrent))
    audit = IngressAuditLog()
    app = AuthIngressMiddleware(
        build_protected_mcp_placeholder_app(),
        policy_store=store,
        secret_resolver=MappingSecretResolver(
            {("environment", "env:DCP_TEST_CONNECTOR_TOKEN"): token}
        ),
        audit_log=audit,
        rate_limiter=ConnectorRateLimiter(),
    )
    return TestClient(app), audit


def test_health_is_unauthenticated_and_does_not_list_tools():
    client, audit = _client()
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "tools" not in body
    assert any(ev.decision == "allow_health" for ev in audit.events())


def test_unauthenticated_mcp_discovery_is_denied():
    client, audit = _client()
    response = client.get("/mcp")
    assert response.status_code == 401
    assert response.json()["error"] == "authentication failed"
    assert "tools" not in response.json()
    assert any(ev.decision == "deny_auth" for ev in audit.events())


def test_forged_connector_header_does_not_authenticate():
    client, _ = _client()
    response = client.get(
        "/mcp",
        headers={
            "X-DCP-Connector-Id": "chatgpt-dopemux-main",
            "X-DCP-Connector-Seal": "forged",
        },
    )
    assert response.status_code == 401


def test_authenticated_mcp_discovery_lists_allowed_tools_only():
    client, audit = _client()
    response = client.get("/mcp", headers={"Authorization": "Bearer [REDACTED]"})
    assert response.status_code == 200
    body = response.json()
    assert body["authenticated_connector"] == "chatgpt-dopemux-main"
    names = {entry["name"] for entry in body["tools"]}
    assert "list_targets" in names
    assert "mutation-tool-denied" not in names
    assert any(ev.decision == "allow" for ev in audit.events())
    # Authorization value must not appear in audit dump.
    dump = audit.dump_json_lines()
    assert "test-token-alpha" not in dump
    assert "Bearer [REDACTED]" not in dump


def test_wrong_token_denied_without_reflection():
    client, audit = _client()
    response = client.get("/mcp", headers={"Authorization": "Bearer [REDACTED]"})
    assert response.status_code == 401
    rendered = response.text + audit.dump_json_lines()
    assert "wrong-secret-token" not in rendered


def test_rate_limit_blocks_after_burst():
    client, audit = _client(burst=2, rpm=2, concurrent=2)
    headers = {"Authorization": "Bearer [REDACTED]"}
    assert client.get("/mcp", headers=headers).status_code == 200
    assert client.get("/mcp", headers=headers).status_code == 200
    limited = client.get("/mcp", headers=headers)
    assert limited.status_code == 429
    assert limited.json()["error"] == "rate limit exceeded"
    assert any(ev.decision == "deny_rate" for ev in audit.events())


def test_rate_limiter_unit_concurrency():
    limiter = ConnectorRateLimiter()
    cfg = RateLimitConfig(requests_per_minute=100, burst=10, max_concurrent=1)
    first = limiter.allow("c1", cfg)
    second = limiter.allow("c1", cfg)
    assert first.allowed is True
    assert second.allowed is False
    limiter.release("c1")
    third = limiter.allow("c1", cfg)
    assert third.allowed is True
    limiter.release("c1")


def test_non_loopback_host_rejected():
    with pytest.raises(NonLoopbackBindError):
        assert_loopback_host("0.0.0.0")
    with pytest.raises(NonLoopbackBindError):
        assert_loopback_host("192.168.1.10")


def test_loopback_socket_probe_binds_127():
    host, port = probe_loopback_bind("127.0.0.1", 0)
    assert host in {"127.0.0.1", "0.0.0.0"} or host.startswith("127.")
    # Platform may report 0.0.0.0 for INADDR_ANY when binding 127? On macOS getsockname is 127.0.0.1
    assert port > 0
    assert host == "127.0.0.1"
