# SuperClaude Integration Module

**Purpose**: SuperClaude command framework enhanced with Dopemux MCPs
**Decision Reference**: #133, #134 (Strategy), #142–144 (Implementation)
**SuperClaude Version**: 4.1.5

**Observed runtime support**: `/sc:` command integration, manual `/dx:save`, `dopemux save`, registered lifecycle hook dispatch, and best-effort Stop/energy/progress hook signals.

**Planned/specification behavior**: `/dx:implement` timers, recurring save checkpoints, break prompts, and hyperfocus pause enforcement are not proven wired in observed Claude runtime.

**`/dx:` command specs**: see `.claude/modules/custom-commands.md` (768L, full YAML per command).

---

## Why SuperClaude?

SuperClaude provides a 25-command framework with 15 specialized agents. Dopemux's MCP stack extends it with superior tooling:

| Feature | SuperClaude Default | Dopemux MCP Stack |
|---------|-------------------|-------------------|
| Multi-model Consensus | None | PAL (thinkdeep, planner, consensus, debug, codereview) |
| Knowledge Graph | Basic memory | ConPort PostgreSQL AGE |
| Code Intelligence | Basic LSP | Serena (LSP + semantic + ADHD) |
| Neural Search | Tavily | Exa (neural) |
| Deep Research | None | GPT-Researcher (4 engines) |
| Documentation | Context7 | Context7 (kept as-is) |

**MCP substitutions applied**: `sequential` → `pal`, `tavily` → `exa` + `gpt-researcher`. Kept: `context7`, `serena`, `morphllm`, `magic`, `playwright`.

**superclaude.yaml key settings**: PAL enabled (consensus/planner/thinkdeep/debug/codereview), ConPort workspace_id auto-detect from git root, Serena adhd_mode true, Exa neural_search true, GPT-Researcher 4-engine, tavily disabled, role_switching via MetaMCP, session_duration 25 min, max_options 3, max_detail_levels 3.

---

## 25 Standard Commands — 4-Category Mapping

### Category 1: USE AS-IS (5 commands)
No enhancement needed — straightforward automation:

1. `/sc:build` — run build process
2. `/sc:deploy` — deploy to environment
3. `/sc:cleanup` — clean up code/files
4. `/sc:spec-panel` — show spec panel
5. `/sc:help` — show help

### Category 2: ENHANCE with Dopemux MCPs (11 commands)

| Command | Enhancement | Tool Routed To |
|---------|-------------|----------------|
| `/sc:brainstorm` | Multi-model idea validation | `mcp__pal__consensus` |
| `/sc:estimate` | 3-model consensus on sizing | `mcp__pal__consensus` |
| `/sc:test` | Test file nav + coverage | `mcp__serena-v2__find_test_file` |
| `/sc:fix` | Systematic root-cause | `mcp__pal__debug` |
| `/sc:troubleshoot` | Deep multi-model debug | `mcp__pal__debug` |
| `/sc:improve` | Semantic refactor patterns | `mcp__serena-v2__find_similar_code` |
| `/sc:optimize` | Hot-path profiling | `mcp__serena-v2__get_unified_complexity` |
| `/sc:document` | Framework-specific examples + ADHD progressive disclosure | `mcp__context7__get-library-docs` |
| `/sc:explain` | Progressive disclosure, max 3 detail levels, visual indicators | (output convention) |
| `/sc:reflect` | Session progress + decision log retrieval | `mcp__conport__get_progress` + `get_decisions` |
| `/sc:index` | Code-to-decision graph links | `mcp__conport__link_conport_items` |

### Category 3: CUSTOMIZE as /dx: Commands (8 commands)
Completely reimplemented for ADHD workflows — full specs in `custom-commands.md`:

| Original | Dopemux Replacement | Purpose |
|----------|--------------------|---------| 
| `/sc:workflow` | `/dx:prd-parse` | PRD decomposition with human review gate |
| `/sc:implement` | `/dx:implement` | ADHD 25-min sessions, energy matching |
| `/sc:design` | `/dx:design` | PAL consensus for architecture decisions |
| `/sc:analyze` | `/dx:analyze` | PAL thinkdeep deep investigation |
| `/sc:review` | `/dx:review` | PAL codereview multi-model validation |
| `/sc:load` | `/dx:load` | ConPort session context restore |
| `/sc:checkpoint` | `/dx:save` | ConPort session state persist |
| `/sc:research` | `/dx:research` | Exa neural + GPT-Researcher 4-engine |

### Category 4: REPLACE (1 command)

`/sc:task` → **ConPort `progress_entry` directly** — direct MCP access is simpler than a command wrapper. Use `mcp__conport__log_progress` / `get_progress` / `update_progress` directly.

---

## 15 Specialized Agents → MetaMCP Role Mapping

| SuperClaude Agent | MetaMCP Role | Tools Mounted | Use Case |
|------------------|--------------|---------------|----------|
| Deep Research Agent | RESEARCH | Exa, GPT-Researcher, PAL, Context7 (10 tools) | Investigation, analysis |
| Analyzer Agent | RESEARCH | PAL thinkdeep, ConPort, Serena (9 tools) | Problem analysis |
| Strategic Analyst | RESEARCH + PLAN | PAL consensus, ConPort decisions (9 tools) | Architecture decisions |
| Frontend Architect | ACT | Serena, Context7 (React/Next.js), morphllm (10 tools) | UI implementation |
| Backend Developer | ACT | Serena, Context7 (FastAPI/Django), ConPort (10 tools) | API implementation |
| Developer (General) | ACT | Full implementation stack (10 tools) | General development |
| Security Engineer | ACT | PAL secaudit, Context7 (OWASP), Serena (10 tools) | Security review |
| QA Engineer | ACT | Serena test nav, ConPort progress, Context7 (10 tools) | Testing |
| Performance Specialist | ACT | Serena profiling, PAL analysis, Context7 (10 tools) | Optimization |
| DevOps Engineer | ACT | ConPort, Context7 (Docker/K8s) (8 tools) | Deployment |
| Refactorer | ACT | Serena semantic, PAL codereview, Context7 (10 tools) | Code improvement |
| Architect | PLAN | PAL consensus + planner, ConPort decisions (9 tools) | System design |
| Technical Writer | PLAN | Context7, ConPort, PAL (8 tools) | Documentation |
| Developer (Simple) | QUICKFIX | Serena basic, ConPort progress (8 tools) | Quick fixes |
| Mentor | ALL | All tools (60+) | Teaching, guidance |

---

**See Also**:
- `.claude/modules/custom-commands.md` — Full `/dx:` command YAML specs
- `.claude/modules/shared/superclaude-workflows.md` — Complete workflow patterns + command selection guide
- `.claude/modules/shared/adhd-patterns.md` — ADHD session management, observed vs planned support
- `.claude/modules/coordination/authority-matrix.md` — Authority boundaries
