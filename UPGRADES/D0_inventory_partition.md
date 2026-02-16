# Phase D: Docs Pipeline Prompts (P0–P5)

## D0: Inventory + Partition Plan

Output files
	•	DOC_INVENTORY.json
	•	PARTITION_PLAN.json

ROLE: Mechanical indexer. No reasoning. JSON only. ASCII only.

TARGET ROOT: dopemux-mvp repo working tree.

SCOPE:
- docs/**/*.md
- docs/**/*.txt

OUTPUT 1: DOC_INVENTORY.json
For each doc:
- path
- size_bytes
- last_modified (if available)
- sha256 (if available)
- line_count_estimate (if available)
- is_archive=true if path starts with docs/archive/ OR docs/04-explanation/archive/
- is_evidence=true if path contains "/_evidence/" OR "/_handoff/" OR "/_opus_inputs/"
- title: first H1 if present (scan first 120 lines only)
- has_code_fences=true if "```" appears (scan first 300 lines only)

OUTPUT 2: PARTITION_PLAN.json
Create deterministic partitions by folder groups:
P2_CORE_ARCH =
  docs/spec/** +
  docs/architecture/** +
  docs/90-adr/** +
  docs/91-rfc/** +
  docs/systems/**

P3_PLANES_ACTIVE =
  docs/planes/** excluding any "/_evidence/" "/_handoff/" "/_opus_inputs/"

P4_PLANES_EVIDENCE =
  docs/planes/**/_evidence/** +
  docs/planes/**/_handoff/** +
  docs/planes/**/_opus_inputs/**

P5_TASK_PACKETS_PM_INV =
  docs/task-packets/** +
  docs/pm/** +
  docs/investigations/**

P6_DIATAXIS =
  docs/01-tutorials/** +
  docs/02-how-to/** +
  docs/03-reference/** +
  docs/04-explanation/** excluding docs/04-explanation/archive/**

P7_MISC =
  docs/api/** +
  docs/projects/** +
  docs/best-practices/** +
  docs/troubleshooting/** +
  docs/05-audit-reports/** +
  docs/06-research/**

P8_ARCHIVE =
  docs/archive/** +
  docs/04-explanation/archive/**

RULE:
If any partition has > 30 docs, split into subpartitions of 20 docs each,
named like P2_CORE_ARCH__01, P2_CORE_ARCH__02, etc.
Order docs within each partition by path ascending.

RULES:
- Do not read full docs here.
- JSON only.
- Deterministic ordering.
