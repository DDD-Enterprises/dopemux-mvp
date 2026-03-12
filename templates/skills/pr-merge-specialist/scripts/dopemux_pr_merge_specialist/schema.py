from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional


PRClass = Literal[
    "READY",
    "CI_ONLY",
    "CONFLICTS_ONLY",
    "COMMENTS_ONLY",
    "MIXED",
    "BLOCKED",
]

PRStatus = Literal["merged", "merge_ready", "blocked", "escalated", "skipped"]

ThreadDispositionType = Literal[
    "implement",
    "decline_with_rationale",
    "auto_resolve_outdated",
    "escalate",
]

MergeActionType = Literal["rebase_merge", "auto_merge_fallback", "blocked"]


@dataclass(frozen=True)
class ThreadComment:
    id: str
    author: str
    body: str
    created_at: str
    path: str = ""
    line: Optional[int] = None
    original_line: Optional[int] = None


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


@dataclass(frozen=True)
class CheckSummary:
    total: int
    success: int
    failure: int
    pending: int


@dataclass(frozen=True)
class PRState:
    pr_id: int
    title: str
    author: str
    state: str
    base_ref: str
    head_ref: str
    ci_status: Literal["SUCCESS", "FAILURE", "PENDING"]
    mergeable: str
    merge_state_status: str
    review_decision: str
    labels: List[str] = field(default_factory=list)
    updated_at: str = ""
    is_draft: bool = False
    additions: int = 0
    deletions: int = 0
    changed_files: int = 0
    unresolved_threads: int = 0
    active_unresolved_threads: int = 0
    outdated_unresolved_threads: int = 0
    pr_class: PRClass = "BLOCKED"
    risk_score: float = 0.0
    check_summary: Optional[CheckSummary] = None

    @property
    def diff_size(self) -> int:
        return self.additions + self.deletions


@dataclass(frozen=True)
class ThreadDisposition:
    thread_id: str
    disposition: ThreadDispositionType
    reason: str
    path: str = ""
    applied: bool = False
    escalation_needed: bool = False


@dataclass(frozen=True)
class MergeDecision:
    action: MergeActionType
    command: List[str]
    reason: str


@dataclass(frozen=True)
class ValidationStepResult:
    name: str
    command: str
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class ValidationReport:
    passed: bool
    steps: List[ValidationStepResult] = field(default_factory=list)
    attempts: int = 1
    remediation_applied: bool = False


@dataclass(frozen=True)
class QueueOrderingLayer:
    layer: int
    pr_ids: List[int]


@dataclass(frozen=True)
class PRMergeReport:
    run_id: str
    pr_id: int
    status: PRStatus
    status_reason: str
    pr_state: PRState
    merge_decision: Optional[MergeDecision] = None
    thread_dispositions: List[ThreadDisposition] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)
    artifacts: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "pr_id": self.pr_id,
            "status": self.status,
            "status_reason": self.status_reason,
            "pr_state": {
                "title": self.pr_state.title,
                "author": self.pr_state.author,
                "base_ref": self.pr_state.base_ref,
                "head_ref": self.pr_state.head_ref,
                "ci_status": self.pr_state.ci_status,
                "mergeable": self.pr_state.mergeable,
                "merge_state_status": self.pr_state.merge_state_status,
                "review_decision": self.pr_state.review_decision,
                "pr_class": self.pr_state.pr_class,
                "risk_score": self.pr_state.risk_score,
                "unresolved_threads": self.pr_state.unresolved_threads,
                "active_unresolved_threads": self.pr_state.active_unresolved_threads,
                "outdated_unresolved_threads": self.pr_state.outdated_unresolved_threads,
                "additions": self.pr_state.additions,
                "deletions": self.pr_state.deletions,
                "changed_files": self.pr_state.changed_files,
                "updated_at": self.pr_state.updated_at,
                "is_draft": self.pr_state.is_draft,
            },
            "merge_decision": (
                None
                if self.merge_decision is None
                else {
                    "action": self.merge_decision.action,
                    "command": self.merge_decision.command,
                    "reason": self.merge_decision.reason,
                }
            ),
            "thread_dispositions": [
                {
                    "thread_id": d.thread_id,
                    "disposition": d.disposition,
                    "reason": d.reason,
                    "path": d.path,
                    "applied": d.applied,
                    "escalation_needed": d.escalation_needed,
                }
                for d in self.thread_dispositions
            ],
            "blockers": self.blockers,
            "artifacts": self.artifacts,
        }

