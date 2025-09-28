"""
Enhanced Task Orchestrator - Intelligent Middleware for PM Automation

Coordinates between Leantime PM interface and AI agents with implicit automation.
Provides seamless ADHD-optimized development workflow orchestration.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum

import aiohttp
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Enhanced task status with ADHD considerations."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    NEEDS_BREAK = "needs_break"
    CONTEXT_SWITCH = "context_switch"
    PAUSED = "paused"


class AgentType(str, Enum):
    """AI agent types for task coordination."""
    CONPORT = "conport"
    SERENA = "serena"
    TASKMASTER = "taskmaster"
    CLAUDE_FLOW = "claude_flow"
    ZEN = "zen"


@dataclass
class OrchestrationTask:
    """Enhanced task representation for orchestration."""
    id: str
    leantime_id: Optional[int] = None
    title: str = ""
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 1
    complexity_score: float = 0.5
    estimated_minutes: int = 25
    assigned_agent: Optional[AgentType] = None

    # ADHD-specific fields
    energy_required: str = "medium"  # low, medium, high
    cognitive_load: float = 0.5  # 0.0-1.0
    context_switches_allowed: int = 2
    break_frequency_minutes: int = 25

    # Orchestration metadata
    dependencies: List[str] = None
    dependents: List[str] = None
    agent_assignments: Dict[str, str] = None
    progress_checkpoints: List[Dict] = None

    # Sync tracking
    last_synced: Optional[datetime] = None
    sync_conflicts: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.dependents is None:
            self.dependents = []
        if self.agent_assignments is None:
            self.agent_assignments = {}
        if self.progress_checkpoints is None:
            self.progress_checkpoints = []
        if self.sync_conflicts is None:
            self.sync_conflicts = []


@dataclass
class SyncEvent:
    """Event for multi-directional synchronization."""
    source_system: str
    target_systems: List[str]
    event_type: str
    task_id: str
    data: Dict[str, Any]
    timestamp: datetime
    adhd_metadata: Dict[str, Any]


class EnhancedTaskOrchestrator:
    """
    Intelligent middleware for PM automation and AI agent coordination.

    Features:
    - Leantime integration with real-time polling
    - Multi-directional sync between all PM systems
    - Event-driven AI agent coordination
    - Implicit automation for sprints, retros, progress tracking
    - ADHD accommodations at every coordination point
    """

    def __init__(
        self,
        leantime_url: str,
        leantime_token: str,
        redis_url: str = "redis://localhost:6379",
        workspace_id: str = "/Users/hue/code/dopemux-mvp"
    ):
        self.leantime_url = leantime_url.rstrip('/')
        self.leantime_token = leantime_token
        self.redis_url = redis_url
        self.workspace_id = workspace_id

        # Component connections
        self.leantime_session: Optional[aiohttp.ClientSession] = None
        self.redis_client: Optional[redis.Redis] = None

        # Task coordination state
        self.orchestrated_tasks: Dict[str, OrchestrationTask] = {}
        self.agent_pool: Dict[AgentType, Dict[str, Any]] = {}
        self.sync_queue: asyncio.Queue = asyncio.Queue()

        # ADHD optimization settings
        self.adhd_config = {
            "max_concurrent_tasks": 3,
            "break_enforcement": True,
            "context_switch_penalty": 0.3,
            "energy_level_matching": True,
            "implicit_progress_tracking": True
        }

        # Orchestration metrics
        self.metrics = {
            "tasks_orchestrated": 0,
            "sync_events_processed": 0,
            "ai_agent_dispatches": 0,
            "adhd_accommodations_applied": 0,
            "implicit_automations_triggered": 0
        }

        # Background workers
        self.workers: List[asyncio.Task] = []
        self.running = False

    async def initialize(self) -> None:
        """Initialize all orchestrator components."""
        logger.info("🚀 Initializing Enhanced Task Orchestrator...")

        # Initialize connections
        await asyncio.gather(
            self._initialize_leantime_connection(),
            self._initialize_redis_connection(),
            self._initialize_agent_pool()
        )

        # Start background workers
        await self._start_background_workers()

        self.running = True
        logger.info("✅ Enhanced Task Orchestrator ready for PM automation!")

    async def _initialize_leantime_connection(self) -> None:
        """Initialize connection to Leantime JSON-RPC API."""
        try:
            self.leantime_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "Authorization": f"Bearer {self.leantime_token}",
                    "Content-Type": "application/json"
                }
            )

            # Test connection
            await self._test_leantime_connection()
            logger.info("🔗 Connected to Leantime API")

        except Exception as e:
            logger.error(f"Failed to connect to Leantime: {e}")
            raise

    async def _test_leantime_connection(self) -> bool:
        """Test Leantime API connectivity."""
        try:
            async with self.leantime_session.post(
                f"{self.leantime_url}/api/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "leantime.rpc.projects.getAllProjects",
                    "params": {"limit": 1},
                    "id": 1
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return "result" in data
                return False

        except Exception as e:
            logger.error(f"Leantime connection test failed: {e}")
            return False

    async def _initialize_redis_connection(self) -> None:
        """Initialize Redis for caching and coordination."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                db=2,  # Separate DB for orchestrator
                decode_responses=True
            )

            await self.redis_client.ping()
            logger.info("🔗 Connected to Redis for coordination")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def _initialize_agent_pool(self) -> None:
        """Initialize AI agent pool for coordination."""
        self.agent_pool = {
            AgentType.CONPORT: {
                "available": True,
                "current_tasks": [],
                "capabilities": ["decision_logging", "progress_tracking", "context_management"],
                "max_concurrent": 5
            },
            AgentType.SERENA: {
                "available": True,
                "current_tasks": [],
                "capabilities": ["code_navigation", "file_analysis", "refactoring"],
                "max_concurrent": 3
            },
            AgentType.TASKMASTER: {
                "available": True,
                "current_tasks": [],
                "capabilities": ["prd_parsing", "complexity_analysis", "research"],
                "max_concurrent": 2
            },
            AgentType.ZEN: {
                "available": True,
                "current_tasks": [],
                "capabilities": ["consensus", "code_review", "architecture_analysis"],
                "max_concurrent": 1  # Intensive operations
            }
        }

        logger.info("🤖 AI agent pool initialized")

    async def _start_background_workers(self) -> None:
        """Start background worker tasks."""
        workers = [
            self._leantime_poller(),
            self._sync_processor(),
            self._adhd_monitor(),
            self._implicit_automation_engine(),
            self._progress_correlator()
        ]

        self.workers = [asyncio.create_task(worker) for worker in workers]
        logger.info("👥 Background workers started")

    # Core Orchestration Methods

    async def _leantime_poller(self) -> None:
        """Background poller for Leantime task updates."""
        logger.info("📡 Started Leantime polling worker")

        while self.running:
            try:
                # Poll for new/updated tasks
                updated_tasks = await self._fetch_updated_leantime_tasks()

                for leantime_task in updated_tasks:
                    await self._process_leantime_task_update(leantime_task)

                # Poll every 30 seconds for updates
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Leantime polling error: {e}")
                await asyncio.sleep(60)  # Back off on error

    async def _fetch_updated_leantime_tasks(self) -> List[Dict[str, Any]]:
        """Fetch tasks updated since last poll."""
        try:
            # Get last poll timestamp
            last_poll = await self.redis_client.get("orchestrator:last_poll")
            if last_poll:
                since_time = datetime.fromisoformat(last_poll)
            else:
                since_time = datetime.now(timezone.utc) - timedelta(hours=24)

            # Fetch updated tasks from Leantime
            async with self.leantime_session.post(
                f"{self.leantime_url}/api/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": "leantime.rpc.tickets.getAllTickets",
                    "params": {
                        "limit": 100,
                        "since": since_time.isoformat()
                    },
                    "id": self._next_request_id()
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    tasks = data.get("result", [])

                    # Update last poll timestamp
                    await self.redis_client.set(
                        "orchestrator:last_poll",
                        datetime.now(timezone.utc).isoformat()
                    )

                    return tasks if isinstance(tasks, list) else []

        except Exception as e:
            logger.error(f"Failed to fetch Leantime tasks: {e}")

        return []

    async def _process_leantime_task_update(self, leantime_task: Dict[str, Any]) -> None:
        """Process updated task from Leantime."""
        try:
            task_id = str(leantime_task.get("id", ""))

            # Convert to orchestration task
            orchestration_task = OrchestrationTask(
                id=f"orch_{task_id}",
                leantime_id=int(task_id),
                title=leantime_task.get("headline", ""),
                description=leantime_task.get("description", ""),
                status=self._map_leantime_status(leantime_task.get("status", "0")),
                priority=int(leantime_task.get("priority", "2")),
                estimated_minutes=self._estimate_task_duration(leantime_task)
            )

            # Apply ADHD optimizations
            orchestration_task = await self._apply_adhd_optimizations(orchestration_task)

            # Store in orchestrated tasks
            self.orchestrated_tasks[orchestration_task.id] = orchestration_task

            # Determine AI agent assignment
            assigned_agent = await self._assign_optimal_agent(orchestration_task)
            if assigned_agent:
                await self._dispatch_to_agent(orchestration_task, assigned_agent)

            # Queue sync event
            sync_event = SyncEvent(
                source_system="leantime",
                target_systems=["conport", "local_adhd"],
                event_type="task_updated",
                task_id=orchestration_task.id,
                data=asdict(orchestration_task),
                timestamp=datetime.now(timezone.utc),
                adhd_metadata={"cognitive_load": orchestration_task.cognitive_load}
            )

            await self.sync_queue.put(sync_event)

            logger.debug(f"📋 Processed Leantime task: {orchestration_task.title}")

        except Exception as e:
            logger.error(f"Failed to process Leantime task update: {e}")

    async def _sync_processor(self) -> None:
        """Background processor for multi-directional synchronization."""
        logger.info("🔄 Started sync processing worker")

        while self.running:
            try:
                # Process sync events from queue
                sync_event = await asyncio.wait_for(self.sync_queue.get(), timeout=10.0)

                await self._execute_sync_event(sync_event)
                self.metrics["sync_events_processed"] += 1

            except asyncio.TimeoutError:
                # No sync events, continue
                continue
            except Exception as e:
                logger.error(f"Sync processing error: {e}")
                await asyncio.sleep(5)

    async def _execute_sync_event(self, event: SyncEvent) -> None:
        """Execute multi-directional sync event."""
        try:
            # Sync to each target system
            for target_system in event.target_systems:
                if target_system == "conport":
                    await self._sync_to_conport(event)
                elif target_system == "local_adhd":
                    await self._sync_to_local_adhd(event)
                elif target_system == "leantime":
                    await self._sync_to_leantime(event)

            logger.debug(f"🔄 Sync completed: {event.event_type} to {len(event.target_systems)} systems")

        except Exception as e:
            logger.error(f"Sync execution failed: {e}")

    async def _sync_to_conport(self, event: SyncEvent) -> None:
        """Sync event to ConPort for decision/progress tracking."""
        try:
            # This would integrate with ConPort v2 MCP API
            if event.event_type == "task_updated":
                # Log progress entry in ConPort
                progress_data = {
                    "status": event.data.get("status", "pending").upper(),
                    "description": f"Task orchestration: {event.data.get('title', 'Unknown task')}",
                    "linked_item_type": "orchestration_task",
                    "linked_item_id": event.task_id
                }

                # Would make MCP call to ConPort here
                logger.debug(f"📊 Synced to ConPort: {event.task_id}")

        except Exception as e:
            logger.error(f"ConPort sync failed: {e}")

    async def _sync_to_local_adhd(self, event: SyncEvent) -> None:
        """Sync event to local ADHD task decomposer."""
        try:
            # This would integrate with the local ADHD task system
            if event.event_type == "task_updated":
                task_data = event.data

                # Create local ADHD task if needed
                if task_data.get("estimated_minutes", 0) > 25:
                    # Auto-decompose large tasks
                    decomposed_tasks = await self._decompose_for_adhd(task_data)
                    logger.debug(f"🧠 ADHD decomposed task into {len(decomposed_tasks)} subtasks")

        except Exception as e:
            logger.error(f"Local ADHD sync failed: {e}")

    async def _adhd_monitor(self) -> None:
        """Background monitor for ADHD accommodations."""
        logger.info("🧠 Started ADHD monitoring worker")

        while self.running:
            try:
                # Check for tasks needing breaks
                await self._check_break_requirements()

                # Monitor cognitive load across active tasks
                await self._monitor_cognitive_load()

                # Detect context switching patterns
                await self._detect_excessive_context_switching()

                # Check every minute for responsiveness
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"ADHD monitoring error: {e}")
                await asyncio.sleep(300)  # 5-minute backoff on error

    async def _implicit_automation_engine(self) -> None:
        """Background engine for implicit PM automation."""
        logger.info("🤖 Started implicit automation engine")

        while self.running:
            try:
                # Check for automation triggers
                await self._check_sprint_automation_triggers()
                await self._check_retrospective_triggers()
                await self._check_task_decomposition_triggers()

                # Run every 5 minutes
                await asyncio.sleep(300)

            except Exception as e:
                logger.error(f"Implicit automation error: {e}")
                await asyncio.sleep(600)  # 10-minute backoff

    async def _progress_correlator(self) -> None:
        """Background correlator for file changes → task progress."""
        logger.info("📈 Started progress correlation worker")

        while self.running:
            try:
                # This would integrate with Serena file change events
                # For now, placeholder implementation
                await self._correlate_code_changes_to_tasks()

                # Check every 2 minutes for code changes
                await asyncio.sleep(120)

            except Exception as e:
                logger.error(f"Progress correlation error: {e}")
                await asyncio.sleep(300)

    # AI Agent Coordination

    async def _assign_optimal_agent(self, task: OrchestrationTask) -> Optional[AgentType]:
        """Assign optimal AI agent based on task characteristics."""
        try:
            # Analyze task content to determine best agent
            title_lower = task.title.lower()
            description_lower = task.description.lower()

            # Decision/architectural tasks → ConPort
            if any(keyword in title_lower or keyword in description_lower
                   for keyword in ["decision", "architecture", "pattern", "strategy"]):
                return AgentType.CONPORT

            # Code-related tasks → Serena
            elif any(keyword in title_lower or keyword in description_lower
                     for keyword in ["implement", "refactor", "debug", "code", "function"]):
                return AgentType.SERENA

            # Research/analysis tasks → TaskMaster
            elif any(keyword in title_lower or keyword in description_lower
                     for keyword in ["research", "analyze", "requirements", "prd"]):
                return AgentType.TASKMASTER

            # Complex coordination → Zen
            elif task.complexity_score > 0.8:
                return AgentType.ZEN

            # Default: ConPort for progress tracking
            return AgentType.CONPORT

        except Exception as e:
            logger.error(f"Agent assignment failed: {e}")
            return None

    async def _dispatch_to_agent(self, task: OrchestrationTask, agent: AgentType) -> bool:
        """Dispatch task to assigned AI agent."""
        try:
            # Check agent availability
            agent_info = self.agent_pool.get(agent)
            if not agent_info or not agent_info["available"]:
                logger.warning(f"Agent {agent.value} not available for task {task.id}")
                return False

            # Check concurrent task limit
            current_tasks = len(agent_info["current_tasks"])
            max_concurrent = agent_info["max_concurrent"]

            if current_tasks >= max_concurrent:
                logger.warning(f"Agent {agent.value} at capacity ({current_tasks}/{max_concurrent})")
                return False

            # Dispatch based on agent type
            dispatch_success = False

            if agent == AgentType.CONPORT:
                dispatch_success = await self._dispatch_to_conport(task)
            elif agent == AgentType.SERENA:
                dispatch_success = await self._dispatch_to_serena(task)
            elif agent == AgentType.TASKMASTER:
                dispatch_success = await self._dispatch_to_taskmaster(task)
            elif agent == AgentType.ZEN:
                dispatch_success = await self._dispatch_to_zen(task)

            if dispatch_success:
                # Update agent state
                agent_info["current_tasks"].append(task.id)
                task.assigned_agent = agent
                task.agent_assignments[agent.value] = datetime.now(timezone.utc).isoformat()

                self.metrics["ai_agent_dispatches"] += 1
                logger.info(f"🤖 Dispatched task {task.id} to {agent.value}")

            return dispatch_success

        except Exception as e:
            logger.error(f"Failed to dispatch task to {agent.value}: {e}")
            return False

    async def _dispatch_to_conport(self, task: OrchestrationTask) -> bool:
        """Dispatch task to ConPort for decision/progress tracking."""
        try:
            # This would make MCP calls to ConPort v2
            # For now, simulate dispatch
            logger.debug(f"📊 ConPort dispatch: {task.title}")
            return True

        except Exception as e:
            logger.error(f"ConPort dispatch failed: {e}")
            return False

    async def _dispatch_to_serena(self, task: OrchestrationTask) -> bool:
        """Dispatch task to Serena for code intelligence."""
        try:
            # This would make MCP calls to Serena v2
            # For now, simulate dispatch
            logger.debug(f"🧠 Serena dispatch: {task.title}")
            return True

        except Exception as e:
            logger.error(f"Serena dispatch failed: {e}")
            return False

    async def _dispatch_to_taskmaster(self, task: OrchestrationTask) -> bool:
        """Dispatch task to TaskMaster for analysis."""
        try:
            # This would make MCP calls to TaskMaster
            # For now, simulate dispatch
            logger.debug(f"🔍 TaskMaster dispatch: {task.title}")
            return True

        except Exception as e:
            logger.error(f"TaskMaster dispatch failed: {e}")
            return False

    async def _dispatch_to_zen(self, task: OrchestrationTask) -> bool:
        """Dispatch task to Zen for multi-model analysis."""
        try:
            # This would make MCP calls to Zen
            # For now, simulate dispatch
            logger.debug(f"🌟 Zen dispatch: {task.title}")
            return True

        except Exception as e:
            logger.error(f"Zen dispatch failed: {e}")
            return False

    # ADHD Optimization Methods

    async def _apply_adhd_optimizations(self, task: OrchestrationTask) -> OrchestrationTask:
        """Apply ADHD optimizations to task."""
        try:
            # Calculate cognitive load based on task characteristics
            cognitive_load = self._calculate_cognitive_load(task)
            task.cognitive_load = cognitive_load

            # Determine energy requirements
            if cognitive_load > 0.8:
                task.energy_required = "high"
            elif cognitive_load > 0.5:
                task.energy_required = "medium"
            else:
                task.energy_required = "low"

            # Set ADHD-friendly break frequency
            if task.estimated_minutes > 25:
                task.break_frequency_minutes = 25  # Pomodoro breaks
            else:
                task.break_frequency_minutes = task.estimated_minutes + 5

            # Limit context switches based on complexity
            if task.complexity_score > 0.7:
                task.context_switches_allowed = 1  # High focus required
            else:
                task.context_switches_allowed = 3  # Normal flexibility

            self.metrics["adhd_accommodations_applied"] += 1
            return task

        except Exception as e:
            logger.error(f"ADHD optimization failed: {e}")
            return task

    def _calculate_cognitive_load(self, task: OrchestrationTask) -> float:
        """Calculate cognitive load for task."""
        try:
            base_load = 0.3  # Base cognitive load

            # Duration factor
            duration_load = min(task.estimated_minutes / 60.0, 0.4)  # Max 0.4 for duration

            # Complexity factor
            complexity_load = task.complexity_score * 0.3

            # Priority stress factor
            priority_load = (task.priority / 10.0) * 0.1

            total_load = min(base_load + duration_load + complexity_load + priority_load, 1.0)
            return total_load

        except Exception:
            return 0.5  # Default moderate load

    async def _check_break_requirements(self) -> None:
        """Check if any active tasks need break reminders."""
        try:
            current_time = datetime.now(timezone.utc)

            for task in self.orchestrated_tasks.values():
                if task.status == TaskStatus.IN_PROGRESS:
                    # Check if break is needed based on work duration
                    if task.agent_assignments:
                        start_time_str = next(iter(task.agent_assignments.values()))
                        start_time = datetime.fromisoformat(start_time_str)
                        work_duration = (current_time - start_time).total_seconds() / 60

                        if work_duration >= task.break_frequency_minutes:
                            # Suggest break
                            await self._suggest_task_break(task)

        except Exception as e:
            logger.error(f"Break requirement check failed: {e}")

    async def _suggest_task_break(self, task: OrchestrationTask) -> None:
        """Suggest break for task with ADHD-friendly messaging."""
        try:
            # Update task status
            task.status = TaskStatus.NEEDS_BREAK

            # Log break suggestion in Redis for UI consumption
            break_suggestion = {
                "task_id": task.id,
                "task_title": task.title,
                "work_duration": task.break_frequency_minutes,
                "suggestion": f"☕ Great work on '{task.title}'! Time for a 5-minute break.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            await self.redis_client.lpush(
                f"orchestrator:break_suggestions:{self.workspace_id}",
                json.dumps(break_suggestion)
            )

            # Trim list to keep only recent suggestions
            await self.redis_client.ltrim(
                f"orchestrator:break_suggestions:{self.workspace_id}",
                0, 9  # Keep only 10 most recent
            )

            logger.info(f"☕ Break suggested for task: {task.title}")

        except Exception as e:
            logger.error(f"Break suggestion failed: {e}")

    # Implicit Automation Methods

    async def _check_sprint_automation_triggers(self) -> None:
        """Check for sprint planning automation triggers."""
        try:
            # Check for new sprints in Leantime
            # This would integrate with Leantime's sprint/iteration API
            # For now, placeholder implementation

            # Simulate checking for new sprint
            new_sprints = await self._check_for_new_sprints()

            for sprint in new_sprints:
                await self._auto_setup_sprint(sprint)

        except Exception as e:
            logger.error(f"Sprint automation check failed: {e}")

    async def _auto_setup_sprint(self, sprint_data: Dict[str, Any]) -> None:
        """Automatically setup sprint with ADHD optimizations."""
        try:
            sprint_id = sprint_data.get("id", "unknown")

            # 1. Analyze sprint tasks for complexity
            sprint_tasks = await self._get_sprint_tasks(sprint_id)

            # 2. Apply ADHD decomposition
            for task in sprint_tasks:
                if task.estimated_minutes > 25:
                    await self._auto_decompose_task(task)

            # 3. Setup ConPort sprint context
            sprint_context = {
                "sprint_id": sprint_id,
                "mode": "PLAN",
                "focus": "Sprint planning automation",
                "tasks_count": len(sprint_tasks),
                "auto_setup": True
            }

            # This would sync to ConPort active context
            logger.info(f"🚀 Auto-setup sprint {sprint_id} with {len(sprint_tasks)} tasks")
            self.metrics["implicit_automations_triggered"] += 1

        except Exception as e:
            logger.error(f"Sprint auto-setup failed: {e}")

    # Utility Methods

    def _map_leantime_status(self, leantime_status: str) -> TaskStatus:
        """Map Leantime status to orchestration status."""
        status_map = {
            "0": TaskStatus.PENDING,
            "1": TaskStatus.IN_PROGRESS,
            "2": TaskStatus.COMPLETED,
            "3": TaskStatus.BLOCKED,
            "6": TaskStatus.NEEDS_BREAK,
            "7": TaskStatus.CONTEXT_SWITCH
        }
        return status_map.get(leantime_status, TaskStatus.PENDING)

    def _estimate_task_duration(self, leantime_task: Dict[str, Any]) -> int:
        """Estimate task duration in minutes."""
        try:
            # Use story points if available
            story_points = leantime_task.get("storypoints")
            if story_points:
                # Rough conversion: 1 story point = 2 hours = 120 minutes
                return int(story_points) * 120

            # Fallback: analyze description length and complexity
            description = leantime_task.get("description", "")
            base_duration = 30  # 30-minute default

            # Adjust based on description complexity
            if len(description) > 500:
                base_duration *= 2
            elif len(description) < 100:
                base_duration = 15

            return base_duration

        except Exception:
            return 25  # Default ADHD-friendly duration

    def _next_request_id(self) -> int:
        """Generate next request ID."""
        return int(datetime.now().timestamp() * 1000)

    # Placeholder methods for integration points
    async def _check_for_new_sprints(self) -> List[Dict[str, Any]]:
        """Check Leantime for new sprints."""
        # Placeholder - would integrate with Leantime API
        return []

    async def _get_sprint_tasks(self, sprint_id: str) -> List[OrchestrationTask]:
        """Get tasks for specific sprint."""
        # Placeholder - would fetch from Leantime
        return []

    async def _auto_decompose_task(self, task: OrchestrationTask) -> List[OrchestrationTask]:
        """Automatically decompose large task for ADHD."""
        # Placeholder - would integrate with ADHD decomposer
        return []

    async def _correlate_code_changes_to_tasks(self) -> None:
        """Correlate file changes to task progress."""
        # Placeholder - would integrate with Serena file monitoring
        pass

    async def _monitor_cognitive_load(self) -> None:
        """Monitor overall cognitive load across tasks."""
        # Placeholder - would analyze active task load
        pass

    async def _detect_excessive_context_switching(self) -> None:
        """Detect and mitigate excessive context switching."""
        # Placeholder - would analyze task switching patterns
        pass

    async def _check_retrospective_triggers(self) -> None:
        """Check for retrospective automation triggers."""
        # Placeholder - would detect sprint completion
        pass

    async def _check_task_decomposition_triggers(self) -> None:
        """Check for automatic task decomposition triggers."""
        # Placeholder - would identify complex tasks needing breakdown
        pass

    # Health and Monitoring

    async def get_orchestration_health(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        try:
            # Component health checks
            leantime_healthy = await self._test_leantime_connection()
            redis_healthy = await self.redis_client.ping() if self.redis_client else False

            # Worker health
            active_workers = len([w for w in self.workers if not w.done()])

            # Overall status
            if leantime_healthy and redis_healthy and active_workers == len(self.workers):
                status = "🚀 Excellent"
            elif leantime_healthy and redis_healthy:
                status = "✅ Good"
            elif leantime_healthy or redis_healthy:
                status = "⚠️ Degraded"
            else:
                status = "🔴 Critical"

            return {
                "overall_status": status,
                "components": {
                    "leantime_api": "🟢 Connected" if leantime_healthy else "🔴 Disconnected",
                    "redis_coordination": "🟢 Connected" if redis_healthy else "🔴 Disconnected",
                    "workers_active": f"{active_workers}/{len(self.workers)}",
                    "ai_agents": {agent.value: info["available"] for agent, info in self.agent_pool.items()}
                },
                "metrics": self.metrics,
                "orchestrated_tasks": len(self.orchestrated_tasks),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"overall_status": "🔴 Error", "error": str(e)}

    async def close(self) -> None:
        """Shutdown orchestrator gracefully."""
        logger.info("🛑 Shutting down Enhanced Task Orchestrator...")

        # Stop background workers
        self.running = False
        if self.workers:
            for worker in self.workers:
                worker.cancel()
            await asyncio.gather(*self.workers, return_exceptions=True)

        # Close connections
        if self.leantime_session:
            await self.leantime_session.close()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("✅ Enhanced Task Orchestrator shutdown complete")


# Main entry point for enhanced orchestrator
async def main():
    """Main entry point for enhanced task orchestrator."""
    # Configuration from environment
    leantime_url = os.getenv("LEANTIME_URL", "http://localhost:8080")
    leantime_token = os.getenv("LEANTIME_TOKEN", "")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    workspace_id = os.getenv("WORKSPACE_ID", "/Users/hue/code/dopemux-mvp")

    if not leantime_token:
        logger.error("LEANTIME_TOKEN environment variable required")
        sys.exit(1)

    orchestrator = EnhancedTaskOrchestrator(
        leantime_url=leantime_url,
        leantime_token=leantime_token,
        redis_url=redis_url,
        workspace_id=workspace_id
    )

    try:
        await orchestrator.initialize()

        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        await orchestrator.close()


if __name__ == "__main__":
    asyncio.run(main())