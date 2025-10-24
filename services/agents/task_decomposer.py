"""
TaskDecomposer - ADHD-Optimized Task Decomposition Agent

Breaks complex tasks into manageable subtasks aligned with ADHD focus windows.

Features:
- Progressive complexity loading (start easy → build momentum)
- 25-minute Pomodoro alignment
- 3-5 subtask limit (decision fatigue prevention)
- Energy-complexity mapping
- Integration with 5 agents (CognitiveGuardian, ToolOrchestrator, TwoPlane, ConPort, MemoryAgent)

Authority: Task planning and decomposition

Version: 1.0.0
Complexity: 0.5 (Medium)
Effort: 1 week (25 focus blocks)
"""

import asyncio
import logging
import math
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Task types for routing and tool selection."""
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    REFACTORING = "refactoring"
    DEBUGGING = "debugging"
    RESEARCH = "research"
    UNKNOWN = "unknown"


@dataclass
class TaskInput:
    """Input task for decomposition."""
    id: str
    description: str
    estimated_minutes: int
    complexity: float  # 0.0-1.0
    priority: int = 5  # 1-10
    tags: List[str] = field(default_factory=list)


@dataclass
class SubTask:
    """Decomposed subtask with ADHD optimizations."""
    id: str
    description: str
    estimated_minutes: int
    complexity: float  # 0.0-1.0
    energy_required: str  # "low", "medium", "high"
    dependencies: List[int]  # Indices of prerequisite subtasks
    parent_task_id: str
    task_type: TaskType = TaskType.UNKNOWN
    sequence_number: int = 0


@dataclass
class DecompositionResult:
    """Complete decomposition result with agent integrations."""
    subtasks: List[SubTask]
    readiness_validations: List[Dict[str, Any]] = field(default_factory=list)
    tool_assignments: List[Dict[str, Any]] = field(default_factory=list)
    plane_routing: Dict[str, List[SubTask]] = field(default_factory=dict)
    decomposition_decision_id: Optional[str] = None
    total_estimated_minutes: int = 0
    total_estimated_cost: float = 0.0
    complexity_distribution: List[float] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class TaskDecomposer:
    """
    ADHD-Optimized Task Decomposition Agent

    Breaks complex tasks into manageable subtasks with progressive complexity loading.

    Example:
        decomposer = TaskDecomposer(workspace_id="/path/to/project")

        task = TaskInput(
            id="T-001",
            description="Implement JWT authentication",
            estimated_minutes=120,
            complexity=0.8
        )

        result = await decomposer.decompose_task(task)
        print(f"Decomposed into {len(result.subtasks)} subtasks")

        for subtask in result.subtasks:
            print(f"  {subtask.description} ({subtask.estimated_minutes}min, "
                  f"complexity: {subtask.complexity}, energy: {subtask.energy_required})")
    """

    def __init__(
        self,
        workspace_id: str,
        cognitive_guardian: Optional[Any] = None,
        tool_orchestrator: Optional[Any] = None,
        two_plane_orchestrator: Optional[Any] = None,
        conport_client: Optional[Any] = None,
        memory_agent: Optional[Any] = None,
        min_subtasks: int = 3,
        max_subtasks: int = 5,
        pomodoro_minutes: int = 25
    ):
        """
        Initialize TaskDecomposer.

        Args:
            workspace_id: Absolute path to workspace
            cognitive_guardian: CognitiveGuardian instance for readiness checks
            tool_orchestrator: ToolOrchestrator for model/tool selection
            two_plane_orchestrator: TwoPlaneOrchestrator for routing
            conport_client: ConPort MCP client for logging
            memory_agent: MemoryAgent for session context
            min_subtasks: Minimum subtasks (ADHD: 3)
            max_subtasks: Maximum subtasks (ADHD: 5)
            pomodoro_minutes: Target minutes per subtask (default: 25)
        """
        self.workspace_id = workspace_id
        self.cognitive_guardian = cognitive_guardian
        self.tool_orchestrator = tool_orchestrator
        self.two_plane_orchestrator = two_plane_orchestrator
        self.conport_client = conport_client
        self.memory_agent = memory_agent

        # ADHD constraints
        self.min_subtasks = min_subtasks
        self.max_subtasks = max_subtasks
        self.pomodoro_minutes = pomodoro_minutes

        # Metrics
        self.decompositions_created = 0
        self.tasks_simplified = 0  # Tasks not needing decomposition
        self.total_subtasks_generated = 0

        logger.info(
            f"TaskDecomposer initialized (subtasks: {min_subtasks}-{max_subtasks}, "
            f"pomodoro: {pomodoro_minutes}min)"
        )

    async def decompose_task(
        self,
        task: TaskInput,
        validate_readiness: bool = True,
        assign_tools: bool = True,
        log_to_conport: bool = True
    ) -> DecompositionResult:
        """
        Decompose task into ADHD-friendly subtasks.

        Args:
            task: Input task to decompose
            validate_readiness: Check readiness with CognitiveGuardian
            assign_tools: Assign tools with ToolOrchestrator
            log_to_conport: Log decomposition to ConPort

        Returns:
            DecompositionResult with subtasks and agent integration data
        """
        logger.info(
            f"Decomposing task: '{task.description}' "
            f"({task.estimated_minutes}min, complexity: {task.complexity})"
        )

        # Check if decomposition needed
        if not self._needs_decomposition(task):
            logger.info("Task already ADHD-optimal, no decomposition needed")
            self.tasks_simplified += 1

            # Return original task as single subtask
            subtask = SubTask(
                id=f"{task.id}-1",
                description=task.description,
                estimated_minutes=task.estimated_minutes,
                complexity=task.complexity,
                energy_required=self._map_energy_requirement(task.complexity),
                dependencies=[],
                parent_task_id=task.id,
                sequence_number=1
            )

            return DecompositionResult(
                subtasks=[subtask],
                total_estimated_minutes=task.estimated_minutes,
                complexity_distribution=[task.complexity],
                recommendations=["Task is already ADHD-optimal (≤25min, <0.3 complexity)"]
            )

        # Generate subtasks
        subtasks = self._generate_subtasks(task)
        self.decompositions_created += 1
        self.total_subtasks_generated += len(subtasks)

        # Create result
        result = DecompositionResult(
            subtasks=subtasks,
            total_estimated_minutes=sum(st.estimated_minutes for st in subtasks),
            complexity_distribution=[st.complexity for st in subtasks]
        )

        # Add ADHD recommendations
        result.recommendations = self._generate_recommendations(task, subtasks)

        # Integration: CognitiveGuardian readiness validation
        if validate_readiness and self.cognitive_guardian:
            result.readiness_validations = await self._validate_subtasks_with_guardian(subtasks)

        # Integration: ToolOrchestrator tool/model assignment
        if assign_tools and self.tool_orchestrator:
            result.tool_assignments = await self._assign_tools_to_subtasks(subtasks)
            result.total_estimated_cost = sum(
                assignment.get("estimated_cost", 0.0)
                for assignment in result.tool_assignments
            )

        # Integration: TwoPlaneOrchestrator routing (always classify, even without orchestrator)
        result.plane_routing = await self._route_subtasks_to_planes(subtasks)

        # Integration: ConPort logging
        if log_to_conport and self.conport_client:
            result.decomposition_decision_id = await self._log_decomposition_to_conport(
                task, result
            )

        # Integration: MemoryAgent context update
        if self.memory_agent:
            await self._integrate_with_memory_agent(subtasks)

        logger.info(
            f"✅ Decomposition complete: {len(subtasks)} subtasks, "
            f"complexity range: {subtasks[0].complexity:.2f} → {subtasks[-1].complexity:.2f}"
        )

        return result

    def _needs_decomposition(self, task: TaskInput) -> bool:
        """
        Check if task needs decomposition.

        ADHD Rule: Tasks ≤25min AND complexity <0.3 are already optimal.

        Args:
            task: Input task

        Returns:
            True if decomposition needed, False otherwise
        """
        return task.estimated_minutes > self.pomodoro_minutes or task.complexity >= 0.3

    def _generate_subtasks(self, task: TaskInput) -> List[SubTask]:
        """
        Generate subtasks with progressive complexity loading.

        Algorithm:
        1. Calculate subtask count (3-5 based on duration and complexity)
        2. Distribute complexity progressively (start 50%, reach 100%)
        3. Assign energy requirements based on complexity
        4. Add sequential dependencies

        Args:
            task: Parent task

        Returns:
            List of ADHD-optimized subtasks
        """
        # Calculate subtask count
        subtask_count = self._calculate_subtask_count(task)

        # Progressive complexity distribution
        base_complexity = task.complexity * 0.5  # Start at 50%
        complexity_increment = (task.complexity - base_complexity) / max(subtask_count - 1, 1)

        # Generate subtasks
        subtasks = []
        minutes_per_subtask = task.estimated_minutes // subtask_count

        for i in range(subtask_count):
            # Progressive complexity
            subtask_complexity = base_complexity + (i * complexity_increment)
            subtask_complexity = round(min(subtask_complexity, 1.0), 2)

            # Energy requirement mapping
            energy_required = self._map_energy_requirement(subtask_complexity)

            # Dependencies (sequential by default)
            dependencies = [i - 1] if i > 0 else []

            # Infer task type from description and sequence
            task_type = self._infer_task_type(task.description, i, subtask_count)

            # Generate description
            subtask_description = self._generate_subtask_description(
                task.description, i + 1, subtask_count, task_type
            )

            subtask = SubTask(
                id=f"{task.id}-{i + 1}",
                description=subtask_description,
                estimated_minutes=minutes_per_subtask,
                complexity=subtask_complexity,
                energy_required=energy_required,
                dependencies=dependencies,
                parent_task_id=task.id,
                task_type=task_type,
                sequence_number=i + 1
            )

            subtasks.append(subtask)

        return subtasks

    def _calculate_subtask_count(self, task: TaskInput) -> int:
        """
        Calculate optimal subtask count.

        Factors:
        - Duration: 1 subtask per 25 minutes (Pomodoro)
        - Complexity: Higher complexity needs more breakdown
        - ADHD limits: 3-5 subtasks

        Args:
            task: Input task

        Returns:
            Subtask count (3-5)
        """
        # Base: 1 subtask per Pomodoro
        count_by_duration = math.ceil(task.estimated_minutes / self.pomodoro_minutes)

        # Complexity multiplier: 0.5 → 1.0 = no change, 0.9 → 1.4 = +40%
        complexity_multiplier = 1.0 + (task.complexity - 0.5)
        count_by_complexity = int(count_by_duration * complexity_multiplier)

        # Apply ADHD limits
        return max(self.min_subtasks, min(self.max_subtasks, count_by_complexity))

    def _map_energy_requirement(self, complexity: float) -> str:
        """
        Map complexity to energy requirement.

        Uses CognitiveGuardian's energy-complexity mapping:
        - Low energy (< 0.4): Simple tasks
        - Medium energy (0.4-0.7): Moderate tasks
        - High energy (≥ 0.7): Complex tasks

        Args:
            complexity: Task complexity 0.0-1.0

        Returns:
            Energy level: "low", "medium", "high"
        """
        if complexity < 0.4:
            return "low"
        elif complexity < 0.7:
            return "medium"
        else:
            return "high"

    def _infer_task_type(
        self,
        description: str,
        sequence: int,
        total: int
    ) -> TaskType:
        """
        Infer task type from description and sequence position.

        Heuristics:
        - Detect mixed tasks (design AND implement) → use position-based
        - Single-purpose tasks → use keyword matching
        - Fallback: position-based inference

        Args:
            description: Task description
            sequence: Subtask sequence (0-indexed)
            total: Total subtask count

        Returns:
            TaskType enum
        """
        desc_lower = description.lower()

        # Detect mixed tasks (multiple task type keywords)
        keyword_groups = [
            ["design", "plan", "architecture", "schema"],
            ["implement", "build", "create", "code"],
            ["test", "validate", "verify"],
            ["document", "readme", "guide"],
            ["refactor", "optimize", "improve"],
            ["debug", "fix", "bug"],
            ["research", "investigate", "explore"]
        ]

        matches = sum(1 for group in keyword_groups if any(word in desc_lower for word in group))

        # Mixed task (2+ keyword groups) → use position-based inference
        if matches >= 2:
            if sequence == 0:
                return TaskType.DESIGN  # First: planning/design
            elif sequence == total - 1:
                return TaskType.TESTING  # Last: testing/validation
            else:
                return TaskType.IMPLEMENTATION  # Middle: implementation

        # Single-purpose task → keyword matching
        if any(word in desc_lower for word in ["design", "plan", "architecture", "schema"]):
            return TaskType.DESIGN
        elif any(word in desc_lower for word in ["test", "validate", "verify"]):
            return TaskType.TESTING
        elif any(word in desc_lower for word in ["document", "readme", "guide"]):
            return TaskType.DOCUMENTATION
        elif any(word in desc_lower for word in ["refactor", "optimize", "improve"]):
            return TaskType.REFACTORING
        elif any(word in desc_lower for word in ["debug", "fix", "bug"]):
            return TaskType.DEBUGGING
        elif any(word in desc_lower for word in ["research", "investigate", "explore"]):
            return TaskType.RESEARCH

        # Fallback: position-based inference
        if sequence == 0:
            return TaskType.DESIGN
        elif sequence == total - 1:
            return TaskType.TESTING
        else:
            return TaskType.IMPLEMENTATION

    def _generate_subtask_description(
        self,
        parent_description: str,
        sequence: int,
        total: int,
        task_type: TaskType
    ) -> str:
        """
        Generate ADHD-friendly subtask description.

        Format: "{parent} - {phase} (Part {n}/{total})"

        Args:
            parent_description: Parent task description
            sequence: Subtask sequence number (1-indexed)
            total: Total subtask count
            task_type: Inferred task type

        Returns:
            Clear, actionable subtask description
        """
        # Phase names based on task type and sequence
        phase_map = {
            TaskType.DESIGN: ["Design", "Plan", "Specify"],
            TaskType.IMPLEMENTATION: ["Implement", "Build", "Create"],
            TaskType.TESTING: ["Test", "Validate", "Verify"],
            TaskType.DOCUMENTATION: ["Document", "Write guide", "Update docs"],
            TaskType.REFACTORING: ["Refactor", "Optimize", "Improve"],
            TaskType.DEBUGGING: ["Debug", "Fix", "Resolve"],
            TaskType.RESEARCH: ["Research", "Investigate", "Explore"]
        }

        # Position-based phase (if type is unknown)
        if task_type == TaskType.UNKNOWN:
            if sequence == 1:
                phase = "Setup"
            elif sequence == total:
                phase = "Finalize"
            else:
                phase = "Work on"
        else:
            phases = phase_map.get(task_type, ["Work on"])
            phase = phases[0]  # Use first phase name

        return f"{parent_description} - {phase} (Part {sequence}/{total})"

    def _generate_recommendations(
        self,
        task: TaskInput,
        subtasks: List[SubTask]
    ) -> List[str]:
        """
        Generate ADHD-friendly recommendations.

        Args:
            task: Parent task
            subtasks: Generated subtasks

        Returns:
            List of actionable recommendations
        """
        recommendations = []

        # Progressive complexity
        recommendations.append(
            f"Start with Part 1 (complexity {subtasks[0].complexity:.1f}) to build momentum"
        )

        # Energy matching
        high_energy_tasks = [st for st in subtasks if st.energy_required == "high"]
        if high_energy_tasks:
            recommendations.append(
                f"Schedule {len(high_energy_tasks)} high-energy tasks for morning/peak focus"
            )

        # Break reminders
        total_minutes = sum(st.estimated_minutes for st in subtasks)
        if total_minutes > 50:
            recommendations.append(
                f"Total time: {total_minutes}min - Take breaks between subtasks"
            )

        # Complexity warning
        if subtasks[-1].complexity >= 0.8:
            recommendations.append(
                f"Final task (complexity {subtasks[-1].complexity:.1f}) is complex - "
                "Save for when you're fresh"
            )

        return recommendations

    async def _validate_subtasks_with_guardian(
        self,
        subtasks: List[SubTask]
    ) -> List[Dict[str, Any]]:
        """
        Validate subtasks with CognitiveGuardian.

        Args:
            subtasks: Subtasks to validate

        Returns:
            List of readiness validations
        """
        if not self.cognitive_guardian:
            return []

        validations = []

        for subtask in subtasks:
            try:
                readiness = await self.cognitive_guardian.check_task_readiness(
                    task_complexity=subtask.complexity,
                    task_energy_required=subtask.energy_required
                )

                validations.append({
                    "subtask_id": subtask.id,
                    "ready": readiness["ready"],
                    "reason": readiness.get("reason", ""),
                    "confidence": readiness.get("confidence", 0.0),
                    "suggestion": readiness.get("suggestion", "")
                })
            except Exception as e:
                logger.error(f"Guardian validation failed for {subtask.id}: {e}")
                validations.append({
                    "subtask_id": subtask.id,
                    "ready": True,  # Fail open
                    "reason": "Validation unavailable",
                    "confidence": 0.5
                })

        return validations

    async def _assign_tools_to_subtasks(
        self,
        subtasks: List[SubTask]
    ) -> List[Dict[str, Any]]:
        """
        Assign tools and models to subtasks via ToolOrchestrator.

        Args:
            subtasks: Subtasks to assign tools

        Returns:
            List of tool assignments
        """
        if not self.tool_orchestrator:
            return []

        assignments = []

        for subtask in subtasks:
            try:
                # Map TaskType to tool orchestrator task type
                task_type_map = {
                    TaskType.DESIGN: "planning",
                    TaskType.IMPLEMENTATION: "implementation",
                    TaskType.TESTING: "testing",
                    TaskType.DOCUMENTATION: "documentation",
                    TaskType.REFACTORING: "refactoring",
                    TaskType.DEBUGGING: "debugging",
                    TaskType.RESEARCH: "research"
                }

                orch_task_type = task_type_map.get(subtask.task_type, "implementation")

                # Select tools
                tools = self.tool_orchestrator.select_tools_for_task(
                    task_type=orch_task_type,
                    complexity=subtask.complexity
                )

                assignments.append({
                    "subtask_id": subtask.id,
                    "tools": tools,
                    "estimated_cost": getattr(tools, 'estimated_cost', 0.0),
                    "estimated_latency": getattr(tools, 'estimated_latency', '0ms')
                })
            except Exception as e:
                logger.error(f"Tool assignment failed for {subtask.id}: {e}")
                assignments.append({
                    "subtask_id": subtask.id,
                    "tools": None,
                    "estimated_cost": 0.0,
                    "estimated_latency": "unknown"
                })

        return assignments

    async def _route_subtasks_to_planes(
        self,
        subtasks: List[SubTask]
    ) -> Dict[str, List[SubTask]]:
        """
        Route subtasks to PM or Cognitive plane via TwoPlaneOrchestrator.

        Routing heuristics:
        - Design/planning → PM plane
        - Implementation → Cognitive plane
        - Testing → Cognitive plane (or PM for test planning)

        Args:
            subtasks: Subtasks to route

        Returns:
            Dict with "pm_plane" and "cognitive_plane" subtask lists
        """
        pm_tasks = []
        cognitive_tasks = []

        for subtask in subtasks:
            if subtask.task_type in [TaskType.DESIGN, TaskType.RESEARCH]:
                pm_tasks.append(subtask)
            elif subtask.task_type == TaskType.DOCUMENTATION:
                # Documentation can go either way, default to PM
                pm_tasks.append(subtask)
            else:
                # Implementation, testing, debugging, refactoring → Cognitive
                cognitive_tasks.append(subtask)

        return {
            "pm_plane": pm_tasks,
            "cognitive_plane": cognitive_tasks
        }

    async def _log_decomposition_to_conport(
        self,
        task: TaskInput,
        result: DecompositionResult
    ) -> Optional[str]:
        """
        Log decomposition to ConPort knowledge graph.

        Creates:
        - Decision record for decomposition
        - Progress entries for each subtask
        - Links between decision and subtasks

        Args:
            task: Parent task
            result: Decomposition result

        Returns:
            Decision ID if successful, None otherwise
        """
        if not self.conport_client:
            return None

        try:
            # Log decision
            decision_id = await self.conport_client.log_decision(
                workspace_id=self.workspace_id,
                summary=f"Decomposed '{task.description}' into {len(result.subtasks)} ADHD-optimized subtasks",
                rationale=(
                    f"Parent task: {task.estimated_minutes}min, complexity {task.complexity:.2f}. "
                    f"Exceeds ADHD thresholds ({self.pomodoro_minutes}min, 0.3 complexity). "
                    f"Applied progressive complexity loading: "
                    f"{result.subtasks[0].complexity:.2f} → {result.subtasks[-1].complexity:.2f}. "
                    f"Subtask count: {len(result.subtasks)} (ADHD limit: {self.min_subtasks}-{self.max_subtasks})."
                ),
                implementation_details=(
                    f"Subtasks:\n" +
                    "\n".join([
                        f"  {i+1}. {st.description} ({st.estimated_minutes}min, "
                        f"complexity {st.complexity:.2f}, energy: {st.energy_required})"
                        for i, st in enumerate(result.subtasks)
                    ])
                ),
                tags=["task-decomposition", "adhd-optimization", "week-9", "task-decomposer"]
            )

            # Create progress entries for subtasks
            for subtask in result.subtasks:
                progress_id = await self.conport_client.log_progress(
                    workspace_id=self.workspace_id,
                    status="TODO",
                    description=subtask.description
                )

                # Link subtask to decomposition decision
                await self.conport_client.link_conport_items(
                    workspace_id=self.workspace_id,
                    source_item_type="decision",
                    source_item_id=str(decision_id),
                    target_item_type="progress_entry",
                    target_item_id=str(progress_id),
                    relationship_type="decomposes_into",
                    description=f"Subtask {subtask.sequence_number}/{len(result.subtasks)}"
                )

            logger.info(f"✅ Logged decomposition to ConPort (decision ID: {decision_id})")
            return str(decision_id)

        except Exception as e:
            logger.error(f"ConPort logging failed: {e}")
            return None

    async def _integrate_with_memory_agent(self, subtasks: List[SubTask]) -> None:
        """
        Update MemoryAgent with decomposition context.

        Args:
            subtasks: Decomposed subtasks
        """
        if not self.memory_agent or not hasattr(self.memory_agent, 'current_session'):
            return

        try:
            session = self.memory_agent.current_session
            if session:
                # Update session with first subtask
                session.current_task = f"Working on: {subtasks[0].description}"
                session.complexity = subtasks[0].complexity

                # Add decomposition metadata
                if hasattr(session, '__dict__'):
                    session.decomposition_active = True
                    session.total_subtasks = len(subtasks)
                    session.completed_subtasks = 0
                    session.current_subtask_index = 0

                await self.memory_agent.save_session()
                logger.info("✅ Updated MemoryAgent with decomposition context")
        except Exception as e:
            logger.error(f"MemoryAgent integration failed: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get TaskDecomposer metrics.

        Returns:
            Performance and usage metrics
        """
        return {
            "decompositions_created": self.decompositions_created,
            "tasks_simplified": self.tasks_simplified,
            "total_subtasks_generated": self.total_subtasks_generated,
            "avg_subtasks_per_decomposition": (
                self.total_subtasks_generated / max(self.decompositions_created, 1)
            ),
            "adhd_constraints": {
                "min_subtasks": self.min_subtasks,
                "max_subtasks": self.max_subtasks,
                "pomodoro_minutes": self.pomodoro_minutes
            }
        }


# Example usage
if __name__ == "__main__":
    async def demo():
        """Demonstrate TaskDecomposer capabilities."""

        print("\n" + "="*70)
        print("TaskDecomposer Demo - ADHD Task Decomposition")
        print("="*70 + "\n")

        # Initialize decomposer
        decomposer = TaskDecomposer(workspace_id="/Users/hue/code/dopemux-mvp")

        # Example 1: Complex task needing decomposition
        print("Example 1: Complex Task (120min, 0.8 complexity)\n")

        task1 = TaskInput(
            id="T-001",
            description="Implement JWT authentication system",
            estimated_minutes=120,
            complexity=0.8,
            tags=["security", "authentication"]
        )

        result1 = await decomposer.decompose_task(
            task1,
            validate_readiness=False,
            assign_tools=False,
            log_to_conport=False
        )

        print(f"Parent: {task1.description}")
        print(f"  Duration: {task1.estimated_minutes}min")
        print(f"  Complexity: {task1.complexity}\n")

        print(f"Decomposed into {len(result1.subtasks)} subtasks:\n")
        for subtask in result1.subtasks:
            print(f"  {subtask.sequence_number}. {subtask.description}")
            print(f"     Time: {subtask.estimated_minutes}min | "
                  f"Complexity: {subtask.complexity:.2f} | "
                  f"Energy: {subtask.energy_required}")
            if subtask.dependencies:
                print(f"     Depends on: Part {subtask.dependencies[0] + 1}")
            print()

        print("Recommendations:")
        for rec in result1.recommendations:
            print(f"  • {rec}")
        print()

        # Example 2: Simple task (no decomposition)
        print("="*70)
        print("\nExample 2: Simple Task (15min, 0.2 complexity)\n")

        task2 = TaskInput(
            id="T-002",
            description="Fix typo in README.md",
            estimated_minutes=15,
            complexity=0.2
        )

        result2 = await decomposer.decompose_task(
            task2,
            validate_readiness=False,
            assign_tools=False,
            log_to_conport=False
        )

        print(f"Task: {task2.description}")
        print(f"  Duration: {task2.estimated_minutes}min")
        print(f"  Complexity: {task2.complexity}\n")

        print(f"Result: {len(result2.subtasks)} subtask (no decomposition needed)")
        print(f"  {result2.subtasks[0].description}")
        print(f"  Reason: {result2.recommendations[0]}\n")

        # Show metrics
        print("="*70)
        print("\nTaskDecomposer Metrics:")
        print("="*70)
        metrics = decomposer.get_metrics()
        for key, value in metrics.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")
        print()

    # Run demo
    asyncio.run(demo())
