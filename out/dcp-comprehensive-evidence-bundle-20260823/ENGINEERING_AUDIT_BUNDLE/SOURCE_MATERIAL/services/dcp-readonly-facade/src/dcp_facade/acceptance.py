"""Acceptance harness for TP-DCP-MCP-RO-0017.

Default mode is **deterministic-only**. Live/provider/tunnel gates remain
NOT_RUN unless every live consent env is set. A skipped live gate is never PASS.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .auth_context import MappingSecretResolver, authenticate_bearer, authorize_target, authorize_tool
from .connector_policy import parse_connector_policy_document
from .ownership import OwnershipEvidence, verify_ownership
from .rate_limit import ConnectorRateLimiter, RateLimitConfig
from .route_manifest import RELEASE_ONE_DENIED_OPERATIONS, is_release_one_operation
from .safe_adapters import deny_blocked_operation

LIVE_CONSENT_ENV = "DCP_ACCEPTANCE_LIVE"
LIVE_TOKEN_ENV = "DCP_ACCEPTANCE_LIVE_TOKEN"  # must be set for live; never committed
LIVE_PROVIDER_ENV = "DCP_ACCEPTANCE_LIVE_PROVIDERS"  # e.g. none|local|chatgpt,grok

VENDOR_PROVIDERS = frozenset({"chatgpt", "grok", "gemini", "gemini_api", "gemini_deep_research"})
LOCAL_PROVIDERS = frozenset({"local", "loopback", "local_loopback"})


@dataclass
class GateResult:
    test_id: str
    status: str  # PASS | FAIL | NOT_RUN | BLOCKED
    gate_type: str  # deterministic | live
    blocking: bool
    detail: str
    evidence: dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> dict[str, Any]:
        return asdict(self)


def parse_live_providers() -> list[str]:
    raw = os.getenv(LIVE_PROVIDER_ENV, "").strip()
    if not raw or raw.lower() == "none":
        return []
    return [part.strip().lower() for part in raw.split(",") if part.strip()]


def live_mode_authorized() -> tuple[bool, str]:
    """Live gates require explicit dual consent; credentials are never defaulted."""
    if os.getenv(LIVE_CONSENT_ENV, "").strip() != "1":
        return False, f"{LIVE_CONSENT_ENV}!=1 (live gates not authorized)"
    token: [REDACTED], "").strip()
    if not token: [REDACTED] False, f"{LIVE_TOKEN_ENV} unset (no live credential authorized)"
    # Token must not look empty-placeholder; actual value never returned.
    if token.startswith("<") and token.endswith(">"):
        return False, f"{LIVE_TOKEN_ENV} is still a placeholder"
    providers = parse_live_providers()
    if not providers:
        return False, f"{LIVE_PROVIDER_ENV} unset or none"
    return True, "live consent env present (value not disclosed)"


def _pass(test_id: str, gate_type: str, detail: str, **evidence: Any) -> GateResult:
    return GateResult(test_id, "PASS", gate_type, True, detail, evidence)


def _fail(test_id: str, gate_type: str, detail: str, **evidence: Any) -> GateResult:
    return GateResult(test_id, "FAIL", gate_type, True, detail, evidence)


def _not_run(test_id: str, gate_type: str, detail: str, **evidence: Any) -> GateResult:
    return GateResult(test_id, "NOT_RUN", gate_type, True, detail, evidence)


def run_deterministic_gates() -> list[GateResult]:
    """Execute hermetic acceptance checks using pure modules (no network)."""
    results: list[GateResult] = []

    # ACC-001 / ACC-014 style: unauthorized tool and progress blocked
    if not is_release_one_operation("conport", "get_progress"):
        results.append(
            _pass(
                "DCP-ACC-014",
                "deterministic",
                "get_progress not in release-one allowlist",
            )
        )
    else:
        results.append(_fail("DCP-ACC-014", "deterministic", "get_progress unexpectedly allowed"))

    denied = deny_blocked_operation("get_progress", "conport")
    if denied.allowed is False:
        results.append(
            _pass("DCP-ACC-016", "deterministic", "progress side-effect path denied without adapter call")
        )
    else:
        results.append(_fail("DCP-ACC-016", "deterministic", "progress was allowed"))

    for op in RELEASE_ONE_DENIED_OPERATIONS:
        if is_release_one_operation("conport", op) or is_release_one_operation("dope_memory", op):
            results.append(
                _fail("DCP-ACC-015", "deterministic", f"denied op listed as release-one: {op}")
            )
            break
    else:
        results.append(
            _pass(
                "DCP-ACC-015",
                "deterministic",
                "release-one allowlist excludes mutation-shaped denied ops",
            )
        )

    # ACC-013 connector target authz
    policy = {
        "schema_version": "1.0.0",
        "connector_id": "chatgpt-dopemux-main",
        "provider": "chatgpt",
        "transport_class": "local_streamable_http",
        "credential_ref": {
            "kind": "environment",
            "reference": "env:DCP_TEST_CONNECTOR_TOKEN",
            "verification_fingerprint": "fp:chatgpt:acc013",
            "rotation_group": "dcp-chatgpt",
        },
        "default_target_id": "dopemux-main",
        "allowed_target_ids": ["dopemux-main"],
        "multi_target_authorized": False,
        "allowed_tools": ["list_targets", "get_target_capabilities"],
        "denied_tools": ["mutation-tool-denied"],
        "enabled": True,
        "rate_limit": {
            "requests_per_minute": 30,
            "burst": 5,
            "max_concurrent": 2,
            "deny_on_backend_unavailable": True,
        },
        "audit_label": "provider.chatgpt.dopemux-main",
        "created_by": "acceptance",
        "created_at": "2099-01-01T00:00:00Z",
        "expires_at": "2099-02-01T00:00:00Z",
        "last_verified_at": None,
        "source_documentation_date": "2026-07-16",
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
    store = parse_connector_policy_document(policy)
    resolver = MappingSecretResolver(
        {("environment", "env:DCP_TEST_CONNECTOR_TOKEN"): "acc-token-alpha"}
    )
    ctx, decision = authenticate_bearer(
        store, presented_token="acc-token-alpha", secret_resolver=resolver
    )
    if not decision.allowed or ctx is None:
        results.append(_fail("DCP-ACC-013", "deterministic", "auth failed for fixture connector"))
    else:
        ok = authorize_target(ctx, "dopemux-main")
        bad = authorize_target(ctx, "feature-review-a7")
        invented = authorize_target(ctx, "invented-target")
        tool_ok = authorize_tool(ctx, "list_targets")
        tool_deny = authorize_tool(ctx, "mutation-tool-denied")
        if (
            ok.allowed
            and not bad.allowed
            and not invented.allowed
            and tool_ok.allowed
            and not tool_deny.allowed
        ):
            results.append(
                _pass(
                    "DCP-ACC-013",
                    "deterministic",
                    "connector allows only authorized target/tool; others blocked",
                )
            )
        else:
            results.append(_fail("DCP-ACC-013", "deterministic", "authz matrix unexpected"))

    # ACC-001 unknown target (opaque unknown blocked by authorize_target)
    if ctx is not None:
        unknown = authorize_target(ctx, "unknown-opaque-id")
        if not unknown.allowed and unknown.reason:
            results.append(
                _pass(
                    "DCP-ACC-001",
                    "deterministic",
                    "unknown target blocked with generic reason",
                    public_reason=unknown.reason,
                )
            )
        else:
            results.append(_fail("DCP-ACC-001", "deterministic", "unknown target not blocked"))

    # ACC-006 / 008 / 010 ownership port-only and wrong project / ambiguous
    port_only = verify_ownership(
        OwnershipEvidence(
            family="conport",
            expected_project_id="proj-a",
            expected_project_root="/tmp/a",
            expected_worktree_root="/tmp/a/wt",
            has_listening_port=True,
            candidate_count=1,
        )
    )
    if not port_only.verified and (
        "port_only" in port_only.evidence_codes or "unlabeled" in port_only.evidence_codes
    ):
        results.append(
            _pass("DCP-ACC-006", "deterministic", "port-only ownership rejected without labels/identity")
        )
    else:
        results.append(_fail("DCP-ACC-006", "deterministic", "port-only unexpectedly verified"))

    wrong = verify_ownership(
        OwnershipEvidence(
            family="conport",
            expected_project_id="proj-a",
            expected_project_root="/tmp/a",
            expected_worktree_root="/tmp/a/wt",
            runtime_project_id="other",
            runtime_project_root="/tmp/a",
            runtime_worktree_root="/tmp/a/wt",
            labels={
                "dopemux.project_id": "proj-a",
                "dopemux.service": "conport",
                "dopemux.worktree_root": "/tmp/a/wt",
            },
            mounts=("/tmp/a/wt",),
            protocol_ok=True,
            candidate_count=1,
        )
    )
    if not wrong.verified:
        results.append(_pass("DCP-ACC-009", "deterministic", "wrong project identity blocked"))
    else:
        results.append(_fail("DCP-ACC-009", "deterministic", "wrong project verified"))

    ambiguous = verify_ownership(
        OwnershipEvidence(
            family="conport",
            expected_project_id="proj-a",
            expected_project_root="/tmp/a",
            expected_worktree_root="/tmp/a/wt",
            candidate_count=2,
            protocol_ok=True,
            labels={
                "dopemux.project_id": "proj-a",
                "dopemux.service": "conport",
                "dopemux.worktree_root": "/tmp/a/wt",
            },
        )
    )
    if not ambiguous.verified and "ambiguous" in ambiguous.evidence_codes:
        results.append(_pass("DCP-ACC-010", "deterministic", "ambiguous candidates blocked"))
    else:
        results.append(_fail("DCP-ACC-010", "deterministic", "ambiguous not blocked"))

    stale = verify_ownership(
        OwnershipEvidence(
            family="conport",
            expected_project_id="proj-a",
            expected_project_root="/tmp/a",
            expected_worktree_root="/tmp/a/wt",
            candidate_count=1,
            stale=True,
            protocol_ok=True,
            labels={
                "dopemux.project_id": "proj-a",
                "dopemux.service": "conport",
                "dopemux.worktree_root": "/tmp/a/wt",
            },
        )
    )
    if not stale.verified:
        results.append(_pass("DCP-ACC-008", "deterministic", "stale candidate blocked"))
    else:
        results.append(_fail("DCP-ACC-008", "deterministic", "stale verified"))

    # ACC-022 rate limits
    limiter = ConnectorRateLimiter()
    cfg = RateLimitConfig(requests_per_minute=2, burst=2, max_concurrent=1)
    a = limiter.allow("c", cfg)
    b = limiter.allow("c", cfg)  # concurrent
    if a.allowed and not b.allowed:
        results.append(_pass("DCP-ACC-022", "deterministic", "concurrency limit enforced"))
    else:
        results.append(_fail("DCP-ACC-022", "deterministic", "concurrency limit not enforced"))
    limiter.release("c")

    # ACC-017 prompt remains data — policy table unchanged after "ignore policy" style input
    # (no policy mutation API exists; ensure denied op still denied)
    inj = deny_blocked_operation("memory_store", "dope_memory")
    if inj.allowed is False:
        results.append(
            _pass(
                "DCP-ACC-017",
                "deterministic",
                "no policy mutation path; denied op stays denied under injection-style names",
            )
        )
    else:
        results.append(_fail("DCP-ACC-017", "deterministic", "mutation op allowed"))

    # ACC-012 blocked family not release-one
    if not is_release_one_operation("dope_context", "search_code_docs"):
        results.append(
            _pass("DCP-ACC-012", "deterministic", "dope_context not in release-one operations")
        )
    else:
        results.append(_fail("DCP-ACC-012", "deterministic", "dope_context unexpectedly release-one"))

    return results


def _fixture_policy(connector_id: str, token_env: str, targets: list[str], rpm: int = 30, burst: int = 5) -> dict[str, Any]:
    return {
        "schema_version": "1.0.0",
        "connector_id": connector_id,
        "provider": "chatgpt",
        "transport_class": "local_streamable_http",
        "credential_ref": {
            "kind": "environment",
            "reference": f"env:{token_env}",
            "verification_fingerprint": f"fp:{connector_id}:live",
            "rotation_group": "dcp-live-acc",
        },
        "default_target_id": targets[0],
        "allowed_target_ids": targets,
        "multi_target_authorized": len(targets) > 1,
        "allowed_tools": [
            "list_targets",
            "get_target_capabilities",
            "list_decisions",
            "get_decision",
        ],
        "denied_tools": ["mutation-tool-denied", "get_progress"],
        "enabled": True,
        "rate_limit": {
            "requests_per_minute": rpm,
            "burst": burst,
            "max_concurrent": 2,
            "deny_on_backend_unavailable": True,
        },
        "audit_label": f"live.{connector_id}",
        "created_by": "acceptance-live",
        "created_at": "2099-01-01T00:00:00Z",
        "expires_at": "2099-02-01T00:00:00Z",
        "last_verified_at": None,
        "source_documentation_date": "2026-07-16",
        "provider_account_class": "local_operator",
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


def run_local_loopback_live_gates(token: [REDACTED] -> list[GateResult]:
    """Bounded local-live gates against loopback ingress with synthetic tokens.

    No public tunnels, no vendor APIs. Uses ephemeral 127.0.0.1 bind only.
    """
    import httpx

    from .loopback_server import LoopbackIngressServer

    results: list[GateResult] = []
    env_name = "DCP_ACCEPTANCE_LIVE_TOKEN"
    # Use MappingSecretResolver so the token need not be exported under a fixed
    # env name inside the server process beyond what the operator already set.
    store = parse_connector_policy_document(
        {
            "records": [
                _fixture_policy("chatgpt-dopemux-main", env_name, ["dopemux-main"], rpm=20, burst=2),
                _fixture_policy("grok-feature-review-a7", "DCP_ACCEPTANCE_LIVE_TOKEN_B", ["feature-review-a7"]),
            ]
        }
    )
    # Second connector uses a different synthetic secret for isolation tests.
    token_b = token + "-b"
    resolver = MappingSecretResolver(
        {
            ("environment", f"env:{env_name}"): token,
            ("environment", "env:DCP_ACCEPTANCE_LIVE_TOKEN_B"): token_b,
        }
    )
    server = LoopbackIngressServer(
        policy_store=store,
        secret_resolver=resolver,
        host="127.0.0.1",
        port=0,
    )
    try:
        health = server.start()
        if not health.running or health.host != "127.0.0.1" or not health.port:
            results.append(_fail("DCP-ACC-028", "live", "loopback ingress failed to start on 127.0.0.1"))
            return results
        base = server.bound_url
        assert base is not None

        with httpx.Client(timeout=3.0) as client:
            # Health unauthenticated
            h = client.get(f"{base}/health")
            if h.status_code != 200 or "tools" in h.json():
                results.append(_fail("DCP-ACC-015", "live", "health missing or leaked tools"))
            else:
                results.append(
                    _pass(
                        "DCP-ACC-015",
                        "live",
                        "health ok without tool disclosure; bind is loopback",
                        bind=health.bind,
                    )
                )

            # Unauthenticated discovery
            unauth = client.get(f"{base}/mcp")
            if unauth.status_code == 401 and "tools" not in unauth.json():
                results.append(
                    _pass("DCP-ACC-021", "live", "unauthenticated MCP denied; no tool list", status=401)
                )
            else:
                results.append(_fail("DCP-ACC-021", "live", f"unauth unexpected status={unauth.status_code}"))

            # Auth discovery
            auth = client.get(f"{base}/mcp", headers={"Authorization": f"Bearer {token}"})
            if auth.status_code == 200 and auth.json().get("authenticated_connector") == "chatgpt-dopemux-main":
                names = {t.get("name") for t in auth.json().get("tools", [])}
                if "mutation-tool-denied" not in names and "get_progress" not in names:
                    results.append(
                        _pass(
                            "DCP-ACC-023",
                            "live",
                            "local connector discovery returns non-mutation tool subset only",
                            tool_count=len(names),
                        )
                    )
                else:
                    results.append(_fail("DCP-ACC-023", "live", "mutation-shaped tool present in discovery"))
            else:
                results.append(_fail("DCP-ACC-023", "live", "authenticated discovery failed"))

            # Cross-connector isolation (ACC-013 live)
            cross = client.get(f"{base}/mcp", headers={"Authorization": f"Bearer {token_b}"})
            if (
                cross.status_code == 200
                and cross.json().get("authenticated_connector") == "grok-feature-review-a7"
            ):
                results.append(
                    _pass(
                        "DCP-ACC-013",
                        "live",
                        "second connector authenticates independently on same ingress",
                    )
                )
            else:
                results.append(_fail("DCP-ACC-013", "live", "second connector auth failed"))

            # Rate limit (ACC-022 live)
            limited_status = None
            for _ in range(5):
                r = client.get(f"{base}/mcp", headers={"Authorization": f"Bearer {token}"})
                if r.status_code == 429:
                    limited_status = 429
                    break
            if limited_status == 429:
                results.append(_pass("DCP-ACC-022", "live", "burst exhaustion returns 429 on live loopback"))
            else:
                results.append(_fail("DCP-ACC-022", "live", "did not observe 429 under low burst policy"))

            # Rotation (ACC-027): old token fails after resolver swap
            server.secret_resolver = MappingSecretResolver(
                {
                    ("environment", f"env:{env_name}"): token + "-rotated",
                    ("environment", "env:DCP_ACCEPTANCE_LIVE_TOKEN_B"): token_b,
                }
            )
            # Middleware holds original resolver reference — replace via app field
            server.app.secret_resolver = server.secret_resolver  # type: ignore[attr-defined]
            old = client.get(f"{base}/mcp", headers={"Authorization": f"Bearer {token}"})
            new = client.get(f"{base}/mcp", headers={"Authorization": f"Bearer {token}-rotated"})
            if old.status_code == 401 and new.status_code in {200, 429}:
                results.append(
                    _pass(
                        "DCP-ACC-027",
                        "live",
                        "credential rotation rejects old token; new token accepted",
                    )
                )
            else:
                results.append(
                    _fail(
                        "DCP-ACC-027",
                        "live",
                        f"rotation unexpected old={old.status_code} new={new.status_code}",
                    )
                )

            # Audit must not contain raw token (ACC-020/021)
            dump = server.audit_log.dump_json_lines()
            if token not in dump and (token + "-rotated") not in dump:
                results.append(
                    _pass("DCP-ACC-020", "live", "audit dump excludes raw bearer token values")
                )
            else:
                results.append(_fail("DCP-ACC-020", "live", "raw token leaked into audit dump"))

        # Disable / stop facade (ACC-028 partial)
        stopped = server.stop()
        if not stopped.running:
            # connection should fail
            try:
                with httpx.Client(timeout=1.0) as client:
                    client.get(f"{base}/health")
                results.append(_fail("DCP-ACC-028", "live", "health still reachable after stop"))
            except Exception:
                results.append(
                    _pass(
                        "DCP-ACC-028",
                        "live",
                        "facade stop ends loopback access (local disable sequence)",
                        bind=health.bind,
                    )
                )
        else:
            results.append(_fail("DCP-ACC-028", "live", "server still running after stop"))
    finally:
        try:
            server.stop()
        except Exception:
            pass

    # Ownership live-shaped evidence (ACC-006/008/009 already deterministic; reaffirm live)
    own = verify_ownership(
        OwnershipEvidence(
            family="conport",
            expected_project_id="proj-live",
            expected_project_root="/tmp/proj-live",
            expected_worktree_root="/tmp/proj-live/wt",
            runtime_project_id="proj-live",
            runtime_project_root="/tmp/proj-live",
            runtime_worktree_root="/tmp/proj-live/wt",
            labels={
                "dopemux.project_id": "proj-live",
                "dopemux.service": "conport",
                "dopemux.worktree_root": "/tmp/proj-live/wt",
            },
            mounts=("/tmp/proj-live/wt",),
            protocol_ok=True,
            has_listening_port=True,
            candidate_count=1,
        )
    )
    if own.verified:
        results.append(
            _pass(
                "DCP-ACC-006",
                "live",
                "ownership verifies only with full evidence; port alone insufficient (covered by matrix tests)",
            )
        )
    else:
        results.append(_fail("DCP-ACC-006", "live", "full evidence failed ownership"))

    return results


def vendor_preflight() -> dict[str, Any]:
    """Inventory required tools/env for vendor gates without printing secrets."""
    import shutil

    def _set(name: str) -> bool:
        v = os.getenv(name, "").strip()
        return bool(v) and not (v.startswith("<") and v.endswith(">"))

    inventory = {
        "tools": {
            "tunnel-client": bool(shutil.which("tunnel-client")),
            "cloudflared": bool(shutil.which("cloudflared")),
            "ngrok": bool(shutil.which("ngrok")),
            "curl": bool(shutil.which("curl")),
        },
        "env_present": {
            "CONTROL_PLANE_API_KEY": _set("CONTROL_PLANE_API_KEY"),
            "OPENAI_API_KEY": _set("OPENAI_API_KEY"),
            "OPENAI_TUNNEL_ID": _set("OPENAI_TUNNEL_ID"),
            "OPENAI_TUNNEL_PROFILE": _set("OPENAI_TUNNEL_PROFILE"),
            "XAI_API_KEY": _set("XAI_API_KEY") or _set("GROK_API_KEY"),
            "PUBLIC_GROK_HOSTNAME": _set("PUBLIC_GROK_HOSTNAME"),
            "GEMINI_API_KEY": _set("GEMINI_API_KEY") or _set("GOOGLE_API_KEY"),
            "PUBLIC_GEMINI_HOSTNAME": _set("PUBLIC_GEMINI_HOSTNAME"),
            "DCP_ACCEPTANCE_LIVE_TOKEN": _set(LIVE_TOKEN_ENV),
        },
    }
    chatgpt_ok = (
        inventory["tools"]["tunnel-client"]
        and inventory["env_present"]["CONTROL_PLANE_API_KEY"]
        and inventory["env_present"]["OPENAI_TUNNEL_ID"]
        and inventory["env_present"]["DCP_ACCEPTANCE_LIVE_TOKEN"]
    )
    grok_ok = inventory["env_present"]["PUBLIC_GROK_HOSTNAME"] and inventory["env_present"][
        "DCP_ACCEPTANCE_LIVE_TOKEN"
    ]
    gemini_ok = inventory["env_present"]["PUBLIC_GEMINI_HOSTNAME"] and inventory["env_present"][
        "DCP_ACCEPTANCE_LIVE_TOKEN"
    ]
    inventory["gates_runnable"] = {
        "DCP-ACC-024_chatgpt_tunnel": chatgpt_ok,
        "DCP-ACC-025_grok_stable": grok_ok,
        "DCP-ACC-026_gemini_transport": gemini_ok,
    }
    missing = []
    if not inventory["tools"]["tunnel-client"]:
        missing.append("install tunnel-client (OpenAI Secure MCP Tunnel)")
    if not inventory["env_present"]["CONTROL_PLANE_API_KEY"]:
        missing.append("set CONTROL_PLANE_API_KEY")
    if not inventory["env_present"]["OPENAI_TUNNEL_ID"]:
        missing.append("set OPENAI_TUNNEL_ID")
    if not inventory["env_present"]["PUBLIC_GROK_HOSTNAME"]:
        missing.append("set PUBLIC_GROK_HOSTNAME (stable named tunnel host)")
    if not inventory["env_present"]["PUBLIC_GEMINI_HOSTNAME"]:
        missing.append("set PUBLIC_GEMINI_HOSTNAME")
    if not inventory["env_present"]["DCP_ACCEPTANCE_LIVE_TOKEN"]:
        missing.append("set DCP_ACCEPTANCE_LIVE_TOKEN (connector bearer)")
    inventory["missing_for_vendor_live"] = missing
    return inventory


def run_two_worktree_isolation_gates() -> list[GateResult]:
    """ACC-029: synthetic two-target isolation without vendor tunnels.

    Proves connector A cannot authorize target B and ownership for A/B is distinct.
    Does not call real ConPort/dope-memory backends.
    """
    results: list[GateResult] = []
    policy_doc = {
        "records": [
            _fixture_policy("conn-a", "DCP_TOKEN_A", ["target-a"]),
            _fixture_policy("conn-b", "DCP_TOKEN_B", ["target-b"]),
        ]
    }
    # multi_target false with one target each
    store = parse_connector_policy_document(policy_doc)
    resolver = MappingSecretResolver(
        {
            ("environment", "env:DCP_TOKEN_A"): "token-a-secret",
            ("environment", "env:DCP_TOKEN_B"): "token-b-secret",
        }
    )
    ctx_a, d_a = authenticate_bearer(store, presented_token="token-a-secret", secret_resolver=resolver)
    ctx_b, d_b = authenticate_bearer(store, presented_token="token-b-secret", secret_resolver=resolver)
    if not (d_a.allowed and d_b.allowed and ctx_a and ctx_b):
        results.append(_fail("DCP-ACC-029", "live", "failed to authenticate dual connector fixtures"))
        return results

    a_ok = authorize_target(ctx_a, "target-a")
    a_cross = authorize_target(ctx_a, "target-b")
    b_ok = authorize_target(ctx_b, "target-b")
    b_cross = authorize_target(ctx_b, "target-a")
    invented = authorize_target(ctx_a, "invented-target")

    own_a = verify_ownership(
        OwnershipEvidence(
            family="conport",
            expected_project_id="proj-a",
            expected_project_root="/tmp/wt-a",
            expected_worktree_root="/tmp/wt-a",
            runtime_project_id="proj-a",
            runtime_project_root="/tmp/wt-a",
            runtime_worktree_root="/tmp/wt-a",
            labels={
                "dopemux.project_id": "proj-a",
                "dopemux.service": "conport",
                "dopemux.worktree_root": "/tmp/wt-a",
            },
            mounts=("/tmp/wt-a",),
            protocol_ok=True,
            candidate_count=1,
        )
    )
    own_b_wrong = verify_ownership(
        OwnershipEvidence(
            family="conport",
            expected_project_id="proj-a",
            expected_project_root="/tmp/wt-a",
            expected_worktree_root="/tmp/wt-a",
            runtime_project_id="proj-b",
            runtime_project_root="/tmp/wt-b",
            runtime_worktree_root="/tmp/wt-b",
            labels={
                "dopemux.project_id": "proj-b",
                "dopemux.service": "conport",
                "dopemux.worktree_root": "/tmp/wt-b",
            },
            mounts=("/tmp/wt-b",),
            protocol_ok=True,
            candidate_count=1,
        )
    )

    if (
        a_ok.allowed
        and b_ok.allowed
        and not a_cross.allowed
        and not b_cross.allowed
        and not invented.allowed
        and own_a.verified
        and not own_b_wrong.verified
    ):
        results.append(
            _pass(
                "DCP-ACC-029",
                "live",
                "two-target connector isolation + wrong-owner ownership block (synthetic, no vendor tunnel)",
            )
        )
    else:
        results.append(_fail("DCP-ACC-029", "live", "two-target isolation matrix unexpected"))
    return results


def run_vendor_live_gates(providers: set[str]) -> list[GateResult]:
    """Vendor tunnel/provider gates: preflight only unless full tooling+env present.

    Never opens public tunnels or invents credentials.
    """
    results: list[GateResult] = []
    inv = vendor_preflight()
    runnable = inv["gates_runnable"]

    # Always attach preflight evidence (no secrets)
    preflight_detail = "vendor preflight: missing=" + ",".join(inv["missing_for_vendor_live"] or ["none"])

    # ACC-024 ChatGPT
    if "chatgpt" in providers or not (providers & VENDOR_PROVIDERS):
        # if vendors requested broadly, evaluate chatgpt when listed or when any vendor listed
        want_chatgpt = "chatgpt" in providers or bool(providers & {"chatgpt"})
    else:
        want_chatgpt = "chatgpt" in providers
    # simplify: if any vendor provider listed, check each
    if providers & VENDOR_PROVIDERS or "vendor" in providers:
        if runnable["DCP-ACC-024_chatgpt_tunnel"] and "chatgpt" in providers:
            results.append(
                _not_run(
                    "DCP-ACC-024",
                    "live",
                    "ChatGPT preflight OK but automated tunnel-client exercise is not auto-run; "
                    "operator must execute tunnel-client and attach redacted doctor/export receipts. "
                    + preflight_detail,
                )
            )
        else:
            results.append(
                _not_run(
                    "DCP-ACC-024",
                    "live",
                    "ChatGPT tunnel not runnable: need tunnel-client + CONTROL_PLANE_API_KEY + "
                    "OPENAI_TUNNEL_ID + connector token. " + preflight_detail,
                    tools=inv["tools"],
                    env_present=inv["env_present"],
                )
            )

        if runnable["DCP-ACC-025_grok_stable"] and "grok" in providers:
            results.append(
                _not_run(
                    "DCP-ACC-025",
                    "live",
                    "Grok hostname present but stable tunnel restart acceptance is manual; "
                    "attach redacted DNS/HTTPS + discovery receipts. " + preflight_detail,
                )
            )
        else:
            results.append(
                _not_run(
                    "DCP-ACC-025",
                    "live",
                    "Grok stable route not runnable: need PUBLIC_GROK_HOSTNAME + connector token. "
                    + preflight_detail,
                    env_present=inv["env_present"],
                )
            )

        if runnable["DCP-ACC-026_gemini_transport"] and (
            "gemini" in providers or "gemini_api" in providers
        ):
            results.append(
                _not_run(
                    "DCP-ACC-026",
                    "live",
                    "Gemini host present but unsupported-transport fail-closed check is manual; "
                    "attach provider error + DCP no-call proof. " + preflight_detail,
                )
            )
        else:
            results.append(
                _not_run(
                    "DCP-ACC-026",
                    "live",
                    "Gemini transport gate not runnable: need PUBLIC_GEMINI_HOSTNAME + connector token. "
                    + preflight_detail,
                    env_present=inv["env_present"],
                )
            )
    else:
        for tid, label in (
            ("DCP-ACC-024", "chatgpt"),
            ("DCP-ACC-025", "grok"),
            ("DCP-ACC-026", "gemini"),
        ):
            results.append(
                _not_run(
                    tid,
                    "live",
                    f"vendor provider '{label}' not listed; set "
                    f"DCP_ACCEPTANCE_LIVE_PROVIDERS=local,chatgpt,grok,gemini as applicable. "
                    + preflight_detail,
                )
            )
    return results


def run_live_gates() -> list[GateResult]:
    """Live gates: fail closed without dual consent; local/vendor as requested."""
    ok, reason = live_mode_authorized()
    vendor_ids = ["DCP-ACC-024", "DCP-ACC-025", "DCP-ACC-026"]
    local_capable_ids = {
        "DCP-ACC-006",
        "DCP-ACC-013",
        "DCP-ACC-015",
        "DCP-ACC-020",
        "DCP-ACC-021",
        "DCP-ACC-022",
        "DCP-ACC-023",
        "DCP-ACC-027",
        "DCP-ACC-028",
    }
    all_live_ids = sorted(
        local_capable_ids
        | set(vendor_ids)
        | {"DCP-ACC-007", "DCP-ACC-008", "DCP-ACC-009", "DCP-ACC-010", "DCP-ACC-016", "DCP-ACC-029"}
    )

    if not ok:
        return [_not_run(tid, "live", f"live gate blocked: {reason}") for tid in all_live_ids]

    providers = set(parse_live_providers())
    if "vendor" in providers:
        providers |= {"chatgpt", "grok", "gemini"}

    results: list[GateResult] = []
    token: [REDACTED], "").strip()

    # Local loopback suite
    if providers & LOCAL_PROVIDERS:
        try:
            results.extend(run_local_loopback_live_gates(token))
        except Exception as exc:  # pragma: no cover
            results.append(
                _fail(
                    "DCP-ACC-028",
                    "live",
                    f"local loopback live suite crashed: {exc.__class__.__name__}",
                )
            )
        produced = {r.test_id for r in results}
        for tid in sorted(local_capable_ids - produced):
            results.append(_not_run(tid, "live", "local live suite did not emit this gate"))
    else:
        for tid in sorted(local_capable_ids):
            results.append(
                _not_run(
                    tid,
                    "live",
                    "local loopback not requested; include 'local' in DCP_ACCEPTANCE_LIVE_PROVIDERS",
                )
            )

    # Two-target synthetic isolation
    results.extend(run_two_worktree_isolation_gates())

    # Vendor preflight (never invents credentials or opens tunnels)
    if providers & VENDOR_PROVIDERS:
        results.extend(run_vendor_live_gates(providers))
    else:
        for tid in vendor_ids:
            results.append(
                _not_run(
                    tid,
                    "live",
                    "vendor not listed; set DCP_ACCEPTANCE_LIVE_PROVIDERS=local,chatgpt,grok,gemini",
                )
            )

    return results


def run_acceptance(*, include_live: bool = True) -> dict[str, Any]:
    """Run deterministic gates always; live gates only when include_live."""
    deterministic = run_deterministic_gates()
    live = run_live_gates() if include_live else []
    all_results = deterministic + live

    # Collapse duplicate test_ids: if any FAIL, FAIL; elif any PASS, PASS; else NOT_RUN
    by_id: dict[str, list[GateResult]] = {}
    for item in all_results:
        by_id.setdefault(item.test_id, []).append(item)

    rollup: list[dict[str, Any]] = []
    blocking_failures = 0
    blocking_not_run_live = 0
    for test_id, items in sorted(by_id.items()):
        statuses = {i.status for i in items}
        if "FAIL" in statuses:
            status = "FAIL"
            if any(i.blocking for i in items):
                blocking_failures += 1
        elif "PASS" in statuses and "NOT_RUN" in statuses:
            # Deterministic pass + live not run → overall NOT_READY, status MIXED
            status = "PASS_PARTIAL"
            if any(i.blocking and i.status == "NOT_RUN" and i.gate_type == "live" for i in items):
                blocking_not_run_live += 1
        elif "PASS" in statuses:
            status = "PASS"
        else:
            status = "NOT_RUN"
            if any(i.blocking and i.gate_type == "live" for i in items):
                blocking_not_run_live += 1
        rollup.append(
            {
                "test_id": test_id,
                "status": status,
                "results": [i.to_public_dict() for i in items],
            }
        )

    ready = blocking_failures == 0 and blocking_not_run_live == 0
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "live_authorized": live_mode_authorized()[0],
        "release_ready": ready,
        "blocking_failures": blocking_failures,
        "blocking_live_not_run": blocking_not_run_live,
        "note": (
            "release_ready is true only when every blocking gate PASSes. "
            "Live NOT_RUN keeps release_ready false."
        ),
        "rollup": rollup,
        "deterministic_count": len(deterministic),
        "live_count": len(live),
    }


def main() -> None:
    report = run_acceptance(include_live=True)
    print(json.dumps(report, indent=2, sort_keys=True))
    # Exit 0 for harness success; readiness is in report.release_ready
    # Exit 2 if deterministic FAIL
    if report["blocking_failures"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
