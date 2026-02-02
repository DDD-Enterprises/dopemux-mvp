"""
Promotion Engine - Deterministic event promotion for Dope-Memory.

Converts raw events into curated work log entries based on
the Phase 1 promotion rules defined in spec 05_promotion_redaction.md.
"""

from dataclasses import dataclass
from typing import Any, Optional

from .redactor import Redactor

# Phase 1 promotable event types (canonical dotted form)
PROMOTABLE_EVENT_TYPES = frozenset(
    [
        "decision.logged",
        "task.completed",
        "task.failed",
        "task.blocked",
        "error.encountered",
        "workflow.phase_changed",
        "manual.memory_store",
    ]
)

# Deterministic importance scores (no LLM in Phase 1)
IMPORTANCE_SCORES = {
    "decision.logged": 7,
    "task.failed": 7,
    "task.blocked": 7,
    "error.encountered": 6,
    "task.completed": 5,
    "workflow.phase_changed": 5,
    "manual.memory_store": 6,  # default, can be overridden by payload
}


def normalize_event_type(event_type: str) -> str:
    """Normalize event type to canonical dotted form.

    Handles:
    - Underscore to dot conversion (decision_logged -> decision.logged)
    - Whitespace trimming
    - Lowercase normalization
    """
    if not event_type:
        return "unknown"
    t = event_type.strip().lower()
    if not t:  # Empty after stripping whitespace
        return "unknown"
    # If already dotted, return as-is
    if "." in t:
        return t
    # Convert underscores to dots
    return t.replace("_", ".")


@dataclass
class PromotedEntry:
    """A promoted work log entry ready for storage."""

    category: str
    entry_type: str
    summary: str
    outcome: str
    importance_score: int
    workflow_phase: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    reasoning: Optional[str] = None
    tags: Optional[list[str]] = None
    linked_decisions: Optional[list[str]] = None
    linked_files: Optional[list[dict[str, str]]] = None
    linked_commits: Optional[list[str]] = None
    linked_chat_range: Optional[dict[str, Any]] = None
    duration_sec: Optional[int] = None


class PromotionEngine:
    """Promotes high-signal events to curated work log entries.

    Phase 1 rules are deterministic - no LLM involvement.
    """

    def __init__(self) -> None:
        self.redactor = Redactor()

    def is_promotable(self, event_type: str) -> bool:
        """Check if an event type is eligible for promotion.

        Normalizes event type before checking (handles underscore/dot variants).
        """
        normalized = normalize_event_type(event_type)
        return normalized in PROMOTABLE_EVENT_TYPES

    def promote(
        self, event_type: str, data: dict[str, Any]
    ) -> Optional[PromotedEntry]:
        """Promote an event to a work log entry.

        Args:
            event_type: The event type (e.g., "decision.logged" or "decision_logged")
            data: The event data payload (already redacted at ingest)

        Returns:
            PromotedEntry if promotable, None otherwise
        """
        normalized = normalize_event_type(event_type)
        if normalized not in PROMOTABLE_EVENT_TYPES:
            return None

        # Dispatch to specific handler (use normalized dotted form)
        handler = getattr(self, f"_promote_{normalized.replace('.', '_')}", None)
        if handler:
            return handler(data)

        return None


    def _extract_tags(self, data: dict[str, Any]) -> list[str]:
        """Extract and normalize tags from event data.

        Order: explicit tags first (preserved order), then inferred (sorted).
        Cap at 12.
        """
        explicit_tags = data.get("tags", [])
        if isinstance(explicit_tags, str):
            explicit_tags = [explicit_tags]

        # ASCII normalize
        explicit_tags = [t.strip().lower() for t in explicit_tags if t]

        # Infer tags from known fields
        inferred = set()
        if data.get("service"):
            inferred.add(f"service:{data['service']}")
        if data.get("phase"):
            inferred.add(f"phase:{data['phase']}")
        if data.get("ci_job"):
            inferred.add("ci")

        # Combine: explicit first, then inferred sorted
        all_tags = list(explicit_tags)
        for tag in sorted(inferred):
            if tag not in all_tags:
                all_tags.append(tag)

        return all_tags[:12]

    def _redact_files(
        self, files: Optional[list[dict[str, str]]]
    ) -> Optional[list[dict[str, str]]]:
        """Redact linked files through the redactor."""
        if not files:
            return None
        return self.redactor.redact_linked_files(files)

    # ─────────────────────────────────────────────────────────────────
    # Promotion Handlers
    # ─────────────────────────────────────────────────────────────────

    def _promote_decision_logged(self, data: dict[str, Any]) -> Optional[PromotedEntry]:
        """Promote decision.logged event.

        Requires: decision_id, title, choice OR rationale
        """
        decision_id = data.get("decision_id")
        title = data.get("title", "")
        choice = data.get("choice", "")
        rationale = data.get("rationale", "")

        if not decision_id or not title:
            return None
        if not choice and not rationale:
            return None

        # Determine category
        tags = self._extract_tags(data)
        category = "architecture" if any("arch" in t for t in tags) else "planning"

        summary = f"Decided: {title}"
        if choice:
            summary += f" -> {choice}"

        return PromotedEntry(
            category=category,
            entry_type="decision",
            summary=summary[:500],
            outcome="success",
            importance_score=max(7, data.get("importance", 7)),
            reasoning=rationale[:2000] if rationale else None,
            tags=tags,
            linked_decisions=[str(decision_id)],
            linked_files=self._redact_files(data.get("affected_files")),
        )

    def _promote_task_failed(self, data: dict[str, Any]) -> Optional[PromotedEntry]:
        """Promote task.failed event."""
        task_id = data.get("task_id")
        title = data.get("title", "")
        error_msg = data.get("error", {}).get("message", "") if isinstance(data.get("error"), dict) else str(data.get("error", ""))

        if not task_id and not title and not error_msg:
            return None

        summary = f"Task failed: {title or task_id or 'Unknown task'}"
        if error_msg:
            summary += f" - {error_msg[:100]}"

        details = {
            "task_id": task_id,
            "error": error_msg[:500] if error_msg else None,
            "service": data.get("service"),
            "ci_job": data.get("ci_job"),
        }
        # Redact details
        details = self.redactor.redact_payload(details)

        return PromotedEntry(
            category="debugging",
            entry_type="error",
            summary=summary[:500],
            outcome="failed",
            importance_score=7,
            details=details,
            tags=self._extract_tags(data),
            duration_sec=data.get("duration_seconds"),
        )

    def _promote_task_blocked(self, data: dict[str, Any]) -> Optional[PromotedEntry]:
        """Promote task.blocked event."""
        task_id = data.get("task_id")
        title = data.get("title", "")
        reason = data.get("reason", "")

        if not task_id and not title:
            return None

        summary = f"Task blocked: {title or task_id}"
        if reason:
            summary += f" - {reason[:100]}"

        return PromotedEntry(
            category="debugging",
            entry_type="blocker",
            summary=summary[:500],
            outcome="blocked",
            importance_score=7,
            details=self.redactor.redact_payload({"task_id": task_id, "reason": reason}),
            tags=self._extract_tags(data),
        )

    def _promote_task_completed(self, data: dict[str, Any]) -> Optional[PromotedEntry]:
        """Promote task.completed event."""
        task_id = data.get("task_id")
        title = data.get("title", "")

        if not task_id and not title:
            return None

        return PromotedEntry(
            category="implementation",
            entry_type="milestone",
            summary=f"Completed: {title or task_id}"[:500],
            outcome="success",
            importance_score=5,
            tags=self._extract_tags(data),
            duration_sec=data.get("duration_seconds"),
        )

    def _promote_error_encountered(self, data: dict[str, Any]) -> Optional[PromotedEntry]:
        """Promote error.encountered event."""
        message = data.get("message", "")
        error_kind = data.get("error_kind", "error")

        if not message:
            return None

        # Extract headline
        headline = message.split("\n")[0][:100]
        summary = f"Error: {error_kind} - {headline}" if error_kind != "error" else f"Error: {headline}"

        details = {
            "error_kind": error_kind,
            "file": data.get("file"),
            "test": data.get("test"),
            "ci_job": data.get("ci_job"),
        }

        return PromotedEntry(
            category="debugging",
            entry_type="error",
            summary=summary[:500],
            outcome="in_progress",
            importance_score=6,
            details=self.redactor.redact_payload(details),
            tags=self._extract_tags(data),
        )

    def _promote_workflow_phase_changed(
        self, data: dict[str, Any]
    ) -> Optional[PromotedEntry]:
        """Promote workflow.phase_changed event."""
        from_phase = data.get("from_phase", "unknown")
        to_phase = data.get("to_phase", "unknown")

        if from_phase == "unknown" and to_phase == "unknown":
            return None

        # Derive category from to_phase
        phase_to_category = {
            "planning": "planning",
            "implementation": "implementation",
            "review": "review",
            "audit": "review",
            "deployment": "deployment",
            "maintenance": "deployment",
        }
        category = phase_to_category.get(to_phase, "planning")

        return PromotedEntry(
            category=category,
            entry_type="workflow_transition",
            summary=f"Phase: {from_phase} -> {to_phase}",
            outcome="success",
            importance_score=5,
            workflow_phase=to_phase if to_phase in phase_to_category else None,
            tags=self._extract_tags(data),
        )

    def _promote_manual_memory_store(
        self, data: dict[str, Any]
    ) -> Optional[PromotedEntry]:
        """Promote manual.memory_store event.

        Requires: category, entry_type, summary
        """
        category = data.get("category")
        entry_type = data.get("entry_type")
        summary = data.get("summary")

        if not category or not entry_type or not summary:
            return None

        # Validate category/entry_type
        valid_categories = {
            "planning",
            "implementation",
            "review",
            "debugging",
            "research",
            "deployment",
            "architecture",
            "documentation",
        }
        valid_entry_types = {
            "manual_note",
            "decision",
            "blocker",
            "resolution",
            "milestone",
        }

        if category not in valid_categories or entry_type not in valid_entry_types:
            return None

        # Get importance from payload or default
        importance = data.get("importance_score", 6)
        if not isinstance(importance, int) or not 1 <= importance <= 10:
            importance = 6

        details = data.get("details")
        if details:
            details = self.redactor.redact_payload(details)

        links = data.get("links", {})

        return PromotedEntry(
            category=category,
            entry_type=entry_type,
            summary=summary[:500],
            outcome=data.get("outcome", "in_progress"),
            importance_score=importance,
            workflow_phase=data.get("workflow_phase"),
            details=details,
            reasoning=data.get("reasoning"),
            tags=self._extract_tags(data),
            linked_decisions=links.get("decisions"),
            linked_files=self._redact_files(links.get("files")),
            linked_commits=links.get("commits"),
            linked_chat_range=links.get("chat_range"),
        )
