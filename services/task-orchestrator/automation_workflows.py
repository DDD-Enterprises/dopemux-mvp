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

        # Background workers
        self.workers: List[asyncio.Task] = []
        self.running = False

    async def initialize(self) -> None:
        """Initialize automation engine and register workflows."""
        logger.info("🤖 Initializing Implicit Automation Engine...")

        # Register default workflows
        await self._register_default_workflows()

        # Start background processing
        await self._start_automation_workers()

        self.running = True
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

            # Remove from active automations
            self.active_automations.discard(workflow.id)

            self.automation_stats["workflows_executed"] += 1
            logger.info(f"✅ Automation completed: {workflow.automation_type.value}")

            return True

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
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
            # await self.conport_client.update_active_context(patch_content=sprint_context)

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
        return True  # Placeholder

    async def _get_current_cognitive_load(self) -> float:
        """Get current system cognitive load."""
        return 0.3  # Placeholder

    async def _defer_automation(self, trigger: AutomationTrigger, data: Dict, delay_minutes: int) -> None:
        """Defer automation execution."""
        pass  # Placeholder

    async def _store_sprint_analysis(self, sprint_id: str, analysis: Dict) -> None:
        """Store sprint analysis data."""
        pass  # Placeholder

    async def _get_active_tasks(self) -> List[Dict[str, Any]]:
        """Get currently active tasks from Leantime."""
        return []  # Placeholder

    async def _calculate_file_task_correlation(self, file_path: str, task: Dict) -> float:
        """Calculate correlation between file and task."""
        return 0.7  # Placeholder

    async def _explain_correlation(self, file_path: str, task: Dict) -> List[str]:
        """Explain why file correlates to task."""
        return ["File path matches task description"]  # Placeholder

    async def _store_progress_correlation(self, data: Dict) -> None:
        """Store progress correlation data."""
        pass  # Placeholder

    async def _analyze_code_completion(self, file_path: str, task: Dict, correlation: float) -> Dict:
        """Analyze code to estimate completion percentage."""
        return {"percentage": 50.0, "confidence": 0.8, "changes_analyzed": 5}  # Placeholder

    async def _store_progress_estimate(self, update: Dict) -> None:
        """Store progress estimate."""
        pass  # Placeholder

    async def _batch_update_leantime(self, updates: List[Dict]) -> bool:
        """Batch update Leantime tasks."""
        return True  # Placeholder

    async def _batch_update_conport(self, updates: List[Dict]) -> bool:
        """Batch update ConPort progress."""
        return True  # Placeholder

    async def _batch_update_local(self, updates: List[Dict]) -> bool:
        """Batch update local ADHD system."""
        return True  # Placeholder

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
            await asyncio.sleep(1)

    async def _workflow_monitor(self) -> None:
        """Monitor workflow health."""
        while self.running:
            await asyncio.sleep(60)

    async def _adhd_optimization_monitor(self) -> None:
        """Monitor ADHD optimization effectiveness."""
        while self.running:
            await asyncio.sleep(120)

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

    async def _store_sprint_analysis(self, sprint_id: str, analysis: Dict) -> None:
        pass

    async def _get_sprint_analysis(self, sprint_id: str) -> Optional[Dict]:
        return {}

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
        pass

    async def _store_retrospective_insights(self, sprint_id: str, items: Dict) -> None:
        pass