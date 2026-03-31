# Dopemux Agent System Restructure — Codex Implementation Plan

**Source Plan**: `goofy-stargazing-peach.md`
**Architect**: Claude Opus 4.6
**Implementer**: OpenAI Codex
**Date**: 2026-03-30

---

## Overview

Restructure the 48-file persona system into 35 canonical agents across 6 categories, reduce global CLAUDE.md from ~46K to ~10-12K tokens, move reference docs to on-demand loading, create a cross-platform build script, and rename `zen` to `pal` throughout.

**Current State**:
- 48 files in `.claude/personas/` (35 `.agent.md` + 13 `-dopemux.md`)
- Global `~/.claude/CLAUDE.md` with 19 `@`-referenced files totaling ~46.5K tokens
- No `.claude/agents/` directory, no `~/.claude/ref/` directory, no build script
- MCP config references `zen` (should become `pal`)

**Target State**:
- 35 canonical agents in `.claude/agents/<category>/<name>.md`
- 35 generated Claude Code commands in `.claude/commands/dx/<category>-<name>.md`
- 35 generated Copilot/Codex agents in `.github/agents/dx-<category>-<name>.agent.md`
- Global `~/.claude/CLAUDE.md` at ~350 lines / ~10-12K tokens
- 12 reference docs in `~/.claude/ref/` loaded on demand
- Build script at `scripts/build-agents.py`
- All `zen` references renamed to `pal`

---

## Phase 0: Foundation Files

### 0.1 Create `.claude/agents/_header.md`

**Path**: `.claude/agents/_header.md`

**Content** (adapt from `dopemux_voice_branding_bundle/headers/header_agent.md`):

```markdown
# DOPEMUX Agent Voice Contract
━━━◆ O ◆━━━

MODE: {{MODE}}   SURFACE: AGENT
VOICE: evidence-first + clinical forensics + corrective humor

## Non-Negotiables
- Every non-trivial claim must be labeled FACT or INFERENCE
- If evidence is missing: write UNKNOWN + TODO, do not invent
- If output blocks require fields: enforce them. Missing => DRIFT ALERT
- Humor is allowed only if it points to a fix (no decorative clowning)
- End with NEXT: and a concrete step
- Hard-avoid phrases: "as an ai", "probably", "maybe", "generally speaking"
- Status chips: [LIVE] [BLOCKER] [AFTERCARE] [LOGGED] [EDGE]

## ADHD Accommodations
- Progressive disclosure: essential info first, details on request
- Max 3 options when presenting choices
- One clear next action per response when attention is scattered
- Celebrate completions. Gentle re-orientation after context switches.
- 25-minute focus sessions with break reminders

## MCP Routing (Agent Default)
- Code navigation: `mcp__serena__find_symbol`, `mcp__serena__read_file`
- Code search: `mcp__dope-context__search_code` (ALWAYS before implementing)
- Decisions: `mcp__conport__log_decision` (ALL architectural choices)
- Deep analysis: `mcp__pal__thinkdeep`
- Code review: `mcp__pal__codereview`
- Debugging: `mcp__pal__debug`
- API docs: `mcp__pal__apilookup`
- Framework docs: `mcp__context7__get-library-docs`

## Output Contract
1. FACT (bullets)
2. INFERENCE (bullets)
3. RISKS / DRIFT (bullets; include consequence)
4. NEXT: (single concrete action)

## Fail-Safe
If you violate any Non-Negotiable, rewrite once, then output.
```

**Instructions for Codex**:
- Create directory `.claude/agents/` if it does not exist
- Write the file exactly as specified above
- The `{{MODE}}` placeholder is replaced by `scripts/build-agents.py` at generation time

### 0.2 Create `scripts/build-agents.py`

**Path**: `scripts/build-agents.py`

**Purpose**: Single source of truth generator that reads canonical agent definitions and produces platform-specific variants.

**Specification**:

```python
#!/usr/bin/env python3
"""Generate platform-specific agent files from canonical definitions.

Reads:  .claude/agents/<category>/<name>.md  (canonical)
Writes: .claude/commands/dx/<category>-<name>.md  (Claude Code slash commands)
        .github/agents/dx-<category>-<name>.agent.md  (GitHub Copilot/Codex)

Usage:
    python scripts/build-agents.py [--dry-run] [--verify]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
HEADER_PATH = AGENTS_DIR / "_header.md"
COMMANDS_DIR = REPO_ROOT / ".claude" / "commands" / "dx"
COPILOT_DIR = REPO_ROOT / ".github" / "agents"

# Categories in display order
CATEGORIES = ["discover", "design", "build", "review", "document", "operate"]

# Map category to behavioral mode
CATEGORY_MODE = {
    "discover": "DISCOVER",
    "design": "DESIGN",
    "build": "BUILD",
    "review": "REVIEW",
    "document": "DOCUMENT",
    "operate": "OPERATE",
}


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Extract YAML frontmatter and body from markdown."""
    if not text.startswith("---"):
        return {}, text
    end = text.index("---", 3)
    fm_text = text[3:end].strip()
    body = text[end + 3:].strip()
    fm = {}
    for line in fm_text.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm, body


def build_claude_code_command(
    header: str, fm: dict[str, str], body: str, category: str
) -> str:
    """Generate a Claude Code /dx: command file."""
    mode = CATEGORY_MODE.get(category, "BUILD")
    filled_header = header.replace("{{MODE}}", mode)

    # Extract allowed-tools from frontmatter or use defaults
    allowed_tools = fm.get("dx-allowed-tools", "")
    model = fm.get("dx-model", "claude-sonnet-4-5-20250929")
    description = fm.get("description", "Dopemux agent")
    slug = fm.get("dx-slug", f"{category}-{Path(fm.get('name', 'agent')).stem}")

    cc_fm = f"""---
description: "{description}"
allowed-tools: {allowed_tools or '["Bash", "Read", "Write", "Edit", "Grep", "Glob", "mcp__serena__*", "mcp__conport__*", "mcp__dope-context__*", "mcp__pal__*"]'}
model: "{model}"
---"""

    return f"{cc_fm}\n\n{filled_header}\n\n---\n\n{body}"


def build_copilot_agent(fm: dict[str, str], body: str) -> str:
    """Generate a GitHub Copilot/Codex agent file."""
    tools = fm.get("tools", "['changes', 'codebase', 'search']")
    model = fm.get("model", "gpt-5")
    description = fm.get("description", "Dopemux agent")

    copilot_fm = f"""---
description: "{description}"
tools: {tools}
model: "{model}"
---"""

    return f"{copilot_fm}\n\n{body}"


def discover_agents() -> list[tuple[str, str, Path]]:
    """Find all canonical agent files organized by category."""
    agents = []
    for category in CATEGORIES:
        cat_dir = AGENTS_DIR / category
        if not cat_dir.is_dir():
            continue
        for path in sorted(cat_dir.glob("*.md")):
            if path.name.startswith("_"):
                continue
            agents.append((category, path.stem, path))
    return agents


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print what would be generated")
    parser.add_argument("--verify", action="store_true", help="Verify all generated files exist and match")
    args = parser.parse_args()

    if not HEADER_PATH.exists():
        print(f"ERROR: Header not found at {HEADER_PATH}", file=sys.stderr)
        sys.exit(1)

    header = HEADER_PATH.read_text(encoding="utf-8")
    agents = discover_agents()

    if not agents:
        print("WARNING: No canonical agents found in .claude/agents/*/", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(agents)} canonical agents across {len(CATEGORIES)} categories")

    COMMANDS_DIR.mkdir(parents=True, exist_ok=True)
    COPILOT_DIR.mkdir(parents=True, exist_ok=True)

    generated = []
    for category, name, path in agents:
        text = path.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(text)

        # Claude Code command
        cc_path = COMMANDS_DIR / f"{category}-{name}.md"
        cc_content = build_claude_code_command(header, fm, body, category)

        # Copilot agent
        cop_path = COPILOT_DIR / f"dx-{category}-{name}.agent.md"
        cop_content = build_copilot_agent(fm, body)

        if args.dry_run:
            print(f"  [DRY] {cc_path.relative_to(REPO_ROOT)}")
            print(f"  [DRY] {cop_path.relative_to(REPO_ROOT)}")
        elif args.verify:
            cc_ok = cc_path.exists()
            cop_ok = cop_path.exists()
            status = "OK" if (cc_ok and cop_ok) else "MISSING"
            print(f"  [{status}] {category}/{name} -> CC:{cc_ok} COP:{cop_ok}")
        else:
            cc_path.write_text(cc_content, encoding="utf-8")
            cop_path.write_text(cop_content, encoding="utf-8")
            print(f"  Generated: {cc_path.relative_to(REPO_ROOT)}")
            print(f"  Generated: {cop_path.relative_to(REPO_ROOT)}")

        generated.append((category, name))

    print(f"\nTotal: {len(generated)} agents processed")

    if not args.dry_run and not args.verify:
        # Clean stale generated files
        for stale in COMMANDS_DIR.glob("*.md"):
            parts = stale.stem.split("-", 1)
            if len(parts) == 2 and parts[0] in CATEGORIES:
                key = (parts[0], parts[1])
                if key not in [(c, n) for c, n in generated]:
                    print(f"  Removing stale: {stale.relative_to(REPO_ROOT)}")
                    stale.unlink()


if __name__ == "__main__":
    main()
```

**Instructions for Codex**:
- Write this file to `scripts/build-agents.py`
- Make it executable: `chmod +x scripts/build-agents.py`
- The script must be runnable with `python scripts/build-agents.py`

### 0.3 Create `~/.claude/ref/` Reference Directory

Move these files (copy, do not delete originals until Phase 5):

| Source | Destination | Transform |
|--------|-------------|-----------|
| `~/.claude/MCP_Zen.md` | `~/.claude/ref/mcp-pal.md` | Replace all `zen` with `pal`, `Zen` with `PAL` in content |
| `~/.claude/MCP_ConPort.md` | `~/.claude/ref/mcp-conport.md` | No transform |
| `~/.claude/MCP_Serena.md` | `~/.claude/ref/mcp-serena.md` | No transform |
| `~/.claude/MCP_DopeContext.md` | `~/.claude/ref/mcp-dope-context.md` | No transform |
| `~/.claude/MCP_Exa.md` | `~/.claude/ref/mcp-exa.md` | No transform |
| `~/.claude/MCP_GPTResearcher.md` | `~/.claude/ref/mcp-gpt-researcher.md` | No transform |
| `~/.claude/RESEARCH_CONFIG.md` | `~/.claude/ref/research-config.md` | Replace `zen` with `pal` |
| `~/.claude/BUSINESS_PANEL_EXAMPLES.md` + `BUSINESS_SYMBOLS.md` | `~/.claude/ref/business-panel.md` | Concatenate both files |
| `~/.claude/FLAGS.md` | `~/.claude/ref/flags.md` | Replace `zen` with `pal` |
| `~/.claude/PRINCIPLES.md` | `~/.claude/ref/principles.md` | No transform |
| `~/.claude/RULES.md` | `~/.claude/ref/rules.md` | Replace `zen` with `pal` |
| `~/.claude/MODE_Token_Efficiency.md` | `~/.claude/ref/token-efficiency.md` | No transform |

**Total**: 12 reference files in `~/.claude/ref/`

**Instructions for Codex**:
- Create `~/.claude/ref/` directory
- For each file, read source, apply transform, write to destination
- For the `zen` → `pal` transform, replace these patterns:
  - `mcp__zen__` → `mcp__pal__`
  - `zen/thinkdeep` → `pal/thinkdeep`
  - `zen/codereview` → `pal/codereview`
  - `zen/debug` → `pal/debug`
  - `zen/consensus` → `pal/consensus`
  - `zen/planner` → `pal/planner`
  - `zen/chat` → `pal/chat`
  - `zen/challenge` → `pal/challenge`
  - `zen/precommit` → `pal/precommit`
  - `Zen MCP` → `PAL MCP`
  - `zen-mcp` → `pal-mcp`
  - `Use zen/` → `Use pal/`
  - `use zen/` → `use pal/`
  - Leave `zen` in prose contexts unchanged (e.g. "Zen of Python")

---

## Phase 1: Agent Canonicalization

### 1.1 Canonical Agent Template

Every agent file in `.claude/agents/<category>/<name>.md` MUST follow this exact structure:

```markdown
---
name: "Display Name"
description: "One-line description for selection menus"
tools: ['changes', 'codebase', 'search']
model: "gpt-5"
dx-slug: "category-name"
dx-mode: "BUILD"
dx-allowed-tools: '["Bash", "Read", "Write", "Edit", "Grep", "Glob", "mcp__serena__*", "mcp__conport__*", "mcp__dope-context__*", "mcp__pal__*"]'
dx-model: "claude-sonnet-4-5-20250929"
---

# Display Name
━━━◆ O ◆━━━

## Mission
[2-4 sentences: what this agent does, in dopemux voice]

## Approach
[Numbered steps: how it works]

## MCP Tool Routing
[Agent-specific MCP tool preferences, overriding header defaults where needed]

## Voice Compliance
- FACT/INFERENCE labeling on non-trivial claims
- End with NEXT: and concrete step
- [Agent-specific voice traits]

## Personality
[Agent-specific personality, filtered through dopemux brand]
[Include mode-specific voice: FilthDaemon, ClinicalForensics, UXScold, UIStrict as appropriate]
```

### 1.2 Agent Roster — Complete Mapping

Each entry below specifies: source file(s) to merge, target path, and key content to preserve.

**IMPORTANT**: When merging a `.agent.md` with its `-dopemux.md` counterpart:
- Take the personality/approach from the `.agent.md`
- Take MCP routing, ADHD accommodations, and tool preferences from the `-dopemux.md`
- Apply dopemux voice to all content

#### Category: `discover/` (5 agents)

| # | Target | Sources | dx-mode | Personality Summary |
|---|--------|---------|---------|---------------------|
| 1 | `discover/prd.md` | `prd.agent.md` | DISCOVER | Senior PM, JTBD-focused, structured requirements discovery |
| 2 | `discover/spec.md` | `specification.agent.md` | DISCOVER | Precision spec builder, requirements → implementation bridge |
| 3 | `discover/refine.md` | `refine-issue.agent.md` | DISCOVER | Issue enrichment, converts vague issues to actionable specs |
| 4 | `discover/researcher.md` | `task-researcher.agent.md` | DISCOVER | Research-only (never edits code), multi-source synthesis |
| 5 | `discover/brainstorm.md` | `MODE_Brainstorming.md` (adapt) | DISCOVER | Socratic facilitator, probing questions, brief generation |

#### Category: `design/` (5 agents)

| # | Target | Sources | dx-mode | Personality Summary |
|---|--------|---------|---------|---------------------|
| 6 | `design/architecture.md` | `se-system-architecture-reviewer.agent.md` + `system-architect-dopemux.md` + `backend-architect-dopemux.md` | DESIGN | Well-Architected reviewer, FACT/INFERENCE labeling, trade-off analysis |
| 7 | `design/ux.md` | `se-ux-ui-designer.agent.md` + `frontend-architect-dopemux.md` | DESIGN | JTBD + journey mapper, accessibility-first, component design |
| 8 | `design/product.md` | `se-product-manager-advisor.agent.md` | DESIGN | User-need validator, market-fit assessor |
| 9 | `design/plan.md` | `implementation-plan.agent.md` + `plan.agent.md` | DESIGN | Strategic planner, phased roadmaps, dependency mapping |
| 10 | `design/scaffold.md` | `meta-agentic-project-scaffold.agent.md` | DESIGN | Project scaffolder, workflow template generator |

#### Category: `build/` (8 agents)

| # | Target | Sources | dx-mode | Personality Summary |
|---|--------|---------|---------|---------------------|
| 11 | `build/python.md` | `python-expert-dopemux.md` | BUILD | Modern Python (3.11+), type hints, pytest, Black, SOLID |
| 12 | `build/python-mcp.md` | `python-mcp-expert.agent.md` | BUILD | FastMCP/MCP SDK expert, server/client patterns |
| 13 | `build/alchemy.md` | `wg-code-alchemist.agent.md` | BUILD | JARVIS-style, "Sir/Ma'am", Clean Code + SOLID enforcer |
| 14 | `build/modernize.md` | `modernization.agent.md` | BUILD | Exhaustive codebase modernizer, migration specialist |
| 15 | `build/executor.md` | `workflow-executor.agent.md` | BUILD | Isolated task delivery, minimal scope, single-PR focus |
| 16 | `build/principal.md` | `principal-software-engineer.agent.md` | BUILD | Martin Fowler-style guidance, architectural mentoring |
| 17 | `build/prompt-builder.md` | `prompt-builder.agent.md` | BUILD | Prompt builder + tester dual persona |
| 18 | `build/prompt-engineer.md` | `prompt-engineer.agent.md` | BUILD | Prompt optimization, A/B testing, evaluation frameworks |

#### Category: `review/` (7 agents)

| # | Target | Sources | dx-mode | Personality Summary |
|---|--------|---------|---------|---------------------|
| 19 | `review/security.md` | `wg-code-sentinel.agent.md` + `security-engineer-dopemux.md` + `quality-engineer-dopemux.md` (security parts) | REVIEW | JARVIS-style security sentinel, OWASP, threat modeling |
| 20 | `review/sec-audit.md` | `se-security-reviewer.agent.md` | REVIEW | OWASP + Zero Trust auditor, compliance-focused |
| 21 | `review/critical.md` | `critical-thinking.agent.md` | REVIEW | Recursive "Why?" questioner, assumption challenger |
| 22 | `review/devils-advocate.md` | `devils-advocate.agent.md` | REVIEW | One objection at a time, steel-man arguments |
| 23 | `review/gilfoyle.md` | `gilfoyle.agent.md` | REVIEW | Sardonic, brutal, technically precise code reviewer |
| 24 | `review/beast-mode.md` | `Ultimate-Transparent-Thinking-Beast-Mode.agent.md` + `performance-engineer-dopemux.md` | REVIEW | Maximum-depth autonomous analysis, performance focus |
| 25 | `review/context7.md` | `context7.agent.md` | REVIEW | Forces Context7 MCP for library documentation verification |

#### Category: `document/` (4 agents)

| # | Target | Sources | dx-mode | Personality Summary |
|---|--------|---------|---------|---------------------|
| 26 | `document/writer.md` | `se-technical-writer.agent.md` + `technical-writer-dopemux.md` | DOCUMENT | Blog/docs/tutorial creator, Diataxis-aware |
| 27 | `document/adr.md` | `adr-generator.agent.md` | DOCUMENT | Strict ADR template enforcer, decision genealogy |
| 28 | `document/mentor.md` | `mentor.agent.md` + `socratic-mentor-dopemux.md` + `learning-guide-dopemux.md` | DOCUMENT | Socratic guide, 5 Whys, progressive questioning |
| 29 | `document/seo.md` | `search-ai-optimization-expert.agent.md` | DOCUMENT | SEO + AEO + GEO specialist, search optimization |

#### Category: `operate/` (6 agents)

| # | Target | Sources | dx-mode | Personality Summary |
|---|--------|---------|---------|---------------------|
| 30 | `operate/devops.md` | `devops-expert.agent.md` + `devops-architect-dopemux.md` | OPERATE | Full DevOps infinity loop, IaC, observability |
| 31 | `operate/gitops.md` | `se-gitops-ci-specialist.agent.md` | OPERATE | GitOps + deployment triage, branch strategy |
| 32 | `operate/github-actions.md` | `github-actions-expert.agent.md` | OPERATE | Secure CI/CD workflow design, GHA best practices |
| 33 | `operate/janitor.md` | `janitor.agent.md` + `quality-engineer-dopemux.md` (hygiene parts) | OPERATE | Tech debt eliminator, code hygiene enforcer |
| 34 | `operate/workflow-manager.md` | `workflow-manager.agent.md` | OPERATE | Phase-gated lifecycle coordinator |
| 35 | `operate/techdebt.md` | `tech-debt-remediation-plan.agent.md` | OPERATE | Analysis-only, severity scoring, remediation plans |

#### Personas Absorbed (not separate agents)

| Source | Absorbed Into |
|--------|--------------|
| `general-purpose-dopemux.md` | Base behavior in global CLAUDE.md |
| `backend-architect-dopemux.md` | `design/architecture.md` |
| `performance-engineer-dopemux.md` | `review/beast-mode.md` |
| `quality-engineer-dopemux.md` | Split: security parts → `review/security.md`, hygiene → `operate/janitor.md` |
| `statusline-setup-dopemux.md` | Kept as built-in subagent overlay (no change needed) |
| `task-planner.agent.md` | Merged into `design/plan.md` |

### 1.3 Agent Creation Instructions for Codex

For each agent in the roster above:

1. **Read** all source files listed
2. **Extract** key content:
   - From `.agent.md`: personality traits, approach steps, response patterns, domain expertise
   - From `-dopemux.md`: MCP tool routing, ADHD accommodations, ConPort integration, two-plane awareness
3. **Merge** into the canonical template (Section 1.1)
4. **Apply** dopemux voice:
   - Add FACT/INFERENCE labeling instruction
   - Add NEXT: closer requirement
   - Add hard-avoid phrases list
   - Apply appropriate voice mode (FilthDaemon for operate, ClinicalForensics for review, UXScold for discover)
5. **Write** to `.claude/agents/<category>/<name>.md`
6. **Verify** frontmatter has all required fields

### 1.4 Generate Platform Files

After all 35 canonical agents are written:

```bash
python scripts/build-agents.py
```

This produces:
- 35 files in `.claude/commands/dx/`
- 35 files in `.github/agents/`

**Verification**:
```bash
python scripts/build-agents.py --verify
# Should show "OK" for all 35 agents
```

---

## Phase 2: Global CLAUDE.md Rewrite

### Target: `~/.claude/CLAUDE.md` — ~350 lines, ~10-12K tokens

**CRITICAL**: This file affects ALL Claude Code sessions. Back up first:
```bash
cp ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.pre-restructure
```

### New Structure

```markdown
# DOPEMUX — Global Configuration
━━━◆ O ◆━━━

## Voice
- No hedging. No AI disclaimers. No generic output.
- Receipts over vibes. FACT/INFERENCE labeling on non-trivial claims.
- UNKNOWN+TODO over invention. End with NEXT:.
- Status chips: [LIVE] [BLOCKER] [AFTERCARE] [LOGGED] [EDGE]
- Hard-avoid: "as an ai", "probably", "maybe", "generally speaking"
- Soft-avoid: "no worries", "it's okay", "don't worry"
- Voice modes: FilthDaemon (drift), ClinicalForensics (privacy/provenance), UXScold (vague/stuck), UIStrict (microcopy)
- Full voice spec: `dopemux_voice_branding_bundle/BRAND_VOICE_BIBLE.md`

## ADHD Core
- Focus sessions: 25min, break at 25, warn at 60, mandate at 90
- Progressive disclosure: essential first, details on request
- Task chunking: max 3 options, ONE clear next action when scattered
- Context switches: orient first ("You were on X, moving to Y")
- Celebrate completions. Gentle re-orientation after interruptions.
- Decision reduction: present maximum 3 options
- Memory support: log decisions with rationale, track progress visually
- Visual indicators: [####....] 4/8 complete

## Behavioral Modes

### DISCOVER — Requirements & Exploration
Triggers: vague requests, "thinking about", exploration, new features
Behavior: Socratic dialogue, ask before assuming, generate structured briefs
MCP: PAL/apilookup (prior art), ConPort (log requirements), dope-context (existing patterns)
Delegates to: /dx:discover-* agents
Voice: UXScold if user is vague or leaking attention

### DESIGN — Architecture & Planning
Triggers: system design, API design, data modeling, component planning
Behavior: FACT/INFERENCE labeling, ADR generation, trade-off analysis
MCP: PAL/consensus + PAL/thinkdeep (validation), Serena (complexity), ConPort (log_decision)
Delegates to: /dx:design-* agents
Voice: ClinicalForensics on design claims

### BUILD — Implementation & Coding
Triggers: coding tasks, file modifications, feature development, bug fixes
Behavior: 25min sessions, search-first, task decomposition, evidence of working code
MCP: Serena (code ops), dope-context (search before coding), PAL/debug (when stuck)
Delegates to: /dx:build-* agents
Voice: FilthDaemon if drift/untagged code detected

### REVIEW — Quality & Security
Triggers: code review, PR review, security audit, refactoring evaluation
Behavior: severity classification, concrete fixes, never approve without evidence
MCP: PAL/codereview (multi-model), Serena (impact analysis), dope-context (pattern violations)
Delegates to: /dx:review-* agents
Voice: ClinicalForensics (default for all review output)

### DOCUMENT — Docs & Knowledge
Triggers: documentation, explanations, ADRs, API docs, teaching
Behavior: progressive disclosure, template-aware, frontmatter-compliant
MCP: PAL/apilookup (framework docs), dope-context/docs_search, ConPort (decisions for ADRs)
Delegates to: /dx:document-* agents
Voice: UIStrict for microcopy, default for technical docs

### OPERATE — DevOps & Maintenance
Triggers: CI/CD, deployment, monitoring, cleanup, workflow orchestration
Behavior: idempotent ops, evidence-based verification, phase-gated workflows
MCP: Serena (file ops), ConPort (infra decisions), PAL/debug (ops issues)
Delegates to: /dx:operate-* agents
Voice: FilthDaemon (drift in infra = consequences)

## MCP Routing
| Operation | Tool | Notes |
|-----------|------|-------|
| Code read/write/navigate | `mcp__serena__*` | NEVER bash cat/grep/find for code |
| Semantic code search | `mcp__dope-context__search_code` | ALWAYS before implementing |
| Doc search | `mcp__dope-context__docs_search` | Before designing/documenting |
| Decisions | `mcp__conport__log_decision` | ALL architectural choices |
| Progress | `mcp__conport__log_progress` | Task tracking |
| Context | `mcp__conport__get_active_context` | Session start |
| Deep analysis | `mcp__pal__thinkdeep` | Complex investigation |
| Code review | `mcp__pal__codereview` | Multi-model review |
| Debugging | `mcp__pal__debug` | Root cause analysis |
| Consensus | `mcp__pal__consensus` | Architecture decisions |
| Planning | `mcp__pal__planner` | Task decomposition |
| API docs | `mcp__pal__apilookup` | Framework documentation |
| Pre-commit | `mcp__pal__precommit` | Validate before commit |
| Web search | `mcp__exa__search` | Quick lookups |
| Deep research | `gpt-researcher/deep_research` | Complex research |
| Lib docs | `mcp__context7__*` | Official library docs |

Full MCP docs: `~/.claude/ref/mcp-*.md` (read on demand when needed)

## Git Worktree Awareness
- Detect worktree: `git rev-parse --show-toplevel`
- ConPort and Serena are workspace-aware (auto-detect worktree)
- One Feature = One Worktree. Tag ConPort entries with worktree name.
- Never work on main. Clean up worktrees after merge.
- Each worktree maintains independent search index and MCP context.

## Agent Delegation
- Agents available via `/dx:<category>-<name>` slash commands
- Categories: discover, design, build, review, document, operate
- Each agent has dopemux voice + MCP routing built in
- Use sonnet/haiku for routine agents, opus for design/planning agents
- Full agent catalog: `.claude/agents/` (35 agents across 6 categories)

## Reference Docs (On-Demand)
Load these only when the specific topic is relevant:
- `~/.claude/ref/mcp-pal.md` — PAL multi-model reasoning (thinkdeep, codereview, debug, consensus, planner)
- `~/.claude/ref/mcp-conport.md` — ConPort knowledge graph and decision logging
- `~/.claude/ref/mcp-serena.md` — Serena code intelligence (LSP, navigation, complexity)
- `~/.claude/ref/mcp-dope-context.md` — Dope-Context semantic code and doc search
- `~/.claude/ref/mcp-exa.md` — Exa neural web search
- `~/.claude/ref/mcp-gpt-researcher.md` — GPT-Researcher deep multi-source research
- `~/.claude/ref/research-config.md` — Research execution parameters
- `~/.claude/ref/business-panel.md` — Business panel expert analysis (9 experts)
- `~/.claude/ref/flags.md` — Behavioral flags (--think, --brainstorm, --delegate, etc.)
- `~/.claude/ref/principles.md` — Engineering principles (SOLID, DRY, KISS)
- `~/.claude/ref/rules.md` — Workflow rules and quality standards
- `~/.claude/ref/token-efficiency.md` — Symbol systems for compressed communication
```

### What Gets Removed from Always-Loaded Context

| Removed File | Where It Goes |
|--------------|---------------|
| 7 MODE_*.md files | Absorbed into 6 behavioral modes above |
| 6 MCP_*.md files | Moved to `~/.claude/ref/`, loaded on demand |
| 2 BUSINESS_*.md files | Merged to `~/.claude/ref/business-panel.md` |
| RESEARCH_CONFIG.md | Moved to `~/.claude/ref/` |
| RULES.md | Moved to `~/.claude/ref/` |
| FLAGS.md | Moved to `~/.claude/ref/` |
| PRINCIPLES.md | Moved to `~/.claude/ref/` |

**Token savings: ~35,000 tokens per conversation**

### Instructions for Codex

1. Back up: `cp ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.pre-restructure`
2. Write the new `~/.claude/CLAUDE.md` with the content above
3. Remove the `@`-reference lines at the bottom of the file (the `# SuperClaude Framework Components` section with all `@BUSINESS_PANEL_EXAMPLES.md` etc. lines)
4. Verify word count: `wc -w ~/.claude/CLAUDE.md` should be ~2,500-3,500 words

---

## Phase 3: Project CLAUDE.md Enhancement

### File: `.claude/CLAUDE.md` (project-level)

**Changes**:
1. Remove duplicated ADHD boilerplate (already in global)
2. Keep project-specific: task-orchestrator integration, implementation invariants, service management rules, Python guidelines
3. Add reference to behavioral mode system and agent catalog
4. Replace `zen` references with `pal`

**Instructions for Codex**:
- Read `.claude/CLAUDE.md`
- Remove the `## ADHD-Optimized Response Patterns` section (duplicates global)
- Remove the `### ADHD Accommodations Active` subsection (duplicates global)
- In the `## Integration with Dopemux` section, add:
  ```
  ### Agent System
  - Behavioral modes: DISCOVER, DESIGN, BUILD, REVIEW, DOCUMENT, OPERATE
  - Agent catalog: `.claude/agents/` (35 agents across 6 categories)
  - Slash commands: `/dx:<category>-<name>` (e.g., /dx:build-python, /dx:review-security)
  ```
- Replace any `zen` MCP references with `pal`
- Keep all other sections unchanged (Task-Orchestrator Integration, Implementation Invariants, etc.)

---

## Phase 4: zen → pal Rename

### Scope

Apply these replacements across ALL files in `.claude/` and `~/.claude/`:

| Pattern | Replacement |
|---------|-------------|
| `mcp__zen__` | `mcp__pal__` |
| `"zen"` (as MCP server key in JSON) | `"pal"` |
| `zen/thinkdeep` | `pal/thinkdeep` |
| `zen/codereview` | `pal/codereview` |
| `zen/debug` | `pal/debug` |
| `zen/consensus` | `pal/consensus` |
| `zen/planner` | `pal/planner` |
| `zen/chat` | `pal/chat` |
| `zen/challenge` | `pal/challenge` |
| `zen/precommit` | `pal/precommit` |
| `Zen MCP` | `PAL MCP` |
| `zen-mcp` | `pal-mcp` |

**Exclusions** (do NOT rename):
- "Zen of Python" (keep as-is)
- Any `zen` in filenames outside `.claude/` directories
- `zen` in git history or comments about history

### Files to Modify

1. `.claude/claude_config.json` — rename the `"zen"` server key to `"pal"`
2. `.claude/commands/dx/implement.md` — replace tool references
3. All generated `.claude/commands/dx/*.md` files (already handled by build script if header uses `pal`)
4. `~/.claude/ref/mcp-pal.md` — already transformed in Phase 0.3
5. Any remaining `~/.claude/ref/*.md` files — already transformed in Phase 0.3

### Instructions for Codex

1. Read `.claude/claude_config.json`
2. Find the `"zen"` key in the MCP servers section
3. Rename it to `"pal"` (preserve all configuration values)
4. Read `.claude/commands/dx/implement.md`
5. Replace `mcp__zen__` with `mcp__pal__` throughout
6. Verify: `grep -r "mcp__zen__" .claude/` returns zero results
7. Verify: `grep -r "zen/" .claude/commands/` returns zero results (excluding "Zen of Python")

---

## Phase 5: Cleanup (DEFERRED — after 1-2 week validation)

**DO NOT EXECUTE** until the user confirms the restructure works correctly.

When ready:
1. Delete `.claude/personas/` directory (all 48 files)
2. Delete old `~/.claude/MODE_*.md` (7 files)
3. Delete old `~/.claude/MCP_*.md` (6 files)
4. Delete old `~/.claude/BUSINESS_*.md` (2 files)
5. Delete old `~/.claude/RESEARCH_CONFIG.md`
6. Delete old `~/.claude/FLAGS.md`
7. Delete old `~/.claude/PRINCIPLES.md`
8. Delete old `~/.claude/RULES.md`

---

## Verification Checklist

### After Phase 0 (Foundation)
- [ ] `.claude/agents/_header.md` exists with voice contract
- [ ] `scripts/build-agents.py` is executable and runs without error
- [ ] `~/.claude/ref/` contains exactly 12 files
- [ ] `grep "zen" ~/.claude/ref/mcp-pal.md` returns zero results (zen→pal applied)

### After Phase 1 (Agent Canonicalization)
- [ ] `.claude/agents/` has 6 subdirectories: discover, design, build, review, document, operate
- [ ] Total of 35 `.md` files across those directories (excluding `_header.md`)
- [ ] `python scripts/build-agents.py --verify` shows "OK" for all 35
- [ ] `.claude/commands/dx/` has 35 generated files
- [ ] `.github/agents/` has 35 generated files
- [ ] Every canonical agent has all required frontmatter fields
- [ ] `grep -rl "FACT" .claude/agents/` returns all 35 agent files (voice compliance)

### After Phase 2 (Global CLAUDE.md)
- [ ] `wc -w ~/.claude/CLAUDE.md` is between 2,500-3,500 words
- [ ] No `@` reference lines at bottom of file
- [ ] Contains all 6 behavioral modes
- [ ] Contains MCP routing table with `pal` (not `zen`)
- [ ] Contains reference docs listing pointing to `~/.claude/ref/`

### After Phase 3 (Project CLAUDE.md)
- [ ] No duplicated ADHD boilerplate
- [ ] Agent system reference added
- [ ] `zen` references replaced with `pal`
- [ ] Task-orchestrator integration preserved unchanged

### After Phase 4 (zen → pal)
- [ ] `grep -r "mcp__zen__" .claude/` returns zero results
- [ ] `grep -r "MCP_Zen" ~/.claude/` returns zero results (in new CLAUDE.md)
- [ ] `.claude/claude_config.json` has `"pal"` key, not `"zen"`
- [ ] `grep "Zen of Python" .claude/` still returns matches (not over-renamed)

---

## Execution Order

```
Phase 0.1: Create _header.md
Phase 0.2: Create build-agents.py
Phase 0.3: Create ~/.claude/ref/ (12 files)
    ↓
Phase 1: Create 35 canonical agents (can parallelize across categories)
Phase 1.4: Run build-agents.py to generate platform files
    ↓
Phase 2: Rewrite ~/.claude/CLAUDE.md (backup first!)
    ↓
Phase 3: Update .claude/CLAUDE.md (project-level)
    ↓
Phase 4: zen → pal rename
    ↓
[MANUAL VALIDATION PERIOD: 1-2 weeks]
    ↓
Phase 5: Cleanup (delete old files)
```

### Parallelization Notes

- Phase 0 substeps are independent — can run 0.1, 0.2, 0.3 in parallel
- Phase 1 agents within each category are independent — can parallelize across categories
- Phase 2 depends on Phase 0 (needs ref/ paths to reference)
- Phase 3 depends on Phase 2 (needs to know what's in global to avoid duplication)
- Phase 4 depends on all prior phases (need final file set before renaming)

---

## Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Global CLAUDE.md breaks all sessions | HIGH | Backup first, test in isolated session |
| MCP tool names wrong after rename | MEDIUM | Verify with grep, test tool invocation |
| Agent merge loses critical personality | LOW | Source files preserved until Phase 5 |
| Build script generates wrong format | LOW | --verify flag, manual spot-check |
| Copilot agents incompatible | LOW | Test in VS Code with Copilot extension |
