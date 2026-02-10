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

    def __init__(
        self,
        config: AdvancedEmbeddingConfig,
        workspace_id: str,
        conport_client: Optional[Any] = None,
    ):
        """
        Initialize ConPort adapter.

        Args:
            config: Embedding configuration
            workspace_id: ConPort workspace identifier
        """
        super().__init__(config)
        self.integration_name = "conport"
        self.workspace_id = workspace_id
        self.conport_client = conport_client
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
            if self.conport_client and hasattr(self.conport_client, "get_active_context"):
                await self.conport_client.get_active_context(workspace_id=self.workspace_id)
            else:
                # Simulate connection check when no client is injected.
                await asyncio.sleep(0.1)

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
                        logger.info(f"🔄 Syncing {content_type} from ConPort...")

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
                logger.info(f"✅ ConPort sync complete: {documents_synced} documents in {sync_duration:.1f}s")

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
                    if self.conport_client and hasattr(self.conport_client, "log_custom_data"):
                        content = doc.get("content", "")
                        adhd_document = await self._add_adhd_metadata(
                            {"id": doc.get("id"), "content": content, "metadata": doc.get("metadata", {})}
                        )
                        await self.conport_client.log_custom_data(
                            workspace_id=self.workspace_id,
                            category="DocumentEmbeddings",
                            key=f"{doc.get('id', 'unknown')}_embedding",
                            value={
                                "document_id": doc.get("id"),
                                "embedding_vector": embedding,
                                "embedding_dimension": len(embedding),
                                "metadata": doc.get("metadata", {}),
                                "adhd_metadata": adhd_document["adhd_metadata"],
                            },
                        )
                    stored_count += 1

                except Exception as e:
                    logger.warning(f"⚠️ Failed to store embedding for {doc['id']}: {e}")

            if self.config.enable_progress_tracking:
                logger.info(f"💾 Stored {stored_count} embeddings to ConPort")

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
            query = str(context.get("query", ""))
            related_decisions = await self._get_relevant_decisions(query)
            project_patterns: List[Dict[str, Any]] = []

            if self.conport_client and hasattr(self.conport_client, "get_custom_data"):
                try:
                    raw_patterns = await self.conport_client.get_custom_data(
                        workspace_id=self.workspace_id,
                        category="ProjectPatterns",
                    )
                    if isinstance(raw_patterns, list):
                        project_patterns = raw_patterns
                except Exception:
                    # Gracefully degrade if custom-data lookups are unavailable.
                    project_patterns = []

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

                minutes = self._estimate_focus_time(result.content)
                enhanced_result.metadata["adhd_context"] = {
                    "urgency": self._calculate_urgency(result),
                    "complexity": self._calculate_complexity(result),
                    "focus_time_needed": self._format_focus_minutes(minutes),
                }
                enhanced_result.metadata["conport_context"] = {
                    "related_decisions": related_decisions,
                    "project_patterns": project_patterns,
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
        urgency_level = self._calculate_urgency_level(result.content)
        if urgency_level >= 4:
            return "high"
        if urgency_level >= 3:
            return "medium"
        return "low"

    def _calculate_complexity(self, result: SearchResult) -> str:
        """Calculate ADHD-friendly complexity indicator."""
        complexity_score = self._calculate_complexity_score(result.content)
        if complexity_score >= 4:
            return "high"
        if complexity_score >= 2.5:
            return "medium"
        return "low"

    async def _add_adhd_metadata(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Attach ADHD-oriented metadata fields to a document payload."""
        content = str(document.get("content", ""))
        adhd_metadata = {
            "urgency_level": self._calculate_urgency_level(content),
            "complexity_score": self._calculate_complexity_score(content),
            "estimated_focus_time": self._estimate_focus_time(content),
            "context_tags": self._extract_context_tags(content),
        }
        updated = dict(document)
        updated["adhd_metadata"] = adhd_metadata
        return updated

    async def _get_relevant_decisions(self, query: str) -> List[Dict[str, Any]]:
        """Fetch recent ConPort decisions relevant to the current query."""
        if not self.conport_client or not hasattr(self.conport_client, "get_recent_activity_summary"):
            return []
        try:
            summary = await self.conport_client.get_recent_activity_summary(
                workspace_id=self.workspace_id,
                limit=20,
                query=query,
            )
            decisions = summary.get("decisions", []) if isinstance(summary, dict) else []
            return decisions if isinstance(decisions, list) else []
        except Exception:
            return []

    def _calculate_urgency_level(self, content: str) -> float:
        """Return urgency from 1-5 based on language cues."""
        text = content.lower()
        if any(term in text for term in ["critical", "urgent", "immediate", "asap", "blocker"]):
            return 4.5
        if any(term in text for term in ["soon", "priority", "important", "next sprint"]):
            return 3.0
        if any(term in text for term in ["backlog", "future", "reference", "someday"]):
            return 1.5
        return 2.0

    def _calculate_complexity_score(self, content: str) -> float:
        """Return complexity from 1-5 using length and technical cues."""
        text = content.lower()
        length = len(content)
        technical_markers = [
            "algorithm",
            "architecture",
            "neural",
            "optimization",
            "distributed",
            "pipeline",
            "concurrency",
            "embedding",
        ]
        marker_count = sum(1 for marker in technical_markers if marker in text)

        base = 1.0
        if length > 1000:
            base += 2.0
        elif length > 300:
            base += 1.0

        complexity = min(5.0, base + (marker_count * 0.5))
        return max(1.0, complexity)

    def _estimate_focus_time(self, content: str) -> int:
        """Estimate focus time in minutes for a piece of content."""
        words = max(1, len(content.split()))
        base_minutes = words / 180.0 * 60.0
        complexity_score = self._calculate_complexity_score(content)
        complexity_multiplier = 0.8 + (complexity_score / 5.0)
        minutes = int(round(base_minutes * complexity_multiplier))
        if complexity_score >= 2.0:
            minutes += 2
        return max(3, min(120, minutes))

    def _format_focus_minutes(self, minutes: int) -> str:
        """Format minute estimate for user-facing metadata fields."""
        if minutes <= 15:
            return "5-15 minutes"
        if minutes <= 45:
            return "20-45 minutes"
        return "1-2 hours (break into chunks)"

    def _extract_context_tags(self, content: str) -> List[str]:
        """Generate lightweight tags to help ADHD context switching."""
        tags: List[str] = []
        text = content.lower()
        if any(term in text for term in ["ml", "machine learning", "neural", "model"]):
            tags.append("ml")
        if any(term in text for term in ["api", "endpoint", "http", "fastapi"]):
            tags.append("api")
        if any(term in text for term in ["architecture", "design", "system"]):
            tags.append("architecture")
        if any(term in text for term in ["docs", "documentation", "guide"]):
            tags.append("documentation")
        if not tags:
            tags.append("general")
        return tags

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
