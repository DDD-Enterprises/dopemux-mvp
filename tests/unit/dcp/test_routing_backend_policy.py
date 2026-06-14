"""Unit tests for DMX-DCP-MODEL-ROUTING-MVP-0003 backend policy.

Coverage targets:
- Pure import and static no-go checks
- Hard gates for blocked, unknown, red-lane, supervisor, escalation cases
- No runnable backend policy for security, live-write, connector, MCP,
  Dopetask, or Task Orchestrator cases
- Deterministic preferred, fallback, and forbidden backend metadata
- Evidence, stop conditions, immutability, serializability, and helper parity
"""

from __future__ import annotations

from dataclasses import asdict
import inspect

import pytest

from dopemux.dcp.routing_classifier import RoutingClassificationInput, classify_route
from dopemux.dcp.routing_model import (
    AuditRequirement,
    AuthorityClass,
    BackendKind,
    ComplexityClass,
    EscalationRequirement,
    RedLaneState,
    RiskClass,
    RouteDecision,
    RouteStatus,
    RuntimeImpact,
    TaskSource,
    TaskType,
)


FORBIDDEN_IMPORTS_IN_POLICY = {
    "subprocess",
    "requests",
    "httpx",
    "urllib",
    "socket",
    "github",
    "docker",
    "mcp",
    "dopetask",
    "task_orchestrator",
    "conport",
    "dope_memory",
    "dope_context",
}

FORBIDDEN_METHOD_PREFIXES = (
    "def run",
    "def execute",
    "def dispatch",
    "def invoke",
    "def merge",
)


def _safe_read_route() -> RouteDecision:
    return classify_route(
        RoutingClassificationInput(
            task_source=TaskSource.OPERATOR,
            task_type=TaskType.READ_ONLY,
            risk_class=RiskClass.R0_READ,
            complexity_class=ComplexityClass.LOW,
            authority_class=AuthorityClass.OPERATOR,
            runtime_impact=RuntimeImpact.READ_ONLY,
            has_unknown_authority=False,
        )
    )


def _safe_code_route(
    *,
    risk_class: RiskClass = RiskClass.R1_LOW,
    complexity_class: ComplexityClass = ComplexityClass.LOW,
) -> RouteDecision:
    return classify_route(
        RoutingClassificationInput(
            task_source=TaskSource.OPERATOR,
            task_type=TaskType.CODE_CHANGE,
            risk_class=risk_class,
            complexity_class=complexity_class,
            authority_class=AuthorityClass.OPERATOR,
            runtime_impact=RuntimeImpact.LOCAL_ONLY,
            has_unknown_authority=False,
        )
    )


def test_import_backend_policy_module() -> None:
    import dopemux.dcp.routing_backend_policy as mod

    assert callable(mod.select_backend_policy)
    assert callable(mod.select_backend_policy_for_input)
    assert hasattr(mod, "BackendPolicyDecision")


def test_default_unknown_route_is_not_allowed_policy() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    policy = select_backend_policy(RouteDecision())

    assert policy.policy_status == "UNKNOWN_POLICY"
    assert policy.preferred_backend is BackendKind.UNKNOWN
    assert "route_not_runnable" in policy.reason_codes


def test_red_lane_route_produces_blocked_policy() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    route = RouteDecision(
        route_id="red",
        status=RouteStatus.ALLOWED,
        red_lane_state=RedLaneState.RED_LANE,
        authority_class=AuthorityClass.OPERATOR,
    )
    policy = select_backend_policy(route)

    assert policy.policy_status == "BLOCKED_POLICY"
    assert policy.preferred_backend is BackendKind.NONE
    assert BackendKind.CODEX in policy.forbidden_backends


def test_blocked_route_produces_blocked_policy() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    policy = select_backend_policy(
        RouteDecision(
            route_id="blocked",
            status=RouteStatus.BLOCKED,
            red_lane_state=RedLaneState.CLEAR,
            authority_class=AuthorityClass.OPERATOR,
        )
    )

    assert policy.policy_status == "BLOCKED_POLICY"
    assert policy.preferred_backend is BackendKind.NONE


def test_unknown_route_produces_unknown_policy() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    policy = select_backend_policy(
        RouteDecision(
            route_id="unknown",
            status=RouteStatus.UNKNOWN,
            red_lane_state=RedLaneState.CLEAR,
            authority_class=AuthorityClass.OPERATOR,
        )
    )

    assert policy.policy_status == "UNKNOWN_POLICY"
    assert policy.preferred_backend is BackendKind.UNKNOWN


def test_supervisor_needed_route_produces_supervisor_policy() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    policy = select_backend_policy(
        RouteDecision(
            route_id="supervisor",
            status=RouteStatus.NEEDS_SUPERVISOR,
            red_lane_state=RedLaneState.CLEAR,
            authority_class=AuthorityClass.OPERATOR,
        )
    )

    assert policy.policy_status == "SUPERVISOR_POLICY"
    assert policy.preferred_backend is BackendKind.NONE
    assert "supervisor_required" in policy.reason_codes


def test_escalation_required_route_is_not_allowed_policy() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    route = _safe_code_route()
    route.escalation_requirement = EscalationRequirement.ON_RISK
    policy = select_backend_policy(route)

    assert policy.policy_status == "SUPERVISOR_POLICY"
    assert policy.preferred_backend is BackendKind.NONE


def test_security_route_has_no_runnable_backend_policy() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    route = classify_route(RoutingClassificationInput(touches_security=True))
    policy = select_backend_policy(route)

    assert policy.policy_status == "BLOCKED_POLICY"
    assert policy.preferred_backend is BackendKind.NONE
    assert BackendKind.CODEX in policy.forbidden_backends


@pytest.mark.parametrize(
    "flag",
    [
        "touches_auth",
        "touches_secrets",
        "touches_destructive_path",
        "requires_live_write",
        "requires_connector_call",
        "requires_mcp_call",
        "requires_dopetask_execution",
        "requires_task_orchestrator_write",
    ],
)
def test_red_lane_input_flags_have_no_runnable_backend_policy(flag: str) -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    route = classify_route(RoutingClassificationInput(**{flag: True}))
    policy = select_backend_policy(route)

    assert not route.is_runnable()
    assert policy.policy_status == "BLOCKED_POLICY"
    assert policy.preferred_backend is BackendKind.NONE
    assert not policy.fallback_backends


def test_read_only_known_route_gets_deterministic_preferred_backend() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    policy = select_backend_policy(_safe_read_route())

    assert policy.policy_status == "ALLOWED_POLICY"
    assert policy.preferred_backend is BackendKind.CODEX
    assert policy.fallback_backends == (BackendKind.CLAUDE_CODE, BackendKind.GEMINI_CLI)


def test_local_code_change_route_gets_deterministic_preferred_backend() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    policy = select_backend_policy(_safe_code_route())

    assert policy.policy_status == "ALLOWED_POLICY"
    assert policy.preferred_backend is BackendKind.CODEX
    assert policy.fallback_backends == (BackendKind.CLAUDE_CODE, BackendKind.GEMINI_CLI)


def test_medium_complexity_code_change_prefers_claude_code_data() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    policy = select_backend_policy(
        _safe_code_route(
            risk_class=RiskClass.R2_MEDIUM,
            complexity_class=ComplexityClass.MEDIUM,
        )
    )

    assert policy.policy_status == "ALLOWED_POLICY"
    assert policy.preferred_backend is BackendKind.CLAUDE_CODE
    assert policy.fallback_backends == (BackendKind.CODEX, BackendKind.GEMINI_CLI)


def test_architectural_complexity_route_is_supervisor_policy() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    route = classify_route(
        RoutingClassificationInput(
            task_source=TaskSource.OPERATOR,
            task_type=TaskType.CODE_CHANGE,
            risk_class=RiskClass.R1_LOW,
            complexity_class=ComplexityClass.ARCHITECTURAL,
            authority_class=AuthorityClass.OPERATOR,
            runtime_impact=RuntimeImpact.LOCAL_ONLY,
            has_unknown_authority=False,
        )
    )
    policy = select_backend_policy(route)

    assert route.status is RouteStatus.NEEDS_SUPERVISOR
    assert policy.policy_status == "SUPERVISOR_POLICY"


def test_high_risk_route_is_supervisor_policy() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    route = _safe_code_route(risk_class=RiskClass.R3_HIGH)
    policy = select_backend_policy(route)

    assert route.status is RouteStatus.NEEDS_SUPERVISOR
    assert policy.policy_status == "SUPERVISOR_POLICY"


def test_fallback_order_is_deterministic() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    route = _safe_code_route()

    assert (
        select_backend_policy(route).fallback_backends
        == select_backend_policy(route).fallback_backends
    )


def test_forbidden_backends_are_deterministic() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    route = _safe_code_route()

    assert select_backend_policy(route).forbidden_backends == (
        BackendKind.OPENCODE,
        BackendKind.GROK,
        BackendKind.LOCAL_SCRIPT,
    )


def test_evidence_refs_are_preserved() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    route = _safe_read_route()
    route.evidence_refs.append("proof/example.json")
    policy = select_backend_policy(route)

    assert policy.evidence_refs == ("proof/example.json",)


def test_stop_conditions_are_preserved() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    route = RouteDecision(
        route_id="stopped",
        status=RouteStatus.BLOCKED,
        red_lane_state=RedLaneState.RED_LANE,
        stop_conditions=["red_lane_active", "network_required"],
    )
    policy = select_backend_policy(route)

    assert policy.stop_conditions == ("red_lane_active", "network_required")


def test_policy_does_not_mutate_input_route() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    route = _safe_code_route()
    before = route.to_dict()
    select_backend_policy(route)

    assert route.to_dict() == before


def test_calling_policy_twice_returns_identical_decision() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    route = _safe_code_route()

    assert select_backend_policy(route) == select_backend_policy(route)


def test_classify_input_helper_matches_classify_then_select() -> None:
    from dopemux.dcp.routing_backend_policy import (
        select_backend_policy,
        select_backend_policy_for_input,
    )

    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.READ_ONLY,
        risk_class=RiskClass.R0_READ,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        runtime_impact=RuntimeImpact.READ_ONLY,
        has_unknown_authority=False,
    )

    assert select_backend_policy_for_input(inp) == select_backend_policy(
        classify_route(inp)
    )


def test_no_forbidden_imports_in_backend_policy_source() -> None:
    import dopemux.dcp.routing_backend_policy as mod

    source = inspect.getsource(mod)
    import_lines = [
        line.strip()
        for line in source.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    for forbidden in FORBIDDEN_IMPORTS_IN_POLICY:
        for line in import_lines:
            assert forbidden not in line, (
                f"Forbidden import '{forbidden}' found in backend policy: {line}"
            )


def test_no_callable_backend_references_are_stored() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    policy = select_backend_policy(_safe_code_route())

    assert not callable(policy.preferred_backend)
    assert all(not callable(backend) for backend in policy.fallback_backends)
    assert all(not callable(backend) for backend in policy.forbidden_backends)


def test_policy_does_not_expose_run_execute_dispatch_invoke_methods() -> None:
    import dopemux.dcp.routing_backend_policy as mod

    source = inspect.getsource(mod)
    for prefix in FORBIDDEN_METHOD_PREFIXES:
        assert prefix not in source


def test_policy_does_not_expose_merge_capability() -> None:
    import dopemux.dcp.routing_backend_policy as mod

    source = inspect.getsource(mod)
    assert "merge_pull_request" not in source
    assert "gh pr merge" not in source


def test_policy_handles_available_generic_backend_enum_members() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    policy = select_backend_policy(_safe_read_route())

    assert isinstance(policy.preferred_backend, BackendKind)


def test_policy_decision_is_serializable_with_asdict() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    d = asdict(select_backend_policy(_safe_read_route()))

    assert d["policy_status"] == "ALLOWED_POLICY"
    assert d["preferred_backend"] is BackendKind.CODEX


def test_route_evidence_and_stop_condition_tuples_are_caller_isolated() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    route = _safe_read_route()
    policy = select_backend_policy(route)
    route.evidence_refs.append("later")
    route.stop_conditions.append("later-stop")

    assert policy.evidence_refs == ()
    assert policy.stop_conditions == ()


def test_supervisor_audit_requirement_is_supervisor_policy() -> None:
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    route = _safe_code_route()
    route.audit_requirement = AuditRequirement.SUPERVISOR_AUDIT
    policy = select_backend_policy(route)

    assert policy.policy_status == "SUPERVISOR_POLICY"
    assert policy.preferred_backend is BackendKind.NONE
