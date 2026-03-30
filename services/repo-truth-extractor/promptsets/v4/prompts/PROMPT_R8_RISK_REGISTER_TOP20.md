# PROMPT_R8

## Goal
Produce `R8` outputs for phase `R` with strict schema, explicit evidence, and deterministic normalization.
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
- `CONFLICT_LEDGER.md`
- `CODE_HEALTH_SURFACE.json`
- `DEAD_CODE_INVENTORY.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `RISK_REGISTER_TOP20.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `RISK_REGISTER_TOP20.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `R8`
    - `id_rule`: `RISK_REGISTER_TOP20:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk, severity, location, evidence`

## Extraction Procedure
1. Load Phase R6 (Portability Risks), R7 (Conflicts), B (Boundaries), and C (Code Health/Dead Code) artifacts.
2. Extract **Quality Risks**: Pull from `CODE_HEALTH_SURFACE.json` (complexity) and `DEAD_CODE_INVENTORY.json`.
3. Extract **Integrity Risks**: Identify non-deterministic logic, concurrency issues, or idempotency failures from Phase C8 scans.
4. Extract **Security Risks**: Map boundary bypasses identified in Phase R3 (Trinity) or B3 (Bypass Paths).
5. Perform **Severity Ranking**: Assign risk levels (Critical/High/Medium/Low) based on evidence impact.
6. Output Format: List Top-20 risks with `ID | Risk | Severity | Location | Evidence`.
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
Goal: RISK_REGISTER_TOP20.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce top-20 risk register.

MUST INCLUDE:
- Determinism/idempotency/concurrency risks
- Boundary bypass risks
- Code quality risks (high-complexity hotspots, dead code, missing error handling from CODE_HEALTH_SURFACE and DEAD_CODE_INVENTORY)
- Severity ranking with evidence
- Minimal mechanical bounding mechanisms

RULES:
- Cite every risk item.
- No large refactor recommendations.
```
