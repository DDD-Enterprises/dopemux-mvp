# PROMPT_G9

## Goal
Produce `G9` outputs for phase `G` with strict schema, explicit evidence, and deterministic normalization.
Focus on CI gates, policy enforcement, and governance drift risks.

## Inputs
- Source scope (scan these roots first):
- `.github/workflows/**`
- `pyproject.toml`
- `scripts/**`
- `config/**`
- `docs/90-adr/**`
- Upstream normalized artifacts available to this step:
- `GOV_INVENTORY.json`
- `GOV_PARTITIONS.json`
- `GOV_CI_GATES.json`
- `GOV_HYGIENE_POLICIES.json`
- `GOV_POLICIES.json`
- `GOV_SECRETS_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `GOV_MERGED.json`
- `GOV_QA.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `GOV_MERGED.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G9`
    - `id_rule`: `GOV_MERGED:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence, path, line_range`
    - `required_registry_fields`: `path, line_range, id`
  - `GOV_QA.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G9`
    - `id_rule`: `GOV_QA:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, status, checks, issues, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Load all upstream G-phase artifacts (`GOV_INVENTORY.json`, `GOV_PARTITIONS.json`, `GOV_CI_GATES.json`, `GOV_HYGIENE_POLICIES.json`, `GOV_POLICIES.json`, `GOV_SECRETS_SURFACE.json`). Validate each against its declared schema contract.
2. Merge all governance artifacts into `GOV_MERGED.json` using `itemlist_by_id` merge strategy with deterministic conflict resolution. Normalize arrays by stable sort keys.
3. Generate `GOV_QA.json` with coverage checks: all governance files inventoried, all partitions produced output, no missing expected artifacts, and cross-artifact consistency (every CI gate references an existing governance file).
4. Flag governance gaps: policies without enforcement, CI gates without corresponding policy documentation, and secrets patterns without reduction mechanisms. Aggregate into a `governance_gaps` section in QA output.
5. Legacy Context is intent guidance only and is never evidence.
6. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
7. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
8. Attach evidence to every non-derived field and every relationship edge.
9. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
10. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
11. Emit exactly the declared outputs and no additional files.

## Evidence Rules
- Every load-bearing value must carry at least one evidence object:
```json
{
  "path": "<repo-relative-path>",
  "line_range": [<start>, <end>],
  "excerpt": "<exact substring <=200 chars>"
}
```
- `path` must be repo-relative (never absolute in norm artifacts).
- `excerpt` must be exact (no paraphrase) and <= 200 chars.
- If the source is ambiguous, include multiple evidence objects and set value to `UNKNOWN`.

## Determinism Rules
- Norm outputs MUST NOT contain: `generated_at`, `timestamp`, `created_at`, `updated_at`, `run_id`.
- Sort `items` by `(path, line_start, id)` when available; otherwise by `id` then stable JSON text.
- Merge duplicates deterministically:
  - union evidence by `(path,line_range,excerpt)`
  - union arrays with stable sort
  - choose scalar conflicts by non-empty, else lexicographically smallest stable value
- Output byte content must be reproducible for same commit + same configuration.

## Anti-Fabrication Rules
- Do not invent endpoints, handlers, dependencies, env vars, commands, or policy claims.
- Do not infer intent from filenames alone; require direct textual/code evidence.
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- Upstream artifact missing entirely: include in `missing_expected_outputs` and set overall QA status to `incomplete`.
- Conflicting governance rules across different policy files: emit both with `status: conflicting_policies` and evidence from each source.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_G9 — Governance merge + QA

ROLE: Deterministic normalizer + QA bot.
GOAL: merge governance outputs and provide coverage/consistency checks.

OUTPUTS:
  • GOV_MERGED.json
  • GOV_QA.json

RULES:
  • Sort arrays stably and remove duplicates.
```
