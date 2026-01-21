"""
DDDPG SQLite Storage Backend
Local cache for fast reads, multi-instance support
"""

import aiosqlite
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from .interface import StorageBackend
from ..core.models import Decision, DecisionVisibility, WorkSession


class SQLiteBackend(StorageBackend):
    """
    SQLite storage backend - optimized for fast local reads
    
    Features:
    - FTS5 full-text search
    - Multi-instance isolation
    - Per-instance database files
    - TTL-based cache expiration
    """
    
    def __init__(
        self,
        db_path: Optional[str] = None,
        workspace_id: str = "/default",
        instance_id: str = "A"
    ):
        """
        Initialize SQLite backend
        
        Args:
            db_path: Path to SQLite database (if None, uses ~/.dddpg/cache/...)
            workspace_id: Workspace identifier
            instance_id: Instance identifier
        """
        self.workspace_id = workspace_id
        self.instance_id = instance_id
        
        if db_path:
            self.db_path = Path(db_path)
        else:
            # Default: ~/.dddpg/cache/{workspace_id}/{instance_id}/decisions.db
            cache_dir = Path.home() / ".dddpg" / "cache"
            # Sanitize workspace_id for filesystem
            workspace_safe = workspace_id.replace("/", "_").strip("_")
            self.db_path = cache_dir / workspace_safe / instance_id / "decisions.db"
        
        self.conn = None
        self._next_id = 1  # For auto-incrementing IDs
    
    async def connect(self) -> None:
        """Create/open SQLite database"""
        # Ensure directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connect
        self.conn = await aiosqlite.connect(str(self.db_path))
        
        # Enable foreign keys
        await self.conn.execute("PRAGMA foreign_keys = ON")
        
        # Initialize schema
        await self._init_schema()
        
        # Load next ID
        await self._load_next_id()
    
    async def disconnect(self) -> None:
        """Close database connection"""
        if self.conn:
            await self.conn.close()
            self.conn = None
    
    async def health_check(self) -> bool:
        """Check if database is accessible"""
        if not self.conn:
            return False
        try:
            await self.conn.execute("SELECT 1")
            return True
        except Exception as e:
            return False
    
            logger.error(f"Error: {e}")
    async def _init_schema(self):
        """Initialize database schema from migration file"""
        # Read schema SQL
        schema_path = Path(__file__).parent / "migrations" / "sqlite" / "001_init_schema.sql"
        schema_sql = schema_path.read_text()
        
        # Execute (may contain multiple statements)
        await self.conn.executescript(schema_sql)
        await self.conn.commit()
    
    async def _load_next_id(self):
        """Load next available ID from database"""
        cursor = await self.conn.execute("SELECT MAX(id) FROM decisions")
        row = await cursor.fetchone()
        if row and row[0]:
            self._next_id = row[0] + 1
        else:
            self._next_id = 1
    
    def _decision_to_row(self, decision: Decision) -> tuple:
        """Convert Decision model to database row"""
        return (
            decision.id,
            decision.summary,
            decision.rationale,
            decision.implementation_details,
            decision.workspace_id,
            decision.instance_id,
            decision.visibility.value if isinstance(decision.visibility, DecisionVisibility) else decision.visibility,
            decision.status.value if hasattr(decision.status, 'value') else decision.status,
            decision.decision_type.value if decision.decision_type and hasattr(decision.decision_type, 'value') else decision.decision_type,
            json.dumps(decision.tags) if decision.tags else "[]",
            decision.user_id,
            decision.cognitive_load,
            json.dumps(decision.agent_metadata) if decision.agent_metadata else "{}",
            json.dumps(decision.code_references) if decision.code_references else "[]",
            json.dumps(decision.related_decisions) if decision.related_decisions else "[]",
            decision.created_at.isoformat() if decision.created_at else datetime.utcnow().isoformat(),
            decision.updated_at.isoformat() if decision.updated_at else None,
        )
    
    def _row_to_decision(self, row: tuple) -> Decision:
        """Convert database row to Decision model"""
        return Decision(
            id=row[0],
            summary=row[1],
            rationale=row[2],
            implementation_details=row[3],
            workspace_id=row[4],
            instance_id=row[5],
            visibility=row[6],
            status=row[7],
            decision_type=row[8],
            tags=json.loads(row[9]) if row[9] else [],
            user_id=row[10],
            cognitive_load=row[11],
            agent_metadata=json.loads(row[12]) if row[12] else {},
            code_references=json.loads(row[13]) if row[13] else [],
            related_decisions=json.loads(row[14]) if row[14] else [],
            created_at=datetime.fromisoformat(row[15]) if row[15] else None,
            updated_at=datetime.fromisoformat(row[16]) if row[16] else None,
        )
    
    # ===== Decision CRUD =====
    
    async def create_decision(self, decision: Decision) -> Decision:
        """Create new decision"""
        # Assign ID if not set
        if decision.id is None:
            decision.id = self._next_id
            self._next_id += 1
        
        # Set timestamps
        if decision.created_at is None:
            decision.created_at = datetime.utcnow()
        
        # Insert
        query = """
        INSERT INTO decisions (
            id, summary, rationale, implementation_details,
            workspace_id, instance_id, visibility,
            status, decision_type, tags, user_id,
            cognitive_load, agent_metadata, code_references, related_decisions,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        await self.conn.execute(query, self._decision_to_row(decision))
        await self.conn.commit()
        
        return decision
    
    async def get_decision(self, decision_id: int) -> Optional[Decision]:
        """Get decision by ID"""
        query = "SELECT * FROM decisions WHERE id = ?"
        cursor = await self.conn.execute(query, (decision_id,))
        row = await cursor.fetchone()
        
        if row:
            return self._row_to_decision(row)
        return None
    
    async def list_decisions(
        self,
        workspace_id: str,
        instance_id: str,
        include_shared: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[Decision]:
        """List decisions for instance"""
        # Build visibility filter
        if include_shared:
            visibility_filter = "visibility IN ('shared', 'global') OR (visibility = 'private' AND instance_id = ?)"
            params = [workspace_id, instance_id, limit, offset]
        else:
            visibility_filter = "instance_id = ?"
            params = [workspace_id, instance_id, limit, offset]
        
        query = f"""
        SELECT * FROM decisions
        WHERE workspace_id = ?
          AND ({visibility_filter})
          AND status != 'archived'
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
        """
        
        cursor = await self.conn.execute(query, params)
        rows = await cursor.fetchall()
        
        return [self._row_to_decision(row) for row in rows]
    
    async def update_decision(self, decision: Decision) -> Decision:
        """Update existing decision"""
        decision.updated_at = datetime.utcnow()
        
        query = """
        UPDATE decisions SET
            summary = ?, rationale = ?, implementation_details = ?,
            workspace_id = ?, instance_id = ?, visibility = ?,
            status = ?, decision_type = ?, tags = ?, user_id = ?,
            cognitive_load = ?, agent_metadata = ?, code_references = ?,
            related_decisions = ?, updated_at = ?
        WHERE id = ?
        """
        
        row = self._decision_to_row(decision)
        params = row[1:16] + (decision.updated_at.isoformat(), decision.id)
        
        await self.conn.execute(query, params)
        await self.conn.commit()
        
        return decision
    
    async def delete_decision(self, decision_id: int) -> bool:
        """Delete decision (soft delete)"""
        query = "UPDATE decisions SET status = 'archived', updated_at = ? WHERE id = ?"
        
        cursor = await self.conn.execute(query, (datetime.utcnow().isoformat(), decision_id))
        await self.conn.commit()
        
        return cursor.rowcount > 0
    
    # ===== Search =====
    
    async def search_decisions(
        self,
        query: str,
        workspace_id: str,
        instance_id: str,
        limit: int = 10
    ) -> List[Decision]:
        """Full-text search using FTS5"""
        search_query = """
        SELECT d.* FROM decisions d
        JOIN decisions_fts fts ON d.id = fts.rowid
        WHERE decisions_fts MATCH ?
          AND d.workspace_id = ?
          AND (d.visibility IN ('shared', 'global') OR (d.visibility = 'private' AND d.instance_id = ?))
        ORDER BY rank
        LIMIT ?
        """
        
        cursor = await self.conn.execute(search_query, (query, workspace_id, instance_id, limit))
        rows = await cursor.fetchall()
        
        return [self._row_to_decision(row) for row in rows]
    
    # ===== Work Sessions =====
    
    async def create_session(self, session: WorkSession) -> WorkSession:
        """Create work session"""
        query = """
        INSERT INTO work_sessions (
            session_id, workspace_id, instance_id,
            started_at, last_activity, ended_at,
            focus_level, break_needed, context_preserved,
            current_file, current_decisions,
            total_decisions_created, total_decisions_viewed
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            session.session_id,
            session.workspace_id,
            session.instance_id,
            session.started_at.isoformat(),
            session.last_activity.isoformat(),
            session.ended_at.isoformat() if session.ended_at else None,
            session.focus_level,
            1 if session.break_needed else 0,
            1 if session.context_preserved else 0,
            session.current_file,
            json.dumps(session.current_decisions),
            session.total_decisions_created,
            session.total_decisions_viewed,
        )
        
        await self.conn.execute(query, params)
        await self.conn.commit()
        
        return session
    
    async def get_active_session(self, workspace_id: str, instance_id: str) -> Optional[WorkSession]:
        """Get active session for instance"""
        query = """
        SELECT * FROM work_sessions
        WHERE workspace_id = ? AND instance_id = ? AND ended_at IS NULL
        ORDER BY started_at DESC
        LIMIT 1
        """
        
        cursor = await self.conn.execute(query, (workspace_id, instance_id))
        row = await cursor.fetchone()
        
        if row:
            return WorkSession(
                session_id=row[0],
                workspace_id=row[1],
                instance_id=row[2],
                started_at=datetime.fromisoformat(row[3]),
                last_activity=datetime.fromisoformat(row[4]),
                ended_at=datetime.fromisoformat(row[5]) if row[5] else None,
                focus_level=row[6],
                break_needed=bool(row[7]),
                context_preserved=bool(row[8]),
                current_file=row[9],
                current_decisions=json.loads(row[10]) if row[10] else [],
                total_decisions_created=row[11],
                total_decisions_viewed=row[12],
            )
        return None


__all__ = ["SQLiteBackend"]
