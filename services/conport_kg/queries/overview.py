#!/usr/bin/env python3
"""
Tier 1: Overview Queries
ADHD-optimized top-level decision discovery

Limits cognitive load with:
- Maximum 3 results (prevents overwhelm)
- High-level summaries only
- Recent decisions first
"""

import psycopg2
from typing import List, Dict, Optional


class OverviewQueries:
    """
    Tier 1: Overview - Top-3 Pattern

    Provides highest-level view of decision landscape.
    Designed for quick orientation and context loading.
    """

    def __init__(self, age_url: str = None):
        self.age_url = age_url or "postgresql://dopemux_age:dopemux_age_dev_password@localhost:5455/dopemux_knowledge_graph"

    def _execute_cypher(self, cypher: str) -> List[tuple]:
        """Execute Cypher query via docker exec"""
        import subprocess

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
        return lines

    def get_recent_decisions(self, limit: int = 3) -> List[Dict]:
        """
        Get most recent decisions (Top-3 pattern)

        ADHD Optimization: Limits to 3 for quick scanning
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
            if '|' in row:
                parts = [p.strip() for p in row.split('|')]
                if len(parts) >= 3:
                    decisions.append({
                        'id': parts[0],
                        'summary': parts[1].strip('"'),
                        'timestamp': parts[2]
                    })

        return decisions

    def get_decision_summary(self, decision_id: int) -> Dict:
        """
        Get single decision with 1-hop context count

        Shows decision + count of related (doesn't load full related decisions)
        """

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision {{id: {decision_id}}})
                OPTIONAL MATCH (d)-[r]-(related:Decision)
                RETURN d.id, d.summary, d.rationale, COUNT(DISTINCT related) as related_count
            $$) as (id agtype, summary agtype, rationale agtype, count agtype);
        """

        results = self._execute_cypher(cypher)

        if results and len(results) > 0:
            row = results[0]
            if '|' in row:
                parts = [p.strip() for p in row.split('|')]
                return {
                    'id': parts[0],
                    'summary': parts[1].strip('"') if len(parts) > 1 else '',
                    'rationale': parts[2].strip('"') if len(parts) > 2 else '',
                    'related_count': parts[3] if len(parts) > 3 else '0'
                }

        return {}

    def get_root_decisions(self, limit: int = 3) -> List[Dict]:
        """
        Get root decisions (no incoming edges)

        These are foundational decisions that others build upon.
        Good starting point for genealogy exploration.
        """

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision)
                WHERE NOT EXISTS {{
                    MATCH (d)<-[]-(other:Decision)
                }}
                RETURN d.id, d.summary
                ORDER BY d.id DESC
                LIMIT {limit}
            $$) as (id agtype, summary agtype);
        """

        results = self._execute_cypher(cypher)

        decisions = []
        for row in results:
            if '|' in row:
                parts = [p.strip() for p in row.split('|')]
                if len(parts) >= 2:
                    decisions.append({
                        'id': parts[0],
                        'summary': parts[1].strip('"')
                    })

        return decisions

    def search_by_tag(self, tag: str, limit: int = 3) -> List[Dict]:
        """
        Search decisions by tag (Top-3 pattern)

        ADHD Optimization: Limits to 3 for quick scanning
        Tags are stored as JSONB array in AGE
        """

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision)
                WHERE '{tag}' = ANY(d.tags)
                RETURN d.id, d.summary, d.timestamp
                ORDER BY d.timestamp DESC
                LIMIT {limit}
            $$) as (id agtype, summary agtype, timestamp agtype);
        """

        results = self._execute_cypher(cypher)

        decisions = []
        for row in results:
            if '|' in row:
                parts = [p.strip() for p in row.split('|')]
                if len(parts) >= 3:
                    decisions.append({
                        'id': parts[0],
                        'summary': parts[1].strip('"'),
                        'timestamp': parts[2]
                    })

        return decisions


if __name__ == "__main__":
    # Test Tier 1 queries
    print("=" * 60)
    print("Tier 1: Overview Queries (ADHD Top-3 Pattern)")
    print("=" * 60)

    queries = OverviewQueries()

    print("\n[1] Recent Decisions (Top 3):")
    recent = queries.get_recent_decisions(3)
    for i, d in enumerate(recent, 1):
        print(f"  {i}. #{d['id']}: {d['summary'][:60]}...")

    print("\n[2] Root Decisions (Foundational):")
    roots = queries.get_root_decisions(3)
    for i, d in enumerate(roots, 1):
        print(f"  {i}. #{d['id']}: {d['summary'][:60]}...")

    print("\n[3] Decision Summary (with context count):")
    summary = queries.get_decision_summary(85)
    print(f"  ID: {summary.get('id')}")
    print(f"  Summary: {summary.get('summary', '')[:60]}...")
    print(f"  Related decisions: {summary.get('related_count')}")
