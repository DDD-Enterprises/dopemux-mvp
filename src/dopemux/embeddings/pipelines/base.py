"""
Base abstractions for embedding pipeline orchestration.

Provides abstract interfaces for coordinating complex embedding workflows
including document processing, search orchestration, and integration sync.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from ..core import AdvancedEmbeddingConfig, EmbeddingHealthMetrics

logger = logging.getLogger(__name__)


class PipelineStage(str, Enum):
    """Pipeline execution stages."""
    INITIALIZATION = "initialization"
    VALIDATION = "validation"
    PROCESSING = "processing"
    STORAGE = "storage"
    ENHANCEMENT = "enhancement"
    COMPLETION = "completion"
    ERROR_HANDLING = "error_handling"


@dataclass
class PipelineResult:
    """Result of pipeline execution."""

    success: bool
    stage: PipelineStage
    processed_items: int = 0
    failed_items: int = 0
    duration_seconds: float = 0.0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/storage."""
        return {
            "success": self.success,
            "stage": self.stage.value,
            "processed_items": self.processed_items,
            "failed_items": self.failed_items,
            "duration_seconds": self.duration_seconds,
            "errors": self.errors,
            "metadata": self.metadata
        }


class BasePipeline(ABC):
    """
    Abstract base class for embedding pipeline orchestrators.

    Pipeline orchestrators coordinate complex workflows involving
    multiple components like providers, storage, enhancers, and integrations.
    """

    def __init__(self, config: AdvancedEmbeddingConfig, pipeline_id: str):
        """
        Initialize pipeline orchestrator.

        Args:
            config: Embedding configuration
            pipeline_id: Unique pipeline identifier
        """
        self.config = config
        self.pipeline_id = pipeline_id
        self.metrics = EmbeddingHealthMetrics()

        # Pipeline state
        self.current_stage: PipelineStage = PipelineStage.INITIALIZATION
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.results: List[PipelineResult] = []

        # Stage handlers
        self.stage_handlers: Dict[PipelineStage, Callable] = {}
        self.error_handlers: Dict[Exception, Callable] = {}

        logger.info(f"🏗️ Pipeline initialized: {pipeline_id}")

    @abstractmethod
    async def execute(self, input_data: Any) -> PipelineResult:
        """
        Execute the complete pipeline workflow.

        Args:
            input_data: Pipeline input data

        Returns:
            Pipeline execution result
        """
        pass

    @abstractmethod
    async def validate_inputs(self, input_data: Any) -> bool:
        """
        Validate pipeline inputs before execution.

        Args:
            input_data: Input data to validate

        Returns:
            True if inputs are valid
        """
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up pipeline resources after execution."""
        pass

    async def execute_stage(self, stage: PipelineStage,
                           stage_func: Callable,
                           *args, **kwargs) -> PipelineResult:
        """
        Execute a pipeline stage with error handling and metrics.

        Args:
            stage: Pipeline stage identifier
            stage_func: Stage function to execute
            *args: Stage function arguments
            **kwargs: Stage function keyword arguments

        Returns:
            Stage execution result
        """
        stage_start = datetime.now()
        self.current_stage = stage

        if self.config.enable_progress_tracking:
            print(f"🔄 Executing stage: {stage.value}")

        try:
            # Execute stage function
            result = await stage_func(*args, **kwargs)

            # Create success result
            stage_result = PipelineResult(
                success=True,
                stage=stage,
                duration_seconds=(datetime.now() - stage_start).total_seconds(),
                metadata={"result": result}
            )

            self.results.append(stage_result)

            if self.config.enable_progress_tracking:
                print(f"✅ Stage {stage.value} completed in {stage_result.duration_seconds:.1f}s")

            return stage_result

        except Exception as e:
            # Handle stage error
            stage_result = PipelineResult(
                success=False,
                stage=stage,
                duration_seconds=(datetime.now() - stage_start).total_seconds(),
                errors=[str(e)]
            )

            self.results.append(stage_result)

            # Check for custom error handler
            error_handler = self.error_handlers.get(type(e))
            if error_handler:
                try:
                    await error_handler(e, stage_result)
                except Exception as handler_error:
                    logger.error(f"❌ Error handler failed: {handler_error}")

            logger.error(f"❌ Stage {stage.value} failed: {e}")

            if self.config.gentle_error_messages:
                print(f"💙 Stage {stage.value} had some trouble - that's okay, continuing...")
            else:
                print(f"❌ Stage {stage.value} failed: {e}")

            return stage_result

    def register_stage_handler(self, stage: PipelineStage, handler: Callable):
        """Register a handler for a specific pipeline stage."""
        self.stage_handlers[stage] = handler
        logger.debug(f"📝 Registered handler for stage: {stage.value}")

    def register_error_handler(self, exception_type: type, handler: Callable):
        """Register a handler for a specific exception type."""
        self.error_handlers[exception_type] = handler
        logger.debug(f"🛡️ Registered error handler for: {exception_type.__name__}")

    async def run_with_stages(self, stages: List[tuple]) -> List[PipelineResult]:
        """
        Run pipeline through a series of stages.

        Args:
            stages: List of (stage, function, args, kwargs) tuples

        Returns:
            List of stage results
        """
        stage_results = []

        for stage_def in stages:
            if len(stage_def) == 2:
                stage, func = stage_def
                args, kwargs = (), {}
            elif len(stage_def) == 3:
                stage, func, args = stage_def
                kwargs = {}
            else:
                stage, func, args, kwargs = stage_def

            result = await self.execute_stage(stage, func, *args, **kwargs)
            stage_results.append(result)

            # Stop on critical failure
            if not result.success and stage in [PipelineStage.INITIALIZATION, PipelineStage.VALIDATION]:
                logger.error(f"❌ Critical stage {stage.value} failed - stopping pipeline")
                break

        return stage_results

    def get_pipeline_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive pipeline execution summary.

        Returns:
            Summary dictionary with metrics and results
        """
        total_duration = 0.0
        if self.start_time and self.end_time:
            total_duration = (self.end_time - self.start_time).total_seconds()

        successful_stages = sum(1 for r in self.results if r.success)
        failed_stages = sum(1 for r in self.results if not r.success)

        total_processed = sum(r.processed_items for r in self.results)
        total_failed = sum(r.failed_items for r in self.results)

        all_errors = []
        for result in self.results:
            all_errors.extend(result.errors)

        return {
            "pipeline_id": self.pipeline_id,
            "current_stage": self.current_stage.value,
            "total_duration_seconds": total_duration,
            "stages_executed": len(self.results),
            "successful_stages": successful_stages,
            "failed_stages": failed_stages,
            "total_processed_items": total_processed,
            "total_failed_items": total_failed,
            "overall_success": failed_stages == 0,
            "errors": all_errors,
            "stage_results": [r.to_dict() for r in self.results],
            "metrics": self.metrics.get_summary()
        }

    def display_summary(self):
        """Display ADHD-friendly pipeline summary."""
        summary = self.get_pipeline_summary()

        print(f"🏗️ Pipeline Summary: {self.pipeline_id}")
        print("=" * 50)
        print(f"⏱️ Duration: {summary['total_duration_seconds']:.1f}s")
        print(f"📊 Stages: {summary['successful_stages']}/{summary['stages_executed']} successful")
        print(f"📦 Items: {summary['total_processed_items']} processed, {summary['total_failed_items']} failed")

        if summary['overall_success']:
            print("✅ Overall Status: SUCCESS")
        else:
            print("❌ Overall Status: FAILED")
            if summary['errors']:
                print("🚨 Errors:")
                for error in summary['errors'][:3]:  # Show max 3 errors
                    print(f"   • {error}")
                if len(summary['errors']) > 3:
                    print(f"   ... and {len(summary['errors']) - 3} more")

    async def retry_failed_stages(self, max_retries: int = 3) -> List[PipelineResult]:
        """
        Retry failed pipeline stages.

        Args:
            max_retries: Maximum number of retry attempts

        Returns:
            List of retry results
        """
        failed_results = [r for r in self.results if not r.success]
        retry_results = []

        if not failed_results:
            logger.info("✅ No failed stages to retry")
            return retry_results

        if self.config.enable_progress_tracking:
            print(f"🔄 Retrying {len(failed_results)} failed stages...")

        for failed_result in failed_results:
            stage = failed_result.stage
            handler = self.stage_handlers.get(stage)

            if not handler:
                logger.warning(f"⚠️ No handler registered for stage {stage.value}")
                continue

            for attempt in range(max_retries):
                if self.config.enable_progress_tracking:
                    print(f"🔄 Retry {attempt + 1}/{max_retries} for stage {stage.value}")

                retry_result = await self.execute_stage(stage, handler)
                retry_results.append(retry_result)

                if retry_result.success:
                    if self.config.enable_progress_tracking:
                        print(f"✅ Stage {stage.value} succeeded on retry {attempt + 1}")
                    break
            else:
                logger.error(f"❌ Stage {stage.value} failed after {max_retries} retries")

        return retry_results

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform pipeline health check.

        Returns:
            Health status information
        """
        return {
            "pipeline_id": self.pipeline_id,
            "stage": self.current_stage.value,
            "healthy": len([r for r in self.results if not r.success]) == 0,
            "last_execution": self.end_time.isoformat() if self.end_time else None,
            "registered_stages": len(self.stage_handlers),
            "registered_error_handlers": len(self.error_handlers)
        }