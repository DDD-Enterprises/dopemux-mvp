"""
Agent Spawner - Step 3 of Phase 1 (REFINED DESIGN)
Spawn and manage AI CLI instances using subprocess (not pure tmux)

Based on Zen architectural validation:
- subprocess.Popen for reliable control
- Optional tmux panes for visibility
- ConPort for context sharing between agents

Complexity: 0.65 (Medium-High)
Effort: 6 focus blocks (150 minutes)
"""

from typing import Optional, Literal
from dataclasses import dataclass
from enum import Enum
import subprocess
import threading
import queue
import time
import libtmux


class AgentType(Enum):
    """Available AI CLI agents."""

    DOPE_BRAINZ = "dope_brainz"
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
    command: list[str]  # CLI command + args
    env: dict[str, str]  # Environment variables
    tmux_pane: Optional[str] = None  # Optional pane for visibility
    auto_restart: bool = True
    max_restarts: int = 3
    health_check_interval: int = 30  # seconds


class AIAgent:
    """
    Manages a single AI CLI instance.

    Control via subprocess.Popen (reliable)
    Optional tmux mirroring (visibility)
    """

    def __init__(self, config: AgentConfig):
        """
        Initialize AI agent.

        Args:
            config: Agent configuration
        """
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.status = AgentStatus.STOPPED
        self.output_queue: queue.Queue = queue.Queue()
        self.restart_count = 0
        self.last_health_check: Optional[float] = None

    def start(self) -> bool:
        """
        Start the AI CLI process.

        Returns:
            True if started successfully, False otherwise
        """
        if self.status == AgentStatus.RUNNING:
            print(f"⚠️ {self.config.agent_type.value} already running")
            return True

        try:
            self.status = AgentStatus.STARTING
            print(f"🚀 Starting {self.config.agent_type.value}...")

            # Start subprocess
            self.process = subprocess.Popen(
                self.config.command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                env={**subprocess.os.environ, **self.config.env},
            )

            # Start output reader thread
            self.output_thread = threading.Thread(
                target=self._read_output, daemon=True
            )
            self.output_thread.start()

            # Start error reader thread
            self.error_thread = threading.Thread(
                target=self._read_errors, daemon=True
            )
            self.error_thread.start()

            # Wait briefly to check if process crashes immediately
            time.sleep(1)

            if self.process.poll() is None:
                # Still running
                self.status = AgentStatus.RUNNING
                print(f"✅ {self.config.agent_type.value} running (PID: {self.process.pid})")
                return True
            else:
                # Crashed immediately
                self.status = AgentStatus.CRASHED
                print(f"❌ {self.config.agent_type.value} crashed on startup")
                return False

        except Exception as e:
            self.status = AgentStatus.ERROR
            print(f"❌ Failed to start {self.config.agent_type.value}: {e}")
            return False

    def _read_output(self):
        """Read stdout in background thread."""
        if not self.process or not self.process.stdout:
            return

        try:
            for line in self.process.stdout:
                self.output_queue.put(("stdout", line))

                # Mirror to tmux pane if configured
                if self.config.tmux_pane:
                    self._mirror_to_tmux(line)
        except Exception as e:
            print(f"⚠️ Output reader error for {self.config.agent_type.value}: {e}")

    def _read_errors(self):
        """Read stderr in background thread."""
        if not self.process or not self.process.stderr:
            return

        try:
            for line in self.process.stderr:
                self.output_queue.put(("stderr", line))
                print(f"⚠️ {self.config.agent_type.value} stderr: {line.strip()}")
        except Exception as e:
            print(f"⚠️ Error reader error for {self.config.agent_type.value}: {e}")

    def _mirror_to_tmux(self, output: str):
        """Mirror output to tmux pane for visibility."""
        if not self.config.tmux_pane:
            return

        try:
            # Send output to tmux pane
            subprocess.run(
                [
                    "tmux",
                    "send-keys",
                    "-t",
                    self.config.tmux_pane,
                    output.strip(),
                ],
                check=False,
            )
        except Exception as e:
            # Don't fail if tmux mirror fails
            pass

    def send_command(self, command: str) -> bool:
        """
        Send command to AI agent.

        Args:
            command: Command/prompt to send

        Returns:
            True if sent successfully
        """
        if self.status != AgentStatus.RUNNING or not self.process:
            print(f"❌ Cannot send to {self.config.agent_type.value}: not running")
            return False

        try:
            self.process.stdin.write(f"{command}\n")
            self.process.stdin.flush()
            return True
        except Exception as e:
            print(f"❌ Failed to send command to {self.config.agent_type.value}: {e}")
            self.status = AgentStatus.ERROR
            return False

    def get_output(self, timeout: float = 1.0) -> list[str]:
        """
        Get available output from agent.

        Args:
            timeout: Seconds to wait for output

        Returns:
            List of output lines
        """
        output_lines = []
        deadline = time.time() + timeout

        while time.time() < deadline:
            try:
                source, line = self.output_queue.get(timeout=0.1)
                output_lines.append(line)
            except queue.Empty:
                if output_lines:
                    # Got some output, can return
                    break
                continue

        return output_lines

    def is_healthy(self) -> bool:
        """
        Check if agent is healthy.

        Returns:
            True if running and responsive
        """
        if self.status != AgentStatus.RUNNING:
            return False

        if not self.process:
            return False

        # Check if process is still alive
        if self.process.poll() is not None:
            # Process has exited
            self.status = AgentStatus.CRASHED
            return False

        self.last_health_check = time.time()
        return True

    def stop(self) -> None:
        """Stop the agent gracefully."""
        if not self.process:
            return

        print(f"🛑 Stopping {self.config.agent_type.value}...")

        try:
            # Try graceful shutdown
            self.process.terminate()
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # Force kill if not responding
            print(f"⚠️ {self.config.agent_type.value} not responding, force killing...")
            self.process.kill()
            self.process.wait()

        self.status = AgentStatus.STOPPED
        self.process = None
        print(f"✅ {self.config.agent_type.value} stopped")

    def restart(self) -> bool:
        """
        Restart the agent.

        Returns:
            True if restarted successfully
        """
        if self.restart_count >= self.config.max_restarts:
            print(f"❌ Max restarts reached for {self.config.agent_type.value}")
            return False

        print(f"🔄 Restarting {self.config.agent_type.value}...")
        self.stop()
        time.sleep(2)  # Brief pause

        success = self.start()
        if success:
            self.restart_count += 1

        return success


class AgentSpawner:
    """
    Manages multiple AI CLI instances.

    Responsibilities:
    - Spawn Claude, Gemini, Codex processes
    - Health monitoring with auto-restart
    - Coordinate command routing
    - Aggregate results
    """

    def __init__(self):
        """Initialize agent spawner."""
        self.agents: dict[AgentType, AIAgent] = {}
        self.health_check_thread: Optional[threading.Thread] = None
        self.running = False

    def register_agent(self, agent_type: AgentType, config: AgentConfig) -> None:
        """
        Register an AI agent for spawning.

        Args:
            agent_type: Type of AI agent
            config: Agent configuration
        """
        agent = AIAgent(config)
        self.agents[agent_type] = agent
        print(f"📝 Registered {agent_type.value} agent")

    def start_all(self) -> dict[AgentType, bool]:
        """
        Start all registered agents.

        Returns:
            Dict mapping agent type to success status
        """
        results = {}

        for agent_type, agent in self.agents.items():
            success = agent.start()
            results[agent_type] = success

        # Start health monitoring
        self.start_health_monitoring()

        return results

    def start_health_monitoring(self):
        """Start background health check thread."""
        if self.health_check_thread and self.health_check_thread.is_alive():
            return  # Already running

        self.running = True
        self.health_check_thread = threading.Thread(
            target=self._health_check_loop, daemon=True
        )
        self.health_check_thread.start()
        print("💓 Health monitoring started")

    def _health_check_loop(self):
        """Background health checking with auto-restart."""
        while self.running:
            time.sleep(30)  # Check every 30 seconds

            for agent_type, agent in self.agents.items():
                if not agent.is_healthy():
                    print(f"⚠️ {agent_type.value} unhealthy, attempting restart...")

                    if agent.config.auto_restart:
                        success = agent.restart()
                        if not success:
                            print(f"❌ Failed to restart {agent_type.value}")

    def send_to_agent(
        self, agent_type: AgentType, command: str
    ) -> Optional[list[str]]:
        """
        Send command to specific agent and get response.

        Args:
            agent_type: Target agent
            command: Command/prompt to send

        Returns:
            Agent's response lines or None if failed
        """
        agent = self.agents.get(agent_type)
        if not agent:
            print(f"❌ Agent not found: {agent_type.value}")
            return None

        if not agent.is_healthy():
            print(f"❌ Agent not healthy: {agent_type.value}")
            return None

        # Send command
        success = agent.send_command(command)
        if not success:
            return None

        # Wait for response (TODO: smarter completion detection)
        time.sleep(2)  # Give AI time to respond

        return agent.get_output(timeout=5.0)

    def stop_all(self):
        """Stop all agents gracefully."""
        self.running = False

        for agent_type, agent in self.agents.items():
            agent.stop()

        print("✅ All agents stopped")

    def get_status(self) -> dict:
        """
        Get status of all agents.

        Returns:
            Status dictionary for monitoring
        """
        return {
            agent_type.value: {
                "status": agent.status.value,
                "pid": agent.process.pid if agent.process else None,
                "restart_count": agent.restart_count,
                "last_health_check": agent.last_health_check,
            }
            for agent_type, agent in self.agents.items()
        }


if __name__ == "__main__":
    """Test agent spawner."""

    # Create spawner
    spawner = AgentSpawner()

    # Register Claude agent
    spawner.register_agent(
        AgentType.CLAUDE,
        AgentConfig(
            agent_type=AgentType.CLAUDE,
            command=["claude", "chat"],
            env={},
        ),
    )

    # Register Gemini agent (if installed)
    spawner.register_agent(
        AgentType.GEMINI,
        AgentConfig(
            agent_type=AgentType.GEMINI,
            command=["gemini", "-p"],  # Prompt mode
            env={},
        ),
    )

    # Start all
    print("Starting agents...")
    results = spawner.start_all()

    print(f"\nStartup results:")
    for agent_type, success in results.items():
        status = "✅" if success else "❌"
        print(f"  {status} {agent_type.value}")

    # Show status
    print(f"\nAgent status:")
    import json
    print(json.dumps(spawner.get_status(), indent=2))

    # Test sending command
    if results.get(AgentType.CLAUDE):
        print("\nTesting command send to Claude...")
        response = spawner.send_to_agent(AgentType.CLAUDE, "What is 2+2?")
        if response:
            print(f"Response: {response[:3]}")  # First 3 lines

    # Cleanup
    input("\nPress Enter to stop agents...")
    spawner.stop_all()
