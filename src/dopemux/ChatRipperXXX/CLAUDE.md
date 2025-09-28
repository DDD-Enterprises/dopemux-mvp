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
**Search**: Exa (high-signal realtime web research), **Context7** (authoritative library docs)  
**Integration**: **CLI (Shell Command MCP)** — whitelisted `git`/`gh` (optional read-only `ls`,`cat`); **Zen** (multi-model orchestration; untrimmed)  
**Docs**: **Context7** — tech docs ingestion + query *(authoritative API docs)*

> Manage: `claude mcp list|add-json|get|remove`

---

## Development Workflow (Slice-based)

**/bootstrap** → preflight: summarize task (≤5 bullets), fetch hot files, get API docs, query memory, confirm constraints, propose tiny test-first plan

**Research** → `/research` pulls **Context7** *(authoritative library docs)* + **Exa** *(web research)* → synthesize requirements + risks  
**Story** → `/story` converts research → user story + AC + non-functional constraints → **ConPort**  
**Plan** → `/plan` uses **sequential_thinking** → ≤5 steps mapping to files + tests  
**Implement** → `/implement` writes tests first, minimal edits via **local_files/Serena**, runs checks, loops until green  
**Debug** → `/debug` narrows repro, instruments, proposes smallest fix + cites **Context7** API behavior  
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
  * **Token thrift nudges** (Target: <25k MCP context):
    * **Zen (~29k tokens)** → MANDATORY `files≤1` + `continuation_id` reuse; avoid for simple tasks
    * **TaskMaster (~21k tokens)** → ALWAYS use `status=pending` + `withSubtasks=false` (saves ~15k)
    * **ConPort (~17k tokens)** → use `limit=3-5` on searches; summaries before full context
    * **Serena (~15k tokens)** → prefer symbolic tools over full file reads
    * **Claude-Context** → cap results ≤3 (down from 5)
    * **Exa** → refine over-broad queries, min 5 chars; prefer specific lib/error terms
    * **Fast-Markdown (~4k tokens)** → use section-specific queries vs full file reads
* **PostToolUse** (on write/edit, including **Serena** changes): run `ruff`, `mypy`, and `pytest --cov-fail-under=${HOOKS_COV_MIN:-90}`.

See `.claude/hooks/README.md` for matcher examples (include both `mcp__claude-context__.*` and `mcp__claude_context__.*`).

---

## Tool Selection Priority (MANDATORY)

**ALWAYS use the best tool for the task - never resort to basic bash commands when sophisticated tools are available:**

1. **File Discovery & Analysis**: Use `mcp__serena__list_dir`, `mcp__serena__find_file`, `Glob` - NOT `find`, `ls`
2. **Code Search**: Use `mcp__claude-context__search_code`, `Grep` - NOT `grep`, `rg` via bash  
3. **Content Analysis**: Use `mcp__serena__search_for_pattern`, `mcp__serena__read_file` - NOT `cat`, `head`, `tail`
4. **Symbol Operations**: Use `mcp__serena__find_symbol`, `mcp__serena__get_symbols_overview` - NOT manual code inspection
5. **Repository Operations**: Use semantic tools first, bash only for git commands and operations the sophisticated tools cannot handle

**Enforcement**: This is a hard requirement - using basic bash commands when better tools exist is a workflow violation.

## MCP Server Token Budget Management (CRITICAL)

**Current Usage: ~93k tokens from MCP tools alone**

### High-Impact Token Reduction (Priority Order)

1. **Zen Server (~29k tokens)** - MOST EXPENSIVE
   - Use ONLY for complex multi-step workflows requiring expert analysis
   - MANDATORY: `files≤1` parameter (not ≤2)
   - ALWAYS reuse `continuation_id` for follow-ups
   - Consider basic tools first before Zen workflows

2. **TaskMaster (~21k tokens)** - SECOND MOST EXPENSIVE  
   - DEFAULT pattern: `status=pending withSubtasks=false` (saves ~15k tokens)
   - Use `get_task id=X` for specific tasks vs `get_tasks`
   - Filter by status before expanding with subtasks
   - Batch operations when possible

3. **ConPort (~17k tokens)** - THIRD MOST EXPENSIVE
   - ALWAYS use `limit=3-5` on searches and gets
   - Use `search_*_fts` with targeted queries vs broad gets
   - Summary-first approach: search → targeted get → full context (last resort)

4. **Serena (~15k tokens)** - FOURTH MOST EXPENSIVE
   - Prefer `find_symbol` + `get_symbols_overview` over `read_file`
   - Use `search_for_pattern` with specific regex vs broad file reads
   - Target specific functions/classes, not entire files

### Token-Efficient Alternatives

| Instead of | Use This | Token Savings |
|------------|----------|---------------|
| `zen` workflow | Basic tools (Read, Edit, Bash) | ~25k tokens |
| `get_tasks` unlimited | `get_tasks status=pending withSubtasks=false` | ~15k tokens |
| ConPort full context | `search_decisions_fts` with `limit=3` | ~10k tokens |
| `read_file` entire file | `find_symbol` + targeted reads | ~5k tokens |
| `get_active_context` | `search_custom_data_value_fts` | ~3k tokens |

### Emergency Token Budget Protocol

If context exceeds 100k tokens:
1. **STOP** using Zen tools immediately  
2. Switch TaskMaster to `status=pending withSubtasks=false`
3. Use ConPort with `limit=1-2` maximum
4. Prefer Serena symbolic tools over file reads
5. Consider `/clear` to reset context

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
* `/research` — **Context7 + Exa integration**: Auto-query library docs + web research → comprehensive requirements
* `/story` — user story + AC + test checklist → **ConPort**
* `/plan` — sequential plan with explicit file list + test ordering
* `/implement` — **Context7-driven TDD**: Tests-first with automatic library doc context + examples
* `/debug` — **Context7-verified debugging**: Cross-reference against official API docs during diagnosis
* `/ship` — docs + ADR stub + **ConPort** decision; commit/PR/merge via **CLI MCP** (`git`/`gh`)
* `/complete` — full quality gates (lint/types/tests/coverage) + feature branch + conventional commit + detailed PR
* `/commit-pr` — quick automated commit/PR with quality verification (tests/lint/types/coverage ≥90%)
* `/tm/complete-task` — TaskMaster task completion + quality gates + commit/PR workflow
* `/switch` — compact state → **OpenMemory** + **ConPort**; clear transient memory
* `/retrospect` — post-run: what worked/failed + follow-ups → Mem0 + backlog

**Integrated Context7 Features**:
* **Implicit Documentation**: Automatically queries Context7 when libraries/APIs are detected
* **Pre-Implementation Context**: Library documentation loaded before code generation begins
* **API Verification**: Cross-references implementation against official documentation
* **Code Examples**: Pulls authoritative examples and patterns during implementation
* **Debug Validation**: Verifies fixes against official API specifications

**Memory Helpers**:
* `/decision` — log decision to **ConPort** (mirror to OpenMemory if cross-project)
* `/caveat` — add constraint to **ConPort** (mirror to OpenMemory if personal)
* `/followup` — add progress/todo to **ConPort**
* `/mem-query` — query **OpenMemory** by topic/keyword
* `/pattern` — save reusable pattern/snippet in `docs/patterns/**` and log to **ConPort**
* `/runbook-update` — append steps/lessons to `docs/runbooks/**` and log to **ConPort`
* `/scratch` — *(retired)* use ConPort `log_progress` for short-lived notes

---

## TDD Loop + Feature Completion Workflow

### TDD Implementation:
1. Read **AC** + **Interfaces** (reference `docs/` on-demand)
2. Generate failing tests (unit + integration + **RFC-7807** negative paths + edge cases)
3. **Local checks**:

```bash
python -m pip install -e .[dev]
ruff check .
mypy src
pytest --cov=src/chatx --cov-fail-under=90 --cov-report=term-missing
```

4. Minimal code → pass tests → refactor → docs → ADR

### Feature Completion (Automated):
5. **Quality Gates**: `/complete` or `/tm/complete-task`
   - ✅ Tests ≥90% coverage, lint clean, types clean
   - ✅ Feature branch, conventional commit, detailed PR
   - ✅ TaskMaster updated, ConPort/OpenMemory logged
6. **Multi-Session**: Independent branches for concurrent work
7. **Integration**: PR review → merge → cleanup

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
| `/research`         | `.claude/commands/research.md`                   | **Context7 + Exa**: Auto-query library docs + web research.     |
| `/story`            | `.claude/commands/story.md`                      | Story + AC + NFR; write docs; ConPort decision.                 |
| `/plan`             | `.claude/commands/plan.md`                       | Sequential steps (+ slice mode); log to ConPort.                |
| `/implement`        | `.claude/commands/implement.md`                  | **Context7-driven TDD**: Library docs + examples integrated.    |
| `/debug`            | `.claude/commands/debug.md`                      | **Context7-verified**: Cross-reference official API docs.       |
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
| `/zen`              | `.claude/commands/zen.md`                        | Route instruction to Zen workflow.                              |
| `/zen-continue`     | `.claude/commands/zen-continue.md`               | Zen context recovery.                                           |
| `/git-commit`       | `.claude/commands/git/git-commit.md`             | Conventional Commit → push.                                     |
| `/pr-create`        | `.claude/commands/gh/pr-create.md`               | Open a PR.                                                      |
| `/pr-checks`        | `.claude/commands/gh/pr-checks.md`               | Monitor CI.                                                     |
| `/pr-merge`         | `.claude/commands/gh/pr-merge.md`                | Merge PR (squash).                                              |
| `/issue-create`     | `.claude/commands/gh/issue-create.md`            | Create issue.                                                   |

> **Token thrift**: Claude-Context ≤**3**; ConPort `limit` **3–5**; **TaskMaster** `status` + `withSubtasks=false`; **Zen** `files≤2` + `continuation_id`; **Context7** auto-integrated (no manual calls needed); prefer summaries before full context pulls.
- use serena for file and shell work