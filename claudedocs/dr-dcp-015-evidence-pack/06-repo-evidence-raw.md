# Repo Evidence — Raw Findings

Grounded answers to DR-DCP-015 §14 ("Questions For Repo Evidence"), gathered from this repo (current branch + PR diffs). This is the evidence backing the corrections in [`01-reconciliation-memo.md`](01-reconciliation-memo.md) §2. Each item is a real file path / command result.

## A. Claude Code hooks — single dispatcher, not per-event scripts

All **11** lifecycle events register in `.claude/settings.json` and route to **one** entry point: `python3 "$CLAUDE_PROJECT_DIR/src/dopemux/claude/native_hooks.py"` (stdin JSON). The dispatcher reads `hook_event_name` and branches internally.

| Event | Handler (in `native_hooks.py`) | Can block? |
|---|---|---|
| `SessionStart` | `_on_session_start()` — orchestrator cache + workflow context inject | no |
| `SubagentStart` | `_on_subagent_start(data)` — reads `agent_type`; injects protocol for non-Explore/Plan | no |
| `UserPromptSubmit` | `_on_user_prompt(data)` — reads `prompt`; Redis activity event | no |
| `PreToolUse` | `_on_pre_tool_use(data)` — reads `tool_name`,`tool_input`; **block via exit 2** | **yes** |
| `PermissionRequest` | `_on_permission_request(data)` — auto-allows safe read-only tools | allow |
| `PostToolUse` | `_on_post_tool_use(data)` — reads `tool_name`,`tool_input`,`tool_response` | no |
| `PostToolUseFailure` | `_on_post_tool_use_failure(data)` — reads `error` | no |
| `Stop` / `SubagentStop` | `_on_stop(data)` — reads `stop_hook_active` + response keys; **block stop via exit 2** | **yes** |
| `PreCompact` | `_on_pre_compact()` — workflow context inject | no |
| `SessionEnd` | `_on_session_end(data)` — reads `reason`; saves workflow state | no |

The `.claude/hooks/*.sh` scripts (`check_energy.sh`, `log_progress.sh`, `save_context.sh`, `track_file_edit.sh`) and `prompt_analyzer.py` / `session_lifecycle.py` are **legacy orphans NOT wired in settings.json**. The `orchestrator_*.py` modules under `.claude/hooks/` are imported by `native_hooks.py` (not invoked directly).

### Real hook payload schema (keys the code actually reads)

```json
// PreToolUse / PermissionRequest
{ "hook_event_name": "PreToolUse", "session_id": "...", "tool_name": "...", "tool_input": { } }
// PostToolUse
{ "hook_event_name": "PostToolUse", "tool_name": "...", "tool_input": { }, "tool_response": "..." }
// PostToolUseFailure
{ "hook_event_name": "PostToolUseFailure", "tool_name": "...", "tool_input": { }, "error": "..." }
// Stop / SubagentStop
{ "hook_event_name": "Stop", "stop_hook_active": true,
  "response": "...", "assistant_response": "...", "completion": "...", "text": "...", "stop_text": "..." }  // fallback key order
// UserPromptSubmit
{ "hook_event_name": "UserPromptSubmit", "prompt": "..." }
// SubagentStart
{ "hook_event_name": "SubagentStart", "agent_type": "Explore|Plan|..." }
// SessionEnd
{ "hook_event_name": "SessionEnd", "reason": "..." }
```

Output shapes written to stdout:
```json
// allow + inject context (exit 0)
{ "systemMessage": "...", "hookSpecificOutput": { "additionalContext": "...", "hookEventName": "..." } }
// block tool (exit 2)
{ "systemMessage": "...", "hookSpecificOutput": { "permissionDecision": "deny", "decision": "block", "additionalContext": "..." } }
// block stop (exit 2)
{ "decision": "block", "systemMessage": "...", "hookSpecificOutput": { "additionalContext": "..." } }
// auto-allow permission (exit 0)
{ "hookSpecificOutput": { "permissionDecision": "allow", "additionalContext": "..." } }
```

## B. Slash commands / skills — markdown files, no plugin manifest

- Commands live in `.claude/commands/*.md`; path maps to name (`.claude/commands/dx/implement.md` → `/dx:implement`). Structure = YAML frontmatter (`description`, `arguments`, `allowed-tools`, `model`) + Markdown instruction body (prose+pseudocode, not executable).
- **No plugin system:** `find . -name plugin.json -not -path '*/node_modules/*'` → empty; `find . -name .claude-plugin` → empty. Skills come from the global `~/.claude/` SuperClaude framework, not a local plugin manifest.

> Implication: DR-DCP-015 §4's `dcp-control-plane-plugin/.claude-plugin/plugin.json` package is a **proposed new architecture**, not an existing pattern to standardize.

## C. No `dopemux dcp` CLI

- `pyproject.toml`: `dopemux = "dopemux.cli:main"`. `rg "\bdcp\b" src/dopemux/cli.py` → **no match**.
- Existing top-level subcommands: `agent_loop, audit, autoresponder, backup, capture, cockpit, decisions, dev, extract, instances, kernel, mcp, memory, mobile, mobile-env, native-hooks, orchestrator, personas, profile, routing, rte, save, servers, switch, system-data, tmux, trigger, update, upgrades, wizard, workflow`.
- `src/dopemux/dcp/` exists but is a **library only**: `__init__.py`, `control_snapshot.py`, `proof_family.py`, `proof_pointer_reader.py`, `red_lane.py`, `red_lane_rules.py`, `red_lane_scanner.py`. No CLI entrypoint wired to it.

> Implication: DR-DCP-015 §7's entire `dopemux dcp` command table is greenfield.

## D. "DCP" = Data Control Plane

- `schemas/dcp/README.md`: *"the DCP (Data Control Plane) core contract floor."*
- `task-packets/TP-DCP-0002.md`: `Project: DCP — Data Control Plane`.
- Secondary surface: `services/dcp-readonly-facade/` = a loopback-only read-only MCP evidence projector built on top.
- **Not** DopeContext (always written "dope-context"). No `\bDCP\b` in markdown maps to dope-context.

## E. Schema inventory (`schemas/dcp/` + `schemas/proof/`)

`schemas/dcp/` (19 files; the 5 core contracts in **bold**):
- **`dcp_red_lane_taxonomy.schema.json`** (.v0) · **`dcp_mutation_class.schema.json`** (.v0) · **`dcp_helper_receipt.schema.json`** (.v0) · **`dcp_approval_artifact.schema.json`** (.v0) · **`dcp_project_resource_map.schema.json`** (.v0)
- `dcp_chronicle_receipt.schema.json` (.v0) · `dcp_control_snapshot.schema.json` (.v0) · `dcp_evidence_hit.schema.json` (.v0) · `dcp_proof_pointer.schema.json` (.v0) · `dcp_red_lane_report.schema.json`
- `dcp_audit_route` · `dcp_authority_surface` · `dcp_backend_runner` · `dcp_execution_lane` · `dcp_model_slot` · `dcp_routing_classification` · `dcp_routing_decision` · `dcp_routing_proof_extension` · `dcp_stop_condition` (no version const)

`schemas/proof/` (3 files, no version const): `auditor_route.schema.json` · `embedded_audit.schema.json` · `multi_model_pr_audit.schema.json`

> `schemas/dcp/README.md` rule: *"No schema in this directory should be treated as the authoritative source for runtime enforcement until upgraded past `.v0` by a subsequent task packet."*
