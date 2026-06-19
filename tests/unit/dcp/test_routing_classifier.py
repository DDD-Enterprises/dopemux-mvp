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
    TaskSource,
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


_READ_ONLY_BASE_ALLOWED = [
    "inspect_runtime_code",
    "run_targeted_tests",
    "capture_proof",
]


def test_unknown_authority_allowed_actions_exclude_mutations() -> None:
    decision = classify_route(_default())
    assert decision.status is RouteStatus.UNKNOWN
    assert decision.allowed_actions == _READ_ONLY_BASE_ALLOWED
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


@pytest.mark.parametrize(
    "action",
    ["merge_pr", "execute_runner", "network_access", "external_service_access"],
)
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
    assert "forbidden_requested_action" in decision.stop_conditions
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
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.READ_ONLY,
        risk_class=RiskClass.R0_READ,
        runtime_impact=RuntimeImpact.READ_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.status is RouteStatus.ALLOWED
    assert decision.allowed_actions == _READ_ONLY_BASE_ALLOWED
    assert "edit_allowlisted_files" not in decision.allowed_actions
    assert "open_pr" not in decision.allowed_actions


def test_unknown_runtime_impact_is_not_runnable() -> None:
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.runtime_impact is RuntimeImpact.UNKNOWN
    assert decision.status is RouteStatus.UNKNOWN
    assert not _is_runnable(decision)
    assert decision.allowed_actions == _READ_ONLY_BASE_ALLOWED


def test_ci_touching_route_requires_supervisor_and_is_not_runnable() -> None:
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
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
        task_source=TaskSource.OPERATOR,
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
        task_source=TaskSource.OPERATOR,
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
    assert decision.allowed_actions == _READ_ONLY_BASE_ALLOWED


def test_architectural_complexity_requires_supervisor_and_is_not_runnable() -> None:
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.LOCAL_ONLY,
        complexity_class=ComplexityClass.ARCHITECTURAL,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.status is RouteStatus.NEEDS_SUPERVISOR
    assert decision.escalation_requirement is EscalationRequirement.ON_RISK
    assert not _is_runnable(decision)
    assert "edit_allowlisted_files" not in decision.allowed_actions
    assert "open_pr" not in decision.allowed_actions


def test_mutating_classification_requires_proof_obligations() -> None:
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.LOCAL_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.status is RouteStatus.ALLOWED
    assert ProofRequirement.DIFF_STAT in decision.proof_requirements
    assert ProofRequirement.FULL_PROOF_BUNDLE in decision.proof_requirements


def test_mutating_classification_requires_audit_obligation() -> None:
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.LOCAL_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.status is RouteStatus.ALLOWED
    assert decision.audit_requirement is AuditRequirement.SELF_CHECK


def test_classify_route_uses_deterministic_route_id() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.READ_ONLY,
        risk_class=RiskClass.R0_READ,
        runtime_impact=RuntimeImpact.READ_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        evidence_refs=["proof/a.json"],
    )
    first = classify_route(inp)
    second = classify_route(inp)
    assert first.route_id == second.route_id


def test_unknown_task_source_is_not_runnable() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.LOCAL_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    decision = classify_route(inp)
    assert decision.task_source is TaskSource.UNKNOWN
    assert decision.status is RouteStatus.UNKNOWN
    assert not _is_runnable(decision)
    assert "task_source_unknown" in decision.unknowns


def test_unknown_task_source_is_recorded_in_unknowns() -> None:
    decision = classify_route(_default())
    assert "task_source_unknown" in decision.unknowns


def test_unknown_task_source_does_not_allow_edit_or_open_pr() -> None:
    inp = RoutingClassificationInput(
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.LOCAL_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        requested_actions=["edit_allowlisted_files", "open_pr"],
    )
    decision = classify_route(inp)
    assert decision.task_source is TaskSource.UNKNOWN
    assert not _is_runnable(decision)
    assert "edit_allowlisted_files" not in decision.allowed_actions
    assert "open_pr" not in decision.allowed_actions


def test_read_only_requested_run_targeted_tests_does_not_grant_edit_or_open_pr() -> None:
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.READ_ONLY,
        risk_class=RiskClass.R0_READ,
        runtime_impact=RuntimeImpact.READ_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        requested_actions=["run_targeted_tests"],
    )
    decision = classify_route(inp)
    assert decision.status is RouteStatus.ALLOWED
    assert decision.allowed_actions == ["run_targeted_tests"]
    assert "edit_allowlisted_files" not in decision.allowed_actions
    assert "open_pr" not in decision.allowed_actions


def test_read_only_requested_capture_proof_does_not_grant_edit_or_open_pr() -> None:
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.READ_ONLY,
        risk_class=RiskClass.R0_READ,
        runtime_impact=RuntimeImpact.READ_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        requested_actions=["capture_proof"],
    )
    decision = classify_route(inp)
    assert decision.status is RouteStatus.ALLOWED
    assert decision.allowed_actions == ["capture_proof"]
    assert "edit_allowlisted_files" not in decision.allowed_actions
    assert "open_pr" not in decision.allowed_actions


def test_requested_actions_narrow_not_widen_allowed_actions() -> None:
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.LOCAL_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        requested_actions=["run_targeted_tests", "open_pr", "edit_allowlisted_files"],
    )
    decision = classify_route(inp)
    assert decision.status is RouteStatus.ALLOWED
    assert decision.allowed_actions == [
        "run_targeted_tests",
        "open_pr",
        "edit_allowlisted_files",
    ]
    assert "run_embedded_audit" not in decision.allowed_actions
    assert "capture_proof" not in decision.allowed_actions


@pytest.mark.parametrize("action", ["run_targeted_tests", "capture_proof"])
def test_read_only_requested_actions_do_not_grant_edit_or_pr(action: str) -> None:
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.READ_ONLY,
        risk_class=RiskClass.R0_READ,
        runtime_impact=RuntimeImpact.READ_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        requested_actions=[action],
    )
    decision = classify_route(inp)
    assert decision.status is RouteStatus.ALLOWED
    assert decision.allowed_actions == [action]
    assert "edit_allowlisted_files" not in decision.allowed_actions
    assert "open_pr" not in decision.allowed_actions
    assert "run_embedded_audit" not in decision.allowed_actions


def test_forbidden_requested_merge_pr_blocks_route() -> None:
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.LOCAL_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        requested_actions=["merge_pr"],
    )
    decision = classify_route(inp)
    assert not _is_runnable(decision)
    assert "forbidden_requested_action" in decision.stop_conditions


def test_forbidden_requested_execute_runner_blocks_route() -> None:
    inp = RoutingClassificationInput(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.LOCAL_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
        requested_actions=["execute_runner"],
    )
    decision = classify_route(inp)
    assert not _is_runnable(decision)
    assert "forbidden_requested_action" in decision.stop_conditions


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


# ─────────────────────────────────────────────
# 0002R: Reconciliation invariant lock-down tests
# ─────────────────────────────────────────────
# These 5 tests assert ALREADY-IMPLEMENTED behaviour only.
# No new classifier fields or logic were introduced.
# See task-packets/DMX-DCP-MODEL-ROUTING-MVP-0002R.md for full rationale
# and the DEFERRED lane-concept cases (0003+ lane-engine work).
# ─────────────────────────────────────────────


def test_unknown_authority_blocks_mutation() -> None:
    """Lock: unknown authority must not permit any mutation actions.

    When has_unknown_authority=True and authority_class=UNKNOWN the
    classifier MUST produce a non-runnable decision AND MUST NOT include
    any mutation-capable action (edit/open_pr/write) in allowed_actions.

    Invariant source: _derive_route_status returns RouteStatus.UNKNOWN for
    unknown authority; _derive_allowed_actions grants only _READ_ONLY_BASE_ALLOWED
    when status is not ALLOWED.
    """
    inp = RoutingClassificationInput(
        has_unknown_authority=True,
        authority_class=AuthorityClass.UNKNOWN,
    )
    decision = classify_route(inp)

    # Must not be runnable
    assert not decision.is_runnable()

    # Must not contain any mutation-capable action
    mutation_actions = {"edit_allowlisted_files", "open_pr", "run_embedded_audit"}
    for action in decision.allowed_actions:
        assert action not in mutation_actions, (
            f"Mutation action '{action}' must not be allowed under unknown authority"
        )


def test_dopetask_boundary_blocks_dcp_core_execution() -> None:
    """Lock: dopetask execution boundary must be enforced as an explicit forbidden action.

    When requires_dopetask_execution=True the classifier enters RED_LANE,
    which blocks execution (status=BLOCKED, not runnable) and records
    "execute_dopetask" and/or "execute_dopetask_live" in forbidden_actions.

    This explicitly asserts the DCP-core-execution boundary: dopetask execution
    is never delegatable through the pure-flag classifier.
    """
    inp = RoutingClassificationInput(
        requires_dopetask_execution=True,
    )
    decision = classify_route(inp)

    # RED_LANE → not runnable
    assert not decision.is_runnable()

    # The "dopetask" token must appear in at least one forbidden action
    assert any("dopetask" in action for action in decision.forbidden_actions), (
        "expected 'dopetask' in forbidden_actions, got: "
        + repr(decision.forbidden_actions)
    )


def test_live_write_without_contract_blocks() -> None:
    """Lock: requires_live_write alone must produce status=BLOCKED and not runnable.

    No contract or proof path in the pure-flag classifier can open a live-write
    route. The RED_LANE gate is unconditional.
    """
    inp = RoutingClassificationInput(
        requires_live_write=True,
    )
    decision = classify_route(inp)

    assert decision.status is RouteStatus.BLOCKED, (
        f"expected BLOCKED status for live-write input, got {decision.status}"
    )
    assert not decision.is_runnable()


def test_unresolved_review_threads_block_readiness() -> None:
    """Lock: has_stale_proof=True blocks the route (status=BLOCKED) regardless of authority.

    Note: "unresolved review threads" as a PR-Steward concern is a HIGHER-LAYER
    readiness check that lives outside this classifier.  The stale-proof gate
    (has_stale_proof=True → RouteStatus.BLOCKED) is the analogous in-classifier
    gate: a route with stale or invalidated evidence is not actionable until proof
    is refreshed.

    PRECEDENCE (fixed in PRE-PROMPT6-0002, was a latent gap deferred from 0002R):
    A hard-BLOCKED reason such as stale proof MUST be reported in ``status`` even
    when authority is also unknown (the conservative default).  ``_derive_route_status``
    now applies the hard-BLOCKED checks (authority BLOCKED, missing proof, stale
    proof) BEFORE the UNKNOWN-authority guard — a most-severe-first ordering
    (BLOCKED > UNKNOWN).  The default ``has_unknown_authority=True`` therefore no
    longer masks the stale-proof BLOCKED status.
    """
    inp = RoutingClassificationInput(
        has_stale_proof=True,
        # Default authority is UNKNOWN: the stale-proof BLOCKED reason must still
        # surface in ``status`` (this is the precedence fix being locked).
    )
    decision = classify_route(inp)

    assert decision.status is RouteStatus.BLOCKED, (
        f"expected BLOCKED for stale proof input, got {decision.status}"
    )
    assert not decision.is_runnable()
    # The stale-proof reason is surfaced in both status and stop_conditions.
    assert "stale_proof" in decision.stop_conditions


def test_hard_blocked_reason_wins_over_unknown_authority() -> None:
    """Lock: status precedence is most-severe-first — BLOCKED beats UNKNOWN.

    Each hard-BLOCKED reason must be reported in ``status`` even when authority is
    also unknown (the default).  Before the PRE-PROMPT6-0002 precedence fix the
    UNKNOWN-authority guard returned first and masked these reasons as
    RouteStatus.UNKNOWN.
    """
    # Stale proof + default unknown authority → BLOCKED (not UNKNOWN).
    stale = classify_route(RoutingClassificationInput(has_stale_proof=True))
    assert stale.status is RouteStatus.BLOCKED

    # Explicitly BLOCKED authority + default unknown-authority flag → BLOCKED.
    blocked_auth = classify_route(
        RoutingClassificationInput(authority_class=AuthorityClass.BLOCKED)
    )
    assert blocked_auth.status is RouteStatus.BLOCKED

    # Missing proof on a mutating/non-trivial route + unknown authority → BLOCKED.
    missing = classify_route(
        RoutingClassificationInput(
            has_missing_proof=True,
            is_repo_changing=True,
            is_non_trivial=True,
        )
    )
    assert missing.status is RouteStatus.BLOCKED


def test_unknown_authority_alone_still_reports_unknown() -> None:
    """Lock: with no hard-BLOCKED reason, unknown authority still yields UNKNOWN.

    The precedence fix must not over-block: a route whose only defect is unknown
    authority (no stale/missing proof, not red-lane) remains RouteStatus.UNKNOWN.
    """
    decision = classify_route(
        RoutingClassificationInput(
            has_unknown_authority=True,
            authority_class=AuthorityClass.UNKNOWN,
        )
    )
    assert decision.status is RouteStatus.UNKNOWN
    assert not decision.is_runnable()


def test_secret_pattern_routes_to_supervisor() -> None:
    """Lock: touches_secrets=True must set RED_LANE, SUPERVISOR_AUDIT, and ALWAYS escalation.

    Three invariants locked simultaneously because they are all derived from the
    same flag in the classifier and must move together:
    1. is_red_lane() True  — hard block on execution.
    2. audit_requirement == SUPERVISOR_AUDIT  — strongest audit obligation.
    3. escalation_requirement == ALWAYS  — unconditional escalation to supervisor.
    """
    inp = RoutingClassificationInput(
        touches_secrets=True,
    )
    decision = classify_route(inp)

    assert decision.is_red_lane(), (
        "touches_secrets must produce RED_LANE state"
    )
    assert decision.audit_requirement is AuditRequirement.SUPERVISOR_AUDIT, (
        f"expected SUPERVISOR_AUDIT, got {decision.audit_requirement}"
    )
    assert decision.escalation_requirement is EscalationRequirement.ALWAYS, (
        f"expected ALWAYS escalation, got {decision.escalation_requirement}"
    )


# ─────────────────────────────────────────────
# DMX-DCP-MODEL-ROUTING-MVP-0006 — Classifier Provenance Hardening
#
# Provenance signals can only LOWER trust, never raise it, and override a
# claimed-but-laundered authority_class. All new fields default to a no-op
# (zero regression). Composes with the #904 most-severe-first ordering.
# ─────────────────────────────────────────────


def _allowed_baseline(**overrides) -> RoutingClassificationInput:
    """A fully-specified input that classifies to ALLOWED + runnable.

    Mutating scope (task_type=CODE_CHANGE). Used to prove a provenance vector
    DOWNGRADES an otherwise-executable route.
    """
    base = dict(
        task_source=TaskSource.OPERATOR,
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R1_LOW,
        runtime_impact=RuntimeImpact.LOCAL_ONLY,
        complexity_class=ComplexityClass.LOW,
        authority_class=AuthorityClass.OPERATOR,
        has_unknown_authority=False,
    )
    base.update(overrides)
    return RoutingClassificationInput(**base)


def test_allowed_baseline_is_runnable_sanity() -> None:
    """Guard: the baseline really is ALLOWED + runnable (so downgrades are meaningful)."""
    decision = classify_route(_allowed_baseline())
    assert decision.status is RouteStatus.ALLOWED
    assert decision.is_runnable()


def test_bridge_proxy_authority_coerced_to_unknown() -> None:
    """Lane case: bridge/proxy authority is never trusted (the laundering exploit).

    A caller claims authority_class=AUTOMATED_SAFE + has_unknown_authority=False
    for a task whose TRUE authority is a bridge/proxy. authority_via_bridge_proxy
    MUST coerce effective authority -> UNKNOWN -> not ALLOWED / not runnable.
    """
    decision = classify_route(
        _allowed_baseline(
            authority_class=AuthorityClass.AUTOMATED_SAFE,
            authority_via_bridge_proxy=True,
        )
    )
    assert decision.status is not RouteStatus.ALLOWED
    assert not decision.is_runnable()


def test_bridge_proxy_preserves_blocked_authority() -> None:
    """Bridge/proxy coercion must not weaken an explicit BLOCKED authority."""
    decision = classify_route(
        _allowed_baseline(
            authority_class=AuthorityClass.BLOCKED,
            authority_via_bridge_proxy=True,
        )
    )
    assert decision.authority_class is AuthorityClass.BLOCKED
    assert decision.status is RouteStatus.BLOCKED
    assert not decision.is_runnable()


def test_retrieval_derived_without_source_blocks_mutation() -> None:
    """Retrieval-derived evidence without the exact source fetched cannot back mutation."""
    decision = classify_route(
        _allowed_baseline(evidence_is_retrieval_derived=True)
    )
    assert decision.status is RouteStatus.BLOCKED
    assert not decision.is_runnable()


def test_retrieval_derived_with_source_fetched_permits() -> None:
    """With exact_source_fetched=True the retrieval-derived block clears (no regression)."""
    decision = classify_route(
        _allowed_baseline(
            evidence_is_retrieval_derived=True,
            exact_source_fetched=True,
        )
    )
    assert decision.status is RouteStatus.ALLOWED
    assert decision.is_runnable()


def test_ecc_intake_static_only() -> None:
    """ECC external intake may only do read-only/static work; any mutation -> BLOCKED."""
    decision = classify_route(_allowed_baseline(is_ecc_external_intake=True))
    assert decision.status is RouteStatus.BLOCKED
    assert not decision.is_runnable()


def test_ecc_intake_read_only_not_blocked_by_provenance() -> None:
    """ECC intake on a pure read-only route is not blocked by the ECC provenance guard."""
    decision = classify_route(
        RoutingClassificationInput(
            task_source=TaskSource.OPERATOR,
            task_type=TaskType.READ_ONLY,
            risk_class=RiskClass.R0_READ,
            runtime_impact=RuntimeImpact.READ_ONLY,
            complexity_class=ComplexityClass.LOW,
            authority_class=AuthorityClass.OPERATOR,
            has_unknown_authority=False,
            is_ecc_external_intake=True,
        )
    )
    assert decision.status is RouteStatus.ALLOWED
    assert "ecc_external_intake" not in decision.stop_conditions


def test_retrieval_derived_read_only_does_not_emit_stop_condition() -> None:
    """Retrieval-derived evidence is advisory on read-only routes, not a stop condition."""
    decision = classify_route(
        RoutingClassificationInput(
            task_source=TaskSource.OPERATOR,
            task_type=TaskType.READ_ONLY,
            risk_class=RiskClass.R0_READ,
            runtime_impact=RuntimeImpact.READ_ONLY,
            complexity_class=ComplexityClass.LOW,
            authority_class=AuthorityClass.OPERATOR,
            has_unknown_authority=False,
            evidence_is_retrieval_derived=True,
            exact_source_fetched=False,
        )
    )
    assert decision.status is RouteStatus.ALLOWED
    assert "retrieval_derived_evidence_unverified" not in decision.stop_conditions


def test_retrieval_derived_nontrivial_audit_read_only_not_blocked() -> None:
    """Non-trivial read-only audit work is not mutating provenance scope."""
    decision = classify_route(
        RoutingClassificationInput(
            task_source=TaskSource.OPERATOR,
            task_type=TaskType.AUDIT,
            risk_class=RiskClass.R0_READ,
            runtime_impact=RuntimeImpact.READ_ONLY,
            complexity_class=ComplexityClass.LOW,
            authority_class=AuthorityClass.OPERATOR,
            has_unknown_authority=False,
            is_non_trivial=True,
            evidence_is_retrieval_derived=True,
            exact_source_fetched=False,
        )
    )
    assert decision.status is RouteStatus.ALLOWED
    assert "retrieval_derived_evidence_unverified" not in decision.stop_conditions


def test_opencode_backend_requires_wrapper_proof() -> None:
    """OPENCODE backend without wrapper proof blocks mutation; proof clears it."""
    blocked = classify_route(_allowed_baseline(backend_kind=BackendKind.OPENCODE))
    assert blocked.status is RouteStatus.BLOCKED
    assert not blocked.is_runnable()

    proven = classify_route(
        _allowed_baseline(
            backend_kind=BackendKind.OPENCODE,
            has_backend_wrapper_proof=True,
        )
    )
    assert proven.status is RouteStatus.ALLOWED
    assert proven.is_runnable()


def test_grok_backend_requires_wrapper_proof() -> None:
    """GROK backend without wrapper proof blocks mutation; proof clears it."""
    blocked = classify_route(_allowed_baseline(backend_kind=BackendKind.GROK))
    assert blocked.status is RouteStatus.BLOCKED
    assert not blocked.is_runnable()

    proven = classify_route(
        _allowed_baseline(
            backend_kind=BackendKind.GROK,
            has_backend_wrapper_proof=True,
        )
    )
    assert proven.status is RouteStatus.ALLOWED


def test_secure_mcp_readonly_still_red_lane() -> None:
    """Case-6 boundary: requires_mcp_call stays RED_LANE (ACL is a facade concern)."""
    decision = classify_route(_allowed_baseline(requires_mcp_call=True))
    assert decision.red_lane_state is RedLaneState.RED_LANE
    assert not decision.is_runnable()


def test_provenance_defaults_are_noop_regression() -> None:
    """All five provenance fields defaulting False must not change a known classification."""
    decision = classify_route(_allowed_baseline())
    assert decision.status is RouteStatus.ALLOWED
    assert decision.is_runnable()


@pytest.mark.parametrize(
    "vector",
    [
        {"authority_via_bridge_proxy": True},
        {"evidence_is_retrieval_derived": True},
        {"is_ecc_external_intake": True},
        {"backend_kind": BackendKind.OPENCODE},
        {"backend_kind": BackendKind.GROK},
    ],
)
def test_provenance_coercion_overrides_claimed_authority(vector: dict) -> None:
    """Generalization: any provenance vector overrides a claimed AUTOMATED_SAFE authority."""
    decision = classify_route(
        _allowed_baseline(authority_class=AuthorityClass.AUTOMATED_SAFE, **vector)
    )
    assert decision.status is not RouteStatus.ALLOWED
    assert not decision.is_runnable()


@pytest.mark.parametrize(
    "vector",
    [
        {"authority_via_bridge_proxy": True},
        {"evidence_is_retrieval_derived": True},
        {"exact_source_fetched": True},
        {"is_ecc_external_intake": True},
        {"has_backend_wrapper_proof": True},
    ],
)
def test_provenance_fields_change_route_id(vector: dict) -> None:
    """Each provenance/trust field must participate in route-id separation."""
    baseline = _allowed_baseline()
    baseline_id = classify_route(baseline).route_id
    toggled_id = classify_route(_allowed_baseline(**vector)).route_id
    assert toggled_id != baseline_id
