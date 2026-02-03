"""
ReflectionGenerator - Deterministic reflection card generation.

Per docs/spec/dope-memory/v1/08_phased_roadmap.md Phase 2:
- Generate reflection cards at session end / idle trigger
- Top-3 decisions/blockers (deterministic sorting)
- Progress summary by entry_type + outcomes
- Suggested next steps (blocker -> task -> in_progress)

No LLM calls - purely rule-based.
"""

import json
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

        # Idempotency check: if recent reflection exists with same window_end (within 5 min), return it
        existing = self._check_existing_reflection(workspace_id, instance_id, window_end, session_id)
        if existing:
            return existing

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

    def _check_existing_reflection(
        self,
        workspace_id: str,
        instance_id: str,
        window_end: str,
        session_id: Optional[str] = None,
    ) -> Optional[dict[str, Any]]:
        """Check if a reflection already exists for this window_end (within 5 min).
        
        Returns existing reflection dict or None.
        """
        conn = self.store.connect()
        
        # Parse window_end timestamp - handle both string and datetime
        if isinstance(window_end, datetime):
            window_end_dt = window_end
        elif isinstance(window_end, str):
            # Remove timezone suffix if present for parsing
            window_end_clean = window_end.replace('+00:00', '').replace('Z', '')
            try:
                window_end_dt = datetime.fromisoformat(window_end_clean)
            except ValueError:
                # If parsing fails, just return None (no idempotency check)
                return None
        else:
            return None
        
        # Ensure timezone aware
        if window_end_dt.tzinfo is None:
            window_end_dt = window_end_dt.replace(tzinfo=timezone.utc)
        
        window_end_min = (window_end_dt - timedelta(minutes=5)).isoformat()
        window_end_max = (window_end_dt + timedelta(minutes=5)).isoformat()
        
        if session_id:
            row = conn.execute(
                """
                SELECT id, window_start_utc, window_end_utc, trajectory,
                       top_decisions_json, top_blockers_json, progress_json, next_suggested_json
                FROM reflection_cards
                WHERE workspace_id = ? AND instance_id = ? AND session_id = ?
                  AND window_end_utc >= ? AND window_end_utc <= ?
                ORDER BY ts_utc DESC
                LIMIT 1
                """,
                (workspace_id, instance_id, session_id, window_end_min, window_end_max),
            ).fetchone()
        else:
            row = conn.execute(
                """
                SELECT id, window_start_utc, window_end_utc, trajectory,
                       top_decisions_json, top_blockers_json, progress_json, next_suggested_json
                FROM reflection_cards
                WHERE workspace_id = ? AND instance_id = ?
                  AND window_end_utc >= ? AND window_end_utc <= ?
                ORDER BY ts_utc DESC
                LIMIT 1
                """,
                (workspace_id, instance_id, window_end_min, window_end_max),
            ).fetchone()
        
        if not row:
            return None
        
        import json
        return {
            "reflection_id": row["id"],
            "workspace_id": workspace_id,
            "instance_id": instance_id,
            "session_id": session_id,
            "window_start": row["window_start_utc"],
            "window_end": row["window_end_utc"],
            "trajectory_summary": row["trajectory"],
            "top_decisions": json.loads(row["top_decisions_json"]),
            "top_blockers": json.loads(row["top_blockers_json"]),
            "progress_summary": json.loads(row["progress_json"]),
            "suggested_next": json.loads(row["next_suggested_json"]),
            "source_entry_ids": [],  # Not stored separately, would need to reconstruct
        }

    def select_top_decisions(self, entries: list[dict]) -> list[dict]:
        """Select top 3 decisions, deterministic sort.

        Sort by: (importance_score DESC, ts_utc DESC, id ASC)
        """
        decisions = [e for e in entries if e["entry_type"] == "decision"]
        # Sort: importance_score DESC (negate), ts_utc DESC (negate), id ASC (normal)
        decisions.sort(
            key=lambda x: (-x["importance_score"], x["ts_utc"], x["id"]),
            reverse=False,  # Don't reverse because we want DESC for first two, ASC for last
        )
        # Actually, that's still wrong. Let me think...
        # For DESC on ts_utc, we want LATER timestamps first
        # When we negate a timestamp string, that doesn't work
        # Solution: use tuple of (-importance, -timestamp_as_number, id) OR just use reverse on ts
        decisions.sort(
            key=lambda x: (
                -x["importance_score"],  # Higher scores first
                x["ts_utc"],             # This needs to be reversed for DESC
                x["id"]                  # ASC
            )
        )
        # Wait, if we don't use reverse=True, ts_utc will sort ascending (older first)
        # We want DESC (newer first), so we need to negate or reverse
        # Let's use proper multi-key sorting:
        decisions.sort(
            key=lambda x: x["id"]  # Third sort: id ASC
        )
        decisions.sort(
            key=lambda x: x["ts_utc"], reverse=True  # Second sort: ts_utc DESC
        )
        decisions.sort(
            key=lambda x: x["importance_score"], reverse=True  # First sort: importance DESC
        )
        return [{"id": d["id"], "summary": d["summary"]} for d in decisions[:3]]

    def select_top_blockers(self, entries: list[dict]) -> list[dict]:
        """Select top 3 blockers/errors, deterministic sort.

        Sort by: (importance_score DESC, ts_utc DESC, id ASC)
        """
        blockers = [e for e in entries if e["entry_type"] in ("blocker", "error")]
        # Stable multi-key sort: sort in reverse order of priority
        blockers.sort(
            key=lambda x: x["id"]  # Third sort: id ASC
        )
        blockers.sort(
            key=lambda x: x["ts_utc"], reverse=True  # Second sort: ts_utc DESC
        )
        blockers.sort(
            key=lambda x: x["importance_score"], reverse=True  # First sort: importance DESC
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
    ) -> list[dict]:
        """Compute suggested next steps (deterministic).

        Priority:
        1. Unresolved blockers first
        2. Top decisions to implement
        3. Last incomplete tasks
        4. Last in_progress items
        
        Returns:
            List of max 3 dicts with 'type' and 'summary' fields
        """
        suggestions = []

        # 1. Blockers
        if top_blockers:
            suggestions.append({
                "type": "resolve_blocker",
                "summary": f"Resolve: {top_blockers[0]['summary'][:80]}",
                "entry_id": top_blockers[0]["id"],
            })

        # 2. Decisions to implement
        decisions = [e for e in entries if e["entry_type"] == "decision"]
        if decisions and len(suggestions) < 3:
            # Sort by importance DESC, ts DESC, id ASC for determinism
            decisions.sort(key=lambda x: x["id"])
            decisions.sort(key=lambda x: x["ts_utc"], reverse=True)
            decisions.sort(key=lambda x: x["importance_score"], reverse=True)
            suggestions.append({
                "type": "implement_decision",
                "summary": f"Implement: {decisions[0]['summary'][:80]}",
                "entry_id": decisions[0]["id"],
            })

        # 3. Incomplete tasks (outcome != success)
        incomplete = [
            e
            for e in entries
            if e["entry_type"] in ("task_event", "workflow_transition")
            and e["outcome"] != "success"
        ]
        if incomplete and len(suggestions) < 3:
            # Use first incomplete (already sorted by importance_score DESC, ts_utc DESC, id ASC from get_work_log_window)
            suggestions.append({
                "type": "complete_task",
                "summary": f"Complete: {incomplete[0]['summary'][:80]}",
                "entry_id": incomplete[0]["id"],
            })

        # 4. In-progress items
        in_progress = [e for e in entries if e["outcome"] == "in_progress"]
        if in_progress and len(suggestions) < 3:
            suggestions.append({
                "type": "continue_work",
                "summary": f"Continue: {in_progress[0]['summary'][:80]}",
                "entry_id": in_progress[0]["id"],
            })

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
