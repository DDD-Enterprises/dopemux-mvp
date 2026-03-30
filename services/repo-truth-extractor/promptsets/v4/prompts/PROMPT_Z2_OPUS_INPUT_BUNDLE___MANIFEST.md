# PROMPT_Z2

## Goal
Produce `Z2` outputs for phase `Z` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `OPUS_INPUT_MANIFEST.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `OPUS_INPUT_MANIFEST.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `Z2`
    - `id_rule`: `OPUS_INPUT_MANIFEST:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, artifact_name, sha256, writer_step_id, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all finalized extraction artifacts as input for opus input bundle and manifest
2. Compute checksums and integrity metadata for OPUS_INPUT_BUNDLE
3. Build OPUS_INPUT_BUNDLE: compile all required components with provenance tracking
4. Validate completeness: verify all expected artifacts are present and checksums match
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
# PROMPT_Z2 — OPUS INPUT BUNDLE / MANIFEST

TASK: Generate a deterministic export bundle manifest for Opus + Codex.

OUTPUTS:
	•	OPUS_INPUT_MANIFEST.json
```
