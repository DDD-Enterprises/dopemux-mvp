"""DCP Lane Engine — DMX-DCP-MODEL-ROUTING-MVP-0005.

Pure-function engine: maps (RouteDecision, RoutingClassificationInput) → LaneDecision.

Invariants enforced by design:
- No I/O, network, shell, filesystem, external services.
- Only imports stdlib and dopemux.dcp model/classifier/lane_model.
- Classifier decision is the authoritative gate; this engine never re-derives safety.
- RED_LANE or BLOCKED status always → LaneKind.BLOCKED, is_executable=False, allowed_actions=().
- allowed_actions ⊆ decision.allowed_actions (inherited; never widened).
- EXTERNAL_INTAKE and BLOCKED are never executable.
- is_executable is stricter than RouteDecision.is_runnable() when lane safety requires.
- Proof, audit, escalation are surfaced (inherited), not flattened.
- decide_lane() does not mutate its inputs.
"""

from __future__ import annotations

from dopemux.dcp.lane_model import LaneDecision, LaneKind
from dopemux.dcp.routing_classifier import RoutingClassificationInput
from dopemux.dcp.routing_model import (
    AuditRequirement,
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

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

# Lanes that may be executable when the gate conditions are met.
# BLOCKED and EXTERNAL_INTAKE are never in this set.
_EXECUTABLE_LANES: frozenset[LaneKind] = frozenset({
    LaneKind.READ_ONLY_EVIDENCE,
    LaneKind.DOCS_ONLY,
    LaneKind.PROOF_ONLY,
    LaneKind.CLASSIFIER_ROUTING,
    LaneKind.LOCAL_CODE_IMPLEMENTATION,
    LaneKind.TEST_VALIDATION,
    LaneKind.EMBEDDED_AUDIT,
    LaneKind.PR_STEWARD_READINESS,
})

# External agent task sources — used for EXTERNAL_INTAKE lane detection.
_EXTERNAL_TASK_SOURCES: frozenset[TaskSource] = frozenset({
    TaskSource.CODEX,
    TaskSource.CLAUDE,
    TaskSource.OPENCODE,
    TaskSource.GROK,
    TaskSource.GEMINI,
    TaskSource.AGY,
})

# Extra tokens EXTERNAL_INTAKE adds to forbidden_actions
_EXTERNAL_INTAKE_EXTRA_FORBIDDEN: tuple[str, ...] = (
    "execute",
    "import",
    "install",
)

# Mutating actions that must never appear on passive or blocked lane decisions.
_MUTATING_ACTIONS: frozenset[str] = frozenset({
    "edit_allowlisted_files",
    "open_pr",
    "commit_changes",
    "merge_pr",
    "apply_patch",
    "run_dopetask_execution",
    "run_live_write",
    "call_mcp",
    "run_embedded_audit",
})

# Passive lanes must never expose mutating actions, even when otherwise executable.
_PASSIVE_LANES: frozenset[LaneKind] = frozenset({
    LaneKind.READ_ONLY_EVIDENCE,
    LaneKind.EMBEDDED_AUDIT,
    LaneKind.PR_STEWARD_READINESS,
    LaneKind.EXTERNAL_INTAKE,
    LaneKind.BLOCKED,
})

# Read-only / proof-safe actions permitted when the lane is not executable.
_READ_ONLY_PROOF_SAFE_ACTIONS: frozenset[str] = frozenset({
    "inspect_runtime_code",
    "run_targeted_tests",
    "capture_proof",
})


def _has_mutating_intent(inp: RoutingClassificationInput) -> bool:
    """Return True for repo-changing scope or explicitly mutating requested actions."""
    return (
        inp.is_repo_changing
        or inp.touches_files
        or inp.touches_public_behavior
        or any(action in _MUTATING_ACTIONS for action in inp.requested_actions)
    )


def _has_mutating_scope(inp: RoutingClassificationInput) -> bool:
    """Return True when classifier scope flags indicate mutation is in play."""
    return (
        inp.is_repo_changing
        or inp.touches_files
        or inp.touches_public_behavior
    )


def _has_unknown_decision_contract(decision: RouteDecision) -> bool:
    """Fail closed on restored/incomplete decisions with UNKNOWN contract fields."""
    return (
        decision.task_source is TaskSource.UNKNOWN
        or decision.task_type is TaskType.UNKNOWN
        or decision.risk_class is RiskClass.UNKNOWN
        or decision.complexity_class is ComplexityClass.UNKNOWN
        or decision.runtime_impact is RuntimeImpact.UNKNOWN
        or any(req is ProofRequirement.UNKNOWN for req in decision.proof_requirements)
        or decision.audit_requirement is AuditRequirement.UNKNOWN
        or decision.escalation_requirement is EscalationRequirement.UNKNOWN
    )


# ─────────────────────────────────────────────
# Gate helper
# ─────────────────────────────────────────────


def _has_blocking_stop_or_escalation(decision: RouteDecision) -> bool:
    """Return True when unresolved stop conditions or mandatory escalation block work."""
    if decision.stop_conditions:
        return True
    return decision.escalation_requirement is not EscalationRequirement.NONE


def _compute_is_executable(decision: RouteDecision, lane: LaneKind) -> bool:
    """Return True only when the lane is executable AND the decision is runnable.

    Stricter than raw ``RouteDecision.is_runnable()``: also fail-closes on restored
    UNKNOWN contract fields, UNKNOWN proof requirements, stop conditions, and
    mandatory escalation. BLOCKED and EXTERNAL_INTAKE are never in
    ``_EXECUTABLE_LANES``.
    """
    if lane not in _EXECUTABLE_LANES:
        return False
    if _has_unknown_decision_contract(decision):
        return False
    if _has_blocking_stop_or_escalation(decision):
        return False
    return decision.is_runnable()


def _strip_mutating_actions(actions: tuple[str, ...]) -> tuple[str, ...]:
    """Remove mutating tokens from an allowed-action tuple."""
    return tuple(a for a in actions if a not in _MUTATING_ACTIONS)


def _narrow_allowed_actions_for_non_runnable(
    actions: tuple[str, ...],
) -> tuple[str, ...]:
    """Fail-closed: strip mutating actions from non-executable lane decisions."""
    return _strip_mutating_actions(
        tuple(a for a in actions if a in _READ_ONLY_PROOF_SAFE_ACTIONS)
    )


# ─────────────────────────────────────────────
# Lane assignment — precedence-ordered, first match wins
# ─────────────────────────────────────────────


def _assign_lane(
    decision: RouteDecision,
    inp: RoutingClassificationInput,
) -> LaneKind:
    """Return the LaneKind for this route using precedence-ordered matching.

    The classifier's decision is the authoritative gate.  inp is used only to
    pick the lane KIND — it never overrides the decision's safety verdict.

    Precedence order (spec table rows 1–10):
    1. RED_LANE or BLOCKED → BLOCKED
    2. task_type is AUDIT → EMBEDDED_AUDIT
    3. "pr_steward_readiness" in requested_actions with no mutating intent → PR_STEWARD_READINESS
    4. External agent + READ_ONLY + evidence_refs + no code/test/docs scope → EXTERNAL_INTAKE
    5. task_type is PROOF_BUNDLE → PROOF_ONLY
    6. touches_tests and not touches_files → TEST_VALIDATION
    7. touches_docs and not (touches_files or touches_tests) and task_type not in {CODE_CHANGE, SCHEMA_ONLY} → DOCS_ONLY
    8. task_type in {CODE_CHANGE, SCHEMA_ONLY} or mutating scope → LOCAL_CODE_IMPLEMENTATION
    9. task_type is DESIGN_ONLY → CLASSIFIER_ROUTING
    10. fallback → READ_ONLY_EVIDENCE
    """
    # Row 1: hard block gate
    if (
        decision.red_lane_state is RedLaneState.RED_LANE
        or decision.status is RouteStatus.BLOCKED
    ):
        return LaneKind.BLOCKED

    # Row 2: audit task
    if decision.task_type is TaskType.AUDIT:
        return LaneKind.EMBEDDED_AUDIT

    # Row 3: PR steward readiness
    if "pr_steward_readiness" in inp.requested_actions and not _has_mutating_intent(inp):
        return LaneKind.PR_STEWARD_READINESS

    # Row 4: external intake — external agent, READ_ONLY, evidence refs, no scope mutations
    if (
        decision.task_source in _EXTERNAL_TASK_SOURCES
        and decision.task_type is TaskType.READ_ONLY
        and bool(inp.evidence_refs)
        and not inp.touches_files
        and not inp.touches_tests
        and not inp.touches_docs
    ):
        return LaneKind.EXTERNAL_INTAKE

    # Row 5: proof bundle
    if decision.task_type is TaskType.PROOF_BUNDLE:
        return LaneKind.PROOF_ONLY

    # Row 6: test-only scope
    if inp.touches_tests and not inp.touches_files:
        return LaneKind.TEST_VALIDATION

    # Row 7: docs-only scope (not code/test types, no file or test touches)
    if (
        inp.touches_docs
        and not inp.touches_files
        and not inp.touches_tests
        and decision.task_type not in (TaskType.CODE_CHANGE, TaskType.SCHEMA_ONLY)
    ):
        return LaneKind.DOCS_ONLY

    # Row 8: code / schema implementation or any mutating scope
    if (
        decision.task_type in (TaskType.CODE_CHANGE, TaskType.SCHEMA_ONLY)
        or _has_mutating_scope(inp)
    ):
        return LaneKind.LOCAL_CODE_IMPLEMENTATION

    # Row 9: design/routing classification
    if decision.task_type is TaskType.DESIGN_ONLY:
        return LaneKind.CLASSIFIER_ROUTING

    # Row 10: fallback
    return LaneKind.READ_ONLY_EVIDENCE


# ─────────────────────────────────────────────
# Rationale builder
# ─────────────────────────────────────────────


def _build_rationale(
    decision: RouteDecision,
    inp: RoutingClassificationInput,
    lane: LaneKind,
    is_executable: bool,
) -> tuple[str, ...]:
    """Return an ordered tuple of labels explaining the lane assignment."""
    labels: list[str] = []

    if decision.red_lane_state is RedLaneState.RED_LANE:
        labels.append("red_lane_blocked")
    if decision.status is RouteStatus.BLOCKED:
        labels.append("status_blocked")
    if lane is LaneKind.BLOCKED:
        if not labels:
            labels.append("blocked_by_gate")
        return tuple(labels)

    labels.append(f"status_{decision.status.value.lower()}")

    if decision.task_type is TaskType.AUDIT:
        labels.append("task_type_audit")
    elif "pr_steward_readiness" in inp.requested_actions:
        labels.append("requested_pr_steward_readiness")
    elif lane is LaneKind.EXTERNAL_INTAKE:
        labels.append("external_agent_read_only_intake")
    elif decision.task_type is TaskType.PROOF_BUNDLE:
        labels.append("task_type_proof_bundle")
    elif lane is LaneKind.TEST_VALIDATION:
        labels.append("touches_tests_only")
    elif lane is LaneKind.DOCS_ONLY:
        labels.append("touches_docs_only")
    elif lane is LaneKind.LOCAL_CODE_IMPLEMENTATION:
        labels.append("task_type_code_change")
    elif lane is LaneKind.CLASSIFIER_ROUTING:
        labels.append("task_type_design_only")
    else:
        labels.append("fallback_read_only_evidence")

    if is_executable:
        labels.append("gate_pass_executable")
    else:
        labels.append("gate_fail_not_executable")

    return tuple(labels)


# ─────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────


def decide_lane(
    decision: RouteDecision,
    classification_input: RoutingClassificationInput,
) -> LaneDecision:
    """Map a RouteDecision + RoutingClassificationInput into an explicit LaneDecision.

    Pure function: no I/O, no mutation of inputs, no external calls.

    Parameters
    ----------
    decision:
        Authoritative safety gate from classify_route(). Status, red_lane_state,
        allowed/forbidden actions, proof/audit/escalation, stop_conditions are
        all read but never overridden.
    classification_input:
        Intent signals for picking lane KIND (task_type, task_source, scope flags,
        evidence_refs, requested_actions). Never used to override the gate.

    Returns
    -------
    LaneDecision
        Frozen, pure data. is_executable reflects the gate, not the lane alone.
    """
    lane = _assign_lane(decision, classification_input)
    is_exec = _compute_is_executable(decision, lane)

    # allowed_actions: inherit from decision; never widen.
    # BLOCKED / EXTERNAL_INTAKE → always ()
    # Non-executable → read-only/proof-safe only (mutating actions stripped)
    if lane is LaneKind.BLOCKED or lane is LaneKind.EXTERNAL_INTAKE:
        allowed_actions: tuple[str, ...] = ()
    elif not is_exec:
        allowed_actions = _narrow_allowed_actions_for_non_runnable(
            tuple(decision.allowed_actions)
        )
    elif lane in _PASSIVE_LANES:
        allowed_actions = _strip_mutating_actions(tuple(decision.allowed_actions))
    else:
        allowed_actions = tuple(decision.allowed_actions)

    # forbidden_actions: inherit from decision; EXTERNAL_INTAKE adds extras.
    base_forbidden = tuple(decision.forbidden_actions)
    if lane is LaneKind.EXTERNAL_INTAKE:
        # Add execute/import/install without duplicating
        existing = set(base_forbidden)
        extras = tuple(
            t for t in _EXTERNAL_INTAKE_EXTRA_FORBIDDEN if t not in existing
        )
        forbidden_actions: tuple[str, ...] = base_forbidden + extras
    else:
        forbidden_actions = base_forbidden

    # proof_requirements, audit_requirement, escalation_requirement: inherited
    proof_requirements = tuple(decision.proof_requirements)
    audit_requirement = decision.audit_requirement
    escalation_requirement = decision.escalation_requirement

    # stop_conditions: inherited
    stop_conditions = tuple(decision.stop_conditions)

    rationale = _build_rationale(decision, classification_input, lane, is_exec)

    return LaneDecision(
        lane=lane,
        route_status=decision.status,
        is_executable=is_exec,
        allowed_actions=allowed_actions,
        forbidden_actions=forbidden_actions,
        proof_requirements=proof_requirements,
        audit_requirement=audit_requirement,
        escalation_requirement=escalation_requirement,
        stop_conditions=stop_conditions,
        rationale=rationale,
    )


__all__ = [
    "decide_lane",
]
