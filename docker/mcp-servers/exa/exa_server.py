#!/usr/bin/env python3

"""
Exa MCP Server - Official Implementation
Uses the official exa-py package for web research capabilities.
Based on Exa API documentation from /exa-labs/exa-py
"""

import json
import os
import sys
import traceback
from typing import List, Optional, Dict, Any
import asyncio
from contextlib import asynccontextmanager

from fastmcp import FastMCP
from exa_py import Exa
import uvicorn

# Try to import validation functions, but don't fail if they're not available
try:
    from exa_py.api import validate_search_options, validate_find_similar_options
    HAS_VALIDATION = True
except ImportError:
    HAS_VALIDATION = False

# Initialize Exa client
exa_api_key = os.getenv("EXA_API_KEY")
if not exa_api_key:
    raise ValueError("EXA_API_KEY environment variable is required")

exa = Exa(exa_api_key)

# FastMCP server setup
@asynccontextmanager
async def lifespan(app):
    """Server lifespan management"""
    print("🔍 Starting Exa MCP Server...")
    print(f"🔑 API Key configured: {bool(exa_api_key)}")
    yield
    print("🔍 Shutting down Exa MCP Server...")

mcp = FastMCP("Exa Research", lifespan=lifespan)

# Add health endpoint for Docker health checks
@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for Docker container"""
    from starlette.responses import JSONResponse
    try:
        # Quick test to verify Exa client is working
        return JSONResponse({
            "status": "healthy",
            "service": "Exa MCP Server",
            "exa_api_configured": bool(exa_api_key),
            "version": "1.0.0"
        })
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e),
            "service": "Exa MCP Server"
        })

@mcp.tool()
def search_web(
    query: str,
    num_results: int = 10,
    use_autoprompt: bool = True,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    start_published_date: Optional[str] = None,
    end_published_date: Optional[str] = None,
    type: str = "neural",
    category: Optional[str] = None
) -> str:
    """
    Search the web using Exa's AI-powered search engine.

    Args:
        query: The search query string
        num_results: Number of search results to return (default: 10)
        use_autoprompt: Whether to use Exa's autoprompt feature (default: True)
        include_domains: List of domains to include in search
        exclude_domains: List of domains to exclude from search
        start_published_date: Results published after this date (YYYY-MM-DD format)
        end_published_date: Results published before this date (YYYY-MM-DD format)
        type: Search type - 'neural' or 'keyword' (default: 'neural')
        category: Data category to focus on (currently only 'company' supported)

    Returns:
        JSON string containing search results with URLs, titles, IDs, and published dates
    """
    try:
        # Build search parameters
        search_params = {
            "query": query,
            "num_results": num_results,
            "use_autoprompt": use_autoprompt,
            "type": type
        }

        # Add optional parameters if provided
        if include_domains:
            search_params["include_domains"] = include_domains
        if exclude_domains:
            search_params["exclude_domains"] = exclude_domains
        if start_published_date:
            search_params["start_published_date"] = start_published_date
        if end_published_date:
            search_params["end_published_date"] = end_published_date
        if category:
            search_params["category"] = category

        # Validate search options using Exa's built-in validation (if available)
        if HAS_VALIDATION:
            try:
                validate_search_options(search_params)
            except ValueError as ve:
                return json.dumps({"error": f"Invalid search parameters: {str(ve)}"}, indent=2)

        # Perform search
        response = exa.search(**search_params)

        # Format results
        results = []
        for result in response.results:
            result_data = {
                "id": result.id,
                "url": result.url,
                "title": result.title,
                "published_date": result.published_date,
                "author": getattr(result, 'author', None),
                "score": getattr(result, 'score', None)
            }
            results.append(result_data)

        return json.dumps({
            "results": results,
            "autoprompt_string": getattr(response, 'autoprompt_string', None),
            "query": query,
            "num_results": len(results)
        }, indent=2, ensure_ascii=False)

    except Exception as e:
        error_msg = f"Exa search failed: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return json.dumps({"error": error_msg}, indent=2)

@mcp.tool()
def get_contents(
    urls: List[str],
    text_length_limit: Optional[int] = None
) -> str:
    """
    Get detailed content from specific URLs using Exa.

    Args:
        urls: List of URLs to fetch content from
        text_length_limit: Maximum length of text content per result

    Returns:
        JSON string containing detailed content for each URL
    """
    try:
        # First, search to get IDs for the URLs
        ids = []
        for url in urls:
            # For direct URL content retrieval, we need to search first to get IDs
            # This is a limitation of the Exa API - it primarily works with IDs
            try:
                search_response = exa.search(f"site:{url}", num_results=1)
                if search_response.results:
                    ids.append(search_response.results[0].id)
            except:
                continue

        if not ids:
            return json.dumps({"error": "No valid IDs found for the provided URLs"}, indent=2)

        # Get contents using IDs
        contents_response = exa.get_contents(ids)

        # Format results
        contents = []
        for content in contents_response.contents:
            content_data = {
                "id": content.id,
                "url": content.url,
                "title": content.title,
                "extract": content.extract[:text_length_limit] if text_length_limit else content.extract,
                "author": getattr(content, 'author', None)
            }
            contents.append(content_data)

        return json.dumps({
            "contents": contents,
            "num_contents": len(contents)
        }, indent=2, ensure_ascii=False)

    except Exception as e:
        error_msg = f"Exa get contents failed: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return json.dumps({"error": error_msg}, indent=2)

@mcp.tool()
def search_and_contents(
    query: str,
    num_results: int = 5,
    use_autoprompt: bool = True,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    start_published_date: Optional[str] = None,
    end_published_date: Optional[str] = None,
    type: str = "neural",
    text_length_limit: Optional[int] = 1000
) -> str:
    """
    Search the web and get detailed content in one operation.

    Args:
        query: The search query string
        num_results: Number of search results to return (default: 5)
        use_autoprompt: Whether to use Exa's autoprompt feature (default: True)
        include_domains: List of domains to include in search
        exclude_domains: List of domains to exclude from search
        start_published_date: Results published after this date (YYYY-MM-DD format)
        end_published_date: Results published before this date (YYYY-MM-DD format)
        type: Search type - 'neural' or 'keyword' (default: 'neural')
        text_length_limit: Maximum length of text content per result (default: 1000)

    Returns:
        JSON string containing search results with full content
    """
    try:
        # Build search parameters
        search_params = {
            "query": query,
            "num_results": num_results,
            "use_autoprompt": use_autoprompt,
            "type": type
        }

        # Add optional parameters if provided
        if include_domains:
            search_params["include_domains"] = include_domains
        if exclude_domains:
            search_params["exclude_domains"] = exclude_domains
        if start_published_date:
            search_params["start_published_date"] = start_published_date
        if end_published_date:
            search_params["end_published_date"] = end_published_date

        # Perform search and get contents
        response = exa.search_and_contents(**search_params)

        # Format results with content
        results = []
        for result in response.results:
            result_data = {
                "id": result.id,
                "url": result.url,
                "title": result.title,
                "published_date": result.published_date,
                "author": getattr(result, 'author', None),
                "score": getattr(result, 'score', None),
                "text": result.text[:text_length_limit] if text_length_limit and result.text else result.text
            }
            results.append(result_data)

        return json.dumps({
            "results": results,
            "autoprompt_string": getattr(response, 'autoprompt_string', None),
            "query": query,
            "num_results": len(results)
        }, indent=2, ensure_ascii=False)

    except Exception as e:
        error_msg = f"Exa search and contents failed: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return json.dumps({"error": error_msg}, indent=2)

@mcp.tool()
def find_similar(
    url: str,
    num_results: int = 5,
    include_domains: Optional[List[str]] = None,
    exclude_domains: Optional[List[str]] = None,
    exclude_source_domain: bool = True,
    category: Optional[str] = None
) -> str:
    """
    Find websites similar to a given URL using Exa.

    Args:
        url: The URL to find similar sites for
        num_results: Number of similar results to return (default: 5)
        include_domains: List of domains to include in results
        exclude_domains: List of domains to exclude from results
        exclude_source_domain: Whether to exclude the source domain (default: True)
        category: Data category to focus on (currently only 'company' supported)

    Returns:
        JSON string containing similar websites with URLs, titles, and metadata
    """
    try:
        # Build parameters
        params = {
            "url": url,
            "num_results": num_results,
            "exclude_source_domain": exclude_source_domain
        }

        # Add optional parameters if provided
        if include_domains:
            params["include_domains"] = include_domains
        if exclude_domains:
            params["exclude_domains"] = exclude_domains
        if category:
            params["category"] = category

        # Find similar sites
        response = exa.find_similar(**params)

        # Format results
        results = []
        for result in response.results:
            result_data = {
                "id": result.id,
                "url": result.url,
                "title": result.title,
                "published_date": result.published_date,
                "author": getattr(result, 'author', None),
                "score": getattr(result, 'score', None)
            }
            results.append(result_data)

        return json.dumps({
            "results": results,
            "source_url": url,
            "num_results": len(results)
        }, indent=2, ensure_ascii=False)

    except Exception as e:
        error_msg = f"Exa find similar failed: {str(e)}"
        print(f"❌ {error_msg}")
        traceback.print_exc()
        return json.dumps({"error": error_msg}, indent=2)

if __name__ == "__main__":
    # Check if we should run in stdio mode for mcp-proxy
    run_mode = os.getenv("MCP_RUN_MODE", "stdio")

    if run_mode == "stdio":
        print("🔍 Starting Exa MCP Server in stdio mode", file=sys.stderr)
        import asyncio
        asyncio.run(mcp.run())
    else:
        # Legacy HTTP mode
        port = int(os.getenv("MCP_SERVER_PORT", 3008))
        print(f"🔍 Starting Exa MCP Server on port {port}")
        import asyncio
        asyncio.run(mcp.run_http_async(
            host="0.0.0.0",
            port=port,
            show_banner=True,
            transport="http"
        ))