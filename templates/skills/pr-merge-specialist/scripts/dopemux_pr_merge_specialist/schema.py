from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

ARTIFACT_VERSION = "3.1"
POLICY_SCHEMA_VERSION = 1
TOOL_VERSION = "3.1.0"


class ValidationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    NOT_EXECUTED = "not_executed"


class PRState(str, Enum):
    DISCOVERED = "discovered"
    SCANNED = "scanned"
    PLANNED = "planned"
    APPLY_READY = "apply_ready"
    APPLY_BLOCKED = "apply_blocked"
    APPLIED = "applied"
    MERGE_READY = "merge_ready"
    MERGE_BLOCKED = "merge_blocked"
    QUEUED_FOR_MERGE = "queued_for_merge"
    MERGED = "merged"
    ESCALATED = "escalated"
    ABORTED = "aborted"


class BlockerType(str, Enum):
    REQUIRED_CHECK_PENDING = "required_check_pending"
    REQUIRED_CHECK_FAILED = "required_check_failed"
    OPTIONAL_CHECK_PENDING = "optional_check_pending"
    APPROVAL_MISSING = "approval_missing"
    CHANGES_REQUESTED = "changes_requested"
    ACTIVE_THREAD = "active_thread"
    MERGE_QUEUE_REQUIRED = "merge_queue_required"
    BRANCH_PROTECTION_BLOCK = "branch_protection_block"
    VALIDATION_FAILED = "validation_failed"
    CONFLICT_DETECTED = "conflict_detected"


class FallbackReason(str, Enum):
    MERGE_QUEUE_REQUIRED = "merge_queue_required"
    DIRECT_MERGE_DISALLOWED_BY_POLICY = "direct_merge_disallowed_by_policy"
    AUTO_MERGE_REQUIRED_BY_PROTECTION = "auto_merge_required_by_protection"


class FindingSeverity(str, Enum):
    BLOCKER = "blocker"
    WARNING = "warning"
    OBSERVATION = "observation"


class ThreadDispositionType(str, Enum):
    IMPLEMENT = "implement"
    DECLINE_WITH_RATIONALE = "decline_with_rationale"
    AUTO_RESOLVE_OUTDATED = "auto_resolve_outdated"
    ESCALATE = "escalate"


class MergeActionType(str, Enum):
    REBASE_MERGE = "rebase_merge"
    AUTO_MERGE_ENABLE = "auto_merge_enable"
    AUTO_MERGE_FALLBACK = "auto_merge_fallback"
    ADMIN_BYPASS_SQUASH = "admin_bypass_squash"
    BLOCKED = "blocked"
    PLANNED = "planned"


class PRClass(str, Enum):
    READY = "READY"
    CI_ONLY = "CI_ONLY"
    CONFLICTS_ONLY = "CONFLICTS_ONLY"
    COMMENTS_ONLY = "COMMENTS_ONLY"
    MIXED = "MIXED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class ArtifactMeta:
    artifact_version: str = ARTIFACT_VERSION
    tool_version: str = TOOL_VERSION
    policy_schema_version: int = POLICY_SCHEMA_VERSION
    generated_at: str = ""
    run_id: str = ""
    repo_root: str = ""
    git_remote_origin_url: str = ""
    git_repo_name: str = ""
    current_branch: str = ""
    default_branch: str = ""
    pr_head_sha: str = ""
    base_sha: str = ""
    applied_tree_sha: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OverrideRecord:
    override_type: str
    actor: str
    reason: str
    scope: str
    source: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Blocker:
    type: str
    source: str
    name: Optional[str] = None
    details: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Finding:
    kind: FindingSeverity
    finding_type: str
    message: str
    id: str = ""
    severity: Optional[FindingSeverity] = None
    category: str = ""
    suggestion: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    override: Optional[OverrideRecord] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["kind"] = (
            self.kind.value
            if isinstance(self.kind, FindingSeverity)
            else str(self.kind)
        )
        payload["override"] = None if self.override is None else self.override.to_dict()
        return payload

    def as_blocker(self) -> Blocker:
        return Blocker(
            type=self.finding_type,
            source=self.source,
            name=self.message,
            details=self.details.get("detail") if self.details else None,
            metadata={
                **self.details,
                **(
                    {"override": self.override.to_dict()}
                    if self.override is not None
                    else {}
                ),
            },
        )


@dataclass(frozen=True)
class TruthSource:
    name: str
    status: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Fingerprint:
    input_fingerprint: str
    valid_for_sha: str
    stale_if: List[str] = field(default_factory=list)
    created_from_state: str = ""
    review_state_hash: str = ""
    check_state_hash: str = ""
    validation_command_hash: str = ""
    apply_tree_sha: str = ""
    dirty_state: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ThreadComment:
    id: str
    author: str
    body: str
    created_at: str
    path: str = ""
    line: Optional[int] = None
    original_line: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewThread:
    id: str
    is_resolved: bool
    is_outdated: bool
    viewer_can_resolve: bool
    path: str = ""
    line: Optional[int] = None
    original_line: Optional[int] = None
    original_start_line: Optional[int] = None
    comments: List[ThreadComment] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["comments"] = [item.to_dict() for item in self.comments]
        return payload


@dataclass(frozen=True)
class CheckSummary:
    total: int = 0
    success: int = 0
    failure: int = 0
    pending: int = 0
    required_pending: int = 0
    required_failure: int = 0
    optional_pending: int = 0
    optional_failure: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationStepResult:
    name: str
    command: str
    status: str
    returncode: Optional[int] = None
    stdout: str = ""
    stderr: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationResult:
    status: ValidationStatus
    required_for_merge_ready: bool = True
    steps: List[ValidationStepResult] = field(default_factory=list)
    attempts: int = 1
    remediation_applied: bool = False
    fingerprint: Optional[Fingerprint] = None

    @property
    def passed(self) -> bool:
        return (
            self.status.value
            if isinstance(self.status, ValidationStatus)
            else str(self.status)
        ) == ValidationStatus.PASSED.value

    @property
    def failing_step(self) -> Optional[ValidationStepResult]:
        if self.passed or not self.steps:
            return None
        # Return the last step, since validation loop breaks on the first failure
        return self.steps[-1]

    @property
    def failure_fingerprint(self) -> Optional[str]:
        step = self.failing_step
        if not step:
            return None
        error_output = (step.stderr or "").strip() or (step.stdout or "").strip()
        significant_error_part = error_output.encode("utf-8")[-512:]
        fingerprint_source = f"{step.name}:{significant_error_part.decode('utf-8', errors='ignore')}".encode("utf-8")
        import hashlib
        return hashlib.sha256(fingerprint_source).hexdigest()

    @property
    def input_fingerprint(self) -> Optional[Fingerprint]:
        return self.fingerprint

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": (
                self.status.value
                if isinstance(self.status, ValidationStatus)
                else str(self.status)
            ),
            "required_for_merge_ready": self.required_for_merge_ready,
            "passed": self.passed,
            "attempts": self.attempts,
            "remediation_applied": self.remediation_applied,
            "steps": [step.to_dict() for step in self.steps],
            "input_fingerprint": (
                None if self.fingerprint is None else self.fingerprint.to_dict()
            ),
            "failure_fingerprint": self.failure_fingerprint,
        }


ValidationReport = ValidationResult


@dataclass(frozen=True)
class QueueOrderingLayer:
    layer: int
    pr_ids: List[int]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PullRequestState:
    pr_id: int
    title: str
    author: str
    state: str
    base_ref: str
    head_ref: str
    ci_status: str
    mergeable: str
    merge_state_status: str
    review_decision: str
    labels: List[str] = field(default_factory=list)
    updated_at: str = ""
    is_draft: bool = False
    auto_merge_enabled: bool = False
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    unresolved_threads: int = 0
    active_unresolved_threads: int = 0
    outdated_unresolved_threads: int = 0
    pr_class: str = PRClass.BLOCKED.value
    risk_score: float = 0.0
    check_summary: Optional[CheckSummary] = None
    lifecycle_state: PRState = PRState.DISCOVERED
    head_sha: str = ""
    base_sha: str = ""

    @property
    def diff_size(self) -> int:
        return self.additions + self.deletions

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["lifecycle_state"] = (
            self.lifecycle_state.value
            if isinstance(self.lifecycle_state, PRState)
            else str(self.lifecycle_state)
        )
        payload["check_summary"] = (
            None if self.check_summary is None else self.check_summary.to_dict()
        )
        return payload


PRStateSnapshot = PullRequestState
PRStateRecord = PullRequestState
PRStateData = PullRequestState


@dataclass(frozen=True)
class ThreadDisposition:
    thread_id: str
    disposition: ThreadDispositionType
    reason: str
    path: str = ""
    applied: bool = False
    escalation_needed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["disposition"] = (
            self.disposition.value
            if isinstance(self.disposition, ThreadDispositionType)
            else str(self.disposition)
        )
        return payload


@dataclass(frozen=True)
class MergeDecision:
    action: MergeActionType
    command: List[str]
    reason: str
    reason_code: str = ""

    def to_dict(self) -> Dict[str, Any]:
        payload = asdict(self)
        payload["action"] = (
            self.action.value
            if isinstance(self.action, MergeActionType)
            else str(self.action)
        )
        return payload


@dataclass(frozen=True)
class PlanDecision:
    pr_number: int
    state: str
    blockers: List[Blocker] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    observations: List[Dict[str, Any]] = field(default_factory=list)
    validation: Optional[ValidationResult] = None
    decision_basis: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pr_number": self.pr_number,
            "state": self.state,
            "blockers": [item.to_dict() for item in self.blockers],
            "warnings": self.warnings,
            "observations": self.observations,
            "validation": (
                None if self.validation is None else self.validation.to_dict()
            ),
            "decision_basis": self.decision_basis,
        }


@dataclass(frozen=True)
class PhaseRecord:
    phase: str
    lifecycle_state: str
    findings: List[Finding] = field(default_factory=list)
    truth_sources: List[TruthSource] = field(default_factory=list)
    precedence_order: List[str] = field(default_factory=list)
    decision_basis: Dict[str, Any] = field(default_factory=dict)
    fingerprint: Optional[Fingerprint] = None
    artifacts: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase,
            "lifecycle_state": self.lifecycle_state,
            "findings": [item.to_dict() for item in self.findings],
            "truth_sources": [item.to_dict() for item in self.truth_sources],
            "precedence_order": self.precedence_order,
            "decision_basis": self.decision_basis,
            "fingerprint": (
                None if self.fingerprint is None else self.fingerprint.to_dict()
            ),
            "artifacts": self.artifacts,
        }


@dataclass(frozen=True)
class PolicyResolution:
    source: str
    path: str
    fingerprint: str
    policy_schema_version: int = POLICY_SCHEMA_VERSION
    overrides: List[OverrideRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "path": self.path,
            "fingerprint": self.fingerprint,
            "policy_schema_version": self.policy_schema_version,
            "overrides": [item.to_dict() for item in self.overrides],
        }


@dataclass(frozen=True)
class PreflightCheck:
    name: str
    status: str
    required: bool
    details: str = ""
    remediation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PreflightResult:
    ok: bool
    checks: List[PreflightCheck] = field(default_factory=list)
    policy_resolution: Optional[PolicyResolution] = None
    override_records: List[OverrideRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ok": self.ok,
            "checks": [item.to_dict() for item in self.checks],
            "policy_resolution": (
                None
                if self.policy_resolution is None
                else self.policy_resolution.to_dict()
            ),
            "override_records": [item.to_dict() for item in self.override_records],
        }


@dataclass(frozen=True)
class PRResult:
    run_id: str
    pr_state: PullRequestState
    lifecycle_state: str
    apply_actions: List[str] = field(default_factory=list)
    merge_decision: Optional[MergeDecision] = None
    findings: List[Finding] = field(default_factory=list)
    truth_sources: List[TruthSource] = field(default_factory=list)
    precedence_order: List[str] = field(default_factory=list)
    decision_basis: Dict[str, Any] = field(default_factory=dict)
    validation_report: Optional[ValidationResult] = None
    thread_dispositions: List[ThreadDisposition] = field(default_factory=list)
    fingerprint: Optional[Fingerprint] = None
    artifacts: Dict[str, str] = field(default_factory=dict)
    blocked_by_global_fix_pr: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        blockers = [
            item.as_blocker().to_dict()
            for item in self.findings
            if (
                item.kind.value
                if isinstance(item.kind, FindingSeverity)
                else str(item.kind)
            )
            == FindingSeverity.BLOCKER.value
        ]
        warnings = [
            item.to_dict()
            for item in self.findings
            if (
                item.kind.value
                if isinstance(item.kind, FindingSeverity)
                else str(item.kind)
            )
            == FindingSeverity.WARNING.value
        ]
        observations = [
            item.to_dict()
            for item in self.findings
            if (
                item.kind.value
                if isinstance(item.kind, FindingSeverity)
                else str(item.kind)
            )
            == FindingSeverity.OBSERVATION.value
        ]
        return {
            "run_id": self.run_id,
            "pr_state": self.pr_state.to_dict(),
            "lifecycle_state": (
                self.lifecycle_state.value
                if isinstance(self.lifecycle_state, PRState)
                else str(self.lifecycle_state)
            ),
            "apply_actions": self.apply_actions,
            "merge_decision": (
                None if self.merge_decision is None else self.merge_decision.to_dict()
            ),
            "blockers": blockers,
            "warnings": warnings,
            "observations": observations,
            "truth_sources": [item.to_dict() for item in self.truth_sources],
            "precedence_order": self.precedence_order,
            "decision_basis": self.decision_basis,
            "validation_report": (
                None
                if self.validation_report is None
                else self.validation_report.to_dict()
            ),
            "thread_dispositions": [
                item.to_dict() for item in self.thread_dispositions
            ],
            "fingerprint": (
                None if self.fingerprint is None else self.fingerprint.to_dict()
            ),
            "artifacts": self.artifacts,
            "blocked_by_global_fix_pr": self.blocked_by_global_fix_pr,
        }


@dataclass(frozen=True)
class ArbitrationRoleTrace:
    run_id: str
    analyzer: Optional[Any] = None
    challenger: Optional[Any] = None
    arbiter: Optional[Any] = None


@dataclass(frozen=True)
class ConsensusDecision:
    case_id: str
    preferred_candidate: str
    merge_strategy: str
    rationale: str
    confidence: str
    defer_to_human: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MergeExecutionPlan:
    strategy: str
    autonomy_level: str
    ordered_steps: List[str]
    human_review_required: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RequiredVerificationPlan:
    required_checks: List[str]
    targeted_tests: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AutonomyGateReport:
    decision: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewReplyAction:
    id: str
    thread_id: str
    reply_body: str
    should_resolve: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReviewReplyPlan:
    actions: List[ReviewReplyAction] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"actions": [a.to_dict() for a in self.actions]}


@dataclass(frozen=True)
class PRMergeReport:
    pr_id: str
    status: str
    blockers: List[Blocker] = field(default_factory=list)
    initial_state: Optional[PullRequestState] = None
    telemetry: Dict[str, Any] = field(default_factory=dict)
    remediation_plan: Optional[Any] = None
    review_reply_plan: Optional[ReviewReplyPlan] = None
    consensus_decision: Optional[ConsensusDecision] = None
    autonomy_report: Optional[AutonomyGateReport] = None
    verification_plan: Optional[Any] = None
    metadata_update: Optional[Any] = None
    remediation_flow_trace: Optional[RemediationFlowTrace] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pr_id": self.pr_id,
            "status": self.status,
            "blockers": [b.to_dict() for b in self.blockers],
            "telemetry": self.telemetry,
            "review_reply_plan": (
                self.review_reply_plan.to_dict() if self.review_reply_plan else None
            ),
            "consensus_decision": (
                self.consensus_decision.to_dict() if self.consensus_decision else None
            ),
            "autonomy_report": (
                self.autonomy_report.to_dict() if self.autonomy_report else None
            ),
            "remediation_flow_trace": (
                self.remediation_flow_trace.to_dict() if self.remediation_flow_trace else None
            ),
        }


@dataclass(frozen=True)
class RemediationStageResult:
    name: str
    status: str
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RemediationFlowTrace:
    run_id: str
    stages: List[RemediationStageResult] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "stages": [s.to_dict() for s in self.stages],
        }


@dataclass(frozen=True)
class RunManifest:
    run_id: str
    mode: str
    repo_root: str
    repo_slug: str
    policy_fingerprint: str
    artifact_schema_versions: Dict[str, str] = field(default_factory=dict)
    completed_phases: List[str] = field(default_factory=list)
    resumable_phases: List[str] = field(default_factory=list)
    invalidation_conditions: List[str] = field(default_factory=list)
    pr_states: Dict[str, str] = field(default_factory=dict)
    artifact_pointers: Dict[str, str] = field(default_factory=dict)
    optional_artifacts: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
