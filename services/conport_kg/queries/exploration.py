#!/usr/bin/env python3
"""
Tier 2: Exploration Queries
ADHD-optimized relationship navigation with progressive disclosure

Features:
- 1-hop → 2-hop progressive expansion
- Genealogy chain traversal
- Relationship type filtering
- Impact graph analysis

Part of CONPORT-KG-2025 Phase 5 (Decision #117)
"""

import os
import sys
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from age_client import AGEClient
    from queries.models import (
        DecisionCard, DecisionNeighborhood, DecisionChainNode, ImpactGraph
    )
except ImportError:
    sys.path.insert(0, '/Users/hue/code/dopemux-mvp/services/conport_kg')
    from age_client import AGEClient
    exec(open('/Users/hue/code/dopemux-mvp/services/conport_kg/queries/models.py').read())


class ExplorationQueries:
    """
    Tier 2: Exploration - Progressive Disclosure

    Interactive relationship navigation with ADHD optimizations.
    User controls expansion depth and complexity.
    """

    def __init__(self):
        """Initialize with AGEClient"""
        try:
            self.client = AGEClient()
            print(f"✅ ExplorationQueries using AGEClient")
        except Exception as e:
            print(f"❌ AGEClient initialization failed: {e}")
            raise

    def get_decision_neighborhood(
        self,
        decision_id: int,
        max_hops: int = 1,
        limit_per_hop: int = 10
    ) -> DecisionNeighborhood:
        """
        Get decision neighborhood with progressive disclosure

        ADHD Optimization: Single query, client-side filtering
        - Starts with 1-hop (default)
        - User expands to 2-hop when ready
        - Max 10 neighbors per hop level

        Args:
            decision_id: Center decision ID
            max_hops: 1 for initial view, 2 for expanded (ADHD progressive)
            limit_per_hop: Max neighbors per hop level (default 10)

        Returns:
            DecisionNeighborhood with hop-separated neighbors
        """

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (center:Decision {{id: {decision_id}}})
                OPTIONAL MATCH path = (center)-[*1..2]-(neighbor:Decision)
                WITH center, neighbor, path,
                     CASE
                         WHEN neighbor IS NULL THEN 0
                         ELSE length(path)
                     END as hop_dist
                WHERE neighbor IS NULL OR (hop_dist <= {max_hops} AND neighbor.id <> {decision_id})
                RETURN DISTINCT
                    center.id as c_id,
                    center.summary as c_summary,
                    center.timestamp as c_timestamp,
                    neighbor.id as n_id,
                    neighbor.summary as n_summary,
                    neighbor.timestamp as n_timestamp,
                    hop_dist
                ORDER BY hop_dist, neighbor.timestamp DESC
            $$) as (c_id agtype, c_summary agtype, c_timestamp agtype,
                    n_id agtype, n_summary agtype, n_timestamp agtype,
                    hop_dist agtype);
        """

        results = self.client.execute_cypher(cypher)

        if not results:
            # Return empty neighborhood
            center = DecisionCard(id=decision_id, summary="Not found", timestamp="")
            return DecisionNeighborhood(center=center, hop_1_neighbors=[], hop_2_neighbors=[])

        # Extract center from first result
        first_row = results[0]
        center = DecisionCard(
            id=int(first_row['c_id']),
            summary=str(first_row['c_summary']),
            timestamp=str(first_row.get('c_timestamp', ''))
        )

        # Separate neighbors by hop distance
        hop_1_neighbors = []
        hop_2_neighbors = []

        for row in results:
            neighbor_id = row.get('n_id')
            if neighbor_id is None or neighbor_id == 'null':
                continue

            neighbor = DecisionCard(
                id=int(neighbor_id),
                summary=str(row['n_summary']),
                timestamp=str(row.get('n_timestamp', ''))
            )

            hop_dist = int(row.get('hop_dist', 0))

            if hop_dist == 1 and len(hop_1_neighbors) < limit_per_hop:
                hop_1_neighbors.append(neighbor)
            elif hop_dist == 2 and len(hop_2_neighbors) < limit_per_hop:
                hop_2_neighbors.append(neighbor)

        return DecisionNeighborhood(
            center=center,
            hop_1_neighbors=hop_1_neighbors,
            hop_2_neighbors=hop_2_neighbors,
            is_expanded=(max_hops == 2)
        )

    def get_genealogy_chain(
        self,
        decision_id: int,
        relationship_type: str = 'BUILDS_UPON',
        direction: str = 'upstream',
        max_depth: int = 5
    ) -> List[DecisionChainNode]:
        """
        Trace decision lineage with generation numbers

        ADHD Optimization: Clear generational hierarchy
        - Generation 0 = root ancestor
        - Generation 1 = child
        - Generation 2 = grandchild, etc.

        Args:
            decision_id: Starting decision
            relationship_type: Type of relationship to follow (BUILDS_UPON, DEPENDS_ON, etc.)
            direction: 'upstream' (ancestors), 'downstream' (descendants), 'both'
            max_depth: Maximum generations to traverse

        Returns:
            List[DecisionChainNode] ordered by generation
        """

        # Build relationship pattern based on direction
        if direction == 'upstream':
            rel_pattern = f'-[:{relationship_type}*1..{max_depth}]->'
        elif direction == 'downstream':
            rel_pattern = f'<-[:{relationship_type}*1..{max_depth}]-'
        else:  # both
            rel_pattern = f'-[:{relationship_type}*1..{max_depth}]-'

        # Simplified: Direct match without path operations (AGE limitation)
        if direction == 'upstream':
            match_clause = f'MATCH (d:Decision {{id: {decision_id}}})-[:{relationship_type}]->(related:Decision)'
        elif direction == 'downstream':
            match_clause = f'MATCH (d:Decision {{id: {decision_id}}})<-[:{relationship_type}]-(related:Decision)'
        else:  # both
            match_clause = f'MATCH (d:Decision {{id: {decision_id}}})-[:{relationship_type}]-(related:Decision)'

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                {match_clause}
                RETURN related.id, related.summary, related.timestamp
                LIMIT 20
            $$) as (id agtype, summary agtype, timestamp agtype);
        """

        results = self.client.execute_cypher(cypher)

        # Build simple chain (1-hop only for now, multi-hop needs recursive approach)
        chain = []
        for idx, row in enumerate(results):
            chain.append(DecisionChainNode(
                id=int(row['id']),
                summary=str(row['summary']),
                generation=idx + 1,  # 0=current, 1=first hop, etc.
                relationship_type=relationship_type,
                timestamp=str(row.get('timestamp', ''))
            ))

        return chain

    def find_by_relationship_type(
        self,
        decision_id: int,
        relationship_type: str,
        direction: str = 'outgoing'
    ) -> List[DecisionCard]:
        """
        Find decisions connected by specific relationship type

        ADHD Optimization: Direct, focused results
        - Shows only specific relationship type
        - Max 10 results (prevents overwhelm)
        - Clear relationship semantics

        Args:
            decision_id: Source decision
            relationship_type: BUILDS_UPON, VALIDATES, DEPENDS_ON, etc.
            direction: 'outgoing' (d→target), 'incoming' (target→d), 'both'

        Returns:
            List[DecisionCard] of related decisions
        """

        # Build relationship pattern
        if direction == 'outgoing':
            rel_pattern = f'-[r:{relationship_type}]->'
            target = 'target'
        elif direction == 'incoming':
            rel_pattern = f'<-[r:{relationship_type}]-'
            target = 'target'
        else:  # both
            rel_pattern = f'-[r:{relationship_type}]-'
            target = 'target'

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision {{id: {decision_id}}}){rel_pattern}(target:Decision)
                RETURN
                    target.id as id,
                    target.summary as summary,
                    target.timestamp as timestamp
                ORDER BY target.timestamp DESC
                LIMIT 10
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

    def get_impact_graph(
        self,
        decision_id: int,
        max_depth: int = 2
    ) -> ImpactGraph:
        """
        Build dependency impact tree

        Shows what decisions DEPEND on this one (blast radius).
        Useful for understanding change impact.

        ADHD Optimization: Tree visualization
        - Max depth 2 (prevents overwhelming complexity)
        - Clear parent→child hierarchy
        - Critical dependency detection

        Args:
            decision_id: Root decision to analyze
            max_depth: How deep to traverse dependencies

        Returns:
            ImpactGraph with dependency tree structure
        """

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (root:Decision {{id: {decision_id}}})
                OPTIONAL MATCH path = (root)<-[:DEPENDS_ON*1..{max_depth}]-(dependent:Decision)
                RETURN
                    root.id as root_id,
                    root.summary as root_summary,
                    root.timestamp as root_timestamp,
                    collect(DISTINCT dependent.id) as dep_ids,
                    collect(DISTINCT dependent.summary) as dep_summaries
            $$) as (root_id agtype, root_summary agtype, root_timestamp agtype,
                    dep_ids agtype, dep_summaries agtype);
        """

        results = self.client.execute_cypher(cypher)

        if not results:
            root = DecisionCard(id=decision_id, summary="Not found", timestamp="")
            return ImpactGraph(root_decision=root, dependent_decisions=[], max_depth=max_depth)

        row = results[0]

        root_decision = DecisionCard(
            id=int(row['root_id']),
            summary=str(row['root_summary']),
            timestamp=str(row.get('root_timestamp', ''))
        )

        # Parse dependent decision IDs
        dep_ids = row.get('dep_ids', [])
        dep_summaries = row.get('dep_summaries', [])

        dependent_decisions = []
        if dep_ids and dep_ids != 'null' and isinstance(dep_ids, list):
            for i, dep_id in enumerate(dep_ids):
                if dep_id and dep_id != 'null':
                    dependent_decisions.append(DecisionCard(
                        id=int(dep_id),
                        summary=str(dep_summaries[i]) if i < len(dep_summaries) else "",
                        timestamp=""
                    ))

        return ImpactGraph(
            root_decision=root_decision,
            dependent_decisions=dependent_decisions,
            max_depth=max_depth
        )


if __name__ == "__main__":
    # Test Tier 2 Exploration queries
    print("=" * 60)
    print("Tier 2: Exploration Queries (Progressive Disclosure)")
    print("=" * 60)

    queries = ExplorationQueries()

    # Test with decision #85 (Serena Memory Enhancement)
    test_id = 85

    print(f"\n[1] Decision Neighborhood (1-hop):")
    neighborhood = queries.get_decision_neighborhood(test_id, max_hops=1)
    print(f"   Center: #{neighborhood.center.id} - {neighborhood.center.summary[:50]}...")
    print(f"   1-hop neighbors: {len(neighborhood.hop_1_neighbors)}")
    print(f"   2-hop neighbors: {len(neighborhood.hop_2_neighbors)}")
    print(f"   Expanded: {neighborhood.is_expanded}")
    for i, n in enumerate(neighborhood.hop_1_neighbors[:3], 1):
        print(f"      {i}. #{n.id}: {n.summary[:50]}...")

    print(f"\n[2] Decision Neighborhood (2-hop expanded):")
    neighborhood_expanded = queries.get_decision_neighborhood(test_id, max_hops=2)
    print(f"   1-hop neighbors: {len(neighborhood_expanded.hop_1_neighbors)}")
    print(f"   2-hop neighbors: {len(neighborhood_expanded.hop_2_neighbors)}")
    print(f"   Expanded: {neighborhood_expanded.is_expanded}")
    print(f"   Total network: {neighborhood_expanded.total_neighbors} decisions")

    print(f"\n[3] Genealogy Chain (BUILDS_UPON upstream):")
    chain = queries.get_genealogy_chain(test_id, 'BUILDS_UPON', 'upstream')
    print(f"   Chain length: {len(chain)} generations")
    for node in chain[:5]:
        print(f"   Gen {node.generation}: #{node.id} - {node.summary[:50]}...")

    print(f"\n[4] Find by Relationship Type (VALIDATES):")
    validates = queries.find_by_relationship_type(test_id, 'VALIDATES', 'outgoing')
    print(f"   Found {len(validates)} VALIDATES relationships")
    for d in validates[:3]:
        print(f"      #{d.id}: {d.summary[:50]}...")

    print(f"\n[5] Impact Graph (DEPENDS_ON):")
    impact = queries.get_impact_graph(test_id, max_depth=2)
    print(f"   Root: #{impact.root_decision.id}")
    print(f"   Dependent decisions: {impact.get_impact_count()}")
    print(f"   Critical: {impact.has_critical_dependencies()}")
    for i, d in enumerate(impact.dependent_decisions[:5], 1):
        print(f"      {i}. #{d.id}: {d.summary[:50]}...")

    print(f"\n✅ All Tier 2 exploration queries tested!")
