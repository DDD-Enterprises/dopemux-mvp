#!/usr/bin/env python3
"""
Dopemux Slash Commands for Claude Code Integration.

Provides slash command functionality for health monitoring and service management
that can be called directly from Claude Code sessions.
"""

import sys
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, Any, Optional, List

# Import Dopemux modules with proper error handling
def setup_dopemux_imports():
    """Setup Dopemux imports with proper path handling."""
    project_root = Path(__file__).parent.parent
    src_dir = project_root / "src"

    if not src_dir.exists():
        raise ImportError(f"Source directory not found: {src_dir}")

    # Only add to path if not already there
    src_str = str(src_dir)
    if src_str not in sys.path:
        sys.path.insert(0, src_str)

    try:
        from dopemux.health import HealthChecker, HealthStatus
        from dopemux.adhd.context_manager import ContextManager
        return HealthChecker, HealthStatus, ContextManager
    except ImportError as e:
        # Clean up path on failure
        if src_str in sys.path:
            sys.path.remove(src_str)
        raise ImportError(f"Could not import Dopemux modules: {e}")

try:
    HealthChecker, HealthStatus, ContextManager = setup_dopemux_imports()
except ImportError as e:
    print(f"Error: {e}")
    print("Make sure you're running this from the Dopemux project root")
    sys.exit(1)

# Import our session formatter
try:
    from session_formatter import SessionFormatter
except ImportError:
    # Fallback if running from different directory
    sys.path.insert(0, str(Path(__file__).parent))
    from session_formatter import SessionFormatter


class SlashCommandProcessor:
    """Process slash commands for Claude Code integration."""

    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.health_checker = HealthChecker(self.project_path)
        self.context_manager = ContextManager(self.project_path)
        self.session_formatter = SessionFormatter()

    def process_command(self, command: str, args: list = None) -> Dict[str, Any]:
        """Process a slash command and return structured results."""
        args = args or []

        try:
            if command == "health":
                return self._handle_health_command(args)
            elif command == "health-quick":
                return self._handle_quick_health()
            elif command == "health-fix":
                return self._handle_health_fix()
            elif command == "mcp-status":
                return self._handle_mcp_status()
            elif command == "docker-status":
                return self._handle_docker_status()
            elif command == "system-status":
                return self._handle_system_status()
            elif command == "adhd-status":
                return self._handle_adhd_status()
            # Session Management Commands
            elif command == "save":
                return self._handle_save_session(args)
            elif command == "restore":
                return self._handle_restore_session(args)
            elif command == "sessions":
                return self._handle_list_sessions(args)
            elif command == "session-details":
                return self._handle_session_details(args)
            else:
                return {
                    "success": False,
                    "error": f"Unknown command: {command}",
                    "available_commands": [
                        "health", "health-quick", "health-fix",
                        "mcp-status", "docker-status", "system-status", "adhd-status",
                        "save", "restore", "sessions", "session-details"
                    ]
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    def _handle_health_command(self, args: list) -> Dict[str, Any]:
        """Handle comprehensive health check command."""
        detailed = "--detailed" in args or "-d" in args

        results = self.health_checker.check_all(detailed=detailed)

        # Convert to serializable format
        health_data = {}
        overall_status = "healthy"

        for service_name, health in results.items():
            status_name, emoji, color = health.status.value

            health_data[service_name] = {
                "status": status_name,
                "emoji": emoji,
                "message": health.message,
                "response_time_ms": health.response_time_ms,
                "details": health.details if detailed else {}
            }

            # Determine overall status
            if health.status == HealthStatus.CRITICAL:
                overall_status = "critical"
            elif health.status == HealthStatus.WARNING and overall_status != "critical":
                overall_status = "warning"

        # Format for Claude Code display
        status_emoji = "🔴" if overall_status == "critical" else "🟡" if overall_status == "warning" else "🟢"

        return {
            "success": True,
            "command": "health",
            "overall_status": overall_status,
            "overall_emoji": status_emoji,
            "services": health_data,
            "summary": self._generate_health_summary(health_data),
            "timestamp": results[list(results.keys())[0]].last_check.isoformat() if results else None
        }

    def _handle_quick_health(self) -> Dict[str, Any]:
        """Handle quick health status check."""
        quick_status = self.health_checker.quick_status()

        return {
            "success": True,
            "command": "health-quick",
            "status": quick_status,
            "formatted": "\\n".join([f"{name}: {status}" for name, status in quick_status.items()])
        }

    def _handle_health_fix(self) -> Dict[str, Any]:
        """Handle automatic health fix attempt."""
        restarted = self.health_checker.restart_unhealthy_services()

        return {
            "success": True,
            "command": "health-fix",
            "restarted_services": restarted,
            "message": f"Restarted {len(restarted)} services" if restarted else "No services needed restart"
        }

    def _handle_mcp_status(self) -> Dict[str, Any]:
        """Handle MCP servers status check."""
        mcp_health = self.health_checker._check_mcp_servers(detailed=True)

        return {
            "success": True,
            "command": "mcp-status",
            "status": mcp_health.status.value[0],
            "emoji": mcp_health.status.value[1],
            "message": mcp_health.message,
            "details": mcp_health.details
        }

    def _handle_docker_status(self) -> Dict[str, Any]:
        """Handle Docker services status check."""
        docker_health = self.health_checker._check_docker_services(detailed=True)

        return {
            "success": True,
            "command": "docker-status",
            "status": docker_health.status.value[0],
            "emoji": docker_health.status.value[1],
            "message": docker_health.message,
            "details": docker_health.details
        }

    def _handle_system_status(self) -> Dict[str, Any]:
        """Handle system resources status check."""
        system_health = self.health_checker._check_system_resources(detailed=True)

        return {
            "success": True,
            "command": "system-status",
            "status": system_health.status.value[0],
            "emoji": system_health.status.value[1],
            "message": system_health.message,
            "details": system_health.details
        }

    def _handle_adhd_status(self) -> Dict[str, Any]:
        """Handle ADHD features status check."""
        adhd_health = self.health_checker._check_adhd_features(detailed=True)

        return {
            "success": True,
            "command": "adhd-status",
            "status": adhd_health.status.value[0],
            "emoji": adhd_health.status.value[1],
            "message": adhd_health.message,
            "details": adhd_health.details
        }

    # Session Management Commands

    def _handle_save_session(self, args: List[str]) -> Dict[str, Any]:
        """Handle session save command with ADHD-friendly output."""
        try:
            # Parse arguments
            message = None
            force = False
            tags = []

            i = 0
            while i < len(args):
                if args[i] in ["--message", "-m"] and i + 1 < len(args):
                    message = args[i + 1]
                    i += 2
                elif args[i] in ["--force", "-f"]:
                    force = True
                    i += 1
                elif args[i] in ["--tag", "-t"] and i + 1 < len(args):
                    tags.append(args[i + 1])
                    i += 2
                else:
                    i += 1

            # Save session using context manager
            session_id = self.context_manager.save_context(message=message, force=force)

            # Get session data for formatting
            sessions = self.context_manager.list_sessions(limit=1)
            session_data = sessions[0] if sessions else {"session_id": session_id}

            # Add tags if provided
            if tags:
                session_data["tags"] = tags

            return {
                "success": True,
                "command": "save",
                "session_id": session_id,
                "session_data": session_data,
                "formatted_output": self.session_formatter.format_save_confirmation(session_data)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": "save"
            }

    def _handle_restore_session(self, args: List[str]) -> Dict[str, Any]:
        """Handle session restore command with preview."""
        try:
            session_id = None
            preview_only = "--preview" in args or "-p" in args

            # Parse session ID
            for arg in args:
                if not arg.startswith("-"):
                    session_id = arg
                    break

            if session_id:
                # Restore specific session
                context_data = self.context_manager.restore_session(session_id)
                if not context_data:
                    return {
                        "success": False,
                        "error": f"Session {session_id} not found",
                        "command": "restore"
                    }
            else:
                # Restore latest session
                context_data = self.context_manager.restore_latest()
                if not context_data:
                    return {
                        "success": False,
                        "error": "No sessions found to restore",
                        "command": "restore"
                    }

            if preview_only:
                formatted_output = self.session_formatter.format_restore_preview(context_data)
            else:
                # Show confirmation after restore
                formatted_output = f"✅ **Session Restored Successfully!**\\n\\n"
                formatted_output += f"🎯 **Goal**: {context_data.get('current_goal', 'No goal set')}\\n"
                formatted_output += f"📁 **Files**: {len(context_data.get('open_files', []))} files restored\\n"
                formatted_output += f"⏰ **From**: {context_data.get('timestamp', 'unknown time')}"

            return {
                "success": True,
                "command": "restore",
                "session_data": context_data,
                "formatted_output": formatted_output
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": "restore"
            }

    def _handle_list_sessions(self, args: List[str]) -> Dict[str, Any]:
        """Handle session listing with visual gallery."""
        try:
            limit = 10
            search_term = None
            tag_filter = None

            # Parse arguments
            i = 0
            while i < len(args):
                if args[i] in ["--limit", "-l"] and i + 1 < len(args):
                    try:
                        limit = int(args[i + 1])
                    except ValueError:
                        pass
                    i += 2
                elif args[i] in ["--search", "-s"] and i + 1 < len(args):
                    search_term = args[i + 1]
                    i += 2
                elif args[i] in ["--tag", "-t"] and i + 1 < len(args):
                    tag_filter = args[i + 1]
                    i += 2
                else:
                    i += 1

            # Get sessions from context manager
            sessions = self.context_manager.list_sessions(limit=limit * 2)  # Get more for filtering

            # Apply search filter
            if search_term:
                filtered_sessions = []
                search_lower = search_term.lower()
                for session in sessions:
                    if (search_lower in session.get("current_goal", "").lower() or
                        search_lower in session.get("message", "").lower()):
                        filtered_sessions.append(session)
                sessions = filtered_sessions[:limit]

            # Apply tag filter (if we had tags implemented)
            if tag_filter:
                # This would filter by tags when we implement tagging
                pass

            # Format using session formatter
            formatted_output = self.session_formatter.format_session_gallery(sessions, limit)

            return {
                "success": True,
                "command": "sessions",
                "sessions": sessions,
                "formatted_output": formatted_output
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": "sessions"
            }

    def _handle_session_details(self, args: List[str]) -> Dict[str, Any]:
        """Handle detailed session view."""
        try:
            if not args:
                return {
                    "success": False,
                    "error": "Session ID required",
                    "command": "session-details"
                }

            session_id = args[0]
            sessions = self.context_manager.list_sessions(limit=50)

            # Find matching session
            session_data = None
            for session in sessions:
                if session["id"].startswith(session_id):
                    session_data = session
                    break

            if not session_data:
                return {
                    "success": False,
                    "error": f"Session {session_id} not found",
                    "command": "session-details"
                }

            formatted_output = self.session_formatter.format_session_details(session_data)

            return {
                "success": True,
                "command": "session-details",
                "session_data": session_data,
                "formatted_output": formatted_output
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": "session-details"
            }

    def _generate_health_summary(self, health_data: Dict[str, Any]) -> str:
        """Generate a human-readable health summary."""
        healthy_count = sum(1 for h in health_data.values() if h["status"] == "healthy")
        warning_count = sum(1 for h in health_data.values() if h["status"] == "warning")
        critical_count = sum(1 for h in health_data.values() if h["status"] == "critical")

        summary_parts = []

        if healthy_count > 0:
            summary_parts.append(f"🟢 {healthy_count} healthy")
        if warning_count > 0:
            summary_parts.append(f"🟡 {warning_count} warnings")
        if critical_count > 0:
            summary_parts.append(f"🔴 {critical_count} critical")

        return " • ".join(summary_parts)


def format_for_claude_code(result: Dict[str, Any]) -> str:
    """Format command results for Claude Code display."""
    if not result["success"]:
        return f"❌ **Error**: {result['error']}"

    command = result["command"]

    if command == "health":
        lines = [
            f"🏥 **Dopemux Health Check** {result['overall_emoji']}",
            "",
            f"**Overall Status**: {result['overall_status'].title()}",
            f"**Summary**: {result['summary']}",
            ""
        ]

        for service_name, health in result["services"].items():
            service_display = service_name.replace('_', ' ').title()
            lines.append(f"{health['emoji']} **{service_display}**: {health['message']}")

        return "\\n".join(lines)

    elif command == "health-quick":
        return f"🏥 **Quick Health**: \\n{result['formatted']}"

    elif command == "health-fix":
        if result["restarted_services"]:
            services = ", ".join(result["restarted_services"])
            return f"🔧 **Health Fix**: Restarted {services}"
        else:
            return "🔧 **Health Fix**: No services needed restart"

    elif command in ["mcp-status", "docker-status", "system-status", "adhd-status"]:
        service_name = command.replace("-", " ").title()
        return f"{result['emoji']} **{service_name}**: {result['message']}"

    # Session Management Commands
    elif command in ["save", "restore", "sessions", "session-details"]:
        if result.get("formatted_output"):
            return result["formatted_output"]
        else:
            # Fallback formatting for session commands
            if command == "save":
                return f"💾 **Session Saved**: {result.get('session_id', 'unknown')[:8]}"
            elif command == "restore":
                return f"🔄 **Session Restored**: {result.get('session_data', {}).get('current_goal', 'Unknown goal')}"
            elif command == "sessions":
                session_count = len(result.get('sessions', []))
                return f"📚 **Found {session_count} sessions**"
            elif command == "session-details":
                return f"📍 **Session Details**: {result.get('session_data', {}).get('current_goal', 'Unknown')}"

    return json.dumps(result, indent=2)


def main():
    """Main entry point for slash command processing."""
    parser = argparse.ArgumentParser(description="Dopemux Slash Commands")
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("args", nargs="*", help="Command arguments")
    parser.add_argument("--format", choices=["json", "claude"], default="claude",
                       help="Output format")
    parser.add_argument("--project-path", type=Path, help="Project path")

    # Parse known args to handle session command arguments properly
    args, unknown = parser.parse_known_args()

    # Combine parsed args with unknown args for command processing
    all_args = args.args + unknown

    processor = SlashCommandProcessor(args.project_path)
    result = processor.process_command(args.command, all_args)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        # For session commands, use the Rich formatted output directly
        session_commands = ["save", "restore", "sessions", "session-details"]
        if result.get("formatted_output") and any(cmd in args.command for cmd in session_commands):
            from rich.console import Console
            console = Console()

            # Check if it's a Rich object
            if hasattr(result["formatted_output"], '__rich_console__') or hasattr(result["formatted_output"], '__rich__'):
                console.print(result["formatted_output"])
            else:
                # Fallback to regular formatting
                print(format_for_claude_code(result))
        else:
            print(format_for_claude_code(result))


if __name__ == "__main__":
    main()