# PROMPT_B3

## Goal
Produce `B3` outputs for phase `B` with strict schema, explicit evidence, and deterministic normalization.
Focus on boundary enforcement points, refusal rails, and concrete bypass evidence.

## Inputs
- Source scope (scan these roots first):
- `src/**`
- `services/**`
- `docs/90-adr/**`
- `.claude/**`
- `AGENTS.md`
- Upstream normalized artifacts available to this step:
- `BOUNDARY_INVENTORY.json`
- `BOUNDARY_PARTITIONS.json`
- `BOUNDARY_ENFORCEMENT_POINTS.json`
- `REFUSAL_GUARDRAILS_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `BOUNDARY_BYPASS_RISKS.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `BOUNDARY_BYPASS_RISKS.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `B3`
    - `id_rule`: `BOUNDARY_BYPASS_RISKS:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, risk, severity, location, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load `BOUNDARY_ENFORCEMENT_POINTS.json` and `REFUSAL_GUARDRAILS_SURFACE.json`.
2. Identify **Weak Guards**: Locate checks that can be circumvented via `DEBUG=True`, `SKIP_AUTH=1`, or missing `Depends()` on sensitive sub-routes.
3. Trace **Bypass Paths**: Document evidenced routes that allow unauthorized access to sensitive data without triggering refusal rails.
4. Check **Permission Leaks**: Verify if `.claude/settings.json` allows tools to access files or perform actions outside their declared scope.
5. Arbitration: Only report bypasses evidenced by an alternate code path or a missing check near a sensitive operation.
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
# PROMPT_B3 — BYPASS PATHS / WEAK GUARDS

TASK: Identify bypass paths and weak guards.

RULE: only report bypass when evidenced by an alternate path or missing check near a sensitive operation.

OUTPUTS:
	•	BOUNDARY_BYPASS_RISKS.json
```
