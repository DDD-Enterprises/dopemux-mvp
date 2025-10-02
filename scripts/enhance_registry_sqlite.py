#!/usr/bin/env python3
import argparse
import sqlite3
from pathlib import Path

VIEWS_AND_INDEXES_SQL = [
    # Views
    (
        "CREATE VIEW IF NOT EXISTS research_recent_high_confidence AS\n"
        "SELECT research_id, title, research_type, recency_days, source_quality, confidence\n"
        "FROM research\n"
        "WHERE (recency_days IS NOT NULL AND recency_days <= 90)\n"
        "  AND (confidence IS NOT NULL AND confidence >= 0.8)\n"
        "ORDER BY recency_days ASC, confidence DESC;"
    ),
    (
        "CREATE VIEW IF NOT EXISTS components_security_gaps AS\n"
        "SELECT component_id, name, subsystem_id, security_notes, threat_model_refs\n"
        "FROM components\n"
        "WHERE (security_notes IS NULL OR security_notes = '')\n"
        "   OR (threat_model_refs IS NULL OR threat_model_refs = '');"
    ),
    (
        "CREATE VIEW IF NOT EXISTS components_missing_slos AS\n"
        "SELECT component_id, name, subsystem_id\n"
        "FROM components\n"
        "WHERE (slo_availability IS NULL OR slo_availability = '')\n"
        "   OR (slo_latency IS NULL OR slo_latency = '');"
    ),
    (
        "CREATE VIEW IF NOT EXISTS evidence_density_by_component AS\n"
        "SELECT c.component_id, c.name, COUNT(el.to_id) AS evidence_incoming\n"
        "FROM components c\n"
        "LEFT JOIN evidence_links el ON el.to_id = c.component_id\n"
        "GROUP BY c.component_id, c.name\n"
        "ORDER BY evidence_incoming DESC;"
    ),
    (
        "CREATE VIEW IF NOT EXISTS evidence_density_by_feature AS\n"
        "SELECT f.feature_id, f.title, COUNT(el.to_id) AS evidence_incoming\n"
        "FROM features f\n"
        "LEFT JOIN evidence_links el ON el.to_id = f.feature_id\n"
        "GROUP BY f.feature_id, f.title\n"
        "ORDER BY evidence_incoming DESC;"
    ),
    # Indexes
    "CREATE INDEX IF NOT EXISTS idx_components_subsystem ON components(subsystem_id);",
    "CREATE INDEX IF NOT EXISTS idx_components_name ON components(name);",
    "CREATE INDEX IF NOT EXISTS idx_features_priority ON features(priority);",
    "CREATE INDEX IF NOT EXISTS idx_research_confidence ON research(confidence);",
    "CREATE INDEX IF NOT EXISTS idx_research_recency ON research(recency_days);",
    "CREATE INDEX IF NOT EXISTS idx_evidence_from ON evidence_links(from_id);",
    "CREATE INDEX IF NOT EXISTS idx_evidence_to ON evidence_links(to_id);",
]


def main():
    parser = argparse.ArgumentParser(description="Enhance registries SQLite with views and indexes")
    parser.add_argument("db", help="Path to registries.db (e.g., build_combined/registries.db)")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    for sql in VIEWS_AND_INDEXES_SQL:
        try:
            cur.execute(sql)
        except Exception as e:
            print(f"Warning: could not apply SQL: {e}\nSQL: {sql[:120]}...")
    conn.commit()
    conn.close()
    print(f"✅ Enhanced SQLite with views and indexes: {db_path}")


if __name__ == "__main__":
    main()

