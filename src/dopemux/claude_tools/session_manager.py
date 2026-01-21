"""
Session Manager for Claude-Code-Tools Integration

Provides unified session search and resume functionality across
Claude, Codex, and Dopemux sessions.

Features:
- Unified search across multiple agent types
- Interactive Rich table UI for session selection
- Session resume with directory restoration
- Cross-agent compatibility
"""

import os
import subprocess
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box

import logging
logger = logging.getLogger(__name__)

from ..adhd.context_manager import ContextManager
from ..tmux.cli import list_sessions


class SessionManagerError(Exception):
    """Raised when session management operations fail."""
    pass


class SessionManager:
    """
    Unified session management for Dopemux.

    Supports search and resume across Claude, Codex, and Dopemux sessions.
    """

    def __init__(self, context_manager: ContextManager, workspace_id: str = None):
        """
        Initialize session manager.

        Args:
            context_manager: Dopemux context manager instance
            workspace_id: Workspace identifier for ConPort
        """
        self.context_manager = context_manager
        self.workspace_id = workspace_id or os.getcwd()
        self.console = Console()
        self.session_index = {}
        self.conport_available = self._check_conport_availability()

    def _check_conport_availability(self) -> bool:
        """
        Check if ConPort is available for session storage.

        Returns:
            True if ConPort is available, False otherwise
        """
        try:
            # Try to import ConPort client
            from ..tools.conport_client import ConPortClient
            self.conport_client = ConPortClient(self.workspace_id)
            return True
        except ImportError:
            return False
        except Exception as e:
            return False

            logger.error(f"Error: {e}")
    def _store_session_in_conport(self, session_data: Dict[str, Any]) -> bool:
        """
        Store session data in ConPort.

        Args:
            session_data: Session data to store

        Returns:
            True if stored successfully, False otherwise
        """
        if not self.conport_available:
            return False

        try:
            # Store as custom data with category 'claude_tools_sessions'
            result = self.conport_client.log_custom_data(
                category="claude_tools_sessions",
                key=f"session_{session_data['id']}",
                value=session_data
            )
            return result.get('success', False)
        except Exception as e:
            self.console.logger.error(f"[yellow]Warning: Failed to store session in ConPort: {e}[/yellow]")
            return False

    def _retrieve_sessions_from_conport(self) -> List[Dict[str, Any]]:
        """
        Retrieve sessions from ConPort.

        Returns:
            List of session dictionaries
        """
        if not self.conport_available:
            return []

        try:
            result = self.conport_client.get_custom_data(category="claude_tools_sessions")
            if result.get('success'):
                return list(result.get('data', {}).values())
            return []
        except Exception as e:
            self.console.logger.error(f"[yellow]Warning: Failed to retrieve sessions from ConPort: {e}[/yellow]")
            return []

    def find_sessions(self, keywords: Optional[str] = None,
                     agent_filter: Optional[str] = None,
                     limit: int = 20) -> List[Dict[str, Any]]:
        """
        Search for sessions across all supported agents.

        Args:
            keywords: Optional search keywords
            agent_filter: Optional agent type filter
            limit: Maximum results to return

        Returns:
            List of session dictionaries
        """
        sessions = []

        # Search Dopemux sessions
        dopemux_sessions = self._find_dopemux_sessions(keywords, agent_filter)
        sessions.extend(dopemux_sessions)

        # Search Claude sessions
        claude_sessions = self._find_claude_sessions(keywords, agent_filter)
        sessions.extend(claude_sessions)

        # Search Codex sessions
        codex_sessions = self._find_codex_sessions(keywords, agent_filter)
        sessions.extend(codex_sessions)

        # Sort by timestamp (most recent first)
        sessions.sort(key=lambda x: x['timestamp'], reverse=True)

        # Apply limit
        return sessions[:limit]

    def _find_dopemux_sessions(self, keywords: Optional[str] = None,
                              agent_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Find Dopemux sessions.

        Args:
            keywords: Search keywords
            agent_filter: Agent filter

        Returns:
            List of Dopemux session dictionaries
        """
        sessions = []

        # Get sessions from context manager
        try:
            dopemux_sessions = self.context_manager.get_all_sessions()
            for session in dopemux_sessions:
                if self._session_matches(session, keywords, agent_filter):
                    sessions.append({
                        'id': session['session_id'],
                        'agent': 'dopemux',
                        'timestamp': datetime.fromisoformat(session['timestamp']),
                        'project': session.get('workspace_id', 'unknown'),
                        'branch': session.get('git_branch', 'unknown'),
                        'message': session.get('message', ''),
                        'goal': session.get('current_goal', ''),
                        'files': len(session.get('open_files', [])),
                        'duration': session.get('focus_duration', 0),
                        'path': session.get('session_path', '')
                    })
        except Exception as e:
            logger.warning(f"Error searching Dopemux sessions: {e}")

        return sessions

    def _find_claude_sessions(self, keywords: Optional[str] = None,
                            agent_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Find Claude sessions.

        Args:
            keywords: Search keywords
            agent_filter: Agent filter

        Returns:
            List of Claude session dictionaries
        """
        sessions = []
        claude_sessions_dir = Path.home() / ".claude" / "sessions"

        if not claude_sessions_dir.exists():
            return sessions

        for session_file in claude_sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)

                # Parse Claude session format
                timestamp = datetime.fromisoformat(data.get('timestamp', ''))
                message = data.get('last_message', '')

                if self._session_matches({'message': message}, keywords, agent_filter):
                    sessions.append({
                        'id': session_file.stem,
                        'agent': 'claude',
                        'timestamp': timestamp,
                        'project': 'claude',
                        'branch': 'unknown',
                        'message': message,
                        'goal': 'unknown',
                        'files': 0,
                        'duration': 0,
                        'path': str(session_file)
                    })
            except Exception as e:
                logger.warning(f"Error reading Claude session {session_file}: {e}")

        return sessions

    def _find_codex_sessions(self, keywords: Optional[str] = None,
                           agent_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Find Codex sessions.

        Args:
            keywords: Search keywords
            agent_filter: Agent filter

        Returns:
            List of Codex session dictionaries
        """
        sessions = []
        codex_sessions_dir = Path.home() / ".codex" / "sessions"

        if not codex_sessions_dir.exists():
            return sessions

        for session_file in codex_sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    data = json.load(f)

                # Parse Codex session format (similar to Claude)
                timestamp = datetime.fromisoformat(data.get('timestamp', ''))
                message = data.get('last_message', '')

                if self._session_matches({'message': message}, keywords, agent_filter):
                    sessions.append({
                        'id': session_file.stem,
                        'agent': 'codex',
                        'timestamp': timestamp,
                        'project': 'codex',
                        'branch': 'unknown',
                        'message': message,
                        'goal': 'unknown',
                        'files': 0,
                        'duration': 0,
                        'path': str(session_file)
                    })
            except Exception as e:
                logger.warning(f"Error reading Codex session {session_file}: {e}")

        return sessions

    def _session_matches(self, session: Dict[str, Any], keywords: Optional[str],
                        agent_filter: Optional[str]) -> bool:
        """
        Check if a session matches the search criteria.

        Args:
            session: Session dictionary
            keywords: Search keywords
            agent_filter: Agent filter

        Returns:
            True if session matches, False otherwise
        """
        # Agent filter
        if agent_filter:
            if session.get('agent') != agent_filter:
                return False

        # Keyword search (simple implementation)
        if keywords:
            search_text = f"{session.get('message', '')} {session.get('goal', '')}"
            for keyword in keywords.split():
                if keyword.lower() not in search_text.lower():
                    return False

        return True

    def display_sessions(self, sessions: List[Dict[str, Any]]) -> None:
        """
        Display sessions in Rich table format.

        Args:
            sessions: List of session dictionaries
        """
        if not sessions:
            self.console.logger.info("No sessions found matching your criteria.")
            self.console.logger.info("Use '/save' to create your first session!")
            return

        # Group sessions by time
        grouped = self._group_sessions_by_time(sessions)

        # Display grouped sessions
        for group_name, group_sessions in grouped.items():
            self.console.logger.info(f"[bold cyan]Recent Sessions - {group_name}[/bold cyan]")

            table = Table(box=box.ROUNDED)
            table.add_column("Agent", style="cyan", no_wrap=True)
            table.add_column("Project", style="magenta")
            table.add_column("Branch", style="green")
            table.add_column("Time", style="dim")
            table.add_column("Files", justify="right")
            table.add_column("Duration", justify="right")
            table.add_column("Message", style="white")

            for session in group_sessions:
                time_str = self._format_relative_time(session['timestamp'])
                table.add_row(
                    session['agent'],
                    session['project'],
                    session['branch'],
                    time_str,
                    str(session['files']),
                    f"{session['duration']}m",
                    session['message'][:50] + "..." if len(session['message']) > 50 else session['message']
                )

            self.console.logger.info(table)
            self.console.logger.info()

    def _group_sessions_by_time(self, sessions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group sessions by time periods.

        Args:
            sessions: List of session dictionaries

        Returns:
            Dict with time groups as keys
        """
        now = datetime.now()
        groups = {
            "Today": [],
            "Yesterday": [],
            "This Week": [],
            "Older": []
        }

        for session in sessions:
            delta = now - session['timestamp']

            if delta < timedelta(days=1):
                groups["Today"].append(session)
            elif delta < timedelta(days=2):
                groups["Yesterday"].append(session)
            elif delta < timedelta(weeks=1):
                groups["This Week"].append(session)
            else:
                groups["Older"].append(session)

        return groups

    def _format_relative_time(self, timestamp: str) -> str:
        """
        Format timestamp as relative time.

        Args:
            timestamp: Session timestamp string (ISO format)

        Returns:
            Relative time string
        """
        try:
            timestamp_dt = datetime.fromisoformat(timestamp)
        except ValueError:
            return "unknown time"

        now = datetime.now()
        delta = now - timestamp_dt

        if delta < timedelta(minutes=1):
            return "just now"
        elif delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() / 60)
            return f"{minutes}m ago"
        elif delta < timedelta(days=1):
            hours = int(delta.total_seconds() / 3600)
            return f"{hours}h ago"
        else:
            return timestamp_dt.strftime("%m/%d %H:%M")

    def resume_session(self, session: Dict[str, Any]) -> bool:
        """
        Resume a session.

        Args:
            session: Session dictionary to resume

        Returns:
            True if resume successful, False otherwise
        """
        try:
            if session['agent'] == 'dopemux':
                return self._resume_dopemux_session(session)
            elif session['agent'] == 'claude':
                return self._resume_claude_session(session)
            elif session['agent'] == 'codex':
                return self._resume_codex_session(session)
            else:
                self.console.logger.info(f"[red]Unsupported agent: {session['agent']}[/red]")
                return False

        except Exception as e:
            logger.error(f"Error resuming session {session['id']}: {e}")
            self.console.logger.error(f"[red]Failed to resume session: {e}[/red]")
            return False

    def _resume_dopemux_session(self, session: Dict[str, Any]) -> bool:
        """
        Resume a Dopemux session.

        Args:
            session: Dopemux session dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            # Use context manager to restore
            self.context_manager.restore_session(session['id'])
            self.console.logger.info(f"[green]Resumed Dopemux session: {session['id']}[/green]")
            return True
        except Exception as e:
            logger.error(f"Failed to resume Dopemux session: {e}")
            return False

    def _resume_claude_session(self, session: Dict[str, Any]) -> bool:
        """
        Resume a Claude session.

        Args:
            session: Claude session dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            session_path = Path(session['path'])
            session_dir = session_path.parent

            # Change to session directory
            os.chdir(session_dir)

            # Launch Claude with resume
            subprocess.run([
                "claude",
                "-r", session['id'],
                "--no-recovery"
            ])

            self.console.logger.info(f"[green]Resumed Claude session: {session['id']}[/green]")
            return True
        except Exception as e:
            logger.error(f"Failed to resume Claude session: {e}")
            return False

    def _resume_codex_session(self, session: Dict[str, Any]) -> bool:
        """
        Resume a Codex session.

        Args:
            session: Codex session dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            session_path = Path(session['path'])
            session_dir = session_path.parent

            # Change to session directory
            os.chdir(session_dir)

            # Launch Codex with resume (assuming similar CLI)
            subprocess.run([
                "codex",
                "resume", session['id']
            ])

            self.console.logger.info(f"[green]Resumed Codex session: {session['id']}[/green]")
            return True
        except Exception as e:
            logger.error(f"Failed to resume Codex session: {e}")
            return False