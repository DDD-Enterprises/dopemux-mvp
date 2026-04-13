---
id: docs__01-decisions__RFC-zero-touch-sync
title: Docs  01 Decisions  Rfc Zero Touch Sync
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-04-13'
last_review: '2026-04-13'
next_review: '2026-07-12'
prelude: Docs  01 Decisions  Rfc Zero Touch Sync (explanation) for dopemux documentation
  and developer workflows.
---
# RFC: Zero‑Touch Sync across Leantime, Task‑Master, and ConPort

**Status:** Draft → Proposed
**Authors:** Dopemux Platform
**Reviewers:** PM, Eng, Ops
**Created:** 2025‑09‑25
**Last Updated:** 2025‑09‑25 (America/Vancouver)

## Abstract

Design a minimum‑touch workflow where **Leantime** is the team‑facing source of truth for status/roadmap, **Task‑Master** is the AI planner/executor (PRD → hierarchical tasks, next‑action), and **ConPort** is the project memory (decisions, patterns, rationale). Sync is maintained with a lightweight MCP‑driven loop and clear field ownership/precedence rules.

## Motivation

* We have multiple places where work is represented (tickets, AI‑generated task trees, ad‑hoc notes)
* Cognitive overhead and status drift occur without an opinionated sync
* We want **daily zero‑touch** upkeep and an ADHD‑friendly experience (Top‑3 Today, digest updates)

## Goals / Non‑Goals

### Goals

* One list of **in‑flight** work aggregated from all systems
* Clear ownership of fields (status, subtasks, decisions) and reconciliation strategy
* Minimal manual updates; safe defaults; fast rollout

### Non‑Goals

* Replacing Leantime/Task‑Master UIs
* Building a generic ETL; this is purpose‑built for Dopemux

## Stakeholders

* **Engineering** (implementation, reliability)
* **PM** (status accuracy, roadmap)
* **Operator** (runtime, incidents)
* **End users** (clarity, low friction)

## Glossary

* **MCP**: Model Context Protocol (tools/resources/prompts for agents)
* **LWW**: Last‑Write‑Wins, based on timestamps
* **Top‑3 Today**: Daily surfaced next‑actions (ADHD‑friendly)

## Background

We already use: Leantime (JSON‑RPC/MCP), Task‑Master (MCP/CLI), ConPort (MCP). Prior investigations defined each tool's specialization and an initial sync plan.

## High‑Level Design

### Roles

* **Leantime** → authoritative **status/roadmap**
* **Task‑Master** → authoritative **subtasks/next‑action** (PRD → tasks)
* **ConPort** → authoritative **decisions/context** (why/how, patterns)

### Sync Loop (every 300s by default)

1. Poll Leantime tickets/milestones; poll Task‑Master tasks; query ConPort for WIP/active decisions
2. Normalize titles → dedupe (title+hash)
3. Reconcile with precedence:
   * **status** ← Leantime
   * **subtasks** ← Task‑Master
   * **decisions** ← ConPort
   * Otherwise **LWW**
4. Push updates:
   * Reflect Task‑Master status into Leantime **only** if Leantime record is stale/empty
   * Create Leantime link‑backs when Task‑Master adds subtasks
   * Batch‑log decisions to ConPort

### ADHD Defaults

* **Top‑3 Today** (auto‑posted to Leantime "My Work")
* **Daily digest** (done/blocked/next)
* **Batch logging** to reduce notification noise

## Data Model Alignment

| Concept       | Leantime          | Task‑Master  | ConPort             | Owner of Truth  |
| ------------- | ----------------- | ------------ | ------------------- | --------------- |
| Title         | `headline`        | `title`      | `summary`           | —               |
| Status        | `status`          | `status`     | —                   | **Leantime**    |
| Subtasks      | limited           | `subtasks[]` | —                   | **Task‑Master** |
| Decision/Why  | —                 | —            | `log_decision(...)` | **ConPort**     |
| Owner         | `userId/assignee` | `assignee`   | `author`            | Leantime        |
| Last Activity | timestamp         | `updated_at` | timestamp           | LWW             |

## Interfaces & Contracts

### Leantime (JSON‑RPC/MCP)

* **Read**: list tickets/milestones (filter: in‑flight)
* **Write**: update ticket status, add comment/link to Task‑Master task, create ticket (optional)

### Task‑Master (MCP/CLI)

* **Read**: `list_tasks`, `next_task`
* **Write**: `set_status`, `expand_task`, `parse_prd` (pipeline step)

### ConPort (MCP)

* **Read**: `get_decisions`, search by tag `WIP`
* **Write**: `log_decision`, `batch_log_items`

## Conflict Handling

* **Status diverges** → prefer Leantime; if TM newer by >N minutes and LT unchanged, mark for review
* **Field changes** (title/notes) → **LWW** with audit trail
* **Mapping drift** (enum/status) → small map + unit tests; warn on unknowns

## Security & Privacy

* PAT/API keys per system; least privilege scopes
* Store secrets in Dopemux vault or env vars
* Audit sync writes; redact PII in logs

## Ops & Reliability

* Retries with exponential backoff; jitter
* Dead‑letter queue for failed writes
* Health checks for each endpoint
* Metrics: sync latency, error rate, drift count, manual reviews/day

## Deployment

* One small service (Python/Node) packaged as container; cron/timer loop (300s)
* Config via env: endpoints, tokens, interval, feature flags (top3/digest/batch)

## Rollout Plan

* **P0 Inventory** → print merged in‑flight list
* **P1 Uni‑directional** → TM→LT status, decisions→ConPort
* **P2 Bi‑directional + conflicts** → precedence+LWW+review queue
* **P3 Automation & Nudges** → Top‑3, digest, batch logging

## Success Metrics

* ≤10 min average drift across systems
* ≥95% automated sync of status changes
* <5 items/day in manual review (steady‑state)
* Positive UX feedback on Top‑3/Digest

## Alternatives Considered

* Webhooks/event bus (future; requires infra)
* Full CRDT merge (complex; overkill now)
* Single‑system migration (locks us in; loses strengths)

## Open Questions

* Exact status enum map LT↔TM
* Threshold for "TM newer than LT" exception
* Whether to auto‑create LT tickets from new TM tasks

## References

- [ADR-037: Status Source of Truth](../adr/037-status-source-leantime.md)
- [ADR-038: Subtask Authority](../adr/038-subtask-authority-taskmaster.md)
- [ADR-039: Decisions Authority](../adr/039-decisions-authority-conport.md)
- [ADR-040: Sync Mechanism](../adr/040-sync-mechanism-polling-mcp.md)
- [ADR-041: Conflict Resolution](../adr/041-conflict-resolution-lww-precedence.md)
- [Architecture: Zero-Touch Sync](../94-architecture/zero-touch-sync-architecture.md)
- [Runbook: Zero-Touch Sync Operations](../92-runbooks/runbook-zero-touch-sync.md)