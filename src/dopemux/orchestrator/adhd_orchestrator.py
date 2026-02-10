"""
ADHD Orchestrator Integration for Dopemux

Integrates ADHD workflow management, visual progress display, and interactive
prompts into the main Dopemux orchestrator. Provides seamless ADHD-optimized
workflow management across all Dopemux operations.
"""

import asyncio

import logging

logger = logging.getLogger(__name__)
from ..config import ConfigManager

from typing import Dict, Any, Optional
from datetime import datetime

from ..adhd.workflow_manager import ADHDWorkflowManager
from ..ux.progress_display import ProgressDisplay
from ..ux.interactive_prompts import InteractivePrompts
from ..tmux.controller import TmuxController
from ..tmux.layouts import EnergyLayoutManager
from ..adhd.attention_monitor import AttentionMonitor, AttentionState, AttentionMetrics
from pathlib import Path

from ..console import console

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
        
        # Tmux integration
        self.tmux_controller = TmuxController()
        self.layout_manager = EnergyLayoutManager(self.tmux_controller)
        self.attention_monitor: Optional[AttentionMonitor] = None

        # Session state
        self.active_session = None
        self.current_operation = None

    def enable_attention_monitoring(self, project_path: Path) -> None:
        """
        Enable Attention Monitor and wire it to dynamic layout switching.
        
        Args:
            project_path: Path to the project root for storing metrics.
        """
        if self.attention_monitor:
            logger.warning("Attention monitoring already enabled")
            return

        config_manager = ConfigManager()
        attention_config = config_manager.load_config().attention

        self.attention_monitor = AttentionMonitor(project_path, config=attention_config)
        self.attention_monitor.add_callback(self._on_attention_update)
        self.attention_monitor.start_monitoring()
        logger.info("Enabled dynamic attention monitoring")

    def _on_attention_update(self, metrics: AttentionMetrics) -> None:
        """
        Callback for attention state updates.
        Triggers layout changes based on state transitions.
        """
        state_to_energy = {
            AttentionState.SCATTERED: "low",
            AttentionState.DISTRACTED: "low",
            AttentionState.NORMAL: "medium",
            AttentionState.FOCUSED: "high",
            AttentionState.HYPERFOCUS: "high"
        }
        
        energy_level = state_to_energy.get(metrics.attention_state, "medium")
        
        # Only switch if we have an active session tracked
        # For now, we apply to 'active_session' if set, or just log
        # In a real scenario, we might want to target the currently focused session in tmux
        try:
             # We need to know which session to apply to.
             # If we have self.active_session (ADHD session), we might assume it maps to a tmux session?
             # Or we ask controller for active session.
             current_session = self.tmux_controller.get_active_session_name()
             if current_session:
                 self.apply_energy_layout(current_session, energy_level)
                 self._publish_attention_state(current_session, metrics.attention_state)
        except Exception as e:
             logger.warning(f"Failed to auto-apply energy layout: {e}")

    def _publish_attention_state(self, session: str, state: AttentionState) -> None:
        """Publish attention state to tmux options for status bar integration."""
        icons = {
            AttentionState.SCATTERED: "🌫️",
            AttentionState.DISTRACTED: "🐿️",
            AttentionState.NORMAL: "👤",
            AttentionState.FOCUSED: "🧠",
            AttentionState.HYPERFOCUS: "🔥"
        }
        icon = icons.get(state, "❓")
        
        try:
            self.tmux_controller.set_session_option(session, "@adhd_state", state)
            self.tmux_controller.set_session_option(session, "@adhd_icon", icon)
            # Optional: Refresh client to update status bar immediately
            # self.tmux_controller.server.cmd("refresh-client", "-S") # access to server? No.
        except Exception as e:
            logger.debug("Failed to publish attention state for session %s: %s", session, e)


    def apply_energy_layout(self, session_name: str, energy_level: str) -> None:
        """
        Apply an energy-appropriate layout to the specified session.
        
        Args:
            session_name: The tmux session name.
            energy_level: 'low', 'medium', or 'high'.
        """
        self.layout_manager.apply_layout(session_name, energy_level)

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
                console.log(f"[yellow]Taking break: {selected_break}[/yellow]")
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
                console.log(f"[yellow]Taking break: {selected_activity}[/yellow]")
                
                # Enter visual break mode
                self.enter_break_mode(self.workflow_manager.break_duration_minutes)
                
                try:
                    await asyncio.sleep(self.workflow_manager.break_duration_minutes * 60)
                finally:
                    self.exit_break_mode()
                
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

    def enter_break_mode(self, duration_minutes: int) -> None:
        """
        Enter a visual break mode in tmux.
        Displays a full-screen popup to encourage stepping away.
        """
        try:
             # We use a simple shell command to display the break message
             # 'read' keeps it open until timeout or user interaction, but we want it to persist?
             # actually sleep is better.
             seconds = int(duration_minutes * 60)
             cmd = f"echo '🌿 BREAK TIME 🌿\n\nTake a breath.\nStep away from the screen.\n\nResuming in {duration_minutes} minutes...'; sleep {seconds}"
             self.tmux_controller.display_popup(cmd, width="100%", height="100%")
        except Exception as e:
             logger.warning(f"Failed to enter break mode: {e}")

    def exit_break_mode(self) -> None:
        """Exit break mode (close popup)."""
        # Try to close popup early by sending Escape to active pane.
        # If popup already exited, this is a no-op.
        try:
            panes = self.tmux_controller.list_panes()
            active = next((p for p in panes if p.active), None)
            if active:
                self.tmux_controller.send_key(active.pane_id, "Escape")
        except Exception as e:
            logger.debug("Failed to exit break mode popup explicitly: %s", e)

    def end_session(self) -> Dict[str, Any]:
        """End the current session."""
        if self.active_session:
            summary = self.workflow_manager.end_session()
            self.active_session = None
            return summary
        return {"error": "No active session"}


# Global instance for easy access
# Global instance removed to prevent import side effects
# adhd_orchestrator = ADHDOrchestrator()


# Convenience functions for orchestrator integration
async def execute_adhd_optimized(operation, **kwargs):
    """Convenience function for ADHD-optimized operation execution."""
    # Ensure fresh instance or Singleton pattern properly implemented if needed
    # For now, create new instance to avoid global state issues
    orchestrator = ADHDOrchestrator()
    return await orchestrator.execute_with_adhd_optimization(operation, **kwargs)


async def prompt_adhd_action(actions: list, context: str = "") -> Optional[str]:
    """Convenience function for ADHD-optimized prompting."""
    orchestrator = ADHDOrchestrator()
    return await orchestrator.prompt_user_action(actions, context)


def get_adhd_status() -> Dict[str, Any]:
    """Get current ADHD status."""
    orchestrator = ADHDOrchestrator()
    return orchestrator.get_status_snapshot()
