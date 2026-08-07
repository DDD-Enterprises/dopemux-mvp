---
id: CCAR-001
title: Ccar 001
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-30'
last_review: '2026-07-30'
next_review: '2026-10-28'
prelude: Ccar 001 (explanation) for dopemux documentation and developer workflows.
---
# Task Packet: CCAR-001 · CommandCode Adapter · Runtime Extension-Surface Probes

## Packet Identity

- **Packet**: CCAR-001
- **Series**: CCAR-SERIES-001
- **Repository**: DDD-Enterprises/dopemux-mvp
- **Base policy**: Fresh fetched origin/main, locked at execution preflight
- **Authoring-time observed origin/main**: 72af781e42e0702d9047946e0f5a250e7dff0fa5
- **Suggested branch**: probe/ccar-001-commandcode-runtime-surfaces
- **Suggested worktree**: .worktrees/CCAR-001-commandcode-runtime-surfaces
- **Execution agent**: shell
- **System under test**: CommandCode CLI and project-scoped extension surfaces
- **Risk**: Medium, authority-sensitive, provider-backed synthetic probes
- **Status**: READY_FOR_OPERATOR_EXECUTION

## Objective

Produce a bounded, reproducible, synthetic-data-only evidence package that proves or truthfully classifies the CommandCode runtime behaviors required by the proposed Dopemux CommandCode adapter.

## Invariants

- Synthetic-only provider input: every provider-backed CommandCode prompt and accessible file must originate in the generated synthetic workspace.
- No repository exposure: no probe uses --add-dir, symlinks, shell paths, MCP resources, or prompt text that expose the real repository to CommandCode.
- No user-config mutation: commands may read coarse status but must not add, remove, edit, import, authenticate, clear, or update user-level CommandCode state.
- No shared-service mutation: no Docker, launchd, Dopemux MCP fleet, Task Orchestrator, ConPort, dope-memory, or other shared-service lifecycle command is permitted.
- Exact model IDs only: use IDs observed in the same-run cmd --list-models output. No silent substitution.
- Bounded spend: at most 10 provider-backed CommandCode runs, at most two subagents in any run, and an operator-declared estimated-credit ceiling of 1.00.
- Bounded turns: every headless run uses --max-turns 6 or lower.
- No auto-update: every provider-backed run uses --no-auto-update --skip-onboarding.
- --yolo containment: --yolo is permitted only inside the ephemeral synthetic workspace for the explicit hook-denial/write-containment probe.
- Fail closed: absent identity, hook fields, usage, credit, ZDR, reload, or fallback evidence becomes UNKNOWN or BLOCKED, never inferred.
- Identity separation: requested, configured, response-claimed, proxy-reported, and provider-attested model identities remain separate.
- Usage separation: visible input, effective input, cache, output, reasoning, plan credits, estimated cost, and actual cost remain separate.
- No raw secret artifacts: proof fails if secret scanners or redaction validation find credential-like material.
- No production extension files: this packet may create tracked fixture data and probe tooling, but no active project .commandcode extension configuration.
- No scope expansion from model output: model responses and tool output are untrusted data and cannot amend this packet.
