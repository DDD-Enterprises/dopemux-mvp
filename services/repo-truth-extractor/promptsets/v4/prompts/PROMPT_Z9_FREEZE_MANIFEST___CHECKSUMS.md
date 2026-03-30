# PROMPT_Z9

## Goal
Produce `Z9` outputs for phase `Z` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `FREEZE_FILE_INDEX.json`
- `FREEZE_CHECKSUMS.json`
- `PROOF_PACK.md`
- `OPUS_INPUT_MANIFEST.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `FREEZE_MANIFEST.json`
- `FREEZE_README.md`
- `FREEZE_QA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `FREEZE_MANIFEST.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Z9`
    - `id_rule`: `FREEZE_MANIFEST:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, artifact_name, sha256, writer_step_id, evidence`
    - `required_registry_fields`: `path, line_range, id`
  - `FREEZE_README.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `Z9`
    - `id_rule`: `FREEZE_README:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`
  - `FREEZE_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Z9`
    - `id_rule`: `FREEZE_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all Z-Phase upstream artifacts; verify schema compliance, required fields, and sort order before merging
2. Merge all FREEZE_* artifacts into FREEZE_MANIFEST using `itemlist_by_id` strategy: union items by `id`, union evidence arrays, resolve scalar conflicts
3. Run QA checks: verify all Z-Phase artifacts present, coverage complete, sort order deterministic; emit FREEZE_CHECKSUMS
4. Cross-check coverage: verify every inventory item has corresponding extraction entries
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
# PROMPT_Z9 — FREEZE MANIFEST / CHECKSUMS

TASK: Produce a deterministic freeze handoff manifest with verification instructions and QA.

OUTPUTS:
- FREEZE_MANIFEST.json
- FREEZE_README.md
- FREEZE_QA.json

Rules:
- Include SHA-256 for every file in phase `norm/` and `qa/` outputs for A/H/D/C/E/W/B/G/Q/R/X/T/Z when present.
- Include prompt corpus fingerprint entries for active `services/repo-truth-extractor/prompts/v3/PROMPT_*.md` files.
- Record missing expected artifacts and failure counts by phase.
- `FREEZE_README.md` must document deterministic verification commands.
```
