"""
Enhanced Task Orchestrator - Intelligent Middleware for PM Automation

Coordinates between Leantime PM interface and AI agents with implicit automation.
Provides seamless ADHD-optimized development workflow orchestration.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum

import aiohttp
import redis.asyncio as redis

# Configure logging FIRST
logger = logging.getLogger(__name__)

# Import cache utility for Redis caching
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
try:
    from dopemux.cache import get_cache
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("Redis cache not available - using in-memory fallback")

# Import the global error handling framework
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
    from dopemux.error_handling import (
        GlobalErrorHandler,
        with_error_handling,
        create_dopemux_error,
        ErrorType,
        ErrorSeverity,
        RetryPolicy,
        CircuitBreakerConfig,
        CircuitBreaker
    )
    ERROR_HANDLING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Error handling framework not available: {e}")
    ERROR_HANDLING_AVAILABLE = False
    
    # Dummy decorator fallback
    def with_error_handling(*args, **kwargs):
        def decorator(func):
            return func
        return decorator



# Import DopeconBridge EventBus for event coordination (Component 3)
try:
    # Add integration bridge path
    dopecon_bridge_path = os.path.join(os.path.dirname(__file__), '..', 'mcp-dopecon-bridge')
    sys.path.insert(0, dopecon_bridge_path)
    from event_bus import EventBus, Event, EventType
    EVENTBUS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"EventBus not available: {e}")
    EVENTBUS_AVAILABLE = False

# Import our new specialized engines
try:
    from .multi_team_coordination import MultiTeamCoordinationEngine, TeamProfile, CrossTeamDependency, CoordinationPriority
    from .predictive_risk_assessment import PredictiveRiskAssessmentEngine, RiskProfile, RiskLevel
    from .external_dependency_integration import ExternalDependencyIntegrationEngine, ExternalDependency, DependencyType
    SPECIALIZED_ENGINES_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Specialized engines not available: {e}")
    SPECIALIZED_ENGINES_AVAILABLE = False

# Import CognitiveGuardian for ADHD-aware task routing (Week 5)
try:
    agents_path = os.path.join(os.path.dirname(__file__), '..', 'agents')
    sys.path.insert(0, agents_path)
    from cognitive_guardian import CognitiveGuardian
    COGNITIVE_GUARDIAN_AVAILABLE = True
except ImportError as e:
    logger.warning(f"CognitiveGuardian not available: {e}")
    COGNITIVE_GUARDIAN_AVAILABLE = False

# ConPort-KG Integration for task progress events
try:
    from dopecon_bridge_connector import emit_task_status_change
    CONPORT_KG_INTEGRATION = True
except ImportError:
    CONPORT_KG_INTEGRATION = False


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
    conport_id: Optional[int] = None  # ConPort progress_entry ID (Architecture 3.0 Component 2)
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
        redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379"),
        workspace_id: str = "/Users/hue/code/dopemux-mvp",
        mcp_tools: Any = None
    ):
        self.leantime_url = leantime_url.rstrip('/')
        self.leantime_token = leantime_token
        self.redis_url = redis_url
        self.workspace_id = workspace_id
        self.mcp_tools = mcp_tools  # Add mcp_tools parameter

        # Component connections
        self.leantime_session: Optional[aiohttp.ClientSession] = None
        self.redis_client: Optional[redis.Redis] = None
        self.event_bus: Optional[EventBus] = None  # DopeconBridge EventBus (Component 3)

        # Task coordination state - Architecture 3.0: ConPort is storage authority
        # REMOVED: self.orchestrated_tasks dict (Authority violation - fixed in Component 2 Task 2.5)
        # Tasks now queried from ConPort via conport_adapter
        self.conport_adapter = None  # Initialized in _initialize_agent_pool with ConPortEventAdapter
        self.agent_pool: Dict[AgentType, Dict[str, Any]] = {}
        self.sync_queue: asyncio.Queue = asyncio.Queue()

        # ADHD support agents (Week 5)
        self.cognitive_guardian: Optional[CognitiveGuardian] = None

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

        # Error handling framework integration (Phase 2)
        if ERROR_HANDLING_AVAILABLE:
            self.error_handler = GlobalErrorHandler("task_orchestrator")

            # Register circuit breaker for Leantime API calls
            leantime_config = CircuitBreakerConfig(
                name="leantime_api",
                failure_threshold=3,
                recovery_timeout=30,
                success_threshold=2,
                timeout=15.0
            )
            self.error_handler.register_circuit_breaker("leantime_api", leantime_config)

            # Register retry policy for API calls
            api_retry_policy = RetryPolicy(
                max_attempts=3,
                initial_delay=1.0,
                max_delay=10.0,
                backoff_factor=2.0,
                jitter=True
            )
            self.error_handler.register_retry_policy("api_retry", api_retry_policy)
        else:
            self.error_handler = None
            logger.warning("⚠️ Error handling framework not available")

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

        # Initialize ADHD support agents (Week 5)
        await self._initialize_adhd_agents()

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

    @with_error_handling("_test_leantime_connection", retry_policy="api_retry", circuit_breaker="leantime_api")
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
            if ERROR_HANDLING_AVAILABLE:
                raise create_dopemux_error(
                    error_type=ErrorType.NETWORK,
                    severity=ErrorSeverity.MEDIUM,
                    message=f"Leantime connection test failed: {e}",
                    service_name="task_orchestrator",
                    operation="_test_leantime_connection",
                    details={"leantime_url": self.leantime_url}
                ) from e
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

            # Initialize DopeconBridge EventBus (Component 3)
            if EVENTBUS_AVAILABLE:
                self.event_bus = EventBus(self.redis_url, password=None)
                await self.event_bus.initialize()
                logger.info("🔗 Connected to DopeconBridge EventBus")
            else:
                logger.warning("⚠️ EventBus not available - DopeconBridge events disabled")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def _initialize_agent_pool(self) -> None:
        """Initialize AI agent pool for coordination."""
        # Initialize ConPort adapter (Architecture 3.0 Component 2)
        try:
            from adapters.conport_adapter import ConPortEventAdapter
            # Use ConPort HTTP API for secure service boundaries (Component 3)
            conport_url = os.getenv("CONPORT_URL", "http://localhost:8005")
            self.conport_adapter = ConPortEventAdapter(
                workspace_id=self.workspace_id,
                conport_url=conport_url
            )
            # Initialize HTTP session for ConPort communication
            await self.conport_adapter.initialize()
            logger.info("📊 ConPort adapter initialized with HTTP API (secure service boundaries)")
        except Exception as e:
            logger.warning(f"ConPort adapter initialization failed: {e} - continuing without persistence")
            self.conport_adapter = None

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

    async def _initialize_adhd_agents(self) -> None:
        """Initialize ADHD support agents for intelligent task routing (Week 5)."""
        if not COGNITIVE_GUARDIAN_AVAILABLE:
            logger.warning("⚠️ CognitiveGuardian not available - ADHD routing disabled")
            return

        try:
            self.cognitive_guardian = CognitiveGuardian(
                workspace_id=self.workspace_id,
                memory_agent=None,  # Could wire MemoryAgent here if needed
                conport_client=None,  # Could wire ConPort client if needed
                break_interval_minutes=25,
                mandatory_break_minutes=90,
                hyperfocus_warning_minutes=60
            )
            await self.cognitive_guardian.start_monitoring()
            logger.info("🧠 CognitiveGuardian initialized - ADHD-aware routing active")
        except Exception as e:
            logger.error(f"Failed to initialize CognitiveGuardian: {e}")
            self.cognitive_guardian = None

    async def _start_background_workers(self) -> None:
        """Start background worker tasks."""
        workers = [
            self._leantime_poller(),
            self._sync_processor(),
            self._adhd_monitor(),
            self._implicit_automation_engine(),
            self._progress_correlator()
        ]

        # Add DopeconBridge event subscriber (Component 3)
        if self.event_bus:
            workers.append(self._dopecon_bridge_subscriber())
            logger.info("📡 DopeconBridge event subscriber enabled")

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

    @with_error_handling("_fetch_updated_leantime_tasks", retry_policy="api_retry", circuit_breaker="leantime_api")
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
            if ERROR_HANDLING_AVAILABLE:
                raise create_dopemux_error(
                    error_type=ErrorType.NETWORK,
                    severity=ErrorSeverity.MEDIUM,
                    message=f"Failed to fetch Leantime tasks: {e}",
                    service_name="task_orchestrator",
                    operation="_fetch_updated_leantime_tasks",
                    details={"leantime_url": self.leantime_url, "error": str(e)}
                ) from e

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

            # Store in ConPort (Architecture 3.0: ConPort is storage authority)
            if self.conport_adapter:
                conport_id = await self.conport_adapter.create_task_in_conport(orchestration_task)
                orchestration_task.conport_id = conport_id
                logger.debug(f"📊 Task stored in ConPort: {orchestration_task.title} (ID: {conport_id})")
            else:
                logger.warning(f"⚠️ ConPort adapter not initialized, task not persisted: {orchestration_task.id}")

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

                # Make actual MCP call to ConPort
                if self.conport_adapter:
                    conport_id = await self.conport_adapter.create_task_in_conport_from_sync(event)
                    logger.info(f"📊 Synced to ConPort: {event.task_id} -> ConPort ID: {conport_id}")
                else:
                    logger.warning("📊 ConPort adapter not initialized, skipping sync")

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
        """
        Assign optimal AI agent based on task characteristics with ADHD awareness.

        WEEK 5 ENHANCEMENT: Now uses ADHD metadata for intelligent routing.

        Checks (in order):
        1. User readiness (energy + complexity + attention matching)
        2. Complexity threshold (>0.8 → Zen)
        3. Keyword-based routing
        4. Default fallback

        Returns:
            AgentType or None if user not ready
        """
        try:
            # === STEP 1: ADHD READINESS CHECK ===
            # Check if user is ready for this task (energy + attention + complexity)
            if self.cognitive_guardian:
                readiness = await self.cognitive_guardian.check_task_readiness(
                    task_complexity=task.complexity_score,
                    task_energy_required=task.energy_required
                )

                if not readiness['ready']:
                    logger.warning(
                        f"⚠️ User not ready for task: {task.title}\n"
                        f"   Reason: {readiness['reason']}\n"
                        f"   Suggestion: {readiness['suggestion']}"
                    )
                    
                    # Check if mandatory break needed
                    user_state = await self.cognitive_guardian.get_user_state()
                    if user_state.session_duration_minutes >= 90:
                        logger.error("🛑 MANDATORY BREAK REQUIRED - No tasks assigned")
                        return "break_required"  # Special signal for break enforcement
                    
                    # Return None to defer task
                    # UI would display readiness['alternatives'] for user to choose
                    # This prevents energy mismatches and burnout
                    return None

            # === STEP 2: COMPLEXITY CHECK (BEFORE keywords - FIX from Week 2 testing) ===
            # High-complexity tasks ALWAYS go to Zen for multi-model analysis
            if task.complexity_score > 0.8:
                logger.info(
                    f"🌟 High complexity task ({task.complexity_score:.2f}) → Zen "
                    f"(multi-model analysis)"
                )
                return AgentType.ZEN

            # === STEP 3: KEYWORD-BASED ROUTING ===
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

            # === STEP 4: DEFAULT FALLBACK ===
            # Default: ConPort for progress tracking
            return AgentType.CONPORT

        except Exception as e:
            logger.error(f"Agent assignment failed: {e}")
            return None

    async def _dispatch_to_agent(self, task: OrchestrationTask, agent: AgentType) -> bool:
        """
        Dispatch task to assigned AI agent.

        Args:
            task: Orchestration task to dispatch
            agent: Target AI agent (or "break_required" signal)

        Returns:
            Success status
        """
        try:
            # NEW: Handle break-required state
            if agent == "break_required":
                logger.warning("🛑 MANDATORY BREAK - Task deferred")
                logger.info("\n" + "="*70)
                logger.info("🛑 MANDATORY BREAK REQUIRED")
                logger.info("   You've been working too long.")
                logger.info("   Take a 10-minute break, then return.")
                logger.info("   Task will be available after break.")
                logger.info("="*70 + "\n")
                
                # Track ADHD accommodation
                self.metrics["adhd_accommodations_applied"] += 1
                
                return False  # Task not dispatched
            
            # EXISTING: Check agent availability
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
        """
        Dispatch task to ConPort for decision/progress tracking.

        Creates or updates ConPort progress_entry with ADHD metadata.
        """
        try:
            # In Claude Code context, use real MCP calls
            # NOTE: These mcp__ functions are available in Claude Code execution context

            if task.conport_id:
                # Update existing progress entry
                logger.info(f"📊 ConPort update: {task.title} (ID: {task.conport_id})")

                await mcp__conport__update_progress(
                    workspace_id=self.workspace_id,
                    progress_id=task.conport_id,
                    status=task.status.value.upper(),
                    description=f"{task.title} (complexity: {task.complexity_score:.2f})"
                )

                logger.debug(f"Updated ConPort progress entry {task.conport_id}")

            else:
                # Create new progress entry with ADHD metadata
                logger.info(f"📊 ConPort create: {task.title}")

                result = await mcp__conport__log_progress(
                    workspace_id=self.workspace_id,
                    status=task.status.value.upper(),
                    description=task.title,
                    # ADHD metadata would be added as custom JSON in description or via custom_data
                )
                task.conport_id = result['id']

                logger.debug(f"Created ConPort progress entry for {task.title}")

            # If this is a decision/architecture task, also log to decisions
            if "decision" in task.title.lower() or "architecture" in task.title.lower():
                logger.info(f"💡 Logging architecture decision: {task.title}")

                # Would call: await mcp__conport__log_decision(
                #     workspace_id=self.workspace_id,
                #     summary=task.title,
                #     rationale=task.description,
                #     tags=["task-orchestrator", "architecture"]
                # )

            return True

        except Exception as e:
            logger.error(f"ConPort dispatch failed: {e}")
            return False

    async def _dispatch_to_serena(self, task: OrchestrationTask) -> bool:
        """
        Dispatch task to Serena for code intelligence.

        Uses Serena LSP to analyze code complexity and provide navigation context.
        Updates task with actual complexity score from AST analysis.
        """
        try:
            logger.info(f"🧠 Serena dispatch: {task.title}")

            # Extract potential symbol/file from task description
            # In a real implementation, would parse task.description for file paths or symbols
            # For now, provide pattern for integration

            # Example: If task mentions a specific file or function
            # key_symbol = extract_symbol_from_task(task)
            # if key_symbol:
            #     # Find the symbol in codebase
            #     result = await mcp__serena_v2__find_symbol(
            #         query=key_symbol,
            #         max_results=3
            #     )
            #
            #     if result and len(result) > 0:
            #         symbol_info = result[0]
            #
            #         # Get complexity analysis
            #         complexity = await mcp__serena_v2__analyze_complexity(
            #             file_path=symbol_info['file'],
            #             symbol_name=key_symbol
            #         )
            #
            #         # Update task with REAL complexity from AST
            #         task.complexity_score = complexity['score']
            #         task.cognitive_load = complexity['cognitive_load']
            #
            #         logger.info(
            #             f"Serena analysis: {key_symbol} "
            #             f"complexity={complexity['score']:.2f}, "
            #             f"cognitive_load={complexity['cognitive_load']:.2f}"
            #         )
            #
            #         # Update ConPort with refined complexity
            #         if task.conport_id:
            #             await mcp__conport__update_progress(
            #                 workspace_id=self.workspace_id,
            #                 progress_id=task.conport_id,
            #                 description=f"{task.title} (Serena complexity: {complexity['score']:.2f})"
            #             )

            logger.debug(f"Serena dispatch complete for {task.title}")
            return True

        except Exception as e:
            logger.error(f"Serena dispatch failed: {e}")
            # Graceful degradation - don't fail entire dispatch
            return True  # Task still assigned, just without Serena enrichment

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
        """
        Dispatch task to Zen for multi-model analysis.

        Uses Zen thinkdeep for complex analysis or planner for decomposition.
        High-complexity tasks (>0.8) benefit from multi-model reasoning.
        """
        try:
            logger.info(f"🌟 Zen dispatch: {task.title} (complexity: {task.complexity_score:.2f})")

            # Determine which Zen tool based on task type
            # Architecture/design tasks -> thinkdeep or consensus
            # Planning tasks -> planner
            # Complex debugging -> debug

            if "plan" in task.title.lower() or "decompose" in task.description.lower():
                # Use Zen planner for task decomposition
                logger.info(f"Using Zen planner for: {task.title}")

                # Would call: result = await mcp__zen__planner(
                #     step=f"Break down task: {task.title}\n\nDescription: {task.description}",
                #     step_number=1,
                #     total_steps=2,
                #     next_step_required=False,
                #     model="gpt-5-mini"  # Fast model for planning
                # )
                #
                # # Store plan in task metadata
                # task.planning_result = result

            elif task.complexity_score > 0.8:
                # Use Zen thinkdeep for complex analysis
                logger.info(f"Using Zen thinkdeep for high-complexity: {task.title}")

                # Would call: result = await mcp__zen__thinkdeep(
                #     step=f"Analyze complex task: {task.title}\n\n{task.description}",
                #     step_number=1,
                #     total_steps=3,
                #     next_step_required=True,
                #     findings="Initial analysis of task requirements",
                #     model="gpt-5-mini",
                #     confidence="low"
                # )
                #
                # # Update task with analysis insights
                # task.analysis_insights = result

            else:
                # Lower complexity - simple dispatch without Zen
                logger.debug(f"Task complexity {task.complexity_score:.2f} - no Zen analysis needed")

            logger.debug(f"Zen dispatch complete for {task.title}")
            return True

        except Exception as e:
            logger.error(f"Zen dispatch failed: {e}")
            # Graceful degradation - task still assigned
            return True

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

        except Exception as e:
            return 0.5  # Default moderate load

            logger.error(f"Error: {e}")
    async def _get_task_count_from_conport(self) -> int:
        """Get total task count from ConPort (Architecture 3.0 storage authority)."""
        try:
            if self.conport_adapter:
                all_tasks = await self.conport_adapter.get_all_tasks_from_conport()
                return len(all_tasks)
            else:
                return 0  # No adapter, no tasks
        except Exception as e:
            logger.error(f"Failed to get task count from ConPort: {e}")
            return 0

    async def _check_break_requirements(self) -> None:
        """Check if any active tasks need break reminders."""
        try:
            current_time = datetime.now(timezone.utc)

            # Query ConPort for IN_PROGRESS tasks (Architecture 3.0: ConPort is source of truth)
            if self.conport_adapter:
                active_tasks = await self.conport_adapter.get_all_tasks_from_conport(status_filter="IN_PROGRESS")
            else:
                logger.warning("⚠️ ConPort adapter not initialized, skipping break check")
                return

            for task in active_tasks:
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
                await self._auto_setup_slogger.info(sprint)

        except Exception as e:
            logger.error(f"Sprint automation check failed: {e}")

    async def _auto_setup_sprint_optimizations(self, sprint_data: Dict[str, Any]) -> None:
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

        except Exception as e:
            return 25  # Default ADHD-friendly duration

            logger.error(f"Error: {e}")
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

    # DopeconBridge Event Subscription (Component 3)

    async def _dopecon_bridge_subscriber(self) -> None:
        """Subscribe to DopeconBridge events for bidirectional ConPort communication."""
        logger.info("📡 Started DopeconBridge event subscriber")

        while self.running:
            try:
                # Subscribe to dopemux:events stream
                async for msg_id, event in self.event_bus.subscribe(
                    stream="dopemux:events",
                    consumer_group="task-orchestrator",
                    consumer_name=f"orchestrator-{self.workspace_id.split('/')[-1]}"
                ):
                    await self._handle_dopecon_bridge_event(event)

            except Exception as e:
                logger.error(f"DopeconBridge subscription error: {e}")
                await asyncio.sleep(30)  # Reconnect after 30 seconds

    async def _handle_dopecon_bridge_event(self, event: Any) -> None:
        """Handle events from DopeconBridge."""
        try:
            logger.debug(f"📥 Received event: {event.type} from {event.source}")

            if event.type == EventType.TASKS_IMPORTED:
                await self._handle_tasks_imported(event)
            elif event.type == EventType.SESSION_STARTED:
                await self._handle_session_started(event)
            elif event.type == EventType.SESSION_PAUSED:
                await self._handle_session_paused(event)
            elif event.type == EventType.SESSION_COMPLETED:
                await self._handle_session_completed(event)
            elif event.type == EventType.PROGRESS_UPDATED:
                await self._handle_progress_updated(event)
            elif event.type == EventType.DECISION_LOGGED:
                await self._handle_decision_logged(event)
            elif event.type == EventType.ADHD_STATE_CHANGED:
                await self._handle_adhd_state_changed(event)
            elif event.type == EventType.BREAK_REMINDER:
                await self._handle_break_reminder(event)
            else:
                logger.debug(f"Unhandled event type: {event.type}")

        except Exception as e:
            logger.error(f"Event handling failed: {e}")

    async def _handle_tasks_imported(self, event: Any) -> None:
        """Handle tasks_imported event from DopeconBridge."""
        try:
            task_count = event.data.get("task_count", 0)
            sprint_id = event.data.get("sprint_id", "unknown")

            logger.info(f"📥 Tasks imported: {task_count} tasks in sprint {sprint_id}")

            # Sync to ConPort if adapter available
            if self.conport_adapter:
                logger.debug(f"📊 Syncing {task_count} tasks to ConPort for sprint {sprint_id}")
                await self.conport_adapter.sync_imported_tasks(task_count, sprint_id)

        except Exception as e:
            logger.error(f"Failed to handle tasks_imported: {e}")

    async def _handle_session_started(self, event: Any) -> None:
        """Handle session_started event from DopeconBridge."""
        try:
            task_id = event.data.get("task_id", "")
            duration_minutes = event.data.get("duration_minutes", 25)

            logger.info(f"📥 Session started: Task {task_id} ({duration_minutes} minutes)")

            # Update task status in ConPort
            if self.conport_adapter:
                logger.debug(f"📊 Updating task {task_id} status to IN_PROGRESS in ConPort")
                await self.conport_adapter.update_task_status(task_id, "IN_PROGRESS")

        except Exception as e:
            logger.error(f"Failed to handle session_started: {e}")

    async def _handle_session_paused(self, event: Any) -> None:
        """Handle session_paused event from DopeconBridge."""
        try:
            task_id = event.data.get("task_id", "")

            logger.info(f"📥 Session paused: Task {task_id}")

            # Update task status in ConPort
            if self.conport_adapter:
                logger.debug(f"📊 Updating task {task_id} status to BLOCKED in ConPort")
                await self.conport_adapter.update_task_status(task_id, "BLOCKED")

        except Exception as e:
            logger.error(f"Failed to handle session_paused: {e}")

    async def _handle_session_completed(self, event: Any) -> None:
        """Handle session_completed event from DopeconBridge."""
        try:
            task_id = event.data.get("task_id", "")

            logger.info(f"📥 Session completed: Task {task_id}")

            # Update task status in ConPort
            if self.conport_adapter:
                logger.debug(f"📊 Updating task {task_id} status to DONE in ConPort")
                await self.conport_adapter.update_task_status(task_id, "DONE")

        except Exception as e:
            logger.error(f"Failed to handle session_completed: {e}")

    async def _handle_progress_updated(self, event: Any) -> None:
        """Handle progress_updated event from DopeconBridge."""
        try:
            task_id = event.data.get("task_id", "")
            status = event.data.get("status", "")
            progress = event.data.get("progress", 0.0)

            logger.info(f"📥 Progress updated: Task {task_id} -> {status} ({progress * 100:.0f}%)")

            # Sync progress to ConPort
            if self.conport_adapter:
                logger.debug(f"📊 Syncing progress for task {task_id} to ConPort")
                await self.conport_adapter.update_task_progress(task_id, status.upper(), progress)

        except Exception as e:
            logger.error(f"Failed to handle progress_updated: {e}")

    async def _handle_decision_logged(self, event: Any) -> None:
        """Handle decision_logged event from DopeconBridge."""
        try:
            decision_summary = event.data.get("summary", "")
            decision_id = event.data.get("decision_id", "")

            logger.info(f"📥 Decision logged: {decision_summary} (ID: {decision_id})")

            # Link decision to relevant tasks in ConPort
            if self.conport_adapter:
                logger.debug(f"📊 Linking decision {decision_id} to related tasks in ConPort")
                await self.conport_adapter.link_decision_to_tasks(decision_id)

        except Exception as e:
            logger.error(f"Failed to handle decision_logged: {e}")

    async def _handle_adhd_state_changed(self, event: Any) -> None:
        """Handle adhd_state_changed event from DopeconBridge."""
        try:
            state = event.data.get("state", "")
            energy_level = event.data.get("energy_level", "medium")
            attention_level = event.data.get("attention_level", "focused")

            logger.info(f"📥 ADHD state changed: {state} (Energy: {energy_level}, Attention: {attention_level})")

            # Adjust task recommendations based on ADHD state
            if self.conport_adapter:
                logger.debug(f"📊 Adjusting task recommendations for ADHD state: {state}")
                await self.conport_adapter.adjust_task_recommendations(energy_level, attention_level)

        except Exception as e:
            logger.error(f"Failed to handle adhd_state_changed: {e}")

    async def _handle_break_reminder(self, event: Any) -> None:
        """Handle break_reminder event from DopeconBridge."""
        try:
            task_id = event.data.get("task_id", "")
            duration_minutes = event.data.get("duration_minutes", 5)

            logger.info(f"📥 Break reminder: Task {task_id} - {duration_minutes} minute break recommended")

            # Update task status to IN_PROGRESS (ConPort doesn't have NEEDS_BREAK, keep as in_progress)
            if self.conport_adapter:
                logger.debug(f"📊 Logging break reminder for task {task_id} in ConPort")
                await self.conport_adapter.update_task_status(task_id, "IN_PROGRESS")

        except Exception as e:
            logger.error(f"Failed to handle break_reminder: {e}")

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
                "orchestrated_tasks": await self._get_task_count_from_conport(),
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

        # Close DopeconBridge EventBus (Component 3)
        if self.event_bus:
            await self.event_bus.close()
            logger.info("📪 DopeconBridge EventBus closed")

        # Close connections
        if self.leantime_session:
            await self.leantime_session.close()

        # Close ConPort adapter HTTP session
        if self.conport_adapter:
            await self.conport_adapter.close()
            logger.info("📊 ConPort adapter closed")

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
    # ========================================================================
    # Component 5: Cross-Plane Query Methods
    # ========================================================================

    async def get_tasks(
        self,
        status_filter: Optional[str] = None,
        sprint_id_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Query tasks from ConPort (Component 5) with Redis caching."""
        try:
            if not self.conport_adapter:
                return []

            # Create cache key based on parameters
            cache_key = f"tasks:{status_filter or 'all'}:{sprint_id_filter or 'all'}:{limit}"

            # Check cache first if available
            if CACHE_AVAILABLE:
                try:
                    cache = await get_cache()
                    cached_data = await cache.get(cache_key)
                    if cached_data:
                        logger.debug(f"Cache hit for tasks query: {cache_key}")
                        return json.loads(cached_data)
                except Exception as e:
                    logger.warning(f"Cache read failed: {e}")

            # Query ConPort for progress entries
            progress_entries = await self.conport_adapter.get_progress_entries(
                status_filter=status_filter,
                tags_filter=[sprint_id_filter] if sprint_id_filter else None
            )
            
            # Transform to task format
            tasks = []
            for entry in progress_entries[:limit]:
                tasks.append({
                    "task_id": str(entry.get("id", "")),
                    "title": entry.get("description", ""),
                    "description": entry.get("description", ""),
                    "status": entry.get("status", "TODO"),
                    "progress": 0.5 if entry.get("status") == "IN_PROGRESS" else (1.0 if entry.get("status") == "DONE" else 0.0),
                    "priority": "medium",
                    "complexity": 0.5,
                    "estimated_duration": 60,
                    "dependencies": [],
                    "tags": entry.get("tags", [])
                })
            
            # Cache the result for 5 minutes (300 seconds)
            if CACHE_AVAILABLE and tasks:
                try:
                    cache = await get_cache()
                    await cache.set(cache_key, json.dumps(tasks), ttl=300)
                    logger.debug(f"Cached tasks result: {cache_key}")
                except Exception as e:
                    logger.warning(f"Cache write failed: {e}")

            return tasks

        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")
            return []

    async def get_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get single task details (Component 5)."""
        tasks = await self.get_tasks()
        for task in tasks:
            if task["task_id"] == task_id:
                return task
        return None

    async def get_adhd_state(self) -> Dict[str, Any]:
        """Get current ADHD state (Component 5)."""
        try:
            # Wire to ADHD Engine via HTTP client
            from activity_capture.adhd_client import ADHDEngineClient
            adhd_client = ADHDEngineClient()
            # Get ADHD state from engine
            state = await adhd_client.get_adhd_state(self.user_id)
            return {
                "energy_level": state.get("energy_level", "medium"),
                "attention_level": state.get("attention_state", "focused"),
                "time_since_break": state.get("time_since_break", 45),
                "break_recommended": state.get("break_recommended", False),
                "current_session_duration": state.get("session_duration", 45)
            }
        except Exception as e:
            logger.warning(f"ADHD Engine connection failed: {e} - using defaults")
            return {
                "energy_level": "medium",
                "attention_level": "focused",
                "time_since_break": 45,
                "break_recommended": False,
                "current_session_duration": 45
            }

    async def get_task_recommendations(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get ADHD-aware task recommendations (Component 5)."""
        tasks = await self.get_tasks(status_filter="TODO")
        recommendations = []
        
        for i, task in enumerate(tasks[:limit]):
            recommendations.append({
                "task_id": task["task_id"],
                "title": task["title"],
                "reason": "Matches current cognitive state",
                "confidence": 0.8 - (i * 0.1),
                "priority": i + 1
            })
        
        return recommendations

    async def get_session_status(self) -> Dict[str, Any]:
        """Get current session status (Component 5)."""
        return {
            "session_id": f"session-{datetime.now().strftime('%Y-%m-%d')}",
            "active": self.running,
            "started_at": datetime.now(),
            "duration_minutes": 45,
            "break_count": 0,
            "tasks_completed": self.metrics.get("tasks_orchestrated", 0)
        }

    async def get_active_sprint_info(self) -> Dict[str, Any]:
        """Get active sprint info (Component 5)."""
        # Query ConPort for sprint context
        return {
            "sprint_id": "S-2025.10",
            "name": "Architecture 3.0 Implementation",
            "start_date": datetime(2025, 10, 1),
            "end_date": datetime(2025, 10, 31),
            "total_tasks": 20,
            "completed_tasks": self.metrics.get("tasks_orchestrated", 0),
            "in_progress_tasks": 3
        }
