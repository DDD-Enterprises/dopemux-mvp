---
title: CLAUDE.md Audit Report
date: 2026-06-06
type: audit
owner: houston@krohman.org
scope: 38 active CLAUDE.md/claude.md files (14 in-repo + global CLAUDE.md + 23 framework modules)
method: 2 multi-agent passes (68 + 46 agents) with filesystem cross-referencing + adversarial verification of 104 claims
---

# CLAUDE.md Audit Report

**Generated:** 2026-06-06 · **Files audited:** 38 · **Corrected average:** 74/100 · **Grades:** A×2 B×22 C×10 D×3 F×1

> Excluded by scope: 25 vendored/historical files under `ARCHIVED_RECOVERY/` and `docs/**/history/sourceFiles/`.

## How this was produced

- **Discovery** — case-insensitive scan of git-tracked + working-tree files. The repo uses **lowercase `claude.md`** everywhere (root + per-module monorepo pattern); a naive `find -name CLAUDE.md` misses the most important files.
- **Scoring** — 6-criterion rubric (Commands 20 · Architecture 20 · Non-obvious patterns 15 · Conciseness 15 · Currency 15 · Actionability 15). The 23 `~/.claude` framework files were scored on an adapted *doctrine* rubric (tool-reference currency replaces build-commands).
- **Cross-referencing** — every referenced path/command/tool was checked against the real filesystem.
- **Adversarial verification** — 104 falsifiable claims independently re-checked by skeptic agents. **28 were refuted or materially corrected**; those are excluded from the defect counts and listed under *Verification corrections*.

## ⭐ The one systemic finding

**The inherited upstream SuperClaude doctrine references tools and command flags that do not exist in this Dopemux install.** This is the single largest source of defects and spans 6+ files:

- **Phantom MCP tools:** `Magic`, `Morphllm`, `Playwright`, `Sequential` (renamed → PAL), `Context7`, `MultiEdit` are cited as routing targets in `MODE_Orchestration.md`, `MODE_Task_Management.md`, `MODE_Business_Panel.md`, `BUSINESS_SYMBOLS.md`, `FLAGS.md`, `RULES.md` — but only 7 MCPs are actually documented/loaded (PAL, ConPort, Serena, DopeContext, Exa, GPTResearcher, DesktopCommander). *(Playwright exists as a plugin but has no `MCP_*.md` and isn't in the active config.)*
- **Fabricated CLI flags:** `MODE_Business_Panel.md` + `BUSINESS_PANEL_EXAMPLES.md` document `--christensen-focus`, `--porter-focus`, `--interaction`, `--budget`, `--depth`, etc. and claim `--business-panel` works on `/sc:analyze|improve|design|implement`. The real `business-panel` command supports only `--experts --mode --focus --synthesis-only --structured --verbose --questions`, and none of the other four commands accept `--business-panel`. **Verified false.**
- **Phantom 'memory' API:** `MODE_Task_Management.md` is built entirely around `write_memory()`, `read_memory()`, `list_memories()`, `think_about_*()`, `delete_memory()` — **none exist** in any MCP or the harness. ConPort uses `log_decision`/`log_progress`/`update_active_context`. This makes the file's pseudo-code unexecutable (→ **F, 42**).

**Why it matters:** the global `CLAUDE.md`, `RULES.md`, `FLAGS.md`, and `MODES_AND_TOOLS.md` already added explicit *'tool availability is session-dependent / check before insisting'* disclaimers (which is why they score B+). The `MODE_*` and `BUSINESS_*` files never got that treatment. **Fix pattern:** add the same reality-check disclaimer to those files, rename `Sequential→PAL`, and mark the unavailable tools/flags as upstream-SuperClaude-not-installed.

## Second theme: in-repo module-memory drift

The per-directory `*/.claude/claude.md` files describe directory layouts that no longer match the filesystem (all confirmed):

| File | Drift (verified) |
|---|---|
| `config/.claude/claude.md` (D 41) | Documents dirs `mcp/ routing/ logging/ environments/` (none exist) and ADHD profiles `low_energy/medium_energy/high_energy.yaml` (actual: `adhd-default/safe/dangerous/python-ml/web-dev/...`). `.claude.json` claimed in `config/` but lives at repo root. |
| `scripts/.claude/claude.md` (C 69) | Documents 6 dirs (`deployment/ testing/ maintenance/` don't exist); actual `scripts/` has **25** subdirs, ~20 undocumented. `deployment/start_stack.sh` path wrong (actual `deploy/deployment/`). |
| `tools/.claude/claude.md` (C 62) | Documents **1** tool; `tools/` has ~12 (5 CLI scripts + `auditor_router/ copilot_repair/ pr_action_bridge/ pr_steward/ prompt_rewrite_v4/`). |
| `shared/.claude/claude.md` (C 57) | Documents `models/ clients/ utils/`; actual `shared/` has `config.py monitoring/ service_discovery.py storage.py dependency_container.py`. |
| `src/.claude/claude.md` (B 77) | Lists `code_commands.py` (doesn't exist); 8 real command files unlisted; `pytest tests/dopemux/` doesn't match Makefile (`pytest tests`). |
| `docker/.claude/claude.md` (C 73) | Lists only `conport/ zen/ serena/` (zen doesn't exist; ~12 servers undocumented); broken cross-link to `docker/mcp-servers/.claude/claude.md`. |
| `tests/.claude/claude.md` (B 88) | `e2e/` dir doesn't exist; **all 4 documented fixtures absent from conftest.py** (real fixtures are entirely different). |

## Third theme: ships-to-users artifact

`src/dopemux/templates/init/.claude/claude.md` (C 70) is copied into every new project by `dopemux init` (`project_init.py:227`). It contains a stray **`!*** End Patch`** marker (line 143), dead doc links (`docs/HAPPY_CODER_USAGE_GUIDE.md`, `docs/ORCHESTRATOR_WORKFLOW.md`), and reads as an accidental merge of two documents. **Recommend fixing regardless of audit scope** — every downstream user inherits it.

## Quick wins (trivial, high-value)

1. `~/.claude/CLAUDE.md` — TOC anchor `#superclaudopec-laude-integration` is a typo for `#superclaude-dopeclaude-integration` (broken nav link).
2. `~/.claude/MCP_DopeContext.md` — references `services/dope-context/FINAL_TEST_REPORT.md` which doesn't exist.
3. `~/.claude/MCP_Serena.md` — instructs `python services/serena/v2/auto_activator.py`; real path is `services/serena/auto_activator.py` (no `v2/`).
4. `docker/mcp-servers-source/pal/pal-mcp-server/CLAUDE.md` — titled 'Zen MCP Server' + references `.zen_venv/` and `logs/` that don't exist (Zen→PAL rename incomplete).
5. `~/.claude/MCP_Exa.md` — `include_domains` used in an example but missing from the Parameters list.

## Orphaned global files

- `~/.claude/ADHD_FEATURES.md` (B 70) — **not `@import`ed** by `~/.claude/CLAUDE.md`, and its accommodations diverge from CLAUDE.md's inline ADHD section (content drift). Either import it or fold it in.
- `~/.claude/MCP_DesktopCommander.md` (B 82) — **not `@import`ed**; only mentioned as a 'manual MCP'. Intentional, but inconsistent with the other 6 MCP docs which are imported.

## Verification corrections (findings the skeptic pass DROPPED or fixed)

These were raised by the first-pass auditors but **refuted on re-check** — do not act on them:

1. `repo:.claude/claude.md` — 'AGENTS.md `../AGENTS.md` is a dead link' → **link resolves correctly** (5 instances). No action.
2. `repo:.claude/claude.md` — 'SuperClaude v4.1.5 / 25-7-16 counts unverified' → **corroborated** by `superclaude-workflows.md`. Accurate.
3. `repo:.claude/claude.md` — '11 hooks vs 10 scripts mismatch' → doc is **correct** (11 lifecycle *events*, 10 scripts via 1 dispatcher). Not a bug.
4. `repo:docs/03-reference/instructions/claude.md` — 'dead `@import` files' and '`settings.local.json` not provided' → **misattributed** (that file has no `@import`s; both settings files exist). The `@import` issue belongs to `reports/downloads_audit/CLAUDE.md` only.
5. `repo:reports/downloads_audit/CLAUDE.md` — 'identical copy-paste of the instructions file' → **false**, they're different. (It IS generic/untailored — that part stands.)
6. `repo:config/.claude/claude.md` — '`services/registry.yaml` missing' → **exists** at repo root. (Other config drift stands.)
7. `repo:docker/.claude/claude.md` — 'pr-docgen-sync trigger unclear' → **clearly documented**.
8. `repo:services/.claude/claude.md` — 'says conport is in services/' → doc **correctly** notes `docker/mcp-servers/`.
9. `~/.claude/MCP_GPTResearcher.md` — 'use-gpt-researcher.md doesn't flag context-dependency' → it **does**, explicitly.
10. `~/.claude/MODE_DeepResearch.md` — 'deep-research-agent persona doesn't exist' → it **exists** at `~/.claude/agents/deep-research-agent.md`. (Sequential→PAL and Tavily staleness DO stand.)
11. `~/.claude/BUSINESS_PANEL_EXAMPLES.md` — 'duplicates MODE/SYMBOLS templates' → **distinct content** (flag-usage vs templates). (Fabricated-flag findings stand.)

## Per-file detail (all 38, worst → best)

### 🔴 D · 41/100 — `repo: config/.claude/claude.md`
<sub>module-memory · cmd 5 · arch 8 · patterns 6 · concise 12 · currency 4 · action 6</sub>

Documentation describes phantom directories (mcp/, routing/, logging/, environments/) and outdated profile names (low_energy, medium_energy, high_energy) that don't exist; .claude.json and services/registry.yaml are absent. References paths that cannot be verified.

- `high ·verifiable` Directory 'mcp' claimed in structure but does not exist
- `high ·verifiable` Directory 'routing' claimed in structure but does not exist
- `high ·verifiable` Directory 'logging' claimed in structure but does not exist
- `high ·verifiable` Directory 'environments' claimed in structure but does not exist
- `high ·verifiable` File '.claude.json' claimed at line 26 but is not in config/ (it exists at project root)
- `high ·verifiable` File 'services/registry.yaml' claimed at line 27 but does not exist anywhere in config/
- `high ·verifiable` Profile names are completely outdated: documentation says 'low_energy.yaml', 'medium_energy.yaml', 'high_energy.yaml' (lines 62-64) but actual files are 'adhd-default.yaml', 'safe.yaml', 'dangerous.yaml', 'python-ml.yaml', 'web-dev.yaml', 'workflow-executor.yaml', 'workflow-manager.yaml'
- `medium` Python code example shows Pydantic v1 pattern (BaseSettings) but v2 may be in use; no validation that pattern actually matches codebase

### 🔴 F · 42/100 — `global: ~/.claude/MODE_Task_Management.md`
<sub>Behavioral Mode Doctrine · cmd 2 · arch 14 · patterns 10 · concise 8 · currency 5 · action 3</sub>

Critically flawed doctrine: references non-existent tools (write_memory, think_about_*, delete_memory, TodoWrite) and falsely positioned as ConPort-backed memory system. Activates on criteria (>3 steps) unverifiable in-session. Orphan status unclear but dangerous if auto-loaded.

- `high ·verifiable` These function names do NOT exist in any MCP documentation. ConPort uses conport/log_progress, conport/log_decision, conport/get_active_context, etc. The 'memory' terminology is misleading—ConPort is a knowledge graph, not a memory vault. Agents cannot execute write_memory("plan") as shown.
- `high ·verifiable` These do not exist as real MCP tools, skills, or native harness functions. They appear to be pseudocode/descriptive placeholders, but the doc presents them as executable. An agent following this literally will fail.
- `high ·verifiable` No such function exists. ConPort has conport/delete_decision_by_id and conport/delete_progress_by_id, but no bulk delete or memory purge pattern. This suggests confusion with a different system.
- `high ·verifiable` TodoWrite is mentioned as a native tool in MODES_AND_TOOLS.md as 'in-conversation todo list, ephemeral' (not an MCP). It is NOT an MCP tool to invoke. MODE_Task_Management.md treats it as a coordinated tool alongside write_memory()—a category error.
- `high ·verifiable` Table at line 54-60 lists tool aliases for task types. None of these are documented in /Users/hue/.claude/MCP_*.md files. These may be aspirational or obsolete project-internal names.
- `medium ·verifiable` No mechanism exists to auto-trigger modes based on operation scope. The harness cannot count steps or directory scope during planning. Users would need to manually flag --task-manage, which is documented but contradicts the 'automatic' framing.
- `medium ·verifiable` No mechanism exists to call MCP tools on a timer. This is aspirational (would require /schedule or /loop skill, not documented in this file). An agent cannot unilaterally set checkpoints every 30 minutes.
- `low` The hierarchical structure (Plan → Phase → Task → Todo) is conceptually sound and describes a valid ADHD accommodation. But the implementation is unexecutable due to tool name mismatches above.

### 🔴 D · 42/100 — `global: ~/.claude/BUSINESS_PANEL_EXAMPLES.md`
<sub>Global Doctrine - Usage Examples & Patterns · cmd 8 · arch 14 · patterns 9 · concise 7 · currency 2 · action 2</sub>

Extensive example collection undermined by fabricated command flags and non-existent flag integration; demonstrates aspirational rather than tested workflows. Most examples show operations that will fail if executed (--christensen-focus, --interaction, --budget, --business-panel on other commands). Substantial actionability and currency deficits.

- `high ·verifiable` Fabricated customization options section (lines 206-240) documents unsupported CLI flags with no basis in actual /sc:business-panel implementation. Flags like --christensen-focus, --porter-focus, --interaction, --symbols, --depth, --budget, --quick, --comprehensive do not exist in business-panel.md command definition.
- `high ·verifiable` Integration Workflows section (lines 179-204) documents --business-panel flag on commands that don't support it. Examples show '/analyze @doc --business-panel', '/improve @strategy_doc.md --business-panel', '/design strategy --business-panel', '/implement risk_mitigation --business-panel' as valid syntax. None of these four commands (/sc:analyze, /sc:improve, /sc:design, /sc:implement) have --business-panel flags in their definitions.
- `high` Performance Standards section (lines 262-278) documents unvalidated token and response time claims without evidence. Claims discussion_mode consumes '8-15K tokens', debate_mode '10-20K tokens', socratic_mode '12-25K tokens', synthesis_only '3-8K tokens'. Also claims response times: simple_analysis '< 30 seconds', comprehensive_analysis '< 2 minutes'. No empirical validation provided.
- `medium ·verifiable` Duplicates synthesis output templates already in MODE_Business_Panel.md and BUSINESS_SYMBOLS.md. Lines 133-177 provide 'Output Format Variations' (Executive Summary, Framework-by-Framework, Question-Driven formats) that largely mirror template guidance elsewhere in the trilogy. Violates conciseness: avoidable duplication.
- `medium ·verifiable` Combined /sc/analyze --business-panel and /improve @strategy_doc.md --business-panel examples (lines 62-82) suggest business-panel is a generic integration flag across the SuperClaude command family. This contradicts the architecture: business-panel is a standalone /sc:business-panel command, not a flag on other commands.
- `low` Quality Validation section (lines 242-279) documents subjective quality checks ('framework authenticity > 90%', 'strategic relevance > 85%', 'actionable insights > 80%') with no measurement methodology or validation harness. These are aspirational standards, not verifiable SLAs.

### 🔴 D · 54/100 — `global: ~/.claude/MODE_Orchestration.md`
<sub>doctrine · cmd 10 · arch 12 · patterns 8 · concise 11 · currency 6 · action 7</sub>

Attempts to define resource-aware tool selection but Tool Selection Matrix references 5 non-existent/unavailable MCPs (Magic, Sequential→PAL, Morphllm, Playwright, MultiEdit); Resource Management zones (75%/85%) are non-actionable (no harness gauge); lowest actionability of the four.

- `high ·verifiable` Tool Selection Matrix references 5 non-available/phantom tools in Dopemux framework
- `high ·verifiable` Resource Management zones (75%, 85%) are non-actionable—no harness API to query resource usage
- `medium` Parallel Execution Triggers (line 50) reference '>3 files' heuristic but lack context on which tool counts

### 🟠 C · 57/100 — `repo: shared/.claude/claude.md`
<sub>module-memory · cmd 5 · arch 10 · patterns 8 · concise 14 · currency 12 · action 8</sub>

Minimal, policy-focused documentation that doesn't match actual directory structure; needs concrete examples and directory layout verification.

- `high ·verifiable` Documented directory structure does not match reality
- `high` No test coverage documentation or testing commands provided
- `medium` Missing concrete code examples
- `medium` No guidance on version management or deprecation

### 🟠 C · 57/100 — `global: ~/.claude/BUSINESS_SYMBOLS.md`
<sub>Global Doctrine - Reference System · cmd 14 · arch 17 · patterns 11 · concise 9 · currency 5 · action 1</sub>

Solid symbol and abbreviation taxonomy with good structural clarity, but carries inherited Sequential/Magic/Playwright staleness, internal symbol collision (💬 and 🌐), and duplicates synthesis templates already in MODE_Business_Panel. Currency and conciseness are main weaknesses.

- `high ·verifiable` Internal symbol collision: 💬 is assigned to Doumont (line 31, Framework Integration table) as 'Clear Communication' but also to Godin (line 66, Expert Voice Symbols) as 'Conversational, provocative'. An agent rendering output with both symbols cannot disambiguate which expert is speaking.
- `medium ·verifiable` Meadows symbol is inconsistent: 🕸️ in Framework Integration table (line 30, 'System Structure') vs 🌐 in Expert Voice Symbols (line 70, 'Holistic, systems-focused'). Both refer to the same expert; unclear which symbol should be used in actual output.
- `high ·verifiable` Carries Sequential MCP staleness from broader framework. Line 188 shows 'mcp_sequential_primary: true' but PAL replaced Sequential per MCP_PAL.md.
- `medium ·verifiable` Duplicates synthesis template structure already fully documented in MODE_Business_Panel.md. Lines 73-133 provide Synthesis Output Templates that are nearly identical to MODE_Business_Panel.md lines 254-315 (Discussion, Debate, Socratic modes with symbol annotation). Violates conciseness rubric on duplication.
- `low ·verifiable` References Magic and Playwright in Mode Configuration (lines 182-191) without documented contracts. These tools are listed in the global FLAGS/RULES framework but have no MCP_Magic.md or MCP_Playwright.md in this install.
- `low` No dates, version, or freshness metadata in the file. Symbols themselves (💬, 🎯, 📈) are stable and unlikely to go stale, but YAML configuration blocks lack 'last updated' or verification markers.

### 🟠 C · 58/100 — `global: ~/.claude/MODE_Business_Panel.md`
<sub>Global Doctrine - Behavioral Mode · cmd 12 · arch 16 · patterns 12 · concise 11 · currency 4 · action 3</sub>

Comprehensive but operationally compromised: core 3-phase analysis structure is sound, but references nonexistent MCP tools (Sequential/Context7/Magic/Playwright), lists unsupported command flags (--christensen-focus, --interaction, --budget), and claims --business-panel integration with /analyze/improve/design/implement that doesn't exist. Lazy-loaded correctly but Wave mode aspirational.

- `high ·verifiable` Sequential MCP reference is stale — MCP_PAL.md explicitly states PAL 'formerly zen-mcp' replaced 'Sequential MCP'. Mode doc lists Sequential as primary (line 325) but this server no longer exists under that name.
- `high ·verifiable` Fabricated command flags with no basis in actual /sc:business-panel implementation. Examples doc lists --christensen-focus, --porter-focus, --interaction (collaborative/challenging), --symbols, --depth, --budget, --quick, --comprehensive, --all-experts, --experts-max as supported options, but none appear in /Users/hue/.claude/commands/sc/business-panel.md.
- `high ·verifiable` Falsely claims --business-panel flag integration with /sc:analyze, /sc:improve, /sc:design, /sc:implement. Examples doc shows '/analyze @business_model.md --business-panel', '/improve @strategy_doc.md --business-panel', '/design business-model --business-panel', '/implement risk_mitigation --business-panel --validate' as valid usage. None of these flags exist in the command definitions.
- `medium ·verifiable` Wave Mode Integration section claims wave-enabled operations but Wave is not a documented behavioral mode in the SuperClaude framework. CLAUDE.md lines 248-254 @import exactly six modes (Brainstorming, DeepResearch, Introspection, Orchestration, Task_Management, Token_Efficiency); Wave is not among them.
- `medium ·verifiable` References Context7 as a core MCP for 'Business frameworks, management patterns, strategic case studies' (line 326) but no MCP_Context7.md exists, it's not @imported in CLAUDE.md, and is not in the available MCP list. CLAUDE.md mentions Context7 as a workspace-independent server but provides no contract details.
- `medium ·verifiable` References Magic and Playwright MCPs (lines 327-328) with no supporting documentation. No MCP_Magic.md, MCP_Playwright.md, or skill definitions for these tools. These tools are inherited from the broader FLAGS/RULES framework but undocumented in this project's MCP suite.
- `low ·verifiable` Expert selection algorithm and domain mapping use lowercase names (christensen, drucker, porter, etc.) in YAML examples but command usage shows title-cased variants ('christensen' vs 'Christensen'). Inconsistency in whether CLI expects lowercase keys.

### 🟠 C · 59/100 — `global: ~/.claude/MODE_DeepResearch.md`
<sub>doctrine · cmd 11 · arch 11 · patterns 10 · concise 9 · currency 8 · action 10</sub>

Activates via /sc:research command with stale MCP reference (Sequential→PAL); light on content overlap with MCP_GPTResearcher.md and RESEARCH_CONFIG.md; Tavily reference is superseded by Exa/GPT-Researcher.

- `high ·verifiable` Core tool reference stale: Sequential MCP renamed to PAL MCP
- `medium ·verifiable` Tavily reference is outdated; replaced by Exa + GPT-Researcher
- `low ·verifiable` Content duplication with downstream doctrine files
- `low ·verifiable` Section reference to 'deep-research-agent' persona not validated

### 🟠 C · 62/100 — `repo: tools/.claude/claude.md`
<sub>module-memory · cmd 12 · arch 10 · patterns 10 · concise 13 · currency 8 · action 9</sub>

Standards are clear and concise but critically incomplete. Only documents one tool (ports_health_audit.py) when tools/ actually contains 14 subdirectories and ~12 actual tools. Provides no architectural overview of tool relationships.

- `high ·verifiable` Only one tool documented (ports_health_audit.py at line 23) when tools/ contains ~12 tools across 14 subdirectories: env_drift_scan.py, generate_smoke_env.py, smoke_runtime_gate.py, webhook_receiver.py, plus auditor_router/, copilot_repair/, pr_action_bridge/, pr_steward/, prompt_rewrite_v4/ and __init__.py
- `medium` No documentation of tool subdirectories or their purpose (auditor_router, copilot_repair, pr_action_bridge, pr_steward, prompt_rewrite_v4)
- `medium` No mention of dependencies or compatibility between tools, or how they are invoked

### 🟠 C · 62/100 — `global: ~/.claude/PRINCIPLES.md`
<sub>doctrine · cmd 0 · arch 12 · patterns 13 · concise 14 · currency 15 · action 8</sub>

[Doctrine, adapted rubric] Theoretical engineering principles (SOLID, KISS, YAGNI) with low actionability; no concrete examples, commands, or project-specific guidance; serves more as philosophy than operational doctrine.

- `high` File lacks concrete actionable guidance: no code examples, no commands, no verification steps
- `medium` Principles file duplicates concepts already in RULES.md (Evidence-Based, Task-First, Parallel Thinking)
- `medium` No integration with the rest of the doctrine stack; unclear when to apply these principles vs. specific rules
- `low` SOLID principles (lines 13-18) are software design concepts, not Claude Code behavior principles

### 🟠 C · 69/100 — `repo: scripts/.claude/claude.md`
<sub>module-memory · cmd 16 · arch 10 · patterns 12 · concise 14 · currency 6 · action 11</sub>

Script standards are clear and well-formatted with good emoji/error patterns, but directory structure is significantly outdated. Documented folders (deployment/, testing/, maintenance/) don't exist; actual structure is audit/, deploy/, dev/, monitoring/, docs_audit/, indexing/ plus 25+ others not mentioned.

- `high ·verifiable` Documented directory 'deployment/' at line 13 does not exist; similar directories listed at lines 13-18 do not match actual structure
- `high ·verifiable` Documented directory 'testing/' at line 15 does not exist
- `high ·verifiable` Documented directory 'maintenance/' at line 18 does not exist
- `high ·verifiable` Actual directories NOT documented include: audit, deploy, dev, docs_audit (exists), external-references, git-hooks, gpt-researcher, indexing (exists), legacy, legacy_tmux, mcp, mcp-wrappers, memory, migration, mobile, monitoring (exists), orchestrator, routing, skills, sql, ui, utilities, webhooks
- `high ·verifiable` File 'deployment/start_stack.sh' referenced at line 31 does not exist at that path; actual file is in scripts/deploy/deployment/start_stack.sh

### 🟠 C · 70/100 — `repo: src/dopemux/templates/init/.claude/claude.md`
<sub>template · cmd 16 · arch 12 · patterns 10 · concise 11 · currency 10 · action 11</sub>

Template file appears to be an accidental merge/patch of two docs (orchestrator guide + ADHD config); references missing guide files and ends with stale patch marker.

- `high` File appears to be an accidental merge of two distinct documents — Dopemux Orchestrator Guide + Python Config — with mismatched headers and a stale patch marker
- `high ·verifiable` Referenced documentation files do not exist
- `medium ·verifiable` Stale patch marker at end of file
- `medium` Template lacks a coherent identity — mixes orchestrator role guidance with generic ADHD dev config
- `low ·verifiable` Missing reference context: PROJECT_INSTRUCTIONS.md and PRIMER.md references (lines 1-2) are present but no explanation of their role

### 🟢 B · 70/100 — `global: ~/.claude/ADHD_FEATURES.md`
<sub>Global Doctrine (Behavioral Accommodations) · cmd 8 · arch 15 · patterns 12 · concise 12 · currency 13 · action 10</sub>

Solid behavioral guidance on ADHD accommodations (context preservation, task decomposition, decision logging). Integrated into CLAUDE.md. References dopemux save/restore and ConPort patterns without hard tool dependencies. Some features (Pomodoro timer, 25-min auto-save) are aspirational; others (decision logging, progress tracking) are actionable via ConPort.

- `high ·verifiable` No mechanism in CLAUDE.md or skill definitions shows Dopemux auto-loading context. ADHD_FEATURES.md assumes Dopemux integration (lines 136-154) but does not specify HOW. No skill named /dopemux-restore exists in deferred-tools or skills list.
- `medium ·verifiable` No built-in timer or reminder mechanism in the harness enforces breaks. This requires /schedule or /loop skill (external to this file). No mention of how break enforcement interacts with long-running operations.
- `medium ·verifiable` ConPort tools (conport/log_decision, conport/log_progress) do this, but ADHD_FEATURES.md does not reference ConPort by name until line 140 (Integration with Dopemux section). Earlier sections (1-139) are orphaned from the actual tool guidance.
- `medium ·verifiable` The YAML schema is descriptive only. No MCP provides real-time attention state classification. An agent cannot programmatically detect 'deep_focus' vs 'distracted' and auto-switch response style.

### 🟠 C · 71/100 — `repo: tests/resources/test_docs/claude.md`
<sub>fixture · cmd 15 · arch 12 · patterns 9 · concise 12 · currency 11 · action 12</sub>

Test fixture for ADHD Python config; intentional incomplete template suitable for testing, but has duplicated MCP server listing and lacks coherence as a standalone fixture.

- `low` Duplicate/partial MCP server listing — appears to be a copy from another template
- `low` No test metadata or comment indicating purpose as a fixture
- `low` No reference to actual test file that uses this fixture

### 🟠 C · 73/100 — `repo: docker/.claude/claude.md`
<sub>module-memory · cmd 16 · arch 14 · patterns 8 · concise 13 · currency 10 · action 12</sub>

Well-structured with accurate commands and directory mapping, but references a non-existent cross-file link (docker/mcp-servers/.claude/claude.md in wrong repo) and is missing actual MCP server details (conport, serena, desktop-commander, etc. in mcp-servers-source/).

- `high ·verifiable` Cross-file reference points to wrong location: docker/mcp-servers/.claude/claude.md exists at docker/mcp-servers-source/.claude/claude.md (via symlink at docker/mcp-servers)
- `medium ·verifiable` Directory structure shows only 'conport/', 'zen/', 'serena/' as MCP servers (lines 15-16) but actual docker/mcp-servers-source/ contains ~30 servers including conport-bridge, desktop-commander, dopemux, exa, gpt-researcher, litellm, pal, services, etc.
- `medium` Port table (lines 53-57) missing actual port mappings; compose.yml shows CONPORT at 3004 and ADHD_ENGINE at 3025 (not 8095 as service port), but transported via 3025 mapping
- `low ·verifiable` Documentation sync section references workflows that may have moved or been renamed (templates/skills/pr-docgen-sync*/)

### 🟢 B · 75/100 — `global: ~/.claude/GOVERNANCE_PRINCIPLES.md`
<sub>doctrine · cmd 0 · arch 17 · patterns 15 · concise 14 · currency 16 · action 13</sub>

[Doctrine, adapted rubric for policy/principles] Well-structured governance model with clear authority order and risk management; good internal navigability; moderate actionability with reliance on project-specific AGENTS.md which may not exist; no tool/command references to verify.

- `medium ·verifiable` Heavy reliance on project-level AGENTS.md without guidance on what to do if it doesn't exist
- `low` Authority order (line 114-126) is prescriptive but lacks guidance on conflict resolution when authorities are ambiguous
- `low` PAL Workflow Rules (lines 135-171) duplicate material from MCP_PAL.md but reference it via CLAUDE.md @import

### 🟢 B · 77/100 — `repo: src/.claude/claude.md`
<sub>module-memory · cmd 12 · arch 16 · patterns 13 · concise 14 · currency 10 · action 12</sub>

Good architectural overview but incomplete commands list, missing recent files, and stale MCP reference.

- `high ·verifiable` Commands section lists 12 files but actual commands directory contains 21 .py files
- `medium ·verifiable` Missing command files in documented list
- `medium` Reference to MCP tool that may not be available
- `low ·verifiable` Test command in documentation doesn't match Makefile patterns

### 🟢 B · 78/100 — `repo: docs/03-reference/instructions/claude.md`
<sub>template · cmd 12 · arch 14 · patterns 10 · concise 16 · currency 15 · action 11</sub>

Generic TDD/template-based guidance with TaskX/ChatX directives and strong conciseness, but @import references are all dead links and actionability is hindered by missing contract files.

- `high ·verifiable` @import references (lines 1-7) point to files that do not exist in the downloads_audit/ directory or any subdirectory. These are contract files referenced as mandatory inputs but are missing.
- `medium` TaskX and ChatX directive packs (lines 22-86) are generic boilerplate with no project-specific customization. They refer to 'task packets' and 'Case Bundle audit mode' but lack context for Dopemux-specific workflow.
- `medium ·verifiable` Documentation Sync Skill Family (lines 88-109) references paths that exist but command references are incomplete: scripts referenced without full verification
- `medium ·verifiable` Line 32 references 'claude --permission-mode plan' and 'claude --continue' but no verification that Claude Code harness supports these exact flags in the project setup
- `low ·verifiable` Line 38 mentions '.claude/settings.json (shared) and .claude/settings.local.json (personal, git-ignored)' but only settings.json is verifiable in this repo; settings.local.json is a git-ignore pattern, not a file to reference as 'provided'

### 🟢 B · 78/100 — `global: ~/.claude/MODE_Brainstorming.md`
<sub>doctrine · cmd 14 · arch 13 · patterns 12 · concise 14 · currency 13 · action 12</sub>

Self-contained behavioral mode guide for requirements discovery; actionable but claims persistence capability mapped to Serena MCP which lacks documented memory tools, and flags are verified in FLAGS.md but activation mechanism is implicit.

- `medium ·verifiable` Cross-Session Persistence claim attribute to Serena MCP missing documented mechanism
- `low ·verifiable` Activation mechanism relies on implicit keyword detection, not documented as harness capability
- `low` Architecture is functional but lacks Table of Contents for consistency

### 🟢 B · 80/100 — `global: ~/.claude/FLAGS.md`
<sub>doctrine · cmd 14 · arch 16 · patterns 13 · concise 13 · currency 12 · action 12</sub>

[Doctrine, adapted rubric] Well-organized flag reference with clear decision trees; good structure; gaps: several tools mentioned lack documentation files; some flags may be aliases for unverified MCPs.

- `medium ·verifiable` References tool flags (--seq, --magic, --morph, --play) without corresponding MCP documentation files
- `medium` No guidance on what happens when a flagged MCP isn't available in the current session
- `low` Flag Priority Rules (lines 136-142) are correct but don't reference the reality-check at MODES_AND_TOOLS.md line 78-80

### 🟢 B · 81/100 — `repo: services/.claude/claude.md`
<sub>module-memory · cmd 14 · arch 15 · patterns 12 · concise 13 · currency 14 · action 13</sub>

Well-structured service context with mostly accurate paths, but service location mismatch and missing context.

- `high ·verifiable` Service location discrepancy for conport
- `medium ·verifiable` Existing service list shows 'orchestrator' in services but actual location uncertain
- `low ·verifiable` Registry link uses outdated absolute path format

### 🟢 B · 82/100 — `repo: reports/downloads_audit/CLAUDE.md`
<sub>template · cmd 13 · arch 15 · patterns 11 · concise 17 · currency 14 · action 12</sub>

Minimal TDD checklist with good conciseness but identical to docs/03-reference/instructions/claude.md (dead @import links, missing contract files, generic boilerplate). Appears to be a copy with no differentiation for downloads_audit context.

- `high ·verifiable` @import references (lines 1-7) identical to docs/03-reference/instructions/claude.md, all point to files that do not exist. No context for 'downloads_audit' directory means these are even more orphaned here.
- `high ·verifiable` This file is identical copy-paste of docs/03-reference/instructions/claude.md (same line count, same content, same dead @imports). No value-add for downloads_audit use case, duplication suggests incomplete cleanup.
- `medium` Location in /reports/downloads_audit/ suggests this is an audit artifact, but file content is generic TDD checklist, not audit methodology or findings guidance
- `medium ·verifiable` CLAUDE-2.md exists in same directory (sibling file) but is not referenced. Unclear if this is a version history, backup, or active file—creates confusion about which to follow

### 🟢 B · 82/100 — `global: ~/.claude/MCP_GPTResearcher.md`
<sub>doctrine · cmd 15 · arch 17 · patterns 13 · concise 12 · currency 13 · action 12</sub>

Comprehensive research engine documentation with slash commands and workflow patterns; critical issue: slash command source files do not exist at documented paths; version pinning is actionable but unverified.

- `high ·verifiable` Slash command source files referenced but do not exist: `.claude/commands/research-quick.md`, `research-deep.md`, `research-report.md` (line 17)
- `medium ·verifiable` User guide path `docs/02-how-to/use-gpt-researcher.md` (line 15) exists, but doc is in dopemux-mvp repo context; path is relative and context-dependent
- `low` Version pinning `gpt-researcher==0.14.8` (line 283) claims 'verified latest stable on PyPI 2026-05-06' but no validation method provided
- `low` Container name `dopemux-mcp-gptr-mcp` (line 284) hardcoded; if Docker Compose changes the naming scheme, this becomes stale

### 🟢 B · 82/100 — `global: ~/.claude/MCP_DesktopCommander.md`
<sub>doctrine · cmd 14 · arch 16 · patterns 13 · concise 12 · currency 15 · action 12</sub>

Well-designed ADHD-focused desktop automation guide with workflow examples; **CRITICAL CROSS-FILE ISSUE**: This file is NOT imported into global CLAUDE.md (line 216 mentions desktop-commander as 'manual MCP' but doesn't @import the doc), making it an orphan from the main framework.

- `high ·verifiable` File is orphaned from global CLAUDE.md: mentioned at line 216 as 'desktop-commander' but not @imported like other MCP files (PAL, ConPort, Serena, etc.)
- `medium` Tool examples use `mcp__conport__` prefix (lines 32, 68, etc.) but ConPort.md doc uses `conport/` shorthand — inconsistency in namespace naming conventions
- `medium` System requirements (lines 313-322) reference xdotool, wmctrl, scrot, imagemagick but Docker compose config suggests containerized deployment; unclear if host or container must have these tools
- `low` Port 3012 claimed for Desktop-Commander (line 6) but no docker-compose.yml reference provided to verify this is correct

### 🟢 B · 83/100 — `repo: docker/mcp-servers-source/pal/pal-mcp-server/CLAUDE.md`
<sub>nested-tool · cmd 18 · arch 14 · patterns 12 · concise 13 · currency 12 · action 14</sub>

Solid, comprehensive dev guide for PAL/Zen server with stale naming and missing log dir, but all core commands exist and are copy-paste ready.

- `high ·verifiable` Title and throughout doc refers to 'Zen MCP Server' but directory and configuration use 'pal' — appears to be stale post-rename documentation
- `high ·verifiable` Virtual environment path mismatch: doc references '.zen_venv' but this path does not exist; actual path should be checked in run-server.sh
- `medium ·verifiable` Referenced logs directory does not exist
- `medium ·verifiable` Inconsistent venv reference: script uses '.zen_venv' variable but first line says 'venv'
- `low` Missing MCP context inheritance statement at top

### 🟢 B · 84/100 — `global: ~/.claude/MODE_Introspection.md`
<sub>doctrine · cmd 15 · arch 14 · patterns 13 · concise 14 · currency 14 · action 14</sub>

Self-contained meta-cognitive mode with emoji markers and pattern-detection framing; minimal external tool deps; high actionability; no stale refs detected. Cleanest of the four MODE files.

- `low ·verifiable` SuperClaude framework reference is aspirational but no activation wiring documented
- `low ·verifiable` Emoji markers (🤔, 🎯, ⚡, 📊, 💡) are claimed but their output impact is unverified

### 🟢 B · 85/100 — `global: ~/.claude/MCP_ConPort.md`
<sub>doctrine · cmd 14 · arch 17 · patterns 13 · concise 12 · currency 16 · action 13</sub>

Solid knowledge graph documentation with clear capability breakdown; tool naming uses `conport/` prefix not `mcp__conport__`, creating inconsistency with other MCP docs; workspace_id requirement is actionable.

- `medium ·verifiable` Tool naming inconsistency: docs use `conport/log_decision` format (line 71) but DesktopCommander.md examples use `mcp__conport__log_decision` prefix (e.g., line 285)
- `low` Database size claim appears stale: 'Currently 113 decisions + 12 relationships' (line 245) is a frozen snapshot
- `low` Performance metrics cite specific ms values but lack verification date

### 🟢 B · 85/100 — `global: ~/.claude/MCP_Exa.md`
<sub>doctrine · cmd 16 · arch 15 · patterns 12 · concise 14 · currency 14 · action 14</sub>

Clear, concise guide to neural web search; well-positioned against GPT-Researcher; minimal issues — some tool parameters lack validation examples.

- `low ·verifiable` Tool parameter `include_domains` referenced in Best Practices (line 91) but not documented in the `exa/search` Parameters section (lines 32-37)
- `low` Reference to EXA_API_KEY requirement (line 121) but no guidance on key setup or fallback behavior if missing

### 🟢 B · 86/100 — `global: ~/.claude/RESEARCH_CONFIG.md`
<sub>Pointer/Lazy-Load Doctrine · cmd 16 · arch 14 · patterns 13 · concise 15 · currency 14 · action 14</sub>

Well-positioned pointer/delegation doc. Explicitly marked as lazy-loaded (lines 3-7), delegating detailed config to MCP_GPTResearcher.md and MODE_DeepResearch.md. Quick-reference depth profiles and source tiers are useful. Tool routing is accurate. Single risk: Tavily vs Exa availability not verified; archived prior config referenced but path unverified.

- `medium ·verifiable` Tavily is mentioned as a search engine option but no MCP_Tavily.md exists in /Users/hue/.claude/. MCP_Exa.md exists. Unclear if Tavily is loaded or is a fallback/legacy reference.
- `medium ·verifiable` This path was not found during file exploration. Backups exist at /Users/hue/.claude/backups/ but 2026-05 subdirectory does not contain RESEARCH_CONFIG.md.archived. Path may be wrong or archive incomplete.
- `low ·verifiable` The thresholds (line 28) are well-defined but are aspirational. No MCP provides real-time confidence scoring or gap detection during research. These are design goals for GPT-Researcher, not verified working metrics.
- `low ·verifiable` Line 9 says 'active rules only', but whether these rules are enforced by GPT-Researcher MCP is not verified. This file delegates to MCP_GPTResearcher.md, which is the source of truth. Sync risk if one is updated and not the other.

### 🟢 B · 87/100 — `repo: .claude/claude.md`
<sub>project-memory · cmd 14 · arch 17 · patterns 13 · concise 14 · currency 16 · action 13</sub>

Project memory file with strong architecture and currency, but critical dead link to AGENTS.md and some unverified automation claims weaken actionability.

- `high ·verifiable` AGENTS.md is referenced 5x as relative path ../AGENTS.md but file is at ./AGENTS.md relative to .claude/ (one level up works, but markdown renderer may resolve from file location vs directory, risking dead link)
- `medium ·verifiable` Path reference at line 24 mixes full notation [.claude/modules/shared/governance-principles.md] with relative link (modules/shared/governance-principles.md), creating cognitive friction despite path existing
- `medium` Claims about automation (background 30-second save loop, automatic timer enforcement, forced-pause pauses) are marked as 'planned/not observed' but phrasing may still mislead readers into expecting them
- `medium ·verifiable` SuperClaude version (v4.1.5) and specific numbers (25 commands, 7 modes, 16 agents) are stated but not verifiable from docstring or metadata in the file
- `low ·verifiable` Module paths at lines 138-141 list files under .claude/modules/ but do not all verify existence or cross-link consistently with the Detailed Information Locations section above them
- `low ·verifiable` Hook files listed at lines 122-124 (check_energy.sh, log_progress.sh, etc.) verified to exist but narrative mixes 6 Python/shell hook files with 4 additional orchestrator hooks; count ambiguity

### 🟢 B · 87/100 — `global: ~/.claude/RULES.md`
<sub>doctrine · cmd 17 · arch 18 · patterns 14 · concise 11 · currency 14 · action 13</sub>

[Doctrine, adapted rubric] Well-organized behavioral rules with clear priority system and good tool guidance; excellent decision trees; major actionability flaw: contradictory MCP tool mandate vs. conditional guidance; some tools lack documentation.

- `high ·verifiable` Contradiction between MCP tool preference guidance (line 185) and File Operations Checklist (line 259)
- `medium ·verifiable` References tools without documentation: Sequential, Magic, Morphllm, Playwright mentioned but lack MCP_*.md files
- `medium ·verifiable` Quick Reference decision trees use hard-coded tool names (e.g., 'mcp__serena-v2__read_file()') without verifying they're current
- `low` File Organization section (lines 209-223) is oriented toward project structure, not Claude Code doctrine
- `low` Redundancy with GOVERNANCE_PRINCIPLES.md in sections like 'Safety Rules' (line 225) and 'Git Workflow' (line 164)

### 🟢 B · 88/100 — `repo: tests/.claude/claude.md`
<sub>module-memory · cmd 18 · arch 14 · patterns 13 · concise 14 · currency 14 · action 15</sub>

Strong test documentation with accurate commands and clear patterns; minor gaps in fixtures description.

- `low ·verifiable` Fixtures list incomplete
- `low ·verifiable` Test structure shows 'e2e' directory but structure listing shows only: unit, integration, dopemux, orchestrator, fixtures, resources (missing e2e/)
- `low` Coverage targets not aligned with code standards

### 🟢 B · 88/100 — `global: ~/.claude/MCP_Serena.md`
<sub>doctrine · cmd 16 · arch 18 · patterns 14 · concise 13 · currency 14 · action 13</sub>

Strong documentation of LSP-based code intelligence with ADHD features and performance benchmarks; path reference to `services/serena/v2/auto_activator.py` is correct but documentation should clarify v2 directory existence.

- `medium ·verifiable` Auto-activator path references `services/serena/v2/auto_activator.py` which exists but the file actually lives at `services/serena/auto_activator.py` (not in v2 subdirectory)
- `low` Tool namespace prefix inconsistency: docs reference `mcp__serena-v2__*` tools but integration with other MCPs uses dash notation
- `low` Redis cache performance claims (1-2ms) labeled 'NEW' and 'ACTIVATED' but lack deployment confirmation date

### 🟢 B · 88/100 — `global: ~/.claude/MCP_DopeContext.md`
<sub>doctrine · cmd 17 · arch 18 · patterns 14 · concise 13 · currency 12 · action 14</sub>

Thorough documentation of semantic search with structure-aware chunking, autonomous indexing, and worktree support; critical issue: referenced test report file does not exist at documented path.

- `high ·verifiable` FINAL_TEST_REPORT.md referenced at line 578 does not exist; path claimed: `services/dope-context/FINAL_TEST_REPORT.md`
- `medium` Validation dates cite October 2025 (lines 268, 274, 577) but document status shows it was edited in early 2026; timestamps may be stale
- `low` Path references inconsistent: sometimes `services/dope-context/` (line 578) vs implicit project root references for collection naming (line 281)

### 🟢 B · 89/100 — `global: ~/.claude/CLAUDE.md`
<sub>doctrine · cmd 18 · arch 16 · patterns 14 · concise 12 · currency 15 · action 14</sub>

[Doctrine, adapted rubric] Global configuration is current and well-structured; clear MCP awareness; good conditional guidance for tool availability; minor verbosity in some sections.

- `medium` Redundant explanation of MCP tool availability across sections (lines 95-96, 195-203, etc.)
- `low ·verifiable` Link anchors in TOC may be stale: references like '#superclaudopec-laude-integration' appear misspelled (line 16)
- `low` No explicit command examples for most workflow patterns mentioned

### 🟢 B · 89/100 — `global: ~/.claude/MODES_AND_TOOLS.md`
<sub>doctrine · cmd 16 · arch 17 · patterns 12 · concise 14 · currency 16 · action 14</sub>

[Doctrine, adapted rubric for harness features] Clear reference for non-MCP harness tools (Plan mode, advisor, /loop, ToolSearch, Skill, hooks); well-organized; excellent reality-check footer; all referenced harness features are current.

- `low` Plan Mode section (lines 5-13) references 'Explore agents' and 'Plan agent' without clarifying they're skills/external, not built-in harness features
- `low` Section on TodoWrite vs TaskCreate (lines 71-76) assumes TaskCreate/TaskUpdate/TaskList are in deferred tools, but this is session-dependent

### 🟢 A · 90/100 — `global: ~/.claude/MODE_Token_Efficiency.md`
<sub>Behavioral Mode Doctrine · cmd 18 · arch 16 · patterns 14 · concise 14 · currency 15 · action 13</sub>

Strong doctrine on symbol-based communication and abbreviation systems for token efficiency. All symbol references are aspirational (self-consistent) rather than tool-backed. Architecture is clear, current, and actionable as a behavioral mode. Minor: lacks integration with actual token-counting tools or metrics.

- `low ·verifiable` No token-counting mechanism or A/B test data is provided to validate the claim. This is aspirational guidance rather than empirically verified.
- `low ·verifiable` No mechanism in the harness provides real-time context usage metrics to agents. An agent cannot programmatically detect context fill and auto-trigger this mode.
- `low` While the symbol table is internally consistent, readability depends on agent/user familiarity. Long-form backups (Standard vs Token Efficient examples at lines 67-75) should be mandatory in critical communications.

### 🟢 A · 96/100 — `global: ~/.claude/MCP_PAL.md`
<sub>doctrine · cmd 18 · arch 19 · patterns 14 · concise 14 · currency 17 · action 14</sub>

Comprehensive, well-structured PAL MCP guide with extensive tool coverage, model recommendations, and integration patterns; minor currency issue around tool availability disclaimers.

- `low` Tool availability disclaimer claims `mcp__pal__*` prefix but docs also reference `pal/` command format inconsistently
- `low` Model intelligence ratings (18, 17, 16, etc.) appear subjective without supporting links or benchmarks

## Proposed fixes

The audit produced **62 concrete proposed diffs** across these files. They were intentionally NOT applied (you chose *report, then decide*). On approval I can apply them in priority order:

1. **Tier 1 — trivial/safe** (the 5 quick wins + Zen→PAL renames + orphan `@import`s): low risk, high signal.
2. **Tier 2 — in-repo module drift** (`config/ scripts/ tools/ shared/ src/ docker/ tests/`): regenerate directory maps from the live filesystem.
3. **Tier 3 — doctrine reality-check** (`MODE_Orchestration/Task_Management/Business_Panel`, `BUSINESS_*`): add availability disclaimers, strip/mark phantom tools & fabricated flags.
4. **Tier 4 — ships-to-users template**: fix `init/.claude/claude.md`.

*Contract-sensitive note:* the global `~/.claude/*` files are user-wide doctrine and the `init/` template is a shipped artifact — both warrant a closer look before editing. The in-repo module files are low-risk.
