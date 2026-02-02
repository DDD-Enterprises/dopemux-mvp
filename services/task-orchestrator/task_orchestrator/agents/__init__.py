"""
Task-Orchestrator Agent Coordination.

AI agent assignment, dispatch, and pool management.
Extracted from enhanced_orchestrator.py lines 693-960.
"""

import logging
from typing import Any, Dict, List, Optional

from ..config import settings
from ..models import AgentPoolEntry, AgentType, OrchestrationTask


logger = logging.getLogger(__name__)


class AgentCoordinator:
    """Manages AI agent pool and task assignment."""

    def __init__(self):
        self.agent_pool: Dict[AgentType, AgentPoolEntry] = {}
        self.metrics = {
            "ai_agent_dispatches": 0,
            "adhd_accommodations_applied": 0
        }
        # CognitiveGuardian for ADHD-aware routing
        self.cognitive_guardian = None

    def initialize_pool(self):
        """Initialize AI agent pool."""
        self.agent_pool = {
            AgentType.CONPORT: AgentPoolEntry(
                available=True,
                capabilities=["decision_logging", "progress_tracking", "context_management"],
                max_concurrent=5
            ),
            AgentType.SERENA: AgentPoolEntry(
                available=True,
                capabilities=["code_navigation", "file_analysis", "refactoring"],
                max_concurrent=3
            ),
            AgentType.TASKMASTER: AgentPoolEntry(
                available=True,
                capabilities=["prd_parsing", "complexity_analysis", "research"],
                max_concurrent=2
            ),
            AgentType.PAL: AgentPoolEntry(
                available=True,
                capabilities=["consensus", "code_review", "architecture_analysis"],
                max_concurrent=1  # Intensive operations
            )
        }
        logger.info("🤖 AI agent pool initialized")

    async def assign_optimal_agent(self, task: OrchestrationTask) -> Optional[AgentType]:
        """
        Assign optimal AI agent based on task characteristics with ADHD awareness.

        Checks (in order):
        1. User readiness (energy + complexity + attention matching)
        2. Complexity threshold (>0.8 → Pal for multi-model analysis)
        3. Keyword-based routing
        4. Default fallback
        """
        try:
            # Step 1: ADHD readiness check (if CognitiveGuardian available)
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
                    
                    user_state = await self.cognitive_guardian.get_user_state()
                    if user_state.session_duration_minutes >= 90:
                        logger.error("🛑 MANDATORY BREAK REQUIRED - No tasks assigned")
                        return None  # Special signal for break enforcement
                    
                    return None

            # Step 2: High-complexity check (before keywords)
            if task.complexity_score > 0.8:
                logger.info(
                    f"🌟 High complexity task ({task.complexity_score:.2f}) → Pal "
                    f"(multi-model analysis)"
                )
                return AgentType.PAL

            # Step 3: Keyword-based routing
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

            # Step 4: Default fallback - ConPort for progress tracking
            return AgentType.CONPORT

        except Exception as e:
            logger.error(f"Agent assignment failed: {e}")
            return None

    async def dispatch_to_agent(
        self,
        task: OrchestrationTask,
        agent: AgentType
    ) -> bool:
        """Dispatch task to assigned AI agent."""
        try:
            agent_entry = self.agent_pool.get(agent)
            if not agent_entry or not agent_entry.available:
                logger.warning(f"Agent {agent.value} not available")
                return False

            if len(agent_entry.current_tasks) >= agent_entry.max_concurrent:
                logger.warning(f"Agent {agent.value} at capacity")
                return False

            # Add task to agent's current tasks
            agent_entry.current_tasks.append(task.id)
            self.metrics["ai_agent_dispatches"] += 1

            logger.info(f"🚀 Dispatched task '{task.title}' to {agent.value}")
            return True

        except Exception as e:
            logger.error(f"Agent dispatch failed: {e}")
            return False

    async def release_task(self, task_id: str, agent: AgentType):
        """Release task from agent's current tasks."""
        agent_entry = self.agent_pool.get(agent)
        if agent_entry and task_id in agent_entry.current_tasks:
            agent_entry.current_tasks.remove(task_id)
            logger.debug(f"Released task {task_id} from {agent.value}")

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents."""
        return {
            agent.value: {
                "available": entry.available,
                "current_load": len(entry.current_tasks),
                "max_concurrent": entry.max_concurrent,
                "capabilities": entry.capabilities
            }
            for agent, entry in self.agent_pool.items()
        }


# Global singleton instance
agent_coordinator = AgentCoordinator()
