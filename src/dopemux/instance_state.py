"""
Instance State Persistence for Session Recovery.

Tracks instance state in ConPort database to enable automatic resume
after crashes or restarts.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
import json
import os
import socket
from urllib.parse import urlparse
import asyncio
import aiohttp
import logging

logger = logging.getLogger(__name__)

DEFAULT_CONPORT_PORT = 3004


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
        # Normalize to UTC ISO8601 with 'Z'
        def _to_utc_iso(dt: datetime) -> str:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt.isoformat().replace('+00:00', 'Z')

        data['created_at'] = _to_utc_iso(self.created_at)
        data['last_active'] = _to_utc_iso(self.last_active)
        return data

    @classmethod
    def from_dict(cls, data: dict) -> 'InstanceState':
        """Create from dictionary."""
        data = data.copy()
        def _parse_iso(s: str) -> datetime:
            # Support 'Z' suffix and naive inputs
            if isinstance(s, str):
                s2 = s.replace('Z', '+00:00')
                try:
                    dt = datetime.fromisoformat(s2)
                except Exception as e:
                    # Fallback to naive parse
                    dt = datetime.strptime(s.split('.')[0], '%Y-%m-%dT%H:%M:%S')
            else:
                dt = datetime.now(timezone.utc)

            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)

        data['created_at'] = _parse_iso(data['created_at'])
        data['last_active'] = _parse_iso(data['last_active'])
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
        self._last_error: Optional[Exception] = None
        self._conport_available: bool = True

    @property
    def conport_available(self) -> bool:
        """Return whether the last ConPort interaction succeeded."""
        return self._conport_available

    @property
    def last_error(self) -> Optional[Exception]:
        """Return the last ConPort-related error, if any."""
        return self._last_error

    def _mark_conport_ok(self) -> None:
        self._last_error = None
        self._conport_available = True

    def _mark_conport_error(self, exc: Exception) -> None:
        self._last_error = exc
        self._conport_available = False

    def _is_connection_error(self, exc: Exception) -> bool:
        return isinstance(
            exc,
            (
                aiohttp.ClientConnectorError,
                aiohttp.ClientConnectionError,
                aiohttp.ClientOSError,
                asyncio.TimeoutError,
                OSError,
            ),
        )

    def _log_conport_error(self, action: str, exc: Exception) -> None:
        if self._is_connection_error(exc):
            logger.debug("ConPort unavailable while %s: %s", action, exc)
        else:
            logger.warning("ConPort error while %s: %s", action, exc)

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def _close_session(self):
        """Close aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - ensures session cleanup."""
        await self._close_session()
        return False

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
                self._mark_conport_ok()
                if response.status == 200:
                    logger.info(f"✅ Saved instance state for {state.instance_id}")
                    return True
                else:
                    logger.warning(f"⚠️ Failed to save instance state: HTTP {response.status}")
                    return False

        except Exception as e:
            self._mark_conport_error(e)
            self._log_conport_error("saving instance state", e)
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
                self._mark_conport_ok()
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
            self._mark_conport_error(e)
            self._log_conport_error("loading instance state", e)
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
                self._mark_conport_ok()
                if response.status == 200:
                    result = await response.json()
                    # Result format: [{"category": "...", "key": "...", "value": {...}}, ...]
                    # OR: {"items": [{"category": "...", "key": "...", "value": {...}}, ...]}
                    states = []
                    
                    items = []
                    if isinstance(result, list):
                        items = result
                    elif isinstance(result, dict) and "items" in result:
                        items = result["items"]
                        
                    for item in items:
                        if 'value' in item:
                            states.append(InstanceState.from_dict(item['value']))
                    
                    logger.info(f"✅ Loaded {len(states)} instance states")
                    return states
                else:
                    logger.warning(f"⚠️ Failed to list instance states: HTTP {response.status}")
                    return []

        except Exception as e:
            self._mark_conport_error(e)
            self._log_conport_error("listing instance states", e)
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
            state.last_active = datetime.now(timezone.utc)
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
            state.last_active = datetime.now(timezone.utc)
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

        def _as_utc(dt: datetime) -> datetime:
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)

        # Filter by age
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        filtered = [
            state for state in orphaned
            if _as_utc(state.last_active) >= cutoff_date
        ]

        # Sort by most recent first if requested
        if sort_by_recent:
            filtered.sort(key=lambda s: _as_utc(s.last_active), reverse=True)

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
                self._mark_conport_ok()
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
            self._mark_conport_error(e)
            self._log_conport_error("cleaning instance state", e)
            return False


def _safe_int(value: Optional[str]) -> Optional[int]:
    """Best-effort integer parsing."""
    if value is None:
        return None
    try:
        return int(value.strip())
    except (ValueError, AttributeError):
        return None


def _port_is_listening(port: int, host: str = "127.0.0.1", timeout: float = 0.35) -> bool:
    """Check whether a port is open on localhost (best-effort, non-fatal)."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def resolve_conport_port(port: Optional[int] = None) -> int:
    """
    Resolve the ConPort HTTP port with graceful fallbacks.

    Order of precedence:
        1. Explicit argument
        2. DOPEMUX_CONPORT_PORT / CONPORT_PORT environment overrides
        3. Port extracted from CONPORT_URL
        4. DOPEMUX_PORT_BASE + 7 (per-instance mapping)
        5. Preferred defaults (3007, then 3004 legacy)

    If multiple candidates are available, the resolver probes localhost
    to pick whichever port is actively listening to minimize user setup.
    """
    candidates: List[int] = []
    seen: set[int] = set()

    def add_candidate(value: Optional[int]) -> None:
        if value is None or value <= 0:
            return
        if value not in seen:
            candidates.append(value)
            seen.add(value)

    add_candidate(port)
    add_candidate(_safe_int(os.getenv("DOPEMUX_CONPORT_PORT")))
    add_candidate(_safe_int(os.getenv("CONPORT_PORT")))

    url_host: Optional[str] = None
    url_value = os.getenv("CONPORT_URL")
    if url_value:
        try:
            parsed = urlparse(url_value)
            if parsed.port:
                add_candidate(parsed.port)
            url_host = parsed.hostname
        except Exception:
            pass

    base_port = _safe_int(os.getenv("DOPEMUX_PORT_BASE"))
    if base_port:
        add_candidate(base_port + 7)

    add_candidate(DEFAULT_CONPORT_PORT)
    add_candidate(3004)  # Legacy default

    if not candidates:
        candidates.append(DEFAULT_CONPORT_PORT)

    can_probe_local = url_host in (None, "", "localhost", "127.0.0.1")

    async def _async_probe(candidate: int) -> bool:
        """Probe if port is ConPort via /health."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://127.0.0.1:{candidate}/health", timeout=0.5) as resp:
                    return resp.status == 200
        except Exception:
            return _port_is_listening(candidate)

    if can_probe_local:
        # Try a quick sync check for open ports first to avoid waiting for timeouts on closed ones
        listening_candidates = [c for c in candidates if _port_is_listening(c)]
        
        # If any are listening, try to find one that is actually ConPort
        if listening_candidates:
            try:
                # Use a simple loop for the probe to keep it simple for now
                for candidate in listening_candidates:
                    # We use a nested loop with asyncio.run for the probe if not in a running loop
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # If we are in a running loop, we can't use wait/run easily here without blocking
                            # Fallback to listening check
                            return candidate
                        else:
                            if asyncio.run(_async_probe(candidate)):
                                return candidate
                    except Exception:
                        if _port_is_listening(candidate):
                            return candidate
            except Exception:
                pass

        # Fallback to first listening candidate if probe failed
        if listening_candidates:
            return listening_candidates[0]

    # Fallback: return first candidate even if nothing is reachable
    return candidates[0]


# Synchronous wrapper functions for CLI usage

def save_instance_state_sync(
    state: InstanceState,
    workspace_id: str,
    conport_port: Optional[int] = None
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
    resolved_port = resolve_conport_port(conport_port)
    manager = InstanceStateManager(workspace_id, resolved_port)
    try:
        return asyncio.run(manager.save_instance_state(state))
    finally:
        asyncio.run(manager._close_session())


def load_instance_state_sync(
    instance_id: str,
    workspace_id: str,
    conport_port: Optional[int] = None
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
    resolved_port = resolve_conport_port(conport_port)
    manager = InstanceStateManager(workspace_id, resolved_port)
    try:
        return asyncio.run(manager.load_instance_state(instance_id))
    finally:
        asyncio.run(manager._close_session())


def list_all_instance_states_sync(
    workspace_id: str,
    conport_port: Optional[int] = None
) -> List[InstanceState]:
    """
    Synchronous wrapper for list_all_instance_states.

    Args:
        workspace_id: Workspace root path
        conport_port: ConPort API port

    Returns:
        List of all InstanceState objects
    """
    resolved_port = resolve_conport_port(conport_port)
    manager = InstanceStateManager(workspace_id, resolved_port)
    try:
        return asyncio.run(manager.list_all_instance_states())
    finally:
        asyncio.run(manager._close_session())


def cleanup_instance_state_sync(
    instance_id: str,
    workspace_id: str,
    conport_port: Optional[int] = None
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
    resolved_port = resolve_conport_port(conport_port)
    manager = InstanceStateManager(workspace_id, resolved_port)
    try:
        return asyncio.run(manager.cleanup_instance_state(instance_id))
    finally:
        asyncio.run(manager._close_session())
