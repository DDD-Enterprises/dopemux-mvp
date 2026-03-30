# PROMPT_R5

## Goal
Produce `R5` outputs for phase `R` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOWS_TRUTH_GRAPH.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOWS_TRUTH_GRAPH.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `R5`
    - `id_rule`: `WORKFLOWS_TRUTH_GRAPH:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `nodes, edges, schema`

## Extraction Procedure
1. Load Phase A, C, and W (Workflow) artifacts, specifically `WORKFLOW_RUNNER_SURFACE.json`, `HOME_TMUX_WORKFLOW_SURFACE.json`, and `COMPOSE_SERVICE_GRAPH.json`.
2. Map **Bootstrap Flows**: Identify how the system starts via Tmux, Docker Compose, or standalone scripts from Phase A/W.
3. Trace **Multi-Service Workflows**: Connect services into a dependency graph, identifying order of execution and state triggers.
4. Extract **I/O & Artifacts**: Identify explicit file inputs, outputs, and intermediate artifacts for each workflow step.
5. Identify **Instruction-Driven Steps**: Map how `.md` or `.json` instruction files drive specific runner behaviors (Phase W).
6. Arbitration: Resolve conflicts between `W` (Workflow Inventory) and `C` (Code Implementation) by prioritizing evidenced code paths.
7. Output Format: Produce a Markdown graph with nodes (steps/services) and edges (triggers/dependencies), plus a list of workflows (W1..Wn) with literal citations.
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
Goal: WORKFLOWS_TRUTH_GRAPH.md

ROLE: Supervisor/Auditor.
HARD RULE: Reason only from normalized A/H/D/C artifacts.

TASK:
Produce workflow truth graph.

MUST INCLUDE:
- Bootstrap flows (tmux, compose, scripts)
- Multi-service workflows with order/dependencies
- Inputs/outputs/artifacts where explicit
- Instruction-file-driven workflow steps

OUTPUT:
- Workflow list (W1..Wn) with literal steps + citations
- Services involved per workflow
- UNKNOWN markers where evidence is missing

RULES:
- No inferred steps.
- Use WORKFLOW_RUNNER_SURFACE + HOME_TMUX_WORKFLOW_SURFACE + compose graph evidence.
```
