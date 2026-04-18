"""
Agent Loop Commands

The `dopemux agent-loop` group drives the autonomous orchestrator loop.
`start` kicks off or halts a recursive goal-execution loop; `brief`
prepares the source-of-truth PRD for a new run.
"""

import logging
from pathlib import Path
from typing import Optional

import click

from ..console import console

logger = logging.getLogger(__name__)


@click.group("agent-loop")
def agent_loop_cmd():
    """
    🤖 Grand Orchestrator: Agentic workflow execution loop

    Engage the recursive workflow engine to independently plan and execute
    tasks according to the strict Dopemux phase protocol.
    """
    pass


@agent_loop_cmd.command("start")
@click.option("--goal", help="🚀 Initiate the execution loop with a goal.", required=False)
@click.option("--stop", is_flag=True, help="🛑 Terminate an active loop.", required=False)
@click.pass_context
def agent_loop_start(ctx, goal: Optional[str], stop: bool):
    """
    🔄 Loop Controller: Manage the Orchestrator loop
    """
    from ..agent.loop import AgentLoopOrchestrator

    orchestrator = AgentLoopOrchestrator(Path.cwd())

    if stop:
        console.logger.info("[warning]Stopping the active agent loop...[/warning]")
        orchestrator.stop_loop()
        return

    if goal:
        console.logger.info(f"[info]Starting loop for goal: {goal}[/info]")
        orchestrator.start_loop(goal)
        return

    console.logger.info("[warning]Please provide --goal <goal> or --stop[/warning]")


@agent_loop_cmd.command("brief")
@click.option("--interactive", "-i", is_flag=True, help="Engage interactive PRD drafting.")
@click.pass_context
def agent_brief(ctx, interactive: bool):
    """
    📝 Brief Drafter: Prepare a source-of-truth PRD
    """
    if interactive:
        console.logger.info("[info]Starting interactive brief mapping...[/info]")
        # Placeholder for launching Claude in brief-drafter mode
        cmd = ["dopemux", "start", "--role", "brief-drafter"]
        console.logger.info(f"Executing: {' '.join(cmd)}")
    else:
        console.logger.info("[info]Brief drafter available in --interactive mode.[/info]")
