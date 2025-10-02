#!/usr/bin/env python3
"""
AGE Node Loading Script
Part of CONPORT-KG-2025 Two-Phase Migration (Decision #112)

Loads decisions from upgraded ConPort to AGE graph.
Simple 1:1 copy - no transformations needed!
"""

import asyncio
import asyncpg
import psycopg2
import sys
from typing import List, Dict


class AGENodeLoader:
    """Loads decision nodes into AGE graph"""

    def __init__(self, conport_url: str, age_url: str):
        self.conport_url = conport_url
        self.age_url = age_url
        self.conport_conn = None
        self.age_conn = None

    async def connect(self):
        """Establish database connections"""
        self.conport_conn = await asyncpg.connect(self.conport_url)
        # AGE requires psycopg2 for Cypher queries
        self.age_conn = psycopg2.connect(self.age_url)
        print(f"✓ Connected to ConPort and AGE databases")

    def disconnect(self):
        """Close database connections"""
        if self.conport_conn:
            asyncio.create_task(self.conport_conn.close())
        if self.age_conn:
            self.age_conn.close()

    async def extract_decisions(self, workspace_id: str) -> List[Dict]:
        """Extract decisions from upgraded ConPort schema"""

        query = """
            SELECT
                id,
                workspace_id,
                summary,
                rationale,
                status,
                implementation,
                tags::text as tags,
                confidence_level,
                decision_type,
                graph_version,
                hop_distance,
                created_at
            FROM decisions
            WHERE workspace_id = $1
            ORDER BY id ASC
        """

        rows = await self.conport_conn.fetch(query, workspace_id)

        decisions = [dict(row) for row in rows]
        print(f"✓ Extracted {len(decisions)} decisions from ConPort")

        return decisions

    def load_decision_to_age(self, decision: Dict):
        """Load single decision as AGE vertex"""

        # Prepare Cypher parameters
        cypher = """
            SELECT * FROM cypher('conport_knowledge', $$
                CREATE (:Decision {
                    id: %s,
                    workspace_id: %s,
                    summary: %s,
                    rationale: %s,
                    status: %s,
                    implementation: %s,
                    tags: %s,
                    confidence_level: %s,
                    decision_type: %s,
                    graph_version: %s,
                    hop_distance: %s,
                    timestamp: %s,
                    last_updated: NOW()
                })
            $$) as (v agtype);
        """

        cursor = self.age_conn.cursor()

        try:
            cursor.execute(
                cypher % (
                    decision['id'],
                    repr(decision['workspace_id']),
                    repr(decision['summary']),
                    repr(decision['rationale']),
                    repr(decision['status']),
                    repr(decision['implementation']) if decision['implementation'] else 'NULL',
                    repr(decision['tags']),
                    repr(decision['confidence_level']),
                    repr(decision['decision_type']),
                    decision['graph_version'],
                    decision['hop_distance'] if decision['hop_distance'] is not None else 'NULL',
                    repr(decision['created_at'].isoformat())
                )
            )

            self.age_conn.commit()

        except Exception as e:
            self.age_conn.rollback()
            raise e
        finally:
            cursor.close()

    async def load_all_nodes(self, workspace_id: str):
        """Load all decisions to AGE"""

        await self.connect()

        try:
            decisions = await self.extract_decisions(workspace_id)

            print(f"\nLoading {len(decisions)} decisions to AGE graph...")

            successful = 0
            failed = []

            for decision in decisions:
                try:
                    self.load_decision_to_age(decision)
                    successful += 1

                    if successful % 10 == 0:
                        print(f"  Progress: {successful}/{len(decisions)}")

                except Exception as e:
                    failed.append({
                        'id': decision['id'],
                        'summary': decision['summary'][:50],
                        'error': str(e)
                    })
                    print(f"  ✗ Failed decision {decision['id']}: {e}")

            print(f"\n✓ Loaded {successful} nodes to AGE")

            if failed:
                print(f"\n✗ {len(failed)} failures:")
                for f in failed:
                    print(f"  - ID {f['id']}: {f['summary']}... ({f['error']})")
                return False

            return True

        finally:
            self.disconnect()


async def main():
    """Main node loading procedure"""

    # Configuration
    CONPORT_URL = "postgresql://dopemux:dopemux_dev_password@localhost:5432/dopemux_memory"
    AGE_URL = "postgresql://dopemux_age:dopemux_age_password@localhost:5455/dopemux_knowledge_graph"
    WORKSPACE_ID = "/Users/hue/code/dopemux-mvp"

    print("=" * 60)
    print("AGE Node Loading (Phase 2)")
    print("=" * 60)
    print(f"Workspace: {WORKSPACE_ID}")
    print()

    loader = AGENodeLoader(CONPORT_URL, AGE_URL)

    try:
        success = await loader.load_all_nodes(WORKSPACE_ID)

        if success:
            print("\n✓ SUCCESS: All nodes loaded to AGE")
            print("\nNext steps:")
            print("  1. Run load_age_edges.py")
            return 0
        else:
            print("\n✗ FAILURE: Some nodes failed to load")
            return 1

    except Exception as e:
        print(f"\n✗ ERROR: Node loading failed")
        print(f"  {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
