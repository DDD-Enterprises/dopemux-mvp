"""
ADHD Orchestrator Integration for Dopemux

Integrates ADHD workflow management, visual progress display, and interactive
prompts into the main Dopemux orchestrator. Provides seamless ADHD-optimized
workflow management across all Dopemux operations.
"""

import asyncio

import logging

logger = logging.getLogger(__name__)

from typing import Dict, Any, Optional
from datetime import datetime

from ..adhd.workflow_manager import ADHDWorkflowManager
from ..ux.progress_display import ProgressDisplay
from ..ux.interactive_prompts import InteractivePrompts

class ADHDOrchestrator:
    """
    Main orchestrator for ADHD-optimized workflows in Dopemux.

    Coordinates between workflow management, visual feedback, and user
    interactions to create a cohesive ADHD-friendly development experience.
    """

    def __init__(self):
        self.workflow_manager = ADHDWorkflowManager()
        self.progress_display = ProgressDisplay()
        self.interactive_prompts = InteractivePrompts()

        # Session state
        self.active_session = None
        self.current_operation = None

    async def execute_with_adhd_optimization(self, operation: callable, **kwargs) -> Any:
        """
        Execute an operation with ADHD workflow optimizations.

        Args:
            operation: The operation to execute (async function)
            **kwargs: Arguments for the operation

        Returns:
            Result of the operation
        """
        # Start session if not active
        if not self.active_session:
            self.active_session = self.workflow_manager.start_session(
                task_description=kwargs.get('task_description', 'Dopemux operation')
            )

        # Update cognitive load before operation
        self.workflow_manager.update_cognitive_load(
            load_level=0.5,  # Default starting load
            context=f"Starting {operation.__name__}"
        )

        try:
            # Show progress with complexity awareness
            complexity = kwargs.get('complexity', 0.5)
            total_steps = kwargs.get('total_steps', None)

            self.progress_display.show_operation_start(
                operation_name=operation.__name__,
                total_steps=total_steps,
                complexity=complexity
            )

            # Execute operation
            result = await operation(**kwargs)

            # Update progress completion
            self.progress_display.show_operation_complete(
                operation_name=operation.__name__,
                duration=kwargs.get('duration', 0.0),
                success=True,
                results={"result": result}
            )

            # Update cognitive load after operation
            self.workflow_manager.update_cognitive_load(
                load_level=complexity,  # Use operation complexity
                context=f"Completed {operation.__name__}"
            )

            return result

        except Exception as e:
            # Show error with ADHD-friendly display
            self.progress_display.show_error(
                operation_name=operation.__name__,
                error=str(e),
                complexity=0.8  # High load for errors
            )

            # Update load for error condition
            self.workflow_manager.update_cognitive_load(
                load_level=0.8,
                context=f"Error in {operation.__name__}"
            )

            raise e

            logger.error(f"Error: {e}")
    async def prompt_user_action(self, actions: list, context: str = "") -> Optional[str]:
        """
        Prompt user for action selection with ADHD optimizations.

        Args:
            actions: List of available actions
            context: Context for the prompt

        Returns:
            Selected action or None
        """
        # Check if break is needed first
        break_suggestion = self.workflow_manager.suggest_break()
        if break_suggestion['suggested']:
            selected_break = self.interactive_prompts.ask_break_suggestion(break_suggestion)
            if selected_break:
                self.workflow_manager.take_break()
                console.logger.info(f"[yellow]Taking break: {selected_break}[/yellow]")
                # Wait for break duration
                await asyncio.sleep(self.workflow_manager.break_duration_minutes * 60)

        # Get progressive info based on current load
        current_load = self.workflow_manager._calculate_avg_cognitive_load()
        user_level = "beginner" if current_load > 0.7 else "intermediate"

        # Prompt with limited choices
        selected_action = self.interactive_prompts.ask_action_selection(
            actions=actions,
            context=context
        )

        # Log the decision
        self.workflow_manager.update_cognitive_load(
            load_level=current_load + 0.1,  # Decision-making load
            context=f"User decision: {selected_action}"
        )

        return selected_action

    async def check_and_suggest_break(self) -> bool:
        """
        Check if break is needed and suggest if appropriate.

        Returns:
            Whether break was taken
        """
        break_needed, reason = self.workflow_manager.check_break_needed()

        if break_needed:
            suggestion = self.workflow_manager.suggest_break()
            selected_activity = self.interactive_prompts.ask_break_suggestion(suggestion)

            if selected_activity:
                self.workflow_manager.take_break()
                console.logger.info(f"[yellow]Taking break: {selected_activity}[/yellow]")
                await asyncio.sleep(self.workflow_manager.break_duration_minutes * 60)
                return True

        return False

    def get_status_snapshot(self) -> Dict[str, Any]:
        """
        Get current ADHD workflow status.

        Returns:
            Complete status snapshot
        """
        status = self.workflow_manager.get_context_snapshot()
        status['current_operation'] = self.current_operation
        status['break_recommended'] = self.workflow_manager.check_break_needed()[0]

        return status

    def start_session(self, task_description: str = "") -> Dict[str, Any]:
        """Start a new ADHD-optimized session."""
        self.active_session = self.workflow_manager.start_session(task_description)
        return self.active_session

    def end_session(self) -> Dict[str, Any]:
        """End the current session."""
        if self.active_session:
            summary = self.workflow_manager.end_session()
            self.active_session = None
            return summary
        return {"error": "No active session"}


# Global instance for easy access
adhd_orchestrator = ADHDOrchestrator()


# Convenience functions for orchestrator integration
async def execute_adhd_optimized(operation, **kwargs):
    """Convenience function for ADHD-optimized operation execution."""
    return await adhd_orchestrator.execute_with_adhd_optimization(operation, **kwargs)


async def prompt_adhd_action(actions: list, context: str = "") -> Optional[str]:
    """Convenience function for ADHD-optimized prompting."""
    return await adhd_orchestrator.prompt_user_action(actions, context)


def get_adhd_status() -> Dict[str, Any]:
    """Get current ADHD status."""
    return adhd_orchestrator.get_status_snapshot()
