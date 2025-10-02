# CONPORT-KG-2025 Migration Scripts

**Decision #112**: Two-Phase Clean Migration Strategy
**Epic**: DB-001 Database Foundation
**Status**: Ready for execution

## Overview

Complete migration system for upgrading ConPort schema and migrating to PostgreSQL AGE knowledge graph.

### Two-Phase Approach

**Phase 1: ConPort Schema Upgrade**
- Upgrade from UUID to INTEGER primary keys
- Expand from 4 to 8 relationship types
- Convert TEXT[] to JSONB
- Add AGE-compatible fields (status, implementation, hop_distance)

**Phase 2: Simple AGE Migration**
- Direct 1:1 copy (schemas now match!)
- Create performance indexes
- Compute hop distances
- Validate <150ms p95 performance

## Scripts

### Phase 1: ConPort Upgrade

| Script | Purpose | Runtime |
|--------|---------|---------|
| `001_create_decisions_v2.sql` | Create upgraded decision schema | <1 min |
| `002_create_relationships_v2.sql` | Create upgraded relationship schema | <1 min |
| `export_conport.py` | Export 94 decisions + 18 relationships to JSON | ~1 min |
| `transformer.py` | Schema transformation logic (UUID→INT, etc.) | Library |
| `reingest.py` | Re-ingest with transformations | ~2 min |
| `validate.py` | 4-point validation system | <1 min |
| `switchover.py` | Atomic table rename + MCP restart | ~2 min |
| `rollback.py` | Emergency recovery to old schema | ~1 min |

### Phase 2: AGE Migration

| Script | Purpose | Runtime |
|--------|---------|---------|
| `load_age_nodes.py` | Load 94 decisions as AGE vertices | ~2 min |
| `load_age_edges.py` | Load 18 relationships as AGE edges | ~1 min |
| `003_create_age_indexes.sql` | Create 12 performance indexes | ~2 min |
| `compute_hop_distance.py` | BFS hop distance computation | ~1 min |
| `benchmark_age.py` | Performance validation (<150ms) | ~2 min |

### Orchestration

| Script | Purpose |
|--------|---------|
| `migrate.py` | Master orchestration script |

## Quick Start

### Dry-Run Test (Recommended First!)

```bash
cd /Users/hue/code/dopemux-mvp

# Test with validation only
python scripts/migration/migrate.py --dry-run
```

### Full Migration

```bash
# Complete two-phase migration
python scripts/migration/migrate.py --full
```

### Phase-by-Phase

```bash
# Phase 1 only
python scripts/migration/migrate.py --phase1

# Phase 2 only (after Phase 1 complete)
python scripts/migration/migrate.py --phase2
```

## Manual Execution Steps

If you prefer manual control:

### Phase 1: ConPort Upgrade

```bash
# 1. Export data
python scripts/migration/export_conport.py

# 2. Create upgraded schema
psql postgresql://dopemux:dopemux_dev_password@localhost:5432/dopemux_memory \
  < scripts/migration/001_create_decisions_v2.sql

psql postgresql://dopemux:dopemux_dev_password@localhost:5432/dopemux_memory \
  < scripts/migration/002_create_relationships_v2.sql

# 3. Re-ingest
python scripts/migration/reingest.py

# 4. Validate
python scripts/migration/validate.py

# 5. Switchover (requires MCP server stop!)
docker stop conport-mcp-server
python scripts/migration/switchover.py
docker start conport-mcp-server
```

### Phase 2: AGE Migration

```bash
# 1. Load nodes
python scripts/migration/load_age_nodes.py

# 2. Load edges
python scripts/migration/load_age_edges.py

# 3. Create indexes
psql postgresql://dopemux_age:dopemux_age_password@localhost:5455/dopemux_knowledge_graph \
  < scripts/migration/003_create_age_indexes.sql

# 4. Compute hop distances
python scripts/migration/compute_hop_distance.py

# 5. Benchmark performance
python scripts/migration/benchmark_age.py
```

## Validation Checkpoints

### After Phase 1

- [ ] Decision count: 94 → 94
- [ ] Relationship count: 18 → 18
- [ ] No orphaned edges
- [ ] UUID mapping complete
- [ ] ConPort MCP server responds
- [ ] Can query decisions via ConPort

### After Phase 2

- [ ] AGE node count: 94
- [ ] AGE edge count: 18
- [ ] All indexes created
- [ ] All hop_distances computed
- [ ] 3-hop queries <150ms p95
- [ ] ADHD filtering works
- [ ] Workspace filtering works

## Rollback Procedures

### Phase 1 Rollback

```bash
python scripts/migration/rollback.py
docker restart conport-mcp-server
```

### Phase 2 Rollback

```sql
-- Drop AGE graph and recreate
SELECT drop_graph('conport_knowledge', true);
SELECT create_graph('conport_knowledge');
```

## Schema Transformations

### Decision Fields

| Old Field | New Field | Transformation |
|-----------|-----------|----------------|
| `id UUID` | `id SERIAL` | Sequential by created_at |
| `tags TEXT[]` | `tags JSONB` | JSON encoding |
| `alternatives JSONB` | `alternatives JSONB` | Preserved |
| `confidence_level` | `status` | Derived mapping |
| N/A | `implementation` | Derived from alternatives |
| N/A | `graph_version` | Default 1 |
| N/A | `hop_distance` | Computed post-migration |
| N/A | `old_uuid` | Temporary mapping |

### Relationship Types

| Old Type | New Type | Mapping |
|----------|----------|---------|
| `implements` | `IMPLEMENTS` | Direct |
| `relates_to` | `RELATES_TO` | Direct |
| `blocks` | `DEPENDS_ON` | Semantic |
| `caused_by` | `BUILDS_UPON` | Semantic |
| N/A | `SUPERSEDES` | Future use |
| N/A | `EXTENDS` | Future use |
| N/A | `VALIDATES` | Future use |
| N/A | `CORRECTS` | Future use |

## Dependencies

```bash
# Python packages
pip install asyncpg psycopg2-binary

# PostgreSQL AGE
# Already installed: localhost:5455
```

## Support

**Logged as**: Decision #112
**Task Breakdown**: 11 tasks in ConPort TaskOrchestrator category
**Documentation**: This README

For issues, check validation output and consult Decision #112 rationale.
