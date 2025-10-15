"""
Instance State Persistence for Session Recovery.

Tracks instance state in ConPort database to enable automatic resume
after crashes or restarts.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import json
import asyncio
import aiohttp
import logging

logger = logging.getLogger(__name__)


@dataclass
class InstanceState:
    """Persistent state for a Dopemux instance."""

    instance_id: str
    port_base: int
    worktree_path: str
    git_branch: str
    created_at: datetime
    last_active: datetime
    status: str  # 'active', 'stopped', 'orphaned'

    # Session context
    last_working_directory: Optional[str] = None
    last_focus_context: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_active'] = self.last_active.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'InstanceState':
        """Create from dictionary."""
        data = data.copy()
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['last_active'] = datetime.fromisoformat(data['last_active'])
        return cls(**data)


class InstanceStateManager:
    """Manages instance state persistence via ConPort."""

    CATEGORY = "instance_state"

    def __init__(self, workspace_id: str, conport_port: int = 3004):
        """
        Initialize state manager.

        Args:
            workspace_id: Absolute path to workspace root
            conport_port: ConPort HTTP API port (default 3004 for MCP ConPort)
        """
        self.workspace_id = workspace_id
        self.conport_url = f"http://localhost:{conport_port}"
        self.session: Optional[aiohttp.ClientSession] = None

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def _close_session(self):
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def save_instance_state(self, state: InstanceState) -> bool:
        """
        Save instance state to ConPort.

        Args:
            state: InstanceState to persist

        Returns:
            True if saved successfully, False otherwise
        """
        await self._ensure_session()

        try:
            # ConPort custom_data endpoint: POST /custom_data
            data = {
                "workspace_id": self.workspace_id,
                "category": self.CATEGORY,
                "key": state.instance_id,
                "value": state.to_dict()
            }

            async with self.session.post(
                f"{self.conport_url}/api/custom_data",
                json=data,
                timeout=aiohttp.ClientTimeout(total=5.0)
            ) as response:
                if response.status == 200:
                    logger.info(f"✅ Saved instance state for {state.instance_id}")
                    return True
                else:
                    logger.warning(f"⚠️ Failed to save instance state: HTTP {response.status}")
                    return False

        except Exception as e:
            logger.warning(f"⚠️ Could not save instance state (ConPort unavailable?): {e}")
            return False

    async def load_instance_state(self, instance_id: str) -> Optional[InstanceState]:
        """
        Load instance state from ConPort.

        Args:
            instance_id: Instance to load state for

        Returns:
            InstanceState if found, None otherwise
        """
        await self._ensure_session()

        try:
            # ConPort custom_data endpoint: GET /custom_data?category=X&key=Y
            params = {
                "workspace_id": self.workspace_id,
                "category": self.CATEGORY,
                "key": instance_id
            }

            async with self.session.get(
                f"{self.conport_url}/api/custom_data",
                params=params,
                timeout=aiohttp.ClientTimeout(total=5.0)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    # Result format: {"category": "...", "key": "...", "value": {...}}
                    if result and 'value' in result:
                        logger.info(f"✅ Loaded instance state for {instance_id}")
                        return InstanceState.from_dict(result['value'])
                    return None
                elif response.status == 404:
                    logger.debug(f"No saved state found for instance {instance_id}")
                    return None
                else:
                    logger.warning(f"⚠️ Failed to load instance state: HTTP {response.status}")
                    return None

        except Exception as e:
            logger.warning(f"⚠️ Could not load instance state (ConPort unavailable?): {e}")
            return None

    async def list_all_instance_states(self) -> List[InstanceState]:
        """
        List all instance states for workspace.

        Returns:
            List of InstanceState objects
        """
        await self._ensure_session()

        try:
            # ConPort custom_data endpoint: GET /custom_data?category=X (no key = all in category)
            params = {
                "workspace_id": self.workspace_id,
                "category": self.CATEGORY
            }

            async with self.session.get(
                f"{self.conport_url}/api/custom_data",
                params=params,
                timeout=aiohttp.ClientTimeout(total=5.0)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    # Result format: [{"category": "...", "key": "...", "value": {...}}, ...]
                    states = []
                    if isinstance(result, list):
                        for item in result:
                            if 'value' in item:
                                states.append(InstanceState.from_dict(item['value']))
                    logger.info(f"✅ Loaded {len(states)} instance states")
                    return states
                else:
                    logger.warning(f"⚠️ Failed to list instance states: HTTP {response.status}")
                    return []

        except Exception as e:
            logger.warning(f"⚠️ Could not list instance states (ConPort unavailable?): {e}")
            return []

    async def mark_instance_stopped(self, instance_id: str) -> bool:
        """
        Mark instance as stopped (clean shutdown).

        Args:
            instance_id: Instance that stopped

        Returns:
            True if successfully marked, False otherwise
        """
        state = await self.load_instance_state(instance_id)
        if state:
            state.status = 'stopped'
            state.last_active = datetime.now()
            return await self.save_instance_state(state)
        return False

    async def mark_instance_orphaned(self, instance_id: str) -> bool:
        """
        Mark instance as orphaned (crashed, worktree exists but no services).

        Args:
            instance_id: Instance that became orphaned

        Returns:
            True if successfully marked, False otherwise
        """
        state = await self.load_instance_state(instance_id)
        if state:
            state.status = 'orphaned'
            state.last_active = datetime.now()
            return await self.save_instance_state(state)
        return False

    async def find_orphaned_instances(self) -> List[InstanceState]:
        """
        Find instances with orphaned worktrees.

        Returns:
            List of orphaned InstanceState objects
        """
        all_states = await self.list_all_instance_states()
        return [
            state for state in all_states
            if state.status == 'orphaned' and Path(state.worktree_path).exists()
        ]

    async def find_orphaned_instances_filtered(
        self,
        max_age_days: int = 7,
        limit: int = 10,
        sort_by_recent: bool = True
    ) -> List[InstanceState]:
        """
        Find orphaned instances with age and count filtering.

        ADHD Optimization: Limits results to reduce decision paralysis.

        Args:
            max_age_days: Only include instances newer than this many days (default: 7)
            limit: Maximum number of instances to return (default: 10, ADHD max: 3 for menus)
            sort_by_recent: Sort by most recent first (default: True)

        Returns:
            Filtered list of orphaned InstanceState objects
        """
        from datetime import timedelta

        # Get all orphaned instances
        orphaned = await self.find_orphaned_instances()

        # Filter by age
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        filtered = [
            state for state in orphaned
            if state.last_active >= cutoff_date
        ]

        # Sort by most recent first if requested
        if sort_by_recent:
            filtered.sort(key=lambda s: s.last_active, reverse=True)

        # Limit count
        return filtered[:limit]

    async def cleanup_instance_state(self, instance_id: str) -> bool:
        """
        Remove instance state from persistence.

        Args:
            instance_id: Instance to remove state for

        Returns:
            True if successfully removed, False otherwise
        """
        await self._ensure_session()

        try:
            # ConPort custom_data endpoint: DELETE /custom_data?category=X&key=Y
            params = {
                "workspace_id": self.workspace_id,
                "category": self.CATEGORY,
                "key": instance_id
            }

            async with self.session.delete(
                f"{self.conport_url}/api/custom_data",
                params=params,
                timeout=aiohttp.ClientTimeout(total=5.0)
            ) as response:
                if response.status == 200:
                    logger.info(f"✅ Cleaned up instance state for {instance_id}")
                    return True
                elif response.status == 404:
                    logger.debug(f"No state to clean up for instance {instance_id}")
                    return True  # Already gone, consider success
                else:
                    logger.warning(f"⚠️ Failed to cleanup instance state: HTTP {response.status}")
                    return False

        except Exception as e:
            logger.warning(f"⚠️ Could not cleanup instance state (ConPort unavailable?): {e}")
            return False


# Synchronous wrapper functions for CLI usage

def save_instance_state_sync(
    state: InstanceState,
    workspace_id: str,
    conport_port: int = 3004
) -> bool:
    """
    Synchronous wrapper for save_instance_state.

    Args:
        state: InstanceState to persist
        workspace_id: Workspace root path
        conport_port: ConPort API port

    Returns:
        True if saved successfully, False otherwise
    """
    manager = InstanceStateManager(workspace_id, conport_port)
    try:
        return asyncio.run(manager.save_instance_state(state))
    finally:
        asyncio.run(manager._close_session())


def load_instance_state_sync(
    instance_id: str,
    workspace_id: str,
    conport_port: int = 3004
) -> Optional[InstanceState]:
    """
    Synchronous wrapper for load_instance_state.

    Args:
        instance_id: Instance to load
        workspace_id: Workspace root path
        conport_port: ConPort API port

    Returns:
        InstanceState if found, None otherwise
    """
    manager = InstanceStateManager(workspace_id, conport_port)
    try:
        return asyncio.run(manager.load_instance_state(instance_id))
    finally:
        asyncio.run(manager._close_session())


def list_all_instance_states_sync(
    workspace_id: str,
    conport_port: int = 3004
) -> List[InstanceState]:
    """
    Synchronous wrapper for list_all_instance_states.

    Args:
        workspace_id: Workspace root path
        conport_port: ConPort API port

    Returns:
        List of all InstanceState objects
    """
    manager = InstanceStateManager(workspace_id, conport_port)
    try:
        return asyncio.run(manager.list_all_instance_states())
    finally:
        asyncio.run(manager._close_session())


def cleanup_instance_state_sync(
    instance_id: str,
    workspace_id: str,
    conport_port: int = 3004
) -> bool:
    """
    Synchronous wrapper for cleanup_instance_state.

    Args:
        instance_id: Instance to remove
        workspace_id: Workspace root path
        conport_port: ConPort API port

    Returns:
        True if cleaned successfully, False otherwise
    """
    manager = InstanceStateManager(workspace_id, conport_port)
    try:
        return asyncio.run(manager.cleanup_instance_state(instance_id))
    finally:
        asyncio.run(manager._close_session())
