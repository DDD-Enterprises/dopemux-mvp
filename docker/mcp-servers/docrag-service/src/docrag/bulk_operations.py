"""
Bulk operations for DocRAG service following ADR-0034
Handles bulk upload, delete, and update operations with rate limiting
"""

import asyncio
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiofiles
import structlog

from .models import (
    BulkOperationRequest,
    BulkOperationResponse,
    IngestionRequest,
    IngestionResponse,
    DocumentType,
    SourceType,
    ModelAttribution
)
from .service import DocRAGService
from .processing import DocumentProcessor

logger = structlog.get_logger(__name__)


class RateLimiter:
    """Simple rate limiter for bulk operations."""

    def __init__(self, max_operations_per_hour: int = 100):
        self.max_operations = max_operations_per_hour
        self.operations_log: List[float] = []

    def check_rate_limit(self) -> bool:
        """Check if operation is within rate limit."""
        now = time.time()
        # Remove operations older than 1 hour
        self.operations_log = [op_time for op_time in self.operations_log if now - op_time < 3600]

        if len(self.operations_log) >= self.max_operations:
            return False

        self.operations_log.append(now)
        return True


class BulkOperationsHandler:
    """Handler for bulk operations with security and rate limiting."""

    def __init__(self, docrag_service: DocRAGService):
        self.service = docrag_service
        self.processor = DocumentProcessor()
        self.upload_rate_limiter = RateLimiter(max_operations_per_hour=50)
        self.delete_rate_limiter = RateLimiter(max_operations_per_hour=100)

    async def handle_bulk_operation(self, request: BulkOperationRequest) -> BulkOperationResponse:
        """Handle bulk operation request with rate limiting."""
        start_time = time.time()

        # Check rate limits
        if request.operation == "upload" and not self.upload_rate_limiter.check_rate_limit():
            return BulkOperationResponse(
                success=False,
                total_requested=len(request.documents),
                total_processed=0,
                total_failed=len(request.documents),
                results=[],
                processing_time_ms=0,
                errors=["Rate limit exceeded for upload operations"]
            )

        if request.operation == "delete" and not self.delete_rate_limiter.check_rate_limit():
            return BulkOperationResponse(
                success=False,
                total_requested=len(request.documents),
                total_processed=0,
                total_failed=len(request.documents),
                results=[],
                processing_time_ms=0,
                errors=["Rate limit exceeded for delete operations"]
            )

        # Dispatch to specific handler
        if request.operation == "upload":
            response = await self._handle_bulk_upload(request)
        elif request.operation == "delete":
            response = await self._handle_bulk_delete(request)
        elif request.operation == "update":
            response = await self._handle_bulk_update(request)
        else:
            response = BulkOperationResponse(
                success=False,
                total_requested=len(request.documents),
                total_processed=0,
                total_failed=len(request.documents),
                results=[],
                processing_time_ms=0,
                errors=[f"Unknown operation: {request.operation}"]
            )

        response.processing_time_ms = (time.time() - start_time) * 1000
        return response

    async def _handle_bulk_upload(self, request: BulkOperationRequest) -> BulkOperationResponse:
        """Handle bulk document upload."""
        results = []
        processed = 0
        failed = 0
        errors = []

        # Extract options
        options = request.options
        default_model = options.get("created_by_model")
        if default_model:
            default_model = ModelAttribution(**default_model)

        # Process documents in batches to avoid overwhelming the system
        batch_size = 5
        for i in range(0, len(request.documents), batch_size):
            batch = request.documents[i:i + batch_size]
            batch_tasks = []

            for doc_path in batch:
                if isinstance(doc_path, str):
                    # File path upload
                    task = self._upload_single_document(
                        doc_path,
                        default_model=default_model,
                        options=options
                    )
                else:
                    # Document data upload
                    task = self._upload_document_data(
                        doc_path,
                        default_model=default_model,
                        options=options
                    )
                batch_tasks.append(task)

            # Process batch
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, Exception):
                    failed += 1
                    errors.append(str(result))
                    results.append({"success": False, "error": str(result)})
                else:
                    if result.success:
                        processed += 1
                    else:
                        failed += 1
                        errors.append(result.message)
                    results.append(result.dict())

        return BulkOperationResponse(
            success=failed == 0,
            total_requested=len(request.documents),
            total_processed=processed,
            total_failed=failed,
            results=results,
            processing_time_ms=0,  # Set by caller
            errors=errors
        )

    async def _upload_single_document(
        self,
        file_path: str,
        default_model: Optional[ModelAttribution] = None,
        options: Dict[str, Any] = None
    ) -> IngestionResponse:
        """Upload a single document from file path."""
        try:
            # Security check: prevent path traversal
            path = Path(file_path).resolve()
            if not self._is_safe_path(path):
                raise ValueError(f"Unsafe file path: {file_path}")

            if not path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Determine document type
            doc_type = self._get_document_type(path)

            # Create ingestion request
            ingestion_request = IngestionRequest(
                source_path=str(path),
                metadata={
                    "source_type": SourceType.UPLOAD.value,
                    "created_by_model": default_model.dict() if default_model else None,
                    "bulk_upload": True,
                    **(options.get("metadata", {}))
                },
                chunk_size=options.get("chunk_size", 1000),
                chunk_overlap=options.get("chunk_overlap", 100)
            )

            return await self.service.ingest_document(ingestion_request)

        except Exception as e:
            logger.error("Error uploading document", file_path=file_path, error=str(e))
            return IngestionResponse(
                success=False,
                message=f"Error uploading {file_path}: {str(e)}",
                chunks_created=0,
                source_path=file_path,
                source_hash="",
                processing_time_ms=0
            )

    async def _upload_document_data(
        self,
        doc_data: Dict[str, Any],
        default_model: Optional[ModelAttribution] = None,
        options: Dict[str, Any] = None
    ) -> IngestionResponse:
        """Upload document from data dict."""
        try:
            # Extract required fields
            content = doc_data.get("content", "")
            title = doc_data.get("title", "Untitled")

            if not content:
                raise ValueError("Document content is required")

            # Create temporary file
            temp_path = f"/tmp/bulk_upload_{int(time.time())}_{title}.txt"

            async with aiofiles.open(temp_path, 'w') as f:
                await f.write(content)

            try:
                # Create ingestion request
                ingestion_request = IngestionRequest(
                    source_path=temp_path,
                    metadata={
                        "title": title,
                        "source_type": SourceType.API.value,
                        "created_by_model": default_model.dict() if default_model else None,
                        "bulk_upload": True,
                        **doc_data.get("metadata", {})
                    },
                    chunk_size=doc_data.get("chunk_size", 1000),
                    chunk_overlap=doc_data.get("chunk_overlap", 100)
                )

                return await self.service.ingest_document(ingestion_request)

            finally:
                # Clean up temp file
                Path(temp_path).unlink(missing_ok=True)

        except Exception as e:
            logger.error("Error uploading document data", title=doc_data.get("title"), error=str(e))
            return IngestionResponse(
                success=False,
                message=f"Error uploading document: {str(e)}",
                chunks_created=0,
                source_path=doc_data.get("title", "unknown"),
                source_hash="",
                processing_time_ms=0
            )

    async def _handle_bulk_delete(self, request: BulkOperationRequest) -> BulkOperationResponse:
        """Handle bulk document deletion."""
        # Implementation would go here - need database delete functionality
        return BulkOperationResponse(
            success=False,
            total_requested=len(request.documents),
            total_processed=0,
            total_failed=len(request.documents),
            results=[],
            processing_time_ms=0,
            errors=["Bulk delete not yet implemented"]
        )

    async def _handle_bulk_update(self, request: BulkOperationRequest) -> BulkOperationResponse:
        """Handle bulk document updates."""
        # Implementation would go here - need database update functionality
        return BulkOperationResponse(
            success=False,
            total_requested=len(request.documents),
            total_processed=0,
            total_failed=len(request.documents),
            results=[],
            processing_time_ms=0,
            errors=["Bulk update not yet implemented"]
        )

    def _is_safe_path(self, path: Path) -> bool:
        """Check if file path is safe (no path traversal)."""
        try:
            # Check for path traversal attempts
            path_str = str(path)
            if ".." in path_str or path_str.startswith("/etc") or path_str.startswith("/sys"):
                return False

            # Only allow certain directories (configurable)
            allowed_dirs = ["/tmp", "/workspace", "/app/data"]
            return any(path_str.startswith(allowed_dir) for allowed_dir in allowed_dirs)

        except Exception:
            return False

    def _get_document_type(self, path: Path) -> DocumentType:
        """Determine document type from file extension."""
        extension = path.suffix.lower()

        if extension == ".pdf":
            return DocumentType.PDF
        elif extension in [".md", ".markdown"]:
            return DocumentType.MARKDOWN
        elif extension in [".html", ".htm"]:
            return DocumentType.HTML
        elif extension == ".docx":
            return DocumentType.DOCX
        elif extension in [".txt", ".text"]:
            return DocumentType.TEXT
        else:
            return DocumentType.UNKNOWN