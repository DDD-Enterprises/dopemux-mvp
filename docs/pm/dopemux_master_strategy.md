---
title: Dopemux Master Strategy
id: PM-DOPMUX-MASTER-STRATEGY
type: explanation
status: draft
owner: pm-plane
author: dopemux-pm
date: 2026-03-06
updated: 2026-03-06
---

# Dopemux Master Strategy

## Document status
Draft v0.1

## Purpose
This document defines the strategic foundation for Dopemux as a public product. It is the top-level decision document for product direction, positioning, release posture, business model, and operating philosophy. It is not the implementation roadmap and it is not the detailed PRD. It exists to answer the higher-order questions:

- What is Dopemux?
- Who is it for?
- What problem does it solve better than competing tools?
- What is the public wedge?
- What is open source versus paid?
- What should be built, shipped, and marketed first?
- What principles should constrain future decisions?

---

# 1. Executive Summary

Dopemux is an **AI devtools platform** designed to help developers understand codebases, execute structured work, recover context, and finish projects.

Publicly, Dopemux should launch with a sharp and understandable wedge:

**Analyze a repository, generate grounded architecture artifacts, and ask useful questions about the system.**

Underneath that wedge, Dopemux is strategically larger. It combines:

- repo intelligence and extraction
- grounded retrieval and codebase context
- supervised planning and deterministic execution
- project memory and interruption recovery
- PM-plane awareness and unfinished-work visibility
- ADHD-aware workflow shaping for real-world development

Dopemux should be run as an **open-core developer infrastructure product**:

- a strong local-first OSS core
- a later hosted cloud layer for team memory and coordination
- enterprise features only after the core wedge, retention loop, and cloud demand are proven

The first release posture is an **ambitious alpha**.

That means Dopemux should tell a meaningful story, expose a visible roadmap, and deliver real product value, while clearly labeling maturity and limitations. It should not pretend every subsystem is equally production-ready.

---

# 2. Product Identity

## 2.1 Product name
**Dopemux**

Usage conventions:
- prose and product pages: **Dopemux**
- CLI/package/repo/config names: `dopemux`

## 2.2 Public category
**AI Devtools**

## 2.3 Deeper category
**AI development runtime**

This split is intentional.

The public category should be legible and fast to understand. “AI devtools” is a better top-line phrase for discovery, launch pages, and social posts.

The deeper category is strategically important because Dopemux is more than a set of utilities. It is a runtime layer coordinating context, execution, memory, and workflow. That deeper positioning should appear in architecture docs, roadmap docs, and later-stage messaging once users understand the wedge.

## 2.4 Product one-line descriptions
Primary:

**Dopemux is AI devtools for understanding codebases, executing structured work, recovering context, and finishing projects.**

Short form:

**Analyze repos, ask grounded questions, execute structured plans.**

Differentiated form:

**Structured AI workflows with project memory and interruption recovery.**

---

# 3. Core Strategic Thesis

Modern AI-assisted development has four major failure modes:

1. **Context loss**
2. **Workflow drift**
3. **Agent unreliability**
4. **Unfinished-work accumulation**

Most existing AI developer tools optimize for output generation. They do not optimize deeply for:

- system understanding
- continuity of work over time
- visible task structure
- interruption recovery
- unfinished-project management
- planning-to-execution coherence

Dopemux should win by focusing on these neglected layers.

The strategic thesis is:

**Developers do not mainly need more raw generation. They need systems that reduce context loss, coordinate execution, and help them finish work.**

This is the center of the entire product strategy.

---

# 4. Product Vision

## 4.1 Long-term vision
Dopemux becomes the execution layer between:

- developers
- AI agents and model providers
- codebase truth and retrieval
- project memory
- PM systems
- and structured task execution

In long-term form, Dopemux is the place where:

- repo understanding
- context retrieval
- planning
- execution
- verification
- recap
- and continuation

all converge.

## 4.2 Near-term vision
In the near term, Dopemux should feel like this:

1. You install it quickly.
2. You point it at a repository.
3. It builds a better mental model of the system than the repo has on its own.
4. You ask grounded questions.
5. You see a clear path from “understanding” to “doing.”
6. You come back later and Dopemux helps you resume without rebuilding context from scratch.

That is enough to be meaningful.

---

# 5. Strategic Wedge

## 5.1 Public wedge
The public wedge is:

**Repo intelligence via `dopemux analyze`**

This should be the top-of-funnel feature and the hero of the first release.

## 5.2 Why this wedge is correct
It is the right wedge because it is:

- instantly understandable
- visually demoable
- useful even without the full platform
- naturally connected to grounded Q&A
- naturally connected to structured execution later
- less dependent on the full maturity of PM, cloud, and multi-agent systems

## 5.3 Immediate second step
After `dopemux analyze`, the second sticky step is:

**Grounded Q&A via `dopemux ask`**

This turns static analysis artifacts into a living product loop.

## 5.4 Third-step expansion
The third expansion step is:

**Structured execution via `dopemux plan` and `dopemux run`**

This proves Dopemux is not “just another repo analyzer.”

---

# 6. Product Pillars

Dopemux should be publicly explained through five pillars.

## 6.1 Understand
Help users build a fast and accurate mental model of a repository.

Capabilities:
- architecture maps
- system overviews
- dependency maps
- API surface maps
- generated documentation
- grounded codebase questions

## 6.2 Execute
Help users move from goals to supervised, visible work.

Capabilities:
- supervised planning
- dopeTask execution
- verification loops
- visible progress and failure states
- resumable execution

## 6.3 Remember
Help users preserve and recover project context over time.

Capabilities:
- recap
- replay
- blockers
- decisions
- recent actions
- next-step suggestions

## 6.4 Stay on Track
Help users avoid cognitive overload and drift.

Capabilities:
- Top-3 recaps
- interruption recovery
- focus-safe output shaping
- unfinished-work visibility
- project continuation cues

## 6.5 Coordinate
Connect work state to planning systems and project-level structures.

Capabilities:
- PM sync
- stale work views
- project/task status
- task-to-plan linkage
- cross-project continuation support

---

# 7. Target Users

## 7.1 Primary users

### AI tooling power users
These users already patch together multiple AI tools and are frustrated by fragmentation.

Their pains:
- tool chaos
- weak continuity
- no shared context layer
- unreliable agent execution
- repeated context rebuild cost

### Open-source maintainers and repo owners
These users need better codebase understanding, contributor support, and architecture recall.

Their pains:
- poor documentation reality
- scattered design intent
- recurring onboarding questions
- weak system visibility

### Neurodivergent and chaotic-workflow developers
These users are especially harmed by interruption cost and unfinished-work accumulation.

Their pains:
- project drift
- too many active threads
- high restart cost
- overload from too much context
- difficulty finishing work consistently

## 7.2 Secondary users

### Small engineering teams
Need shared memory and coordinated execution.

### Startup technical leads
Need codebase understanding and execution discipline with small teams.

### Infrastructure-heavy teams
Need stronger system mapping and workflow continuity.

These users become more important after cloud and shared coordination layers mature.

---

# 8. Jobs to Be Done

## JTBD 1: Enter or re-enter a codebase fast
When I enter a repository, I want Dopemux to map the system and explain it so I stop wasting time orienting myself.

## JTBD 2: Ask grounded system questions
When I need to understand how a system works, I want grounded answers tied to code, docs, and extracted artifacts so I am not relying on hallucinated AI output.

## JTBD 3: Turn goals into structured execution
When I have a task, fix, or initiative, I want a visible plan and controlled execution path so work becomes inspectable and recoverable.

## JTBD 4: Resume interrupted work
When I return after interruption, I want the last steps, blockers, and next moves surfaced clearly so restart cost stays low.

## JTBD 5: Keep unfinished work from disappearing
When I have too many active efforts, I want stale and unfinished threads surfaced without overload so important work does not quietly die.

## JTBD 6: Connect planning to actual code work
When tasks exist in a PM system, I want them linked to plans, execution, and current project state so planning and delivery are not separate universes.

---

# 9. Product Differentiation

Dopemux does not win because any individual subsystem is unique.

It wins because of the **combination**:

- repo truth extraction
- grounded retrieval
- supervised planning
- deterministic task execution
- project memory
- interruption recovery
- unfinished-work visibility
- PM-plane awareness
- terminal-native operator UX

Many tools do one or two of these.
Very few combine them into a coherent developer workflow system.

## 9.1 What Dopemux is not
Dopemux is not:
- just an LLM wrapper
- just a prompt library
- just a coding assistant
- just a repo analyzer
- just a memory tool
- just a PM integration layer

## 9.2 What Dopemux is
Dopemux is:

**A structured AI developer workflow system for understanding systems, executing work, recovering context, and finishing projects.**

---

# 10. Product Principles

These principles should constrain all future decisions.

## 10.1 Opinionated by default, infinitely flexible underneath
The default path should be structured and easy to understand.

Advanced users should be able to override:
- providers
- workflows
- plugins
- plans
- adapters
- execution policies

The default path should not require users to design their own system before they get value.

## 10.2 Determinism where users need trust
Where trust matters, Dopemux should bias toward:
- stable ordering
- stable recap behavior
- visible verification
- repeatable execution paths
- explicit grounding

## 10.3 ADHD-aware without becoming therapy software
The ADHD angle is strategically important, but it should be expressed as performance and execution value:
- reduced restart cost
- less overload
- visible next steps
- unfinished-work tracking
- interruption recovery

The product should not sound sentimental or medicalized.

## 10.4 Memory is a system, not a dumping ground
Memory must remain structured and bounded.
Different layers should retain distinct responsibilities.

## 10.5 PM is part of execution, not an afterthought
Planning, work state, and execution should converge. PM should not feel like a completely separate admin universe.

## 10.6 Public docs must match actual behavior
No aspirational lies. Public trust depends on accurate claims and reproducible workflows.

---

# 11. Public Architecture Language

Internally, Dopemux may wrap or converge older systems and names. Publicly, the architecture should use the dopeXXX naming family.

## 11.1 Public internal family
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

## 11.2 Public explanation rule
Public-facing docs, site copy, and launch assets should prefer this naming system over exposing legacy internal service names immediately.

Deep technical docs may explain the mapping later.

---

# 12. Open-Core Strategy

## 12.1 OSS core includes
- CLI
- repo analyzer
- grounded Q&A
- dopeTask execution engine
- supervisor core
- local memory basics
- PM/focus preview surfaces
- plugin SDK
- examples, docs, demo repo

## 12.2 Cloud later includes
- shared team memory
- hosted project/repo context
- hosted indexing
- cross-user unfinished-work coordination
- collaboration and review flows
- governance/admin surfaces
- analytics and shared workspace features

## 12.3 Strategic rule
The OSS core must remain genuinely useful.
The cloud layer should monetize shared, hosted, organizational value.

---

# 13. Business Model

## 13.1 Recommended model
Open-source core + paid hosted collaboration layer + enterprise later.

## 13.2 Why this model fits
The core user value is local-first and individual-first.

The monetizable value emerges when:
- memory becomes shared
- context becomes hosted
- coordination becomes team-level
- governance becomes necessary

## 13.3 Year 1 business posture
Year 1 should focus on:
1. proving the wedge
2. proving retention paths
3. discovering cloud demand shape

Not on pretending there is already a mature enterprise business.

---

# 14. Cloud Strategy

## 14.1 Launch posture
Waitlist only.

## 14.2 Cloud promise
Dopemux Cloud will eventually offer:
- shared team memory
- hosted project and repo context
- team coordination across unfinished work

## 14.3 Waitlist purpose
The waitlist exists to collect:
- demand signals
- use-case clustering
- feature prioritization
- team-size segmentation
- design partners

It is a research and pipeline asset, not vanity.

---

# 15. Release Posture

## 15.1 First public posture
**Ambitious alpha**

This means:
- bigger story
- real product value
- visible roadmap
- honest maturity labels
- rough edges allowed, but not hidden

## 15.2 Main CTA
**Install Dopemux**

This should be the primary CTA across:
- the website
- the README
- launch posts
- social media bio links

Secondary CTA:
- View on GitHub

Tertiary CTA:
- Join cloud waitlist

---

# 16. Hero Demo and Public Wedge

## 16.1 Hero command
`dopemux analyze`

## 16.2 Why this is the hero
It is the best possible combination of:
- immediate utility
- clarity
- demo value
- artifact generation
- product proof
- natural expansion into ask and execution

## 16.3 Public sequence of revelation
The product should be revealed in this order:

1. **Understand** via analyze
2. **Ask** via grounded Q&A
3. **Execute** via plan/run
4. **Recover** via memory/recap
5. **Coordinate** via PM/focus layers

That sequence should shape:
- homepage sections
- README structure
- demo order
- launch week structure
- social content order

---

# 17. Strategic Risks

## 17.1 Product sprawl
Dopemux can easily become too many things at once.

Mitigation:
Keep the wedge narrow and the public story layered.

## 17.2 Overpromising beyond current system maturity
Some PM and orchestration surfaces are partially mature and some integration seams are still being finished.

Mitigation:
Use maturity labels and keep launch claims aligned with actual behavior.

## 17.3 Memory duplication and architecture drift
Without discipline, context, memory, and graph layers can blur into one noisy mess.

Mitigation:
Keep explicit system boundaries and enforce them through docs and review.

## 17.4 Install or first-run friction
If install or first-run experience is rough, the wedge dies.

Mitigation:
Prioritize package shell, docs, and demo repo hardening early.

## 17.5 Messaging confusion
If the public sees a wall of architecture names and subsystem theory, they will not understand what Dopemux actually does.

Mitigation:
Lead with the wedge and progressive disclosure.

## 17.6 Founder overload
The product scope is ambitious and can easily exceed sane execution bandwidth.

Mitigation:
Use milestone gates, explicit deferrals, and pluginization instead of core bloat.

---

# 18. Success Metrics

## 18.1 Product metrics
- install success rate
- analyze completion rate
- ask-after-analyze conversion
- plan/run usage
- recap/recovery usage
- PM surface usage
- repeat weekly active users

## 18.2 Community metrics
- GitHub stars
- contributors
- issue/discussion activity
- plugin submissions
- docs contributions

## 18.3 Business metrics
- waitlist signups
- waitlist segmentation by role/team size/use case
- design partner conversations
- repeated inbound requests for hosted/shared/team features

---

# 19. Strategic Decisions Locked

The following decisions are considered fixed unless explicitly revised:

- Product name: **Dopemux**
- Public category: **AI Devtools**
- Deeper category: **AI development runtime**
- Repo model: one monorepo including dopeTask
- Language: Python-first
- Open-core business model
- Cloud launch posture: waitlist only
- Hero wedge: `dopemux analyze`
- Main CTA: **Install Dopemux**
- Release posture: **ambitious alpha**
- Public naming family: dopeXXX
- Product philosophy: opinionated by default, infinitely flexible underneath

---

# 20. Strategic Recommendation

Dopemux should launch as a repo-intelligence-first OSS product that proves immediate value through:

- codebase analysis
- grounded system questions
- and a visible path into structured execution

It should not initially compete on breadth against every AI coding or PM product. It should compete on:

- coherence
- truthfulness
- continuity of work
- and finishing power

That is the strongest path available.

---

# 21. Next Documents in the Set

This strategy document should be followed by:

1. **Dopemux PRD**
2. **Dopemux Engineering Roadmap**
3. **Dopemux Launch and GTM Plan**

Those documents inherit this strategy and should not contradict it.
