#!/usr/bin/env python3
"""
Dopemux Health Checker - Comprehensive health monitoring system.

Provides health monitoring for Dopemux, Claude Code, MCP servers, and Docker-based services
with ADHD-optimized reporting and slash command integration.
"""

import json
import time
import psutil
import subprocess
import docker
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn


class HealthStatus(Enum):
    """Health status levels with ADHD-friendly indicators."""
    HEALTHY = ("healthy", "🟢", "green")
    WARNING = ("warning", "🟡", "yellow")
    CRITICAL = ("critical", "🔴", "red")
    UNKNOWN = ("unknown", "⚪", "dim")


@dataclass
class ServiceHealth:
    """Health information for a service."""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any]
    response_time_ms: float = 0.0
    last_check: Optional[datetime] = None


class HealthChecker:
    """
    Comprehensive health checker for Dopemux ecosystem.

    Monitors:
    - Dopemux core services
    - Claude Code integration
    - MCP servers (both Python and Docker-based)
    - System resources
    - ADHD feature effectiveness
    """

    def __init__(self, project_path: Optional[Path] = None, console: Optional[Console] = None):
        self.project_path = project_path or Path.cwd()
        self.console = console or Console()

        # Initialize Docker client (optional)
        try:
            self.docker_client = docker.from_env()
        except Exception:
            self.docker_client = None

        # Health check registry
        self.checks = {
            'dopemux_core': self._check_dopemux_core,
            'claude_code': self._check_claude_code,
            'mcp_servers': self._check_mcp_servers,
            'docker_services': self._check_docker_services,
            'system_resources': self._check_system_resources,
            'adhd_features': self._check_adhd_features,
        }

    def check_all(self, detailed: bool = False) -> Dict[str, ServiceHealth]:
        """Run all health checks and return results."""
        results = {}

        for check_name, check_func in self.checks.items():
            start_time = time.time()
            try:
                result = check_func(detailed=detailed)
                result.response_time_ms = (time.time() - start_time) * 1000
                result.last_check = datetime.now()
                results[check_name] = result
            except Exception as e:
                results[check_name] = ServiceHealth(
                    name=check_name,
                    status=HealthStatus.CRITICAL,
                    message=f"Health check failed: {e}",
                    details={"error": str(e)},
                    response_time_ms=(time.time() - start_time) * 1000,
                    last_check=datetime.now()
                )

        return results

    def quick_status(self) -> Dict[str, str]:
        """Quick status check for slash commands."""
        results = self.check_all(detailed=False)

        status_summary = {}
        for name, health in results.items():
            emoji, _, _ = health.status.value
            status_summary[name] = f"{emoji} {health.message}"

        return status_summary

    def _check_dopemux_core(self, detailed: bool = False) -> ServiceHealth:
        """Check Dopemux core service health."""
        details = {}

        try:
            # Check if project is initialized
            dopemux_dir = self.project_path / '.dopemux'
            claude_dir = self.project_path / '.claude'

            if not dopemux_dir.exists():
                return ServiceHealth(
                    name="dopemux_core",
                    status=HealthStatus.CRITICAL,
                    message="Dopemux not initialized",
                    details={"suggestion": "Run 'dopemux init' to initialize"}
                )

            # Check configuration files
            config_files = [
                dopemux_dir / 'config.json',
                claude_dir / 'config.json',
                claude_dir / 'claude.md'
            ]

            missing_files = [f for f in config_files if not f.exists()]

            if missing_files:
                details["missing_files"] = [str(f) for f in missing_files]
                status = HealthStatus.WARNING
                message = f"Missing {len(missing_files)} config files"
            else:
                status = HealthStatus.HEALTHY
                message = "Core configuration valid"

            if detailed:
                details.update({
                    "project_path": str(self.project_path),
                    "dopemux_dir_exists": dopemux_dir.exists(),
                    "claude_dir_exists": claude_dir.exists(),
                    "config_files_status": {str(f): f.exists() for f in config_files}
                })

            return ServiceHealth(
                name="dopemux_core",
                status=status,
                message=message,
                details=details
            )

        except Exception as e:
            return ServiceHealth(
                name="dopemux_core",
                status=HealthStatus.CRITICAL,
                message=f"Core check failed: {e}",
                details={"error": str(e)}
            )

    def _check_claude_code(self, detailed: bool = False) -> ServiceHealth:
        """Check Claude Code integration health."""
        details = {}

        try:
            # Check for Claude Code processes
            claude_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline') or [])
                    if 'claude' in cmdline.lower() and 'code' in cmdline.lower():
                        claude_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'cmdline': cmdline
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if not claude_processes:
                status = HealthStatus.WARNING
                message = "Claude Code not running"
                details["suggestion"] = "Run 'dopemux start' to launch Claude Code"
            else:
                status = HealthStatus.HEALTHY
                message = f"Claude Code running ({len(claude_processes)} processes)"

            if detailed:
                details["processes"] = claude_processes

            return ServiceHealth(
                name="claude_code",
                status=status,
                message=message,
                details=details
            )

        except Exception as e:
            return ServiceHealth(
                name="claude_code",
                status=HealthStatus.CRITICAL,
                message=f"Claude Code check failed: {e}",
                details={"error": str(e)}
            )

    def _check_mcp_servers(self, detailed: bool = False) -> ServiceHealth:
        """Check MCP server health."""
        details = {}

        try:
            # Check for MCP server processes
            mcp_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'status']):
                try:
                    cmdline = ' '.join(proc.info.get('cmdline') or [])
                    if 'mcp-server' in cmdline or 'sequential-thinking' in cmdline:
                        memory_info = proc.memory_info()
                        mcp_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'status': proc.info['status'],
                            'memory_mb': round(memory_info.rss / 1024 / 1024, 2),
                            'cpu_percent': round(proc.cpu_percent(), 2)
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Try to health check our custom MCP server
            sequential_thinking_health = self._check_sequential_thinking_server()

            if not mcp_processes:
                status = HealthStatus.WARNING
                message = "No MCP servers running"
            elif sequential_thinking_health and sequential_thinking_health.get('status') == 'healthy':
                status = HealthStatus.HEALTHY
                message = f"MCP servers healthy ({len(mcp_processes)} running)"
            else:
                status = HealthStatus.WARNING
                message = f"MCP servers running but issues detected"

            details.update({
                "processes_count": len(mcp_processes),
                "sequential_thinking": sequential_thinking_health or {"status": "not_found"}
            })

            if detailed:
                details["processes"] = mcp_processes

            return ServiceHealth(
                name="mcp_servers",
                status=status,
                message=message,
                details=details
            )

        except Exception as e:
            return ServiceHealth(
                name="mcp_servers",
                status=HealthStatus.CRITICAL,
                message=f"MCP server check failed: {e}",
                details={"error": str(e)}
            )

    def _check_sequential_thinking_server(self) -> Optional[Dict[str, Any]]:
        """Check our custom sequential thinking MCP server."""
        try:
            # Try to run the health monitor script
            script_path = Path(__file__).parent.parent.parent / "docker" / "mcp-servers" / "mcp-server-mas-sequential-thinking" / "scripts" / "health_monitor.py"

            if script_path.exists():
                result = subprocess.run([
                    'python', str(script_path), 'health'
                ], capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    return json.loads(result.stdout)

        except Exception:
            pass

        return None

    def _check_docker_services(self, detailed: bool = False) -> ServiceHealth:
        """Check Docker-based MCP services."""
        details = {}

        if not self.docker_client:
            return ServiceHealth(
                name="docker_services",
                status=HealthStatus.WARNING,
                message="Docker not available",
                details={"suggestion": "Install Docker for container-based MCP servers"}
            )

        try:
            # Check for MCP-related containers
            mcp_containers = []
            for container in self.docker_client.containers.list(all=True):
                if 'mcp' in container.name.lower() or 'mcp' in str(container.image.tags):
                    mcp_containers.append({
                        'name': container.name,
                        'status': container.status,
                        'image': str(container.image.tags[0]) if container.image.tags else 'unknown',
                        'ports': container.ports
                    })

            if not mcp_containers:
                status = HealthStatus.HEALTHY
                message = "No Docker MCP services (normal)"
            else:
                running_containers = [c for c in mcp_containers if c['status'] == 'running']
                if len(running_containers) == len(mcp_containers):
                    status = HealthStatus.HEALTHY
                    message = f"All Docker MCP services healthy ({len(running_containers)})"
                else:
                    status = HealthStatus.WARNING
                    message = f"Some Docker MCP services down ({len(running_containers)}/{len(mcp_containers)})"

            details["containers_count"] = len(mcp_containers)
            details["running_count"] = len([c for c in mcp_containers if c['status'] == 'running'])

            if detailed:
                details["containers"] = mcp_containers

            return ServiceHealth(
                name="docker_services",
                status=status,
                message=message,
                details=details
            )

        except Exception as e:
            return ServiceHealth(
                name="docker_services",
                status=HealthStatus.CRITICAL,
                message=f"Docker services check failed: {e}",
                details={"error": str(e)}
            )

    def _check_system_resources(self, detailed: bool = False) -> ServiceHealth:
        """Check system resource health."""
        details = {}

        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Determine status based on thresholds
            issues = []
            if cpu_percent > 80:
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            if memory.percent > 85:
                issues.append(f"High memory usage: {memory.percent:.1f}%")
            if disk.percent > 90:
                issues.append(f"Low disk space: {disk.percent:.1f}% used")

            if issues:
                status = HealthStatus.WARNING
                message = f"Resource issues: {', '.join(issues)}"
            else:
                status = HealthStatus.HEALTHY
                message = "System resources healthy"

            details.update({
                "cpu_percent": round(cpu_percent, 1),
                "memory_percent": round(memory.percent, 1),
                "memory_available_gb": round(memory.available / 1024**3, 2),
                "disk_percent": round(disk.percent, 1),
                "disk_free_gb": round(disk.free / 1024**3, 2)
            })

            if detailed:
                details.update({
                    "cpu_count": psutil.cpu_count(),
                    "memory_total_gb": round(memory.total / 1024**3, 2),
                    "disk_total_gb": round(disk.total / 1024**3, 2)
                })

            return ServiceHealth(
                name="system_resources",
                status=status,
                message=message,
                details=details
            )

        except Exception as e:
            return ServiceHealth(
                name="system_resources",
                status=HealthStatus.CRITICAL,
                message=f"System resources check failed: {e}",
                details={"error": str(e)}
            )

    def _check_adhd_features(self, detailed: bool = False) -> ServiceHealth:
        """Check ADHD feature effectiveness."""
        details = {}

        try:
            # Check if ADHD features are configured
            dopemux_dir = self.project_path / '.dopemux'

            if not dopemux_dir.exists():
                return ServiceHealth(
                    name="adhd_features",
                    status=HealthStatus.WARNING,
                    message="ADHD features not initialized",
                    details={"suggestion": "Run 'dopemux init' to set up ADHD features"}
                )

            # Check for attention monitoring data
            attention_file = dopemux_dir / 'attention.json'
            context_file = dopemux_dir / 'context.json'

            features_active = []
            features_inactive = []

            if attention_file.exists():
                features_active.append("attention_monitoring")
                try:
                    with open(attention_file) as f:
                        attention_data = json.load(f)
                        details["last_attention_check"] = attention_data.get("last_check")
                        details["focus_score"] = attention_data.get("focus_score", 0)
                except Exception:
                    features_inactive.append("attention_monitoring")
            else:
                features_inactive.append("attention_monitoring")

            if context_file.exists():
                features_active.append("context_preservation")
                try:
                    with open(context_file) as f:
                        context_data = json.load(f)
                        details["last_context_save"] = context_data.get("last_save")
                        details["sessions_count"] = len(context_data.get("sessions", []))
                except Exception:
                    features_inactive.append("context_preservation")
            else:
                features_inactive.append("context_preservation")

            # Determine status
            if len(features_active) == 0:
                status = HealthStatus.WARNING
                message = "ADHD features not active"
            elif len(features_inactive) == 0:
                status = HealthStatus.HEALTHY
                message = "All ADHD features active"
            else:
                status = HealthStatus.WARNING
                message = f"Some ADHD features inactive ({len(features_inactive)})"

            details.update({
                "features_active": features_active,
                "features_inactive": features_inactive,
                "adhd_optimizations_enabled": len(features_active) > 0
            })

            return ServiceHealth(
                name="adhd_features",
                status=status,
                message=message,
                details=details
            )

        except Exception as e:
            return ServiceHealth(
                name="adhd_features",
                status=HealthStatus.CRITICAL,
                message=f"ADHD features check failed: {e}",
                details={"error": str(e)}
            )

    def display_health_report(self, results: Dict[str, ServiceHealth], detailed: bool = False):
        """Display health report with ADHD-friendly formatting."""

        # Overall status
        critical_count = sum(1 for h in results.values() if h.status == HealthStatus.CRITICAL)
        warning_count = sum(1 for h in results.values() if h.status == HealthStatus.WARNING)
        healthy_count = sum(1 for h in results.values() if h.status == HealthStatus.HEALTHY)

        if critical_count > 0:
            overall_status = "🔴 CRITICAL"
            overall_color = "red"
        elif warning_count > 0:
            overall_status = "🟡 WARNING"
            overall_color = "yellow"
        else:
            overall_status = "🟢 HEALTHY"
            overall_color = "green"

        # Main status table
        table = Table(title=f"🧠 Dopemux Health Status - {overall_status}")
        table.add_column("Service", style="cyan", width=20)
        table.add_column("Status", style="bold", width=12)
        table.add_column("Message", style="white", width=40)
        table.add_column("Response", justify="right", style="dim", width=10)

        for service_name, health in results.items():
            emoji, _, color = health.status.value

            table.add_row(
                service_name.replace('_', ' ').title(),
                f"{emoji} {health.status.value[0].title()}",
                health.message,
                f"{health.response_time_ms:.0f}ms"
            )

        self.console.print(table)

        # Detailed information
        if detailed:
            for service_name, health in results.items():
                if health.details:
                    details_table = Table(title=f"📋 {service_name.replace('_', ' ').title()} Details")
                    details_table.add_column("Property", style="cyan")
                    details_table.add_column("Value", style="green")

                    for key, value in health.details.items():
                        if isinstance(value, (dict, list)):
                            value_str = json.dumps(value, indent=2) if len(str(value)) < 100 else f"{type(value).__name__}({len(value)} items)"
                        else:
                            value_str = str(value)

                        details_table.add_row(key.replace('_', ' ').title(), value_str)

                    self.console.print(details_table)

        # Summary panel
        summary_text = f"""
🎯 **Health Summary**
• Healthy: {healthy_count} services
• Warnings: {warning_count} services
• Critical: {critical_count} services

💡 **Quick Actions**
• Run `dopemux start` if Claude Code isn't running
• Use `dopemux init` for uninitialized projects
• Check `dopemux status` for detailed ADHD metrics
        """

        self.console.print(Panel(
            summary_text.strip(),
            title="🏥 Health Summary",
            border_style=overall_color
        ))

    def format_for_slash_command(self, results: Dict[str, ServiceHealth]) -> str:
        """Format health results for slash command display."""
        lines = ["🏥 **Dopemux Health Check**", ""]

        for service_name, health in results.items():
            emoji, _, _ = health.status.value
            service_display = service_name.replace('_', ' ').title()
            lines.append(f"{emoji} **{service_display}**: {health.message}")

        return "\\n".join(lines)

    def restart_unhealthy_services(self) -> List[str]:
        """Attempt to restart unhealthy services."""
        results = self.check_all()
        restarted = []

        for service_name, health in results.items():
            if health.status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
                if service_name == 'mcp_servers':
                    try:
                        # Try to restart MCP server
                        script_path = Path(__file__).parent.parent.parent / "docker" / "mcp-servers" / "mcp-server-mas-sequential-thinking" / "scripts" / "health_monitor.py"
                        if script_path.exists():
                            subprocess.run(['python', str(script_path), 'restart'], timeout=30)
                            restarted.append('MCP Sequential Thinking Server')
                    except Exception:
                        pass

        return restarted