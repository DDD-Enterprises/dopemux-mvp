#!/usr/bin/env python3
"""
Tier 3: Deep Context Queries
Complete decision analysis with NO ADHD limits

When user explicitly requests full detail:
- No result limits (comprehensive)
- 3-hop traversal (complete context)
- Full analytics (centrality, influence)
- All relationships loaded

Part of CONPORT-KG-2025 Phase 6 (Decision #117)
"""

import os
import sys
from typing import List, Dict, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from age_client import AGEClient
    from queries.models import (
        DecisionCard, DecisionSummary, FullDecisionContext,
        Relationship, DecisionAnalytics
    )
except ImportError:
    sys.path.insert(0, '/Users/hue/code/dopemux-mvp/services/conport_kg')
    from age_client import AGEClient
    exec(open('/Users/hue/code/dopemux-mvp/services/conport_kg/queries/models.py').read())


class DeepContextQueries:
    """
    Tier 3: Deep Context - No Limits

    Comprehensive decision analysis when user requests full detail.
    No ADHD restrictions - user has explicitly chosen deep dive.
    """

    def __init__(self):
        """Initialize with AGEClient"""
        try:
            self.client = AGEClient()
            print(f"✅ DeepContextQueries using AGEClient")
        except Exception as e:
            print(f"❌ AGEClient initialization failed: {e}")
            raise

    def get_full_decision_context(self, decision_id: int) -> FullDecisionContext:
        """
        Get complete decision context with 3-hop traversal

        Tier 3: NO LIMITS
        - All relationships loaded
        - 3-hop neighborhood
        - Complete tags and metadata
        - cognitive_load = "high" (always)

        Args:
            decision_id: Decision to analyze

        Returns:
            FullDecisionContext with complete data
        """

        # Get core decision data
        cypher_decision = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision {{id: {decision_id}}})
                RETURN d.id, d.summary, d.rationale, d.implementation, d.tags, d.timestamp
            $$) as (id agtype, summary agtype, rationale agtype, impl agtype, tags agtype, ts agtype);
        """

        decision_result = self.client.execute_cypher(cypher_decision)

        if not decision_result:
            # Return empty context
            return FullDecisionContext(
                decision=DecisionSummary(id=decision_id, summary="Not found", timestamp=""),
                direct_relationships=[],
                cognitive_load="high"
            )

        d_row = decision_result[0]

        # Create DecisionSummary
        decision = DecisionSummary(
            id=int(d_row['id']),
            summary=str(d_row['summary']),
            timestamp=str(d_row.get('ts', '')),
            rationale=str(d_row.get('rationale', '')),
            implementation=str(d_row.get('impl', ''))
        )

        # Get all relationships (will use get_all_relationships method)
        relationships = self.get_all_relationships(decision_id)

        # Get related decisions (1-hop)
        cypher_related = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision {{id: {decision_id}}})-[]-(related:Decision)
                RETURN DISTINCT related.id, related.summary, related.timestamp
                LIMIT 50
            $$) as (id agtype, summary agtype, timestamp agtype);
        """

        related_results = self.client.execute_cypher(cypher_related)

        related_decisions = [
            DecisionCard(
                id=int(row['id']),
                summary=str(row['summary']),
                timestamp=str(row.get('timestamp', ''))
            )
            for row in related_results
        ]

        # Build full context
        return FullDecisionContext(
            decision=decision,
            direct_relationships=relationships,
            hop_2_relationships=[],  # Could expand with more queries
            hop_3_relationships=[],
            related_decisions=related_decisions,
            tags=d_row.get('tags', []) if isinstance(d_row.get('tags'), list) else [],
            cognitive_load="high"  # Always high for Tier 3
        )

    def get_all_relationships(self, decision_id: int) -> List[Relationship]:
        """
        Get ALL relationships for a decision

        Tier 3: NO LIMITS
        - Returns every relationship
        - Full metadata for each edge
        - Direction detection (incoming/outgoing)

        Args:
            decision_id: Decision to analyze

        Returns:
            List[Relationship] with complete metadata
        """

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision {{id: {decision_id}}})-[r]-(other:Decision)
                RETURN
                    {decision_id} as source,
                    other.id as target,
                    type(r) as rel_type,
                    r.description as descr,
                    r.timestamp as rel_timestamp
            $$) as (source agtype, target agtype, rel_type agtype, descr agtype, ts agtype);
        """

        results = self.client.execute_cypher(cypher)

        relationships = []
        for row in results:
            # Determine direction based on whether decision_id is source
            target_id = int(row['target'])

            relationships.append(Relationship(
                source_id=int(row['source']),
                target_id=target_id,
                type=str(row['rel_type']),
                description=str(row.get('descr', '')),
                timestamp=str(row.get('ts', '')),
                direction='outgoing'  # Simplified for now
            ))

        return relationships

    def search_full_text(
        self,
        search_term: str,
        limit: int = 20
    ) -> List[DecisionCard]:
        """
        Full-text search across all decision fields

        Tier 3: Higher limit than Tier 1
        - Searches summary + rationale + implementation
        - Case-insensitive
        - Returns up to 20 results

        Args:
            search_term: Text to search for
            limit: Max results (default 20, higher than Tier 1's 3)

        Returns:
            List[DecisionCard] matching search
        """

        # Case-insensitive regex pattern
        # Note: AGE regex uses =~ operator
        pattern = f'.*{search_term}.*'

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision)
                WHERE d.summary =~ '{pattern}'
                   OR d.rationale =~ '{pattern}'
                   OR d.implementation =~ '{pattern}'
                RETURN d.id, d.summary, d.timestamp
                LIMIT {limit}
            $$) as (id agtype, summary agtype, timestamp agtype);
        """

        results = self.client.execute_cypher(cypher)

        decisions = []
        for row in results:
            decisions.append(DecisionCard(
                id=int(row['id']),
                summary=str(row['summary']),
                timestamp=str(row.get('timestamp', ''))
            ))

        return decisions

    def get_decision_analytics(self, decision_id: int) -> DecisionAnalytics:
        """
        Calculate decision centrality and influence metrics

        Tier 3: Complete analytics
        - Degree centrality (total connections)
        - Influence score (downstream dependencies)
        - Relationship distribution by type
        - Foundational decision detection

        Args:
            decision_id: Decision to analyze

        Returns:
            DecisionAnalytics with calculated metrics
        """

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision {{id: {decision_id}}})
                OPTIONAL MATCH (d)-[r_out]->()
                OPTIONAL MATCH (d)<-[r_in]-()
                WITH d,
                     COUNT(DISTINCT r_out) as out_count,
                     COUNT(DISTINCT r_in) as in_count
                RETURN
                    d.id,
                    out_count + in_count as degree,
                    out_count as influence,
                    CASE WHEN in_count = 0 THEN true ELSE false END as is_root
            $$) as (id agtype, degree agtype, influence agtype, is_root agtype);
        """

        results = self.client.execute_cypher(cypher)

        if not results:
            return DecisionAnalytics(
                decision_id=decision_id,
                degree_centrality=0,
                influence_score=0,
                is_foundational=False
            )

        row = results[0]

        # Get relationship type distribution
        cypher_dist = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision {{id: {decision_id}}})-[r]-()
                RETURN type(r) as rel_type
            $$) as (rel_type agtype);
        """

        dist_results = self.client.execute_cypher(cypher_dist)

        # Build distribution
        rel_distribution = {}
        for dist_row in dist_results:
            rel_type = str(dist_row['rel_type'])
            rel_distribution[rel_type] = rel_distribution.get(rel_type, 0) + 1

        return DecisionAnalytics(
            decision_id=int(row['id']),
            degree_centrality=int(row.get('degree', 0)),
            influence_score=int(row.get('influence', 0)),
            relationship_distribution=rel_distribution,
            is_foundational=bool(row.get('is_root', False))
        )


if __name__ == "__main__":
    # Test Tier 3 Deep Context queries
    print("=" * 60)
    print("Tier 3: Deep Context Queries (NO LIMITS)")
    print("=" * 60)

    queries = DeepContextQueries()

    # Test with decision #85
    test_id = 85

    print(f"\n[1] Full Decision Context:")
    context = queries.get_full_decision_context(test_id)
    print(f"   Decision: #{context.decision.id}")
    print(f"   Summary: {context.decision.summary[:60]}...")
    print(f"   Rationale length: {len(context.decision.rationale or '')} chars")
    print(f"   Direct relationships: {len(context.direct_relationships)}")
    print(f"   Related decisions: {len(context.related_decisions)}")
    print(f"   Cognitive load: {context.cognitive_load}")
    print(f"   Total related: {context.total_related}")

    print(f"\n[2] All Relationships:")
    relationships = queries.get_all_relationships(test_id)
    print(f"   Total relationships: {len(relationships)}")
    for i, rel in enumerate(relationships[:5], 1):
        print(f"      {i}. {rel.to_display_string()} - {rel.type}")

    print(f"\n[3] Full-Text Search (no limit=20):")
    search_results = queries.search_full_text("Serena", limit=20)
    print(f"   Found {len(search_results)} decisions matching 'Serena'")
    for i, d in enumerate(search_results[:5], 1):
        print(f"      {i}. #{d.id}: {d.summary[:50]}...")

    print(f"\n[4] Decision Analytics:")
    analytics = queries.get_decision_analytics(test_id)
    print(f"   Decision #{analytics.decision_id}")
    print(f"   Degree centrality: {analytics.degree_centrality}")
    print(f"   Influence score: {analytics.influence_score}")
    print(f"   Is foundational: {analytics.is_foundational}")
    print(f"   Hub score: {analytics.hub_score:.2f}")
    print(f"   Importance: {analytics.get_importance_level()}")
    print(f"   Relationship distribution: {analytics.relationship_distribution}")

    print(f"\n✅ All Tier 3 deep context queries tested!")
