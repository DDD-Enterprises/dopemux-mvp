"""
Claude Auto Responder Integration for Dopemux

This module manages the ClaudeAutoResponder tool integration, providing
automatic Claude Code confirmation responses with ADHD-optimized controls.
"""

import logging
import subprocess
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from dopemux.config.manager import ClaudeAutoResponderConfig, ConfigManager

logger = logging.getLogger(__name__)


class AutoResponderStatus(Enum):
    """Auto responder status states."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class AutoResponderMetrics:
    """Auto responder performance metrics."""

    start_time: datetime
    responses_sent: int = 0
    last_response_time: Optional[datetime] = None
    errors_count: int = 0
    status: AutoResponderStatus = AutoResponderStatus.STOPPED

    @property
    def uptime_minutes(self) -> float:
        """Calculate uptime in minutes."""
        return (datetime.now() - self.start_time).total_seconds() / 60

    @property
    def responses_per_minute(self) -> float:
        """Calculate responses per minute rate."""
        uptime = self.uptime_minutes
        return self.responses_sent / uptime if uptime > 0 else 0


class ClaudeAutoResponderManager:
    """
    Manages ClaudeAutoResponder integration with ADHD-optimized features.

    Features:
    - Automatic startup/shutdown with Dopemux sessions
    - Attention-aware response delays
    - Terminal scope management
    - Activity timeout handling
    - Integration with attention monitoring
    """

    def __init__(self, config_manager: ConfigManager, project_path: Path):
        """Initialize auto responder manager."""
        self.config_manager = config_manager
        self.project_path = project_path
        self.data_dir = project_path / ".dopemux" / "autoresponder"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._process: Optional[subprocess.Popen] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._metrics = AutoResponderMetrics(start_time=datetime.now())

        # Setup ClaudeAutoResponder repository
        self.car_repo_path = self.data_dir / "ClaudeAutoResponder"
        self.car_executable = self.car_repo_path / "claude_auto_responder.py"

        # ADHD-specific features
        self._last_activity = datetime.now()
        self._attention_state = "normal"

    def setup_autoresponder(self) -> bool:
        """Setup ClaudeAutoResponder repository and dependencies."""
        try:
            if not self.car_repo_path.exists():
                logger.info("Cloning ClaudeAutoResponder repository...")
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "https://github.com/BeehiveInnovations/ClaudeAutoResponder.git",
                        str(self.car_repo_path),
                    ],
                    check=True,
                    capture_output=True,
                )

            # Run setup if needed
            setup_script = self.car_repo_path / "setup.py"
            if setup_script.exists():
                logger.info("Running ClaudeAutoResponder setup...")
                subprocess.run(
                    ["python3", str(setup_script)],
                    cwd=self.car_repo_path,
                    check=True,
                    capture_output=True,
                )

            # Create whitelist configuration
            self._setup_whitelist()

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to setup ClaudeAutoResponder: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during setup: {e}")
            return False

    def _setup_whitelist(self) -> None:
        """Setup whitelisted tools configuration."""
        config = self.config_manager.get_claude_autoresponder_config()

        if config.whitelist_tools:
            whitelist_content = """# Dopemux Auto-Responder Whitelist
# Tools that are safe for automatic confirmation
Read
Write
Edit
MultiEdit
Bash
Glob
Grep
TodoWrite
WebFetch
WebSearch
Task
"""
            whitelist_path = self.car_repo_path / "whitelisted_tools.txt"
            whitelist_path.write_text(whitelist_content)

    def start(self) -> bool:
        """Start the auto responder with current configuration."""
        if self.is_running():
            logger.warning("Auto responder already running")
            return True

        config = self.config_manager.get_claude_autoresponder_config()
        if not config.enabled:
            logger.info("Auto responder disabled in configuration")
            return False

        # Setup if needed
        if not self.car_executable.exists():
            if not self.setup_autoresponder():
                return False

        try:
            self._metrics = AutoResponderMetrics(start_time=datetime.now())
            self._metrics.status = AutoResponderStatus.STARTING

            # Build command arguments
            cmd = self._build_command(config)

            logger.info(f"Starting ClaudeAutoResponder: {' '.join(cmd)}")
            self._process = subprocess.Popen(
                cmd,
                cwd=self.car_repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Start monitoring thread
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(target=self._monitor_process)
            self._monitor_thread.daemon = True
            self._monitor_thread.start()

            # Give it a moment to start
            time.sleep(0.5)

            if self._process and self._process.poll() is None:
                self._metrics.status = AutoResponderStatus.RUNNING
                logger.info("Auto responder started successfully")
                return True
            else:
                self._metrics.status = AutoResponderStatus.ERROR
                logger.error("Auto responder failed to start")
                return False

        except Exception as e:
            self._metrics.status = AutoResponderStatus.ERROR
            logger.error(f"Failed to start auto responder: {e}")
            return False

    def stop(self) -> bool:
        """Stop the auto responder."""
        if not self.is_running():
            return True

        try:
            self._metrics.status = AutoResponderStatus.STOPPING
            logger.info("Stopping auto responder...")

            # Signal monitoring thread to stop
            self._stop_event.set()

            # Terminate process
            if self._process:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.warning("Force killing auto responder process")
                    self._process.kill()
                    self._process.wait()

            # Wait for monitor thread
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=3)

            self._process = None
            self._monitor_thread = None
            self._metrics.status = AutoResponderStatus.STOPPED

            logger.info("Auto responder stopped")
            return True

        except Exception as e:
            self._metrics.status = AutoResponderStatus.ERROR
            logger.error(f"Error stopping auto responder: {e}")
            return False

    def is_running(self) -> bool:
        """Check if auto responder is currently running."""
        return (
            self._process is not None
            and self._process.poll() is None
            and self._metrics.status == AutoResponderStatus.RUNNING
        )

    def get_status(self) -> Dict[str, Any]:
        """Get current status and metrics."""
        return {
            "status": self._metrics.status.value,
            "running": self.is_running(),
            "uptime_minutes": self._metrics.uptime_minutes,
            "responses_sent": self._metrics.responses_sent,
            "responses_per_minute": self._metrics.responses_per_minute,
            "errors_count": self._metrics.errors_count,
            "last_response": (
                self._metrics.last_response_time.isoformat()
                if self._metrics.last_response_time
                else None
            ),
            "attention_state": self._attention_state,
            "config": self.config_manager.get_claude_autoresponder_config().dict(),
        }

    def update_attention_state(self, attention_state: str) -> None:
        """Update current attention state for adaptive responses."""
        self._attention_state = attention_state
        self._last_activity = datetime.now()

        # Adaptive response delays based on attention state
        config = self.config_manager.get_claude_autoresponder_config()
        if attention_state == "scattered" and config.response_delay < 1.0:
            # Add slight delay when scattered to reduce overwhelm
            logger.debug("Adding response delay due to scattered attention")

    def _build_command(self, config: ClaudeAutoResponderConfig) -> List[str]:
        """Build command line for ClaudeAutoResponder."""
        cmd = ["python3", str(self.car_executable)]

        # Response delay
        if config.response_delay > 0:
            cmd.extend(["--delay", str(config.response_delay)])

        # Terminal scope
        if config.terminal_scope == "all":
            cmd.append("--multi-window")
        elif config.terminal_scope == "current":
            cmd.append("--single-window")

        # Debug mode
        if config.debug_mode:
            cmd.append("--debug")

        # Whitelist tools (if file exists)
        whitelist_path = self.car_repo_path / "whitelisted_tools.txt"
        if config.whitelist_tools and whitelist_path.exists():
            cmd.extend(["--whitelist", str(whitelist_path)])

        return cmd

    def _monitor_process(self) -> None:
        """Monitor the auto responder process."""
        config = self.config_manager.get_claude_autoresponder_config()
        timeout_delta = timedelta(minutes=config.timeout_minutes)

        while not self._stop_event.is_set():
            try:
                # Check if process is still running
                if self._process and self._process.poll() is not None:
                    logger.warning("Auto responder process died unexpectedly")
                    self._metrics.status = AutoResponderStatus.ERROR
                    self._metrics.errors_count += 1
                    break

                # Check timeout
                if datetime.now() - self._last_activity > timeout_delta:
                    logger.info("Auto responder timeout reached, stopping")
                    self.stop()
                    break

                # Read output for response counting (basic parsing)
                if self._process and self._process.stdout:
                    # Non-blocking read attempt
                    import select

                    if select.select([self._process.stdout], [], [], 0.1)[0]:
                        line = self._process.stdout.readline()
                        if line and "response sent" in line.lower():
                            self._metrics.responses_sent += 1
                            self._metrics.last_response_time = datetime.now()
                            self._last_activity = datetime.now()

                time.sleep(1)

            except Exception as e:
                logger.error(f"Error in monitor thread: {e}")
                self._metrics.errors_count += 1
                time.sleep(5)

    def restart(self) -> bool:
        """Restart the auto responder."""
        logger.info("Restarting auto responder...")
        self.stop()
        time.sleep(1)
        return self.start()

    def update_config(self, **kwargs) -> bool:
        """Update configuration and restart if running."""
        self.config_manager.update_claude_autoresponder(**kwargs)

        if self.is_running():
            return self.restart()

        return True


def create_autoresponder_manager(
    config_manager: ConfigManager, project_path: Path
) -> ClaudeAutoResponderManager:
    """Factory function to create auto responder manager."""
    return ClaudeAutoResponderManager(config_manager, project_path)
