#!/usr/bin/env python3
"""
Generate AGE SQL from SQLite Export
Creates SQL file that can be executed via docker exec
"""

import json
from pathlib import Path


def generate_age_sql(export_file: Path, output_file: Path):
    """Generate Cypher SQL statements for AGE"""

    with open(export_file, 'r') as f:
        data = json.load(f)

    with open(output_file, 'w') as f:
        # Setup
        f.write("-- AGE Migration SQL\n")
        f.write("LOAD 'age';\n")
        f.write("SET search_path = ag_catalog, conport_knowledge, public;\n\n")

        # Load decisions
        f.write(f"-- Loading {len(data['decisions'])} decisions\n")

        for i, decision in enumerate(data['decisions'], 1):
            # Escape values
            def esc(v):
                if v is None:
                    return 'null'
                return json.dumps(str(v))

            tags = decision.get('tags', '[]')

            sql = f"""SELECT * FROM cypher('conport_knowledge', $$
    CREATE (:Decision {{
        id: {decision['id']},
        summary: {esc(decision['summary'])},
        rationale: {esc(decision['rationale'])},
        implementation: {esc(decision['implementation_details'])},
        tags: '{tags}'::jsonb,
        timestamp: {esc(decision['timestamp'])},
        graph_version: 1,
        hop_distance: null
    }})
$$) as (v agtype);

"""
            f.write(sql)

            if i % 20 == 0:
                print(f"  Generated {i}/{len(data['decisions'])} decisions")

        # Load relationships
        f.write(f"\n-- Loading {len(data['relationships'])} relationships\n")

        for relationship in data['relationships']:
            source = int(relationship['source_item_id'])
            target = int(relationship['target_item_id'])
            rel_type = relationship['relationship_type'].upper().replace(' ', '_')
            desc = json.dumps(relationship.get('description', ''))

            sql = f"""SELECT * FROM cypher('conport_knowledge', $$
    MATCH (s:Decision {{id: {source}}}), (t:Decision {{id: {target}}})
    CREATE (s)-[:{rel_type} {{description: {desc}}}]->(t)
$$) as (e agtype);

"""
            f.write(sql)

    file_size = output_file.stat().st_size / 1024
    print(f"\n✓ Generated {output_file} ({file_size:.1f} KB)")
    print(f"  Execute with: docker exec dopemux-postgres-age psql -U dopemux_age -d dopemux_knowledge_graph -f /path/to/file")


if __name__ == "__main__":
    generate_age_sql(
        Path("conport_sqlite_export.json"),
        Path("age_migration.sql")
    )
