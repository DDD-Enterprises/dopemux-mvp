"""
MCP Service Discovery - /info endpoint template.

Add this to any MCP server to enable automatic service discovery.

Usage:
    from mcp_service_info import add_info_endpoint
    
    app = FastAPI()
    add_info_endpoint(
        app,
        name="my-mcp-server",
        version="1.0.0",
        protocol="sse",
        connection_url="http://localhost:3009/sse",
        description="My MCP server description"
    )
"""

from typing import Dict, Any, Optional, List
from fastapi import FastAPI
from pydantic import BaseModel


class MCPConnectionSSE(BaseModel):
    """SSE connection details."""
    type: str = "sse"
    url: str


class MCPConnectionStdio(BaseModel):
    """Stdio connection details."""
    type: str = "stdio"
    command: str
    args: List[str]


class MCPInfo(BaseModel):
    """MCP protocol information."""
    protocol: str  # "sse" or "stdio"
    connection: Dict[str, Any]
    env: Optional[Dict[str, str]] = None


class ServerInfo(BaseModel):
    """Complete server information for service discovery."""
    name: str
    version: str
    mcp: MCPInfo
    health: str = "/health"
    description: str = ""
    metadata: Optional[Dict[str, Any]] = None


def add_info_endpoint(
    app: FastAPI,
    name: str,
    version: str,
    protocol: str,
    connection_url: Optional[str] = None,
    connection_command: Optional[str] = None,
    connection_args: Optional[List[str]] = None,
    description: str = "",
    env_vars: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """
    Add /info endpoint to FastAPI app for service discovery.
    
    Args:
        app: FastAPI application instance
        name: Server canonical name (e.g., "gpt-researcher")
        version: Semantic version (e.g., "1.0.0")
        protocol: "sse" or "stdio"
        connection_url: SSE endpoint URL (if protocol="sse")
        connection_command: Command for stdio (if protocol="stdio")
        connection_args: Args for stdio (if protocol="stdio")
        description: Human-readable server description
        env_vars: Required environment variables
        metadata: Additional server metadata
    
    Example (SSE):
        add_info_endpoint(
            app,
            name="gpt-researcher",
            version="1.0.0",
            protocol="sse",
            connection_url="http://localhost:3009/sse",
            description="Deep research with comprehensive analysis"
        )
    
    Example (Stdio):
        add_info_endpoint(
            app,
            name="task-orchestrator",
            version="1.0.0",
            protocol="stdio",
            connection_command="python3",
            connection_args=["/app/server.py"],
            description="Task orchestration with 37 tools"
        )
    """
    
    # Build connection info
    if protocol == "sse":
        if not connection_url:
            raise ValueError("connection_url required for SSE protocol")
        connection = {
            "type": "sse",
            "url": connection_url
        }
    elif protocol == "stdio":
        if not connection_command:
            raise ValueError("connection_command required for stdio protocol")
        connection = {
            "type": "stdio",
            "command": connection_command,
            "args": connection_args or []
        }
    else:
        raise ValueError(f"Unknown protocol: {protocol}")
    
    # Build MCP info
    mcp_info = MCPInfo(
        protocol=protocol,
        connection=connection,
        env=env_vars
    )
    
    # Build server info
    server_info = ServerInfo(
        name=name,
        version=version,
        mcp=mcp_info,
        description=description,
        metadata=metadata
    )
    
    @app.get("/info", response_model=ServerInfo)
    async def info():
        """Service discovery endpoint - returns connection details."""
        return server_info


# Example usage for different server types

def example_sse_server():
    """Example: SSE-based MCP server (conport, serena, etc.)"""
    from fastapi import FastAPI
    
    app = FastAPI(title="ConPort MCP")
    
    add_info_endpoint(
        app,
        name="conport",
        version="1.0.0",
        protocol="sse",
        connection_url="http://localhost:3004/sse",
        description="Knowledge graph and context management",
        env_vars={
            "WORKSPACE_ID": "/path/to/workspace",
            "GEMINI_API_KEY": "${GEMINI_API_KEY:-}",
            "VOYAGEAI_API_KEY": "${VOYAGEAI_API_KEY:-}"
        },
        metadata={
            "role": "workflow",
            "priority": "high",
            "dependencies": ["postgres", "qdrant"]
        }
    )
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    return app


def example_http_server():
    """Example: HTTP server that also supports stdio via docker exec"""
    from fastapi import FastAPI
    
    app = FastAPI(title="GPT Researcher")
    
    # Advertise SSE as primary (HTTP/SSE superior to stdio)
    add_info_endpoint(
        app,
        name="gpt-researcher",
        version="1.0.0",
        protocol="sse",
        connection_url="http://localhost:3009/sse",
        description="Deep research with comprehensive analysis",
        env_vars={
            "OPENAI_API_KEY": "${OPENAI_API_KEY:-}",
            "TAVILY_API_KEY": "${TAVILY_API_KEY:-}",
            "EXA_API_KEY": "${EXA_API_KEY:-}"
        },
        metadata={
            "role": "research",
            "priority": "medium",
            "stdio_fallback": {
                "command": "docker",
                "args": ["exec", "-i", "mcp-gptr-mcp", "python", "/app/server.py"]
            }
        }
    )
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    return app


if __name__ == "__main__":
    # Demo: Run example server
    import uvicorn
    
    app = example_sse_server()
    uvicorn.run(app, host="0.0.0.0", port=3004)
