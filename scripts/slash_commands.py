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
from typing import Dict, Any, Optional

# Add the src directory to the path so we can import Dopemux modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from dopemux.health import HealthChecker, HealthStatus
except ImportError as e:
    print(f"Error: Could not import Dopemux modules: {e}")
    print("Make sure you're running this from the Dopemux project root")
    sys.exit(1)


class SlashCommandProcessor:
    """Process slash commands for Claude Code integration."""

    def __init__(self, project_path: Optional[Path] = None):
        self.project_path = project_path or Path.cwd()
        self.health_checker = HealthChecker(self.project_path)

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
            else:
                return {
                    "success": False,
                    "error": f"Unknown command: {command}",
                    "available_commands": [
                        "health", "health-quick", "health-fix",
                        "mcp-status", "docker-status", "system-status", "adhd-status"
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

    return json.dumps(result, indent=2)


def main():
    """Main entry point for slash command processing."""
    parser = argparse.ArgumentParser(description="Dopemux Slash Commands")
    parser.add_argument("command", help="Command to execute")
    parser.add_argument("args", nargs="*", help="Command arguments")
    parser.add_argument("--format", choices=["json", "claude"], default="claude",
                       help="Output format")
    parser.add_argument("--project-path", type=Path, help="Project path")

    args = parser.parse_args()

    processor = SlashCommandProcessor(args.project_path)
    result = processor.process_command(args.command, args.args)

    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(format_for_claude_code(result))


if __name__ == "__main__":
    main()