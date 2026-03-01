from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional, Dict, Any


BlockerType = Literal[
    "COMMENTS",
    "CI_FAIL",
    "CONFLICTS",
    "MISSING_APPROVALS",
    "POLICY_BLOCK",
    "UNKNOWN",
]


@dataclass(frozen=True)
class PRState:
    pr_id: str
    title: str
    author: str
    state: str
    ci_status: str
    mergeable: bool
    labels: List[str] = field(default_factory=list)
    approvals_count: int = 0
    updated_at: str = ""
    diffstat: str = ""


@dataclass(frozen=True)
class BlockerEvidence:
    type: BlockerType
    description: str
    logs: Optional[str] = None
    files: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class MergeAction:
    action_type: str
    target: str
    command: str
    reasoning: str


@dataclass(frozen=True)
class PRMergeReport:
    run_id: str
    pr_id: str
    initial_state: PRState
    blockers: List[BlockerEvidence] = field(default_factory=list)
    planned_actions: List[MergeAction] = field(default_factory=list)
    status: Literal["merged", "merge_ready", "needs_review", "blocked", "escalated"] = "blocked"
    status_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "pr_id": self.pr_id,
            "status": self.status,
            "status_reason": self.status_reason,
            "initial_state": {
                "title": self.initial_state.title,
                "author": self.initial_state.author,
                "ci_status": self.initial_state.ci_status,
                "mergeable": self.initial_state.mergeable,
                "diffstat": self.initial_state.diffstat
            },
            "blockers": [{"type": b.type, "desc": b.description} for b in self.blockers],
            "planned_actions": [{"type": a.action_type, "target": a.target} for a in self.planned_actions]
        }
