#!/usr/bin/env python3
"""
ConPort Data Re-ingestion Script
Part of CONPORT-KG-2025 Two-Phase Migration (Decision #112)

Re-ingests exported data into upgraded schema with transformations.
Transaction-safe with savepoints for error recovery.
"""

import asyncio
import asyncpg
import json
import sys
from pathlib import Path
from typing import Dict, List

from transformer import DecisionTransformer


class ConPortReingester:
    """Re-ingests data into upgraded ConPort schema"""

    def __init__(self, db_url: str):
        self.db_url = db_url
        self.conn = None
        self.transformer = DecisionTransformer()

    async def connect(self):
        """Establish database connection"""
        self.conn = await asyncpg.connect(self.db_url)
        print(f"✓ Connected to ConPort PostgreSQL")

    async def disconnect(self):
        """Close database connection"""
        if self.conn:
            await self.conn.close()

    async def reingest_decisions(self, decisions: List[Dict]):
        """
        Re-ingest decisions into decisions_v2

        CRITICAL: Inserts in created_at order so SERIAL IDs match temporal sequence
        """

        print(f"\nRe-ingesting {len(decisions)} decisions...")

        insert_query = """
            INSERT INTO decisions_v2 (
                workspace_id, summary, rationale, status, implementation,
                tags, alternatives, confidence_level, decision_type,
                graph_version, hop_distance, created_at, updated_at, old_uuid
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            RETURNING id
        """

        successful = 0
        failed = []

        for idx, old_decision in enumerate(decisions, start=1):
            try:
                # Transform decision
                transformed = self.transformer.transform_decision(old_decision, idx)

                # Insert with savepoint for individual rollback
                await self.conn.execute("SAVEPOINT decision_insert")

                new_id = await self.conn.fetchval(
                    insert_query,
                    transformed['workspace_id'],
                    transformed['summary'],
                    transformed['rationale'],
                    transformed['status'],
                    transformed['implementation'],
                    transformed['tags'],
                    transformed['alternatives'],
                    transformed['confidence_level'],
                    transformed['decision_type'],
                    transformed['graph_version'],
                    transformed['hop_distance'],
                    transformed['created_at'],
                    transformed['updated_at'],
                    transformed['old_uuid']
                )

                await self.conn.execute("RELEASE SAVEPOINT decision_insert")

                successful += 1

                if successful % 10 == 0:
                    print(f"  Progress: {successful}/{len(decisions)}")

            except Exception as e:
                await self.conn.execute("ROLLBACK TO SAVEPOINT decision_insert")
                failed.append({
                    'id': old_decision['id'],
                    'summary': old_decision['summary'][:50],
                    'error': str(e)
                })
                print(f"  ✗ Failed decision {old_decision['id']}: {e}")

        print(f"\n✓ Decisions: {successful} successful, {len(failed)} failed")

        if failed:
            print("\nFailed decisions:")
            for f in failed:
                print(f"  - {f['id']}: {f['summary']}... ({f['error']})")

        return successful, failed

    async def reingest_relationships(self, relationships: List[Dict]):
        """Re-ingest relationships into entity_relationships_v2"""

        print(f"\nRe-ingesting {len(relationships)} relationships...")

        insert_query = """
            INSERT INTO entity_relationships_v2 (
                workspace_id, source_type, source_id, target_type, target_id,
                relationship_type, strength, properties, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """

        successful = 0
        failed = []

        for old_rel in relationships:
            try:
                # Transform relationship
                transformed = self.transformer.transform_relationship(old_rel)

                # Insert with savepoint
                await self.conn.execute("SAVEPOINT relationship_insert")

                await self.conn.fetchval(
                    insert_query,
                    transformed['workspace_id'],
                    transformed['source_type'],
                    transformed['source_id'],
                    transformed['target_type'],
                    transformed['target_id'],
                    transformed['relationship_type'],
                    transformed['strength'],
                    transformed['properties'],
                    transformed['created_at']
                )

                await self.conn.execute("RELEASE SAVEPOINT relationship_insert")

                successful += 1

            except Exception as e:
                await self.conn.execute("ROLLBACK TO SAVEPOINT relationship_insert")
                failed.append({
                    'source': old_rel['source_id'],
                    'target': old_rel['target_id'],
                    'type': old_rel['relationship_type'],
                    'error': str(e)
                })
                print(f"  ✗ Failed relationship {old_rel['source_id']}→{old_rel['target_id']}: {e}")

        print(f"\n✓ Relationships: {successful} successful, {len(failed)} failed")

        return successful, failed

    async def reingest_all(self, export_file: Path):
        """Complete re-ingestion procedure"""

        # Load export data
        with open(export_file, 'r') as f:
            export_data = json.load(f)

        print(f"Loaded backup from: {export_file}")
        print(f"  Timestamp: {export_data['metadata']['timestamp']}")
        print(f"  Decisions: {export_data['metadata']['decision_count']}")
        print(f"  Relationships: {export_data['metadata']['relationship_count']}")

        await self.connect()

        try:
            # Start transaction
            async with self.conn.transaction():
                # Re-ingest decisions first
                dec_success, dec_failed = await self.reingest_decisions(
                    export_data['decisions']
                )

                if dec_failed:
                    raise ValueError(f"{len(dec_failed)} decisions failed - aborting")

                # Then re-ingest relationships (needs UUID→ID map)
                rel_success, rel_failed = await self.reingest_relationships(
                    export_data['relationships']
                )

                if rel_failed:
                    raise ValueError(f"{len(rel_failed)} relationships failed - aborting")

                print(f"\n✓ Transaction complete - all data re-ingested")

                # Statistics
                stats = self.transformer.get_statistics()
                print(f"\nTransformation statistics:")
                print(f"  UUID mappings: {stats['uuid_mappings']}")
                print(f"  Relationship type mappings: {len(stats['relationship_type_mappings'])}")

                return {
                    'decisions_success': dec_success,
                    'relationships_success': rel_success,
                    'uuid_mappings': stats['uuid_mappings']
                }

        finally:
            await self.disconnect()


async def main():
    """Main re-ingestion procedure"""

    # Configuration
    DB_URL = "postgresql://dopemux:dopemux_dev_password@localhost:5432/dopemux_memory"
    EXPORT_FILE = Path("conport_backup_dopemux-mvp.json")

    if not EXPORT_FILE.exists():
        print(f"✗ ERROR: Export file not found: {EXPORT_FILE}")
        print("  Run export_conport.py first")
        return 1

    print("=" * 60)
    print("ConPort Data Re-ingestion (Schema Upgrade)")
    print("=" * 60)
    print(f"Export file: {EXPORT_FILE}")
    print()

    reingester = ConPortReingester(DB_URL)

    try:
        result = await reingester.reingest_all(EXPORT_FILE)

        print("\n✓ SUCCESS: Data re-ingested successfully")
        print("\nNext steps:")
        print("  1. Run validate.py to verify data integrity")
        print("  2. If validation passes, run switchover.py")

        return 0

    except Exception as e:
        print(f"\n✗ ERROR: Re-ingestion failed")
        print(f"  {str(e)}")
        print("\nTransaction rolled back - no changes applied")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
