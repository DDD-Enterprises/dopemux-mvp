"""
Leantime MCP Bridge HTTP Server (SSE transport + REST compatibility endpoints).

This service exposes:
- MCP over SSE (`/sse`, `/messages/`)
- Legacy REST tool endpoint used by existing Dopemux services (`/api/tools/{tool}`)
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Sequence

import httpx
import uvicorn
from mcp import types
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount, Route

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
LEANTIME_API_URL = (
    os.getenv("LEANTIME_API_URL")
    or os.getenv("LEANTIME_URL")
    or "http://leantime:80"
)
LEANTIME_API_TOKEN = os.getenv("LEANTIME_API_TOKEN") or os.getenv("LEANTIME_TOKEN", "")
LEAN_TIME_RATE_LIMIT_SECONDS = float(os.getenv("LEAN_TIME_RATE_LIMIT_SECONDS", "1.0"))
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "3015"))


class LeantimeBridgeError(RuntimeError):
    """Base error for bridge-level failures."""


class ToolValidationError(LeantimeBridgeError):
    """Raised when tool arguments are invalid."""


TOOL_METHOD_CANDIDATES: Dict[str, List[str]] = {
    "create_project": [
        "leantime.rpc.Projects.addProject",
        "leantime.rpc.projects.addProject",
        "leantime.addProject",
    ],
    "list_projects": [
        "leantime.rpc.Projects.getAllProjects",
        "leantime.rpc.projects.getAllProjects",
        "leantime.rpc.projects.getAll",
        "leantime.getProjects",
    ],
    "create_ticket": [
        "leantime.rpc.Tickets.addTicket",
        "leantime.rpc.tickets.addTicket",
        "leantime.addTicket",
    ],
    "list_tickets": [
        "leantime.rpc.Tickets.getAllTickets",
        "leantime.rpc.tickets.getAllTickets",
        "leantime.rpc.tickets.getTickets",
        "leantime.getTickets",
    ],
    "update_ticket": [
        "leantime.rpc.Tickets.updateTicket",
        "leantime.rpc.tickets.updateTicket",
        "leantime.rpc.tickets.editTicket",
        "leantime.editTicket",
    ],
    "get_project_stats": [
        "leantime.rpc.Projects.getProjectProgress",
        "leantime.rpc.projects.getProjectProgress",
        "leantime.rpc.Projects.getProjectStats",
        "leantime.rpc.projects.getProjectStats",
        "leantime.getProjectStats",
    ],
    "create_milestone": [
        "leantime.rpc.Projects.addMilestone",
        "leantime.rpc.projects.addMilestone",
        "leantime.addMilestone",
    ],
}


class LeantimeClient:
    """Client for Leantime JSON-RPC API."""

    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.api_endpoint = f"{self.base_url}/api/jsonrpc"
        self.api_token = api_token
        self.client = None
        self._last_call_time = 0.0
        self._request_id = 0

    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def call_api(self, method: str, params: Dict[str, Any] | None = None) -> Dict[str, Any]:
        """Make a JSON-RPC call to Leantime API with rate limiting."""
        if not self.client:
            raise RuntimeError("LeantimeClient not initialized - use as async context manager")

        current_time = time.time()
        time_since_last_call = current_time - self._last_call_time

        if time_since_last_call < LEAN_TIME_RATE_LIMIT_SECONDS:
            wait_time = LEAN_TIME_RATE_LIMIT_SECONDS - time_since_last_call
            await asyncio.sleep(wait_time)

        self._last_call_time = time.time()
        self._request_id += 1

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_token,
        }
        payload = {
            "jsonrpc": "2.0",
            "id": self._request_id,
            "method": method,
            "params": params or {},
        }

        try:
            response = await self.client.post(
                self.api_endpoint,
                json=payload,
                headers=headers,
            )
            if 300 <= response.status_code < 400:
                location = response.headers.get("location", "")
                response_text = (response.text or "")[:400]
                install_hint = "/install" in location.lower() or "/install" in response_text.lower()
                if install_hint:
                    raise LeantimeBridgeError(
                        "Leantime instance requires initial setup at /install before API calls can succeed"
                    )
                raise LeantimeBridgeError(
                    f"Leantime redirected API call ({response.status_code}) to {location or 'unknown target'}"
                )
            response.raise_for_status()
            try:
                result = response.json()
            except ValueError as exc:
                body_preview = (response.text or "")[:400]
                raise LeantimeBridgeError(
                    f"Leantime returned non-JSON response for {method} (status {response.status_code}): "
                    f"{body_preview}"
                ) from exc

            if "error" in result:
                err = result["error"]
                code = err.get("code", "unknown")
                message = err.get("message", "Unknown Leantime JSON-RPC error")
                raise LeantimeBridgeError(
                    f"Leantime API error ({code}) on {method}: {message}"
                )

            return result.get("result")

        except httpx.HTTPStatusError as e:
            logger.error(
                "Leantime HTTP error for %s: status=%s body=%s",
                method,
                e.response.status_code,
                e.response.text[:400],
            )
            if e.response.status_code in {401, 403}:
                raise LeantimeBridgeError(
                    "Leantime authentication failed (401/403). "
                    "Configure LEANTIME_API_TOKEN (or LEANTIME_TOKEN compatibility env) with a valid API key."
                ) from e
            raise LeantimeBridgeError(
                f"Leantime HTTP error {e.response.status_code} for {method}"
            ) from e
        except Exception as e:
            logger.error("Leantime API call failed for %s: %s", method, e)
            raise


def _tool_specs() -> List[types.Tool]:
    """MCP tool schemas."""
    return [
        types.Tool(
            name="create_project",
            description="Create a new project in Leantime",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Project name"},
                    "description": {"type": "string", "description": "Project description"},
                    "state": {
                        "type": "string",
                        "enum": ["0", "1", "2"],
                        "default": "0",
                        "description": "Project state (0=Open, 1=Closed, 2=Archived)",
                    },
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="list_projects",
            description="List all projects in Leantime",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "enum": ["0", "1", "2"],
                        "description": "Filter by state (0=Open, 1=Closed, 2=Archived)",
                    }
                },
            },
        ),
        types.Tool(
            name="create_ticket",
            description="Create a new ticket/task in Leantime",
            inputSchema={
                "type": "object",
                "properties": {
                    "projectId": {"type": "integer", "description": "Project ID"},
                    "headline": {"type": "string", "description": "Ticket headline"},
                    "description": {"type": "string", "description": "Ticket description"},
                    "priority": {
                        "type": "string",
                        "enum": ["1", "2", "3", "4"],
                        "default": "3",
                        "description": "Priority (1=Low, 2=Medium, 3=High, 4=Critical)",
                    },
                    "type": {
                        "type": "string",
                        "enum": ["task", "bug", "story", "epic"],
                        "default": "task",
                    },
                    "milestoneid": {"type": "integer", "description": "Milestone ID (optional)"},
                },
                "required": ["projectId", "headline"],
            },
        ),
        types.Tool(
            name="list_tickets",
            description="List tickets from Leantime",
            inputSchema={
                "type": "object",
                "properties": {
                    "projectId": {"type": "integer", "description": "Project ID"},
                    "status": {"type": "string", "description": "Filter by status"},
                    "assignedTo": {"type": "integer", "description": "Filter by assigned user ID"},
                },
            },
        ),
        types.Tool(
            name="update_ticket",
            description="Update a ticket in Leantime",
            inputSchema={
                "type": "object",
                "properties": {
                    "ticketId": {"type": "integer", "description": "Ticket ID"},
                    "headline": {"type": "string", "description": "New headline"},
                    "description": {"type": "string", "description": "New description"},
                    "status": {"type": "string", "description": "New status"},
                    "priority": {
                        "type": "string",
                        "enum": ["1", "2", "3", "4"],
                        "description": "Priority",
                    },
                    "assignedTo": {"type": "integer", "description": "Assigned user ID"},
                },
                "required": ["ticketId"],
            },
        ),
        types.Tool(
            name="get_project_stats",
            description="Get project statistics and progress",
            inputSchema={
                "type": "object",
                "properties": {
                    "projectId": {"type": "integer", "description": "Project ID"}
                },
                "required": ["projectId"],
            },
        ),
        types.Tool(
            name="create_milestone",
            description="Create a milestone in Leantime",
            inputSchema={
                "type": "object",
                "properties": {
                    "projectId": {"type": "integer", "description": "Project ID"},
                    "headline": {"type": "string", "description": "Milestone headline"},
                    "description": {"type": "string", "description": "Milestone description"},
                    "editFrom": {"type": "string", "format": "date", "description": "Start date"},
                    "editTo": {"type": "string", "format": "date", "description": "End date"},
                },
                "required": ["projectId", "headline"],
            },
        ),
        types.Tool(
            name="sync_with_external",
            description="Sync Leantime data with external task management systems",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {
                        "type": "string",
                        "enum": ["task-master-ai", "task-orchestrator"],
                        "description": "External system to sync with",
                    },
                    "projectId": {"type": "integer", "description": "Project ID to sync"},
                    "syncDirection": {
                        "type": "string",
                        "enum": ["import", "export", "bidirectional"],
                        "default": "bidirectional",
                    },
                },
                "required": ["source", "projectId"],
            },
        ),
    ]


def _coerce_int(value: Any, field_name: str) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ToolValidationError(f"{field_name} must be an integer") from exc


def _normalize_priority(value: Any) -> str:
    if value is None:
        return "2"
    if isinstance(value, int):
        return str(min(max(value, 1), 4))
    if isinstance(value, str) and value.strip().isdigit():
        parsed = int(value.strip())
        return str(min(max(parsed, 1), 4))

    mapped = {
        "low": "1",
        "medium": "2",
        "med": "2",
        "high": "3",
        "critical": "4",
        "urgent": "4",
    }
    return mapped.get(str(value).strip().lower(), "2")


def _method_candidates_for(tool_name: str) -> List[str]:
    candidates = TOOL_METHOD_CANDIDATES.get(tool_name)
    if not candidates:
        raise ToolValidationError(f"Unknown tool: {tool_name}")
    return candidates


def _normalize_tool_and_args(name: str, arguments: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
    tool_name = name.strip()
    args = dict(arguments or {})

    # Backward-compat aliases used by existing Dopemux services
    if tool_name == "update_ticket_status":
        tool_name = "update_ticket"
    if tool_name == "create_task":
        tool_name = "create_ticket"
    elif tool_name == "list_tasks":
        tool_name = "list_tickets"

    if tool_name == "create_ticket":
        if "headline" not in args and "title" in args:
            args["headline"] = args["title"]
        if "projectId" not in args:
            if "project_id" in args:
                args["projectId"] = args["project_id"]
            else:
                args["projectId"] = 1
        args["projectId"] = _coerce_int(args["projectId"], "projectId")
        if "headline" not in args or not str(args["headline"]).strip():
            raise ToolValidationError("create_ticket requires 'headline' (or 'title')")
        args["priority"] = _normalize_priority(args.get("priority"))
        if "milestoneid" in args:
            args["milestoneid"] = _coerce_int(args["milestoneid"], "milestoneid")

    if tool_name == "update_ticket":
        if "ticketId" not in args:
            for fallback_field in ("task_id", "taskId", "id", "sprint_id", "sprintId"):
                if fallback_field in args:
                    args["ticketId"] = args[fallback_field]
                    break
        if "ticketId" not in args:
            raise ToolValidationError("update_ticket requires 'ticketId'")
        args["ticketId"] = _coerce_int(args["ticketId"], "ticketId")
        if "priority" in args:
            args["priority"] = _normalize_priority(args["priority"])

    if tool_name == "create_project":
        if "name" not in args:
            for fallback_field in ("project_name", "title"):
                if fallback_field in args:
                    args["name"] = args[fallback_field]
                    break
        if "description" not in args and "details" in args:
            details = args["details"]
            args["description"] = (
                details if isinstance(details, str) else json.dumps(details, ensure_ascii=True)
            )
        if "name" not in args or not str(args["name"]).strip():
            raise ToolValidationError("create_project requires 'name'")

    if tool_name == "get_project_stats":
        if "projectId" not in args:
            for fallback_field in ("project_id", "id"):
                if fallback_field in args:
                    args["projectId"] = args[fallback_field]
                    break
        if "projectId" not in args:
            raise ToolValidationError("get_project_stats requires 'projectId'")
        args["projectId"] = _coerce_int(args["projectId"], "projectId")

    if tool_name == "create_milestone":
        if "projectId" not in args and "project_id" in args:
            args["projectId"] = args["project_id"]
        if "projectId" not in args:
            raise ToolValidationError("create_milestone requires 'projectId'")
        args["projectId"] = _coerce_int(args["projectId"], "projectId")
        if "headline" not in args and "name" in args:
            args["headline"] = args["name"]
        if "headline" not in args:
            raise ToolValidationError("create_milestone requires 'headline'")

    if tool_name == "list_tickets" and "project_id" in args and "projectId" not in args:
        args["projectId"] = args["project_id"]
    if tool_name == "list_tickets" and "projectId" in args:
        args["projectId"] = _coerce_int(args["projectId"], "projectId")
    if tool_name == "list_tickets" and "assigned_to" in args and "assignedTo" not in args:
        args["assignedTo"] = args["assigned_to"]
    if tool_name == "list_tickets" and "assignedTo" in args:
        args["assignedTo"] = _coerce_int(args["assignedTo"], "assignedTo")

    return tool_name, args


async def _call_tool_with_method_fallback(
    client: LeantimeClient,
    tool_name: str,
    arguments: Dict[str, Any],
) -> Any:
    candidates = _method_candidates_for(tool_name)
    last_error: Exception | None = None

    for method in candidates:
        try:
            return await client.call_api(method, arguments)
        except Exception as exc:
            last_error = exc
            message = str(exc).lower()
            terminal_error = (
                "requires initial setup" in message
                or "/install" in message
                or "authentication failed" in message
            )
            logger.warning(
                "Leantime method candidate failed for %s: %s (%s)",
                tool_name,
                method,
                str(exc)[:200],
            )
            if terminal_error:
                raise

    raise LeantimeBridgeError(
        f"All method candidates failed for tool '{tool_name}': "
        + "; ".join(candidates)
    ) from last_error


async def execute_tool(name: str, arguments: Dict[str, Any]) -> Any:
    """Execute a Leantime tool and return structured JSON-serializable data."""
    tool_name, normalized_args = _normalize_tool_and_args(name, arguments)

    if tool_name == "sync_with_external":
        return {
            "status": "initiated",
            "source": normalized_args.get("source"),
            "projectId": normalized_args.get("projectId"),
            "syncDirection": normalized_args.get("syncDirection", "bidirectional"),
        }

    async with LeantimeClient(LEANTIME_API_URL, LEANTIME_API_TOKEN) as client:
        return await _call_tool_with_method_fallback(client, tool_name, normalized_args)


def _format_mcp_text_result(tool_name: str, result: Any) -> str:
    payload = {
        "tool": tool_name,
        "result": result,
    }
    return json.dumps(payload, indent=2, default=str)


app = Server("leantime-bridge")


@app.list_tools()
async def list_tools() -> List[types.Tool]:
    return _tool_specs()


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Handle MCP tool calls."""
    try:
        result = await execute_tool(name, arguments)
        return [types.TextContent(type="text", text=_format_mcp_text_result(name, result))]
    except Exception as e:
        logger.error("Tool call failed: %s: %s", name, e)
        return [types.TextContent(type="text", text=f"Error: {str(e)}")]


# Create SSE transport
sse = SseServerTransport("/messages/")


async def handle_sse(request: Request) -> Response:
    """Handle SSE connection endpoint."""
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await app.run(
            streams[0], streams[1], app.create_initialization_options()
        )
    return Response()


async def handle_health(request: Request) -> Response:
    """Health endpoint.

    - `GET /health` returns lightweight liveness by default.
    - `GET /health?deep=1` performs a Leantime API call for readiness.
    """
    deep = request.query_params.get("deep", "0").lower() in {"1", "true", "yes"}
    if not deep:
        return JSONResponse(
            {
                "status": "ok",
                "service": "leantime-bridge",
                "transport": "http-sse",
            },
            status_code=200,
        )

    try:
        async with LeantimeClient(LEANTIME_API_URL, LEANTIME_API_TOKEN) as client:
            await _call_tool_with_method_fallback(client, "list_projects", {})
        return JSONResponse(
            {"status": "ok", "service": "leantime-bridge", "leantime": "reachable"},
            status_code=200,
        )
    except Exception as exc:
        message = str(exc)
        setup_required = "/install" in message.lower() or "requires initial setup" in message.lower()
        return JSONResponse(
            {
                "status": "needs_setup" if setup_required else "degraded",
                "service": "leantime-bridge",
                "leantime": "setup_required" if setup_required else "unreachable",
                "error": message,
                "action": "Complete Leantime setup at /install and configure LEANTIME_API_TOKEN"
                if setup_required
                else None,
            },
            status_code=503,
        )


async def handle_info(request: Request) -> Response:
    """Service discovery endpoint (ADR-208)."""
    base_url = str(request.base_url).rstrip("/")

    leantime_status = "unknown"
    leantime_version = None
    try:
        async with LeantimeClient(LEANTIME_API_URL, LEANTIME_API_TOKEN) as client:
            await _call_tool_with_method_fallback(client, "list_projects", {})
            leantime_status = "healthy"
    except Exception as e:
        logger.warning("Leantime health check failed: %s", e)
        if "/install" in str(e).lower() or "requires initial setup" in str(e).lower():
            leantime_status = "setup_required"
        else:
            leantime_status = f"unhealthy: {str(e)[:100]}"

    info = {
        "name": "leantime-bridge",
        "version": "1.1.0",
        "leantime": {
            "url": LEANTIME_API_URL,
            "status": leantime_status,
            "version": leantime_version,
            "rate_limit_seconds": LEAN_TIME_RATE_LIMIT_SECONDS,
        },
        "mcp": {
            "protocol": "sse",
            "endpoints": {
                "sse": f"{base_url}/sse",
                "messages": f"{base_url}/messages/",
                "health": f"{base_url}/health",
                "info": f"{base_url}/info",
                "api_tools": f"{base_url}/api/tools",
            },
            "connection": {
                "type": "sse",
                "url": f"{base_url}/sse",
            },
            "env": {
                "LEANTIME_API_TOKEN": "${LEANTIME_API_TOKEN:-}",
                "LEANTIME_TOKEN": "${LEANTIME_TOKEN:-}",
            },
        },
        "health": "/health",
        "description": "Leantime project management integration bridge (HTTP/SSE + REST compatibility)",
        "metadata": {
            "role": "workflow",
            "priority": "high",
            "integration": "leantime",
            "transport": "http-sse",
            "plane": "pm_plane",
            "tools_count": len(_tool_specs()),
        },
    }
    return Response(json.dumps(info, indent=2), media_type="application/json")


async def handle_list_tools_http(request: Request) -> Response:
    """REST compatibility: list tools available via /api/tools."""
    tools = [
        {
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.inputSchema,
        }
        for tool in _tool_specs()
    ]
    return JSONResponse({"tools": tools, "count": len(tools)}, status_code=200)


async def handle_tool_http(request: Request) -> Response:
    """REST compatibility endpoint used by DopeconBridge MCPClientManager.

    Expected request:
    POST /api/tools/{tool_name}
    Body: JSON object arguments
    """
    tool_name = request.path_params["tool_name"]

    try:
        payload = await request.json()
    except json.JSONDecodeError:
        payload = {}

    if not isinstance(payload, dict):
        return JSONResponse(
            {"error": "Request body must be a JSON object"},
            status_code=400,
        )

    try:
        result = await execute_tool(tool_name, payload)
        return JSONResponse(result, status_code=200)
    except ToolValidationError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:
        logger.error("HTTP tool execution failed (%s): %s", tool_name, exc)
        return JSONResponse({"error": str(exc)}, status_code=502)


# Create Starlette application
starlette_app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Route("/health", endpoint=handle_health, methods=["GET"]),
        Route("/info", endpoint=handle_info, methods=["GET"]),
        Route("/api/tools", endpoint=handle_list_tools_http, methods=["GET"]),
        Route("/api/tools/{tool_name}", endpoint=handle_tool_http, methods=["POST"]),
        Mount("/messages/", app=sse.handle_post_message),
    ]
)


async def main():
    """Run the HTTP MCP server."""
    logger.info("Starting Leantime MCP Bridge HTTP Server")
    logger.info("Server URL: http://%s:%s", MCP_SERVER_HOST, MCP_SERVER_PORT)
    logger.info("SSE Endpoint: http://%s:%s/sse", MCP_SERVER_HOST, MCP_SERVER_PORT)
    logger.info("POST Endpoint: http://%s:%s/messages/", MCP_SERVER_HOST, MCP_SERVER_PORT)
    logger.info("Connecting to Leantime at: %s", LEANTIME_API_URL)

    config = uvicorn.Config(
        starlette_app,
        host=MCP_SERVER_HOST,
        port=MCP_SERVER_PORT,
        log_level="info",
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
