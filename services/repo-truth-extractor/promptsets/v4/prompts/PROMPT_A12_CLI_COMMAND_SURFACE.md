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
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on the CLI command partition.
2. Scan `src/dopemux/cli.py` and `src/dopemux/commands/**/*.py` for framework-specific command definitions:
   - Identify Click decorators: `@click.command`, `@click.group`, `@click.option`, `@click.argument`.
   - Identify Typer decorators: `@app.command`, `@app.callback`.
   - Identify argparse patterns: `argparse.ArgumentParser()` and `.add_argument()` calls.
3. Extract mandatory command metadata:
   - `command_name`: the literal string name (e.g., "run", "sync", "audit").
   - `parent_command`: identify the group or parent parser ID.
   - `arguments`: extract name, type, required status, and default values for every option/argument.
   - `description`: extract from docstrings or the `help` parameter in the decorator.
4. Scan `pyproject.toml`, `setup.py`, and `setup.cfg` for `console_scripts` or `[project.scripts]` entry points.
5. Scan `scripts/` and `tools/` for executable standalone scripts containing `#!/usr/bin/env` and argument parsing logic.
6. Build command tree: map parent-child relationships between groups and subcommands to represent the full hierarchy.
7. For each CLI_COMMAND_SURFACE item, populate `id` (stable-hash of path|command_name|parent_command), required fields, and `evidence`.
8. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
9. Build deterministic IDs using stable content keys (path|symbol|name).
10. Attach evidence to every non-derived field and every relationship edge.
11. Normalize arrays by stable sort keys; deduplicate by ID.
12. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
13. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.
