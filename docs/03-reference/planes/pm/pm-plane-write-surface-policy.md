---
id: pm-plane-write-surface-policy
title: PM Plane Write Surface Policy
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-12'
last_review: '2026-03-12'
next_review: '2026-06-10'
prelude: Policy classification for normalized PM-plane tools and raw subsystem-native write surfaces.
---
# PM Plane Write Surface Policy

## Normalized tool classifications

| surface | classification | canonical backend | policy wrapping | TO adjudication required | adapter-only mediation allowed | notes |
|---|---|---|---|---|---|---|
| `pm_get_project_context` | `safe_read_only` | `ConPort` | `no` | `no` | `n/a` | Read-only normalized context surface. |
| `pm_get_priority_queue` | `safe_read_only` | `Task Orchestrator` | `no` | `n/a` | `n/a` | Read-only workflow queue surface. |
| `pm_get_blockers` | `safe_read_only` | `Task Orchestrator` | `no` | `n/a` | `n/a` | Read-only blocker surface. |
| `pm_get_workflow_state` | `safe_read_only` | `Task Orchestrator` | `no` | `n/a` | `n/a` | Read-only workflow legality surface. |
| `pm_update_work_item` | `policy_wrapped_write` | `Leantime` | `mandatory` | `only when payload becomes workflow-significant` | `yes` | Reject status/transition writes unless separately adjudicated. |
| `pm_transition_work_item` | `policy_wrapped_write` | `Task Orchestrator` | `mandatory` | `yes` | `yes` | Must fail closed while active TO runtime lacks direct project-scoped transition surface. |
| `pm_get_sprint_snapshot` | `safe_read_only` | `Leantime` | `no` | `no` | `n/a` | Read-only PM snapshot. |
| `pm_get_decision_context` | `safe_read_only` | `ConPort` | `no` | `no` | `n/a` | Read-only durable context surface. |
| `pm_log_progress` | `policy_wrapped_write` | `ConPort` | `mandatory` | `no` | `yes` | Durable progress write resolves to ConPort. |
| `pm_get_work_chronicle` | `safe_read_only` | `dope-memory` | `no` | `no` | `n/a` | Read-only chronicle surface. |
| `pm_search_project_knowledge` | `safe_read_only` | `dope-context` | `no` | `no` | `n/a` | Read-only search surface with provenance. |
| `pm_get_technical_context` | `safe_read_only` | `Serena` | `no` | `no` | `n/a` | Read-only technical context surface. |

## Raw subsystem-native surfaces that must never be the agent contract

| raw surface | classification | reason |
|---|---|---|
| `leantime-bridge.create_ticket` | `never_expose_directly` | Backend-native contract; PM plane must normalize IDs, fields, and policy. |
| `leantime-bridge.update_ticket` | `never_expose_directly` | Can drift into workflow-significant mutation without PM-plane policy wrapping. |
| `leantime-bridge.list_tickets` | `never_expose_directly` | Response shape is Leantime-native, not normalized PM-plane shape. |
| raw Leantime JSON-RPC methods | `never_expose_directly` | Agents should be Leantime-backed, not Leantime-shaped. |
| raw Task Orchestrator MCP/HTTP methods | `never_expose_directly` | Workflow backend tools are internal implementation seams. |
| ConPort REST/JSON-RPC/FastMCP method names | `never_expose_directly` | ConPort is authoritative, but the PM-plane contract must stay backend-agnostic. |
| dope-memory HTTP tool names | `never_expose_directly` | Chronicle backend contract is internal to PM-plane composition. |
| dope-context backend-native search methods | `never_expose_directly` | Retrieval results require PM-plane provenance normalization. |
| Serena backend-native methods | `never_expose_directly` | Technical context must be normalized before PM-plane exposure. |

## Policy rules

- `safe_read_only` tools may be exposed directly as normalized PM-plane tools.
- `policy_wrapped_write` tools must validate payload class, authority path, and reconciliation behavior before executing.
- `never_expose_directly` surfaces may exist behind adapters, but they are not the sanctioned long-term contract for agents or supervisors.
