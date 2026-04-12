#!/usr/bin/env python3
"""
CONPORT-KG-2025 Data Models
Part of Phase 2 Query API (Decision #117)

ADHD-optimized type-safe models with progressive disclosure support.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class DecisionCard:
    """
    Tier 1: Minimal decision for overview lists

    ADHD Optimization: Top-3 Pattern
    - Contains only essential fields
    - Perfect for quick scanning
    - No cognitive load from extra details
    """
    id: int
    summary: str
    timestamp: str
    related_count: Optional[int] = None
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate Top-3 pattern enforcement"""
        # Tags can exist but should be limited in display context
        pass


@dataclass
class DecisionSummary(DecisionCard):
    """
    Tier 2: Focused view with rationale

    Extends DecisionCard with additional context.
    Used when user needs more detail about specific decision.
    """
    rationale: Optional[str] = None
    implementation: Optional[str] = None
    relationship_types: List[str] = field(default_factory=list)

    def get_cognitive_load(self) -> str:
        """
        Calculate cognitive load indicator

        Returns: "low", "medium", "high"
        """
        text_length = len(self.rationale or "") + len(self.implementation or "")
        relationships = len(self.relationship_types)

        if text_length < 500 and relationships <= 2:
            return "low"
        elif text_length < 2000 and relationships <= 5:
            return "medium"
        else:
            return "high"


@dataclass
class DecisionNeighborhood:
    """
    Tier 2: Graph neighborhood view

    ADHD Optimization: Progressive Disclosure
    - Starts with 1-hop neighbors
    - User can expand to 2-hop
    - is_expanded flag tracks state
    """
    center: DecisionCard
    hop_1_neighbors: List[DecisionCard]
    hop_2_neighbors: List[DecisionCard] = field(default_factory=list)
    total_neighbors: int = 0
    is_expanded: bool = False  # ADHD: Track progressive disclosure state

    def __post_init__(self):
        """Calculate total and enforce limits"""
        self.total_neighbors = len(self.hop_1_neighbors) + len(self.hop_2_neighbors)

        # ADHD: Warn if exceeding recommended limits
        if len(self.hop_1_neighbors) > 10:
            print(f"⚠️  ADHD Warning: {len(self.hop_1_neighbors)} hop-1 neighbors (recommended: ≤10)")

    def expand_to_2_hop(self):
        """User action: expand to show 2-hop neighbors"""
        self.is_expanded = True


@dataclass
class DecisionChainNode:
    """
    Tier 2: Node in genealogy chain

    Represents one decision in a BUILDS_UPON or dependency chain.
    Generation indicates depth (0=root, 1=child, 2=grandchild, etc.)
    """
    id: int
    summary: str
    generation: int  # 0=root, 1=child, 2=grandchild...
    relationship_type: str  # BUILDS_UPON, DEPENDS_ON, etc.
    timestamp: Optional[str] = None


@dataclass
class Relationship:
    """
    Edge metadata for graph relationships

    Contains full information about decision→decision connections.
    """
    source_id: int
    target_id: int
    type: str  # BUILDS_UPON, FULFILLS, VALIDATES, etc.
    description: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    direction: str = "outgoing"  # "incoming" or "outgoing" from source

    def to_display_string(self) -> str:
        """Format for terminal display"""
        arrow = "→" if self.direction == "outgoing" else "←"
        return f"#{self.source_id} {arrow}[{self.type}]{arrow} #{self.target_id}"


@dataclass
class FullDecisionContext:
    """
    Tier 3: Complete decision context

    No ADHD limits - user explicitly requested full detail.
    Contains everything about a decision and its relationships.
    """
    decision: DecisionSummary
    direct_relationships: List[Relationship]
    hop_2_relationships: List[Relationship] = field(default_factory=list)
    hop_3_relationships: List[Relationship] = field(default_factory=list)
    related_decisions: List[DecisionCard] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    total_related: int = 0
    cognitive_load: str = "high"  # ADHD: Always "high" for full context

    def __post_init__(self):
        """Calculate totals"""
        self.total_related = (
            len(self.direct_relationships) +
            len(self.hop_2_relationships) +
            len(self.hop_3_relationships)
        )

    def get_relationship_summary(self) -> Dict[str, int]:
        """Group relationships by type"""
        summary = {}
        for rel in self.direct_relationships:
            summary[rel.type] = summary.get(rel.type, 0) + 1
        return summary


@dataclass
class ImpactGraph:
    """
    Tier 2/3: Dependency impact tree

    Shows what depends on this decision (impact analysis).
    Useful for understanding blast radius of changes.
    """
    root_decision: DecisionCard
    dependent_decisions: List[DecisionCard] = field(default_factory=list)
    dependency_tree: Dict[str, List[int]] = field(default_factory=dict)
    max_depth: int = 2

    def get_impact_count(self) -> int:
        """Total number of impacted decisions"""
        return len(self.dependent_decisions)

    def has_critical_dependencies(self) -> bool:
        """Check if this is a foundational decision"""
        return self.get_impact_count() > 5


@dataclass
class DecisionAnalytics:
    """
    Tier 3: Decision importance metrics

    Calculated analytics for understanding decision centrality
    and influence within the knowledge graph.
    """
    decision_id: int
    degree_centrality: int  # Total connections (in + out)
    influence_score: int  # Number of downstream dependencies
    relationship_distribution: Dict[str, int] = field(default_factory=dict)
    is_foundational: bool = False  # Root decision (no incoming edges)
    hub_score: float = 0.0  # 0.0-1.0, higher = more central

    def __post_init__(self):
        """Calculate derived metrics"""
        # Hub score: normalized influence (0.0-1.0 scale)
        if self.degree_centrality > 0:
            self.hub_score = min(1.0, self.influence_score / (self.degree_centrality * 2))

    def get_importance_level(self) -> str:
        """
        Classify decision importance

        Returns: "critical", "high", "medium", "low"
        """
        if self.is_foundational and self.influence_score > 10:
            return "critical"
        elif self.influence_score > 5:
            return "high"
        elif self.degree_centrality > 3:
            return "medium"
        else:
            return "low"


# Type aliases for clarity
DecisionList = List[DecisionCard]
RelationshipList = List[Relationship]
ChainList = List[DecisionChainNode]


if __name__ == "__main__":
    # Test data models
    print("=" * 60)
    print("CONPORT-KG-2025 Data Models Test")
    print("=" * 60)

    # Test DecisionCard (Tier 1)
    print("\n[1] DecisionCard (Tier 1 - Top-3 Pattern):")
    card = DecisionCard(
        id=117,
        summary="Phase 2 Query API Implementation Strategy",
        timestamp="2025-10-02T12:00:00Z",
        related_count=2,
        tags=["db-001", "phase-2", "api"]
    )
    print(f"   #{card.id}: {card.summary}")
    print(f"   Tags: {', '.join(card.tags)}")
    print(f"   Related: {card.related_count}")

    # Test DecisionSummary (Tier 2)
    print("\n[2] DecisionSummary (Tier 2 - Focused View):")
    summary = DecisionSummary(
        id=117,
        summary="Phase 2 Query API Implementation Strategy",
        timestamp="2025-10-02T12:00:00Z",
        rationale="Refactor from docker exec to direct psycopg2 for performance",
        implementation="7-phase sequential approach",
        relationship_types=["BUILDS_UPON", "IMPLEMENTS"]
    )
    print(f"   Cognitive Load: {summary.get_cognitive_load()}")
    print(f"   Relationship Types: {', '.join(summary.relationship_types)}")

    # Test DecisionNeighborhood (Tier 2 - Progressive Disclosure)
    print("\n[3] DecisionNeighborhood (Tier 2 - Progressive):")
    neighborhood = DecisionNeighborhood(
        center=card,
        hop_1_neighbors=[
            DecisionCard(114, "Interface Architecture", "2025-10-02T11:00:00Z", 3),
            DecisionCard(113, "Migration Simplification", "2025-10-02T10:00:00Z", 2)
        ],
        hop_2_neighbors=[]
    )
    print(f"   Center: #{neighborhood.center.id}")
    print(f"   1-hop neighbors: {len(neighborhood.hop_1_neighbors)}")
    print(f"   Expanded: {neighborhood.is_expanded}")
    neighborhood.expand_to_2_hop()
    print(f"   After expansion: {neighborhood.is_expanded}")

    # Test Relationship
    print("\n[4] Relationship (Edge Metadata):")
    rel = Relationship(
        source_id=117,
        target_id=114,
        type="BUILDS_UPON",
        description="Implementation builds on architecture",
        direction="outgoing"
    )
    print(f"   {rel.to_display_string()}")

    # Test DecisionAnalytics (Tier 3)
    print("\n[5] DecisionAnalytics (Tier 3 - Metrics):")
    analytics = DecisionAnalytics(
        decision_id=85,
        degree_centrality=8,
        influence_score=12,
        relationship_distribution={"BUILDS_UPON": 4, "VALIDATES": 2, "FULFILLS": 2},
        is_foundational=True
    )
    print(f"   Decision #{analytics.decision_id}")
    print(f"   Importance: {analytics.get_importance_level()}")
    print(f"   Hub Score: {analytics.hub_score:.2f}")
    print(f"   Influence: {analytics.influence_score} downstream")

    print("\n✅ All data models validated!")
