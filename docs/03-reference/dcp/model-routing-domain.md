---
id: model-routing-domain
title: Model Routing Domain
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-09'
last_review: '2026-06-09'
next_review: '2026-09-07'
prelude: Model Routing Domain (reference) for dopemux documentation and developer
  workflows.
---
# DCP Routing Domain Model

**Status**: Design/domain-model only. MVP-0001.

## Clean origin/main baseline

- `origin/main` at `2ffcc2d48fef99ce73a0befe388de67463a25e00`
- `config/ai/model-routing.policy.yaml` exists on clean origin/main
- `.github/workflows/gemini-review.yml` exists on clean origin/main

## Advisory policy warning

`model-routing.policy.yaml` on origin/main is **advisory design input only**.

It explicitly states it is not runtime routing authority.
Do not treat it as a router.

## Runtime health warning

- LiteLLM is unhealthy (carried from 0000E)
- Routing alias contract is stale (unresolved)
- PAL model inventory is not locked for runtime
- MCP/slash/workflow registry is incomplete

These are **stop conditions**, not runtime dependencies.

## Domain objects

Nine domain objects defined as strict JSON schemas:

1. `DcpRoutingClassification` — Risk class + automation safety
2. `DcpRoutingDecision` — Classification + lane + stops + authority + audit
3. `DcpExecutionLane` — Lane with backend authority constraints
4. `DcpModelSlot` — Model slot with evidence quality (NOT runtime health)
5. `DcpBackendRunner` — Backend runner with authority level
6. `DcpAuthoritySurface` — Authority surface with canonical owner
7. `DcpAuditRoute` — Audit route with PAL chain + distinct verdict flag
8. `DcpStopCondition` — Stop condition with evidence + resolution
9. `DcpRoutingProofExtension` — Additive proof extension (NOT replacement)

All schemas enforce:
- `"additionalProperties": false`
- Controlled enums for dangerous fields
- No arbitrary selectors for backend_id, runner_id, model_id, path, url, port, shell_command, mcp_server, mcp_tool, workflow_name, github_action

## Classification rules

Risk classes: R0_READ through R7_FORBIDDEN

Safe automation: safe_read, safe_projection, requires_operator, unsafe_until_proven, forbidden, unknown

Evidence quality distinguishes config-only from runtime-verified.

## Execution lanes

Lanes define allowed risk classes and backend authority.

Design-only lane permits R0_READ and R1_DOCS with backend_only authority.

## Model slot evidence quality

Model slots track evidence quality, not runtime health.

`config_only: true` implies `runtime_healthy: false`.

Config-only model evidence cannot be treated as runtime healthy.

## Backend runner authority

Runners declare authority level: backend_only, validation_only, read_only, adapter, advisory, forbidden, unknown.

OpenCode is constrained to `backend_only` with `open_code_backend_only: true`.

## Authority surfaces

Authority surfaces declare:
- Authority type (pm, memory, retrieval, workflow, bridge_proxy, runtime, decision, progress, chronicle, unknown)
- Canonical owner (conport, leantime, task-orchestrator, dope-memory, dope-context, dopemux, dopetask, none, unknown)
- Unknown status flag

`dopecon-bridge` is bridge_proxy, not canonical authority.

Agent runtime authority remains UNKNOWN.

## Audit route

Audit routes declare:
- `pal_chain_enabled`
- `self_certification_blocked`
- `auditor_verdict_distinct` (auditor_verdict is separate from validation_state)

Dual auditor route requires two independent audits before supervisor review.

## Proof extension

`DcpRoutingProofExtension` is **additive**, not a replacement for existing proof families.

It captures routing-specific evidence for the decision.

Existing proof families (TP, COMMAND_LOG, AUDIT_*, etc.) remain authoritative.

## Stop conditions

21 hard stop conditions defined.

Key stops for 0001:
- LiteLLM unhealthy
- Stale alias contract
- Arbitrary selector allowed
- Forbidden file touched
- OpenCode authority leak
- auditor_verdict merged into validation_state
- Proof family collapsed

## Forbidden shortcuts

- Do not promote advisory policy to runtime authority
- Do not treat config-only model evidence as runtime healthy
- Do not mark unknown MCP/slash/workflow surfaces as safe
- Do not enable Dopetask execution
- Do not enable Task Orchestrator writes
- Do not make OpenCode authoritative
- Do not collapse proof families

## What this packet does not implement

- Does not implement routing
- Does not prove runtime routing health
- Does not lock model slots
- Does not classify all MCP/slash/workflow surfaces
- Does not make OpenCode authoritative
- Does not enable Dopetask execution
- Does not enable Task Orchestrator writes
- Does not make PR Steward merge authority
- Does not collapse proof families
- Does not replace existing proof artifacts

0001 is design/domain-model only.
