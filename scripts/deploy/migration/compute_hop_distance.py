#!/usr/bin/env python3
"""
Hop Distance Computation
Part of CONPORT-KG-2025 Two-Phase Migration (Decision #112)

Computes hop_distance for all decisions using BFS from root nodes.
Root nodes = decisions with no incoming SUPERSEDES edges.
Enables ADHD 3-hop limit filtering.
"""

import asyncio
import psycopg2
import sys
from collections import deque
from typing import Set, Dict, List


class HopDistanceComputer:
    """Computes hop distance using BFS algorithm"""

    def __init__(self, age_url: str):
        self.age_url = age_url
        self.conn = None

    def connect(self):
        """Establish database connection"""
        self.conn = psycopg2.connect(self.age_url)
        print(f"✓ Connected to AGE database")

    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def find_root_decisions(self) -> List[int]:
        """Find root decisions (no incoming SUPERSEDES edges)"""

        cypher = """
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (d:Decision)
                WHERE NOT (d)<-[:SUPERSEDES]-()
                RETURN d.id
            $$) as (decision_id agtype);
        """

        cursor = self.conn.cursor()
        cursor.execute(cypher)
        rows = cursor.fetchall()
        cursor.close()

        root_ids = [row[0] for row in rows]
        print(f"✓ Found {len(root_ids)} root decisions (no incoming SUPERSEDES)")

        return root_ids

    def compute_hop_distances(self):
        """
        Compute hop_distance for all decisions using BFS

        Algorithm:
        1. Find root decisions (no incoming SUPERSEDES)
        2. Set root hop_distance = 0
        3. BFS traversal: each neighbor gets parent_hop + 1
        4. Update all decision nodes with computed distances
        """

        self.connect()

        try:
            # Step 1: Find roots
            root_ids = self.find_root_decisions()

            if not root_ids:
                print("⚠️  WARNING: No root decisions found")
                print("   Setting all decisions to hop_distance = 0")
                # Set all to 0 as fallback
                cursor = self.conn.cursor()
                cursor.execute("""
                    SELECT * FROM cypher('conport_knowledge', $$
                        MATCH (d:Decision)
                        SET d.hop_distance = 0
                    $$) as (result agtype);
                """)
                self.conn.commit()
                cursor.close()
                return

            # Step 2: Initialize roots to hop_distance = 0
            print(f"\nInitializing {len(root_ids)} root decisions to hop_distance = 0...")

            cursor = self.conn.cursor()
            for root_id in root_ids:
                cursor.execute(f"""
                    SELECT * FROM cypher('conport_knowledge', $$
                        MATCH (d:Decision {{id: {root_id}}})
                        SET d.hop_distance = 0
                    $$) as (result agtype);
                """)
            self.conn.commit()
            cursor.close()

            print("✓ Root nodes initialized")

            # Step 3: BFS traversal
            print("\nComputing hop distances via BFS...")

            visited: Set[int] = set(root_ids)
            queue = deque([(root_id, 0) for root_id in root_ids])
            updates = 0

            cursor = self.conn.cursor()

            while queue:
                current_id, current_hop = queue.popleft()

                # Get all neighbors (any relationship type, any direction)
                cursor.execute(f"""
                    SELECT * FROM cypher('conport_knowledge', $$
                        MATCH (current:Decision {{id: {current_id}}})-[]-(neighbor:Decision)
                        WHERE neighbor.hop_distance IS NULL
                        RETURN DISTINCT neighbor.id
                    $$) as (neighbor_id agtype);
                """)

                neighbors = [row[0] for row in cursor.fetchall()]

                for neighbor_id in neighbors:
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        new_hop = current_hop + 1

                        # Limit to max 10 hops (safety for cycles)
                        if new_hop <= 10:
                            # Update hop_distance
                            cursor.execute(f"""
                                SELECT * FROM cypher('conport_knowledge', $$
                                    MATCH (d:Decision {{id: {neighbor_id}}})
                                    SET d.hop_distance = {new_hop}
                                $$) as (result agtype);
                            """)

                            queue.append((neighbor_id, new_hop))
                            updates += 1

                            if updates % 10 == 0:
                                print(f"  Progress: {updates} nodes updated")

            self.conn.commit()
            cursor.close()

            print(f"\n✓ Computed hop_distance for {updates} nodes")

            # Verify all nodes have hop_distance
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT * FROM cypher('conport_knowledge', $$
                    MATCH (d:Decision)
                    WHERE d.hop_distance IS NULL
                    RETURN COUNT(d)
                $$) as (count agtype);
            """)
            null_count = cursor.fetchone()[0]
            cursor.close()

            if null_count > 0:
                print(f"\n⚠️  WARNING: {null_count} decisions still have NULL hop_distance")
                print("   These may be in disconnected components")
            else:
                print("\n✓ All decisions have hop_distance computed")

            return True

        finally:
            self.disconnect()


async def main():
    """Main hop distance computation"""

    # Configuration
    AGE_URL = "postgresql://dopemux_age:dopemux_age_password@localhost:5455/dopemux_knowledge_graph"

    print("=" * 60)
    print("Hop Distance Computation (Phase 2)")
    print("=" * 60)
    print()

    computer = HopDistanceComputer(AGE_URL)

    try:
        success = computer.compute_hop_distances()

        if success:
            print("\n✓ SUCCESS: Hop distances computed")
            print("\nNext steps:")
            print("  1. Run benchmark_age.py to test performance")
            return 0
        else:
            print("\n✗ FAILURE: Hop distance computation failed")
            return 1

    except Exception as e:
        print(f"\n✗ ERROR: Computation failed")
        print(f"  {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
