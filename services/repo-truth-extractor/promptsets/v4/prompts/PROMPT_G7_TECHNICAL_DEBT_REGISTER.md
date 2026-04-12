# PROMPT_G7

## Goal
Produce `G7` outputs for phase `G` with strict schema, explicit evidence, and deterministic normalization.
Extract a technical-debt register from directly evidenced debt markers across the repository: TODO and FIXME comments, deprecated decorators or APIs, `HACK` and `XXX` markers, `CHANGE_ME` placeholders, and large commented-out code blocks that still affect operator understanding or maintenance risk.

## Inputs
- Source scope (scan these roots first):
  - `src/**`
  - `services/**`
  - `scripts/**`
  - `shared/**`
  - `docs/**`
  - `.github/**`
- Upstream normalized artifacts available to this step:
  - `GOV_INVENTORY.json`
  - `GOV_PARTITIONS.json`
  - `GOV_POLICIES.json`
  - `CODE_HEALTH_SURFACE.json`
  - `DEAD_CODE_INVENTORY.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `TECHNICAL_DEBT_REGISTER.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"TECHNICAL_DEBT_REGISTER@v1","items":[...]}`
- Output contracts:
  - `TECHNICAL_DEBT_REGISTER.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `G7`
    - `id_rule`: `TECHNICAL_DEBT_REGISTER:<stable-hash(path|debt_type|symbol|line_start)>`
    - `required_item_fields`: `id, debt_type, description, path, line_range, evidence`
    - `required_registry_fields`: `id, path, line_range`
- `debt_type` enum:
  - `todo_marker`
  - `fixme_marker`
  - `hack_marker`
  - `deprecated_surface`
  - `placeholder_marker`
  - `commented_out_code`

## Extraction Procedure
1. Load governance inventory, partitions, policy context, code health, and dead-code artifacts.
2. Scan for direct debt markers including `TODO`, `FIXME`, `HACK`, `XXX`, `CHANGE_ME`, and similar explicit placeholders.
3. Scan for deprecation signals such as `@deprecated`, warnings, deprecation comments, or compatibility shims that remain active in runtime code.
4. Scan for large commented-out code blocks or disabled command examples that still describe previously active logic.
5. Cross-reference `CODE_HEALTH_SURFACE.json` and `DEAD_CODE_INVENTORY.json` to avoid duplicating the exact same evidence without a distinct governance debt reason.
6. Build deterministic IDs from `(path|debt_type|symbol|line_start)` and attach exact evidence excerpts.
7. Normalize by stable sort keys, deduplicate by ID, and emit exactly `TECHNICAL_DEBT_REGISTER.json`.

## Evidence Rules
- Every item must include the exact debt marker or commented block excerpt.
- Every evidence object must include exact `path`, `line_range`, and `excerpt` keys.
- `description` should stay close to the evidenced text and should not invent remediation plans.
- Use repo-relative paths and narrow line ranges.
- When a debt marker references another file or ticket, include that reference only if it is present in the evidenced text.

## Determinism Rules
- Do not emit timestamps, issue tracker state fetched from outside the repo, or inferred priority values.
- Sort items by `(path, line_start, id)`.
- Use stable enums for `debt_type`.
- Merge duplicates only when they resolve to the same path, debt type, and starting line.

## Anti-Fabrication Rules
- Do not turn general comments into debt markers unless they explicitly carry a debt signal or represent commented-out executable code.
- Do not assume a deprecated API is still used unless the usage site is evidenced.
- Do not copy remediation intent from external docs or tickets into the register without local evidence.
- Do not include stylistic disagreement as technical debt.

## Failure Modes
- If a marker appears in generated files, keep it only if the generated file is committed and operator-relevant.
- If a commented block is ambiguous prose rather than code, classify conservatively or omit it.
- If multiple debt markers occur on the same line, emit separate items only when their debt types differ materially.
- If the owning symbol cannot be recovered safely, keep the item path-scoped rather than inventing symbol ownership.
