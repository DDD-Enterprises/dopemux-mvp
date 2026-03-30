# PROMPT_A5

## Goal
Produce `A5` outputs for phase `A` with strict schema, explicit evidence, and deterministic normalization.
Focus on concrete, machine-verifiable implementation facts.

## Inputs
- Source scope (scan these roots first):
- `.vibe/**`
- `.claude/**`
- `.dopemux/**`
- `.github/**`
- `.githooks/**`
- `.taskx/**`
- `mcp-proxy-config.copilot.yaml`
- `compose/**`
- `config/**`
- `configs/**`
- `docker/**`
- `scripts/**`
- `tools/**`
- `src/dopemux/hooks/**`
- `src/dopemux/mcp/hooks.py`

- `installers/**`
- `ops/**`





- `compose.yml`
- `docker-compose*.yml`
- `README.md`
- `AGENTS.md`
- Upstream normalized artifacts available to this step:
- `REPOCTRL_INVENTORY.json`
- `REPOCTRL_PARTITIONS.json`
- `REPO_INSTRUCTION_SURFACE.json`
- `REPO_INSTRUCTION_REFERENCES.json`
- `REPO_MCP_SERVER_DEFS.json`
- `REPO_MCP_PROXY_SURFACE.json`
- `REPO_ROUTER_SURFACE.json`
- Runner context artifacts:
  - `extraction/*/inputs/INVENTORY.json`
  - `extraction/*/inputs/PARTITIONS.json`
  - `services/repo-truth-extractor/promptsets/v4/promptset.yaml`
  - `services/repo-truth-extractor/promptsets/v4/artifacts.yaml`
- When relevant, use `services/registry.yaml` as canonical service list.

## Outputs
- `REPO_HOOKS_SURFACE.json`

## Schema
- Use deterministic containers only:
  - `ItemList`: `{"schema":"<schema_id>@v1","items":[...]}`
  - `Graph`: `{"schema":"<schema_id>@v1","nodes":[...],"edges":[...]}`
- Output contracts:
  - `REPO_HOOKS_SURFACE.json`
    - `kind`: `json_item_list`
    - `merge_strategy`: `itemlist_by_id`
    - `canonical_writer_step_id`: `A99`
    - `id_rule`: `REPO_HOOKS_SURFACE:<stable-hash(path|symbol|name)>`
    - `required_item_fields`: `id, hook_name, hook_type, trigger, handler_path, is_blocking, path, line_range, evidence`
    - `required_registry_fields`: `path, line_range, id`

### Item Schema
```json
{
  "id": "REPO_HOOKS_SURFACE:<hash>",
  "hook_name": "<human-readable hook identifier>",
  "hook_type": "git_hook|claude_hook|github_action|fastapi_event|signal_handler|pre_commit|taskx_hook|launchd_trigger",
  "trigger": "<event or condition that fires the hook>",
  "handler_path": "<repo-relative path to handler script or function>",
  "handler_symbol": "<function name or script entrypoint, or null for whole-file scripts>",
  "command": "<literal command string executed, or null if code-based>",
  "is_blocking": true,
  "timeout_seconds": "<configured timeout, or null if none>",
  "invoked_paths": ["<repo-relative paths called by this hook>"],
  "path": "<repo-relative path to hook definition/registration>",
  "line_range": [0, 0],
  "status": "ok|needs_review|missing_evidence",
  "evidence": [{"path": "", "line_range": [], "excerpt": ""}]
}
```

### Hook Type Definitions
- **git_hook**: Git hooks in `.githooks/` or `.git/hooks/` (pre-commit, pre-push, post-merge, etc.)
- **claude_hook**: Claude Code hooks defined in `.claude/settings.json` under `hooks` key with trigger/glob/command
- **github_action**: GitHub Actions workflows in `.github/workflows/` triggered by `on:` events
- **fastapi_event**: FastAPI lifecycle events registered via `@app.on_event()` or `app.add_event_handler()`
- **signal_handler**: OS signal handlers registered via `signal.signal()` or framework equivalents
- **pre_commit**: Pre-commit framework hooks in `.pre-commit-config.yaml`
- **taskx_hook**: TaskX/Dopemux hooks in `.taskx/` configuration or `src/dopemux/hooks/`
- **launchd_trigger**: macOS launchd-triggered scripts defined in plist files

### Worked Example
```json
{
  "id": "REPO_HOOKS_SURFACE:c4a8e2f1",
  "hook_name": "PrePush lint check",
  "hook_type": "claude_hook",
  "trigger": "PrePush",
  "handler_path": ".claude/settings.json",
  "handler_symbol": null,
  "command": "scripts/lint-docs.sh",
  "is_blocking": true,
  "timeout_seconds": null,
  "invoked_paths": ["scripts/lint-docs.sh"],
  "path": ".claude/settings.json",
  "line_range": [12, 18],
  "status": "ok",
  "evidence": [{"path": ".claude/settings.json", "line_range": [12, 18], "excerpt": "\"hooks\": {\"PrePush\": [{\"command\": \"scripts/lint-docs.sh\"}]}"}]
}
```

## Extraction Procedure
1. Load upstream `REPOCTRL_INVENTORY.json` and `REPOCTRL_PARTITIONS.json`; focus on the hooks partition.
2. Scan `.githooks/`, `.github/workflows/`, and `.pre-commit-config.yaml` for external hook triggers.
3. Scan `src/dopemux/hooks/**` and `src/dopemux/mcp/hooks.py` for internal hook registrations and decorators.
4. For each hook identified, extract mandatory fields:
   - `hook_type`: categorize as "git-hook", "pre-commit", "ci-pipeline", "task-hook", or "mcp-hook".
   - `trigger`: identify the triggering event (e.g., `git commit`, `cron`, `workflow_dispatch`, `on_task_start`).
   - `command`: extract the literal shell command string or python function name invoked.
   - `invoked_paths`: list file patterns the hook watches or modifies (e.g., `*.py`, `docs/**`).
5. Build relationship graph: link hooks to the files they monitor and the commands they execute.
6. For each HOOKS_SURFACE item, populate `id` (hook:<type>:<name>), required fields, and `evidence`.
7. Enumerate candidate facts only from in-scope inputs and upstream artifacts.
8. Build deterministic IDs using stable content keys (path|symbol|name).
9. Attach evidence to every non-derived field and every relationship edge.
10. Normalize arrays by stable sort keys; deduplicate by ID.
11. Validate required fields; emit `UNKNOWN` for unsatisfied values with evidence gaps.
12. Emit exactly the declared outputs and no additional files.

## Shared Rules
Refer to `PROMPTSET_RULES.md` for Evidence, Determinism, Anti-Fabrication, and Failure Mode protocols.

## Legacy Context (for intent only; never as evidence)
```markdown
# PROMPT: A5 - Repo Hooks Surface

Phase: A
Step: A5

Outputs:
- REPO_HOOKS_SURFACE.json

Mode: extraction
Strict: evidence_only
Format: JSON only (no markdown fences)

Hard rules:
1) Do NOT invent. If not present, write "UNKNOWN".
2) Every non-trivial field must include "evidence" with source_path and either key_path or excerpt.
3) Emit ONLY valid JSON. No commentary.

Input:
You will receive repo control-plane files. Extract only what is explicitly evidenced.

Required JSON shape:
{
  "artifact": "REPO_HOOKS_SURFACE.json",
  "phase": "A",
  "step": "A5",
  "generated_at": "<iso8601>",
  "items": [
    {
      "id": "hook:<type>:<name>",
      "hook_type": "...",
      "trigger": "...",
      "command": "...",
      "invoked_paths": ["..."],
      "evidence": [
        {
          "source_path": "...",
          "key_path": "...",
          "excerpt": "..."
        }
      ]
    }
  ],
  "unknowns": ["..."]
}

Extract:
- Git hooks, pre-commit hooks, CI hooks, taskx/dopemux hooks
- Literal commands invoked, source file locations, triggering conditions if defined
```
