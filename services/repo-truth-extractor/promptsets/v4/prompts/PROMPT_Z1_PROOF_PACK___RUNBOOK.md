# PROMPT_Z1

## Goal
Produce the `Z1` proof-pack output for phase `Z` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable freeze evidence and proof-pack assembly facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- `FREEZE_FILE_INDEX.json`
- `FREEZE_CHECKSUMS.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `PROOF_PACK.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `PROOF_PACK.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `Z1`
    - `id_rule`: `PROOF_PACK:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`

## Extraction Procedure
1. Load all finalized freeze artifacts required to assemble `PROOF_PACK.md`.
2. Compute or verify proof-pack integrity metadata from the supplied freeze inputs.
3. Build `PROOF_PACK.md` as the single declared output with provenance tracking for each required section.
4. Validate completeness: verify all expected proof-pack inputs are present and note any missing components explicitly in the output.
5. For each load-bearing section, attach evidence per the schema contract above.
6. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared output and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_Z1 — PROOF PACK

TASK: Generate a proof pack snapshot.

OUTPUTS:
	•	PROOF_PACK.md
```
