# PROMPT_X0_FEATURE_INDEX_INVENTORY___PARTITION_PLAN

TASK: Build feature-index inventory and deterministic partition plan.

SCAN TARGETS:
- services/
- src/
- docs/
- config/
- scripts/
- Makefile
- docker-compose*.yml

OUTPUTS:
- FEATURE_INDEX_INVENTORY.json
- FEATURE_INDEX_PARTITIONS.json

RULES:
- Enumerate candidate feature surfaces, owning code paths, and related docs.
- Partition deterministically for downstream X1 extraction.
- Preserve literal evidence and source paths.
