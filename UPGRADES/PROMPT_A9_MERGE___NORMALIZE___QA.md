# PHASE A9 — MERGE + NORMALIZE + QA SPEC (PHASE A)
Model: Gemini Flash 3
Goal: Produce A_MERGE_NORMALIZE_QA_SPEC.json

Hard rules:
- This prompt does not “extract repo truth”.
- It outputs a deterministic spec for:
  - how to merge A raw partition outputs into A norm artifacts
  - what QA checks to run on A outputs
- Evidence: cite only the observed file naming patterns and partitioning metadata if present.

Task:
A_MERGE_NORMALIZE_QA_SPEC.json must define:
- required_outputs[] (names: REPO_INVENTORY.json, REPO_PARTITIONS.json, etc.)
- merge_rules[]:
  - target_artifact
  - source_globs
  - dedupe_key (e.g., path+field)
  - stable_sort (fields)
- qa_checks[]:
  - check_id, description, failure_condition
  Examples:
  - "no_empty_services_in_compose_graph"
  - "no_duplicate_server_ids"
  - "all instruction_sources have evidence"
- redaction_rules[] (env var values, tokens, api keys)
