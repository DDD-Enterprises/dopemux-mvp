"""Slash command processor for session workflows."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from dopemux.adhd.context_manager import ContextManager

from session_formatter import SessionFormatter


class SlashCommandProcessor:
    """Process a narrow set of session-oriented slash commands."""

    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.context_manager = ContextManager(self.project_root)
        self.formatter = SessionFormatter()
        self._commands = {
            "save": self._cmd_save,
            "sessions": self._cmd_sessions,
            "restore": self._cmd_restore,
            "session-details": self._cmd_session_details,
        }

    def process_command(self, command: str, args: Optional[List[str]] = None) -> Dict:
        args = args or []
        handler = self._commands.get(command)
        if handler is None:
            return {
                "success": False,
                "error": f"Unknown command: {command}",
                "available_commands": sorted(self._commands.keys()),
            }
        return handler(args)

    def _cmd_save(self, args: List[str]) -> Dict:
        message = self._get_opt(args, "--message")
        tags = self._get_all_opts(args, "--tag")

        session_id = self.context_manager.save_context(message=message, force=True)
        if tags:
            self.context_manager.add_session_tags(session_id, tags)

        session_data = self.context_manager.restore_session(session_id) or {}
        session_data["session_id"] = session_id
        if tags:
            session_data["tags"] = tags
        formatted = self.formatter.format_save_confirmation(session_data)
        return {
            "success": True,
            "command": "save",
            "session_id": session_id,
            "session_data": session_data,
            "formatted_output": formatted,
        }

    def _cmd_sessions(self, args: List[str]) -> Dict:
        search = self._get_opt(args, "--search")
        limit_raw = self._get_opt(args, "--limit")
        limit = int(limit_raw) if limit_raw and limit_raw.isdigit() else 20
        sessions = self.context_manager.list_sessions(limit=limit)
        if search:
            needle = search.lower()
            sessions = [
                s
                for s in sessions
                if needle in str(s.get("message", "")).lower()
                or needle in str(s.get("current_goal", "")).lower()
            ]
        for session in sessions:
            session["tags"] = self.context_manager.get_session_tags(str(session.get("id", "")))
        return {
            "success": True,
            "command": "sessions",
            "sessions": sessions,
            "formatted_output": self.formatter.format_session_gallery(sessions),
        }

    def _cmd_restore(self, args: List[str]) -> Dict:
        preview = "--preview" in args
        target = next((a for a in args if not a.startswith("--")), None)

        if target:
            session = self._find_session_by_prefix(target)
            if session is None:
                return {"success": False, "error": f"Session '{target}' not found"}
            session_id = session["id"]
        else:
            latest = self.context_manager.list_sessions(limit=1)
            if not latest:
                return {"success": False, "error": "No sessions found"}
            session_id = latest[0]["id"]

        if preview:
            return {
                "success": True,
                "command": "restore",
                "session_id": session_id,
                "formatted_output": f"Ready to Restore Session: {session_id}",
            }

        restored = self.context_manager.restore_session(session_id)
        if restored is None:
            return {"success": False, "error": f"Session '{session_id}' not found"}
        return {
            "success": True,
            "command": "restore",
            "session_id": session_id,
            "session_data": restored,
            "formatted_output": f"Restored session: {session_id}",
        }

    def _cmd_session_details(self, args: List[str]) -> Dict:
        if not args:
            return {"success": False, "error": "Session ID required"}
        session = self._find_session_by_prefix(args[0])
        if session is None:
            return {"success": False, "error": f"Session '{args[0]}' not found"}
        details = self.context_manager.restore_session(session["id"]) or {}
        details["session_id"] = session["id"]
        details["tags"] = self.context_manager.get_session_tags(session["id"])
        return {
            "success": True,
            "command": "session-details",
            "session_data": details,
            "formatted_output": self.formatter.format_save_confirmation(details),
        }

    def _find_session_by_prefix(self, session_id_prefix: str) -> Optional[Dict]:
        sessions = self.context_manager.list_sessions(limit=200)
        for session in sessions:
            if str(session.get("id", "")).startswith(session_id_prefix):
                return session
        return None

    @staticmethod
    def _get_opt(args: List[str], name: str) -> Optional[str]:
        for i, arg in enumerate(args):
            if arg == name and i + 1 < len(args):
                return args[i + 1]
        return None

    @staticmethod
    def _get_all_opts(args: List[str], name: str) -> List[str]:
        values: List[str] = []
        for i, arg in enumerate(args):
            if arg == name and i + 1 < len(args):
                values.append(args[i + 1])
        return values
