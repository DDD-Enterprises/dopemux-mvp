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
LIVE_PROVIDER_ENV = "DCP_ACCEPTANCE_LIVE_PROVIDERS"  # e.g. none|chatgpt,grok


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


def live_mode_authorized() -> tuple[bool, str]:
    """Live gates require explicit dual consent; credentials are never defaulted."""
    if os.getenv(LIVE_CONSENT_ENV, "").strip() != "1":
        return False, f"{LIVE_CONSENT_ENV}!=1 (live gates not authorized)"
    token = os.getenv(LIVE_TOKEN_ENV, "").strip()
    if not token:
        return False, f"{LIVE_TOKEN_ENV} unset (no live credential authorized)"
    # Token must not look empty-placeholder; actual value never returned.
    if token.startswith("<") and token.endswith(">"):
        return False, f"{LIVE_TOKEN_ENV} is still a placeholder"
    providers = os.getenv(LIVE_PROVIDER_ENV, "").strip()
    if not providers or providers.lower() == "none":
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


def run_live_gates() -> list[GateResult]:
    """Live gates: fail closed to NOT_RUN without dual consent env."""
    ok, reason = live_mode_authorized()
    live_ids = [
        "DCP-ACC-006",
        "DCP-ACC-007",
        "DCP-ACC-008",
        "DCP-ACC-009",
        "DCP-ACC-010",
        "DCP-ACC-013",
        "DCP-ACC-015",
        "DCP-ACC-016",
        "DCP-ACC-020",
        "DCP-ACC-021",
        "DCP-ACC-023",
        "DCP-ACC-024",
        "DCP-ACC-025",
        "DCP-ACC-026",
        "DCP-ACC-027",
        "DCP-ACC-028",
        "DCP-ACC-029",
    ]
    # Note: some IDs also have deterministic coverage; live re-check is separate.
    if not ok:
        return [
            _not_run(tid, "live", f"live gate blocked: {reason}")
            for tid in live_ids
        ]
    # Even with consent env, this packet does not auto-run vendor tunnels without
    # further operator scripts. Explicitly mark provider rows NOT_RUN unless a
    # future runner is wired.
    return [
        _not_run(
            tid,
            "live",
            "live consent env set but automated provider/tunnel runner not implemented in this packet; "
            "operator must run bounded manual acceptance and attach redacted receipts",
        )
        for tid in live_ids
    ]


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
