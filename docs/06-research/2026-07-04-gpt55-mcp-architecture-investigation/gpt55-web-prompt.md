---
id: gpt55-mcp-architecture-web-prompt
title: GPT55 MCP Architecture Web Prompt
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Ready-to-paste GPT-5.5 Pro prompt for MCP architecture design.
---
# GPT-5.5 Pro Web Prompt

You are GPT-5.5 Pro acting as an independent architecture reviewer for the Dopemux MCP/service fleet.

## Goal

Design the optimal architecture and implementation roadmap for every Dopemux service/server and their integrations with each other, MCP clients, Cockpit/UI, CLI, Task Orchestrator, ConPort, dope-memory, dope-context, Serena, ADHD Engine, dopecon-bridge, DCP facade, PAL, gptr, and underlying tools.

## Inputs I Am Uploading

Use these packet files first:

1. `readme.md`
2. `research.md`
3. `branch-work-audit.md`
4. `transcript-digest.md`
5. `source-manifest.md`
6. prior all-services audit package under `docs/06-research/2026-07-04-dopemux-service-investigation/`

Use any raw transcript path only as optional provenance. Do not treat transcript claims as proof unless the source tree, config, tests, or branch diffs support them.

## Authority Order

Use this truth order:

1. current repo source, config, compose wiring, tests, and active entrypoints
2. current branch diffs and commit history
3. AGENTS.md and architecture/governance docs
4. `claudedocs/*` audit/design docs
5. transcript digest and raw transcripts
6. inference

Mark every important claim as `OBSERVED`, `INFERRED`, `PROPOSED`, or `UNKNOWN`.

## Hard Boundaries

- ConPort owns structured decisions/progress/context.
- dope-memory owns chronicle receipts and historical memory.
- dope-context owns code/docs retrieval and must remain read-only relative to canonical truth.
- Task Orchestrator owns workflow transitions.
- Leantime owns PM metadata.
- dopecon-bridge transports/proxies only.
- ADHD Engine is operator-support/advisory only.
- Serena is code-intelligence/untracked-work detection support unless source evidence proves a stronger role.
- DCP facade is read-only external projection; do not design it as a writer.
- Generated config must be deterministic and must not silently reintroduce retired/dead surfaces.

## Specific Questions To Answer

1. What should be the canonical service/server architecture, by named service?
2. Which current services are canonical, support, adapter, infra, duplicate, legacy, dead, or unknown?
3. Which branch work on `claude/mcp-fleet-audit-complete` should be accepted, modified, split, or rejected?
4. Should Exa be retired per ADR-223 or wired per earlier target design?
5. What is the final MCP catalog/generated-output model?
6. What should `dopemux mcp ensure`, `doctor`, health checks, wrappers, and lifecycle management do?
7. How should ConPort, dope-memory, and dope-context integrate without violating Memory Trinity boundaries?
8. How should Serena/F001, ADHD Engine, and Task Orchestrator cooperate for untracked-work detection, advisory state, and workflow creation?
9. Which dormant features should be wired, rebuilt, explicitly shelved, or deleted?
10. What should Cockpit/UI surface implicitly, and what should require explicit operator confirmation?
11. What tests and drift gates prove the architecture?
12. What is the minimal packetized implementation roadmap, ordered by dependency and risk?

## Required Output

Produce:

1. Executive architecture verdict.
2. Service-by-service target-state matrix.
3. Integration architecture diagram in Mermaid.
4. Canonical writer and authority table.
5. MCP lifecycle and config-generation design.
6. Memory/context/event flow design.
7. ADHD/F001/Task Orchestrator/Cockpit UX design.
8. Dormant feature disposition matrix: wire, rebuild, shelve, delete, unknown.
9. Risk register with fail-closed controls.
10. Task-Packet-ready roadmap with commit-sized slices, tests, rollback, and owner/authority.
11. Open questions that require human decision before implementation.

Do not claim anything is implemented unless current source/branch evidence proves it. Prefer fewer, stronger architecture decisions over broad speculative wiring.
