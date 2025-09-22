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
    BulkOperationRequest,
    BulkOperationResponse,
    DocumentVersion,
    AdvancedSearchFilters,
    SearchAnalytics,
)
from .service import DocRAGService
from .mcp_tools import get_mcp_tools, MCPToolHandler, DpmxRagQueryParams
from .bulk_operations import BulkOperationsHandler

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

# Global service instances
service: DocRAGService = None
mcp_handler: MCPToolHandler = None
bulk_handler: BulkOperationsHandler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan manager."""
    global service, mcp_handler, bulk_handler

    # Initialize service
    config = get_config()
    service = DocRAGService(config)

    try:
        await service.initialize()

        # Initialize handlers
        mcp_handler = MCPToolHandler(service)
        bulk_handler = BulkOperationsHandler(service)

        logger.info("DocRAG service started",
                   host=config.host, port=config.port,
                   features=["semantic_search", "mcp_tools", "bulk_operations", "versioning"])
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


# === ENHANCED API ENDPOINTS (ADR-0034) ===

@app.post("/mcp/dpmx_rag_query")
async def dpmx_rag_query_endpoint(params: DpmxRagQueryParams):
    """MCP-compatible unified RAG query endpoint."""
    if not mcp_handler:
        raise HTTPException(status_code=503, detail="MCP handler not initialized")

    return await mcp_handler.dpmx_rag_query(params)


@app.post("/bulk", response_model=BulkOperationResponse)
async def bulk_operations(request: BulkOperationRequest):
    """Bulk operations endpoint for upload/delete/update."""
    if not bulk_handler:
        raise HTTPException(status_code=503, detail="Bulk handler not initialized")

    return await bulk_handler.handle_bulk_operation(request)


@app.post("/search/advanced", response_model=SearchResponse)
async def advanced_search(query: SearchQuery, filters: AdvancedSearchFilters):
    """Advanced search with comprehensive filtering."""
    if not service:
        raise HTTPException(status_code=503, detail="Service not initialized")

    # Merge advanced filters into query filters
    enhanced_query = query.copy()
    enhanced_query.filters.update({
        k: v for k, v in filters.dict().items()
        if v is not None and v != [] and v != ""
    })

    return await service.search_documents(enhanced_query)


@app.get("/documents/{doc_id}/versions")
async def get_document_versions(doc_id: str):
    """Get version history for a document."""
    # Implementation would require database version tracking
    return {"message": "Document versioning not yet implemented", "doc_id": doc_id}


@app.post("/analytics/search")
async def log_search_analytics(analytics: SearchAnalytics):
    """Log search analytics for usage tracking."""
    # In a real implementation, this would store to analytics database
    logger.info("Search analytics",
               query=analytics.query,
               results_count=analytics.results_count,
               query_time_ms=analytics.query_time_ms)
    return {"status": "logged"}


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