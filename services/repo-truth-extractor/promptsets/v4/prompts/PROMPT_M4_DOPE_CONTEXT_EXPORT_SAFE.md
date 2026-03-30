# PROMPT_M4

## Goal
Produce `M4` outputs for phase `M` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `services/**`
- `docker/**`
- `extraction/**`
- Upstream normalized artifacts available to this step:
- `M0_RUNTIME_EXPORT_INVENTORY.json`
- `M1_SQLITE_SCHEMA_SNAPSHOTS.json`
- `M2_SQLITE_TABLE_COUNTS.json`
- `M3_CONPORT_EXPORT_SAFE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `M4_DOPE_CONTEXT_EXPORT_SAFE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `M4_DOPE_CONTEXT_EXPORT_SAFE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `M4`
    - `id_rule`: `M4_DOPE_CONTEXT_EXPORT_SAFE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load runtime state and configuration as input for dope context export (safe)
2. Extract dope context export (safe) data: query live state, sanitize sensitive values, and capture metadata
3. Build DOPE_CONTEXT_EXPORT: compile extracted data with timestamps and provenance
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
Goal: M4_DOPE_CONTEXT_EXPORT_SAFE.json

Prompt:
- Task: produce a safe dope-context runtime export summary using M0/M1/M2 and config references.
- Include:
  - schema summary references
  - table count references
  - config surface references (path + key names only)
  - implementer metadata: implementer="GPT-5.3-Codex", authority="Codex CLI/Desktop"
- Hard rules:
  - Redact all values; keep key names only.
  - Hash stable identifiers as sha256(value)[:12].
  - Never include raw memory/chat/content fields.
```
