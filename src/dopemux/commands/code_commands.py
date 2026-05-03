"""
Code Commands
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from subprocess import CalledProcessError
from typing import Optional, Dict, List, Sequence

import click
import yaml
from dopemux.ui.progress import branded_progress
from dopemux.ui.progress import branded_progress
from rich.progress import Progress, SpinnerColumn, TextColumn

from ..console import console


def _ensure_genetic_agent_path() -> Path:
    """Expose the repo-local genetic_agent service package when present."""
    repo_root = Path(__file__).resolve().parents[3]
    services_path = repo_root / "services"
    if not (services_path / "genetic_agent").exists():
        raise ImportError(f"genetic_agent service not found under {services_path}")
    if str(services_path) not in sys.path:
        sys.path.insert(0, str(services_path))
    return services_path

@click.group()
@click.pass_context
def code(ctx):
    """
    🧠 Cognitive Repair: Vanilla Agent Code Repair

    Orchestrates traditional LLM-based iterative code fixes. Best for 
    straightforward bugs and rapid development cycles, synchronizing 
    automated repair rituals across the project workspace.
    """
    pass


@code.command()
@click.argument('bug_description')
@click.option('--file', '-f', 'file_path', help='🔬 Artifact Coordinate: Path to the file containing the reported bug.')
@click.option('--line', '-l', type=int, help='📍 Signal Anchor: Specific line number where the bug manifests.')
@click.option('--verbose', '-v', is_flag=True, help='📊 Deep Telemetry: Enable verbose output for high-fidelity diagnostics.')
@click.option('--dry-run', is_flag=True, help='🔬 Ritual Preview: Simulate repair operations without mutating artifacts.')
@click.pass_context
def repair(ctx, bug_description, file_path, line, verbose, dry_run):
    """
    💊 Execute Remediation: Run the vanilla agent code repair ritual

    Initiates an iterative repair sequence to resolve the specified bug. 
    Synchronizes across file coordinates and reported signals to MATERIALISE 
    a high-fidelity fix.
    """
    # Import here to avoid circular dependencies
    try:
        _ensure_genetic_agent_path()

        from genetic_agent.vanilla.vanilla_agent import VanillaAgent
        from genetic_agent.core.config import AgentConfig
        import asyncio

        async def run_repair():
            config = AgentConfig()
            agent = VanillaAgent(config)

            task = {
                "bug_description": bug_description,
                "file_path": file_path or "",
                "line_number": line or 0
            }

            if dry_run:
                console.logger.info("[warning]🔍 Dry run mode - analyzing bug without repair[/warning]")
                analysis = await agent._analyze_bug(bug_description, file_path or "", line or 0)
                console.logger.info("Analysis Results:")
                console.logger.info(f"  Description: {analysis.get('description', 'N/A')}")
                console.logger.info(f"  Complexity: {analysis.get('complexity', {}).get('score', 'N/A')}")
                console.logger.info(f"  Similar patterns: {len(analysis.get('similar_patterns', {}).get('results', []))}")
                return True

            result = await agent.process_task(task)

            if result.get('success'):
                console.logger.info("[success]✅ Repair successful![/success]")
                console.logger.info(f"Confidence: {result.get('confidence', 0):.2f}")
                console.logger.info(f"Iterations: {result.get('iterations', 0)}")
                if result.get('repair'):
                    console.logger.info("\n[info]Generated Repair:[/info]")
                    console.logger.info(result['repair'])
                if result.get('explanation'):
                    console.logger.info(f"\n[warning]Explanation:[/warning] {result['explanation']}")
                return True
            else:
                console.logger.error("[error]❌ Repair failed[/error]")
                console.logger.error(f"Reason: {result.get('explanation', 'Unknown error')}")
                if verbose:
                    console.logger.debug(f"Debug: Iterations attempted: {result.get('iterations', 0)}")
                return False

        if not asyncio.run(run_repair()):
            raise click.ClickException("Code repair failed")

    except click.ClickException:
        raise
    except Exception as e:
        console.logger.error(f"[error]❌ Code repair failed: {e}[/error]")
        if verbose:
            import traceback
            traceback.print_exc()
        raise click.ClickException(f"Code repair failed: {e}") from e


@code.command()
@click.argument('bug_description')
@click.option('--file', '-f', 'file_path', help='🔬 Artifact Coordinate: Target file path for diagnostic analysis.')
@click.option('--line', '-l', type=int, help='📍 Signal Anchor: Target line number for isolated analysis.')
@click.option('--verbose', '-v', is_flag=True, help='📊 Deep Telemetry: Enable detailed analytic readout.')
@click.pass_context
def analyze(ctx, bug_description, file_path, line, verbose):
    """
    🔬 Pattern Synthesis: Analyze bug surface area without executing repairs

    Generates cognitive insights, ritual complexity assessments, and 
    recommended repair strategies for manual remediation.
    """
    try:
        _ensure_genetic_agent_path()

        from genetic_agent.vanilla.vanilla_agent import VanillaAgent
        from genetic_agent.core.config import AgentConfig
        import asyncio

        async def run_analysis():
            config = AgentConfig()
            agent = VanillaAgent(config)

            analysis = await agent._analyze_bug(bug_description, file_path or "", line or 0)

            console.logger.info("[info]🔍 Bug Analysis Complete[/info]")
            console.logger.info(f"Description: {analysis.get('description', 'N/A')}")
            console.logger.info(f"Complexity Score: {analysis.get('complexity', {}).get('score', 'N/A')}")
            console.logger.info(f"Similar Patterns Found: {len(analysis.get('similar_patterns', {}).get('results', []))}")

            if verbose:
                if analysis.get('complexity', {}).get('details'):
                    console.logger.info("Complexity Details:")
                    for key, value in analysis['complexity']['details'].items():
                        console.logger.info(f"  {key}: {value}")

        asyncio.run(run_analysis())

    except click.ClickException:
        raise
    except Exception as e:
        console.logger.error(f"[error]❌ Analysis failed: {e}[/error]")
        if verbose:
            import traceback
            traceback.print_exc()
        raise click.ClickException(f"Analysis failed: {e}") from e


def _run_code_agent_status(verbose):
    try:
        _ensure_genetic_agent_path()

        import aiohttp
        from genetic_agent.core.config import AgentConfig
        import asyncio

        async def show_status():
            config = AgentConfig()

            console.logger.info("[info]🧠 Vanilla Code Agent Status[/info]")
            console.logger.info(f"Container Zen URL: {config.zen_url}")
            console.logger.info(f"Container ConPort URL: {config.conport_url}")
            console.logger.info(f"Container Serena URL: {config.serena_url}")
            console.logger.info(f"Container Dope-Context URL: {config.dope_context_url}")
            console.logger.info(f"Max Iterations: {config.max_iterations}")
            console.logger.info(f"Confidence Threshold: {config.confidence_threshold}")
            console.logger.info(f"Workspace: {config.workspace_id}")

            console.logger.info("\n[warning]Host MCP Service Status (localhost):[/warning]")
            host_urls = {
                "Zen": "http://localhost:3003",
                "ConPort": "http://localhost:3004",
                "Serena": "http://localhost:3006",
                "Dope-Context": "http://localhost:3010"
            }

            failed_services = []
            timeout = aiohttp.ClientTimeout(total=3.0)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                for service, url in host_urls.items():
                    reachable = False
                    error_msg = ""

                    try:
                        health_url = f"{url.rstrip('/')}/health"
                        async with session.get(health_url) as response:
                            if response.status == 200:
                                reachable = True
                            else:
                                error_msg = f"Health check failed with status {response.status}"
                    except Exception as e:
                        error_msg = f"Connection failed: {str(e)}"
                        console.logger.error(f"Error: {e}")
                    status_icon = "✅" if reachable else "❌"
                    console.logger.info(f"  {status_icon} {service}")
                    if not reachable:
                        failed_services.append(service)
                        console.logger.error(f"    Error: {error_msg}")

            console.logger.info("\n[text.dim]Note: Container uses Docker network names, host uses localhost[/text.dim]")
            return failed_services

        failed_services = asyncio.run(show_status())
        if failed_services:
            raise click.ClickException(
                f"Code agent status check failed for: {', '.join(failed_services)}"
            )

    except click.ClickException:
        raise
    except Exception as e:
        console.logger.error(f"[error]❌ Status check failed: {e}[/error]")
        if verbose:
            import traceback
            traceback.print_exc()
        raise click.ClickException(f"Status check failed: {e}") from e


@code.command("status")
@click.option('--verbose', '-v', is_flag=True, help='📊 Deep Telemetry: Enable verbose diagnostic output.')
@click.pass_context
def code_agent_status_cmd(ctx, verbose):
    """
    📊 Monitoring HUD: Show code agent status and configuration

    Displays the current operational state, cognitive parameters, and
    service connectivity for the vanilla code agent daemon.
    """
    return _run_code_agent_status(verbose)


@code.command("code-agent-status-cmd", hidden=True)
@click.option('--verbose', '-v', is_flag=True, help='📊 Deep Telemetry: Enable verbose diagnostic output.')
@click.pass_context
def code_agent_status_legacy_cmd(ctx, verbose):
    """Deprecated compatibility alias for `status`."""
    return _run_code_agent_status(verbose)
