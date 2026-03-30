# PROMPT_W2

## Goal
Produce `W2` outputs for phase `W` with strict schema, explicit evidence, and deterministic normalization.
Focus on executable workflows, runbooks, and multi-service coordination boundaries.

## Inputs
- Source scope (scan these roots first):
- `scripts/**`
- `services/**`
- `docs/02-how-to/**`
- `docs/03-reference/**`
- `compose.yml`
- Upstream normalized artifacts available to this step:
- `WORKFLOW_INVENTORY.json`
- `WORKFLOW_PARTITIONS.json`
- `WORKFLOW_CATALOG.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOW_IO_MAP.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOW_IO_MAP.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W2`
    - `id_rule`: `WORKFLOW_IO_MAP:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the workflow inputs/outputs/artifacts partition as primary scan surface.
2. Identify workflow inputs: search for `argparse`, `sys.argv`, `os.getenv`, or `input()` calls in scripts, and environment variable requirements in `compose.yml`.
3. Locate artifact production (outputs): search for `open('...', 'w')`, `.to_csv()`, `json.dump()`, or shell redirection `> log.txt` patterns that create persistent files.
4. Scan for data transformation steps: identify code that reads a file (`input`), processes it, and writes a new file (`artifact`).
5. Map artifact locations: identify standard output directories like `out/`, `reports/`, `logs/`, and `proof/`.
6. Identify network and side-effect outputs: search for `requests.*`, `httpx.*`, or database write operations (cross-reference with C3).
7. Build relationship graph: trace the flow of data from inputs to transformation logic and final artifact production.
8. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in workflow I/O mapping.
9. For each WORKFLOW_IO_MAP item, populate `id`, required fields, and `evidence`.
10. Legacy Context is intent guidance only and is never evidence.
11. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
12. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
13. Attach evidence to every non-derived field and every relationship edge.
14. Normalize arrays by stable sort keys; deduplicate by ID.
15. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
16. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_W2 — WORKFLOW INPUTS / OUTPUTS / ARTIFACTS

TASK: Extract workflow I/O and artifact production.

OUTPUTS:
	•	WORKFLOW_IO_MAP.json
```
