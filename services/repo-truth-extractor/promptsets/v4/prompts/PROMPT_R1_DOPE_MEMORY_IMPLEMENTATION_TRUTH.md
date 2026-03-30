# PROMPT_R1

## Goal
Produce `R1` outputs for phase `R` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**/norm/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `CONTROL_PLANE_TRUTH_MAP.md`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
- `DOPE_MEMORY_SCHEMAS.json`
- `DOPE_MEMORY_DB_WRITES.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `R1`
    - `id_rule`: `DOPE_MEMORY_IMPLEMENTATION_TRUTH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `DOPE_MEMORY_SCHEMAS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `R1`
    - `id_rule`: `DOPE_MEMORY_SCHEMAS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `DOPE_MEMORY_DB_WRITES.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `R1`
    - `id_rule`: `DOPE_MEMORY_DB_WRITES:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load `DOPE_MEMORY_SCHEMAS.json`, `DOPE_MEMORY_DB_WRITES.json`, and Phase A/H/C/D artifacts.
2. Inventory **Memory Adapters**: Identify SQLite/Postgres usage and connection logic from Phase C.
3. Map **Schemas & Writes**: Align `DOPE_MEMORY_SCHEMAS.json` and `DOPE_MEMORY_DB_WRITES.json` to code symbols in Phase C.
4. Trace **Retention/TTL**: Locate data expiration logic in `C` or `A` phases.
5. Map **Control-Plane Links**: Bind memory configurations to env vars or Compose wiring from Phase A.
6. Arbitration: Resolve intent conflicts via Phase D `DOC_SUPERSESSION`; if implementation differs from docs, mark as `GAPS/CONFLICTS`.
7. Output Format: Organize by 1) IMPLEMENTED (CODE), 2) PLANNED (DOC), 3) GAPS/CONFLICTS.
8. Legacy Context is intent guidance only and is never evidence.
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
Goal: DOPE_MEMORY_IMPLEMENTATION_TRUTH.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce memory implementation truth for current system behavior.

MUST INCLUDE:
- Stores/adapters (sqlite/postgres/other)
- Schema objects from DOPE_MEMORY_SCHEMAS.json
- Write paths from DOPE_MEMORY_DB_WRITES.json
- Retention/TTL enforcement points
- Replay/re-derive surfaces (if present)
- Control-plane dependencies (env vars, compose wiring, home DBs)

FORMAT:
1) IMPLEMENTED (CODE evidence)
2) PLANNED (DOC evidence)
3) GAPS/CONFLICTS (both sides cited)
4) Minimal verification command suggestions

RULES:
- Cite statements for tables/triggers/enforcement points.
- If docs conflict, use DOC_SUPERSESSION then recency tie-breaker.
```
