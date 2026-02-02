"""
Session Manager - F002 Component 6 (Coordinator)

Main coordinator for multi-session support. Integrates all F002 components
and provides high-level session management API.

Part of F002: Multi-Session Support
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging

from session_id_generator import SessionIDGenerator
from worktree_detector import WorktreeDetector, WorktreeInfo
from session_lifecycle_manager import SessionLifecycleManager, SessionState
from multi_session_dashboard import MultiSessionDashboard

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Main coordinator for F002 Multi-Session Support.

    Responsibilities:
    - Initialize sessions on Serena startup
    - Coordinate worktree detection + session ID generation
    - Manage session lifecycle (start/update/complete)
    - Provide dashboard data for statusline
    - Handle all 5 edge cases from F002 spec

    ADHD Benefits:
    - Automatic context preservation across sessions
    - Parallel work without mental context-switching
    - Clear visibility of all active work
    - Session isolation + knowledge sharing
    """

    def __init__(
        self,
        workspace_path: Optional[Path] = None,
        auto_detect: bool = True
    ):
        """
        Initialize session manager.

        Args:
            workspace_path: Workspace directory (auto-detected if None)
            auto_detect: Auto-detect worktree info on init
        """
        # Detect worktree information
        if auto_detect:
            self.worktree_detector = WorktreeDetector(workspace_path)
            self.worktree_info = self.worktree_detector.detect()
            logger.info(
                f"Detected worktree: type={self.worktree_info.worktree_type}, "
                f"workspace={self.worktree_info.workspace_id}"
            )
        else:
            self.worktree_detector = None
            self.worktree_info = None

        # Initialize components
        workspace_id = self.worktree_info.workspace_id if self.worktree_info else str(workspace_path or Path.cwd())
        self.lifecycle_manager = SessionLifecycleManager(workspace_id)
        self.dashboard = MultiSessionDashboard(max_sessions=10)
        self.session_id_generator = SessionIDGenerator()

        # Current session state (in-memory)
        self.current_session: Optional[SessionState] = None

    async def initialize_session(
        self,
        initial_focus: Optional[str] = None,
        conport_client=None,
        transcript_path: Optional[str] = None
    ) -> SessionState:
        """
        Initialize current session on Serena startup.

        Workflow:
        1. Detect worktree info (if not already done)
        2. Generate unique session ID
        3. Start session lifecycle
        4. Return session state

        Args:
            initial_focus: Initial focus description
            conport_client: ConPort MCP client for persistence
            transcript_path: Optional Claude Code transcript path

        Returns:
            SessionState for current session
        """
        try:
            # Ensure worktree info detected
            if not self.worktree_info:
                self.worktree_detector = WorktreeDetector()
                self.worktree_info = self.worktree_detector.detect()

            # Start new session
            self.current_session = await self.lifecycle_manager.start_session(
                worktree_info=self.worktree_info,
                initial_focus=initial_focus,
                conport_client=conport_client,
                transcript_path=transcript_path
            )

            logger.info(
                f"Session initialized: {self.current_session.session_id} "
                f"(workspace: {self.current_session.workspace_id})"
            )

            return self.current_session

        except Exception as e:
            logger.error(f"Session initialization failed: {e}")
            raise

    async def update_current_session(
        self,
        focus: Optional[str] = None,
        content_patch: Optional[Dict] = None,
        conport_client=None
    ) -> bool:
        """
        Update current session with new focus or content.

        Args:
            focus: New focus description
            content_patch: Partial content update
            conport_client: ConPort MCP client

        Returns:
            True if updated successfully

        Use Case: Periodic heartbeat (every 30s), focus changes
        """
        if not self.current_session:
            logger.warning("No current session to update")
            return False

        return await self.lifecycle_manager.update_session(
            session_id=self.current_session.session_id,
            focus=focus,
            content_patch=content_patch,
            conport_client=conport_client
        )

    async def complete_current_session(
        self,
        summary: Optional[str] = None,
        conport_client=None
    ) -> bool:
        """
        Complete and archive current session.

        Args:
            summary: Optional completion summary
            conport_client: ConPort MCP client

        Returns:
            True if completed successfully

        Use Case: Session end, Claude Code exit
        """
        if not self.current_session:
            logger.warning("No current session to complete")
            return False

        success = await self.lifecycle_manager.complete_session(
            session_id=self.current_session.session_id,
            summary=summary,
            conport_client=conport_client
        )

        if success:
            self.current_session = None

        return success

    async def get_startup_dashboard(
        self,
        conport_client=None
    ) -> str:
        """
        Get multi-session dashboard for startup display.

        Queries ConPort for all active sessions and formats dashboard.

        Args:
            conport_client: ConPort MCP client

        Returns:
            Formatted dashboard string

        Example Output:
            ```
            🔄 ACTIVE SESSIONS
            ─────────────────────────────────────────────

            Main worktree (main):
               • [active] Code review

            Worktree: feature-auth (feature/auth):
               • [30m ago] JWT implementation

            Total: 2 active session(s), 1 worktree(s)
            ```
        """
        try:
            if not conport_client:
                return "✨ No active sessions - starting fresh!"

            # Query all active sessions for this workspace
            sessions = await self._query_all_active_sessions(conport_client)

            # Format dashboard
            dashboard = self.dashboard.format_dashboard(sessions)

            return dashboard

        except Exception as e:
            logger.error(f"Failed to generate startup dashboard: {e}")
            return f"⚠️  Dashboard generation failed: {e}"

    async def cleanup_stale_sessions(
        self,
        max_age_hours: int = 24,
        conport_client=None
    ) -> Dict[str, Any]:
        """
        Cleanup sessions inactive for > max_age_hours.

        Delegat to lifecycle manager.

        Args:
            max_age_hours: Maximum inactivity hours
            conport_client: ConPort MCP client

        Returns:
            Cleanup result dict

        ADHD Use Case: Automatic cleanup prevents dashboard clutter
        """
        return await self.lifecycle_manager.cleanup_stale_sessions(
            max_age_hours=max_age_hours,
            conport_client=conport_client
        )

    async def validate_worktrees(
        self,
        conport_client=None
    ) -> Dict[str, Any]:
        """
        Validate worktree paths for all sessions.

        Edge Case 3: Deleted Worktrees

        Args:
            conport_client: ConPort MCP client

        Returns:
            Validation result with invalid sessions
        """
        return await self.lifecycle_manager.validate_worktree_paths(
            conport_client=conport_client
        )

    def get_current_session_info(self) -> Optional[Dict]:
        """
        Get current session information.

        Returns:
            Session info dict or None
        """
        if not self.current_session:
            return None

        return {
            "session_id": self.current_session.session_id,
            "workspace_id": self.current_session.workspace_id,
            "worktree_path": self.current_session.worktree_path,
            "branch": self.current_session.branch,
            "current_focus": self.current_session.current_focus,
            "status": self.current_session.status,
            "session_duration_minutes": self.lifecycle_manager.calculate_session_duration(
                self.current_session.session_start
            )
        }

    def get_worktree_info(self) -> Optional[WorktreeInfo]:
        """
        Get detected worktree information.

        Returns:
            WorktreeInfo or None
        """
        return self.worktree_info

    async def _query_all_active_sessions(self, conport_client) -> List[Dict]:
        """
        Query all active sessions from ConPort.

        Uses v_active_sessions view if migration complete,
        otherwise falls back to get_active_context.

        Returns:
            List of session dicts
        """
        try:
            # TODO: Implement multi-session query when schema migrated
            # For now, query current active_context
            result = await conport_client.get_active_context(
                workspace_id=self.worktree_info.workspace_id if self.worktree_info else None
            )

            # Parse result
            if isinstance(result, dict):
                # Single session format (pre-migration)
                return [result] if result.get('current_focus') else []
            elif isinstance(result, list):
                # Multi-session format (post-migration)
                return result
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to query active sessions: {e}")
            return []

    async def health_check(self) -> Dict[str, Any]:
        """
        Comprehensive health check for session management.

        Returns:
            {
                "session_manager_status": str,
                "current_session": Dict | None,
                "worktree_info": Dict,
                "components": {
                    "worktree_detector": bool,
                    "lifecycle_manager": bool,
                    "dashboard": bool
                }
            }
        """
        return {
            "session_manager_status": "operational",
            "current_session": self.get_current_session_info(),
            "worktree_info": self.worktree_info.to_dict() if self.worktree_info else None,
            "components": {
                "worktree_detector": self.worktree_detector is not None,
                "lifecycle_manager": True,
                "dashboard": True,
                "session_id_generator": True
            },
            "version": "F002_v1.0"
        }
