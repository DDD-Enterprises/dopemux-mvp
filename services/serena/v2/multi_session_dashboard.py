"""
Multi-Session Dashboard - F002 Component 3

Formats startup display showing all active sessions across worktrees.
Groups sessions by worktree for ADHD-optimized visual clarity.

Part of F002: Multi-Session Support
"""

from typing import List, Dict, Optional
from datetime import datetime, timezone
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class MultiSessionDashboard:
    """
    Format multi-session dashboard for startup display.

    Shows all active work across sessions and worktrees.

    ADHD Benefits:
    - Visual grouping by worktree (mental clarity)
    - Time anchors ([30m ago]) for memory aids
    - Max 10 sessions shown (prevents overwhelm)
    - Clear summary with actionable suggestions
    """

    def __init__(self, max_sessions: int = 10):
        """
        Initialize dashboard formatter.

        Args:
            max_sessions: Maximum sessions to display (ADHD limit)
        """
        self.max_sessions = max_sessions

    def format_dashboard(self, sessions: List[Dict]) -> str:
        """
        Format startup dashboard showing all active sessions.

        Args:
            sessions: List of session dicts from ConPort query
                Each dict: {
                    session_id, worktree_path, branch, focus,
                    minutes_ago, status
                }

        Returns:
            Formatted dashboard string

        Example Output:
            ```
            🔄 ACTIVE SESSIONS
            ─────────────────────────────────────────────

            Main worktree (main):
               • [active] Code review
               • [active] Documentation ⚠️ multiple

            Worktree: feature-auth (feature/auth):
               • [30m ago] JWT implementation

            Total: 3 active session(s), 1 worktree(s)
            ```
        """
        if not sessions:
            return self._no_sessions_message()

        # Limit sessions for ADHD (max 10)
        if len(sessions) > self.max_sessions:
            sessions = sessions[:self.max_sessions]
            truncated = True
        else:
            truncated = False

        lines = ["🔄 ACTIVE SESSIONS"]
        lines.append("─" * 45)
        lines.append("")

        # Group sessions by worktree
        by_worktree = self._group_by_worktree(sessions)

        # Display each worktree group
        for worktree, sess_list in by_worktree.items():
            worktree_lines = self._format_worktree_group(worktree, sess_list)
            lines.extend(worktree_lines)
            lines.append("")

        # Summary
        worktree_count = len(by_worktree)
        secondary_worktrees = worktree_count - 1 if "main" in by_worktree else worktree_count

        summary = f"Total: {len(sessions)} active session(s), {secondary_worktrees} worktree(s)"
        if truncated:
            summary += f" (showing first {self.max_sessions})"

        lines.append(summary)

        # ADHD guidance
        if len(sessions) > 1:
            lines.append("")
            lines.append("💡 Continue current session or switch worktree?")
        elif secondary_worktrees > 0:
            lines.append("")
            lines.append("💡 Work in progress across multiple worktrees")

        return "\n".join(lines)

    def _group_by_worktree(self, sessions: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Group sessions by worktree path.

        Returns:
            {worktree_path: [session1, session2, ...]}
        """
        by_worktree = {}

        for session in sessions:
            worktree_path = session.get('worktree_path')

            # Key: "main" for main worktree/None, actual path for secondary
            if not worktree_path or worktree_path == session.get('workspace_id'):
                key = "main"
            else:
                key = worktree_path

            if key not in by_worktree:
                by_worktree[key] = []

            by_worktree[key].append(session)

        return by_worktree

    def _format_worktree_group(self, worktree_key: str, sessions: List[Dict]) -> List[str]:
        """Format a single worktree group."""
        lines = []

        # Extract branch from first session
        branch = sessions[0].get('branch') or "unknown"

        # Header: "Main worktree" or "Worktree: feature-auth"
        if worktree_key == "main":
            lines.append(f"Main worktree ({branch}):")
        else:
            worktree_name = Path(worktree_key).name
            lines.append(f"Worktree: {worktree_name} ({branch}):")

        # Show each session in this worktree
        for i, session in enumerate(sessions):
            focus = session.get('focus') or session.get('current_focus') or "No focus set"
            minutes_ago = session.get('minutes_ago', 0)
            time_label = self._format_time_ago(minutes_ago)

            # Truncate long focus descriptions
            if len(focus) > 50:
                focus = focus[:47] + "..."

            # Warning if multiple sessions in same worktree
            if len(sessions) > 1 and i == 1:
                lines.append(f"   • [{time_label}] {focus} ⚠️ multiple sessions")
            else:
                lines.append(f"   • [{time_label}] {focus}")

        return lines

    def _format_time_ago(self, minutes: float) -> str:
        """
        Format time since last activity.

        Args:
            minutes: Minutes since last activity

        Returns:
            Human-readable time label

        Examples:
            - "active" (< 5 min)
            - "10m ago"
            - "2h ago"
            - "3d ago"
        """
        if minutes < 5:
            return "active"
        elif minutes < 60:
            return f"{int(minutes)}m ago"
        elif minutes < 1440:  # < 24 hours
            hours = int(minutes / 60)
            return f"{hours}h ago"
        else:
            days = int(minutes / 1440)
            return f"{days}d ago"

    def _no_sessions_message(self) -> str:
        """Message when no active sessions found."""
        return "✨ No active sessions - starting fresh!"

    def format_session_detail(self, session: Dict) -> str:
        """
        Format detailed view of a single session.

        Args:
            session: Session dict with full data

        Returns:
            Detailed formatted string

        Use Case: User requests details on specific session
        """
        lines = ["📋 SESSION DETAILS"]
        lines.append("─" * 45)
        lines.append("")

        # Basic info
        lines.append(f"Session ID: {session.get('session_id', 'Unknown')}")
        lines.append(f"Branch: {session.get('branch', 'Unknown')}")

        # Worktree info
        worktree = session.get('worktree_path')
        if worktree:
            worktree_name = Path(worktree).name
            lines.append(f"Worktree: {worktree_name}")
            lines.append(f"Path: {worktree}")
        else:
            lines.append("Worktree: Main repository")

        lines.append("")

        # Current focus
        focus = session.get('focus') or session.get('current_focus') or "No focus set"
        lines.append(f"Current Focus:")
        lines.append(f"  {focus}")
        lines.append("")

        # Timing
        minutes_ago = session.get('minutes_ago', 0)
        time_ago = self._format_time_ago(minutes_ago)
        lines.append(f"Last Active: {time_ago}")

        # Session content (if available)
        content = session.get('content', {})
        if isinstance(content, dict):
            if 'session_start' in content:
                lines.append(f"Started: {content['session_start']}")

            if 'mode' in content:
                lines.append(f"Mode: {content['mode']}")

        return "\n".join(lines)

    def format_worktree_summary(self, workspace_id: str, all_worktrees: List[Dict]) -> str:
        """
        Format summary of all worktrees (active and inactive).

        Args:
            workspace_id: Main repository path
            all_worktrees: List from WorktreeDetector.get_all_worktrees()

        Returns:
            Formatted worktree summary

        Example:
            ```
            📂 WORKTREES FOR: dopemux-mvp
            ─────────────────────────────────────────────

            1. [current] main → /Users/hue/code/dopemux-mvp
            2. feature/auth → /Users/hue/code/dopemux-mvp-feature-auth
            3. bugfix/login → /Users/hue/code/dopemux-mvp-bugfix-login

            Total: 3 worktrees
            ```
        """
        if not all_worktrees:
            return "No worktrees configured"

        workspace_name = Path(workspace_id).name
        lines = [f"📂 WORKTREES FOR: {workspace_name}"]
        lines.append("─" * 45)
        lines.append("")

        for i, worktree in enumerate(all_worktrees, 1):
            path = worktree['path']
            branch = worktree['branch'] or "detached"
            is_current = worktree['is_current']

            current_marker = "[current] " if is_current else ""
            lines.append(f"{i}. {current_marker}{branch} → {path}")

        lines.append("")
        lines.append(f"Total: {len(all_worktrees)} worktree(s)")

        return "\n".join(lines)
