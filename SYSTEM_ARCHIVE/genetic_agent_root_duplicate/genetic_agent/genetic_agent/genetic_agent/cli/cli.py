"""CLI interface for the Genetic Coding Agent system."""

import asyncio
import click
import json
import sys
from pathlib import Path
from typing import Optional

from core.config import AgentConfig
from vanilla.vanilla_agent import VanillaAgent
from genetic.genetic_agent import GeneticAgent
from shared.mcp.memory_adapter import MemoryAdapter
from shared.mcp.conport_client import ConPortClient


class CLIProgress:
    """Progress indicator for CLI operations."""

    def __init__(self, description: str = "Processing"):
        self.description = description
        self.current_step = 0
        self.total_steps = 1

    def update(self, step: int, total: int, message: str = None):
        """Update progress display."""
        self.current_step = step
        self.total_steps = total
        self._display_progress(message)

    def _display_progress(self, message: str = None):
        """Display progress bar."""
        percent = int((self.current_step / self.total_steps) * 100) if self.total_steps > 0 else 0
        bar_length = 40
        filled_length = int(bar_length * self.current_step // self.total_steps)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)

        status = f"{self.description}: [{bar}] {percent}%"
        if message:
            status += f" - {message}"

        # Clear line and write new status
        click.echo(f"\r{status}", nl=False, err=True)
        if self.current_step >= self.total_steps:
            click.echo("", err=True)  # New line when complete


class GeneticAgentCLI:
    """CLI interface for genetic coding agent operations."""

    def __init__(self):
        self.config = AgentConfig()
        self.vanilla_agent = None
        self.genetic_agent = None
        self.progress = None

    async def initialize_agents(self):
        """Initialize both vanilla and genetic agents."""
        try:
            self.vanilla_agent = VanillaAgent(self.config)

            # Initialize genetic agent with all MCP integrations
            self.genetic_agent = GeneticAgent(self.config)

            click.echo("✅ Agents initialized successfully", err=True)
            return True
        except Exception as e:
            click.echo(f"❌ Failed to initialize agents: {e}", err=True)
            return False

    async def repair_bug(self, file_path: str, description: str, line_number: int = 1,
                        use_genetic: bool = False, output_format: str = "json"):
        """Repair a bug using the specified agent."""

        if not await self.initialize_agents():
            return

        # Prepare task
        task = {
            "bug_description": description,
            "file_path": str(file_path),
            "line_number": line_number
        }

        # Initialize progress tracking
        self.progress = CLIProgress("Analyzing bug")
        self.progress.update(0, 4, "Starting analysis")

        try:
            # Select agent
            if use_genetic and self.genetic_agent:
                agent = self.genetic_agent
                agent_name = "Genetic Agent"
            elif self.vanilla_agent:
                agent = self.vanilla_agent
                agent_name = "Vanilla Agent"
            else:
                click.echo("❌ No suitable agent available", err=True)
                return

            self.progress.update(1, 4, f"Using {agent_name}")

            # Execute repair
            result = await agent.process_task(task)

            self.progress.update(2, 4, "Processing results")

            # Format output
            if output_format == "json":
                click.echo(json.dumps(result, indent=2))
            else:
                self._format_human_readable(result, agent_name)

            self.progress.update(3, 4, "Complete")

        except Exception as e:
            click.echo(f"❌ Repair failed: {e}", err=True)
            if self.progress:
                self.progress.update(4, 4, "Failed")

    def _format_human_readable(self, result: dict, agent_name: str):
        """Format result for human-readable output."""
        success = result.get("success", False)
        confidence = result.get("confidence", 0.0)
        method = result.get("method", "unknown")
        iterations = result.get("iterations", 0)

        if success:
            click.echo(f"✅ {agent_name} successfully repaired the bug!")
            click.echo(f"   Confidence: {confidence:.1%}")
            click.echo(f"   Method: {method}")
            click.echo(f"   Iterations: {iterations}")

            if "repair" in result:
                click.echo("\n   Repair:")
                click.echo(f"   {result['repair']}")

            if "explanation" in result:
                click.echo("\n   Explanation:")
                click.echo(f"   {result['explanation']}")
        else:
            click.echo(f"❌ {agent_name} could not repair the bug")
            click.echo(f"   Error: {result.get('error', 'Unknown error')}")

    async def show_status(self):
        """Show system status and statistics."""
        if not await self.initialize_agents():
            return

        click.echo("🧬 Genetic Coding Agent Status")
        click.echo("=" * 50)

        # Agent status
        click.echo("🤖 Agents:")
        if self.vanilla_agent:
            vanilla_status = self.vanilla_agent.get_status()
            click.echo(f"   ✅ Vanilla Agent: {vanilla_status.get('state', 'unknown')}")
        else:
            click.echo("   ❌ Vanilla Agent: Not initialized")

        if self.genetic_agent:
            genetic_status = self.genetic_agent.get_status()
            click.echo(f"   ✅ Genetic Agent: {genetic_status.get('state', 'unknown')}")
        else:
            click.echo("   ❌ Genetic Agent: Not initialized")

        # MCP Status
        click.echo("\n🔗 MCP Services:")
        mcp_status = {
            "Serena": "✅ Connected" if hasattr(self.config, 'serena_url') else "❌ Not configured",
            "Dope-Context": "✅ Connected" if hasattr(self.config, 'dope_context_url') else "❌ Not configured",
            "ConPort": "✅ Connected" if hasattr(self.config, 'conport_url') else "❌ Not configured"
        }

        for service, status in mcp_status.items():
            click.echo(f"   {status} {service}")

        # Performance stats (if available)
        try:
            if self.genetic_agent and hasattr(self.genetic_agent, 'memory_adapter'):
                patterns = await self.genetic_agent.memory_adapter.get_operator_success_patterns(limit=5)
                if patterns:
                    click.echo("\n📊 Top Performing Operators:")
                    for op_name, op_data in patterns.items():
                        avg_fitness = op_data.get('avg_fitness', 0)
                        success_rate = op_data.get('success_rate', 0)
                        uses = op_data.get('total_uses', 0)
                        click.echo(".3f")
        except Exception as e:
            click.echo(f"\n⚠️  Could not load performance stats: {e}")

    async def show_dashboard(self):
        """Show monitoring dashboard with success rates and operator performance."""
        if not await self.initialize_agents():
            return

        click.echo("📊 Genetic Agent Performance Dashboard")
        click.echo("=" * 60)

        try:
            if self.genetic_agent and hasattr(self.genetic_agent, 'memory_adapter'):
                # Get operator performance
                operator_patterns = await self.genetic_agent.memory_adapter.get_operator_success_patterns(limit=10)

                if operator_patterns:
                    click.echo("🎯 Operator Performance Ranking:")
                    click.echo("-" * 60)
                    click.echo("<12")
                    click.echo("-" * 60)

                    for i, (op_name, op_data) in enumerate(operator_patterns.items(), 1):
                        avg_fitness = op_data.get('avg_fitness', 0)
                        success_rate = op_data.get('success_rate', 0)
                        uses = op_data.get('total_uses', 0)

                        rank_indicator = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}.")
                        click.echo("12")

                # Get recent failure patterns
                failure_patterns = await self.genetic_agent.memory_adapter.get_failure_patterns(limit=5)

                if failure_patterns:
                    click.echo("\n🚨 Recent Failure Patterns:")
                    click.echo("-" * 60)

                    for pattern in failure_patterns[:3]:  # Show top 3
                        signals = pattern.get('signals', [])
                        timestamp = pattern.get('timestamp', 'unknown')
                        click.echo(f"   📅 {timestamp[:19]}")
                        click.echo(f"   🔍 Signals: {', '.join(signals[:3])}")
                        click.echo()

        except Exception as e:
            click.echo(f"❌ Could not load dashboard data: {e}")


# Global CLI instance
cli = GeneticAgentCLI()


@click.group()
@click.version_option(version="0.1.0")
def dmx():
    """Genetic Coding Agent CLI - dmx fix --genetic"""
    pass


@dmx.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--description', '-d', required=True, help='Bug description')
@click.option('--line', '-l', default=1, help='Line number where bug occurs')
@click.option('--genetic', '-g', is_flag=True, help='Use genetic agent instead of vanilla')
@click.option('--format', '-f', type=click.Choice(['json', 'human']), default='human',
              help='Output format')
def fix(file_path, description, line, genetic, format):
    """Fix a bug in the specified file."""
    asyncio.run(cli.repair_bug(
        file_path=Path(file_path),
        description=description,
        line_number=line,
        use_genetic=genetic,
        output_format=format
    ))


@dmx.command()
def status():
    """Show system status and agent health."""
    asyncio.run(cli.show_status())


@dmx.command()
def dashboard():
    """Show performance dashboard with success rates."""
    asyncio.run(cli.show_dashboard())


if __name__ == "__main__":
    dmx()