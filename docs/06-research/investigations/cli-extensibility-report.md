---
id: CLI_EXTENSIBILITY_REPORT
title: Cli Extensibility Report
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-18'
last_review: '2026-03-18'
next_review: '2026-06-16'
prelude: Cli Extensibility Report (explanation) for dopemux documentation and developer
  workflows.
---
# Reconnaissance Report on CLI Extensibility and Safe Capture Surfaces

## Executive Summary

The three targets expose **very different integration surfaces**.

**entity["company","Anthropic","ai company"]’s `claude-code` repository** contains a **first-class hook and plugin ecosystem** (hooks, commands, agents, MCP integration patterns, and test harnesses) with concrete evidence that hooks receive **structured JSON input via stdin** including a `transcript_path`, and can return structured decisions (e.g., block) as JSON. This is the only target where **tool-call interception and transcript access are demonstrably reachable through documented, scriptable hooks**. citeturn31view0turn39view0turn41view1turn42view0turn32view0

**entity["company","GitHub","software company"]’s `copilot-cli` repository** (as of 2026-02-11) appears to be primarily **installer + changelog + README**, not the full runnable source code of the CLI. Nevertheless, the changelog claims multiple extensibility surfaces: `preToolUse` hooks that can deny/modify tool args, plugin installation from repos/URLs/local paths, plugin-provided hooks for session lifecycle events, and extensive MCP management. This means the integration story is **configuration/hook-surface driven**, but “source-code-first” verification of internal behavior is limited by what’s actually published in the repo. citeturn2view1turn43view0turn45view0turn45view1

**entity["company","Microsoft","technology company"]’s `Codex-CLI` repository is a Python-based “natural language → shell command completion” tooling** activated from the shell (Ctrl+G) that **pipes the current buffer into a Python script** and inserts the completion back into the interactive line editor. It has a file-based “multi-turn” context mechanism (`current_context.txt` + config), but **no hook/plugin architecture** and no tool execution abstraction layer (it emits text suggestions; it does not execute tools as a harness). Extension is primarily via **prompt/context files** and minor config commands. citeturn50view0turn50view1turn17view1turn17view0turn1view0

## Capability Matrix

| CLI | Pre-Hook | Post-Hook | Tool Intercept | Transcript Access | Plugin Support | MCP Support | Safe Capture Feasible | Risk Level |
|---|---|---|---|---|---|---|---|---|
| microsoft/Codex-CLI | No | No | No | Yes (context file) | No | No | Yes (but needs wrapper/patch) | Medium |
| anthropics/claude-code | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Medium |
| github/copilot-cli | Yes | UNKNOWN | Yes | UNKNOWN | Yes | Yes | Likely, but UNKNOWN details | High |

**Evidence anchors for matrix decisions (per CLI):**

- **microsoft/Codex-CLI:** interaction pattern is a shell plugin function that pipes the current line buffer into `src/codex_query.py` and inserts returned text; there is no generalized hook system or plugin architecture. citeturn50view0turn50view1turn50view2
- **anthropics/claude-code:** hook events explicitly include `PreToolUse`, `PostToolUse`, `Stop`, `UserPromptSubmit`, `SessionStart`, `SessionEnd` with sample JSON containing `transcript_path`; a plugin’s `Stop` hook demonstrates reading a transcript file and returning a structured `{ decision: "block", ... }`. citeturn31view0turn39view0turn39view1turn41view1turn32view0
- **github/copilot-cli:** changelog claims `preToolUse` hooks can deny tool execution and modify args, and that plugins can provide hooks for session lifecycle events; README claims MCP-powered extensibility and documents config locations (e.g., `~/.copilot/lsp-config.json`). Repository file list suggests the shipped code is not present here. citeturn43view0turn45view1turn2view1

## Detailed Findings per CLI

**microsoft/Codex-CLI**

**Verified (from repository source files and shell integration scripts)**
- **Control-plane / activation surface (shell keybinding):**
  - Bash: `create_completion()` reads the current readline buffer and computes `completion=$(echo -n "$text" | $CODEX_CLI_PATH/src/codex_query.py)` then appends it to the buffer. File: `scripts/bash_plugin.sh` (excerpt). citeturn50view0
  - zsh: similarly uses `BUFFER` and pipes to `src/codex_query.py`. File: `scripts/zsh_plugin.zsh` (excerpt). citeturn50view1
  - PowerShell: binds Ctrl+g via `Set-PSReadLineKeyHandler`, captures the buffer, pipes to `python $nl_cli_script`, inserts results. File: `scripts/powershell_plugin.ps1` (excerpt). citeturn50view2
  **Implication:** There is no “session harness” abstraction; the integration surface is “shell calls a python completer and inserts text.”

- **Native “memory” mechanism (file-based, multi-turn):**
  - `codex_query.py` instantiates `PromptFile(...)` and builds `codex_query = prefix + prompt_file.read_prompt_file(user_query) + user_query`; when multi-turn is on, it appends the `(user_query, completion)` pair into the prompt file. File: `src/codex_query.py` (excerpt). citeturn17view1
  - `prompt_file.py` defines `default_context_filename = "current_context.txt"` and a `default_config_path = ... "current_context.config"`, and writes/updates config and context. File: `src/prompt_file.py` (excerpt). citeturn17view0

- **User-exposed command surface (not extensibility hooks):**
  - `get_command_result(...)` parses inputs like `start multi-turn`, `stop multi-turn`, `load context`, `save context`, `show config`, `set temperature/max_tokens/shell/engine`. File: `src/commands.py` (excerpt). citeturn48view0

- **Setup scripts persist credentials/config and bind Ctrl+G:**
  - zsh setup writes `openaiapirc`, sources `zsh_plugin.zsh`, binds `^G`. Files: `scripts/zsh_setup.sh` (excerpt). citeturn22view0
  - bash setup writes `openaiapirc` and binds `bind -x '"\C-g":"create_completion"'`. File: `scripts/bash_setup.sh` (excerpt). citeturn22view1
  - PowerShell setup writes `openaiapirc` and injects plugin into `$PROFILE`. File: `scripts/powershell_setup.ps1` (excerpt). citeturn22view2

**UNKNOWN (not evidenced in repo code excerpts obtained)**
- Any formal **pre/post hook framework**, plugin loader, or stable tool protocol support beyond “prompt/context files” and local shell scripts is not present in the repo evidence surfaced above. citeturn50view0turn50view1turn17view1

**Inferred (explicitly labeled inference)**
- Because output is inserted directly into the interactive shell buffer, any deterministic event envelope would likely have to be generated either by (a) modifying the shell plugin scripts or (b) modifying `src/codex_query.py` to emit structured side-channel output (e.g., file/log). This is an inference from the observed I/O topology (stdin → stdout completion string). citeturn50view0turn17view1

---

**anthropics/claude-code**

**Verified (from repository docs, hook scripts, plugin config, and examples)**
- **Plugin architecture exists and is first-class in-repo:**
  - The plugins directory documents that plugins can extend behavior with custom slash commands, specialized agents, **hooks**, and **MCP servers**, and shows standard structure with `.claude-plugin/plugin.json`, `commands/`, `agents/`, etc. File: `plugins/README.md`. citeturn32view0
  - Example plugin manifests exist as JSON metadata (name/version/description). Example: `plugins/feature-dev/.claude-plugin/plugin.json`. citeturn33view2

- **Hook system supports multiple lifecycle and tool events with structured JSON input:**
  - The hook testing helper enumerates and emits sample inputs for events including **PreToolUse**, **PostToolUse**, **Stop/SubagentStop**, **UserPromptSubmit**, **SessionStart/SessionEnd**. The sample JSON includes `session_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`, and tool-specific fields such as `tool_name`, `tool_input`, and `tool_result`. File: `plugins/plugin-dev/skills/hook-development/scripts/test-hook.sh`. citeturn31view0
  - The Hook Development guide explicitly describes hooks as event-driven scripts and names supported events (including PreToolUse, PostToolUse, Stop, SubagentStop, UserPromptSubmit, SessionStart, SessionEnd, plus additional events referenced in the header metadata). It also distinguishes **plugin `hooks/hooks.json` wrapper format** vs **user `.claude/settings.json` direct format**, and provides an example PreToolUse output shape with an allow/deny/ask decision and `updatedInput`. File: `plugins/plugin-dev/skills/hook-development/SKILL.md`. citeturn41view1

- **Tool-call interception is real (not just theoretical):**
  - A concrete PreToolUse hook example (`bash_command_validator_example.py`) reads JSON from stdin, checks `tool_name == "Bash"`, inspects `tool_input.command`, and uses exit code `2` to block tool execution while emitting stderr messages. File: `examples/hooks/bash_command_validator_example.py`. citeturn28view0
  - A concrete Stop hook (`plugins/ralph-wiggum/hooks/stop-hook.sh`) reads hook input (stdin), extracts `transcript_path`, reads the transcript file, and outputs JSON with `"decision": "block"` and a `"reason"` payload to continue looping. File: `plugins/ralph-wiggum/hooks/stop-hook.sh`. citeturn39view0
  - The same plugin’s `hooks/hooks.json` binds the `Stop` event to running the command `${CLAUDE_PLUGIN_ROOT}/hooks/stop-hook.sh`. File: `plugins/ralph-wiggum/hooks/hooks.json`. citeturn39view1
  - The plugin README explicitly states the technique uses a **Stop hook** to intercept exit attempts and references `hooks/stop-hook.sh`. File: `plugins/ralph-wiggum/README.md`. citeturn37view0

- **Transcript storage is accessible (path provided to hooks):**
  - Hook sample inputs include `transcript_path`. File: `plugins/plugin-dev/skills/hook-development/scripts/test-hook.sh`. citeturn31view0
  - The Stop hook expects transcript to be JSONL (“one JSON per line”) and filters lines containing `"role":"assistant"` before parsing. File: `plugins/ralph-wiggum/hooks/stop-hook.sh`. citeturn39view0

- **Per-project local state/config patterns exist (for plugins):**
  - The Plugin Settings pattern documents `.claude/plugin-name.local.md` for plugin config/state (YAML frontmatter + markdown body), notes it should typically be gitignored, and shows hooks reading/using it. File: `plugins/plugin-dev/skills/plugin-settings/SKILL.md`. citeturn41view0

- **MCP / tool protocol support is explicitly documented for plugins:**
  - MCP Integration guide documents plugin bundling via `.mcp.json` or `mcpServers` in `plugin.json`, supports multiple server types (stdio/SSE/HTTP/WebSocket), and documents tool name prefixing and lifecycle expectations (e.g., restart needed after config changes; `/mcp` command for viewing). File: `plugins/plugin-dev/skills/mcp-integration/SKILL.md`. citeturn42view0

- **Native memory features are mentioned in changelog (product-level):**
  - The changelog states “Claude now automatically records and recalls memories as it works” and adds a `memory` frontmatter field for agents enabling persistent memory scopes (`user`, `project`, `local`). File: `CHANGELOG.md` (2.1.32 and 2.1.33 entries). citeturn52view0

**UNKNOWN (explicitly not evidenced in the repo artifacts above)**
- Whether hook input includes a **reliable event timestamp** suitable as an authoritative `ts_utc` is not evidenced in the sample JSON structures shown (they include `session_id`, `transcript_path`, etc., but no explicit timestamp field is shown). citeturn31view0turn28view0
- Whether there is a **stable, versioned SDK API** for event emission beyond hooks (e.g., a formal “event emitter” API) is not directly confirmed by the plugin/hook artifacts examined here. The changelog does mention telemetry (OTel) and events, but the callable surface is not shown in this repo evidence set. citeturn52view0

**Inferred (explicitly labeled inference)**
- The existence of command hooks with timeouts (the hook test helper uses `timeout` and reports blocking behavior) implies hook execution is typically synchronous with bounded runtime; therefore truly non-blocking capture would depend on hook scripts being fast or delegating work. This is inferred from the test harness structure, not from core runtime source. citeturn31view0

---

**github/copilot-cli**

**Verified (from repository contents, installer script, README, and changelog)**
- **Repository content surface suggests the CLI itself is distributed as releases, not as source here:**
  - Root file list (as rendered by GitHub) shows only a small set of top-level files (e.g., `.github/`, `LICENSE.md`, `README.md`, `changelog.md`, `install.sh`) with no `src/` tree visible in that listing excerpt. citeturn2view1
  - `install.sh` downloads a tarball from GitHub releases (`releases/latest/download/copilot-<platform>-<arch>.tar.gz`), optionally validates against `SHA256SUMS.txt`, and installs a `copilot` binary into `$PREFIX/bin`. File: `install.sh`. citeturn45view0

- **Hooks / interception claims exist (but details are mostly in changelog text, not source code):**
  - The changelog entry states: “preToolUse hooks can deny tool execution and modify arguments.” File: `changelog.md` (0.0.396 entry). citeturn43view0
  - Changelog also states: “Plugins can provide hooks for session lifecycle events.” File: `changelog.md` (0.0.402 entry). citeturn43view0
  - Changelog states: “Add agentStop and subagentStop hooks to control agent completion.” File: `changelog.md` (0.0.401 entry). citeturn43view0

- **Plugin architecture exists and is actively evolving:**
  - Changelog mentions `/plugin install` supports GitHub repos, URLs, and local paths, and multiple plugin behaviors (skills translation, plugin marketplace add accepts URLs, etc.). File: `changelog.md`. citeturn43view0
  - README discusses the CLI as “Powered by the same agentic harness as GitHub’s Copilot coding agent” and references “MCP-powered extensibility.” File: `README.md`. citeturn45view1

- **MCP support is explicitly documented and repeatedly referenced as a feature:**
  - README describes MCP-powered extensibility. citeturn45view1
  - Changelog contains numerous MCP-related feature entries (e.g., workspace-local MCP config via `.vscode/mcp.json`, `/mcp show`, enable/disable, OAuth improvements, tool response structured content). File: `changelog.md` (multiple entries including 0.0.407, 0.0.406, 0.0.404, etc.). citeturn43view0

- **Configuration and “transcript-like” artifacts visible from README (limited scope):**
  - README documents user-level and repo-level LSP config locations (`~/.copilot/lsp-config.json` and `.github/lsp.json`) and implies the CLI reads these files. File: `README.md`. citeturn45view1

**UNKNOWN (explicitly not evidenced in the repo artifacts above)**
- **Post-tool hooks** (a “post” equivalent to `preToolUse`) are not confirmed in the changelog excerpt examined; therefore Post-Hook is UNKNOWN for this repo-based evidence set. citeturn43view0
- **Transcript storage location / format** for sessions is not described in the repo artifacts inspected (no `transcript_path` equivalent is visible in the README/installer/changelog evidence surfaced here). citeturn45view1turn43view0
- A stable, code-level **tool execution abstraction layer** suitable for interception beyond the mentioned hooks is not directly inspectable because the implementation source is not present in this repo snapshot; only behavior claims appear in changelog/README. citeturn2view1turn43view0

**Inferred (explicitly labeled inference)**
- Because installation fetches a compiled/bundled artifact from releases, integration that depends on internal modules would likely not be possible without treating the CLI as an external executable and relying on documented configuration/hooks. This is inferred from the installer’s release-binary workflow. citeturn45view0turn2view1

## Integration Risk Assessment

This section remains **pure reconnaissance**: it classifies likely coupling risk based on *observable surfaces*, without prescribing a new architecture.

**microsoft/Codex-CLI — Medium risk**
- **Wrapper/patch pressure:** There is no extensibility API beyond context files and shell scripts piping stdin/stdout; therefore capture and deterministic envelope emission would likely require a wrapper around `src/codex_query.py` I/O or changes to scripts/code. citeturn50view0turn17view1turn48view0
- **Low tool-risk but weak surfaces:** This project appears to generate suggestions (not execute them) via shell buffer insertion, reducing tool-execution interception needs but also limiting lifecycle observability. citeturn50view1turn17view1
- **Stability caveat:** Repo README states it is “not intended to be a released product,” implying an unstable long-term surface. citeturn1view0

**anthropics/claude-code — Medium risk (best evidenced surfaces, some safety concerns)**
- **Strong direct surfaces:** Hook events cover both tool lifecycle (PreToolUse/PostToolUse) and session lifecycle (SessionStart/SessionEnd) and include `transcript_path` in hook inputs, enabling high observability. citeturn31view0turn41view1turn39view0
- **Safety concerns surfaced by examples:** The Ralph stop-hook parses transcript using `grep`, `tail`, `jq`, and Perl regex-based extraction of `<promise>` content; this is a concrete example of potentially fragile text processing patterns inside hook logic. citeturn39view0turn37view0
- **Blocking risk is real:** Hooks can block tool execution (exit code patterns) and stop flow decisions (`decision: "block"`), meaning careless capture logic could add latency. This is evidenced by hook behavior patterns and the testing harness. citeturn28view0turn31view0turn39view0

**github/copilot-cli — High risk (limited code visibility, high churn, binary distribution)**
- **Coupling risk:** The repo largely distributes an installed binary via releases and does not expose implementation code in the visible tree excerpt, pushing integrations toward external-facing configs/hooks rather than internal modules. citeturn2view1turn45view0
- **Churn risk:** The changelog shows rapid iteration (including an entry dated 2026-02-11) and many feature changes spanning hooks, MCP, plugins, background agents, and SDK responses. Tight coupling to undocumented internal behavior would be fragile. citeturn43view0
- **Safety surface complexity:** Features such as background agents, autopilot mode, and broad tool ecosystems via MCP raise the complexity of ensuring deterministic, non-injectable capture without explicit, documented event envelopes. The repo evidence indicates these capabilities exist, but does not expose the detailed event payload formats. citeturn43view0turn45view1

## Recommended Integration Pattern

High-level classification only (no redesign proposals, no implementation plan).

**Safest for direct integration (based on repo-evidenced surfaces):**
- `anthropics/claude-code`, because hooks provide explicit interception points (PreToolUse, PostToolUse, Stop, SessionStart/End, UserPromptSubmit) with structured JSON input including `transcript_path`, and demonstrated structured decision outputs. citeturn31view0turn41view1turn39view0turn39view1

**Requires adapter layer (official surfaces exist, but evidence is indirect / format UNKNOWN):**
- `github/copilot-cli`, because hook/plugin/MCP capabilities are described (not source-inspected) and the runtime is installed as a binary; integration should assume only the exposed config/hook interfaces are stable. citeturn45view0turn43view0turn45view1

**Requires wrapper (no native hook system; capture must be external):**
- `microsoft/Codex-CLI`, because the core integration pattern is piping a shell buffer to `codex_query.py` and inserting returned text, with file-based context as the only “memory” mechanism; no plugin/hook/middleware interception layer is present. citeturn50view0turn50view1turn17view1turn17view0

**Should not be tightly coupled (as a long-lived integration dependency):**
- `microsoft/Codex-CLI` specifically signals it is not intended as a product release, suggesting weaker long-term API stability; therefore tight coupling to internals would be brittle. citeturn1view0
