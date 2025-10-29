"""
DDDPG Query Service
ADHD-optimized query patterns for decision retrieval
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..storage import StorageBackend
from ..core.models import Decision, DecisionGraph


class QueryService:
    """
    ADHD-optimized query patterns
    
    Three-tier approach:
    1. Overview: Top-3 most recent/relevant (never overwhelming)
    2. Exploration: Progressive depth (1-3 levels)
    3. Deep: Full context dump (when needed)
    """
    
    def __init__(self, storage: StorageBackend):
        self.storage = storage
    
    # ===== TIER 1: Overview (Top-3 ADHD Pattern) =====
    
    async def overview(
        self,
        workspace_id: str,
        instance_id: str,
        limit: int = 3
    ) -> List[Decision]:
        """
        Top-3 most recent decisions
        ADHD-friendly: Never show more than 3 items by default
        
        Args:
            workspace_id: Workspace identifier
            instance_id: Instance identifier
            limit: Max results (default 3)
        
        Returns:
            List of most recent decisions
        """
        return await self.storage.list_decisions(
            workspace_id=workspace_id,
            instance_id=instance_id,
            include_shared=True,
            limit=limit,
            offset=0
        )
    
    async def overview_by_type(
        self,
        workspace_id: str,
        instance_id: str,
        decision_type: str,
        limit: int = 3
    ) -> List[Decision]:
        """
        Top-3 decisions of specific type
        
        Args:
            decision_type: architecture, implementation, etc
        """
        all_decisions = await self.storage.list_decisions(
            workspace_id=workspace_id,
            instance_id=instance_id,
            limit=100
        )
        
        # Filter by type
        typed = [d for d in all_decisions if d.decision_type and d.decision_type.value == decision_type]
        
        return typed[:limit]
    
    async def overview_by_tags(
        self,
        workspace_id: str,
        instance_id: str,
        tags: List[str],
        limit: int = 3
    ) -> List[Decision]:
        """
        Top-3 decisions matching any of the tags
        """
        all_decisions = await self.storage.list_decisions(
            workspace_id=workspace_id,
            instance_id=instance_id,
            limit=100
        )
        
        # Filter by tags (any match)
        tagged = [
            d for d in all_decisions
            if d.tags and any(tag in d.tags for tag in tags)
        ]
        
        return tagged[:limit]
    
    # ===== TIER 2: Exploration (Progressive Depth) =====
    
    async def explore_recent(
        self,
        workspace_id: str,
        instance_id: str,
        depth: int = 1,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Explore recent decisions with progressive depth
        
        Depth levels:
        - 1: Just decisions (10 items)
        - 2: + Related decisions (30 items)
        - 3: + Full context (100 items)
        
        Args:
            depth: 1-3 (progressive disclosure)
            limit: Multiplied by depth
        """
        if depth < 1 or depth > 3:
            depth = 1
        
        # Calculate limit based on depth
        actual_limit = limit * depth
        
        decisions = await self.storage.list_decisions(
            workspace_id=workspace_id,
            instance_id=instance_id,
            limit=actual_limit
        )
        
        result = {
            "depth": depth,
            "total": len(decisions),
            "decisions": decisions,
            "metadata": {
                "workspace_id": workspace_id,
                "instance_id": instance_id,
                "queried_at": datetime.utcnow().isoformat()
            }
        }
        
        # Depth 2+: Add related decisions
        if depth >= 2:
            related_ids = set()
            for d in decisions:
                related_ids.update(d.related_decisions)
            
            if related_ids:
                related = []
                for rid in related_ids:
                    r = await self.storage.get_decision(rid)
                    if r:
                        related.append(r)
                result["related"] = related
        
        # Depth 3: Add stats and patterns
        if depth >= 3:
            result["stats"] = await self._compute_stats(decisions)
        
        return result
    
    async def explore_by_timeframe(
        self,
        workspace_id: str,
        instance_id: str,
        hours: int = 24,
        limit: int = 100
    ) -> List[Decision]:
        """
        Explore decisions from last N hours
        Useful for "what did I decide today?"
        """
        all_decisions = await self.storage.list_decisions(
            workspace_id=workspace_id,
            instance_id=instance_id,
            limit=limit
        )
        
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        recent = [
            d for d in all_decisions
            if d.created_at and d.created_at >= cutoff
        ]
        
        return recent
    
    async def explore_by_cognitive_load(
        self,
        workspace_id: str,
        instance_id: str,
        max_load: int = 3,
        limit: int = 10
    ) -> List[Decision]:
        """
        Find low cognitive load decisions
        ADHD-friendly: Show easy wins when energy is low
        
        Args:
            max_load: Max cognitive load (1-5)
        """
        all_decisions = await self.storage.list_decisions(
            workspace_id=workspace_id,
            instance_id=instance_id,
            limit=100
        )
        
        easy = [
            d for d in all_decisions
            if d.cognitive_load and d.cognitive_load <= max_load
        ]
        
        return easy[:limit]
    
    # ===== TIER 3: Deep Context =====
    
    async def deep_context(
        self,
        workspace_id: str,
        instance_id: str,
        include_archived: bool = False
    ) -> Dict[str, Any]:
        """
        Full context dump
        Everything for this workspace/instance
        """
        # Get all decisions (large limit)
        decisions = await self.storage.list_decisions(
            workspace_id=workspace_id,
            instance_id=instance_id,
            limit=1000
        )
        
        # Compute comprehensive stats
        stats = await self._compute_stats(decisions)
        
        # Group by type
        by_type = {}
        for d in decisions:
            dt = d.decision_type.value if d.decision_type else "other"
            if dt not in by_type:
                by_type[dt] = []
            by_type[dt].append(d)
        
        # Group by tags
        tag_counts = {}
        for d in decisions:
            for tag in d.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Top tags
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_decisions": len(decisions),
            "workspace_id": workspace_id,
            "instance_id": instance_id,
            "stats": stats,
            "decisions": decisions,
            "by_type": {k: len(v) for k, v in by_type.items()},
            "top_tags": top_tags,
            "queried_at": datetime.utcnow().isoformat()
        }
    
    async def deep_search(
        self,
        workspace_id: str,
        instance_id: str,
        query: str,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Deep full-text search with context
        """
        results = await self.storage.search_decisions(
            query=query,
            workspace_id=workspace_id,
            instance_id=instance_id,
            limit=limit
        )
        
        return {
            "query": query,
            "total_results": len(results),
            "results": results,
            "searched_at": datetime.utcnow().isoformat()
        }
    
    # ===== Utility Methods =====
    
    async def _compute_stats(self, decisions: List[Decision]) -> Dict[str, Any]:
        """Compute statistics for a set of decisions"""
        if not decisions:
            return {
                "total": 0,
                "avg_cognitive_load": 0,
                "status_breakdown": {},
                "type_breakdown": {}
            }
        
        # Status breakdown
        status_counts = {}
        for d in decisions:
            status = d.status.value if hasattr(d.status, 'value') else str(d.status)
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Type breakdown
        type_counts = {}
        for d in decisions:
            dtype = d.decision_type.value if d.decision_type else "other"
            type_counts[dtype] = type_counts.get(dtype, 0) + 1
        
        # Cognitive load stats
        loads = [d.cognitive_load for d in decisions if d.cognitive_load]
        avg_load = sum(loads) / len(loads) if loads else 0
        
        # Recent activity
        if decisions:
            most_recent = max(decisions, key=lambda d: d.created_at or datetime.min)
            oldest = min(decisions, key=lambda d: d.created_at or datetime.max)
        else:
            most_recent = None
            oldest = None
        
        return {
            "total": len(decisions),
            "status_breakdown": status_counts,
            "type_breakdown": type_counts,
            "avg_cognitive_load": round(avg_load, 2),
            "most_recent": most_recent.created_at.isoformat() if most_recent and most_recent.created_at else None,
            "oldest": oldest.created_at.isoformat() if oldest and oldest.created_at else None,
        }
    
    # ===== ADHD-Specific Queries =====
    
    async def focus_suggestions(
        self,
        workspace_id: str,
        instance_id: str,
        current_focus_level: int = 3
    ) -> List[Decision]:
        """
        Suggest decisions based on current focus level
        
        High focus (4-5): Show complex tasks
        Medium focus (3): Show moderate tasks
        Low focus (1-2): Show easy wins
        """
        if current_focus_level >= 4:
            # High focus: show complex work
            return await self.explore_by_cognitive_load(
                workspace_id, instance_id, max_load=5, limit=5
            )
        elif current_focus_level >= 3:
            # Medium focus: show moderate work
            return await self.explore_by_cognitive_load(
                workspace_id, instance_id, max_load=3, limit=5
            )
        else:
            # Low focus: show easy wins
            return await self.explore_by_cognitive_load(
                workspace_id, instance_id, max_load=2, limit=5
            )
    
    async def break_detector(
        self,
        workspace_id: str,
        instance_id: str,
        session_duration_minutes: int = 90
    ) -> Dict[str, Any]:
        """
        Detect if a break is needed based on decision patterns
        
        Heuristics:
        - High cognitive load decisions in short time = break needed
        - Many decisions in short time = fatigue
        - Long time since last decision = already on break
        """
        recent = await self.explore_by_timeframe(
            workspace_id, instance_id, hours=2
        )
        
        if not recent:
            return {
                "break_needed": False,
                "reason": "No recent activity",
                "suggestion": "You might already be on a break!"
            }
        
        # Calculate average cognitive load
        loads = [d.cognitive_load for d in recent if d.cognitive_load]
        avg_load = sum(loads) / len(loads) if loads else 0
        
        # High intensity work?
        high_intensity = avg_load >= 4
        many_decisions = len(recent) >= 10
        
        if high_intensity or many_decisions:
            return {
                "break_needed": True,
                "reason": f"High intensity work detected (avg load: {avg_load:.1f})",
                "suggestion": "Take a 15 minute break! You've earned it! ☕",
                "decisions_analyzed": len(recent)
            }
        
        return {
            "break_needed": False,
            "reason": "Energy levels look good",
            "suggestion": "Keep crushing it! 🚀",
            "decisions_analyzed": len(recent)
        }


__all__ = ["QueryService"]
