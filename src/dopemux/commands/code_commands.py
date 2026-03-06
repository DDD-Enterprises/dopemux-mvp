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
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from ..console import console

@click.group()
@click.pass_context
def code(ctx):
    """
    🧠 AI Code Repair - Vanilla Agent

    Quick and reliable code fixes using traditional LLM-based iterative repair.
    Best for straightforward bugs and rapid development cycles.

    Examples:
        dopemux code repair "undefined variable error" --file script.py
        dopemux code analyze "null pointer issue" --file app.py
        dopemux code status
    """
    pass


@code.command()
@click.argument('bug_description')
@click.option('--file', '-f', 'file_path', help='Path to file containing the bug')
@click.option('--line', '-l', type=int, help='Line number where bug occurs')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.option('--dry-run', is_flag=True, help='Show what would be done without making changes')
@click.pass_context
def repair(ctx, bug_description, file_path, line, verbose, dry_run):
    """
    Repair code using the vanilla agent.

    BUG_DESCRIPTION: Description of the bug to fix

    Examples:
        dopemux code repair "variable not defined" --file script.py --line 42
        dopemux code repair "null pointer exception" --file app.py --verbose
    """
    # Import here to avoid circular dependencies
    try:
        # Add services to Python path if needed
        services_path = Path(__file__).resolve().parent.parent / 'services'
        if str(services_path) not in sys.path:
            sys.path.insert(0, str(services_path))

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
                console.logger.info("[yellow]🔍 Dry run mode - analyzing bug without repair[/yellow]")
                analysis = await agent._analyze_bug(bug_description, file_path or "", line or 0)
                console.logger.info("Analysis Results:")
                console.logger.info(f"  Description: {analysis.get('description', 'N/A')}")
                console.logger.info(f"  Complexity: {analysis.get('complexity', {}).get('score', 'N/A')}")
                console.logger.info(f"  Similar patterns: {len(analysis.get('similar_patterns', {}).get('results', []))}")
                return

            result = await agent.process_task(task)

            if result.get('success'):
                console.logger.info("[green]✅ Repair successful![/green]")
                console.logger.info(f"Confidence: {result.get('confidence', 0):.2f}")
                console.logger.info(f"Iterations: {result.get('iterations', 0)}")
                if result.get('repair'):
                    console.logger.info("\n[blue]Generated Repair:[/blue]")
                    console.logger.info(result['repair'])
                if result.get('explanation'):
                    console.logger.info(f"\n[yellow]Explanation:[/yellow] {result['explanation']}")
            else:
                console.logger.error("[red]❌ Repair failed[/red]")
                console.logger.error(f"Reason: {result.get('explanation', 'Unknown error')}")
                if verbose:
                    console.logger.debug(f"Debug: Iterations attempted: {result.get('iterations', 0)}")

        asyncio.run(run_repair())

    except Exception as e:
        console.logger.error(f"[red]❌ Code repair failed: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()


@code.command()
@click.argument('bug_description')
@click.option('--file', '-f', 'file_path', help='Path to file to analyze')
@click.option('--line', '-l', type=int, help='Line number to analyze')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def analyze(ctx, bug_description, file_path, line, verbose):
    """
    Analyze a bug without attempting repair.

    Provides insights, complexity assessment, and repair strategy recommendations.
    """
    try:
        services_path = Path(__file__).resolve().parent.parent / 'services'
        if str(services_path) not in sys.path:
            sys.path.insert(0, str(services_path))

        from genetic_agent.vanilla.vanilla_agent import VanillaAgent
        from genetic_agent.core.config import AgentConfig
        import asyncio

        async def run_analysis():
            config = AgentConfig()
            agent = VanillaAgent(config)

            analysis = await agent._analyze_bug(bug_description, file_path or "", line or 0)

            console.logger.info("[blue]🔍 Bug Analysis Complete[/blue]")
            console.logger.info(f"Description: {analysis.get('description', 'N/A')}")
            console.logger.info(f"Complexity Score: {analysis.get('complexity', {}).get('score', 'N/A')}")
            console.logger.info(f"Similar Patterns Found: {len(analysis.get('similar_patterns', {}).get('results', []))}")

            if verbose:
                if analysis.get('complexity', {}).get('details'):
                    console.logger.info("Complexity Details:")
                    for key, value in analysis['complexity']['details'].items():
                        console.logger.info(f"  {key}: {value}")

        asyncio.run(run_analysis())

    except Exception as e:
        console.logger.error(f"[red]❌ Analysis failed: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()


@code.command()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def code_agent_status_cmd(ctx, verbose):
    """
    Show code agent status and configuration.
    """
    try:
        services_path = Path(__file__).resolve().parent.parent / 'services'
        if str(services_path) not in sys.path:
            sys.path.insert(0, str(services_path))

        from genetic_agent.core.config import AgentConfig
        import asyncio

        async def show_status():
            config = AgentConfig()

            console.logger.info("[blue]🧠 Vanilla Code Agent Status[/blue]")
            console.logger.info(f"Container Zen URL: {config.zen_url}")
            console.logger.info(f"Container ConPort URL: {config.conport_url}")
            console.logger.info(f"Container Serena URL: {config.serena_url}")
            console.logger.info(f"Container Dope-Context URL: {config.dope_context_url}")
            console.logger.info(f"Max Iterations: {config.max_iterations}")
            console.logger.info(f"Confidence Threshold: {config.confidence_threshold}")
            console.logger.info(f"Workspace: {config.workspace_id}")

            # Test MCP connectivity from host (localhost URLs)
            console.logger.info("\n[yellow]Host MCP Service Status (localhost):[/yellow]")
            host_urls = {
                "Zen": "http://localhost:3003",
                "ConPort": "http://localhost:3004",
                "Serena": "http://localhost:3006",
                "Dope-Context": "http://localhost:3010"
            }

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

                        logger.error(f"Error: {e}")
                    status_icon = "✅" if reachable else "❌"
                    console.logger.info(f"  {status_icon} {service}")
                    if not reachable:
                        console.logger.error(f"    Error: {error_msg}")

            console.logger.info("\n[dim]Note: Container uses Docker network names, host uses localhost[/dim]")

        asyncio.run(show_status())

    except Exception as e:
        console.logger.error(f"[red]❌ Status check failed: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()


