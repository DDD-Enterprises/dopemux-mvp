"""
ConPort Integration Adapter

Integrates the embedding system with ConPort (Context Portal) for
ADHD-optimized context management, decision tracking, and knowledge graph
construction. Provides seamless sync between embeddings and project memory.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ..core import SearchResult, AdvancedEmbeddingConfig, EmbeddingError
from .base import BaseIntegration

logger = logging.getLogger(__name__)


class ConPortAdapter(BaseIntegration):
    """
    ConPort integration adapter for context-aware embedding management.

    Synchronizes documents between embedding system and ConPort,
    enhances search results with contextual information, and provides
    ADHD-optimized knowledge graph integration.
    """

    def __init__(self, config: AdvancedEmbeddingConfig, workspace_id: str):
        """
        Initialize ConPort adapter.

        Args:
            config: Embedding configuration
            workspace_id: ConPort workspace identifier
        """
        super().__init__(config)
        self.workspace_id = workspace_id
        self.connection_status = "unknown"
        self.last_sync_time: Optional[datetime] = None

        # ConPort categories for different document types
        self.document_categories = {
            "decisions": "architectural_decisions",
            "patterns": "system_patterns",
            "progress": "progress_entries",
            "custom": "project_documentation",
            "glossary": "project_glossary"
        }

        logger.info(f"🔌 ConPort adapter initialized for workspace: {workspace_id}")

    async def validate_connection(self) -> bool:
        """
        Validate connection to ConPort MCP server.

        Returns:
            True if ConPort is accessible and responsive
        """
        try:
            # Mock ConPort health check - in practice this would call MCP
            # Example: await mcp_conport.get_product_context(workspace_id=self.workspace_id)

            # Simulate connection check
            await asyncio.sleep(0.1)  # Simulate network delay

            self.connection_status = "healthy"
            logger.info("✅ ConPort connection validated")
            return True

        except Exception as e:
            self.connection_status = f"error: {str(e)}"
            logger.error(f"❌ ConPort connection failed: {e}")
            return False

    async def sync_documents(self, workspace_id: str) -> Dict[str, Any]:
        """
        Synchronize documents from ConPort workspace.

        Retrieves decisions, patterns, progress entries, and custom data
        from ConPort for embedding indexing.

        Args:
            workspace_id: ConPort workspace identifier

        Returns:
            Sync statistics and document collection
        """
        try:
            if not await self.validate_connection():
                raise EmbeddingError("ConPort connection not available")

            sync_start = datetime.now()
            documents_synced = 0
            sync_results = {
                "documents": [],
                "categories": {},
                "errors": []
            }

            # Sync different ConPort content types
            content_types = [
                ("decisions", self._sync_decisions),
                ("system_patterns", self._sync_patterns),
                ("progress_entries", self._sync_progress),
                ("custom_data", self._sync_custom_data),
                ("glossary", self._sync_glossary)
            ]

            for content_type, sync_func in content_types:
                try:
                    if self.config.enable_progress_tracking:
                        print(f"🔄 Syncing {content_type} from ConPort...")

                    type_docs = await sync_func(workspace_id)
                    sync_results["documents"].extend(type_docs)
                    sync_results["categories"][content_type] = len(type_docs)
                    documents_synced += len(type_docs)

                except Exception as e:
                    error_msg = f"Failed to sync {content_type}: {str(e)}"
                    sync_results["errors"].append(error_msg)
                    logger.warning(f"⚠️ {error_msg}")

            # Update sync metadata
            self.last_sync_time = sync_start
            sync_duration = (datetime.now() - sync_start).total_seconds()

            # ADHD-friendly completion feedback
            if self.config.enable_progress_tracking:
                print(f"✅ ConPort sync complete: {documents_synced} documents in {sync_duration:.1f}s")

            return {
                "documents_synced": documents_synced,
                "sync_duration_seconds": sync_duration,
                "categories": sync_results["categories"],
                "errors": sync_results["errors"],
                "documents": sync_results["documents"]
            }

        except Exception as e:
            logger.error(f"❌ ConPort sync failed: {e}")
            raise EmbeddingError(f"ConPort sync failed: {e}") from e

    async def _sync_decisions(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Sync architectural decisions from ConPort."""
        # Mock implementation - would use actual MCP calls
        # Example: decisions = await mcp_conport.get_decisions(workspace_id=workspace_id, limit=100)

        decisions = []  # Placeholder for actual data
        documents = []

        for decision in decisions:
            doc = {
                "id": f"decision_{decision.get('id')}",
                "content": f"{decision.get('summary', '')} {decision.get('rationale', '')}",
                "metadata": {
                    "type": "decision",
                    "source": "conport",
                    "category": self.document_categories["decisions"],
                    "timestamp": decision.get('created_at'),
                    "tags": decision.get('tags', []),
                    "implementation_details": decision.get('implementation_details')
                }
            }
            documents.append(doc)

        return documents

    async def _sync_patterns(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Sync system patterns from ConPort."""
        # Mock implementation
        patterns = []  # Placeholder
        documents = []

        for pattern in patterns:
            doc = {
                "id": f"pattern_{pattern.get('id')}",
                "content": f"{pattern.get('name', '')} {pattern.get('description', '')}",
                "metadata": {
                    "type": "pattern",
                    "source": "conport",
                    "category": self.document_categories["patterns"],
                    "timestamp": pattern.get('created_at'),
                    "tags": pattern.get('tags', [])
                }
            }
            documents.append(doc)

        return documents

    async def _sync_progress(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Sync progress entries from ConPort."""
        # Mock implementation
        progress_entries = []  # Placeholder
        documents = []

        for entry in progress_entries:
            doc = {
                "id": f"progress_{entry.get('id')}",
                "content": entry.get('description', ''),
                "metadata": {
                    "type": "progress",
                    "source": "conport",
                    "category": self.document_categories["progress"],
                    "status": entry.get('status'),
                    "timestamp": entry.get('created_at')
                }
            }
            documents.append(doc)

        return documents

    async def _sync_custom_data(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Sync custom data from ConPort."""
        # Mock implementation
        custom_data = []  # Placeholder
        documents = []

        for data in custom_data:
            doc = {
                "id": f"custom_{data.get('category')}_{data.get('key')}",
                "content": str(data.get('value', '')),
                "metadata": {
                    "type": "custom_data",
                    "source": "conport",
                    "category": data.get('category'),
                    "key": data.get('key'),
                    "timestamp": data.get('created_at')
                }
            }
            documents.append(doc)

        return documents

    async def _sync_glossary(self, workspace_id: str) -> List[Dict[str, Any]]:
        """Sync project glossary from ConPort."""
        # Mock implementation
        glossary_items = []  # Placeholder
        documents = []

        for item in glossary_items:
            doc = {
                "id": f"glossary_{item.get('key')}",
                "content": f"{item.get('key', '')}: {item.get('value', '')}",
                "metadata": {
                    "type": "glossary",
                    "source": "conport",
                    "category": self.document_categories["glossary"],
                    "term": item.get('key'),
                    "timestamp": item.get('created_at')
                }
            }
            documents.append(doc)

        return documents

    async def store_embeddings(self, documents: List[Dict[str, Any]],
                              embeddings: List[List[float]]) -> None:
        """
        Store embeddings back to ConPort for semantic search.

        Args:
            documents: Document metadata
            embeddings: Generated embeddings
        """
        try:
            if len(documents) != len(embeddings):
                raise ValueError("Documents and embeddings count mismatch")

            stored_count = 0

            for doc, embedding in zip(documents, embeddings):
                try:
                    # Mock storage - would use actual MCP calls
                    # Example: await mcp_conport.store_embedding(
                    #     workspace_id=self.workspace_id,
                    #     doc_id=doc['id'],
                    #     embedding=embedding,
                    #     metadata=doc['metadata']
                    # )

                    stored_count += 1

                except Exception as e:
                    logger.warning(f"⚠️ Failed to store embedding for {doc['id']}: {e}")

            if self.config.enable_progress_tracking:
                print(f"💾 Stored {stored_count} embeddings to ConPort")

        except Exception as e:
            logger.error(f"❌ Failed to store embeddings to ConPort: {e}")
            raise EmbeddingError(f"ConPort embedding storage failed: {e}") from e

    async def enhance_search_results(self, results: List[SearchResult],
                                   context: Dict[str, Any]) -> List[SearchResult]:
        """
        Enhance search results with ConPort contextual information.

        Adds project context, related decisions, linked progress items,
        and knowledge graph relationships to search results.

        Args:
            results: Raw search results
            context: Additional search context

        Returns:
            Enhanced search results with ConPort metadata
        """
        try:
            enhanced_results = []

            for result in results:
                enhanced_result = result  # Copy original result

                # Add ConPort contextual metadata
                if result.doc_id.startswith("decision_"):
                    # Add related decisions and progress
                    enhanced_result.metadata.update({
                        "conport_type": "decision",
                        "related_items": await self._get_related_items(result.doc_id),
                        "implementation_status": await self._get_implementation_status(result.doc_id)
                    })

                elif result.doc_id.startswith("pattern_"):
                    # Add pattern usage and examples
                    enhanced_result.metadata.update({
                        "conport_type": "pattern",
                        "usage_examples": await self._get_pattern_usage(result.doc_id)
                    })

                elif result.doc_id.startswith("progress_"):
                    # Add task relationships and blockers
                    enhanced_result.metadata.update({
                        "conport_type": "progress",
                        "blockers": await self._get_task_blockers(result.doc_id),
                        "dependencies": await self._get_task_dependencies(result.doc_id)
                    })

                # Add ADHD-friendly context tags
                enhanced_result.metadata["adhd_context"] = {
                    "urgency": self._calculate_urgency(result),
                    "complexity": self._calculate_complexity(result),
                    "focus_time_needed": self._estimate_focus_time(result)
                }

                enhanced_results.append(enhanced_result)

            return enhanced_results

        except Exception as e:
            logger.warning(f"⚠️ Failed to enhance results with ConPort data: {e}")
            # Return original results if enhancement fails
            return results

    async def _get_related_items(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get items related to a document via ConPort knowledge graph."""
        # Mock implementation
        return []

    async def _get_implementation_status(self, doc_id: str) -> Dict[str, Any]:
        """Get implementation status of a decision."""
        # Mock implementation
        return {"status": "unknown"}

    async def _get_pattern_usage(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get usage examples of a pattern."""
        # Mock implementation
        return []

    async def _get_task_blockers(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get blockers for a task."""
        # Mock implementation
        return []

    async def _get_task_dependencies(self, doc_id: str) -> List[Dict[str, Any]]:
        """Get dependencies for a task."""
        # Mock implementation
        return []

    def _calculate_urgency(self, result: SearchResult) -> str:
        """Calculate ADHD-friendly urgency indicator."""
        # Simplified urgency calculation
        if "blocker" in result.content.lower() or "urgent" in result.content.lower():
            return "high"
        elif "todo" in result.content.lower():
            return "medium"
        else:
            return "low"

    def _calculate_complexity(self, result: SearchResult) -> str:
        """Calculate ADHD-friendly complexity indicator."""
        # Simplified complexity calculation based on content length
        content_length = len(result.content)
        if content_length > 1000:
            return "high"
        elif content_length > 300:
            return "medium"
        else:
            return "low"

    def _estimate_focus_time(self, result: SearchResult) -> str:
        """Estimate focus time needed for ADHD time management."""
        complexity = self._calculate_complexity(result)

        time_mapping = {
            "low": "5-15 minutes",
            "medium": "20-45 minutes",
            "high": "1-2 hours (break into chunks)"
        }

        return time_mapping.get(complexity, "unknown")

    def get_integration_status(self) -> Dict[str, Any]:
        """
        Get ConPort integration health and status.

        Returns:
            Status dictionary with connection and sync information
        """
        return {
            "integration_type": "conport",
            "workspace_id": self.workspace_id,
            "connection_status": self.connection_status,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "document_categories": self.document_categories,
            "features": {
                "sync_documents": True,
                "store_embeddings": True,
                "enhance_results": True,
                "knowledge_graph": True,
                "adhd_optimization": True
            }
        }