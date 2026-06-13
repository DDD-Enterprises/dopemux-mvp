"""DCP Routing Domain Model — DMX-DCP-MODEL-ROUTING-MVP-0001R.

Pure data types for the DCP Routing & Execution Plane.

Invariants enforced by design:
- No I/O.
- No network.
- No external process execution.
- No runner, connector, MCP, GitHub, Dopetask, OpenCode,
  Grok, Claude, Gemini, AGY, ConPort, dope-memory, dope-context,
  or Task Orchestrator imports.
- UNKNOWN and BLOCKED are first-class values.
- RED_LANE state overrides route preference (enforced by caller gates;
  representable here as first-class field).
- ProofRequirement and AuditRequirement are first-class fields.
- Runner/backend/connector choice is data, not executable behavior.
- No live-write state is enabled.
- No merge-readiness is claimed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ─────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────


class TaskSource(str, Enum):
    """Where a task request originates."""

    OPERATOR = "OPERATOR"
    SUPERVISOR = "SUPERVISOR"
    AUTOMATED = "AUTOMATED"
    CODEX = "CODEX"
    CLAUDE = "CLAUDE"
    OPENCODE = "OPENCODE"
    GROK = "GROK"
    GEMINI = "GEMINI"
    AGY = "AGY"
    UNKNOWN = "UNKNOWN"


class TaskType(str, Enum):
    """Coarse classification of what a task does."""

    READ_ONLY = "READ_ONLY"
    DESIGN_ONLY = "DESIGN_ONLY"
    SCHEMA_ONLY = "SCHEMA_ONLY"
    CODE_CHANGE = "CODE_CHANGE"
    PROOF_BUNDLE = "PROOF_BUNDLE"
    AUDIT = "AUDIT"
    MERGE = "MERGE"
    LIVE_WRITE = "LIVE_WRITE"
    UNKNOWN = "UNKNOWN"


class RiskClass(str, Enum):
    """Risk level that gates routing and proof requirements."""

    R0_READ = "R0_READ"
    R1_LOW = "R1_LOW"
    R2_MEDIUM = "R2_MEDIUM"
    R3_HIGH = "R3_HIGH"
    RED_LANE = "RED_LANE"
    UNKNOWN = "UNKNOWN"


class ComplexityClass(str, Enum):
    """Estimated implementation complexity."""

    TRIVIAL = "TRIVIAL"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    ARCHITECTURAL = "ARCHITECTURAL"
    UNKNOWN = "UNKNOWN"


class AuthorityClass(str, Enum):
    """Who holds authority to approve or execute this task."""

    OPERATOR = "OPERATOR"
    SUPERVISOR = "SUPERVISOR"
    DUAL = "DUAL"
    AUTOMATED_SAFE = "AUTOMATED_SAFE"
    BLOCKED = "BLOCKED"
    UNKNOWN = "UNKNOWN"


class RuntimeImpact(str, Enum):
    """Whether executing this task touches live runtime state."""

    NONE = "NONE"
    READ_ONLY = "READ_ONLY"
    LOCAL_ONLY = "LOCAL_ONLY"
    SERVICE_MUTATION = "SERVICE_MUTATION"
    LIVE_WRITE = "LIVE_WRITE"
    UNKNOWN = "UNKNOWN"


class BackendKind(str, Enum):
    """Which backend runner would execute this task."""

    CODEX = "CODEX"
    CLAUDE_CODE = "CLAUDE_CODE"
    OPENCODE = "OPENCODE"
    GROK = "GROK"
    GEMINI_CLI = "GEMINI_CLI"
    AGY = "AGY"
    LOCAL_SCRIPT = "LOCAL_SCRIPT"
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"


class ConnectorKind(str, Enum):
    """Which connector (transport/protocol) would be used."""

    DIRECT = "DIRECT"
    MCP = "MCP"
    HTTP = "HTTP"
    STDIO = "STDIO"
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"


class ProofRequirement(str, Enum):
    """Proof obligations for this route."""

    NONE = "NONE"
    COMMAND_LOG = "COMMAND_LOG"
    DIFF_STAT = "DIFF_STAT"
    FULL_PROOF_BUNDLE = "FULL_PROOF_BUNDLE"
    AUDIT_REPORT = "AUDIT_REPORT"
    SUPERVISOR_REVIEW = "SUPERVISOR_REVIEW"
    UNKNOWN = "UNKNOWN"


class AuditRequirement(str, Enum):
    """Audit obligations for this route."""

    NONE = "NONE"
    SELF_CHECK = "SELF_CHECK"
    EMBEDDED_AUDITOR = "EMBEDDED_AUDITOR"
    DISTINCT_AUDITOR = "DISTINCT_AUDITOR"
    SUPERVISOR_AUDIT = "SUPERVISOR_AUDIT"
    UNKNOWN = "UNKNOWN"


class EscalationRequirement(str, Enum):
    """When and how to escalate this route."""

    NONE = "NONE"
    ON_RISK = "ON_RISK"
    ON_UNKNOWN = "ON_UNKNOWN"
    ALWAYS = "ALWAYS"
    UNKNOWN = "UNKNOWN"


class RedLaneState(str, Enum):
    """Red-lane gate state.

    RED_LANE overrides any ALLOW routing preference.
    A route gate MUST check this field before permitting execution.
    """

    CLEAR = "CLEAR"
    RED_LANE = "RED_LANE"
    UNKNOWN = "UNKNOWN"


class RouteStatus(str, Enum):
    """Overall disposition of the route decision."""

    PENDING = "PENDING"
    ALLOWED = "ALLOWED"
    BLOCKED = "BLOCKED"
    NEEDS_SUPERVISOR = "NEEDS_SUPERVISOR"
    UNKNOWN = "UNKNOWN"


# ─────────────────────────────────────────────
# Route Decision dataclass
# ─────────────────────────────────────────────


@dataclass
class RouteDecision:
    """Minimal DCP routing domain model record.

    This is pure data. No methods trigger I/O, network, external process run,
    runner invocation, or external service access.

    Default values are intentionally conservative:
    - ``confidence`` defaults to ``"LOW"`` (not VERIFIED).
    - ``status`` defaults to ``RouteStatus.PENDING`` (not runnable).
    - ``red_lane_state`` defaults to ``RedLaneState.UNKNOWN`` (fail-closed).
    - ``authority_class`` defaults to ``AuthorityClass.UNKNOWN``.
    - UNKNOWN authority MUST NOT be coerced into allowed mutation.
    """

    # Identity
    route_id: str = "UNKNOWN"

    # Classification inputs
    task_source: TaskSource = TaskSource.UNKNOWN
    task_type: TaskType = TaskType.UNKNOWN
    risk_class: RiskClass = RiskClass.UNKNOWN
    complexity_class: ComplexityClass = ComplexityClass.UNKNOWN
    authority_class: AuthorityClass = AuthorityClass.UNKNOWN
    runtime_impact: RuntimeImpact = RuntimeImpact.UNKNOWN

    # Backend / connector (data only, not executable)
    backend_kind: BackendKind = BackendKind.UNKNOWN
    connector_kind: ConnectorKind = ConnectorKind.UNKNOWN

    # Proof / audit obligations (first-class fields)
    proof_requirements: list[ProofRequirement] = field(default_factory=list)
    audit_requirement: AuditRequirement = AuditRequirement.UNKNOWN
    escalation_requirement: EscalationRequirement = EscalationRequirement.UNKNOWN

    # Red-lane gate (MUST be checked before allowing execution)
    red_lane_state: RedLaneState = RedLaneState.UNKNOWN

    # Decision metadata
    allowed_actions: list[str] = field(default_factory=list)
    forbidden_actions: list[str] = field(default_factory=list)
    stop_conditions: list[str] = field(default_factory=list)
    evidence_refs: list[str] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)

    # Confidence and status
    # Default "LOW" — implementer must raise confidence through evidence gates.
    confidence: str = "LOW"
    # Default PENDING — not runnable until authority gates pass.
    status: RouteStatus = RouteStatus.PENDING

    # ── Serialization helpers ──────────────────────────────────────

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dictionary.

        No external services are accessed. All enum values are
        rendered as their string values for portability.
        """
        return {
            "route_id": self.route_id,
            "task_source": self.task_source.value,
            "task_type": self.task_type.value,
            "risk_class": self.risk_class.value,
            "complexity_class": self.complexity_class.value,
            "authority_class": self.authority_class.value,
            "runtime_impact": self.runtime_impact.value,
            "backend_kind": self.backend_kind.value,
            "connector_kind": self.connector_kind.value,
            "proof_requirements": [p.value for p in self.proof_requirements],
            "audit_requirement": self.audit_requirement.value,
            "escalation_requirement": self.escalation_requirement.value,
            "red_lane_state": self.red_lane_state.value,
            "allowed_actions": list(self.allowed_actions),
            "forbidden_actions": list(self.forbidden_actions),
            "stop_conditions": list(self.stop_conditions),
            "evidence_refs": list(self.evidence_refs),
            "unknowns": list(self.unknowns),
            "confidence": self.confidence,
            "status": self.status.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RouteDecision":
        """Construct from a plain dictionary.

        Missing keys fall back to conservative defaults.
        Unrecognised enum values fall back to UNKNOWN.
        No external services are accessed.
        """

        def _ts(val: str) -> TaskSource:
            try:
                return TaskSource(val)
            except ValueError:
                return TaskSource.UNKNOWN

        def _tt(val: str) -> TaskType:
            try:
                return TaskType(val)
            except ValueError:
                return TaskType.UNKNOWN

        def _rc(val: str) -> RiskClass:
            try:
                return RiskClass(val)
            except ValueError:
                return RiskClass.UNKNOWN

        def _cc(val: str) -> ComplexityClass:
            try:
                return ComplexityClass(val)
            except ValueError:
                return ComplexityClass.UNKNOWN

        def _ac(val: str) -> AuthorityClass:
            try:
                return AuthorityClass(val)
            except ValueError:
                return AuthorityClass.UNKNOWN

        def _ri(val: str) -> RuntimeImpact:
            try:
                return RuntimeImpact(val)
            except ValueError:
                return RuntimeImpact.UNKNOWN

        def _bk(val: str) -> BackendKind:
            try:
                return BackendKind(val)
            except ValueError:
                return BackendKind.UNKNOWN

        def _ck(val: str) -> ConnectorKind:
            try:
                return ConnectorKind(val)
            except ValueError:
                return ConnectorKind.UNKNOWN

        def _pr(val: str) -> ProofRequirement:
            try:
                return ProofRequirement(val)
            except ValueError:
                return ProofRequirement.UNKNOWN

        def _ar(val: str) -> AuditRequirement:
            try:
                return AuditRequirement(val)
            except ValueError:
                return AuditRequirement.UNKNOWN

        def _er(val: str) -> EscalationRequirement:
            try:
                return EscalationRequirement(val)
            except ValueError:
                return EscalationRequirement.UNKNOWN

        def _rls(val: str) -> RedLaneState:
            try:
                return RedLaneState(val)
            except ValueError:
                return RedLaneState.UNKNOWN

        def _rs(val: str) -> RouteStatus:
            try:
                return RouteStatus(val)
            except ValueError:
                return RouteStatus.UNKNOWN

        proof_list = [
            _pr(p) for p in data.get("proof_requirements", [])
        ]

        return cls(
            route_id=str(data.get("route_id", "UNKNOWN")),
            task_source=_ts(data.get("task_source", "UNKNOWN")),
            task_type=_tt(data.get("task_type", "UNKNOWN")),
            risk_class=_rc(data.get("risk_class", "UNKNOWN")),
            complexity_class=_cc(data.get("complexity_class", "UNKNOWN")),
            authority_class=_ac(data.get("authority_class", "UNKNOWN")),
            runtime_impact=_ri(data.get("runtime_impact", "UNKNOWN")),
            backend_kind=_bk(data.get("backend_kind", "UNKNOWN")),
            connector_kind=_ck(data.get("connector_kind", "UNKNOWN")),
            proof_requirements=proof_list,
            audit_requirement=_ar(data.get("audit_requirement", "UNKNOWN")),
            escalation_requirement=_er(
                data.get("escalation_requirement", "UNKNOWN")
            ),
            red_lane_state=_rls(data.get("red_lane_state", "UNKNOWN")),
            allowed_actions=list(data.get("allowed_actions", [])),
            forbidden_actions=list(data.get("forbidden_actions", [])),
            stop_conditions=list(data.get("stop_conditions", [])),
            evidence_refs=list(data.get("evidence_refs", [])),
            unknowns=list(data.get("unknowns", [])),
            confidence=str(data.get("confidence", "LOW")),
            status=_rs(data.get("status", "PENDING")),
        )

    def is_red_lane(self) -> bool:
        """Return True if this decision is in RED_LANE state.

        Callers MUST check this before permitting any execution.
        RED_LANE overrides any ALLOW routing preference.
        """
        return self.red_lane_state is RedLaneState.RED_LANE

    def is_blocked(self) -> bool:
        """Return True if this decision has BLOCKED status."""
        return self.status is RouteStatus.BLOCKED

    def is_runnable(self) -> bool:
        """Return True only if status is ALLOWED, red-lane is CLEAR, and
        authority is not UNKNOWN or BLOCKED.

        Fail-closed rules:
        - UNKNOWN red-lane → not runnable (fail-closed gate).
        - RED_LANE red-lane → not runnable (explicit block).
        - UNKNOWN authority → not runnable (must not be coerced into mutation).
        - BLOCKED authority → not runnable.
        - Status must be ALLOWED.
        """
        if self.red_lane_state is not RedLaneState.CLEAR:
            # Covers both RED_LANE and UNKNOWN (fail-closed)
            return False
        if self.authority_class is AuthorityClass.UNKNOWN:
            return False
        if self.authority_class is AuthorityClass.BLOCKED:
            return False
        return self.status is RouteStatus.ALLOWED
