# PROMPT_C0 - CODE INVENTORY + PARTITION PLAN

GOAL:
- Build deterministic code inventory and partition plan artifacts.

OUTPUTS:
- CODE_INVENTORY.json
- CODE_PARTITIONS.json

INPUT SCOPE:
- services/**
- src/**
- shared/**
- scripts/**
- tools/**
- compose.yml
- docker-compose*.yml
- services/registry.yaml

EXTRACTION PROCEDURE:
1) Scan in-scope sources and collect candidate code artifacts with path and type metadata.
2) Classify each artifact into a subsystem category using direct evidence from code or config.
3) Build CODE_PARTITIONS by grouping artifacts into stable partition buckets with explicit rationale.
4) For each CODE_INVENTORY item, populate id/path/kind/summary/evidence.
5) For each CODE_PARTITIONS item, populate id/partition_id/files/reason/evidence.
6) Enumerate candidate facts only from in-scope files and provided runner context.
7) Build deterministic IDs from stable keys (path, symbol, service name).
8) Attach evidence for every non-trivial field.
9) Sort arrays deterministically and deduplicate by stable IDs.
10) Emit only declared outputs.

PARTITION HINTS:
- services/** entrypoints
- shared/**
- src/**
- workflow scripts
- eventbus modules
- dope-memory modules
- boundary/guardrail modules
- taskx bridges
