---
id: deep-research-report 1
title: Deep Research Report 1
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-11'
last_review: '2026-02-11'
next_review: '2026-05-12'
prelude: Deep Research Report 1 (explanation) for dopemux documentation and developer
  workflows.
---
# DR-CLI-INT-01 — Agent CLI Integration Surfaces for Dopemux

## Sources and scope notes

This research prioritizes primary sources: official documentation from entity["company","Anthropic","ai company"] and entity["company","GitHub","code hosting company"], plus repo-level primary material for entity["company","Microsoft","software company"]’s Codex-CLI precedent. citeturn23view0turn23view1turn23view2turn27search0turn5view0turn23view3turn15view0

“Claude Code” and “GitHub Copilot CLI” both expose stable lifecycle hook surfaces and MCP integration points, so the stop conditions do **not** trigger. citeturn25view7turn5view0turn4view0turn23view3turn9view0

## Capability matrix

Copy/pasteable table. “UNKNOWN” means I could not confirm from the sources above; I list the next-best artifact to fetch in the “Risk notes” column.

| CLI | Hook points (pre / post / tool-call / command-done / session-end) | Tool protocol support | Config locations + formats | Transcript availability + structure | “Memory” concept (native) + where it lives | Sandboxing / execution model | Auth / secrets flow | Determinism knobs (temp, replayability, etc.) | Extension risk notes |
|---|---|---|---|---|---|---|---|---|---|
| Claude Code | **Yes.** SessionStart, UserPromptSubmit, PreToolUse, PermissionRequest, PostToolUse, PostToolUseFailure, PreCompact, Stop, SubagentStop, SessionEnd (plus subagent transcript surfaces). citeturn25view0turn25view1turn25view2turn25view3turn25view6 | **MCP:** project-scoped `.mcp.json`, plus user/local MCP state in `~/.claude.json`. citeturn23view0turn21search5 **Plugins:** plugin format supports hooks + agents + skills; plugin hooks are merged with user/project hooks. citeturn21search5turn22search5 | `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json`. Managed enterprise settings + managed MCP files exist. Also `~/.claude.json` stores preferences, OAuth session, per-project trust/allowed-tools state, caches, and MCP configs (user/local scopes). citeturn23view0 | **Yes.** Hooks receive `transcript_path` pointing to a per-session JSONL file under `~/.claude/projects/.../*.jsonl`. Subagents have their own transcript paths in nested `subagents/` folders. citeturn21search1turn25view6 **Schema:** JSONL line schema is not fully specified in docs → **UNKNOWN**. | **Yes (file-based).** Hierarchical `CLAUDE.md` “memory files” (enterprise, project, user, local) are loaded into context; imports supported; `/memory` to inspect/edit. citeturn26search0turn23view0 Also “auto memory” can be disabled with env var `CLAUDE_CODE_DISABLE_AUTO_MEMORY`. citeturn24view4 | **Yes (native sandboxing).** Sandboxed bash tool provides filesystem + network isolation; configured via `settings.json` sandbox keys and permission rules; OS primitives enforce isolation. Limitations include platform support and command compatibility. citeturn27search0turn27search1 Interactive execution includes backgrounding Bash with Ctrl+B and retrieving buffered output via BashOutput tool. citeturn28search0 | Multiple routes: `/login` (OAuth) is the interactive path; env var `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN` supported; `apiKeyHelper` can generate auth headers. citeturn23view0turn24view4 | **Model selection:** `model` setting supported. citeturn23view0 **Compaction threshold:** adjustable via `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`. citeturn24view4 **Replayability / temperature / seeding:** no explicit knobs found in settings docs → **UNKNOWN**. | Silent no-op risks: hooks can be disabled (`disableAllHooks`) or constrained by managed policy (`allowManagedHooksOnly`). citeturn23view0 Transcript retention is finite: local session cleanup default 30 days (configurable). citeturn23view0turn22search1 Ordering/races: multiple hooks (including plugin hooks) can run for same event; define deterministic merge + write strategy (your side). citeturn22search5turn2search6 |
| Copilot CLI | **Yes.** `sessionStart`, `userPromptSubmitted`, `preToolUse`, `postToolUse`, `sessionEnd`, `errorOccurred`. Input JSON schemas documented. citeturn7view0turn7view1turn7view2turn6view6turn7view3 | **MCP:** supports MCP servers; server config stored in `mcp-config.json` under `~/.copilot` by default; supports disabling built-in MCPs. citeturn4view0turn23view3 Hook system executes shell commands on lifecycle events. citeturn5view0turn6view6 | Config in `~/.copilot/config.json` by default; location affected by `XDG_CONFIG_HOME`; also `--config-dir` CLI flag exists. citeturn4view0turn23view3 Hooks: for Copilot CLI, hooks are loaded from the current working directory. citeturn4view4 | **No official transcript file pointer in hook input.** Hook inputs include timestamp/cwd/toolName/toolArgs (and toolResult for post) but not a transcript path. citeturn6view6turn7view0turn7view1 You can build your own JSONL logs using hooks (example shows structured logging). citeturn6view6 **If resuming hosted coding-agent sessions:** GitHub session logs exist (internal monologue + tools used) but this is documented for coding agent sessions, not explicitly as a local “transcript file” for Copilot CLI. citeturn13view1 | **Yes, but opaque/vendor-managed.** Copilot Memory is repo-scoped; can be enabled/curated in GitHub settings; auto-deletes after 28 days; used by Copilot CLI. citeturn26search1turn26search3 Local “trusted folders” list lives in `config.json` (`trusted_folders` array). citeturn8search0 | Execution is permission- and trust-gated: user must trust directory; tool approvals exist; flags allow/deny tools and MCP servers. Tool protection outside trusted dirs is heuristic and not guaranteed. Recommended mitigation: run in restricted environment (VM/container) if using auto-approvals. citeturn4view3turn8search0turn8search1 | Auth via `/login` (interactive). Repo README also documents PAT-based auth: fine-grained PAT with “Copilot Requests” permission via `GH_TOKEN`/`GITHUB_TOKEN`. citeturn9view0 | Model choice appears user-switchable (`/model` in README) and tool shows token usage + auto history compression near token limit (95%). citeturn9view0turn8search4 Replayability / temperature / seeding: not documented in surfaced sources → **UNKNOWN**. | High change risk: CLI is explicitly “public preview” and subject to change. citeturn8search4turn9view0 Silent-no-op: hooks only load if the hooks JSON is in the expected location and valid. citeturn4view4turn5view0 Tool-scoping heuristics make “safe boundary” assumptions brittle; prefer explicit deny rules + sandboxing around the CLI. citeturn8search0 |
| Codex-CLI (precedent) | **No formal hooks.** Interaction is via shell comments + hotkey (Ctrl+G) to generate suggested commands; has internal “commands” like `start multi-turn`, `stop multi-turn`, `set <config-key>`, etc. citeturn15view0turn19search0 | **No MCP/tool registry** in described design; it’s NL → shell-command generation. citeturn15view0turn19search0 | Context examples live in `contexts/` directory; tool writes `current_context.txt` for multi-turn history. Config is modifiable via `set` command (engine, temperature, max_tokens), but persistent config file location is **UNKNOWN** from the accessible sources. citeturn15view0turn19search0 | Transcript-like history is `current_context.txt` in multi-turn mode; otherwise history is not tracked. Precise on-disk format beyond “context text file” is **UNKNOWN**. citeturn15view0turn19search0 | Memory is literally multi-turn mode: prior interactions appended to `current_context.txt`, passed to model on each prompt; multi-turn off is “no memory”. citeturn15view0turn19search0 | No sandboxing described; it generates commands and warns users not to run commands they don’t understand. It is not described as autonomously executing tools. citeturn15view0turn19search0 | Requires entity["company","OpenAI","ai company"] account + API key, org id, and engine id (examples include `code-davinci-002`). citeturn15view0turn19search0 | Determinism claim exists: when multi-turn mode is off, “the same command will always produce the same output”; temperature configurable. (Note: this reflects intent; real LLM APIs are typically stochastic unless hard-constrained.) citeturn15view0turn19search0 | Red flag: repo explicitly states it is **not intended to be a released product** (Build 2022 reference). Treat as historical precedent, not stable integration target. citeturn15view0turn19search0 |

## Integration patterns for Dopemux

Below are 5 patterns designed to maximize leverage across **memory + PM + ADHD + search** planes while respecting tool safety boundaries.

Each is copy/pasteable: it includes (a) exact lifecycle event(s), (b) capture schema fields, (c) write targets (“chronicle” + “derived”), (d) failure mode + fail-closed rule, and (e) privacy boundary expectations.

### Pattern A — Session envelope capture

**When it fires (exact lifecycle event)**
- Claude Code: `SessionStart` and `SessionEnd`. citeturn25view1turn25view2
- Copilot CLI: `sessionStart` and `sessionEnd`. citeturn7view0turn7view1

**What we capture (event schema fields)**
Use a canonical envelope that can be emitted by either hook system:

```json
{
  "event_type": "session.start | session.end",
  "event_version": 1,
  "emitter": "claude-code | copilot-cli",
  "ts": { "unix_ms": 0, "source": "hook_input" },
  "session": {
    "session_id": "string",
    "cwd": "string",
    "project_dir": "string",
    "model": "string",
    "source": "startup|resume|new|clear|compact|...",
    "end_reason": "complete|error|abort|timeout|user_exit|other|..."
  },
  "pointers": {
    "transcript_path": "string|null",
    "subagent_transcripts": ["string"]
  },
  "policy": {
    "permission_mode": "default|plan|acceptEdits|dontAsk|bypassPermissions|UNKNOWN"
  }
}
```

Why these fields are stable: both CLIs give `cwd` + session timing, and Claude Code provides `session_id`, `model`, `source`, and `reason` plus `transcript_path`. citeturn25view1turn25view2turn7view0turn7view1turn21search1

**Where we write (chronicle + derived)**
- Chronicle: append-only JSONL per workspace (recommended):
  - `.dopemux/chronicle/session_events.jsonl` (workspace-local)
  - plus a rolling cache `~/.cache/dopemux/session_index.json` for fast lookup
- Derived:
  - Update “active session” node in memory graph (ConPort-like)
  - Update ADHD plane timers (session duration, break cadence)
  - Emit “session.start/end” to the PM plane router for correlation (task ↔ session)

**Failure mode + fail-closed rule**
- Failure modes: hook script missing, logging pipeline down, disk full.
- Fail-closed: **do not write partial/unredacted payloads**. If redaction fails, write only `{event_type, emitter, session_id, cwd_hash}` (or write nothing) and continue; *never* dump raw prompt/tool args on error.

**Privacy boundary (redaction expectations)**
- Redact: API keys/tokens, `.env` values, secrets file contents, and any `Authorization`-like strings.
- Hash or relativize: absolute paths (see determinism notes) before persistence.
Claude Code settings explicitly recommend using deny rules to make sensitive files “completely invisible,” which is aligned with this boundary. citeturn23view0

### Pattern B — Tool-call audit trail without injection

**When it fires (exact lifecycle event)**
- Claude Code: `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, and optionally `PermissionRequest`. citeturn25view0turn25view6
- Copilot CLI: `preToolUse`, `postToolUse`. citeturn6view6

**What we capture (event schema fields)**

```json
{
  "event_type": "tool.pre | tool.post | tool.fail",
  "event_version": 1,
  "emitter": "claude-code | copilot-cli",
  "ts": { "unix_ms": 0 },
  "session": { "session_id": "string", "cwd": "string" },
  "tool": {
    "name": "string",
    "args": "object|json_string",
    "result": "object|null",
    "result_type": "success|failure|denied|UNKNOWN"
  },
  "pointers": { "transcript_path": "string|null" }
}
```

Field availability differs by CLI: Copilot provides `toolName` and `toolArgs` (as a JSON string) pre-tool, plus `toolResult` post-tool. citeturn6view6 Claude Code provides `tool_name`, rich `tool_input`, and post-tool `tool_response`, plus transcript path. citeturn21search1turn25view0

**Where we write (chronicle + derived)**
- Chronicle: append full tool audit lines to `.dopemux/chronicle/tool_events.jsonl`.
- Derived: ADHD plane can compute “cognitive load heuristics” (e.g., long-running bash, repeated failures); search plane indexes tool activity for later recall (“what commands did I run last Tuesday?”).

**Failure mode + fail-closed rule**
- Failure modes: cannot parse toolArgs JSON; transcript missing; hook times out.
- Fail-closed: if toolArgs cannot be parsed, store a **lossy** payload: `{tool.name, tool.args_raw_sha256}` and set `"tool.args": null`. Do not block execution for logging failures in capture-only mode.

**Privacy boundary (redaction expectations)**
- Treat tool inputs as sensitive by default; only persist allowlisted fields (e.g., for `bash`, store `command` but redact env var expansions; for file writes, store path + hash of content).
Claude Code’s hook inputs explicitly include file paths and contents for write tools, so strict redaction is mandatory. citeturn21search1

### Pattern C — Opt-in injection per lane using Claude Code prompt hooks

This pattern is **only confirmed as fully supported** in Claude Code because hooks can add context and (for some events) control flow. Copilot hook output is primarily for running commands / decisions, and does not document a native “add context to prompt” mechanism. citeturn25view4turn6view6turn7view2

**When it fires (exact lifecycle event)**
- Claude Code: `UserPromptSubmit` (before the prompt is processed). citeturn25view4

**What we capture (event schema fields)**
- `prompt`
- `session_id`, `cwd`, `permission_mode`, `transcript_path` (for anchoring) citeturn25view4turn21search1
- User’s lane-consent state (from config; see below)

**Where we write (chronicle + derived)**
- Chronicle: record prompt + which lanes were injected (not the injected text if it contains sensitive derived content—store hashes).
- Derived:
  - Memory plane: update “working set” (recent decisions / current focus)
  - PM plane: link prompt to active task id (if present)
  - ADHD plane: attach attention mode label (e.g., “quickfix / act / plan”)

**Opt-in mechanism (copy/pasteable)**
Recommended: a Dopemux-owned config that maps lanes to injection sources:

```json
{
  "dopemux": {
    "injection": {
      "enabled": true,
      "lanes": {
        "memory": { "enabled": true, "max_tokens": 350 },
        "pm":      { "enabled": false, "max_tokens": 250 },
        "adhd":    { "enabled": true, "max_tokens": 120 },
        "search":  { "enabled": false, "max_tokens": 0 }
      }
    }
  }
}
```

**Hook behavior**
- If enabled: return `additionalContext` containing **only** the enabled lanes, each clearly labeled, each size-capped. Claude Code explicitly supports adding context from `UserPromptSubmit` hooks. citeturn25view4
- If disabled: return nothing; capture-only.

**Failure mode + fail-closed rule**
- Failure modes: derived lane generator fails; config missing; size cap exceeded.
- Fail-closed: **inject nothing** (empty additionalContext), but still allow the prompt to proceed. Never inject a partially built blob.

**Privacy boundary (redaction expectations)**
- Lane content must be pre-redacted and policy-checked.
- Explicitly avoid injecting secrets by ensuring the sensitive files are denied at the Claude Code permission layer as well (defense in depth). citeturn23view0

### Pattern D — Dual adapter mode for MCP tooling contracts

Goal: make Dopemux work whether you can hook the CLI lifecycle **or** you can only observe MCP tool use.

**When it fires (exact lifecycle event)**
- MCP adapter: fires on any tool invocation matching `mcp__<server>__<tool>` (tool-call boundary).
- Hook adapter: fires on lifecycle hooks (`PreToolUse`/`PostToolUse` or Copilot `preToolUse`/`postToolUse`). citeturn25view0turn6view6turn23view0

**What we capture (event schema fields)**

```json
{
  "event_type": "mcp.tool.call",
  "event_version": 1,
  "transport": "stdio|http",
  "mcp": {
    "server": "string",
    "tool": "string",
    "request": "object",
    "response": "object|null",
    "error": "object|null"
  },
  "session": { "session_id": "string|UNKNOWN", "cwd": "string|UNKNOWN" },
  "ts": { "unix_ms": 0 }
}
```

MCP is explicitly positioned as the standard mechanism for external tool integration in Claude ecosystems, and Copilot CLI also supports MCP servers with configuration stored locally. citeturn0search4turn4view0turn23view3

**Where we write (chronicle + derived)**
- Chronicle: `.dopemux/chronicle/mcp_events.jsonl`
- Derived: search plane can index MCP responses; memory plane can store “facts learned from tools” with provenance.

**Failure mode + fail-closed rule**
- If MCP proxying is used: fail-closed should be **deny tool execution** if you cannot enforce redaction / policy checks, because MCP tools can exfiltrate data.
- If only passive observation: fail-closed should be **drop event** (not persist) if you cannot redact.

**Privacy boundary (redaction expectations)**
- MCP payloads frequently contain raw data (tickets, secrets, code blobs). Default to “store hashes + metadata” unless server/tool is explicitly allowlisted.

### Pattern E — Transcript harvesting and integrity sealing

This pattern is where Dopemux gets “real memory leverage”: you can build durable, searchable, replay-aware artifacts from transcripts.

**When it fires (exact lifecycle event)**
- Claude Code: `SessionEnd` (primary), plus optional periodic sealing on `PreCompact` to preserve pre-compaction state. citeturn25view2turn25view3
- Copilot CLI: no transcript pointer; use your own hook-built logs → run at `sessionEnd`. citeturn7view1turn6view6

**What we capture (event schema fields)**
- `transcript_path` (Claude Code) and a content-derived integrity hash (SHA-256 of entire JSONL). citeturn21search1turn25view2
- A derived “session manifest”:

```json
{
  "session_id": "string",
  "transcript_path": "string",
  "transcript_sha256": "string",
  "tool_count": 0,
  "files_touched": ["rel/path"],
  "token_usage": { "used": 0, "limit": 0, "pct": 0.0 },
  "compactions": 0,
  "model": "string"
}
```

Claude Code status line input includes structured cost + duration + code-diff metrics that can support the manifest even if transcript parsing is imperfect. citeturn22search3

**Where we write (chronicle + derived)**
- Chronicle: store manifest + hash; store the raw transcript file path (not necessarily the content)
- Derived:
  - Memory plane: session summary → “decisions / learnings” nodes
  - PM plane: “work performed” linked to tasks
  - ADHD plane: “overwhelm signals” / break compliance
  - Search plane: index transcript into dope-context-like semantic search

**Failure mode + fail-closed rule**
- If transcript missing: fail-closed to **log a manifest with `"transcript_path": null`** and set a “integrity=false” flag; do not fabricate.
- If hashing/parsing fails: do not store partial content; store only pointer + failure reason.

**Privacy boundary (redaction expectations)**
- Prefer storing transcripts locally and indexing derived embeddings **workspace-scoped**; never cross-contaminate across workspaces.
- Retention: Claude Code local sessions can be cleaned up after inactivity (default 30 days), so harvesting must occur before retention expiry. citeturn23view0turn22search1

## Hard constraints and red flags

These are the highest-risk items for “silent no-op,” transcript integrity, and cross-machine determinism.

Silent no-op risks concentrate around configuration precedence and “loaded from where” logic.

Claude Code can disable hooks globally (`disableAllHooks`) and can further restrict hook loading by managed policy (`allowManagedHooksOnly`). If Dopemux depends on hooks for capture or policy gating, the absence of hooks may not always be obvious unless you also emit a SessionStart “I am alive” marker. citeturn23view0

Copilot CLI hooks are loaded from the **current working directory** (not a global location), so running the CLI from the wrong directory turns your integration into a silent no-op. citeturn4view4 Additionally, hooks require a valid config file format (versioned JSON). citeturn5view0

Transcript integrity is robust in Claude Code (explicit `transcript_path` and per-subagent transcript pointers), but retention is finite and compaction can occur; if Dopemux requires a complete audit trail you should seal pre-compaction state using `PreCompact` and harvest on `SessionEnd`. citeturn25view3turn25view2turn22search1

Copilot CLI does not surface a stable transcript-path pointer in hook input; you must create your own structured logs. That means transcript integrity is “your responsibility,” and can diverge across machines if scripts differ. citeturn6view6turn7view1 Hosted Copilot coding-agent session logs do exist and include internal monologue and tools, but they are documented as part of the coding agent session viewer, not as a guaranteed local CLI transcript artifact. citeturn13view1

Cross-machine determinism will be broken by: absolute paths (`cwd`, file paths in tool args), timestamps (both Copilot and Claude hook inputs include them), system-dependent tool outputs, and background concurrency. Copilot hook inputs explicitly include `timestamp` and `cwd`; Claude hook inputs include `cwd` and transcript paths under user directories. citeturn6view6turn7view0turn21search1

A particularly sharp edge: **tool safety boundaries are not equivalent to sandboxing**. Copilot explicitly warns directory trust scoping is heuristic and not guaranteed to protect all files outside trusted directories. If you ever enable broad auto-approvals, you should assume you need an external sandbox (VM/container) to enforce real boundaries. citeturn8search0 Claude Code, by contrast, provides a first-class sandboxed bash tool with OS-level filesystem+network isolation, but some commands may be incompatible unless configured as excluded/unsandboxed (which weakens safety if misused). citeturn27search0turn27search1

Finally, Codex-CLI (precedent) is explicitly not a product and should not be treated as a stable extension platform; its value is conceptual: multi-turn context as a file, and a user-visible “set temperature/engine/max_tokens” control surface. citeturn15view0turn19search0

## Recommended minimal viable integration

A “2-week” MVP that minimizes surface area but yields real wins should prioritize **capture + sealing + opt-in injection** on the platform that actually exposes stable, rich lifecycle + transcript pointers: Claude Code. citeturn25view7turn21search1turn25view4

Week one should deliver a single Dopemux hook runner with three responsibilities: (1) normalize event envelopes (Pattern A/B), (2) enforce privacy redaction, and (3) append to a workspace chronicle JSONL. Claude Code provides high-leverage events (`SessionStart`, `UserPromptSubmit`, `PreToolUse`, `SessionEnd`) and explicit transcript pointers for harvesting. citeturn25view1turn25view4turn25view2turn21search1 Use `SessionStart` as your “health beacon” and emit a small, deterministic record so you can detect silent no-op early. citeturn25view1

Also in week one: implement a strict fail-closed policy for **exfiltration-shaped tool calls**. On Claude Code, `PreToolUse` decision control supports allow/deny/ask plus `updatedInput`, and there is a dedicated `PermissionRequest` event if you want to auto-decide when a permission dialog is about to appear. citeturn25view0turn25view0 (This is where Dopemux can enforce “consent-first” and avoid approval fatigue by allowing only within the sandbox or within explicit allowlists.) Sandboxing can reduce approval fatigue while maintaining safety if configured correctly. citeturn27search0turn27search1

Week two should add opt-in lane injection (Pattern C) for Claude Code only: on `UserPromptSubmit`, inject small, labeled lane summaries based on a Dopemux config allowlist. Claude Code explicitly supports adding context via prompt hooks; keep it size-capped and never inject sensitive data. citeturn25view4turn23view0turn26search0 In parallel, implement transcript harvesting/sealing (Pattern E) so your memory + search planes aren’t hostage to 30‑day local retention defaults. citeturn23view0turn22search1turn25view2

If you have bandwidth in week two, add Copilot CLI capture-only parity using its hooks system (Pattern A/B) and the documented hook input JSON schemas. citeturn5view0turn6view6turn7view0 Treat Copilot Memory as a complementary, vendor-managed feature: useful, but not a reliable substrate for Dopemux because it’s repository-scoped, preview, and not presented as a programmable transcript surface. citeturn26search1turn26search3
