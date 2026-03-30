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
1. Load `GOV_INVENTORY.json` and relevant partitions from upstream.
2. Extract **Credential Reading Patterns**: Scan code for `os.environ`, `dotenv`, and Secret Manager API calls (symbols and paths only).
3. Identify **Hardcoded Risk**: Scan for potential hardcoded secrets or default credentials in configs and scripts (Patterns + Paths only).
4. Map **Secret Loaders**: Identify exact symbols/classes responsible for injecting secrets into the runtime environment.
5. Check **.gitignore Violations**: Verify if any evidenced secret files (e.g., `.env`, `*.pem`) are missing from `.gitignore`.
6. Arbitration: Never extract secret contents; document only the location, pattern, and loader symbol with evidence.
7. Legacy Context is intent guidance only and is never evidence.
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
# PROMPT_G4 — SECURITY / SECRETS / REDUCTION FACTS

TASK: Extract security and secrets reduction facts.

RULE: No secret contents; extract paths + patterns + loaders only.

OUTPUTS:
	•	GOV_SECRETS_SURFACE.json
```
