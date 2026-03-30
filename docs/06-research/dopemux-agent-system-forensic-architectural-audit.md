---
id: dopemux-agent-system-forensic-architectural-audit
title: Dopemux Agent System Forensic Architectural Audit
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-29'
last_review: '2026-03-29'
next_review: '2026-06-29'
prelude: Forensic and architectural audit of the Dopemux agent system, its persona roster,
  routing overlap, and consolidation opportunities.
---

# Dopemux Agent System: Forensic & Architectural Audit Report

  Date: 2026-03-29
  Model: Opus 4.6
  Scope: Full roster, routing, boundary, token, and usability audit
  Evidence base: 47 persona files, 7 infrastructure agents, 7 modes, 21 built-in subagent types, ~186KB always-loaded
  global config

  ---
  Phase 1 — Roster Stress Test

  Current Landscape (FACT)

  The system contains three distinct agent/persona layers:

  ┌─────────────────────────────┬───────┬───────────────────────────────┬─────────────────────────────────────────┐
  │            Layer            │ Count │           Location            │                 Status                  │
  ├─────────────────────────────┼───────┼───────────────────────────────┼─────────────────────────────────────────┤
  │ Dopemux-enhanced personas   │ 13    │ .claude/personas/*-dopemux.md │ Active, mapped to Claude Code subagent  │
  │                             │       │                               │ types                                   │
  ├─────────────────────────────┼───────┼───────────────────────────────┼─────────────────────────────────────────┤
  │ SuperClaude .agent.md       │ 34    │ .claude/personas/*.agent.md   │ Active, NOT mapped to built-in types    │
  │ personas                    │       │                               │                                         │
  ├─────────────────────────────┼───────┼───────────────────────────────┼─────────────────────────────────────────┤
  │ Infrastructure agents       │ 7     │ services/agents/              │ 1/7 complete (MemoryAgent only)         │
  └─────────────────────────────┴───────┴───────────────────────────────┴─────────────────────────────────────────┘

  Total runtime surface: 47 persona files + 7 infrastructure agent implementations = 54 named entities competing for
  attention.

  AGENT_ARCHITECTURE.md (.claude/AGENT_ARCHITECTURE.md) already acknowledges this is wrong: "Before: 23+ agents →
  After: 7 agents (infrastructure only). Personas are NOT agents." (FACT)

  The "17-Agent" Question (INFERENCE)

  The 17 maps to Claude Code's customizable subagent types (excluding system-level Explore, Plan, claude-code-guide):

  ┌─────┬────────────────────────┬──────────────────────┬────────────────────────────────────────────────────┐
  │  #  │     Built-in Type      │ Has Dopemux Persona? │                Has Base .agent.md?                 │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 1   │ general-purpose        │ Yes                  │ No                                                 │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 2   │ statusline-setup       │ Yes                  │ No                                                 │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 3   │ technical-writer       │ Yes                  │ se-technical-writer                                │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 4   │ backend-architect      │ Yes                  │ No                                                 │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 5   │ frontend-architect     │ Yes                  │ No                                                 │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 6   │ system-architect       │ Yes                  │ se-system-architecture-reviewer                    │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 7   │ python-expert          │ Yes                  │ python-mcp-expert                                  │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 8   │ quality-engineer       │ Yes                  │ wg-code-sentinel, wg-code-alchemist                │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 9   │ security-engineer      │ Yes                  │ se-security-reviewer                               │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 10  │ performance-engineer   │ Yes                  │ No                                                 │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 11  │ socratic-mentor        │ Yes                  │ mentor, critical-thinking                          │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 12  │ learning-guide         │ Yes                  │ No                                                 │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 13  │ devops-architect       │ Yes                  │ devops-expert, se-gitops-ci, github-actions-expert │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 14  │ deep-research-agent    │ No                   │ task-researcher                                    │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 15  │ requirements-analyst   │ No                   │ prd, specification                                 │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 16  │ root-cause-analyst     │ No                   │ No                                                 │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 17  │ refactoring-expert     │ No                   │ modernization, janitor, tech-debt-remediation-plan │
  ├─────┼────────────────────────┼──────────────────────┼────────────────────────────────────────────────────┤
  │ 18  │ business-panel-experts │ No                   │ No                                                 │
  └─────┴────────────────────────┴──────────────────────┴────────────────────────────────────────────────────┘

  13 of 18 customizable types have dopemux personas. 5 do not. The remaining 34 .agent.md files are orphaned — they
  don't map to any built-in subagent type and cannot be invoked through Claude Code's standard Agent tool.

  Overlap Clusters (FACT)

  Cluster A — Planning/Task (CRITICAL REDUNDANCY)
  7 agents for ~3 distinct functions:

  ┌──────────────────────────────┬─────────────────────────────┬───────────────────────────┐
  │            Agent             │          Function           │       Overlap With        │
  ├──────────────────────────────┼─────────────────────────────┼───────────────────────────┤
  │ task-planner.agent.md        │ Create implementation plans │ implementation-plan, plan │
  ├──────────────────────────────┼─────────────────────────────┼───────────────────────────┤
  │ task-researcher.agent.md     │ Research before planning    │ plan                      │
  ├──────────────────────────────┼─────────────────────────────┼───────────────────────────┤
  │ implementation-plan.agent.md │ Machine-readable plans      │ task-planner              │
  ├──────────────────────────────┼─────────────────────────────┼───────────────────────────┤
  │ plan.agent.md                │ Strategic analysis          │ task-researcher           │
  ├──────────────────────────────┼─────────────────────────────┼───────────────────────────┤
  │ prd.agent.md                 │ Requirements docs           │ specification             │
  ├──────────────────────────────┼─────────────────────────────┼───────────────────────────┤
  │ workflow-executor.agent.md   │ Execute workflow steps      │ task-planner              │
  ├──────────────────────────────┼─────────────────────────────┼───────────────────────────┤
  │ specification.agent.md       │ Spec documents              │ prd, adr-generator        │
  └──────────────────────────────┴─────────────────────────────┴───────────────────────────┘

  Distinction: MOSTLY FALSE. The format differences (machine-readable vs human-readable, PRD vs spec) are output
  template choices, not distinct capabilities. The research→plan→execute pipeline needs 2-3 roles max, not 7.

  Cluster B — Mentoring/Thinking (SIGNIFICANT REDUNDANCY)
  5 agents with overlapping Socratic/critical-thinking capabilities:

  ┌────────────────────────────┬──────────────────────────────┬────────────────────────┐
  │           Agent            │           Function           │      Overlap With      │
  ├────────────────────────────┼──────────────────────────────┼────────────────────────┤
  │ socratic-mentor-dopemux.md │ Question-driven learning     │ mentor, learning-guide │
  ├────────────────────────────┼──────────────────────────────┼────────────────────────┤
  │ learning-guide-dopemux.md  │ Teaching concepts            │ socratic-mentor        │
  ├────────────────────────────┼──────────────────────────────┼────────────────────────┤
  │ mentor.agent.md            │ Guidance via Socratic method │ socratic-mentor        │
  ├────────────────────────────┼──────────────────────────────┼────────────────────────┤
  │ critical-thinking.agent.md │ Challenge assumptions        │ devils-advocate        │
  ├────────────────────────────┼──────────────────────────────┼────────────────────────┤
  │ devils-advocate.agent.md   │ Stress-test ideas            │ critical-thinking      │
  └────────────────────────────┴──────────────────────────────┴────────────────────────┘

  Distinction: PARTIALLY FALSE. socratic-mentor and learning-guide are genuinely different (questioning vs.
  explaining). But mentor.agent.md duplicates socratic-mentor. critical-thinking and devils-advocate are the same
  capability with different framing.

  Cluster C — DevOps (MODERATE REDUNDANCY)
  4 agents covering CI/CD:

  ┌──────────────────────────────────┬────────────────────────────────────────────┐
  │              Agent               │                Distinction                 │
  ├──────────────────────────────────┼────────────────────────────────────────────┤
  │ devops-architect-dopemux.md      │ MCP-aware, broad infrastructure            │
  ├──────────────────────────────────┼────────────────────────────────────────────┤
  │ devops-expert.agent.md           │ Lifecycle holistic (superseded by dopemux) │
  ├──────────────────────────────────┼────────────────────────────────────────────┤
  │ se-gitops-ci-specialist.agent.md │ Failure triage specialization              │
  ├──────────────────────────────────┼────────────────────────────────────────────┤
  │ github-actions-expert.agent.md   │ Platform-specific security                 │
  └──────────────────────────────────┴────────────────────────────────────────────┘

  Distinction: PARTIALLY REAL. The dopemux version supersedes the base. The CI-specialist and GH Actions expert are
  narrow enough to be flags/prompts, not standalone agents.

  Cluster D — Code Quality (MODERATE REDUNDANCY)

  ┌─────────────────────────────┬─────────────────────────────────┐
  │            Agent            │           Distinction           │
  ├─────────────────────────────┼─────────────────────────────────┤
  │ quality-engineer-dopemux.md │ Testing/coverage, MCP-aware     │
  ├─────────────────────────────┼─────────────────────────────────┤
  │ wg-code-sentinel.agent.md   │ Security-focused review (OWASP) │
  ├─────────────────────────────┼─────────────────────────────────┤
  │ wg-code-alchemist.agent.md  │ SOLID/clean code review         │
  └─────────────────────────────┴─────────────────────────────────┘

  Distinction: PARTIALLY REAL. These are three review perspectives. But wg-code-sentinel overlaps with
  security-engineer, and wg-code-alchemist overlaps with refactoring-expert. The "JARVIS personality" is style, not
  function.

  Cluster E — Tech Debt (REDUNDANCY)

  ┌─────────────────────────────────────┬────────────────────────────────────────┐
  │                Agent                │              Distinction               │
  ├─────────────────────────────────────┼────────────────────────────────────────┤
  │ modernization.agent.md              │ Deep analysis + recommendations (26KB) │
  ├─────────────────────────────────────┼────────────────────────────────────────┤
  │ tech-debt-remediation-plan.agent.md │ Metrics-based planning                 │
  ├─────────────────────────────────────┼────────────────────────────────────────┤
  │ janitor.agent.md                    │ Aggressive cleanup execution           │
  └─────────────────────────────────────┴────────────────────────────────────────┘

  Distinction: PARTIALLY FALSE. These are three phases of one workflow (analyze → plan → execute), not three
  independent roles.

  Cluster F — Prompt Engineering (REDUNDANCY)

  ┌──────────────────────────┬───────────────────────────────────────┐
  │          Agent           │              Distinction              │
  ├──────────────────────────┼───────────────────────────────────────┤
  │ prompt-builder.agent.md  │ Dual-persona validation system (18KB) │
  ├──────────────────────────┼───────────────────────────────────────┤
  │ prompt-engineer.agent.md │ Systematic framework analysis         │
  └──────────────────────────┴───────────────────────────────────────┘

  Distinction: FALSE. Same capability, different framing.

  Cluster G — Meta/Novelty

  ┌───────────────────────────────────────────────────┬────────────────────────────────────────────────────────────┐
  │                       Agent                       │                         Assessment                         │
  ├───────────────────────────────────────────────────┼────────────────────────────────────────────────────────────┤
  │ Ultimate-Transparent-Thinking-Beast-Mode.agent.md │ Personality override. 29KB of theater. Not a functional    │
  │                                                   │ role.                                                      │
  ├───────────────────────────────────────────────────┼────────────────────────────────────────────────────────────┤
  │ gilfoyle.agent.md                                 │ Personality wrapper on code review. Style, not function.   │
  ├───────────────────────────────────────────────────┼────────────────────────────────────────────────────────────┤
  │ meta-agentic-project-scaffold.agent.md            │ Project scaffolding. Narrow utility.                       │
  ├───────────────────────────────────────────────────┼────────────────────────────────────────────────────────────┤
  │ search-ai-optimization-expert.agent.md            │ SEO/AEO/GEO. Highly specialized, rarely needed.            │
  ├───────────────────────────────────────────────────┼────────────────────────────────────────────────────────────┤
  │ context7.agent.md                                 │ Library docs. This is a tool wrapper disguised as an       │
  │                                                   │ agent.                                                     │
  ├───────────────────────────────────────────────────┼────────────────────────────────────────────────────────────┤
  │ se-ux-ui-designer.agent.md                        │ UX research. Real capability, no dopemux version.          │
  ├───────────────────────────────────────────────────┼────────────────────────────────────────────────────────────┤
  │ se-product-manager-advisor.agent.md               │ Product management. Real capability, no dopemux version.   │
  ├───────────────────────────────────────────────────┼────────────────────────────────────────────────────────────┤
  │ refine-issue.agent.md                             │ Issue refinement. Narrow utility.                          │
  └───────────────────────────────────────────────────┴────────────────────────────────────────────────────────────┘

  Workflow Simulation (15 Scenarios)

  ┌─────┬─────────────────────────────┬───────────────────────────────────┬───────────────────┐
  │  #  │          Scenario           │      Agents Actually Needed       │ Never-Used Agents │
  ├─────┼─────────────────────────────┼───────────────────────────────────┼───────────────────┤
  │ 1   │ Fix a Python bug            │ python-expert, root-cause-analyst │ 40+               │
  ├─────┼─────────────────────────────┼───────────────────────────────────┼───────────────────┤
  │ 2   │ Add REST endpoint           │ backend-architect, python-expert  │ 42+               │
  ├─────┼─────────────────────────────┼───────────────────────────────────┼───────────────────┤
  │ 3   │ Write unit tests            │ quality-engineer, python-expert   │ 42+               │
  ├─────┼─────────────────────────────┼───────────────────────────────────┼───────────────────┤
  │ 4   │ Security audit              │ security-engineer                 │ 43+               │
  ├─────┼─────────────────────────────┼───────────────────────────────────┼───────────────────┤
  │ 5   │ CI/CD pipeline fix          │ devops-architect                  │ 43+               │
  ├─────┼─────────────────────────────┼───────────────────────────────────┼───────────────────┤
  │ 6   │ React component             │ frontend-architect                │ 43+               │
  ├─────┼─────────────────────────────┼───────────────────────────────────┼───────────────────┤
  │ 7   │ System design               │ system-architect                  │ 43+               │
  ├─────┼─────────────────────────────┼───────────────────────────────────┼───────────────────┤
  │ 8   │ Explain codebase to new dev │ learning-guide                    │ 43+               │
  ├─────┼─────────────────────────────┼───────────────────────────────────┼───────────────────┤
  │ 9   │ Refactor complex module     │ refactoring-expert, python-expert │ 42+               │
  ├─────┼─────────────────────────────┼───────────────────────────────────┼───────────────────┤
  │ 10  │ Write API docs              │ technical-writer                  │ 43+               │
  ├─────┼─────────────────────────────┼───────────────────────────────────┼───────────────────┤
  │ 11  │ Performance optimization    │ performance-engineer              │ 43+               │
  ├─────┼─────────────────────────────┼───────────────────────────────────┼───────────────────┤
  │ 12  │ Research unfamiliar library │ deep-research-agent               │ 43+               │
  ├─────┼─────────────────────────────┼───────────────────────────────────┼───────────────────┤
  │ 13  │ Plan feature from PRD       │ general-purpose                   │ 43+               │
  ├─────┼─────────────────────────────┼───────────────────────────────────┼───────────────────┤
  │ 14  │ Code review before merge    │ quality-engineer                  │ 43+               │
  ├─────┼─────────────────────────────┼───────────────────────────────────┼───────────────────┤
  │ 15  │ Debug production incident   │ root-cause-analyst, python-expert │ 42+               │
  └─────┴─────────────────────────────┴───────────────────────────────────┴───────────────────┘

  Key finding: In 15 realistic workflows, a maximum of 2 agents are needed per scenario. The remaining 42-43 agents
  sit idle. Most workflows route to the dopemux-enhanced built-in type — the 34 .agent.md files are almost never the
  correct choice because Claude Code's Agent tool dispatches by subagent_type, which maps to built-in names, not
  .agent.md filenames.

  Agents That Never Get Used (FACT + INFERENCE)

  Dead seats — cannot be invoked via standard Claude Code Agent tool (no matching subagent_type):
  - All 34 .agent.md files. These exist as files but have no dispatch mechanism in Claude Code's subagent routing.
  They could only be invoked by manually reading the file and injecting instructions — which defeats the purpose of an
   agent system.

  Too narrow to justify existence:
  - gilfoyle.agent.md (personality wrapper)
  - refine-issue.agent.md (one task, done rarely)
  - meta-agentic-project-scaffold.agent.md (one-time setup)
  - search-ai-optimization-expert.agent.md (niche domain)

  Duplicate mode behavior:
  - context7.agent.md duplicates what WORKFLOW_AUTOMATION.md already does (auto-routing to PAL apilookup)
  - Ultimate-Transparent-Thinking-Beast-Mode.agent.md duplicates what Introspection mode + --ultrathink flag already
  provides

  Phase 1 Conclusion

  The current system has 54 named entities where at most 13-18 are structurally reachable through Claude Code's
  dispatch and at most 2-3 are needed per workflow. The 34 .agent.md files are effectively dead code — they occupy
  disk space and cognitive overhead but have no runtime dispatch path. The 7 infrastructure agents are a separate
  concern (Python services, not personas).

  PROPOSAL: The canonical roster should contain only entities that map to Claude Code's built-in subagent types OR are
   infrastructure agents with real Python implementations. Everything else is either a prompt template (demote to
  reference), a mode concern (merge into modes), or dead weight (archive).

  ---
  Phase 2 — Routing Clarity Validation

  Agent Classification

  For each proposed canonical agent (the 13 existing dopemux-enhanced + 5 missing types):

  #: 1
  Agent: general-purpose-dopemux
  Should Use For: Default fallback, multi-domain tasks, unclear routing
  Must NOT Use For: Tasks matching a specialist agent
  Conflicts: Absorbs work from specialists when routing is lazy
  Status: VALID
  ────────────────────────────────────────
  #: 2
  Agent: python-expert-dopemux
  Should Use For: Python code, pytest, Python debugging
  Must NOT Use For: Non-Python languages
  Conflicts: Overlaps backend-architect for Python API work
  Status: VALID
  ────────────────────────────────────────
  #: 3
  Agent: backend-architect-dopemux
  Should Use For: API design, database, system reliability
  Must NOT Use For: Frontend, pure Python scripting
  Conflicts: Overlaps system-architect for architecture, python-expert for Python
  Status: WEAK
  ────────────────────────────────────────
  #: 4
  Agent: frontend-architect-dopemux
  Should Use For: React, CSS, browser, accessibility
  Must NOT Use For: Backend, infrastructure
  Conflicts: Clean boundary
  Status: VALID
  ────────────────────────────────────────
  #: 5
  Agent: system-architect-dopemux
  Should Use For: System design, scalability, architecture decisions
  Must NOT Use For: Implementation, narrow code tasks
  Conflicts: Overlaps backend-architect
  Status: WEAK
  ────────────────────────────────────────
  #: 6
  Agent: security-engineer-dopemux
  Should Use For: Vulnerability analysis, compliance, threat modeling
  Must NOT Use For: General code review, feature dev
  Conflicts: Clean boundary
  Status: VALID
  ────────────────────────────────────────
  #: 7
  Agent: quality-engineer-dopemux
  Should Use For: Testing strategy, coverage, test infrastructure
  Must NOT Use For: Security review, performance tuning
  Conflicts: Overlaps security-engineer for security tests
  Status: VALID
  ────────────────────────────────────────
  #: 8
  Agent: performance-engineer-dopemux
  Should Use For: Profiling, optimization, benchmarking
  Must NOT Use For: Feature development, testing strategy
  Conflicts: Clean boundary
  Status: VALID
  ────────────────────────────────────────
  #: 9
  Agent: technical-writer-dopemux
  Should Use For: Documentation, API docs, guides
  Must NOT Use For: Code implementation
  Conflicts: Clean boundary
  Status: VALID
  ────────────────────────────────────────
  #: 10
  Agent: devops-architect-dopemux
  Should Use For: CI/CD, infrastructure, deployment, monitoring
  Must NOT Use For: Application code, business logic
  Conflicts: Clean boundary
  Status: VALID
  ────────────────────────────────────────
  #: 11
  Agent: socratic-mentor-dopemux
  Should Use For: Question-driven learning, discovery
  Must NOT Use For: Direct answers, implementation
  Conflicts: Overlaps learning-guide
  Status: WEAK
  ────────────────────────────────────────
  #: 12
  Agent: learning-guide-dopemux
  Should Use For: Teaching, explaining, progressive learning
  Must NOT Use For: Challenging assumptions, debate
  Conflicts: Overlaps socratic-mentor
  Status: WEAK
  ────────────────────────────────────────
  #: 13
  Agent: statusline-setup-dopemux
  Should Use For: Claude Code UI configuration
  Must NOT Use For: Everything else
  Conflicts: Clean boundary, very narrow
  Status: VALID (but trivial)
  ────────────────────────────────────────
  #: 14
  Agent: deep-research-agent (missing)
  Should Use For: Multi-source investigation, complex research
  Must NOT Use For: Quick lookups, implementation
  Conflicts: None
  Status: VALID (needs dopemux version)
  ────────────────────────────────────────
  #: 15
  Agent: requirements-analyst (missing)
  Should Use For: Requirements discovery, PRD, specifications
  Must NOT Use For: Implementation, testing
  Conflicts: Overlaps general-purpose for planning
  Status: VALID (needs dopemux version)
  ────────────────────────────────────────
  #: 16
  Agent: root-cause-analyst (missing)
  Should Use For: Bug investigation, incident analysis
  Must NOT Use For: Feature development
  Conflicts: Overlaps python-expert for Python debugging
  Status: VALID (needs dopemux version)
  ────────────────────────────────────────
  #: 17
  Agent: refactoring-expert (missing)
  Should Use For: Code improvement, tech debt, cleanup
  Must NOT Use For: New features, architecture
  Conflicts: Overlaps quality-engineer for code quality
  Status: VALID (needs dopemux version)
  ────────────────────────────────────────
  #: 18
  Agent: business-panel-experts (missing)
  Should Use For: Strategic analysis, business decisions
  Must NOT Use For: Technical implementation
  Conflicts: Already covered by MODE_Business_Panel
  Status: INVALID — this is a mode, not an agent

  Top Routing Ambiguities

  1. system-architect vs backend-architect: Both handle architecture. Backend adds database/API specifics. The
  distinction is scope (system-level vs component-level), but in practice a user asking "design the auth system" could
   route to either. Fix: Merge into one architect role with backend/system scope as a parameter, OR sharpen
  boundaries: system-architect = cross-service/infrastructure, backend-architect = single-service internals.
  2. socratic-mentor vs learning-guide: Both teach. Socratic asks questions, learning-guide explains. But the user
  rarely consciously chooses "I want to be questioned" vs "I want to be taught." Fix: Merge into one mentor role.
  Teaching style (Socratic vs direct) should be a flag, not a separate agent.
  3. python-expert vs backend-architect (for Python APIs): If building a FastAPI endpoint, both are valid. Fix:
  python-expert = language-level concerns. backend-architect = architectural concerns. Boundary: "Is this about Python
   idioms or about system design?" Acceptable ambiguity — let general-purpose arbitrate.
  4. quality-engineer vs refactoring-expert: Both improve existing code. Quality focuses on tests, refactoring focuses
   on structure. Fix: Acceptable distinction. Keep separate.
  5. business-panel-experts vs MODE_Business_Panel: The mode already provides this capability with 9 expert personas,
  three interaction modes, and synthesis. A separate subagent adds nothing. Fix: Delete the subagent type. Use the
  mode.

  Phase 2 Conclusion

  Of 18 proposed agents: 13 VALID, 3 WEAK (need boundary sharpening or merge), 1 INVALID (business-panel-experts
  duplicates a mode), 1 trivial (statusline-setup is real but barely qualifies as an "agent").

  Required boundary rewrites: system-architect/backend-architect disambiguation; socratic-mentor/learning-guide merge.

  ---
  Phase 3 — Mode vs Agent Boundary Audit

  Definitions Applied

  - Modes = HOW work is done (posture, execution style, tool selection, context behavior)
  - Agents = WHAT work is done (domain-specific task execution)

  Current Mode Inventory (FACT)

  ┌───────────────────────┬────────────────────────────────────┬──────────────────────────────────────────────────┐
  │         Mode          │          Actual Behavior           │                  Correct Layer?                  │
  ├───────────────────────┼────────────────────────────────────┼──────────────────────────────────────────────────┤
  │ MODE_Brainstorming    │ Discovery mindset, Socratic        │ Yes — mode (execution style)                     │
  │                       │ questions                          │                                                  │
  ├───────────────────────┼────────────────────────────────────┼──────────────────────────────────────────────────┤
  │ MODE_Business_Panel   │ 9 expert personas, 3 interaction   │ HYBRID — contains agent-like expert personas     │
  │                       │ phases                             │                                                  │
  ├───────────────────────┼────────────────────────────────────┼──────────────────────────────────────────────────┤
  │ MODE_DeepResearch     │ Systematic investigation,          │ Yes — mode (execution style)                     │
  │                       │ evidence-based                     │                                                  │
  ├───────────────────────┼────────────────────────────────────┼──────────────────────────────────────────────────┤
  │ MODE_Introspection    │ Meta-cognitive self-analysis       │ Yes — mode (execution style)                     │
  ├───────────────────────┼────────────────────────────────────┼──────────────────────────────────────────────────┤
  │ MODE_Orchestration    │ Tool selection, resource           │ Yes — mode (execution style)                     │
  │                       │ management                         │                                                  │
  ├───────────────────────┼────────────────────────────────────┼──────────────────────────────────────────────────┤
  │ MODE_Task_Management  │ Hierarchical task organization     │ HYBRID — contains workflow coordination (agent   │
  │                       │                                    │ territory)                                       │
  ├───────────────────────┼────────────────────────────────────┼──────────────────────────────────────────────────┤
  │ MODE_Token_Efficiency │ Symbol compression, token          │ Yes — mode (execution style)                     │
  │                       │ reduction                          │                                                  │
  └───────────────────────┴────────────────────────────────────┴──────────────────────────────────────────────────┘

  Boundary Violations

  Violation: Business Panel contains 9 expert agents
  Source: MODE_Business_Panel.md
  Problem: Mode file defines 9 named expert personas with distinct voices and analysis methods. This is agent work
    disguised as a mode.
  Recommendation: KEEP AS MODE — the experts are analysis lenses, not independent workers. The mode controls when/how
    they're applied. This is an acceptable composite mode.
  ────────────────────────────────────────
  Violation: Task Management prescribes workflow coordination
  Source: MODE_Task_Management.md
  Problem: Defines task hierarchy, memory operations, execution patterns. Overlaps with WorkflowCoordinator
    infrastructure agent.
  Recommendation: SPLIT — task organization (mode) vs workflow execution (agent). Mode should set the posture; agent
    should do the work.
  ────────────────────────────────────────
  Violation: FLAGS.md contains MCP server routing
  Source: FLAGS.md
  Problem: --c7, --serena, --magic etc. are tool selection decisions, which is orchestration-mode territory.
  Recommendation: ACCEPTABLE — flags modify mode behavior, not replace it. FLAGS.md is a modifier layer, not a mode.
  ────────────────────────────────────────
  Violation: WORKFLOW_AUTOMATION.md is a routing engine
  Source: WORKFLOW_AUTOMATION.md
  Problem: Automatically selects MCP servers based on detected workflow phase. This is agent/orchestration behavior
    embedded in a config file.
  Recommendation: CORRECT LAYER — this is configuration for the orchestration mode, not a mode itself.

  Items Misclassified

  ┌───────────────────────────────────────────────────┬────────────┬──────────────────────────────────────────────┐
  │                       Item                        │ Currently  │                  Should Be                   │
  │                                                   │     Is     │                                              │
  ├───────────────────────────────────────────────────┼────────────┼──────────────────────────────────────────────┤
  │ context7.agent.md                                 │ Agent      │ Tool wrapper / reference doc — just says     │
  │                                                   │ persona    │ "use Context7 MCP." Delete.                  │
  ├───────────────────────────────────────────────────┼────────────┼──────────────────────────────────────────────┤
  │ Ultimate-Transparent-Thinking-Beast-Mode.agent.md │ Agent      │ Execution modifier / flag — equivalent to    │
  │                                                   │ persona    │ --ultrathink --introspect. Archive.          │
  ├───────────────────────────────────────────────────┼────────────┼──────────────────────────────────────────────┤
  │ gilfoyle.agent.md                                 │ Agent      │ Personality skin — not a functional role.    │
  │                                                   │ persona    │ Archive.                                     │
  ├───────────────────────────────────────────────────┼────────────┼──────────────────────────────────────────────┤
  │                                                   │ Agent      │ Prompt pattern / template — useful reference │
  │ prompt-builder.agent.md                           │ persona    │  but not a runtime agent. Demote to          │
  │                                                   │            │ reference.                                   │
  ├───────────────────────────────────────────────────┼────────────┼──────────────────────────────────────────────┤
  │ prompt-engineer.agent.md                          │ Agent      │ Same as above. Merge with prompt-builder,    │
  │                                                   │ persona    │ demote to reference.                         │
  ├───────────────────────────────────────────────────┼────────────┼──────────────────────────────────────────────┤
  │ search-ai-optimization-expert.agent.md            │ Agent      │ Domain reference doc — specialized SEO       │
  │                                                   │ persona    │ knowledge. Demote to reference.              │
  ├───────────────────────────────────────────────────┼────────────┼──────────────────────────────────────────────┤
  │                                                   │ Global     │ Reference doc — detailed research            │
  │ RESEARCH_CONFIG.md                                │ config     │ parameters. Should not be always-loaded.     │
  │                                                   │            │ Move to on-demand reference.                 │
  ├───────────────────────────────────────────────────┼────────────┼──────────────────────────────────────────────┤
  │                                                   │ Global     │ Reference doc — usage examples for a         │
  │ BUSINESS_PANEL_EXAMPLES.md                        │ config     │ specific mode. Should not be always-loaded.  │
  │                                                   │            │ Move to on-demand reference.                 │
  ├───────────────────────────────────────────────────┼────────────┼──────────────────────────────────────────────┤
  │                                                   │ Global     │ Reference doc — symbol definitions for one   │
  │ BUSINESS_SYMBOLS.md                               │ config     │ mode. Should not be always-loaded. Move to   │
  │                                                   │            │ on-demand reference.                         │
  ├───────────────────────────────────────────────────┼────────────┼──────────────────────────────────────────────┤
  │                                                   │ Global     │ Reference doc — tool documentation for one   │
  │ MCP_Exa.md                                        │ config     │ MCP server. Should not be always-loaded.     │
  │                                                   │            │ Move to on-demand reference.                 │
  ├───────────────────────────────────────────────────┼────────────┼──────────────────────────────────────────────┤
  │ MCP_GPTResearcher.md                              │ Global     │ Reference doc — same as above. Move to       │
  │                                                   │ config     │ on-demand reference.                         │
  └───────────────────────────────────────────────────┴────────────┴──────────────────────────────────────────────┘

  Corrected Layer Model (PROPOSAL)

  ALWAYS-LOADED CONTEXT (~15K tokens target)
  ├── CLAUDE.md (compressed core rules + ADHD principles)
  ├── RULES.md (compressed critical rules only)
  ├── FLAGS.md (compressed flag reference)
  └── WORKFLOW_AUTOMATION.md (auto-routing config)

  ON-DEMAND MODES (loaded when activated by flag/detection)
  ├── MODE_Brainstorming.md
  ├── MODE_Business_Panel.md (includes expert personas)
  ├── MODE_DeepResearch.md
  ├── MODE_Introspection.md
  ├── MODE_Orchestration.md
  ├── MODE_Task_Management.md
  └── MODE_Token_Efficiency.md

  SUBAGENT PERSONAS (loaded per subagent invocation)
  ├── 13 existing dopemux-enhanced personas
  └── 4 new dopemux personas (deep-research, requirements, root-cause, refactoring)

  REFERENCE DOCS (loaded on explicit request only)
  ├── MCP documentation (6 files)
  ├── PRINCIPLES.md
  ├── RESEARCH_CONFIG.md
  ├── BUSINESS_PANEL_EXAMPLES.md
  ├── BUSINESS_SYMBOLS.md
  └── Archived .agent.md files (prompt templates, domain references)

  INFRASTRUCTURE AGENTS (Python services, not context)
  └── 7 agents in services/agents/

  Phase 3 Conclusion

  The mode/agent boundary is mostly clean in concept but polluted in practice by:
  1. 34 orphaned .agent.md files that are neither modes nor dispatchable agents
  2. Reference docs masquerading as always-loaded config (MCP docs, examples, research config)
  3. One mode-agent hybrid (Business Panel) that is acceptable
  4. One mode-agent overlap (Task Management vs WorkflowCoordinator) that needs splitting

  ---
  Phase 4 — Token Economy and Runtime Load Audit

  Current Always-Loaded Footprint (FACT)

  Every Claude Code conversation in this project loads ALL of the following into the system prompt:

  ┌────────────────────────────┬──────────┬─────────────┬────────────────────────┐
  │            File            │  Bytes   │ Est. Tokens │        Category        │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ CLAUDE.md (global)         │ 14,372   │ 3,600       │ Core rules             │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ RULES.md                   │ 21,557   │ 5,400       │ Behavioral rules       │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ FLAGS.md                   │ ~8,000   │ 2,000       │ Flag reference         │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ PRINCIPLES.md              │ ~2,000   │ 500         │ Engineering philosophy │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ RESEARCH_CONFIG.md         │ 10,346   │ 2,600       │ Research parameters    │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ BUSINESS_PANEL_EXAMPLES.md │ ~8,000   │ 2,000       │ Usage examples         │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ BUSINESS_SYMBOLS.md        │ ~6,000   │ 1,500       │ Symbol definitions     │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ MODE_Brainstorming.md      │ ~1,200   │ 300         │ Mode def               │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ MODE_Business_Panel.md     │ 15,378   │ 3,800       │ Mode def               │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ MODE_Introspection.md      │ ~1,200   │ 300         │ Mode def               │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ MODE_Orchestration.md      │ ~1,200   │ 300         │ Mode def               │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ MODE_Task_Management.md    │ ~2,000   │ 500         │ Mode def               │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ MODE_Token_Efficiency.md   │ ~1,600   │ 400         │ Mode def               │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ MODE_DeepResearch.md       │ ~800     │ 200         │ Mode def               │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ MCP_Zen.md                 │ 15,416   │ 3,900       │ Tool doc               │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ MCP_ConPort.md             │ 9,018    │ 2,300       │ Tool doc               │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ MCP_Serena.md              │ 12,255   │ 3,100       │ Tool doc               │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ MCP_DopeContext.md         │ 16,768   │ 4,200       │ Tool doc               │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ MCP_Exa.md                 │ ~4,000   │ 1,000       │ Tool doc               │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ MCP_GPTResearcher.md       │ ~6,000   │ 1,500       │ Tool doc               │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ Project CLAUDE.md          │ ~6,000   │ 1,500       │ Project config         │
  ├────────────────────────────┼──────────┼─────────────┼────────────────────────┤
  │ TOTAL                      │ ~163,000 │ ~41,000     │                        │
  └────────────────────────────┴──────────┴─────────────┴────────────────────────┘

  41,000 tokens of always-loaded behavioral instructions. On a 200K context window, that's 20.5% consumed before the
  first user message.

  What Should NOT Be Always-Loaded

  ┌────────────────────────────┬─────────┬──────────────────────┬────────────────────────────────────────┐
  │            Item            │ Tokens  │        Action        │               Rationale                │
  ├────────────────────────────┼─────────┼──────────────────────┼────────────────────────────────────────┤
  │ BUSINESS_PANEL_EXAMPLES.md │ 2,000   │ Move to ref          │ Only needed during business-panel mode │
  ├────────────────────────────┼─────────┼──────────────────────┼────────────────────────────────────────┤
  │ BUSINESS_SYMBOLS.md        │ 1,500   │ Move to ref          │ Only needed during business-panel mode │
  ├────────────────────────────┼─────────┼──────────────────────┼────────────────────────────────────────┤
  │ RESEARCH_CONFIG.md         │ 2,600   │ Move to ref          │ Only needed during deep-research mode  │
  ├────────────────────────────┼─────────┼──────────────────────┼────────────────────────────────────────┤
  │ MCP_Exa.md                 │ 1,000   │ Move to ref          │ Tool doc, queryable on demand          │
  ├────────────────────────────┼─────────┼──────────────────────┼────────────────────────────────────────┤
  │ MCP_GPTResearcher.md       │ 1,500   │ Move to ref          │ Tool doc, queryable on demand          │
  ├────────────────────────────┼─────────┼──────────────────────┼────────────────────────────────────────┤
  │ MCP_Serena.md              │ 3,100   │ Move to ref          │ Tool doc, queryable on demand          │
  ├────────────────────────────┼─────────┼──────────────────────┼────────────────────────────────────────┤
  │ MCP_DopeContext.md         │ 4,200   │ Move to ref          │ Tool doc, queryable on demand          │
  ├────────────────────────────┼─────────┼──────────────────────┼────────────────────────────────────────┤
  │ MCP_ConPort.md             │ 2,300   │ Move to ref          │ Tool doc, queryable on demand          │
  ├────────────────────────────┼─────────┼──────────────────────┼────────────────────────────────────────┤
  │ MCP_Zen.md                 │ 3,900   │ Move to ref          │ Tool doc, queryable on demand          │
  ├────────────────────────────┼─────────┼──────────────────────┼────────────────────────────────────────┤
  │ MODE_Business_Panel.md     │ 3,800   │ Load on activation   │ Only needed when mode is triggered     │
  ├────────────────────────────┼─────────┼──────────────────────┼────────────────────────────────────────┤
  │ PRINCIPLES.md              │ 500     │ Merge into CLAUDE.md │ 3 bullet points cover it               │
  ├────────────────────────────┼─────────┼──────────────────────┼────────────────────────────────────────┤
  │ Savings                    │ ~26,400 │                      │ 64% reduction                          │
  └────────────────────────────┴─────────┴──────────────────────┴────────────────────────────────────────┘

  Proposed Token Budget

  ┌────────────────────────────────────────────────────┬─────────┬──────────┬─────────┐
  │                      Category                      │ Current │ Proposed │ Change  │
  ├────────────────────────────────────────────────────┼─────────┼──────────┼─────────┤
  │ Core rules (CLAUDE.md compressed)                  │ 3,600   │ 2,500    │ -1,100  │
  ├────────────────────────────────────────────────────┼─────────┼──────────┼─────────┤
  │ Behavioral rules (RULES.md compressed)             │ 5,400   │ 3,000    │ -2,400  │
  ├────────────────────────────────────────────────────┼─────────┼──────────┼─────────┤
  │ Flags (compressed)                                 │ 2,000   │ 1,200    │ -800    │
  ├────────────────────────────────────────────────────┼─────────┼──────────┼─────────┤
  │ Modes (compact summaries, load full on activation) │ 9,800   │ 1,500    │ -8,300  │
  ├────────────────────────────────────────────────────┼─────────┼──────────┼─────────┤
  │ MCP docs (move to reference)                       │ 16,000  │ 0        │ -16,000 │
  ├────────────────────────────────────────────────────┼─────────┼──────────┼─────────┤
  │ Research/Business reference                        │ 6,100   │ 0        │ -6,100  │
  ├────────────────────────────────────────────────────┼─────────┼──────────┼─────────┤
  │ Project config                                     │ 1,500   │ 1,200    │ -300    │
  ├────────────────────────────────────────────────────┼─────────┼──────────┼─────────┤
  │ Workflow routing                                   │ 0       │ 800      │ +800    │
  ├────────────────────────────────────────────────────┼─────────┼──────────┼─────────┤
  │ TOTAL                                              │ ~41,000 │ ~10,200  │ -75%    │
  └────────────────────────────────────────────────────┴─────────┴──────────┴─────────┘

  Duplication Audit

  ┌───────────────────────────────────┬─────────────────────────────────────────────────────────┬─────────────────┐
  │              Content              │                       Appears In                        │   Duplicate     │
  │                                   │                                                         │     Tokens      │
  ├───────────────────────────────────┼─────────────────────────────────────────────────────────┼─────────────────┤
  │ MCP tool usage rules              │ CLAUDE.md + RULES.md + every dopemux persona            │ ~2,000 wasted   │
  ├───────────────────────────────────┼─────────────────────────────────────────────────────────┼─────────────────┤
  │ ADHD accommodation instructions   │ CLAUDE.md + Project CLAUDE.md + every dopemux persona   │ ~1,500 wasted   │
  ├───────────────────────────────────┼─────────────────────────────────────────────────────────┼─────────────────┤
  │ "Never use bash for code          │ CLAUDE.md + RULES.md + every dopemux persona header     │ ~500 wasted     │
  │ operations"                       │                                                         │                 │
  ├───────────────────────────────────┼─────────────────────────────────────────────────────────┼─────────────────┤
  │ PAL/Zen tool descriptions         │ MCP_Zen.md + WORKFLOW_AUTOMATION.md + persona files     │ ~1,000 wasted   │
  ├───────────────────────────────────┼─────────────────────────────────────────────────────────┼─────────────────┤
  │ Authority matrix rules            │ authority-matrix.md + integration-bridge.md + persona   │ ~800 wasted     │
  │                                   │ files                                                   │                 │
  └───────────────────────────────────┴─────────────────────────────────────────────────────────┴─────────────────┘

  Total duplication waste: ~5,800 tokens across the system.

  Token Regression Risks (PROPOSAL)

  If the dopemux persona generator creates more dopemux-enhanced files:
  - Each dopemux persona is ~5-15KB (1,300-3,800 tokens)
  - Per-subagent load, NOT always-loaded — acceptable
  - Risk: If a generator stamps MCP boilerplate into every persona, you get 13x duplication of tool instructions that
  are already in CLAUDE.md

  Phase 4 Conclusion

  The system is consuming 4x more always-loaded context than necessary. 75% reduction is achievable by moving
  reference docs to on-demand loading and compressing core rules. The biggest wins are removing MCP documentation (16K
   tokens) and mode definitions (8.3K tokens) from always-loaded context.

  ---
  Phase 5 — Reality Check Under Operator Stress

  Assumptions About Operator

  Per the prompt: switching contexts, somewhat distracted, under time pressure, not memorizing 35+ special roles,
  trying to get work done.

  Top 10 Friction Points

  ┌─────┬─────────────────────────────┬──────────┬────────────────────────────────────────────────────────────────┐
  │  #  │       Friction Point        │ Severity │                             Impact                             │
  ├─────┼─────────────────────────────┼──────────┼────────────────────────────────────────────────────────────────┤
  │ 1   │ 47 persona files, only 13   │ CRITICAL │ Operator discovers .agent.md files, tries to use them, nothing │
  │     │ dispatchable                │          │  happens. Confusion, wasted time.                              │
  ├─────┼─────────────────────────────┼──────────┼────────────────────────────────────────────────────────────────┤
  │ 2   │ 20% context consumed by     │ HIGH     │ Less room for actual work. Long conversations hit compression  │
  │     │ instructions                │          │ earlier. Complex tasks truncated.                              │
  ├─────┼─────────────────────────────┼──────────┼────────────────────────────────────────────────────────────────┤
  │ 3   │ Duplicate instructions in   │ MEDIUM   │ Operator edits RULES.md, doesn't know CLAUDE.md and persona    │
  │     │ 3+ places                   │          │ files also need updating. Drift.                               │
  ├─────┼─────────────────────────────┼──────────┼────────────────────────────────────────────────────────────────┤
  │ 4   │ system-architect vs         │ MEDIUM   │ Under pressure, operator picks wrong one or gives up and uses  │
  │     │ backend-architect ambiguity │          │ general-purpose for everything.                                │
  ├─────┼─────────────────────────────┼──────────┼────────────────────────────────────────────────────────────────┤
  │ 5   │ socratic-mentor vs          │ LOW      │ Operator won't distinguish these under stress. Will use        │
  │     │ learning-guide              │          │ general-purpose instead.                                       │
  ├─────┼─────────────────────────────┼──────────┼────────────────────────────────────────────────────────────────┤
  │ 6   │ 7 infrastructure agents, 1  │ MEDIUM   │ 6 pending agents create expectations the system can't meet.    │
  │     │ working                     │          │ Operator tries to invoke CognitiveGuardian → nothing happens.  │
  ├─────┼─────────────────────────────┼──────────┼────────────────────────────────────────────────────────────────┤
  │ 7   │ Business Panel mode is 15K  │ MEDIUM   │ Single mode definition is larger than all other modes          │
  │     │ tokens                      │          │ combined. Loaded every conversation even when not needed.      │
  ├─────┼─────────────────────────────┼──────────┼────────────────────────────────────────────────────────────────┤
  │ 8   │ 34 .agent.md files have no  │ HIGH     │ Who maintains these? When SuperClaude updates, do these        │
  │     │ owner                       │          │ update? Who tests them? Maintenance debt.                      │
  ├─────┼─────────────────────────────┼──────────┼────────────────────────────────────────────────────────────────┤
  │ 9   │ Authority matrix is policy, │ MEDIUM   │ Written as "never do X" but nothing prevents it. Relies on LLM │
  │     │  not enforcement            │          │  compliance with markdown instructions.                        │
  ├─────┼─────────────────────────────┼──────────┼────────────────────────────────────────────────────────────────┤
  │     │ Task-Orchestrator hooks     │          │ Project CLAUDE.md says "auto-start session via start_session"  │
  │ 10  │ assumed running             │ MEDIUM   │ — but if the service isn't running, every conversation starts  │
  │     │                             │          │ with a hook failure.                                           │
  └─────┴─────────────────────────────┴──────────┴────────────────────────────────────────────────────────────────┘

  What Breaks First Under Pressure

  1. Agent selection: With 47 named entities, a stressed operator just uses general-purpose for everything. The
  specialization is wasted.
  2. Context window: At 41K tokens of instructions, a complex debugging session with multiple file reads will hit
  compression within 15-20 exchanges. The instructions themselves get compressed away, causing behavioral drift.
  3. Maintenance: Nobody is updating 34 .agent.md files. They rot. Operator encounters outdated instructions
  referencing removed tools.
  4. Mode activation: 7 modes with auto-detection triggers means the system might activate a mode the operator doesn't
   want, changing behavior unexpectedly.

  Simplification Recommendations (PROPOSAL)

  ┌─────┬────────────────────────────────────────────────────────────────┬────────┬──────────────────────────────┐
  │  #  │                         Recommendation                         │ Effort │            Impact            │
  ├─────┼────────────────────────────────────────────────────────────────┼────────┼──────────────────────────────┤
  │ 1   │ Archive all 34 .agent.md files to a reference directory.       │ 10 min │ Removes 34 sources of        │
  │     │ They're not dispatchable.                                      │        │ confusion                    │
  ├─────┼────────────────────────────────────────────────────────────────┼────────┼──────────────────────────────┤
  │ 2   │ Move all MCP docs to on-demand reference                       │ 30 min │ Recovers 16K tokens          │
  ├─────┼────────────────────────────────────────────────────────────────┼────────┼──────────────────────────────┤
  │ 3   │ Compress CLAUDE.md + RULES.md into one file                    │ 2      │ Eliminates duplication,      │
  │     │                                                                │ hours  │ saves 3K tokens              │
  ├─────┼────────────────────────────────────────────────────────────────┼────────┼──────────────────────────────┤
  │ 4   │ Merge socratic-mentor + learning-guide into one mentor persona │ 30 min │ Removes routing ambiguity    │
  ├─────┼────────────────────────────────────────────────────────────────┼────────┼──────────────────────────────┤
  │ 5   │ Add --backend flag to system-architect instead of separate     │ 1 hour │ Reduces roster by 1, clearer │
  │     │ backend-architect                                              │        │  boundary                    │
  ├─────┼────────────────────────────────────────────────────────────────┼────────┼──────────────────────────────┤
  │ 6   │ Load modes on activation only with 1-line summaries            │ 1 hour │ Saves 8K tokens              │
  │     │ always-loaded                                                  │        │                              │
  ├─────┼────────────────────────────────────────────────────────────────┼────────┼──────────────────────────────┤
  │ 7   │ Remove Task-Orchestrator auto-hooks from CLAUDE.md until       │ 10 min │ Prevents hook failures       │
  │     │ service is reliable                                            │        │                              │
  ├─────┼────────────────────────────────────────────────────────────────┼────────┼──────────────────────────────┤
  │ 8   │ Create 4 missing dopemux personas for deep-research,           │ 2      │ Completes the canonical set  │
  │     │ requirements, root-cause, refactoring                          │ hours  │                              │
  └─────┴────────────────────────────────────────────────────────────────┴────────┴──────────────────────────────┘

  Phase 5 Conclusion

  The system is overengineered for its actual usage pattern. A distracted operator will default to general-purpose for
   80% of tasks because the specialization roster is too large to remember and the routing boundaries are too fuzzy to
   trust. The fix is radical simplification: fewer always-loaded instructions, fewer agents, clearer boundaries.

  ---
  Final Recommendation

  Executive Verdict

  APPROVED WITH CHANGES

  The concept of mapping dopemux-enhanced personas to Claude Code's built-in subagent types is structurally sound.
  But:
  - The current count of 13 dopemux personas needs to become 15 (not 17, not 18)
  - The 34 .agent.md files must be archived — they are not dispatchable and create confusion
  - The always-loaded context must be reduced by 75% from 41K to ~10K tokens
  - business-panel-experts should NOT be an agent — it's already a mode

  Final Recommended Modes

  ┌─────┬─────────────────┬────────┬──────────────────────────────────────────────────────────────────────────────┐
  │  #  │      Mode       │ Status │                                    Change                                    │
  ├─────┼─────────────────┼────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 1   │ Brainstorming   │ KEEP   │ Compress to 1-line summary in always-loaded, full on activation              │
  ├─────┼─────────────────┼────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 2   │ Business Panel  │ KEEP   │ Move full definition to on-demand. Remove EXAMPLES and SYMBOLS from          │
  │     │                 │        │ always-loaded.                                                               │
  ├─────┼─────────────────┼────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 3   │ Deep Research   │ KEEP   │ Compress. Move RESEARCH_CONFIG to on-demand.                                 │
  ├─────┼─────────────────┼────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 4   │ Introspection   │ KEEP   │ Already compact                                                              │
  ├─────┼─────────────────┼────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 5   │ Orchestration   │ KEEP   │ Already compact                                                              │
  ├─────┼─────────────────┼────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 6   │ Task Management │ KEEP   │ Split workflow execution concerns to WorkflowCoordinator agent               │
  ├─────┼─────────────────┼────────┼──────────────────────────────────────────────────────────────────────────────┤
  │ 7   │ Token           │ KEEP   │ Already compact                                                              │
  │     │ Efficiency      │        │                                                                              │
  └─────┴─────────────────┴────────┴──────────────────────────────────────────────────────────────────────────────┘

  Mode count: 7 (unchanged)

  Final Recommended Agent Roster

  ┌─────┬───────────────────────┬─────────────────────────────────┬────────────────────────────────────────┐
  │  #  │ Agent (subagent_type) │         Dopemux Persona         │                 Status                 │
  ├─────┼───────────────────────┼─────────────────────────────────┼────────────────────────────────────────┤
  │ 1   │ general-purpose       │ general-purpose-dopemux.md      │ KEEP                                   │
  ├─────┼───────────────────────┼─────────────────────────────────┼────────────────────────────────────────┤
  │ 2   │ python-expert         │ python-expert-dopemux.md        │ KEEP                                   │
  ├─────┼───────────────────────┼─────────────────────────────────┼────────────────────────────────────────┤
  │ 3   │ system-architect      │ system-architect-dopemux.md     │ KEEP (absorbs backend-architect scope) │
  ├─────┼───────────────────────┼─────────────────────────────────┼────────────────────────────────────────┤
  │ 4   │ frontend-architect    │ frontend-architect-dopemux.md   │ KEEP                                   │
  ├─────┼───────────────────────┼─────────────────────────────────┼────────────────────────────────────────┤
  │ 5   │ security-engineer     │ security-engineer-dopemux.md    │ KEEP                                   │
  ├─────┼───────────────────────┼─────────────────────────────────┼────────────────────────────────────────┤
  │ 6   │ quality-engineer      │ quality-engineer-dopemux.md     │ KEEP                                   │
  ├─────┼───────────────────────┼─────────────────────────────────┼────────────────────────────────────────┤
  │ 7   │ performance-engineer  │ performance-engineer-dopemux.md │ KEEP                                   │
  ├─────┼───────────────────────┼─────────────────────────────────┼────────────────────────────────────────┤
  │ 8   │ technical-writer      │ technical-writer-dopemux.md     │ KEEP                                   │
  ├─────┼───────────────────────┼─────────────────────────────────┼────────────────────────────────────────┤
  │ 9   │ devops-architect      │ devops-architect-dopemux.md     │ KEEP                                   │
  ├─────┼───────────────────────┼─────────────────────────────────┼────────────────────────────────────────┤
  │ 10  │ socratic-mentor       │ socratic-mentor-dopemux.md      │ KEEP (absorbs learning-guide)          │
  ├─────┼───────────────────────┼─────────────────────────────────┼────────────────────────────────────────┤
  │ 11  │ deep-research-agent   │ CREATE                          │ NEW — dopemux-enhanced                 │
  ├─────┼───────────────────────┼─────────────────────────────────┼────────────────────────────────────────┤
  │ 12  │ requirements-analyst  │ CREATE                          │ NEW — dopemux-enhanced                 │
  ├─────┼───────────────────────┼─────────────────────────────────┼────────────────────────────────────────┤
  │ 13  │ root-cause-analyst    │ CREATE                          │ NEW — dopemux-enhanced                 │
  ├─────┼───────────────────────┼─────────────────────────────────┼────────────────────────────────────────┤
  │ 14  │ refactoring-expert    │ CREATE                          │ NEW — dopemux-enhanced                 │
  ├─────┼───────────────────────┼─────────────────────────────────┼────────────────────────────────────────┤
  │ 15  │ statusline-setup      │ statusline-setup-dopemux.md     │ KEEP (trivial but harmless)            │
  └─────┴───────────────────────┴─────────────────────────────────┴────────────────────────────────────────┘

  Agent count: 15 (down from proposed 17-18)

  Merge/Delete/Archive Decisions

  MERGE (2 merges):

  ┌──────────────────────────────┬─────────────────────────────┬───────────────────────────────────────────────────┐
  │            Source            │            Into             │                     Rationale                     │
  ├──────────────────────────────┼─────────────────────────────┼───────────────────────────────────────────────────┤
  │ backend-architect-dopemux.md │ system-architect-dopemux.md │ Backend is a scope parameter, not a separate      │
  │                              │                             │ role. Add --backend focus flag.                   │
  ├──────────────────────────────┼─────────────────────────────┼───────────────────────────────────────────────────┤
  │                              │                             │ Teaching style (explain vs question) is a flag,   │
  │ learning-guide-dopemux.md    │ socratic-mentor-dopemux.md  │ not a separate agent. Add --explain vs --question │
  │                              │                             │  behavior.                                        │
  └──────────────────────────────┴─────────────────────────────┴───────────────────────────────────────────────────┘

  DELETE (2 deletions):

  ┌───────────────────────────────────┬────────────────────────────────────────────────────────────────────┐
  │               File                │                             Rationale                              │
  ├───────────────────────────────────┼────────────────────────────────────────────────────────────────────┤
  │ business-panel-experts (proposed) │ MODE_Business_Panel already provides this. An agent adds nothing.  │
  ├───────────────────────────────────┼────────────────────────────────────────────────────────────────────┤
  │ context7.agent.md                 │ Tool wrapper disguised as agent. WORKFLOW_AUTOMATION handles this. │
  └───────────────────────────────────┴────────────────────────────────────────────────────────────────────┘

  ARCHIVE (move to .claude/archived-personas/) (32 files):

  ┌───────────────────────────┬───────────────────────────────────────────────────────────────────────────────────┐
  │           Files           │                                     Rationale                                     │
  ├───────────────────────────┼───────────────────────────────────────────────────────────────────────────────────┤
  │ All remaining .agent.md   │ Not dispatchable via Claude Code's Agent tool. No subagent_type mapping. Useful   │
  │ files (32)                │ as prompt templates for reference only.                                           │
  └───────────────────────────┴───────────────────────────────────────────────────────────────────────────────────┘

  Specifically archived:
  - adr-generator, critical-thinking, devils-advocate, devops-expert, gilfoyle, github-actions-expert,
  implementation-plan, janitor, mentor, meta-agentic-project-scaffold, modernization, plan, prd,
  principal-software-engineer, prompt-builder, prompt-engineer, python-mcp-expert, refine-issue,
  se-gitops-ci-specialist, se-product-manager-advisor, se-security-reviewer, se-system-architecture-reviewer,
  se-technical-writer, se-ux-ui-designer, search-ai-optimization-expert, specification, task-planner, task-researcher,
   tech-debt-remediation-plan, Ultimate-Transparent-Thinking-Beast-Mode, wg-code-alchemist, wg-code-sentinel,
  workflow-executor

  Capability Preservation Checklist

  Source Role: backend-architect-dopemux
  Destination: system-architect-dopemux + --backend flag
  Capabilities Preserved: API design, database patterns, reliability
  Capabilities Dropped: None — scope becomes a parameter
  Rationale: Backend is specialization, not separate discipline
  ────────────────────────────────────────
  Source Role: learning-guide-dopemux
  Destination: socratic-mentor-dopemux + --explain flag
  Capabilities Preserved: Progressive learning, concept explanation, ADHD teaching
  Capabilities Dropped: None — teaching style becomes a parameter
  Rationale: Teaching and questioning are modes of mentoring
  ────────────────────────────────────────
  Source Role: business-panel-experts (proposed)
  Destination: MODE_Business_Panel
  Capabilities Preserved: 9 expert personas, 3 interaction modes, synthesis
  Capabilities Dropped: None — already fully present in mode
  Rationale: Exact duplicate of mode functionality
  ────────────────────────────────────────
  Source Role: context7.agent.md
  Destination: WORKFLOW_AUTOMATION auto-routing
  Capabilities Preserved: Library doc lookup via PAL apilookup
  Capabilities Dropped: Agent persona framing
  Rationale: Auto-routing already handles this
  ────────────────────────────────────────
  Source Role: adr-generator.agent.md
  Destination: Reference: .claude/archived-personas/
  Capabilities Preserved: ADR template, numbering, structure
  Capabilities Dropped: Runtime dispatch
  Rationale: Useful as a template, not as an agent
  ────────────────────────────────────────
  Source Role: task-planner + task-researcher + implementation-plan
  Destination: general-purpose + --plan flag
  Capabilities Preserved: Planning, research, structured output
  Capabilities Dropped: Separate dispatch
  Rationale: general-purpose already handles planning tasks
  ────────────────────────────────────────
  Source Role: prompt-builder + prompt-engineer
  Destination: Reference: .claude/archived-personas/
  Capabilities Preserved: Prompt improvement methodology
  Capabilities Dropped: Runtime dispatch
  Rationale: Useful reference but not a runtime agent
  ────────────────────────────────────────
  Source Role: modernization + janitor + tech-debt-remediation
  Destination: refactoring-expert (new)
  Capabilities Preserved: Deep analysis, cleanup execution, remediation planning
  Capabilities Dropped: Three separate agents for one workflow
  Rationale: Consolidated into one refactoring agent
  ────────────────────────────────────────
  Source Role: critical-thinking + devils-advocate
  Destination: socratic-mentor + --challenge flag
  Capabilities Preserved: Assumption challenging, stress-testing
  Capabilities Dropped: Separate dispatch
  Rationale: Subsets of Socratic mentoring
  ────────────────────────────────────────
  Source Role: mentor.agent.md
  Destination: socratic-mentor-dopemux
  Capabilities Preserved: Socratic questioning, guidance
  Capabilities Dropped: Non-dopemux version
  Rationale: Superseded by dopemux-enhanced version
  ────────────────────────────────────────
  Source Role: wg-code-sentinel + wg-code-alchemist
  Destination: quality-engineer-dopemux + security-engineer-dopemux
  Capabilities Preserved: Security review, clean code review
  Capabilities Dropped: JARVIS personality, separate dispatch
  Rationale: Capabilities absorbed by existing roles
  ────────────────────────────────────────
  Source Role: gilfoyle.agent.md
  Destination: None
  Capabilities Preserved: Sardonic code review
  Capabilities Dropped: Everything
  Rationale: Personality is not a capability
  ────────────────────────────────────────
  Source Role: Ultimate-Transparent-Thinking-Beast-Mode
  Destination: Introspection mode + --ultrathink flag
  Capabilities Preserved: Transparency, maximum reasoning
  Capabilities Dropped: 29KB of theatrical framing
  Rationale: Already available via flag combination
  ────────────────────────────────────────
  Source Role: se-product-manager-advisor
  Destination: requirements-analyst (new)
  Capabilities Preserved: Product management guidance, requirements discovery
  Capabilities Dropped: Separate dispatch
  Rationale: Absorbed into requirements-analyst
  ────────────────────────────────────────
  Source Role: se-ux-ui-designer
  Destination: frontend-architect-dopemux + --ux flag
  Capabilities Preserved: UX research, journey mapping
  Capabilities Dropped: Separate dispatch
  Rationale: UX is a frontend concern
  ────────────────────────────────────────
  Source Role: devops-expert + se-gitops-ci + github-actions-expert
  Destination: devops-architect-dopemux
  Capabilities Preserved: CI/CD lifecycle, failure triage, GH Actions security
  Capabilities Dropped: Separate dispatch
  Rationale: Specializations absorbed into one DevOps role
  ────────────────────────────────────────
  Source Role: python-mcp-expert
  Destination: python-expert-dopemux
  Capabilities Preserved: MCP server development
  Capabilities Dropped: Separate dispatch
  Rationale: Python MCP development is Python development
  ────────────────────────────────────────
  Source Role: search-ai-optimization-expert
  Destination: Reference: .claude/archived-personas/
  Capabilities Preserved: SEO/AEO/GEO knowledge
  Capabilities Dropped: Runtime dispatch
  Rationale: Niche domain reference, not a runtime role
  ────────────────────────────────────────
  Source Role: se-security-reviewer
  Destination: security-engineer-dopemux
  Capabilities Preserved: OWASP review, AI security threats
  Capabilities Dropped: Non-dopemux version
  Rationale: Superseded by dopemux-enhanced version
  ────────────────────────────────────────
  Source Role: se-system-architecture-reviewer
  Destination: system-architect-dopemux
  Capabilities Preserved: Well-Architected review
  Capabilities Dropped: Non-dopemux version
  Rationale: Superseded by dopemux-enhanced version
  ────────────────────────────────────────
  Source Role: se-technical-writer
  Destination: technical-writer-dopemux
  Capabilities Preserved: Audience adaptation, style management
  Capabilities Dropped: Non-dopemux version
  Rationale: Superseded by dopemux-enhanced version

  Phase 0 Safe Actions

  These can be done immediately with zero risk:

  1. Create .claude/archived-personas/ directory
  2. Move all 32 .agent.md files (excluding context7.agent.md which gets deleted) to archived-personas/
  3. Delete context7.agent.md — pure tool wrapper, zero unique capability
  4. Move MCP_*.md files from ~/.claude/ to ~/.claude/reference/ and remove from always-loaded includes
  5. Move BUSINESS_PANEL_EXAMPLES.md and BUSINESS_SYMBOLS.md to ~/.claude/reference/
  6. Move RESEARCH_CONFIG.md to ~/.claude/reference/

  Do Not Do Yet

  1. Do NOT merge backend-architect into system-architect until the system-architect persona is rewritten to absorb
  backend scope
  2. Do NOT merge learning-guide into socratic-mentor until mentor persona supports --explain mode
  3. Do NOT create the 4 new dopemux personas until the dopemux persona template is stabilized and the generator
  verified
  4. Do NOT compress CLAUDE.md + RULES.md until the reference-loading mechanism is confirmed working (modes/MCP docs
  need to load on demand)
  5. Do NOT delete any infrastructure agent code in services/agents/ — these are real Python implementations with a
  different lifecycle
  6. Do NOT remove PRINCIPLES.md until its content is verified merged into CLAUDE.md

  Immediate Next Steps

  1. IMMEDIATE: Archive the 32 .agent.md files and delete context7.agent.md. This removes 32 sources of confusion and
  has zero functional impact since none are dispatchable.
  2. NEXT: Move 6 reference docs (MCP_*.md, BUSINESS_*, RESEARCH_CONFIG) out of always-loaded context. This recovers
  ~22K tokens (54% reduction) with zero behavioral change — the information is still accessible, just not pre-loaded.
  3. NEXT: Compress CLAUDE.md and RULES.md — eliminate the 5.8K tokens of duplication and reduce verbose examples to
  terse rules.
  4. NEXT: Create the 4 missing dopemux personas (deep-research-agent, requirements-analyst, root-cause-analyst,
  refactoring-expert) to complete the canonical 15-agent roster.

  ---
  NEXT: Archive the 32 undispatchable .agent.md files to .claude/archived-personas/ — this is the single
  highest-impact zero-risk action that immediately reduces roster confusion from 47 entities to 15.
