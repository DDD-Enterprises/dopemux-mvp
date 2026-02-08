"""
Implicit Automation Workflows for Task Orchestrator

Seamless PM automation that handles sprint planning, progress tracking,
and retrospectives without developer cognitive overhead.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import re

logger = logging.getLogger(__name__)


class AutomationType(str, Enum):
    """Types of implicit automation."""
    SPRINT_PLANNING = "sprint_planning"
    TASK_DECOMPOSITION = "task_decomposition"
    PROGRESS_TRACKING = "progress_tracking"
    RETROSPECTIVE_GENERATION = "retrospective_generation"
    CONTEXT_MANAGEMENT = "context_management"
    BREAK_ORCHESTRATION = "break_orchestration"


class AutomationTrigger(str, Enum):
    """Automation trigger events."""
    SPRINT_CREATED = "sprint_created"
    SPRINT_ENDED = "sprint_ended"
    TASK_ASSIGNED = "task_assigned"
    FILE_MODIFIED = "file_modified"
    COMMIT_PUSHED = "commit_pushed"
    BREAK_TIME = "break_time"
    ENERGY_CHANGED = "energy_changed"
    CONTEXT_SWITCH = "context_switch"


@dataclass
class AutomationWorkflow:
    """Represents an automation workflow."""
    id: str
    automation_type: AutomationType
    trigger: AutomationTrigger
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    adhd_considerations: Dict[str, Any]

    # Execution state
    enabled: bool = True
    last_executed: Optional[datetime] = None
    execution_count: int = 0
    success_rate: float = 1.0


class ImplicitAutomationEngine:
    """
    Engine for seamless PM automation with ADHD optimizations.

    Handles:
    - Sprint planning automation with intelligent task analysis
    - Progress tracking that correlates code changes to task completion
    - Automatic retrospective generation with pattern analysis
    - Context preservation across workflow boundaries
    - Break orchestration that respects hyperfocus states
    """

    def __init__(
        self,
        workspace_id: str = "/Users/hue/code/dopemux-mvp",
        leantime_client: Any = None,
        conport_client: Any = None,
        serena_client: Any = None
    ):
        self.workspace_id = workspace_id
        self.leantime_client = leantime_client
        self.conport_client = conport_client
        self.serena_client = serena_client

        # Workflow definitions
        self.workflows: Dict[str, AutomationWorkflow] = {}
        self.trigger_handlers: Dict[AutomationTrigger, List[Callable]] = {}

        # Execution state
        self.automation_queue: asyncio.Queue = asyncio.Queue()
        self.active_automations: Set[str] = set()

        # ADHD optimization
        self.automation_batch_size = 3  # Process max 3 automations simultaneously
        self.cognitive_load_threshold = 0.7  # Pause automation if load too high

        # Statistics
        self.automation_stats = {
            "workflows_executed": 0,
            "sprints_automated": 0,
            "progress_correlations": 0,
            "retrospectives_generated": 0,
            "context_preservations": 0,
            "adhd_optimizations_applied": 0
        }
        self._sprint_analysis_store: Dict[str, Dict[str, Any]] = {}
        self._progress_correlation_store: List[Dict[str, Any]] = []
        self._progress_estimate_store: List[Dict[str, Any]] = []
        self._retrospective_store: Dict[str, Dict[str, Any]] = {}
        self._local_task_state: Dict[str, Dict[str, Any]] = {}

        # Background workers
        self.workers: List[asyncio.Task] = []
        self.running = False

    async def initialize(self) -> None:
        """Initialize automation engine and register workflows."""
        logger.info("🤖 Initializing Implicit Automation Engine...")
        self.running = True

        # Register default workflows
        await self._register_default_workflows()

        # Start background processing
        await self._start_automation_workers()

        logger.info("✅ Implicit Automation Engine ready!")

    async def _register_default_workflows(self) -> None:
        """Register default automation workflows."""
        # Sprint Planning Automation
        sprint_planning = AutomationWorkflow(
            id="auto_sprint_planning",
            automation_type=AutomationType.SPRINT_PLANNING,
            trigger=AutomationTrigger.SPRINT_CREATED,
            conditions={
                "min_tasks": 1,
                "max_tasks": 50,
                "has_description": True
            },
            actions=[
                {"type": "analyze_sprint_complexity", "priority": 1},
                {"type": "decompose_large_tasks", "priority": 2},
                {"type": "setup_conport_context", "priority": 3},
                {"type": "optimize_task_sequencing", "priority": 4},
                {"type": "setup_progress_tracking", "priority": 5}
            ],
            adhd_considerations={
                "chunk_large_tasks": True,
                "energy_level_matching": True,
                "break_point_identification": True,
                "cognitive_load_balancing": True
            }
        )

        # Progress Tracking Automation
        progress_tracking = AutomationWorkflow(
            id="auto_progress_tracking",
            automation_type=AutomationType.PROGRESS_TRACKING,
            trigger=AutomationTrigger.FILE_MODIFIED,
            conditions={
                "file_in_project": True,
                "active_task_exists": True,
                "meaningful_change": True
            },
            actions=[
                {"type": "correlate_file_to_task", "priority": 1},
                {"type": "estimate_completion_percentage", "priority": 2},
                {"type": "update_all_systems", "priority": 3},
                {"type": "check_milestone_progress", "priority": 4}
            ],
            adhd_considerations={
                "gentle_progress_feedback": True,
                "avoid_interruption_during_flow": True,
                "batch_multiple_changes": True
            }
        )

        # Retrospective Generation
        retrospective_automation = AutomationWorkflow(
            id="auto_retrospective",
            automation_type=AutomationType.RETROSPECTIVE_GENERATION,
            trigger=AutomationTrigger.SPRINT_ENDED,
            conditions={
                "sprint_has_completed_tasks": True,
                "minimum_sprint_duration": True
            },
            actions=[
                {"type": "analyze_completed_work", "priority": 1},
                {"type": "extract_adhd_patterns", "priority": 2},
                {"type": "identify_workflow_improvements", "priority": 3},
                {"type": "generate_retrospective_items", "priority": 4},
                {"type": "update_future_workflows", "priority": 5}
            ],
            adhd_considerations={
                "focus_on_positive_patterns": True,
                "gentle_improvement_suggestions": True,
                "celebrate_achievements": True,
                "avoid_overwhelming_analysis": True
            }
        )

        # Context Management Automation
        context_management = AutomationWorkflow(
            id="auto_context_management",
            automation_type=AutomationType.CONTEXT_MANAGEMENT,
            trigger=AutomationTrigger.CONTEXT_SWITCH,
            conditions={
                "context_switch_detected": True,
                "preservation_needed": True
            },
            actions=[
                {"type": "preserve_current_context", "priority": 1},
                {"type": "prepare_new_context", "priority": 2},
                {"type": "minimize_cognitive_transition", "priority": 3},
                {"type": "provide_orientation_guidance", "priority": 4}
            ],
            adhd_considerations={
                "seamless_transition": True,
                "context_breadcrumbs": True,
                "gentle_reorientation": True,
                "minimize_setup_overhead": True
            }
        )

        # Register workflows
        workflows = [sprint_planning, progress_tracking, retrospective_automation, context_management]
        for workflow in workflows:
            self.workflows[workflow.id] = workflow
            self._register_trigger_handler(workflow.trigger, workflow)

        logger.info(f"📝 Registered {len(workflows)} automation workflows")

    def _register_trigger_handler(self, trigger: AutomationTrigger, workflow: AutomationWorkflow) -> None:
        """Register workflow for specific trigger."""
        if trigger not in self.trigger_handlers:
            self.trigger_handlers[trigger] = []

        async def handler(trigger_data: Dict[str, Any]):
            await self._execute_workflow(workflow, trigger_data)

        self.trigger_handlers[trigger].append(handler)

    async def _start_automation_workers(self) -> None:
        """Start background automation processing workers."""
        workers = [
            self._automation_processor(),
            self._workflow_monitor(),
            self._adhd_optimization_monitor()
        ]

        self.workers = [asyncio.create_task(worker) for worker in workers]
        logger.info("👥 Automation workers started")

    # Workflow Execution Engine

    async def trigger_automation(
        self,
        trigger: AutomationTrigger,
        trigger_data: Dict[str, Any]
    ) -> None:
        """Trigger automation workflows for specific event."""
        try:
            # Get handlers for this trigger
            handlers = self.trigger_handlers.get(trigger, [])

            if not handlers:
                logger.debug(f"No automation handlers for trigger: {trigger.value}")
                return

            # Execute handlers with ADHD considerations
            for handler in handlers:
                # Check cognitive load before triggering
                current_load = await self._get_current_cognitive_load()

                if current_load > self.cognitive_load_threshold:
                    # Defer automation to reduce cognitive burden
                    logger.info(f"🧠 Deferring automation due to high cognitive load: {trigger.value}")
                    await self._defer_automation(trigger, trigger_data, delay_minutes=5)
                    continue

                # Execute automation
                try:
                    await handler(trigger_data)
                except Exception as e:
                    logger.error(f"Automation handler failed for {trigger.value}: {e}")

        except Exception as e:
            logger.error(f"Automation trigger failed: {e}")

    async def _execute_workflow(
        self,
        workflow: AutomationWorkflow,
        trigger_data: Dict[str, Any]
    ) -> bool:
        """Execute specific automation workflow."""
        try:
            if not workflow.enabled:
                return False

            # Check workflow conditions
            if not await self._check_workflow_conditions(workflow, trigger_data):
                logger.debug(f"Workflow conditions not met: {workflow.id}")
                return False

            # Add to active automations
            self.active_automations.add(workflow.id)

            logger.info(f"🤖 Executing automation: {workflow.automation_type.value}")

            # Execute workflow actions in priority order
            actions = sorted(workflow.actions, key=lambda a: a.get("priority", 5))

            for action in actions:
                success = await self._execute_workflow_action(
                    action, workflow, trigger_data
                )

                if not success:
                    logger.warning(f"Workflow action failed: {action['type']}")
                    # Continue with other actions rather than failing entire workflow

            # Update workflow execution metadata
            workflow.last_executed = datetime.now(timezone.utc)
            workflow.execution_count += 1
            workflow.success_rate = (
                ((workflow.success_rate * (workflow.execution_count - 1)) + 1.0)
                / workflow.execution_count
            )

            # Remove from active automations
            self.active_automations.discard(workflow.id)

            self.automation_stats["workflows_executed"] += 1
            logger.info(f"✅ Automation completed: {workflow.automation_type.value}")

            return True

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            workflow.execution_count += 1
            workflow.success_rate = (
                (workflow.success_rate * (workflow.execution_count - 1))
                / workflow.execution_count
            )
            self.active_automations.discard(workflow.id)
            return False

    async def _execute_workflow_action(
        self,
        action: Dict[str, Any],
        workflow: AutomationWorkflow,
        trigger_data: Dict[str, Any]
    ) -> bool:
        """Execute individual workflow action."""
        try:
            action_type = action.get("type", "unknown")

            # Route to specific action handlers
            if action_type == "analyze_sprint_complexity":
                return await self._action_analyze_sprint_complexity(trigger_data)
            elif action_type == "decompose_large_tasks":
                return await self._action_decompose_large_tasks(trigger_data)
            elif action_type == "setup_conport_context":
                return await self._action_setup_conport_context(trigger_data)
            elif action_type == "correlate_file_to_task":
                return await self._action_correlate_file_to_task(trigger_data)
            elif action_type == "estimate_completion_percentage":
                return await self._action_estimate_completion_percentage(trigger_data)
            elif action_type == "update_all_systems":
                return await self._action_update_all_systems(trigger_data)
            elif action_type == "analyze_completed_work":
                return await self._action_analyze_completed_work(trigger_data)
            elif action_type == "generate_retrospective_items":
                return await self._action_generate_retrospective_items(trigger_data)
            elif action_type == "preserve_current_context":
                return await self._action_preserve_current_context(trigger_data)
            else:
                logger.warning(f"Unknown workflow action: {action_type}")
                return False

        except Exception as e:
            logger.error(f"Workflow action execution failed: {e}")
            return False

    # Sprint Planning Automation Actions

    async def _action_analyze_sprint_complexity(self, trigger_data: Dict[str, Any]) -> bool:
        """Analyze sprint complexity for ADHD optimization."""
        try:
            sprint_id = trigger_data.get("sprint_id")
            sprint_tasks = trigger_data.get("tasks", [])

            logger.info(f"🔍 Analyzing sprint complexity: {sprint_id}")

            # Calculate overall sprint complexity
            total_complexity = 0.0
            high_complexity_tasks = []
            adhd_risk_tasks = []

            for task in sprint_tasks:
                task_complexity = task.get("complexity_score", 0.5)
                total_complexity += task_complexity

                if task_complexity > 0.8:
                    high_complexity_tasks.append(task)

                # Check for ADHD risk factors
                estimated_duration = task.get("estimated_minutes", 25)
                if estimated_duration > 60:  # Long tasks are ADHD risks
                    adhd_risk_tasks.append(task)

            # Generate sprint analysis
            sprint_analysis = {
                "sprint_id": sprint_id,
                "total_tasks": len(sprint_tasks),
                "average_complexity": total_complexity / max(len(sprint_tasks), 1),
                "high_complexity_count": len(high_complexity_tasks),
                "adhd_risk_count": len(adhd_risk_tasks),
                "recommended_decompositions": len(adhd_risk_tasks),
                "cognitive_load_assessment": self._assess_sprint_cognitive_load(total_complexity),
                "adhd_recommendations": self._generate_sprint_adhd_recommendations(
                    sprint_tasks, high_complexity_tasks, adhd_risk_tasks
                ),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat()
            }

            # Store analysis for other workflows
            await self._store_sprint_analysis(sprint_id, sprint_analysis)

            self.automation_stats["sprints_automated"] += 1
            logger.info(f"📊 Sprint analysis complete: {sprint_id} ({sprint_analysis['adhd_risk_count']} ADHD risks)")

            return True

        except Exception as e:
            logger.error(f"Sprint complexity analysis failed: {e}")
            return False

    async def _action_decompose_large_tasks(self, trigger_data: Dict[str, Any]) -> bool:
        """Automatically decompose large tasks for ADHD accommodation."""
        try:
            sprint_id = trigger_data.get("sprint_id")
            sprint_tasks = trigger_data.get("tasks", [])

            decomposed_count = 0

            for task in sprint_tasks:
                estimated_duration = task.get("estimated_minutes", 25)

                if estimated_duration > 25:  # Needs ADHD decomposition
                    # Calculate number of subtasks needed
                    num_subtasks = max(2, (estimated_duration + 24) // 25)  # 25-minute chunks

                    decomposition_plan = {
                        "original_task": task,
                        "num_subtasks": num_subtasks,
                        "subtask_duration": estimated_duration // num_subtasks,
                        "decomposition_strategy": "adhd_optimal_chunking",
                        "break_points": self._identify_task_break_points(task),
                        "energy_requirements": self._distribute_energy_requirements(
                            task, num_subtasks
                        )
                    }

                    # Store decomposition plan
                    await self._store_decomposition_plan(task.get("id"), decomposition_plan)

                    # Trigger actual decomposition in Leantime
                    await self._execute_leantime_decomposition(decomposition_plan)

                    decomposed_count += 1

            logger.info(f"🧩 Auto-decomposed {decomposed_count} large tasks for ADHD")
            return True

        except Exception as e:
            logger.error(f"Task decomposition failed: {e}")
            return False

    async def _action_setup_conport_context(self, trigger_data: Dict[str, Any]) -> bool:
        """Setup ConPort context for sprint automation."""
        try:
            sprint_id = trigger_data.get("sprint_id")
            sprint_data = trigger_data.get("sprint_data", {})

            # Create comprehensive sprint context
            sprint_context = {
                "sprint_id": sprint_id,
                "sprint_name": sprint_data.get("name", f"Sprint {sprint_id}"),
                "mode": "ACT",  # Sprint execution mode
                "focus": f"Sprint {sprint_id} execution with automated PM",
                "automation_enabled": True,
                "adhd_optimized": True,
                "task_count": len(sprint_data.get("tasks", [])),
                "auto_setup_timestamp": datetime.now(timezone.utc).isoformat(),
                "orchestration_active": True
            }

            # This would make ConPort MCP call
            await self.conport_client.update_active_context(patch_content=sprint_context)

            logger.info(f"🎯 ConPort context setup for sprint: {sprint_id}")
            return True

        except Exception as e:
            logger.error(f"ConPort context setup failed: {e}")
            return False

    # Progress Tracking Automation Actions

    async def _action_correlate_file_to_task(self, trigger_data: Dict[str, Any]) -> bool:
        """Correlate file changes to active tasks."""
        try:
            file_path = trigger_data.get("file_path", "")
            change_type = trigger_data.get("change_type", "modification")

            # Get currently active tasks from Leantime
            active_tasks = await self._get_active_tasks()

            # Intelligent correlation based on file path and task content
            correlated_tasks = []

            for task in active_tasks:
                correlation_score = await self._calculate_file_task_correlation(
                    file_path, task
                )

                if correlation_score > 0.6:  # Strong correlation
                    correlated_tasks.append({
                        "task": task,
                        "correlation_score": correlation_score,
                        "correlation_reasons": self._explain_correlation(file_path, task)
                    })

            if correlated_tasks:
                # Store correlations for progress estimation
                correlation_data = {
                    "file_path": file_path,
                    "change_type": change_type,
                    "correlated_tasks": correlated_tasks,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }

                await self._store_progress_correlation(correlation_data)

                logger.info(f"🔗 Correlated {file_path} to {len(correlated_tasks)} tasks")
                self.automation_stats["progress_correlations"] += 1

            return True

        except Exception as e:
            logger.error(f"File-task correlation failed: {e}")
            return False

    async def _action_estimate_completion_percentage(self, trigger_data: Dict[str, Any]) -> bool:
        """Estimate task completion percentage based on code changes."""
        try:
            correlation_data = trigger_data

            for correlation in correlation_data.get("correlated_tasks", []):
                task = correlation["task"]
                correlation_score = correlation["correlation_score"]

                # Analyze code changes to estimate completion
                file_path = correlation_data.get("file_path", "")
                completion_estimate = await self._analyze_code_completion(
                    file_path, task, correlation_score
                )

                if completion_estimate:
                    # Update task progress
                    progress_update = {
                        "task_id": task.get("id"),
                        "completion_percentage": completion_estimate["percentage"],
                        "estimation_confidence": completion_estimate["confidence"],
                        "estimation_method": "code_analysis",
                        "file_changes": completion_estimate["changes_analyzed"],
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }

                    await self._store_progress_estimate(progress_update)

                    logger.debug(f"📈 Estimated {completion_estimate['percentage']:.1f}% completion for task {task.get('id')}")

            return True

        except Exception as e:
            logger.error(f"Completion estimation failed: {e}")
            return False

    async def _action_update_all_systems(self, trigger_data: Dict[str, Any]) -> bool:
        """Update all PM systems with progress information."""
        try:
            progress_updates = trigger_data.get("progress_updates", [])

            # Prepare updates for each system
            leantime_updates = []
            conport_updates = []
            local_updates = []

            for update in progress_updates:
                task_id = update.get("task_id")
                completion_percentage = update.get("completion_percentage", 0)

                # Leantime update
                leantime_updates.append({
                    "task_id": task_id,
                    "progress_percent": completion_percentage,
                    "auto_updated": True,
                    "update_source": "task_orchestrator"
                })

                # ConPort update
                conport_status = "IN_PROGRESS" if completion_percentage < 100 else "DONE"
                conport_updates.append({
                    "status": conport_status,
                    "description": f"Task {task_id} progress: {completion_percentage:.1f}%",
                    "linked_item_type": "leantime_task",
                    "linked_item_id": task_id
                })

                # Local ADHD system update
                local_updates.append({
                    "task_id": task_id,
                    "progress": completion_percentage / 100.0,
                    "auto_updated": True
                })

            # Execute updates in parallel
            update_tasks = [
                self._batch_update_leantime(leantime_updates),
                self._batch_update_conport(conport_updates),
                self._batch_update_local(local_updates)
            ]

            results = await asyncio.gather(*update_tasks, return_exceptions=True)

            # Count successful updates
            successful_updates = sum(1 for r in results if r is True)

            logger.info(f"🔄 Updated {successful_updates}/3 systems with progress information")
            return successful_updates > 0

        except Exception as e:
            logger.error(f"System update failed: {e}")
            return False

    # Retrospective Automation Actions

    async def _action_analyze_completed_work(self, trigger_data: Dict[str, Any]) -> bool:
        """Analyze completed work for retrospective insights."""
        try:
            sprint_id = trigger_data.get("sprint_id")
            completed_tasks = trigger_data.get("completed_tasks", [])

            # Analyze work patterns
            work_analysis = {
                "sprint_id": sprint_id,
                "total_completed": len(completed_tasks),
                "complexity_distribution": self._analyze_complexity_distribution(completed_tasks),
                "duration_accuracy": self._analyze_duration_accuracy(completed_tasks),
                "adhd_patterns": await self._extract_adhd_patterns(completed_tasks),
                "workflow_effectiveness": await self._assess_workflow_effectiveness(sprint_id),
                "blockers_encountered": await self._identify_sprint_blockers(completed_tasks),
                "energy_utilization": await self._analyze_energy_utilization(sprint_id)
            }

            # Store analysis for retrospective generation
            await self._store_sprint_analysis(sprint_id, work_analysis)

            logger.info(f"📊 Analyzed completed work for sprint: {sprint_id}")
            return True

        except Exception as e:
            logger.error(f"Work analysis failed: {e}")
            return False

    async def _action_generate_retrospective_items(self, trigger_data: Dict[str, Any]) -> bool:
        """Generate retrospective items automatically."""
        try:
            sprint_id = trigger_data.get("sprint_id")
            work_analysis = await self._get_sprint_analysis(sprint_id)

            if not work_analysis:
                logger.warning(f"No work analysis available for retrospective: {sprint_id}")
                return False

            # Generate retrospective categories
            retrospective_items = {
                "what_went_well": self._generate_positive_insights(work_analysis),
                "what_could_improve": self._generate_improvement_insights(work_analysis),
                "adhd_accommodations": self._generate_adhd_insights(work_analysis),
                "workflow_optimizations": self._generate_workflow_insights(work_analysis),
                "action_items": self._generate_action_items(work_analysis)
            }

            # Create retrospective in Leantime
            await self._create_leantime_retrospective(sprint_id, retrospective_items)

            # Store in ConPort for future reference
            await self._store_retrospective_insights(sprint_id, retrospective_items)

            logger.info(f"📝 Generated retrospective for sprint: {sprint_id}")
            self.automation_stats["retrospectives_generated"] += 1

            return True

        except Exception as e:
            logger.error(f"Retrospective generation failed: {e}")
            return False

    # Utility Methods

    def _assess_sprint_cognitive_load(self, total_complexity: float) -> str:
        """Assess overall sprint cognitive load."""
        if total_complexity < 2.0:
            return "🟢 Light sprint - comfortable pace"
        elif total_complexity < 4.0:
            return "🟡 Moderate sprint - manageable with focus"
        elif total_complexity < 6.0:
            return "🟠 Heavy sprint - requires energy management"
        else:
            return "🔴 Intense sprint - needs careful pacing and breaks"

    def _generate_sprint_adhd_recommendations(
        self,
        all_tasks: List[Dict],
        high_complexity: List[Dict],
        adhd_risks: List[Dict]
    ) -> List[str]:
        """Generate ADHD-specific sprint recommendations."""
        recommendations = []

        if len(adhd_risks) > len(all_tasks) * 0.3:  # More than 30% risky tasks
            recommendations.append("🧩 Consider decomposing large tasks into 25-minute chunks")

        if len(high_complexity) > 3:
            recommendations.append("🎯 Schedule complex tasks during peak energy hours")
            recommendations.append("🔄 Alternate complex and simple tasks for cognitive balance")

        if len(all_tasks) > 15:
            recommendations.append("📦 Group related tasks to minimize context switching")

        recommendations.append("☕ Plan regular breaks every 25-30 minutes")
        recommendations.append("🎯 Use focus mode for complex implementation tasks")

        return recommendations

    def _identify_task_break_points(self, task: Dict[str, Any]) -> List[str]:
        """Identify natural break points within a task."""
        description = task.get("description", "").lower()

        # Common break points in development tasks
        break_points = []

        if "implement" in description:
            break_points.extend(["Design phase", "Implementation", "Testing", "Review"])
        elif "research" in description:
            break_points.extend(["Initial research", "Deep dive", "Documentation", "Summary"])
        elif "debug" in description:
            break_points.extend(["Problem reproduction", "Root cause analysis", "Fix implementation", "Verification"])
        else:
            # Generic break points
            break_points.extend(["Planning", "Execution", "Review"])

        return break_points

    def _distribute_energy_requirements(
        self,
        task: Dict[str, Any],
        num_subtasks: int
    ) -> List[str]:
        """Distribute energy requirements across subtasks."""
        complexity = task.get("complexity_score", 0.5)

        if complexity > 0.8:
            # High complexity: start high, then medium/low
            return (["high"] + ["medium"] * (num_subtasks - 2) + ["low"])[:num_subtasks]
        elif complexity > 0.5:
            # Medium complexity: mostly medium with some variation
            return (["medium"] * (num_subtasks - 1) + ["low"])[:num_subtasks]
        else:
            # Low complexity: mostly low energy
            return ["low"] * num_subtasks

    # Placeholder methods for integration points

    async def _check_workflow_conditions(self, workflow: AutomationWorkflow, data: Dict) -> bool:
        """Check if workflow conditions are met."""
        conditions = workflow.conditions or {}

        tasks = data.get("tasks", [])
        if conditions.get("min_tasks") and len(tasks) < int(conditions["min_tasks"]):
            return False
        if conditions.get("max_tasks") and len(tasks) > int(conditions["max_tasks"]):
            return False

        if conditions.get("has_description"):
            if tasks and any(not str(task.get("description", "")).strip() for task in tasks):
                return False

        if conditions.get("active_task_exists"):
            active_tasks = await self._get_active_tasks()
            if not active_tasks:
                return False

        if conditions.get("meaningful_change"):
            if data.get("change_type") in {"metadata", "noop"}:
                return False
            if int(data.get("lines_changed", 1)) <= 0:
                return False

        if conditions.get("sprint_has_completed_tasks"):
            if not data.get("completed_tasks"):
                return False

        if conditions.get("context_switch_detected") and not data.get("context_switch_detected", True):
            return False
        if conditions.get("preservation_needed") and not data.get("preservation_needed", True):
            return False

        return True

    async def _get_current_cognitive_load(self) -> float:
        """Get current system cognitive load."""
        if self.serena_client and hasattr(self.serena_client, "get_current_cognitive_load"):
            try:
                result = self.serena_client.get_current_cognitive_load(workspace_id=self.workspace_id)
                if asyncio.iscoroutine(result):
                    result = await result
                if isinstance(result, (int, float)):
                    return max(0.0, min(1.0, float(result)))
                if isinstance(result, dict):
                    raw = result.get("cognitive_load", result.get("load", 0.3))
                    return max(0.0, min(1.0, float(raw)))
            except Exception as exc:
                logger.debug("Failed to fetch cognitive load from Serena: %s", exc)

        queue_load = min(1.0, self.automation_queue.qsize() / 10.0)
        active_load = min(1.0, len(self.active_automations) / max(self.automation_batch_size, 1))
        return round(max(0.2, queue_load, active_load), 2)

    async def _defer_automation(self, trigger: AutomationTrigger, data: Dict, delay_minutes: int) -> None:
        """Defer automation execution."""
        run_at = datetime.now(timezone.utc) + timedelta(minutes=max(delay_minutes, 1))
        await self.automation_queue.put(
            {
                "run_at": run_at,
                "trigger": trigger.value if isinstance(trigger, AutomationTrigger) else str(trigger),
                "data": data,
            }
        )
        self.automation_stats["adhd_optimizations_applied"] += 1

    async def _store_sprint_analysis(self, sprint_id: str, analysis: Dict) -> None:
        """Store sprint analysis data."""
        if not sprint_id:
            return

        payload = dict(analysis)
        payload["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._sprint_analysis_store[sprint_id] = payload

    async def _get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get currently active tasks from Leantime."""
        if self.leantime_client:
            for method_name in ("get_active_tasks", "list_active_tasks", "get_tasks"):
                if not hasattr(self.leantime_client, method_name):
                    continue
                try:
                    method = getattr(self.leantime_client, method_name)
                    if method_name == "get_tasks":
                        result = method(status="IN_PROGRESS")
                    else:
                        result = method()
                    if asyncio.iscoroutine(result):
                        result = await result
                    if isinstance(result, list):
                        return result
                except Exception as exc:
                    logger.debug("Failed loading active tasks via %s: %s", method_name, exc)

        active = []
        for task in self._local_task_state.values():
            status = str(task.get("status", "IN_PROGRESS")).upper()
            if status in {"TODO", "IN_PROGRESS", "BLOCKED"}:
                active.append(task)
        return active

    async def _calculate_file_task_correlation(self, file_path: str, task: Dict) -> float:
        """Calculate correlation between file and task."""
        normalized_path = file_path.lower().strip()
        title = str(task.get("title", task.get("name", ""))).lower()
        description = str(task.get("description", "")).lower()
        task_text = f"{title} {description}"

        path_parts = [p for p in re.split(r"[\\/._\\-]+", normalized_path) if len(p) >= 3]
        overlap = sum(1 for token in set(path_parts) if token in task_text)

        score = 0.15 + min(0.6, overlap * 0.15)

        task_path = str(task.get("file_path", "")).lower()
        if task_path and task_path in normalized_path:
            score += 0.2

        task_id = str(task.get("id", "")).lower()
        if task_id and task_id in normalized_path:
            score += 0.1

        return max(0.0, min(1.0, score))

    async def _explain_correlation(self, file_path: str, task: Dict) -> List[str]:
        """Explain why file correlates to task."""
        reasons: List[str] = []
        normalized_path = file_path.lower()
        title = str(task.get("title", task.get("name", ""))).lower()
        description = str(task.get("description", "")).lower()

        if any(token in (title + " " + description) for token in re.split(r"[\\/._\\-]+", normalized_path) if token):
            reasons.append("Path tokens overlap with task title/description")
        if task.get("file_path") and str(task.get("file_path")).lower() in normalized_path:
            reasons.append("Task references this file directly")
        if not reasons:
            reasons.append("General repository-area match")

        return reasons

    async def _store_progress_correlation(self, data: Dict) -> None:
        """Store progress correlation data."""
        self._progress_correlation_store.append(dict(data))
        if len(self._progress_correlation_store) > 500:
            self._progress_correlation_store = self._progress_correlation_store[-500:]

    async def _analyze_code_completion(self, file_path: str, task: Dict, correlation: float) -> Dict:
        """Analyze code to estimate completion percentage."""
        raw_progress = task.get("progress_percent", task.get("completion_percentage", 0))
        try:
            current_percent = float(raw_progress)
            if current_percent <= 1.0:
                current_percent *= 100.0
        except (TypeError, ValueError):
            current_percent = 0.0

        increment = max(5.0, min(25.0, correlation * 20.0))
        percentage = min(100.0, max(current_percent, current_percent + increment))
        confidence = max(0.5, min(0.95, 0.55 + (correlation * 0.4)))
        changes_analyzed = max(1, int(round(correlation * 6)))

        return {
            "percentage": percentage,
            "confidence": confidence,
            "changes_analyzed": changes_analyzed,
        }

    async def _store_progress_estimate(self, update: Dict) -> None:
        """Store progress estimate."""
        self._progress_estimate_store.append(dict(update))
        if len(self._progress_estimate_store) > 1000:
            self._progress_estimate_store = self._progress_estimate_store[-1000:]

        task_id = str(update.get("task_id", "")).strip()
        if task_id:
            state = self._local_task_state.setdefault(task_id, {"id": task_id})
            state["progress_percent"] = update.get("completion_percentage", 0.0)
            state["status"] = "DONE" if float(update.get("completion_percentage", 0.0)) >= 100.0 else "IN_PROGRESS"
            state["updated_at"] = update.get("timestamp")

    async def _batch_update_leantime(self, updates: List[Dict]) -> bool:
        """Batch update Leantime tasks."""
        if not updates:
            return True
        if not self.leantime_client:
            return True

        success_count = 0
        if hasattr(self.leantime_client, "batch_update_tasks"):
            try:
                result = self.leantime_client.batch_update_tasks(updates)
                if asyncio.iscoroutine(result):
                    await result
                return True
            except Exception as exc:
                logger.debug("Leantime batch update failed, falling back to single updates: %s", exc)

        for update in updates:
            task_id = update.get("task_id")
            progress = update.get("progress_percent")
            try:
                if hasattr(self.leantime_client, "update_task_progress"):
                    result = self.leantime_client.update_task_progress(task_id, progress)
                elif hasattr(self.leantime_client, "update_task"):
                    result = self.leantime_client.update_task(task_id, update)
                else:
                    continue

                if asyncio.iscoroutine(result):
                    await result
                success_count += 1
            except Exception as exc:
                logger.debug("Failed updating Leantime task %s: %s", task_id, exc)

        return success_count > 0

    async def _batch_update_conport(self, updates: List[Dict]) -> bool:
        """Batch update ConPort progress."""
        if not updates:
            return True
        if not self.conport_client:
            return True

        if hasattr(self.conport_client, "batch_update_progress"):
            try:
                result = self.conport_client.batch_update_progress(updates)
                if asyncio.iscoroutine(result):
                    await result
                return True
            except Exception as exc:
                logger.debug("ConPort batch progress update failed: %s", exc)

        success_count = 0
        for update in updates:
            try:
                if hasattr(self.conport_client, "record_task_progress"):
                    result = self.conport_client.record_task_progress(update)
                elif hasattr(self.conport_client, "link_conport_items"):
                    result = self.conport_client.link_conport_items([update])
                else:
                    continue
                if asyncio.iscoroutine(result):
                    await result
                success_count += 1
            except Exception as exc:
                logger.debug("ConPort update failed for task %s: %s", update.get("linked_item_id"), exc)

        return success_count > 0

    async def _batch_update_local(self, updates: List[Dict]) -> bool:
        """Batch update local ADHD system."""
        for update in updates:
            task_id = str(update.get("task_id", "")).strip()
            if not task_id:
                continue
            task_state = self._local_task_state.setdefault(task_id, {"id": task_id})
            task_state.update(update)
            progress = float(update.get("progress", 0.0))
            task_state["status"] = "DONE" if progress >= 1.0 else "IN_PROGRESS"
        return True

    # Health and Monitoring

    async def get_automation_health(self) -> Dict[str, Any]:
        """Get automation engine health status."""
        try:
            # Worker health
            active_workers = len([w for w in self.workers if not w.done()])

            # Queue health
            queue_size = self.automation_queue.qsize()
            active_automations = len(self.active_automations)

            # Workflow health
            enabled_workflows = len([w for w in self.workflows.values() if w.enabled])

            # Overall status
            if active_workers == len(self.workers) and queue_size < 10:
                status = "🤖 Fully Automated"
            elif active_workers >= len(self.workers) - 1:
                status = "✅ Operating"
            else:
                status = "⚠️ Degraded"

            return {
                "overall_status": status,
                "processing": {
                    "workers_active": f"{active_workers}/{len(self.workers)}",
                    "queue_size": queue_size,
                    "active_automations": active_automations
                },
                "workflows": {
                    "registered": len(self.workflows),
                    "enabled": enabled_workflows,
                    "trigger_types": len(self.trigger_handlers)
                },
                "performance": self.automation_stats,
                "adhd_optimizations": {
                    "cognitive_load_threshold": self.cognitive_load_threshold,
                    "batch_size": self.automation_batch_size,
                    "accommodations_applied": self.automation_stats["adhd_optimizations_applied"]
                }
            }

        except Exception as e:
            logger.error(f"Automation health check failed: {e}")
            return {"overall_status": "🔴 Error", "error": str(e)}

    async def close(self) -> None:
        """Shutdown automation engine gracefully."""
        logger.info("🛑 Shutting down Implicit Automation Engine...")

        self.running = False

        # Cancel workers
        if self.workers:
            for worker in self.workers:
                worker.cancel()
            await asyncio.gather(*self.workers, return_exceptions=True)

        logger.info("✅ Implicit Automation Engine shutdown complete")

    # Background Workers (placeholders for remaining methods)

    async def _automation_processor(self) -> None:
        """Background automation processor."""
        while self.running:
            try:
                item = await asyncio.wait_for(self.automation_queue.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue

            try:
                run_at = item.get("run_at")
                if isinstance(run_at, datetime):
                    now = datetime.now(timezone.utc)
                    if run_at > now:
                        await self.automation_queue.put(item)
                        await asyncio.sleep(min(1.0, (run_at - now).total_seconds()))
                        continue

                trigger_raw = item.get("trigger")
                trigger = (
                    trigger_raw
                    if isinstance(trigger_raw, AutomationTrigger)
                    else AutomationTrigger(str(trigger_raw))
                )
                await self.trigger_automation(trigger, item.get("data", {}))
            except Exception as exc:
                logger.error("Deferred automation processing failed: %s", exc)
            finally:
                self.automation_queue.task_done()

    async def _workflow_monitor(self) -> None:
        """Monitor workflow health."""
        while self.running:
            await asyncio.sleep(60)
            for workflow in self.workflows.values():
                if workflow.execution_count < 5:
                    continue
                if workflow.success_rate < 0.7:
                    logger.warning(
                        "Workflow %s success rate degraded: %.2f",
                        workflow.id,
                        workflow.success_rate,
                    )

    async def _adhd_optimization_monitor(self) -> None:
        """Monitor ADHD optimization effectiveness."""
        while self.running:
            await asyncio.sleep(120)
            load = await self._get_current_cognitive_load()
            if load > self.cognitive_load_threshold:
                self.automation_stats["adhd_optimizations_applied"] += 1

    # Additional placeholder methods
    def _analyze_complexity_distribution(self, tasks: List[Dict]) -> Dict:
        return {}

    def _analyze_duration_accuracy(self, tasks: List[Dict]) -> Dict:
        return {}

    async def _extract_adhd_patterns(self, tasks: List[Dict]) -> Dict:
        return {}

    async def _assess_workflow_effectiveness(self, sprint_id: str) -> Dict:
        return {}

    async def _identify_sprint_blockers(self, tasks: List[Dict]) -> List[Dict]:
        return []

    async def _analyze_energy_utilization(self, sprint_id: str) -> Dict:
        return {}

    async def _get_sprint_analysis(self, sprint_id: str) -> Optional[Dict]:
        return self._sprint_analysis_store.get(sprint_id)

    def _generate_positive_insights(self, analysis: Dict) -> List[str]:
        return ["Good sprint velocity maintained"]

    def _generate_improvement_insights(self, analysis: Dict) -> List[str]:
        return ["Consider more break time for complex tasks"]

    def _generate_adhd_insights(self, analysis: Dict) -> List[str]:
        return ["25-minute chunks worked well for focus"]

    def _generate_workflow_insights(self, analysis: Dict) -> List[str]:
        return ["Automation reduced PM overhead effectively"]

    def _generate_action_items(self, analysis: Dict) -> List[str]:
        return ["Continue using automated decomposition"]

    async def _create_leantime_retrospective(self, sprint_id: str, items: Dict) -> None:
        self._retrospective_store[sprint_id] = {
            "items": items,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if not self.leantime_client:
            return

        for method_name in ("create_retrospective", "create_sprint_retrospective", "create_note"):
            if not hasattr(self.leantime_client, method_name):
                continue
            try:
                method = getattr(self.leantime_client, method_name)
                if method_name == "create_note":
                    payload = {"title": f"Sprint {sprint_id} Retrospective", "content": json.dumps(items)}
                    result = method(payload)
                else:
                    result = method(sprint_id=sprint_id, items=items)
                if asyncio.iscoroutine(result):
                    await result
                return
            except Exception as exc:
                logger.debug("Leantime retrospective write via %s failed: %s", method_name, exc)

    async def _store_retrospective_insights(self, sprint_id: str, items: Dict) -> None:
        self._retrospective_store[sprint_id] = {
            "items": items,
            "stored_at": datetime.now(timezone.utc).isoformat(),
        }
        if not self.conport_client:
            return

        payload = {
            "sprint_id": sprint_id,
            "type": "retrospective",
            "insights": items,
            "source": "implicit_automation_engine",
        }
        for method_name in ("store_retrospective", "add_retrospective_insights", "add_observation"):
            if not hasattr(self.conport_client, method_name):
                continue
            try:
                result = getattr(self.conport_client, method_name)(payload)
                if asyncio.iscoroutine(result):
                    await result
                return
            except Exception as exc:
                logger.debug("ConPort retrospective store via %s failed: %s", method_name, exc)
