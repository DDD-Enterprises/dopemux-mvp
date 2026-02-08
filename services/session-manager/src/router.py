"""
Command Router - Step 6 of Phase 1
Routes parsed commands to appropriate AI agents based on mode and complexity

Integrates:
- Command Parser (intent classification)
- Agent Spawner (AI instance management)
- Message Bus (event coordination)
- Context Protocol (ConPort integration)

Complexity: 0.50 (Medium)
Effort: 5 focus blocks (125 minutes)
"""

from typing import Optional

import logging

logger = logging.getLogger(__name__)

from dataclasses import dataclass
from datetime import datetime
import re

from command_parser import CommandParser, ParsedCommand, TargetAgent
from agent_spawner import AgentSpawner, AgentType
from message_bus_v2 import MessageBus, Event, EventType
from context_protocol import ContextSharingProtocol


@dataclass
class RoutingDecision:
    """Result of routing logic."""

    target_agents: list[AgentType]  # Which agents to use
    coordination_strategy: str  # single, parallel, sequential
    context_detail_level: int  # 1-3 for progressive disclosure
    estimated_duration_minutes: int
    adhd_recommendation: str


class CommandRouter:
    """
    Route commands to appropriate AI agents.

    Routing logic:
    1. Parse command (intent + complexity)
    2. Select agent(s) based on mode
    3. Assemble context for agent
    4. Send command via agent spawner
    5. Publish events via message bus
    6. Aggregate results
    """

    def __init__(
        self,
        parser: CommandParser,
        spawner: AgentSpawner,
        message_bus: MessageBus,
        context_protocol: ContextSharingProtocol,
    ):
        """
        Initialize command router.

        Args:
            parser: Command parser for intent classification
            spawner: Agent spawner for AI instance management
            message_bus: Message bus for event coordination
            context_protocol: ConPort context sharing
        """
        self.parser = parser
        self.spawner = spawner
        self.bus = message_bus
        self.context = context_protocol

    def route_command(
        self, 
        user_input: str,
        workspace_path: Optional[str] = None,
        workspace_paths: Optional[list[str]] = None,
    ) -> dict:
        """
        Route user command to appropriate AI agent(s).

        Args:
            user_input: Raw user input
            workspace_path: Single workspace path (optional)
            workspace_paths: Multiple workspace paths (optional)

        Returns:
            Routing result with agent responses

        Example:
            >>> result = router.route_command("Research OAuth2 best practices")
            >>> result["agents"]  # [AgentType.GEMINI]
            >>> result["responses"]  # [gemini's response]
        """
        # Step 1: Parse command
        parsed = self.parser.parse(user_input)
        
        # Add workspace context if provided
        if workspace_path or workspace_paths:
            try:
                from workspace_support import add_workspace_context
                # Enhance parsed command with workspace context
                parsed_dict = {
                    "command": user_input,
                    "mode": parsed.mode.value,
                    "target": parsed.target_agent.value,
                }
                parsed_dict = add_workspace_context(
                    parsed_dict,
                    workspace_path,
                    workspace_paths,
                )
                # Store workspace context for downstream use
                parsed.workspace_context = parsed_dict.get("_workspace_context")
            except Exception as e:
                # Workspace support optional - don't fail if unavailable
                parsed.workspace_context = None

                logger.error(f"Error: {e}")
        # Step 2: Make routing decision
        routing = self._make_routing_decision(parsed)

        # Step 3: Publish command sent event
        self.bus.publish(
            Event(
                type=EventType.COMMAND_SENT,
                source="router",
                timestamp=datetime.now(),
                payload={
                    "command": user_input,
                    "parsed_mode": parsed.mode.value,
                    "target_agents": [a.value for a in routing.target_agents],
                    "complexity": parsed.complexity_score,
                },
            )
        )

        # Step 4: Execute routing strategy
        if routing.coordination_strategy == "single":
            result = self._execute_single_agent(parsed, routing)
        elif routing.coordination_strategy == "parallel":
            result = self._execute_parallel(parsed, routing)
        elif routing.coordination_strategy == "sequential":
            result = self._execute_sequential(parsed, routing)
        else:
            result = {"error": f"Unknown strategy: {routing.coordination_strategy}"}

        # Step 5: Publish completion event
        self.bus.publish(
            Event(
                type=EventType.COMMAND_COMPLETED,
                source="router",
                timestamp=datetime.now(),
                payload={"command": user_input, "result": result},
            )
        )

        return result

    def _make_routing_decision(self, parsed: ParsedCommand) -> RoutingDecision:
        """
        Decide how to route this command.

        Args:
            parsed: Parsed command with intent and complexity

        Returns:
            Routing decision
        """
        # Determine target agents
        if parsed.target_agent == TargetAgent.ALL:
            agents = [AgentType.CLAUDE, AgentType.GEMINI, AgentType.GROK]
            strategy = "parallel"
        elif parsed.target_agent == TargetAgent.AUTO:
            # Use mode-based selection from parser
            agent_map = {
                TargetAgent.CLAUDE: AgentType.CLAUDE,
                TargetAgent.GEMINI: AgentType.GEMINI,
                TargetAgent.GROK: AgentType.GROK,
            }
            # Parser already selected optimal agent
            selected = parsed.target_agent
            agents = [agent_map.get(selected, AgentType.CLAUDE)]
            strategy = "single"
        else:
            # Explicit agent specified
            agent_map = {
                TargetAgent.CLAUDE: AgentType.CLAUDE,
                TargetAgent.GEMINI: AgentType.GEMINI,
                TargetAgent.GROK: AgentType.GROK,
            }
            agents = [agent_map[parsed.target_agent]]
            strategy = "single"

        # High complexity override
        if parsed.complexity_score >= 0.7 and strategy == "single":
            # Suggest parallel validation
            agents.append(AgentType.GEMINI)  # Add validator
            strategy = "parallel"

        # Determine context detail level
        if parsed.complexity_score < 0.3:
            detail_level = 1  # Low complexity = minimal context
        elif parsed.complexity_score < 0.7:
            detail_level = 2  # Medium = moderate context
        else:
            detail_level = 3  # High = full context

        # Estimate duration (ADHD planning)
        # Base: 25 minutes per focus block
        focus_blocks = 1
        if parsed.complexity_score >= 0.7:
            focus_blocks = 3
        elif parsed.complexity_score >= 0.4:
            focus_blocks = 2

        estimated_minutes = focus_blocks * 25

        # ADHD recommendation
        if focus_blocks == 1:
            adhd_rec = "Quick task - complete in current session"
        elif focus_blocks == 2:
            adhd_rec = "Moderate task - take a break halfway"
        else:
            adhd_rec = "Complex task - schedule dedicated focus time, break into subtasks"

        return RoutingDecision(
            target_agents=agents,
            coordination_strategy=strategy,
            context_detail_level=detail_level,
            estimated_duration_minutes=estimated_minutes,
            adhd_recommendation=adhd_rec,
        )

    def _execute_single_agent(
        self, parsed: ParsedCommand, routing: RoutingDecision
    ) -> dict:
        """Execute command with single agent."""
        agent_type = routing.target_agents[0]

        # Assemble context
        context = self.context.get_context_for_agent(
            agent_type=agent_type.value,
            task_description=parsed.message,
            detail_level=routing.context_detail_level,
        )

        # Build prompt with context
        prompt = self._build_prompt_with_context(parsed.message, context)

        # Send to agent
        response = self.spawner.send_to_agent(agent_type, prompt)

        return {
            "agents": [agent_type.value],
            "responses": {agent_type.value: response},
            "strategy": "single",
            "estimated_duration": routing.estimated_duration_minutes,
        }

    def _execute_parallel(
        self, parsed: ParsedCommand, routing: RoutingDecision
    ) -> dict:
        """Execute command with multiple agents in parallel."""
        import concurrent.futures

        # Assemble context once (shared across agents)
        context = self.context.get_context_for_agent(
            agent_type="multi",  # Generic context
            task_description=parsed.message,
            detail_level=routing.context_detail_level,
        )

        def send_to_agent(agent_type):
            prompt = self._build_prompt_with_context(parsed.message, context)
            return agent_type, self.spawner.send_to_agent(agent_type, prompt)

        # Execute in parallel
        responses = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(send_to_agent, agent_type)
                for agent_type in routing.target_agents
            ]

            for future in concurrent.futures.as_completed(futures):
                agent_type, response = future.result()
                responses[agent_type.value] = response

        return {
            "agents": [a.value for a in routing.target_agents],
            "responses": responses,
            "strategy": "parallel",
            "estimated_duration": routing.estimated_duration_minutes,
        }

    def _execute_sequential(
        self, parsed: ParsedCommand, routing: RoutingDecision
    ) -> dict:
        """Execute command sequentially through agents (research → plan → implement)."""
        responses = {}

        for agent_type in routing.target_agents:
            # Get context (may include previous agent's results)
            context = self.context.get_context_for_agent(
                agent_type=agent_type.value,
                task_description=parsed.message,
                detail_level=routing.context_detail_level,
            )

            # Build prompt
            prompt = self._build_prompt_with_context(parsed.message, context)

            # Send to agent
            response = self.spawner.send_to_agent(agent_type, prompt)
            responses[agent_type.value] = response

            # Save result to ConPort for next agent
            if response:
                confidence = self._estimate_response_confidence(response)
                self.context.publish_artifact(
                    artifact_type=f"{parsed.mode.value}_result",
                    agent_type=agent_type.value,
                    content=response,
                    confidence=confidence,
                )

        return {
            "agents": [a.value for a in routing.target_agents],
            "responses": responses,
            "strategy": "sequential",
            "estimated_duration": routing.estimated_duration_minutes,
        }

    def _build_prompt_with_context(self, message: str, context: dict) -> str:
        """
        Build prompt with context for AI agent.

        Args:
            message: User's message/question
            context: Relevant context from ConPort

        Returns:
            Complete prompt with context
        """
        if not context:
            return message

        # Format context for AI
        context_str = "# Context\n\n"

        if "recent_decisions" in context:
            context_str += "## Recent Decisions:\n"
            for dec in context["recent_decisions"]:
                context_str += f"- {dec.get('content', dec)}\n"

        if "related_artifacts" in context:
            context_str += "\n## Related Information:\n"
            for artifact in context["related_artifacts"]:
                context_str += f"- {artifact.get('content', artifact)}\n"

        context_str += f"\n# Task\n\n{message}"

        return context_str

    def _estimate_response_confidence(self, response: Optional[list[str]]) -> float:
        """
        Estimate confidence from raw agent response content.

        Heuristic only: rewards substantive responses and penalizes explicit uncertainty.
        """
        if not response:
            return 0.2

        text = "\n".join(response).strip()
        if not text:
            return 0.2

        length = len(text)
        if length >= 1200:
            confidence = 0.9
        elif length >= 600:
            confidence = 0.82
        elif length >= 200:
            confidence = 0.74
        else:
            confidence = 0.62

        uncertainty_patterns = [
            r"\bnot sure\b",
            r"\bmaybe\b",
            r"\bmight\b",
            r"\bi think\b",
            r"\buncertain\b",
            r"\bcan't\b",
            r"\bunable to\b",
        ]
        for pattern in uncertainty_patterns:
            if re.search(pattern, text, flags=re.IGNORECASE):
                confidence -= 0.08

        if re.search(r"\b(error|exception|failed)\b", text, flags=re.IGNORECASE):
            confidence -= 0.12

        return max(0.1, min(0.95, confidence))


if __name__ == "__main__":
    """Test command router (dry run without real agents)."""
    from datetime import datetime

    logger.info("Testing Command Router:")
    logger.info("=" * 60)

    # Mock components
    from message_bus_v2 import create_message_bus

    parser = CommandParser()
    # spawner = AgentSpawner()  # Would need real agents
    bus = create_message_bus("in_memory")
    context_protocol = ContextSharingProtocol(
        workspace_id="/Users/hue/code/ui-build", session_id="test"
    )

    # Note: Can't fully test without spawner having agents
    # But we can test routing decisions

    logger.info("\nTesting routing decisions:")

    test_commands = [
        "Research OAuth2 PKCE flow",
        "Design authentication architecture",
        "Implement JWT tokens",
        "/consensus should we use microservices?",
    ]

    for cmd in test_commands:
        parsed = parser.parse(cmd)
        # routing = router._make_routing_decision(parsed)  # Would need router instance

        logger.info(f"\nCommand: {cmd}")
        logger.info(f"  Mode: {parsed.mode.value}")
        logger.info(f"  Agent: {parsed.target_agent.value}")
        logger.info(f"  Complexity: {parsed.complexity_score:.2f}")

    bus.shutdown()
    logger.info("\n✅ Router logic test complete")
