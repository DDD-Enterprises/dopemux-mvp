#!/usr/bin/env python3
"""
GPT-Researcher MCP Server

An MCP server that wraps gpt-researcher functionality to provide
deep research capabilities to Claude Code and other MCP clients.

Based on the analysis in CHECKPOINT/gpt-researcher/, this server provides:
- quick_search: Fast web search with relevant snippets
- deep_research: Comprehensive research with tree exploration
- research_resource: Retrieve specific web resources
- write_report: Generate formatted research reports
- get_research_sources: Access research sources and citations
- get_research_context: Retrieve full research context
"""

import os

# Clear deprecated environment variables and set required ones
deprecated_vars = ['EMBEDDING_PROVIDER', 'EMBEDDING_MODEL', 'EMBEDDING_DIMENSION']
for var in deprecated_vars:
    if var in os.environ:
        del os.environ[var]

# Set required environment variables for GPT-Researcher
os.environ['EMBEDDING'] = 'openai:text-embedding-3-large'
os.environ['FAST_LLM'] = 'openai:gpt-4o-mini'
os.environ['SMART_LLM'] = 'openai:gpt-4o'
os.environ['RETRIEVER'] = 'tavily'

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

# MCP Server imports
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# GPT Researcher imports
from gpt_researcher import GPTResearcher
from gpt_researcher.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPTResearcherMCPServer:
    """MCP Server wrapper for GPT-Researcher functionality."""

    def __init__(self):
        self.server = Server("gpt-researcher")
        self.research_sessions = {}  # Store research contexts
        self.config = Config()

        # Register tools
        self._register_tools()

        # Register handlers
        self._register_handlers()

    def _register_tools(self):
        """Register all available research tools."""

        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available research tools."""
            return [
                Tool(
                    name="quick_search",
                    description="Fast web search with relevant snippets",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query"
                            },
                            "max_results": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 10
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="deep_research",
                    description="Comprehensive research with tree exploration (~5 minutes, ~$0.40)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Research topic"
                            },
                            "report_type": {
                                "type": "string",
                                "description": "Type of report",
                                "enum": ["research_report", "detailed", "basic"],
                                "default": "research_report"
                            },
                            "depth": {
                                "type": "integer",
                                "description": "Research depth (1-5)",
                                "default": 3
                            },
                            "breadth": {
                                "type": "integer",
                                "description": "Research breadth (1-10)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="research_resource",
                    description="Retrieve and analyze specific web resources",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "URL to retrieve and analyze"
                            },
                            "extract_content": {
                                "type": "boolean",
                                "description": "Extract and summarize content",
                                "default": True
                            }
                        },
                        "required": ["url"]
                    }
                ),
                Tool(
                    name="write_report",
                    description="Generate formatted reports from research context",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "context": {
                                "type": "string",
                                "description": "Research context to create report from"
                            },
                            "report_type": {
                                "type": "string",
                                "description": "Output format",
                                "enum": ["markdown", "html", "json"],
                                "default": "markdown"
                            },
                            "tone": {
                                "type": "string",
                                "description": "Report tone",
                                "enum": ["professional", "academic", "casual"],
                                "default": "professional"
                            }
                        },
                        "required": ["context"]
                    }
                ),
                Tool(
                    name="get_research_sources",
                    description="Access research sources and citations",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "research_id": {
                                "type": "string",
                                "description": "Research session ID"
                            }
                        },
                        "required": ["research_id"]
                    }
                ),
                Tool(
                    name="get_research_context",
                    description="Retrieve full research context and findings",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "research_id": {
                                "type": "string",
                                "description": "Research session ID"
                            },
                            "include_sources": {
                                "type": "boolean",
                                "description": "Include source citations",
                                "default": True
                            }
                        },
                        "required": ["research_id"]
                    }
                )
            ]

    def _register_handlers(self):
        """Register tool call handlers."""

        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""

            try:
                if name == "quick_search":
                    return await self._quick_search(arguments)
                elif name == "deep_research":
                    return await self._deep_research(arguments)
                elif name == "research_resource":
                    return await self._research_resource(arguments)
                elif name == "write_report":
                    return await self._write_report(arguments)
                elif name == "get_research_sources":
                    return await self._get_research_sources(arguments)
                elif name == "get_research_context":
                    return await self._get_research_context(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]

            except Exception as e:
                logger.error(f"Error executing tool {name}: {e}")
                return [TextContent(type="text", text=f"Error: {str(e)}")]

    async def _quick_search(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute quick search."""
        query = arguments["query"]
        max_results = arguments.get("max_results", 10)

        logger.info(f"Executing quick search: {query}")

        try:
            # Create researcher for quick search
            researcher = GPTResearcher(
                query=query,
                report_type="quick",
                config_path=None,
                verbose=True
            )

            # Conduct quick research
            context = await researcher.conduct_research()
            sources = researcher.get_sources()

            # Format results
            result = {
                "query": query,
                "summary": context[:500] + "..." if len(context) > 500 else context,
                "sources": sources[:max_results],
                "total_sources": len(sources)
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Quick search error: {e}")
            return [TextContent(type="text", text=f"Quick search failed: {str(e)}")]

    async def _deep_research(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Execute deep research with tree exploration."""
        query = arguments["query"]
        report_type = arguments.get("report_type", "research_report")
        depth = arguments.get("depth", 3)
        breadth = arguments.get("breadth", 5)

        logger.info(f"Executing deep research: {query} (depth={depth}, breadth={breadth})")

        try:
            # Create researcher for deep research
            researcher = GPTResearcher(
                query=query,
                report_type=report_type,
                config_path=None,
                verbose=True
            )

            # Set research parameters
            researcher.cfg.max_search_results_per_query = breadth
            researcher.cfg.max_subtopics = depth

            # Conduct research
            context = await researcher.conduct_research()
            report = await researcher.write_report()
            sources = researcher.get_sources()

            # Store session for later retrieval
            session_id = f"research_{len(self.research_sessions)}"
            self.research_sessions[session_id] = {
                "query": query,
                "context": context,
                "report": report,
                "sources": sources,
                "config": {
                    "depth": depth,
                    "breadth": breadth,
                    "report_type": report_type
                }
            }

            # Format response
            result = {
                "research_id": session_id,
                "query": query,
                "report": report,
                "source_count": len(sources),
                "context_length": len(context),
                "status": "completed"
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Deep research error: {e}")
            return [TextContent(type="text", text=f"Deep research failed: {str(e)}")]

    async def _research_resource(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Research specific resource URL."""
        url = arguments["url"]
        extract_content = arguments.get("extract_content", True)

        logger.info(f"Researching resource: {url}")

        try:
            # Use researcher to analyze specific URL
            query = f"Analyze and summarize content from: {url}"
            researcher = GPTResearcher(
                query=query,
                report_type="resource_report",
                config_path=None,
                verbose=True
            )

            # Conduct targeted research
            context = await researcher.conduct_research()

            if extract_content:
                report = await researcher.write_report()
                result = {
                    "url": url,
                    "summary": report,
                    "context": context,
                    "status": "analyzed"
                }
            else:
                result = {
                    "url": url,
                    "context": context,
                    "status": "retrieved"
                }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Resource research error: {e}")
            return [TextContent(type="text", text=f"Resource research failed: {str(e)}")]

    async def _write_report(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Generate formatted report from context."""
        context = arguments["context"]
        report_type = arguments.get("report_type", "markdown")
        tone = arguments.get("tone", "professional")

        logger.info(f"Writing {report_type} report with {tone} tone")

        try:
            # Create researcher to generate report
            researcher = GPTResearcher(
                query="Generate report from provided context",
                report_type="custom_report",
                config_path=None,
                verbose=True
            )

            # Override context and generate report
            researcher.context = context
            report = await researcher.write_report()

            result = {
                "report": report,
                "format": report_type,
                "tone": tone,
                "word_count": len(report.split()),
                "status": "generated"
            }

            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        except Exception as e:
            logger.error(f"Report writing error: {e}")
            return [TextContent(type="text", text=f"Report writing failed: {str(e)}")]

    async def _get_research_sources(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get sources from research session."""
        research_id = arguments["research_id"]

        if research_id not in self.research_sessions:
            return [TextContent(type="text", text=f"Research session {research_id} not found")]

        session = self.research_sessions[research_id]
        result = {
            "research_id": research_id,
            "query": session["query"],
            "sources": session["sources"],
            "source_count": len(session["sources"])
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def _get_research_context(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Get full research context."""
        research_id = arguments["research_id"]
        include_sources = arguments.get("include_sources", True)

        if research_id not in self.research_sessions:
            return [TextContent(type="text", text=f"Research session {research_id} not found")]

        session = self.research_sessions[research_id]
        result = {
            "research_id": research_id,
            "query": session["query"],
            "context": session["context"],
            "report": session["report"],
            "config": session["config"]
        }

        if include_sources:
            result["sources"] = session["sources"]

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    async def run(self):
        """Run the MCP server."""
        logger.info("Starting GPT-Researcher MCP Server")

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="gpt-researcher",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )

def main():
    """Main entry point."""
    server = GPTResearcherMCPServer()
    asyncio.run(server.run())

if __name__ == "__main__":
    main()