#!/usr/bin/env python3
"""
AGE Edge Loading Script
Part of CONPORT-KG-2025 Two-Phase Migration (Decision #112)

Loads relationships from upgraded ConPort to AGE graph as edges.
Simple 1:1 copy - schemas now match!
"""

import asyncio
import asyncpg
import psycopg2
import sys
from typing import List, Dict


class AGEEdgeLoader:
    """Loads relationship edges into AGE graph"""

    def __init__(self, conport_url: str, age_url: str):
        self.conport_url = conport_url
        self.age_url = age_url
        self.conport_conn = None
        self.age_conn = None

    async def connect(self):
        """Establish database connections"""
        self.conport_conn = await asyncpg.connect(self.conport_url)
        self.age_conn = psycopg2.connect(self.age_url)
        print(f"✓ Connected to ConPort and AGE databases")

    def disconnect(self):
        """Close database connections"""
        if self.conport_conn:
            asyncio.create_task(self.conport_conn.close())
        if self.age_conn:
            self.age_conn.close()

    async def extract_relationships(self) -> List[Dict]:
        """Extract relationships from upgraded ConPort schema"""

        query = """
            SELECT
                source_id,
                target_id,
                relationship_type,
                strength,
                properties::text as properties,
                created_at
            FROM entity_relationships
            WHERE source_type = 'decision'
              AND target_type = 'decision'
            ORDER BY created_at ASC
        """

        rows = await self.conport_conn.fetch(query)

        relationships = [dict(row) for row in rows]
        print(f"✓ Extracted {len(relationships)} relationships from ConPort")

        return relationships

    def load_edge_to_age(self, relationship: Dict):
        """Load single relationship as AGE edge"""

        cypher = """
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (source:Decision {id: %s})
                MATCH (target:Decision {id: %s})
                CREATE (source)-[:%s {
                    strength: %s,
                    properties: %s,
                    timestamp: %s
                }]->(target)
            $$) as (e agtype);
        """

        cursor = self.age_conn.cursor()

        try:
            cursor.execute(
                cypher % (
                    relationship['source_id'],
                    relationship['target_id'],
                    relationship['relationship_type'],
                    relationship['strength'],
                    repr(relationship['properties']),
                    repr(relationship['created_at'].isoformat())
                )
            )

            self.age_conn.commit()

        except Exception as e:
            self.age_conn.rollback()
            raise e
        finally:
            cursor.close()

    async def load_all_edges(self):
        """Load all relationships to AGE"""

        await self.connect()

        try:
            relationships = await self.extract_relationships()

            print(f"\nLoading {len(relationships)} edges to AGE graph...")

            successful = 0
            failed = []

            for rel in relationships:
                try:
                    self.load_edge_to_age(rel)
                    successful += 1

                    if successful % 5 == 0:
                        print(f"  Progress: {successful}/{len(relationships)}")

                except Exception as e:
                    failed.append({
                        'source_id': rel['source_id'],
                        'target_id': rel['target_id'],
                        'type': rel['relationship_type'],
                        'error': str(e)
                    })
                    print(f"  ✗ Failed edge {rel['source_id']}→{rel['target_id']}: {e}")

            print(f"\n✓ Loaded {successful} edges to AGE")

            if failed:
                print(f"\n✗ {len(failed)} failures:")
                for f in failed:
                    print(f"  - {f['source_id']}→{f['target_id']} ({f['type']}): {f['error']}")
                return False

            # Validate no orphaned edges
            cursor = self.age_conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM cypher('conport_knowledge', $$
                    MATCH ()-[r]->()
                    RETURN COUNT(r)
                $$) as (count agtype);
            """)
            edge_count = cursor.fetchone()[0]
            cursor.close()

            print(f"\nValidation: {edge_count} edges in AGE graph")

            return True

        finally:
            self.disconnect()


async def main():
    """Main edge loading procedure"""

    # Configuration
    CONPORT_URL = "postgresql://dopemux:dopemux_dev_password@localhost:5432/dopemux_memory"
    AGE_URL = "postgresql://dopemux_age:dopemux_age_password@localhost:5455/dopemux_knowledge_graph"

    print("=" * 60)
    print("AGE Edge Loading (Phase 2)")
    print("=" * 60)
    print()

    loader = AGEEdgeLoader(CONPORT_URL, AGE_URL)

    try:
        success = await loader.load_all_edges()

        if success:
            print("\n✓ SUCCESS: All edges loaded to AGE")
            print("\nNext steps:")
            print("  1. Run 003_create_age_indexes.sql")
            print("  2. Run compute_hop_distance.py")
            return 0
        else:
            print("\n✗ FAILURE: Some edges failed to load")
            return 1

    except Exception as e:
        print(f"\n✗ ERROR: Edge loading failed")
        print(f"  {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
