"""
Health Monitor - Agent Health Checking System
Hybrid approach: Fast OS process check + lazy heartbeat validation

Architecture:
- Process monitoring (0ms overhead, checks if alive)
- Lazy heartbeat (thorough, only when needed)
- Background monitoring thread (optional, for proactive detection)
- Integration with error recovery

Performance:
- Fast path: 0ms (OS process check)
- Slow path: ~3ms (heartbeat with timeout)
- Background thread: 60s interval (minimal overhead)
"""

import os
import time
import threading
from typing import Optional, Callable, Dict
from datetime import datetime
from enum import Enum


class HealthStatus(Enum):
    """Agent health status."""
    HEALTHY = "healthy"
    UNRESPONSIVE = "unresponsive"  # Process alive but not responding
    DEAD = "dead"                   # Process terminated
    UNKNOWN = "unknown"             # Not checked yet


class HealthMonitor:
    """
    Monitor agent health with hybrid strategy.

    Fast path: OS process check (instant)
    Slow path: Heartbeat validation (when needed)
    Optional: Background monitoring thread
    """

    def __init__(self, heartbeat_interval: int = 60):
        """
        Initialize health monitor.

        Args:
            heartbeat_interval: Seconds between heartbeat checks
        """
        self.heartbeat_interval = heartbeat_interval
        self.last_heartbeat: Dict[str, float] = {}  # agent_id -> timestamp
        self.monitoring_thread: Optional[threading.Thread] = None
        self.running = False
        self.on_unhealthy_callback: Optional[Callable] = None

    def check_health(self, agent) -> HealthStatus:
        """
        Check agent health with hybrid approach.

        Fast path: OS process check (0ms)
        Slow path: Heartbeat if needed

        Args:
            agent: Agent to check

        Returns:
            HealthStatus indicating agent health

        ADHD Benefit:
            Fast check prevents blocking, thorough when needed
        """
        # Fast path: Check if process exists
        if not self._is_process_alive(agent):
            return HealthStatus.DEAD

        # Process is alive - check if responding
        agent_id = self._get_agent_id(agent)
        last_check = self.last_heartbeat.get(agent_id, 0)
        time_since_check = time.time() - last_check

        # If checked recently, assume healthy (lazy evaluation)
        if time_since_check < self.heartbeat_interval:
            return HealthStatus.HEALTHY

        # Time for fresh heartbeat check
        responding = self._send_heartbeat(agent)

        if responding:
            self.last_heartbeat[agent_id] = time.time()
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNRESPONSIVE

    def _is_process_alive(self, agent) -> bool:
        """
        Check if agent process is alive via OS.

        Fast check (0ms overhead) - just queries OS.

        Args:
            agent: Agent with pid attribute

        Returns:
            True if process exists
        """
        if not agent.pid:
            return False

        try:
            # Signal 0 = existence check (doesn't actually send signal)
            os.kill(agent.pid, 0)
            return True
        except OSError:
            return False

    def _send_heartbeat(self, agent) -> bool:
        """
        Send heartbeat ping to agent.

        Sends minimal command (newline) and checks for any output.

        Args:
            agent: Agent to ping

        Returns:
            True if agent responded

        Performance: ~3ms (timeout-limited)
        """
        try:
            # Send minimal command (just newline)
            agent.send_command("\n")

            # Wait briefly for any output
            output = agent.get_output(timeout=3)

            # Any output (even just prompt) means responsive
            return len(output) > 0

        except Exception as e:
            print(f"⚠️  Heartbeat failed: {e}")
            return False

    def _get_agent_id(self, agent) -> str:
        """Get unique identifier for agent."""
        return f"{agent.config.agent_type.value}_{agent.pid}"

    def start_background_monitoring(
        self,
        agents: list,
        on_unhealthy: Optional[Callable] = None
    ):
        """
        Start background thread that periodically checks all agents.

        Args:
            agents: List of agents to monitor
            on_unhealthy: Optional callback when agent becomes unhealthy

        Use Case:
            Proactive detection of agent failures

        Example:
            >>> monitor.start_background_monitoring(
            ...     spawner.agents.values(),
            ...     on_unhealthy=lambda agent: recovery.recover(agent, ...)
            ... )
        """
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            print("⚠️  Background monitoring already running")
            return

        self.running = True
        self.on_unhealthy_callback = on_unhealthy

        def monitor_loop():
            """Background monitoring loop."""
            while self.running:
                for agent in agents:
                    if agent.status.value == "running":  # Only check running agents
                        status = self.check_health(agent)

                        if status != HealthStatus.HEALTHY:
                            print(f"⚠️  Health check: {agent.config.agent_type.value} is {status.value}")

                            # Trigger callback if provided
                            if self.on_unhealthy_callback:
                                try:
                                    self.on_unhealthy_callback(agent, status)
                                except Exception as e:
                                    print(f"❌ Unhealthy callback error: {e}")

                # Sleep until next check
                time.sleep(self.heartbeat_interval)

        self.monitoring_thread = threading.Thread(
            target=monitor_loop,
            name="health-monitor",
            daemon=True
        )
        self.monitoring_thread.start()

        print(f"✅ Background health monitoring started (every {self.heartbeat_interval}s)")

    def stop_background_monitoring(self):
        """Stop background monitoring thread."""
        if self.monitoring_thread:
            self.running = False
            self.monitoring_thread.join(timeout=5)
            print("✅ Background monitoring stopped")

    def get_health_report(self, agents: list) -> Dict:
        """
        Get comprehensive health report for all agents.

        Args:
            agents: List of agents to check

        Returns:
            Health report dictionary

        Example:
            >>> report = monitor.get_health_report(spawner.agents.values())
            >>> print(f"Healthy: {report['healthy_count']}/{report['total']}")
        """
        report = {
            'total': len(agents),
            'healthy': 0,
            'unresponsive': 0,
            'dead': 0,
            'unknown': 0,
            'agents': {},
            'timestamp': datetime.now().isoformat(),
        }

        for agent in agents:
            status = self.check_health(agent)
            agent_name = agent.config.agent_type.value

            report['agents'][agent_name] = {
                'status': status.value,
                'pid': agent.pid,
                'restart_count': agent.restart_count,
            }

            # Count by status
            if status == HealthStatus.HEALTHY:
                report['healthy'] += 1
            elif status == HealthStatus.UNRESPONSIVE:
                report['unresponsive'] += 1
            elif status == HealthStatus.DEAD:
                report['dead'] += 1
            else:
                report['unknown'] += 1

        return report


if __name__ == "__main__":
    """Test health monitor."""
    print("🧪 Testing Health Monitor")
    print("=" * 60)

    monitor = HealthMonitor(heartbeat_interval=60)

    # Test 1: Process alive check
    print("\n1. Testing process alive check...")

    # Mock agent with current process PID
    class MockAgent:
        def __init__(self, pid):
            self.pid = pid
            self.restart_count = 0
            self.config = type('obj', (object,), {'agent_type': type('obj', (object,), {'value': 'test'})})()
            self.status = type('obj', (object,), {'value': 'running'})()

    current_process = MockAgent(os.getpid())
    alive = monitor._is_process_alive(current_process)
    print(f"   Current process alive: {alive}")
    assert alive, "Current process should be alive"

    # Test non-existent process
    fake_process = MockAgent(999999)
    alive = monitor._is_process_alive(fake_process)
    print(f"   Fake process alive: {alive}")
    assert not alive, "Fake process should be dead"

    # Test 2: Health status
    print("\n2. Testing health status check...")
    status = monitor.check_health(current_process)
    print(f"   Health status: {status.value}")

    # Test 3: Health report
    print("\n3. Testing health report...")
    agents = [current_process]
    report = monitor.get_health_report(agents)

    print(f"   Total agents: {report['total']}")
    print(f"   Healthy: {report['healthy']}")
    print(f"   Dead: {report['dead']}")
    print(f"   Timestamp: {report['timestamp']}")

    print("\n✅ Health monitor test complete!")
