---
id: DOC_PARTITION_PLAN
title: Doc Partition Plan
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-17'
last_review: '2026-02-17'
next_review: '2026-05-18'
prelude: Doc Partition Plan (explanation) for dopemux documentation and developer
  workflows.
---
# Documentation Partition Plan

**Generated:** 2026-02-15  
**Target:** `/Users/hue/code/dopemux-mvp`  
**Total Docs:** ~903 in primary docs/ + ~80 in services/quarantine/other

---

## Partition Strategy

Based on actual file counts, we create **12 balanced partitions** of ~20-35 files each.

### Partition Mapping

| Partition ID      | Scope                                                                                    | File Count | Bucket Hints                   |
| ----------------- | ---------------------------------------------------------------------------------------- | ---------- | ------------------------------ |
| **P001**          | `docs/01-tutorials/`, `docs/02-how-to/`                                                  | ~41        | E (tools), D (orchestrator)    |
| **P002**          | `docs/03-reference/`                                                                     | ~40        | E (mcp), C (authority)         |
| **P003**          | `docs/04-explanation/architecture/`, `docs/04-explanation/concepts/`                     | ~30        | C (trinity, plane, boundary)   |
| **P004**          | `docs/04-explanation/design-decisions/`, `docs/04-explanation/systems/`                  | ~25        | C (boundary), D (orchestrator) |
| **P005**          | `docs/04-explanation/technical-deep-dives/`, `docs/04-explanation/implementation-plans/` | ~31        | A (memory), B (event)          |
| **P006**          | `docs/05-audit-reports/`, `docs/06-research/`, `docs/investigations/`                    | ~92        | A (memory, chronicle)          |
| **P007**          | `docs/90-adr/`, `docs/architecture/`                                                     | ~25        | C (authority, boundary)        |
| **P008**          | `docs/planes/`, `docs/pm/`                                                               | ~56        | C (plane), A (memory)          |
| **P009**          | `docs/spec/`, `docs/task-packets/`, `docs/best-practices/`                               | ~21        | D (packet, router)             |
| **P010**          | `docs/systems/`                                                                          | ~52        | A, B, C, D, E (all systems)    |
| **P011**          | `docs/projects/`, `docs/api/`, `docs/troubleshooting/`                                   | ~5         | Mixed                          |
| **P-ARCHIVE-001** | `docs/archive/` (first 120 files alphabetically)                                         | 120        | Mixed                          |
| **P-ARCHIVE-002** | `docs/archive/` (next 120 files)                                                         | 120        | Mixed                          |
| **P-ARCHIVE-003** | `docs/archive/` (next 120 files)                                                         | 120        | Mixed                          |
| **P-ARCHIVE-004** | `docs/archive/` (remaining ~117 files)                                                   | 117        | Mixed                          |
| **P-SERVICES**    | `services/*/docs/`, `.claude/docs/`, `docker/mcp-servers/docs/`                          | ~57        | E (mcp, tools)                 |
| **P-QUARANTINE**  | `quarantine/2026-02-04/docs/**`, `_audit_out/**/*.md`                                    | ~2030      | Mixed (large, low priority)    |

---

## Priority Buckets (Token-Based)

Docs are tagged with bucket(s) based on token presence in title/headings:

- **Bucket A**: `memory`, `chronicle`, `sqlite`, `postgres`, `mirror`
- **Bucket B**: `event`, `taxonomy`, `envelope`, `bus`, `producer`, `consumer`
- **Bucket C**: `trinity`, `boundary`, `authority`, `plane`
- **Bucket D**: `taskx`, `orchestrator`, `packet`, `router`
- **Bucket E**: `mcp`, `tool`, `server`, `contract`
- **Bucket F**: `ranking`, `retrieval`, `redaction`, `promotion`

---

## Execution Order

### Phase 1: Core Architecture (High Priority)
Run these first:
1. P003 (architecture, concepts)
2. P007 (ADRs, architecture/)
3. P008 (planes, pm)
4. P002 (reference)

### Phase 2: Systems & Implementation
5. P004 (design-decisions, systems)
6. P005 (technical deep-dives, implementation-plans)
7. P010 (systems/)
8. P-SERVICES

### Phase 3: Audit & Research
9. P006 (audit-reports, research)
10. P001 (tutorials, how-to)
11. P009 (spec, task-packets)
12. P011 (projects, troubleshooting)

### Phase 4: Archive (Low Priority, High Volume)
13. P-ARCHIVE-001
14. P-ARCHIVE-002
15. P-ARCHIVE-003
16. P-ARCHIVE-004
17. P-QUARANTINE (optional - 2030 files, may defer)

---

## Partition Size Balance

| Size Range     | Count | Partition IDs                |
| -------------- | ----- | ---------------------------- |
| Huge (>100)    | 5     | P-ARCHIVE-*, P-QUARANTINE    |
| Large (50-100) | 3     | P006, P008, P010, P-SERVICES |
| Medium (20-50) | 7     | P001-P005, P007, P009        |
| Small (<20)    | 1     | P011                         |

---

## D1 Execution Plan

For each partition, run:
```bash
# Example for P001
flash run PROMPT_D1_NORMATIVE_EXTRACTION.md \
  --var PARTITION_ID=P001 \
  --input DOC_PARTITIONS.json \
  --output-dir ./extraction/d1/
```

Output files per partition:
- `DOC_INDEX.part001.json`
- `DOC_CLAIMS.part001.json`
- `DOC_BOUNDARIES.part001.json`
- `DOC_SUPERSESSION.part001.json`
- `CAP_NOTICES.part001.json`

---

## Expected CAP_NOTICES

Likely candidates for D2 deep extraction:
- All technical deep-dives (~10-15 docs)
- Large architecture docs (MEMORY_PLANE, TRINITY, etc.)
- Audit reports with extensive tables/code
- System design docs in `systems/`

Estimated: **40-60 docs** will hit CAP_NOTICES threshold.

---

## Archive Handling Strategy

**Option 1 (Recommended):** 
- Run D0 on archive to get inventory
- Run D1 on archive partitions to extract claims/boundaries
- **Skip D2** for archive (low ROI, high cost)
- Include in merge for completeness

**Option 2 (Defer):**
- Skip P-ARCHIVE-* entirely in first pass
- Mark as "deferred" in DOC_TODO_QUEUE
- Revisit if QA shows missing critical docs

**Option 3 (Quarantine Skip):**
- Skip P-QUARANTINE entirely (2030 files from 2026-02-04)
- These are archived/quarantined for a reason
- Focus on active docs first
