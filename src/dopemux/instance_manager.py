"""
Multi-Instance Manager for Dopemux.

Coordinates instance detection, worktree creation, and environment setup
for multi-instance ADHD-optimized development workflows.
"""

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import aiohttp
import asyncio


@dataclass
class RunningInstance:
    """Information about a detected running instance."""

    instance_id: str
    port_base: int
    worktree_path: Optional[Path]
    git_branch: Optional[str]
    is_healthy: bool


class InstanceManager:
    """Manages multi-instance detection and coordination."""

    # Port bases for up to 5 concurrent instances
    AVAILABLE_PORTS = [3000, 3030, 3060, 3090, 3120]

    # Instance IDs (A-E for simplicity)
    AVAILABLE_IDS = ['A', 'B', 'C', 'D', 'E']

    def __init__(self, workspace_root: Path):
        """
        Initialize instance manager.

        Args:
            workspace_root: Path to main repository root
        """
        self.workspace_root = workspace_root.resolve()
        self.worktrees_dir = workspace_root / "worktrees"

    async def detect_running_instances(self) -> List[RunningInstance]:
        """
        Detect currently running Dopemux instances.

        Returns:
            List of detected running instances
        """
        running_instances = []

        for port_base in self.AVAILABLE_PORTS:
            instance = await self._probe_instance(port_base)
            if instance:
                running_instances.append(instance)

        return running_instances

    async def _probe_instance(self, port_base: int) -> Optional[RunningInstance]:
        """
        Probe for instance on given port base.

        Tries to connect to ConPort health endpoint (port_base + 7).

        Args:
            port_base: Base port to probe

        Returns:
            RunningInstance if found, None otherwise
        """
        conport_port = port_base + 7

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"http://localhost:{conport_port}/health",
                    timeout=aiohttp.ClientTimeout(total=1.0)
                ) as response:
                    if response.status == 200:
                        # Instance is running
                        instance_id = self._port_to_instance_id(port_base)
                        worktree_path = self._get_worktree_path(instance_id)
                        git_branch = self._detect_git_branch(worktree_path)

                        return RunningInstance(
                            instance_id=instance_id,
                            port_base=port_base,
                            worktree_path=worktree_path,
                            git_branch=git_branch,
                            is_healthy=True
                        )
        except (aiohttp.ClientError, asyncio.TimeoutError):
            # Instance not running on this port
            pass

        return None

    def _port_to_instance_id(self, port_base: int) -> str:
        """Map port base to instance ID."""
        port_index = self.AVAILABLE_PORTS.index(port_base)
        return self.AVAILABLE_IDS[port_index]

    def _instance_id_to_port(self, instance_id: str) -> int:
        """Map instance ID to port base."""
        id_index = self.AVAILABLE_IDS.index(instance_id)
        return self.AVAILABLE_PORTS[id_index]

    def _get_worktree_path(self, instance_id: str) -> Optional[Path]:
        """Get worktree path for instance ID."""
        if instance_id == 'A':
            # Instance A uses main worktree
            return self.workspace_root

        worktree_path = self.worktrees_dir / instance_id
        return worktree_path if worktree_path.exists() else None

    def _detect_git_branch(self, worktree_path: Optional[Path]) -> Optional[str]:
        """Detect current git branch in worktree."""
        if not worktree_path or not worktree_path.exists():
            return None

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(worktree_path),
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return None

    def get_next_available_instance(self, running_instances: List[RunningInstance]) -> Tuple[str, int]:
        """
        Get next available instance ID and port base.

        Args:
            running_instances: List of currently running instances

        Returns:
            Tuple of (instance_id, port_base)

        Raises:
            RuntimeError: If no instances available (max 5 reached)
        """
        used_ids = {inst.instance_id for inst in running_instances}

        for instance_id in self.AVAILABLE_IDS:
            if instance_id not in used_ids:
                port_base = self._instance_id_to_port(instance_id)
                return instance_id, port_base

        raise RuntimeError(
            "Maximum instances (5) already running. "
            "Stop one before starting another:\n"
            + "\n".join([
                f"  - Instance {inst.instance_id} on port {inst.port_base} ({inst.git_branch or 'unknown branch'})"
                for inst in running_instances
            ])
        )

    def create_worktree(
        self,
        instance_id: str,
        branch_name: Optional[str] = None
    ) -> Path:
        """
        Create git worktree for instance.

        Args:
            instance_id: Instance identifier (B-E)
            branch_name: Git branch name (defaults to feature/instance-{id})

        Returns:
            Path to created worktree

        Raises:
            ValueError: If instance_id is 'A' (main worktree)
            RuntimeError: If worktree creation fails
        """
        if instance_id == 'A':
            raise ValueError("Instance A uses main worktree, no worktree creation needed")

        if not branch_name:
            branch_name = f"feature/instance-{instance_id}"

        worktree_path = self.worktrees_dir / instance_id

        # Create worktrees directory if needed
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Create git worktree
            subprocess.run(
                ["git", "worktree", "add", str(worktree_path), "-b", branch_name],
                cwd=str(self.workspace_root),
                check=True,
                capture_output=True,
                text=True
            )

            return worktree_path

        except subprocess.CalledProcessError as e:
            raise RuntimeError(
                f"Failed to create worktree for instance {instance_id}: {e.stderr}"
            )

    def get_instance_env_vars(
        self,
        instance_id: str,
        port_base: int,
        worktree_path: Optional[Path] = None
    ) -> dict:
        """
        Get environment variables for instance.

        Args:
            instance_id: Instance identifier
            port_base: Base port for services
            worktree_path: Path to worktree (None for main worktree)

        Returns:
            Dictionary of environment variables to set
        """
        env_vars = {
            "DOPEMUX_INSTANCE_ID": instance_id if instance_id != 'A' else "",
            "DOPEMUX_WORKSPACE_ID": str(self.workspace_root),
            "DOPEMUX_PORT_BASE": str(port_base),

            # Service ports
            "TASK_MASTER_PORT": str(port_base + 5),
            "SERENA_PORT": str(port_base + 6),
            "CONPORT_PORT": str(port_base + 7),

            # Integration Bridge
            "INTEGRATION_BRIDGE_PORT": str(port_base + 16),

            # Leantime (shared, always on port 3001)
            "LEANTIME_URL": "http://localhost:3001",
        }

        return env_vars

    def list_worktrees(self) -> List[Tuple[str, Path, str]]:
        """
        List all git worktrees.

        Returns:
            List of (instance_id, path, branch) tuples
        """
        try:
            result = subprocess.run(
                ["git", "worktree", "list"],
                cwd=str(self.workspace_root),
                capture_output=True,
                text=True,
                check=True
            )

            worktrees = []
            for line in result.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 3:
                    path = Path(parts[0])
                    branch = parts[-1].strip('[]')

                    # Determine instance ID
                    if path == self.workspace_root:
                        instance_id = 'A'
                    else:
                        instance_id = path.name

                    worktrees.append((instance_id, path, branch))

            return worktrees

        except subprocess.CalledProcessError:
            return [('A', self.workspace_root, 'unknown')]

    def cleanup_worktree(self, instance_id: str) -> bool:
        """
        Remove git worktree for instance.

        Args:
            instance_id: Instance to remove worktree for

        Returns:
            True if removed successfully, False otherwise
        """
        if instance_id == 'A':
            return False  # Cannot remove main worktree

        worktree_path = self.worktrees_dir / instance_id

        try:
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path)],
                cwd=str(self.workspace_root),
                check=True,
                capture_output=True
            )
            return True
        except subprocess.CalledProcessError:
            return False


def detect_instances_sync(workspace_root: Path) -> List[RunningInstance]:
    """
    Synchronous wrapper for detect_running_instances.

    Args:
        workspace_root: Path to workspace root

    Returns:
        List of running instances
    """
    manager = InstanceManager(workspace_root)
    return asyncio.run(manager.detect_running_instances())


def detect_orphaned_instances_sync(
    workspace_root: Path,
    workspace_id: str,
    conport_port: int = 3007
) -> List[dict]:
    """
    Detect orphaned instances (crashed with worktrees still existing).

    Compares running instances from health probes with saved states
    in ConPort to identify instances that crashed.

    Args:
        workspace_root: Path to workspace root
        workspace_id: Workspace ID for ConPort queries
        conport_port: ConPort port (default 3007 for instance A)

    Returns:
        List of orphaned instance dicts with:
            - instance_id: str
            - worktree_path: str
            - git_branch: str
            - last_active: datetime
            - port_base: int
    """
    from .instance_state import (
        list_all_instance_states_sync,
        save_instance_state_sync
    )

    # Get running instances via health probes
    running_instances = detect_instances_sync(workspace_root)
    running_ids = {inst.instance_id for inst in running_instances}

    # Get all saved states from ConPort
    all_states = list_all_instance_states_sync(workspace_id, conport_port)

    # Find orphaned: saved as active but not actually running
    orphaned = []
    for state in all_states:
        # Skip if instance is currently running
        if state.instance_id in running_ids:
            continue

        # Skip if already marked as stopped/orphaned
        if state.status in ('stopped', 'orphaned'):
            continue

        # Check if worktree still exists
        worktree_path = Path(state.worktree_path)
        if not worktree_path.exists():
            continue

        # Mark as orphaned in ConPort
        state.status = 'orphaned'
        save_instance_state_sync(state, workspace_id, conport_port)

        # Add to orphaned list
        orphaned.append({
            'instance_id': state.instance_id,
            'worktree_path': state.worktree_path,
            'git_branch': state.git_branch,
            'last_active': state.last_active,
            'port_base': state.port_base,
            'last_working_directory': state.last_working_directory,
            'last_focus_context': state.last_focus_context,
        })

    return orphaned
