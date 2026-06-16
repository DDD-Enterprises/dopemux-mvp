"""Pure backend policy recommendations for DCP routing decisions.

Backend preferences here are inert data only. They do not authorize execution
and do not call runners, connectors, tools, services, or external systems.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from dopemux.dcp.routing_model import (
    AuditRequirement,
    AuthorityClass,
    BackendKind,
    ComplexityClass,
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

POLICY_VERSION = "DMX-DCP-MODEL-ROUTING-MVP-0003"

_CODE_TASK_TYPES = {
    TaskType.CODE_CHANGE,
    TaskType.SCHEMA_ONLY,
    TaskType.PROOF_BUNDLE,
}

_DOC_TASK_TYPES = {
    TaskType.DESIGN_ONLY,
}

_AUDIT_TASK_TYPES = {
    TaskType.AUDIT,
}

_UNKNOWN_TASK_TYPES = {
    TaskType.UNKNOWN,
}

_UNKNOWN_TASK_SOURCES = {
    TaskSource.UNKNOWN,
}

_UNKNOWN_RISK_CLASSES = {
    RiskClass.UNKNOWN,
}

_UNKNOWN_COMPLEXITY_CLASSES = {
    ComplexityClass.UNKNOWN,
}

_UNKNOWN_RUNTIME_IMPACTS = {
    RuntimeImpact.UNKNOWN,
}

_UNKNOWN_AUDIT_REQUIREMENTS = {
    AuditRequirement.UNKNOWN,
}

_UNKNOWN_PROOF_REQUIREMENTS = {
    ProofRequirement.UNKNOWN,
}

_LIVE_TASK_TYPES = {
    TaskType.MERGE,
    TaskType.LIVE_WRITE,
}

_LIVE_RUNTIME_IMPACTS = {
    RuntimeImpact.SERVICE_MUTATION,
    RuntimeImpact.LIVE_WRITE,
}

_SUPERVISOR_RISKS = {
    RiskClass.R3_HIGH,
    RiskClass.RED_LANE,
    RiskClass.UNKNOWN,
}

_SUPERVISOR_AUTHORITY_CLASSES = {
    AuthorityClass.SUPERVISOR,
    AuthorityClass.DUAL,
}

_SUPERVISOR_AUDIT_REQUIREMENTS = {
    AuditRequirement.SUPERVISOR_AUDIT,
}

_BLOCKING_FORBIDDEN_ACTIONS = frozenset(
    {
        "network_access",
        "external_service_access",
        "merge_task",
        "live_write_to_service",
        "call_connector_live",
        "call_mcp_live",
        "execute_dopetask_live",
        "write_task_orchestrator",
        "execute_runner_live",
    }
)


@dataclass(frozen=True)
class BackendPolicyRule:
    """A pure data rule mapping route shapes to backend preferences."""

    task_types: tuple[TaskType, ...]
    preferred_backend: BackendKind
    fallback_backends: tuple[BackendKind, ...] = ()
    reason_code: str = "no_policy_match"

    def matches(self, decision: RouteDecision) -> bool:
        """Return True when this inert rule applies to the decision data."""
        return decision.task_type in self.task_types


@dataclass(frozen=True)
class BackendPolicyRecommendation:
    """Inert backend preference data for an already-classified route."""

    preferred_backend: BackendKind = BackendKind.NONE
    fallback_backends: list[BackendKind] = field(default_factory=list)
    blocked: bool = True
    requires_supervisor: bool = False
    reason_codes: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    audit_requirement: AuditRequirement = AuditRequirement.UNKNOWN
    escalation_requirement: EscalationRequirement = EscalationRequirement.UNKNOWN
    policy_version: str = POLICY_VERSION

    def is_executable_recommendation(self) -> bool:
        """Return True only when policy data suggests a backend candidate.

        This is not execution authorization. Callers must still enforce their
        own approval, proof, and runtime gates before doing any work.
        """
        return (
            not self.blocked
            and self.preferred_backend
            not in (BackendKind.NONE, BackendKind.UNKNOWN)
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize recommendation data into stable primitive values."""
        return {
            "preferred_backend": self.preferred_backend.value,
            "fallback_backends": [item.value for item in self.fallback_backends],
            "blocked": self.blocked,
            "requires_supervisor": self.requires_supervisor,
            "reason_codes": list(self.reason_codes),
            "notes": list(self.notes),
            "audit_requirement": self.audit_requirement.value,
            "escalation_requirement": self.escalation_requirement.value,
            "policy_version": self.policy_version,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BackendPolicyRecommendation":
        """Construct recommendation data from primitive values."""

        def _backend(value: object) -> BackendKind:
            try:
                return BackendKind(str(value))
            except ValueError:
                return BackendKind.NONE

        def _audit(value: object) -> AuditRequirement:
            try:
                return AuditRequirement(str(value))
            except ValueError:
                return AuditRequirement.UNKNOWN

        def _escalation(value: object) -> EscalationRequirement:
            try:
                return EscalationRequirement(str(value))
            except ValueError:
                return EscalationRequirement.UNKNOWN

        return cls(
            preferred_backend=_backend(data.get("preferred_backend", "NONE")),
            fallback_backends=[
                _backend(item) for item in data.get("fallback_backends", [])
            ],
            blocked=bool(data.get("blocked", True)),
            requires_supervisor=bool(data.get("requires_supervisor", False)),
            reason_codes=sorted(set(data.get("reason_codes", []))),
            notes=list(data.get("notes", [])),
            audit_requirement=_audit(data.get("audit_requirement", "UNKNOWN")),
            escalation_requirement=_escalation(
                data.get("escalation_requirement", "UNKNOWN")
            ),
            policy_version=str(data.get("policy_version", POLICY_VERSION)),
        )


_SAFE_RULES: tuple[BackendPolicyRule, ...] = (
    BackendPolicyRule(
        task_types=tuple(sorted(_AUDIT_TASK_TYPES, key=lambda item: item.value)),
        preferred_backend=BackendKind.AGY,
        fallback_backends=(BackendKind.CLAUDE_CODE, BackendKind.GEMINI_CLI),
        reason_code="safe_audit_route",
    ),
    BackendPolicyRule(
        task_types=tuple(sorted(_DOC_TASK_TYPES, key=lambda item: item.value)),
        preferred_backend=BackendKind.CODEX,
        fallback_backends=(BackendKind.CLAUDE_CODE,),
        reason_code="safe_docs_route",
    ),
    BackendPolicyRule(
        task_types=tuple(sorted(_CODE_TASK_TYPES, key=lambda item: item.value)),
        preferred_backend=BackendKind.CODEX,
        fallback_backends=(BackendKind.CLAUDE_CODE, BackendKind.GEMINI_CLI),
        reason_code="safe_low_risk_code_route",
    ),
)


def select_backend_policy(
    decision: RouteDecision,
) -> BackendPolicyRecommendation:
    """Return an inert backend policy recommendation for *decision*."""
    block_reasons = _block_reasons(decision)
    requires_supervisor = _requires_supervisor(decision)

    if block_reasons:
        return _blocked_recommendation(
            decision,
            reason_codes=block_reasons,
            requires_supervisor=requires_supervisor,
        )

    for rule in _SAFE_RULES:
        if rule.matches(decision):
            return BackendPolicyRecommendation(
                preferred_backend=rule.preferred_backend,
                fallback_backends=list(rule.fallback_backends),
                blocked=False,
                requires_supervisor=False,
                reason_codes=[rule.reason_code],
                notes=[
                    "Backend preference is inert data and does not authorize execution."
                ],
                audit_requirement=decision.audit_requirement,
                escalation_requirement=decision.escalation_requirement,
            )

    return _blocked_recommendation(
        decision,
        reason_codes=["no_policy_match"],
        requires_supervisor=requires_supervisor,
    )


def explain_backend_policy(decision: RouteDecision) -> list[str]:
    """Return deterministic explanation strings for the selected policy."""
    recommendation = select_backend_policy(decision)
    if recommendation.blocked:
        return [
            f"blocked:{code}" for code in recommendation.reason_codes
        ]
    return [
        f"preferred_backend:{recommendation.preferred_backend.value}",
        *[f"reason:{code}" for code in recommendation.reason_codes],
    ]


def _blocked_recommendation(
    decision: RouteDecision,
    *,
    reason_codes: list[str],
    requires_supervisor: bool,
) -> BackendPolicyRecommendation:
    return BackendPolicyRecommendation(
        preferred_backend=BackendKind.NONE,
        fallback_backends=[],
        blocked=True,
        requires_supervisor=requires_supervisor,
        reason_codes=sorted(set(reason_codes)) or ["route_status_not_allowed"],
        notes=[
            "No executable backend recommendation is available for this route."
        ],
        audit_requirement=decision.audit_requirement,
        escalation_requirement=decision.escalation_requirement,
    )


def _block_reasons(decision: RouteDecision) -> list[str]:
    reasons: list[str] = []

    if decision.status is not RouteStatus.ALLOWED:
        reasons.append("route_status_not_allowed")
    if decision.red_lane_state is not RedLaneState.CLEAR:
        reasons.append("red_lane_active")
    if not decision.is_runnable():
        reasons.append("route_status_not_allowed")
    if decision.escalation_requirement is not EscalationRequirement.NONE:
        reasons.append("escalation_required")
    if decision.unknowns:
        reasons.append("unknowns_present")
    if _has_unknown_dimension(decision):
        reasons.append("unknowns_present")
    if decision.stop_conditions:
        reasons.append("stop_conditions_present")
    if _has_stop_condition(decision, "missing_proof"):
        reasons.append("missing_proof")
    if _has_stop_condition(decision, "stale_proof"):
        reasons.append("stale_proof")
    if _has_forbidden_action_marker(decision):
        reasons.append("forbidden_action_present")
    if _has_live_runtime_shape(decision):
        reasons.append("live_runtime_present")
    if _requires_supervisor(decision):
        reasons.append("risk_requires_supervisor")

    return sorted(set(reasons))


def _requires_supervisor(decision: RouteDecision) -> bool:
    return (
        decision.status is RouteStatus.NEEDS_SUPERVISOR
        or decision.risk_class in _SUPERVISOR_RISKS
        or decision.authority_class in _SUPERVISOR_AUTHORITY_CLASSES
        or decision.audit_requirement in _SUPERVISOR_AUDIT_REQUIREMENTS
        or decision.escalation_requirement
        is not EscalationRequirement.NONE
    )


def _has_stop_condition(decision: RouteDecision, marker: str) -> bool:
    return any(marker in condition for condition in decision.stop_conditions)


def _has_unknown_dimension(decision: RouteDecision) -> bool:
    return (
        decision.task_source in _UNKNOWN_TASK_SOURCES
        or decision.task_type in _UNKNOWN_TASK_TYPES
        or decision.risk_class in _UNKNOWN_RISK_CLASSES
        or decision.complexity_class in _UNKNOWN_COMPLEXITY_CLASSES
        or decision.runtime_impact in _UNKNOWN_RUNTIME_IMPACTS
        or decision.audit_requirement in _UNKNOWN_AUDIT_REQUIREMENTS
        or any(
            requirement in _UNKNOWN_PROOF_REQUIREMENTS
            for requirement in decision.proof_requirements
        )
    )


def _has_live_runtime_shape(decision: RouteDecision) -> bool:
    return (
        decision.task_type in _LIVE_TASK_TYPES
        or decision.runtime_impact in _LIVE_RUNTIME_IMPACTS
    )


def _has_forbidden_action_marker(decision: RouteDecision) -> bool:
    return any(
        action in _BLOCKING_FORBIDDEN_ACTIONS
        for action in decision.forbidden_actions
    )


__all__ = [
    "BackendPolicyRecommendation",
    "BackendPolicyRule",
    "explain_backend_policy",
    "select_backend_policy",
]
