"""
Context Sharing Protocol - ConPort Integration
Enables AI agents to share context via persistent knowledge graph

Based on Zen architectural recommendation:
- ConPort as context bus (not ephemeral message passing)
- Explicit protocol prevents ad-hoc sharing
- Persistent across interruptions
"""

from typing import Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class AIArtifact:
    """Artifact produced by an AI agent."""

    artifact_type: str  # decision, analysis, code, plan, debug_finding
    agent_type: str  # claude, gemini, grok
    content: Any  # The actual artifact
    confidence: float  # 0.0-1.0
    timestamp: datetime
    metadata: dict[str, Any]


class ContextSharingProtocol:
    """
    Standard protocol for AI agents to share context via ConPort.

    Design principles:
    - Explicit is better than implicit
    - Persistent beats ephemeral
    - Queryable beats linear
    """

    def __init__(self, workspace_id: str, session_id: str):
        """
        Initialize context protocol.

        Args:
            workspace_id: ConPort workspace ID
            session_id: Current session ID for scoping
        """
        self.workspace_id = workspace_id
        self.session_id = session_id
        # TODO: Initialize ConPort client

    def publish_artifact(
        self,
        artifact_type: str,
        agent_type: str,
        content: Any,
        confidence: float = 0.8,
        metadata: Optional[dict] = None,
    ) -> str:
        """
        AI agent publishes artifact to ConPort.

        Args:
            artifact_type: Type of artifact (decision, analysis, code, etc.)
            agent_type: Which AI produced this
            content: The artifact content
            confidence: Confidence score
            metadata: Additional metadata

        Returns:
            Artifact ID for reference

        Example:
            >>> protocol.publish_artifact(
            ...     artifact_type="decision",
            ...     agent_type="claude",
            ...     content="Use JWT tokens for stateless auth",
            ...     confidence=0.85,
            ...     metadata={"rationale": "Scalability benefits..."}
            ... )
            "artifact_12345"
        """
        artifact = AIArtifact(
            artifact_type=artifact_type,
            agent_type=agent_type,
            content=content,
            confidence=confidence,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )

        # Store in ConPort custom_data
        key = f"{self.session_id}_{artifact_type}_{datetime.now().timestamp()}"

        # TODO: Implement ConPort write
        # conport.log_custom_data(
        #     workspace_id=self.workspace_id,
        #     category=f"ai_artifacts",
        #     key=key,
        #     value={
        #         "artifact_type": artifact_type,
        #         "agent_type": agent_type,
        #         "content": content,
        #         "confidence": confidence,
        #         "metadata": metadata,
        #         "session_id": self.session_id
        #     }
        # )

        print(f"📦 Published {artifact_type} from {agent_type} (confidence: {confidence:.0%})")
        return key

    def query_artifacts(
        self,
        artifact_type: Optional[str] = None,
        agent_type: Optional[str] = None,
        min_confidence: float = 0.5,
        limit: int = 10,
    ) -> list[AIArtifact]:
        """
        Query artifacts from ConPort.

        Args:
            artifact_type: Filter by type (optional)
            agent_type: Filter by source agent (optional)
            min_confidence: Minimum confidence threshold
            limit: Max results to return

        Returns:
            List of matching artifacts

        Example:
            >>> # Get recent decisions from Claude
            >>> artifacts = protocol.query_artifacts(
            ...     artifact_type="decision",
            ...     agent_type="claude",
            ...     min_confidence=0.7
            ... )
        """
        # TODO: Implement ConPort query
        # results = conport.get_custom_data(
        #     workspace_id=self.workspace_id,
        #     category="ai_artifacts",
        #     limit=limit
        # )

        # For now, return empty list
        return []

    def semantic_search(self, query: str, top_k: int = 5) -> list[AIArtifact]:
        """
        Semantic search across all artifacts.

        Args:
            query: Natural language query
            top_k: Number of results

        Returns:
            Most relevant artifacts

        Example:
            >>> # Find relevant authentication context
            >>> artifacts = protocol.semantic_search(
            ...     "authentication architecture decisions",
            ...     top_k=3
            ... )
        """
        # TODO: Implement ConPort semantic search
        # results = conport.semantic_search_conport(
        #     workspace_id=self.workspace_id,
        #     query_text=query,
        #     top_k=top_k,
        #     filter_item_types=["custom_data"]
        # )

        return []

    def get_context_for_agent(
        self, agent_type: str, task_description: str, detail_level: int = 1
    ) -> dict:
        """
        Get relevant context for an AI agent before task execution.

        Implements progressive disclosure:
        - Level 1: Essential (recent decisions, current task)
        - Level 2: Moderate (related artifacts, dependencies)
        - Level 3: Complete (full history, all related items)

        Args:
            agent_type: Which agent needs context
            task_description: What they're about to do
            detail_level: 1-3 (progressive disclosure)

        Returns:
            Context dictionary ready for AI consumption

        Example:
            >>> context = protocol.get_context_for_agent(
            ...     agent_type="grok",
            ...     task_description="Implement JWT token generation",
            ...     detail_level=2
            ... )
            >>> # Pass context to Grok CLI
            >>> grok.send_command(f"Context: {context}\n\nTask: {task_description}")
        """
        context = {}

        # Level 1: Essential (always included)
        if detail_level >= 1:
            # Recent decisions
            recent_decisions = self.query_artifacts(
                artifact_type="decision", limit=3
            )
            context["recent_decisions"] = [
                {"content": a.content, "agent": a.agent_type} for a in recent_decisions
            ]

            # Current mode/focus from ConPort active_context
            # TODO: context["current_focus"] = conport.get_active_context()

        # Level 2: Moderate (on request)
        if detail_level >= 2:
            # Related artifacts via semantic search
            related = self.semantic_search(task_description, top_k=5)
            context["related_artifacts"] = [
                {
                    "type": a.artifact_type,
                    "content": a.content,
                    "confidence": a.confidence,
                }
                for a in related
            ]

        # Level 3: Complete (explicit request only)
        if detail_level >= 3:
            # Full session history
            all_artifacts = self.query_artifacts(limit=50)
            context["session_history"] = [
                {
                    "type": a.artifact_type,
                    "agent": a.agent_type,
                    "content": a.content,
                    "timestamp": a.timestamp.isoformat(),
                }
                for a in all_artifacts
            ]

        return context


if __name__ == "__main__":
    """Test context protocol."""

    protocol = ContextSharingProtocol(
        workspace_id="/Users/hue/code/ui-build", session_id="test-session"
    )

    # Test publishing
    print("Testing artifact publishing:")
    artifact_id = protocol.publish_artifact(
        artifact_type="decision",
        agent_type="claude",
        content="Use JWT tokens with refresh flow for authentication",
        confidence=0.85,
        metadata={
            "rationale": "Stateless scaling benefits",
            "alternatives_considered": ["sessions", "cookies"],
        },
    )
    print(f"✅ Published: {artifact_id}")

    # Test querying
    print("\nTesting artifact query:")
    artifacts = protocol.query_artifacts(artifact_type="decision")
    print(f"Found {len(artifacts)} decisions")

    # Test context assembly
    print("\nTesting context assembly:")
    context = protocol.get_context_for_agent(
        agent_type="grok",
        task_description="Implement JWT token generation",
        detail_level=2,
    )
    print(f"Context keys: {list(context.keys())}")
    print(json.dumps(context, indent=2, default=str))
