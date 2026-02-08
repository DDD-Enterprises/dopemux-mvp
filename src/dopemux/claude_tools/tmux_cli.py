"""
Tmux CLI Integration for Claude-Code-Tools

Provides programmatic control over tmux sessions, enabling AI agents to:
- Launch applications in tmux panes
- Send keystrokes and commands
- Capture output from panes
- Manage pane lifecycle

Based on Claude-Code-Tools tmux-cli functionality.
"""

import subprocess
import json
import time
import logging

logger = logging.getLogger(__name__)
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from ..tmux.controller import TmuxController


@dataclass
class PaneInfo:
    """Information about a tmux pane."""
    session: str
    window: str
    pane: str
    command: str
    active: bool = False

    @property
    def pane_id(self) -> str:
        """Get the full pane identifier."""
        return f"{self.session}:{self.window}.{self.pane}"


class TmuxCliError(Exception):
    """Raised when tmux-cli operations fail."""
    pass


class TmuxCli:
    """
    Claude-Code-Tools tmux-cli integration for Dopemux.

    Provides programmatic control over tmux for AI agents,
    enabling interactive terminal automation.
    """

    def __init__(self, controller: Optional[TmuxController] = None):
        """
        Initialize tmux-cli integration.

        Args:
            controller: Optional TmuxController instance
        """
        self.controller = controller or TmuxController()

    def launch(self, command: str, session_name: Optional[str] = None) -> PaneInfo:
        """
        Launch a command in a new tmux pane.

        Args:
            command: Command to execute
            session_name: Optional session name

        Returns:
            PaneInfo for the created pane
        """
        try:
            # Create new window with the command
            window_name = f"claude-tool-{hash(command) % 1000}"
            # Run the tmux command safely without shell
            from dopemux.safe_subprocess import run
            result = run(["tmux", "new-window", "-d", "-n", window_name, command])

            if result.returncode != 0:
                raise TmuxCliError(f"Tmux command failed: {result.stderr}")

            # Get the current session name if not provided
            if not session_name:
                from dopemux.safe_subprocess import run
                session_result = run(["tmux", "display-message", "-p", "#{session_name}"], check=False)
                session_name = session_result.stdout.strip() if session_result.returncode == 0 else "dopemux"

            return PaneInfo(
                session=session_name,
                window=window_name,
                pane="0",  # Default pane in new window
                command=command
            )
        except Exception as e:
            raise TmuxCliError(f"Failed to launch command: {e}")

            logger.error(f"Error: {e}")
    def send(self, text: str, pane_id: str, enter: bool = True,
             delay_enter: float = 0.1) -> None:
        """
        Send text input to a tmux pane.

        Args:
            text: Text to send
            pane_id: Target pane identifier (session:window.pane)
            enter: Whether to send Enter after text
            delay_enter: Delay before sending Enter
        """
        try:
            import subprocess

            # Send the text to the pane
            from dopemux.safe_subprocess import run
            result = run(["tmux", "send-keys", "-t", pane_id, text])

            if result.returncode != 0:
                raise TmuxCliError(f"Failed to send text: {result.stderr}")

            # Send Enter if requested
            if enter:
                if delay_enter > 0:
                    time.sleep(delay_enter)
                from dopemux.safe_subprocess import run
                enter_result = run(["tmux", "send-keys", "-t", pane_id, "Enter"], check=False)
                if enter_result.returncode != 0:
                    raise TmuxCliError(f"Failed to send Enter: {enter_result.stderr}")

        except Exception as e:
            raise TmuxCliError(f"Failed to send input to pane {pane_id}: {e}")

            logger.error(f"Error: {e}")
    def capture(self, pane_id: str, lines: int = 100) -> str:
        """
        Capture output from a tmux pane.

        Args:
            pane_id: Target pane identifier
            lines: Number of lines to capture

        Returns:
            Captured output text
        """
        try:
            import subprocess

            # Capture pane content using tmux capture-pane
            from dopemux.safe_subprocess import run
            result = run(["tmux", "capture-pane", "-p", "-S", f"-{lines}", "-t", pane_id])

            if result.returncode != 0:
                raise TmuxCliError(f"Failed to capture pane: {result.stderr}")

            return result.stdout

        except Exception as e:
            raise TmuxCliError(f"Failed to capture output from pane {pane_id}: {e}")

            logger.error(f"Error: {e}")
    def interrupt(self, pane_id: str) -> None:
        """
        Send interrupt signal (Ctrl+C) to a pane.

        Args:
            pane_id: Target pane identifier
        """
        try:
            import subprocess

            # Send Ctrl+C to the pane
            from dopemux.safe_subprocess import run
            result = run(["tmux", "send-keys", "-t", pane_id, "C-c"], check=False)

            if result.returncode != 0:
                raise TmuxCliError(f"Failed to interrupt pane: {result.stderr}")

        except Exception as e:
            raise TmuxCliError(f"Failed to interrupt pane {pane_id}: {e}")

            logger.error(f"Error: {e}")
    def kill(self, pane_id: str) -> None:
        """
        Kill a tmux pane.

        Args:
            pane_id: Target pane identifier
        """
        try:
            import subprocess

            # Kill the pane using tmux kill-pane
            from dopemux.safe_subprocess import run
            result = run(["tmux", "kill-pane", "-t", pane_id])

            if result.returncode != 0:
                raise TmuxCliError(f"Failed to kill pane: {result.stderr}")

        except Exception as e:
            raise TmuxCliError(f"Failed to kill pane {pane_id}: {e}")

            logger.error(f"Error: {e}")
    def list_panes(self, session_name: Optional[str] = None) -> List[PaneInfo]:
        """
        List all panes in a session.

        Args:
            session_name: Optional session name filter

        Returns:
            List of PaneInfo objects
        """
        try:
            import subprocess

            if session_name:
                args = ["tmux", "list-panes", "-s", "-t", session_name, "-F", "#{session_name} #{window_index} #{pane_index} #{pane_active} #{pane_command}"]
            else:
                args = ["tmux", "list-panes", "-s", "-F", "#{session_name} #{window_index} #{pane_index} #{pane_active} #{pane_command}"]

            from dopemux.safe_subprocess import run
            result = run(args, check=False)

            if result.returncode != 0:
                raise TmuxCliError(f"Tmux list-panes failed: {result.stderr}")

            panes = []
            for line in result.stdout.strip().split('\n'):
                if line.strip():
                    parts = line.split(maxsplit=4)
                    if len(parts) >= 4:
                        session, window, pane, active, *command = parts
                        panes.append(PaneInfo(
                            session=session,
                            window=window,
                            pane=pane,
                            command=' '.join(command) if command else "",
                            active=active == '1'
                        ))

            return panes

        except Exception as e:
            raise TmuxCliError(f"Failed to list panes: {e}")

            logger.error(f"Error: {e}")
    def wait_idle(self, pane_id: str, idle_time: float = 2.0,
                  timeout: float = 30.0) -> bool:
        """
        Wait for a pane to become idle.

        Args:
            pane_id: Target pane identifier
            idle_time: Time with no output changes
            timeout: Maximum wait time

        Returns:
            True if pane became idle, False if timeout
        """
        start_time = time.time()
        last_output = ""

        while time.time() - start_time < timeout:
            try:
                current_output = self.capture(pane_id, lines=10)
                if current_output == last_output:
                    # Check if we've been idle for the required time
                    if time.time() - start_time >= idle_time:
                        return True
                else:
                    last_output = current_output
                    start_time = time.time()  # Reset timer
            except Exception as e:
                logger.error(f"Error: {e}")
            time.sleep(0.1)

        return False

    def status(self) -> Dict[str, Any]:
        """
        Get current tmux status.

        Returns:
            Status information dictionary
        """
        try:
            import subprocess

            # Get current pane
            from dopemux.safe_subprocess import run
            current_result = run(["tmux", "display-message", "-p", "#{session_name}:#{window_index}.#{pane_index}"], check=False)

            if current_result.returncode == 0:
                current_location = current_result.stdout.strip()
            else:
                current_location = "unknown"

            # Get all panes
            panes = self.list_panes()

            return {
                "current_location": current_location,
                "panes": [
                    {
                        "id": pane.pane_id,
                        "command": pane.command,
                        "active": pane.active
                    }
                    for pane in panes
                ]
            }
        except Exception as e:
            raise TmuxCliError(f"Failed to get status: {e}")