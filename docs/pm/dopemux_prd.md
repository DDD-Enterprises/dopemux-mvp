---
title: Dopemux Product Requirements Document
id: PM-DOPMUX-PRD
type: reference
status: draft
owner: pm-plane
author: dopemux-pm
date: 2026-03-06
updated: 2026-03-06
---

# Dopemux PRD

## Document status

Draft v0.1

## Purpose

This document defines the product requirements for Dopemux as a public product. It translates the strategic direction into concrete product surfaces, workflows, user experiences, command hierarchies, release bands, and UX rules. It is intended to guide implementation, documentation, release scoping, and launch preparation.

This PRD inherits the decisions in **Dopemux Master Strategy** and should not contradict that document.

---

# 1. Product Summary

Dopemux is an **AI devtools platform** that helps developers:

- understand codebases
- ask grounded questions about systems
- execute structured work through supervised flows
- recover project context after interruption
- keep unfinished work visible
- connect code work to PM state

At launch, the primary wedge is:

**Analyze a repository, generate architecture artifacts, and ask grounded questions about the system.**

Dopemux then expands into:

- supervised planning
- deterministic task execution
- recap and recovery
- PM-plane linkage
- ADHD-aware workflow shaping

---

# 2. Product Goals

## 2.1 Primary goals

1. Reduce codebase orientation time.
2. Provide grounded answers about repository structure and behavior.
3. Turn developer goals into visible, recoverable, supervised work.
4. Reduce interruption cost and restart friction.
5. Surface unfinished work without creating overload.
6. Build a clear progression from OSS wedge to cloud/team value later.

## 2.2 Non-goals for v0.1

Dopemux v0.1 is not trying to be:

- a full project management suite
- a full enterprise collaboration platform
- a replacement for every IDE
- a fully autonomous agent swarm product
- a polished GUI-first app

---

# 3. Target Users

## 3.1 Primary personas

### Persona A: AI tooling power user

Already uses multiple AI tools and wants a more coherent workflow.

Needs:

- less tool fragmentation
- better context continuity
- more reliable execution
- stronger repo grounding

### Persona B: Open-source maintainer / repo owner

Needs better system visibility and grounded answers for self and contributors.

Needs:

- repo understanding
- architecture recall
- contributor guidance
- design-intent recovery

### Persona C: Neurodivergent / chaotic-workflow developer

Experiences high interruption cost and unfinished-work accumulation.

Needs:

- visible next steps
- restart help
- low-overload summaries
- unfinished-work resurfacing

## 3.2 Secondary personas

### Persona D: Small engineering team lead

Needs team memory and continuity across work.

### Persona E: Infrastructure-heavy engineer

Needs stronger architecture and dependency insight, plus structured execution.

---

# 4. Jobs to Be Done

## JTBD 1: Understand a repo quickly

When I am entering or re-entering a repository, I want Dopemux to build a useful system map so I can understand the codebase faster.

## JTBD 2: Ask grounded questions

When I need to know where something lives or how something works, I want answers grounded in extracted artifacts and retrieval layers so I can trust the result.

## JTBD 3: Turn intent into a plan

When I want to fix, refactor, or implement something, I want Dopemux to create a visible and recoverable plan so I can execute with structure.

## JTBD 4: Resume work after interruption

When I come back later, I want a recap of what happened, blockers, and likely next steps so I can resume quickly.

## JTBD 5: Keep active work from disappearing

When I have several work threads, I want unfinished work surfaced in a bounded way so I stop silently abandoning important tasks.

## JTBD 6: Connect PM state to code work

When work is tracked in a PM system, I want it linked to plans and execution so planning and actual work are connected.

---

# 5. Product Structure

Dopemux should be publicly understood through five pillars.

## 5.1 Understand

The repo intelligence layer.

Capabilities:

- analyze repository structure
- generate architecture documentation
- generate dependency maps
- generate system overviews
- optionally generate API surface artifacts

## 5.2 Execute

The supervised planning and execution layer.

Capabilities:

- plan generation
- dopeTask execution
- verification hooks
- visible workflow progress
- dry-run and recovery support

## 5.3 Remember

The memory and continuity layer.

Capabilities:

- recap
- replay
- recent blockers
- recent decisions
- resume cues

## 5.4 Stay on Track

The ADHD-aware workflow layer.

Capabilities:

- Top-3 summaries
- interruption recovery
- bounded surfacing
- stale-work visibility
- focus-safe output modes

## 5.5 Coordinate

The PM-plane and continuation layer.

Capabilities:

- PM status
- sync state
- project/task status
- stale work view
- continuation path into active work

---

# 6. Product Surfaces

## 6.1 Primary surface: CLI

The CLI is the main product surface for v0.x.

The CLI must be:

- discoverable
- scriptable
- composable
- understandable in help output
- useful in both guided and advanced workflows

## 6.2 Secondary surface: Generated artifacts

A major part of the wedge is artifact generation.

Examples:

- `architecture.md`
- `system-overview.md`
- `dependency-map.md`
- machine-readable outputs for future workflows

## 6.3 Secondary surface: tmux cockpit

The tmux-based operator surface is a future-facing but strategically important product surface.

At launch it may remain alpha or preview.

## 6.4 Future surface: Cloud waitlist only

No functional cloud product is required at launch. The cloud surface at launch is informational and demand-capturing only.

---

# 7. Command Hierarchy

## 7.1 Top-level commands

```bash
dopemux init
dopemux status
dopemux doctor

dopemux analyze
dopemux ask
dopemux plan
dopemux run

dopemux memory ...
dopemux context ...
dopemux graph ...
dopemux pm ...
dopemux route ...
dopemux plugin ...
dopemux console ...
```

## 7.2 Command priorities

### Tier 1 commands

These are the most important launch commands:

- `dopemux analyze`
- `dopemux ask`
- `dopemux plan`
- `dopemux run`

### Tier 2 commands

- `dopemux memory recap`
- `dopemux memory search`
- `dopemux pm status`
- `dopemux pm stale`
- `dopemux route status`
- `dopemux plugin list`

### Tier 3 commands

- deeper graph/context interfaces
- console operations
- plugin inspection/debugging
- advanced execution and policy flags

---

# 8. Canonical User Flows

## 8.1 First-run flow

1. Install Dopemux.
2. Run `dopemux init`.
3. Run `dopemux analyze`.
4. Review generated outputs.
5. Run `dopemux ask`.
6. Optionally continue into `dopemux plan`.

### First-run success criteria

A new user should understand within minutes:

- what Dopemux does
- what artifacts it creates
- why `ask` matters after `analyze`
- that it supports structured execution later

## 8.2 Daily work flow

1. Start in a repository.
2. Run `dopemux status` or `dopemux memory recap`.
3. Ask questions or inspect current project state.
4. Create or continue a plan.
5. Execute via `run`.
6. Verify and persist state.

## 8.3 Interruption recovery flow

1. Return to project.
2. Run recap or status.
3. Review Top-3 recent items.
4. Follow suggested next step or continue a plan.

## 8.4 PM continuation flow

1. Inspect PM status.
2. Review stale or unfinished work.
3. Select a project/task to continue.
4. Load related memory and/or plan state.
5. Continue execution.

---

# 9. Default Workflow Model

## 9.1 Canonical loop

`analyze -> ask -> plan -> run -> verify -> recap`

This is the opinionated default path.

## 9.2 Why this loop matters

This loop is the product. Everything else is either support, acceleration, or expansion.

## 9.3 User expectation

Users should be able to stay within this loop for a meaningful amount of work without feeling lost or having to stitch together external process glue.

---

# 10. Modes and Interaction Styles

## 10.1 Default mode

The standard user mode.

Behavior:

- visible workflow progression
- bounded context output
- practical suggestions
- verifiable next steps

## 10.2 Focus mode

Designed for low-overload execution.

Behavior:

- Top-3 summaries only where possible
- current task + blocker priority
- minimal extra suggestions
- less noisy output

## 10.3 Fast mode

Designed for experienced users.

Behavior:

- lower confirmation friction
- shorter output
- faster progression through common operations

## 10.4 Strict mode

Designed for audit-grade or high-trust workflows.

Behavior:

- explicit plan emphasis
- more visible provenance and verification
- stronger evidence/proof output
- less tolerance for implicit behavior

---

# 11. Analyze Experience

## 11.1 Core user promise

Run a single command and quickly get a more usable mental model of the codebase.

## 11.2 Required outputs

At minimum, `dopemux analyze` should produce launch-grade outputs such as:

- architecture summary
- system overview
- dependency map

Optional but desirable:

- API surface map
- machine-readable structured graph or summary outputs

## 11.3 Analyze UX requirements

The command should:

- show progress
- fail clearly
- produce visible and legible artifacts
- feel deterministic enough to trust
- complete without needing cloud services

## 11.4 Analyze quality requirements

Outputs must be:

- understandable by humans
- useful as grounding for later questions
- stable enough to be demoed and documented

---

# 12. Ask Experience

## 12.1 Core user promise

Ask a useful question about the codebase and receive a grounded answer using extracted artifacts and context layers.

## 12.2 Ask behavior

`dopemux ask` should:

- use `analyze` outputs when available
- draw from retrieval and memory layers when relevant
- prefer grounded answers over broad speculation
- indicate source grounding or artifact basis
- suggest a next step when appropriate

## 12.3 Ask UX rules

- concise by default
- expandable by request
- no giant unstructured walls of text
- should not pretend certainty when context is weak

## 12.4 Launch expectation

At launch, `ask` must feel meaningfully better than generic chat in the same repo context.

---

# 13. Plan Experience

## 13.1 Core user promise

Turn a developer goal into a visible, structured plan.

## 13.2 Plan behavior

`dopemux plan` should:

- take a plain-language goal
- inspect relevant project and repo context
- produce a visible execution path
- support dry-run or approval-oriented workflows in stricter modes

## 13.3 Plan UX rules

- visible steps
- bounded length by default
- restartable and persistable
- understandable without internal architecture knowledge

## 13.4 Launch requirement

At launch, `plan` does not need every advanced policy or deep integration path to be perfect, but it must visibly demonstrate that Dopemux is a structured workflow tool and not merely an analyzer.

---

# 14. Run Experience

## 14.1 Core user promise

Execute a plan or structured task through a visible and controlled runtime path.

## 14.2 Run behavior

`dopemux run` should:

- execute planned work via dopeTask
- expose dry-run when appropriate
- show progress and status
- record enough state for recap/recovery
- invoke verification where available

## 14.3 Run UX rules

- progress must be visible
- failures must be legible
- users should know whether a run completed, failed, or is resumable
- the command should not feel like an opaque black box

---

# 15. Memory Experience

## 15.1 Core user promise

Dopemux helps users recover what happened, what is blocked, and what to do next.

## 15.2 Memory core actions

- recap
- replay
- search
- blocker inspection
- issue-resolution linking over time

## 15.3 Memory UX rules

- Top-3 by default where overload risk is high
- stable ordering where trust matters
- short by default, expandable on demand
- recent state must be more important than indiscriminate log volume

## 15.4 Launch minimum

At launch, memory must at least support:

- recent recap
- replay basics
- enough persisted state for continuation

---

# 16. PM Experience

## 16.1 Core user promise

Dopemux helps keep projects and unfinished work connected to active execution.

## 16.2 PM actions

- inspect PM state
- view project/task status
- view stale work
- continue a project or task from PM-linked context

## 16.3 PM launch rule

PM is included in the public product, but maturity must be honest.

At launch, PM should feel like a real but early-stage continuation layer, not a complete PM operating system.

## 16.4 PM UX rules

- always show adapter/sync health when relevant
- degrade gracefully if a PM backend is unavailable
- focus on continuity and status more than administrative breadth

---

# 17. Focus and ADHD-Aware UX

## 17.1 Core user promise

Dopemux reduces restart cost and cognitive overload in chaotic real-world workflows.

## 17.2 UX patterns

- Top-3 summaries
- visible next step
- bounded output
- stale-work resurfacing without spam
- continuation-first UX

## 17.3 Public framing rule

The product should present these as workflow and execution benefits, not as vague lifestyle branding.

---

# 18. Plugin Experience

## 18.1 Core user promise

Dopemux ships with strong defaults, then allows advanced users to extend the system.

## 18.2 Plugin categories

- analyzers
- providers
- PM adapters
- tool adapters
- workflow packs
- console panes
- retrieval/memory extensions

## 18.3 Launch expectation

At launch, plugins do not need to be fully mature, but the public extensibility direction should be visible.

---

# 19. tmux Cockpit Experience

## 19.1 Core user promise

A terminal-native operator surface for supervised AI development workflows.

## 19.2 Expected capabilities over time

- supervisor state visibility
- active plan/task queue
- provider/worker state
- memory/context pane
- PM status pane
- log/output pane

## 19.3 Launch posture

Cockpit may remain alpha or roadmap-near in the first public release, but it should be framed as a serious strategic surface rather than a side experiment.

---

# 20. Public Naming Requirements

## 20.1 Public naming family

Dopemux public architecture should use the dopeXXX naming family:

- dopeExtract
- dopeContext
- dopeMemory
- dopeGraph
- dopeTask
- dopeRoute
- dopePM
- dopeFocus
- dopeConsole
- dopePlugin

## 20.2 Naming rule

Public docs and UX should prefer the dopeXXX family rather than exposing legacy names too early.

---

# 21. Release Bands

## 21.1 v0.1 Public Preview

Must include:

- `dopemux analyze`
- `dopemux ask`
- basic `dopemux plan`
- basic `dopemux run`
- recap basics
- route status basics
- plugin skeleton
- PM commands visible and clearly early-stage

## 21.2 v0.2 Structured Execution

Should add:

- stronger supervisor behavior
- deeper dopeTask flow visibility
- better verification and reporting
- stronger recap and continuation quality
- stronger PM linkage

## 21.3 v0.5 Platform Preview

Should add:

- plugin maturity
- tmux cockpit alpha
- stale and unfinished-work improvements
- optional conversation-RAG style plugin direction

## 21.4 v1.0 Stable Core

Should mean:

- wedge loop is trustworthy
- docs and demos are polished
- plugin system is credible
- memory and PM boundaries hold
- core retention loops are real

---

# 22. Success Metrics

## 22.1 Activation metrics

- install success rate
- analyze completion rate
- ask-after-analyze conversion

## 22.2 Usage metrics

- plan/run usage
- recap usage
- PM status/stale usage
- repeat weekly active usage

## 22.3 Qualitative success

Users should describe Dopemux as:

- useful quickly
- clearer than generic AI tools
- more structured than a copilot
- helpful for re-entering work
- valuable for understanding systems

---

# 23. Product Constraints

The following are product constraints, not optional preferences:

- local-first usefulness is required
- install-to-value must be fast
- overload must be controlled where possible
- public docs must match actual behavior
- PM inclusion must be honest about maturity
- the default workflow must remain understandable
- advanced flexibility must not pollute the first-run experience

---

# 24. Open Questions for Future Revision

These questions may be revised later but should not block the current PRD:

- exact shape of cockpit v0.x vs v1.0
- exact cloud alpha feature boundary
- which PM integrations graduate from preview to stable first
- how aggressively the plugin ecosystem is opened at each milestone
- when conversation-RAG style extensions become productized

---

# 25. Summary

Dopemux v0.1 should launch as a repo-intelligence-first alpha that proves value through:

1. analysis
2. grounded questions
3. visible movement into supervised execution
4. recap and continuity support
5. honest PM and focus-aware inclusion

That sequence defines the launch product.
