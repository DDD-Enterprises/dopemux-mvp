"""
Task-Orchestrator Core - Connection management.

Extracted from enhanced_orchestrator.py lines 278-397.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import aiohttp
import redis.asyncio as redis

from .config import settings


logger = logging.getLogger(__name__)

# Request ID counter
_request_id = 0


def _next_request_id() -> int:
    """Generate next JSON-RPC request ID."""
    global _request_id
    _request_id += 1
    return _request_id


class LeantimeClient:
    """Manages connection to Leantime JSON-RPC API."""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = settings.leantime_url.rstrip('/')
        self._initialized = False

    async def initialize(self):
        """Initialize connection to Leantime."""
        if self._initialized:
            return

        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "Authorization": f"Bearer {settings.leantime_token}",
                "Content-Type": "application/json"
            }
        )

        # Test connection
        if await self.test_connection():
            self._initialized = True
            logger.info("🔗 Connected to Leantime API")
        else:
            logger.warning("⚠️ Leantime connection test failed")

    async def test_connection(self) -> bool:
        """Test Leantime API connectivity."""
        try:
            async with self.session.post(
                f"{self.base_url}/api/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "leantime.rpc.projects.getAllProjects",
                    "params": {"limit": 1},
                    "id": _next_request_id()
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return "result" in data
                return False
        except Exception as e:
            logger.error(f"Leantime connection test failed: {e}")
            return False

    async def fetch_updated_tasks(self, since: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Fetch tasks updated since given timestamp."""
        if not self.session:
            return []

        if since is None:
            since = datetime.now(timezone.utc) - timedelta(hours=24)

        try:
            async with self.session.post(
                f"{self.base_url}/api/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "leantime.rpc.tickets.getAllTickets",
                    "params": {
                        "limit": 100,
                        "since": since.isoformat()
                    },
                    "id": _next_request_id()
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    tasks = data.get("result", [])
                    return tasks if isinstance(tasks, list) else []
        except Exception as e:
            logger.error(f"Failed to fetch Leantime tasks: {e}")
        
        return []

    async def update_ticket_status(self, ticket_id: int, status: str) -> bool:
        """Update ticket status in Leantime."""
        if not self.session:
            return False

        try:
            async with self.session.post(
                f"{self.base_url}/api/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "leantime.rpc.tickets.updateTicket",
                    "params": {
                        "id": ticket_id,
                        "status": status
                    },
                    "id": _next_request_id()
                }
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Failed to update Leantime ticket: {e}")
            return False

    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self._initialized = False


class RedisManager:
    """Manages Redis for caching and coordination."""

    def __init__(self):
        self.client: Optional[redis.Redis] = None
        self._initialized = False

    async def initialize(self):
        """Initialize Redis connection."""
        if self._initialized:
            return

        try:
            self.client = redis.from_url(
                settings.redis_url,
                db=settings.redis_db,
                decode_responses=True,
                password=settings.redis_password if settings.redis_password else None
            )
            await self.client.ping()
            self._initialized = True
            logger.info("🔗 Connected to Redis for coordination")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def get_last_poll(self) -> Optional[datetime]:
        """Get last poll timestamp."""
        if not self.client:
            return None
        
        last_poll = await self.client.get("orchestrator:last_poll")
        if last_poll:
            return datetime.fromisoformat(last_poll)
        return None

    async def set_last_poll(self, timestamp: datetime):
        """Set last poll timestamp."""
        if self.client:
            await self.client.set("orchestrator:last_poll", timestamp.isoformat())

    async def cache_set(self, key: str, value: str, ttl: int = 3600):
        """Set cache value with TTL."""
        if self.client:
            await self.client.setex(key, ttl, value)

    async def cache_get(self, key: str) -> Optional[str]:
        """Get cached value."""
        if self.client:
            return await self.client.get(key)
        return None

    async def close(self):
        """Close Redis connection."""
        if self.client:
            await self.client.close()
            self._initialized = False


# Global singleton instances
leantime_client = LeantimeClient()
redis_manager = RedisManager()

# Task decomposition instances (initialized lazily on first request)
_task_coordinator = None
_pal_client = None
_conport_adapter = None


def get_task_coordinator():
    """Get or create TaskCoordinator singleton."""
    global _task_coordinator
    if _task_coordinator is None:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from task_coordinator import TaskCoordinator
        _task_coordinator = TaskCoordinator(workspace_id=settings.workspace_id)
        logger.info(f"✅ TaskCoordinator initialized for workspace: {settings.workspace_id}")
    return _task_coordinator


def get_pal_client():
    """Get or create PALClient singleton."""
    global _pal_client
    if _pal_client is None:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from pal_client import TaskOrchestratorPALClient
        # Pal MCP server runs on port 3003
        _pal_client = TaskOrchestratorPALClient("http://localhost:3003", {})
        logger.info("✅ PALClient initialized (http://localhost:3003)")
    return _pal_client


def get_conport_adapter():
    """Get or create ConPortEventAdapter singleton."""
    global _conport_adapter
    if _conport_adapter is None:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from adapters.conport_adapter import ConPortEventAdapter
        _conport_adapter = ConPortEventAdapter(workspace_id=settings.workspace_id)
        logger.info(f"✅ ConPortEventAdapter initialized for workspace: {settings.workspace_id}")
    return _conport_adapter
