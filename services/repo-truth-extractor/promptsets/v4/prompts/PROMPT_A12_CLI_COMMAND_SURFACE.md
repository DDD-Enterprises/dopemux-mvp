# PROMPT_A12

## Goal
Produce `A12` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
Extract the CLI command tree: all command-line interfaces, subcommands, argument signatures, and entry points defined in the repository.

## Inputs
- Source scope (scan these roots first):
  - `src/dopemux/cli.py`
  - `src/dopemux/commands/**`
  - `src/dopemux/cli/**`
  - `scripts/**`
  - `tools/**`
  - `installers/**`
  - `.vibe/**`
  - `.claude/**`
  - `.dopemux/**`
  - `.github/**`
  - `.taskx/**`
  - `mcp-proxy-config.copilot.yaml`
  - `compose/**`
  - `config/**`
  - `configs/**`
  - `docker/**`
  - `ops/**`
  - `setup.py`
  - `setup.cfg`
  - `pyproject.toml`
- Upstream normalized artifacts available to this step:
  - `REPOCTRL_INVENTORY.json`
  - `REPOCTRL_PARTITIONS.json`
  - `REPO_INSTRUCTION_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`

## Outputs
- `CLI_COMMAND_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
- Output contracts:
  - `CLI_COMMAND_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A12`
    - `id_rule`: `CLI_COMMAND_SURFACE:<stable-hash(path|command_name|parent_command)>`
    - `required_item_fields`: `id, command_name, module_path, parent_command, arguments, subcommands, description, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`
- `arguments` shape: `[{"name": "...", "type": "...", "required": bool, "default": "...", "help": "..."}]`
- `subcommands` shape: `["sub1", "sub2"]` referencing other item IDs

## Extraction Procedure
1. Load upstream inventory and partitions; use the CLI partition as primary scan surface
2. Scan `src/dopemux/cli.py` and `src/dopemux/commands/**` for Click/Typer/argparse command definitions
3. Extract command decorators (`@click.command`, `@click.group`, `@app.command`) with full argument signatures
4. Scan `pyproject.toml`, `setup.py`, `setup.cfg` for `[project.scripts]` and `console_scripts` entry points
5. Scan `scripts/**` for executable shell/python scripts that serve as CLI entry points
6. Build command tree: map parent-child relationships between groups and subcommands
7. For each command, extract `command_name`, `module_path`, `arguments` array, `description` from docstrings
8. Cross-reference with `REPO_INSTRUCTION_SURFACE.json` to identify documented CLI usage patterns
9. Build deterministic IDs using stable content keys (path/command_name/parent_command)
10. Attach evidence to every non-derived field and every relationship edge
11. Normalize arrays by stable sort keys; deduplicate by ID (or stable content hash)
12. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps
13. Emit exactly the declared outputs and no additional files

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
- Do not invent CLI commands, arguments, or entry points.
- Do not infer command behavior from script names alone; require direct code evidence (decorators, function signatures).
- If required evidence is missing, keep item with `UNKNOWN` fields and `missing_evidence_reason`.
- Never copy unsupported keys from upstream QA artifacts into norm artifacts.
- Do not assume a script is a CLI command without verifying it has argument parsing or entry point registration.

## Failure Modes
- Missing input files: emit valid empty containers plus `missing_inputs` list in output items.
- Partial scan coverage: emit partial results with explicit `coverage_notes` and evidence gaps.
- Schema violation risk: drop unverifiable fields, keep item `id` + `evidence` + `UNKNOWN` placeholders.
- Parse/runtime ambiguity: keep all plausible candidates but mark `status: needs_review` with evidence.
- Mixed CLI frameworks: if both Click and argparse are used, emit separate items with `framework` annotation.
- Undocumented commands: emit with `description: UNKNOWN` and source evidence pointing to bare function definition.
