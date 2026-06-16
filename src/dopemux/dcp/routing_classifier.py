"""DCP Routing Classification Engine — DMX-DCP-MODEL-ROUTING-MVP-0002.

Pure-function classifier: maps RoutingClassificationInput → RouteDecision.

Invariants enforced by design:
- No I/O, filesystem writes, network, shell, or external services.
- Only imports stdlib and routing_model.
- Unknown / conflicting / risky inputs fail closed.
- RED_LANE state overrides any ALLOW preference.
- Proof, audit, and escalation requirements increase with risk.
- Backend and connector fields remain inert data, never callable.
- Classifier does not mutate its input.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace

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
# Input dataclass
# ─────────────────────────────────────────────

_HIGH_RISK_CLASSES = {RiskClass.R3_HIGH}


@dataclass
class RoutingClassificationInput:
    """Structured, local, in-memory task attributes for route classification.

    All defaults are conservative: the classifier fails closed unless
    attributes are explicitly set to safe values.
    """

    # Classification inputs
    task_source: TaskSource = TaskSource.UNKNOWN
    task_type: TaskType = TaskType.UNKNOWN
    risk_class: RiskClass = RiskClass.UNKNOWN
    complexity_class: ComplexityClass = ComplexityClass.UNKNOWN
    authority_class: AuthorityClass = AuthorityClass.UNKNOWN
    runtime_impact: RuntimeImpact = RuntimeImpact.UNKNOWN
    backend_kind: BackendKind = BackendKind.NONE
    connector_kind: ConnectorKind = ConnectorKind.NONE

    # Task description / evidence
    description: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    requested_actions: list[str] = field(default_factory=list)

    # Surface flags
    touches_files: bool = False
    touches_tests: bool = False
    touches_docs: bool = False
    touches_ci: bool = False
    touches_security: bool = False
    touches_auth: bool = False
    touches_secrets: bool = False
    touches_public_behavior: bool = False
    touches_destructive_path: bool = False

    # Execution requirement flags — all default to False (fail-open → fail-closed)
    requires_network: bool = False
    requires_external_service: bool = False
    requires_live_write: bool = False
    requires_runner_execution: bool = False
    requires_connector_call: bool = False
    requires_mcp_call: bool = False
    requires_dopetask_execution: bool = False
    requires_task_orchestrator_write: bool = False

    # Authority / evidence state
    has_unknown_authority: bool = True   # conservative default
    has_conflicting_evidence: bool = False
    has_stale_proof: bool = False
    has_missing_proof: bool = False

    # Scope flags
    is_repo_changing: bool = False
    is_non_trivial: bool = False


# ─────────────────────────────────────────────
# Forbidden-action constants
# ─────────────────────────────────────────────

_ALWAYS_FORBIDDEN: list[str] = [
    "execute_runner",
    "call_connector",
    "call_mcp",
    "write_github_state",
    "merge_pr",
    "touch_secrets",
    "run_destructive_command",
    "mutate_task_orchestrator",
    "execute_dopetask",
]

_READ_ONLY_ALLOWED: list[str] = [
    "inspect_runtime_code",
    "run_targeted_tests",
    "capture_proof",
]

_MUTATING_ALLOWED: list[str] = [
    "edit_allowlisted_files",
    "run_targeted_tests",
    "capture_proof",
    "run_embedded_audit",
    "open_pr",
]

_REQUESTED_ACTION_RED_LANE: frozenset[str] = frozenset(
    _ALWAYS_FORBIDDEN
    + [
        "live_write_to_service",
        "network_access",
        "external_service_access",
        "call_connector_live",
        "call_mcp_live",
        "execute_dopetask_live",
        "write_task_orchestrator",
        "execute_runner_live",
    ]
)

# ─────────────────────────────────────────────
# Helper derivers
# ─────────────────────────────────────────────


def _normalize_enum(value: object, enum_cls: type) -> object:
    """Normalize enum members and string names/values; otherwise UNKNOWN."""
    if isinstance(value, enum_cls):
        return value
    if isinstance(value, str):
        for member in enum_cls:
            if value == member.name or value == member.value:
                return member
    return enum_cls.UNKNOWN


def _normalize_input(inp: RoutingClassificationInput) -> RoutingClassificationInput:
    """Return a normalized copy without mutating caller-owned input."""
    return replace(
        inp,
        task_source=_normalize_enum(inp.task_source, TaskSource),
        task_type=_normalize_enum(inp.task_type, TaskType),
        risk_class=_normalize_enum(inp.risk_class, RiskClass),
        complexity_class=_normalize_enum(inp.complexity_class, ComplexityClass),
        authority_class=_normalize_enum(inp.authority_class, AuthorityClass),
        runtime_impact=_normalize_enum(inp.runtime_impact, RuntimeImpact),
        backend_kind=_normalize_enum(inp.backend_kind, BackendKind),
        connector_kind=_normalize_enum(inp.connector_kind, ConnectorKind),
    )


def _derive_red_lane_state(inp: RoutingClassificationInput) -> RedLaneState:
    """Return RED_LANE when any hard-block flag is set; CLEAR otherwise."""
    red_flags = (
        inp.touches_secrets
        or inp.touches_auth
        or inp.touches_security
        or inp.touches_destructive_path
        or inp.requires_network
        or inp.requires_external_service
        or inp.requires_live_write
        or inp.requires_runner_execution
        or inp.requires_connector_call
        or inp.requires_mcp_call
        or inp.requires_dopetask_execution
        or inp.requires_task_orchestrator_write
        or inp.has_conflicting_evidence
        or inp.risk_class is RiskClass.RED_LANE
        or inp.task_type is TaskType.MERGE
        or inp.task_type is TaskType.LIVE_WRITE
        or inp.runtime_impact is RuntimeImpact.SERVICE_MUTATION
        or inp.runtime_impact is RuntimeImpact.LIVE_WRITE
        or bool(_requested_forbidden_actions(inp))
    )
    return RedLaneState.RED_LANE if red_flags else RedLaneState.CLEAR


def _derive_route_status(
    inp: RoutingClassificationInput,
    red_lane: RedLaneState,
) -> RouteStatus:
    """Derive conservative route status from attributes and red-lane state.

    Status precedence is most-severe-first: a hard-BLOCKED reason outranks an
    UNKNOWN one. The hard-BLOCKED checks (red-lane, BLOCKED authority, missing
    proof on a mutating/non-trivial route, stale proof) are evaluated BEFORE the
    UNKNOWN-authority guard so that a caller inspecting ``status`` learns *why* a
    route is blocked even when authority is also unknown. An unknown-authority
    route is non-runnable regardless, so this ordering strengthens
    discoverability without weakening any fail-closed guarantee.
    """
    if red_lane is RedLaneState.RED_LANE:
        return RouteStatus.BLOCKED

    if inp.authority_class is AuthorityClass.BLOCKED:
        return RouteStatus.BLOCKED

    if inp.has_missing_proof and (_has_mutating_scope(inp) or inp.is_non_trivial):
        return RouteStatus.BLOCKED

    if inp.has_stale_proof:
        return RouteStatus.BLOCKED

    if inp.has_unknown_authority or inp.authority_class is AuthorityClass.UNKNOWN:
        return RouteStatus.UNKNOWN

    if inp.task_source is TaskSource.UNKNOWN:
        return RouteStatus.UNKNOWN

    if inp.runtime_impact is RuntimeImpact.UNKNOWN:
        return RouteStatus.UNKNOWN

    if inp.complexity_class is ComplexityClass.UNKNOWN:
        return RouteStatus.UNKNOWN

    if inp.risk_class is RiskClass.UNKNOWN or inp.task_type is TaskType.UNKNOWN:
        return RouteStatus.UNKNOWN

    if inp.complexity_class is ComplexityClass.ARCHITECTURAL:
        return RouteStatus.NEEDS_SUPERVISOR

    if inp.risk_class in _HIGH_RISK_CLASSES:
        return RouteStatus.NEEDS_SUPERVISOR

    if inp.touches_ci:
        return RouteStatus.NEEDS_SUPERVISOR

    if inp.authority_class in (AuthorityClass.SUPERVISOR, AuthorityClass.DUAL):
        return RouteStatus.NEEDS_SUPERVISOR

    if inp.authority_class is AuthorityClass.AUTOMATED_SAFE:
        return RouteStatus.ALLOWED

    if inp.authority_class is AuthorityClass.OPERATOR:
        return RouteStatus.ALLOWED

    return RouteStatus.PENDING


def _derive_proof_requirements(inp: RoutingClassificationInput) -> list[ProofRequirement]:
    """Return an increasing set of proof obligations based on risk."""
    proofs: list[ProofRequirement] = []

    if _has_mutating_scope(inp) or inp.is_non_trivial:
        proofs.append(ProofRequirement.DIFF_STAT)
        proofs.append(ProofRequirement.FULL_PROOF_BUNDLE)

    if inp.touches_tests or inp.touches_public_behavior:
        if ProofRequirement.COMMAND_LOG not in proofs:
            proofs.append(ProofRequirement.COMMAND_LOG)

    if inp.touches_ci or inp.touches_security or inp.touches_auth or inp.touches_secrets:
        for p in (ProofRequirement.FULL_PROOF_BUNDLE, ProofRequirement.AUDIT_REPORT):
            if p not in proofs:
                proofs.append(p)

    if inp.risk_class in _HIGH_RISK_CLASSES:
        for p in (ProofRequirement.AUDIT_REPORT, ProofRequirement.SUPERVISOR_REVIEW):
            if p not in proofs:
                proofs.append(p)

    if not proofs and inp.touches_files:
        proofs.append(ProofRequirement.COMMAND_LOG)

    return proofs


def _derive_audit_requirement(inp: RoutingClassificationInput) -> AuditRequirement:
    """Return the strongest audit obligation demanded by the task attributes."""
    if inp.touches_security or inp.touches_auth or inp.touches_secrets:
        return AuditRequirement.SUPERVISOR_AUDIT

    if inp.risk_class in _HIGH_RISK_CLASSES:
        return AuditRequirement.SUPERVISOR_AUDIT

    if inp.is_non_trivial and inp.is_repo_changing:
        return AuditRequirement.EMBEDDED_AUDITOR

    if inp.touches_ci or inp.touches_public_behavior:
        return AuditRequirement.EMBEDDED_AUDITOR

    if inp.requires_runner_execution or inp.requires_connector_call:
        return AuditRequirement.EMBEDDED_AUDITOR

    if _has_mutating_scope(inp) or inp.is_non_trivial:
        return AuditRequirement.SELF_CHECK

    return AuditRequirement.NONE


def _derive_escalation_requirement(
    inp: RoutingClassificationInput,
    red_lane: RedLaneState,
) -> EscalationRequirement:
    """Return escalation level based on risk, authority, and evidence state."""
    if (
        red_lane is RedLaneState.RED_LANE
        or inp.has_conflicting_evidence
        or inp.touches_security
        or inp.touches_auth
        or inp.touches_secrets
        or inp.touches_ci
        or inp.touches_destructive_path
        or inp.requires_live_write
        or inp.requires_runner_execution
        or inp.requires_connector_call
        or inp.requires_mcp_call
        or inp.has_missing_proof
        or inp.has_stale_proof
    ):
        return EscalationRequirement.ALWAYS

    if inp.has_unknown_authority or inp.authority_class is AuthorityClass.UNKNOWN:
        return EscalationRequirement.ON_UNKNOWN

    if inp.risk_class in _HIGH_RISK_CLASSES:
        return EscalationRequirement.ON_RISK

    if inp.complexity_class is ComplexityClass.ARCHITECTURAL:
        return EscalationRequirement.ON_RISK

    return EscalationRequirement.NONE


def _derive_allowed_actions(
    inp: RoutingClassificationInput,
    red_lane: RedLaneState,
    status: RouteStatus,
) -> list[str]:
    """Return actions permitted for this route.

    Mutating actions (edit_allowlisted_files, open_pr) are only permitted
    when the route is fully ALLOWED with mutating scope. requested_actions
    may only narrow the classification base set — never widen it.
    """
    if red_lane is RedLaneState.RED_LANE or status is RouteStatus.BLOCKED:
        return []

    if status is RouteStatus.ALLOWED and _has_mutating_scope(inp):
        base_allowed = list(_MUTATING_ALLOWED)
    else:
        base_allowed = list(_READ_ONLY_ALLOWED)

    if inp.requested_actions:
        return [
            action for action in inp.requested_actions if action in base_allowed
        ]
    return base_allowed


def _derive_forbidden_actions(inp: RoutingClassificationInput) -> list[str]:
    """Build the list of forbidden actions, always including hard-block set."""
    forbidden = list(_ALWAYS_FORBIDDEN)

    if inp.requires_network:
        _append_unique(forbidden, "network_access")
    if inp.requires_external_service:
        _append_unique(forbidden, "external_service_access")
    if inp.task_type is TaskType.MERGE:
        _append_unique(forbidden, "merge_task")
    if (
        inp.requires_live_write
        or inp.task_type is TaskType.LIVE_WRITE
        or inp.runtime_impact is RuntimeImpact.SERVICE_MUTATION
        or inp.runtime_impact is RuntimeImpact.LIVE_WRITE
    ):
        _append_unique(forbidden, "live_write_to_service")
    if inp.requires_connector_call:
        _append_unique(forbidden, "call_connector_live")
    if inp.requires_mcp_call:
        _append_unique(forbidden, "call_mcp_live")
    if inp.requires_dopetask_execution:
        _append_unique(forbidden, "execute_dopetask_live")
    if inp.requires_task_orchestrator_write:
        _append_unique(forbidden, "write_task_orchestrator")
    if inp.requires_runner_execution:
        _append_unique(forbidden, "execute_runner_live")

    return forbidden


def _derive_stop_conditions(
    inp: RoutingClassificationInput,
    red_lane: RedLaneState,
) -> list[str]:
    """Enumerate stop conditions that gate execution."""
    conditions: list[str] = []

    if red_lane is RedLaneState.RED_LANE:
        conditions.append("red_lane_active")
    if inp.has_unknown_authority or inp.authority_class is AuthorityClass.UNKNOWN:
        conditions.append("unknown_authority")
    if inp.has_conflicting_evidence:
        conditions.append("conflicting_evidence")
    if inp.has_missing_proof:
        conditions.append("missing_proof")
    if inp.has_stale_proof:
        conditions.append("stale_proof")
    if inp.touches_secrets:
        conditions.append("secrets_surface_in_scope")
    if inp.touches_auth:
        conditions.append("auth_surface_in_scope")
    if inp.touches_ci:
        conditions.append("ci_surface_in_scope")
    if inp.requires_network:
        conditions.append("network_required")
    if inp.requires_external_service:
        conditions.append("external_service_required")
    if inp.task_type is TaskType.MERGE:
        conditions.append("merge_task_requested")
    if inp.runtime_impact is RuntimeImpact.SERVICE_MUTATION:
        conditions.append("service_mutation_requested")
    if (
        inp.requires_live_write
        or inp.task_type is TaskType.LIVE_WRITE
        or inp.runtime_impact is RuntimeImpact.LIVE_WRITE
    ):
        conditions.append("live_write_requested")
    if inp.requires_runner_execution:
        conditions.append("runner_execution_requested")
    forbidden_requested = _requested_forbidden_actions(inp)
    if forbidden_requested:
        conditions.append("forbidden_requested_action")
        for action in forbidden_requested:
            conditions.append(f"forbidden_action_requested:{action}")

    return conditions


def _collect_unknowns(inp: RoutingClassificationInput) -> list[str]:
    """Record which authority/risk dimensions are unknown."""
    unknowns: list[str] = []
    if inp.task_source is TaskSource.UNKNOWN:
        unknowns.append("task_source_unknown")
    if inp.authority_class is AuthorityClass.UNKNOWN or inp.has_unknown_authority:
        unknowns.append("authority_class_unknown")
    if inp.task_type is TaskType.UNKNOWN:
        unknowns.append("task_type_unknown")
    if inp.risk_class is RiskClass.UNKNOWN:
        unknowns.append("risk_class_unknown")
    if inp.runtime_impact is RuntimeImpact.UNKNOWN:
        unknowns.append("runtime_impact_unknown")
    if inp.complexity_class is ComplexityClass.UNKNOWN:
        unknowns.append("complexity_class_unknown")
    return unknowns


def _append_unique(lst: list[str], item: str) -> None:
    if item not in lst:
        lst.append(item)


def _requested_forbidden_actions(inp: RoutingClassificationInput) -> list[str]:
    """Return requested actions that are explicitly never delegated."""
    return [
        action
        for action in inp.requested_actions
        if action in _REQUESTED_ACTION_RED_LANE
    ]


def _has_mutating_scope(inp: RoutingClassificationInput) -> bool:
    """Return True only when a route is explicitly repo/code/proof changing."""
    return (
        inp.is_repo_changing
        or inp.touches_files
        or inp.touches_tests
        or inp.touches_docs
        or inp.touches_public_behavior
        or inp.task_type
        in (TaskType.CODE_CHANGE, TaskType.SCHEMA_ONLY, TaskType.PROOF_BUNDLE)
    )


def _stable_route_id(inp: RoutingClassificationInput) -> str:
    """Return a deterministic route identifier for replayable decisions."""
    payload = (
        inp.task_source.value,
        inp.task_type.value,
        inp.risk_class.value,
        inp.complexity_class.value,
        inp.authority_class.value,
        inp.runtime_impact.value,
        inp.backend_kind.value,
        inp.connector_kind.value,
        inp.description,
        tuple(inp.evidence_refs),
        tuple(inp.requested_actions),
        inp.touches_files,
        inp.touches_tests,
        inp.touches_docs,
        inp.touches_ci,
        inp.touches_security,
        inp.touches_auth,
        inp.touches_secrets,
        inp.touches_public_behavior,
        inp.touches_destructive_path,
        inp.requires_network,
        inp.requires_external_service,
        inp.requires_live_write,
        inp.requires_runner_execution,
        inp.requires_connector_call,
        inp.requires_mcp_call,
        inp.requires_dopetask_execution,
        inp.requires_task_orchestrator_write,
        inp.has_unknown_authority,
        inp.has_conflicting_evidence,
        inp.has_stale_proof,
        inp.has_missing_proof,
        inp.is_repo_changing,
        inp.is_non_trivial,
    )
    return str(uuid.uuid5(uuid.NAMESPACE_URL, repr(payload)))


# ─────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────


def classify_route(inp: RoutingClassificationInput) -> RouteDecision:
    """Classify a task's routing attributes into a conservative RouteDecision.

    Pure function: no I/O, no mutation of *inp*, no external calls.
    """
    normalized = _normalize_input(inp)

    red_lane = _derive_red_lane_state(normalized)
    status = _derive_route_status(normalized, red_lane)
    proof_reqs = _derive_proof_requirements(normalized)
    audit_req = _derive_audit_requirement(normalized)
    escalation_req = _derive_escalation_requirement(normalized, red_lane)
    allowed = _derive_allowed_actions(normalized, red_lane, status)
    forbidden = _derive_forbidden_actions(normalized)
    stop_conds = _derive_stop_conditions(normalized, red_lane)
    unknowns = _collect_unknowns(normalized)

    confidence = "LOW" if unknowns or red_lane is RedLaneState.RED_LANE else "MEDIUM"

    return RouteDecision(
        route_id=_stable_route_id(normalized),
        task_source=normalized.task_source,
        task_type=normalized.task_type,
        risk_class=normalized.risk_class,
        complexity_class=normalized.complexity_class,
        authority_class=normalized.authority_class,
        runtime_impact=normalized.runtime_impact,
        backend_kind=normalized.backend_kind,
        connector_kind=normalized.connector_kind,
        proof_requirements=proof_reqs,
        audit_requirement=audit_req,
        escalation_requirement=escalation_req,
        red_lane_state=red_lane,
        allowed_actions=allowed,
        forbidden_actions=forbidden,
        stop_conditions=stop_conds,
        evidence_refs=list(normalized.evidence_refs),
        unknowns=unknowns,
        confidence=confidence,
        status=status,
    )
