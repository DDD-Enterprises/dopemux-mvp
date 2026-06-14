"""Unit tests for DMX-DCP-MODEL-ROUTING-MVP-0002 routing classifier.

Coverage targets:
- Import and module purity
- Default input yields non-runnable decision
- Unknown authority blocks
- Missing proof blocks repo-changing non-trivial task
- Conflicting evidence triggers escalation
- Secret/auth/security-touching tasks → RED_LANE
- CI-touching task → audit/proof/escalation required
- Live-write/connector/MCP/dopetask/runner/task-orchestrator requests → forbidden
- Simple docs-only task avoids RED_LANE
- Non-trivial repo-changing task → embedded audit required
- High-risk → supervisor escalation
- Backend/connector are data only
- Evidence refs and unknowns preserved
- Allowed/forbidden action content
- is_red_lane() and is_blocked() semantics
- String enum fallback
- Serialization round-trip
- CI-repair classified as proof/audit required, not blocked by red-lane
- PR merge forbidden
- Input immutability
- No forbidden imports or methods in classifier source
"""

from __future__ import annotations

import inspect

import pytest

from dopemux.dcp.routing_classifier import (
    RoutingClassificationInput,
    classify_route,
)
from dopemux.dcp.routing_model import (
    AuditRequirement,
    AuthorityClass,
    BackendKind,
    ComplexityClass,
    ConnectorKind,
    EscalationRequirement,
    ProofRequirement,
    RedLaneState,
    RiskClass,
    RouteDecision,
    RouteStatus,
    RuntimeImpact,
    TaskType,
)

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

FORBIDDEN_IMPORTS_IN_CLASSIFIER = {
    "subprocess",
    "requests",
    "httpx",
    "urllib.request",
    "socket",
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
}

FORBIDDEN_METHODS = {
    "run(",
    "execute(",
    "dispatch(",
    "call(",
    "merge(",
    "push(",
    "invoke(",
}


def _default() -> RoutingClassificationInput:
    """Return the most conservative (all-default) input."""
    return RoutingClassificationInput()


def _is_runnable(decision: RouteDecision) -> bool:
    """Use the authoritative model method — fail-closed on UNKNOWN red-lane."""
    return decision.is_runnable()


# ─────────────────────────────────────────────
# Test 1 — Import classifier module
# ─────────────────────────────────────────────


def test_import_classifier_module() -> None:
    """Classifier module and main entry point are importable."""
    import dopemux.dcp.routing_classifier as mod

    assert callable(mod.classify_route)
    assert hasattr(mod, "RoutingClassificationInput")


# ─────────────────────────────────────────────
# Test 2 — Default input → non-runnable
# ─────────────────────────────────────────────


def test_default_input_is_non_runnable() -> None:
    """All-default input must not produce a runnable decision."""
    decision = classify_route(_default())
    assert not _is_runnable(decision)


# ─────────────────────────────────────────────
# Test 3 — Unknown authority blocks
# ─────────────────────────────────────────────


def test_unknown_authority_blocks() -> None:
    inp = RoutingClassificationInput(
        has_unknown_authority=True,
        authority_class=AuthorityClass.UNKNOWN,
    )
    decision = classify_route(inp)
    assert decision.is_blocked() or decision.is_red_lane() or decision.status is RouteStatus.UNKNOWN


# ─────────────────────────────────────────────
# Test 4 — Missing proof blocks repo-changing non-trivial task
# ─────────────────────────────────────────────


def test_missing_proof_blocks_repo_changing_nontrivial() -> None:
    inp = RoutingClassificationInput(
        is_repo_changing=True,
        is_non_trivial=True,
        has_missing_proof=True,
    )
    decision = classify_route(inp)
    assert not _is_runnable(decision)


# ─────────────────────────────────────────────
# Test 5 — Conflicting evidence triggers escalation
# ─────────────────────────────────────────────


def test_conflicting_evidence_triggers_escalation() -> None:
    inp = RoutingClassificationInput(has_conflicting_evidence=True)
    decision = classify_route(inp)
    # Conflicting evidence must trigger the highest escalation level.
    assert decision.escalation_requirement is EscalationRequirement.ALWAYS


# ─────────────────────────────────────────────
# Test 6 — Secret-touching → RED_LANE
# ─────────────────────────────────────────────


def test_secrets_touching_is_red_lane() -> None:
    inp = RoutingClassificationInput(touches_secrets=True)
    decision = classify_route(inp)
    assert decision.is_red_lane()
    assert decision.red_lane_state is RedLaneState.RED_LANE


# ─────────────────────────────────────────────
# Test 7 — Auth-touching → RED_LANE
# ─────────────────────────────────────────────


def test_auth_touching_is_red_lane() -> None:
    inp = RoutingClassificationInput(touches_auth=True)
    decision = classify_route(inp)
    assert decision.is_red_lane()


# ─────────────────────────────────────────────
# Test 8 — Security-touching → RED_LANE
# ─────────────────────────────────────────────


def test_security_touching_is_red_lane() -> None:
    inp = RoutingClassificationInput(touches_security=True)
    decision = classify_route(inp)
    assert decision.is_red_lane()


# ─────────────────────────────────────────────
# Test 9 — CI-touching → audit/proof/escalation
# ─────────────────────────────────────────────


def test_ci_touching_requires_audit_proof_escalation() -> None:
    inp = RoutingClassificationInput(touches_ci=True)
    decision = classify_route(inp)
    assert decision.audit_requirement is not AuditRequirement.NONE
    assert decision.proof_requirements  # non-empty
    assert decision.escalation_requirement is not EscalationRequirement.NONE


# ─────────────────────────────────────────────
# Test 10 — Live-write → forbidden
# ─────────────────────────────────────────────


def test_live_write_is_forbidden() -> None:
    inp = RoutingClassificationInput(requires_live_write=True)
    decision = classify_route(inp)
    assert not _is_runnable(decision)
    assert any("live_write" in a or "write" in a for a in decision.forbidden_actions)


# ─────────────────────────────────────────────
# Test 11 — Connector call → forbidden
# ─────────────────────────────────────────────


def test_connector_call_is_forbidden() -> None:
    inp = RoutingClassificationInput(requires_connector_call=True)
    decision = classify_route(inp)
    assert not _is_runnable(decision)
    assert any("connector" in a for a in decision.forbidden_actions)


# ─────────────────────────────────────────────
# Test 12 — MCP call → forbidden
# ─────────────────────────────────────────────


def test_mcp_call_is_forbidden() -> None:
    inp = RoutingClassificationInput(requires_mcp_call=True)
    decision = classify_route(inp)
    assert not _is_runnable(decision)
    assert any("mcp" in a for a in decision.forbidden_actions)


# ─────────────────────────────────────────────
# Test 13 — Dopetask execution → forbidden
# ─────────────────────────────────────────────


def test_dopetask_execution_is_forbidden() -> None:
    inp = RoutingClassificationInput(requires_dopetask_execution=True)
    decision = classify_route(inp)
    assert not _is_runnable(decision)
    assert any("dopetask" in a for a in decision.forbidden_actions)


# ─────────────────────────────────────────────
# Test 14 — Task Orchestrator write → forbidden
# ─────────────────────────────────────────────


def test_task_orchestrator_write_is_forbidden() -> None:
    inp = RoutingClassificationInput(requires_task_orchestrator_write=True)
    decision = classify_route(inp)
    assert not _is_runnable(decision)
    assert any("orchestrator" in a or "task_orchestrator" in a for a in decision.forbidden_actions)


# ─────────────────────────────────────────────
# Test 15 — Runner execution → forbidden
# ─────────────────────────────────────────────


def test_runner_execution_is_forbidden() -> None:
    inp = RoutingClassificationInput(requires_runner_execution=True)
    decision = classify_route(inp)
    assert not _is_runnable(decision)
    assert any("runner" in a or "execute_runner" in a for a in decision.forbidden_actions)


# ─────────────────────────────────────────────
# Test 16 — Simple docs-only low-risk avoids RED_LANE
# ─────────────────────────────────────────────


def test_simple_docs_only_avoids_red_lane() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.DESIGN_ONLY,
        risk_class=RiskClass.R0_READ,
        touches_docs=True,
        touches_files=False,
        touches_tests=False,
        touches_ci=False,
        touches_security=False,
        touches_auth=False,
        touches_secrets=False,
        touches_destructive_path=False,
        requires_network=False,
        requires_live_write=False,
        requires_runner_execution=False,
        requires_connector_call=False,
        requires_mcp_call=False,
        requires_dopetask_execution=False,
        requires_task_orchestrator_write=False,
        requires_external_service=False,
        has_unknown_authority=False,
        has_conflicting_evidence=False,
        is_non_trivial=False,
        is_repo_changing=False,
        authority_class=AuthorityClass.AUTOMATED_SAFE,
    )
    decision = classify_route(inp)
    assert not decision.is_red_lane()


# ─────────────────────────────────────────────
# Test 17 — Simple unit-test-only → proof required, no RED_LANE
# ─────────────────────────────────────────────


def test_unit_test_task_requires_proof_no_red_lane() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        touches_tests=True,
        touches_ci=False,
        touches_security=False,
        touches_auth=False,
        touches_secrets=False,
        touches_destructive_path=False,
        requires_live_write=False,
        requires_runner_execution=False,
        requires_connector_call=False,
        requires_mcp_call=False,
        requires_dopetask_execution=False,
        requires_task_orchestrator_write=False,
        has_unknown_authority=False,
        has_conflicting_evidence=False,
        authority_class=AuthorityClass.OPERATOR,
    )
    decision = classify_route(inp)
    assert not decision.is_red_lane()
    assert decision.proof_requirements  # non-empty


# ─────────────────────────────────────────────
# Test 18 — Non-trivial repo-changing → embedded audit
# ─────────────────────────────────────────────


def test_nontrivial_repo_changing_requires_embedded_audit() -> None:
    inp = RoutingClassificationInput(
        is_non_trivial=True,
        is_repo_changing=True,
    )
    decision = classify_route(inp)
    assert decision.audit_requirement in (
        AuditRequirement.EMBEDDED_AUDITOR,
        AuditRequirement.DISTINCT_AUDITOR,
        AuditRequirement.SUPERVISOR_AUDIT,
    )


# ─────────────────────────────────────────────
# Test 19 — High-risk → supervisor escalation
# ─────────────────────────────────────────────


def test_high_risk_requires_supervisor_escalation() -> None:
    inp = RoutingClassificationInput(
        risk_class=RiskClass.R3_HIGH,
        is_non_trivial=True,
        is_repo_changing=True,
        # Isolate risk-class path by providing known-good authority
        has_unknown_authority=False,
        authority_class=AuthorityClass.OPERATOR,
    )
    decision = classify_route(inp)
    assert decision.escalation_requirement in (
        EscalationRequirement.ALWAYS,
        EscalationRequirement.ON_RISK,
        EscalationRequirement.ON_UNKNOWN,  # also valid escalation
    )


# ─────────────────────────────────────────────
# Test 20 — Backend kind is data only, not callable
# ─────────────────────────────────────────────


def test_backend_kind_is_data_not_callable() -> None:
    inp = RoutingClassificationInput(backend_kind=BackendKind.CODEX)
    decision = classify_route(inp)
    assert decision.backend_kind is BackendKind.CODEX
    assert not callable(decision.backend_kind.value)


# ─────────────────────────────────────────────
# Test 21 — Connector kind is data only, not callable
# ─────────────────────────────────────────────


def test_connector_kind_is_data_not_callable() -> None:
    inp = RoutingClassificationInput(connector_kind=ConnectorKind.MCP)
    decision = classify_route(inp)
    assert decision.connector_kind is ConnectorKind.MCP
    assert not callable(decision.connector_kind.value)


# ─────────────────────────────────────────────
# Test 22 — Evidence refs preserved
# ─────────────────────────────────────────────


def test_evidence_refs_preserved() -> None:
    refs = ["proof/abc.json", "git-diff-2026.txt"]
    inp = RoutingClassificationInput(evidence_refs=refs)
    decision = classify_route(inp)
    for ref in refs:
        assert ref in decision.evidence_refs


# ─────────────────────────────────────────────
# Test 23 — Unknowns preserved
# ─────────────────────────────────────────────


def test_unknowns_preserved_from_input() -> None:
    inp = RoutingClassificationInput(
        has_unknown_authority=True,
        authority_class=AuthorityClass.UNKNOWN,
    )
    decision = classify_route(inp)
    assert decision.unknowns  # at least one unknown recorded


# ─────────────────────────────────────────────
# Test 24 — Allowed actions are passive/safe
# ─────────────────────────────────────────────


def test_allowed_actions_are_passive_safe() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        touches_tests=True,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        has_conflicting_evidence=False,
        touches_secrets=False,
        touches_auth=False,
        touches_security=False,
        touches_destructive_path=False,
        requires_live_write=False,
        requires_runner_execution=False,
        requires_connector_call=False,
        requires_mcp_call=False,
        requires_dopetask_execution=False,
        requires_task_orchestrator_write=False,
    )
    decision = classify_route(inp)
    # Allowed actions must not include live-execution verbs
    disallowed_in_allowed = {
        "execute_runner",
        "call_connector",
        "call_mcp",
        "merge_pr",
        "touch_secrets",
        "run_destructive_command",
        "mutate_task_orchestrator",
        "execute_dopetask",
        "write_github_state",
    }
    for action in decision.allowed_actions:
        assert action not in disallowed_in_allowed


# ─────────────────────────────────────────────
# Test 25 — Forbidden actions include live execution
# ─────────────────────────────────────────────


def test_forbidden_actions_include_live_execution() -> None:
    inp = _default()
    decision = classify_route(inp)
    forbidden_str = " ".join(decision.forbidden_actions)
    assert "runner" in forbidden_str or "execute" in forbidden_str or "connector" in forbidden_str


# ─────────────────────────────────────────────
# Test 26 — RED_LANE decision is not runnable
# ─────────────────────────────────────────────


def test_red_lane_is_not_runnable() -> None:
    inp = RoutingClassificationInput(touches_secrets=True)
    decision = classify_route(inp)
    assert decision.is_red_lane()
    assert not _is_runnable(decision)


# ─────────────────────────────────────────────
# Test 27 — Unknown red-lane is not runnable
# ─────────────────────────────────────────────


def test_unknown_red_lane_not_runnable() -> None:
    inp = RoutingClassificationInput(
        has_unknown_authority=True,
        has_missing_proof=True,
        is_repo_changing=True,
        is_non_trivial=True,
    )
    decision = classify_route(inp)
    assert not _is_runnable(decision)


# ─────────────────────────────────────────────
# Test 28 — String enum input normalizes safely
# ─────────────────────────────────────────────


def test_string_risk_class_normalizes() -> None:
    inp = RoutingClassificationInput(risk_class="R1_LOW")
    decision = classify_route(inp)
    assert isinstance(decision.risk_class, RiskClass)
    assert decision.risk_class is RiskClass.R1_LOW


# ─────────────────────────────────────────────
# Test 29 — Invalid enum string falls back to UNKNOWN or blocks
# ─────────────────────────────────────────────


def test_invalid_enum_string_falls_back_safely() -> None:
    inp = RoutingClassificationInput(
        task_type="NOT_A_TASK_TYPE",
        risk_class=RiskClass.R1_LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.task_type is TaskType.UNKNOWN
    assert not _is_runnable(decision)


# ─────────────────────────────────────────────
# Test 30 — No forbidden imports in classifier source
# ─────────────────────────────────────────────


def test_no_forbidden_imports_in_classifier_source() -> None:
    import dopemux.dcp.routing_classifier as mod

    source = inspect.getsource(mod)
    import_lines = [
        line.strip()
        for line in source.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]
    for forbidden in FORBIDDEN_IMPORTS_IN_CLASSIFIER:
        for line in import_lines:
            assert forbidden not in line, (
                f"Forbidden import '{forbidden}' found in classifier: {line}"
            )


# ─────────────────────────────────────────────
# Test 31 — No forbidden method names in classifier
# ─────────────────────────────────────────────


def test_no_forbidden_method_names_in_classifier_source() -> None:
    import dopemux.dcp.routing_classifier as mod

    source = inspect.getsource(mod)
    # Exclude pure string field assignments (values in quotes)
    code_lines = [
        line for line in source.splitlines()
        if not line.strip().startswith("#")
        and not line.strip().startswith('"')
        and not line.strip().startswith("'")
    ]
    code_text = "\n".join(code_lines)
    for method in FORBIDDEN_METHODS:
        # Only fail if it appears as a def, not as a string value
        assert f"def {method}" not in code_text and f"self.{method}" not in code_text, (
            f"Forbidden method '{method}' found as active code in classifier"
        )


# ─────────────────────────────────────────────
# Test 32 — Serialization of RouteDecision works
# ─────────────────────────────────────────────


def test_serialization_works() -> None:
    inp = _default()
    decision = classify_route(inp)
    d = decision.to_dict()
    assert isinstance(d, dict)
    assert "status" in d
    assert "red_lane_state" in d


def test_to_dict_after_string_enum_input() -> None:
    inp = RoutingClassificationInput(
        task_type="CODE_CHANGE",
        risk_class="R1_LOW",
        complexity_class="LOW",
        authority_class="OPERATOR",
        runtime_impact="LOCAL_ONLY",
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    d = decision.to_dict()
    assert d["task_type"] == "CODE_CHANGE"
    assert d["risk_class"] == "R1_LOW"
    assert d["runtime_impact"] == "LOCAL_ONLY"


def test_task_type_live_write_enum_blocks_and_is_not_runnable() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.LIVE_WRITE,
        risk_class=RiskClass.R1_LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.red_lane_state is RedLaneState.RED_LANE
    assert not _is_runnable(decision)
    assert "live_write_to_service" in decision.forbidden_actions


def test_runtime_impact_live_write_enum_blocks_and_is_not_runnable() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.LIVE_WRITE,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.red_lane_state is RedLaneState.RED_LANE
    assert not _is_runnable(decision)
    assert "live_write_to_service" in decision.forbidden_actions


def test_unknown_authority_allowed_actions_exclude_mutations() -> None:
    decision = classify_route(_default())
    assert decision.status is RouteStatus.UNKNOWN
    assert decision.allowed_actions == ["inspect_runtime_code"]
    assert "edit_allowlisted_files" not in decision.allowed_actions
    assert "open_pr" not in decision.allowed_actions
    assert "run_embedded_audit" not in decision.allowed_actions


def test_risk_class_red_lane_string_normalizes_and_blocks() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.CODE_CHANGE,
        risk_class="RED_LANE",
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.risk_class is RiskClass.RED_LANE
    assert decision.red_lane_state is RedLaneState.RED_LANE
    assert not _is_runnable(decision)


def test_network_requirement_blocks_and_is_not_runnable() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        requires_network=True,
    )
    decision = classify_route(inp)
    assert decision.red_lane_state is RedLaneState.RED_LANE
    assert not _is_runnable(decision)
    assert "network_required" in decision.stop_conditions


def test_external_service_requirement_blocks_and_is_not_runnable() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        requires_external_service=True,
    )
    decision = classify_route(inp)
    assert decision.red_lane_state is RedLaneState.RED_LANE
    assert not _is_runnable(decision)
    assert "external_service_required" in decision.stop_conditions


@pytest.mark.parametrize("action", ["merge_pr", "execute_runner"])
def test_forbidden_requested_action_blocks_route(action: str) -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        requested_actions=[action],
    )
    decision = classify_route(inp)
    assert decision.red_lane_state is RedLaneState.RED_LANE
    assert not _is_runnable(decision)
    assert f"forbidden_action_requested:{action}" in decision.stop_conditions


def test_merge_task_type_blocks_and_is_not_runnable() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.MERGE,
        risk_class=RiskClass.R1_LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.red_lane_state is RedLaneState.RED_LANE
    assert not _is_runnable(decision)
    assert "merge_task_requested" in decision.stop_conditions


def test_service_mutation_runtime_impact_blocks_and_is_not_runnable() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.SERVICE_MUTATION,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.red_lane_state is RedLaneState.RED_LANE
    assert not _is_runnable(decision)
    assert "service_mutation_requested" in decision.stop_conditions


def test_read_only_route_excludes_mutating_allowed_actions() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.READ_ONLY,
        risk_class=RiskClass.R0_READ,
        runtime_impact=RuntimeImpact.READ_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.status is RouteStatus.ALLOWED
    assert decision.allowed_actions == ["inspect_runtime_code"]
    assert "edit_allowlisted_files" not in decision.allowed_actions
    assert "open_pr" not in decision.allowed_actions


def test_unknown_runtime_impact_is_not_runnable() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.runtime_impact is RuntimeImpact.UNKNOWN
    assert decision.status is RouteStatus.UNKNOWN
    assert not _is_runnable(decision)
    assert decision.allowed_actions == ["inspect_runtime_code"]


def test_ci_touching_route_requires_supervisor_and_is_not_runnable() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.LOCAL_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        touches_ci=True,
    )
    decision = classify_route(inp)
    assert decision.escalation_requirement is EscalationRequirement.ALWAYS
    assert decision.status is RouteStatus.NEEDS_SUPERVISOR
    assert not _is_runnable(decision)
    assert "edit_allowlisted_files" not in decision.allowed_actions
    assert "open_pr" not in decision.allowed_actions


def test_missing_proof_blocks_mutating_classification() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.LOCAL_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        has_missing_proof=True,
    )
    decision = classify_route(inp)
    assert decision.status is RouteStatus.BLOCKED
    assert not _is_runnable(decision)
    assert decision.allowed_actions == []


def test_unknown_complexity_is_not_runnable() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.LOCAL_ONLY,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.complexity_class is ComplexityClass.UNKNOWN
    assert decision.status is RouteStatus.UNKNOWN
    assert not _is_runnable(decision)
    assert decision.allowed_actions == ["inspect_runtime_code"]


# ─────────────────────────────────────────────
# Test 33 — Round-trip from_dict works
# ─────────────────────────────────────────────


def test_round_trip_from_dict() -> None:
    inp = RoutingClassificationInput(
        is_non_trivial=True,
        is_repo_changing=True,
    )
    decision = classify_route(inp)
    d = decision.to_dict()
    decision2 = RouteDecision.from_dict(d)
    assert decision2.status == decision.status
    assert decision2.red_lane_state == decision.red_lane_state
    assert decision2.audit_requirement == decision.audit_requirement


# ─────────────────────────────────────────────
# Test 34 — CI repair task → proof/audit required, not RED_LANE
# ─────────────────────────────────────────────


def test_ci_repair_task_classified_as_proof_not_red_lane() -> None:
    """CI-touching tasks need proof/audit but are not automatically RED_LANE."""
    inp = RoutingClassificationInput(
        task_type=TaskType.CODE_CHANGE,
        touches_ci=True,
        touches_secrets=False,
        touches_auth=False,
        touches_security=False,
        touches_destructive_path=False,
        requires_live_write=False,
        requires_runner_execution=False,
        requires_connector_call=False,
        requires_mcp_call=False,
        requires_dopetask_execution=False,
        requires_task_orchestrator_write=False,
    )
    decision = classify_route(inp)
    # CI touch → proof and audit required
    assert decision.proof_requirements
    assert decision.audit_requirement is not AuditRequirement.NONE
    # CI touch alone is NOT automatically RED_LANE (may be BLOCKED/NEEDS_SUPERVISOR)
    assert not decision.is_red_lane()


# ─────────────────────────────────────────────
# Test 35 — PR merge request is forbidden
# ─────────────────────────────────────────────


def test_pr_merge_is_forbidden_action() -> None:
    inp = _default()
    decision = classify_route(inp)
    assert any("merge" in a for a in decision.forbidden_actions)


# ─────────────────────────────────────────────
# Test 36 — Classifier does not mutate input object
# ─────────────────────────────────────────────


def test_classifier_does_not_mutate_input() -> None:
    inp = RoutingClassificationInput(
        is_non_trivial=True,
        touches_secrets=False,
        evidence_refs=["ref1"],
    )
    original_refs = list(inp.evidence_refs)
    original_non_trivial = inp.is_non_trivial
    classify_route(inp)
    assert inp.evidence_refs == original_refs
    assert inp.is_non_trivial == original_non_trivial


# ─────────────────────────────────────────────
# Additional: destructive path → RED_LANE
# ─────────────────────────────────────────────


def test_destructive_path_is_red_lane() -> None:
    inp = RoutingClassificationInput(touches_destructive_path=True)
    decision = classify_route(inp)
    assert decision.is_red_lane()


# Additional: conflicting evidence → RED_LANE or BLOCKED
def test_conflicting_evidence_blocks() -> None:
    inp = RoutingClassificationInput(has_conflicting_evidence=True)
    decision = classify_route(inp)
    assert decision.is_red_lane() or decision.is_blocked()
