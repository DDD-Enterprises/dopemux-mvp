# PROMPT_R0

## Goal
Produce `R0` outputs for phase `R` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `extraction/**/norm/**`
- `docs/**`
- `services/repo-truth-extractor/**`
- Upstream normalized artifacts available to this step:
- None; this step can rely on phase inventory inputs.
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `CONTROL_PLANE_TRUTH_MAP.md`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `CONTROL_PLANE_TRUTH_MAP.md`
    - `kind`: `markdown`
    - `merge_strategy`: `markdown_concat`
    - `canonical_writer_step_id`: `R0`
    - `id_rule`: `CONTROL_PLANE_TRUTH_MAP:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, evidence`

## Extraction Procedure
1. Load merged artifacts from A99 and H9 (repo and home control plane outputs); use both as the complete control plane surface.
2. Synthesize the CONTROL_PLANE_TRUTH_MAP: combine repo-level and home-level control plane facts into a unified truth document organized by control plane category (MCP, routing, hooks, LiteLLM, TaskX, compose).
3. For each control plane element, produce a prose summary with: what it does, where it is configured, what depends on it, and known risks.
4. Cross-reference with governance artifacts (G-Phase) to annotate each element with its enforcement status.
5. For each truth map section, embed evidence citations as inline references.
6. Legacy Context is intent guidance only and is never evidence.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path/symbol/name/service_id).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash).
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

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
- Incomplete control plane: if either repo or home control plane data is missing, produce a partial truth map and note the gap explicitly in the document header.
- Conflicting truth: if repo and home control planes contradict on the same element, present both versions with evidence and flag as `status: conflict`.

## Legacy Context (for intent only; never as evidence)
```markdown
Goal: CONTROL_PLANE_TRUTH_MAP.md

ROLE: Supervisor/Auditor. Evidence-first.
HARD RULE: Reason only from Phase A/H/D/C normalized artifacts. If evidence is missing, write UNKNOWN and name the missing artifact.

TASK:
Produce the repo/home control-plane truth map.

MUST INCLUDE:
- Repo control plane surfaces (instructions, hooks, compose, router, litellm, mcp)
- Home control plane surfaces (configs, router, litellm, mcp, sqlite state)
- Invocation graph (what starts what)
- Control-plane to runtime coupling points
- Portability risks

RULES:
- Cite every claim with REPOCTRL:/HOMECTRL:/CODE:/DOC references.
- No repo rescans. No implementation changes.
- Label unevidenced statements UNKNOWN.
```
