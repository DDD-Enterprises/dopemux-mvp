# Dopemux Dev Orchestration — Detailed Design/Feature Spec (v0.2)

**Author:** Dopemux Core • **Status:** Draft for implementation • **Updated:** 2025‑09‑17 • **Scope:** Phase 1–2

---

## 0) Executive summary
Dopemux delivers a Claude‑Code–style, slice‑based development loop integrated into a tmux‑first terminal UI. **Leantime** is the **source of truth** for PM (projects, milestones, tasks). **Task‑Master** is used tactically for **task breakdown and specialized analysis** only. **Letta** provides **stateful memory** (replacing OpenMemory/ConPort). Documentation grounding is via **Context7**. There is **no privacy gate** in Phase 1; guardrails focus on safe tool execution and quality gates (lint/type/test). The statusline is **rich‑density** by default.

---

## 1) Goals, non‑goals, assumptions
### 1.1 Goals
- Recreate and enhance Claude Code’s end‑to‑end dev loop entirely inside Dopemux.
- Keep Leantime as the single authoritative PM system (create/update tasks, milestones, track progress).
- Use Task‑Master **only** for PRD parsing, decomposition, estimation, research assists, and complexity analysis.
- Replace OpenMemory/ConPort with Letta’s self‑editing memory blocks and archival vector store.
- Integrate Context7 for authoritative docs/SDK references at code time.
- Provide a modern tmux interface with **popup‑first** modals and a **rich** statusline.

### 1.2 Non‑goals
- No privacy scanning/post‑edit PII checks in Phase 1 (can be toggled in later phases).
- No IDE plugin work (VS Code / Vim) beyond what MCP/LSP tools already support.

### 1.3 Assumptions
- Claude Code CLI + MCP host available on target machines.
- Leantime reachable via JSON‑RPC and/or MCP Server plugin; API keys configured.
- Letta reachable (cloud or self‑hosted) for memory blocks.

---

## 2) System overview
### 2.1 High‑level components
- **Dopemux Core (Node + tmux):** session orchestrator, command router, statusline engine, hooks.
- **Claude Code CLI:** slash command runner + MCP host; executes our command prompts.
- **MCP servers:**
  - **Leantime MCP** (authoritative PM)
  - **Task‑Master MCP** (tactical breakdown)
  - **Serena (LSP edits)**
  - **Context7 (docs ingestion/query)**
  - **Repo tools** (semantic code search)
- **Letta:** memory tiers (core/recall/archival), self‑editing blocks per project.
- **CI/Test runner:** ruff, mypy/pyright, pytest + coverage; language‑specific equivalents per project type.

### 2.2 Data flow (happy‑path)
1) User invokes a Dopemux slash command (e.g., `/bootstrap`).
2) Dopemux prompts Claude Code with the command template; tools allowed for that command are declared.
3) Claude Code invokes MCP tools (Leantime/Task‑Master/Context7/Serena) under guardrails.
4) On file edits, post‑edit quality gates run (lint/type/test). Results stream back to the statusline.
5) Task state updates are pushed to **Leantime**; Task‑Master artifacts remain as local tactical records.
6) Decisions/notes are written to **Letta** (memory blocks) and ADR files in the repo.

---

## 3) Detailed architecture
### 3.1 Command host and sandbox
- **Process model:** Dopemux (Node) spawns Claude Code as a managed child process; streams JSONL; restarts on crash; preserves session IDs.
- **Context:** `.dopemux/` per‑project folder holds cache, local config, session DB.
- **Policy:** Pre‑tool guardrails (allow/ask/block); post‑edit quality gates; token optimizer hints.

### 3.2 MCP server roster
| Server | Purpose | Transport | Auth | Notes |
|---|---|---|---|---|
| Leantime MCP | Projects, tasks, milestones, timesheets | STDIO/HTTP | API key / PAT | Source of truth; bidirectional sync |
| Task‑Master MCP | PRD→tasks, expand, complexity, research | STDIO | N/A (local) | Tactical only; output mapped then synced |
| Serena LSP | Structured, safe code edits & file ops | STDIO | – | All edits pass here (no raw shell writes) |
| Context7 | Library/API docs fetching & Q/A | STDIO/HTTP | – | Ground code with authoritative docs |
| Repo search | Semantic code search/index | STDIO | – | Scopes per project root |

### 3.3 Memory model (Letta)
- **Blocks:** `persona`, `project_context`, `decisions`, `patterns`, `runbook`, `lessons`.
- **Lifecycles:** commands append/replace blocks; retrospectives consolidate.
- **Archival:** repo docs, ADRs, and selected artifacts embedded to vector store for recall.

### 3.4 PM model (Leantime as SOT)
- **Entities:** Project, Milestone, Sprint, Ticket (task/issue), Timesheet.
- **Mapping from Task‑Master:** `title→headline`, `description→description`, `status→status`, `priority→priority`, `deps→relations`, `storypoints→storypoints`.
- **Sync policy:** Create/Update in Leantime; store foreign IDs back in Task‑Master metadata. Last‑writer‑wins on status.

### 3.5 Quality enforcement
- **Triggers:** any write/edit (from Serena) → `lint` → `typecheck` → `tests`.
- **Gates:** `/complete` requires ≥90% coverage, clean lint/type, PR linked to a Leantime ticket.

### 3.6 Security & safety
- **Pre‑tool guard:** allow (safe ops), ask (package install, network reads), block (sudo/rm‑rf/curl|bash). Per‑project learning (whitelist cache). No privacy scanning in Phase 1.
- **Token optimizer:** narrows tool calls, sets limits, reuses continuation IDs for "Zen".

---

## 4) tmux UX specification (rich‑density)
### 4.1 Layout & key tables
- **Default session windows:**
  1) **orchestrator** (Claude session + command palette popup)
  2) **code** (editor + test pane + logs)
  3) **project** (Leantime tasks popup, burndown preview)
  4) **memory** (Letta inspector + ADR viewer)
- **Popup‑first:** all pickers (tasks, docs, which‑key, PRD upload) use `display-popup -E -w 80% -h 80%`.
- **Key layers:** `prefix + ?` opens which‑key palette; `prefix + p` project panel; `prefix + m` memory; `prefix + t` tasks; `prefix + d` docs.

### 4.2 Statusline (rich)
- **Segments (left→right):** `mode badge` · `repo branch` · `git dirty` · `tests: pass/fail %` · `type/lint` · `token usage` · `active MCP` · `next task` · `time`.
- **Update cadence:** dynamic segments (tests/token/MCP) poll every 2s; static (time) every 10s.
- **Visuals:** subtle gradient background, glyph separators (NerdFonts), clear contrast; zoom indicator when a pane is zoomed.

### 4.3 Accessibility & ADHD support
- Progressive disclosure (help tiers), celebratory micro‑animations in popups, focus timers (Pomodoro) surfaced near `next task`, low‑latency shortcuts.

---

## 5) Slash commands (behavioral spec)
> Each command is defined by: **Purpose**, **Inputs**, **Preconditions**, **Side effects**, **Allowed tools**, **Outputs**, **Errors**, **Config**.

### 5.1 Lifecycle commands
- **/bootstrap**
  - Purpose: Prime context for a slice of work.
  - Inputs: optional ticket ID or free‑text goal.
  - Allowed tools: `leantime.projects.list`, `leantime.tickets.get`, `repo.search`, `letta.blocks.get`.
  - Outputs: `tiny_plan.md`, `hot_files.json`, memory updates (`project_context`).

- **/research**
  - Purpose: Ground requirements with docs and web research.
  - Allowed tools: `context7.docs.search`, `context7.docs.fetch`, `taskmaster.research` (optional), `repo.search`.
  - Outputs: `research.md` (sources, risks), memory append (`decisions`).

- **/story**
  - Purpose: Produce story + acceptance criteria; log ADR.
  - Allowed tools: `letta.blocks.append`, `fs.write`, `leantime.tickets.add` (if story creates epic/parent).
  - Outputs: `story.md`, `docs/adr/ADR-xxxx.md`, Leantime epic.

- **/plan**
  - Purpose: 3–5 step plan (files/tests), link to Leantime subtasks.
  - Allowed tools: `leantime.tickets.add`, `repo.search`, `context7.docs.fetch`.
  - Outputs: `plan.md`, task tree in Leantime.

- **/implement**
  - Purpose: TDD loop (red→green→refactor) with Serena edits.
  - Preconditions: plan exists.
  - Allowed tools: `serena.*`, `context7.docs.fetch`, `test.run`.
  - Side effects: triggers quality gates after each write.

- **/debug**
  - Purpose: Min repro, doc‑verified fix.
  - Allowed tools: `test.run --select`, `repo.search`, `context7.docs.fetch`.

- **/ship**
  - Purpose: Docs up‑to‑date; commit; PR; move tasks to Done.
  - Allowed tools: `git.add/commit`, `gh.pr.*`, `leantime.tickets.update`.

- **/switch**
  - Purpose: Summarize, compact logs, store memories; prep next slice.
  - Allowed tools: `letta.blocks.append`, `fs.write`.

### 5.2 Quality & completion
- **/complete**: enforce DoD (≥90% cov, lint/type clean, PR + ticket linkage).
- **/commit-pr**: quick commit + PR after one last test/lint run.
- **/retrospect**: lessons learned → Letta `lessons` + Leantime notes/task.

### 5.3 Tasking (Leantime SOT; Task‑Master tactical)
- **/plan-tasks**: Use Task‑Master `parse_prd` → show preview → create Leantime tasks/milestones. Store Task‑Master IDs in Leantime custom fields.
- **/tasks**: List/filter Leantime tasks; quick actions (start timer, assign, change status).
- **/next-task**: Heuristic pick from Leantime (priority, due, WIP limits).
- **/task-done**: Mark Done in Leantime; sync Task‑Master if linked.

---

## 6) Interfaces & contracts
### 6.1 Configuration files
- **`.dopemux/config.yaml`**
```yaml
project:
  name: my-app
  root: "."
  language: python

pm:
  provider: leantime
  base_url: https://pm.example.com
  api_key_env: LEANTIME_API_KEY

memory:
  provider: letta
  base_url: https://api.letta.ai/v1
  token_env: LETTA_TOKEN
  blocks: [persona, project_context, decisions, patterns, runbook, lessons]

hooks:
  pre_tool_guard: enabled
  token_optimizer: enabled
  privacy_gate: disabled

statusline:
  density: rich
  segments: [mode, branch, git_dirty, tests, type_lint, tokens, mcp, next_task, clock]
```

- **`.mcp.json` (per project)**
```json
{
  "clients": {
    "leantime": { "transport": "http", "baseUrl": "https://pm.example.com/mcp", "auth": {"type":"apiKey","env":"LEANTIME_API_KEY"} },
    "taskmaster": { "transport": "stdio", "command": "npx", "args": ["claude-task-master", "mcp"] },
    "serena": { "transport": "stdio", "command": "serena-lsp" },
    "context7": { "transport": "http", "baseUrl": "https://context7.example.com" }
  }
}
```

### 6.2 Leantime JSON‑RPC examples
- **Create task**
```bash
curl -X POST "$LT/api/jsonrpc" \
  -H "x-api-key: $LT_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0","id":"t1","method":"leantime.rpc.tickets.addTicket",
    "params":{"headline":"Implement Dopemux integration","type":"task","projectId":"42"}
  }'
```

- **Update status**
```bash
curl -X POST "$LT/api/jsonrpc" \
  -H "x-api-key: $LT_API_KEY" -H "Content-Type: application/json" \
  -d '{
    "jsonrpc":"2.0","id":"t2","method":"leantime.rpc.tickets.updateTicket",
    "params":{"id":"1234","status":3}
  }'
```

### 6.3 Task‑Master to Leantime mapping (schema)
| Task‑Master | Leantime | Notes |
|---|---|---|
| id | customField.taskmasterId | stored on Leantime ticket |
| title | headline | required |
| description | description | markdown supported |
| status (pending/in_progress/done/deferred/cancelled) | status (numeric) | translate via map |
| dependencies[] | relations | directional edges |
| priority | priority | 1–5 |
| storypoints | storypoints | integer |

### 6.4 Memory block operations (Letta)
- `SET project_context`: summarize plan, links to tickets/PRs.
- `APPEND decisions`: log ADR anchors, trade‑offs.
- `APPEND patterns`: catalog reusable snippets.
- `APPEND runbook`: operational steps/lessons.

### 6.5 Quality gate API (language‑agnostic)
```json
{
  "lint": {"cmd": "ruff .", "okExit": 0},
  "typecheck": {"cmd": "mypy .", "okExit": 0},
  "tests": {"cmd": "pytest -q --maxfail=1 --cov=src", "okExit": 0, "coverageMin": 0.90}
}
```

---

## 7) Hook system (policies)
### 7.1 Pre‑tool guard
- **Allow:** git status, read file ops, tests, lsp reads.
- **Ask:** package installs (`pip/npm`), network fetch for docs, writing outside project.
- **Block:** `sudo`, destructive file ops, piping remote scripts.
- **Learning:** confirm once → cached whitelist scoped to project.

### 7.2 Token optimizer
- Limit `context7` fetches per step; cap repo search results to 3; reuse Zen continuation tokens; advise filters for PM queries.

### 7.3 Post‑edit quality gates
- On `serena.write*` → run {lint → type → tests}; if fail, annotate diff and retry loop inside `/implement` or `/debug`.

---

## 8) Error handling & telemetry
- **Error taxonomy:** `MCP_INIT_FAIL`, `AUTH_FAIL`, `RATE_LIMIT`, `EDIT_CONFLICT`, `QUALITY_GATE_FAIL`, `PR_FAIL`.
- **Retries:** exponential backoff with jitter; bounded retries (3) then surface actionable remediation.
- **Telemetry:** per‑command metrics (latency, token usage, passes), surfaced in statusline and logs.

---

## 9) CI/CD & DevEx
- **DoD enforcement:** `/complete` blocks until coverage≥90%, lint/type clean, PR linked to Leantime ticket.
- **PR templates:** auto‑compose description (story, plan, tests, screenshots).
- **Branching:** `feat/<ticketId>-slug` by default.

---

## 10) Performance SLOs
- Command median E2E < 10m; Memory update < 500ms; Agent spawn < 2s; Token efficiency > 80%; Cache hit > 70%.

---

## 11) Security posture (Phase 1)
- No privacy scans; focus on least‑privilege tool policy; audit logs for tool decisions; API keys in env vars; optional IP allowlist for Leantime.

---

## 12) Rollout plan
**Week 1**
- Wire Claude Code CLI + `/bootstrap → /plan → /implement` minimal loop.
- Connect Leantime MCP/JSON‑RPC; `/tasks`, `/plan-tasks` preview.
- Letta blocks (`project_context`, `decisions`) + ADR writes.
- Tmux base layout + rich statusline skeleton.

**Week 2**
- Serena edits gated by tests; Context7 integrated; `/ship`, `/complete`, `/commit-pr`.
- Two‑way sync for Task‑Master IDs; timers + burndown in popups.

---

## 13) Risks & mitigations
- **API instability (Leantime MCP beta):** fallback to JSON‑RPC; feature flags per tool.
- **Token overuse:** optimizer + caps per command; visible token HUD.
- **Test flakiness:** quarantine list; rerun policy.
- **Complexity creep:** plugin boundaries; command contracts frozen per minor version.

---

## 14) Appendix — Claude Code → Dopemux mapping
| Claude Code feature | Dopemux implementation |
|---|---|
| OpenMemory/ConPort | Letta blocks (`decisions`, `patterns`, etc.) + ADR files |
| TaskMaster (PM) | Tactical breakdown only; Leantime is SOT |
| Serena edits | Same (all edits via LSP), quality gates post‑edit |
| Context7 docs | Same; added caps + caching |
| /ship, /commit-pr | gh‑CLI flows; link PR↔ticket |
| Zen mode | Optional heavyweight planning/refactor; reuses continuation IDs |

---

## 15) Acceptance criteria (Phase 1)
- From a blank repo, operator can: `/bootstrap` → `/plan` (Leantime subtasks created) → `/implement` (tests pass) → `/commit-pr` (PR opened & linked) → `/complete` (gates pass) — **entirely inside Dopemux**.

**End of spec v0.2**

