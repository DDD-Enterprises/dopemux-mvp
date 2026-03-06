---
title: Dopemux Public Release Master Plan
id: PM-DOPMUX-PUBLIC-RELEASE-MASTER-PLAN
type: explanation
status: draft
owner: pm-plane
author: dopemux-pm
date: 2026-03-06
updated: 2026-03-06
last_review: '2026-03-06'
next_review: '2026-06-04'
prelude: Dopemux Public Release Master Plan (explanation) for dopemux documentation
  and developer workflows.
---
Dopemux Public Release Master Plan

Document Set

This workspace consolidates the planning output into four executable artifacts:
    1.    Master Strategy
    2.    Product Requirements Document (PRD)
    3.    Engineering Roadmap
    4.    Go-To-Market (GTM) and Launch Plan

⸻

1. Master Strategy

1.1 Product Identity

Dopemux is an AI devtools platform for understanding codebases, executing structured work, recovering context, and finishing projects.

Public category

AI Devtools

Deeper category

AI development runtime

Product thesis

Developers do not primarily need more raw generation. They need systems that reduce context loss, coordinate execution, and help them finish work.

1.2 Strategic wedge

The public entry wedge is:
    •    Repo intelligence via dopemux analyze
    •    followed by grounded Q&A via dopemux ask
    •    then structured execution via dopemux plan and dopemux run

1.3 Product pillars
    •    Understand: repo analysis, architecture artifacts, grounded answers
    •    Execute: supervised planning, dopeTask, verification loops
    •    Remember: recaps, blockers, replay, recent work state
    •    Stay on Track: focus-safe output, interruption recovery, unfinished work visibility
    •    Coordinate: PM-plane integration, stale work surfacing, project continuation

1.4 Open-core strategy

OSS core
    •    CLI
    •    repo analyzer
    •    grounded Q&A
    •    dopeTask execution engine
    •    supervisor core
    •    local memory basics
    •    PM/focus preview surfaces
    •    plugin SDK

Cloud later
    •    shared team memory
    •    hosted project/repo context
    •    team coordination
    •    hosted indexing
    •    governance and analytics

1.5 Product principles
    •    Opinionated by default, infinitely flexible underneath
    •    Determinism where users need trust
    •    ADHD-aware without becoming therapy software
    •    Memory is a system, not a dumping ground
    •    PM is part of execution, not an attachment
    •    Public docs must match actual behavior

⸻

2. Product Requirements Document (PRD)

2.1 Target users

Primary
    •    AI tooling power users
    •    Open-source maintainers
    •    Neurodivergent / chaotic-workflow developers

Secondary
    •    Startup engineering teams
    •    Infrastructure-heavy teams
    •    Internal platform teams

2.2 Jobs to be done
    1.    Enter or re-enter a codebase fast
    2.    Ask grounded questions about the system
    3.    Turn a goal into a supervised plan
    4.    Resume after interruption
    5.    Keep unfinished work from disappearing
    6.    Tie planning to actual execution

2.3 Core CLI surface

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

2.4 Public dopeXXX naming
    •    dopeExtract
    •    dopeContext
    •    dopeMemory
    •    dopeGraph
    •    dopeTask
    •    dopeRoute
    •    dopePM
    •    dopeFocus
    •    dopeConsole
    •    dopePlugin

2.5 Canonical default workflow

analyze -> ask -> plan -> run -> verify -> recap

2.6 Release bands

v0.1 Public Preview
    •    dopemux analyze
    •    dopemux ask
    •    basic dopemux plan
    •    basic dopemux run
    •    recap/search basics
    •    route status basics
    •    plugin skeleton
    •    PM commands present and clearly early-stage

v0.2 Structured Execution
    •    stronger supervisor modes
    •    better dopeTask loops
    •    verification/report surfaces
    •    issue-resolution links
    •    stronger PM linkage

v0.5 Platform Preview
    •    plugin SDK maturity
    •    tmux cockpit alpha
    •    unfinished-work views
    •    better project continuation flows
    •    optional conversation-RAG plugin path

v1.0 Stable Core
    •    wedge loop rock-solid
    •    stable plugin system
    •    proven memory boundaries
    •    useful PM flow
    •    usable cockpit
    •    polished docs and demos

⸻

3. Engineering Roadmap

3.1 Engineering premise

This is a convergence and productization effort, not a greenfield build. The strongest existing systems are wrapped, unified, renamed, and hardened behind a coherent product shell.

3.2 Top-level monorepo shape

src/dopemux/
  cli/
  core/
  supervisor/
  task/
  extract/
  context/
  memory/
  graph/
  route/
  pm/
  focus/
  console/
  plugins/
  providers/
  adapters/
  schemas/
  utils/
plugins/
docs/
examples/
tests/

3.3 Main engineering workstreams

Product shell
    •    package layout
    •    CLI hierarchy
    •    install profiles
    •    docs/examples

Runtime convergence
    •    supervisor split
    •    dopeTask integration
    •    provider/tool selection layer
    •    verification and recovery loops

Knowledge convergence
    •    dopeExtract
    •    dopeContext
    •    dopeMemory
    •    dopeGraph
    •    shared scoping and grounding rules

PM/focus convergence
    •    PM sync facade
    •    stale and unfinished work flows
    •    focus-safe output shaping
    •    interruption recovery integration

3.4 Main missing seams
    •    supervisor split
    •    deep CLI tool integrations
    •    PM-plane / orchestration wiring hardening
    •    public-facing productization and abstraction

3.5 90-day milestone sequence

M1 Product Shell Ready
    •    package + CLI shell + docs skeleton + demo repo + naming layer

M2 Analyzer Wedge Ready
    •    dopemux analyze stable enough for demo and launch

M3 Query Loop Ready
    •    dopemux ask works after analyze with grounded answers

M4 Structured Execution Ready
    •    basic plan/run visible and persisted

M5 Recovery/PM/Focus Included
    •    recap exists, PM surfaces visible, maturity labels honest

M6 Launch Ready
    •    repo, site, demos, waitlist, changelog, and release process complete

3.6 Key explicit deferrals
    •    cloud product beyond waitlist
    •    enterprise features
    •    full PM automation
    •    cockpit as a launch dependency
    •    every deep CLI integration path
    •    deep internal refactors that do not improve wedge or launch quality

⸻

4. GTM and Launch Plan

4.1 Launch thesis

Dopemux should launch as an OSS-first, proof-led alpha with the repo analyzer as the hero demo.

4.2 Launch message hierarchy

Hero

Understand any codebase faster.

Subhero

Dopemux scans your repo, generates architecture and dependency artifacts, and lets you ask grounded questions using extracted system context.

Deeper message

It then helps you turn goals into structured plans and recover context when work gets interrupted.

4.3 Hero demo sequence

pip install dopemux
dopemux analyze
dopemux ask "where is authentication handled?"
dopemux plan "fix the failing tests"

4.4 Launch format

Mini launch week
    •    Day 1: Repo analyzer
    •    Day 2: Grounded Q&A
    •    Day 3: Structured execution
    •    Day 4: Memory and recovery
    •    Day 5: PM and focus story

4.5 Primary channels
    •    GitHub
    •    Hacker News
    •    X / Twitter
    •    Reddit
    •    Blog / docs site

4.6 Website / repo CTA order
    1.    Install Dopemux
    2.    View on GitHub
    3.    Join cloud waitlist

4.7 Cloud waitlist promise

Dopemux Cloud is coming with:
    •    shared team memory
    •    hosted project and repo context
    •    team coordination across unfinished work

4.8 90-day GTM outputs
    •    launch-quality README
    •    quickstart
    •    landing page
    •    20-second demo
    •    1-minute demo
    •    launch week post set
    •    waitlist form + segmentation
    •    discussions and contribution scaffolding

⸻

5. Immediate Next Actions

5.1 Convert planning into execution artifacts

Create next:
    1.    docs/strategy/Dopemux_Master_Strategy.md
    2.    docs/product/Dopemux_PRD.md
    3.    docs/roadmap/Dopemux_Engineering_Roadmap.md
    4.    docs/gtm/Dopemux_Launch_and_GTM.md

5.2 First operating sequence
    1.    Finalize product shell and package structure
    2.    Lock dopeXXX naming and public abstraction map
    3.    Stabilize dopemux analyze
    4.    Stabilize dopemux ask
    5.    Finish supervisor split enough for visible plan/run
    6.    Build README, quickstart, demo repo, and launch assets
    7.    Launch ambitious alpha with waitlist live

5.3 Core rule

Every week should produce at least one of the following:
    •    user-visible capability
    •    proof artifact
    •    launch asset
    •    release hardening

⸻

6. Operating Notes

Release posture

Ambitious alpha

Main CTA

Install Dopemux

Public wedge

dopemux analyze

Product order of revelation

Understand -> Ask -> Plan -> Run -> Recover -> Coordinate

Core constitutional constraints
    •    determinism where trust matters
    •    Top-3 default outputs where overload matters
    •    clean dopeMemory / dopeContext / dopeGraph boundaries
    •    local-first usefulness
    •    honest maturity labelingx
