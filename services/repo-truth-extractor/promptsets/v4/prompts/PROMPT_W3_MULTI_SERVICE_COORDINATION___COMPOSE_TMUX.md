# PROMPT_W3

## Goal
Produce `W3` outputs for phase `W` with strict schema, explicit evidence, and deterministic normalization.
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
- `WORKFLOW_IO_MAP.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `WORKFLOW_COORDINATION_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `WORKFLOW_COORDINATION_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `W3`
    - `id_rule`: `WORKFLOW_COORDINATION_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load upstream inventory and partitions; use the multi-service coordination (compose/tmux) partition as primary scan surface.
2. Map Docker Compose coordination: scan `compose.yml` for `depends_on`, `healthcheck`, `networks`, and `volumes` that define service inter-dependencies.
3. Map TMUX coordination: scan `tmux.conf` or `*.tmux.yaml` for session layouts, window names, and specific commands sent to panes via `send-keys`.
4. Identify synchronization points: search for `wait-for-it.sh`, `nc -z`, or health-check polling loops that block service startup until dependencies are ready.
5. Locate global orchestrator logic: identify scripts like `dopemux.rb` or `install.sh` that trigger both Compose and TMUX setup in sequence.
6. Build coordination graph: trace how a single orchestrator command propagates through TMUX panes to eventually start Docker Compose services.
7. Cross-reference with upstream artifacts to identify overrides, shadows, and conflicts in service coordination.
8. For each WORKFLOW_COORDINATION_SURFACE item, populate `id`, required fields, and `evidence`.
9. Legacy Context is intent guidance only and is never evidence.
10. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
11. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
12. Attach evidence to every non-derived field and every relationship edge.
13. Normalize arrays by stable sort keys; deduplicate by ID.
14. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
15. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_W3 — MULTI-SERVICE COORDINATION / COMPOSE / TMUX

TASK: Tie compose + tmux + scripts into a coordination view.

OUTPUTS:
	•	WORKFLOW_COORDINATION_SURFACE.json
```
