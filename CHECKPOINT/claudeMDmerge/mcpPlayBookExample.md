
@docs/README.md
@docs/architecture.md
@docs/interfaces.md
@docs/implementation.md
@docs/acceptance-criteria.md
@docs/development/test-strategy.md
@docs/operations/non-functional-requirements.md

# CLAUDE.md — ChatX/ChatRipper + MCP Playbook
Status: Draft | Owner: <TBD> | Last Updated: 2025-09-03

## Purpose
Make Claude Code produce **small, correct patches** that build and pass on the first run, while leveraging **Model Context Protocol (MCP)** servers for persistent memory, context injection, search, and integrations. This file is auto-loaded as project memory at session start; the `@…` imports above bring key specs into context without copy-pasting.

## Editing policy
- In Claude Code sessions (terminal): you may edit files directly or return a unified diff (we'll apply with `git apply`).
- In web/chat sessions: return a Repo Prompt XML edits document (see `docs/repo-prompt-xml.md`) and we'll apply via Repo Prompt's Apply tab or MCP tool.

---

MCP: Open User Configuration
User = default_user

1. On every interaction, retrieve all relevant memory.
2. When new facts show up, store them (identity, behavior, preferences, goals, relationships).
3. Use the “openmemory (Mem0)” server to persist decisions and caveats; use “server-memory” for short-lived notes; use “memory-bank” for curated patterns.
4. Use “sequential_thinking” whenever multi‑step reasoning is needed.
5. Keep queries concise.

## 0) Session bootstrap (run /bootstrap first)
Run **/bootstrap** to perform a quick preflight:
1) Summarize the task in ≤5 bullets; identify impacted files.  
2) Use **claude-context** to fetch hot files (recent churn, TODOs) and list them.  
3) Use **context7** to fetch authoritative docs for any mentioned libraries/frameworks (pin versions).  
4) Query **openmemory (Mem0)** for open decisions & caveats for this project/slice.  
5) Confirm constraints: language/runtime, lint/type/test gates (≥60% coverage), interfaces/SLA, schemas, **RFC-7807**.  
6) Propose a **tiny test-first plan**, await confirmation before edits.

---

## 1) MCP servers & tools (what's available)
MCP provides a standard "USB-C for AI" to connect tools and data sources. Claude Code can add servers from JSON and use them in sessions.

**Categories & examples:**
- **Persistence**
  - *OpenMemory (mem0)* — cross-session memory for decisions, preferences, caveats (hosted instance).
  - *Server-Memory* — short-lived scratch memory for the current slice.
  - *Memory Bank* — curated patterns, runbooks, prompts, finalized checklists.
- **Context & Planning**
  - *Context7* — up-to-date API/framework docs injection.
  - *Sequential Thinking* — structured multi-step reasoning to break down tasks.
  - *Claude-Context* — semantic code search for hot files/snippets in repo.
- **Search**
  - *Exa* — high-signal dev search; *DuckDuckGo* — broad fallback.
- **Integration**
  - *GitHub* — issues/PRs/code; *Filesystem* — local project file ops.
  - *Trigger.dev* — jobs/workflows; *Conport* — local services/ports control.

> Manage servers: `claude mcp list`, `claude mcp add-json <name> '<json>'`, `claude mcp get <name>`, `claude mcp remove <name>`.

---

## 2) Development workflow (slice-based with MCP)
**Research** — `/research` pulls **context7** (APIs), optionally **exa** for curated sources, then synthesizes requirements + risks.  
**Story** — `/story` converts research into a user story with AC, non-functional constraints, and test ideas; syncs to **memory-bank**.  
**Plan** — `/plan` uses **sequential_thinking** to break work into ≤5 steps, each step mapping to specific files and tests.  
**Implement** — `/implement` writes tests first, performs minimal edits via **local_files**, runs checks, and loops until green.  
**Debug** — `/debug` narrows repro, instruments, and proposes smallest viable fix; cites **context7** lines for API behavior.  
**Document & Log** — `/ship` updates docs & ADR stubs, adds **Mem0** decisions (why/how/risks), then creates a small commit via **git_local**.  
**Switch** — `/switch` compacts the current slice (state, files, TODOs), stores decisions to **Mem0**, pushes patterns/snippets to **memory-bank**, clears transient memory.

---

## 3) Permissions & safety (least privilege)
Use project settings + hooks to control tools. Inspect and tweak permissions in `/permissions`; settings resolve user → project → local.

**Rules (enforced by `.claude/settings.json` + hooks):**
- Allowed: read, edits in `src/**` and `tests/**`, and specific tools: `python`, `pip`, `pytest`, `ruff`, `mypy`, `git status/diff/add/commit`.
- Ask: `git push`.
- Deny: `rm`, `sudo`, generic network (`curl`/`wget`), reading `.env` or `secrets/**`.
- Prefer **explicit** allow entries (e.g., `Bash(pytest:*)`) rather than `Bash(*)`.
- Hooks run on **PreToolUse**/**PostToolUse** to block risky calls and enforce lint/type/test gates after edits.

---

## 4) Modes & flags that matter
- Start complex work in **Plan Mode** (read-only), then elevate when ready.  
- Resume work with `claude --continue` or `claude --resume <id>`.  
- Keep outputs token-efficient: summaries → minimal diffs (avoid whole-file dumps).

---

## 5) TDD loop (what "good" looks like)
1) Read **AC** + **Interfaces** (already imported above).  
2) Generate failing tests (unit + schema validation + **RFC-7807** negative paths).  
3) Local checks:
```bash
python -m pip install -e .[dev]
ruff check .
mypy src
pytest --cov=src/chatx --cov-fail-under=60
```
4) Minimal code → pass tests → refactor → docs → ADR.

---

## 6) Diff etiquette
- Propose **unified diffs**, smallest viable hunks.  
- Only touch files you list; separate config/CI changes into their own tiny patch with rationale.

---

## 7) Slash commands (kept in `.claude/commands/`)
Core commands:
- `/bootstrap` — session preflight (context gather + constraints + tiny plan).
- `/research` — API/doc ingest (context7 + exa), risks, unknowns → memory-bank.
- `/story` — user story + AC + test checklist → memory-bank.
- `/plan` — sequential plan with explicit file list and test ordering.
- `/implement` — tests-first loop; minimal diffs only; cite any docs used.
- `/debug` — repro → isolate → fix; add guard tests.
- `/switch` — compact state → Mem0 + memory-bank; clear transient memory.
- `/ship` — docs, ADR stub, PR body, small commit.
- `/retrospect` — brief post-run: what worked/failed, follow-ups → Mem0 + backlog.

Memory helpers:
- `/decision` — add a decision to OpenMemory (Mem0) with tags.
- `/caveat` — add a caveat/constraint to OpenMemory (Mem0) with tags.
- `/followup` — add a follow-up/todo to OpenMemory (Mem0) with tags.
- `/mem-search` — query OpenMemory for decisions/caveats by project/slice/tag.
- `/pattern` — save a reusable pattern/snippet in Memory-Bank.
- `/runbook-update` — append steps/lessons to a Memory-Bank runbook.
- `/scratch` — jot short-lived notes in server-memory (cleared by /switch).

---

## 8) Model selection (router-aware)
- **Local Gemma via Ollama** — default for routine coding/testing.  
- **Claude Sonnet** — when local confidence is low or slice spans many files.  
- **Claude Opus** — heavy reasoning (architecture/design tradeoffs).  
- Router may select based on task complexity and context.

---

## 9) MCP quick reference
- List servers: `claude mcp list`  
- Add from JSON: `claude mcp add-json <name> '<json>'`  
- Inspect: `claude mcp get <name>`  
- Remove: `claude mcp remove <name>`

---

## 10) Definition of Done
- Lint, types, tests **green**; coverage **≥ 60%** for changed code.
- JSON/HTTP **schemas valid**; errors are **RFC-7807** problem+json.  
- Behavior documented; ADR stub added if design shifted; commit message is clear and scoped.

---

## 11) Memory automation rules
**OpenMemory (Mem0):** log decisions, caveats, and preferences as atomic items (one idea per entry) with tags: `project`, `slice`, `decision|caveat|followup`.  
**Memory-Bank:** store reusable patterns, runbooks, prompts, and finalized checklists under `docs/patterns/**` and `docs/runbooks/**`.  
**Server-Memory:** scratch notes for current slice; may be cleared by `/switch`.  
**At session start**, retrieve: “open decisions for <project>”, “recent caveats”, and “today’s TODO”.  
**At session end**, append: “decisions made”, “follow-ups”, “snippets added”, “risks accepted”.

---

## Updating this file
Keep MCP server entries and env requirements in sync with `scripts/setup_mcp_servers.sh`. Add new servers only with explicit approval.
