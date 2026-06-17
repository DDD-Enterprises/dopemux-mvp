"""DCP Lane Model — DMX-DCP-MODEL-ROUTING-MVP-0005.

Pure data types for DCP lane classification decisions.

Invariants enforced by design:
- No I/O, network, shell, filesystem, external services.
- Only imports stdlib and dopemux.dcp routing_model.
- LaneDecision is frozen — immutable after construction.
- allowed_actions is always a subset of the RouteDecision's allowed_actions.
- BLOCKED and EXTERNAL_INTAKE are never executable.
- Deferred lanes (SECURE_MCP_FACADE, RUNNER_BACKEND_EXECUTION,
  CONNECTOR_CALL_EXECUTION, FUTURE_LIVE_WRITE) are NOT members of this enum —
  they are out of scope for this MVP.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from dopemux.dcp.routing_model import (
    AuditRequirement,
    EscalationRequirement,
    ProofRequirement,
    RouteStatus,
)


# ─────────────────────────────────────────────
# LaneKind — 10 members exactly as in the spec
# ─────────────────────────────────────────────


class LaneKind(Enum):
    """Explicit lane classification for a DCP route decision.

    Members
    -------
    READ_ONLY_EVIDENCE
        Passive evidence-gathering only; no mutations.
    DOCS_ONLY
        Documentation / design changes, no code or test scope.
    PROOF_ONLY
        Proof-bundle construction; no live execution.
    CLASSIFIER_ROUTING
        Design-only routing / classification task (DESIGN_ONLY).
    LOCAL_CODE_IMPLEMENTATION
        Local code / schema change; audit obligation inherited.
    TEST_VALIDATION
        Test files only; no production code changes.
    EMBEDDED_AUDIT
        Independent audit run; no production mutations.
    PR_STEWARD_READINESS
        PR-Steward pre-flight readiness check (read-only, no merge).
    EXTERNAL_INTAKE
        External-agent evidence intake; never executable.
    BLOCKED
        Hard-blocked route; never executable.

    Deferred (NOT in this enum):
        SECURE_MCP_FACADE, RUNNER_BACKEND_EXECUTION,
        CONNECTOR_CALL_EXECUTION, FUTURE_LIVE_WRITE
    """

    READ_ONLY_EVIDENCE = "read_only_evidence"
    DOCS_ONLY = "docs_only"
    PROOF_ONLY = "proof_only"
    CLASSIFIER_ROUTING = "classifier_routing"
    LOCAL_CODE_IMPLEMENTATION = "local_code_implementation"
    TEST_VALIDATION = "test_validation"
    EMBEDDED_AUDIT = "embedded_audit"
    PR_STEWARD_READINESS = "pr_steward_readiness"
    EXTERNAL_INTAKE = "external_intake"
    BLOCKED = "blocked"


# ─────────────────────────────────────────────
# LaneDecision — frozen dataclass
# ─────────────────────────────────────────────


@dataclass(frozen=True)
class LaneDecision:
    """Immutable result of lane classification for a single RouteDecision.

    Fields
    ------
    lane
        The lane kind assigned to this route.
    route_status
        The RouteDecision's status, carried through for caller convenience.
    is_executable
        True only when status is ALLOWED, red_lane_state is CLEAR, and
        lane is in the executable set. BLOCKED and EXTERNAL_INTAKE are
        never executable.
    allowed_actions
        Subset of RouteDecision.allowed_actions; never widened by the engine.
        EXTERNAL_INTAKE narrows to ().
    forbidden_actions
        Superset of RouteDecision.forbidden_actions; engine may add extras
        (e.g. EXTERNAL_INTAKE adds execute/import/install).
    proof_requirements
        Inherited from RouteDecision.proof_requirements; engine may only
        strengthen, never weaken.
    audit_requirement
        Inherited from RouteDecision.audit_requirement; never flattened.
    escalation_requirement
        Inherited from RouteDecision.escalation_requirement; never flattened.
    stop_conditions
        Inherited from RouteDecision.stop_conditions; engine may add extras.
    rationale
        Ordered tuple of labels explaining the lane assignment and gate.
    """

    lane: LaneKind
    route_status: RouteStatus
    is_executable: bool
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    proof_requirements: tuple[ProofRequirement, ...]
    audit_requirement: AuditRequirement
    escalation_requirement: EscalationRequirement
    stop_conditions: tuple[str, ...]
    rationale: tuple[str, ...]


__all__ = [
    "LaneDecision",
    "LaneKind",
]
