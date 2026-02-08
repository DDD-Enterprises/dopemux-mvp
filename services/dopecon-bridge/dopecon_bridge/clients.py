"""
DopeconBridge Clients - MCP and ConPort HTTP clients.

Extracted from main.py lines 417-656.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp
from fastapi import HTTPException, Request
from tenacity import retry, stop_after_attempt, wait_exponential

from .config import settings
from .core import cache_manager


logger = logging.getLogger(__name__)


def _build_mcp_error_detail(
    service: str,
    tool_name: str,
    status: Optional[int] = None,
    upstream_text: str = "",
    transport_error: Optional[str] = None,
) -> str:
    """Generate actionable error details for MCP upstream failures."""
    context = f"{service}.{tool_name}"
    if transport_error:
        base = f"MCP call failed for {context}: {transport_error}"
    else:
        base = f"MCP call failed for {context} with upstream status {status}"
        if upstream_text:
            base += f" ({upstream_text[:300]})"

    if service == "leantime-bridge":
        lowered = upstream_text.lower()
        setup_signals = (
            "token",
            "api key",
            "unauthorized",
            "forbidden",
            "setup",
            "install",
            "wizard",
            "login",
            "not configured",
            "redirect",
        )
        if transport_error or status in {401, 403, 404, 409, 422, 500, 502, 503} or any(
            signal in lowered for signal in setup_signals
        ):
            base += (
                " | Leantime readiness hint: complete the Leantime web setup wizard at "
                "http://localhost:8080, generate/verify API credentials, and configure "
                "LEANTIME_API_TOKEN for leantime-bridge."
            )
    return base


class MCPClientManager:
    """Manages connections to instance-specific MCP servers."""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        """Initialize HTTP session for MCP server communication."""
        if self.session:
            return
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(timeout=timeout)
        logger.info("✅ MCP client manager initialized")

    async def call_tool(self, service: str, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on an instance-specific MCP service."""
        if not self.session:
            raise RuntimeError("MCP client not initialized")

        service_url = self._get_service_url(service)
        url = f"{service_url}/api/tools/{tool_name}"

        try:
            async with self.session.post(url, json=arguments) as response:
                raw_text = await response.text()
                if response.status >= 400:
                    detail = _build_mcp_error_detail(
                        service=service,
                        tool_name=tool_name,
                        status=response.status,
                        upstream_text=raw_text,
                    )
                    logger.error("❌ %s", detail)
                    raise HTTPException(status_code=502, detail=detail)

                if raw_text:
                    try:
                        result = json.loads(raw_text)
                    except json.JSONDecodeError:
                        result = {"raw_response": raw_text}
                else:
                    result = {}
                logger.debug(f"🔧 {service}.{tool_name} -> {result}")
                return result

        except HTTPException:
            raise
        except aiohttp.ClientError as e:
            detail = _build_mcp_error_detail(
                service=service,
                tool_name=tool_name,
                transport_error=str(e),
            )
            logger.error("❌ %s", detail)
            raise HTTPException(status_code=502, detail=detail)

    def _get_service_url(self, service: str) -> str:
        """Get instance-specific service URL."""
        urls = {
            "task-master-ai": settings.task_master_url,
            "task-orchestrator": settings.task_orchestrator_url,
            "leantime-bridge": settings.leantime_bridge_url
        }
        url = urls.get(service)
        if not url:
            raise ValueError(f"Unknown service: {service}")
        return url

    async def health_check_all(self) -> Dict[str, bool]:
        """Check health of all connected services."""
        if not self.session:
            return {"status": "not_initialized"}

        services = ["task-master-ai", "task-orchestrator", "leantime-bridge"]
        health_status = {}

        for service in services:
            try:
                service_url = self._get_service_url(service)
                async with self.session.get(f"{service_url}/health") as response:
                    health_status[service] = response.status == 200
            except Exception as e:
                health_status[service] = False
                logger.error(f"Health check failed for {service}: {e}")
        
        return health_status

    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None


class ConPortClient:
    """ConPort client for ADHD-friendly context preservation across instances."""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = settings.conport_url
        self.workspace_id = settings.default_workspace_id
        self._initialized = False

    async def initialize(self):
        """Lazy initialization of HTTP session."""
        if self._initialized:
            return
        timeout = aiohttp.ClientTimeout(total=10, connect=5)
        self.session = aiohttp.ClientSession(timeout=timeout)
        self._initialized = True
        logger.info("✅ ConPort client initialized")

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    async def get_context(self, context_token: str) -> Dict[str, Any]:
        """Get context from ConPort with circuit breaker pattern."""
        if not self.session:
            await self.initialize()

        try:
            url = f"{self.base_url}/api/context/{context_token}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    context = await response.json()
                    logger.debug(f"🧠 Retrieved context for token {context_token[:8]}...")
                    return context
                elif response.status == 404:
                    return {"workspace_id": self.workspace_id, "session_data": {}}
                else:
                    response.raise_for_status()

        except Exception as e:
            logger.warning(f"⚠️ ConPort context retrieval failed: {e}")
            return await self._get_fallback_context(context_token)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=10))
    async def update_context(self, context_token: str, context_deltas: Dict[str, Any]) -> bool:
        """Update context in ConPort with deltas."""
        if not self.session:
            await self.initialize()

        try:
            url = f"{self.base_url}/api/context/{context_token}"
            payload = {
                "workspace_id": self.workspace_id,
                "deltas": context_deltas,
                "timestamp": datetime.utcnow().isoformat()
            }

            async with self.session.patch(url, json=payload) as response:
                if response.status in [200, 201]:
                    logger.debug(f"💾 Updated context for token {context_token[:8]}...")
                    await self._update_fallback_context(context_token, context_deltas)
                    return True
                else:
                    response.raise_for_status()

        except Exception as e:
            logger.warning(f"⚠️ ConPort context update failed: {e}")
            await self._update_fallback_context(context_token, context_deltas)
            return False

    async def _get_fallback_context(self, context_token: str) -> Dict[str, Any]:
        """Get context from Redis fallback cache."""
        try:
            cache_client = await cache_manager.get_client()
            cached_context = await cache_client.get(f"context_fallback:{context_token}")
            if cached_context:
                return json.loads(cached_context)
        except Exception as e:
            logger.error(f"❌ Fallback context retrieval failed: {e}")

        return {"workspace_id": self.workspace_id, "session_data": {}}

    async def _update_fallback_context(self, context_token: str, context_deltas: Dict[str, Any]):
        """Update Redis fallback cache with context deltas."""
        try:
            cache_client = await cache_manager.get_client()

            existing_raw = await cache_client.get(f"context_fallback:{context_token}")
            existing_context = json.loads(existing_raw) if existing_raw else {
                "workspace_id": self.workspace_id, 
                "session_data": {}
            }

            for key, value in context_deltas.items():
                if value == "__DELETE__":
                    existing_context["session_data"].pop(key, None)
                else:
                    existing_context["session_data"][key] = value

            await cache_client.setex(
                f"context_fallback:{context_token}",
                3600,  # 1 hour TTL
                json.dumps(existing_context, default=str)
            )

        except Exception as e:
            logger.error(f"❌ Fallback context update failed: {e}")

    async def close(self):
        """Close HTTP session."""
        if self.session:
            await self.session.close()
            self._initialized = False


class ConPortMiddleware:
    """Middleware for ADHD-friendly context preservation."""

    def __init__(self, conport_client: ConPortClient):
        self.conport_client = conport_client

    async def __call__(self, request: Request, call_next):
        """Process request with context hydration and delta persistence."""
        context_token = request.headers.get("X-Context-Token")

        if context_token:
            try:
                context = await self.conport_client.get_context(context_token)
                request.state.context = context
                request.state.context_token = context_token
                request.state.context_deltas = {}
                logger.debug(f"🧠 Context hydrated for {request.url.path}")
            except Exception as e:
                logger.warning(f"⚠️ Context hydration failed: {e}")
                request.state.context = {"workspace_id": self.conport_client.workspace_id, "session_data": {}}
                request.state.context_token = context_token
                request.state.context_deltas = {}
        else:
            request.state.context = None
            request.state.context_token = None
            request.state.context_deltas = {}

        response = await call_next(request)

        # Persist context deltas after request
        if context_token and hasattr(request.state, 'context_deltas') and request.state.context_deltas:
            try:
                await self.conport_client.update_context(context_token, request.state.context_deltas)
                logger.debug(f"💾 Context deltas persisted for {request.url.path}")
            except Exception as e:
                logger.warning(f"⚠️ Context delta persistence failed: {e}")

        return response


def update_context_delta(request: Request, key: str, value: Any):
    """Update context delta during request processing."""
    if hasattr(request.state, 'context_deltas'):
        request.state.context_deltas[key] = value
        logger.debug(f"📝 Context delta: {key} = {value}")


# Global singleton instances
mcp_client = MCPClientManager()
conport_client = ConPortClient()
