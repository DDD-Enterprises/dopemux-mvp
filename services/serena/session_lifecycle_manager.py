"""
Session Lifecycle Manager - F002 Component 4

Manages complete session lifecycle: start, update, complete, cleanup.
Integrates with ConPort for persistent storage and handles all edge cases.

Part of F002: Multi-Session Support
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging
import json

from worktree_detector import WorktreeInfo
from session_id_generator import SessionIDGenerator

logger = logging.getLogger(__name__)


@dataclass
class SessionState:
    """
    Current state of an active session.

    Tracks session-specific data (focus, attention) separate from
    global workspace knowledge (decisions, progress).
    """
    session_id: str
    workspace_id: str
    worktree_path: Optional[str]
    branch: Optional[str]
    current_focus: Optional[str]
    session_start: datetime
    last_updated: datetime
    status: str  # active, completed, invalid_worktree
    content: Dict[str, Any]  # Full session content (JSONB)

    def to_dict(self) -> Dict:
        """Convert to dictionary for ConPort storage."""
        return {
            "session_id": self.session_id,
            "workspace_id": self.workspace_id,
            "worktree_path": self.worktree_path,
            "branch": self.branch,
            "current_focus": self.current_focus,
            "session_start": self.session_start.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "status": self.status,
            "content": self.content
        }


class SessionLifecycleManager:
    """
    Manage session lifecycle with ConPort integration.

    Responsibilities:
    - Start new sessions with worktree detection
    - Update session state (focus, content patches)
    - Complete sessions with duration tracking
    - Cleanup stale sessions (24h auto-expire)
    - Validate worktree paths (detect deleted worktrees)

    ADHD Benefit: Automatic context preservation across interruptions
    """

    def __init__(self, workspace_id: str):
        """
        Initialize session lifecycle manager.

        Args:
            workspace_id: Main repository path (from worktree detection)
        """
        self.workspace_id = workspace_id

    async def start_session(
        self,
        worktree_info: WorktreeInfo,
        initial_focus: Optional[str] = None,
        conport_client=None,
        transcript_path: Optional[str] = None
    ) -> SessionState:
        """
        Start a new session with ConPort tracking.

        Args:
            worktree_info: Detected worktree information
            initial_focus: Initial focus description
            conport_client: ConPort MCP client for storage
            transcript_path: Optional Claude Code transcript path

        Returns:
            SessionState for the new session

        ConPort Integration:
            Stores in active_context table with composite key
            (workspace_id, session_id)
        """
        try:
            # Generate unique session ID
            session_id = SessionIDGenerator.generate(transcript_path)

            # Create session state
            now = datetime.now(timezone.utc)
            session_state = SessionState(
                session_id=session_id,
                workspace_id=worktree_info.workspace_id,
                worktree_path=worktree_info.worktree_path,
                branch=worktree_info.branch,
                current_focus=initial_focus,
                session_start=now,
                last_updated=now,
                status="active",
                content={
                    "session_start": now.isoformat(),
                    "worktree_type": worktree_info.worktree_type,
                    "initial_focus": initial_focus
                }
            )

            # Store in ConPort
            if conport_client:
                await self._store_session_to_conport(session_state, conport_client)

            logger.info(
                f"Started session {session_id} "
                f"(worktree: {worktree_info.worktree_type}, branch: {worktree_info.branch})"
            )

            return session_state

        except Exception as e:
            logger.error(f"Failed to start session: {e}")
            raise

    async def update_session(
        self,
        session_id: str,
        focus: Optional[str] = None,
        content_patch: Optional[Dict] = None,
        conport_client=None
    ) -> bool:
        """
        Update existing session with new focus or content.

        Args:
            session_id: Session identifier
            focus: New focus description (optional)
            content_patch: Partial content update (merged with existing)
            conport_client: ConPort MCP client

        Returns:
            True if updated successfully

        Use Case: Periodic heartbeat updates (every 30s)
        """
        try:
            if not conport_client:
                logger.warning("No ConPort client - session update skipped")
                return False

            # Build update payload
            update_data = {
                "last_updated": datetime.now(timezone.utc).isoformat()
            }

            if focus:
                update_data["current_focus"] = focus

            # Merge content patch if provided
            if content_patch:
                # Get existing content, merge with patch
                existing_content = await self._get_session_content(
                    session_id, conport_client
                )
                merged_content = {**existing_content, **content_patch}
                update_data["content"] = merged_content

            # Update in ConPort
            await conport_client.update_active_context(
                workspace_id=self.workspace_id,
                session_id=session_id,
                patch_content=update_data
            )

            logger.debug(f"Updated session {session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update session {session_id}: {e}")
            return False

    async def complete_session(
        self,
        session_id: str,
        summary: Optional[str] = None,
        conport_client=None
    ) -> bool:
        """
        Mark session as completed and archive to session_history.

        Args:
            session_id: Session to complete
            summary: Optional completion summary
            conport_client: ConPort MCP client

        Returns:
            True if completed successfully

        Actions:
            1. Calculate session duration
            2. Update status to 'completed'
            3. Archive to session_history table
            4. Remove from active_context
        """
        try:
            if not conport_client:
                logger.warning("No ConPort client - session completion skipped")
                return False

            # Get session data for archiving
            session_data = await self._get_session_data(session_id, conport_client)

            if not session_data:
                logger.warning(f"Session {session_id} not found")
                return False

            # Calculate duration
            now = datetime.now(timezone.utc)
            start_time = datetime.fromisoformat(
                session_data.get('session_start', now.isoformat()).replace('Z', '+00:00')
            )
            duration_minutes = int((now - start_time).total_seconds() / 60)

            # Archive to session_history
            history_entry = {
                "workspace_id": self.workspace_id,
                "session_id": session_id,
                "worktree_path": session_data.get('worktree_path'),
                "branch": session_data.get('branch'),
                "content": {
                    **session_data.get('content', {}),
                    "completion_summary": summary,
                    "completed_at": now.isoformat()
                },
                "created_at": session_data.get('session_start'),
                "completed_at": now.isoformat(),
                "duration_minutes": duration_minutes
            }

            # Store in session_history (via custom_data until table exists)
            await conport_client.log_custom_data(
                workspace_id=self.workspace_id,
                category="session_history",
                key=session_id,
                value=history_entry
            )

            # Remove from active_context
            await self._remove_from_active_context(session_id, conport_client)

            logger.info(f"Completed session {session_id} ({duration_minutes} min)")
            return True

        except Exception as e:
            logger.error(f"Failed to complete session {session_id}: {e}")
            return False

    async def cleanup_stale_sessions(
        self,
        max_age_hours: int = 24,
        conport_client=None
    ) -> Dict[str, Any]:
        """
        Cleanup sessions inactive for > max_age_hours.

        Args:
            max_age_hours: Maximum hours of inactivity before cleanup
            conport_client: ConPort MCP client

        Returns:
            {
                "cleaned_up": int,
                "session_ids": List[str],
                "reason": "stale_sessions"
            }

        ADHD Benefit: Prevents dashboard clutter from forgotten sessions
        """
        try:
            if not conport_client:
                logger.warning("No ConPort client - cleanup skipped")
                return {"cleaned_up": 0, "session_ids": [], "reason": "no_client"}

            # Query stale sessions
            stale_sessions = await self._find_stale_sessions(
                max_age_hours, conport_client
            )

            cleaned_up = []
            for session in stale_sessions:
                session_id = session['session_id']

                # Mark as completed (auto-cleaned)
                success = await self.complete_session(
                    session_id,
                    summary=f"Auto-cleaned after {max_age_hours}h inactivity",
                    conport_client=conport_client
                )

                if success:
                    cleaned_up.append(session_id)

            logger.info(f"Cleaned up {len(cleaned_up)} stale sessions")

            return {
                "cleaned_up": len(cleaned_up),
                "session_ids": cleaned_up,
                "reason": "stale_sessions"
            }

        except Exception as e:
            logger.error(f"Stale session cleanup failed: {e}")
            return {"cleaned_up": 0, "session_ids": [], "error": str(e)}

    async def validate_worktree_paths(
        self,
        conport_client=None
    ) -> Dict[str, Any]:
        """
        Validate worktree paths for all active sessions.

        Detects deleted worktrees and marks sessions as invalid.

        Returns:
            {
                "validated": int,
                "invalid": int,
                "invalid_sessions": [
                    {"session_id": str, "worktree_path": str}
                ]
            }

        Edge Case 3: Deleted Worktrees
        """
        try:
            if not conport_client:
                return {"validated": 0, "invalid": 0, "invalid_sessions": []}

            # Get all active sessions
            sessions = await self._get_all_active_sessions(conport_client)

            validated = 0
            invalid_list = []

            for session in sessions:
                worktree_path = session.get('worktree_path')

                # Skip main worktree or no path
                if not worktree_path:
                    validated += 1
                    continue

                # Check if path exists
                if not Path(worktree_path).exists():
                    # Mark as invalid
                    await self._mark_session_invalid(
                        session['session_id'],
                        "worktree_deleted",
                        conport_client
                    )

                    invalid_list.append({
                        "session_id": session['session_id'],
                        "worktree_path": worktree_path
                    })
                else:
                    validated += 1

            if invalid_list:
                logger.warning(f"Found {len(invalid_list)} sessions with deleted worktrees")

            return {
                "validated": validated,
                "invalid": len(invalid_list),
                "invalid_sessions": invalid_list
            }

        except Exception as e:
            logger.error(f"Worktree validation failed: {e}")
            return {"validated": 0, "invalid": 0, "error": str(e)}

    # Private helper methods

    async def _store_session_to_conport(
        self,
        session_state: SessionState,
        conport_client
    ):
        """Store session to ConPort active_context."""
        try:
            # Store session with session_id parameter
            await conport_client.update_active_context(
                workspace_id=session_state.workspace_id,
                session_id=session_state.session_id,
                content=session_state.to_dict()
            )

        except Exception as e:
            logger.error(f"Failed to store session to ConPort: {e}")
            raise

    async def _get_session_content(self, session_id: str, conport_client) -> Dict:
        """Get session content from ConPort."""
        try:
            # Query active_context for this session
            result = await conport_client.get_active_context(
                workspace_id=self.workspace_id
            )

            # Parse result to find session content
            if isinstance(result, dict) and result.get('session_id') == session_id:
                return result.get('content', {})

            return {}

        except Exception as e:
            logger.debug(f"Could not get session content: {e}")
            return {}

    async def _get_session_data(self, session_id: str, conport_client) -> Optional[Dict]:
        """Get full session data from ConPort."""
        try:
            result = await conport_client.get_active_context(
                workspace_id=self.workspace_id
            )

            if isinstance(result, dict) and result.get('session_id') == session_id:
                return result

            return None

        except Exception as e:
            logger.error(f"Failed to get session data: {e}")
            return None

    async def _remove_from_active_context(self, session_id: str, conport_client):
        """Remove session from active_context (called after archiving)."""
        try:
            # Get current active context
            current_context = await conport_client.get_active_context(self.workspace_id)

            # Remove this session from active sessions
            if "active_context" in current_context and "active_sessions" in current_context["active_context"]:
                active_sessions = current_context["active_context"]["active_sessions"]
                if isinstance(active_sessions, list):
                    # Remove session by ID
                    updated_sessions = [s for s in active_sessions if s.get("session_id") != session_id]
                    current_context["active_context"]["active_sessions"] = updated_sessions

                    # Update the active context
                    await conport_client.update_active_context(self.workspace_id, current_context)
                    logger.info(f"Removed session {session_id} from active context")
                else:
                    logger.warning("Active sessions is not a list")
            else:
                logger.warning("No active context or active sessions found")

        except Exception as e:
            logger.error(f"Failed to remove session {session_id} from active context: {e}")

    async def _find_stale_sessions(
        self,
        max_age_hours: int,
        conport_client
    ) -> List[Dict]:
        """Find sessions inactive for > max_age_hours."""
        try:
            # Get active context to find all sessions
            context = await conport_client.get_active_context(self.workspace_id)

            if "active_context" not in context or "active_sessions" not in context["active_context"]:
                return []

            active_sessions = context["active_context"]["active_sessions"]
            if not isinstance(active_sessions, list):
                return []

            stale_sessions = []
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

            for session in active_sessions:
                if isinstance(session, dict) and "last_updated" in session:
                    try:
                        # Parse the timestamp
                        if isinstance(session["last_updated"], str):
                            last_updated = datetime.fromisoformat(session["last_updated"].replace('Z', '+00:00'))
                        else:
                            last_updated = session["last_updated"]

                        if last_updated < cutoff_time:
                            stale_sessions.append(session)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid timestamp format for session {session.get('session_id', 'unknown')}: {e}")
                        # Consider sessions with invalid timestamps as stale
                        stale_sessions.append(session)

            logger.info(f"Found {len(stale_sessions)} stale sessions (inactive > {max_age_hours}h)")
            return stale_sessions

        except Exception as e:
            logger.error(f"Failed to find stale sessions: {e}")
            return []

    async def _get_all_active_sessions(self, conport_client) -> List[Dict]:
        """Get all active sessions for workspace."""
        try:
            # Get active context which contains session information
            context = await conport_client.get_active_context(self.workspace_id)

            if "active_context" not in context or "active_sessions" not in context["active_context"]:
                return []

            active_sessions = context["active_context"]["active_sessions"]
            if isinstance(active_sessions, list):
                return active_sessions
            else:
                logger.warning("Active sessions in context is not a list")
                return []

        except Exception as e:
            logger.error(f"Failed to get all active sessions: {e}")
            return []

    async def _mark_session_invalid(
        self,
        session_id: str,
        reason: str,
        conport_client
    ):
        """Mark session as invalid (deleted worktree, etc.)."""
        try:
            await conport_client.update_active_context(
                workspace_id=self.workspace_id,
                content={
                    "session_id": session_id,
                    "status": "invalid_worktree",
                    "invalid_reason": reason,
                    "invalidated_at": datetime.now(timezone.utc).isoformat()
                }
            )

        except Exception as e:
            logger.error(f"Failed to mark session invalid: {e}")

    def calculate_session_duration(
        self,
        session_start: datetime,
        session_end: Optional[datetime] = None
    ) -> int:
        """
        Calculate session duration in minutes.

        Args:
            session_start: Session start timestamp
            session_end: Session end timestamp (defaults to now)

        Returns:
            Duration in minutes
        """
        if not session_end:
            session_end = datetime.now(timezone.utc)

        # Ensure timezone-aware
        if session_start.tzinfo is None:
            session_start = session_start.replace(tzinfo=timezone.utc)
        if session_end.tzinfo is None:
            session_end = session_end.replace(tzinfo=timezone.utc)

        duration = session_end - session_start
        return int(duration.total_seconds() / 60)

    async def get_session_statistics(
        self,
        conport_client=None
    ) -> Dict[str, Any]:
        """
        Get statistics for session management.

        Returns:
            {
                "active_sessions": int,
                "worktrees_active": int,
                "oldest_session_age_minutes": int,
                "needs_cleanup": bool
            }

        Use Case: Health monitoring, dashboard summary
        """
        try:
            if not conport_client:
                return {
                    "active_sessions": 0,
                    "worktrees_active": 0,
                    "oldest_session_age_minutes": 0,
                    "needs_cleanup": False
                }

            sessions = await self._get_all_active_sessions(conport_client)

            # Calculate stats
            unique_worktrees = set(
                s.get('worktree_path') or "main"
                for s in sessions
            )

            # Find oldest session
            oldest_age = 0
            if sessions:
                now = datetime.now(timezone.utc)
                for session in sessions:
                    last_updated = session.get('last_updated')
                    if last_updated:
                        try:
                            updated_dt = datetime.fromisoformat(
                                last_updated.replace('Z', '+00:00')
                            )
                            age_minutes = (now - updated_dt).total_seconds() / 60
                            if age_minutes > oldest_age:
                                oldest_age = age_minutes
                        except Exception as e:
                            logger.error(f"Error: {e}")
            needs_cleanup = oldest_age > (24 * 60)  # > 24 hours

            return {
                "active_sessions": len(sessions),
                "worktrees_active": len(unique_worktrees),
                "oldest_session_age_minutes": int(oldest_age),
                "needs_cleanup": needs_cleanup
            }

        except Exception as e:
            logger.error(f"Failed to get session statistics: {e}")
            return {
                "active_sessions": 0,
                "error": str(e)
            }
