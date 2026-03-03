from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Literal, Optional, Dict, Any


ActionKind = Literal[
    "comment_pr",
    "suggest_labels",
    "suggest_duplicates",
    "draft_release_notes",
    "summarize_ci_failure",
    "detect_pr_hygiene",
]

Confidence = Literal["HIGH", "MED", "LOW"]


@dataclass(frozen=True)
class EvidenceRef:
    kind: Literal["pr", "commit", "file", "ci_log", "issue", "link"]
    ref: str  # e.g. "PR#123", "abc1234", "services/x.py", "job:tests step:pytest", "ISSUE#77"
    excerpt: Optional[str] = None  # short snippet only


@dataclass(frozen=True)
class Suggestion:
    title: str
    detail: str
    confidence: Confidence
    evidence: List[EvidenceRef] = field(default_factory=list)


@dataclass(frozen=True)
class ProposedAction:
    kind: ActionKind
    title: str
    body_md: str
    suggestions: List[Suggestion] = field(default_factory=list)
    safe_to_execute: bool = False  # must be false unless deterministic rules mark safe
    evidence: List[EvidenceRef] = field(default_factory=list)


@dataclass(frozen=True)
class Report:
    run_id: str
    scope: Literal["pr", "issue", "repo", "ci"]
    target: str  # e.g. "PR#123", "ISSUE#7", "repo", "CI:run/abc"
    top_k: int = 3
    actions: List[ProposedAction] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    blocked: bool = False
    blocked_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        # deterministic conversion (stable keys)
        def ev(e: EvidenceRef) -> Dict[str, Any]:
            d = {"kind": e.kind, "ref": e.ref}
            if e.excerpt is not None:
                d["excerpt"] = e.excerpt
            return d

        def sug(s: Suggestion) -> Dict[str, Any]:
            return {
                "title": s.title,
                "detail": s.detail,
                "confidence": s.confidence,
                "evidence": [ev(x) for x in s.evidence],
            }

        def act(a: ProposedAction) -> Dict[str, Any]:
            return {
                "kind": a.kind,
                "title": a.title,
                "body_md": a.body_md,
                "suggestions": [sug(x) for x in a.suggestions],
                "safe_to_execute": a.safe_to_execute,
                "evidence": [ev(x) for x in a.evidence],
            }

        return {
            "run_id": self.run_id,
            "scope": self.scope,
            "target": self.target,
            "top_k": self.top_k,
            "actions": [act(x) for x in self.actions],
            "warnings": list(self.warnings),
            "blocked": self.blocked,
            "blocked_reason": self.blocked_reason,
        }
