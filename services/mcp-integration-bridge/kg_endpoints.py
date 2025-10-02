#!/usr/bin/env python3
"""
Knowledge Graph REST Endpoints
Part of CONPORT-KG-2025 Phase 10

Provides HTTP API for cross-plane KG access:
- PM Plane: Read-only access to decision context
- Cognitive Plane: Full access
- Authority enforcement via middleware

Integration Bridge at PORT_BASE+16
"""

from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional, List
import sys
import os

# Add conport_kg to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'conport_kg'))

try:
    from queries.overview import OverviewQueries
    from queries.exploration import ExplorationQueries
    from queries.deep_context import DeepContextQueries
    from queries.models import DecisionCard, DecisionSummary, DecisionNeighborhood, FullDecisionContext
except ImportError as e:
    print(f"⚠️  ConPort KG queries not available: {e}")
    OverviewQueries = None


# Create router
router = APIRouter(
    prefix="/kg",
    tags=["knowledge-graph"],
    responses={404: {"description": "Not found"}}
)


# Initialize query classes (singleton pattern)
_overview_queries = None
_exploration_queries = None
_deep_context_queries = None


def get_query_classes():
    """Lazy initialization of query classes"""
    global _overview_queries, _exploration_queries, _deep_context_queries

    if _overview_queries is None and OverviewQueries:
        _overview_queries = OverviewQueries()
        _exploration_queries = ExplorationQueries()
        _deep_context_queries = DeepContextQueries()

    return _overview_queries, _exploration_queries, _deep_context_queries


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        overview, _, _ = get_query_classes()
        if overview:
            # Quick test query
            overview.get_recent_decisions(1)
            return {"status": "healthy", "message": "KG queries operational"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

    return {"status": "unavailable", "message": "KG queries not initialized"}


@router.get("/decisions/recent")
async def get_recent_decisions(
    limit: int = Query(3, ge=1, le=20),
    x_source_plane: Optional[str] = Header(None)
):
    """
    Get recent decisions (Tier 1)

    ADHD: Top-3 pattern (default limit=3)
    Performance: ~2.5ms p95

    Authority: PM plane (read-only) OR Cognitive plane (full)
    """

    # Validate authority
    if x_source_plane and x_source_plane not in ["pm_plane", "cognitive_plane"]:
        raise HTTPException(status_code=403, detail=f"Invalid source plane: {x_source_plane}")

    overview, _, _ = get_query_classes()
    if not overview:
        raise HTTPException(status_code=503, detail="KG queries not available")

    try:
        decisions = overview.get_recent_decisions(limit)

        # Convert DecisionCard to dict for JSON serialization
        return {
            "decisions": [
                {
                    "id": d.id,
                    "summary": d.summary,
                    "timestamp": d.timestamp,
                    "related_count": d.related_count,
                    "tags": d.tags
                }
                for d in decisions
            ],
            "count": len(decisions),
            "tier": 1
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/decisions/{decision_id}/summary")
async def get_decision_summary(
    decision_id: int,
    x_source_plane: Optional[str] = Header(None)
):
    """
    Get decision summary with relationship count (Tier 1)

    Includes: cognitive_load indicator
    Performance: ~2.5ms p95

    Authority: PM plane (read-only) OR Cognitive plane (full)
    """

    if x_source_plane and x_source_plane not in ["pm_plane", "cognitive_plane"]:
        raise HTTPException(status_code=403, detail=f"Invalid source plane: {x_source_plane}")

    overview, _, _ = get_query_classes()
    if not overview:
        raise HTTPException(status_code=503, detail="KG queries not available")

    try:
        summary = overview.get_decision_summary(decision_id)

        return {
            "id": summary.id,
            "summary": summary.summary,
            "rationale": summary.rationale,
            "implementation": summary.implementation,
            "timestamp": summary.timestamp,
            "related_count": summary.related_count,
            "relationship_types": summary.relationship_types,
            "cognitive_load": summary.get_cognitive_load(),
            "tags": summary.tags,
            "tier": 1
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/decisions/{decision_id}/neighborhood")
async def get_decision_neighborhood(
    decision_id: int,
    max_hops: int = Query(1, ge=1, le=2),
    limit_per_hop: int = Query(10, ge=1, le=20),
    x_source_plane: Optional[str] = Header(None)
):
    """
    Get decision neighborhood with progressive disclosure (Tier 2)

    ADHD: Progressive 1-hop → 2-hop expansion
    Performance: ~3.4ms p95

    Authority: PM plane (read-only) OR Cognitive plane (full)
    """

    if x_source_plane and x_source_plane not in ["pm_plane", "cognitive_plane"]:
        raise HTTPException(status_code=403, detail=f"Invalid source plane: {x_source_plane}")

    _, exploration, _ = get_query_classes()
    if not exploration:
        raise HTTPException(status_code=503, detail="KG queries not available")

    try:
        neighborhood = exploration.get_decision_neighborhood(
            decision_id, max_hops, limit_per_hop
        )

        return {
            "center": {
                "id": neighborhood.center.id,
                "summary": neighborhood.center.summary,
                "timestamp": neighborhood.center.timestamp
            },
            "hop_1_neighbors": [
                {"id": d.id, "summary": d.summary, "timestamp": d.timestamp}
                for d in neighborhood.hop_1_neighbors
            ],
            "hop_2_neighbors": [
                {"id": d.id, "summary": d.summary, "timestamp": d.timestamp}
                for d in neighborhood.hop_2_neighbors
            ],
            "total_neighbors": neighborhood.total_neighbors,
            "is_expanded": neighborhood.is_expanded,
            "tier": 2
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/decisions/{decision_id}/context")
async def get_full_context(
    decision_id: int,
    x_source_plane: Optional[str] = Header(None)
):
    """
    Get complete decision context (Tier 3)

    Includes: 3-hop traversal, all relationships, analytics
    Performance: ~4.8ms p95
    No ADHD limits (user explicitly requested detail)

    Authority: PM plane (read-only) OR Cognitive plane (full)
    """

    if x_source_plane and x_source_plane not in ["pm_plane", "cognitive_plane"]:
        raise HTTPException(status_code=403, detail=f"Invalid source plane: {x_source_plane}")

    _, _, deep_context = get_query_classes()
    if not deep_context:
        raise HTTPException(status_code=503, detail="KG queries not available")

    try:
        context = deep_context.get_full_decision_context(decision_id)

        return {
            "decision": {
                "id": context.decision.id,
                "summary": context.decision.summary,
                "rationale": context.decision.rationale,
                "implementation": context.decision.implementation,
                "timestamp": context.decision.timestamp,
                "tags": context.decision.tags
            },
            "direct_relationships": [
                {
                    "source_id": r.source_id,
                    "target_id": r.target_id,
                    "type": r.type,
                    "description": r.description,
                    "timestamp": r.timestamp,
                    "direction": r.direction
                }
                for r in context.direct_relationships
            ],
            "related_decisions": [
                {"id": d.id, "summary": d.summary, "timestamp": d.timestamp}
                for d in context.related_decisions
            ],
            "total_related": context.total_related,
            "cognitive_load": context.cognitive_load,
            "tier": 3
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.get("/decisions/search")
async def search_decisions(
    tag: Optional[str] = None,
    text: Optional[str] = None,
    limit: int = Query(3, ge=1, le=20),
    x_source_plane: Optional[str] = Header(None)
):
    """
    Search decisions by tag or full-text

    Tag search: Tier 1 (Top-3 pattern)
    Text search: Tier 3 (higher limits)

    Authority: PM plane (read-only) OR Cognitive plane (full)
    """

    if x_source_plane and x_source_plane not in ["pm_plane", "cognitive_plane"]:
        raise HTTPException(status_code=403, detail=f"Invalid source plane: {x_source_plane}")

    overview, _, deep_context = get_query_classes()
    if not overview or not deep_context:
        raise HTTPException(status_code=503, detail="KG queries not available")

    try:
        if tag:
            # Tier 1: Tag search
            decisions = overview.search_by_tag(tag, limit)
            tier = 1
        elif text:
            # Tier 3: Full-text search
            decisions = deep_context.search_full_text(text, limit)
            tier = 3
        else:
            raise HTTPException(status_code=400, detail="Must provide 'tag' or 'text' parameter")

        return {
            "decisions": [
                {"id": d.id, "summary": d.summary, "timestamp": d.timestamp}
                for d in decisions
            ],
            "count": len(decisions),
            "query_type": "tag" if tag else "text",
            "tier": tier
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")
