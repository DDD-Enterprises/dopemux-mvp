# PROMPT_T1

## Goal
Produce `T1` outputs for phase `T` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `services/repo-truth-extractor/**`
- `docs/90-adr/**`
- `docs/05-audit-reports/**`
- Upstream normalized artifacts available to this step:
- `PROJECT_INSTRUCTIONS.md`
- `TP_BACKLOG_TOPN.json`
- `TP_INDEX.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TP_PACKETS_TOP10.partX.md`
- `TP_PACKET_IMPLEMENTATION_INDEX.json`
- `TP_BACKLOG_TOPN.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `TP_PACKETS_TOP10.partX.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `T1`
    - `id_rule`: `TP_PACKETS_TOP10:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `TP_PACKET_IMPLEMENTATION_INDEX.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T1`
    - `id_rule`: `TP_PACKET_IMPLEMENTATION_INDEX:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, name, path, kind, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `TP_BACKLOG_TOPN.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `T9`
    - `id_rule`: `TP_BACKLOG_TOPN:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all upstream extraction artifacts and synthesis reports as input for top-10 task packet emission
2. Analyze extraction outputs to identify actionable work items for TASK_PACKETS_TOP10
3. For each task packet, determine scope, priority, dependencies, and acceptance criteria from evidence
4. Validate packet completeness: ensure each packet has sufficient context for execution
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
MODE: Arbitration output only. Do not implement code.
EVIDENCE REQUIRED: Every load-bearing claim must map to authority input paths.
OUTPUT: Markdown packets plus JSON index.
STABLE ORDER: Sort packets by priority, then tp_id.
CHUNKING: If output would exceed context, emit PART files and a CAP_NOTICES file.

# Phase T1: Emit Task Packets (Top 10)

Outputs:
- TP_PACKETS_TOP10.partX.md
- TP_PACKET_IMPLEMENTATION_INDEX.json

Prompt:
ROLE: GPT-5.2 (arbitration).
Inputs:
- TP_BACKLOG_TOPN.json
- R norm artifact paths referenced by each backlog item

Action:
Generate complete Task Packet markdowns for the top 10 items in the backlog.
Each packet must be implementation-ready for Codex Desktop and must not relitigate truth.

Required packet header block (exact keys):
- Implementer: Codex Desktop (GPT-5.3-Codex)
- Authority Inputs: <list of R/X norm artifact paths>
- Forbidden: re-run extraction; reinterpret truth without new evidence
- Required Proofs: git diff --stat, tests run, acceptance checks, rollback verification

Required sections per packet:
- Objective
- Scope (IN / OUT)
- Invariants
- Plan
- Exact commands
- Acceptance criteria
- Rollback
- Stop conditions

Required schema keys for TP_PACKET_IMPLEMENTATION_INDEX.json:
- run_id
- generated_at
- packet_count
- packets (array)
- packets[].tp_id
- packets[].title
- packets[].implementer_target
- packets[].authority_inputs
- packets[].packet_markdown_locator
```
