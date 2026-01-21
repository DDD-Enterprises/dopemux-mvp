"""
WorkflowCoordinator - Multi-Step Workflow Orchestration Agent

Coordinates complex multi-step workflows with automatic checkpointing.
Manages persona activation, agent coordination, and workflow progress.

Authority: Multi-step workflow orchestration

Week: 10
Complexity: 0.6 (Medium-High)
Effort: 5 days (10 focus blocks)
Code Reuse: 60% from Zen continuation + agent coordination
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class WorkflowType(str, Enum):
    """Predefined workflow types"""
    FEATURE_IMPLEMENTATION = "feature_implementation"
    BUG_INVESTIGATION = "bug_investigation"
    ARCHITECTURE_DECISION = "architecture_decision"
    REFACTORING = "refactoring"
    CODE_REVIEW = "code_review"
    CUSTOM = "custom"


class StepType(str, Enum):
    """Types of workflow steps"""
    DESIGN = "design"
    IMPLEMENT = "implement"
    TEST = "test"
    VALIDATE = "validate"
    DOCUMENT = "document"
    REVIEW = "review"
    RESEARCH = "research"


@dataclass
class WorkflowStep:
    """A single step in a workflow"""
    id: str
    name: str
    step_type: StepType
    description: str
    persona: Optional[str] = None  # SuperClaude persona to apply
    agent: Optional[str] = None  # Infrastructure agent to use
    estimated_minutes: int = 45
    requires_checkpoint: bool = True
    dependencies: List[str] = field(default_factory=list)
    workspace_path: Optional[str] = None  # Multi-workspace tracking


@dataclass
class WorkflowTemplate:
    """Template for a workflow type"""
    workflow_type: WorkflowType
    name: str
    description: str
    steps: List[WorkflowStep]
    total_estimated_minutes: int
    recommended_breaks: int
    workspace_path: Optional[str] = None  # Multi-workspace tracking


@dataclass
class WorkflowExecution:
    """Execution state of a workflow"""
    workflow_id: str
    workflow_type: WorkflowType
    started_at: datetime
    current_step: int
    completed_steps: List[str]
    checkpoints: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    workspace_path: Optional[str] = None  # Multi-workspace tracking


class WorkflowCoordinator:
    """
    Multi-Step Workflow Orchestration Agent.

    Responsibilities:
    1. Manage predefined workflow templates
    2. Coordinate agent and persona activation
    3. Auto-checkpoint after each step
    4. Track workflow progress
    5. Enable workflow resume after interruptions

    Example:
        coordinator = WorkflowCoordinator(workspace_id="/path/to/project")
        await coordinator.initialize()

        # Start feature implementation workflow
        workflow = await coordinator.start_workflow(
            workflow_type=WorkflowType.FEATURE_IMPLEMENTATION,
            description="Add user authentication"
        )

        # Execute workflow steps
        for step in workflow.steps:
            result = await coordinator.execute_step(
                workflow_id=workflow.workflow_id,
                step=step
            )
            # Auto-checkpoint after each step
    """

    def __init__(
        self,
        workspace_id: str,
        memory_agent: Optional[Any] = None,
        conport_client: Optional[Any] = None
    ):
        """
        Initialize WorkflowCoordinator.

        Args:
            workspace_id: Absolute path to workspace
            memory_agent: MemoryAgent for auto-checkpointing
            conport_client: ConPort MCP client for logging
        """
        self.workspace_id = workspace_id
        self.memory_agent = memory_agent
        self.conport_client = conport_client

        # Workflow templates
        self.templates: Dict[WorkflowType, WorkflowTemplate] = {}

        # Active workflows
        self.active_workflows: Dict[str, WorkflowExecution] = {}

        # Metrics
        self.metrics = {
            "workflows_started": 0,
            "workflows_completed": 0,
            "steps_executed": 0,
            "checkpoints_created": 0
        }

        logger.info(f"WorkflowCoordinator initialized (workspace: {workspace_id})")

    async def initialize(self):
        """Initialize WorkflowCoordinator and load templates"""
        logger.info("🚀 Initializing WorkflowCoordinator...")

        # Load workflow templates
        self._load_workflow_templates()

        logger.info(f"✅ WorkflowCoordinator ready ({len(self.templates)} templates loaded)")

    def _load_workflow_templates(self):
        """Load predefined workflow templates"""

        # Feature Implementation Workflow
        self.templates[WorkflowType.FEATURE_IMPLEMENTATION] = WorkflowTemplate(
            workflow_type=WorkflowType.FEATURE_IMPLEMENTATION,
            name="Feature Implementation",
            description="Complete workflow for implementing new features",
            steps=[
                WorkflowStep(
                    id="step_1",
                    name="Design and Plan",
                    step_type=StepType.DESIGN,
                    description="Design architecture and plan implementation",
                    persona="system-architect",
                    agent="TaskDecomposer",
                    estimated_minutes=45
                ),
                WorkflowStep(
                    id="step_2",
                    name="Implement Core",
                    step_type=StepType.IMPLEMENT,
                    description="Implement core functionality",
                    persona="python-expert",
                    estimated_minutes=90,
                    dependencies=["step_1"]
                ),
                WorkflowStep(
                    id="step_3",
                    name="Write Tests",
                    step_type=StepType.TEST,
                    description="Create comprehensive test suite",
                    persona="quality-engineer",
                    estimated_minutes=60,
                    dependencies=["step_2"]
                ),
                WorkflowStep(
                    id="step_4",
                    name="Validate Compliance",
                    step_type=StepType.VALIDATE,
                    description="Validate architectural compliance",
                    agent="DopemuxEnforcer",
                    estimated_minutes=15,
                    dependencies=["step_2"]
                ),
                WorkflowStep(
                    id="step_5",
                    name="Documentation",
                    step_type=StepType.DOCUMENT,
                    description="Write feature documentation",
                    persona="technical-writer",
                    estimated_minutes=30,
                    dependencies=["step_2", "step_3"]
                ),
            ],
            total_estimated_minutes=240,
            recommended_breaks=3
        )

        # Bug Investigation Workflow
        self.templates[WorkflowType.BUG_INVESTIGATION] = WorkflowTemplate(
            workflow_type=WorkflowType.BUG_INVESTIGATION,
            name="Bug Investigation and Fix",
            description="Systematic bug investigation workflow",
            steps=[
                WorkflowStep(
                    id="step_1",
                    name="Reproduce Issue",
                    step_type=StepType.TEST,
                    description="Reproduce and document the issue",
                    estimated_minutes=30
                ),
                WorkflowStep(
                    id="step_2",
                    name="Investigate Root Cause",
                    step_type=StepType.RESEARCH,
                    description="Debug and find root cause",
                    agent="zen/debug",
                    persona="root-cause-analyst",
                    estimated_minutes=60,
                    dependencies=["step_1"]
                ),
                WorkflowStep(
                    id="step_3",
                    name="Implement Fix",
                    step_type=StepType.IMPLEMENT,
                    description="Implement the fix",
                    persona="python-expert",
                    estimated_minutes=45,
                    dependencies=["step_2"]
                ),
                WorkflowStep(
                    id="step_4",
                    name="Validate Fix",
                    step_type=StepType.TEST,
                    description="Validate fix resolves issue",
                    persona="quality-engineer",
                    estimated_minutes=30,
                    dependencies=["step_3"]
                ),
            ],
            total_estimated_minutes=165,
            recommended_breaks=2
        )

        # Architecture Decision Workflow
        self.templates[WorkflowType.ARCHITECTURE_DECISION] = WorkflowTemplate(
            workflow_type=WorkflowType.ARCHITECTURE_DECISION,
            name="Architecture Decision",
            description="Systematic architecture decision-making",
            steps=[
                WorkflowStep(
                    id="step_1",
                    name="Research Options",
                    step_type=StepType.RESEARCH,
                    description="Research available options and patterns",
                    agent="exa",
                    estimated_minutes=45
                ),
                WorkflowStep(
                    id="step_2",
                    name="Design Evaluation",
                    step_type=StepType.DESIGN,
                    description="Evaluate options with Zen consensus",
                    agent="zen/consensus",
                    persona="system-architect",
                    estimated_minutes=60,
                    dependencies=["step_1"]
                ),
                WorkflowStep(
                    id="step_3",
                    name="Document Decision",
                    step_type=StepType.DOCUMENT,
                    description="Document decision in ConPort",
                    agent="ConPort",
                    estimated_minutes=30,
                    dependencies=["step_2"]
                ),
            ],
            total_estimated_minutes=135,
            recommended_breaks=1
        )

        logger.info(f"📋 Loaded {len(self.templates)} workflow templates")

    async def start_workflow(
        self,
        workflow_type: WorkflowType,
        description: str,
        custom_steps: Optional[List[WorkflowStep]] = None
    ) -> WorkflowExecution:
        """
        Start a new workflow execution.

        Args:
            workflow_type: Type of workflow to execute
            description: Description of the work
            custom_steps: Optional custom steps (overrides template)

        Returns:
            WorkflowExecution instance
        """
        self.metrics["workflows_started"] += 1

        # Use timestamp + counter to ensure uniqueness
        workflow_id = f"workflow_{int(datetime.now().timestamp())}_{self.metrics['workflows_started']}"

        # Get template
        if workflow_type in self.templates:
            template = self.templates[workflow_type]
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

        # Create execution
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            started_at=datetime.now(timezone.utc),
            current_step=0,
            completed_steps=[],
            checkpoints=[],
            metadata={
                "description": description,
                "template_name": template.name,
                "total_steps": len(template.steps)
            }
        )

        self.active_workflows[workflow_id] = execution

        logger.info(
            f"🚀 Started workflow: {template.name} "
            f"({len(template.steps)} steps, ~{template.total_estimated_minutes} min)"
        )

        return execution

    async def execute_step(
        self,
        workflow_id: str,
        step: WorkflowStep,
        result_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow step and checkpoint.

        Args:
            workflow_id: Workflow execution ID
            step: Step to execute
            result_data: Optional result data from step execution

        Returns:
            Step execution result
        """
        self.metrics["steps_executed"] += 1

        execution = self.active_workflows.get(workflow_id)
        if not execution:
            raise ValueError(f"Workflow not found: {workflow_id}")

        logger.info(f"▶️  Executing step: {step.name} (type: {step.step_type.value})")

        # Mark step as current
        execution.current_step += 1

        # Create checkpoint if required
        if step.requires_checkpoint and self.memory_agent:
            checkpoint = await self._create_checkpoint(workflow_id, step, result_data)
            execution.checkpoints.append(checkpoint)
            self.metrics["checkpoints_created"] += 1

        # Mark step complete
        execution.completed_steps.append(step.id)

        logger.info(f"✅ Step complete: {step.name}")

        return {
            "workflow_id": workflow_id,
            "step_id": step.id,
            "step_name": step.name,
            "completed": True,
            "checkpoint_created": step.requires_checkpoint
        }

    async def _create_checkpoint(
        self,
        workflow_id: str,
        step: WorkflowStep,
        result_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create checkpoint for workflow step"""

        checkpoint = {
            "workflow_id": workflow_id,
            "step_id": step.id,
            "step_name": step.name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "result_data": result_data or {}
        }

        # Save via MemoryAgent if available
        if self.memory_agent:
            await self.memory_agent.save_checkpoint(
                checkpoint_name=f"workflow_{workflow_id}_step_{step.id}",
                checkpoint_data=checkpoint
            )

        logger.debug(f"💾 Checkpoint created: {step.name}")

        return checkpoint

    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current status of workflow execution"""

        execution = self.active_workflows.get(workflow_id)
        if not execution:
            raise ValueError(f"Workflow not found: {workflow_id}")

        template = self.templates[execution.workflow_type]

        total_steps = len(template.steps)
        completed = len(execution.completed_steps)
        progress_pct = (completed / total_steps) * 100 if total_steps > 0 else 0

        return {
            "workflow_id": workflow_id,
            "workflow_type": execution.workflow_type.value,
            "started_at": execution.started_at.isoformat(),
            "current_step": execution.current_step,
            "total_steps": total_steps,
            "completed_steps": completed,
            "progress_pct": round(progress_pct, 1),
            "checkpoints_created": len(execution.checkpoints),
            "metadata": execution.metadata
        }

    async def complete_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Mark workflow as complete and cleanup"""

        execution = self.active_workflows.get(workflow_id)
        if not execution:
            raise ValueError(f"Workflow not found: {workflow_id}")

        self.metrics["workflows_completed"] += 1

        # Create final summary
        summary = await self.get_workflow_status(workflow_id)
        summary["completed_at"] = datetime.now(timezone.utc).isoformat()
        summary["duration_minutes"] = (
            datetime.now(timezone.utc) - execution.started_at
        ).total_seconds() / 60

        # Remove from active
        del self.active_workflows[workflow_id]

        logger.info(f"🏁 Workflow complete: {workflow_id}")

        return summary

    def get_workflow_template(
        self,
        workflow_type: WorkflowType
    ) -> WorkflowTemplate:
        """Get workflow template by type"""
        return self.templates.get(workflow_type)

    async def get_metrics_summary(self) -> Dict[str, Any]:
        """Get workflow coordination metrics"""
        return {
            "workflows_started": self.metrics["workflows_started"],
            "workflows_completed": self.metrics["workflows_completed"],
            "active_workflows": len(self.active_workflows),
            "steps_executed": self.metrics["steps_executed"],
            "checkpoints_created": self.metrics["checkpoints_created"],
            "completion_rate": round(
                (self.metrics["workflows_completed"] / self.metrics["workflows_started"] * 100)
                if self.metrics["workflows_started"] > 0 else 0, 1
            )
        }

    async def close(self):
        """Shutdown WorkflowCoordinator"""
        logger.info("🛑 WorkflowCoordinator shutdown complete")


# ============================================================================
# Demo / Test
# ============================================================================

async def demo():
    """Demonstrate WorkflowCoordinator"""

    logger.info("\n" + "="*70)
    logger.info("WORKFLOW COORDINATOR DEMO")
    logger.info("="*70)

    coordinator = WorkflowCoordinator(
        workspace_id="/Users/hue/code/dopemux-mvp"
    )

    await coordinator.initialize()

    # Example 1: Feature Implementation Workflow
    logger.info("\n" + "="*70)
    logger.info("Example 1: Feature Implementation Workflow")
    logger.info("="*70)

    template = coordinator.get_workflow_template(WorkflowType.FEATURE_IMPLEMENTATION)

    logger.info(f"\nWorkflow: {template.name}")
    logger.info(f"Description: {template.description}")
    logger.info(f"Total Steps: {len(template.steps)}")
    logger.info(f"Estimated Time: {template.total_estimated_minutes} min")
    logger.info(f"Recommended Breaks: {template.recommended_breaks}")

    logger.info(f"\nSteps:")
    for idx, step in enumerate(template.steps, 1):
        logger.info(f"\n{idx}. {step.name} ({step.step_type.value})")
        logger.info(f"   Description: {step.description}")
        logger.info(f"   Persona: {step.persona or 'N/A'}")
        logger.info(f"   Agent: {step.agent or 'N/A'}")
        logger.info(f"   Estimated: {step.estimated_minutes} min")
        if step.dependencies:
            logger.info(f"   Dependencies: {', '.join(step.dependencies)}")

    # Start workflow
    logger.info(f"\n{'='*70}")
    logger.info("Starting Workflow Execution")
    logger.info(f"{'='*70}")

    execution = await coordinator.start_workflow(
        workflow_type=WorkflowType.FEATURE_IMPLEMENTATION,
        description="Add JWT authentication"
    )

    logger.info(f"\nWorkflow ID: {execution.workflow_id}")
    logger.info(f"Started At: {execution.started_at.isoformat()}")

    # Simulate executing steps
    for step in template.steps[:2]:  # Execute first 2 steps for demo
        result = await coordinator.execute_step(
            workflow_id=execution.workflow_id,
            step=step,
            result_data={"step": step.name, "status": "completed"}
        )
        logger.info(f"\n✅ Completed: {result['step_name']}")

    # Check status
    status = await coordinator.get_workflow_status(execution.workflow_id)

    logger.info(f"\n{'='*70}")
    logger.info("Workflow Status")
    logger.info(f"{'='*70}")

    logger.info(f"\nProgress: {status['completed_steps']}/{status['total_steps']} steps")
    logger.info(f"Progress: {status['progress_pct']}%")
    logger.info(f"Checkpoints: {status['checkpoints_created']}")

    # Metrics
    logger.info(f"\n{'='*70}")
    logger.info("Coordination Metrics")
    logger.info(f"{'='*70}")

    metrics = await coordinator.get_metrics_summary()
    logger.info(f"\nWorkflows Started: {metrics['workflows_started']}")
    logger.info(f"Active Workflows: {metrics['active_workflows']}")
    logger.info(f"Steps Executed: {metrics['steps_executed']}")
    logger.info(f"Checkpoints Created: {metrics['checkpoints_created']}")

    await coordinator.close()

    logger.info("\n" + "="*70)
    logger.info("✅ Demo complete!")
    logger.info("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(demo())
