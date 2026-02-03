#!/usr/bin/env python3
"""
Simple MCP Server for Dope-Context - Basic implementation without fastmcp dependency
"""

import asyncio

import logging

logger = logging.getLogger(__name__)

import json
from typing import Any, Dict, List

class SimpleMCPServer:
    def __init__(self):
        self.port = 3010
        self.tools = [
            {
                "name": "search_code",
                "description": "Search indexed code with hybrid dense + sparse search",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "top_k": {"type": "integer", "description": "Number of results", "default": 10},
                        "profile": {"type": "string", "description": "Search profile", "default": "hybrid"}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "docs_search",
                "description": "Search indexed documentation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "top_k": {"type": "integer", "description": "Number of results", "default": 5}
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "get_index_status",
                "description": "Get status of the code index",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        self.running = False

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP requests."""
        if request.get("type") == "call_tool":
            tool_name = request.get("name")
            args = request.get("arguments", {})

            if tool_name == "search_code":
                return await self.search_code(args)
            elif tool_name == "docs_search":
                return await self.docs_search(args)
            elif tool_name == "get_index_status":
                return await self.get_index_status()
            else:
                return {"error": f"Unknown tool: {tool_name}"}

        elif request.get("type") == "list_tools":
            return {"tools": self.tools}

        else:
            return {"error": "Unknown request type"}

    async def search_code(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock search_code implementation."""
        query = args.get("query", "")
        top_k = args.get("top_k", 10)

        # Mock results
        results = []
        for i in range(min(top_k, 3)):
            results.append({
                "file_path": f"/src/mock_file_{i}.py",
                "code": f"# Mock code result for '{query}'",
                "complexity": 0.5,
                "score": 0.8 - i * 0.1
            })

        return {
            "status": "success",
            "results": results,
            "query": query,
            "top_k": len(results)
        }

    async def docs_search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock docs_search implementation."""
        query = args.get("query", "")
        top_k = args.get("top_k", 5)

        # Mock results
        results = []
        for i in range(min(top_k, 2)):
            results.append({
                "source_path": f"/docs/mock_doc_{i}.md",
                "text": f"Mock documentation for '{query}'",
                "score": 0.9 - i * 0.1
            })

        return {
            "status": "success",
            "results": results,
            "query": query,
            "top_k": len(results)
        }

    async def get_index_status(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Mock get_index_status implementation."""
        return {
            "status": "mock_index_active",
            "total_files": 42,
            "total_vectors": 1284,
            "languages": ["python", "javascript", "typescript"],
            "last_indexed": "2025-11-10T18:00:00Z"
        }

    def run(self):
        """Run the simple MCP server."""
        import uvicorn
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware

        app = FastAPI(title="Simple Dope-Context MCP Server")

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.post("/mcp")
        async def mcp_endpoint(request: Dict[str, Any]):
            return await self.handle_request(request)

        @app.get("/health")
        async def health():
            return {"status": "healthy", "service": "dope-context-mcp-simple"}

        @app.get("/info")
        async def info():
            """Service discovery endpoint - auto-config support (ADR-208)"""
            return {
                "name": "dope-context",
                "version": "1.0.0",
                "mcp": {
                    "protocol": "sse",
                    "connection": {
                        "type": "sse",
                        "url": f"http://localhost:{self.port}/mcp"
                    },
                    "env": {
                        "VOYAGE_API_KEY": "${VOYAGEAI_API_KEY:-}",
                        "OPENAI_API_KEY": "${OPENAI_API_KEY:-}",
                        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY:-}"
                    }
                },
                "health": "/health",
                "description": "Semantic code search and autonomous indexing",
                "metadata": {
                    "role": "workflow",
                    "priority": "high",
                    "adhd_integration": True,
                    "autonomous_indexing": True,
                    "simple_server": True
                }
            }

        self.running = True
        uvicorn.run(app, host="0.0.0.0", port=self.port)
        self.running = False

if __name__ == "__main__":
    server = SimpleMCPServer()
    logger.info(f"Starting Simple MCP Server on port {server.port}")
    server.run()  # Direct call, not async