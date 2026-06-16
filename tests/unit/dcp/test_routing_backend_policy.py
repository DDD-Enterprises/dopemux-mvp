"""Unit tests for DMX-DCP-MODEL-ROUTING-MVP-0003 backend policy data.

The backend policy layer is pure recommendation data. It must never turn a
non-runnable RouteDecision into an executable recommendation.
"""

from __future__ import annotations

import ast
import copy
import inspect

from dopemux.dcp.routing_classifier import (
    RoutingClassificationInput,
    classify_route,
)
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


def _safe_decision(**overrides: object) -> RouteDecision:
    values = {
        "route_id": "safe-route",
        "task_source": TaskSource.OPERATOR,
        "task_type": TaskType.CODE_CHANGE,
        "risk_class": RiskClass.R1_LOW,
        "complexity_class": ComplexityClass.LOW,
        "authority_class": AuthorityClass.OPERATOR,
        "runtime_impact": RuntimeImpact.LOCAL_ONLY,
        "backend_kind": BackendKind.NONE,
        "audit_requirement": AuditRequirement.SELF_CHECK,
        "escalation_requirement": EscalationRequirement.NONE,
        "red_lane_state": RedLaneState.CLEAR,
        "allowed_actions": ["edit_allowlisted_files", "run_targeted_tests"],
        "forbidden_actions": [],
        "stop_conditions": [],
        "evidence_refs": ["test-proof"],
        "unknowns": [],
        "confidence": "MEDIUM",
        "status": RouteStatus.ALLOWED,
    }
    values.update(overrides)
    return RouteDecision(**values)


def _recommend(decision: RouteDecision):
    from dopemux.dcp.routing_backend_policy import select_backend_policy

    return select_backend_policy(decision)


def _assert_no_backend(decision: RouteDecision, expected_reason: str) -> None:
    recommendation = _recommend(decision)
    assert recommendation.blocked is True
    assert recommendation.preferred_backend is BackendKind.NONE
    assert recommendation.fallback_backends == []
    assert recommendation.is_executable_recommendation() is False
    assert expected_reason in recommendation.reason_codes


def test_module_imports() -> None:
    import dopemux.dcp.routing_backend_policy as mod

    assert callable(mod.select_backend_policy)
    assert callable(mod.explain_backend_policy)


def test_default_route_decision_blocks_backend() -> None:
    _assert_no_backend(RouteDecision(), "route_status_not_allowed")


def test_red_lane_decision_blocks_backend() -> None:
    decision = _safe_decision(red_lane_state=RedLaneState.RED_LANE)
    _assert_no_backend(decision, "red_lane_active")


def test_unknown_red_lane_decision_blocks_backend() -> None:
    decision = _safe_decision(red_lane_state=RedLaneState.UNKNOWN)
    _assert_no_backend(decision, "red_lane_active")


def test_blocked_status_blocks_backend() -> None:
    decision = _safe_decision(status=RouteStatus.BLOCKED)
    _assert_no_backend(decision, "route_status_not_allowed")


def test_unknown_status_blocks_backend() -> None:
    decision = _safe_decision(status=RouteStatus.UNKNOWN)
    _assert_no_backend(decision, "route_status_not_allowed")


def test_pending_status_blocks_backend() -> None:
    decision = _safe_decision(status=RouteStatus.PENDING)
    _assert_no_backend(decision, "route_status_not_allowed")


def test_needs_supervisor_status_blocks_backend_and_marks_supervisor() -> None:
    decision = _safe_decision(status=RouteStatus.NEEDS_SUPERVISOR)
    recommendation = _recommend(decision)
    assert recommendation.blocked is True
    assert recommendation.requires_supervisor is True
    assert recommendation.preferred_backend is BackendKind.NONE
    assert "route_status_not_allowed" in recommendation.reason_codes


def test_escalation_always_blocks_backend() -> None:
    decision = _safe_decision(escalation_requirement=EscalationRequirement.ALWAYS)
    _assert_no_backend(decision, "escalation_required")


def test_unknown_escalation_blocks_backend() -> None:
    decision = _safe_decision(escalation_requirement=EscalationRequirement.UNKNOWN)
    _assert_no_backend(decision, "escalation_required")


def test_on_unknown_escalation_blocks_backend() -> None:
    decision = _safe_decision(escalation_requirement=EscalationRequirement.ON_UNKNOWN)
    _assert_no_backend(decision, "escalation_required")


def test_non_empty_unknowns_block_backend() -> None:
    decision = _safe_decision(unknowns=["authority_class_unknown"])
    _assert_no_backend(decision, "unknowns_present")


def test_reloaded_unknown_runtime_field_blocks_backend_without_unknowns_list() -> None:
    decision = RouteDecision.from_dict(
        {
            "route_id": "partial-safe-looking-route",
            "task_source": TaskSource.OPERATOR.value,
            "task_type": TaskType.CODE_CHANGE.value,
            "risk_class": RiskClass.R1_LOW.value,
            "complexity_class": ComplexityClass.LOW.value,
            "authority_class": AuthorityClass.OPERATOR.value,
            "red_lane_state": RedLaneState.CLEAR.value,
            "escalation_requirement": EscalationRequirement.NONE.value,
            "status": RouteStatus.ALLOWED.value,
        }
    )

    assert decision.unknowns == []
    assert decision.runtime_impact is RuntimeImpact.UNKNOWN
    _assert_no_backend(decision, "unknowns_present")


def test_reloaded_unknown_audit_requirement_blocks_backend_without_unknowns_list() -> None:
    decision = RouteDecision.from_dict(
        {
            "route_id": "partial-safe-looking-audit-route",
            "task_source": TaskSource.OPERATOR.value,
            "task_type": TaskType.CODE_CHANGE.value,
            "risk_class": RiskClass.R1_LOW.value,
            "complexity_class": ComplexityClass.LOW.value,
            "authority_class": AuthorityClass.OPERATOR.value,
            "runtime_impact": RuntimeImpact.LOCAL_ONLY.value,
            "red_lane_state": RedLaneState.CLEAR.value,
            "escalation_requirement": EscalationRequirement.NONE.value,
            "status": RouteStatus.ALLOWED.value,
        }
    )

    assert decision.unknowns == []
    assert decision.audit_requirement is AuditRequirement.UNKNOWN
    _assert_no_backend(decision, "unknowns_present")


def test_non_empty_stop_conditions_block_backend() -> None:
    decision = _safe_decision(stop_conditions=["operator_stop"])
    _assert_no_backend(decision, "stop_conditions_present")


def test_missing_proof_stop_condition_blocks_backend() -> None:
    decision = _safe_decision(stop_conditions=["missing_proof"])
    recommendation = _recommend(decision)
    assert recommendation.is_executable_recommendation() is False
    assert "missing_proof" in recommendation.reason_codes


def test_stale_proof_stop_condition_blocks_backend() -> None:
    decision = _safe_decision(stop_conditions=["stale_proof"])
    recommendation = _recommend(decision)
    assert recommendation.is_executable_recommendation() is False
    assert "stale_proof" in recommendation.reason_codes


def test_live_write_forbidden_action_blocks_backend() -> None:
    decision = _safe_decision(forbidden_actions=["live_write_to_service"])
    _assert_no_backend(decision, "forbidden_action_present")


def test_live_write_runtime_impact_blocks_backend_without_forbidden_action() -> None:
    decision = _safe_decision(runtime_impact=RuntimeImpact.LIVE_WRITE)
    _assert_no_backend(decision, "live_runtime_present")


def test_merge_task_type_blocks_backend_without_forbidden_action() -> None:
    decision = _safe_decision(task_type=TaskType.MERGE)
    _assert_no_backend(decision, "live_runtime_present")


def test_connector_forbidden_action_blocks_backend() -> None:
    decision = _safe_decision(forbidden_actions=["call_connector_live"])
    _assert_no_backend(decision, "forbidden_action_present")


def test_mcp_forbidden_action_blocks_backend() -> None:
    decision = _safe_decision(forbidden_actions=["call_mcp_live"])
    _assert_no_backend(decision, "forbidden_action_present")


def test_dopetask_forbidden_action_blocks_backend() -> None:
    decision = _safe_decision(forbidden_actions=["execute_dopetask_live"])
    _assert_no_backend(decision, "forbidden_action_present")


def test_safe_low_risk_code_route_prefers_codex_data() -> None:
    recommendation = _recommend(_safe_decision(task_type=TaskType.CODE_CHANGE))
    assert recommendation.blocked is False
    assert recommendation.preferred_backend is BackendKind.CODEX
    assert BackendKind.CLAUDE_CODE in recommendation.fallback_backends
    assert "safe_low_risk_code_route" in recommendation.reason_codes


def test_safe_classifier_code_route_ignores_baseline_guardrail_forbidden_actions() -> None:
    decision = classify_route(
        RoutingClassificationInput(
            task_source=TaskSource.OPERATOR,
            task_type=TaskType.CODE_CHANGE,
            risk_class=RiskClass.R1_LOW,
            complexity_class=ComplexityClass.LOW,
            authority_class=AuthorityClass.OPERATOR,
            runtime_impact=RuntimeImpact.LOCAL_ONLY,
            touches_files=True,
            touches_tests=True,
            has_unknown_authority=False,
            is_repo_changing=True,
            is_non_trivial=True,
        )
    )

    assert decision.is_runnable() is True
    assert "call_connector" in decision.forbidden_actions
    recommendation = _recommend(decision)
    assert recommendation.blocked is False
    assert recommendation.preferred_backend is BackendKind.CODEX
    assert "safe_low_risk_code_route" in recommendation.reason_codes


def test_safe_docs_route_prefers_codex_data() -> None:
    decision = _safe_decision(
        task_type=TaskType.DESIGN_ONLY,
        risk_class=RiskClass.R0_READ,
        runtime_impact=RuntimeImpact.READ_ONLY,
        allowed_actions=["inspect_runtime_code"],
    )
    recommendation = _recommend(decision)
    assert recommendation.preferred_backend is BackendKind.CODEX
    assert "safe_docs_route" in recommendation.reason_codes


def test_safe_audit_route_prefers_audit_capable_backend_data() -> None:
    decision = _safe_decision(
        task_type=TaskType.AUDIT,
        runtime_impact=RuntimeImpact.READ_ONLY,
        allowed_actions=["inspect_runtime_code"],
    )
    recommendation = _recommend(decision)
    assert recommendation.preferred_backend is BackendKind.AGY
    assert BackendKind.CLAUDE_CODE in recommendation.fallback_backends
    assert "safe_audit_route" in recommendation.reason_codes


def test_high_risk_route_requires_supervisor_and_no_backend() -> None:
    decision = _safe_decision(
        risk_class=RiskClass.R3_HIGH,
        status=RouteStatus.NEEDS_SUPERVISOR,
        escalation_requirement=EscalationRequirement.ON_RISK,
    )
    recommendation = _recommend(decision)
    assert recommendation.requires_supervisor is True
    assert recommendation.preferred_backend is BackendKind.NONE
    assert recommendation.is_executable_recommendation() is False
    assert "risk_requires_supervisor" in recommendation.reason_codes


def test_supervisor_audit_requirement_requires_supervisor_and_no_backend() -> None:
    decision = _safe_decision(audit_requirement=AuditRequirement.SUPERVISOR_AUDIT)
    recommendation = _recommend(decision)
    assert recommendation.requires_supervisor is True
    assert recommendation.preferred_backend is BackendKind.NONE
    assert recommendation.is_executable_recommendation() is False
    assert "risk_requires_supervisor" in recommendation.reason_codes


def test_unknown_backend_kind_on_safe_route_does_not_crash() -> None:
    decision = _safe_decision(backend_kind=BackendKind.UNKNOWN)
    recommendation = _recommend(decision)
    assert recommendation.preferred_backend in BackendKind
    assert recommendation.preferred_backend is not BackendKind.UNKNOWN


def test_policy_is_deterministic_for_identical_input() -> None:
    decision = _safe_decision()
    assert _recommend(decision) == _recommend(decision)


def test_recommendation_serializes_to_dict() -> None:
    recommendation = _recommend(_safe_decision())
    payload = recommendation.to_dict()
    assert payload["preferred_backend"] == BackendKind.CODEX.value
    assert payload["fallback_backends"]
    assert payload["blocked"] is False
    assert payload["policy_version"]


def test_recommendation_from_dict_round_trips() -> None:
    from dopemux.dcp.routing_backend_policy import BackendPolicyRecommendation

    recommendation = _recommend(_safe_decision())
    restored = BackendPolicyRecommendation.from_dict(recommendation.to_dict())
    assert restored == recommendation


def test_backend_policy_does_not_mutate_route_decision() -> None:
    decision = _safe_decision()
    before = copy.deepcopy(decision)
    _recommend(decision)
    assert decision == before


def test_policy_module_has_no_forbidden_imports() -> None:
    import dopemux.dcp.routing_backend_policy as mod

    forbidden = {
        "sub" + "process",
        "req" + "uests",
        "ht" + "tpx",
        "url" + "lib",
        "sock" + "et",
        "github",
        "docker",
        "task_" + "orchestrator",
        "dopetask",
    }
    tree = ast.parse(inspect.getsource(mod))
    imports = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    imported_modules = []
    for node in imports:
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif node.module:
            imported_modules.append(node.module)
    assert not any(
        module == name or module.startswith(f"{name}.")
        for module in imported_modules
        for name in forbidden
    )


def test_policy_module_exposes_no_execution_methods() -> None:
    import dopemux.dcp.routing_backend_policy as mod

    forbidden_names = {"run", "execute", "dispatch", "invoke", "call", "merge", "push"}
    exported_callables = {
        name for name in mod.__all__ if callable(getattr(mod, name, None))
    }
    assert exported_callables.isdisjoint(forbidden_names)


def test_preferred_backend_is_plain_enum_data() -> None:
    recommendation = _recommend(_safe_decision())
    assert isinstance(recommendation.preferred_backend, BackendKind)
    assert not callable(recommendation.preferred_backend)


def test_fallback_backends_are_plain_enum_data() -> None:
    recommendation = _recommend(_safe_decision())
    assert all(isinstance(item, BackendKind) for item in recommendation.fallback_backends)
    assert not any(callable(item) for item in recommendation.fallback_backends)


def test_blocked_decision_has_stable_non_empty_reason_codes() -> None:
    recommendation = _recommend(RouteDecision())
    assert recommendation.reason_codes
    assert recommendation.reason_codes == sorted(set(recommendation.reason_codes))


def test_safe_route_reason_code_explains_match() -> None:
    recommendation = _recommend(_safe_decision(task_type=TaskType.PROOF_BUNDLE))
    assert recommendation.reason_codes == ["safe_low_risk_code_route"]


def test_no_policy_match_returns_blocked_default_recommendation() -> None:
    decision = _safe_decision(task_type=TaskType.READ_ONLY)
    recommendation = _recommend(decision)
    assert recommendation.blocked is True
    assert recommendation.preferred_backend is BackendKind.NONE
    assert recommendation.reason_codes == ["no_policy_match"]


def test_tests_cover_current_backend_enum_members() -> None:
    assert {member.value for member in BackendKind} == {
        "CODEX",
        "CLAUDE_CODE",
        "OPENCODE",
        "GROK",
        "GEMINI_CLI",
        "AGY",
        "LOCAL_SCRIPT",
        "NONE",
        "UNKNOWN",
    }


def test_red_lane_route_can_never_be_executable_recommendation() -> None:
    decision = _safe_decision(
        status=RouteStatus.ALLOWED,
        red_lane_state=RedLaneState.RED_LANE,
        risk_class=RiskClass.RED_LANE,
    )
    assert decision.is_runnable() is False
    assert _recommend(decision).is_executable_recommendation() is False
