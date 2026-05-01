---
id: 05-claude-mem
title: 05 Claude Mem
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-01'
last_review: '2026-05-01'
next_review: '2026-07-30'
prelude: 05 Claude Mem (explanation) for dopemux documentation and developer workflows.
---
# DR Pack 05: Claude-Mem / claude-mem

Access date: 2026-04-28

## Objective

Research current Claude-Mem hook, worker, memory, and context-injection patterns and map them to Dopemux hook ingestion, dope-memory chronicle, and ConPort promotion design.

## Source Seeds

- https://github.com/customable/claude-mem
- https://github.com/thedotmack/claude-mem
- https://docs.claude-mem.ai/
- https://docs.claude-mem.ai/hooks-architecture
- https://www.npmjs.com/package/claude-mem
- `docs/research/mcp-customization/data/upstream-source-manifest.json`
- Dopemux memory seed: `services/working-memory-assistant/dope_memory_main.py`
- Dopemux memory docs seed: `docs/03-reference/planes/memory-plane.md`

Observed source status:

- `customable/claude-mem`: latest release v3.0.4 published 2026-01-25T22:21:34Z.
- `thedotmack/claude-mem`: latest release v12.4.8 published 2026-04-28T02:41:54Z.
- npm `claude-mem`: latest 12.4.8, repository points to `thedotmack/claude-mem`.
- docs hooks architecture URL returned HTTP 200.

## Required Extraction Fields

- hook event names and payload schemas
- worker/service architecture
- context injection behavior
- storage backends
- search/index behavior
- privacy/redaction model
- replay/idempotency model
- correction/delete model
- portability beyond Claude Code
- package/release lineage

## Dopemux Boundary Constraints

- CLAUDE.md or injected summaries must not become canonical memory.
- Raw tool output must be redacted before storage and before promotion.
- dope-memory owns chronicle receipts; ConPort owns structured decisions/progress.
- Hook names from Claude Code are not automatically portable to Codex, Gemini, Copilot, or other runtimes.


## Full Boundary Baseline

Every server-specific answer must preserve all of these Dopemux boundaries: dopemux is operator/control only; dopetask is external execution after wrapper handoff; Leantime owns passive PM metadata and snapshots; task-orchestrator owns workflow transitions and workflow views; ConPort owns structured decisions, progress, project context, custom data, and relationships; dope-memory owns chronicle receipts and evidence history; dope-context owns derived code/docs retrieval; dopecon-bridge is adapter/proxy/event transport only; Serena is support/code-intelligence unless runtime authority is proven.

## Authority Conflict Checks

- Does upstream overwrite or delete memory without audit semantics?
- Does summary memory replace evidence chronology?
- Does hook ingestion capture secrets?
- Does context injection hide provenance?
- Which lineage is active: customable, thedotmack, package registry, or docs site?

## Output Contract

Return exactly:

- `items`: Top-3 actionable findings.
- `more_count`
- `next_token`
- evidence matrix
- fact vs inference separation
- UNKNOWN list
- blocker list
- responsibility collision matrix
- implementation slices with validation

## UNKNOWN / Blocker Handling

Keep `customable` and `thedotmack` lineage separate until migration/package ownership is proven. Mark non-portable hook behavior UNKNOWN for non-Claude runtimes.

## Adopt / Adapt / Reject / Hide / Defer Table Requirements

Include rows for:

- hook capture
- queue/worker
- redaction
- context injection
- memory search
- SQLite/Qdrant or other storage
- deletion/correction
- replay/idempotency
- Claude-only behavior

## Validation Requirements

- Require redaction tests before storage.
- Require idempotency by `event_id`.
- Require replay/correction tests.
- Require proof that summaries are derived, not canonical.
