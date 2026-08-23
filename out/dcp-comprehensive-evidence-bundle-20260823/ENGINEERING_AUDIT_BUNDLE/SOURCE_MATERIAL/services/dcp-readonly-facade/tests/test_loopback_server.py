"""Loopback server start/stop/health lifecycle tests (TP-0014)."""

from __future__ import annotations

import httpx

from dcp_facade.auth_context import MappingSecretResolver
from dcp_facade.connector_policy import parse_connector_policy_document
from dcp_facade.loopback_server import LoopbackIngressServer, NonLoopbackBindError, assert_loopback_host


def _store():
    return parse_connector_policy_document(
        {
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
            "allowed_tools": ["list_targets", "get_target_capabilities"],
            "denied_tools": [],
            "enabled": True,
            "rate_limit": {
                "requests_per_minute": 60,
                "burst": 10,
                "max_concurrent": 2,
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
    )


def test_server_start_stop_health_and_auth_gate():
    server = LoopbackIngressServer(
        policy_store=_store(),
        secret_resolver=MappingSecretResolver(
            {("environment", "env:DCP_TEST_CONNECTOR_TOKEN"): "live-token"}
        ),
        host="127.0.0.1",
        port=0,
    )
    health = server.start()
    assert health.running is True
    assert health.host == "127.0.0.1"
    assert health.port is not None and health.port > 0
    assert health.auth_required is True
    base = server.bound_url
    assert base is not None

    with httpx.Client(timeout=2.0) as client:
        health_resp = client.get(f"{base}/health")
        assert health_resp.status_code == 200
        denied = client.get(f"{base}/mcp")
        assert denied.status_code == 401
        allowed = client.get(f"{base}/mcp", headers={"Authorization": "Bearer live-token"})
        assert allowed.status_code == 200
        assert allowed.json()["authenticated_connector"] == "chatgpt-dopemux-main"

    stopped = server.stop()
    assert stopped.running is False
    assert server.bound_url is None


def test_constructor_rejects_public_bind():
    try:
        LoopbackIngressServer(host="0.0.0.0", port=0)
        assert False, "expected NonLoopbackBindError"
    except NonLoopbackBindError:
        pass
    assert assert_loopback_host("127.0.0.1") == "127.0.0.1"
