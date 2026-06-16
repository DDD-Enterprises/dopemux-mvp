"""Unit tests for DMX-DCP-MODEL-ROUTING-MVP-0005 lane engine.

14 required tests (numbered per spec):
1.  test_blocked_route_maps_to_blocked_lane_not_executable
2.  test_red_lane_mcp_route_blocked_no_facade_bypass
3.  test_live_write_route_blocked
4.  test_dopetask_execution_route_blocked
5.  test_unknown_authority_route_non_mutating_not_executable
6.  test_docs_only_safe_route_maps_to_docs_only
7.  test_proof_only_fresh_proof_route  + test_proof_only_stale_proof_is_blocked
8.  test_classifier_routing_task_maps_to_classifier_routing
9.  test_test_validation_task_maps_to_test_validation
10. test_local_code_implementation_preserves_audit
11. test_external_intake_no_execution

Structural guards:
12. test_allowed_actions_never_widen_decision
13. test_no_forbidden_imports_in_lane_engine_source
14. test_lane_engine_does_not_mutate_inputs
"""

from __future__ import annotations

import inspect

from dopemux.dcp.lane_engine import decide_lane
from dopemux.dcp.lane_model import LaneKind
from dopemux.dcp.routing_classifier import (
    RoutingClassificationInput,
    classify_route,
)
from dopemux.dcp.routing_model import (
    AuditRequirement,
    AuthorityClass,
    ComplexityClass,
    RedLaneState,
    RiskClass,
    RouteDecision,
    RouteStatus,
    RuntimeImpact,
    TaskSource,
    TaskType,
)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

FORBIDDEN_IMPORTS_IN_LANE_ENGINE = {
    "subprocess",
    "socket",
    "requests",
    "httpx",
    "urllib.request",
    "opencode",
    "grok",
    "github",
    "docker",
    "conport",
    "dope_memory",
    "dope_context",
    "task_orchestrator",
    "dopetask",
    "mcp.tool",
    "GraphQL",
    "runner",
    "connector",
}

# An operator input that is safe, ALLOWED, mutating, non-trivial code change.
def _safe_code_change_input(
    *,
    task_type: TaskType = TaskType.CODE_CHANGE,
    task_source: TaskSource = TaskSource.OPERATOR,
    risk_class: RiskClass = RiskClass.R1_LOW,
    runtime_impact: RuntimeImpact = RuntimeImpact.LOCAL_ONLY,
    complexity_class: ComplexityClass = ComplexityClass.LOW,
    authority_class: AuthorityClass = AuthorityClass.OPERATOR,
    is_non_trivial: bool = True,
    is_repo_changing: bool = True,
    touches_files: bool = True,
    **kwargs: object,
) -> RoutingClassificationInput:
    return RoutingClassificationInput(
        task_source=task_source,
        task_type=task_type,
        risk_class=risk_class,
        runtime_impact=runtime_impact,
        complexity_class=complexity_class,
        authority_class=authority_class,
        is_non_trivial=is_non_trivial,
        is_repo_changing=is_repo_changing,
        touches_files=touches_files,
        has_unknown_authority=False,
        has_conflicting_evidence=False,
        has_stale_proof=False,
        has_missing_proof=False,
        **kwargs,
    )


# ─────────────────────────────────────────────
# Test 1 — BLOCKED route → LaneKind.BLOCKED, not executable, allowed_actions=()
# ─────────────────────────────────────────────


def test_blocked_route_maps_to_blocked_lane_not_executable() -> None:
    """A stale-proof route (BLOCKED by classifier) → LaneKind.BLOCKED, not executable."""
    inp = RoutingClassificationInput(
        has_stale_proof=True,
        task_type=TaskType.CODE_CHANGE,
        is_repo_changing=True,
    )
    decision = classify_route(inp)
    assert decision.status is RouteStatus.BLOCKED  # pre-condition

    lane_decision = decide_lane(decision, inp)

    assert lane_decision.lane is LaneKind.BLOCKED
    assert lane_decision.is_executable is False
    assert lane_decision.allowed_actions == ()


# ─────────────────────────────────────────────
# Test 2 — requires_mcp_call → BLOCKED, no SECURE_MCP_FACADE bypass
# ─────────────────────────────────────────────


def test_red_lane_mcp_route_blocked_no_facade_bypass() -> None:
    """requires_mcp_call → RED_LANE → LaneKind.BLOCKED; no SECURE_MCP_FACADE produced."""
    inp = RoutingClassificationInput(
        requires_mcp_call=True,
        task_type=TaskType.READ_ONLY,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.red_lane_state is RedLaneState.RED_LANE  # pre-condition

    lane_decision = decide_lane(decision, inp)

    assert lane_decision.lane is LaneKind.BLOCKED
    assert lane_decision.is_executable is False
    # Must not be the Secure-MCP-Facade lane — that lane is never even defined.
    assert not hasattr(LaneKind, "SECURE_MCP_FACADE")
    # The MCP tokens must appear somewhere in forbidden_actions
    forbidden_str = " ".join(lane_decision.forbidden_actions)
    assert "mcp" in forbidden_str or "call_mcp" in forbidden_str


def test_executability_gate_mirrors_is_runnable_on_forged_decision() -> None:
    """Defense-in-depth (audit RISK-1): a RouteDecision with ALLOWED status +
    CLEAR red-lane but BLOCKED/UNKNOWN authority — constructible via from_dict,
    never emitted by classify_route — must NOT be executable. The lane gate
    delegates to RouteDecision.is_runnable(), which fail-closes on authority.
    """
    inp = RoutingClassificationInput(
        task_type=TaskType.CODE_CHANGE,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    for bad_authority in (AuthorityClass.BLOCKED, AuthorityClass.UNKNOWN):
        forged = RouteDecision.from_dict(
            {
                "status": "ALLOWED",
                "red_lane_state": "CLEAR",
                "authority_class": bad_authority.value,
                "allowed_actions": ["edit_allowlisted_files"],
            }
        )
        assert forged.is_runnable() is False  # is_runnable already fail-closes
        lane_decision = decide_lane(forged, inp)
        assert lane_decision.is_executable is False, (
            f"forged ALLOWED + {bad_authority.value} authority must not be executable"
        )


def test_non_runnable_lane_strips_mutating_allowed_actions_from_forged_decision() -> None:
    """P2 regression: forged/restored RouteDecision with ALLOWED + CLEAR red-lane
    but UNKNOWN/BLOCKED authority must not expose mutating allowed_actions even when
    those actions are present on the source decision.
    """
    inp = RoutingClassificationInput(
        task_type=TaskType.CODE_CHANGE,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    mutating_actions = [
        "edit_allowlisted_files",
        "open_pr",
        "run_embedded_audit",
        "run_targeted_tests",
        "capture_proof",
    ]
    mutating_tokens = {"edit_allowlisted_files", "open_pr", "run_embedded_audit"}

    for bad_authority in (AuthorityClass.BLOCKED, AuthorityClass.UNKNOWN):
        forged = RouteDecision.from_dict(
            {
                "status": "ALLOWED",
                "red_lane_state": "CLEAR",
                "authority_class": bad_authority.value,
                "allowed_actions": mutating_actions,
            }
        )
        lane_decision = decide_lane(forged, inp)

        assert lane_decision.is_executable is False
        for action in lane_decision.allowed_actions:
            assert action not in mutating_tokens, (
                f"non-runnable lane must not expose mutating action '{action}' "
                f"for authority={bad_authority.value}"
            )


def test_lane_assignment_uses_normalized_enums_for_string_inputs() -> None:
    """Audit P2 (codex thread): decide_lane must classify the lane from the
    decision's NORMALIZED enums. classify_route tolerates string enum inputs;
    the lane KIND must still be correct (not fall through to the fallback).
    """
    inp = RoutingClassificationInput(
        task_type="AUDIT",  # string, not TaskType.AUDIT — classifier normalizes it
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.task_type is TaskType.AUDIT  # classifier normalized it

    lane_decision = decide_lane(decision, inp)
    assert lane_decision.lane is LaneKind.EMBEDDED_AUDIT


# ─────────────────────────────────────────────
# Test 3 — requires_live_write → BLOCKED, not executable
# ─────────────────────────────────────────────


def test_live_write_route_blocked() -> None:
    """requires_live_write → RED_LANE → LaneKind.BLOCKED, not executable."""
    inp = RoutingClassificationInput(
        requires_live_write=True,
    )
    decision = classify_route(inp)
    assert decision.red_lane_state is RedLaneState.RED_LANE  # pre-condition

    lane_decision = decide_lane(decision, inp)

    assert lane_decision.lane is LaneKind.BLOCKED
    assert lane_decision.is_executable is False


# ─────────────────────────────────────────────
# Test 4 — requires_dopetask_execution → BLOCKED, dopetask in forbidden_actions
# ─────────────────────────────────────────────


def test_dopetask_execution_route_blocked() -> None:
    """requires_dopetask_execution → RED_LANE → LaneKind.BLOCKED; dopetask in forbidden."""
    inp = RoutingClassificationInput(
        requires_dopetask_execution=True,
    )
    decision = classify_route(inp)
    assert decision.red_lane_state is RedLaneState.RED_LANE  # pre-condition

    lane_decision = decide_lane(decision, inp)

    assert lane_decision.lane is LaneKind.BLOCKED
    assert lane_decision.is_executable is False
    assert any("dopetask" in action for action in lane_decision.forbidden_actions)


# ─────────────────────────────────────────────
# Test 5 — Unknown authority → not executable, no mutating tokens in allowed_actions
# ─────────────────────────────────────────────


def test_unknown_authority_route_non_mutating_not_executable() -> None:
    """Default input (unknown authority) → not executable AND no mutating token in allowed_actions."""
    inp = RoutingClassificationInput(
        has_unknown_authority=True,
        authority_class=AuthorityClass.UNKNOWN,
    )
    decision = classify_route(inp)
    # status should be UNKNOWN (not BLOCKED) given no hard block
    assert decision.status is RouteStatus.UNKNOWN
    assert not decision.is_runnable()

    lane_decision = decide_lane(decision, inp)

    assert lane_decision.is_executable is False
    mutating_tokens = {"edit_allowlisted_files", "open_pr", "run_embedded_audit"}
    for action in lane_decision.allowed_actions:
        assert action not in mutating_tokens, (
            f"Mutation action '{action}' must not be allowed under unknown authority"
        )


# ─────────────────────────────────────────────
# Test 6 — Safe docs-only route → LaneKind.DOCS_ONLY
# ─────────────────────────────────────────────


def test_docs_only_safe_route_maps_to_docs_only() -> None:
    """A safe docs-only route (OPERATOR, known dims, touches_docs, not code/test) → DOCS_ONLY."""
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.DESIGN_ONLY,
        risk_class=RiskClass.R0_READ,
        runtime_impact=RuntimeImpact.READ_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        has_conflicting_evidence=False,
        has_stale_proof=False,
        has_missing_proof=False,
        touches_docs=True,
        touches_files=False,
        touches_tests=False,
        touches_ci=False,
        touches_security=False,
        touches_auth=False,
        touches_secrets=False,
        requires_live_write=False,
        requires_runner_execution=False,
        requires_connector_call=False,
        requires_mcp_call=False,
        requires_dopetask_execution=False,
        requires_task_orchestrator_write=False,
    )
    decision = classify_route(inp)

    lane_decision = decide_lane(decision, inp)

    assert lane_decision.lane is LaneKind.DOCS_ONLY


# ─────────────────────────────────────────────
# Test 7a — Fresh PROOF_BUNDLE → LaneKind.PROOF_ONLY
# ─────────────────────────────────────────────


def test_proof_only_fresh_proof_route() -> None:
    """A safe PROOF_BUNDLE task (no stale/missing proof, OPERATOR) → LaneKind.PROOF_ONLY."""
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.PROOF_BUNDLE,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.LOCAL_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        has_conflicting_evidence=False,
        has_stale_proof=False,
        has_missing_proof=False,
        touches_files=True,
        is_repo_changing=True,
    )
    decision = classify_route(inp)
    # Must be ALLOWED for the lane to be PROOF_ONLY (not BLOCKED)
    assert decision.status is RouteStatus.ALLOWED, (
        f"expected ALLOWED for fresh-proof input, got {decision.status}"
    )

    lane_decision = decide_lane(decision, inp)

    assert lane_decision.lane is LaneKind.PROOF_ONLY


# ─────────────────────────────────────────────
# Test 7b — Stale proof → LaneKind.BLOCKED (not PROOF_ONLY)
# ─────────────────────────────────────────────


def test_proof_only_stale_proof_is_blocked() -> None:
    """Stale proof is BLOCKED by classifier; must map to LaneKind.BLOCKED, not PROOF_ONLY."""
    inp = RoutingClassificationInput(
        task_type=TaskType.PROOF_BUNDLE,
        has_stale_proof=True,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.status is RouteStatus.BLOCKED  # pre-condition

    lane_decision = decide_lane(decision, inp)

    assert lane_decision.lane is LaneKind.BLOCKED
    assert lane_decision.lane is not LaneKind.PROOF_ONLY


# ─────────────────────────────────────────────
# Test 8 — DESIGN_ONLY → LaneKind.CLASSIFIER_ROUTING
# ─────────────────────────────────────────────


def test_classifier_routing_task_maps_to_classifier_routing() -> None:
    """A safe DESIGN_ONLY routing task → LaneKind.CLASSIFIER_ROUTING."""
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.DESIGN_ONLY,
        risk_class=RiskClass.R0_READ,
        runtime_impact=RuntimeImpact.READ_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        has_conflicting_evidence=False,
        has_stale_proof=False,
        has_missing_proof=False,
        # No docs, files, tests: pure design
        touches_docs=False,
        touches_files=False,
        touches_tests=False,
    )
    decision = classify_route(inp)

    lane_decision = decide_lane(decision, inp)

    assert lane_decision.lane is LaneKind.CLASSIFIER_ROUTING


# ─────────────────────────────────────────────
# Test 9 — touches_tests + not touches_files → LaneKind.TEST_VALIDATION
# ─────────────────────────────────────────────


def test_test_validation_task_maps_to_test_validation() -> None:
    """touches_tests=True, touches_files=False → LaneKind.TEST_VALIDATION."""
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.LOCAL_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        has_conflicting_evidence=False,
        has_stale_proof=False,
        has_missing_proof=False,
        touches_tests=True,
        touches_files=False,
    )
    decision = classify_route(inp)

    lane_decision = decide_lane(decision, inp)

    assert lane_decision.lane is LaneKind.TEST_VALIDATION


# ─────────────────────────────────────────────
# Test 10 — Non-trivial CODE_CHANGE → LOCAL_CODE_IMPLEMENTATION, audit preserved
# ─────────────────────────────────────────────


def test_local_code_implementation_preserves_audit() -> None:
    """Non-trivial repo-changing CODE_CHANGE → LOCAL_CODE_IMPLEMENTATION; audit_requirement preserved."""
    inp = _safe_code_change_input(
        task_type=TaskType.CODE_CHANGE,
        is_non_trivial=True,
        is_repo_changing=True,
        touches_files=True,
    )
    decision = classify_route(inp)
    assert decision.status is RouteStatus.ALLOWED

    lane_decision = decide_lane(decision, inp)

    assert lane_decision.lane is LaneKind.LOCAL_CODE_IMPLEMENTATION
    # audit_requirement must be inherited, not flattened
    assert lane_decision.audit_requirement == decision.audit_requirement
    assert lane_decision.audit_requirement in (
        AuditRequirement.EMBEDDED_AUDITOR,
        AuditRequirement.SUPERVISOR_AUDIT,
        AuditRequirement.SELF_CHECK,
        AuditRequirement.DISTINCT_AUDITOR,
    )


def test_repo_changing_read_only_without_file_touch_maps_to_implementation() -> None:
    """Repo-changing scope must not fall through to READ_ONLY_EVIDENCE."""
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.READ_ONLY,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.READ_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        is_repo_changing=True,
        touches_files=False,
    )
    decision = classify_route(inp)

    lane_decision = decide_lane(decision, inp)

    assert lane_decision.lane is LaneKind.LOCAL_CODE_IMPLEMENTATION
    assert "fallback_read_only_evidence" not in lane_decision.rationale


def test_file_touching_read_only_maps_to_implementation() -> None:
    """File-touching scope must not be classified as evidence-only work."""
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.READ_ONLY,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.READ_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        is_repo_changing=False,
        touches_files=True,
    )
    decision = classify_route(inp)

    lane_decision = decide_lane(decision, inp)

    assert lane_decision.lane is LaneKind.LOCAL_CODE_IMPLEMENTATION
    assert "fallback_read_only_evidence" not in lane_decision.rationale


def test_pr_steward_readiness_does_not_override_mutating_scope() -> None:
    """PR readiness must not inherit mutating scope or mutating requested actions."""
    inp = _safe_code_change_input(
        requested_actions=["pr_steward_readiness", "open_pr"],
    )
    decision = classify_route(inp)
    assert decision.is_runnable()

    lane_decision = decide_lane(decision, inp)

    assert lane_decision.lane is LaneKind.LOCAL_CODE_IMPLEMENTATION
    assert lane_decision.lane is not LaneKind.PR_STEWARD_READINESS


def test_restored_decision_with_unknown_contract_fields_not_executable() -> None:
    """Restored ALLOWED decisions with UNKNOWN defaults must fail closed."""
    inp = _safe_code_change_input()
    restored = RouteDecision.from_dict(
        {
            "status": "ALLOWED",
            "red_lane_state": "CLEAR",
            "authority_class": "OPERATOR",
            "allowed_actions": ["edit_allowlisted_files"],
        }
    )
    assert restored.is_runnable()

    lane_decision = decide_lane(restored, inp)

    assert lane_decision.is_executable is False
    assert "edit_allowlisted_files" not in lane_decision.allowed_actions


def test_restored_decision_with_unknown_proof_requirement_not_executable() -> None:
    """UNKNOWN proof requirements from restored decisions must fail closed."""
    inp = _safe_code_change_input()
    restored = RouteDecision.from_dict(
        {
            "status": "ALLOWED",
            "red_lane_state": "CLEAR",
            "authority_class": "OPERATOR",
            "task_source": "OPERATOR",
            "task_type": "CODE_CHANGE",
            "risk_class": "R1_LOW",
            "complexity_class": "LOW",
            "runtime_impact": "LOCAL_ONLY",
            "proof_requirements": ["UNKNOWN"],
            "audit_requirement": "SELF_CHECK",
            "escalation_requirement": "NONE",
            "allowed_actions": ["edit_allowlisted_files"],
        }
    )
    assert restored.is_runnable()

    lane_decision = decide_lane(restored, inp)

    assert lane_decision.is_executable is False
    assert "edit_allowlisted_files" not in lane_decision.allowed_actions


# ─────────────────────────────────────────────
# Test 11 — External intake READ_ONLY evidence → EXTERNAL_INTAKE, not executable
# ─────────────────────────────────────────────


def test_external_intake_no_execution() -> None:
    """External-agent READ_ONLY with evidence_refs → LaneKind.EXTERNAL_INTAKE, not executable."""
    # Build an input that truly hits EXTERNAL_INTAKE row: external agent, READ_ONLY, evidence, no scope
    inp_external = RoutingClassificationInput(
        task_source=TaskSource.CODEX,
        task_type=TaskType.READ_ONLY,
        risk_class=RiskClass.R0_READ,
        runtime_impact=RuntimeImpact.READ_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        has_conflicting_evidence=False,
        has_stale_proof=False,
        has_missing_proof=False,
        evidence_refs=["proof/abc.json"],
        touches_files=False,
        touches_tests=False,
        touches_docs=False,
        is_repo_changing=False,
        # no requested_actions that are pr_steward_readiness
    )
    decision = classify_route(inp_external)

    lane_decision = decide_lane(decision, inp_external)

    assert lane_decision.lane is LaneKind.EXTERNAL_INTAKE
    assert lane_decision.is_executable is False
    disallowed = {"execute", "import", "install"}
    for action in lane_decision.allowed_actions:
        assert action not in disallowed, (
            f"EXTERNAL_INTAKE must not permit '{action}' in allowed_actions"
        )


# ─────────────────────────────────────────────
# Test 12 — allowed_actions never widen decision.allowed_actions
# ─────────────────────────────────────────────


def test_allowed_actions_never_widen_decision() -> None:
    """For a sample of routes: set(lane.allowed_actions) ⊆ set(decision.allowed_actions)."""
    sample_inputs = [
        RoutingClassificationInput(),  # all-default
        RoutingClassificationInput(
            task_source=TaskSource.OPERATOR,
            task_type=TaskType.READ_ONLY,
            risk_class=RiskClass.R0_READ,
            runtime_impact=RuntimeImpact.READ_ONLY,
            complexity_class=ComplexityClass.LOW,
            authority_class=AuthorityClass.OPERATOR,
            has_unknown_authority=False,
        ),
        _safe_code_change_input(),
        RoutingClassificationInput(
            task_type=TaskType.PROOF_BUNDLE,
            task_source=TaskSource.OPERATOR,
            risk_class=RiskClass.R1_LOW,
            runtime_impact=RuntimeImpact.LOCAL_ONLY,
            complexity_class=ComplexityClass.LOW,
            authority_class=AuthorityClass.OPERATOR,
            has_unknown_authority=False,
            touches_files=True,
        ),
        RoutingClassificationInput(has_stale_proof=True),
        RoutingClassificationInput(requires_mcp_call=True),
    ]
    for inp in sample_inputs:
        decision = classify_route(inp)
        lane_decision = decide_lane(decision, inp)
        lane_set = set(lane_decision.allowed_actions)
        decision_set = set(decision.allowed_actions)
        assert lane_set <= decision_set, (
            f"allowed_actions widened: lane={lane_set - decision_set} not in decision={decision_set}"
        )


# ─────────────────────────────────────────────
# Test 13 — No forbidden imports in lane_engine source
# ─────────────────────────────────────────────


def test_no_forbidden_imports_in_lane_engine_source() -> None:
    """Lane engine source must not import subprocess, socket, requests, httpx, mcp, connector, runner, etc."""
    import dopemux.dcp.lane_engine as mod

    source = inspect.getsource(mod)
    import_lines = [
        line.strip()
        for line in source.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    for forbidden in FORBIDDEN_IMPORTS_IN_LANE_ENGINE:
        for line in import_lines:
            # Allow "runner" as a comment or string, only check import lines
            assert forbidden not in line, (
                f"Forbidden import '{forbidden}' found in lane_engine: {line}"
            )


# ─────────────────────────────────────────────
# Test 14 — decide_lane does not mutate inputs
# ─────────────────────────────────────────────


def test_lane_engine_does_not_mutate_inputs() -> None:
    """decide_lane must not mutate decision or classification_input."""
    inp = RoutingClassificationInput(
        is_non_trivial=True,
        touches_tests=False,
        evidence_refs=["ref1", "ref2"],
        touches_files=True,
        is_repo_changing=True,
    )
    decision = classify_route(inp)

    # Deep-copy decision's mutable state to compare after
    original_allowed = list(decision.allowed_actions)
    original_forbidden = list(decision.forbidden_actions)
    original_stop = list(decision.stop_conditions)
    original_refs = list(inp.evidence_refs)
    original_non_trivial = inp.is_non_trivial

    decide_lane(decision, inp)

    # decision not mutated
    assert decision.allowed_actions == original_allowed
    assert decision.forbidden_actions == original_forbidden
    assert decision.stop_conditions == original_stop
    # inp not mutated
    assert inp.evidence_refs == original_refs
    assert inp.is_non_trivial == original_non_trivial
