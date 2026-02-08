"""
Decomposition Coordinator

Coordinates task decomposition between:
- ADHD Engine (complexity detection, pattern decomposition)
- Task Orchestrator (Pal planner, ConPort persistence, Leantime sync)
- User consent (ADHD-friendly notifications)

This is the central orchestration layer for automatic and explicit decomposition.
"""
from typing import Awaitable, Callable, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
import logging
import asyncio

from .task_decomposition_assistant import (
    TaskDecompositionAssistant,
    TaskComplexity
)
from ...core.task_orchestrator_client import TaskOrchestratorClient

logger = logging.getLogger(__name__)


@dataclass
class DecompositionRequest:
    """Request to decompose a task."""
    task_id: str
    task_description: str
    estimated_minutes: int
    complexity_score: float
    reason: str  # Why decomposition is suggested
    adhd_context: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    user_consent: Optional[bool] = None


class DecompositionCoordinator:
    """
    Coordinates task decomposition across ADHD Engine and Task Orchestrator.
    
    Flow:
    1. ADHD Engine detects complexity (via event listener or explicit request)
    2. Coordinator analyzes and decides if decomposition needed
    3. If needed, asks user consent (ADHD-friendly)
    4. Calls Task Orchestrator → Pal planner (AI) or ADHD Engine (pattern fallback)
    5. Task Orchestrator handles:
       - Converting to OrchestrationTask objects
       - Persisting to ConPort (parent BLOCKED, subtasks TODO, relationships)
       - Syncing to Leantime (create child tickets)
    6. Returns structured breakdown to user
    """
    
    def __init__(
        self,
        decomposer: TaskDecompositionAssistant,
        task_orchestrator_url: str = "http://localhost:8000",
        bridge_client = None,  # AsyncDopeconBridgeClient
        adhd_state_provider: Optional[Callable[[], Union[Dict[str, Any], Awaitable[Dict[str, Any]]]]] = None,
        consent_provider: Optional[Callable[[DecompositionRequest], Union[str, bool, Awaitable[Union[str, bool]]]]] = None,
    ):
        """
        Initialize decomposition coordinator.
        
        Args:
            decomposer: ADHD Engine task decomposition assistant
            task_orchestrator_url: Task Orchestrator API URL
            bridge_client: DopeconBridge client for events (optional)
            adhd_state_provider: Optional callback for current ADHD state
            consent_provider: Optional callback for decomposition consent
        """
        self.decomposer = decomposer
        self.task_orchestrator_url = task_orchestrator_url
        self.bridge_client = bridge_client
        self.adhd_state_provider = adhd_state_provider
        self.consent_provider = consent_provider
        self.pending_requests: Dict[str, DecompositionRequest] = {}
        
        logger.info("DecompositionCoordinator initialized")
    
    async def should_auto_decompose(
        self,
        task: Dict[str, Any],
        adhd_state: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """
        Automatic decomposition detection.
        
        Trigger Conditions (ANY of):
        1. Time-based: Estimated duration >2 hours
        2. Complexity-based: Complexity score >0.6 (out of 1.0)
        3. Keyword-based: Description contains high-complexity keywords
        4. Paralysis detection: Task in TODO for >24h without progress
        5. Procrastination pattern: User skips task 3+ times
        
        Args:
            task: Task data (id, description, estimated_minutes, created_at, status)
            adhd_state: Current ADHD state (energy, attention, cognitive_load)
        
        Returns:
            (should_decompose: bool, reason: str)
        """
        task_id = task.get("id", "unknown")
        description = task.get("description", "")
        estimated_minutes = task.get("estimated_minutes", 30)
        created_at = task.get("created_at")
        status = task.get("status", "TODO")
        
        # 1. Time-based trigger
        if estimated_minutes > 120:
            return (True, f"Task exceeds 2h threshold ({estimated_minutes}min)")
        
        # 2. Complexity-based trigger
        complexity_level, _ = self.decomposer.analyze_task_complexity(
            description,
            estimated_minutes,
        )
        complexity_score = self._complexity_level_to_score(complexity_level)
        if complexity_score > 0.6:
            return (
                True,
                f"High complexity detected ({complexity_score:.2f}, "
                f"level: {complexity_level.value})"
            )
        
        # 3. Keyword trigger
        high_complexity_keywords = [
            "architecture", "migrate", "integrate", "research", "redesign",
            "refactor", "overhaul", "rewrite"
        ]
        if any(kw in description.lower() for kw in high_complexity_keywords):
            matched_kw = next(kw for kw in high_complexity_keywords if kw in description.lower())
            return (
                True,
                f"High-complexity keyword detected: '{matched_kw}' in '{description[:50]}...'"
            )
        
        # 4. Paralysis detection (task sitting in TODO >24h)
        if created_at and status == "TODO":
            try:
                created_iso = str(created_at).replace("Z", "+00:00")
                created_dt = datetime.fromisoformat(created_iso)
                age_hours = (datetime.now() - created_dt).total_seconds() / 3600
                if age_hours > 24:
                    return (
                        True,
                        f"Task stalled in TODO for {age_hours:.1f}h - possible paralysis"
                    )
            except (ValueError, TypeError) as e:
                logger.warning(f"Could not parse created_at timestamp: {e}")
        
        # 5. Procrastination pattern (future: integrate with procrastination_detector)
        # if self.procrastination_detector:
        #     pattern = await self.procrastination_detector.check_procrastination(task_id)
        #     if pattern and pattern.pattern_type in ["decision_paralysis", "overwhelm_avoidance"]:
        #         return (True, f"Procrastination pattern detected: {pattern.pattern_type}")
        
        return (False, "Task suitable for single execution")
    
    async def request_decomposition_consent(
        self,
        task: Dict[str, Any],
        reason: str,
        adhd_state: Dict[str, Any],
        estimated_subtasks: int = 6
    ) -> bool:
        """
        Ask user consent for automatic decomposition.
        
        ADHD Design Principles:
        - Consent-first: Never force decomposition
        - Adaptive verbosity: Based on energy level
        - Gentle notifications: Respect attention state
        - Clear reasoning: Explain why suggesting decomposition
        
        Args:
            task: Task data
            reason: Why decomposition is suggested
            adhd_state: Current ADHD state
            estimated_subtasks: Estimated number of subtasks
        
        Returns:
            True if user consents, False otherwise
        """
        energy = adhd_state.get("energy_level", "medium")
        attention = adhd_state.get("attention_state", "focused")
        task_id = str(task.get("id", "unknown"))
        task_desc = task.get("description", "Unknown task")
        request = DecompositionRequest(
            task_id=task_id,
            task_description=task_desc,
            estimated_minutes=int(task.get("estimated_minutes", 30)),
            complexity_score=float(task.get("complexity_score", 0.5)),
            reason=reason,
            adhd_context=adhd_state,
        )
        
        # Don't interrupt hyperfocus - queue for later
        if attention == "hyperfocus":
            logger.info(
                f"Queueing decomposition consent request for task {task_id} "
                "(user in hyperfocus, will ask later)"
            )
            self.pending_requests[task_id] = request
            return False
        
        # Build consent message (verbosity based on energy)
        if energy == "low":
            # Minimal message for low energy
            message = (
                f"🧠 Break down '{task_desc[:30]}...' into {estimated_subtasks} tasks?\n"
                f"Reason: {reason}\n"
                f"[Y/n/p for preview]: "
            )
        else:
            # Detailed message for medium/high energy
            message = f"""
🧠 ADHD Engine detected high-complexity task

Task: {task_desc}
Reason: {reason}
Estimated subtasks: ~{estimated_subtasks} (10-25min each)

💡 Recommendation: Break this down into micro-tasks
   - Reduces decision paralysis
   - Easier to start ("just 15 minutes")
   - Better progress tracking

Would you like to decompose this task?
[Y] Yes, break it down
[N] No, keep as single task
[P] Preview breakdown first

Your choice: """
        
        logger.info(
            f"{'Gentle' if attention == 'distracted' else 'Standard'} decomposition consent request: "
            f"{message[:120]}..."
        )
        response = await self._resolve_consent_response(request, default_response="y")
        
        # Parse response
        response_lower = str(response).lower().strip()
        
        if response_lower in ["y", "yes", ""]:
            logger.info(f"User consented to decompose task {task_id}")
            return True
        elif response_lower in ["p", "preview"]:
            preview = self.decomposer.decompose_task(
                task_id=task_id,
                task_description=task_desc,
                time_estimate=int(task.get("estimated_minutes", 30)),
                current_energy=energy,
            )
            preview_steps = [mt.description for mt in preview.micro_tasks[:3]]
            logger.info(
                f"Decomposition preview for {task_id}: "
                f"{' | '.join(preview_steps) if preview_steps else 'no micro-tasks generated'}"
            )
            return True
        else:
            logger.info(f"User declined decomposition for task {task_id}")
            return False
    
    async def decompose_task(
        self,
        task_id: str,
        method: str = "ai",  # "ai" (Pal), "pattern" (ADHD Engine fallback), "manual"
        adhd_context: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Orchestrate task decomposition.
        
        Flow:
        1. Get current ADHD state (if not provided)
        2. Analyze complexity (ADHD Engine)
        3. Call Task Orchestrator for decomposition
           - Task Orchestrator calls Pal planner (AI) or uses pattern fallback
           - Task Orchestrator persists to ConPort
           - Task Orchestrator syncs to Leantime
        4. Emit completion event
        5. Return structured breakdown
        
        Args:
            task_id: Task ID to decompose
            method: "ai" (Pal planner), "pattern" (ADHD Engine), or "manual"
            adhd_context: Current ADHD state (auto-detected if None)
            user_preferences: User preferences (max_subtasks, target_duration, etc.)
        
        Returns:
            {
                "parent_task_id": "T-123",
                "subtask_ids": ["T-124", "T-125", ...],
                "subtasks": [...],
                "total_estimated_minutes": 120,
                "method": "pal_planner",
                "leantime_synced": true,
                "conport_persisted": true
            }
        """
        logger.info(f"Starting decomposition for task {task_id} with method: {method}")
        
        # Get current ADHD state if not provided
        if adhd_context is None:
            adhd_context = await self._get_current_adhd_state()
        
        # Get task from Task Orchestrator
        async with TaskOrchestratorClient(self.task_orchestrator_url) as orch_client:
            # Health check
            if not await orch_client.health_check():
                raise RuntimeError(
                    f"Task Orchestrator unavailable at {self.task_orchestrator_url}"
                )
            
            # Complexity analysis (ADHD Engine)
            task = await orch_client.get_task(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found in Task Orchestrator")
            
            complexity_level, _ = self.decomposer.analyze_task_complexity(
                task.get("description", ""),
                task.get("estimated_minutes"),
            )
            complexity_score = self._complexity_level_to_score(complexity_level)
            logger.info(
                f"Task complexity: {complexity_score:.2f} "
                f"({complexity_level.value})"
            )
            
            # Determine decomposition method
            if method == "ai":
                # Task Orchestrator will call Pal planner
                orch_method = "pal"
            elif method == "pattern":
                # Task Orchestrator will use pattern fallback (or ADHD Engine can provide)
                orch_method = "pattern"
            else:
                orch_method = "manual"
            
            # Extract user preferences
            max_subtasks = user_preferences.get("max_subtasks", 7) if user_preferences else 7
            target_duration = user_preferences.get("target_duration_minutes", 15) if user_preferences else 15
            
            # Request decomposition from Task Orchestrator
            # Task Orchestrator handles:
            # - Calling Pal planner
            # - Converting to OrchestrationTask
            # - Persisting to ConPort
            # - Syncing to Leantime
            breakdown = await orch_client.request_decomposition(
                task_id=task_id,
                adhd_context=adhd_context,
                method=orch_method,
                max_subtasks=max_subtasks,
                target_duration_minutes=target_duration
            )
        
        # Emit completion event via DopeconBridge
        if self.bridge_client:
            try:
                await self.bridge_client.publish_event(
                    event_type="decomposition.completed",
                    data={
                        "parent_task_id": task_id,
                        "subtask_ids": breakdown.get("subtask_ids", []),
                        "method": method,
                        "total_duration": breakdown.get("total_estimated_minutes"),
                        "complexity_score": complexity_score,
                        "adhd_context": adhd_context
                    },
                    source="adhd-engine"
                )
                logger.info(f"Published decomposition.completed event for task {task_id}")
            except Exception as e:
                logger.error(f"Failed to publish decomposition event: {e}")
        
        logger.info(
            f"Decomposition complete for task {task_id}: "
            f"{len(breakdown.get('subtask_ids', []))} subtasks created"
        )
        
        return breakdown
    
    async def handle_task_event(self, event: Dict[str, Any]) -> None:
        """
        Handle task.created or task.updated events from EventBus.
        
        Automatic detection flow:
        1. Receive task event
        2. Check if decomposition needed (should_auto_decompose)
        3. If yes, request user consent
        4. If consent granted, trigger decomposition
        
        Args:
            event: Event data from DopeconBridge
                {
                    "event_type": "task.created",
                    "data": {...},
                    "source": "task-orchestrator",
                    "timestamp": "..."
                }
        """
        event_type = event.get("event_type")
        task_data = event.get("data", {})
        task_id = task_data.get("id")
        
        if not task_id:
            logger.warning(f"Received {event_type} event without task ID")
            return
        
        logger.info(f"Processing {event_type} for task {task_id}")
        
        # Get current ADHD state
        adhd_state = await self._get_current_adhd_state()
        
        # Auto-detection
        should_decompose, reason = await self.should_auto_decompose(
            task_data, adhd_state
        )
        
        if not should_decompose:
            logger.debug(f"Task {task_id} does not need decomposition: {reason}")
            return
        
        logger.info(f"Task {task_id} needs decomposition: {reason}")
        
        # Estimate subtask count for consent message
        complexity_level, _ = self.decomposer.analyze_task_complexity(
            task_data.get("description", ""),
            task_data.get("estimated_minutes"),
        )
        estimated_subtasks = min(
            7,
            max(3, int(self._complexity_level_to_score(complexity_level) * 10)),
        )
        
        # Request user consent
        user_consent = await self.request_decomposition_consent(
            task_data, reason, adhd_state, estimated_subtasks
        )
        
        if user_consent:
            # Trigger decomposition
            try:
                await self.decompose_task(task_id, method="ai", adhd_context=adhd_state)
                logger.info(f"Auto-decomposition completed for task {task_id}")
            except Exception as e:
                logger.error(f"Auto-decomposition failed for task {task_id}: {e}")
        else:
            logger.info(f"User declined auto-decomposition for task {task_id}")

    def _complexity_level_to_score(self, level: TaskComplexity) -> float:
        """Map TaskComplexity enum to normalized 0.0-1.0 score."""
        mapping = {
            TaskComplexity.TRIVIAL: 0.10,
            TaskComplexity.SIMPLE: 0.25,
            TaskComplexity.MODERATE: 0.50,
            TaskComplexity.COMPLEX: 0.70,
            TaskComplexity.VERY_COMPLEX: 0.85,
            TaskComplexity.EPIC: 0.95,
        }
        return mapping.get(level, 0.5)

    async def _resolve_consent_response(
        self,
        request: DecompositionRequest,
        default_response: str = "y",
    ) -> Union[str, bool]:
        """Resolve consent response via callback when available."""
        if not self.consent_provider:
            return default_response
        try:
            response = self.consent_provider(request)
            if asyncio.iscoroutine(response):
                response = await response
            return response
        except Exception as exc:
            logger.warning(f"Consent provider failed, using default response: {exc}")
            return default_response

    async def _get_current_adhd_state(self) -> Dict[str, Any]:
        """
        Retrieve current ADHD state from provider with safe fallback.
        """
        if self.adhd_state_provider:
            try:
                state = self.adhd_state_provider()
                if asyncio.iscoroutine(state):
                    state = await state
                if isinstance(state, dict) and state:
                    return state
            except Exception as exc:
                logger.warning(f"ADHD state provider failed, using fallback state: {exc}")

        return {
            "energy_level": "medium",
            "attention_state": "focused",
            "cognitive_load": 0.5,
        }
