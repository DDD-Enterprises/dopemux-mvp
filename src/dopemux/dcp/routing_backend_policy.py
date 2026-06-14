"""Pure backend policy map for DCP routing decisions.

DMX-DCP-MODEL-ROUTING-MVP-0003 adds inert backend preference data on top of
classified :class:`RouteDecision` records. It does not invoke backends,
connectors, runners, provider APIs, GitHub, MCP, Dopetask, or workflow tools.
"""

from __future__ import annotations

from dataclasses import dataclass

from dopemux.dcp.routing_classifier import (
    RoutingClassificationInput,
    classify_route,
)
from dopemux.dcp.routing_model import (
    AuditRequirement,
    BackendKind,
    ComplexityClass,
    EscalationRequirement,
    RedLaneState,
    RiskClass,
    RouteDecision,
    RouteStatus,
    RuntimeImpact,
    TaskType,
)


ALLOWED_POLICY = "ALLOWED_POLICY"
BLOCKED_POLICY = "BLOCKED_POLICY"
SUPERVISOR_POLICY = "SUPERVISOR_POLICY"
UNKNOWN_POLICY = "UNKNOWN_POLICY"
ADVISORY_ONLY = "ADVISORY_ONLY"

_EXECUTION_BACKENDS: tuple[BackendKind, ...] = (
    BackendKind.CODEX,
    BackendKind.CLAUDE_CODE,
    BackendKind.OPENCODE,
    BackendKind.GROK,
    BackendKind.GEMINI_CLI,
    BackendKind.AGY,
    BackendKind.LOCAL_SCRIPT,
)

_NON_DEFAULT_EXECUTION_BACKENDS: tuple[BackendKind, ...] = (
    BackendKind.OPENCODE,
    BackendKind.GROK,
    BackendKind.LOCAL_SCRIPT,
)

_BLOCKING_STOP_CONDITIONS: frozenset[str] = frozenset(
    {
        "red_lane_active",
        "conflicting_evidence",
        "secrets_surface_in_scope",
        "auth_surface_in_scope",
        "ci_surface_in_scope",
        "network_required",
        "external_service_required",
        "merge_task_requested",
        "service_mutation_requested",
        "live_write_requested",
        "runner_execution_requested",
        "forbidden_requested_action",
    }
)


@dataclass(frozen=True)
class BackendPolicyDecision:
    """Inert backend preference metadata for a classified route."""

    route_id: str
    preferred_backend: BackendKind
    fallback_backends: tuple[BackendKind, ...] = ()
    forbidden_backends: tuple[BackendKind, ...] = ()
    policy_status: str = UNKNOWN_POLICY
    reason_codes: tuple[str, ...] = ()
    stop_conditions: tuple[str, ...] = ()
    escalation_required: bool = False
    evidence_refs: tuple[str, ...] = ()


def select_backend_policy(route: RouteDecision) -> BackendPolicyDecision:
    """Select inert backend policy metadata for an existing route decision."""
    stop_conditions = tuple(route.stop_conditions)
    evidence_refs = tuple(route.evidence_refs)

    if _is_blocked_policy(route):
        return BackendPolicyDecision(
            route_id=route.route_id,
            preferred_backend=BackendKind.NONE,
            forbidden_backends=_EXECUTION_BACKENDS,
            policy_status=BLOCKED_POLICY,
            reason_codes=_reason_codes(route, "blocked_route", "route_not_runnable"),
            stop_conditions=stop_conditions,
            escalation_required=True,
            evidence_refs=evidence_refs,
        )

    if _is_unknown_policy(route):
        return BackendPolicyDecision(
            route_id=route.route_id,
            preferred_backend=BackendKind.UNKNOWN,
            forbidden_backends=_EXECUTION_BACKENDS,
            policy_status=UNKNOWN_POLICY,
            reason_codes=_reason_codes(route, "unknown_route", "route_not_runnable"),
            stop_conditions=stop_conditions,
            escalation_required=_requires_escalation(route),
            evidence_refs=evidence_refs,
        )

    if _is_supervisor_policy(route):
        return BackendPolicyDecision(
            route_id=route.route_id,
            preferred_backend=BackendKind.NONE,
            forbidden_backends=_EXECUTION_BACKENDS,
            policy_status=SUPERVISOR_POLICY,
            reason_codes=_reason_codes(
                route, "supervisor_required", "route_not_runnable"
            ),
            stop_conditions=stop_conditions,
            escalation_required=True,
            evidence_refs=evidence_refs,
        )

    if not route.is_runnable():
        return BackendPolicyDecision(
            route_id=route.route_id,
            preferred_backend=BackendKind.NONE,
            forbidden_backends=_EXECUTION_BACKENDS,
            policy_status=ADVISORY_ONLY,
            reason_codes=_reason_codes(route, "route_not_runnable"),
            stop_conditions=stop_conditions,
            escalation_required=_requires_escalation(route),
            evidence_refs=evidence_refs,
        )

    preferred, fallbacks = _allowed_backend_order(route)
    return BackendPolicyDecision(
        route_id=route.route_id,
        preferred_backend=preferred,
        fallback_backends=fallbacks,
        forbidden_backends=_NON_DEFAULT_EXECUTION_BACKENDS,
        policy_status=ALLOWED_POLICY,
        reason_codes=_reason_codes(route, "route_runnable", "backend_policy_data_only"),
        stop_conditions=stop_conditions,
        escalation_required=False,
        evidence_refs=evidence_refs,
    )


def select_backend_policy_for_input(
    inp: RoutingClassificationInput,
) -> BackendPolicyDecision:
    """Classify input, then select inert backend policy metadata."""
    return select_backend_policy(classify_route(inp))


def _is_blocked_policy(route: RouteDecision) -> bool:
    if route.red_lane_state is RedLaneState.RED_LANE:
        return True
    if route.status is RouteStatus.BLOCKED:
        return True
    if route.risk_class is RiskClass.RED_LANE:
        return True
    if route.task_type in (TaskType.MERGE, TaskType.LIVE_WRITE):
        return True
    if route.runtime_impact in (
        RuntimeImpact.SERVICE_MUTATION,
        RuntimeImpact.LIVE_WRITE,
    ):
        return True
    return any(
        stop in _BLOCKING_STOP_CONDITIONS
        or stop.startswith("forbidden_action_requested:")
        for stop in route.stop_conditions
    )


def _is_unknown_policy(route: RouteDecision) -> bool:
    return (
        route.status is RouteStatus.UNKNOWN
        or route.red_lane_state is RedLaneState.UNKNOWN
        or bool(route.unknowns)
    )


def _is_supervisor_policy(route: RouteDecision) -> bool:
    return (
        route.status is RouteStatus.NEEDS_SUPERVISOR
        or _requires_escalation(route)
        or route.audit_requirement is AuditRequirement.SUPERVISOR_AUDIT
        or route.risk_class is RiskClass.R3_HIGH
        or route.complexity_class is ComplexityClass.ARCHITECTURAL
    )


def _requires_escalation(route: RouteDecision) -> bool:
    return route.escalation_requirement is not EscalationRequirement.NONE


def _allowed_backend_order(
    route: RouteDecision,
) -> tuple[BackendKind, tuple[BackendKind, ...]]:
    if (
        route.complexity_class is ComplexityClass.MEDIUM
        or route.risk_class is RiskClass.R2_MEDIUM
    ):
        return BackendKind.CLAUDE_CODE, (
            BackendKind.CODEX,
            BackendKind.GEMINI_CLI,
        )
    return BackendKind.CODEX, (
        BackendKind.CLAUDE_CODE,
        BackendKind.GEMINI_CLI,
    )


def _reason_codes(route: RouteDecision, *extra: str) -> tuple[str, ...]:
    reasons: list[str] = []
    for reason in extra:
        _append_unique(reasons, reason)
    if route.status is RouteStatus.BLOCKED:
        _append_unique(reasons, "status_blocked")
    if route.status is RouteStatus.UNKNOWN:
        _append_unique(reasons, "status_unknown")
    if route.status is RouteStatus.NEEDS_SUPERVISOR:
        _append_unique(reasons, "status_needs_supervisor")
    if route.red_lane_state is RedLaneState.RED_LANE:
        _append_unique(reasons, "red_lane")
    if route.red_lane_state is RedLaneState.UNKNOWN:
        _append_unique(reasons, "red_lane_unknown")
    if _requires_escalation(route):
        _append_unique(reasons, "escalation_required")
    if route.audit_requirement is AuditRequirement.SUPERVISOR_AUDIT:
        _append_unique(reasons, "supervisor_audit_required")
    return tuple(reasons)


def _append_unique(items: list[str], item: str) -> None:
    if item not in items:
        items.append(item)
