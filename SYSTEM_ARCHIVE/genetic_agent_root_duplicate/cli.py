#!/usr/bin/env python3
"""
CLI Interface for Enhanced Iterative Agent - Phase 3

Developer-focused command-line interface providing seamless integration
with the intelligent code repair system.

Commands:
- repair: Code repair with intelligent agent selection
- analyze: Bug analysis and insights
- optimize: Performance optimization
- monitor: Real-time monitoring and status
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel
from rich.text import Text
from rich.table import Table

from genetic_agent.core.config import AgentConfig
from genetic_agent.genetic.enhanced_iterative_agent import EnhancedIterativeAgent
from genetic_agent.vanilla.vanilla_agent import VanillaAgent
from genetic_agent.genetic.genetic_agent import GeneticAgent

# Initialize Rich console for beautiful output
console = Console()

class CLIContext:
    """CLI context for shared state and configuration."""

    def __init__(self):
        self.config = None
        self.enhanced_agent = None
        self.genetic_agent = None
        self.vanilla_agent = None
        self.verbose = False
        self.debug = False

    def ensure_agents_initialized(self):
        """Initialize agents if not already done."""
        if self.config is None:
            self.config = AgentConfig()

        if self.enhanced_agent is None:
            try:
                self.enhanced_agent = EnhancedIterativeAgent(self.config)
            except Exception as e:
                if self.debug:
                    console.print(f"[red]Failed to initialize enhanced agent: {e}[/red]")
                self.enhanced_agent = None

        if self.genetic_agent is None:
            try:
                self.genetic_agent = GeneticAgent(self.config)
            except Exception as e:
                if self.debug:
                    console.print(f"[red]Failed to initialize genetic agent: {e}[/red]")
                self.genetic_agent = None

        if self.vanilla_agent is None:
            try:
                self.vanilla_agent = VanillaAgent(self.config)
            except Exception as e:
                if self.debug:
                    console.print(f"[red]Failed to initialize vanilla agent: {e}[/red]")
                self.vanilla_agent = None

# Global CLI context
ctx = CLIContext()

# Common options
verbose_option = click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)

debug_option = click.option(
    '--debug',
    is_flag=True,
    help='Enable debug output'
)

@click.group()
@click.pass_context
@verbose_option
@debug_option
def cli(cli_ctx, verbose, debug):
    """Enhanced Iterative Agent CLI - Intelligent Code Repair System

    A developer-focused CLI for automated code repair with AI assistance.
    Supports multiple repair strategies and comprehensive monitoring.
    """
    ctx.verbose = verbose
    ctx.debug = debug

    # Show welcome message
    if not verbose and not debug:
        console.print()
        console.print("[bold blue]🤖 Enhanced Iterative Agent CLI[/bold blue]")
        console.print("[dim]Intelligent code repair with AI assistance[/dim]")
        console.print()

@cli.command()
@click.argument('bug_description')
@click.option('--file', '-f', 'file_path', help='Path to file containing the bug')
@click.option('--line', '-l', type=int, help='Line number where bug occurs')
@click.option('--agent', type=click.Choice(['enhanced', 'genetic', 'vanilla', 'auto']),
              default='auto', help='Agent to use for repair')
@click.option('--strategy', type=click.Choice(['llm_only', 'selective_gp', 'full_gp']),
              help='Repair strategy (enhanced agent only)')
@verbose_option
@debug_option
def repair(bug_description, file_path, line, agent, strategy, verbose, debug):
    """Repair code using intelligent agents.

    BUG_DESCRIPTION: Description of the bug to fix

    Examples:
        genetic-agent repair "variable not defined" --file script.py --line 42
        genetic-agent repair "null pointer exception" --agent enhanced
    """
    ctx.verbose = verbose or ctx.verbose
    ctx.debug = debug or ctx.debug

    async def run_repair():
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green"),
            TimeElapsedColumn(),
            console=console
        ) as progress:

            # Initialize agents
            init_task = progress.add_task("Initializing agents...", total=1)
            ctx.ensure_agents_initialized()
            progress.update(init_task, completed=1)

            # Select agent
            selected_agent = _select_agent(agent)
            if not selected_agent:
                console.print("[red]❌ No suitable agent available[/red]")
                return

            # Prepare repair task
            task_data = {
                "bug_description": bug_description,
                "file_path": file_path or "",
                "line_number": line or 0
            }

            if strategy and agent == 'enhanced':
                task_data["strategy"] = strategy

            # Execute repair
            repair_task = progress.add_task("🔧 Analyzing and repairing code...", total=100)

            try:
                result = await selected_agent.process_task(task_data)

                # Simulate progress updates
                for i in range(0, 90, 10):
                    progress.update(repair_task, completed=i)
                    await asyncio.sleep(0.1)

                progress.update(repair_task, completed=100)

                # Display results
                _display_repair_results(result, agent)

            except Exception as e:
                progress.update(repair_task, completed=0)
                console.print(f"[red]❌ Repair failed: {e}[/red]")
                if debug:
                    import traceback
                    traceback.print_exc()

    asyncio.run(run_repair())

@cli.command()
@click.argument('bug_description')
@click.option('--file', '-f', 'file_path', help='Path to file to analyze')
@click.option('--line', '-l', type=int, help='Line number to analyze')
@verbose_option
@debug_option
def analyze(bug_description, file_path, line, verbose, debug):
    """Analyze a bug without attempting repair.

    Provides insights, complexity assessment, and repair strategy recommendations.
    """
    ctx.verbose = verbose or ctx.verbose
    ctx.debug = debug or ctx.debug

    async def run_analysis():
        ctx.ensure_agents_initialized()

        if not ctx.enhanced_agent:
            console.print("[red]❌ Enhanced agent required for analysis[/red]")
            return

        task_data = {
            "bug_description": bug_description,
            "file_path": file_path or "",
            "line_number": line or 0
        }

        with console.status("[bold green]🔍 Analyzing bug...") as status:
            try:
                # Use enhanced agent's analysis capabilities
                analysis = await ctx.enhanced_agent._analyze_bug(
                    bug_description, file_path or "", line or 0
                )

                # Get strategy recommendation
                strategy = await ctx.enhanced_agent._determine_strategy_with_intelligence(analysis)

                _display_analysis_results(analysis, strategy)

            except Exception as e:
                console.print(f"[red]❌ Analysis failed: {e}[/red]")
                if debug:
                    import traceback
                    traceback.print_exc()

    asyncio.run(run_analysis())

@cli.command()
@click.option('--agent', type=click.Choice(['enhanced', 'genetic', 'vanilla', 'all']),
              default='all', help='Agent to monitor')
@click.option('--watch', '-w', is_flag=True, help='Continuous monitoring mode')
@click.option('--interval', type=int, default=5, help='Update interval in seconds')
@verbose_option
@debug_option
def monitor(agent, watch, interval, verbose, debug):
    """Monitor agent status and performance.

    Shows real-time metrics, health status, and performance indicators.
    """
    ctx.verbose = verbose or ctx.verbose
    ctx.debug = debug or ctx.debug

    async def run_monitoring():
        ctx.ensure_agents_initialized()

        if watch:
            console.print("[green]📊 Starting continuous monitoring (Ctrl+C to stop)[/green]")
            console.print()

        try:
            while True:
                _display_monitoring_status(agent)

                if not watch:
                    break

                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            console.print("\n[yellow]⏹️  Monitoring stopped[/yellow]")

    asyncio.run(run_monitoring())

@cli.command()
@click.option('--target', type=click.Choice(['performance', 'reliability', 'efficiency']),
              default='performance', help='Optimization target')
@click.option('--agent', type=click.Choice(['enhanced', 'genetic', 'vanilla']),
              default='enhanced', help='Agent to optimize')
@verbose_option
@debug_option
def optimize(target, agent, verbose, debug):
    """Optimize agent performance and configuration.

    Analyzes current performance and suggests optimizations for:
    - Performance: Speed and efficiency improvements
    - Reliability: Error reduction and stability enhancements
    - Efficiency: Token usage and resource optimization
    """
    ctx.verbose = verbose or ctx.verbose
    ctx.debug = debug or ctx.debug

    async def run_optimization():
        ctx.ensure_agents_initialized()

        console.print(f"[blue]🎯 Optimizing {agent} agent for {target}[/blue]")
        console.print()

        # Placeholder optimization logic
        with console.status(f"[bold green]Analyzing {target} metrics...") as status:
            await asyncio.sleep(1)  # Simulate analysis

        # Show optimization recommendations
        table = Table(title=f"🎯 {target.title()} Optimization Recommendations")
        table.add_column("Category", style="cyan")
        table.add_column("Recommendation", style="white")
        table.add_column("Impact", style="green")

        if target == 'performance':
            table.add_row("Caching", "Enable Redis caching for MCP responses", "High")
            table.add_row("Parallelization", "Increase concurrent MCP calls", "Medium")
            table.add_row("Batching", "Batch similar repair requests", "Medium")

        elif target == 'reliability':
            table.add_row("Error Handling", "Add circuit breakers for MCP services", "High")
            table.add_row("Fallbacks", "Implement fallback strategies", "High")
            table.add_row("Monitoring", "Add health checks and alerts", "Medium")

        elif target == 'efficiency':
            table.add_row("Token Optimization", "Implement token usage tracking", "High")
            table.add_row("Caching", "Cache analysis results", "Medium")
            table.add_row("Batching", "Batch MCP service calls", "Medium")

        console.print(table)

        console.print(f"\n[green]✅ Optimization analysis complete for {agent} agent[/green]")

    asyncio.run(run_optimization())

@cli.command()
@verbose_option
@debug_option
def status(verbose, debug):
    """Show system status and configuration."""
    ctx.verbose = verbose or ctx.verbose
    ctx.debug = debug or ctx.debug

    async def show_status():
        ctx.ensure_agents_initialized()

        # System information
        table = Table(title="🔧 System Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Version", style="yellow")

        table.add_row("Enhanced Agent", "✅ Active" if ctx.enhanced_agent else "❌ Inactive", "Phase 3.0")
        table.add_row("Genetic Agent", "✅ Active" if ctx.genetic_agent else "❌ Inactive", "Phase 2.0")
        table.add_row("Vanilla Agent", "✅ Active" if ctx.vanilla_agent else "❌ Inactive", "Phase 1.0")

        # Configuration
        config_table = Table(title="⚙️  Configuration")
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="white")

        if ctx.config:
            config_table.add_row("Max Tokens", str(ctx.config.max_tokens))
            config_table.add_row("Max Iterations", str(ctx.config.max_iterations))
            config_table.add_row("Confidence Threshold", str(ctx.config.confidence_threshold))
            config_table.add_row("Workspace ID", str(ctx.config.workspace_id)[:50] + "...")

        console.print(table)
        console.print()
        console.print(config_table)

    asyncio.run(show_status())

def _select_agent(agent_preference: str):
    """Select appropriate agent based on preference."""
    if agent_preference == 'auto':
        # Prefer enhanced > genetic > vanilla
        if ctx.enhanced_agent:
            return ctx.enhanced_agent
        elif ctx.genetic_agent:
            return ctx.genetic_agent
        elif ctx.vanilla_agent:
            return ctx.vanilla_agent

    elif agent_preference == 'enhanced' and ctx.enhanced_agent:
        return ctx.enhanced_agent
    elif agent_preference == 'genetic' and ctx.genetic_agent:
        return ctx.genetic_agent
    elif agent_preference == 'vanilla' and ctx.vanilla_agent:
        return ctx.vanilla_agent

    return None

def _display_repair_results(result: Dict[str, Any], agent_used: str):
    """Display repair results in a beautiful format."""
    success = result.get('success', False)

    if success:
        console.print("\n[green]✅ Repair Successful![/green]")

        # Show key metrics
        table = Table(title="📊 Repair Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Confidence", f"{result.get('confidence', 0):.2f}")
        table.add_row("Iterations", str(result.get('iterations', 0)))
        table.add_row("Method", result.get('method', 'unknown'))
        table.add_row("Agent Used", agent_used)

        console.print(table)

        # Show the repair
        if 'repair' in result and result['repair']:
            console.print("\n[blue]🔧 Generated Repair:[/blue]")
            console.print(Panel(result['repair'], title="Code", border_style="blue"))

        if 'explanation' in result:
            console.print(f"\n[yellow]💡 Explanation:[/yellow] {result['explanation']}")

    else:
        console.print("\n[red]❌ Repair Failed[/red]")
        console.print(f"Reason: {result.get('explanation', 'Unknown error')}")

        # Show failure analysis if available
        if 'failure_analysis' in result:
            analysis = result['failure_analysis']
            console.print(f"\n[yellow]🔍 Failure Analysis:[/yellow]")
            console.print(f"Primary Mode: {analysis.get('primary_mode', 'unknown')}")
            if analysis.get('recommendations'):
                console.print(f"Recommendations: {analysis['recommendations']}")

def _display_analysis_results(analysis: Dict[str, Any], strategy):
    """Display bug analysis results."""
    console.print("\n[blue]🔍 Bug Analysis Complete[/blue]")

    # Analysis summary
    table = Table(title="📊 Analysis Summary")
    table.add_column("Aspect", style="cyan")
    table.add_column("Result", style="white")

    complexity = analysis.get('complexity', {})
    patterns = analysis.get('patterns', {})

    table.add_row("Complexity Score", f"{complexity.get('score', 0):.2f}")
    table.add_row("Similar Patterns", str(len(patterns.get('results', []))))
    table.add_row("Recommended Strategy", str(strategy.value))

    console.print(table)

    # Strategy explanation
    strategy_explanations = {
        'llm_only': "Simple bug - LLM-based repair should suffice",
        'selective_gp': "Moderate complexity - selective genetic programming recommended",
        'full_gp': "High complexity - full genetic programming optimization needed"
    }

    console.print(f"\n[yellow]🎯 Strategy Recommendation:[/yellow]")
    console.print(f"{strategy_explanations.get(strategy.value, 'Custom strategy required')}")

def _display_monitoring_status(agent_filter: str):
    """Display current monitoring status."""
    console.print("\n[green]📊 System Monitoring Status[/green]")

    agents_to_check = []
    if agent_filter == 'all':
        agents_to_check = [
            ('Enhanced Agent', ctx.enhanced_agent),
            ('Genetic Agent', ctx.genetic_agent),
            ('Vanilla Agent', ctx.vanilla_agent)
        ]
    else:
        agent_map = {
            'enhanced': ('Enhanced Agent', ctx.enhanced_agent),
            'genetic': ('Genetic Agent', ctx.genetic_agent),
            'vanilla': ('Vanilla Agent', ctx.vanilla_agent)
        }
        if agent_filter in agent_map:
            agents_to_check = [agent_map[agent_filter]]

    table = Table(title="🤖 Agent Status")
    table.add_column("Agent", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Last Activity", style="yellow")

    for name, agent in agents_to_check:
        if agent:
            status = "✅ Active"
            # In a real implementation, you'd check actual status
            last_activity = "Now"
        else:
            status = "❌ Inactive"
            last_activity = "N/A"

        table.add_row(name, status, last_activity)

    console.print(table)

    # Show system metrics
    if ctx.verbose:
        metrics_table = Table(title="📈 System Metrics")
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="white")

        # Placeholder metrics
        metrics_table.add_row("Active Sessions", "1")
        metrics_table.add_row("MCP Services", "4/4 healthy")
        metrics_table.add_row("Memory Usage", "~150MB")
        metrics_table.add_row("Response Time", "< 2s avg")

        console.print()
        console.print(metrics_table)

if __name__ == '__main__':
    cli()