---
id: MEMORY_INTEGRATION
title: Memory Integration
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-18'
last_review: '2026-03-18'
next_review: '2026-06-16'
prelude: Memory Integration (explanation) for dopemux documentation and developer
  workflows.
---
# Evidence-first integration of Dopemux Memory with Claude Code without MCP fragility

## Verified integration surfaces

**VERIFIED:** The surfaces below are documented in publicly accessible Claude Code documentation and/or the public `anthropics/claude-code` changelog. Where documentation does **not** specify a guarantee (or where multiple docs appear to diverge), it is marked **UNKNOWN** or called out explicitly. citeturn6view3turn15view0turn11view0turn11view1turn14view0

| surface | lifecycle stage | data available | guarantees | citations |
|---|---|---|---|---|
| Hooks runtime contract (all hook handlers: `command`, `prompt`, `agent`) | Throughout a session; fires on defined “hook events” | Hook receives **JSON via stdin** with common fields: `session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name` (plus event-specific fields). | Matching hooks run **in parallel** and identical handlers are **deduplicated** (for prompt/agent handlers per docs). Default timeouts exist (`timeout` defaults: 600s command, 30s prompt, 60s agent). Exit codes determine behaviour: `0` success; `2` is “blocking error” (event-dependent); other non‑zero codes are “non-blocking error” (execution continues). Stdout is generally hidden except verbose mode, **but** `UserPromptSubmit` + `SessionStart` treat stdout as **context** Claude can see. Hook scripts run with your **user permissions**. | citeturn6view3turn6view4turn5view1turn5view5turn9view4 |
| Hooks: `SessionStart` event | When a session starts or resumes; matcher indicates `startup`, `resume`, `clear`, `compact` | Common fields + `source`, `model`, optionally `agent_type` | Any text printed to stdout is **added as context** for Claude; an `additionalContext` field is also supported (concatenated across hooks). Cannot be blocked via exit‑2 semantics (exit‑2 shows stderr to user only for `SessionStart`). | citeturn12view8turn6view4turn9view0 |
| Hooks: `UserPromptSubmit` event | When user submits a prompt, **before** Claude processes it | Common fields + `prompt` | Can **block** prompt processing; on exit 2 it “blocks prompt processing and erases the prompt”. On success, can add context via plaintext stdout or via JSON `additionalContext`. | citeturn12view7turn6view4turn4view2 |
| Hooks: `PreToolUse` event | After Claude creates tool parameters; **before** tool executes | Common fields + `tool_name`, `tool_input`, `tool_use_id` | Can block tool call via exit‑2, and supports decision control for “allow/deny/ask” via `hookSpecificOutput.permissionDecision`. Matches built-in tool names plus MCP tool names. **Format drift:** docs note older top‑level `decision/reason` for `PreToolUse` is deprecated in favour of `hookSpecificOutput.permissionDecision`. | citeturn4view2turn6view1turn9view2turn13view6turn14view0 |
| Hooks: `PermissionRequest` event | When a permission dialog is about to be shown (interactive contexts) | Common fields + `tool_name`, `tool_input`, and optionally `permission_suggestions` | Can allow/deny on behalf of user; can **modify tool input** via `updatedInput` (allow case) and update permissions via `updatedPermissions`. **Non‑interactive gap:** docs state `PermissionRequest` hooks do **not** fire in non-interactive “print mode” (`-p`); use `PreToolUse` instead. | citeturn13view6turn9view6turn11view1 |
| Hooks: `PostToolUse` event | Immediately after a tool completes successfully | Common fields + `tool_name`, `tool_input`, `tool_response`, `tool_use_id` | Cannot undo the tool action (it has already happened). Can provide feedback/extra context after tool execution (via decision control and `additionalContext`). | citeturn12view0turn9view6turn4view2 |
| Hooks: `PostToolUseFailure` event | After a tool fails (errors or failure results) | Common fields + `tool_name`, `tool_input`, `tool_use_id`, plus `error`, optional `is_interrupt` | Cannot undo the failed action; can add `additionalContext` alongside the error for Claude to consider. | citeturn12view1turn4view2 |
| Hooks: `Stop` and `SubagentStop` events | When the main agent finishes responding (`Stop`); when a subagent finishes (`SubagentStop`) | Common fields + `stop_hook_active`; `SubagentStop` adds `agent_id`, `agent_type`, `agent_transcript_path` | Can prevent stopping (exit‑2 or JSON decision “block”, depending on event). Docs warn Stop hooks can loop indefinitely unless you check `stop_hook_active`. Stop does **not** run on user interrupt. | citeturn12view10turn9view7turn9view6 |
| Hooks: `PreCompact` event | Before a compact operation | Common fields + `trigger` (`manual` or `auto`) and `custom_instructions` | Runs before compaction; matcher indicates manual vs auto. (Docs do not specify any blocking/decision control here.) | citeturn13view0turn6view1 |
| Hooks: `SessionEnd` event | When a session terminates; matcher filters by exit reason | Common fields + `reason` | Explicitly has **no decision control** (cannot block termination). Intended for cleanup/logging. | citeturn12view9turn4view2 |
| Hook configuration scope + control knobs | Before session start (config load); then fixed for the session | Hook config can live in `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`, managed policy, plugin `hooks/hooks.json`, or skill/agent frontmatter | Users can disable *all hooks* with `disableAllHooks`. Claude Code snapshots hooks at startup; modifications require review and do not silently take effect mid-session. Managed environments can enforce `allowManagedHooksOnly` (blocks user/project/plugin hooks; allows managed + SDK hooks). | citeturn6view4turn6view0turn20view1turn20view3 |
| Plugins (packaging + distribution) | Install/enable time; during startup (component discovery + registration) | Plugins can provide **skills**, **agents**, **hooks**, **MCP servers**, and **LSP servers**; plugin root path via `${CLAUDE_PLUGIN_ROOT}` | Installed plugins can be enabled/disabled via settings (`enabledPlugins`) and CLI (`claude plugin enable/disable/...`). Plugins are copied to a **cache directory** and cannot reference files outside their copied structure (path traversal limitation); `${CLAUDE_PLUGIN_ROOT}` is the supported escape hatch for stable paths. Plugin MCP servers “start automatically when the plugin is enabled.” | citeturn15view0turn20view2 |
| Skills (slash commands) | On-demand in conversation or auto-invoked when relevant | Skill content from `SKILL.md` and frontmatter; can include supporting files; invocation controls exist | Skills are supported extension mechanism; custom slash commands are represented as skills; can be distributed via plugins and managed settings. (Skills are not “deterministic execution”; they are model-mediated.) | citeturn3view5turn15view0 |
| Memory files (“CLAUDE.md memory” + rules + local) | Loaded at launch; some loaded on-demand when reading files | CLAUDE.md hierarchy; `.claude/rules/*.md`; `CLAUDE.local.md`; imports via `@path/to/import` | CLAUDE.md above the cwd loads at launch; child CLAUDE.md loads on-demand when reading in those directories. Imports require an approval dialog the first time for external imports; if declined, imports stay disabled (one-time decision per project). | citeturn11view0turn19view0 |
| Auto memory (built-in feature) | Persisted across sessions; loaded at session start | Stored at `~/.claude/projects/<project>/memory/` with `MEMORY.md` entrypoint and topic files | First 200 lines of `MEMORY.md` are loaded into Claude’s **system prompt** at the start of every session; topic files are read on demand. Rollout is gradual; can force on/off via `CLAUDE_CODE_DISABLE_AUTO_MEMORY`. | citeturn11view0 |
| Session transcripts (local persistence) | Written continuously during sessions | Stored on disk; hooks receive `transcript_path` | Claude Code stores “each message, tool use, and result” locally to enable resuming/rewinding/forking; hooks receive the path to the transcript (`transcript_path`). **UNKNOWN:** official docs do not publish the transcript JSONL schema in the sources reviewed here. | citeturn11view2turn6view4 |
| CLI surfaces that can affect extension behaviour | Process start; per-session | Flags like `-p` (non-interactive print/SDK mode), system prompt replacement/append flags, and disabling slash commands | `--system-prompt` replaces the entire default system prompt (blank slate). `--disable-slash-commands` disables skills/slash commands. `-p` runs non-interactive. **Conflict/UNKNOWN:** CLI reference lists `--init`, `--init-only`, and `--maintenance` as “initialization/maintenance hooks,” but the reviewed hooks reference does not document a corresponding hook event/config schema for these flags. | citeturn11view1turn9view6turn17view0 |
| Status line command | Runs on UI updates during session | stdin JSON includes `session_id`, `transcript_path`, model, cost, context usage, etc. | Script output is displayed in UI; used for monitoring. Can be disabled via `disableAllHooks` (which disables hooks + “any custom status line”). Not a documented prompt/tool mutation surface. | citeturn11view4turn20view1 |

## Failure and trust analysis

### Verified trust boundaries

**VERIFIED: Hooks can see raw prompts and tool inputs/outputs (within defined events).** A `UserPromptSubmit` hook receives the user’s prompt text in the `prompt` field. citeturn12view7 A `PostToolUse` hook receives both the tool arguments (`tool_input`) and the tool result (`tool_response`), while `PostToolUseFailure` includes error details. citeturn12view0turn12view1

**VERIFIED: Hooks run with the full permissions of the user account executing Claude Code.** The hooks reference explicitly warns that hooks “run with your system user’s full permissions” and can modify/delete/access files. citeturn5view5 This is the core trust boundary: a Dopemux hook is effectively trusted local code, not a sandboxed plugin script.

**VERIFIED: Hooks cannot “reach back into Claude” except through the documented stdout/stderr/exit-code/JSON response contract.** Hooks “communicate through stdin, stdout, stderr, and exit codes.” citeturn9view3turn9view4 They cannot directly trigger slash commands or tool calls. citeturn9view6

**VERIFIED: Users (or admins) can disable hooks.** Users can set `disableAllHooks: true` or toggle it in `/hooks`. citeturn6view3turn20view1 Enterprise-managed systems can also set `allowManagedHooksOnly` to block loading of user/project/plugin hooks. citeturn20view3turn6view1

**VERIFIED: Plugins are not in-place; they are cached.** Claude Code copies plugins into a cache directory, and plugins cannot reference paths outside their copied root (unless you restructure/symlink into the copied tree). citeturn15view0 This matters because Dopemux must not rely on relative paths that escape `CLAUDE_PLUGIN_ROOT`.

### Verified failure behaviours for hooks

**VERIFIED: Hook failure modes are largely “continue unless explicitly blocking,” which creates silent-failure risk.**

- Exit `0`: success; JSON output processed (if present). citeturn6view4
- Exit `2`: treated as blocking error; effect depends on event (e.g., blocks tool call for `PreToolUse`, erases prompt for `UserPromptSubmit`). Stdout is ignored; stderr is used as feedback to Claude or user depending on event. citeturn6view4turn4view2
- Any other exit code: non-blocking error; execution continues; stderr generally only visible in verbose mode. citeturn6view4turn9view4

**Implication (INFERRED, evidence-backed):** If Dopemux “must” capture memory but crashes intermittently, Claude Code will often proceed with no visible indication, unless Dopemux intentionally uses `systemMessage` or strategically blocks. This is the main “silent failure” hazard for capture. citeturn6view4turn4view2

**VERIFIED: Async hooks are explicitly non-blocking and lose control semantics.** Setting `"async": true` for a command hook runs it in the background; “decision” fields have no effect because the triggering action already completed. Output (e.g., `systemMessage` or `additionalContext`) is delivered on the next conversation turn. citeturn5view1turn5view2

**Implication (INFERRED, evidence-backed):** For Dopemux injection, async is usually the wrong choice for “must be present before the model responds,” because the context may arrive one turn later. citeturn5view2turn12view7turn12view8

### Verified plugin failure modes affecting Dopemux

**VERIFIED: Misconfiguration and structure errors are expected and documented.** The plugins reference lists common issues such as invalid `plugin.json`, wrong directory structure, and non-executable hook scripts; it also recommends `claude --debug` and `claude plugin validate` for diagnosis. citeturn15view0

**VERIFIED: Plugin path and dependency mistakes are common due to caching constraints.** If a plugin references sibling directories via `../`, those files will not be present after caching. citeturn15view0

### Failure modes Dopemux should treat as fail-closed

Below, **fail-closed** means: *do not inject potentially wrong/unsafe memory into Claude’s context silently.* It does **not** necessarily mean “block the user,” unless you deliberately choose that product behaviour.

**Tool disabled / non-interactive mode**

- **VERIFIED:** `PermissionRequest` hooks do not fire in non-interactive mode (`-p`), so any design depending on that hook for gating or rewriting tool inputs will fail in that mode. citeturn9view6turn11view1
- **Fail-closed recommendation (INFERRED):** Dopemux capture/injection should rely on `UserPromptSubmit` + `PreToolUse` + `PostToolUse` primarily, and treat the absence of `PermissionRequest` as expected in `-p` rather than as a fatal condition. citeturn9view6turn12view7turn6view1

**Plugin misconfigured / version drift**

- **VERIFIED:** PreToolUse decision output has documented deprecations (top-level `decision/reason` deprecated; `hookSpecificOutput.permissionDecision` preferred). citeturn13view6turn4view2
- **Fail-closed recommendation (INFERRED):** Dopemux should validate its own hook output format (strict JSON-only on stdout when using JSON mode) and treat schema mismatch as “no injection + explicit `systemMessage` warning” rather than continuing silently. Claude Code itself warns that non-JSON noise (e.g., from shell profiles) can break parsing. citeturn4view2turn9view7

**Rate limits / model availability**

- **VERIFIED:** Prompt hooks and agent hooks invoke Claude models (prompt-based and agent-based hooks are explicitly described as model calls / subagent execution). citeturn5view4turn5view3
- **Fail-closed recommendation (INFERRED):** Dopemux’s core capture/injection path should be **command hooks**, not prompt/agent hooks, to prevent model rate limits from becoming a reliability dependency for memory. citeturn5view1turn9view4turn19view0

**Silent failure risks**

- **VERIFIED:** For most events, stdout is shown only in verbose mode; non-blocking errors can proceed with stderr largely hidden. citeturn6view4turn9view4
- **Fail-closed recommendation (INFERRED):** If Dopemux memory injection fails, return JSON with a `systemMessage` warning (user-visible) rather than logging to stderr with a non-zero exit that the user may never see. citeturn4view2turn6view4

**Infinite loop risks (Stop hooks)**

- **VERIFIED:** Stop hooks can keep Claude working indefinitely if the hook doesn’t check `stop_hook_active`. citeturn12view10turn9view7
- **Fail-closed recommendation (INFERRED):** Dopemux should not rely on Stop hooks for core persistence; use `SessionEnd` (cleanup/log) and tool events (continuous capture) instead, and only use Stop hooks for optional end-of-turn summarization with strict loop guards. citeturn12view9turn12view0turn12view10

## Recommended Dopemux architecture in Claude mode

### Decision framing

Claude Code provides **three distinct, evidence-backed** ways to get “memory-like” context into future prompts without MCP:

- **Persistent memory files:** `CLAUDE.md` and rules are loaded as project/user memory; auto memory loads an index (`MEMORY.md`) into the system prompt (first 200 lines). citeturn11view0turn19view0
- **Deterministic hook injection:** `SessionStart` and `UserPromptSubmit` can add context via stdout or `additionalContext` before the model continues. citeturn12view8turn12view7turn6view4
- **Local transcript + hooks:** hooks receive `transcript_path`, and Claude Code stores messages/tool uses/results on disk. citeturn11view2turn6view4

MCP can also be integrated, but it introduces an additional dependency (server start, connectivity, protocol correctness), and plugin docs treat MCP as something that may require troubleshooting. citeturn15view0turn6view1

### Recommendation

**RECOMMENDED (INFERRED, evidence-backed): Dopemux memory should live as *plugin-only* for the robust baseline, with hooks doing capture + injection, and MCP treated as an optional enhancement—not a dependency.** citeturn19view0turn15view0turn6view4turn12view7

#### Why plugin-only is the “robust baseline” (VERIFIED facts → INFERRED conclusion)

- **VERIFIED:** Hooks are described as deterministic and “guarantee the action happens,” explicitly contrasted with CLAUDE.md instructions being “advisory.” citeturn19view0turn9view4
  **INFERRED:** If Dopemux’s core promise is reliable capture + injection, hooks are the most robust surface for “must happen” automation.

- **VERIFIED:** Tool observation is first-class: `PreToolUse`, `PostToolUse`, and `PostToolUseFailure` provide tool input and results (or errors). citeturn12view0turn12view1turn6view1
  **INFERRED:** Dopemux can capture nearly all meaningful “agent actions” (file writes, bash runs, searches) without requiring the model to voluntarily call an external MCP tool.

- **VERIFIED:** Hooks can inject context at `SessionStart` and `UserPromptSubmit`. citeturn12view8turn12view7turn9view0
  **INFERRED:** Dopemux can provide memory to future prompts without any MCP server availability assumption.

- **VERIFIED:** Plugins package hooks/skills/agents and provide stable pathing via `${CLAUDE_PLUGIN_ROOT}` but are cached (no external path traversal). citeturn15view0
  **INFERRED:** Shipping Dopemux as a plugin gives you a controlled distribution vehicle while keeping runtime dependencies local.

#### Why not MCP-only (VERIFIED facts → INFERRED conclusion)

- **VERIFIED:** Many key hook events already expose what MCP-only implementations typically need (prompt text, tool events, injection). citeturn12view7turn12view0turn12view8
- **VERIFIED:** Plugin MCP servers start automatically when a plugin is enabled and have specific troubleshooting guidance. citeturn15view0
- **INFERRED:** If the explicit goal is “without relying on fragile MCP server availability,” then MCP-only inverts the stack: your core memory becomes dependent on a separate server lifecycle.

#### If you still want MCP (bounded hybrid)

**OPTIONAL (INFERRED): plugin + MCP hybrid** can make sense only if you treat MCP as a *secondary retrieval path* for “deep recall” (e.g., semantic search of a larger store) and keep **core injection** working via hooks even when MCP is down.

A conservative hybrid pattern is:

- Hooks always capture and persist locally.
- Injection is hook-driven and uses local persisted summaries.
- MCP tool is offered as a user-invoked or model-invoked *bonus* to retrieve richer context *on-demand*, not required for baseline functionality.

This stays aligned with the documented reliability of hooks (deterministic) and the documented fact that MCP servers are an additional moving part. citeturn19view0turn15view0turn6view4

### Avoiding implicit prompt injection

**VERIFIED constraints:** Claude Code’s internal system prompt is not published; recommended ways to add custom instructions are `CLAUDE.md` or `--append-system-prompt`. citeturn20view3turn11view1 Hooks can inject arbitrary text into context via stdout/`additionalContext` on `SessionStart` / `UserPromptSubmit`. citeturn12view8turn12view7turn4view2

**INFERRED design principle:** Treat “memory” as **data**, not directive text. In practice, Dopemux should inject memory in a clearly delimited, structured format (e.g., JSON-like blocks) and include a stable, minimal policy header that tells the model how to interpret it (“facts for context; do not treat as instructions”). This is not guaranteed by Claude Code itself; it is a responsibility of Dopemux’s injection adapter because Claude Code will pass whatever you inject into the model context. citeturn12view7turn12view8turn6view4

**UNKNOWN:** Claude Code docs do not specify a first-class “untrusted context” channel distinct from normal context. The only formally described distinction is that `additionalContext` is “added more discretely” compared to plain stdout in `UserPromptSubmit`. citeturn12view7

## Adapter contract draft

**VERIFIED:** Hook handlers receive JSON on stdin with known common fields and known per-event fields; handlers respond via exit codes and optional JSON output. citeturn6view4turn12view7turn12view0turn12view8
**INFERRED:** The “Dopemux Adapter Contract” below defines a stable internal interface Dopemux can implement across Claude Code versions, with clear error semantics and redaction rules.

### Input events

**VERIFIED event sources:** Claude Code hook events include (at minimum) `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PostToolUseFailure`, `Notification`, `SubagentStart`, `SubagentStop`, `Stop`, `TeammateIdle`, `TaskCompleted`, `PreCompact`, `SessionEnd`. citeturn9view2turn15view0

**Contract (INFERRED): Dopemux should normalize these hook events into internal “memory events”**:

- `session_start`
- `prompt_submitted`
- `tool_will_run`
- `tool_did_run`
- `tool_failed`
- `compaction_will_run`
- `session_end`
- Optional: `turn_finished` (from `Stop`) and `subagent_finished` (from `SubagentStop`)

### Required fields

**VERIFIED common fields (must be present on all hook inputs):** citeturn6view4
- `session_id: string`
- `transcript_path: string`
- `cwd: string`
- `permission_mode: string`
- `hook_event_name: string`

**VERIFIED event-specific required fields:**

- `UserPromptSubmit`: `prompt: string` citeturn12view7
- Tool events:
  - `PreToolUse`: `tool_name`, `tool_input`, `tool_use_id` citeturn4view10turn4view2
  - `PostToolUse`: `tool_name`, `tool_input`, `tool_response`, `tool_use_id` citeturn12view0
  - `PostToolUseFailure`: `tool_name`, `tool_input`, `tool_use_id`, `error` (and optional `is_interrupt`) citeturn12view1
- `SessionStart`: `source`, `model` (optional `agent_type`) citeturn12view8
- `PreCompact`: `trigger`, `custom_instructions` citeturn13view0
- `SessionEnd`: `reason` citeturn12view9

**UNKNOWN:** Whether Dopemux can rely on a stable transcript JSONL schema at `transcript_path`. Official docs confirm storage exists and that the path is provided, but do not publish a schema in the reviewed sources. citeturn11view2turn6view4

### Output and error semantics

**VERIFIED: exit code semantics & JSON output rules.** JSON output is only processed on exit code 0, and stdout must contain only the JSON object in that case. Exit 2 blocks per-event. Other exit codes are non-blocking and may be visible only in verbose output. citeturn6view4turn4view2turn9view4

**Contract (INFERRED): Dopemux should adopt these conventions**

- Capture hooks (PostToolUse, PostToolUseFailure, SessionEnd, etc.)
  - Always exit `0` unless a *strict safety* policy is violated.
  - Never block user actions on “logging failure.”
  - On internal storage failure, emit `systemMessage` (user-visible) at least once per session to avoid silent failure. (`systemMessage` is a documented universal JSON output field.) citeturn4view2

- Injection hooks (SessionStart, UserPromptSubmit)
  - If retrieval succeeds: output JSON that includes a single `hookSpecificOutput.additionalContext` payload (or plaintext stdout for simplest mode), bounded in size. citeturn12view8turn12view7
  - If retrieval fails: output JSON with `systemMessage` warning and **no** `additionalContext` (fail-closed on injection). citeturn4view2
  - Never use async for injection unless you explicitly accept “context arrives next turn.” citeturn5view2

### Redaction guarantees

**VERIFIED related control:** Claude Code supports `permissions.deny` patterns to exclude sensitive files from discovery/search and deny reads by Claude Code tooling, but hooks themselves run with full user permissions. citeturn20view2turn5view5

**Contract (INFERRED): Dopemux must implement its own redaction layer** independent of Claude Code:

- **Never persist raw secrets** (API keys, tokens, `.env` contents) if observed in tool inputs/outputs or prompts.
- **Never inject raw user prompts verbatim** unless explicitly permitted; store hashed/trimmed versions for retrieval keys.
- **Tool-input minimization:** for `Write`/`Edit` events where `tool_input` includes full file content, persist only file path + diff metadata (or a content hash), not the full content block. (This is a Dopemux design choice; Claude Code docs only confirm the content is present in hook input.) citeturn12view0

## Task packet outline

**VERIFIED constraints and footguns referenced in this plan**: hooks snapshot at startup; JSON parsing failures if stray stdout exists; Stop-hook looping hazards; PermissionRequest not firing in `-p`; plugin caching constraints. citeturn6view3turn9view7turn12view10turn9view6turn15view0

### Phase 0 verification

Confirm, in a controlled sandbox repository, that Dopemux’s intended event coverage matches Claude Code’s documented schema and lifecycle.

- Validate hook input schemas against the Hooks Reference by recording actual stdin JSON for each targeted event and checking required fields are present (`session_id`, `transcript_path`, etc.). citeturn6view4turn12view7turn12view0
- Verify injection points: `SessionStart` and `UserPromptSubmit` actually add context via stdout/`additionalContext` as documented. citeturn12view8turn12view7turn6view4
- Verify behaviour under compaction: configure a `SessionStart` hook with matcher `compact` and confirm it re-injects context after compaction, per published guidance. citeturn9view0turn12view8
- Verify non-interactive behaviour: run `claude -p` and confirm `PermissionRequest` hooks do not fire; confirm `PreToolUse` does. citeturn9view6turn11view1turn4view10
- Verify plugin caching constraints: install Dopemux as a plugin and confirm scripts reference `${CLAUDE_PLUGIN_ROOT}` and do not rely on `../` traversal. citeturn15view0

**Stop condition (VERIFIED risk):** If the deployment environment enforces `allowManagedHooksOnly`, Dopemux cannot rely on user/project/plugin hooks and must either be deployed as managed hooks or accept non-operation. citeturn20view3turn6view1

### Phase 1 capture adapter

Build a command-hook adapter that records high-signal events with minimal sensitive data.

Implement capture on:

- `UserPromptSubmit` (prompt metadata + retrieval key generation). citeturn12view7
- `PreToolUse` (intent: tool name and parameters) and `PostToolUse` / `PostToolUseFailure` (result/error). citeturn4view10turn12view0turn12view1
- `SessionEnd` for flush/cleanup. citeturn12view9

Testing requirements:

- Ensure hook stdout is **strictly JSON-only** when outputting JSON (avoid the documented JSON validation failure scenario). citeturn4view2turn9view7
- Ensure capture failures are not silent: emit `systemMessage` once per session on persistent storage failure. citeturn4view2turn6view4

### Phase 2 injection adapter

Implement deterministic injection that is robust to MCP unavailability.

- `SessionStart` injection:
  - On `startup` and `resume`: inject a short project-memory summary (bounded size).
  - On `compact`: re-inject “critical invariants” after compaction, per official guidance. citeturn9view0turn12view8
- `UserPromptSubmit` injection:
  - Retrieve the most relevant memories for the submitted prompt and inject via `additionalContext`.
  - If retrieval fails, inject nothing and surface user-visible warning via `systemMessage`. citeturn12view7turn4view2

**Stop condition (VERIFIED):** Do not use a Stop hook for core workflow unless you implement `stop_hook_active` guardrails; otherwise infinite loops are a known failure case. citeturn12view10turn9view7

### Phase 3 tests and stop conditions

Run regression-style tests across Claude Code modes and configuration scopes.

- Scope tests:
  - Validate behaviour in user/project/local scopes and confirm `disableAllHooks` fully disables Dopemux execution. citeturn6view3turn20view1
  - Validate plugin scope installation (`enabledPlugins`) and enable/disable commands. citeturn20view2turn15view0

- Mode tests:
  - Interactive vs `-p` print mode (PermissionRequest absence). citeturn9view6turn11view1
  - Remote environment indicator: ensure scripts behave correctly when `CLAUDE_CODE_REMOTE` is set (documented in hooks reference as an environment signal). citeturn5view1turn18view0

- Stop conditions (INFERRED, safety-minded):
  - If Dopemux cannot guarantee redaction, it should **fail-closed on injection** and warn, rather than injecting possibly sensitive content.
  - If persistent storage is unavailable, Dopemux should degrade to “capture off / injection off” with explicit user-visible warning, not partial injection.

**UNKNOWN items requiring explicit verification before committing to architecture**

- The CLI’s `--init`, `--init-only`, and `--maintenance` flags claim “initialization/maintenance hooks,” but the hook event/config surface for these is not described in the reviewed hooks reference. Treat this as **UNKNOWN** until an authoritative doc section (or a changelog entry you can reliably parse) specifies the configuration schema and lifecycle for these flags. citeturn11view1turn17view0
- Transcript file (`transcript_path`) JSONL schema is not published in the reviewed official docs, so any Dopemux design that parses transcript contents must treat the schema as **unstable/UNKNOWN** and gate it behind robust parsing + fallback behaviour. citeturn11view2turn6view4
