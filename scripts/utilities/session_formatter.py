#!/usr/bin/env python3
"""
Session Formatter for ADHD-friendly visual session management.

Provides Rich-based formatting utilities for beautiful, accessible session displays
optimized for neurodivergent developers.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

console = Console()


class SessionFormatter:
    """
    ADHD-optimized session formatter with visual elements.

    Features:
    - Color-coded session states
    - Emoji indicators for quick recognition
    - Time anchoring with relative timestamps
    - Progress visualizations
    - Chunked information display (max 5 items)
    """

    # Color scheme for ADHD-friendly recognition
    COLORS = {
        "success": "green",
        "info": "blue",
        "warning": "yellow",
        "error": "red",
        "muted": "dim",
        "bright": "bright_white"
    }

    # Emoji indicators for session types and states
    EMOJIS = {
        "session": "📍",
        "save": "💾",
        "restore": "🔄",
        "active": "🎯",
        "complete": "✅",
        "in_progress": "⏳",
        "recent": "🔥",
        "old": "📚",
        "feature": "✨",
        "fix": "🔧",
        "bug": "🐛",
        "docs": "📚",
        "refactor": "♻️",
        "test": "🧪",
        "config": "⚙️"
    }

    def __init__(self):
        """Initialize formatter with ADHD-optimized settings."""
        self.max_items_per_view = 5
        self.max_description_length = 50

    def format_save_confirmation(self, session_data: Dict[str, Any]) -> str:
        """Format session save confirmation with visual preview."""
        session_id = session_data.get("session_id", "unknown")[:8]
        message = session_data.get("message", "")
        goal = session_data.get("current_goal", "No goal set")
        open_files = len(session_data.get("open_files", []))

        # Auto-detect session type from changes
        session_type = self._detect_session_type(session_data)
        emoji = self.EMOJIS.get(session_type, self.EMOJIS["session"])

        # Create preview panel
        content = Text()
        content.append(f"{self.EMOJIS['save']} Session Saved Successfully!\n\n", style="green bold")
        content.append(f"{emoji} ", style="bright_white")
        content.append(f"ID: {session_id}\n", style="cyan")

        if message:
            content.append(f"📝 Note: {message}\n", style="dim")

        content.append(f"🎯 Goal: {self._truncate_text(goal, 40)}\n", style="blue")
        content.append(f"📁 Files: {open_files} files saved\n", style="yellow")
        content.append(f"⏰ Time: {self._format_relative_time(session_data.get('timestamp'))}", style="dim")

        return Panel(
            Align.center(content),
            title=f"{self.EMOJIS['session']} Session Saved",
            border_style="green",
            padding=(1, 2)
        )

    def format_session_gallery(self, sessions: List[Dict[str, Any]], limit: int = None) -> str:
        """Format sessions in a card-based gallery view."""
        if not sessions:
            empty_panel = Panel(
                Align.center(Text("No sessions found\n\nTip: Use '/save' to create your first session!", style="dim")),
                title="📚 Sessions",
                border_style="yellow"
            )
            return empty_panel

        # Limit sessions for ADHD-friendly display
        display_limit = min(limit or self.max_items_per_view, len(sessions))
        display_sessions = sessions[:display_limit]

        # Group sessions by time period
        grouped_sessions = self._group_sessions_by_time(display_sessions)

        content = Text()

        for group_name, group_sessions in grouped_sessions.items():
            if not group_sessions:
                continue

            content.append(f"\n{self._get_time_group_emoji(group_name)} {group_name} ({len(group_sessions)} sessions)\n",
                         style="bright_white bold")
            content.append("─" * 60 + "\n", style="dim")

            for session in group_sessions:
                session_card = self._format_session_card(session)
                content.append(session_card)
                content.append("\n")

        if len(sessions) > display_limit:
            remaining = len(sessions) - display_limit
            content.append(f"\n... and {remaining} more sessions\n", style="dim")
            content.append("💡 Use '--limit' to show more or '--search' to filter\n", style="blue")

        return Panel(
            content,
            title="📚 Recent Sessions",
            border_style="blue",
            padding=(1, 2)
        )

    def format_session_details(self, session_data: Dict[str, Any]) -> str:
        """Format detailed view of a specific session."""
        session_id = session_data.get("session_id", "unknown")

        # Create detailed table
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Field", style="cyan", width=15)
        table.add_column("Value", style="white")

        # Session overview
        table.add_row("ID", session_id[:8])
        table.add_row("Timestamp", self._format_relative_time(session_data.get("timestamp")))

        if session_data.get("message"):
            table.add_row("Message", session_data["message"])

        table.add_row("Goal", session_data.get("current_goal", "No goal set"))

        # File information
        open_files = session_data.get("open_files", [])
        table.add_row("Open Files", str(len(open_files)))

        if open_files:
            file_list = "\n".join(f"• {f.get('path', f)}" for f in open_files[:5])
            if len(open_files) > 5:
                file_list += f"\n... and {len(open_files) - 5} more files"
            table.add_row("", file_list)

        # Git information
        git_state = session_data.get("git_state", {})
        if git_state:
            table.add_row("Git Branch", git_state.get("branch", "unknown"))
            if git_state.get("has_changes"):
                table.add_row("Git Status", "Has uncommitted changes")

        # Session metrics
        focus_duration = session_data.get("focus_duration", 0)
        if focus_duration > 0:
            table.add_row("Focus Time", f"{focus_duration:.1f} minutes")

        context_switches = session_data.get("context_switches", 0)
        if context_switches > 0:
            table.add_row("Context Switches", str(context_switches))

        return Panel(
            table,
            title=f"{self.EMOJIS['session']} Session Details",
            border_style="blue",
            padding=(1, 1)
        )

    def format_restore_preview(self, session_data: Dict[str, Any]) -> str:
        """Format restoration preview with confirmation prompt."""
        session_id = session_data.get("session_id", "unknown")[:8]
        goal = session_data.get("current_goal", "No goal set")
        open_files = len(session_data.get("open_files", []))
        timestamp = self._format_relative_time(session_data.get("timestamp"))

        content = Text()
        content.append(f"{self.EMOJIS['restore']} Ready to Restore Session\n\n", style="blue bold")
        content.append(f"📍 ID: {session_id}\n", style="cyan")
        content.append(f"🎯 Goal: {self._truncate_text(goal, 40)}\n", style="yellow")
        content.append(f"📁 Files: {open_files} files to restore\n", style="green")
        content.append(f"⏰ From: {timestamp}\n\n", style="dim")
        content.append("This will restore your workspace to this saved state.\n", style="white")
        content.append("Any unsaved changes will be preserved.", style="yellow")

        return Panel(
            Align.center(content),
            title=f"{self.EMOJIS['restore']} Restore Preview",
            border_style="blue",
            padding=(1, 2)
        )

    def format_progress_bar(self, description: str, total: Optional[int] = None) -> Progress:
        """Create ADHD-friendly progress bar with visual feedback."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}", justify="left"),
            BarColumn(bar_width=30),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
            transient=True
        )

    def _format_session_card(self, session: Dict[str, Any]) -> Text:
        """Format individual session as a card."""
        session_id = session.get("id", "unknown")[:8]
        goal = session.get("current_goal", "No goal set")
        timestamp = self._format_relative_time(session.get("timestamp"))
        open_files = len(session.get("open_files", []))
        git_branch = session.get("git_branch", "")
        message = session.get("message", "")

        # Detect session type and get appropriate emoji
        session_type = self._detect_session_type(session)
        emoji = self.EMOJIS.get(session_type, self.EMOJIS["session"])

        card = Text()

        # Header line with emoji and description
        if message:
            description = message
        else:
            description = self._truncate_text(goal, self.max_description_length)

        card.append(f"{emoji} ", style="bright_white")
        card.append(description, style="white bold")
        card.append("\n")

        # Details line
        details = Text()
        details.append(f"📍 {timestamp}", style="dim")
        details.append(f" • {open_files} files", style="blue")
        if git_branch:
            details.append(f" • {git_branch}", style="yellow")
        card.append(details)
        card.append("\n")

        # Progress bar (simulated completion based on session metrics)
        completion = self._calculate_session_completion(session)
        progress_chars = "█" * int(completion * 10) + "░" * (10 - int(completion * 10))
        card.append(f"[{progress_chars}] {completion:.0%} complete", style="green")

        return card

    def _group_sessions_by_time(self, sessions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group sessions by time periods for ADHD-friendly organization."""
        now = datetime.now()
        today = now.date()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)

        groups = {
            "Today": [],
            "Yesterday": [],
            "This Week": [],
            "Older": []
        }

        for session in sessions:
            timestamp_str = session.get("timestamp", "")
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                session_date = timestamp.date()

                if session_date == today:
                    groups["Today"].append(session)
                elif session_date == yesterday:
                    groups["Yesterday"].append(session)
                elif session_date > week_ago:
                    groups["This Week"].append(session)
                else:
                    groups["Older"].append(session)
            except (ValueError, AttributeError):
                groups["Older"].append(session)

        return groups

    def _get_time_group_emoji(self, group_name: str) -> str:
        """Get emoji for time group."""
        emojis = {
            "Today": "🔥",
            "Yesterday": "📅",
            "This Week": "📆",
            "Older": "📚"
        }
        return emojis.get(group_name, "📍")

    def _detect_session_type(self, session_data: Dict[str, Any]) -> str:
        """Auto-detect session type from git changes and context."""
        message = session_data.get("message", "").lower()
        git_state = session_data.get("git_state", {})

        # Check message for keywords
        if any(word in message for word in ["fix", "bug", "error", "issue"]):
            return "fix"
        elif any(word in message for word in ["feat", "feature", "add", "new"]):
            return "feature"
        elif any(word in message for word in ["doc", "readme", "guide"]):
            return "docs"
        elif any(word in message for word in ["test", "spec", "coverage"]):
            return "test"
        elif any(word in message for word in ["refactor", "clean", "optimize"]):
            return "refactor"
        elif any(word in message for word in ["config", "setup", "install"]):
            return "config"

        # Check recent files for patterns
        open_files = session_data.get("open_files", [])
        file_extensions = []
        for file_info in open_files:
            if isinstance(file_info, dict):
                path = file_info.get("path", "")
            else:
                path = str(file_info)

            if path:
                ext = Path(path).suffix
                file_extensions.append(ext)

        if any(ext in [".md", ".rst", ".txt"] for ext in file_extensions):
            return "docs"
        elif any("test" in str(f) for f in open_files):
            return "test"

        return "session"  # Default

    def _format_relative_time(self, timestamp_str: Optional[str]) -> str:
        """Format timestamp as relative time (ADHD-friendly)."""
        if not timestamp_str:
            return "unknown time"

        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()

            diff = now - timestamp

            if diff.total_seconds() < 60:
                return "just now"
            elif diff.total_seconds() < 3600:  # Less than 1 hour
                minutes = int(diff.total_seconds() / 60)
                return f"{minutes} min ago"
            elif diff.total_seconds() < 86400:  # Less than 1 day
                hours = int(diff.total_seconds() / 3600)
                return f"{hours}h ago"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            else:
                return timestamp.strftime("%b %d")
        except (ValueError, AttributeError):
            return "unknown time"

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to prevent cognitive overload."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."

    def _calculate_session_completion(self, session: Dict[str, Any]) -> float:
        """Calculate session completion based on available metrics."""
        # This is a heuristic - in reality, completion would be based on actual task progress
        factors = []

        # Factor 1: Has files open (indicates active work)
        open_files = len(session.get("open_files", []))
        if open_files > 0:
            factors.append(min(open_files / 10.0, 1.0))  # Normalize to max 10 files

        # Factor 2: Has goal set
        if session.get("current_goal") and session.get("current_goal") != "No goal set":
            factors.append(0.3)

        # Factor 3: Has message (indicates intentional save)
        if session.get("message"):
            factors.append(0.2)

        # Factor 4: Focus duration
        focus_duration = session.get("focus_duration", 0)
        if focus_duration > 0:
            # Normalize focus duration (25 min = good session)
            factors.append(min(focus_duration / 25.0, 1.0))

        if not factors:
            return 0.5  # Default middle completion

        return min(sum(factors) / len(factors), 1.0)