# Dopemux Multi-Agent MVP — Research Findings, Architecture, and Plan

Last updated: 2025-09-08

## Executive Summary
Dopemux will be a multiplexed Claude Code orchestrator that runs coordinated subagents (planner, researcher, implementer, tester, reviewer, releaser) under a deterministic supervisor. It uses a lightweight, file-backed IPC bus for agent-to-agent handoffs and standardizes capability access through MCP servers (Serena, ConPort, OpenMemory, Claude-Context, TaskMaster, Exa). The MVP emphasizes small, correct patches (tests-first), strict quality gates, and token-thrift policies derived from the project’s existing CLAUDE.md.

## Landscape Review (2024–2025)
- Supervisor graphs (LangGraph Supervisor, Microsoft AutoGen teams): best fit for SDLC due to explicit routing, deterministic handoffs, and easier QA/traceability.
- Swarm/mesh (OpenAI Swarm): flexible/emergent; harder to bound for CI-grade quality gates.
- Lightweight code agents (Hugging Face smolagents): pragmatic executors within a supervised system.
- Knowledge/GraphRAG (LlamaIndex Workflows/GraphRAG): powerful for future multi-level memory; not required for MVP.

## Proven Patterns to Adopt (from current repo)
- Tool priority and bans (CLAUDE.md): prefer Serena/Claude-Context/ConPort over generic shell tools.
- Token thrift enforcement: ConPort limit=3–5; TaskMaster status filters; Serena symbol-first; rare/explicit Zen.
- Hooks-driven quality gates: PostToolUse = ruff + mypy + pytest --cov-fail-under=90.
- Slice-based SDLC workflow: bootstrap → research → story → plan → implement → debug → ship.
- Smart hooks dashboards: token/security dashboards exposed via Dopemux statusline.
- Role templates: task-orchestrator, task-executor, task-checker, privacy-guardian.

## MVP Architecture
### Components
- dopemux CLI (supervisor, statusline, run control)
- Subagents (lanes): planner, researcher, implementer, tester, reviewer, releaser (+ privacy-guardian)
- IPC bus: file-backed JSONL mailboxes with watchdog; ack/retry
- Memory: OpenMemory (personal), ConPort (project decisions/progress), per-lane short-term buffers
- MCP servers: Serena, Claude-Context, TaskMaster, ConPort, OpenMemory, Exa (wired via Dopemux policy layer)

### Envelope Schema (JSONL)
- envelope: { id, ts, type, from, to, corr, body, attachments?, severity?, tags[] }
- types: task.plan, task.handoff, research.findings, code.diff, code.review, test.report, decision.log, alert
- ack: { ackOf, status, notes }

### Supervisor Routing (deterministic)
planner → researcher (if unknowns) → planner (refine) → implementer (tests-first) → tester (gates) → reviewer (lint/types/review) → releaser (PR) → done

### Subagent Responsibilities
- Planner: acceptance criteria, file impact, TaskMaster tickets, plan.json
- Researcher: Exa/authoritative docs; stores sources in ConPort/OpenMemory
- Implementer: Serena edits; minimal diffs; emits code.diff + rationale
- Tester: pytest + coverage; publishes test.report; fails <90%
- Reviewer: ruff/mypy; review checklist; requests changes when needed
- Releaser: conventional commit; PR creation/checks/merge (ask-on-push preserved); ConPort decision
- Privacy-guardian: blocks sensitive paths; scans envelopes/attachments

### Statusline
- Per-lane state, token gauges, active tool, last event, coverage, PR status, hook alerts

## MCP Servers (MVP Set & Defaults)
- Serena: code search/symbol ops/edits (symbol-first; avoid full-file reads)
- Claude-Context: semantic code search (cap results)
- TaskMaster: task ops (status=pending, withSubtasks=false by default)
- ConPort: decisions/progress/glossary (limit=3–5)
- OpenMemory: personal/cross-session memory
- Exa: focused research queries
- Zen: disabled by default; enable explicitly per-slice/role

## Policies & Guardrails
- Enforce CLAUDE.md tool selection priorities and denylist (rm/sudo/.env/secrets).
- Apply hooks: PreToolUse (risk + budget checks), PostToolUse (ruff, mypy, pytest with ≥90% coverage) on edits.
- Token budgets per lane; fail-closed on overruns.

## Implementation Plan
1) Scaffold
- src/dopemux/{cli.py, supervisor.py, bus.py, policies.py, registry.py, agents/{planner.py,researcher.py,implementer.py,tester.py,reviewer.py,releaser.py,privacy_guardian.py}}
- .dopemux/bus/{inbox,outbox}/<agent>/*.jsonl (ignored by VCS)

2) Minimal IPC bus
- JSONL append + atomic rename publish; watchdog-based delivery; acks + retry/backoff

3) Registry & policies
- Role → MCP entitlements + token ceilings; enforce CLAUDE.md priorities and thrift rules

4) Subagent skeletons
- Process/thread loops; Implementer/Tester wired to Serena/pytest; Reviewer to ruff/mypy; Releaser to gh (ask-on-push)

5) Statusline & dashboards
- Display lanes, tokens, current tool, last event, coverage, PR state; integrate smart hooks outputs

6) Slash-commands
- dopemux start|status|lane:add|lane:logs|lane:pause|run:flow sdlc
- Flow emits envelopes for bootstrap→research→plan→implement→test→review→ship

7) Pilot & hardening
- Dry run on a small repo; validate gates; session replay; quick-start docs

## Risks & Mitigations
- IPC scalability: start with file bus; swap to sockets/NATS if concurrency increases
- Multi-repo orchestration: one bus per workspace initially; later global supervisor index
- Persona mode: “filthy/dopemux” gated behind a flag; default professional tone
- Zen misuse: disabled by default; explicit per-lane opt-in
- Windows support: validate atomic writes/watchdog behavior

## Open Questions
- Approve file-bus MVP vs sockets for day one
- Confirm six core roles (+ privacy-guardian)
- Approve carrying CLAUDE.md guardrails verbatim as Dopemux policies
- Statusline theme (classic vs dopemux mode)

## Next Actions
- Confirm choices above
- Scaffold directories/files (no commits until requested)
- Implement minimal planner→implementer→tester loop
- Hook in statusline and dashboards
- Pilot flow and iterate
