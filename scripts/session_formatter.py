"""Formatting helpers for ADHD-friendly session command output."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List


class SessionFormatter:
    """Format session command responses for humans and tests."""

    def format_save_confirmation(self, session_data: Dict) -> str:
        session_id = str(session_data.get("session_id", "unknown"))
        short_id = session_id[:10]
        message = session_data.get("message", "Session saved")
        files = session_data.get("open_files", []) or []
        return (
            "💾 Session Saved Successfully!\n"
            f"ID: {short_id}\n"
            f"{message}\n"
            f"{len(files)} files saved"
        )

    def format_session_gallery(self, sessions: List[Dict]) -> str:
        if not sessions:
            return "No sessions found\nUse '/save' to create your first session!"
        lines = ["Recent Sessions"]
        for session in sessions:
            when = self._format_relative_time(str(session.get("timestamp", "")))
            msg = session.get("message") or session.get("current_goal") or "No message"
            lines.append(f"- {session.get('id', 'unknown')[:8]} ({when}): {msg}")
        return "\n".join(lines)

    def _detect_session_type(self, session_data: Dict) -> str:
        text = f"{session_data.get('message', '')} {session_data.get('current_goal', '')}".lower()
        if any(word in text for word in ("fix", "bug", "error")):
            return "bugfix"
        if any(word in text for word in ("feature", "implement", "add")):
            return "feature"
        return "general"

    def _group_sessions_by_time(self, sessions: List[Dict]) -> Dict[str, List[Dict]]:
        grouped: Dict[str, List[Dict]] = {
            "Today": [],
            "Yesterday": [],
            "This Week": [],
            "Older": [],
        }
        now = datetime.now()
        for session in sessions:
            ts = self._parse_ts(str(session.get("timestamp", "")))
            if ts is None:
                grouped["Older"].append(session)
                continue
            delta_days = (now.date() - ts.date()).days
            if delta_days == 0:
                grouped["Today"].append(session)
            elif delta_days == 1:
                grouped["Yesterday"].append(session)
            elif delta_days <= 7:
                grouped["This Week"].append(session)
            else:
                grouped["Older"].append(session)
        return grouped

    def _format_relative_time(self, timestamp: str) -> str:
        ts = self._parse_ts(timestamp)
        if ts is None:
            return "unknown"
        delta = datetime.now() - ts
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return "just now"
        if seconds < 3600:
            return f"{seconds // 60} min ago"
        if seconds < 86400:
            return f"{seconds // 3600} h ago"
        return f"{seconds // 86400} d ago"

    def _calculate_session_completion(self, session: Dict) -> float:
        score = 0.0
        if session.get("current_goal"):
            score += 0.25
        if session.get("message"):
            score += 0.2
        if session.get("open_files"):
            score += 0.25
        if (session.get("focus_duration") or 0) > 0:
            score += 0.3
        return min(max(score, 0.0), 1.0)

    @staticmethod
    def _parse_ts(timestamp: str) -> datetime | None:
        if not timestamp:
            return None
        try:
            return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None
