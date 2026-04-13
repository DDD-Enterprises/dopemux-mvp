#!/usr/bin/env python3
"""
Direct SQLite→AGE Migration
Part of CONPORT-KG-2025 Simplified Migration (Decision #113)

Loads ConPort data directly from SQLite export to AGE graph.
Minimal transformations needed - schemas already compatible!
"""

import json
import psycopg2
import sys
from pathlib import Path
from typing import Dict, List


class DirectAGELoader:
    """Loads SQLite data directly to AGE"""

    def __init__(self, age_url: str):
        self.age_url = age_url
        self.conn = None

    def connect(self):
        """Establish AGE connection"""
        # Force IPv4 to avoid IPv6 connection issues
        import psycopg2.extensions
        self.conn = psycopg2.connect(
            self.age_url,
            connect_timeout=10,
            options='-c client_encoding=UTF8'
        )
        cursor = self.conn.cursor()
        cursor.execute("LOAD 'age';")
        cursor.execute("SET search_path = ag_catalog, conport_knowledge, public;")
        cursor.close()
        print(f"✓ Connected to AGE database")

    def disconnect(self):
        """Close connection"""
        if self.conn:
            self.conn.close()

    def load_decision(self, decision: Dict):
        """Load single decision to AGE (direct mapping!)"""

        cursor = self.conn.cursor()

        # Escape strings for Cypher
        def escape(val):
            if val is None:
                return 'null'
            return json.dumps(str(val))

        # Tags: TEXT → JSONB conversion
        tags_json = decision.get('tags', '[]')

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                CREATE (:Decision {{
                    id: {decision['id']},
                    summary: {escape(decision['summary'])},
                    rationale: {escape(decision['rationale'])},
                    implementation: {escape(decision['implementation_details'])},
                    tags: '{tags_json}'::jsonb,
                    timestamp: {escape(decision['timestamp'])},
                    graph_version: 1,
                    hop_distance: null
                }})
            $$) as (v agtype);
        """

        try:
            cursor.execute(cypher)
            self.conn.commit()
            cursor.close()
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            raise e

    def load_relationship(self, relationship: Dict):
        """Load single relationship to AGE"""

        cursor = self.conn.cursor()

        # Convert VARCHAR IDs to INTEGER
        source_id = int(relationship['source_item_id'])
        target_id = int(relationship['target_item_id'])

        # Normalize relationship type to uppercase
        rel_type = relationship['relationship_type'].upper().replace(' ', '_')

        # Escape description
        desc = json.dumps(relationship.get('description', ''))

        cypher = f"""
            SELECT * FROM cypher('conport_knowledge', $$
                MATCH (source:Decision {{id: {source_id}}})
                MATCH (target:Decision {{id: {target_id}}})
                CREATE (source)-[:{rel_type} {{
                    description: {desc},
                    timestamp: {json.dumps(relationship['timestamp'])}
                }}]->(target)
            $$) as (e agtype);
        """

        try:
            cursor.execute(cypher)
            self.conn.commit()
            cursor.close()
        except Exception as e:
            self.conn.rollback()
            cursor.close()
            raise e

    def load_all(self, export_file: Path):
        """Load all data from export"""

        with open(export_file, 'r') as f:
            export_data = json.load(f)

        print(f"Loaded export from: {export_file}")
        print(f"  Decisions: {export_data['metadata']['decision_count']}")
        print(f"  Relationships: {export_data['metadata']['relationship_count']}")
        print()

        self.connect()

        try:
            # Load decisions
            print(f"Loading {len(export_data['decisions'])} decisions to AGE...")

            successful_decisions = 0
            failed_decisions = []

            for decision in export_data['decisions']:
                try:
                    self.load_decision(decision)
                    successful_decisions += 1

                    if successful_decisions % 20 == 0:
                        print(f"  Progress: {successful_decisions}/{len(export_data['decisions'])}")

                except Exception as e:
                    failed_decisions.append({
                        'id': decision['id'],
                        'summary': decision['summary'][:50],
                        'error': str(e)
                    })
                    print(f"  ✗ Failed decision {decision['id']}: {e}")

            print(f"\n✓ Loaded {successful_decisions} decisions to AGE")

            if failed_decisions:
                print(f"✗ {len(failed_decisions)} failures - aborting")
                return False

            # Load relationships
            print(f"\nLoading {len(export_data['relationships'])} relationships to AGE...")

            successful_rels = 0
            failed_rels = []

            for relationship in export_data['relationships']:
                try:
                    self.load_relationship(relationship)
                    successful_rels += 1

                    if successful_rels % 5 == 0:
                        print(f"  Progress: {successful_rels}/{len(export_data['relationships'])}")

                except Exception as e:
                    failed_rels.append({
                        'source': relationship['source_item_id'],
                        'target': relationship['target_item_id'],
                        'type': relationship['relationship_type'],
                        'error': str(e)
                    })
                    print(f"  ✗ Failed: {relationship['source_item_id']}→{relationship['target_item_id']}: {e}")

            print(f"\n✓ Loaded {successful_rels} relationships to AGE")

            if failed_rels:
                print(f"⚠️  {len(failed_rels)} relationship failures")
                for f in failed_rels[:5]:
                    print(f"  - {f['source']}→{f['target']} ({f['type']}): {f['error']}")

            return len(failed_decisions) == 0

        finally:
            self.disconnect()


def main():
    """Main migration procedure"""

    AGE_URL = "postgresql://dopemux_age:dopemux_age_password@localhost:5455/dopemux_knowledge_graph"
    EXPORT_FILE = Path("conport_sqlite_export.json")

    if not EXPORT_FILE.exists():
        print(f"✗ ERROR: Export file not found: {EXPORT_FILE}")
        print("  Run export_sqlite.py first")
        return 1

    print("=" * 60)
    print("Direct SQLite→AGE Migration")
    print("=" * 60)
    print()

    loader = DirectAGELoader(AGE_URL)

    try:
        success = loader.load_all(EXPORT_FILE)

        if success:
            print("\n✓ SUCCESS: Data loaded to AGE")
            print("\nNext steps:")
            print("  1. Run 003_create_age_indexes.sql")
            print("  2. Run compute_hop_distance.py")
            print("  3. Run benchmark_age.py")
            return 0
        else:
            print("\n✗ FAILURE: Some data failed to load")
            return 1

    except Exception as e:
        print(f"\n✗ ERROR: Migration failed")
        print(f"  {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
