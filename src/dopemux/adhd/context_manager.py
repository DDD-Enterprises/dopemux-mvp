"""
Context Manager for ADHD-optimized development.

Handles automatic preservation and restoration of development context including
files, cursor positions, mental model, and decision history.
"""

import hashlib
import json
import shlex
import sqlite3
import subprocess
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console

console = Console()


class ContextSnapshot:
    """Represents a saved development context."""

    def __init__(self, **kwargs):
        self.session_id = kwargs.get("session_id", str(uuid.uuid4()))
        self.timestamp = kwargs.get("timestamp", datetime.now().isoformat())
        self.working_directory = kwargs.get("working_directory", str(Path.cwd()))
        self.open_files = kwargs.get("open_files", [])
        self.current_goal = kwargs.get("current_goal", "")
        self.mental_model = kwargs.get("mental_model", {})
        self.git_state = kwargs.get("git_state", {})
        self.recent_commands = kwargs.get("recent_commands", [])
        self.decisions = kwargs.get("decisions", [])
        self.attention_state = kwargs.get("attention_state", "normal")
        self.focus_duration = kwargs.get("focus_duration", 0)
        self.context_switches = kwargs.get("context_switches", 0)
        self.unsaved_changes = kwargs.get("unsaved_changes", False)
        self.message = kwargs.get("message", "")
        self.tags = kwargs.get("tags", [])
        self.auto_description = kwargs.get("auto_description", "")
        self.session_type = kwargs.get("session_type", "general")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "session_id": self.session_id,
            "timestamp": self.timestamp,
            "working_directory": self.working_directory,
            "open_files": self.open_files,
            "current_goal": self.current_goal,
            "mental_model": self.mental_model,
            "git_state": self.git_state,
            "recent_commands": self.recent_commands,
            "decisions": self.decisions,
            "attention_state": self.attention_state,
            "focus_duration": self.focus_duration,
            "context_switches": self.context_switches,
            "unsaved_changes": self.unsaved_changes,
            "message": self.message,
            "tags": self.tags,
            "auto_description": self.auto_description,
            "session_type": self.session_type,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextSnapshot":
        """Create from dictionary."""
        return cls(**data)


class ContextManager:
    """
    Manages development context preservation and restoration.

    Features:
    - Auto-save every 30 seconds
    - Capture file states, cursor positions, mental model
    - SQLite storage for fast access
    - Git integration for change tracking
    - Emergency context saves on interruption
    """

    def __init__(self, project_path: Path):
        """Initialize context manager for project."""
        self.project_path = project_path
        self.dopemux_dir = project_path / ".dopemux"
        self.db_path = self.dopemux_dir / "context.db"
        self.sessions_dir = self.dopemux_dir / "sessions"

        # Create directories if they don't exist (needed for database)
        self.dopemux_dir.mkdir(exist_ok=True)
        self.sessions_dir.mkdir(exist_ok=True)

        self._init_storage()
        self._auto_save_enabled = False
        self._current_session_id = None

    def initialize(self) -> None:
        """Initialize context manager for new project."""
        self.dopemux_dir.mkdir(exist_ok=True)
        self.sessions_dir.mkdir(exist_ok=True)
        self._init_storage()

        # Create initial session
        self._current_session_id = str(uuid.uuid4())
        console.print("[green]✓ Context manager initialized[/green]")

    def _validate_project_path(self, file_path: Path) -> bool:
        """
        Ensure file path is within project boundaries to prevent directory traversal.

        Args:
            file_path: Path to validate

        Returns:
            True if path is safe and within project, False otherwise
        """
        try:
            # Resolve both paths to handle symlinks and relative paths
            resolved_file = file_path.resolve()
            resolved_project = self.project_path.resolve()

            # Check if file path is within project boundaries
            resolved_file.relative_to(resolved_project)
            return True

        except (ValueError, OSError):
            # ValueError: path is outside project
            # OSError: path doesn't exist or permission issues
            console.print(f"[red]Security: Blocked access to path outside project: {file_path}[/red]")
            return False

    def _run_git_command(self, args: List[str], timeout: int = 10) -> Optional[str]:
        """
        Securely run git command with input validation and timeout.

        Args:
            args: Git command arguments (without 'git')
            timeout: Command timeout in seconds

        Returns:
            Command output if successful, None if failed
        """
        # Validate git command arguments
        allowed_commands = {
            "branch", "status", "log", "show", "diff", "rev-parse", "config"
        }

        if not args or args[0] not in allowed_commands:
            console.print(f"[red]Security: Git command not allowed: {args}[/red]")
            return None

        # Build secure command
        cmd = ["git"] + args

        try:
            # Run with security constraints
            result = subprocess.run(
                cmd,
                cwd=str(self.project_path),  # Ensure we're in project directory
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False  # Don't raise on non-zero exit
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                # Log error but don't expose it to prevent information leakage
                console.print(f"[yellow]Git command failed (code {result.returncode})[/yellow]")
                return None

        except subprocess.TimeoutExpired:
            console.print(f"[red]Git command timed out after {timeout}s[/red]")
            return None
        except Exception as e:
            console.print(f"[red]Git command error: {type(e).__name__}[/red]")
            return None

    def _init_storage(self) -> None:
        """Initialize SQLite database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS context_snapshots (
                    session_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    working_directory TEXT NOT NULL,
                    data TEXT NOT NULL,
                    hash TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_metadata (
                    session_id TEXT PRIMARY KEY,
                    project_path TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    last_active TEXT NOT NULL,
                    total_duration INTEGER DEFAULT 0,
                    context_switches INTEGER DEFAULT 0,
                    focus_score REAL DEFAULT 0.0,
                    tags TEXT DEFAULT '[]',
                    auto_description TEXT DEFAULT '',
                    session_type TEXT DEFAULT 'general'
                )
            """
            )

            # Create session tags table for better tag management
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS session_tags (
                    session_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (session_id, tag),
                    FOREIGN KEY (session_id) REFERENCES context_snapshots(session_id) ON DELETE CASCADE
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp
                ON context_snapshots(timestamp DESC)
            """
            )

    def save_context(self, message: Optional[str] = None, force: bool = False) -> str:
        """
        Save current development context.

        Args:
            message: Optional message describing the save
            force: Force save even if no changes detected

        Returns:
            Session ID of saved context
        """
        try:
            # Capture current state
            context = self._capture_current_state()
            if message:
                context.message = message

            # Check if context has changed (unless forced)
            if not force and not self._has_context_changed(context):
                return context.session_id

            # Store in database
            self._store_context(context)

            # Update session metadata
            self._update_session_metadata(context.session_id)

            # Save detailed session file
            self._save_session_file(context)

            self._current_session_id = context.session_id
            return context.session_id

        except Exception as e:
            console.print(f"[red]Error saving context: {e}[/red]")
            # Emergency fallback
            emergency_session_id = self._emergency_save()
            return emergency_session_id or str(uuid.uuid4())

    def restore_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Restore specific session by ID.

        Args:
            session_id: Session ID to restore

        Returns:
            Context data or None if not found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT data FROM context_snapshots WHERE session_id = ?",
                    (session_id,),
                )
                row = cursor.fetchone()

                if row:
                    context_data = json.loads(row[0])
                    self._apply_context(context_data)
                    return context_data

            return None

        except Exception as e:
            console.print(f"[red]Error restoring session {session_id}: {e}[/red]")
            return None

    def restore_latest(self) -> Optional[Dict[str, Any]]:
        """
        Restore most recent session.

        Returns:
            Latest context data or None if none found
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """SELECT session_id, data FROM context_snapshots
                       WHERE working_directory = ?
                       ORDER BY timestamp DESC LIMIT 1""",
                    (str(self.project_path),),
                )
                row = cursor.fetchone()

                if row:
                    context_data = json.loads(row[1])
                    self._apply_context(context_data)
                    return context_data

            return None

        except Exception as e:
            console.print(f"[red]Error restoring latest session: {e}[/red]")
            return None

    def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        List recent sessions.

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of session information
        """
        sessions = []

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """SELECT session_id, timestamp, data
                       FROM context_snapshots
                       WHERE working_directory = ?
                       ORDER BY timestamp DESC LIMIT ?""",
                    (str(self.project_path), limit),
                )

                for row in cursor.fetchall():
                    session_id, timestamp, data_json = row
                    data = json.loads(data_json)

                    sessions.append(
                        {
                            "id": session_id,
                            "timestamp": timestamp,
                            "current_goal": data.get("current_goal", "No goal set"),
                            "open_files": data.get("open_files", []),
                            "git_branch": data.get("git_state", {}).get(
                                "branch", "unknown"
                            ),
                            "focus_duration": data.get("focus_duration", 0),
                            "message": data.get("message", ""),
                        }
                    )

        except Exception as e:
            console.print(f"[red]Error listing sessions: {e}[/red]")

        return sessions

    def get_current_context(self) -> Dict[str, Any]:
        """Get current context information."""
        try:
            context = self._capture_current_state()
            return context.to_dict()
        except Exception as e:
            console.print(f"[red]Error getting current context: {e}[/red]")
            return {}

    def start_auto_save(self, interval: int = 30) -> None:
        """Start automatic context saving."""
        self._auto_save_enabled = True
        # In a real implementation, this would start a background thread
        console.print(f"[blue]Auto-save enabled (every {interval}s)[/blue]")

    def stop_auto_save(self) -> None:
        """Stop automatic context saving."""
        self._auto_save_enabled = False
        console.print("[blue]Auto-save disabled[/blue]")

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Clean up sessions older than specified days.

        Args:
            days: Number of days to keep

        Returns:
            Number of sessions cleaned up
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.isoformat()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM context_snapshots WHERE timestamp < ?", (cutoff_str,)
                )
                deleted_count = cursor.rowcount

                # Also clean up session files
                for session_file in self.sessions_dir.glob("session-*.json"):
                    if session_file.stat().st_mtime < cutoff_date.timestamp():
                        session_file.unlink()

                console.print(
                    f"[green]✓ Cleaned up {deleted_count} old sessions[/green]"
                )
                return deleted_count

        except Exception as e:
            console.print(f"[red]Error cleaning up sessions: {e}[/red]")
            return 0

    def generate_smart_description(self, context: ContextSnapshot) -> str:
        """Generate smart description based on git changes and context."""
        git_state = context.git_state

        # Check git status for recent changes
        if git_state.get("status"):
            status_lines = git_state["status"].split("\n")
            modified_files = []
            added_files = []
            deleted_files = []

            for line in status_lines:
                line = line.strip()
                if line.startswith("M "):
                    modified_files.append(line[2:])
                elif line.startswith("A "):
                    added_files.append(line[2:])
                elif line.startswith("D "):
                    deleted_files.append(line[2:])

            # Generate description based on changes
            if added_files:
                if len(added_files) == 1:
                    return f"Added {Path(added_files[0]).name}"
                else:
                    return f"Added {len(added_files)} new files"
            elif modified_files:
                # Determine primary file type
                extensions = [Path(f).suffix for f in modified_files]
                common_ext = max(set(extensions), key=extensions.count) if extensions else ""

                if len(modified_files) == 1:
                    return f"Modified {Path(modified_files[0]).name}"
                elif common_ext == ".py":
                    return f"Updated Python code ({len(modified_files)} files)"
                elif common_ext in [".js", ".ts", ".tsx"]:
                    return f"Updated JavaScript/TypeScript ({len(modified_files)} files)"
                elif common_ext == ".md":
                    return f"Updated documentation ({len(modified_files)} files)"
                else:
                    return f"Modified {len(modified_files)} files"
            elif deleted_files:
                return f"Removed {len(deleted_files)} files"

        # Fallback to goal-based description
        goal = context.current_goal
        if goal and goal != "Continue development":
            return goal[:50] + ("..." if len(goal) > 50 else "")

        # Check last commit for context
        last_commit = git_state.get("last_commit", "")
        if last_commit and len(last_commit.split()) > 1:
            # Extract meaningful part of commit message
            commit_msg = " ".join(last_commit.split()[1:])
            return f"Continue: {commit_msg[:40]}..."

        return "Development session"

    def auto_tag_session(self, context: ContextSnapshot) -> List[str]:
        """Automatically generate tags based on session context."""
        tags = []

        # Analyze git changes for automatic tagging
        git_state = context.git_state
        if git_state.get("status"):
            status = git_state["status"].lower()

            # File type tags
            if ".py" in status:
                tags.append("python")
            if any(ext in status for ext in [".js", ".ts", ".tsx", ".jsx"]):
                tags.append("javascript")
            if ".md" in status or "readme" in status:
                tags.append("docs")
            if "test" in status or ".test." in status:
                tags.append("testing")
            if any(ext in status for ext in [".yml", ".yaml", ".json", "config"]):
                tags.append("config")

        # Analyze file paths for context
        open_files = context.open_files
        file_paths = []
        for file_info in open_files:
            if isinstance(file_info, dict):
                path = file_info.get("path", "")
            else:
                path = str(file_info)
            file_paths.append(path.lower())

        combined_paths = " ".join(file_paths)

        # Feature detection
        if any(keyword in combined_paths for keyword in ["feature", "feat", "new"]):
            tags.append("feature")
        if any(keyword in combined_paths for keyword in ["fix", "bug", "error"]):
            tags.append("bugfix")
        if any(keyword in combined_paths for keyword in ["test", "spec", "__test__"]):
            tags.append("testing")
        if any(keyword in combined_paths for keyword in ["doc", "readme", "guide"]):
            tags.append("documentation")
        if any(keyword in combined_paths for keyword in ["refactor", "clean"]):
            tags.append("refactor")

        # Analyze message for manual tags
        message = context.message.lower() if context.message else ""
        if message:
            if any(keyword in message for keyword in ["wip", "progress", "working"]):
                tags.append("wip")
            if any(keyword in message for keyword in ["done", "complete", "finish"]):
                tags.append("complete")
            if any(keyword in message for keyword in ["break", "pause", "save"]):
                tags.append("checkpoint")

        # Time-based tags
        hour = datetime.now().hour
        if 6 <= hour < 12:
            tags.append("morning")
        elif 12 <= hour < 17:
            tags.append("afternoon")
        elif 17 <= hour < 22:
            tags.append("evening")
        else:
            tags.append("late-night")

        # Focus duration tags
        focus_duration = context.focus_duration
        if focus_duration > 45:
            tags.append("deep-work")
        elif focus_duration > 20:
            tags.append("focused")
        elif focus_duration > 0:
            tags.append("quick-session")

        return list(set(tags))  # Remove duplicates

    def detect_session_type(self, context: ContextSnapshot) -> str:
        """Detect session type based on context and changes."""
        message = context.message.lower() if context.message else ""
        git_state = context.git_state

        # Check commit message patterns
        if git_state.get("last_commit"):
            last_commit = git_state["last_commit"].lower()
            if any(word in last_commit for word in ["feat:", "feature:", "add:"]):
                return "feature"
            elif any(word in last_commit for word in ["fix:", "bug:", "hotfix:"]):
                return "bugfix"
            elif any(word in last_commit for word in ["docs:", "doc:"]):
                return "documentation"
            elif any(word in last_commit for word in ["test:", "tests:"]):
                return "testing"
            elif any(word in last_commit for word in ["refactor:", "clean:"]):
                return "refactor"
            elif any(word in last_commit for word in ["config:", "setup:"]):
                return "configuration"

        # Check message for type indicators
        if any(keyword in message for keyword in ["implement", "add", "create", "new"]):
            return "feature"
        elif any(keyword in message for keyword in ["fix", "bug", "error", "issue"]):
            return "bugfix"
        elif any(keyword in message for keyword in ["doc", "readme", "guide", "explain"]):
            return "documentation"
        elif any(keyword in message for keyword in ["test", "coverage", "spec"]):
            return "testing"
        elif any(keyword in message for keyword in ["refactor", "clean", "optimize"]):
            return "refactor"
        elif any(keyword in message for keyword in ["debug", "investigate", "explore"]):
            return "debugging"
        elif any(keyword in message for keyword in ["review", "check", "validate"]):
            return "review"

        # Check files being worked on
        open_files = context.open_files
        test_files = 0
        doc_files = 0
        config_files = 0

        for file_info in open_files:
            if isinstance(file_info, dict):
                path = file_info.get("path", "")
            else:
                path = str(file_info)

            path_lower = path.lower()
            if "test" in path_lower or path_lower.endswith((".test.py", ".spec.js")):
                test_files += 1
            elif path_lower.endswith((".md", ".rst", ".txt")):
                doc_files += 1
            elif any(config_word in path_lower for config_word in ["config", "settings", ".env", ".yml", ".yaml"]):
                config_files += 1

        # Determine type based on file patterns
        total_files = len(open_files)
        if total_files > 0:
            if test_files / total_files > 0.5:
                return "testing"
            elif doc_files / total_files > 0.5:
                return "documentation"
            elif config_files / total_files > 0.5:
                return "configuration"

        return "general"  # Default type

    def add_session_tags(self, session_id: str, tags: List[str]) -> None:
        """Add tags to a session."""
        with sqlite3.connect(self.db_path) as conn:
            for tag in tags:
                conn.execute(
                    """INSERT OR IGNORE INTO session_tags (session_id, tag)
                       VALUES (?, ?)""",
                    (session_id, tag)
                )

    def get_session_tags(self, session_id: str) -> List[str]:
        """Get tags for a session."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT tag FROM session_tags WHERE session_id = ?",
                (session_id,)
            )
            return [row[0] for row in cursor.fetchall()]

    def search_sessions_by_tag(self, tag: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search sessions by tag."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """SELECT DISTINCT cs.session_id, cs.timestamp, cs.data
                   FROM context_snapshots cs
                   JOIN session_tags st ON cs.session_id = st.session_id
                   WHERE st.tag = ? AND cs.working_directory = ?
                   ORDER BY cs.timestamp DESC LIMIT ?""",
                (tag, str(self.project_path), limit)
            )

            sessions = []
            for row in cursor.fetchall():
                session_id, timestamp, data_json = row
                data = json.loads(data_json)
                sessions.append({
                    "id": session_id,
                    "timestamp": timestamp,
                    "current_goal": data.get("current_goal", "No goal set"),
                    "open_files": data.get("open_files", []),
                    "git_branch": data.get("git_state", {}).get("branch", "unknown"),
                    "focus_duration": data.get("focus_duration", 0),
                    "message": data.get("message", ""),
                    "tags": self.get_session_tags(session_id)
                })

            return sessions

    def _capture_current_state(self) -> ContextSnapshot:
        """Capture current development state."""
        # Get open files (this would integrate with editor)
        open_files = self._get_open_files()

        # Get git state
        git_state = self._get_git_state()

        # Get recent commands (from shell history)
        recent_commands = self._get_recent_commands()

        # Create context snapshot
        context = ContextSnapshot(
            session_id=self._current_session_id or str(uuid.uuid4()),
            working_directory=str(self.project_path),
            open_files=open_files,
            git_state=git_state,
            recent_commands=recent_commands,
            # These would be populated by other components
            current_goal=self._get_current_goal(),
            mental_model=self._get_mental_model(),
            decisions=self._get_recent_decisions(),
            attention_state="normal",  # Would come from attention monitor
            focus_duration=0,  # Would come from attention monitor
            context_switches=0,  # Would come from attention monitor
            unsaved_changes=self._has_unsaved_changes(),
        )

        # Add smart features
        context.auto_description = self.generate_smart_description(context)
        context.session_type = self.detect_session_type(context)
        context.tags = self.auto_tag_session(context)

        return context

    def _get_open_files(self) -> List[Dict[str, Any]]:
        """Get list of currently open files."""
        # This would integrate with the editor to get actual open files
        # For now, return recently modified files as approximation
        open_files = []

        try:
            # Find recently modified files with security validation
            for file_path in self.project_path.rglob("*"):
                # Validate path is within project boundaries
                if not self._validate_project_path(file_path):
                    continue

                if (
                    file_path.is_file()
                    and not any(part.startswith(".") for part in file_path.parts)
                    and file_path.suffix
                    in [".py", ".js", ".ts", ".rs", ".md", ".yaml", ".json"]
                ):

                    # Check if modified in last hour
                    mtime = file_path.stat().st_mtime
                    if time.time() - mtime < 3600:  # 1 hour
                        open_files.append(
                            {
                                "path": str(file_path.relative_to(self.project_path)),
                                "absolute_path": str(file_path),
                                "last_modified": datetime.fromtimestamp(
                                    mtime
                                ).isoformat(),
                                "cursor_position": {"line": 1, "column": 1},  # Default
                                "scroll_position": 0,
                                "unsaved_changes": False,
                            }
                        )

        except Exception as e:
            console.print(f"[yellow]Warning: Could not get open files: {e}[/yellow]")

        return open_files[:10]  # Limit to 10 most recent

    def _get_git_state(self) -> Dict[str, Any]:
        """Get current git repository state with secure git operations."""
        git_state = {}

        try:
            # Get current branch
            branch = self._run_git_command(["branch", "--show-current"])
            if branch:
                git_state["branch"] = branch

            # Get status
            status = self._run_git_command(["status", "--porcelain"])
            if status is not None:
                git_state["status"] = status
                git_state["has_changes"] = bool(status)

            # Get last commit
            last_commit = self._run_git_command(["log", "-1", "--oneline"])
            if last_commit:
                git_state["last_commit"] = last_commit

        except Exception as e:
            console.print(f"[yellow]Warning: Could not get git state: {e}[/yellow]")

        return git_state

    def _get_recent_commands(self) -> List[str]:
        """Get recent shell commands."""
        # This would integrate with shell history
        # For now, return empty list
        return []

    def _get_current_goal(self) -> str:
        """Get current development goal."""
        # This would be maintained by the task decomposer
        return "Continue development"

    def _get_mental_model(self) -> Dict[str, Any]:
        """Get current mental model."""
        # This would be maintained by the system
        return {
            "approach": "Implementing ADHD features",
            "next_steps": ["Complete context manager", "Add attention monitoring"],
            "blockers": [],
        }

    def _get_recent_decisions(self) -> List[Dict[str, Any]]:
        """Get recent development decisions."""
        # This would be maintained by the system
        return []

    def _has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        # This would integrate with the editor
        git_state = self._get_git_state()
        return git_state.get("has_changes", False)

    def _has_context_changed(self, context: ContextSnapshot) -> bool:
        """Check if context has meaningfully changed."""
        # For now, always return True (save every time)
        # In a real implementation, this would compare with last saved context
        return True

    def _store_context(self, context: ContextSnapshot) -> None:
        """Store context in database."""
        data_json = json.dumps(context.to_dict())
        data_hash = hashlib.sha256(data_json.encode()).hexdigest()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO context_snapshots
                   (session_id, timestamp, working_directory, data, hash, size)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    context.session_id,
                    context.timestamp,
                    context.working_directory,
                    data_json,
                    data_hash,
                    len(data_json),
                ),
            )

            # Store tags in separate table
            if context.tags:
                # Clear existing tags for this session
                conn.execute(
                    "DELETE FROM session_tags WHERE session_id = ?",
                    (context.session_id,)
                )
                # Insert new tags
                for tag in context.tags:
                    conn.execute(
                        """INSERT INTO session_tags (session_id, tag)
                           VALUES (?, ?)""",
                        (context.session_id, tag)
                    )

    def _update_session_metadata(self, session_id: str) -> None:
        """Update session metadata."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO session_metadata
                   (session_id, project_path, started_at, last_active)
                   VALUES (?, ?, ?, ?)""",
                (
                    session_id,
                    str(self.project_path),
                    datetime.now().isoformat(),
                    datetime.now().isoformat(),
                ),
            )

    def _save_session_file(self, context: ContextSnapshot) -> None:
        """Save detailed session file."""
        session_file = self.sessions_dir / f"session-{context.session_id}.json"
        with open(session_file, "w") as f:
            json.dump(context.to_dict(), f, indent=2)

    def _apply_context(self, context_data: Dict[str, Any]) -> None:
        """Apply restored context (placeholder for editor integration)."""
        # This would integrate with the editor to restore file positions
        # For now, just print what would be restored
        console.print(
            f"[blue]Restoring context: {context_data.get('current_goal', 'Unknown')}[/blue]"
        )

    def _emergency_save(self) -> Optional[str]:
        """Emergency context save on system failure."""
        try:
            emergency_file = self.dopemux_dir / "emergency_context.json"
            # Create minimal context without calling potentially failing methods
            emergency_session_id = str(uuid.uuid4())
            emergency_context = {
                "session_id": emergency_session_id,
                "timestamp": datetime.now().isoformat(),
                "working_directory": str(self.project_path),
                "emergency_save": True,
                "message": "Emergency save due to system failure",
            }
            with open(emergency_file, "w") as f:
                json.dump(emergency_context, f, indent=2)
            console.print("[yellow]Emergency context saved[/yellow]")
            return emergency_session_id
        except Exception as e:
            console.print(f"[red]Emergency save failed: {e}[/red]")
            return None
