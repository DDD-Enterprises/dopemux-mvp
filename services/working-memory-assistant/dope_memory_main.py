#!/usr/bin/env python3
"""
Dope-Memory HTTP Server - FastAPI wrapper for MCP tools.

Exposes Dope-Memory MCP tools over HTTP on port 3020.
This is the canonical entry point for the Dope-Memory service.

Per registry.yaml:
- Port: 3020
- Health: /health
- Category: mcp
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import sys
import uuid
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

# Add parent dir to path for package imports when run directly
_THIS_DIR = Path(__file__).parent.resolve()
if str(_THIS_DIR) not in sys.path:
    sys.path.insert(0, str(_THIS_DIR))

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Use absolute imports now that we've fixed the path
from canonical_ledger import CanonicalLedgerError, resolve_canonical_ledger
from chronicle.store import ChronicleStore
from promotion.redactor import Redactor
from promotion.promotion import PromotionEngine
from reflection.reflection import ReflectionGenerator
from trajectory.manager import TrajectoryManager

# Logging setup
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Configuration
PORT = int(os.getenv("PORT", os.getenv("DOPE_MEMORY_PORT", "3020")))
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", str(PORT)))
SERVICE_NAME = os.getenv("SERVICE_NAME", "dope-memory")
HEALTH_CHECK_PATH = os.getenv("HEALTH_CHECK_PATH", "/health")
DATA_DIR = Path(os.getenv("DOPE_MEMORY_DATA_DIR", str(Path.home() / ".dope-memory")))
DEFAULT_WORKSPACE_ID = os.getenv("DOPE_MEMORY_WORKSPACE_ID", "default")
DEFAULT_INSTANCE_ID = os.getenv("DOPE_MEMORY_INSTANCE_ID", "A")

# CORS configuration
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8097,http://adhd-dashboard:8097"
    ).split(",") if o.strip()
]

# CORS configuration
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:8097,http://adhd-dashboard:8097"
    ).split(",") if o.strip()
]

# CORS configuration
# ═══════════════════════════════════════════════════════════════════════════════
# MCP Server (Inline to avoid import issues)
# ═══════════════════════════════════════════════════════════════════════════════


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
        workspace_id: str,
        instance_id: str = "A",
    ):
        self.default_workspace_id = workspace_id
        self.default_instance_id = instance_id
        self.redactor = Redactor()
        self.promotion_engine = PromotionEngine()
        # Keyed by resolved canonical ledger path
        self._stores: dict[str, ChronicleStore] = {}

    def _get_store(self, workspace_id: str) -> ChronicleStore:
        """Get or create a ChronicleStore for the canonical ledger.

        Resolves workspace_id to the single canonical ledger per ADR-213.
        """
        db_path = resolve_canonical_ledger(workspace_id)
        path_key = str(db_path)
        if path_key not in self._stores:
            store = ChronicleStore(db_path)
            store.initialize_schema()
            self._stores[path_key] = store
        return self._stores[path_key]

    def _encode_cursor(
        self, importance_score: int, ts_utc: str, entry_id: str, scope_hash: str
    ) -> str:
        """Encode a pagination cursor."""
        data = {"i": importance_score, "t": ts_utc, "id": entry_id, "h": scope_hash}
        return base64.urlsafe_b64encode(json.dumps(data).encode()).decode()

    def _decode_cursor(
        self, cursor: str, expected_scope_hash: str
    ) -> Optional[tuple[int, str, str]]:
        """Decode and validate a pagination cursor."""
        try:
            data = json.loads(base64.urlsafe_b64decode(cursor.encode()))
            if data.get("h") != expected_scope_hash:
                return None
            return (data["i"], data["t"], data["id"])
        except Exception:
            return None

    def _compute_scope_hash(self, **filters: Any) -> str:
        """Compute hash of search scope for cursor validation."""
        normalized = json.dumps(filters, sort_keys=True)
        return hashlib.sha256(normalized.encode()).hexdigest()[:8]

    def memory_search(
        self,
        query: str,
        workspace_id: str,
        instance_id: str,
        session_id: Optional[str] = None,
        filters: Optional[dict[str, Any]] = None,
        top_k: int = 3,
        cursor: Optional[str] = None,
        include_superseded: bool = False,
    ) -> ToolResponse:
        """Search work log entries with trajectory boost applied to ranking."""
        try:
            top_k = min(max(1, top_k), 10)
            store = self._get_store(workspace_id)
            
            f = filters or {}
            search_filters = {
                "query": query.strip().lower(),
                "session_id": session_id,
                "category": f.get("category"),
                "entry_type": f.get("entry_type"),
                "workflow_phase": f.get("workflow_phase"),
                "tags_any": f.get("tags_any"),
                "time_range": f.get("time_range", "all"),
            }

            scope_hash = self._compute_scope_hash(
                workspace_id=workspace_id, instance_id=instance_id, **search_filters
            )
            decoded_cursor = None
            if cursor:
                decoded_cursor = self._decode_cursor(cursor, scope_hash)

            # Fetch extra rows to account for boost re-ranking
            # Fetch 2x top_k to have candidates for boost re-ranking
            fetch_limit = min(top_k * 2, 20)
            
            rows = store.search_work_log(
                workspace_id=workspace_id,
                instance_id=instance_id,
                query=query.strip().lower() if query.strip() else None,
                session_id=session_id,
                category=f.get("category"),
                entry_type=f.get("entry_type"),
                workflow_phase=f.get("workflow_phase"),
                tags_any=f.get("tags_any"),
                time_range=f.get("time_range"),
                limit=fetch_limit + 1,
                cursor=decoded_cursor,
                include_superseded=include_superseded,
            )

            # Apply trajectory boost to ranking
            trajectory_mgr = TrajectoryManager(store)
            trajectory = trajectory_mgr.get_trajectory(workspace_id, instance_id)
            
            # Calculate boosted scores
            boosted_rows = []
            for row in rows:
                base_score = row["importance_score"]
                boost = trajectory_mgr.get_boost_factor(row, trajectory)
                boosted_score = base_score + boost
                
                boosted_rows.append({
                    **row,
                    "_boosted_score": boosted_score,
                    "_boost_applied": boost,
                })
            
            # Re-sort by boosted score (desc), then ts_utc (desc), then id (asc)
            boosted_rows.sort(
                key=lambda r: (-r["_boosted_score"], -datetime.fromisoformat(r["ts_utc"]).timestamp(), r["id"])
            )
            
            # Apply Top-K after boost
            has_more = len(boosted_rows) > top_k
            items = boosted_rows[:top_k]

            next_token = None
            if has_more and items:
                last = items[-1]
                next_token = self._encode_cursor(
                    last["importance_score"], last["ts_utc"], last["id"], scope_hash
                )

            response_items = []
            for row in items:
                item = {
                    "id": row["id"],
                    "ts_utc": row["ts_utc"],
                    "summary": row["summary"],
                    "category": row["category"],
                    "entry_type": row["entry_type"],
                    "workflow_phase": row.get("workflow_phase"),
                    "outcome": row["outcome"],
                    "importance_score": row["importance_score"],
                    "tags": json.loads(row.get("tags_json", "[]")),
                    # Include boost metadata for debugging (optional)
                    "_boost_applied": row.get("_boost_applied", 0.0),
                }
                # Include chain annotations when superseded entries are shown (Packet F §5.2)
                if include_superseded:
                    item["is_head"] = row.get("is_head", True)
                    item["superseded_by"] = row.get("superseded_by")
                    item["supersedes"] = row.get("supersedes")
                    item["chain_position"] = row.get("chain_position")
                response_items.append(item)

            return ToolResponse(
                success=True,
                data={
                    "items": response_items,
                    "more_count": max(0, len(boosted_rows) - top_k - 1) if has_more else 0,
                    "next_token": next_token,
                },
            )
        except Exception as e:
            logger.error(f"memory_search error: {e}")
            return ToolResponse(success=False, data={}, error=str(e))

    def memory_store(
        self,
        workspace_id: str,
        instance_id: str,
        category: str,
        entry_type: str,
        summary: str,
        session_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        reasoning: Optional[str] = None,
        outcome: str = "in_progress",
        importance_score: int = 6,
        tags: Optional[list[str]] = None,
        links: Optional[dict[str, Any]] = None,
    ) -> ToolResponse:
        """Store a manual work log entry."""
        try:
            store = self._get_store(workspace_id)

            redacted_details = None
            if details:
                redacted_details = self.redactor.redact_payload(details)

            linked_files = None
            if links and links.get("files"):
                linked_files = self.redactor.redact_linked_files(links["files"])

            now_utc = datetime.now(timezone.utc).isoformat()
            
            # Manual entry provenance (Packet D §4.3)
            source_event_id = f"manual-{uuid.uuid4()}"

            entry_id = store.insert_work_log_entry(
                workspace_id=workspace_id,
                instance_id=instance_id,
                category=category,
                entry_type=entry_type,
                summary=summary[:500],
                source_event_id=source_event_id,
                source_event_type="manual.memory_store",
                source_adapter="mcp-server",
                source_event_ts_utc=now_utc,
                promotion_rule="manual",
                session_id=session_id,
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

            return ToolResponse(success=True, data={"entry_id": entry_id, "created": True})
        except Exception as e:
            logger.error(f"memory_store error: {e}")
            return ToolResponse(success=False, data={}, error=str(e))

    def memory_recap(
        self,
        workspace_id: str,
        instance_id: str,
        scope: str = "session",
        session_id: Optional[str] = None,
        top_k: int = 3,
    ) -> ToolResponse:
        """Get a recap of recent work."""
        try:
            top_k = min(max(1, top_k), 10)
            store = self._get_store(workspace_id)

            time_range = {"session": None, "today": "today", "last_2_hours": "today"}.get(
                scope, "today"
            )

            entries = store.search_work_log(
                workspace_id=workspace_id,
                instance_id=instance_id,
                session_id=session_id if scope == "session" else None,
                time_range=time_range,
                limit=20,
            )

            if not entries:
                return ToolResponse(
                    success=True,
                    data={"trajectory": "No recent activity", "cards": [], "more_count": 0},
                )

            cards = []
            used_ids = set()

            # Card 1: Decision or top activity
            decision = next(
                (e for e in entries if e["entry_type"] == "decision" and e["id"] not in used_ids),
                None,
            )
            if decision:
                cards.append({"title": "Decision", "summary": decision["summary"], "entry_ids": [decision["id"]]})
                used_ids.add(decision["id"])
            elif entries:
                cards.append({"title": "Activity", "summary": entries[0]["summary"], "entry_ids": [entries[0]["id"]]})
                used_ids.add(entries[0]["id"])

            # Card 2: Blocker/Error
            blocker = next(
                (e for e in entries if e["entry_type"] in ("blocker", "error") and e["id"] not in used_ids),
                None,
            )
            if blocker and len(cards) < top_k:
                cards.append({
                    "title": "Blocker" if blocker["entry_type"] == "blocker" else "Error",
                    "summary": blocker["summary"],
                    "entry_ids": [blocker["id"]],
                })
                used_ids.add(blocker["id"])

            # Card 3: Next suggestion
            if len(cards) < top_k:
                if blocker:
                    cards.append({"title": "Next", "summary": f"Resolve: {blocker['summary'][:80]}", "entry_ids": [blocker["id"]]})
                elif entries:
                    cards.append({"title": "Next", "summary": f"Continue: {entries[0]['summary'][:80]}", "entry_ids": [entries[0]["id"]]})

            trajectory = f"Working on {', '.join(sorted(set(e['category'] for e in entries[:5])))} activities" if entries else "No recent activity"

            return ToolResponse(
                success=True,
                data={"trajectory": trajectory, "cards": cards[:top_k], "more_count": max(0, len(entries) - top_k)},
            )
        except Exception as e:
            logger.error(f"memory_recap error: {e}")
            return ToolResponse(success=False, data={}, error=str(e))

    def memory_mark_issue(
        self,
        workspace_id: str,
        instance_id: str,
        issue_entry_id: str,
        description: str,
        confidence: float = 0.7,
        evidence_window_min: int = 30,
        tags: Optional[list[str]] = None,
    ) -> ToolResponse:
        """Mark an entry as an issue source."""
        try:
            store = self._get_store(workspace_id)
            entry = store.get_entry_by_id(workspace_id, instance_id, issue_entry_id)
            if not entry:
                return ToolResponse(success=False, data={"issue_marked": False}, error="Entry not found")
            return ToolResponse(success=True, data={"issue_marked": True})
        except Exception as e:
            logger.error(f"memory_mark_issue error: {e}")
            return ToolResponse(success=False, data={}, error=str(e))

    def memory_link_resolution(
        self,
        workspace_id: str,
        instance_id: str,
        issue_entry_id: str,
        resolution_entry_id: str,
        confidence: float = 0.8,
        evidence_window_min: int = 30,
    ) -> ToolResponse:
        """Link an issue entry to its resolution."""
        try:
            store = self._get_store(workspace_id)
            issue = store.get_entry_by_id(workspace_id, instance_id, issue_entry_id)
            resolution = store.get_entry_by_id(workspace_id, instance_id, resolution_entry_id)
            if not issue or not resolution:
                return ToolResponse(success=False, data={"linked": False}, error="Entry not found")

            store.insert_issue_link(
                workspace_id=workspace_id,
                instance_id=instance_id,
                issue_entry_id=issue_entry_id,
                resolution_entry_id=resolution_entry_id,
                confidence=confidence,
                evidence_window_min=evidence_window_min,
            )
            return ToolResponse(success=True, data={"linked": True})
        except Exception as e:
            logger.error(f"memory_link_resolution error: {e}")
            return ToolResponse(success=False, data={}, error=str(e))

    def memory_replay_session(
        self,
        workspace_id: str,
        instance_id: str,
        session_id: str,
        top_k: int = 3,
        cursor: Optional[str] = None,
        mode: str = "replay_current",
    ) -> ToolResponse:
        """Replay session entries chronologically.
        
        Modes (Packet F §5.3):
        - replay_current (default): Only chain heads (corrected narrative)
        - replay_full: All entries including superseded, with annotations
        """
        try:
             store = self._get_store(workspace_id)
             top_k = min(max(1, top_k), 50)
             
             decoded_cursor = None
             if cursor:
                 try:
                     parts = base64.urlsafe_b64decode(cursor.encode()).decode().split("|")
                     if len(parts) == 2:
                         decoded_cursor = (parts[0], parts[1])
                 except Exception:
                     pass
            
             rows = store.replay_work_log(
                 workspace_id=workspace_id,
                 instance_id=instance_id,
                 session_id=session_id,
                 limit=top_k + 1,
                 cursor=decoded_cursor,
                 mode=mode,
             )
             
             has_more = len(rows) > top_k
             items = rows[:top_k]
             
             next_token = None
             if has_more and items:
                 last = items[-1]
                 raw_token = f"{last['source_event_ts_utc']}|{last['id']}"
                 next_token = base64.urlsafe_b64encode(raw_token.encode()).decode()

             response_items = []
             for row in items:
                 item = {
                     "id": row["id"],
                     "ts_utc": row["source_event_ts_utc"],
                     "category": row["category"],
                     "entry_type": row["entry_type"],
                     "summary": row["summary"],
                     "outcome": row["outcome"],
                     "importance_score": row["importance_score"],
                     "details": json.loads(row.get("details_json") or "{}"),
                 }
                 # Include chain annotations in replay_full mode (Packet F §5.3)
                 if mode == "replay_full":
                     item["is_head"] = row.get("is_head", True)
                     item["superseded_by"] = row.get("superseded_by")
                     item["supersedes"] = row.get("supersedes")
                     item["chain_position"] = row.get("chain_position")
                 response_items.append(item)

             return ToolResponse(
                 success=True,
                 data={
                     "items": response_items,
                     "more_count": 1 if has_more else 0,
                     "next_token": next_token,
                 },
             )
        except Exception as e:
            logger.error(f"memory_replay_session error: {e}")
            return ToolResponse(success=False, data={}, error=str(e))

    def memory_correct(
        self,
        workspace_id: str,
        instance_id: str,
        entry_id: str,
        correction_type: str,
        corrected_summary: Optional[str] = None,
        corrected_tags: Optional[list[str]] = None,
        corrected_category: Optional[str] = None,
        corrected_entry_type: Optional[str] = None,
        corrected_outcome: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> ToolResponse:
        """Supersede an existing work log entry with a corrected version.
        
        The original entry is preserved immutably; a new entry replaces it.
        Per Packet F §6.
        """
        try:
            store = self._get_store(workspace_id)
            new_id = store.insert_corrected_work_log_entry(
                workspace_id=workspace_id,
                instance_id=instance_id,
                supersedes_entry_id=entry_id,
                correction_type=correction_type,
                summary=corrected_summary or "Retraction" if correction_type == "retraction" else corrected_summary or "Correction",
                outcome=corrected_outcome,
                idempotency_key=idempotency_key,
            )
            return ToolResponse(
                success=True,
                data={
                    "corrected": True,
                    "new_entry_id": new_id,
                    "superseded_entry_id": entry_id,
                    "correction_type": correction_type,
                },
            )
        except ValueError as e:
            return ToolResponse(success=False, data={"corrected": False}, error=str(e))
        except Exception as e:
            logger.error(f"memory_correct error: {e}")
            return ToolResponse(success=False, data={}, error=str(e))

    # ─────────────────────────────────────────────────────────────────
    # Phase 2: Reflection + Trajectory
    # ─────────────────────────────────────────────────────────────────

    def memory_generate_reflection(
        self,
        workspace_id: str,
        instance_id: str,
        session_id: Optional[str] = None,
        window_hours: int = 2,
    ) -> ToolResponse:
        """Generate a reflection card from recent work.
        
        Uses ReflectionGenerator for deterministic reflection with:
        - Top-3 decisions
        - Top-3 blockers
        - Progress summary
        - Next steps
        """
        try:
            store = self._get_store(workspace_id)
            now_utc = datetime.now(timezone.utc)
            window_start = (now_utc - timedelta(hours=window_hours)).isoformat()
            window_end = now_utc.isoformat()
            
            # Generate reflection using ReflectionGenerator
            generator = ReflectionGenerator(store)
            reflection = generator.generate_reflection(
                workspace_id=workspace_id,
                instance_id=instance_id,
                session_id=session_id,
                window_start=window_start,
                window_end=window_end,
            )
            
            # If no data, return early
            if reflection["reflection_id"] is None:
                return ToolResponse(
                    success=True,
                    data={
                        "reflection_id": None,
                        "trajectory": reflection["trajectory_summary"],
                        "top_decisions": [],
                        "top_blockers": [],
                        "progress": {},
                        "next_suggested": [],
                    },
                )
            
            # Store reflection card
            store.insert_reflection_card(reflection)
            
            # Update trajectory state using TrajectoryManager
            trajectory_mgr = TrajectoryManager(store)
            # Get most recent entry to update trajectory
            recent_entries = store.search_work_log(
                workspace_id=workspace_id,
                instance_id=instance_id,
                session_id=session_id,
                limit=1,
            )
            if recent_entries:
                trajectory_mgr.update_trajectory(
                    workspace_id=workspace_id,
                    instance_id=instance_id,
                    entry=recent_entries[0],
                )
            
            # Format response to match existing API contract
            # Convert progress_summary format
            progress = reflection["progress_summary"]
            progress_formatted = {
                "total_entries": progress["total_entries"],
                "categories": progress["by_type"],
                "active_session": session_id or "multi",
            }
            
            # suggested_next is already in dict format from ReflectionGenerator
            # Just pass it through directly
            next_suggested = reflection["suggested_next"]
            
            return ToolResponse(
                success=True,
                data={
                    "reflection_id": reflection["reflection_id"],
                    "trajectory": reflection["trajectory_summary"],
                    "top_decisions": reflection["top_decisions"],
                    "top_blockers": reflection["top_blockers"],
                    "progress": progress_formatted,
                    "next_suggested": next_suggested,
                },
            )
        except Exception as e:
            logger.error(f"memory_generate_reflection error: {e}")
            return ToolResponse(success=False, data={}, error=str(e))

    def memory_reflections(
        self,
        workspace_id: str,
        instance_id: str,
        session_id: Optional[str] = None,
        limit: int = 3,
    ) -> ToolResponse:
        """Fetch recent reflection cards with staleness detection (Packet F §7.1)."""
        try:
            store = self._get_store(workspace_id)
            reflections = store.get_reflection_cards(
                workspace_id=workspace_id,
                instance_id=instance_id,
                session_id=session_id,
                limit=limit,
            )
            
            return ToolResponse(
                success=True,
                data={"reflections": reflections, "count": len(reflections)},
            )
        except Exception as e:
            logger.error(f"memory_reflections error: {e}")
            return ToolResponse(success=False, data={}, error=str(e))

    def memory_trajectory(
        self,
        workspace_id: str,
        instance_id: str,
    ) -> ToolResponse:
        """Get current trajectory state using TrajectoryManager."""
        try:
            store = self._get_store(workspace_id)
            trajectory_mgr = TrajectoryManager(store)
            
            trajectory = trajectory_mgr.get_trajectory(workspace_id, instance_id)
            
            if not trajectory:
                return ToolResponse(
                    success=True,
                    data={
                        "current_stream": "idle",
                        "current_goal": {},
                        "last_steps": [],
                        "boost_factor": 1.0,
                    },
                )
            
            # Calculate time-based boost factor (1.0-2.0 range, decays over 24 hours)
            updated_at = datetime.fromisoformat(trajectory["updated_at_utc"])
            now_utc = datetime.now(timezone.utc)
            hours_since = (now_utc - updated_at).total_seconds() / 3600
            boost_factor = max(1.0, min(2.0, 2.0 - (hours_since / 24)))
            
            return ToolResponse(
                success=True,
                data={
                    "current_stream": trajectory.get("current_stream", "idle"),
                    "current_goal": trajectory.get("current_goal", {}),
                    "last_steps": trajectory.get("last_steps", []),
                    "boost_factor": round(boost_factor, 2),
                },
            )
        except Exception as e:
            logger.error(f"memory_trajectory error: {e}")
            return ToolResponse(success=False, data={}, error=str(e))


# Global MCP server instance
mcp_server: Optional[DopeMemoryMCPServer] = None


# ═══════════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════════


class MemorySearchRequest(BaseModel):
    """Request for memory_search tool."""

    query: str = ""
    workspace_id: str = DEFAULT_WORKSPACE_ID
    instance_id: str = DEFAULT_INSTANCE_ID
    session_id: Optional[str] = None
    category: Optional[str] = None
    entry_type: Optional[str] = None
    workflow_phase: Optional[str] = None
    tags_any: Optional[list[str]] = None
    time_range: Optional[str] = None
    top_k: int = Field(default=3, ge=1, le=20)
    cursor: Optional[str] = None
    include_superseded: bool = False


class MemoryStoreRequest(BaseModel):
    """Request for memory_store tool."""

    workspace_id: str = DEFAULT_WORKSPACE_ID
    instance_id: str = DEFAULT_INSTANCE_ID
    category: str
    entry_type: str
    summary: str
    session_id: Optional[str] = None
    details: Optional[dict[str, Any]] = None
    reasoning: Optional[str] = None
    outcome: str = "in_progress"
    importance_score: int = Field(default=6, ge=1, le=10)
    tags: Optional[list[str]] = None
    links: Optional[dict[str, Any]] = None


class MemoryRecapRequest(BaseModel):
    """Request for memory_recap tool."""

    workspace_id: str = DEFAULT_WORKSPACE_ID
    instance_id: str = DEFAULT_INSTANCE_ID
    scope: str = Field(default="session", pattern=r"^(session|today|last_2_hours)$")
    session_id: Optional[str] = None
    top_k: int = Field(default=3, ge=1, le=10)


class MemoryMarkIssueRequest(BaseModel):
    """Request for memory_mark_issue tool."""

    workspace_id: str = DEFAULT_WORKSPACE_ID
    instance_id: str = DEFAULT_INSTANCE_ID
    issue_entry_id: str
    description: str
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    evidence_window_min: int = Field(default=30, ge=1, le=1440)
    tags: Optional[list[str]] = None


class MemoryLinkResolutionRequest(BaseModel):
    """Request for memory_link_resolution tool."""

    workspace_id: str = DEFAULT_WORKSPACE_ID
    instance_id: str = DEFAULT_INSTANCE_ID
    issue_entry_id: str
    resolution_entry_id: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    evidence_window_min: int = Field(default=30, ge=1, le=1440)


class MemoryReplaySessionRequest(BaseModel):
    """Request for memory_replay_session tool."""

    workspace_id: str = DEFAULT_WORKSPACE_ID
    instance_id: str = DEFAULT_INSTANCE_ID
    session_id: str
    top_k: int = Field(default=3, ge=1, le=20)
    cursor: Optional[str] = None
    mode: str = Field(default="replay_current", pattern=r"^(replay_current|replay_full)$")


class MemoryCorrectRequest(BaseModel):
    """Request for memory_correct tool (Packet F §6.5)."""

    workspace_id: str = DEFAULT_WORKSPACE_ID
    instance_id: str = DEFAULT_INSTANCE_ID
    entry_id: str
    correction_type: str = Field(pattern=r"^(summary|tags|category|outcome|retraction)$")
    corrected_summary: Optional[str] = None
    corrected_tags: Optional[list[str]] = None
    corrected_category: Optional[str] = None
    corrected_entry_type: Optional[str] = None
    corrected_outcome: Optional[str] = None
    idempotency_key: Optional[str] = None


class MemoryGenerateReflectionRequest(BaseModel):
    """Request for memory_generate_reflection tool."""

    workspace_id: str = DEFAULT_WORKSPACE_ID
    instance_id: str = DEFAULT_INSTANCE_ID
    session_id: Optional[str] = None
    window_hours: int = Field(default=2, ge=1, le=24)


class MemoryReflectionsRequest(BaseModel):
    """Request for memory_reflections tool."""

    workspace_id: str = DEFAULT_WORKSPACE_ID
    instance_id: str = DEFAULT_INSTANCE_ID
    session_id: Optional[str] = None
    limit: int = Field(default=3, ge=1, le=10)


class MemoryTrajectoryRequest(BaseModel):
    """Request for memory_trajectory tool."""

    workspace_id: str = DEFAULT_WORKSPACE_ID
    instance_id: str = DEFAULT_INSTANCE_ID


# EventBus consumer (optional, started if REDIS_URL is set)
ENABLE_EVENTBUS = os.getenv("ENABLE_EVENTBUS", "false").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL", "")

# Retention job configuration
ENABLE_RETENTION_JOB = os.getenv("ENABLE_RETENTION_JOB", "true").lower() == "true"
RETENTION_INTERVAL_SEC = int(os.getenv("RETENTION_INTERVAL_SEC", "3600"))  # Default: 1 hour

# Postgres mirror sync configuration
ENABLE_MIRROR_SYNC = os.getenv("ENABLE_MIRROR_SYNC", "false").lower() == "true"
POSTGRES_URL = os.getenv("POSTGRES_URL", os.getenv("DATABASE_URL", ""))

# Global EventBus consumer and tasks
eventbus_consumer = None
eventbus_task = None
retention_task = None
mirror_sync = None
mirror_sync_task = None


def _log_background_task_exception(task_name: str, task: asyncio.Task[Any]) -> None:
    """Log uncaught exceptions from background tasks."""
    if task.cancelled():
        return
    try:
        exc = task.exception()
    except asyncio.CancelledError:
        return
    if exc:
        logger.error(
            "❌ Background task '%s' crashed: %s",
            task_name,
            exc,
            exc_info=(type(exc), exc, exc.__traceback__),
        )


async def run_retention_job(mcp_server: DopeMemoryMCPServer, interval_sec: int = 3600):
    """Background task that periodically cleans up expired raw events."""
    logger.info(f"🧹 Retention job started (interval: {interval_sec}s)")
    while True:
        try:
            await asyncio.sleep(interval_sec)
            # Run cleanup for all known workspaces
            total_deleted = 0
            for workspace_id, store in mcp_server._stores.items():
                try:
                    deleted = store.cleanup_expired_raw_events()
                    if deleted > 0:
                        logger.info(f"🗑️  Cleaned up {deleted} expired raw events from {workspace_id}")
                        total_deleted += deleted
                except Exception as e:
                    logger.warning(f"⚠️  Retention job error for {workspace_id}: {e}")

            if total_deleted > 0:
                logger.info(f"🧹 Retention job: deleted {total_deleted} total expired events")
        except asyncio.CancelledError:
            logger.info("🧹 Retention job stopping")
            break
        except Exception as e:
            logger.error(f"❌ Retention job error: {e}")
            # Continue running despite errors


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global mcp_server, eventbus_consumer, eventbus_task, retention_task
    global mirror_sync, mirror_sync_task

    logger.info("Initializing Dope-Memory MCP server (canonical ledger mode)")

    mcp_server = DopeMemoryMCPServer(
        workspace_id=DEFAULT_WORKSPACE_ID,
        instance_id=DEFAULT_INSTANCE_ID,
    )

    # Start EventBus consumer if enabled
    if ENABLE_EVENTBUS and REDIS_URL:
        try:
            from eventbus_consumer import EventBusConsumer

            logger.info("Starting EventBus consumer for real-time ingestion")
            eventbus_consumer = EventBusConsumer(
                redis_url=REDIS_URL,
            )
            await eventbus_consumer.initialize()
            eventbus_task = asyncio.create_task(eventbus_consumer.start())
            logger.info("✅ EventBus consumer started")
        except Exception as e:
            logger.warning(f"⚠️  Failed to start EventBus consumer: {e}")
            eventbus_consumer = None
            eventbus_task = None

    # Start retention job if enabled
    if ENABLE_RETENTION_JOB:
        retention_task = asyncio.create_task(
            run_retention_job(mcp_server, RETENTION_INTERVAL_SEC)
        )
        logger.info("✅ Retention job started")

    mirror_ledger_path = "unresolved"
    try:
        mirror_ledger_path = str(resolve_canonical_ledger(DEFAULT_WORKSPACE_ID))
    except CanonicalLedgerError as e:
        mirror_ledger_path = f"error:{e}"
    logger.info(
        "Postgres mirror config: enabled=%s interval_sec=%s ledger=%s",
        ENABLE_MIRROR_SYNC,
        os.getenv("MIRROR_SYNC_INTERVAL_SEC", "60"),
        mirror_ledger_path,
    )

    # Start Postgres mirror sync if enabled
    if ENABLE_MIRROR_SYNC and POSTGRES_URL:
        try:
            from postgres_mirror_sync import PostgresMirrorSync

            logger.info("Starting Postgres mirror sync")
            mirror_sync = PostgresMirrorSync(
                postgres_url=POSTGRES_URL,
            )
            await mirror_sync.initialize()
            mirror_sync_task = asyncio.create_task(mirror_sync.start())
            mirror_sync_task.add_done_callback(
                lambda task: _log_background_task_exception("postgres-mirror-sync", task)
            )
            logger.info("✅ Postgres mirror sync started")
        except Exception as e:
            logger.warning(f"⚠️  Failed to start Postgres mirror sync: {e}")
            mirror_sync = None
            mirror_sync_task = None

    logger.info(f"Dope-Memory HTTP server started on port {PORT}")
    yield

    # Cleanup
    if mirror_sync_task:
        logger.info("Stopping Postgres mirror sync...")
        await mirror_sync.stop()
        mirror_sync_task.cancel()
        try:
            await mirror_sync_task
        except asyncio.CancelledError:
            pass
        logger.info("Postgres mirror sync stopped")

    if retention_task:
        logger.info("Stopping retention job...")
        retention_task.cancel()
        try:
            await retention_task
        except asyncio.CancelledError:
            pass
        logger.info("Retention job stopped")

    if eventbus_consumer:
        logger.info("Stopping EventBus consumer...")
        await eventbus_consumer.stop()
        if eventbus_task:
            eventbus_task.cancel()
            try:
                await eventbus_task
            except asyncio.CancelledError:
                pass
        logger.info("EventBus consumer stopped")

    logger.info("Dope-Memory HTTP server stopping")


# ═══════════════════════════════════════════════════════════════════════════════
# FastAPI Application
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="Dope-Memory",
    description="Temporal chronicle and working-context manager for Dopemux",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# Health & Info Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@app.get(HEALTH_CHECK_PATH)
async def health_check():
    """Health check endpoint per registry contract."""
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": SERVICE_NAME,
        "version": "1.0.0",
        "description": "Temporal chronicle and working-context manager",
        "spec_path": "docs/spec/dope-memory/v1/",
        "tools": [
            "memory_search",
            "memory_store",
            "memory_recap",
            "memory_mark_issue",
            "memory_link_resolution",
            "memory_replay_session",
            "memory_correct",
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MCP Tool Endpoints
# ═══════════════════════════════════════════════════════════════════════════════


@app.post("/tools/memory_search")
async def memory_search(request: MemorySearchRequest):
    """Search work log entries. Returns Top-3 (default) with pagination support."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")

    filters = {k: v for k, v in {
        "category": request.category,
        "entry_type": request.entry_type,
        "workflow_phase": request.workflow_phase,
        "tags_any": request.tags_any,
        "time_range": request.time_range,
    }.items() if v is not None}

    result = mcp_server.memory_search(
        query=request.query,
        workspace_id=request.workspace_id,
        instance_id=request.instance_id,
        session_id=request.session_id,
        filters=filters if filters else None,
        top_k=request.top_k,
        cursor=request.cursor,
        include_superseded=request.include_superseded,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@app.post("/tools/memory_store")
async def memory_store(request: MemoryStoreRequest):
    """Store a manual work log entry."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")

    result = mcp_server.memory_store(
        workspace_id=request.workspace_id,
        instance_id=request.instance_id,
        category=request.category,
        entry_type=request.entry_type,
        summary=request.summary,
        session_id=request.session_id,
        details=request.details,
        reasoning=request.reasoning,
        outcome=request.outcome,
        importance_score=request.importance_score,
        tags=request.tags,
        links=request.links,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@app.post("/tools/memory_recap")
async def memory_recap(request: MemoryRecapRequest):
    """Get a recap of recent work (session/today/last_2_hours)."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")

    result = mcp_server.memory_recap(
        workspace_id=request.workspace_id,
        instance_id=request.instance_id,
        scope=request.scope,
        session_id=request.session_id,
        top_k=request.top_k,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@app.post("/tools/memory_mark_issue")
async def memory_mark_issue(request: MemoryMarkIssueRequest):
    """Mark an entry as an issue source."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")

    result = mcp_server.memory_mark_issue(
        workspace_id=request.workspace_id,
        instance_id=request.instance_id,
        issue_entry_id=request.issue_entry_id,
        description=request.description,
        confidence=request.confidence,
        evidence_window_min=request.evidence_window_min,
        tags=request.tags,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@app.post("/tools/memory_link_resolution")
async def memory_link_resolution(request: MemoryLinkResolutionRequest):
    """Link an issue entry to its resolution."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")

    result = mcp_server.memory_link_resolution(
        workspace_id=request.workspace_id,
        instance_id=request.instance_id,
        issue_entry_id=request.issue_entry_id,
        resolution_entry_id=request.resolution_entry_id,
        confidence=request.confidence,
        evidence_window_min=request.evidence_window_min,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@app.post("/tools/memory_replay_session")
async def memory_replay_session(request: MemoryReplaySessionRequest):
    """Replay session entries chronologically."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")

    result = mcp_server.memory_replay_session(
        workspace_id=request.workspace_id,
        instance_id=request.instance_id,
        session_id=request.session_id,
        top_k=request.top_k,
        cursor=request.cursor,
        mode=request.mode,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@app.post("/tools/memory_correct")
async def memory_correct(request: MemoryCorrectRequest):
    """Supersede a work log entry with a corrected version (Packet F)."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")

    result = mcp_server.memory_correct(
        workspace_id=request.workspace_id,
        instance_id=request.instance_id,
        entry_id=request.entry_id,
        correction_type=request.correction_type,
        corrected_summary=request.corrected_summary,
        corrected_tags=request.corrected_tags,
        corrected_category=request.corrected_category,
        corrected_entry_type=request.corrected_entry_type,
        corrected_outcome=request.corrected_outcome,
        idempotency_key=request.idempotency_key,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@app.post("/tools/memory_generate_reflection")
async def memory_generate_reflection(request: MemoryGenerateReflectionRequest):
    """Generate a reflection card from recent work."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")

    result = mcp_server.memory_generate_reflection(
        workspace_id=request.workspace_id,
        instance_id=request.instance_id,
        session_id=request.session_id,
        window_hours=request.window_hours,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@app.post("/tools/memory_reflections")
async def memory_reflections(request: MemoryReflectionsRequest):
    """Fetch recent reflection cards."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")

    result = mcp_server.memory_reflections(
        workspace_id=request.workspace_id,
        instance_id=request.instance_id,
        session_id=request.session_id,
        limit=request.limit,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


@app.post("/tools/memory_trajectory")
async def memory_trajectory(request: MemoryTrajectoryRequest):
    """Get current trajectory state."""
    if not mcp_server:
        raise HTTPException(status_code=503, detail="MCP server not initialized")

    result = mcp_server.memory_trajectory(
        workspace_id=request.workspace_id,
        instance_id=request.instance_id,
    )

    if not result.success:
        raise HTTPException(status_code=400, detail=result.error)
    return result.data


# ═══════════════════════════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    uvicorn.run(
        "dope_memory_main:app",
        host="0.0.0.0",
        port=PORT,
        reload=os.getenv("ENVIRONMENT", "development") == "development",
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )
