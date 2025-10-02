#!/usr/bin/env python3
"""
Tier 1: Overview Queries
ADHD-optimized top-level decision discovery

Limits cognitive load with:
- Maximum 3 results (prevents overwhelm)
- High-level summaries only
- Recent decisions first

Phase 4 Refactor: Uses AGEClient with connection pooling (Decision #117)
"""

import os
import sys
import subprocess
from typing import List, Union
from dataclasses import dataclass, field
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from age_client import AGEClient
    from queries.models import DecisionCard, DecisionSummary
except ImportError:
    # Fallback for testing
    sys.path.insert(0, '/Users/hue/code/dopemux-mvp/services/conport_kg')
    from age_client import AGEClient
    # Import models inline for testing
    exec(open('/Users/hue/code/dopemux-mvp/services/conport_kg/queries/models.py').read())


# Feature flag for rollback safety
USE_DIRECT_CONNECTION = os.getenv('KG_DIRECT_CONNECTION', 'true').lower() == 'true'


class OverviewQueries:
    """
    Tier 1: Overview - Top-3 Pattern

    Provides highest-level view of decision landscape.
    Designed for quick orientation and context loading.

    Now uses AGEClient for <50ms performance (was 50-100ms with docker exec)
    """

    def __init__(self, age_url: str = None, use_direct: bool = None):
        """
        Initialize with AGEClient or fallback to docker exec

        Args:
            age_url: Optional connection URL (uses defaults if not provided)
            use_direct: Override feature flag for testing
        """
        self.use_direct = use_direct if use_direct is not None else USE_DIRECT_CONNECTION

        if self.use_direct:
            try:
                self.client = AGEClient()
                print(f"✅ OverviewQueries using AGEClient (direct connection)")
            except Exception as e:
                print(f"⚠️  AGEClient failed, falling back to docker exec: {e}")
                self.client = None
                self.use_direct = False
        else:
            self.client = None
            print(f"ℹ️  OverviewQueries using docker exec (feature flag disabled)")

    def _execute_cypher_direct(self, cypher: str) -> List[dict]:
        """Execute via AGEClient (fast path)"""
        return self.client.execute_cypher(cypher)

    def _execute_cypher_fallback(self, cypher: str) -> List[dict]:
        """Execute via docker exec (fallback path)"""
        cmd = [
            'docker', 'exec', 'dopemux-postgres-age',
            'psql', '-U', 'dopemux_age', '-d', 'dopemux_knowledge_graph',
            '-t', '-c', f"LOAD 'age'; SET search_path = ag_catalog, conport_knowledge, public; {cypher}"
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

        if result.returncode != 0:
            raise Exception(f"Query failed: {result.stderr}")

        # Parse simple results
        lines = [l.strip() for l in result.stdout.strip().split('\n') if l.strip() and '(' not in l]

        # Convert to list of dicts (matching AGEClient format)
        parsed_results = []
        for line in lines:
            if '|' in line:
                parts = [p.strip() for p in line.split('|')]
                # This is a simplified parser - AGEClient handles this better
                parsed_results.append({'raw': line, 'parts': parts})

        return parsed_results

    def _execute_cypher(self, cypher: str) -> List[dict]:
        """Execute Cypher query via best available method"""
        if self.use_direct and self.client:
            return self._execute_cypher_direct(cypher)
        else:
            return self._execute_cypher_fallback(cypher)

    def get_recent_decisions(self, limit: int = 3) -> List[DecisionCard]:
        """
        Get most recent decisions (Top-3 pattern)

        ADHD Optimization: Limits to 3 for quick scanning

        Returns: List[DecisionCard] with typed data
        """

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision)
                RETURN d.id, d.summary, d.timestamp
                ORDER BY d.timestamp DESC
                LIMIT {limit}
            $$) as (id agtype, summary agtype, timestamp agtype);
        """

        results = self._execute_cypher(cypher)

        decisions = []
        for row in results:
            if self.use_direct:
                # AGEClient returns parsed dicts
                decisions.append(DecisionCard(
                    id=int(row['id']),
                    summary=str(row['summary']),
                    timestamp=str(row['timestamp'])
                ))
            else:
                # Fallback parser
                parts = row.get('parts', [])
                if len(parts) >= 3:
                    decisions.append(DecisionCard(
                        id=int(parts[0]),
                        summary=parts[1].strip('"'),
                        timestamp=parts[2]
                    ))

        return decisions

    def get_decision_summary(self, decision_id: int) -> DecisionSummary:
        """
        Get single decision with 1-hop context count

        Shows decision + count of related (doesn't load full related decisions)

        Returns: DecisionSummary with typed data
        """

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision {{id: {decision_id}}})
                OPTIONAL MATCH (d)-[r]-(related:Decision)
                WITH d, COUNT(DISTINCT related) as rel_count, COLLECT(DISTINCT type(r)) as rel_types
                RETURN d.id, d.summary, d.rationale, rel_count, rel_types
            $$) as (id agtype, summary agtype, rationale agtype, rel_count agtype, rel_types agtype);
        """

        results = self._execute_cypher(cypher)

        if results and len(results) > 0:
            row = results[0]

            if self.use_direct:
                return DecisionSummary(
                    id=int(row['id']),
                    summary=str(row['summary']),
                    timestamp="",  # Not queried in this view
                    rationale=str(row.get('rationale', '')),
                    related_count=int(row.get('rel_count', 0)),
                    relationship_types=row.get('rel_types', [])
                )
            else:
                # Fallback parser
                parts = row.get('parts', [])
                if len(parts) >= 3:
                    return DecisionSummary(
                        id=int(parts[0]),
                        summary=parts[1].strip('"'),
                        timestamp="",
                        rationale=parts[2].strip('"') if len(parts) > 2 else '',
                        related_count=int(parts[3]) if len(parts) > 3 else 0
                    )

        return DecisionSummary(id=decision_id, summary="Not found", timestamp="")

    def get_root_decisions(self, limit: int = 3) -> List[DecisionCard]:
        """
        Get root decisions (no incoming edges)

        These are foundational decisions that others build upon.
        Good starting point for genealogy exploration.

        Returns: List[DecisionCard] with typed data
        """

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision)
                WHERE NOT EXISTS {{
                    MATCH (d)<-[]-(other:Decision)
                }}
                RETURN d.id, d.summary, d.timestamp
                ORDER BY d.id DESC
                LIMIT {limit}
            $$) as (id agtype, summary agtype, timestamp agtype);
        """

        results = self._execute_cypher(cypher)

        decisions = []
        for row in results:
            if self.use_direct:
                decisions.append(DecisionCard(
                    id=int(row['id']),
                    summary=str(row['summary']),
                    timestamp=str(row.get('timestamp', ''))
                ))
            else:
                parts = row.get('parts', [])
                if len(parts) >= 2:
                    decisions.append(DecisionCard(
                        id=int(parts[0]),
                        summary=parts[1].strip('"'),
                        timestamp=parts[2] if len(parts) > 2 else ''
                    ))

        return decisions

    def search_by_tag(self, tag: str, limit: int = 3) -> List[DecisionCard]:
        """
        Search decisions by tag (Top-3 pattern)

        ADHD Optimization: Limits to 3 for quick scanning
        Tags are stored as JSONB array in AGE

        Returns: List[DecisionCard] with typed data
        """

        # AGE doesn't support ANY function, use array contains check
        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision)
                WHERE d.tags @> ['"{tag}"']
                RETURN d.id, d.summary, d.timestamp
                ORDER BY d.timestamp DESC
                LIMIT {limit}
            $$) as (id agtype, summary agtype, timestamp agtype);
        """

        results = self._execute_cypher(cypher)

        decisions = []
        for row in results:
            if self.use_direct:
                decisions.append(DecisionCard(
                    id=int(row['id']),
                    summary=str(row['summary']),
                    timestamp=str(row['timestamp'])
                ))
            else:
                parts = row.get('parts', [])
                if len(parts) >= 3:
                    decisions.append(DecisionCard(
                        id=int(parts[0]),
                        summary=parts[1].strip('"'),
                        timestamp=parts[2]
                    ))

        return decisions


if __name__ == "__main__":
    # Test Tier 1 queries with AGEClient
    print("=" * 60)
    print("Tier 1: Overview Queries (ADHD Top-3 Pattern)")
    print("Using: AGEClient with connection pooling" if USE_DIRECT_CONNECTION else "Using: Docker exec fallback")
    print("=" * 60)

    queries = OverviewQueries()

    print("\n[1] Recent Decisions (Top 3):")
    recent = queries.get_recent_decisions(3)
    for i, d in enumerate(recent, 1):
        print(f"  {i}. #{d.id}: {d.summary[:60]}...")
        print(f"     Type: {type(d).__name__}")

    print("\n[2] Root Decisions (Foundational):")
    roots = queries.get_root_decisions(3)
    for i, d in enumerate(roots, 1):
        print(f"  {i}. #{d.id}: {d.summary[:60]}...")
        print(f"     Type: {type(d).__name__}")

    print("\n[3] Decision Summary (with context count):")
    summary = queries.get_decision_summary(85)
    print(f"  ID: {summary.id}")
    print(f"  Summary: {summary.summary[:60]}...")
    print(f"  Related decisions: {summary.related_count}")
    print(f"  Cognitive load: {summary.get_cognitive_load()}")
    print(f"  Type: {type(summary).__name__}")

    print("\n[4] Search by tag:")
    tag_results = queries.search_by_tag("adhd-optimization", 3)
    print(f"  Found {len(tag_results)} decisions with tag 'adhd-optimization'")
    for i, d in enumerate(tag_results, 1):
        print(f"  {i}. #{d.id}: {d.summary[:60]}...")

    print(f"\n✅ All queries returning typed models ({type(recent[0]).__name__ if recent else 'N/A'})")
