"""
Diagnostics Commands

`dopemux theme`, `dopemux analyze`, and `dopemux health` — the trio of
introspection commands. `theme` toggles the ritual aesthetic, `analyze`
runs the high-fidelity document processor, and `health` is the full
ecosystem diagnostic HUD with optional orphan cleanup, service fix,
and continuous watch mode.
"""

import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from ..config import ConfigManager
from ..console import console
from ..health import HealthChecker
from ..ui.output import emit
from ..ui.progress import branded_progress
from ..ui.theme import Glyphs, styled_panel, styled_table

logger = logging.getLogger(__name__)


@click.command("theme")
@click.argument("name", required=False)
@click.option("--list", "list_themes", is_flag=True, help="List all available ritual aesthetics.")
@click.pass_context
def theme(ctx, name: Optional[str], list_themes: bool):
    """
    🎭 Aesthetic Synchronizer: Manage UI themes and ritual palettes.
    """
    available_themes = ["mint-mojo", "pastel-neon-dreams", "pastel-neon-dreamscape"]
    cfg_manager = ctx.obj.get("config_manager") if ctx.obj else ConfigManager()

    if list_themes or not name:
        current = cfg_manager.load_config().theme
        table = styled_table("Ritual Aesthetics", "Name", "Status")
        for t in available_themes:
            status = "[success]active[/success]" if t == current else "[text.dim]available[/text.dim]"
            table.add_row(t, status)
        console.print(table)
        return

    if name not in available_themes:
        console.logger.error(f"[error]Invalid aesthetic: {name}[/error]")
        console.print(f"Available: {', '.join(available_themes)}")
        sys.exit(1)

    cfg_manager.set_theme(name)
    console.print(f"[success]✅ Ritual aesthetic synchronized to: [mint]{name}[/mint][/success]")
    console.print("[text.dim]Next ritual cycle will reflect the new palette.[/text.dim]")


@click.command("analyze")
@click.argument("directory", default=".")
@click.option("--output", "-o", help="📂 Harvest Coordinate: Output directory for high-fidelity analysis results.")
@click.option(
    "--embedding-model", "-m", default="voyage-context-3", help="🧠 Cognitive Model: Select the embedding model for ritual analysis (default: voyage-context-3)."
)
@click.option("--milvus-uri", help="📜 Vector Anchor: Milvus database URI or local coordinate for Lite mode.")
@click.option("--max-files", type=int, help="📊 Artifact Limit: Maximum number of files to process during the ritual.")
@click.option("--batch-size", type=int, default=10, help="📊 Signal Density: Artifacts per processing batch.")
@click.option("--extensions", help="🔬 Signal Filter: Comma-separated list of allowed file extensions.")
@click.option("--exclude", help="🛡️  Bypass Patterns: Comma-separated list of coordinates to exclude from the ritual.")
@click.pass_context
def analyze(
    ctx,
    directory: str,
    output: Optional[str],
    embedding_model: str,
    milvus_uri: Optional[str],
    max_files: Optional[int],
    batch_size: int,
    extensions: Optional[str],
    exclude: Optional[str],
):
    """
    🔬 Deep Inspection: Run high-fidelity codebase analysis and embedding

    Engages the semantic analysis engine to audit the codebase and generate
    high-fidelity embeddings. Synchronizes artifacts with the vector
    database to enable cross-workspace ritual search.
    """
    from ..analysis import DocumentProcessor, ProcessingConfig

    # Prepare configuration
    source_path = Path(directory).resolve()
    if not source_path.exists():
        console.logger.info(
            f"[error]❌ Directory does not exist: {source_path}[/error]"
        )
        sys.exit(1)

    # Set output directory
    if output:
        output_path = Path(output).resolve()
    else:
        output_path = source_path / ".dopemux" / "analysis"

    output_path.mkdir(parents=True, exist_ok=True)

    # Parse extensions
    file_extensions = None
    if extensions:
        file_extensions = [
            f".{ext.strip().lstrip('.')}" for ext in extensions.split(",")
        ]

    # Parse exclusion patterns
    exclude_patterns = None
    if exclude:
        exclude_patterns = [pattern.strip() for pattern in exclude.split(",")]

    # Create configuration
    config = ProcessingConfig(
        source_directory=source_path,
        output_directory=output_path,
        max_files=max_files,
        file_extensions=file_extensions,
        exclude_patterns=exclude_patterns,
        embedding_model=embedding_model,
        milvus_uri=milvus_uri,
        batch_size=batch_size,
        show_progress=True,
        gentle_feedback=True,
    )

    # Initialize and run processor
    console.logger.info(
        f"[info]🧠 Starting ADHD-optimized analysis of {source_path}[/info]"
    )
    console.logger.info(f"[text.dim]Output: {output_path}[/text.dim]")

    try:
        processor = DocumentProcessor(config)
        results = processor.analyze_directory()

        if results["success"]:
            console.print(
                f"[success]✅ Analysis complete! Results saved to {output_path}[/success]"
            )
            console.print(
                f"[info]📊 Processing time: {results['processing_time']:.1f}s[/info]"
            )

            # Show usage suggestions
            console.print(
                styled_panel(
                    f"🎯 Next steps:\n\n"
                    f"• Browse results in {output_path}\n"
                    f"• Use semantic search with embeddings\n"
                    f"• Explore feature and component registries\n"
                    f"• Review evidence links for traceability",
                    title=f"{Glyphs.SUCCESS} Ready to Explore",
                )
            )
        else:
            console.logger.error("[error]❌ Analysis failed[/error]")
            sys.exit(1)

    except Exception as e:
        console.logger.error(f"[error]❌ Analysis error: {e}[/error]")
        if (ctx.obj or {}).get("verbose"):
            import traceback

            traceback.print_exc()
        sys.exit(1)


@click.command("health")
@click.option("--detailed", "-d", is_flag=True, help="📊 Deep Telemetry: Show high-fidelity health diagnostics for all subsystems.")
@click.option("--service", "-s", help="🔬 Target Daemon: Check the health of a specific ritual service.")
@click.option("--fix", "-f", is_flag=True, help="🔧 Auto-Remediation: Attempt to restore unhealthy services to stable coordinates.")
@click.option("--cleanup", "-c", is_flag=True, help="🧹 Purge Orphans: Find and terminate abandoned MCP server processes.")
@click.option("--watch", "-w", is_flag=True, help="👁️  Continuous HUD: Engage persistent monitoring mode.")
@click.option(
    "--interval", "-i", type=int, default=30, help="⏱️ Scan Frequency: Watch interval in seconds (default: 30)."
)
@click.pass_context
def health(
    ctx,
    detailed: bool,
    service: Optional[str],
    fix: bool,
    cleanup: bool,
    watch: bool,
    interval: int,
):
    """
    🏥 Diagnostic HUD: Comprehensive health check for the DØPEMÜX ecosystem

    Monitors core daemon health, Claude Code integration, MCP server
    stability, Docker service status, and ADHD cockpit effectiveness.
    Synchronizes across all subsystems to ensure a stable ritual environment.
    """
    project_path = Path.cwd()
    health_checker = HealthChecker(project_path, console)

    # Handle cleanup flag first
    if cleanup:
        console.logger.info("[info]🧹 Cleaning up orphaned MCP processes...[/info]")

        try:
            # Find orphaned MCP processes
            result = subprocess.run(
                ["ps", "aux"], capture_output=True, text=True, check=True
            )

            orphaned_pids = []
            mcp_patterns = [
                "conport-mcp",
                "serena/v2/mcp_server.py",
                "src.mcp.server",
                "dopemux-gpt-researcher",
            ]

            for line in result.stdout.split("\n"):
                # Check if it's an MCP process
                if any(pattern in line for pattern in mcp_patterns):
                    # Extract PID
                    parts = line.split()
                    if len(parts) > 1:
                        pid = parts[1]
                        # Check if parent process (Claude Code) is still running
                        try:
                            parent_check = subprocess.run(
                                ["ps", "-o", "ppid=", "-p", pid],
                                capture_output=True,
                                text=True,
                            )
                            ppid = parent_check.stdout.strip()
                            if ppid:
                                parent_cmd = subprocess.run(
                                    ["ps", "-o", "comm=", "-p", ppid],
                                    capture_output=True,
                                    text=True,
                                )
                                # If parent is not Claude Code, it's orphaned
                                if "claude" not in parent_cmd.stdout.lower():
                                    orphaned_pids.append(pid)
                        except (subprocess.SubprocessError, OSError) as e:
                            logger.error(f"Process parent check failed: {e}")
                        except Exception:
                            logger.error(
                                "Unexpected process parent check error", exc_info=True
                            )
            if orphaned_pids:
                console.print(
                    f"[warning]Found {len(orphaned_pids)} orphaned MCP processes[/warning]"
                )

                if click.confirm("Kill these processes?", default=True):
                    killed = 0
                    for pid in orphaned_pids:
                        try:
                            os.kill(int(pid), signal.SIGTERM)
                            killed += 1
                        except (OSError, ValueError) as e:
                            logger.debug("Failed to terminate PID %s: %s", pid, e)

                    console.print(
                        f"[success]✅ Cleaned up {killed} orphaned processes[/success]"
                    )
                else:
                    console.print("[warning]Cleanup cancelled[/warning]")
            else:
                console.print("[success]✅ No orphaned MCP processes found[/success]")

        except Exception as e:
            console.print(f"[error]❌ Cleanup failed: {e}[/error]")

        # Exit after cleanup unless combined with other flags
        if not (detailed or service or fix or watch):
            return

    if watch:
        console.print(
            f"[info]👁️ Starting continuous health monitoring (interval: {interval}s)[/info]"
        )
        console.print("[text.dim]Press Ctrl+C to stop[/text.dim]")

        try:
            while True:
                console.clear()
                console.print(
                    f"[text.dim]Last check: {datetime.now().strftime('%H:%M:%S')}[/text.dim]"
                )

                results = health_checker.check_all(detailed=detailed)
                health_checker.display_health_report(results, detailed=detailed)

                time.sleep(interval)
        except KeyboardInterrupt:
            console.print("\n[warning]🛑 Health monitoring stopped[/warning]")
            return

    # Single health check
    with branded_progress(console=console) as progress:
        task = progress.add_task("Running health checks...", total=None)

        if service:
            # Check specific service
            checker_method = getattr(health_checker, f"_check_{service}", None)
            if not checker_method:
                console.logger.info(f"[error]❌ Unknown service: {service}[/error]")
                console.print(
                    f"[warning]Available services: {', '.join(health_checker.checks.keys())}[/warning]"
                )
                sys.exit(1)

            result = checker_method(detailed=detailed)
            results = {service: result}
        else:
            # Check all services
            results = health_checker.check_all(detailed=detailed)

        progress.update(task, description="Health checks complete!", completed=True)

    # Display results
    def _rich_health():
        health_checker.display_health_report(results, detailed=detailed)

    emit(
        ctx,
        data={
            "services": {
                name: {
                    "status": h.status.value[0],
                    "message": h.message,
                    "response_time_ms": h.response_time_ms,
                }
                for name, h in results.items()
            },
            "critical": sum(
                1 for h in results.values() if h.status.value[0] == "critical"
            ),
            "healthy": sum(
                1 for h in results.values() if h.status.value[0] == "healthy"
            ),
        },
        rich_render=_rich_health,
    )

    # Fix unhealthy services if requested
    if fix:
        console.logger.info("\n[info]🔧 Attempting to fix unhealthy services...[/info]")

        with branded_progress(console=console) as progress:
            fix_task = progress.add_task("Fixing services...", total=None)

            restarted = health_checker.restart_unhealthy_services()

            progress.update(
                fix_task, description="Fix attempts complete!", completed=True
            )

        if restarted:
            console.print(
                f"[success]✅ Restarted services: {', '.join(restarted)}[/success]"
            )
            console.logger.info(
                "[info]💡 Run 'dopemux health' again to verify fixes[/info]"
            )
        else:
            console.logger.info(
                "[warning]⚠️ No services could be automatically fixed[/warning]"
            )
            console.logger.info(
                "[text.dim]Manual intervention may be required[/text.dim]"
            )

    # Exit with appropriate code for scripting
    critical_count = sum(1 for h in results.values() if h.status.value[0] == "critical")
    if critical_count > 0:
        sys.exit(1)
