"""
Sync Pipeline

Orchestrates synchronization between the embedding system and external
integrations, handling bidirectional data flow and maintaining consistency
across ConPort, Serena, and other dopemux components.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Set
from datetime import datetime, timedelta

from ..core import AdvancedEmbeddingConfig, EmbeddingError
from ..storage import HybridVectorStore
from ..integrations import BaseIntegration
from .base import BasePipeline, PipelineStage, PipelineResult
from .document_pipeline import DocumentPipeline

logger = logging.getLogger(__name__)


class SyncPipeline(BasePipeline):
    """
    Integration synchronization pipeline.

    Orchestrates bidirectional synchronization between the embedding
    system and external integrations, ensuring data consistency and
    enabling seamless workflows across dopemux components.
    """

    def __init__(self, config: AdvancedEmbeddingConfig,
                 vector_store: HybridVectorStore,
                 integrations: List[BaseIntegration],
                 document_pipeline: Optional[DocumentPipeline] = None,
                 pipeline_id: str = "sync_pipeline"):
        """
        Initialize sync pipeline.

        Args:
            config: Embedding configuration
            vector_store: Hybrid vector store
            integrations: List of integrations to sync
            document_pipeline: Document pipeline for processing new docs
            pipeline_id: Unique pipeline identifier
        """
        super().__init__(config, pipeline_id)

        self.vector_store = vector_store
        self.integrations = integrations
        self.document_pipeline = document_pipeline

        # Sync state
        self.sync_results: Dict[str, Dict[str, Any]] = {}
        self.new_documents: List[Dict[str, Any]] = []
        self.updated_documents: List[Dict[str, Any]] = []
        self.deleted_documents: List[str] = []

        # Sync tracking
        self.last_sync_times: Dict[str, datetime] = {}
        self.sync_conflicts: List[Dict[str, Any]] = []

        # Register pipeline stages
        self._register_stages()

        logger.info(f"🔄 Sync pipeline initialized with {len(integrations)} integrations")

    def _register_stages(self):
        """Register pipeline stage handlers."""
        self.register_stage_handler(PipelineStage.VALIDATION, self._validate_stage)
        self.register_stage_handler(PipelineStage.PROCESSING, self._sync_stage)
        self.register_stage_handler(PipelineStage.STORAGE, self._storage_stage)
        self.register_stage_handler(PipelineStage.COMPLETION, self._completion_stage)

    async def execute(self, sync_config: Optional[Dict[str, Any]] = None) -> PipelineResult:
        """
        Execute the complete sync pipeline.

        Args:
            sync_config: Sync configuration options
                - full_sync: Perform full synchronization (default: False)
                - workspace_ids: List of workspace IDs to sync (default: all)
                - integration_names: List of integration names to sync (default: all)
                - max_age_hours: Only sync documents modified within hours (default: 24)

        Returns:
            Pipeline execution result
        """
        self.start_time = datetime.now()
        sync_config = sync_config or {}

        if self.config.enable_progress_tracking:
            full_sync = sync_config.get("full_sync", False)
            sync_mode = "full" if full_sync else "incremental"
            print(f"🔄 Starting {sync_mode} sync pipeline...")

        try:
            # Define pipeline stages
            stages = [
                (PipelineStage.VALIDATION, self._validate_stage, sync_config),
                (PipelineStage.PROCESSING, self._sync_stage, sync_config),
                (PipelineStage.STORAGE, self._storage_stage),
                (PipelineStage.COMPLETION, self._completion_stage)
            ]

            # Execute stages
            stage_results = await self.run_with_stages(stages)

            # Calculate final result
            overall_success = all(r.success for r in stage_results)
            total_processed = sum(r.processed_items for r in stage_results)
            total_failed = sum(r.failed_items for r in stage_results)

            final_result = PipelineResult(
                success=overall_success,
                stage=PipelineStage.COMPLETION,
                processed_items=total_processed,
                failed_items=total_failed,
                duration_seconds=(datetime.now() - self.start_time).total_seconds(),
                metadata={
                    "sync_config": sync_config,
                    "integrations_synced": len(self.sync_results),
                    "new_documents": len(self.new_documents),
                    "updated_documents": len(self.updated_documents),
                    "deleted_documents": len(self.deleted_documents),
                    "sync_conflicts": len(self.sync_conflicts)
                }
            )

            self.end_time = datetime.now()

            if self.config.enable_progress_tracking:
                if overall_success:
                    print(f"✅ Sync completed: {total_processed} items processed")
                else:
                    print(f"⚠️ Sync completed with issues: {total_failed} failed")

            return final_result

        except Exception as e:
            self.end_time = datetime.now()
            error_result = PipelineResult(
                success=False,
                stage=self.current_stage,
                duration_seconds=(datetime.now() - self.start_time).total_seconds(),
                errors=[str(e)]
            )

            logger.error(f"❌ Sync pipeline failed: {e}")
            return error_result

    async def validate_inputs(self, sync_config: Dict[str, Any]) -> bool:
        """
        Validate sync configuration and pipeline components.

        Args:
            sync_config: Sync configuration to validate

        Returns:
            True if configuration is valid
        """
        # Validate integrations
        if not self.integrations:
            logger.error("❌ No integrations configured for sync")
            return False

        # Validate workspace IDs if specified
        workspace_ids = sync_config.get("workspace_ids", [])
        if workspace_ids and not all(isinstance(wid, str) for wid in workspace_ids):
            logger.error("❌ All workspace IDs must be strings")
            return False

        # Validate integration names if specified
        integration_names = sync_config.get("integration_names", [])
        available_names = [i.__class__.__name__ for i in self.integrations]

        for name in integration_names:
            if name not in available_names:
                logger.error(f"❌ Integration '{name}' not available. Available: {available_names}")
                return False

        # Validate max age
        max_age_hours = sync_config.get("max_age_hours", 24)
        if not isinstance(max_age_hours, (int, float)) or max_age_hours <= 0:
            logger.error("❌ max_age_hours must be a positive number")
            return False

        return True

    async def _validate_stage(self, sync_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate sync configuration and integration health."""
        validation_start = datetime.now()

        # Validate inputs
        if not await self.validate_inputs(sync_config):
            raise EmbeddingError("Sync configuration validation failed")

        # Check integration health
        integration_health = {}
        healthy_count = 0

        for integration in self.integrations:
            integration_name = integration.__class__.__name__

            try:
                is_healthy = await integration.validate_connection()
                integration_health[integration_name] = {
                    "healthy": is_healthy,
                    "status": integration.get_integration_status()
                }

                if is_healthy:
                    healthy_count += 1

            except Exception as e:
                logger.warning(f"⚠️ Integration {integration_name} health check failed: {e}")
                integration_health[integration_name] = {
                    "healthy": False,
                    "error": str(e)
                }

        if healthy_count == 0:
            raise EmbeddingError("No healthy integrations available for sync")

        # Check vector store
        store_stats = self.vector_store.get_stats()

        validation_duration = (datetime.now() - validation_start).total_seconds()

        return {
            "sync_config": sync_config,
            "integration_health": integration_health,
            "healthy_integrations": healthy_count,
            "total_integrations": len(self.integrations),
            "vector_store_stats": store_stats,
            "validation_duration": validation_duration
        }

    async def _sync_stage(self, sync_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute synchronization with all integrations."""
        sync_start = datetime.now()

        # Determine which integrations to sync
        target_integrations = self._get_target_integrations(sync_config)

        if self.config.enable_progress_tracking:
            print(f"🔄 Syncing {len(target_integrations)} integrations...")

        # Process each integration
        for integration in target_integrations:
            integration_name = integration.__class__.__name__

            try:
                if self.config.enable_progress_tracking:
                    print(f"🔗 Syncing {integration_name}...")

                # Sync documents from integration
                sync_result = await self._sync_integration(integration, sync_config)
                self.sync_results[integration_name] = sync_result

            except Exception as e:
                logger.error(f"❌ Sync failed for {integration_name}: {e}")
                self.sync_results[integration_name] = {
                    "success": False,
                    "error": str(e),
                    "documents_synced": 0
                }

        # Detect and resolve conflicts
        await self._detect_sync_conflicts()

        sync_duration = (datetime.now() - sync_start).total_seconds()

        total_new = len(self.new_documents)
        total_updated = len(self.updated_documents)
        total_deleted = len(self.deleted_documents)

        return {
            "integrations_synced": len(self.sync_results),
            "new_documents": total_new,
            "updated_documents": total_updated,
            "deleted_documents": total_deleted,
            "sync_conflicts": len(self.sync_conflicts),
            "sync_duration": sync_duration
        }

    def _get_target_integrations(self, sync_config: Dict[str, Any]) -> List[BaseIntegration]:
        """Get list of integrations to sync based on configuration."""
        integration_names = sync_config.get("integration_names", [])

        if not integration_names:
            return self.integrations

        target_integrations = []
        for integration in self.integrations:
            if integration.__class__.__name__ in integration_names:
                target_integrations.append(integration)

        return target_integrations

    async def _sync_integration(self, integration: BaseIntegration,
                               sync_config: Dict[str, Any]) -> Dict[str, Any]:
        """Sync documents from a specific integration."""
        integration_name = integration.__class__.__name__

        # Determine workspace IDs to sync
        workspace_ids = sync_config.get("workspace_ids", [])

        if not workspace_ids:
            # Try to get default workspace from integration
            status = integration.get_integration_status()
            if "workspace_id" in status:
                workspace_ids = [status["workspace_id"]]
            elif "project_root" in status:
                workspace_ids = [status["project_root"]]
            else:
                logger.warning(f"⚠️ No workspace IDs available for {integration_name}")
                return {"success": False, "error": "No workspace IDs"}

        sync_result = {
            "success": True,
            "documents_synced": 0,
            "workspaces": {},
            "errors": []
        }

        # Sync each workspace
        for workspace_id in workspace_ids:
            try:
                workspace_result = await integration.sync_documents(workspace_id)

                sync_result["workspaces"][workspace_id] = workspace_result
                sync_result["documents_synced"] += workspace_result.get("documents_synced", 0)

                # Collect new documents
                workspace_docs = workspace_result.get("documents", [])
                for doc in workspace_docs:
                    if self._is_new_document(doc):
                        self.new_documents.append(doc)
                    else:
                        self.updated_documents.append(doc)

            except Exception as e:
                error_msg = f"Workspace {workspace_id} sync failed: {str(e)}"
                sync_result["errors"].append(error_msg)
                logger.warning(f"⚠️ {error_msg}")

        # Update last sync time
        self.last_sync_times[integration_name] = datetime.now()

        if sync_result["errors"]:
            sync_result["success"] = False

        return sync_result

    def _is_new_document(self, doc: Dict[str, Any]) -> bool:
        """Check if document is new or updated."""
        doc_id = doc.get("id")
        if not doc_id:
            return True

        # Check if document exists in vector store
        try:
            store_stats = self.vector_store.get_stats()
            # This is simplified - in practice would check actual document existence
            return True  # Assume new for now
        except Exception:
            return True

    async def _detect_sync_conflicts(self):
        """Detect and handle synchronization conflicts."""
        # Group documents by ID
        doc_groups: Dict[str, List[Dict[str, Any]]] = {}

        for doc in self.new_documents + self.updated_documents:
            doc_id = doc.get("id")
            if doc_id:
                if doc_id not in doc_groups:
                    doc_groups[doc_id] = []
                doc_groups[doc_id].append(doc)

        # Find conflicts (same ID from multiple sources)
        for doc_id, docs in doc_groups.items():
            if len(docs) > 1:
                conflict = {
                    "document_id": doc_id,
                    "sources": [doc.get("metadata", {}).get("source") for doc in docs],
                    "last_modified": [doc.get("metadata", {}).get("timestamp") for doc in docs],
                    "resolution": "most_recent"  # Simple resolution strategy
                }

                self.sync_conflicts.append(conflict)

                # Resolve by keeping most recent
                most_recent_doc = max(docs, key=lambda d: d.get("metadata", {}).get("timestamp", ""))

                # Remove duplicates
                for doc in docs:
                    if doc != most_recent_doc:
                        if doc in self.new_documents:
                            self.new_documents.remove(doc)
                        if doc in self.updated_documents:
                            self.updated_documents.remove(doc)

        if self.sync_conflicts and self.config.enable_progress_tracking:
            print(f"⚠️ Resolved {len(self.sync_conflicts)} sync conflicts")

    async def _storage_stage(self) -> Dict[str, Any]:
        """Store synced documents using document pipeline."""
        storage_start = datetime.now()

        documents_to_store = self.new_documents + self.updated_documents

        if not documents_to_store:
            logger.debug("ℹ️ No documents to store")
            return {"stored_count": 0, "storage_duration": 0}

        if self.config.enable_progress_tracking:
            print(f"💾 Processing {len(documents_to_store)} synced documents...")

        stored_count = 0

        try:
            if self.document_pipeline:
                # Use document pipeline for processing
                pipeline_result = await self.document_pipeline.execute(documents_to_store)
                stored_count = pipeline_result.processed_items

            else:
                # Direct storage to vector store
                await self.vector_store.add_documents(documents_to_store)
                stored_count = len(documents_to_store)

            # Handle deletions
            if self.deleted_documents:
                await self.vector_store.delete_documents(self.deleted_documents)

            storage_duration = (datetime.now() - storage_start).total_seconds()

            return {
                "stored_count": stored_count,
                "deleted_count": len(self.deleted_documents),
                "storage_duration": storage_duration,
                "used_pipeline": self.document_pipeline is not None
            }

        except Exception as e:
            logger.error(f"❌ Storage stage failed: {e}")
            raise EmbeddingError(f"Document storage failed: {e}") from e

    async def _completion_stage(self) -> Dict[str, Any]:
        """Complete sync and update integration states."""
        completion_start = datetime.now()

        # Update sync timestamps
        sync_timestamp = datetime.now()

        # Notify integrations of successful sync
        notification_results = {}

        for integration in self.integrations:
            integration_name = integration.__class__.__name__

            if integration_name in self.sync_results:
                try:
                    # In a real implementation, you might call an integration method
                    # to update its internal sync state
                    notification_results[integration_name] = "notified"

                except Exception as e:
                    logger.warning(f"⚠️ Failed to notify {integration_name}: {e}")
                    notification_results[integration_name] = f"failed: {str(e)}"

        # Cleanup resources
        await self.cleanup()

        completion_duration = (datetime.now() - completion_start).total_seconds()

        return {
            "sync_timestamp": sync_timestamp.isoformat(),
            "notification_results": notification_results,
            "completion_duration": completion_duration,
            "total_pipeline_duration": (datetime.now() - self.start_time).total_seconds()
        }

    async def cleanup(self) -> None:
        """Clean up pipeline resources after execution."""
        try:
            # Clear processing state
            self.new_documents.clear()
            self.updated_documents.clear()
            self.deleted_documents.clear()
            self.sync_conflicts.clear()

            logger.debug("🧹 Sync pipeline cleanup completed")

        except Exception as e:
            logger.warning(f"⚠️ Sync cleanup warning: {e}")

    async def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current sync status for monitoring.

        Returns:
            Current sync pipeline status
        """
        return {
            "pipeline_id": self.pipeline_id,
            "current_stage": self.current_stage.value,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "integrations_count": len(self.integrations),
            "new_documents": len(self.new_documents),
            "updated_documents": len(self.updated_documents),
            "deleted_documents": len(self.deleted_documents),
            "sync_conflicts": len(self.sync_conflicts),
            "last_sync_times": {
                name: time.isoformat() for name, time in self.last_sync_times.items()
            },
            "sync_results": self.sync_results
        }

    def get_sync_summary(self) -> Dict[str, Any]:
        """Get comprehensive sync summary."""
        summary = self.get_pipeline_summary()

        # Add sync-specific information
        summary.update({
            "sync_results": self.sync_results,
            "conflicts_resolved": len(self.sync_conflicts),
            "last_sync_times": {
                name: time.isoformat() for name, time in self.last_sync_times.items()
            }
        })

        return summary

    def display_sync_summary(self):
        """Display ADHD-friendly sync summary."""
        summary = self.get_sync_summary()

        print(f"🔄 Sync Summary: {self.pipeline_id}")
        print("=" * 50)

        # Overall status
        if summary["overall_success"]:
            print("✅ Overall Status: SUCCESS")
        else:
            print("❌ Overall Status: FAILED")

        print(f"⏱️ Duration: {summary['total_duration_seconds']:.1f}s")
        print(f"🔗 Integrations: {len(self.sync_results)} synced")

        # Document summary
        total_docs = len(self.new_documents) + len(self.updated_documents)
        print(f"📄 Documents: {total_docs} processed")
        print(f"   • {len(self.new_documents)} new")
        print(f"   • {len(self.updated_documents)} updated")
        if self.deleted_documents:
            print(f"   • {len(self.deleted_documents)} deleted")

        # Conflicts
        if self.sync_conflicts:
            print(f"⚠️ Conflicts: {len(self.sync_conflicts)} resolved")

        # Integration details
        print("\n🔗 Integration Results:")
        for name, result in self.sync_results.items():
            status_emoji = "✅" if result.get("success", False) else "❌"
            docs_synced = result.get("documents_synced", 0)
            print(f"   {status_emoji} {name}: {docs_synced} documents")

        if summary["errors"]:
            print(f"\n🚨 Errors: {len(summary['errors'])}")
            for error in summary["errors"][:3]:
                print(f"   • {error}")
            if len(summary["errors"]) > 3:
                print(f"   ... and {len(summary['errors']) - 3} more")