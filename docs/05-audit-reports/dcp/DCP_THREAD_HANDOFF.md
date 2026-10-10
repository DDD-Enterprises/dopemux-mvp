---
id: DCP_THREAD_HANDOFF
title: Dcp Thread Handoff
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-11'
last_review: '2026-06-11'
next_review: '2026-09-09'
prelude: Dcp Thread Handoff (reference) for dopemux documentation and developer workflows.
---
# DCP Thread Handoff

This packet rebuilt the read-only facade discovery pack from the saved GPT-5.5 recon source and current repo state at `ac3a26f746e472feb8a31f1b634d8c0432e08db6`. It inspected source/config/docs with shell read commands only and produced a bounded phase-1 facade direction for GPT-5.5 design work.

## What Codex Inspected

- Repo identity, branch, head, status.
- MCP and HTTP route declarations.
- Proof, handoff, and evidence source references.
- Targeted system references for dope-memory, ConPort, dope-context, task-orchestrator, Repo Truth Extractor, and dopecon-bridge.

## Confirmed Safe Phase-1 Surfaces

Use filesystem proof fetchers, repo state snapshot, and wrapped read-only/search endpoints only after source allowlisting, redaction, and freshness labels.

## Denied / Unsafe Surfaces

- Raw MCP exposure.
- Tunnel setup in this packet.
- Mutating routes.
- Direct ConPort/dope-memory writes.
- Task-orchestrator transitions.
- Raw local path browsing.

## Unknowns Requiring GPT-5.5 Design Decision

- Exact wrapper schemas and size limits.
- Whether POST search/replay endpoints are acceptable behind read-only wrappers.
- Freshness model for stale proof versus current branch truth.

## Recommended Facade Architecture

- Local facade only.
- Static backend allowlist.
- Tool-specific adapters, not raw proxying.
- Per-result authority label.
- Per-result freshness label.
- Per-result redaction state.
- Deny mutating routes by method and handler classification.
- Separate proof filesystem adapter from runtime adapters.
- Treat bridge output as proxy unless upstream authority is explicit.
- Require network-deny test harness before runtime confidence claims.

## Proposed Next GPT-5.5 Pro Design Prompt Inputs

- `RUNTIME_SURFACE_INVENTORY.md`
- `READ_ONLY_SURFACE_INVENTORY.json`
- `AUTHORITY_AND_RISK_REGISTER.md`
- `PROPOSED_FACADE_TOOLS.md`
- `PROOF_BUNDLE_AND_EVIDENCE_SOURCES.md`

## Artifact List Produced

See `proof/TP-DCP-MCP-RO-0001/PROOF.json`.

## Do Not Do This

Do not expose all MCP tools, run tunnel setup, call mutating routes, infer bridge authority, attach secrets, or claim repo-wide tests passed.
