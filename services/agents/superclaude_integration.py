"""
SuperClaude Integration Layer - Weeks 15-16

Connects all 7 Dopemux agents with SuperClaude /sc: and /dx: commands.
Provides unified API for command framework to use agent ecosystem.

Version: 1.0.0
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# Import all 7 agents
from memory_agent import MemoryAgent
from cognitive_guardian import CognitiveGuardian
from two_plane_orchestrator import TwoPlaneOrchestrator
from dopemux_enforcer import DopemuxEnforcer
from tool_orchestrator import ToolOrchestrator
from task_decomposer import TaskDecomposer, TaskInput
from workflow_coordinator import WorkflowCoordinator, WorkflowType

logger = logging.getLogger(__name__)


@dataclass
class AgentEcosystem:
    """Complete agent ecosystem for commands"""
    memory: Optional[MemoryAgent] = None
    guardian: Optional[CognitiveGuardian] = None
    two_plane: Optional[TwoPlaneOrchestrator] = None
    enforcer: Optional[DopemuxEnforcer] = None
    tool_selector: Optional[ToolOrchestrator] = None
    task_decomp: Optional[TaskDecomposer] = None
    workflow_coord: Optional[WorkflowCoordinator] = None


class SuperClaudeIntegration:
    """
    Integration layer for SuperClaude commands.

    Provides unified access to all 7 Dopemux agents for /sc: and /dx: commands.

    Example:
        integration = SuperClaudeIntegration(workspace_id="/path/to/project")
        await integration.initialize()

        # Use in /dx:implement command
        session = await integration.start_implementation_session(
            task_description="Add user authentication",
            estimated_complexity=0.6
        )

        # Use in /sc:brainstorm command
        tasks = await integration.decompose_requirements(prd_text)

        # Use in /sc:troubleshoot command
        workflow = await integration.start_bug_workflow(bug_description)
    """

    def __init__(
        self,
        workspace_id: str,
        bridge_url: str = "http://localhost:3016",
        conport_client: Optional[Any] = None
    ):
        """
        Initialize SuperClaude integration.

        Args:
            workspace_id: Absolute path to workspace
            bridge_url: DopeconBridge URL
            conport_client: ConPort MCP client
        """
        self.workspace_id = workspace_id
        self.bridge_url = bridge_url
        self.conport_client = conport_client

        # Agent ecosystem
        self.agents = AgentEcosystem()

        # Active session tracking
        self.active_session = None

        logger.info("SuperClaudeIntegration initialized")

    async def initialize(self, agents_to_load: Optional[List[str]] = None):
        """
        Initialize agent ecosystem.

        Args:
            agents_to_load: Specific agents to load, or None for all
        """
        logger.info("🚀 Initializing Dopemux agent ecosystem...")

        agents_to_load = agents_to_load or [
            "memory", "guardian", "two_plane", "enforcer",
            "tool_selector", "task_decomp", "workflow_coord"
        ]

        # Initialize agents
        if "memory" in agents_to_load:
            self.agents.memory = MemoryAgent(workspace_id=self.workspace_id)
            logger.info("  ✅ MemoryAgent loaded")

        if "guardian" in agents_to_load:
            self.agents.guardian = CognitiveGuardian(
                workspace_id=self.workspace_id,
                memory_agent=self.agents.memory
            )
            logger.info("  ✅ CognitiveGuardian loaded")

        if "two_plane" in agents_to_load:
            self.agents.two_plane = TwoPlaneOrchestrator(
                workspace_id=self.workspace_id,
                bridge_url=self.bridge_url,
                conport_client=self.conport_client
            )
            await self.agents.two_plane.initialize()
            logger.info("  ✅ TwoPlaneOrchestrator loaded")

        if "enforcer" in agents_to_load:
            self.agents.enforcer = DopemuxEnforcer(
                workspace_id=self.workspace_id,
                conport_client=self.conport_client
            )
            await self.agents.enforcer.initialize()
            logger.info("  ✅ DopemuxEnforcer loaded")

        if "tool_selector" in agents_to_load:
            self.agents.tool_selector = ToolOrchestrator(
                workspace_id=self.workspace_id,
                conport_client=self.conport_client
            )
            await self.agents.tool_selector.initialize()
            logger.info("  ✅ ToolOrchestrator loaded")

        if "task_decomp" in agents_to_load:
            self.agents.task_decomp = TaskDecomposer(
                workspace_id=self.workspace_id,
                cognitive_guardian=self.agents.guardian,
                tool_orchestrator=self.agents.tool_selector,
                two_plane_orchestrator=self.agents.two_plane,
                conport_client=self.conport_client,
                memory_agent=self.agents.memory
            )
            logger.info("  ✅ TaskDecomposer loaded")

        if "workflow_coord" in agents_to_load:
            self.agents.workflow_coord = WorkflowCoordinator(
                workspace_id=self.workspace_id,
                memory_agent=self.agents.memory,
                conport_client=self.conport_client
            )
            await self.agents.workflow_coord.initialize()
            logger.info("  ✅ WorkflowCoordinator loaded")

        logger.info("✅ Dopemux agent ecosystem ready!")

    # ========================================================================
    # /dx:implement Command Integration
    # ========================================================================

    async def start_implementation_session(
        self,
        task_description: str,
        estimated_complexity: float = 0.5,
        duration_minutes: int = 25
    ) -> Dict[str, Any]:
        """
        Start ADHD-optimized implementation session.

        Integrates: MemoryAgent, CognitiveGuardian, ToolOrchestrator

        Args:
            task_description: What to implement
            estimated_complexity: 0.0-1.0
            duration_minutes: Target duration

        Returns:
            Session info with readiness check and tool selection
        """
        # 1. Start session (MemoryAgent)
        if self.agents.memory:
            await self.agents.memory.start_session(
                task_description,
                complexity=estimated_complexity
            )

        # 2. Check readiness (CognitiveGuardian)
        readiness = {"ready": True}
        if self.agents.guardian:
            await self.agents.guardian.start_monitoring()
            readiness = await self.agents.guardian.check_task_readiness(
                task_complexity=estimated_complexity,
                task_energy_required=self._map_energy(estimated_complexity)
            )

        # 3. Select tools (ToolOrchestrator)
        tools = None
        if self.agents.tool_selector:
            try:
                tools = await self.agents.tool_selector.select_tools_for_task(
                    task_type="implementation",
                    complexity=estimated_complexity
                )
            except Exception as e:
                logger.warning(f"Tool selection failed: {e}")
                tools = None

        self.active_session = {
            "task": task_description,
            "complexity": estimated_complexity,
            "started_at": asyncio.get_event_loop().time(),
            "target_duration": duration_minutes
        }

        return {
            "session_started": True,
            "readiness": readiness,
            "tools_selected": tools,
            "break_reminder_at": duration_minutes
        }

    # ========================================================================
    # /dx:prd-parse Command Integration
    # ========================================================================

    async def decompose_prd(
        self,
        prd_text: str,
        max_tasks: int = 20
    ) -> Dict[str, Any]:
        """
        Decompose PRD into ADHD-optimized tasks.

        Integrates: TaskDecomposer (which uses all 7 agents internally)

        Args:
            prd_text: PRD content
            max_tasks: Max tasks to prevent overwhelm

        Returns:
            Decomposed tasks with ADHD metadata
        """
        if not self.agents.task_decomp:
            raise RuntimeError("TaskDecomposer not initialized")

        # TaskDecomposer handles decomposition with full agent integration
        tasks = await self.agents.task_decomp.decompose_prd(prd_text)

        return {
            "tasks": tasks[:max_tasks],
            "total_tasks": len(tasks),
            "adhd_optimized": True,
            "ready_for_review": True
        }

    # ========================================================================
    # /sc:implement Command Integration
    # ========================================================================

    async def start_feature_workflow(
        self,
        feature_description: str,
        complexity: float = 0.6
    ) -> Dict[str, Any]:
        """
        Start feature implementation workflow.

        Integrates: WorkflowCoordinator + all agents

        Args:
            feature_description: Feature to implement
            complexity: Estimated complexity

        Returns:
            Workflow execution info
        """
        if not self.agents.workflow_coord:
            raise RuntimeError("WorkflowCoordinator not initialized")

        # Start Feature Implementation workflow
        execution = await self.agents.workflow_coord.start_workflow(
            WorkflowType.FEATURE_IMPLEMENTATION,
            description=feature_description
        )

        return {
            "workflow_id": execution.workflow_id,
            "workflow_type": "feature_implementation",
            "total_steps": 5,
            "estimated_minutes": 240,
            "agents_active": True
        }

    # ========================================================================
    # /sc:troubleshoot Command Integration
    # ========================================================================

    async def start_bug_workflow(
        self,
        bug_description: str
    ) -> Dict[str, Any]:
        """
        Start bug investigation workflow.

        Integrates: WorkflowCoordinator (Bug Investigation template)

        Args:
            bug_description: Bug to investigate

        Returns:
            Workflow execution info
        """
        if not self.agents.workflow_coord:
            raise RuntimeError("WorkflowCoordinator not initialized")

        execution = await self.agents.workflow_coord.start_workflow(
            WorkflowType.BUG_INVESTIGATION,
            description=bug_description
        )

        return {
            "workflow_id": execution.workflow_id,
            "workflow_type": "bug_investigation",
            "total_steps": 4,
            "estimated_minutes": 165,
            "agents_active": True
        }

    # ========================================================================
    # /sc:design Command Integration
    # ========================================================================

    async def start_architecture_workflow(
        self,
        decision_description: str
    ) -> Dict[str, Any]:
        """
        Start architecture decision workflow.

        Integrates: WorkflowCoordinator (Architecture Decision template)

        Args:
            decision_description: Decision to make

        Returns:
            Workflow execution info
        """
        if not self.agents.workflow_coord:
            raise RuntimeError("WorkflowCoordinator not initialized")

        execution = await self.agents.workflow_coord.start_workflow(
            WorkflowType.ARCHITECTURE_DECISION,
            description=decision_description
        )

        return {
            "workflow_id": execution.workflow_id,
            "workflow_type": "architecture_decision",
            "total_steps": 3,
            "estimated_minutes": 135,
            "agents_active": True
        }

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _map_energy(self, complexity: float) -> str:
        """Map complexity to energy level"""
        if complexity < 0.4:
            return "low"
        elif complexity < 0.7:
            return "medium"
        else:
            return "high"

    async def validate_code_compliance(
        self,
        file_path: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Validate code compliance.

        Integrates: DopemuxEnforcer

        Args:
            file_path: Path to file
            content: File content

        Returns:
            Compliance report
        """
        if not self.agents.enforcer:
            return {"compliant": True, "message": "Enforcer not initialized"}

        report = await self.agents.enforcer.validate_code_change(
            file_path=file_path,
            content=content
        )

        return {
            "compliant": report.compliant,
            "violations": len(report.violations),
            "summary": report.summary,
            "details": [
                {
                    "severity": v.severity.value,
                    "message": v.message,
                    "suggestion": v.suggestion
                }
                for v in report.violations
            ]
        }

    async def get_pm_tasks(self, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """
        Get tasks from PM plane.

        Integrates: TwoPlaneOrchestrator

        Args:
            status_filter: Optional status filter

        Returns:
            Tasks from PM plane
        """
        if not self.agents.two_plane:
            return {"tasks": [], "source": "no_orchestrator"}

        result = await self.agents.two_plane.cognitive_to_pm(
            operation="get_tasks",
            data={"status": status_filter} if status_filter else {}
        )

        return result

    async def end_session(self):
        """End active session and cleanup"""
        if self.agents.memory and self.active_session:
            await self.agents.memory.end_session()

        if self.agents.guardian:
            await self.agents.guardian.stop_monitoring()

        self.active_session = None

    async def close(self):
        """Shutdown all agents"""
        # Close agents that have close() methods
        for agent_name in ["two_plane", "enforcer", "tool_selector", "task_decomp", "workflow_coord"]:
            agent = getattr(self.agents, agent_name, None)
            if agent and hasattr(agent, 'close'):
                try:
                    await agent.close()
                except Exception as e:
                    logger.warning(f"Error closing {agent_name}: {e}")

        logger.info("✅ SuperClaude integration shutdown complete")


# ============================================================================
# Command Integration Examples
# ============================================================================

async def demo_sc_implement():
    """Demo: /sc:implement integration"""
    print("\n" + "="*70)
    print("/sc:implement Integration Demo")
    print("="*70)

    integration = SuperClaudeIntegration(
        workspace_id="/Users/hue/code/dopemux-mvp"
    )

    await integration.initialize()

    # Start implementation session
    session = await integration.start_implementation_session(
        task_description="Add JWT authentication",
        estimated_complexity=0.6,
        duration_minutes=25
    )

    print("\n✅ Session Started:")
    print(f"  Ready: {session['readiness']['ready']}")
    if session['tools_selected']:
        tools_info = session['tools_selected'].get('primary', {})
        if hasattr(tools_info, 'primary_tool'):
            print(f"  Tools: {tools_info.primary_tool} + {tools_info.model}")
        else:
            print(f"  Tools: {tools_info}")
    else:
        print(f"  Tools: (selection unavailable)")
    print(f"  Break at: {session['break_reminder_at']} min")

    await integration.close()


async def demo_sc_brainstorm():
    """Demo: /sc:brainstorm (TaskDecomposer)"""
    print("\n" + "="*70)
    print("/sc:brainstorm Integration Demo (TaskDecomposer)")
    print("="*70)

    integration = SuperClaudeIntegration(
        workspace_id="/Users/hue/code/dopemux-mvp"
    )

    await integration.initialize(agents_to_load=["task_decomp", "tool_selector", "guardian"])

    # Decompose PRD
    prd = """
## Authentication Feature

Implement JWT-based authentication with login, logout, and token refresh.

## Requirements
- POST /auth/login
- POST /auth/logout
- POST /auth/refresh
- JWT token generation
- Token validation middleware
"""

    result = await integration.decompose_prd(prd, max_tasks=10)

    print(f"\n✅ PRD Decomposed:")
    print(f"  Tasks: {len(result['tasks'])}")
    print(f"  ADHD Optimized: {result['adhd_optimized']}")

    for i, task in enumerate(result['tasks'][:3], 1):
        print(f"\n  {i}. {task.title}")
        print(f"     Complexity: {task.complexity}, Energy: {task.energy_required}")

    await integration.close()


async def demo_sc_troubleshoot():
    """Demo: /sc:troubleshoot (Bug workflow)"""
    print("\n" + "="*70)
    print("/sc:troubleshoot Integration Demo (WorkflowCoordinator)")
    print("="*70)

    integration = SuperClaudeIntegration(
        workspace_id="/Users/hue/code/dopemux-mvp"
    )

    await integration.initialize(agents_to_load=["workflow_coord", "memory"])

    # Start bug workflow
    workflow = await integration.start_bug_workflow(
        bug_description="Login fails with 401 error"
    )

    print(f"\n✅ Bug Workflow Started:")
    print(f"  Workflow ID: {workflow['workflow_id']}")
    print(f"  Steps: {workflow['total_steps']}")
    print(f"  Estimated: {workflow['estimated_minutes']} min")

    await integration.close()


async def main():
    """Run all integration demos"""
    print("\n" + "="*70)
    print("SUPERCLAUDE INTEGRATION DEMOS - Weeks 15-16")
    print("="*70)

    await demo_sc_implement()
    await demo_sc_brainstorm()
    await demo_sc_troubleshoot()

    print("\n" + "="*70)
    print("✅ All integration demos complete!")
    print("="*70)
    print("\nSuperClaude commands can now use all 7 Dopemux agents!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
