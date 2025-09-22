"""
MCP tools for DocRAG service - implements dpmx_rag_query tool
Following ADR-0034 specification for PluggedIn UI parity
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import json
import time
from datetime import datetime

from .models import SearchQuery, SearchResponse, DocumentChunk
from .service import DocRAGService


class AiSearchResult(BaseModel):
    """AI search result format matching PluggedIn specification"""
    id: str
    name: str
    content: str
    relevance_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AiSearchResponse(BaseModel):
    """AI search response format matching PluggedIn specification"""
    answer: str
    documents: List[AiSearchResult]
    sources: List[str]
    confidence: float
    query_time_ms: int
    total_results: int


class DpmxRagQueryParams(BaseModel):
    """Parameters for dpmx_rag_query MCP tool"""
    query: str = Field(description="Search query text")
    max_results: int = Field(default=8, description="Maximum number of results to return")
    threshold: float = Field(default=0.1, description="Minimum relevance threshold")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Search filters (source, date, model, tags)")
    enable_hybrid: bool = Field(default=True, description="Enable hybrid search (dense + sparse)")
    enable_reranking: bool = Field(default=True, description="Enable Voyage reranking")


class MCPToolHandler:
    """Handler for MCP tools in DocRAG service"""

    def __init__(self, docrag_service: DocRAGService):
        self.service = docrag_service

    async def dpmx_rag_query(self, params: DpmxRagQueryParams) -> AiSearchResponse:
        """
        Unified RAG query tool implementing PluggedIn-compatible interface

        Retrieval path: Milvus ANN → (optional Hybrid) → Voyage rerank-2.5 → response formatting
        """
        start_time = time.time()

        # Create internal search query
        search_query = SearchQuery(
            query=params.query,
            limit=min(params.max_results * 4, 32),  # Get more for reranking
            threshold=params.threshold,
            filters=params.filters or {},
            enable_hybrid=params.enable_hybrid,
            enable_reranking=params.enable_reranking
        )

        # Execute search through DocRAG service
        search_response = await self.service.search_documents(search_query)

        # Transform to PluggedIn-compatible format
        ai_results = []
        sources = set()

        for chunk in search_response.results[:params.max_results]:
            # Extract source information
            source_path = chunk.metadata.source_path or "unknown"
            sources.add(source_path)

            # Create AI search result
            ai_result = AiSearchResult(
                id=chunk.id,
                name=chunk.metadata.title or source_path.split('/')[-1],
                content=chunk.text,
                relevance_score=chunk.score,
                metadata={
                    "source_path": source_path,
                    "chunk_index": chunk.metadata.chunk_index,
                    "page_number": chunk.metadata.page_number,
                    "section": chunk.metadata.section,
                    "tags": chunk.metadata.tags,
                    "created_at": chunk.metadata.created_at.isoformat() if chunk.metadata.created_at else None,
                    "updated_at": chunk.metadata.updated_at.isoformat() if chunk.metadata.updated_at else None
                }
            )
            ai_results.append(ai_result)

        # Generate answer from top results
        answer = await self._generate_answer(params.query, ai_results[:3])

        # Calculate confidence based on top result scores
        confidence = self._calculate_confidence(ai_results)

        query_time_ms = int((time.time() - start_time) * 1000)

        return AiSearchResponse(
            answer=answer,
            documents=ai_results,
            sources=list(sources),
            confidence=confidence,
            query_time_ms=query_time_ms,
            total_results=search_response.total_results
        )

    async def _generate_answer(self, query: str, top_results: List[AiSearchResult]) -> str:
        """Generate a concise answer from top search results"""
        if not top_results:
            return f"No relevant documents found for query: '{query}'"

        # Simple answer generation - could be enhanced with LLM integration
        context_snippets = []
        for result in top_results:
            # Get first 200 chars of content
            snippet = result.content[:200]
            if len(result.content) > 200:
                snippet += "..."
            context_snippets.append(f"From {result.name}: {snippet}")

        answer = f"Based on {len(top_results)} relevant documents:\n\n"
        answer += "\n\n".join(context_snippets)

        return answer

    def _calculate_confidence(self, results: List[AiSearchResult]) -> float:
        """Calculate confidence score based on result quality"""
        if not results:
            return 0.0

        # Use top result score as base confidence
        top_score = results[0].relevance_score

        # Adjust based on number of quality results
        quality_results = len([r for r in results if r.relevance_score > 0.3])
        confidence_boost = min(quality_results * 0.1, 0.3)

        return min(top_score + confidence_boost, 1.0)


# MCP tool registration function
def get_mcp_tools(docrag_service: DocRAGService) -> Dict[str, Any]:
    """Get MCP tool definitions for DocRAG service"""
    handler = MCPToolHandler(docrag_service)

    return {
        "dpmx_rag_query": {
            "description": "Unified semantic search across documents with PluggedIn-compatible interface",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query text"
                    },
                    "max_results": {
                        "type": "integer",
                        "default": 8,
                        "description": "Maximum number of results to return"
                    },
                    "threshold": {
                        "type": "number",
                        "default": 0.1,
                        "description": "Minimum relevance threshold"
                    },
                    "filters": {
                        "type": "object",
                        "description": "Search filters (source, date, model, tags)",
                        "properties": {
                            "source": {"type": "string"},
                            "date_from": {"type": "string", "format": "date"},
                            "date_to": {"type": "string", "format": "date"},
                            "model": {"type": "string"},
                            "tags": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "enable_hybrid": {
                        "type": "boolean",
                        "default": True,
                        "description": "Enable hybrid search (dense + sparse)"
                    },
                    "enable_reranking": {
                        "type": "boolean",
                        "default": True,
                        "description": "Enable Voyage reranking"
                    }
                },
                "required": ["query"]
            },
            "handler": handler.dpmx_rag_query
        }
    }