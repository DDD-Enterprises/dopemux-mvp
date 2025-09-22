"""
FastAPI application and MCP server for DocRAG service.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from typing import List

import structlog
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
# MCP integration - using a simpler approach for now
# from mcp.server.fastmcp import FastMCP
# from mcp.types import Tool

from .config import get_config
from .models import (
    HealthStatus,
    IngestionRequest,
    IngestionResponse,
    SearchQuery,
    SearchResponse,
)
from .service import DocRAGService

# Configure logging
logging.basicConfig(level=logging.INFO)
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Global service instance
service: DocRAGService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager."""
    global service

    # Initialize service
    config = get_config()
    service = DocRAGService(config)

    try:
        await service.initialize()
        logger.info("DocRAG service started", host=config.host, port=config.port)
        yield
    finally:
        if service:
            await service.shutdown()
        logger.info("DocRAG service stopped")


# Create FastAPI app
app = FastAPI(
    title="DocRAG Service",
    description="Document ingestion and semantic search with Milvus and Voyage AI",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthStatus)
async def health_check():
    """Get service health status."""
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    return await service.get_health_status()


@app.post("/ingest", response_model=IngestionResponse)
async def ingest_document(request: IngestionRequest):
    """Ingest a document into the search index."""
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    return await service.ingest_document(request)


@app.post("/search", response_model=SearchResponse)
async def search_documents(query: SearchQuery):
    """Search for documents."""
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    return await service.search_documents(query)


# Future: MCP Server Integration will be added here
# For now, we provide REST API endpoints


def main():
    """Main entry point for the DocRAG service."""
    config = get_config()

    # Run server
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        workers=config.workers,
        log_level=config.log_level.lower(),
    )


if __name__ == "__main__":
    main()