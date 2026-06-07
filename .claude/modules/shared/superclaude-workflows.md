# SuperClaude + Dopemux Workflow Integration

**Purpose**: Command-selection guidance and Dopemux-specific integration patterns for SuperClaude.
**For /dx: command specs** (full YAML, parameters, examples): see `.claude/modules/custom-commands.md`.
**For MCP tool contracts** (ConPort, Serena, PAL, Exa, GPT-Researcher): see `~/.claude/MCP_*.md` (auto-imported).

---

## Primary Development Flow

```
1. Session Start    /sc:load                    → ConPort: get_active_context
2. Task Selection   ConPort query               → filter by energy_level, complexity, cognitive_load
3. Code Navigation  Serena LSP                  → symbol search, complexity scoring
4. Implementation   /sc:implement <feature>     → Context7 patterns first, then PAL planner
5. Quality          PAL codereview + precommit  → multi-model validation before commit
6. Session End      /sc:save                    → ConPort: update_active_context + log_decision
```

---

## Command Selection Guide

### /sc: Commands — When to Use Which

**Analysis & Planning**:
- `/sc:analyze` — structured code/system analysis (routes to PAL thinkdeep)
- `/sc:brainstorm` — vague requests, requirements discovery (routes to PAL consensus)
- `/sc:design` — architecture decisions; log result in ConPort
- `/sc:estimate` — development estimation

**Implementation**:
- `/sc:implement` — feature development (Context7 patterns first, then PAL planner, agents coordinate)
- `/sc:improve` — code quality / performance pass (routes to PAL + Serena complexity)
- `/sc:cleanup` — dead code removal
- `/sc:build` — build and packaging

**Research & Documentation**:
- `/sc:research` — simple: Exa; with `--deep`: GPT-Researcher multi-source synthesis
- `/sc:document` — doc generation (Technical Writer agent)
- `/sc:explain` — educational explanations with progressive disclosure

**Session Management**:
- `/sc:load` — restore from ConPort active_context (always start here)
- `/sc:save` — persist to ConPort (always end here; log decisions)
- `/sc:reflect` — task validation with Serena semantic analysis

**Workflow & Debugging**:
- `/sc:workflow` — PRD to phased plan (routes to PAL planner)
- `/sc:task` — complex multi-step task management
- `/sc:troubleshoot` — error investigation (routes to PAL debug + Serena navigation)

### /dx: Commands — When to Use Which

Use /dx: commands for Dopemux-specific workflows requiring direct MCP integration or ADHD-optimized sessions. For full specs, parameters, and YAML: see `.claude/modules/custom-commands.md`.

- `/dx:prd-parse` — PRD decomposition → PAL planner → ConPort import (human review required before import)
- `/dx:implement` — ADHD-optimized 25-minute sessions with manual save checkpoints
- `/dx:analyze` — direct PAL thinkdeep (skip /sc: orchestration overhead)
- `/dx:review` — direct PAL codereview with multi-model validation
- `/dx:session` — focus session management
- `/dx:switch-role` — MetaMCP role switching (QUICKFIX, ACT, PLAN, RESEARCH, ALL)

---

## MCP Selection by Task Type

| Task | Use | Route |
|------|-----|-------|
| Quick lookup / recent docs | Exa | `/sc:research` default |
| Deep multi-source research | GPT-Researcher | `/sc:research --deep` |
| Linear feature breakdown | PAL planner | `/sc:workflow` |
| Multi-perspective decision | PAL consensus | `/sc:brainstorm` or direct `pal/consensus` |
| Complex investigation / root cause | PAL thinkdeep | `/sc:analyze` or `/dx:analyze` |
| Bug investigation | PAL debug | `/sc:troubleshoot` |
| Code navigation / symbol search | Serena LSP | `/sc:implement` or direct `serena/find_symbol` |
| Decisions / progress / patterns | ConPort | direct `conport/log_decision` + `log_progress` |
| Official framework docs | Context7 | mandatory before writing any framework code |
| Pre-commit validation | PAL precommit | before every commit |

**Full tool contracts**: `~/.claude/MCP_PAL.md`, `MCP_ConPort.md`, `MCP_Serena.md`, `MCP_Exa.md`, `MCP_GPTResearcher.md`.

---

## Agent Activation

SuperClaude auto-activates agents based on command context and file type:

- `/sc:implement` → Frontend + Backend + Security agents coordinate
- `/sc:troubleshoot` → Root Cause Analyst agent
- `/sc:research` → Deep Research agent
- `*.py` files → Python Expert; `*.tsx` → Frontend Architect; `Dockerfile` → DevOps Architect
- Keywords: "security audit" → Security Engineer; "performance" → Performance Engineer

For complex features, multiple agents run in parallel (e.g., payment system: System Architect + Backend + Frontend + Security + QA).

**15 available agents** map to MetaMCP roles — tool-level boundaries enforced via MetaMCP role-based filtering per `.claude/modules/superclaude-integration.md`.

---

## Common Workflow Patterns

### Feature Implementation
1. `Context7` — query framework docs first (mandatory)
2. `/sc:workflow` — PAL planner breakdown into phases
3. `serena/find_symbol` or `find_similar_code` — locate existing patterns
4. `/sc:implement` — agents coordinate; Magic generates UI components
5. `/sc:test` — Playwright automated testing
6. `pal/codereview` → `pal/precommit` — quality gate
7. `conport/log_decision` — document any architectural choices; create ADR if needed

### Bug Investigation
1. Capture error + logs + context
2. `/sc:troubleshoot` or direct `pal/debug` — hypothesis-driven analysis
3. `serena/find_symbol` from stack trace — navigate to root cause
4. Implement fix → `pal/codereview` — verify correctness + add regression test
5. `conport/log_decision` — record why the bug occurred

### Research & Decision
1. Exa quick search — get an overview
2. `/sc:research --deep` (GPT-Researcher) if multi-source synthesis needed
3. `pal/consensus` — for/against/neutral perspectives on approach
4. `conport/log_decision` + ADR in `docs/90-adr/` — single source of truth

---

## ADHD Session Notes

**Observed runtime support**: `/sc:load`, `/sc:save`, manual `dopemux save`, `/dx:save`, lifecycle hook dispatch (Stop/energy/progress signals).

**Not proven wired**: `/dx:implement` automatic timers, recurring save checkpoints every 5 min, break prompts, and hyperfocus pause enforcement. Use `/loop` or `ScheduleWakeup` if you need scheduled saves/reminders.

For the full ADHD behavioral contract (max-3-options, gentle language, attention-state adaptation, energy routing, session specs): see `.claude/modules/shared/adhd-patterns.md`.

---

## Troubleshooting

**MCP not responding**:
```bash
claude mcp list          # check status
```

**SuperClaude command not found**:
```bash
cat ~/.claude/.superclaude-metadata.json
ls ~/.claude/commands/sc/<command>.md
```

**Context not restoring after `/sc:load`**:
```bash
# Verify ConPort directly
conport/get_active_context --workspace_id <path>
conport/get_recent_activity_summary --workspace_id <path> --hours_ago 24

# Check local context DB (if ADHD engine is running)
sqlite3 .dopemux/context.db "SELECT * FROM session_metadata ORDER BY last_active DESC LIMIT 5"
```

**PAL tool errors**: confirm `mcp__pal__*` is in your session's deferred-tools list; use `advisor()` as fallback for second-opinion reasoning.
