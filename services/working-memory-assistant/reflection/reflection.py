"""
ReflectionGenerator - Deterministic reflection card generation.

Per docs/spec/dope-memory/v1/08_phased_roadmap.md Phase 2:
- Generate reflection cards at session end / idle trigger
- Top-3 decisions/blockers (deterministic sorting)
- Progress summary by entry_type + outcomes
- Suggested next steps (blocker -> task -> in_progress)

No LLM calls - purely rule-based.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional


class ReflectionGenerator:
    """Deterministic reflection card generator from work log entries."""

    def __init__(self, chronicle_store):
        """Initialize with a ChronicleStore instance."""
        self.store = chronicle_store

    def generate_reflection(
        self,
        workspace_id: str,
        instance_id: str,
        session_id: Optional[str] = None,
        window_start: Optional[str] = None,
        window_end: Optional[str] = None,
    ) -> dict[str, Any]:
        """Generate a reflection card from work log entries.

        Args:
            workspace_id: Workspace identifier
            instance_id: Instance identifier
            session_id: Optional session filter
            window_start: Optional ISO timestamp (default: 2 hours ago)
            window_end: Optional ISO timestamp (default: now)

        Returns:
            Reflection card dict ready for SQLite insert
        """
        now_utc = datetime.now(timezone.utc)

        # Default window: last 2 hours
        if not window_start:
            window_start = (now_utc - timedelta(hours=2)).isoformat()
        if not window_end:
            window_end = now_utc.isoformat()

        # Fetch entries in window
        entries = self.store.get_work_log_window(
            workspace_id=workspace_id,
            instance_id=instance_id,
            session_id=session_id,
            window_start=window_start,
            window_end=window_end,
        )

        if not entries:
            # Empty reflection
            return {
                "reflection_id": None,
                "workspace_id": workspace_id,
                "instance_id": instance_id,
                "session_id": session_id,
                "window_start": window_start,
                "window_end": window_end,
                "trajectory_summary": "No activity in window",
                "top_decisions": [],
                "top_blockers": [],
                "progress_summary": {},
                "suggested_next": [],
                "source_entry_ids": [],
            }

        # Extract components
        top_decisions = self.select_top_decisions(entries)
        top_blockers = self.select_top_blockers(entries)
        progress = self.compute_progress_summary(entries)
        suggested_next = self.compute_suggested_next(entries, top_blockers)
        trajectory = self._compute_trajectory(entries)

        source_entry_ids = [e["id"] for e in entries]

        return {
            "reflection_id": str(uuid.uuid4()),
            "workspace_id": workspace_id,
            "instance_id": instance_id,
            "session_id": session_id,
            "window_start": window_start,
            "window_end": window_end,
            "trajectory_summary": trajectory,
            "top_decisions": top_decisions,
            "top_blockers": top_blockers,
            "progress_summary": progress,
            "suggested_next": suggested_next,
            "source_entry_ids": source_entry_ids,
        }

    def select_top_decisions(self, entries: list[dict]) -> list[dict]:
        """Select top 3 decisions, deterministic sort.

        Sort by: (importance_score DESC, ts_utc DESC, id ASC)
        """
        decisions = [e for e in entries if e["entry_type"] == "decision"]
        # Sort: importance_score descending (higher first), ts_utc descending (recent first), id ascending
        decisions.sort(
            key=lambda x: (x["importance_score"], x["ts_utc"], -ord(x["id"][0]) if x["id"] else 0),
            reverse=True,
        )
        return [{"id": d["id"], "summary": d["summary"]} for d in decisions[:3]]

    def select_top_blockers(self, entries: list[dict]) -> list[dict]:
        """Select top 3 blockers/errors, deterministic sort.

        Sort by: (importance_score DESC, ts_utc DESC, id ASC)
        """
        blockers = [e for e in entries if e["entry_type"] in ("blocker", "error")]
        blockers.sort(
            key=lambda x: (x["importance_score"], x["ts_utc"], -ord(x["id"][0]) if x["id"] else 0),
            reverse=True,
        )
        return [{"id": b["id"], "summary": b["summary"]} for b in blockers[:3]]

    def compute_progress_summary(self, entries: list[dict]) -> dict[str, Any]:
        """Compute progress summary by category and outcomes."""
        by_category = {}
        by_outcome = {}

        for e in entries:
            category = e["category"]
            outcome = e["outcome"]

            by_category[category] = by_category.get(category, 0) + 1
            by_outcome[outcome] = by_outcome.get(outcome, 0) + 1

        return {
            "total_entries": len(entries),
            "by_type": by_category,  # Changed from entry_type to category
            "by_outcome": by_outcome,
        }

    def compute_suggested_next(
        self, entries: list[dict], top_blockers: list[dict]
    ) -> list[str]:
        """Compute suggested next steps (deterministic).

        Priority:
        1. Unresolved blockers first
        2. Top decisions to implement
        3. Last incomplete tasks
        4. Last in_progress items
        """
        suggestions = []

        # 1. Blockers
        if top_blockers:
            suggestions.append(f"Resolve: {top_blockers[0]['summary'][:80]}")

        # 2. Decisions to implement
        decisions = [e for e in entries if e["entry_type"] == "decision"]
        if decisions and len(suggestions) < 3:
            # Sort by importance DESC (highest first)
            decisions.sort(key=lambda x: x["importance_score"], reverse=True)
            suggestions.append(f"Implement: {decisions[0]['summary'][:80]}")

        # 3. Incomplete tasks (outcome != success)
        incomplete = [
            e
            for e in entries
            if e["entry_type"] in ("task_event", "workflow_transition")
            and e["outcome"] != "success"
        ]
        if incomplete and len(suggestions) < 3:
            suggestions.append(f"Complete: {incomplete[0]['summary'][:80]}")

        # 4. In-progress items
        in_progress = [e for e in entries if e["outcome"] == "in_progress"]
        if in_progress and len(suggestions) < 3:
            suggestions.append(f"Continue: {in_progress[0]['summary'][:80]}")

        return suggestions[:3]  # Cap at 3

    def _compute_trajectory(self, entries: list[dict]) -> str:
        """Compute 1-sentence trajectory summary."""
        if not entries:
            return "No activity"

        # Find most common category
        categories = {}
        for e in entries:
            cat = e["category"]
            categories[cat] = categories.get(cat, 0) + 1

        top_cat = max(categories.items(), key=lambda x: x[1])[0]
        return f"Active in {top_cat}"
