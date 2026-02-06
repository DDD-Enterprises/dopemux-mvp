---
id: DOPEMUX_UX_RESEARCH_REQUEST
title: Dopemux_Ux_Research_Request
type: explanation
owner: '@hu3mann'
last_review: '2025-11-10'
next_review: '2026-02-08'
---
# Dopemux UX Enhancement - Comprehensive Research & Design Request

**Date:** 2025-10-30
**Status:** Research Request for Zen Multi-Model Analysis
**Project:** Dopemux UX + HYPERFOCUS REVIVAL Integration
**Output:** Design document ready for Claude Code implementation

---

## Context

We're building **4 interconnected UX enhancements** for Dopemux:

1. **HYPERFOCUS REVIVAL TUI** - Interactive dashboard for untracked work management
2. **Enhanced Status Display** - Better role/persona visualization
3. **Research Mode Launcher** - Quick access to deep research capabilities
4. **Unified UX Framework** - Consistent ADHD-optimized patterns across all features

**Technology Stack:**
- **Textual** (6.3.0) - Terminal UI framework (already installed)
- **MCP SDK** (1.12.4) - Model Context Protocol integration (already installed)
- **Rich** - Already in use for CLI output
- **Click** - CLI framework (already in use)

**Current State:**
- ✅ 9 MCP servers running (ConPort, Zen, Serena, PAL apilookup, etc.)
- ✅ Role/persona switching working (`dopemux start --role <role>`)
- ✅ Status dashboard exists (basic tables)
- ✅ HYPERFOCUS REVIVAL spec complete (F001-ENHANCED)

---

## Research Request for Zen

Please use Zen's multi-model analysis to research, design, and plan the following:

### 1. HYPERFOCUS REVIVAL TUI Research

**Research Questions:**
- What are best practices for TUI design with Textual?
- How to design ADHD-friendly terminal interfaces?
- What interaction patterns work for task management TUIs?
- How to visualize "50 false starts" without causing shame?
- What's the optimal information density for ADHD users?
- How to make revival suggestions feel empowering, not overwhelming?

**Design Requirements:**
- Dashboard showing untracked work statistics
- Interactive list of abandoned projects (sortable, filterable)
- Quick actions: Track, Revive, Archive, Design-First
- Real-time git/filesystem monitoring display
- Cognitive load indicator
- Energy-aware UI (adapts to ADHD state)

**Technical Questions:**
- How to integrate Textual with existing Click CLI?
- How to connect TUI to ConPort MCP for data?
- Real-time updates vs polling strategy?
- How to handle TUI + tmux layouts gracefully?
- Performance considerations for file watching?

**Output Needed:**
- TUI wireframe/layout design
- Component architecture
- Data flow diagram (git → detector → ConPort → TUI)
- Key/command shortcuts design
- ADHD optimization recommendations

---

### 2. Enhanced Status Display Research

**Research Questions:**
- How to visualize current role/persona in statusline?
- What metrics matter most for ADHD developers?
- How to show MCP server health compactly?
- Best practices for real-time dashboard updates?
- Color schemes for neurodivergent users?

**Design Requirements:**
- Current role/persona prominently displayed
- Active MCP servers with health indicators
- Attention state visualization (from ADHD Engine)
- Energy level display
- Session duration with break recommendations
- Token usage (Claude context window)
- Git branch + untracked work indicator

**Technical Questions:**
- Update frequency (avoid flicker)?
- Integration with existing statusline.sh?
- How to make it tmux-aware?
- Async data fetching strategy?

**Output Needed:**
- Enhanced status layout design
- Update mechanism architecture
- Integration points with existing code
- ADHD-optimized color/symbol scheme

---

### 3. Research Mode Launcher Design

**Research Questions:**
- How to make research mode discoverable?
- What setup is needed before research starts?
- How to capture research output automatically?
- Best UX for selecting research tools (GPT-R, Exa, Zen)?
- How to make research prompts reusable?

**Design Requirements:**
- Quick launcher: `dopemux research <topic>`
- Interactive mode: guided research session
- Auto-save research to ConPort
- Template library for common research patterns
- Integration with HYPERFOCUS REVIVAL research
- Support for multi-step research workflows

**Technical Questions:**
- How to pre-configure GPT-Researcher?
- Exa API integration patterns?
- How to orchestrate Zen + GPT-R + Exa together?
- Output formatting (markdown with citations)?
- How to resume interrupted research sessions?

**Output Needed:**
- Research launcher UX flow
- Command structure design
- Research session state management
- Template system architecture

---

### 4. Unified UX Framework Research

**Research Questions:**
- How to create consistent ADHD-optimized patterns?
- What are universal accessibility needs for neurodivergent users?
- How to balance information richness with cognitive load?
- Best practices for progressive disclosure in CLIs?
- How to make complex tools feel simple?

**Design Requirements:**
- Consistent color scheme (ADHD-friendly)
- Standard layouts across all features
- Shared components (tables, panels, forms)
- Unified keyboard shortcuts
- Help system that doesn't overwhelm
- Gentle nudging patterns (not annoying)

**Technical Questions:**
- How to create reusable Textual components?
- Shared state management across TUIs?
- How to maintain UX consistency in CLI vs TUI?
- Testing strategy for interactive UIs?

**Output Needed:**
- UX design system specification
- Component library design
- Style guide (colors, typography, spacing)
- Interaction pattern catalog
- ADHD accommodation guidelines

---

## Cross-Cutting Concerns

### ADHD Optimization Principles

Research and apply these principles to ALL UX designs:

1. **Progressive Disclosure** - Show essentials first, details on demand
2. **Gentle Nudging** - Helpful reminders, not nagging
3. **Quick Wins Visible** - Celebrate small completions
4. **Interruption Recovery** - Easy to resume after context switches
5. **Cognitive Load Awareness** - Adapt complexity to user state
6. **Visual Hierarchy** - Clear priorities, scannable layouts
7. **Shame-Free Messaging** - Encouraging, not judgmental
8. **Autonomy Respect** - Easy to disable/customize features

### Integration Architecture

Design how these 4 features work together:

```
┌─────────────────────────────────────────────────┐
│  Dopemux CLI (Click + Rich)                     │
│  ├─ start --role <role>                         │
│  ├─ status (enhanced display)                   │
│  ├─ research <topic> (launcher)                 │
│  └─ hyperfocus (TUI)                            │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  Unified UX Framework                           │
│  ├─ Textual Components                          │
│  ├─ ADHD Patterns Library                       │
│  ├─ State Management                            │
│  └─ MCP Integration Layer                       │
└─────────────────┬───────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────┐
│  MCP Services                                    │
│  ├─ ConPort (data storage)                      │
│  ├─ Zen (analysis)                              │
│  ├─ GPT-Researcher (web search)                 │
│  ├─ Exa (semantic search)                       │
│  ├─ Serena (code navigation)                    │
│  └─ ADHD Engine (attention monitoring)          │
└─────────────────────────────────────────────────┘
```

---

## Deliverable Structure

Please create a comprehensive document with:

### 1. Executive Summary (2 pages)
- **TL;DR Box** - 5 key takeaways
- Vision for unified Dopemux UX
- Research synthesis highlights
- Go/no-go for each of 4 features
- Implementation priority order

### 2. Research Findings (10-15 pages)

**For Each Feature (HYPERFOCUS TUI, Status, Research, Framework):**
- Research summary (what we learned)
- Best practices discovered
- Design patterns that work
- Anti-patterns to avoid
- ADHD-specific considerations
- Technical feasibility assessment

### 3. Design Specifications (15-20 pages)

**For Each Feature:**
- User flows (step-by-step scenarios)
- Wireframes (ASCII art is fine!)
- Component breakdown
- Data models
- API contracts (MCP integration)
- Keyboard shortcuts
- Error handling
- ADHD accommodations built-in

### 4. Technical Architecture (10-15 pages)

**System Design:**
- Overall architecture diagram
- Component relationships
- Data flow diagrams
- State management strategy
- MCP integration patterns
- File structure (where code lives)
- Dependencies needed
- Testing strategy

**For Each Feature:**
- Implementation approach
- Key classes/modules
- Integration points
- Performance considerations
- Security/privacy safeguards

### 5. Implementation Plan (5-10 pages)

**Phase Breakdown:**
- Phase 1: Foundation (UX framework + components)
- Phase 2: Enhanced Status Display (quickest win)
- Phase 3: Research Mode Launcher (high value)
- Phase 4: HYPERFOCUS REVIVAL TUI (flagship feature)

**For Each Phase:**
- Time estimate (realistic for ADHD developer)
- Deliverables
- Success metrics
- Dependencies
- Testing approach
- Rollout strategy

### 6. UX Design System (5-8 pages)

- Color palette (ADHD-optimized)
- Typography scale
- Spacing system
- Component library catalog
- Interaction patterns
- Animation guidelines (minimal, purposeful)
- Accessibility checklist
- ADHD accommodation patterns

### 7. Developer Guide (3-5 pages)

- How to add new TUI screens
- How to integrate with MCP servers
- How to follow UX patterns
- Testing interactive UIs
- Debugging TUI issues
- Common pitfalls

### 8. User Guide (3-5 pages)

- How to use HYPERFOCUS REVIVAL TUI
- How to use research mode
- How to customize UX
- Keyboard shortcuts reference
- Troubleshooting

### 9. Success Metrics (2-3 pages)

**Quantitative:**
- Task completion rates
- Time to complete common workflows
- Error rates
- Feature adoption rates

**Qualitative:**
- User satisfaction (ADHD developers)
- Perceived cognitive load
- Shame-free experience validation
- Empowerment vs overwhelm

### 10. Open Questions & Risks (2-3 pages)

- Technical unknowns
- UX assumptions to validate
- Potential user experience issues
- Performance risks
- Scope creep concerns
- Mitigation strategies

---

## Research Methodology

**Use Zen to orchestrate:**

1. **Multi-Model Consensus** on design decisions
2. **Web Search** for Textual best practices, ADHD UX research
3. **Code Analysis** of existing Dopemux CLI patterns
4. **Synthesis** across all 4 features for consistency

**Models to Leverage:**
- GPT-5 (architecture design)
- Claude Sonnet 4.5 (UX patterns, ADHD research)
- o1-mini (technical planning)
- Gemini 2.0 (visual design suggestions)

---

## Output Format

**Markdown Document:**
- Ready to paste into Claude Code
- Clear headings, scannable
- Code examples where relevant
- ASCII diagrams for architecture
- TL;DR boxes in each section
- Checklist format for implementation steps

**File Name:** `DOPEMUX_UX_COMPREHENSIVE_DESIGN.md`

**Location:** `docs/development/planning/`

---

## Success Criteria

This design document should:

1. ✅ Provide complete specs for all 4 features
2. ✅ Be implementable by single developer (ADHD-aware pacing)
3. ✅ Include ADHD optimization in every design decision
4. ✅ Show how features integrate cohesively
5. ✅ Provide clear next steps for implementation
6. ✅ Be comprehensive yet scannable (ADHD-friendly)
7. ✅ Include realistic timelines and milestones
8. ✅ Validate against ADHD research evidence

---

## Special Focus: HYPERFOCUS REVIVAL Integration

Since HYPERFOCUS REVIVAL is the flagship feature, ensure deep integration:

- TUI is the primary interface for revival system
- Detection engine runs in background, surfaces in TUI
- ConPort integration for all data storage
- Zen analysis for revival scoring
- Dashboard shows aggregate stats beautifully
- Interactive actions: Track, Revive, Design-First, Archive

**Reference Documents:**
- `docs/03-reference/F001-ENHANCED-untracked-work-system.md`
- `docs/development/research/HYPERFOCUS_REVIVAL_RESEARCH_REQUEST.md`

---

## Zen Research Prompt

Please analyze this entire request and:

1. **Research** all topics using web search + code analysis
2. **Design** all 4 features with UX best practices
3. **Plan** implementation with realistic timelines
4. **Synthesize** into comprehensive design document
5. **Validate** against ADHD research and accessibility standards

**Use your multi-model capabilities to ensure:**
- Technical feasibility (GPT-5, o1)
- UX excellence (Claude, Gemini)
- ADHD optimization (Claude + research)
- Architectural soundness (GPT-5, o1)

---

## Timeline

**Research + Design + Planning:** 1-2 hours (Zen autonomous work)
**Document Generation:** 30-45 minutes
**Total:** ~2-3 hours

---

**Goal:** Create the definitive UX design specification for Dopemux enhancements, grounded in research, optimized for ADHD, and ready for immediate implementation in Claude Code.

---

**Document Status:** Research Request - Ready for Zen Execution
**Priority:** Critical - Foundation for next development phase
**Expected Output:** ~50-60 page comprehensive design document
