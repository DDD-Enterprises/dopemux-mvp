# PROMPT_M0

## Goal
Produce `M0` outputs for phase `M` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `services/**`
- `docker/**`
- `extraction/**`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `M0_RUNTIME_EXPORT_INVENTORY.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `M0_RUNTIME_EXPORT_INVENTORY.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `M0`
    - `id_rule`: `M0_RUNTIME_EXPORT_INVENTORY:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, path, kind, summary, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load runtime state and configuration as input for runtime export inventory
2. Extract runtime export inventory data: query live state, sanitize sensitive values, and capture metadata
3. Build RUNTIME_EXPORT_INVENTORY: compile extracted data with timestamps and provenance
4. Validate export safety: ensure no secrets or sensitive data in output; redact if found
5. For each output item, populate `id`, required fields, and `evidence` per schema contracts
6. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: M0_RUNTIME_EXPORT_INVENTORY.json

Prompt:
- Task: detect runtime stores and config surfaces only within allowlisted home roots:
  - ~/.dopemux/**
  - ~/.config/dopemux/**
  - ~/.config/taskx/**
  - ~/.config/litellm/**
  - ~/.config/mcp/**
- Identify likely state stores: *.sqlite, *.sqlite3, *.db, context.db, global_index.sqlite.
- Output fields must include for each path:
  - path, size, mtime, classification (sqlite_db|config|cache|unknown), exportability (ok|permission_denied|missing_tool|unsafe).
- Hard rules:
  - No full file content dumps.
  - If caps are hit, emit TRUNCATED marker and counts.
  - Do not include secrets, tokens, or raw message content.
```
