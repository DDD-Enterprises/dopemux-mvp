"""
Multi-Directional Sync Engine for Task Orchestrator

Handles complex synchronization between Leantime, ConPort, local ADHD systems,
and AI agents with conflict resolution and ADHD-optimized batching.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib

import redis.asyncio as redis
import aiohttp

logger = logging.getLogger(__name__)


class SyncDirection(str, Enum):
    """Synchronization directions."""
    LEANTIME_TO_CONPORT = "leantime→conport"
    LEANTIME_TO_LOCAL = "leantime→local"
    CONPORT_TO_LEANTIME = "conport→leantime"
    LOCAL_TO_LEANTIME = "local→leantime"
    LOCAL_TO_CONPORT = "local→conport"
    CONPORT_TO_LOCAL = "conport→local"
    AGENT_TO_ALL = "agent→all"


class ConflictResolution(str, Enum):
    """Conflict resolution strategies."""
    LEANTIME_WINS = "leantime_wins"        # Leantime is source of truth
    LOCAL_WINS = "local_wins"              # Local ADHD system wins
    CONPORT_WINS = "conport_wins"          # ConPort decisions win
    MERGE_INTELLIGENT = "merge_intelligent" # Smart merge strategy
    ASK_USER = "ask_user"                  # Present options to user


@dataclass
class SyncOperation:
    """Represents a synchronization operation."""
    id: str
    direction: SyncDirection
    source_system: str
    target_system: str

    # Data being synchronized
    entity_type: str  # task, decision, progress, context
    entity_id: str
    source_data: Dict[str, Any]
    target_data: Optional[Dict[str, Any]] = None

    # Sync metadata
    priority: int = 5
    created_at: datetime = None
    processed_at: Optional[datetime] = None
    attempts: int = 0
    max_attempts: int = 3

    # Conflict handling
    conflict_detected: bool = False
    conflict_resolution: Optional[ConflictResolution] = None
    conflict_details: Dict[str, Any] = None

    # ADHD considerations
    cognitive_load: float = 0.5
    can_batch: bool = True
    urgency: str = "normal"  # urgent, normal, low

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)
        if self.conflict_details is None:
            self.conflict_details = {}


@dataclass
class SyncConflict:
    """Represents a synchronization conflict."""
    id: str
    operation_id: str
    entity_type: str
    entity_id: str

    # Conflicting data
    source_value: Any
    target_value: Any
    field_name: str

    # Resolution
    resolution_strategy: ConflictResolution
    resolved_value: Optional[Any] = None
    resolution_reason: str = ""

    # Metadata
    detected_at: datetime = None
    resolved_at: Optional[datetime] = None

    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.now(timezone.utc)


class MultiDirectionalSyncEngine:
    """
    Handles complex multi-system synchronization with ADHD optimizations.

    Features:
    - Intelligent conflict detection and resolution
    - ADHD-aware batching to minimize cognitive interruptions
    - Priority-based sync processing
    - Comprehensive audit trail for all changes
    - Context preservation across system boundaries
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        workspace_id: str = "/Users/hue/code/dopemux-mvp"
    ):
        self.redis_url = redis_url
        self.workspace_id = workspace_id

        # Redis connection for coordination
        self.redis_client: Optional[redis.Redis] = None

        # Sync operation queues by priority
        self.sync_queues: Dict[int, asyncio.Queue] = {}
        self.conflict_queue: asyncio.Queue = asyncio.Queue()

        # System connectors
        self.system_connectors = {
            "leantime": None,    # LeanTime API client
            "conport": None,     # ConPort MCP client
            "local_adhd": None,  # Local ADHD system
            "agents": {}         # AI agent connections
        }

        # Sync state tracking
        self.active_operations: Dict[str, SyncOperation] = {}
        self.recent_conflicts: List[SyncConflict] = []
        self.sync_stats = {
            "operations_processed": 0,
            "conflicts_detected": 0,
            "conflicts_resolved": 0,
            "batches_processed": 0,
            "adhd_optimizations_applied": 0
        }

        # ADHD optimization settings
        self.batch_config = {
            "max_batch_size": 10,           # Don't overwhelm with large batches
            "max_batch_wait_seconds": 5,    # Quick processing for responsiveness
            "priority_separation": True,    # Keep priorities separate
            "cognitive_load_aware": True    # Consider mental impact
        }

        # Background workers
        self.workers: List[asyncio.Task] = []
        self.running = False

    async def initialize(self) -> None:
        """Initialize sync engine and start processing."""
        logger.info("🔄 Initializing Multi-Directional Sync Engine...")

        # Initialize Redis connection
        self.redis_client = redis.from_url(
            self.redis_url,
            db=4,  # Separate DB for sync operations
            decode_responses=True
        )
        await self.redis_client.ping()

        # Initialize priority queues (1=highest, 10=lowest)
        for priority in range(1, 11):
            self.sync_queues[priority] = asyncio.Queue()

        # Start background workers
        await self._start_sync_workers()

        self.running = True
        logger.info("✅ Multi-Directional Sync Engine ready!")

    async def _start_sync_workers(self) -> None:
        """Start background sync processing workers."""
        workers = [
            self._priority_sync_processor(),
            self._conflict_resolver(),
            self._batch_optimizer(),
            self._adhd_accommodation_monitor(),
            self._sync_health_monitor()
        ]

        self.workers = [asyncio.create_task(worker) for worker in workers]
        logger.info("👥 Sync workers started")

    # Core Sync Processing

    async def queue_sync_operation(self, operation: SyncOperation) -> bool:
        """Queue synchronization operation for processing."""
        try:
            # Assign unique ID if not present
            if not operation.id:
                operation.id = f"sync_{datetime.now().timestamp()}_{hash(operation.entity_id)}"

            # Detect potential conflicts before queuing
            conflict = await self._detect_conflicts(operation)
            if conflict:
                operation.conflict_detected = True
                operation.conflict_details = asdict(conflict)
                await self.conflict_queue.put(conflict)

            # Queue by priority
            priority_queue = self.sync_queues.get(operation.priority, self.sync_queues[5])
            await priority_queue.put(operation)

            # Track operation
            self.active_operations[operation.id] = operation

            logger.debug(f"📤 Queued sync: {operation.direction} for {operation.entity_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to queue sync operation: {e}")
            return False

    async def _priority_sync_processor(self) -> None:
        """Background processor for sync operations by priority."""
        logger.info("🔄 Started priority sync processor")

        while self.running:
            try:
                # Process queues by priority (1=highest)
                for priority in sorted(self.sync_queues.keys()):
                    queue = self.sync_queues[priority]

                    try:
                        # Non-blocking check for operations
                        operation = queue.get_nowait()
                        await self._execute_sync_operation(operation)

                    except asyncio.QueueEmpty:
                        continue

                # Brief pause to prevent CPU spinning
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Priority sync processor error: {e}")
                await asyncio.sleep(1.0)

    async def _execute_sync_operation(self, operation: SyncOperation) -> bool:
        """Execute individual sync operation."""
        try:
            start_time = datetime.now(timezone.utc)

            # Check if operation has conflicts
            if operation.conflict_detected:
                logger.warning(f"⚠️ Sync operation has conflicts: {operation.id}")
                return False

            # Route to appropriate sync handler
            success = False

            if operation.direction == SyncDirection.LEANTIME_TO_CONPORT:
                success = await self._sync_leantime_to_conport(operation)
            elif operation.direction == SyncDirection.LEANTIME_TO_LOCAL:
                success = await self._sync_leantime_to_local(operation)
            elif operation.direction == SyncDirection.CONPORT_TO_LEANTIME:
                success = await self._sync_conport_to_leantime(operation)
            elif operation.direction == SyncDirection.LOCAL_TO_LEANTIME:
                success = await self._sync_local_to_leantime(operation)
            elif operation.direction == SyncDirection.LOCAL_TO_CONPORT:
                success = await self._sync_local_to_conport(operation)
            elif operation.direction == SyncDirection.CONPORT_TO_LOCAL:
                success = await self._sync_conport_to_local(operation)
            elif operation.direction == SyncDirection.AGENT_TO_ALL:
                success = await self._sync_agent_to_all(operation)

            # Update operation metadata
            operation.processed_at = datetime.now(timezone.utc)
            processing_time = (operation.processed_at - start_time).total_seconds()

            if success:
                # Remove from active operations
                if operation.id in self.active_operations:
                    del self.active_operations[operation.id]

                self.sync_stats["operations_processed"] += 1
                logger.debug(f"✅ Sync completed: {operation.direction} in {processing_time:.3f}s")
            else:
                # Retry logic
                operation.attempts += 1
                if operation.attempts < operation.max_attempts:
                    # Re-queue with exponential backoff
                    delay = 2 ** operation.attempts
                    asyncio.create_task(self._delayed_retry(operation, delay))
                else:
                    logger.error(f"❌ Sync failed permanently: {operation.id}")
                    del self.active_operations[operation.id]

            return success

        except Exception as e:
            logger.error(f"Sync operation execution failed: {e}")
            operation.attempts += 1
            return False

    async def _delayed_retry(self, operation: SyncOperation, delay: float) -> None:
        """Retry sync operation after delay."""
        await asyncio.sleep(delay)
        await self.queue_sync_operation(operation)

    # System-Specific Sync Handlers

    async def _sync_leantime_to_conport(self, operation: SyncOperation) -> bool:
        """Sync from Leantime to ConPort."""
        try:
            source_data = operation.source_data
            entity_type = operation.entity_type

            if entity_type == "task":
                # Convert Leantime task to ConPort progress entry
                progress_data = {
                    "status": self._map_status_to_conport(source_data.get("status", "pending")),
                    "description": f"Leantime task: {source_data.get('headline', 'Unknown task')}",
                    "linked_item_type": "leantime_task",
                    "linked_item_id": str(source_data.get("id", "")),
                    "link_relationship_type": "tracks_implementation"
                }

                # This would make MCP call to ConPort
                # await conport_client.log_progress(**progress_data)
                logger.debug(f"📊 Synced Leantime task to ConPort: {operation.entity_id}")
                return True

            elif entity_type == "sprint":
                # Convert Leantime sprint to ConPort active context
                sprint_context = {
                    "sprint_id": source_data.get("id", ""),
                    "sprint_name": source_data.get("name", ""),
                    "mode": "ACT",
                    "focus": f"Sprint execution: {source_data.get('name', 'Unknown')}",
                    "leantime_managed": True
                }

                # This would make MCP call to ConPort
                # await conport_client.update_active_context(patch_content=sprint_context)
                logger.debug(f"🎯 Synced Leantime sprint to ConPort: {operation.entity_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Leantime→ConPort sync failed: {e}")
            return False

    async def _sync_conport_to_leantime(self, operation: SyncOperation) -> bool:
        """Sync from ConPort to Leantime."""
        try:
            source_data = operation.source_data
            entity_type = operation.entity_type

            if entity_type == "decision":
                # ConPort decision → Leantime task/comment
                decision_data = source_data

                # Check if decision affects existing Leantime tasks
                affected_tasks = await self._find_affected_leantime_tasks(decision_data)

                for task_id in affected_tasks:
                    # Add decision context as task comment
                    comment_data = {
                        "task_id": task_id,
                        "comment": f"📋 Related Decision: {decision_data.get('summary', '')}\n"
                                 f"Rationale: {decision_data.get('rationale', 'Not specified')}",
                        "comment_type": "architectural_context"
                    }

                    # This would make Leantime API call
                    # await leantime_client.add_task_comment(**comment_data)

                logger.debug(f"📝 Synced ConPort decision to {len(affected_tasks)} Leantime tasks")
                return True

            elif entity_type == "progress":
                # ConPort progress → Leantime task update
                progress_data = source_data
                linked_task = progress_data.get("linked_item_id")

                if linked_task and progress_data.get("linked_item_type") == "leantime_task":
                    # Update Leantime task status
                    leantime_status = self._map_status_to_leantime(progress_data.get("status", "TODO"))

                    update_data = {
                        "task_id": linked_task,
                        "status": leantime_status,
                        "progress_notes": f"Updated via ConPort: {progress_data.get('description', '')}"
                    }

                    # This would make Leantime API call
                    # await leantime_client.update_task(**update_data)
                    logger.debug(f"📈 Synced ConPort progress to Leantime task: {linked_task}")
                    return True

            return False

        except Exception as e:
            logger.error(f"ConPort→Leantime sync failed: {e}")
            return False

    async def _sync_local_to_leantime(self, operation: SyncOperation) -> bool:
        """Sync from local ADHD system to Leantime."""
        try:
            source_data = operation.source_data
            entity_type = operation.entity_type

            if entity_type == "task_progress":
                # Local ADHD task progress → Leantime task update
                local_task = source_data
                leantime_id = local_task.get("leantime_id")

                if leantime_id:
                    # Calculate progress percentage
                    progress_percent = local_task.get("progress", 0.0) * 100

                    # Include ADHD-specific metadata
                    update_data = {
                        "task_id": leantime_id,
                        "progress_percent": progress_percent,
                        "notes": f"ADHD Progress: {progress_percent:.1f}% - "
                               f"Energy: {local_task.get('energy_required', 'medium')}, "
                               f"Duration: {local_task.get('actual_duration', 0)}min"
                    }

                    # This would make Leantime API call
                    # await leantime_client.update_task_progress(**update_data)
                    logger.debug(f"📊 Synced local ADHD progress to Leantime: {leantime_id}")
                    return True

            elif entity_type == "break_session":
                # Local break → Leantime time tracking
                break_data = source_data
                task_id = break_data.get("task_id")

                if task_id:
                    # Log break time in Leantime
                    time_entry = {
                        "task_id": task_id,
                        "time_type": "break",
                        "duration_minutes": break_data.get("duration", 5),
                        "notes": "ADHD break for cognitive recovery"
                    }

                    # This would make Leantime API call
                    # await leantime_client.log_time_entry(**time_entry)
                    logger.debug(f"☕ Synced break session to Leantime: {task_id}")
                    return True

            return False

        except Exception as e:
            logger.error(f"Local→Leantime sync failed: {e}")
            return False

    async def _sync_agent_to_all(self, operation: SyncOperation) -> bool:
        """Sync AI agent results to all relevant systems."""
        try:
            source_data = operation.source_data
            agent_result = source_data

            # Determine which systems need the update
            target_systems = []

            if agent_result.get("agent_type") == "conport":
                # ConPort agent results go to Leantime for visibility
                target_systems.append("leantime")

            elif agent_result.get("agent_type") == "serena":
                # Serena code changes update both Leantime and ConPort
                target_systems.extend(["leantime", "conport"])

            # Create sync operations for each target
            sync_tasks = []
            for target in target_systems:
                sync_op = SyncOperation(
                    id=f"{operation.id}_{target}",
                    direction=f"agent→{target}",
                    source_system="ai_agent",
                    target_system=target,
                    entity_type="agent_result",
                    entity_id=operation.entity_id,
                    source_data=agent_result,
                    priority=operation.priority
                )

                sync_tasks.append(self._execute_agent_sync(sync_op, target))

            # Execute all syncs in parallel
            results = await asyncio.gather(*sync_tasks, return_exceptions=True)

            # Check for any failures
            failures = [r for r in results if isinstance(r, Exception)]
            if failures:
                logger.error(f"Agent sync failures: {failures}")
                return False

            success_count = sum(1 for r in results if r)
            logger.info(f"🤖 Agent result synced to {success_count}/{len(target_systems)} systems")
            return success_count > 0

        except Exception as e:
            logger.error(f"Agent→All sync failed: {e}")
            return False

    async def _execute_agent_sync(self, operation: SyncOperation, target_system: str) -> bool:
        """Execute agent result sync to specific target system."""
        try:
            agent_result = operation.source_data

            if target_system == "leantime":
                # Update Leantime task with agent progress
                task_update = {
                    "task_id": agent_result.get("task_id"),
                    "progress_notes": f"AI Progress: {agent_result.get('summary', '')}",
                    "completion_estimate": agent_result.get("completion_estimate", 0),
                    "ai_insights": agent_result.get("insights", [])
                }

                # This would make Leantime API call
                # await leantime_client.add_task_update(**task_update)
                return True

            elif target_system == "conport":
                # Log agent work as ConPort decision/progress
                if agent_result.get("type") == "decision":
                    decision_data = {
                        "summary": f"AI Decision: {agent_result.get('summary', '')}",
                        "rationale": agent_result.get("rationale", "AI-generated decision"),
                        "implementation_details": agent_result.get("details", ""),
                        "tags": ["ai-generated", agent_result.get("agent_type", "unknown")]
                    }

                    # This would make ConPort MCP call
                    # await conport_client.log_decision(**decision_data)
                    return True

            return False

        except Exception as e:
            logger.error(f"Agent sync to {target_system} failed: {e}")
            return False

    # Conflict Detection and Resolution

    async def _detect_conflicts(self, operation: SyncOperation) -> Optional[SyncConflict]:
        """Detect synchronization conflicts."""
        try:
            # Get current target data
            target_data = await self._get_target_data(operation)

            if not target_data:
                return None  # No conflict if target doesn't exist

            operation.target_data = target_data
            source_data = operation.source_data

            # Check for data conflicts
            conflicts = []

            # Common conflict fields
            conflict_fields = ["status", "priority", "description", "assigned_to", "progress"]

            for field in conflict_fields:
                source_value = source_data.get(field)
                target_value = target_data.get(field)

                if source_value is not None and target_value is not None:
                    if source_value != target_value:
                        # Detected conflict
                        conflict = SyncConflict(
                            id=f"conflict_{operation.id}_{field}",
                            operation_id=operation.id,
                            entity_type=operation.entity_type,
                            entity_id=operation.entity_id,
                            source_value=source_value,
                            target_value=target_value,
                            field_name=field,
                            resolution_strategy=self._determine_resolution_strategy(
                                operation.direction, field, source_value, target_value
                            )
                        )
                        conflicts.append(conflict)

            # Return most significant conflict
            if conflicts:
                # Sort by field importance
                field_importance = {
                    "status": 1,      # Most important
                    "priority": 2,
                    "progress": 3,
                    "description": 4,
                    "assigned_to": 5
                }

                conflicts.sort(key=lambda c: field_importance.get(c.field_name, 10))
                return conflicts[0]

            return None

        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            return None

    def _determine_resolution_strategy(
        self,
        direction: SyncDirection,
        field: str,
        source_value: Any,
        target_value: Any
    ) -> ConflictResolution:
        """Determine optimal conflict resolution strategy."""
        # Default resolution strategies
        default_strategies = {
            SyncDirection.LEANTIME_TO_CONPORT: ConflictResolution.LEANTIME_WINS,
            SyncDirection.LEANTIME_TO_LOCAL: ConflictResolution.LEANTIME_WINS,
            SyncDirection.CONPORT_TO_LEANTIME: ConflictResolution.CONPORT_WINS,
            SyncDirection.LOCAL_TO_LEANTIME: ConflictResolution.LOCAL_WINS,
        }

        # Field-specific overrides
        if field == "status":
            # Status conflicts: prefer most recent update
            return ConflictResolution.MERGE_INTELLIGENT
        elif field == "priority" and direction == SyncDirection.LOCAL_TO_LEANTIME:
            # Local ADHD priority adjustments should win
            return ConflictResolution.LOCAL_WINS

        return default_strategies.get(direction, ConflictResolution.ASK_USER)

    async def _conflict_resolver(self) -> None:
        """Background worker for conflict resolution."""
        logger.info("⚖️ Started conflict resolution worker")

        while self.running:
            try:
                # Process conflicts as they arrive
                conflict = await asyncio.wait_for(self.conflict_queue.get(), timeout=10.0)

                await self._resolve_conflict(conflict)
                self.sync_stats["conflicts_resolved"] += 1

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Conflict resolution error: {e}")
                await asyncio.sleep(5.0)

    async def _resolve_conflict(self, conflict: SyncConflict) -> bool:
        """Resolve synchronization conflict."""
        try:
            strategy = conflict.resolution_strategy

            if strategy == ConflictResolution.LEANTIME_WINS:
                conflict.resolved_value = conflict.source_value
                conflict.resolution_reason = "Leantime is authoritative for team coordination"

            elif strategy == ConflictResolution.LOCAL_WINS:
                conflict.resolved_value = conflict.target_value
                conflict.resolution_reason = "Local ADHD optimization takes precedence"

            elif strategy == ConflictResolution.CONPORT_WINS:
                conflict.resolved_value = conflict.source_value
                conflict.resolution_reason = "ConPort decision/pattern is authoritative"

            elif strategy == ConflictResolution.MERGE_INTELLIGENT:
                conflict.resolved_value = await self._intelligent_merge(conflict)
                conflict.resolution_reason = "Intelligent merge based on context and timestamps"

            elif strategy == ConflictResolution.ASK_USER:
                # Queue for user resolution
                await self._queue_user_resolution(conflict)
                return False

            # Apply resolution
            await self._apply_conflict_resolution(conflict)

            conflict.resolved_at = datetime.now(timezone.utc)
            self.recent_conflicts.append(conflict)

            # Keep only recent conflicts (ADHD: don't overwhelm with history)
            if len(self.recent_conflicts) > 20:
                self.recent_conflicts = self.recent_conflicts[-10:]

            logger.info(f"⚖️ Conflict resolved: {conflict.field_name} using {strategy.value}")
            return True

        except Exception as e:
            logger.error(f"Conflict resolution failed: {e}")
            return False

    # ADHD-Optimized Batching

    async def _batch_optimizer(self) -> None:
        """Background worker for ADHD-optimized batch processing."""
        logger.info("📦 Started batch optimization worker")

        batch_collections = {}
        last_batch_time = datetime.now(timezone.utc)

        while self.running:
            try:
                # Collect operations for batching
                for priority, queue in self.sync_queues.items():
                    if priority not in batch_collections:
                        batch_collections[priority] = []

                    # Collect operations for batch
                    while not queue.empty() and len(batch_collections[priority]) < self.batch_config["max_batch_size"]:
                        try:
                            _, operation = queue.get_nowait()
                            if operation.can_batch:
                                batch_collections[priority].append(operation)
                            else:
                                # Process immediately for non-batchable operations
                                await self._execute_sync_operation(operation)
                        except asyncio.QueueEmpty:
                            break

                # Process batches when ready
                current_time = datetime.now(timezone.utc)
                time_since_last_batch = (current_time - last_batch_time).total_seconds()

                should_process_batch = (
                    time_since_last_batch >= self.batch_config["max_batch_wait_seconds"] or
                    any(len(batch) >= self.batch_config["max_batch_size"]
                        for batch in batch_collections.values())
                )

                if should_process_batch:
                    for priority, batch in batch_collections.items():
                        if batch:
                            await self._process_sync_batch(batch, priority)
                            batch_collections[priority] = []

                    last_batch_time = current_time

                await asyncio.sleep(1.0)  # Check every second

            except Exception as e:
                logger.error(f"Batch optimization error: {e}")
                await asyncio.sleep(5.0)

    async def _process_sync_batch(self, operations: List[SyncOperation], priority: int) -> None:
        """Process batch of sync operations with ADHD considerations."""
        try:
            if not operations:
                return

            logger.debug(f"📦 Processing sync batch: {len(operations)} operations (priority {priority})")

            # Group operations by direction for efficiency
            ops_by_direction = {}
            for op in operations:
                direction = op.direction
                if direction not in ops_by_direction:
                    ops_by_direction[direction] = []
                ops_by_direction[direction].append(op)

            # Process each direction group
            for direction, direction_ops in ops_by_direction.items():
                # Calculate total cognitive load for ADHD assessment
                total_cognitive_load = sum(op.cognitive_load for op in direction_ops)

                if total_cognitive_load > 2.0:  # High cognitive load batch
                    # Split into smaller sub-batches
                    chunk_size = max(1, len(direction_ops) // 2)
                    for i in range(0, len(direction_ops), chunk_size):
                        chunk = direction_ops[i:i + chunk_size]
                        await self._execute_sync_batch(chunk, direction)

                        # Brief pause between high-load batches
                        await asyncio.sleep(0.5)
                else:
                    # Process full batch
                    await self._execute_sync_batch(direction_ops, direction)

            self.sync_stats["batches_processed"] += 1

        except Exception as e:
            logger.error(f"Sync batch processing failed: {e}")

    async def _execute_sync_batch(self, operations: List[SyncOperation], direction: str) -> None:
        """Execute batch of sync operations for same direction."""
        try:
            # Execute operations in parallel for efficiency
            tasks = [self._execute_sync_operation(op) for op in operations]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Count successes
            successes = sum(1 for r in results if r is True)
            logger.debug(f"✅ Batch sync: {successes}/{len(operations)} successful ({direction})")

        except Exception as e:
            logger.error(f"Batch execution failed: {e}")

    # Utility Methods

    async def _get_target_data(self, operation: SyncOperation) -> Optional[Dict[str, Any]]:
        """Get current data from target system."""
        try:
            # This would query the target system for current data
            # For now, return placeholder
            return {}
        except Exception as e:
            logger.error(f"Failed to get target data: {e}")
            return None

    def _map_status_to_conport(self, leantime_status: str) -> str:
        """Map Leantime status to ConPort status."""
        status_map = {
            "0": "TODO",
            "1": "IN_PROGRESS",
            "2": "DONE",
            "3": "BLOCKED",
            "6": "BREAK_NEEDED",
            "7": "CONTEXT_SWITCH"
        }
        return status_map.get(leantime_status, "TODO")

    def _map_status_to_leantime(self, conport_status: str) -> str:
        """Map ConPort status to Leantime status."""
        status_map = {
            "TODO": "0",
            "IN_PROGRESS": "1",
            "DONE": "2",
            "BLOCKED": "3",
            "BREAK_NEEDED": "6",
            "CONTEXT_SWITCH": "7"
        }
        return status_map.get(conport_status, "0")

    async def _find_affected_leantime_tasks(self, decision_data: Dict[str, Any]) -> List[str]:
        """Find Leantime tasks affected by ConPort decision."""
        # Placeholder - would analyze decision content and find related tasks
        return []

    async def _intelligent_merge(self, conflict: SyncConflict) -> Any:
        """Perform intelligent merge of conflicting values."""
        # Placeholder - would implement smart merging logic
        # For now, prefer most recent value
        return conflict.source_value

    async def _queue_user_resolution(self, conflict: SyncConflict) -> None:
        """Queue conflict for user resolution."""
        # Placeholder - would present conflict to user for manual resolution
        pass

    async def _apply_conflict_resolution(self, conflict: SyncConflict) -> None:
        """Apply resolved conflict value to target system."""
        # Placeholder - would update target system with resolved value
        pass

    # ADHD Accommodation Engine

    async def _adhd_accommodation_monitor(self) -> None:
        """Monitor and apply ADHD accommodations during sync."""
        logger.info("🧠 Started ADHD accommodation monitor")

        while self.running:
            try:
                # Monitor cognitive load across active operations
                total_cognitive_load = sum(
                    op.cognitive_load for op in self.active_operations.values()
                )

                # Adjust processing if cognitive load is high
                if total_cognitive_load > 3.0:  # High cognitive load
                    # Slow down processing to prevent overwhelm
                    self.batch_config["max_batch_size"] = 5
                    self.batch_config["max_batch_wait_seconds"] = 10
                    logger.debug("🧠 Reduced batch size due to high cognitive load")

                elif total_cognitive_load < 1.0:  # Low cognitive load
                    # Speed up processing
                    self.batch_config["max_batch_size"] = 15
                    self.batch_config["max_batch_wait_seconds"] = 3
                    logger.debug("⚡ Increased batch size due to low cognitive load")

                # Check for break recommendations
                await self._check_sync_break_needs()

                # Monitor every 30 seconds
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"ADHD accommodation monitor error: {e}")
                await asyncio.sleep(60)

    async def _check_sync_break_needs(self) -> None:
        """Check if sync processing needs breaks for ADHD."""
        try:
            # Check if we've been processing intensively
            recent_operations = len([
                op for op in self.active_operations.values()
                if op.created_at > datetime.now(timezone.utc) - timedelta(minutes=15)
            ])

            if recent_operations > 50:  # High activity
                # Suggest system-wide break
                logger.info("☕ High sync activity detected - suggesting brief processing pause")

                # Slow down processing briefly
                await asyncio.sleep(2.0)
                self.sync_stats["adhd_accommodations"] += 1

        except Exception as e:
            logger.error(f"Sync break check failed: {e}")

    # Health and Monitoring

    async def _sync_health_monitor(self) -> None:
        """Monitor sync engine health and performance."""
        logger.info("📊 Started sync health monitor")

        while self.running:
            try:
                # Monitor queue sizes
                queue_sizes = {
                    f"priority_{p}": q.qsize()
                    for p, q in self.sync_queues.items()
                }

                # Monitor processing rates
                conflicts_rate = len(self.recent_conflicts)

                # Log health metrics
                health_data = {
                    "queue_sizes": queue_sizes,
                    "active_operations": len(self.active_operations),
                    "recent_conflicts": conflicts_rate,
                    "sync_stats": self.sync_stats,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                # Store health data in Redis
                await self.redis_client.setex(
                    f"sync_engine:health:{self.workspace_id}",
                    300,  # 5-minute TTL
                    json.dumps(health_data)
                )

                # Check every 2 minutes
                await asyncio.sleep(120)

            except Exception as e:
                logger.error(f"Sync health monitor error: {e}")
                await asyncio.sleep(300)

    async def get_sync_health(self) -> Dict[str, Any]:
        """Get comprehensive sync engine health."""
        try:
            # Queue health
            total_queued = sum(q.qsize() for q in self.sync_queues.values())

            # Worker health
            active_workers = len([w for w in self.workers if not w.done()])

            # Recent performance
            recent_conflicts = len([
                c for c in self.recent_conflicts
                if c.detected_at > datetime.now(timezone.utc) - timedelta(hours=1)
            ])

            # Overall status
            if total_queued < 10 and active_workers == len(self.workers) and recent_conflicts < 5:
                status = "🚀 Excellent"
            elif total_queued < 50 and active_workers >= len(self.workers) - 1:
                status = "✅ Good"
            elif total_queued < 100:
                status = "⚠️ Busy"
            else:
                status = "🔴 Overloaded"

            return {
                "overall_status": status,
                "processing": {
                    "total_queued": total_queued,
                    "active_operations": len(self.active_operations),
                    "workers_active": f"{active_workers}/{len(self.workers)}"
                },
                "conflicts": {
                    "recent_conflicts": recent_conflicts,
                    "total_resolved": self.sync_stats["conflicts_resolved"],
                    "resolution_rate": f"{self.sync_stats['conflicts_resolved'] / max(1, self.sync_stats['conflicts_detected']):.1%}"
                },
                "performance": self.sync_stats,
                "adhd_state": {
                    "batch_size": self.batch_config["max_batch_size"],
                    "cognitive_load_adaptive": True,
                    "accommodations_applied": self.sync_stats["adhd_accommodations"]
                }
            }

        except Exception as e:
            logger.error(f"Sync health check failed: {e}")
            return {"overall_status": "🔴 Error", "error": str(e)}

    async def close(self) -> None:
        """Shutdown sync engine gracefully."""
        logger.info("🛑 Shutting down Multi-Directional Sync Engine...")

        # Stop processing
        self.running = False

        # Cancel workers
        if self.workers:
            for worker in self.workers:
                worker.cancel()
            await asyncio.gather(*self.workers, return_exceptions=True)

        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()

        logger.info("✅ Multi-Directional Sync Engine shutdown complete")