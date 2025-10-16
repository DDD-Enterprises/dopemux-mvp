"""
Agent Spawner with PTY Support
FIX for TTY requirement - gives AI CLIs real terminal

Key change: Use pty.spawn() or pty.openpty() instead of subprocess.Popen
This provides a pseudo-terminal so CLIs think they're in interactive mode

Complexity: 0.70 (Higher due to PTY handling)
"""

import pty
import os
import select
import subprocess
import threading
import time
from typing import Optional
from enum import Enum
from dataclasses import dataclass


class AgentType(Enum):
    """Available AI CLI agents."""

    CLAUDE = "claude"
    GEMINI = "gemini"
    CODEX = "codex"
    AIDER = "aider"


class AgentStatus(Enum):
    """Agent lifecycle states."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    ERROR = "error"
    CRASHED = "crashed"


@dataclass
class AgentConfig:
    """Configuration for AI agent instance."""

    agent_type: AgentType
    command: list[str]
    env: dict[str, str]
    auto_restart: bool = True
    max_restarts: int = 3


class PTYAgent:
    """
    AI CLI agent with PTY (pseudo-terminal) support.

    Solves: "stdout is not a terminal" errors
    Provides: Real terminal to CLI, enabling interactive features
    """

    def __init__(self, config: AgentConfig):
        """Initialize PTY-based agent."""
        self.config = config
        self.status = AgentStatus.STOPPED
        self.master_fd: Optional[int] = None
        self.slave_fd: Optional[int] = None
        self.pid: Optional[int] = None
        self.output_buffer: list[str] = []
        self.output_thread: Optional[threading.Thread] = None
        self.running = False

    def start(self) -> bool:
        """
        Start AI CLI with PTY.

        Returns:
            True if started successfully
        """
        if self.status == AgentStatus.RUNNING:
            return True

        try:
            self.status = AgentStatus.STARTING
            print(f"🚀 Starting {self.config.agent_type.value} with PTY...")

            # Create pseudo-terminal
            self.master_fd, self.slave_fd = pty.openpty()

            # Fork and exec the command
            self.pid = os.fork()

            if self.pid == 0:
                # Child process
                os.close(self.master_fd)

                # Set slave as stdin/stdout/stderr
                os.dup2(self.slave_fd, 0)  # stdin
                os.dup2(self.slave_fd, 1)  # stdout
                os.dup2(self.slave_fd, 2)  # stderr

                os.close(self.slave_fd)

                # Update environment
                env = os.environ.copy()
                env.update(self.config.env)

                # Exec the command
                os.execvpe(self.config.command[0], self.config.command, env)

            else:
                # Parent process
                os.close(self.slave_fd)

                # Start output reader thread
                self.running = True
                self.output_thread = threading.Thread(target=self._read_output, daemon=True)
                self.output_thread.start()

                # Wait briefly to check if crashes
                time.sleep(1)

                # Check if process still alive
                try:
                    pid, status = os.waitpid(self.pid, os.WNOHANG)
                    if pid != 0:
                        # Process exited
                        self.status = AgentStatus.CRASHED
                        print(f"❌ {self.config.agent_type.value} crashed immediately")
                        return False
                except OSError:
                    pass

                self.status = AgentStatus.RUNNING
                print(f"✅ {self.config.agent_type.value} running (PID: {self.pid})")
                return True

        except Exception as e:
            self.status = AgentStatus.ERROR
            print(f"❌ Failed to start {self.config.agent_type.value}: {e}")
            return False

    def _read_output(self):
        """Read output from PTY in background thread."""
        while self.running and self.master_fd:
            try:
                # Check if data available
                ready, _, _ = select.select([self.master_fd], [], [], 0.1)

                if ready:
                    data = os.read(self.master_fd, 4096)
                    if data:
                        decoded = data.decode("utf-8", errors="ignore")
                        lines = decoded.split("\n")
                        self.output_buffer.extend(lines)

                        # Keep buffer limited
                        if len(self.output_buffer) > 1000:
                            self.output_buffer = self.output_buffer[-1000:]

            except OSError:
                # PTY closed
                break
            except Exception as e:
                print(f"⚠️ Output reader error: {e}")
                break

    def send_command(self, command: str) -> bool:
        """
        Send command to AI via PTY.

        Args:
            command: Command to send

        Returns:
            True if sent successfully
        """
        if self.status != AgentStatus.RUNNING or not self.master_fd:
            return False

        try:
            # Write to PTY master
            os.write(self.master_fd, f"{command}\n".encode("utf-8"))
            return True
        except Exception as e:
            print(f"❌ Failed to send: {e}")
            return False

    def get_output(self, clear: bool = False) -> list[str]:
        """
        Get output from agent.

        Args:
            clear: Clear buffer after reading

        Returns:
            Lines of output
        """
        output = self.output_buffer.copy()

        if clear:
            self.output_buffer.clear()

        return output

    def is_healthy(self) -> bool:
        """Check if agent is healthy."""
        if self.status != AgentStatus.RUNNING:
            return False

        if not self.pid:
            return False

        # Check if process still alive
        try:
            pid, status = os.waitpid(self.pid, os.WNOHANG)
            if pid != 0:
                # Process exited
                self.status = AgentStatus.CRASHED
                return False
        except OSError:
            return False

        return True

    def stop(self):
        """Stop the agent."""
        self.running = False

        if self.pid:
            try:
                os.kill(self.pid, 15)  # SIGTERM
                time.sleep(1)

                # Check if still alive
                try:
                    os.waitpid(self.pid, os.WNOHANG)
                except:
                    pass

            except:
                pass

        if self.master_fd:
            try:
                os.close(self.master_fd)
            except:
                pass

        self.status = AgentStatus.STOPPED
        print(f"✅ {self.config.agent_type.value} stopped")


if __name__ == "__main__":
    """Test PTY agent."""

    print("Testing PTY Agent Spawning:")
    print("=" * 60)

    # Test with Claude
    agent = PTYAgent(
        AgentConfig(
            agent_type=AgentType.CLAUDE,
            command=["/Users/hue/.local/bin/claude", "chat"],
            env={},
        )
    )

    success = agent.start()
    print(f"\nAgent started: {success}")
    print(f"Status: {agent.status.value}")

    if success:
        time.sleep(2)

        # Check output
        output = agent.get_output()
        print(f"\nCaptured {len(output)} lines of output")
        if output:
            print(f"First few lines:")
            for line in output[:5]:
                print(f"  {line[:80]}")

        # Try sending command
        print("\nSending test command...")
        agent.send_command("What is 2+2?")

        time.sleep(3)

        # Get response
        new_output = agent.get_output(clear=True)
        print(f"New output: {len(new_output)} lines")

    # Cleanup
    input("\nPress Enter to stop agent...")
    agent.stop()

    print("\n✅ PTY test complete")
