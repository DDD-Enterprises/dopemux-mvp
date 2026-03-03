#!/usr/bin/env python3
"""
FastMCP Server for Dope-Context
Exposes semantic code search and documentation search tools via MCP SSE
"""

import os
import logging
from typing import Dict, Any
from fastmcp import FastMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s][%(levelname)s] - %(message)s',
)
logger = logging.getLogger("dope-context-mcp")

# Initialize FastMCP server
mcp = FastMCP(
    name="Dope-Context"
)

@mcp.tool()
async def search_code(query: str, top_k: int = 10, profile: str = "hybrid") -> Dict[str, Any]:
    """
    Search indexed code with hybrid dense + sparse search.
    
    Args:
        query: Search query
        top_k: Number of results to return
        profile: Search profile (hybrid, dense, sparse)
    """
    logger.info(f"Searching code for: {query} (top_k={top_k})")
    
    # Mock results for now
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

@mcp.tool()
async def docs_search(query: str, top_k: int = 5) -> Dict[str, Any]:
    """
    Search indexed documentation.
    
    Args:
        query: Search query
        top_k: Number of results to return
    """
    logger.info(f"Searching docs for: {query} (top_k={top_k})")
    
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

@mcp.tool()
async def get_index_status() -> Dict[str, Any]:
    """Get status of the code index."""
    return {
        "status": "mock_index_active",
        "total_files": 42,
        "total_vectors": 1284,
        "languages": ["python", "javascript", "typescript"],
        "last_indexed": "2025-11-10T18:00:00Z"
    }

if __name__ == "__main__":
    # Get port from environment or default to 3010
    port = int(os.getenv("MCP_SERVER_PORT", "3010"))
    transport = os.getenv("MCP_TRANSPORT", "sse")
    
    logger.info(f"🚀 Starting Dope-Context MCP Server on port {port} (transport={transport})")
    
    # Run using FastMCP's built-in support
    if transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="sse", host="0.0.0.0", port=port)
