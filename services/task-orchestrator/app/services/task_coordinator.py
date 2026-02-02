"""
Task Coordinator - Phase 2 Task Orchestrator

Coordinates task execution across agents, monitors ADHD state, and manages task synchronization
with ConPort. Handles task batching, dependency resolution, and ADHD-aware task scheduling.

Key Responsibilities:
- Orchestrate task execution across multiple agents
- Monitor ADHD state and adjust task allocation dynamically
- Manage task dependencies and blocking states
- Sync task progress with ConPort knowledge graph
- Handle context switching and state preservation
- Implement 25-minute focus sessions with break recommendations

Integration Points:
- Uses ConPortEventAdapter for bidirectional synchronization
- Integrates with CognitiveGuardian for task prioritization
- Monitors ADHD state from ADHD Engine
- Coordinates with EventBus for cross-system events

Usage:
    coordinator = TaskCoordinator()
    await coordinator.coordinate_tasks(tasks, current_adhd_state)
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum

import asyncio
import logging

from app.services.enhanced_orchestrator import OrchestrationTask, TaskStatus
from app.adapters.conport_adapter import ConPortEventAdapter
from intelligence.cognitive_load_balancer import CognitiveLoadBalancer
from intelligence.context_switch_recovery import ContextSwitchRecovery
from pal_client import TaskOrchestratorPALClient

logger = logging.getLogger(__name__)

@dataclass
class CoordinationState:
    """Current coordination state for task execution"""
    current_adhd_state: Dict[str, str]  # energy, attention, mode
    active_tasks: List[str]  # task IDs in progress
    blocked_tasks: List[str]  # tasks waiting on dependencies
    focus_session_timer: int  # seconds since session start
    current_batch: List[OrchestrationTask]  # tasks in current batch
    session_id: str
    coordination_mode: str = "ADHD_ADAPTIVE"
    workspace_path: Optional[str] = None  # Track workspace context

class TaskCoordinator:
    """
    Central coordinator for task execution and synchronization.

    Manages:
    - Task batching based on cognitive load
    - ADHD-aware task sequencing
    - Dependency resolution across agents
    - Context switching detection
    - Break recommendations
    - ConPort synchronization
    """

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.conport_adapter = ConPortEventAdapter(workspace_id)
        self.cognitive_guardian = CognitiveLoadBalancer(workspace_id=workspace_id, conport_client=self.conport_adapter)
        self.context_recovery = ContextSwitchRecovery(workspace_id, self.conport_adapter)
        self.pal_client = TaskOrchestratorPALClient("http://localhost:3003", {})

        # State tracking
        self.coordination_state = CoordinationState(
            current_adhd_state={},
            active_tasks=[],
            blocked_tasks=[],
            focus_session_timer=0,
            current_batch=[],
            session_id=f"coord_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )

        # Configuration
        self.max_batch_size = 3  # ADHD-friendly batch limits
        self.focus_session_duration = 1500  # 25 minutes in seconds
        self.break_duration = 300  # 5 minute breaks
        self.max_context_switches = 2

    async def coordinate_tasks(
        self,
        tasks: List[OrchestrationTask],
        current_adhd_state: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Main coordination loop for task execution.

        Args:
            tasks: List of OrchestrationTasks to coordinate
            current_adhd_state: Current ADHD metrics (energy, attention, load)

        Returns:
            Dict with execution plan, batch assignments, and next actions
        """
        logger.info(f"🚀 Coordinating {len(tasks)} tasks with ADHD state: {current_adhd_state}")

        # Update coordination state
        self.coordination_state.current_adhd_state = current_adhd_state
        self.coordination_state.active_tasks = [t.id for t in tasks if t.status == TaskStatus.IN_PROGRESS]

        # Step 1: Assess task batch based on cognitive capacity
        batch_plan = await self._assess_cognitive_batch(tasks, current_adhd_state)

        # Step 2: Resolve dependencies
        resolved_tasks = await self._resolve_dependencies(tasks)

        # Step 3: Sequence tasks by ADHD-aware priorities using Zen planner for complex tasks
        sequenced_plan = await self._sequence_tasks_with_zen(resolved_tasks, current_adhd_state)

        # Step 4: Sync coordination state to ConPort
        await self._sync_coordination_state()

        # Step 5: Execute batch with monitoring
        execution_results = await self._execute_batch(sequenced_plan)

        return {
            "coordination_id": self.coordination_state.session_id,
            "batch_plan": batch_plan,
            "sequence": sequenced_plan,
            "execution_results": execution_results,
            "adhd_state": current_adhd_state,
            "recommendations": self._generate_recommendations(current_adhd_state),
            "next_batch_size": len(execution_results['completed']) if execution_results else 0
        }

    async def _sequence_tasks_with_zen(
        self,
        tasks: List[OrchestrationTask],
        adhd_state: Dict[str, str]
    ) -> Dict[str, Any]:
        """Sequence tasks using Zen planner for complex task prioritization."""
        try:
            # Check if we have complex tasks that would benefit from Zen planning
            complex_tasks = [t for t in tasks if getattr(t, 'complexity_score', 0) > 0.7 or len(tasks) > 5]

            if complex_tasks and len(tasks) >= 3:
                # Use Zen for intelligent prioritization
                task_data = [{'description': t.description, 'complexity': getattr(t, 'complexity_score', 0.5),
                             'estimated_minutes': getattr(t, 'estimated_duration', 30)} for t in tasks]

                zen_context = {
                    'energy_level': adhd_state.get('energy', 'MEDIUM'),
                    'attention_state': adhd_state.get('attention', 'FOCUSED'),
                    'cognitive_load': float(adhd_state.get('cognitive_load', 0.5)),
                    'available_time': 120,  # Assume 2 hours available
                    'peak_hours': adhd_state.get('peak_hours', 'morning')
                }

                zen_prioritization = await self.pal_client.prioritize_task_queue(task_data, zen_context)

                # Apply Zen prioritization to tasks
                prioritized_indices = zen_prioritization.get('prioritized_order', list(range(len(tasks))))
                prioritized_tasks = [tasks[i] for i in prioritized_indices]

                return {
                    "tasks": prioritized_tasks,
                    "strategy": "zen_intelligent",
                    "batches": zen_prioritization.get('execution_batches', [list(range(len(tasks)))]),
                    "break_schedule": zen_prioritization.get('break_schedule', []),
                    "rationale": zen_prioritization.get('rationale', 'Zen-optimized sequencing')
                }
            else:
                # Fall back to standard sequencing for simpler cases
                return await self._sequence_tasks(tasks, adhd_state)

        except Exception as e:
            logger.warning(f"Zen task sequencing failed: {e}")
            # Fall back to standard sequencing
            return await self._sequence_tasks(tasks, adhd_state)

    async def break_down_complex_task(self, task: OrchestrationTask, adhd_context: Dict[str, Any]) -> Dict[str, Any]:
        """Use Zen planner to break down a complex task into manageable subtasks."""
        try:
            task_data = {
                'description': task.description,
                'complexity': getattr(task, 'complexity_score', 0.5),
                'estimated_minutes': getattr(task, 'estimated_duration', 30)
            }

            zen_breakdown = await self.pal_client.plan_task_breakdown(task_data, adhd_context)

            # Convert Zen breakdown to OrchestrationTask subtasks
            subtasks = []
            for subtask_data in zen_breakdown.get('subtasks', []):
                subtask = OrchestrationTask(
                    id=f"{task.id}_sub_{len(subtasks)}",
                    description=subtask_data['description'],
                    complexity_score=subtask_data.get('complexity_score', 0.3),
                    estimated_duration=subtask_data['duration_minutes'],
                    dependencies=subtask_data.get('dependencies', []),
                    status=TaskStatus.PENDING
                )
                subtasks.append(subtask)

            return {
                'original_task': task,
                'subtasks': subtasks,
                'execution_order': zen_breakdown.get('execution_order', []),
                'total_duration': zen_breakdown.get('total_duration', task.estimated_duration),
                'break_points': zen_breakdown.get('break_points', []),
                'progress_checkpoints': zen_breakdown.get('progress_checkpoints', []),
                'strategy': 'zen_breakdown'
            }

        except Exception as e:
            logger.warning(f"Zen task breakdown failed: {e}")
            return {
                'original_task': task,
                'subtasks': [task],  # Return original task unchanged
                'execution_order': [task.id],
                'total_duration': task.estimated_duration,
                'break_points': [],
                'progress_checkpoints': [],
                'strategy': 'fallback'
            }

    async def _assess_cognitive_batch(
        self,
        tasks: List[OrchestrationTask],
        adhd_state: Dict[str, str]
    ) -> Dict[str, List[str]]:
        """
        Assess which tasks can be batched based on cognitive capacity.

        Considers:
        - Task complexity scores
        - Cognitive load capacity from ADHD state
        - Task dependencies
        - Break recommendations
        """
        cognitive_capacity = self.cognitive_guardian.assess_capacity(adhd_state)

        # Filter and score tasks
        viable_tasks = []
        for task in tasks:
            load_score = self.cognitive_guardian.calculate_load(task)

            if load_score <= cognitive_capacity:
                viable_tasks.append({
                    "task": task,
                    "load": load_score,
                    "energy_cost": self._estimate_energy_cost(task, adhd_state)
                })
            else:
                logger.info(f"⏳ Task {task.id} deferred: complexity {load_score:.2f} > capacity {cognitive_capacity:.2f}")

        # Sort by optimal sequence
        viable_tasks.sort(key=lambda x: x['load'])

        # Create batches (max 3 tasks per batch for ADHD)
        batches = []
        current_batch = []
        current_load = 0

        for task_data in viable_tasks:
            if current_load + task_data['load'] <= cognitive_capacity:
                current_batch.append(task_data['task'].id)
                current_load += task_data['load']
            else:
                if current_batch:
                    batches.append(current_batch)
                current_batch = [task_data['task'].id]
                current_load = task_data['load']

        if current_batch:
            batches.append(current_batch)

        logger.info(f"🧠 Created {len(batches)} batches with avg load {current_load/len(batches):.2f}")
        return {
            "total_tasks": len(tasks),
            "viable_tasks": len(viable_tasks),
            "deferred_tasks": len(tasks) - len(viable_tasks),
            "batches": batches,
            "capacity": cognitive_capacity
        }

    async def _resolve_dependencies(
        self,
        tasks: List[OrchestrationTask]
    ) -> List[OrchestrationTask]:
        """
        Resolve task dependencies across the batch.

        Blocks tasks until dependencies are resolved.
        """
        resolved = []
        blocked = []

        for task in tasks:
            if not task.dependencies:
                resolved.append(task)
            else:
                # Check if all dependencies are completed
                deps_completed = True
                for dep_id in task.dependencies:
                    dep_task = next((t for t in tasks if t.id == dep_id), None)
                    if dep_task and dep_task.status != TaskStatus.COMPLETED:
                        deps_completed = False
                        break

                if deps_completed:
                    resolved.append(task)
                else:
                    blocked.append(task)
                    logger.info(f"⛓️ Task {task.id} blocked by dependencies: {task.dependencies}")

        logger.info(f"🔗 Resolved {len(resolved)} tasks, {len(blocked)} blocked")
        return resolved + blocked

    async def _sequence_tasks(
        self,
        tasks: List[OrchestrationTask],
        adhd_state: Dict[str, str]
    ) -> List[str]:
        """
        Sequence tasks optimally based on ADHD state.

        High-energy → complex tasks
        Low-energy → simple tasks
        Focused → sequential tasks
        Scattered → parallel tasks (limited)
        """
        sequenced = []

        # Simple heuristic sequencing
        if adhd_state.get('energy') == 'high':
            # High energy: complex first
            tasks.sort(key=lambda t: t.complexity_score, reverse=True)
        else:
            # Low/medium energy: simple first
            tasks.sort(key=lambda t: t.complexity_score)

        # Attention state adjustments
        if adhd_state.get('attention') == 'scattered':
            # Limit parallel execution, interleave with breaks
            sequenced = [task.id for task in tasks[:2]]  # Max 2 for scattered
        else:
            # Focused attention: full sequence
            sequenced = [task.id for task in tasks]

        return sequenced

    async def _execute_batch(self, sequenced_tasks: List[str]) -> Dict[str, Any]:
        """
        Execute sequenced task batch with ADHD monitoring.
        """
        results = {
            "completed": [],
            "in_progress": [],
            "failed": [],
            "context_switches": 0
        }

        for task_id in sequenced_tasks:
            # Execute task (placeholder - actual execution via agents)
            task = next((t for t in self.coordination_state.active_tasks if t == task_id), None)
            if task:
                try:
                    # Simulate execution with monitoring
                    await self._monitor_execution(task)

                    # Update status
                    task.status = TaskStatus.IN_PROGRESS
                    results["in_progress"].append(task_id)

                    # Sync to ConPort
                    await self.conport_adapter.update_task_in_conport(task)

                except Exception as e:
                    logger.error(f"❌ Task execution failed {task_id}: {e}")
                    results["failed"].append(task_id)
                    break

        # Check for context switching
        switches = self.context_recovery.detect_switches()
        if switches > self.max_context_switches:
            logger.warning(f"⚠️ Detected {switches} context switches - recommending break")
            results["recommend_break"] = True

        logger.info(f"🏁 Batch execution: {len(results['in_progress'])} in progress, {len(results['failed'])} failed")
        return results

    def _estimate_energy_cost(self, task: OrchestrationTask, adhd_state: Dict[str, str]) -> float:
        """
        Estimate energy cost of task based on current ADHD state.
        """
        base_cost = task.complexity_score

        # Adjust for energy level
        energy_modifiers = {
            'high': 0.8,    # Tasks cost less energy when energetic
            'medium': 1.0,
            'low': 1.3      # Tasks cost more when low energy
        }

        energy_cost = base_cost * energy_modifiers.get(adhd_state.get('energy'), 1.0)
        return min(1.0, energy_cost)  # Cap at 1.0

    async def _monitor_execution(self, task: OrchestrationTask):
        """
        Monitor task execution with ADHD-aware breaks.
        """
        start_time = datetime.now()

        # Check energy decay over time
        while self.coordination_state.focus_session_timer < self.focus_session_duration:
            await asyncio.sleep(60)  # Check every minute

            # Check for break recommendation
            if self.cognitive_guardian.should_break(task):
                logger.info(f"⏸️ Break recommended for task {task.id}")
                await self._recommend_break()
                break

        duration = (datetime.now() - start_time).seconds
        logger.info(f"⏱️ Task {task.id} monitored for {duration} seconds")

    async def _recommend_break(self):
        """
        Recommend and take a break based on current state.
        """
        # Update ConPort with break activity
        break_recommendation = {
            "type": "adh_break",
            "duration": self.break_duration,
            "reason": "cognitive_load_threshold_exceeded",
            "timestamp": datetime.now()
        }

        await self.conport_adapter.log_progress(
            status="PAUSED",
            description=f"ADHD break: {break_recommendation['reason']}"
        )

        logger.info("☕ Taking recommended break...")
        await asyncio.sleep(self.break_duration)

    async def _sync_coordination_state(self):
        """
        Sync coordination state to ConPort for persistence.
        """
        state_data = asdict(self.coordination_state)
        state_data["workspace_id"] = self.workspace_id
        state_data["timestamp"] = datetime.now()

        await self.conport_adapter.update_task_in_conport(
            OrchestrationTask(
                id=self.coordination_state.session_id,
                title="Coordination State",
                description="ADHD Task Coordination State",
                status=TaskStatus.IN_PROGRESS,
                priority=1,
                complexity_score=0.2,
                estimated_minutes=5,
                assigned_agent=None,
                energy_required="low",
                custom_data=state_data  # Store full state as custom data
            )
        )

    def _generate_recommendations(self, adhd_state: Dict[str, str]) -> List[str]:
        """
        Generate task execution recommendations.
        """
        recommendations = []

        if adhd_state.get('energy') == 'low':
            recommendations.append("📉 Low energy: Consider simple tasks or take a break")
        elif adhd_state.get('energy') == 'high':
            recommendations.append("⚡ High energy: Ready for complex tasks")

        if adhd_state.get('attention') == 'scattered':
            recommendations.append("🌪️ Scattered attention: Limit to 1-2 simple tasks")
        elif adhd_state.get('attention') == 'focused':
            recommendations.append("🎯 Focused attention: Ready for deep work")

        if self.coordination_state.focus_session_timer > self.focus_session_duration * 0.8:
            recommendations.append("⏰ Focus session nearing limit - break soon recommended")

        return recommendations

# Example usage
async def main():
    coordinator = TaskCoordinator(workspace_id="/Users/hue/code/dopemux-mvp")

    # Sample tasks
    tasks = [
        OrchestrationTask(
            id="task-1",
            title="Implement ConPort adapter",
            description="Bidirectional sync implementation",
            complexity_score=0.7,
            energy_required="high",
            estimated_minutes=120,
            status=TaskStatus.PENDING
        ),
        OrchestrationTask(
            id="task-2",
            title="Update documentation",
            description="Phase 2 documentation updates",
            complexity_score=0.3,
            energy_required="low",
            estimated_minutes=45,
            status=TaskStatus.PENDING
        )
    ]

    adhd_state = {"energy": "medium", "attention": "focused", "load": 0.4}

    result = await coordinator.coordinate_tasks(tasks, adhd_state)
    logger.info(f"Coordination complete: {result}")

if __name__ == "__main__":
    asyncio.run(main())
