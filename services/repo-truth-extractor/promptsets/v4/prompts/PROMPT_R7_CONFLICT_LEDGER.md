# PROMPT_R7

## Goal
Produce `R7` outputs for phase `R` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**/norm/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `CONTROL_PLANE_TRUTH_MAP.md`
- `DOPE_MEMORY_IMPLEMENTATION_TRUTH.md`
- `DOPE_MEMORY_SCHEMAS.json`
- `DOPE_MEMORY_DB_WRITES.json`
- `EVENTBUS_WIRING_TRUTH.md`
- `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`
- `TASKX_INTEGRATION_TRUTH.md`
- `WORKFLOWS_TRUTH_GRAPH.md`
- `PORTABILITY_AND_MIGRATION_RISK_LEDGER.md`
- `CODE_HEALTH_SURFACE.json`
- `DEAD_CODE_INVENTORY.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `CONFLICT_LEDGER.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `CONFLICT_LEDGER.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `R7`
    - `id_rule`: `CONFLICT_LEDGER:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`

## Extraction Procedure
1. Load Phase D (Docs), Phase C (Code), and Phase A (Architecture) artifacts from upstream norm results.
2. Identify **Doc-vs-Code Conflicts**: Compare architectural claims in `docs/**/*.md` against actual implementations in Phase C artifacts.
3. Identify **Doc-vs-Doc Conflicts**: Scan for contradictory statements within documentation files (Phase D).
4. Apply **Arbitration Rules**:
    - Code (Phase C) always overrides Documentation (Phase D).
    - For Doc-vs-Doc, apply `DOC_SUPERSESSION` logic (newer/higher-authority docs win).
5. Document **Authority Decisions**: Explicitly state which source was chosen as "truth" and why, citing both sides.
6. Output Format: List each conflict with "Side A", "Side B", "Resolution", and "Rationale", citing evidence for all claims.
7. Legacy Context is intent guidance only and is never evidence.
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
Goal: CONFLICT_LEDGER.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce conflict ledger across docs/code/control planes.

MUST INCLUDE:
- doc claim vs code truth
- doc vs doc conflicts
- authority decisions using evidence hierarchy

RULES:
- Use DOC_SUPERSESSION first, then recency tie-breaker for doc-vs-doc only.
- Never override code reality with docs.
- Cite both sides for each conflict.
```
