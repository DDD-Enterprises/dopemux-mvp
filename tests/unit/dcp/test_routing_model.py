"""Unit tests for DMX-DCP-MODEL-ROUTING-MVP-0001R routing domain model.

Coverage targets:
- UNKNOWN default values (all critical fields)
- BLOCKED status representation
- RED_LANE state representation and override behaviour
- Serialization round-trip (to_dict / from_dict)
- Proof requirement fields (first-class, listable)
- Audit requirement field (first-class)
- Escalation requirement field
- Default confidence is not VERIFIED
- Default status is not runnable
- UNKNOWN authority is not runnable
- RED_LANE overrides ALLOWED status in is_runnable()
- from_dict falls back to UNKNOWN for unrecognised enum values
- is_blocked() helper
- is_red_lane() helper
- No I/O, network, subprocess, or external imports (static)
"""

import inspect

import pytest

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
# Static / import purity checks
# ─────────────────────────────────────────────

FORBIDDEN_IMPORTS = {
    "subprocess",
    "requests",
    "httpx",
    "urllib",
    "socket",
    "opencode",
    "grok",
    "gh",
    "docker",
    "mcp",
    "dopetask",
    "task_orchestrator",
    "conport",
    "dope_memory",
    "dope_context",
}


def test_routing_model_module_has_no_forbidden_imports() -> None:
    """Domain model must not import runner/connector/IO packages."""
    import dopemux.dcp.routing_model as mod

    source = inspect.getsource(mod)
    for forbidden in FORBIDDEN_IMPORTS:
        # Allow appearances in comments/docstrings describing what is NOT imported
        # This is a simple heuristic: check import statements specifically.
        import_lines = [
            line.strip()
            for line in source.splitlines()
            if line.strip().startswith(("import ", "from "))
        ]
        for line in import_lines:
            assert forbidden not in line, (
                f"Forbidden import '{forbidden}' found in routing_model: {line!r}"
            )


# ─────────────────────────────────────────────
# UNKNOWN defaults
# ─────────────────────────────────────────────


def test_default_route_decision_has_unknown_task_source() -> None:
    rd = RouteDecision()
    assert rd.task_source is TaskSource.UNKNOWN


def test_default_route_decision_has_unknown_task_type() -> None:
    rd = RouteDecision()
    assert rd.task_type is TaskType.UNKNOWN


def test_default_route_decision_has_unknown_risk_class() -> None:
    rd = RouteDecision()
    assert rd.risk_class is RiskClass.UNKNOWN


def test_default_route_decision_has_unknown_complexity_class() -> None:
    rd = RouteDecision()
    assert rd.complexity_class is ComplexityClass.UNKNOWN


def test_default_route_decision_has_unknown_authority_class() -> None:
    rd = RouteDecision()
    assert rd.authority_class is AuthorityClass.UNKNOWN


def test_default_route_decision_has_unknown_runtime_impact() -> None:
    rd = RouteDecision()
    assert rd.runtime_impact is RuntimeImpact.UNKNOWN


def test_default_route_decision_has_unknown_backend_kind() -> None:
    rd = RouteDecision()
    assert rd.backend_kind is BackendKind.UNKNOWN


def test_default_route_decision_has_unknown_connector_kind() -> None:
    rd = RouteDecision()
    assert rd.connector_kind is ConnectorKind.UNKNOWN


def test_default_route_decision_has_unknown_audit_requirement() -> None:
    rd = RouteDecision()
    assert rd.audit_requirement is AuditRequirement.UNKNOWN


def test_default_route_decision_has_unknown_red_lane_state() -> None:
    """Default red-lane is UNKNOWN (fail-closed)."""
    rd = RouteDecision()
    assert rd.red_lane_state is RedLaneState.UNKNOWN


def test_default_route_decision_has_low_confidence() -> None:
    """Default confidence must not imply verified state."""
    rd = RouteDecision()
    assert rd.confidence == "LOW"
    assert rd.confidence != "VERIFIED"
    assert rd.confidence != "HIGH"


def test_default_route_decision_has_pending_status() -> None:
    """Default status must not imply runnable state."""
    rd = RouteDecision()
    assert rd.status is RouteStatus.PENDING
    assert rd.status is not RouteStatus.ALLOWED


# ─────────────────────────────────────────────
# BLOCKED state
# ─────────────────────────────────────────────


def test_blocked_route_status_is_representable() -> None:
    rd = RouteDecision(status=RouteStatus.BLOCKED)
    assert rd.status is RouteStatus.BLOCKED


def test_is_blocked_helper_true_when_blocked() -> None:
    rd = RouteDecision(status=RouteStatus.BLOCKED)
    assert rd.is_blocked() is True


def test_is_blocked_helper_false_when_allowed() -> None:
    rd = RouteDecision(status=RouteStatus.ALLOWED)
    assert rd.is_blocked() is False


def test_blocked_route_is_not_runnable() -> None:
    rd = RouteDecision(
        status=RouteStatus.BLOCKED,
        red_lane_state=RedLaneState.CLEAR,
        authority_class=AuthorityClass.OPERATOR,
    )
    assert rd.is_runnable() is False


# ─────────────────────────────────────────────
# RED_LANE state
# ─────────────────────────────────────────────


def test_red_lane_state_is_representable() -> None:
    rd = RouteDecision(risk_class=RiskClass.RED_LANE)
    assert rd.risk_class is RiskClass.RED_LANE


def test_red_lane_gate_state_is_representable() -> None:
    rd = RouteDecision(red_lane_state=RedLaneState.RED_LANE)
    assert rd.red_lane_state is RedLaneState.RED_LANE


def test_is_red_lane_helper_true_when_red_lane() -> None:
    rd = RouteDecision(red_lane_state=RedLaneState.RED_LANE)
    assert rd.is_red_lane() is True


def test_is_red_lane_helper_false_when_clear() -> None:
    rd = RouteDecision(red_lane_state=RedLaneState.CLEAR)
    assert rd.is_red_lane() is False


def test_red_lane_overrides_allowed_status_in_is_runnable() -> None:
    """RED_LANE must override ALLOWED status — invariant 9."""
    rd = RouteDecision(
        status=RouteStatus.ALLOWED,
        authority_class=AuthorityClass.OPERATOR,
        red_lane_state=RedLaneState.RED_LANE,
    )
    assert rd.is_runnable() is False


def test_clear_red_lane_and_allowed_status_is_runnable() -> None:
    rd = RouteDecision(
        status=RouteStatus.ALLOWED,
        authority_class=AuthorityClass.OPERATOR,
        red_lane_state=RedLaneState.CLEAR,
    )
    assert rd.is_runnable() is True


def test_unknown_red_lane_is_not_runnable() -> None:
    """UNKNOWN red-lane is fail-closed (not runnable)."""
    rd = RouteDecision(
        status=RouteStatus.ALLOWED,
        authority_class=AuthorityClass.OPERATOR,
        red_lane_state=RedLaneState.UNKNOWN,
    )
    assert rd.is_runnable() is False


# ─────────────────────────────────────────────
# UNKNOWN authority is not runnable — invariant
# ─────────────────────────────────────────────


def test_unknown_authority_is_not_runnable() -> None:
    """UNKNOWN authority must not be coerced into allowed mutation."""
    rd = RouteDecision(
        status=RouteStatus.ALLOWED,
        red_lane_state=RedLaneState.CLEAR,
        authority_class=AuthorityClass.UNKNOWN,
    )
    assert rd.is_runnable() is False


def test_blocked_authority_is_not_runnable() -> None:
    rd = RouteDecision(
        status=RouteStatus.ALLOWED,
        red_lane_state=RedLaneState.CLEAR,
        authority_class=AuthorityClass.BLOCKED,
    )
    assert rd.is_runnable() is False


# ─────────────────────────────────────────────
# Proof / Audit requirement fields (first-class)
# ─────────────────────────────────────────────


def test_proof_requirements_are_listable() -> None:
    rd = RouteDecision(
        proof_requirements=[
            ProofRequirement.COMMAND_LOG,
            ProofRequirement.DIFF_STAT,
            ProofRequirement.AUDIT_REPORT,
        ]
    )
    assert ProofRequirement.COMMAND_LOG in rd.proof_requirements
    assert ProofRequirement.DIFF_STAT in rd.proof_requirements
    assert ProofRequirement.AUDIT_REPORT in rd.proof_requirements


def test_proof_requirements_default_empty() -> None:
    rd = RouteDecision()
    assert rd.proof_requirements == []


def test_audit_requirement_is_first_class() -> None:
    rd = RouteDecision(audit_requirement=AuditRequirement.DISTINCT_AUDITOR)
    assert rd.audit_requirement is AuditRequirement.DISTINCT_AUDITOR


def test_escalation_requirement_is_first_class() -> None:
    rd = RouteDecision(escalation_requirement=EscalationRequirement.ON_RISK)
    assert rd.escalation_requirement is EscalationRequirement.ON_RISK


def test_full_proof_bundle_requirement_is_representable() -> None:
    rd = RouteDecision(
        proof_requirements=[ProofRequirement.FULL_PROOF_BUNDLE]
    )
    assert ProofRequirement.FULL_PROOF_BUNDLE in rd.proof_requirements


# ─────────────────────────────────────────────
# Serialization — to_dict
# ─────────────────────────────────────────────


def test_to_dict_returns_plain_dict() -> None:
    rd = RouteDecision()
    d = rd.to_dict()
    assert isinstance(d, dict)


def test_to_dict_has_all_required_keys() -> None:
    required_keys = {
        "route_id",
        "task_source",
        "task_type",
        "risk_class",
        "complexity_class",
        "authority_class",
        "runtime_impact",
        "backend_kind",
        "connector_kind",
        "proof_requirements",
        "audit_requirement",
        "escalation_requirement",
        "red_lane_state",
        "allowed_actions",
        "forbidden_actions",
        "stop_conditions",
        "evidence_refs",
        "unknowns",
        "confidence",
        "status",
    }
    d = RouteDecision().to_dict()
    assert required_keys <= set(d.keys())


def test_to_dict_enum_values_are_strings() -> None:
    rd = RouteDecision(
        task_source=TaskSource.OPERATOR,
        risk_class=RiskClass.RED_LANE,
        status=RouteStatus.BLOCKED,
        red_lane_state=RedLaneState.RED_LANE,
    )
    d = rd.to_dict()
    assert d["task_source"] == "OPERATOR"
    assert d["risk_class"] == "RED_LANE"
    assert d["status"] == "BLOCKED"
    assert d["red_lane_state"] == "RED_LANE"


def test_to_dict_proof_requirements_are_string_list() -> None:
    rd = RouteDecision(
        proof_requirements=[
            ProofRequirement.COMMAND_LOG,
            ProofRequirement.DIFF_STAT,
        ]
    )
    d = rd.to_dict()
    assert d["proof_requirements"] == ["COMMAND_LOG", "DIFF_STAT"]


def test_to_dict_does_not_require_external_services() -> None:
    """Serialization must be purely local — no services accessed."""
    rd = RouteDecision(
        route_id="test-route-001",
        task_source=TaskSource.OPERATOR,
        risk_class=RiskClass.R2_MEDIUM,
    )
    # If this raises, something called a service.
    d = rd.to_dict()
    assert d["route_id"] == "test-route-001"


# ─────────────────────────────────────────────
# Deserialization — from_dict
# ─────────────────────────────────────────────


def test_from_dict_round_trips_to_dict() -> None:
    original = RouteDecision(
        route_id="round-trip-001",
        task_source=TaskSource.CODEX,
        task_type=TaskType.CODE_CHANGE,
        risk_class=RiskClass.R2_MEDIUM,
        complexity_class=ComplexityClass.MEDIUM,
        authority_class=AuthorityClass.SUPERVISOR,
        runtime_impact=RuntimeImpact.LOCAL_ONLY,
        backend_kind=BackendKind.CODEX,
        connector_kind=ConnectorKind.STDIO,
        proof_requirements=[ProofRequirement.COMMAND_LOG, ProofRequirement.DIFF_STAT],
        audit_requirement=AuditRequirement.EMBEDDED_AUDITOR,
        escalation_requirement=EscalationRequirement.ON_RISK,
        red_lane_state=RedLaneState.CLEAR,
        allowed_actions=["read", "write_allowed_files"],
        forbidden_actions=["exec", "network"],
        stop_conditions=["ci_dirty"],
        evidence_refs=["proof/X/PROOF.json"],
        unknowns=["agent_authority"],
        confidence="MEDIUM",
        status=RouteStatus.ALLOWED,
    )
    d = original.to_dict()
    reconstructed = RouteDecision.from_dict(d)
    assert reconstructed.to_dict() == d


def test_from_dict_unknown_enum_falls_back_to_unknown() -> None:
    """Unrecognised enum values must fall back to UNKNOWN, not raise."""
    d = {
        "task_source": "MARTIAN_SURFACE",
        "risk_class": "CHAOS_CLASS",
        "status": "FLYING",
        "red_lane_state": "MAUVE",
        "authority_class": "ROBO_GOD",
    }
    rd = RouteDecision.from_dict(d)
    assert rd.task_source is TaskSource.UNKNOWN
    assert rd.risk_class is RiskClass.UNKNOWN
    assert rd.status is RouteStatus.UNKNOWN
    assert rd.red_lane_state is RedLaneState.UNKNOWN
    assert rd.authority_class is AuthorityClass.UNKNOWN


def test_from_dict_empty_dict_uses_safe_defaults() -> None:
    rd = RouteDecision.from_dict({})
    assert rd.task_source is TaskSource.UNKNOWN
    assert rd.status is RouteStatus.PENDING
    assert rd.confidence == "LOW"
    assert rd.red_lane_state is RedLaneState.UNKNOWN
    assert rd.proof_requirements == []


def test_from_dict_proof_requirements_parsed() -> None:
    d = {"proof_requirements": ["COMMAND_LOG", "FULL_PROOF_BUNDLE"]}
    rd = RouteDecision.from_dict(d)
    assert ProofRequirement.COMMAND_LOG in rd.proof_requirements
    assert ProofRequirement.FULL_PROOF_BUNDLE in rd.proof_requirements


def test_from_dict_proof_requirements_unknown_falls_back() -> None:
    d = {"proof_requirements": ["MAGIC_PROOF"]}
    rd = RouteDecision.from_dict(d)
    assert rd.proof_requirements == [ProofRequirement.UNKNOWN]


# ─────────────────────────────────────────────
# RED_LANE and BLOCKED in stop_conditions
# ─────────────────────────────────────────────


def test_stop_conditions_list_is_representable() -> None:
    rd = RouteDecision(
        stop_conditions=["ci_dirty", "red_lane_active", "unknown_authority"]
    )
    assert "red_lane_active" in rd.stop_conditions


def test_unknowns_list_is_representable() -> None:
    rd = RouteDecision(unknowns=["agent_authority", "mcp_surface"])
    assert "agent_authority" in rd.unknowns


# ─────────────────────────────────────────────
# Backend / connector are data, not executable
# ─────────────────────────────────────────────


def test_backend_kind_is_data_not_callable() -> None:
    rd = RouteDecision(backend_kind=BackendKind.CODEX)
    assert rd.backend_kind is BackendKind.CODEX
    # BackendKind is an Enum member, not a callable executor
    assert not callable(rd.backend_kind.value)


def test_connector_kind_is_data_not_callable() -> None:
    rd = RouteDecision(connector_kind=ConnectorKind.MCP)
    assert rd.connector_kind is ConnectorKind.MCP
    assert not callable(rd.connector_kind.value)


# ─────────────────────────────────────────────
# All UNKNOWN enum members exist
# ─────────────────────────────────────────────


def test_all_key_enums_have_unknown_member() -> None:
    """UNKNOWN must be representable for every key enum — invariant 7."""
    assert TaskSource.UNKNOWN
    assert TaskType.UNKNOWN
    assert RiskClass.UNKNOWN
    assert ComplexityClass.UNKNOWN
    assert AuthorityClass.UNKNOWN
    assert RuntimeImpact.UNKNOWN
    assert BackendKind.UNKNOWN
    assert ConnectorKind.UNKNOWN
    assert ProofRequirement.UNKNOWN
    assert AuditRequirement.UNKNOWN
    assert EscalationRequirement.UNKNOWN
    assert RedLaneState.UNKNOWN
    assert RouteStatus.UNKNOWN
