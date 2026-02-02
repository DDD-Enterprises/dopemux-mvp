"""
ConPort Insight Publisher - Architecture 3.0 Component 2

Publishes AI agent decisions and insights to ConPort knowledge graph.
Enables automatic linking between decisions and related tasks.

Created: 2025-10-19 (Task 2.3)
Specification: docs/implementation-plans/conport-event-schema-design.md
"""

import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

# Import from parent directory
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from enhanced_orchestrator import AgentType

logger = logging.getLogger(__name__)


# ============================================================================
# AI Decision Event Schema (from Task 2.1 Specification)
# ============================================================================

@dataclass
class AIDecisionEvent:
    """
    Event representing an AI agent decision to be logged in ConPort.

    Based on Task 2.1 specification for AI decision capture pattern.
    """
    # === Decision Content ===
    summary: str                           # Concise decision statement
    rationale: str                         # Why this decision was made
    implementation_details: str            # How to implement this decision

    # === AI Metadata ===
    agent_type: AgentType                  # Which AI agent made the decision
    confidence: float                      # 0.0-1.0 confidence score
    alternatives_considered: List[str]     # Other options evaluated

    # === Linking ===
    related_task_id: Optional[str] = None           # OrchestrationTask.id this relates to
    related_conport_progress_id: Optional[int] = None  # ConPort progress_entry ID

    # === Tags ===
    tags: List[str] = None                 # Custom tags (auto-generated if None)

    # === Metadata ===
    decision_id: Optional[int] = None      # ConPort decision ID (set after creation)
    timestamp: Optional[datetime] = None   # Auto-set if None

    def __post_init__(self):
        """Initialize defaults."""
        if self.tags is None:
            # Auto-generate tags
            self.tags = [
                "ai-generated",
                f"agent-{self.agent_type.value}",
                f"confidence-{int(self.confidence * 10)}"
            ]

        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_conport_decision(self) -> Dict[str, Any]:
        """
        Convert to ConPort decision format.

        Returns dict ready for mcp__conport__log_decision() call.
        """
        return {
            "summary": self.summary,
            "rationale": self.rationale,
            "implementation_details": self.implementation_details,
            "tags": self.tags
        }


# ============================================================================
# ConPort Insight Publisher
# ============================================================================

class ConPortInsightPublisher:
    """
    Publisher for AI agent insights and decisions to ConPort knowledge graph.

    Features:
    - Log AI decisions to ConPort
    - Automatic linking to related tasks
    - Batch decision logging
    - Error handling with graceful degradation

    Usage:
        publisher = ConPortInsightPublisher(workspace_id, conport_client)
        decision_id = await publisher.log_ai_decision(ai_decision_event)
        await publisher.link_decision_to_task(decision_id, task_conport_id)
    """

    def __init__(self, workspace_id: str, conport_client: Any = None):
        """
        Initialize insight publisher.

        Args:
            workspace_id: Absolute path to workspace
            conport_client: ConPort MCP client (optional, uses placeholder if None)
        """
        self.workspace_id = workspace_id
        self.conport_client = conport_client
        self.decision_cache: Dict[str, AIDecisionEvent] = {}  # Local cache

    # ------------------------------------------------------------------------
    # Decision Logging Methods
    # ------------------------------------------------------------------------

    async def log_ai_decision(self, event: AIDecisionEvent) -> Optional[int]:
        """
        Log AI agent decision to ConPort.

        Args:
            event: AIDecisionEvent to log

        Returns:
            ConPort decision ID if successful, None otherwise
        """
        try:
            # Convert to ConPort format
            decision_data = event.to_conport_decision()
            decision_data["workspace_id"] = self.workspace_id

            # Call ConPort with retry
            decision_id = await self._resilient_log_decision(decision_data)

            if decision_id:
                # Store decision ID in event
                event.decision_id = decision_id

                # Auto-link to related task if specified
                if event.related_conport_progress_id:
                    await self.link_decision_to_task(
                        decision_id,
                        event.related_conport_progress_id
                    )

                logger.info(f"✅ Logged AI decision to ConPort: {event.summary[:50]}... (ID: {decision_id})")
                return decision_id
            else:
                # Fallback: Cache locally
                self.decision_cache[event.summary] = event
                logger.warning(f"⚠️ ConPort unavailable, cached decision locally")
                return None

        except Exception as e:
            logger.error(f"Failed to log AI decision: {e}")
            return None

    async def link_decision_to_task(
        self,
        decision_id: int,
        task_conport_id: int,
        relationship_type: str = "informs_implementation"
    ) -> bool:
        """
        Link AI decision to related task in ConPort knowledge graph.

        Args:
            decision_id: ConPort decision ID
            task_conport_id: ConPort progress_entry ID
            relationship_type: Type of relationship (default: "informs_implementation")

        Returns:
            True if link created successfully
        """
        try:
            if not self.conport_client:
                logger.warning("ConPort client not configured for linking")
                return False

            # Call ConPort link_conport_items
            await self.conport_client.link_conport_items(
                workspace_id=self.workspace_id,
                source_item_type="decision",
                source_item_id=str(decision_id),
                target_item_type="progress_entry",
                target_item_id=str(task_conport_id),
                relationship_type=relationship_type,
                description=f"AI decision {decision_id} {relationship_type} task {task_conport_id}"
            )

            logger.info(f"📎 Linked decision {decision_id} to task {task_conport_id} ({relationship_type})")
            return True

        except Exception as e:
            logger.error(f"Failed to link decision to task: {e}")
            return False

    async def batch_log_decisions(self, events: List[AIDecisionEvent]) -> List[Optional[int]]:
        """
        Log multiple AI decisions to ConPort.

        Args:
            events: List of AIDecisionEvent objects

        Returns:
            List of ConPort decision IDs (None for failures)
        """
        decision_ids = []

        for event in events:
            decision_id = await self.log_ai_decision(event)
            decision_ids.append(decision_id)

        successful = sum(1 for id in decision_ids if id is not None)
        logger.info(f"✅ Batch logged {successful}/{len(events)} AI decisions to ConPort")

        return decision_ids

    # ------------------------------------------------------------------------
    # AI Agent Result Parsing
    # ------------------------------------------------------------------------

    def parse_zen_result(self, zen_result: Dict[str, Any], task_id: Optional[str] = None) -> AIDecisionEvent:
        """
        Parse Zen MCP agent result into AIDecisionEvent.

        Args:
            zen_result: Result from Zen thinkdeep/consensus/debug
            task_id: Related OrchestrationTask ID

        Returns:
            AIDecisionEvent ready to log
        """
        return AIDecisionEvent(
            summary=zen_result.get("summary", "Zen analysis result"),
            rationale=zen_result.get("rationale", zen_result.get("findings", "")),
            implementation_details=zen_result.get("details", zen_result.get("recommendations", "")),
            agent_type=AgentType.ZEN,
            confidence=zen_result.get("confidence", 0.7),
            alternatives_considered=zen_result.get("alternatives", []),
            related_task_id=task_id,
            tags=["ai-generated", "agent-zen", zen_result.get("tool", "unknown")]
        )

    def parse_serena_result(self, serena_result: Dict[str, Any], task_id: Optional[str] = None) -> AIDecisionEvent:
        """
        Parse Serena MCP agent result into AIDecisionEvent.

        Args:
            serena_result: Result from Serena code analysis
            task_id: Related OrchestrationTask ID

        Returns:
            AIDecisionEvent ready to log
        """
        return AIDecisionEvent(
            summary=serena_result.get("summary", "Serena code analysis"),
            rationale=serena_result.get("analysis", ""),
            implementation_details=serena_result.get("recommendations", ""),
            agent_type=AgentType.SERENA,
            confidence=serena_result.get("confidence", 0.8),
            alternatives_considered=[],
            related_task_id=task_id,
            tags=["ai-generated", "agent-serena", "code-analysis"]
        )

    def parse_taskmaster_result(self, taskmaster_result: Dict[str, Any], task_id: Optional[str] = None) -> AIDecisionEvent:
        """
        Parse TaskMaster agent result into AIDecisionEvent.

        Args:
            taskmaster_result: Result from TaskMaster PRD parsing
            task_id: Related OrchestrationTask ID

        Returns:
            AIDecisionEvent ready to log
        """
        return AIDecisionEvent(
            summary=taskmaster_result.get("summary", "TaskMaster PRD analysis"),
            rationale=taskmaster_result.get("complexity_analysis", ""),
            implementation_details=taskmaster_result.get("decomposition", ""),
            agent_type=AgentType.TASKMASTER,
            confidence=taskmaster_result.get("confidence", 0.75),
            alternatives_considered=[],
            related_task_id=task_id,
            tags=["ai-generated", "agent-taskmaster", "prd-parsing"]
        )

    # ------------------------------------------------------------------------
    # ConPort MCP Client Methods (Resilient wrappers)
    # ------------------------------------------------------------------------

    async def _resilient_log_decision(self, decision_data: Dict) -> Optional[int]:
        """
        Log decision to ConPort with retry logic.

        Returns ConPort decision ID if successful, None otherwise.
        """
        max_retries = 3

        for attempt in range(max_retries):
            try:
                if self.conport_client:
                    # Call actual ConPort MCP client
                    result = await self.conport_client.log_decision(**decision_data)
                    return result.get("id")
                else:
                    # Placeholder: No client available
                    logger.warning("ConPort client not configured for decision logging")
                    return None

            except ConnectionError as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"ConPort connection failed (attempt {attempt+1}/{max_retries}), retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"ConPort unavailable after {max_retries} attempts: {e}")
                    return None

            except Exception as e:
                logger.error(f"ConPort API error: {e}")
                return None

        return None

    # ------------------------------------------------------------------------
    # Utility Methods
    # ------------------------------------------------------------------------

    def get_cache_stats(self) -> Dict[str, int]:
        """Get local cache statistics."""
        return {
            "cached_decisions": len(self.decision_cache),
            "cache_size_bytes": sum(len(str(v)) for v in self.decision_cache.values())
        }

    async def flush_cache_to_conport(self) -> int:
        """
        Flush locally cached decisions to ConPort.

        Returns number of decisions successfully flushed.
        """
        if not self.decision_cache:
            return 0

        flushed = 0
        failed_events = {}

        for summary, event in self.decision_cache.items():
            decision_id = await self.log_ai_decision(event)
            if decision_id:
                flushed += 1
            else:
                failed_events[summary] = event

        # Update cache with only failed events
        self.decision_cache = failed_events

        logger.info(f"✅ Flushed {flushed} cached decisions to ConPort, {len(failed_events)} remain")
        return flushed


# ============================================================================
# Convenience Functions
# ============================================================================

def create_architecture_decision(
    summary: str,
    rationale: str,
    implementation_details: str,
    agent_type: AgentType = AgentType.ZEN,
    confidence: float = 0.8,
    task_id: Optional[str] = None
) -> AIDecisionEvent:
    """
    Convenience function to create architecture decision event.

    Args:
        summary: Decision summary
        rationale: Why this decision
        implementation_details: How to implement
        agent_type: Which agent made decision (default: Zen)
        confidence: Confidence score 0.0-1.0
        task_id: Related task ID

    Returns:
        AIDecisionEvent ready to log
    """
    return AIDecisionEvent(
        summary=summary,
        rationale=rationale,
        implementation_details=implementation_details,
        agent_type=agent_type,
        confidence=confidence,
        alternatives_considered=[],
        related_task_id=task_id,
        tags=["ai-generated", f"agent-{agent_type.value}", "architecture"]
    )


def create_code_review_decision(
    summary: str,
    findings: str,
    recommendations: str,
    agent_type: AgentType = AgentType.SERENA,
    severity: str = "medium",
    task_id: Optional[str] = None
) -> AIDecisionEvent:
    """
    Convenience function to create code review decision event.

    Args:
        summary: Review summary
        findings: What was found
        recommendations: What to do
        agent_type: Which agent reviewed (default: Serena)
        severity: Issue severity (low/medium/high/critical)
        task_id: Related task ID

    Returns:
        AIDecisionEvent ready to log
    """
    return AIDecisionEvent(
        summary=summary,
        rationale=findings,
        implementation_details=recommendations,
        agent_type=agent_type,
        confidence=0.7,  # Code review confidence typically moderate
        alternatives_considered=[],
        related_task_id=task_id,
        tags=["ai-generated", f"agent-{agent_type.value}", "code-review", f"severity-{severity}"]
    )
