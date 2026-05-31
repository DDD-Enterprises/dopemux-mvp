---
id: task-orchestrator-operator-integration-authority
title: Task Orchestrator Operator Integration Authority
type: reference
owner: '@hu3mann'
author: codex
date: '2026-05-25'
last_review: '2026-05-25'
next_review: '2026-08-23'
prelude: System authority document for read-only task-orchestrator operator integration boundaries and deferred mutation gates.
---
# Task Orchestrator Operator Integration Authority

## Scope

This document converts the 2026-05-25 operator integration assessment into
task-orchestrator system authority for the next operator integration slices.

It is authority for planning order, boundary language, approval tiers, and
operator-facing command design for task-orchestrator integration. It is not runtime proof. Runtime behavior still
comes from code, config, tests, compose wiring, active entrypoints, and the
active Task Packet.

## Relationship To dopeTask

This is a task-orchestrator system authority document.

The accompanying `TP-DMX-ORCH-DOCS-003` Task Packet uses the
`dopetask-canonical-spec.json` schema only because this repository requires
repo-changing work to be packet-scoped and schema-validated. That packet is the
audit wrapper for the change; it is not the subject authority and does not make
this a dopeTask system document.

Labels:

- `OBSERVED`: directly supported by inspected repo source, config, current docs,
  or active tool surface.
- `RISK`: supported concern with incomplete enforcement or incomplete chain.
- `PROPOSED`: allowed target design, still requiring Task Packet execution.
- `UNKNOWN`: not proven by current evidence; fail closed.

## Executive Verdict

Read-only operator integration is allowed.

The repo is ready for a minimal read-only/operator-status integration around
task-orchestrator status, queue, blockers, and daily summary views. It is not
ready for mutation-heavy orchestration, autonomous workflow mutation, automatic
event-to-memory writes, GitHub mutation, broad MCP write wrapping, or destructive
context/index actions.

Mutation remains deferred until all of the following are true:

- the canonical writer for the mutation is identified;
- approval tier and receipt requirements are enforced;
- proof bundle shape is settled;
- replay/idempotency behavior is tested;
- downstream consumers are traced;
- `UNKNOWN` authority surfaces are resolved or explicitly blocked.

Do not centralize authority in task-orchestrator. Its correct role is workflow
state/view/transition coordination. It must not become PM metadata owner,
memory owner, proof owner, retrieval owner, execution runtime, acceptance
authority, bridge owner, or agent sovereign.

## Authority Used

| Source | Label | Used For |
| --- | --- | --- |
| `AGENTS.md` | OBSERVED | Truth order, packet rules, architecture boundaries, proof requirements, known dangers. |
| `PROJECT.md` | OBSERVED | Repo is a composed multi-system workspace with split authority. |
| `ARCHITECTURE.md` | OBSERVED | Dopemux is not a unified orchestration brain; bridges/adapters are not authority. |
| `PM_PLANE.md` | OBSERVED | PM reads/writes are split across Leantime, task-orchestrator, ConPort, dope-memory, and bridge routes. |
| `SERVICE_CATALOG.md` | OBSERVED | Current service roles and task-orchestrator drift classifications. |
| `docs/03-reference/governance/authority-boundaries.md` | OBSERVED | Canonical writer and non-authority matrix. |
| `docs/03-reference/systems/task-orchestrator/system-taskorchestrator.md` | OBSERVED | In-repo FastAPI task-orchestrator boundaries and upstream 13-tool MCP distinction. |
| `src/dopemux/pm/reads.py` | OBSERVED | Existing Python library calls for queue, blockers, and workflow state. |
| `src/dopemux/pm/adapters/orchestrator.py` | OBSERVED | Adapter endpoints for queue, blockers, state, and transition. |
| `services/task-orchestrator/app/api/project_workflow.py` | OBSERVED | FastAPI project workflow queue, blocker, state, and transition endpoints. |
| `src/dopemux/mcp/default_catalog.yaml` | OBSERVED | Current 13-tool upstream MCP task-orchestrator launcher and repo-scoped state. |
| `services/task-orchestrator/server.py` | RISK | Legacy wrapper claims a Kotlin/37-tool runtime lineage; not current authority by itself. |
| Current MCP `get_context()` health check | OBSERVED | Active MCP task-orchestrator had no active, blocked, or stalled items at authoring time. |

## Evidence Ledger

| Claim | Label | Evidence | Confidence |
| --- | --- | --- | --- |
| Dopemux is a multi-system workspace, not a monolith. | OBSERVED | `PROJECT.md`, `ARCHITECTURE.md`, `SERVICE_CATALOG.md`. | HIGH |
| `dopemux` is the operator control and CLI surface. | OBSERVED | `PROJECT.md`, `ARCHITECTURE.md`, `AGENTS.md`. | HIGH |
| task-orchestrator owns workflow-significant transitions and workflow views. | OBSERVED | `PM_PLANE.md`, `src/dopemux/pm/reads.py`, `src/dopemux/pm/writes.py`, `services/task-orchestrator/app/api/project_workflow.py`. | HIGH |
| task-orchestrator must not own PM metadata, ConPort decisions/progress, dope-memory chronicle, or dope-context retrieval. | OBSERVED | `AGENTS.md`, `PROJECT.md`, `PM_PLANE.md`, `authority-boundaries.md`. | HIGH |
| dopecon-bridge must not be treated as authority. | OBSERVED | `AGENTS.md`, `PM_PLANE.md`, `ARCHITECTURE.md`, `authority-boundaries.md`. | HIGH |
| Existing direct operator workflow has PM read helpers but no `dopemux orchestrator status/queue/blockers/daily` command group. | OBSERVED | `src/dopemux/pm/reads.py`, `src/dopemux/cli.py`, `src/dopemux/commands/*`. | HIGH |
| Read-only status/queue/blocker/daily CLI is the safe first integration. | PROPOSED | Existing read helpers and authority split support T0/T1 reads. | HIGH |
| Packet/proof validation is the next safe surface after status reads. | PROPOSED | Governance and proof requirements in `AGENTS.md` and proof docs. | MEDIUM |
| EventCoordinator/event paths do not yet prove end-to-end event to ConPort to dope-memory to proof receipt correlation. | RISK | Event emission and adapters exist, but this packet did not validate a full consumer/proof chain. | MEDIUM |
| Upstream 13-tool MCP task-orchestrator is active in local MCP config. | OBSERVED | `src/dopemux/mcp/default_catalog.yaml`, current tool surface. | HIGH |
| Kotlin task-orchestrator implementation as a current proven runtime dependency remains unresolved and risky for proof-envelope design. | UNKNOWN | `services/task-orchestrator/server.py` claims Kotlin/37 tools, but current docs/catalog distinguish the upstream 13-tool MCP runtime and in-repo FastAPI service. | MEDIUM |
| Agent authority remains unresolved and should be treated as a workflow risk until a specific runtime path is verified. | UNKNOWN | `AGENTS.md`, `PROJECT.md`, `ARCHITECTURE.md`. | HIGH |

## System Role Table

| System | Primary Authority | Should Own | Must Not Own | Integration Risk |
| --- | --- | --- | --- | --- |
| `dopemux` | Operator control, CLI, startup, MCP/service coordination. | Daily command surface, routing, service health views, operator prompts. | PM truth, durable memory truth, execution kernel, retrieval truth. | Medium: CLI can accidentally centralize authority. |
| In-repo task-orchestrator FastAPI service | Workflow views and workflow-significant transitions. | Queue, blockers, workflow state, transition routing, workflow read model. | PM metadata, ConPort records, dope-memory chronicle, dope-context retrieval, proof authority. | High if promoted into a general orchestration brain. |
| Upstream 13-tool MCP Task Orchestrator | MCP work item state machine and role progression for local Codex/Dopemux workflows. | Work item roles, dependencies, next-item routing, note-gated progression. | dopetask execution, ConPort decisions, dope-memory history, repo PM metadata. | Medium: separate from in-repo FastAPI service; proof envelope remains incomplete. |
| `dopetask` | Task Packet execution kernel and proof production after handoff. | Packet execution, validation handoff, proof output. | PM authority, workflow legality, memory, retrieval. | Medium: schema/version naming drift. |
| Leantime | Passive PM metadata and snapshots. | Task/project metadata, ticket snapshots. | Workflow legality, decisions, chronicle history. | Low to medium. |
| ConPort | Structured decisions, progress, context, custom data. | Decision/progress/context records. | PM metadata, workflow legality, chronicle, retrieval ranking. | Medium: port/client split and writer consistency remain risks. |
| dope-memory | Chronicle and historical receipt memory. | Durable receipts, recap, replay, chronology. | PM truth, workflow legality, structured decision authority. | Medium: overlap with working-memory surfaces. |
| dope-context | Code/docs retrieval and indexing. | Deterministic search and index status. | PM truth, memory truth, current workflow state. | High for destructive/index actions such as clear/reset paths. |
| Serena | Code intelligence and symbol navigation. | Symbol lookup, impact mapping, refactor/test discovery. | Proof, validation, workflow authority. | Medium: runtime/canonicality duplicate surfaces. |
| dopecon-bridge | Adapter, proxy, and event transport. | Safe routing, transport, compatibility proxy, event bus paths. | Task, workflow, decision, progress, PM, memory, chronicle, retrieval authority. | High because broad routes can look authoritative. |
| ADHD Engine | Operator-support and cognitive-state surfaces. | Energy/load state, recommendations, operator support. | PM, ConPort, chronicle, workflow legality. | Medium: auto-trigger temptation. |
| Repo Truth Extractor | Repo extraction/audit artifacts. | Evidence artifacts about repo truth. | Live runtime truth. | Low if kept advisory. |
| Supervisor Ledger | Governance acceptance. | Acceptance decisions, signoff, final verdicts. | Runtime state, execution. | High if absent from proof. |
| Agents | Operators, implementers, reviewers. | Implementation, audit, critique, packet execution. | PM truth, acceptance authority. | High: repo-wide authority remains UNKNOWN. |

## Authority Boundary Rules

| Capability | Owner | task-orchestrator Role | Approval | Failure Behavior |
| --- | --- | --- | --- | --- |
| Morning status read | `dopemux` plus task-orchestrator reads | Supply queue, blockers, workflow state | No for T0 reads | Degrade to partial dashboard. |
| Workflow transition | task-orchestrator | Canonical transition endpoint | Yes for operator-facing writes unless inside approved packet | Fail closed if unavailable. |
| PM metadata update | Leantime | Route or observe only | Yes when mutating | Reject if routed through task-orchestrator as owner. |
| Decision logging | ConPort | Observe or emit event only | Yes for writes | Do not write if ConPort unavailable. |
| Progress logging | ConPort primary, dope-memory mirror | Observe or trigger canonical writer only | Yes for writes | Report partial mirror failure explicitly. |
| Chronicle receipt | dope-memory | Observe only | Yes for writes | Never fabricate receipt. |
| Code/docs retrieval | dope-context | Request context only | Read-only allowed | Mark retrieval stale or derived. |
| Symbol lookup | Serena | Request analysis only | Read-only allowed | Never treat as proof. |
| Packet validation | dopetask schema or repo schema | Provide T1 wrapper only | No for validation; yes for durable writes | Fail closed on schema error. |
| Packet execution | dopetask | Route handoff only | Yes, valid Task Packet required | Refuse if no valid packet. |
| Proof assembly | dopetask/proof tooling plus Supervisor Ledger | Draft or collect only | Yes for final write | Block if manifest/chain missing. |
| PR status | GitHub/dopemux-github | Observe/read only | No for reads; yes for comments/merge | Do not mutate silently. |
| Context freshness | dope-context, ConPort, dope-memory by slice | Observe only | No for reads | Preserve partial freshness state. |
| Context/index refresh | dope-context | Must not own | Yes, T4 | Block broad/destructive refresh. |
| Destructive action | Canonical tool owner plus operator | Must not automate | Typed approval | Default deny. |

## Daily Workflow Mapping

| Workflow | Trigger | Inputs | Allowed Tools | Outputs | Automation Tier | Human Gate |
| --- | --- | --- | --- | --- | --- | --- |
| Morning Operator Startup | `dopemux orchestrator daily` or session start | Git state, PRs, task packets, queue, blockers, ConPort context, dope-memory receipts, dope-context status | dopemux CLI, task-orchestrator reads, ConPort reads, dope-memory reads, Git/GitHub reads | Top 3 lanes, blocked work, next packet, do-not-touch list | T0/T1 | Required before writing plan/artifact. |
| Task Packet Forge | Operator objective | Supervisor Ledger, repo truth, decisions, memory, retrieval, schema | dope-context reads, Serena reads, schema validator | One Task Packet draft | T1/T2 | Required before durable artifact write. |
| Implementation Intake | Implementer output | Diff, proof, commands, git status, claimed changes | git, schema validator, proof checker | Intake verdict | T0/T1 | Required before acceptance. |
| Audit / Red Team | After implementation or high risk | Diff, tests, proof, authority map, MCP surfaces | PAL/challenge/codereview, repo checks | PASS/FAIL/BLOCKED | T1 | Required for risky mutation. |
| PR Queue Readiness | Daily or pre-merge | PR list, CI, proof bundles, reviews, branch age | GitHub reads, local proof validator | Mergeable/blocked/stale/dangerous table | T0/T1 | T5 approval for comments/merge. |
| Context Refresh | Manual or stale-context detector | Changed files, index status, recent decisions, receipts | dope-context status, ConPort search, dope-memory recap | Freshness receipt | T0/T1, T4 for index writes | Approval for indexing/sync. |
| Personal Daily Workflow | Morning or after interruption | Daily state plus operator load and available agents | `dopemux daily`, ADHD reads, supervisor review | First task, delegate list, review points, parked work | T0/T1 | Approval before delegation/mutation. |

## MCP Tool Registry Rules

The following names are proposed operator-facing wrappers. They are not runtime
claims unless implemented by a later Task Packet.

| Tool Name | Purpose | Read/Write | Tier | Receipt |
| --- | --- | --- | --- | --- |
| `orchestrator.status.queue` | Read workflow queue. | Read | T0 | No |
| `orchestrator.status.blockers` | Read blockers. | Read | T0 | No |
| `orchestrator.status.state` | Read workflow state. | Read | T0 | No |
| `orchestrator.daily.summary` | Daily command-center view. | Read/analysis | T0/T1 | Optional |
| `orchestrator.packet.validate` | Validate Task Packet schema. | Read/local analysis | T1 | Yes |
| `orchestrator.packet.inspect` | Inspect packet against authority boundaries. | Read/local analysis | T1 | Yes |
| `orchestrator.review.intake` | Check implementation output against packet/proof. | Read/local analysis | T1 | Yes |
| `orchestrator.proof.validate` | Validate proof bundle shape. | Read/local analysis | T1 | Yes |
| `orchestrator.transition.preview` | Preview workflow transition. | Read | T1 | Yes |
| `orchestrator.transition.apply` | Apply canonical workflow transition. | Write | T4 | Mandatory |
| `orchestrator.plan.decompose_preview` | Draft decomposition without writes. | Read/local draft | T1/T2 | Yes if saved |
| `orchestrator.plan.decompose_apply` | Create or advance workflow items. | Write | T4 | Mandatory |
| `orchestrator.memory.record_decision` | Route decision to ConPort. | Write through ConPort | T4 | Mandatory |
| `orchestrator.memory.record_progress` | Route progress to ConPort plus dope-memory mirror. | Write through canonical writers | T4 | Mandatory |
| `orchestrator.github.pr_readiness` | Classify PR readiness. | Read | T0/T1 | No |
| `orchestrator.github.comment` | Comment on PR. | Write | T5 | Mandatory |
| `orchestrator.github.merge` | Merge PR. | Write | T5/T6 | Mandatory typed approval |
| `orchestrator.context.refresh_status` | Assess context freshness. | Read | T0/T1 | Optional |
| `orchestrator.context.refresh_index` | Trigger scoped dope-context sync/index. | Write/index | T4 | Mandatory |
| `orchestrator.route.pm` | Wrap bridge PM route directly. | N/A | Do not expose | N/A |
| `orchestrator.destructive.clear_index` | Delete dope-context index. | Write/destructive | Block | N/A |

Auto-invocation is limited to T0/T1. T2 may draft only. T4 and higher require
explicit operator approval and receipts.

## Hook Architecture

| Hook | Trigger | Allowed Actions | Forbidden Actions | Failure Behavior |
| --- | --- | --- | --- | --- |
| `on_startup` | `dopemux start` or session start | T0 health/status reads, queue/blockers/state | Writes, transitions, decomposition | Degrade partial. |
| `on_repo_scan` | Manual scan | Read git, files, status, schema locations | Edits, index deletion | Fail closed on dirty/mismatch. |
| `on_context_refresh` | Manual or stale index | Status reads, scoped sync with approval | `clear_index`, broad reindex without approval | Fail closed if scope unknown. |
| `on_packet_created` | Packet draft saved | Schema validate, authority review | Execution, branch mutation | Block if invalid. |
| `on_packet_started` | Operator-approved packet | Verify worktree, branch, marker | Continue on mismatch | Stop. |
| `on_packet_completed` | Implementer proof returned | Intake review, proof validation | Mark complete without evidence | BLOCKED if incomplete. |
| `on_proof_received` | Proof bundle uploaded | Validate shape, chain, commands | Accept missing artifacts | Fail closed. |
| `on_audit_requested` | Manual/high-risk | Read-only red team | Mutate code | Fail if evidence missing. |
| `on_pr_opened` | PR created | Read PR, CI, proof refs | Comment/label without approval | Partial if GitHub unavailable. |
| `on_pr_updated` | New commit/check | Re-read status | Auto-merge | Fail closed on stale proof. |
| `on_merge_candidate` | PR appears ready | Readiness classification | Merge without typed approval | Block on missing proof. |
| `on_blocker_detected` | Queue/proof/audit blocker | Surface blocker; write only via owner | Hide or auto-resolve | Fail visible. |
| `on_daily_plan_requested` | Operator daily | Read and rank | Mutate workflow | Degrade. |
| `on_memory_write_requested` | Decision/progress receipt | Route to canonical writer | Write through task-orchestrator as owner | Fail closed. |
| `on_authority_violation` | Duplicate writer/proxy authority | Block and warn | Continue | Hard stop. |

The machine-readable registry for these hooks is
`config/orchestrator/plugin_hooks.yaml`. The registry is read-only
classification and audit input only. It does not load plugins, execute hooks,
grant approvals, apply transitions, write memory, mutate GitHub, or replace a
canonical writer.

## Memory Write Policy

Write receipts, not guesses.

| Data Type | Write Target | Owner | Automatic | Approval |
| --- | --- | --- | --- | --- |
| Governance acceptance | Supervisor Ledger | Supervisor/human/reviewer | No | Yes |
| Structured decision | ConPort | ConPort | No meaningful auto-writes | Yes |
| Progress status | ConPort primary, dope-memory mirror | ConPort plus dope-memory | Low-risk receipts only if policy exists | Usually yes |
| Historical receipt | dope-memory | dope-memory | Only after canonical write | Yes if user-originating |
| Code/docs index | dope-context | dope-context | Status read only | Yes for sync/index |
| Local docs | repo | active Task Packet scope | No | Yes, packet required |
| Proof artifact | proof path | dopetask/proof tooling | Draft only | Yes for final |
| ChatGPT project memory | operator/supervisor | operator/supervisor | No for repo facts | Yes |
| Daily ephemeral plan | stdout/no durable target | dopemux daily | Yes | No |
| Blocker | ConPort or proof artifact | ConPort/proof owner | No if workflow-significant | Yes |
| Retrieval result | none | upstream source remains owner | No | N/A |

task-orchestrator may propose, route, and observe. It must not become a memory
sink.

## Workflow DSL Policy

Minimal workflow definitions may be introduced later, but they must remain
boring and auditable.

Required fields:

```yaml
schema_version
id
title
owner
authority.primary_owner
automation_tier
triggers
inputs
steps[].id
steps[].tool
steps[].mode
steps[].validation
steps[].on_failure
outputs
approval.required
```

Forbidden fields or semantics:

```yaml
god_mode: true
canonical_writer: "task-orchestrator"   # unless capability is workflow transition/view
auto_approve: true
silent_write: true
destructive: true                       # use T6 and typed confirmation instead
bridge_as_authority: true
```

Validation rules:

- `automation_tier` must be one of `T0`, `T1`, `T2`, `T3`, `T4`, `T5`, `T6`,
  `TX`, or `TU`.
- Any step with `mode: write` must name the canonical writer.
- Any T4 or higher workflow requires approval.
- Any bridge-mediated write must name the upstream canonical writer.
- Any proof/packet workflow must reference its schema path.
- Any TX or TU workflow refuses by default.
- Output lists must respect the operator contract: top 3, `items`,
  `more_count`, and `next_token` where paging applies.

## Automation Safety Tiers

| Tier | Examples | Automatic | Approval | Receipt |
| --- | --- | --- | --- | --- |
| T0 Read-only status | queue, blockers, git status, PR status | Yes | No | Optional |
| T1 Local analysis | packet validate, proof validate, diff inspect | Yes | No | Yes if decision-affecting |
| T2 Draft artifact | draft plan, draft proof, temp markdown | Maybe | Before durable write | Yes |
| T3 Repo-local docs edit | docs update, command docs | No | Yes plus Task Packet | Yes |
| T4 Source/config/runtime state | code edit, ConPort write, transition, index sync | No | Yes | Mandatory |
| T5 GitHub mutation | PR comment, label, merge, push | No | Yes plus preview | Mandatory |
| T6 Destructive/deploy/release | clear index, deploy, force push, delete records | No | Typed phrase and operator present | Mandatory |
| TX Unknown | opaque or externally unresolved tool | No | Cannot approve safely | Violation receipt |
| TU Unclassified | unenumerated tools | No | Cannot approve safely | Violation receipt |

The machine-readable registry for these tiers and the proposed
operator-facing capabilities is
`config/orchestrator/approval_policy.yaml`. The registry is a classification
and validation source only. It does not grant approval, apply workflow
transitions, write receipts, mutate GitHub, write memory, or override a
canonical writer. Unregistered capabilities classify as `TU` and refuse by
default.

Typed confirmation pattern:

```text
I AUTHORIZE <exact operation> ON <repo/workspace/resource> USING <canonical writer> WITH PROOF <proof-id>
```

## CLI/TUI Surface Policy

Proposed commands:

| Command | Purpose | Read/Write | Tier |
| --- | --- | --- | --- |
| `dopemux orchestrator status` | Queue/blocker/state summary. | Read | T0 |
| `dopemux orchestrator daily` | Daily command center. | Read/analysis | T0/T1 |
| `dopemux orchestrator queue` | Show queue. | Read | T0 |
| `dopemux orchestrator blockers` | Show blockers. | Read | T0 |
| `dopemux orchestrator transition preview` | Preview transition. | Read/analysis | T1 |
| `dopemux orchestrator transition apply` | Apply transition. | Write | T4 |
| `dopemux orchestrator packet validate` | Validate packet schema. | Read/analysis | T1 |
| `dopemux orchestrator intake` | Intake implementation proof. | Read/analysis | T1 |
| `dopemux orchestrator audit` | Red-team packet or PR. | Read/analysis | T1 |
| `dopemux orchestrator proof validate` | Validate proof bundle. | Read/analysis | T1 |
| `dopemux orchestrator context status` | Context freshness view. | Read | T0 |
| `dopemux orchestrator context refresh` | Scoped context refresh. | Write/index | T4 |
| `dopemux orchestrator plugins doctor` | Plugin safety status. | Read | T0 |
| `dopemux orchestrator hooks list` | Hook and tier list. | Read | T0 |
| `dopemux orchestrator dangerous check` | Guard-consumer status. | Read/analysis | T1 |

Proposed TUI panels:

| Panel | Contents | Tier |
| --- | --- | --- |
| `Today` | Active lanes, next packet, blockers. | T0 |
| `Authority` | Canonical writers per slice. | T0 |
| `Packets` | Draft/active/completed packets and validation status. | T0/T1 |
| `Proof` | Proof completeness and missing artifacts. | T1 |
| `Risks` | TX/TU tools and T4+ pending approvals. | T0 |
| `PR Queue` | Mergeable, blocked, stale, dangerous. | T0/T1 |
| `Context` | dope-context, ConPort, dope-memory freshness. | T0 |
| `Do Not Touch` | Blocked branches, destructive tools, stale assumptions. | T0 |

## Minimal Viable Integration

Build this first, in one to two packets.

### Packet 1: Read-only orchestrator status/daily surface

Goal: expose `status`, `queue`, `blockers`, and `daily` as read-only CLI
commands using existing task-orchestrator read helpers and local git status.

Why first: it gives operator value without touching workflow state. It is T0/T1,
proofable, and bounded.

Scope:

- add CLI group under `dopemux orchestrator`;
- call existing PM/task-orchestrator read helpers;
- output top-3 operator format with `more_count` and `next_token`;
- no writes;
- no MCP mutation;
- no GitHub mutation;
- no bridge-as-authority claim.

Validation:

- unit tests for command rendering;
- mocked adapter tests for timeout and partial failure;
- `python -m compileall -q src`;
- relevant pytest subset;
- manual command output captured as proof.

### Packet 2: Packet/proof validation surface

Goal: expose `dopemux orchestrator packet validate` and
`dopemux orchestrator proof validate`.

Why second: it closes the governance loop before mutation.

Scope:

- schema lookup;
- JSON schema validation;
- proof field completeness;
- no execution;
- no write except optional temp report.

Validation:

- known-good and known-bad fixtures;
- missing-field errors;
- schema path test.

Do not start with event consumers, auto-decomposition, GitHub comments,
workflow transition application, memory writes, or index refresh.

## Medium Integration

Build only after the first read-only/status packet proves stable.

1. Operator-gated workflow transition command:
   preview first, apply second, idempotency key required, receipt mandatory.
2. Daily workflow TUI panel:
   queue, blockers, state, next packet, stale proof indicators, do-not-touch list.
3. Proof bundle validator:
   reconcile proof templates, require manifest, chain of custody, warnings,
   blockers, and command evidence.
4. Context refresh policy:
   read-only freshness check first; scoped refresh only with approval; explicitly
   block destructive index clearing.
5. Event consumer audit packet:
   inspect EventCoordinator consumers and map missing ConPort/dope-memory/proof
   chain before implementing any event-to-memory automation.

Local implementation note (2026-05-26): `src/dopemux/orchestrator/operator_workflows.py`
implements the remaining integration surfaces as fail-closed local plans,
receipts, previews, validators, and read-only snapshots. The module does not
write context indexes, ConPort, dope-memory, workflow state, GitHub state, or
acceptance records; T4/T5 paths only report readiness for the named canonical
writer after exact typed approval.

## Advanced Integration Deferred

| Capability | Why Deferred |
| --- | --- |
| Auto-decomposition from objectives | Implicit mutation risk before approval tiers and proof are enforced. |
| Automatic ConPort/dope-memory writes from workflow events | Requires correlation IDs, proof receipt, replay semantics, and consumer audit. |
| GitHub PR comments, labels, merges | T5 mutation requiring proof model and typed confirmation. |
| Full MCP `orchestrator.*` write registry | Too much blast radius before approval tiers are enforced. |
| Upstream MCP proof envelope integration | Needs response schema and receipt contract. |
| dopeUI to dopemux to dopeTask flow | Schema/source mismatch is unresolved in current authority docs. |
| dNh_CRM proof forwarding | Adjacent integration docs are not implementation proof here. |
| Agent-runner auto-routing | Agent authority is unresolved. |

## Candidate Packet IDs

| ID | Objective | Risk | Validation | Proof |
| --- | --- | --- | --- | --- |
| `TP-DMX-ORCH-STATUS-001` | Add read-only `dopemux orchestrator status/daily/queue/blockers`. | Low | CLI tests, mocked adapter, compileall. | Command outputs, test logs, diff. |
| `TP-DMX-ORCH-PROOF-002` | Add packet/proof validation commands. | Medium | Schema fixtures, missing-field tests. | Validation report, fixture outputs. |
| `TP-DMX-ORCH-DOCS-003` | Document task-orchestrator stack and authority boundaries. | Low | Docs validation, schema validation, grep checks. | Docs diff, citation ledger. |
| `TP-DMX-ORCH-TRANSITION-004` | Add operator-gated transition preview/apply. | High | Mocked transition, approval tests, idempotency tests. | Transition receipt fixture. |
| `TP-DMX-ORCH-EVENTAUDIT-005` | Audit EventCoordinator to ConPort/dope-memory/proof chain. | Medium | Static inventory, no writes. | Audit report. |
| `TP-DMX-ORCH-CONTEXT-006` | Add context freshness read-only command. | Low | Mocked reads. | Freshness output. |
| `TP-DMX-ORCH-MCP-007` | Add T0/T1 MCP wrappers only. | Medium | Tool registry tests, tier checks. | MCP registry proof. |
| `TP-DMX-ORCH-SAFETY-008` | Add TX/TU/T6 refusal registry. | Medium | Destructive-tool refusal tests. | Safety receipt. |

## First Recommended Macro-Packet

The first implementation packet should be exactly this shape:

```json
{
  "id": "TP-DMX-ORCH-STATUS-001",
  "project": "dopemux-mvp",
  "target": "Read-only task-orchestrator daily/status CLI surface",
  "repo_binding": {
    "project_id": "DDD-Enterprises/dopemux-mvp",
    "repo_marker": ".dopetaskroot",
    "origin_hint": "https://github.com/DDD-Enterprises/dopemux-mvp.git",
    "require_identity_match": true
  },
  "series": {
    "id": "DMX-ORCH-INTEGRATION",
    "base_branch": "main",
    "parent_tp_id": null,
    "final_packet": false
  },
  "execution": {
    "agent": "codex",
    "branch": "codex/tp-dmx-orch-status-001",
    "base_branch": "main"
  },
  "commit": {
    "message": "feat(orchestrator): add read-only daily status CLI",
    "allowlist": [
      "src/dopemux/**",
      "tests/**",
      "docs/03-reference/**",
      "task-packets/generated/TP-DMX-ORCH-STATUS-001.json",
      "proof/orchestrator/TP-DMX-ORCH-STATUS-001/**"
    ],
    "verify": [
      "python -m compileall -q src",
      "python -m pytest -q tests/unit -k orchestrator",
      "git diff --check"
    ]
  },
  "pr": {
    "title": "feat(orchestrator): add read-only daily status CLI",
    "body": "Adds a read-only operator status surface for task-orchestrator queue, blockers, workflow state, and daily summary. No workflow mutation.",
    "base": "main"
  },
  "pal_chain": {
    "enabled": true,
    "steps": [
      "analyze",
      "thinkdeep",
      "challenge",
      "planner",
      "challenge",
      "codereview",
      "precommit"
    ]
  },
  "invariants": [
    "task-orchestrator must not own PM metadata, ConPort decisions/progress, dope-memory chronicle, or dope-context retrieval",
    "dopecon-bridge must not be treated as source truth",
    "all new commands are read-only T0/T1",
    "no workflow transitions, writes, GitHub mutations, index mutations, or memory writes",
    "output uses top-3 operator contract with more_count and next_token"
  ],
  "steps": [
    {
      "id": "preflight",
      "task": "Verify repo identity, branch, marker, dirty state, and locate existing read helpers.",
      "validation": [
        "Capture pwd, git root, branch, HEAD, status, marker check, and relevant rg output."
      ]
    },
    {
      "id": "inspect",
      "task": "Inspect existing dopemux CLI structure and task-orchestrator adapter read methods only.",
      "validation": [
        "Produce evidence ledger naming exact files and read-only methods."
      ]
    },
    {
      "id": "implement",
      "task": "Add read-only CLI commands for orchestrator status, queue, blockers, and daily summary with partial-failure handling.",
      "validation": [
        "No writes, no transitions, no bridge-authority claims, no destructive tools."
      ]
    },
    {
      "id": "test",
      "task": "Add unit tests using mocked adapter responses for success, timeout, and partial failure.",
      "validation": [
        "Run compileall and targeted pytest; capture exit codes."
      ]
    },
    {
      "id": "review",
      "task": "Inspect diff and run codereview/precommit stage.",
      "validation": [
        "Diff contains only allowlisted files and no write-capable command behavior."
      ]
    }
  ]
}
```

## Open Questions Blocking Larger Integration

1. Is `dopetask-canonical-spec.json` the same contract as any dopeTask-owned
   `task_packet.schema.json`, or is there a real schema split?
2. Is there dopeTask version drift between this repo's expected execution
   wrapper and the currently installed external `dopetask` runtime?
3. Should `services/task-orchestrator/task_orchestrator/app.py` remain as a
   hard-failing tripwire or be quarantined?
4. Who owns final acceptance authority when proof exists but signer separation
   is absent?
5. What is the real event-consumer state for task-orchestrator to ConPort,
   dope-memory, and proof?
6. Should the upstream 13-tool MCP task-orchestrator write tools be exposed to
   agents before source and proof envelopes are tied into this repo?
7. Should task-orchestrator ever write memory directly? This document says no.
8. Should dopeUI and dope-agent enter the next cross-repo pass? Likely yes, but
   current repo authority is insufficient.
9. Is `services/mcp-integration-bridge` dead, orphaned, or still reachable?
10. Which proof schema wins for merge-readiness automation?

TP-DMX-ORCH-001 reconciliation note: the repo-local validator added by
TP-DMX-ORCH-003 validates this repository's
`dopetask-canonical-spec.json` and a local proof-governance shape only. It does
not prove equivalence with an external dopeTask-owned schema, installed
dopeTask runtime version, Supervisor Ledger acceptance contract, or final
merge-readiness proof schema. Those remain `UNKNOWN` until separately verified.

## Bottom Line

Build read-only daily/status integration first. Then build packet/proof
validation. Only after those are proven should transition mutation, event
consumers, GitHub automation, or memory/index writes be considered.

Correct authority shape:

```text
dopemux = operator console
task-orchestrator = workflow state/view/transition authority
dopetask = execution/proof runtime
ConPort = structured decisions/progress/context
dope-memory = chronicle receipts
dope-context = code/docs retrieval
dopecon-bridge = adapter/proxy/event transport
Supervisor Ledger = acceptance/governance
```

Any design that collapses those into one orchestration owner violates current
repo authority.
