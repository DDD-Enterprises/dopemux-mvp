---
id: CLAUDE_FULL_REFERENCE
title: Claude Full Reference
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-18'
last_review: '2026-03-18'
next_review: '2026-06-16'
prelude: Claude Full Reference (explanation) for dopemux documentation and developer
  workflows.
---
# CLAUDE.md — ChatX/ChatRipper MCP Playbook

Status: Compact | Owner: <TBD> | Last Updated: 2025-09-05 PT

## Purpose

Produce **small, correct patches** that build and pass first run, leveraging **MCP** for persistent memory, context injection, search, and integrations. Auto-loaded as project memory; see `docs/` for full architectural specs.

## Editing Policy

* **Terminal sessions**: Edit files directly or return unified diff (apply with `git apply`)
* **Web/chat sessions**: Return Repo Prompt XML edits document

---

## MCP User Configuration

**User = default_user**

1. On every interaction, retrieve all relevant memory
2. Store new facts (identity, behavior, preferences, goals, relationships)
3. Use **OpenMemory** for personal/long-term preferences; **ConPort** for project decisions, notes, and summaries *(server-memory & memory-bank retired)*
4. Use **sequential_thinking** for multi-step reasoning
5. Keep queries concise

## MCP Servers Available

**Persistence**: OpenMemory (cross-session personal), ConPort (project memory/knowledge)
**Context & Planning**: Sequential Thinking (reasoning), TaskMaster (task breakdown/exec), Claude-Context (semantic code search), Serena (IDE LSP edits)
**Search**: Exa (high-signal realtime dev search)
**Integration**: **CLI (Shell Command MCP)** — whitelisted `git`/`gh` (optional read-only `ls`,`cat`); **Zen** (multi-model orchestration; untrimmed)
**Docs**: **DevDocs (CyberAGI)** — tech docs ingestion + query *(TOC → Section Access)*

> Manage: `claude mcp list|add-json|get|remove`

---

## Development Workflow (Slice-based)

**/bootstrap** → preflight: summarize task (≤5 bullets), fetch hot files, get API docs, query memory, confirm constraints, propose tiny test-first plan

**Research** → `/research` pulls **DevDocs** *(TOC → Section)* + **Exa** sources → synthesize requirements + risks
**Story** → `/story` converts research → user story + AC + non-functional constraints → **ConPort**
**Plan** → `/plan` uses **sequential_thinking** → ≤5 steps mapping to files + tests
**Implement** → `/implement` writes tests first, minimal edits via **local_files/Serena**, runs checks, loops until green
**Debug** → `/debug` narrows repro, instruments, proposes smallest fix + cites **DevDocs** section behavior
**Ship** → `/ship` updates docs + ADR stubs + **ConPort** decision; then via **CLI MCP**:
`git add -A` → `git commit -m "type(scope): summary"` → `git push` →
`gh pr create -t "<title>" -b "<desc>"` → monitor `gh pr status` / `gh pr checks` →
`gh pr merge --squash`; capture follow-ups with `gh issue create` and link in ConPort
**Switch** → `/switch` compacts slice state → **OpenMemory** + **ConPort**, clears transient memory

---

## Permissions & Safety (Least Privilege)

**Rules (`.claude/settings.json` + hooks):**

* ✅ **Allowed**: read, edits in `src/**` + `tests/**`; specific tools: `python`, `pip`, `pytest`, `ruff`, `mypy`, `git status/diff/add/commit`
* ❓ **Ask**: `git push`
* ❌ **Deny**: `rm`, `sudo`, generic network (`curl`/`wget`), reading `.env` or `secrets/**`
* **Prefer explicit** allow entries (e.g., `Bash(pytest:*)` not `Bash(*)`)
* **Hooks** run Pre/PostToolUse to enforce lint/type/test gates

## Hooks (Pre/PostToolUse) — Token & Quality Guardrails

* **PreToolUse**
  * Block/ask on dangerous shell (`sudo`, `rm`) and network installs (`curl`, `wget`, `pip install`, `npm install`).
  * Prevent reading sensitive files (`.env`, `secrets/**`).
  * Token thrift nudges:
    * **ConPort** → use summaries/search with small `limit` before full context.
    * **Claude-Context** → cap results ≤ 5.
    * **Exa** → refine over-broad queries.
* **PostToolUse** (on write/edit, including **Serena** changes): run `ruff`, `mypy`, and `pytest --cov-fail-under=${HOOKS_COV_MIN:-90}`.

See `.claude/hooks/README.md` for matcher examples (include both `mcp__claude-context__.*` and `mcp__claude_context__.*`).

---

## Core Project Constraints

* **Privacy**: Policy Shield ≥99.5% coverage (≥99.9% strict), attachments NEVER cloud, local-first processing with optional cloud via `--allow-cloud`
* **Quality**: lint + mypy clean + pytest (≥**90%** coverage), RFC-7807 problem+json errors, JSON schema validation
* **Models**: Local Gemma-2-9B (temp≤0.3, streaming off, fixed seed) default; \
* **TDD**: tests → minimal code → pass → refactor → docs → ADR
* **Diffs**: unified diffs, smallest viable hunks, separate config changes with rationale

---

## Slash Commands

**Core Workflow**:
* `/bootstrap` — session preflight (context gather + constraints + tiny plan)
* `/research` — API/doc ingest (**DevDocs** + Exa) → risks + unknowns → **ConPort**
* `/story` — user story + AC + test checklist → **ConPort**
* `/plan` — sequential plan with explicit file list + test ordering
* `/implement` — tests-first loop; minimal diffs; cite docs used
* `/debug` — repro → isolate → fix; add guard tests
* `/ship` — docs + ADR stub + **ConPort** decision; commit/PR/merge via **CLI MCP** (`git`/`gh`)
* `/switch` — compact state → **OpenMemory** + **ConPort**; clear transient memory
* `/retrospect` — post-run: what worked/failed + follow-ups → Mem0 + backlog

**Memory Helpers**:
* `/decision` — log decision to **ConPort** (mirror to OpenMemory if cross-project)
* `/caveat` — add constraint to **ConPort** (mirror to OpenMemory if personal)
* `/followup` — add progress/todo to **ConPort**
* `/mem-query` — query **OpenMemory** by topic/keyword
* `/pattern` — save reusable pattern/snippet in `docs/patterns/**` and log to **ConPort**
* `/runbook-update` — append steps/lessons to `docs/runbooks/**` and log to **ConPort`
* `/scratch` — *(retired)* use ConPort `log_progress` for short-lived notes

---

## TDD Loop ("Good" Looks Like)

1. Read **AC** + **Interfaces** (reference `docs/` on-demand)
2. Generate failing tests (unit + schema validation + **RFC-7807** negative paths)
3. **Local checks**:

```bash
python -m pip install -e .[dev]
ruff check .
mypy src
pytest --cov=src/chatx --cov-fail-under=90
```

4. Minimal code → pass tests → refactor → docs → ADR

---

## Model Selection (Router-aware)

* **Local Gemma via Ollama** — default for routine coding/testing
* **Claude Sonnet** — when local confidence low or slice spans many files
* **Claude Opus** — heavy reasoning (architecture/design tradeoffs)

---

## Definition of Done

✅ Lint, types, tests **green**; coverage **≥ 90%** for changed code
✅ JSON/HTTP **schemas valid**; errors are **RFC-7807** problem+json
✅ Behavior documented; ADR stub if design shifted; clear commit message; TODO & next.md updated

---

## Memory Automation Rules

**OpenMemory (cross-session personal)**: decisions, caveats, preferences that span projects (topic-tagged)
**ConPort (project-scoped)**: decisions, progress, glossary, and context summaries for retrieval

**Session lifecycle**:
* **Start**: retrieve recent decisions/progress from ConPort; fetch relevant personal prefs from OpenMemory (by tag/topic)
* **During**: after key choices, `log_decision` in ConPort; after completing tasks, `log_progress`
* **End**: compact state — summarize the slice to ConPort; add durable insights to OpenMemory; clear transient scratch notes

---

## Task Master AI Instructions

**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md

### Command Quick Reference (files)

These markdown prompts live under `.claude/commands/` so you (and Claude) can reuse them consistently:

| Slash command       | Prompt file                                      | Notes                                                           |
| ------------------- | ------------------------------------------------ | --------------------------------------------------------------- |
| `/bootstrap`        | `.claude/commands/bootstrap.md`                  | Hot files + Exa docs + OpenMemory/ConPort fetch; tiny TDD plan. |
| `/research`         | `.claude/commands/research.md`                   | DevDocs TOC→Section + Exa; log to ConPort.                      |
| `/story`            | `.claude/commands/story.md`                      | Story + AC + NFR; write docs; ConPort decision.                 |
| `/plan`             | `.claude/commands/plan.md`                       | Sequential steps (+ slice mode); log to ConPort.                |
| `/implement`        | `.claude/commands/implement.md`                  | Tests-first; Serena edits; ConPort progress.                    |
| `/debug`            | `.claude/commands/debug.md`                      | Repro→isolate→fix; postmortem; cite DevDocs.                    |
| `/ship`             | `.claude/commands/ship.md`                       | Docs + ADR stub; ConPort decision; commit/PR/merge (CLI MCP).   |
| `/switch`           | `.claude/commands/switch.md`                     | Compact slice → ConPort/OpenMemory.                             |
| `/tdd`              | `.claude/commands/tdd-loop.md`                   | Red→Green→Refactor; cov `${HOOKS_COV_MIN:-90}`.               |
| `/code-search`      | `.claude/commands/code-search.md`                | Claude-Context semantic search (≤5).                            |
| `/plan-tasks`       | `.claude/commands/plan-tasks.md`                 | Generate TaskMaster tasks from spec.                            |
| `/tasks`            | `.claude/commands/tm/list.md`                    | List TaskMaster tasks.                                          |
| `/next-task`        | `.claude/commands/tm/next/next-task.md`          | Pull next TaskMaster task.                                      |
| `/task-done`        | `.claude/commands/tm/set-status/to-done.md`      | Mark TaskMaster task done.                                      |
| `/expand-task`      | `.claude/commands/tm/expand/expand-task.md`      | Expand TaskMaster task.                                         |
| `/log-dec`          | `.claude/commands/decision.md`                   | ConPort `log_decision`.                                         |
| `/get-decisions`    | `.claude/commands/get-decisions.md`              | ConPort decisions list.                                         |
| `/search-decisions` | `.claude/commands/search-decisions.md`           | ConPort FTS over decisions.                                     |
| `/mem-query`        | `.claude/commands/mem-query.md`                  | OpenMemory retrieval.                                           |
| `/docs-toc`         | `.claude/commands/docs/docs-toc.md`              | DevDocs TOC (small limit).                                      |
| `/docs-get`         | `.claude/commands/docs/docs-get.md`              | DevDocs section by id.                                          |
| `/docs-index`       | `.claude/commands/docs/docs-index.md`            | DevDocs add/crawl a source.                                     |
| `/zen`              | `.claude/commands/zen.md`                        | Route instruction to Zen workflow.                              |
| `/zen-continue`     | `.claude/commands/zen-continue.md`               | Zen context recovery.                                           |
| `/git-commit`       | `.claude/commands/git/git-commit.md`             | Conventional Commit → push.                                     |
| `/pr-create`        | `.claude/commands/gh/pr-create.md`               | Open a PR.                                                      |
| `/pr-checks`        | `.claude/commands/gh/pr-checks.md`               | Monitor CI.                                                     |
| `/pr-merge`         | `.claude/commands/gh/pr-merge.md`                | Merge PR (squash).                                              |
| `/issue-create`     | `.claude/commands/gh/issue-create.md`            | Create issue.                                                   |

> Token thrift: Claude-Context results ≤ **5**; ConPort list/search with `limit` **3–5**; DevDocs use **TOC → Section** with small limits; prefer summaries before full context pulls.
