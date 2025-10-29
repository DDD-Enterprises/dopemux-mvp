"""
Leantime MCP Bridge HTTP Server (SSE Transport)
Connects Leantime JSON-RPC API to MCP protocol via HTTP/SSE for task management integration
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional, Sequence

import httpx
import uvicorn
from mcp import types
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from pydantic import BaseModel
from jsonrpcclient import request, parse, Ok
from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
LEANTIME_API_URL = os.getenv("LEANTIME_API_URL", "http://leantime:80")
LEANTIME_API_TOKEN = os.getenv("LEANTIME_API_TOKEN", "")
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "3015"))

class LeantimeClient:
    """Client for Leantime JSON-RPC API"""

    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url.rstrip('/')
        self.api_endpoint = f"{self.base_url}/api/jsonrpc"
        self.api_token = api_token
        self.client = None

    async def __aenter__(self):
        # Use httpx instead of aiohttp (works better in Docker)
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def call_api(self, method: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a JSON-RPC call to Leantime API"""
        if not self.client:
            raise RuntimeError("LeantimeClient not initialized - use as async context manager")

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_token
        }

        payload = request(method, params or {})

        try:
            response = await self.client.post(
                self.api_endpoint,
                json=payload,
                headers=headers
            )
            response.raise_for_status()
            result = response.json()

            parsed = parse(result)
            if isinstance(parsed, Ok):
                return parsed.result
            else:
                raise Exception(f"Leantime API error: {parsed}")

        except Exception as e:
            logger.error(f"Leantime API call failed: {e}")
            raise

# Initialize MCP server
app = Server("leantime-bridge")

@app.list_tools()
async def list_tools() -> List[types.Tool]:
    """List available Leantime integration tools"""
    return [
        types.Tool(
            name="create_project",
            description="Create a new project in Leantime",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Project name"},
                    "description": {"type": "string", "description": "Project description"},
                    "state": {"type": "string", "enum": ["0", "1", "2"], "default": "0", "description": "Project state (0=Open, 1=Closed, 2=Archived)"}
                },
                "required": ["name"]
            }
        ),
        types.Tool(
            name="list_projects",
            description="List all projects in Leantime",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {"type": "string", "enum": ["0", "1", "2"], "description": "Filter by state (0=Open, 1=Closed, 2=Archived)"}
                }
            }
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
                    "priority": {"type": "string", "enum": ["1", "2", "3", "4"], "default": "3", "description": "Priority (1=Low, 2=Medium, 3=High, 4=Critical)"},
                    "type": {"type": "string", "enum": ["task", "bug", "story", "epic"], "default": "task"},
                    "milestoneid": {"type": "integer", "description": "Milestone ID (optional)"}
                },
                "required": ["projectId", "headline"]
            }
        ),
        types.Tool(
            name="list_tickets",
            description="List tickets from Leantime",
            inputSchema={
                "type": "object",
                "properties": {
                    "projectId": {"type": "integer", "description": "Project ID"},
                    "status": {"type": "string", "description": "Filter by status"},
                    "assignedTo": {"type": "integer", "description": "Filter by assigned user ID"}
                }
            }
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
                    "priority": {"type": "string", "enum": ["1", "2", "3", "4"], "description": "Priority"},
                    "assignedTo": {"type": "integer", "description": "Assigned user ID"}
                },
                "required": ["ticketId"]
            }
        ),
        types.Tool(
            name="get_project_stats",
            description="Get project statistics and progress",
            inputSchema={
                "type": "object",
                "properties": {
                    "projectId": {"type": "integer", "description": "Project ID"}
                },
                "required": ["projectId"]
            }
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
                    "editTo": {"type": "string", "format": "date", "description": "End date"}
                },
                "required": ["projectId", "headline"]
            }
        ),
        types.Tool(
            name="sync_with_external",
            description="Sync Leantime data with external task management systems",
            inputSchema={
                "type": "object",
                "properties": {
                    "source": {"type": "string", "enum": ["task-master-ai", "task-orchestrator"], "description": "External system to sync with"},
                    "projectId": {"type": "integer", "description": "Project ID to sync"},
                    "syncDirection": {"type": "string", "enum": ["import", "export", "bidirectional"], "default": "bidirectional"}
                },
                "required": ["source", "projectId"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> Sequence[types.TextContent]:
    """Handle tool calls to Leantime API"""

    async with LeantimeClient(LEANTIME_API_URL, LEANTIME_API_TOKEN) as client:
        try:
            if name == "create_project":
                result = await client.call_api("leantime.addProject", arguments)
                return [types.TextContent(
                    type="text",
                    text=f"Project created successfully: {json.dumps(result, indent=2)}"
                )]

            elif name == "list_projects":
                result = await client.call_api("leantime.getProjects", arguments)
                return [types.TextContent(
                    type="text",
                    text=f"Projects: {json.dumps(result, indent=2)}"
                )]

            elif name == "create_ticket":
                result = await client.call_api("leantime.addTicket", arguments)
                return [types.TextContent(
                    type="text",
                    text=f"Ticket created successfully: {json.dumps(result, indent=2)}"
                )]

            elif name == "list_tickets":
                result = await client.call_api("leantime.getTickets", arguments)
                return [types.TextContent(
                    type="text",
                    text=f"Tickets: {json.dumps(result, indent=2)}"
                )]

            elif name == "update_ticket":
                result = await client.call_api("leantime.editTicket", arguments)
                return [types.TextContent(
                    type="text",
                    text=f"Ticket updated successfully: {json.dumps(result, indent=2)}"
                )]

            elif name == "get_project_stats":
                result = await client.call_api("leantime.getProjectStats", arguments)
                return [types.TextContent(
                    type="text",
                    text=f"Project statistics: {json.dumps(result, indent=2)}"
                )]

            elif name == "create_milestone":
                result = await client.call_api("leantime.addMilestone", arguments)
                return [types.TextContent(
                    type="text",
                    text=f"Milestone created successfully: {json.dumps(result, indent=2)}"
                )]

            elif name == "sync_with_external":
                # This would implement synchronization logic with other MCP servers
                return [types.TextContent(
                    type="text",
                    text=f"Sync operation initiated: {json.dumps(arguments, indent=2)}"
                )]

            else:
                raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            return [types.TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]

# Create SSE transport
sse = SseServerTransport("/messages/")

async def handle_sse(request: Request) -> Response:
    """Handle SSE connection endpoint"""
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await app.run(
            streams[0], streams[1], app.create_initialization_options()
        )
    return Response()

# Create Starlette application
starlette_app = Starlette(
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages/", app=sse.handle_post_message),
    ]
)

async def main():
    """Run the HTTP MCP server"""
    logger.info(f"Starting Leantime MCP Bridge HTTP Server")
    logger.info(f"Server URL: http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}")
    logger.info(f"SSE Endpoint: http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}/sse")
    logger.info(f"POST Endpoint: http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}/messages/")
    logger.info(f"Connecting to Leantime at: {LEANTIME_API_URL}")

    config = uvicorn.Config(
        starlette_app,
        host=MCP_SERVER_HOST,
        port=MCP_SERVER_PORT,
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
