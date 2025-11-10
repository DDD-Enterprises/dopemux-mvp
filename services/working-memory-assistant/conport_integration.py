"""
ConPort Knowledge Graph Integration for Working Memory Assistant

This module handles integration with ConPort MCP to provide semantic context
enrichment for WMA snapshots by linking to relevant decisions, progress entries,
and system patterns.
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from conport_client import ConPortClient

@dataclass
class ConPortContext:
    """Context data from ConPort for WMA snapshots"""
    recent_decisions: List[Dict[str, Any]]
    active_progress: List[Dict[str, Any]]
    relevant_patterns: List[Dict[str, Any]]
    linked_items: List[Dict[str, Any]]
    semantic_context: str  # Summary of relevant ConPort context

class ConPortIntegration:
    """Integration layer between WMA and ConPort knowledge graph"""

    def __init__(self, workspace_id: str):
        self.workspace_id = workspace_id
        self.conport_client = ConPortClient(workspace_id=workspace_id)

    async def get_recent_context(self, limit: int = 5) -> ConPortContext:
        """Get recent ConPort context relevant to current work"""
        try:
            # Get recent decisions
            recent_decisions = await self.conport_client.get_decisions(limit=limit)

            # Get active progress entries
            active_progress = await self.conport_client.get_progress(
                status_filter="IN_PROGRESS", limit=limit
            )

            # Get relevant system patterns
            relevant_patterns = await self.conport_client.get_system_patterns(
                limit=limit, tags_filter_include_any=["development", "adhd"]
            )

            # Get linked items for the current session (if session_id available)
            linked_items = await self.conport_client.get_linked_items(
                item_type="active_context", item_id="current_session"
            )

            # Generate semantic context summary
            semantic_context = await self._generate_semantic_summary(
                recent_decisions, active_progress, relevant_patterns
            )

            return ConPortContext(
                recent_decisions=recent_decisions,
                active_progress=active_progress,
                relevant_patterns=relevant_patterns,
                linked_items=linked_items,
                semantic_context=semantic_context
            )

        except Exception as e:
            # Fallback to empty context if ConPort unavailable
            print(f"ConPort unavailable, using fallback: {e}")
            return ConPortContext(
                recent_decisions=[],
                active_progress=[],
                relevant_patterns=[],
                linked_items=[],
                semantic_context="ConPort unavailable - working with limited context"
            )

    async def _generate_semantic_summary(
        self, decisions: List[Dict[str, Any]],
        progress: List[Dict[str, Any]],
        patterns: List[Dict[str, Any]]
    ) -> str:
        """Generate semantic summary of ConPort context"""
        # Simple summary generation - would use LLM in production
        summary_parts = []

        if decisions:
            summary_parts.append(f"Recent decisions: {len(decisions)} items")

        if progress:
            active_tasks = [p['description'] for p in progress if p['status'] == 'IN_PROGRESS']
            if active_tasks:
                summary_parts.append(f"Active tasks: {', '.join(active_tasks[:3])}")

        if patterns:
            summary_parts.append(f"Relevant patterns: {len(patterns)}")

        return " | ".join(summary_parts) if summary_parts else "No recent ConPort context"

    async def enrich_snapshot_with_conport(self, snapshot_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich snapshot with ConPort data"""
        context = await self.get_recent_context()

        # Add ConPort context to snapshot metadata
        snapshot_data['conport_context'] = {
            'recent_decisions': context.recent_decisions,
            'active_progress': context.active_progress,
            'relevant_patterns': context.relevant_patterns,
            'semantic_summary': context.semantic_context
        }

        # Create ConPort links for the snapshot
        for decision in context.recent_decisions:
            await self.conport_client.link_conport_items(
                source_item_type='wma_snapshot',
                source_item_id=snapshot_data['id'],
                target_item_type='decision',
                target_item_id=str(decision['id']),
                relationship_type='context_for',
                description=f"Working memory snapshot during decision {decision['id']}"
            )

        for progress in context.active_progress:
            await self.conport_client.link_conport_items(
                source_item_type='wma_snapshot',
                source_item_id=snapshot_data['id'],
                target_item_type='progress_entry',
                target_item_id=str(progress['id']),
                relationship_type='implements',
                description=f"Working memory snapshot for progress entry {progress['id']}"
            )

        return snapshot_data

async def test_conport_integration():
    """Test ConPort integration"""
    workspace_id = "current_workspace"  # Would be dynamic from git rev-parse
    integration = ConPortIntegration(workspace_id)

    context = await integration.get_recent_context()
    print("ConPort Context:")
    print(f"Recent decisions: {len(context.recent_decisions)}")
    print(f"Active progress: {len(context.active_progress)}")
    print(f"Relevant patterns: {len(context.relevant_patterns)}")
    print(f"Semantic summary: {context.semantic_context}")

if __name__ == "__main__":
    asyncio.run(test_conport_integration())
