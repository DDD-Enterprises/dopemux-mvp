# PROMPT_R3

## Goal
Produce `R3` outputs for phase `R` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `R3`
    - `id_rule`: `TRINITY_BOUNDARY_ENFORCEMENT_TRA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`

## Extraction Procedure
1. Load Phase A, B, C, and D artifacts, focusing on `TRINITY_BOUNDARY_ENFORCEMENT_SURFACES.json`.
2. Trace **Enforcement Points**: Identify exact symbols/files where boundary checks (FastAPI `Depends`, etc.) are implemented.
3. Map **Refusal Rails**: Trace how authorization failures propagate to the user/caller.
4. Identify **Bypass Paths**: Document any evidenced routes that circumvent boundary checks.
5. Arbitration: Explicitly separate IMPLEMENTED checks (Phase C) from PLANNED rules (Phase D).
6. Output Format: 1) Boundary list with enforcement status, 2) Guardrail pipeline diagram (text), 3) Bypass risks.
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
Goal: TRINITY_BOUNDARY_ENFORCEMENT_TRACE.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce boundary enforcement trace.

MUST INCLUDE:
- Evidenced boundaries only
- Enforcement points (exact symbols/files)
- Refusal rails and propagation paths
- Bypass paths only when evidenced

OUTPUT:
- Boundary list with enforcement checks
- Guardrail pipeline diagram (text)
- Known bypass risks with evidence

RULES:
- Separate IMPLEMENTED checks from PLANNED doc rules.
- Do not invent boundaries.
```
