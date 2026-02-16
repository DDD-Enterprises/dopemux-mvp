---
id: COMPREHENSIVE_SET
title: Comprehensive Set
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-16'
last_review: '2026-02-16'
next_review: '2026-05-17'
prelude: Comprehensive Set (explanation) for dopemux documentation and developer workflows.
---
# Dopemux Opus Evidence Bundle: Comprehensive Set

Bundle root:
`docs/planes/pm/dopemux/_opus_inputs/bundle_20260213`

## Included artifacts

### Bundle meta (1)
- `COMPREHENSIVE_SET.md`

### Core evidence bundle (13)
- `00_BUNDLE_INDEX.md`
- `01_GLOBAL_SERVICE_INVENTORY.md`
- `02_TOPOLOGY_AND_STORES.md`
- `03_STORE_WRITE_OWNERSHIP_MATRIX.md`
- `04_EVENT_ENVELOPE_STREAMS_AND_SCHEMA.md`
- `05_CONPORT_AUTHORITY_SURFACES.md`
- `06_DOPE_MEMORY_PROMOTION_RETENTION_PROVENANCE.md`
- `07_PM_PLANE_BYPASS_AND_EXECUTION_SURFACES.md`
- `08_ADHD_COGNITIVE_PLANE_SURFACES.md`
- `09_SEARCH_PLANE_SURFACES.md`
- `10_DETERMINISM_LEAKS_AND_ENFORCEMENT_POINTS.md`
- `11_UNKNOWNs_AND_REQUIRED_EVIDENCE.md`
- `12_OPUS_PROMPTS_READY.md`

### PM doc snapshot used in validation context (6)
- `pm_docs_snapshot/01_SYSTEM_ARCHITECTURE.md`
- `pm_docs_snapshot/02_MEMORY_AND_STATE.md`
- `pm_docs_snapshot/04_ROUTING_POLICY_AND_COST.md`
- `pm_docs_snapshot/05_ADHD_EXECUTION_MODEL.md`
- `pm_docs_snapshot/08_SUPERVISOR_PACKET_FORMAT.md`
- `pm_docs_snapshot/09_USAGE_LIMITS_AND_RESETS.md`

Total artifacts in this comprehensive set: `20` (`19` evidence artifacts + `1` bundle manifest)

## Sanity checks
- `python3 scripts/doc_gate.py`
- `rg --files docs/planes/pm/dopemux/_opus_inputs/bundle_20260213 | sort`
- `rg -o "docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/[A-Za-z0-9_./-]+\\.md" docs/planes/pm/dopemux/_opus_inputs/bundle_20260213/12_OPUS_PROMPTS_READY.md | sort -u`

Latest run status:
- Doc gate: `PASS`
- Bundle file count: `20`
- Prompt reference existence check: `ALL_PROMPT_REFERENCES_EXIST`
