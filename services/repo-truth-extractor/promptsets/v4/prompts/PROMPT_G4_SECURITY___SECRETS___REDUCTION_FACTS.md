# PROMPT_G4

## Goal
Produce `G4` outputs for phase `G` with strict schema, explicit evidence, and deterministic normalization.
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
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `GOV_SECRETS_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `GOV_SECRETS_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G4`
    - `id_rule`: `GOV_SECRETS_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, component, symbol, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

## Extraction Procedure
1. Scan for secret storage patterns: `.env` files, `*.env.*` variants, credential configuration files, key stores, and vault references. Record the path patterns and loading mechanisms only (never actual secret values). Evidence must cite the file and line range of the storage reference.
2. Extract secrets reduction facts: mechanisms that minimize secret exposure, including environment variable injection at runtime (compose `env_file`), secret rotation scripts, credential helper configurations, and vault integration patterns. Record each mechanism with evidence.
3. Identify secret scanning configurations: `.gitleaks.toml`, `trufflehog` configs, GitHub secret scanning settings, and pre-commit hooks that detect leaked secrets. Record the tool, patterns scanned, and enforcement location.
4. Cross-reference discovered secret patterns against upstream `SECRETS_RISK_LOCATIONS.json` to validate coverage: every secret risk location should have a corresponding reduction mechanism or a `status: unmitigated` flag.
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
- Secret value accidentally appears in a non-secret file (e.g., hardcoded in source): do NOT emit the secret value; emit only the file path, line range, and `status: hardcoded_secret_detected` with a redacted excerpt.
- Secret management uses an external vault service with no local configuration: emit with `storage_type: external_vault` and `config: UNKNOWN` with `missing_evidence_reason: external_service`.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT_G4 — SECURITY / SECRETS / REDUCTION FACTS

TASK: Extract security and secrets reduction facts.

RULE: No secret contents; extract paths + patterns + loaders only.

OUTPUTS:
	•	GOV_SECRETS_SURFACE.json
```
