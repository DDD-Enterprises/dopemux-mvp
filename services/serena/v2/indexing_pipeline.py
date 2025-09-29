"""
Serena v2 Dual-Mode Indexing Pipeline

Comprehensive indexing system for initial codebase analysis and incremental updates.
Provides real-time code intelligence with ADHD optimizations and multi-instance support.
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import hashlib

from watchdog import observers, events
import redis.asyncio as redis

from .code_structure_analyzer import CodeStructureAnalyzer
from .code_graph_storage import CodeGraphStorage, CodeNode, CodeRelationship, NodeType, RelationshipType
from .claude_context_integration import ClaudeContextIntegration

logger = logging.getLogger(__name__)


class IndexingMode(str, Enum):
    """Indexing pipeline modes."""
    INITIAL = "initial"      # Full codebase analysis
    INCREMENTAL = "incremental"  # Real-time updates
    MAINTENANCE = "maintenance"  # Background optimization
    PAUSED = "paused"       # User-requested pause


class IndexingPhase(str, Enum):
    """Phases of initial indexing."""
    DISCOVERY = "discovery"
    FILTERING = "filtering"
    PRIORITIZATION = "prioritization"
    PARSING = "parsing"
    GRAPH_CONSTRUCTION = "graph_construction"
    CACHE_WARMING = "cache_warming"
    COMPLETE = "complete"


@dataclass
class IndexingProgress:
    """Progress tracking for ADHD-friendly feedback."""
    mode: IndexingMode
    phase: IndexingPhase
    files_total: int = 0
    files_processed: int = 0
    symbols_extracted: int = 0
    relationships_mapped: int = 0
    estimated_completion: Optional[datetime] = None
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # ADHD-specific progress
    last_feedback: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    cognitive_load_estimate: float = 0.5
    pausable: bool = True
    can_resume: bool = True


@dataclass
class FileChangeEvent:
    """Represents a file change for incremental indexing."""
    file_path: str
    change_type: str  # created, modified, deleted, moved
    timestamp: datetime
    workspace_id: str
    instance_id: str = "default"

    # Impact assessment
    impact_calculated: bool = False
    affected_files: List[str] = field(default_factory=list)
    processing_priority: int = 5  # 1=urgent, 5=normal, 10=low


class SerenaIndexingPipeline:
    """
    Dual-mode indexing pipeline with ADHD optimizations and multi-instance support.

    Features:
    - Initial indexing: Full codebase analysis with progress tracking
    - Incremental indexing: Real-time updates with <1 second response
    - ADHD accommodations: Progress feedback, pause/resume, cognitive load management
    - Multi-instance coordination: Workspace isolation, shared results, conflict resolution
    - Performance optimization: Parallel processing, intelligent batching, resource limits
    """

    def __init__(
        self,
        workspace_path: Path,
        instance_id: str = "default",
        redis_url: str = "redis://localhost:6379"
    ):
        self.workspace_path = workspace_path
        self.instance_id = instance_id
        self.workspace_id = str(workspace_path)
        self.redis_url = redis_url

        # Core components
        self.code_analyzer: Optional[CodeStructureAnalyzer] = None
        self.graph_storage: Optional[CodeGraphStorage] = None
        self.claude_integration: Optional[ClaudeContextIntegration] = None
        self.redis_client: Optional[redis.Redis] = None

        # Pipeline state
        self.current_mode = IndexingMode.INITIAL
        self.progress = IndexingProgress(IndexingMode.INITIAL, IndexingPhase.DISCOVERY)
        self.running = False
        self.paused = False

        # File monitoring
        self.file_observer: Optional[observers.Observer] = None
        self.change_queue: asyncio.Queue = asyncio.Queue()
        self.processing_locks: Set[str] = set()

        # Performance settings
        self.max_workers = 4
        self.batch_size = 10
        self.max_cpu_percent = 50  # ADHD: Don't overwhelm system
        self.progress_feedback_interval = 5  # seconds

        # Multi-instance coordination
        self.coordination_enabled = True
        self.instance_locks: Dict[str, str] = {}

        # Background workers
        self.workers: List[asyncio.Task] = []

    async def initialize(self) -> None:
        """Initialize indexing pipeline components."""
        logger.info("📂 Initializing Serena Indexing Pipeline...")

        # Initialize core components
        await self._initialize_components()

        # Setup file monitoring for incremental indexing
        await self._setup_file_monitoring()

        # Start background workers
        await self._start_background_workers()

        logger.info("✅ Serena Indexing Pipeline ready!")

    async def _initialize_components(self) -> None:
        """Initialize core pipeline components."""
        # Initialize Redis for coordination
        self.redis_client = redis.from_url(
            self.redis_url,
            db=7,  # Separate DB for indexing coordination
            decode_responses=True
        )
        await self.redis_client.ping()

        # Initialize code analyzer
        self.code_analyzer = CodeStructureAnalyzer(self.workspace_path)
        await self.code_analyzer.initialize()

        # Initialize graph storage (would be configured separately)
        # self.graph_storage = await create_code_graph_storage(config, self.workspace_id)

        # Initialize claude-context integration (would be configured separately)
        # self.claude_integration = await create_claude_context_integration(config, navigation_cache, lsp_wrapper)

        logger.info("🔧 Pipeline components initialized")

    async def _setup_file_monitoring(self) -> None:
        """Setup file system monitoring for incremental indexing."""
        try:
            # Create file change handler
            change_handler = FileChangeHandler(self.change_queue, self.workspace_path)

            # Setup watchdog observer
            self.file_observer = observers.Observer()
            self.file_observer.schedule(
                change_handler,
                str(self.workspace_path),
                recursive=True
            )

            self.file_observer.start()
            logger.info("👁️ File monitoring started for incremental indexing")

        except Exception as e:
            logger.error(f"File monitoring setup failed: {e}")

    async def _start_background_workers(self) -> None:
        """Start background processing workers."""
        workers = [
            self._incremental_processing_worker(),
            self._progress_reporter(),
            self._coordination_worker()
        ]

        self.workers = [asyncio.create_task(worker) for worker in workers]
        logger.info("👥 Background workers started")

    # Initial Indexing Implementation

    async def run_initial_indexing(
        self,
        progress_callback: Optional[Callable] = None,
        resume_from_checkpoint: bool = False
    ) -> Dict[str, Any]:
        """
        Run complete initial indexing with ADHD accommodations.

        Args:
            progress_callback: Optional callback for progress updates
            resume_from_checkpoint: Resume from previous checkpoint if available

        Returns:
            Indexing results and statistics
        """
        try:
            logger.info("🚀 Starting initial codebase indexing...")

            # Check for previous checkpoint
            if resume_from_checkpoint:
                checkpoint = await self._load_indexing_checkpoint()
                if checkpoint:
                    logger.info("📂 Resuming from previous checkpoint")
                    self.progress = IndexingProgress(**checkpoint)

            # Phase 1: Discovery
            self.progress.phase = IndexingPhase.DISCOVERY
            if progress_callback:
                progress_callback("🔍 Discovering code files...")

            discovered_files = await self._discover_code_files()
            self.progress.files_total = len(discovered_files)

            # Phase 2: Filtering and Prioritization
            self.progress.phase = IndexingPhase.FILTERING
            if progress_callback:
                progress_callback(f"📋 Filtering {len(discovered_files)} files...")

            filtered_files = await self._filter_and_prioritize_files(discovered_files)

            # Phase 3: Parallel Processing
            self.progress.phase = IndexingPhase.PARSING
            if progress_callback:
                progress_callback(f"⚡ Parsing {len(filtered_files)} files...")

            analysis_results = await self._parallel_file_processing(
                filtered_files, progress_callback
            )

            # Phase 4: Graph Construction
            self.progress.phase = IndexingPhase.GRAPH_CONSTRUCTION
            if progress_callback:
                progress_callback("🕸️ Building code relationship graph...")

            graph_stats = await self._build_complete_graph(analysis_results)

            # Phase 5: Cache Warming
            self.progress.phase = IndexingPhase.CACHE_WARMING
            if progress_callback:
                progress_callback("🔥 Warming navigation cache...")

            cache_stats = await self._warm_navigation_cache(analysis_results)

            # Phase 6: Complete
            self.progress.phase = IndexingPhase.COMPLETE
            completion_time = datetime.now(timezone.utc)
            total_duration = (completion_time - self.progress.start_time).total_seconds() / 60

            # Generate final report
            final_stats = {
                "status": "completed",
                "duration_minutes": round(total_duration, 1),
                "files_processed": self.progress.files_processed,
                "symbols_extracted": self.progress.symbols_extracted,
                "relationships_mapped": self.progress.relationships_mapped,
                "graph_stats": graph_stats,
                "cache_stats": cache_stats,
                "completion_time": completion_time.isoformat(),
                "adhd_accommodations": {
                    "progress_updates_sent": self._count_progress_updates(),
                    "pause_points_available": True,
                    "cognitive_load_managed": True
                }
            }

            # Store completion checkpoint
            await self._store_completion_checkpoint(final_stats)

            # Switch to incremental mode
            self.current_mode = IndexingMode.INCREMENTAL

            if progress_callback:
                progress_callback(f"✅ Initial indexing complete! {final_stats['symbols_extracted']} symbols analyzed")

            logger.info(f"🎉 Initial indexing completed in {total_duration:.1f} minutes")
            return final_stats

        except Exception as e:
            logger.error(f"Initial indexing failed: {e}")
            await self._store_error_checkpoint(str(e))
            return {"status": "error", "error": str(e)}

    async def _discover_code_files(self) -> List[str]:
        """Discover code files in workspace with intelligent filtering."""
        try:
            code_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.rs', '.go', '.java', '.cpp', '.c', '.h'}
            exclude_patterns = {
                'node_modules', '__pycache__', '.git', 'build', 'dist',
                'target', '.pytest_cache', '.mypy_cache', 'venv', 'env'
            }

            discovered_files = []

            for file_path in self.workspace_path.rglob("*"):
                if file_path.is_file():
                    # Check extension
                    if file_path.suffix.lower() not in code_extensions:
                        continue

                    # Check exclude patterns
                    if any(pattern in str(file_path) for pattern in exclude_patterns):
                        continue

                    # Check file size (skip very large files)
                    if file_path.stat().st_size > 1024 * 1024:  # 1MB limit
                        continue

                    discovered_files.append(str(file_path))

            logger.info(f"🔍 Discovered {len(discovered_files)} code files")
            return discovered_files

        except Exception as e:
            logger.error(f"File discovery failed: {e}")
            return []

    async def _filter_and_prioritize_files(self, files: List[str]) -> List[str]:
        """Filter and prioritize files for processing."""
        try:
            # Priority scoring
            scored_files = []

            for file_path in files:
                score = await self._calculate_file_priority(file_path)
                scored_files.append((score, file_path))

            # Sort by priority (higher score = higher priority)
            scored_files.sort(reverse=True)

            # Return files in priority order
            prioritized_files = [file_path for _, file_path in scored_files]

            logger.info(f"📋 Prioritized {len(prioritized_files)} files for processing")
            return prioritized_files

        except Exception as e:
            logger.error(f"File prioritization failed: {e}")
            return files  # Return original list on error

    async def _calculate_file_priority(self, file_path: str) -> float:
        """Calculate processing priority for file."""
        try:
            score = 0.0
            path = Path(file_path)

            # Entry point detection
            if path.name in ['main.py', 'index.ts', 'app.py', '__init__.py']:
                score += 10.0

            # Recently modified files
            mtime = path.stat().st_mtime
            age_days = (time.time() - mtime) / (24 * 3600)
            if age_days < 7:
                score += 5.0 - age_days  # More recent = higher priority

            # File size consideration (medium-sized files often most important)
            size_kb = path.stat().st_size / 1024
            if 10 <= size_kb <= 100:  # Sweet spot for important files
                score += 3.0

            # Directory importance
            if any(important in str(path) for important in ['src', 'lib', 'core', 'main']):
                score += 2.0

            # Test files have lower priority
            if 'test' in str(path).lower():
                score -= 1.0

            return max(0.0, score)

        except Exception:
            return 1.0  # Default priority

    async def _parallel_file_processing(
        self,
        files: List[str],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Process files in parallel with ADHD progress tracking."""
        try:
            all_analysis_results = {}
            processed_count = 0

            # Process files in batches for ADHD feedback
            for i in range(0, len(files), self.batch_size):
                if self.paused:
                    logger.info("⏸️ Indexing paused by user")
                    await self._wait_for_resume()

                batch = files[i:i + self.batch_size]

                # Process batch in parallel
                batch_tasks = [
                    self._process_single_file(file_path)
                    for file_path in batch
                ]

                batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

                # Collect successful results
                for file_path, result in zip(batch, batch_results):
                    if isinstance(result, Exception):
                        logger.warning(f"File processing failed for {file_path}: {result}")
                    elif result:
                        all_analysis_results[file_path] = result
                        processed_count += 1

                        # Update progress
                        self.progress.files_processed = processed_count
                        if result.get("symbols"):
                            self.progress.symbols_extracted += len(result["symbols"])

                # ADHD: Provide regular progress feedback
                if progress_callback and (i % (self.batch_size * 2) == 0):
                    progress_percent = (processed_count / len(files)) * 100
                    eta = self._calculate_eta(processed_count, len(files))
                    progress_callback(
                        f"📊 Progress: {processed_count}/{len(files)} files ({progress_percent:.1f}%) - ETA: {eta}"
                    )

                # Save checkpoint periodically for resumability
                if processed_count % 50 == 0:
                    await self._save_progress_checkpoint()

                # Brief pause to prevent overwhelming system
                await asyncio.sleep(0.1)

            logger.info(f"⚡ Parallel processing complete: {processed_count} files analyzed")
            return all_analysis_results

        except Exception as e:
            logger.error(f"Parallel file processing failed: {e}")
            return {}

    async def _process_single_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Process single file with error handling."""
        try:
            if not self.code_analyzer:
                return None

            # Claim file for processing (multi-instance coordination)
            if self.coordination_enabled:
                if not await self._claim_file_processing(file_path):
                    return None  # Another instance is processing this file

            # Analyze file structure
            analysis_result = await self.code_analyzer.analyze_file_structure(
                file_path, include_dependencies=True
            )

            # Release processing claim
            if self.coordination_enabled:
                await self._release_file_processing(file_path)

            return analysis_result

        except Exception as e:
            logger.error(f"Single file processing failed for {file_path}: {e}")
            await self._release_file_processing(file_path)
            return None

    # Incremental Indexing Implementation

    async def _incremental_processing_worker(self) -> None:
        """Background worker for incremental processing."""
        logger.info("🔄 Started incremental processing worker")

        while self.running:
            try:
                # Wait for file change events
                change_event = await asyncio.wait_for(self.change_queue.get(), timeout=5.0)

                # Process change with impact analysis
                await self._process_file_change(change_event)

            except asyncio.TimeoutError:
                # No changes, continue monitoring
                continue
            except Exception as e:
                logger.error(f"Incremental processing error: {e}")
                await asyncio.sleep(1.0)

    async def _process_file_change(self, change_event: FileChangeEvent) -> None:
        """Process individual file change with impact analysis."""
        try:
            start_time = time.time()

            # Step 1: Impact Analysis (target: <100ms)
            if not change_event.impact_calculated:
                await self._calculate_change_impact(change_event)

            # Step 2: Claim processing (multi-instance coordination)
            if not await self._claim_change_processing(change_event):
                return  # Another instance is handling this change

            # Step 3: Selective Re-analysis (target: <500ms)
            if change_event.change_type == "deleted":
                await self._handle_file_deletion(change_event)
            else:
                await self._handle_file_modification(change_event)

            # Step 4: Graph Updates (target: <200ms)
            await self._update_graph_incrementally(change_event)

            # Step 5: Cache Invalidation (target: <100ms)
            await self._invalidate_affected_cache(change_event)

            # Step 6: Notify claude-context (async, non-blocking)
            asyncio.create_task(self._notify_claude_context_changes(change_event))

            # Performance tracking
            processing_time = (time.time() - start_time) * 1000  # milliseconds
            if processing_time > 1000:  # Warn if over 1 second
                logger.warning(f"⏰ Slow incremental processing: {processing_time:.0f}ms for {change_event.file_path}")
            else:
                logger.debug(f"⚡ Incremental update: {processing_time:.0f}ms for {Path(change_event.file_path).name}")

        except Exception as e:
            logger.error(f"File change processing failed: {e}")
        finally:
            await self._release_change_processing(change_event)

    async def _calculate_change_impact(self, change_event: FileChangeEvent) -> None:
        """Calculate impact of file change on code graph."""
        try:
            file_path = change_event.file_path

            # Find affected files through relationships
            affected_files = set()

            if self.graph_storage:
                # Find files that import this file
                importers = await self.graph_storage.find_related_nodes(
                    self._generate_file_node_id(file_path),
                    self.workspace_id,
                    relationship_types=[RelationshipType.IMPORTS],
                    max_depth=1
                )
                affected_files.update(node["file_path"] for node in importers)

                # Find files this file imports (might have new dependencies)
                imported = await self.graph_storage.find_related_nodes(
                    self._generate_file_node_id(file_path),
                    self.workspace_id,
                    relationship_types=[RelationshipType.IMPORTS],
                    max_depth=1
                )
                affected_files.update(node["file_path"] for node in imported)

            change_event.affected_files = list(affected_files)
            change_event.impact_calculated = True

            logger.debug(f"📊 Impact calculated: {len(affected_files)} files affected by {Path(file_path).name}")

        except Exception as e:
            logger.error(f"Impact calculation failed: {e}")
            change_event.affected_files = []
            change_event.impact_calculated = True

    # Multi-Instance Coordination

    async def _claim_file_processing(self, file_path: str) -> bool:
        """Claim file for processing (multi-instance coordination)."""
        try:
            file_hash = hashlib.sha256(file_path.encode()).hexdigest()[:12]
            lock_key = f"indexing:file_lock:{file_hash}"

            # Try to acquire lock with 5-minute expiration
            acquired = await self.redis_client.set(
                lock_key, self.instance_id, ex=300, nx=True
            )

            if acquired:
                self.processing_locks.add(file_path)
                return True
            else:
                # Check who owns the lock
                owner = await self.redis_client.get(lock_key)
                logger.debug(f"🔒 File {Path(file_path).name} locked by instance {owner}")
                return False

        except Exception as e:
            logger.error(f"File processing claim failed: {e}")
            return False

    async def _release_file_processing(self, file_path: str) -> None:
        """Release file processing claim."""
        try:
            file_hash = hashlib.sha256(file_path.encode()).hexdigest()[:12]
            lock_key = f"indexing:file_lock:{file_hash}"

            await self.redis_client.delete(lock_key)
            self.processing_locks.discard(file_path)

        except Exception as e:
            logger.error(f"File processing release failed: {e}")

    # ADHD Accommodations

    async def _progress_reporter(self) -> None:
        """Background worker for ADHD progress reporting."""
        while self.running:
            try:
                if self.current_mode == IndexingMode.INITIAL and self.progress.phase != IndexingPhase.COMPLETE:
                    # Calculate progress percentage
                    if self.progress.files_total > 0:
                        progress_percent = (self.progress.files_processed / self.progress.files_total) * 100
                        eta = self._calculate_eta(self.progress.files_processed, self.progress.files_total)

                        # Store progress for UI consumption
                        progress_data = {
                            "mode": self.current_mode.value,
                            "phase": self.progress.phase.value,
                            "progress_percent": progress_percent,
                            "files_processed": self.progress.files_processed,
                            "files_total": self.progress.files_total,
                            "symbols_extracted": self.progress.symbols_extracted,
                            "eta": eta,
                            "pausable": self.progress.pausable,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }

                        await self.redis_client.setex(
                            f"indexing:progress:{self.instance_id}:{hashlib.sha256(self.workspace_id.encode()).hexdigest()[:8]}",
                            60,  # 1-minute TTL
                            json.dumps(progress_data)
                        )

                # Report every 5 seconds for ADHD responsiveness
                await asyncio.sleep(self.progress_feedback_interval)

            except Exception as e:
                logger.error(f"Progress reporting error: {e}")
                await asyncio.sleep(10)

    async def pause_indexing(self) -> Dict[str, Any]:
        """Pause indexing for ADHD break support."""
        try:
            self.paused = True
            self.current_mode = IndexingMode.PAUSED

            # Save current state
            checkpoint = await self._save_progress_checkpoint()

            return {
                "status": "paused",
                "message": "☕ Indexing paused - take your time!",
                "progress_saved": checkpoint is not None,
                "can_resume": True,
                "pause_time": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Pause indexing failed: {e}")
            return {"status": "error", "error": str(e)}

    async def resume_indexing(self) -> Dict[str, Any]:
        """Resume indexing after ADHD break."""
        try:
            self.paused = False
            self.current_mode = IndexingMode.INITIAL

            return {
                "status": "resumed",
                "message": "🚀 Welcome back! Resuming indexing...",
                "resume_time": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Resume indexing failed: {e}")
            return {"status": "error", "error": str(e)}

    # Utility Methods

    def _calculate_eta(self, processed: int, total: int) -> str:
        """Calculate estimated time to completion."""
        try:
            if processed == 0:
                return "Calculating..."

            elapsed = (datetime.now(timezone.utc) - self.progress.start_time).total_seconds()
            rate = processed / elapsed  # files per second
            remaining = total - processed
            eta_seconds = remaining / rate

            if eta_seconds < 60:
                return f"{eta_seconds:.0f} seconds"
            elif eta_seconds < 3600:
                return f"{eta_seconds / 60:.1f} minutes"
            else:
                return f"{eta_seconds / 3600:.1f} hours"

        except Exception:
            return "Unknown"

    async def _wait_for_resume(self) -> None:
        """Wait for indexing to be resumed."""
        while self.paused:
            await asyncio.sleep(1.0)

    def _generate_file_node_id(self, file_path: str) -> str:
        """Generate consistent node ID for file."""
        file_hash = hashlib.sha256(f"{self.workspace_id}:{file_path}".encode()).hexdigest()[:12]
        return f"file_{file_hash}"

    # Health and Monitoring

    async def get_pipeline_health(self) -> Dict[str, Any]:
        """Get indexing pipeline health status."""
        try:
            return {
                "status": "🚀 Active" if self.running else "⏹️ Stopped",
                "current_mode": self.current_mode.value,
                "current_phase": self.progress.phase.value if self.current_mode == IndexingMode.INITIAL else "N/A",
                "progress": {
                    "files_processed": self.progress.files_processed,
                    "files_total": self.progress.files_total,
                    "symbols_extracted": self.progress.symbols_extracted,
                    "relationships_mapped": self.progress.relationships_mapped
                },
                "workers": {
                    "active_workers": len([w for w in self.workers if not w.done()]),
                    "total_workers": len(self.workers)
                },
                "coordination": {
                    "instance_id": self.instance_id,
                    "coordination_enabled": self.coordination_enabled,
                    "active_locks": len(self.processing_locks)
                },
                "performance": {
                    "max_workers": self.max_workers,
                    "batch_size": self.batch_size,
                    "cpu_limit": f"{self.max_cpu_percent}%"
                }
            }

        except Exception as e:
            logger.error(f"Pipeline health check failed: {e}")
            return {"status": "🔴 Error", "error": str(e)}

    async def close(self) -> None:
        """Shutdown indexing pipeline gracefully."""
        logger.info("🛑 Shutting down indexing pipeline...")

        # Stop processing
        self.running = False

        # Stop file monitoring
        if self.file_observer:
            self.file_observer.stop()
            self.file_observer.join(timeout=5)

        # Cancel workers
        if self.workers:
            for worker in self.workers:
                worker.cancel()
            await asyncio.gather(*self.workers, return_exceptions=True)

        # Release all locks
        for file_path in list(self.processing_locks):
            await self._release_file_processing(file_path)

        # Close connections
        if self.redis_client:
            await self.redis_client.close()

        logger.info("✅ Indexing pipeline shutdown complete")

    # Placeholder methods for full implementation
    async def _build_complete_graph(self, analysis_results: Dict) -> Dict[str, Any]:
        """Build complete relationship graph."""
        return {"nodes": 0, "relationships": 0}

    async def _warm_navigation_cache(self, analysis_results: Dict) -> Dict[str, Any]:
        """Warm navigation cache with frequently accessed symbols."""
        return {"cache_entries": 0}

    async def _save_progress_checkpoint(self) -> bool:
        """Save progress checkpoint for resumability."""
        return True

    async def _load_indexing_checkpoint(self) -> Optional[Dict]:
        """Load previous indexing checkpoint."""
        return None

    async def _store_completion_checkpoint(self, stats: Dict) -> None:
        """Store completion checkpoint."""
        pass

    async def _store_error_checkpoint(self, error: str) -> None:
        """Store error checkpoint."""
        pass

    def _count_progress_updates(self) -> int:
        """Count progress updates sent."""
        return 0

    async def _handle_file_deletion(self, change_event: FileChangeEvent) -> None:
        """Handle file deletion."""
        pass

    async def _handle_file_modification(self, change_event: FileChangeEvent) -> None:
        """Handle file modification."""
        pass

    async def _update_graph_incrementally(self, change_event: FileChangeEvent) -> None:
        """Update graph incrementally."""
        pass

    async def _invalidate_affected_cache(self, change_event: FileChangeEvent) -> None:
        """Invalidate affected cache entries."""
        pass

    async def _notify_claude_context_changes(self, change_event: FileChangeEvent) -> None:
        """Notify claude-context of changes."""
        pass

    async def _claim_change_processing(self, change_event: FileChangeEvent) -> bool:
        """Claim change processing."""
        return True

    async def _release_change_processing(self, change_event: FileChangeEvent) -> None:
        """Release change processing."""
        pass

    async def _coordination_worker(self) -> None:
        """Background coordination worker."""
        while self.running:
            await asyncio.sleep(10)


class FileChangeHandler(events.FileSystemEventHandler):
    """File system event handler for incremental indexing."""

    def __init__(self, change_queue: asyncio.Queue, workspace_path: Path):
        self.change_queue = change_queue
        self.workspace_path = workspace_path
        self.last_events: Dict[str, datetime] = {}
        self.debounce_delay = 0.5  # seconds

    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and self._should_process_file(event.src_path):
            self._queue_change_event(event.src_path, "modified")

    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory and self._should_process_file(event.src_path):
            self._queue_change_event(event.src_path, "created")

    def on_deleted(self, event):
        """Handle file deletion events."""
        if not event.is_directory and self._should_process_file(event.src_path):
            self._queue_change_event(event.src_path, "deleted")

    def _should_process_file(self, file_path: str) -> bool:
        """Check if file should be processed."""
        try:
            path = Path(file_path)

            # Check extension
            code_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.rs', '.go', '.java'}
            if path.suffix.lower() not in code_extensions:
                return False

            # Check exclude patterns
            exclude_patterns = {'__pycache__', '.git', 'node_modules', 'build', 'dist'}
            if any(pattern in str(path) for pattern in exclude_patterns):
                return False

            # Debounce rapid changes
            now = datetime.now()
            if file_path in self.last_events:
                if (now - self.last_events[file_path]).total_seconds() < self.debounce_delay:
                    return False

            self.last_events[file_path] = now
            return True

        except Exception:
            return False

    def _queue_change_event(self, file_path: str, change_type: str) -> None:
        """Queue file change event for processing."""
        try:
            change_event = FileChangeEvent(
                file_path=file_path,
                change_type=change_type,
                timestamp=datetime.now(timezone.utc),
                workspace_id=str(self.workspace_path)
            )

            # Queue for processing (non-blocking)
            try:
                self.change_queue.put_nowait(change_event)
            except asyncio.QueueFull:
                logger.warning("Change queue full - dropping oldest events")

        except Exception as e:
            logger.error(f"Failed to queue change event: {e}")


# Factory function
async def create_indexing_pipeline(
    workspace_path: Path,
    instance_id: str = "default",
    redis_url: str = "redis://localhost:6379"
) -> SerenaIndexingPipeline:
    """Create and initialize indexing pipeline."""
    pipeline = SerenaIndexingPipeline(workspace_path, instance_id, redis_url)
    await pipeline.initialize()
    return pipeline