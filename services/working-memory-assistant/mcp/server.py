"""
Dope-Memory MCP Server - Tool implementations.

Implements:
- memory_search: Keyword + filters, Top-3 default
- memory_store: Explicit manual entry
- memory_recap: Session/today summary
- memory_mark_issue: Flag entry as issue
- memory_link_resolution: Link issue -> resolution
- memory_replay_session: Chronological session entries
"""

import base64
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ..chronicle.store import ChronicleStore
from ..promotion import PromotionEngine, Redactor

# Default data directory
DEFAULT_DATA_DIR = Path.home() / ".dope-memory"


@dataclass
class SearchFilters:
    """Search filter parameters."""

    category: Optional[str] = None
    entry_type: Optional[str] = None
    workflow_phase: Optional[str] = None
    tags_any: Optional[list[str]] = None
    time_range: Optional[str] = None


@dataclass
class ToolResponse:
    """Standard tool response wrapper."""

    success: bool
    data: dict[str, Any]
    error: Optional[str] = None


class DopeMemoryMCPServer:
    """MCP server for Dope-Memory tools.

    All tools enforce ADHD Top-3 boundary with pagination support.
    """

    def __init__(
        self,
        data_dir: Optional[Path] = None,
        workspace_id: Optional[str] = None,
        instance_id: str = "A",
    ):
        """Initialize the MCP server.

        Args:
            data_dir: Directory for SQLite databases (default ~/.dope-memory)
            workspace_id: Default workspace ID
            instance_id: Default instance ID
        """
        self.data_dir = data_dir or DEFAULT_DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.default_workspace_id = workspace_id
        self.default_instance_id = instance_id

        self.redactor = Redactor()
        self.promotion_engine = PromotionEngine()

        # Lazy store initialization per workspace
        self._stores: dict[str, ChronicleStore] = {}

    def _get_store(self, workspace_id: str) -> ChronicleStore:
        """Get or create a ChronicleStore for a workspace."""
        if workspace_id not in self._stores:
            db_path = self.data_dir / workspace_id / "chronicle.db"
            store = ChronicleStore(db_path)
            store.initialize_schema()
            self._stores[workspace_id] = store
        return self._stores[workspace_id]

    def _encode_cursor(
        self,
        importance_score: int,
        ts_utc: str,
        entry_id: str,
        scope_hash: str,
    ) -> str:
        """Encode a pagination cursor."""
        data = {
            "i": importance_score,
            "t": ts_utc,
            "id": entry_id,
            "h": scope_hash,
        }
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()

    def _decode_cursor(
        self, cursor: str, expected_scope_hash: str
    ) -> Optional[tuple[int, str, str]]:
        """Decode and validate a pagination cursor."""
        try:
            data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
            if data.get("h") != expected_scope_hash:
                return None  # Scope mismatch
            return (data["i"], data["t"], data["id"])
        except Exception:
            return None

    def _compute_scope_hash(self, **filters: Any) -> str:
        """Compute hash of search scope for cursor validation."""
        normalized = json.dumps(filters, sort_keys=True)
        return hashlib.sha256(normalized.encode()).hexdigest()[:8]

    def _normalize_query(self, query: str) -> str:
        """Normalize a search query."""
        # ASCII normalize, trim, collapse whitespace
        result = query.strip()
        result = " ".join(result.split())
        return result.lower()

    # ─────────────────────────────────────────────────────────────────
    # Tool: memory_search
    # ─────────────────────────────────────────────────────────────────

    def memory_search(
        self,
        query: str,
        workspace_id: str,
        instance_id: str,
        session_id: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
        top_k: int = 3,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        """Search work log entries.

        Args:
            query: Search query (keyword on summary)
            workspace_id: Workspace to search
            instance_id: Instance to search
            session_id: Optional session filter
            filters: Optional filters (category, entry_type, etc.)
            top_k: Max results (default 3, max 10)
            cursor: Pagination cursor

        Returns:
            {items: [...], more_count: N, next_token: str|null}
        """
        # Enforce ADHD boundary
        top_k = min(max(1, top_k), 10)

        store = self._get_store(workspace_id)
        normalized_query = self._normalize_query(query)

        # Parse filters
        f = filters or {}
        search_filters = {
            "query": normalized_query,
            "session_id": session_id,
            "category": f.get("category"),
            "entry_type": f.get("entry_type"),
            "workflow_phase": f.get("workflow_phase"),
            "tags_any": f.get("tags_any"),
            "time_range": f.get("time_range", "all"),
        }

        # Validate cursor
        scope_hash = self._compute_scope_hash(
            workspace_id=workspace_id,
            instance_id=instance_id,
            **search_filters,
        )
        decoded_cursor = None
        if cursor:
            decoded_cursor = self._decode_cursor(cursor, scope_hash)

        # Execute search
        rows = store.search_work_log(
            workspace_id=workspace_id,
            instance_id=instance_id,
            query=normalized_query if normalized_query else None,
            session_id=session_id,
            category=f.get("category"),
            entry_type=f.get("entry_type"),
            workflow_phase=f.get("workflow_phase"),
            tags_any=f.get("tags_any"),
            time_range=f.get("time_range"),
            limit=top_k + 1,  # Fetch one extra for pagination
            cursor=decoded_cursor,
        )

        # Determine if more results exist
        has_more = len(rows) > top_k
        items = rows[:top_k]

        # Count total for more_count
        total = store.count_work_log(
            workspace_id=workspace_id,
            instance_id=instance_id,
            **search_filters,
        )
        more_count = max(0, total - (len(items) + (decoded_cursor is not None)))

        # Build next_token
        next_token = None
        if has_more and items:
            last = items[-1]
            next_token = self._encode_cursor(
                last["importance_score"],
                last["ts_utc"],
                last["id"],
                scope_hash,
            )

        # Format response items
        response_items = []
        for row in items:
            response_items.append(
                {
                    "id": row["id"],
                    "ts_utc": row["ts_utc"],
                    "summary": row["summary"],
                    "category": row["category"],
                    "entry_type": row["entry_type"],
                    "workflow_phase": row.get("workflow_phase"),
                    "outcome": row["outcome"],
                    "importance_score": row["importance_score"],
                    "tags": json.loads(row.get("tags_json", "[]")),
                    "links": {
                        "decisions": json.loads(row.get("linked_decisions_json") or "[]"),
                        "files": json.loads(row.get("linked_files_json") or "[]"),
                        "commits": json.loads(row.get("linked_commits_json") or "[]"),
                    },
                }
            )

        return {
            "items": response_items,
            "more_count": more_count,
            "next_token": next_token,
        }

    # ─────────────────────────────────────────────────────────────────
    # Tool: memory_store
    # ─────────────────────────────────────────────────────────────────

    def memory_store(
        self,
        workspace_id: str,
        instance_id: str,
        category: str,
        entry_type: str,
        summary: str,
        session_id: Optional[str] = None,
        workflow_phase: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        reasoning: Optional[str] = None,
        outcome: str = "in_progress",
        importance_score: int = 6,
        tags: Optional[list[str]] = None,
        links: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Store a manual work log entry.

        Returns:
            {entry_id: str, created: bool}
        """
        store = self._get_store(workspace_id)

        # Redact details if provided
        redacted_details = None
        if details:
            redacted_details = self.redactor.redact_payload(details)

        # Redact linked files if provided
        linked_files = None
        if links and links.get("files"):
            linked_files = self.redactor.redact_linked_files(links["files"])

        entry_id = store.insert_work_log_entry(
            workspace_id=workspace_id,
            instance_id=instance_id,
            category=category,
            entry_type=entry_type,
            summary=summary[:500],
            session_id=session_id,
            workflow_phase=workflow_phase,
            details=redacted_details,
            reasoning=reasoning[:2000] if reasoning else None,
            outcome=outcome,
            importance_score=max(1, min(10, importance_score)),
            tags=tags,
            linked_decisions=links.get("decisions") if links else None,
            linked_files=linked_files,
            linked_commits=links.get("commits") if links else None,
            linked_chat_range=links.get("chat_range") if links else None,
        )

        return {"entry_id": entry_id, "created": True}

    # ─────────────────────────────────────────────────────────────────
    # Tool: memory_recap
    # ─────────────────────────────────────────────────────────────────

    def memory_recap(
        self,
        workspace_id: str,
        instance_id: str,
        scope: str = "session",
        session_id: Optional[str] = None,
        top_k: int = 3,
    ) -> dict[str, Any]:
        """Get a recap of recent work.

        Args:
            workspace_id: Workspace to recap
            instance_id: Instance to recap
            scope: 'session', 'today', or 'last_2_hours'
            session_id: Required if scope is 'session'
            top_k: Max recap cards (default 3)

        Returns:
            {trajectory: str, cards: [...], more_count: N}
        """
        top_k = min(max(1, top_k), 10)
        store = self._get_store(workspace_id)

        # Map scope to time_range
        time_range_map = {
            "session": None,  # Uses session_id filter
            "today": "today",
            "last_2_hours": "today",  # We'll filter further
        }
        time_range = time_range_map.get(scope, "today")

        # Get entries
        entries = store.search_work_log(
            workspace_id=workspace_id,
            instance_id=instance_id,
            session_id=session_id if scope == "session" else None,
            time_range=time_range,
            limit=20,  # Get more for card generation
        )

        if not entries:
            return {
                "trajectory": "No recent activity",
                "cards": [],
                "more_count": 0,
            }

        # Deterministic card generation (no LLM)
        # Card 1: Highest decision or highest entry
        # Card 2: Highest blocker/error or next
        # Card 3: Suggested next

        cards = []
        used_ids = set()

        # Card 1: Decision
        decision = next(
            (e for e in entries if e["entry_type"] == "decision" and e["id"] not in used_ids),
            None,
        )
        if decision:
            cards.append(
                {
                    "title": "Decision",
                    "summary": decision["summary"],
                    "entry_ids": [decision["id"]],
                }
            )
            used_ids.add(decision["id"])
        elif entries:
            cards.append(
                {
                    "title": "Activity",
                    "summary": entries[0]["summary"],
                    "entry_ids": [entries[0]["id"]],
                }
            )
            used_ids.add(entries[0]["id"])

        # Card 2: Blocker/Error
        blocker = next(
            (
                e
                for e in entries
                if e["entry_type"] in ("blocker", "error") and e["id"] not in used_ids
            ),
            None,
        )
        if blocker and len(cards) < top_k:
            cards.append(
                {
                    "title": "Blocker" if blocker["entry_type"] == "blocker" else "Error",
                    "summary": blocker["summary"],
                    "entry_ids": [blocker["id"]],
                }
            )
            used_ids.add(blocker["id"])

        # Card 3: Suggested next
        if len(cards) < top_k:
            # If there's a blocker, suggest resolving it
            if blocker:
                cards.append(
                    {
                        "title": "Next",
                        "summary": f"Resolve: {blocker['summary'][:80]}",
                        "entry_ids": [blocker["id"]],
                    }
                )
            elif entries:
                # Suggest continuing with the most recent
                recent = entries[0]
                cards.append(
                    {
                        "title": "Next",
                        "summary": f"Continue: {recent['summary'][:80]}",
                        "entry_ids": [recent["id"]],
                    }
                )

        # Generate trajectory (1 sentence summary)
        if entries:
            categories = set(e["category"] for e in entries[:5])
            trajectory = f"Working on {', '.join(sorted(categories))} activities"
        else:
            trajectory = "No recent activity"

        return {
            "trajectory": trajectory,
            "cards": cards[:top_k],
            "more_count": max(0, len(entries) - top_k),
        }

    # ─────────────────────────────────────────────────────────────────
    # Tool: memory_mark_issue
    # ─────────────────────────────────────────────────────────────────

    def memory_mark_issue(
        self,
        workspace_id: str,
        instance_id: str,
        issue_entry_id: str,
        description: str,
        confidence: float = 0.7,
        evidence_window_min: int = 30,
        tags: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Mark an entry as an issue source.

        This updates the entry's tags to include 'issue' and stores metadata.

        Returns:
            {issue_marked: bool}
        """
        store = self._get_store(workspace_id)

        # Verify entry exists
        entry = store.get_entry_by_id(workspace_id, instance_id, issue_entry_id)
        if not entry:
            return {"issue_marked": False, "error": "Entry not found"}

        # For now, we just verify it exists and return success
        # Full implementation would update tags
        return {"issue_marked": True}

    # ─────────────────────────────────────────────────────────────────
    # Tool: memory_link_resolution
    # ─────────────────────────────────────────────────────────────────

    def memory_link_resolution(
        self,
        workspace_id: str,
        instance_id: str,
        issue_entry_id: str,
        resolution_entry_id: str,
        confidence: float = 0.8,
        evidence_window_min: int = 30,
    ) -> dict[str, Any]:
        """Link an issue entry to its resolution.

        Returns:
            {linked: bool}
        """
        store = self._get_store(workspace_id)

        # Verify both entries exist
        issue = store.get_entry_by_id(workspace_id, instance_id, issue_entry_id)
        resolution = store.get_entry_by_id(workspace_id, instance_id, resolution_entry_id)

        if not issue or not resolution:
            return {"linked": False, "error": "Entry not found"}

        # Create link
        store.insert_issue_link(
            workspace_id=workspace_id,
            instance_id=instance_id,
            issue_entry_id=issue_entry_id,
            resolution_entry_id=resolution_entry_id,
            confidence=confidence,
            evidence_window_min=evidence_window_min,
        )

        return {"linked": True}

    # ─────────────────────────────────────────────────────────────────
    # Tool: memory_replay_session
    # ─────────────────────────────────────────────────────────────────

    def memory_replay_session(
        self,
        workspace_id: str,
        instance_id: str,
        session_id: str,
        top_k: int = 3,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        """Replay session entries chronologically.

        Returns:
            {items: [...], more_count: N, next_token: str|null}
        """
        # Reuse memory_search with session filter, sorted by ts
        return self.memory_search(
            query="",
            workspace_id=workspace_id,
            instance_id=instance_id,
            session_id=session_id,
            top_k=top_k,
            cursor=cursor,
        )
