---
id: gpt55-mcp-architecture-phased-runbook
title: GPT55 MCP Architecture Phased Runbook
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Phased runbook for GPT-5.5 MCP architecture prompts and bundles.
---
# Phased GPT-5.5 Runbook

Use this runbook when running the architecture investigation through GPT-5.5 Pro web. The point is to keep GPT-5.5 from collapsing evidence triage, branch adjudication, target design, implementation planning, and UX design into one lossy answer.

## Run Order

0. Preflight the two recent synthesis attachments listed in `source-manifest.md`; classify them as advisory until live repo/GitHub evidence confirms the claims.
1. `prompt-00-evidence-triage.md` with `bundle-00-evidence-triage.md`
2. `prompt-01-current-state.md` with `bundle-01-current-state.md`
3. `prompt-02-branch-adjudication.md` with `bundle-02-branch-adjudication.md`
4. `prompt-03-target-architecture.md` with `bundle-03-target-architecture.md`
5. `prompt-04-roadmap.md` with `bundle-04-roadmap.md`
6. `prompt-05-operator-ux.md` with `bundle-05-operator-ux.md`
7. `prompt-06-final-synthesis.md` with `bundle-06-final-synthesis.md`

## Stop Gates

- Stop after Phase 0 if GPT-5.5 requests missing input that materially affects authority, branch state, PR #1002 status, or runtime truth.
- Stop after Phase 2 if Exa, PAL, Serena, or dead-surface disposition requires a human decision before target design.
- Stop after Phase 2 if PR #1002 is still open and the proposed architecture depends on #1002 changes as if they were already merged.
- Stop after Phase 3 if GPT-5.5 proposes an authority change that conflicts with Memory Trinity or Task Orchestrator ownership.
- Stop after Phase 4 if roadmap slices are too broad to become Task Packets.

## Chunking Rules

- Upload or paste one phase at a time.
- Keep each phase answer bounded to the requested output schema.
- Carry forward only the prior phase's final tables, open questions, and explicit decisions.
- Do not paste raw transcript JSONL unless GPT-5.5 identifies a precise disputed claim.
- Do not paste raw compose output that includes environment values.
- Chunk PR evidence separately from target-design evidence. PR reconciliation is a gate, not architecture by itself.

## Collection Priority

If time is limited, collect the bundles in this order:

1. Phase 0 and Phase 1 bundles.
2. Phase 2 branch evidence plus the recent reconciliation synthesis attachments.
3. Phase 3 authority and target-design sources.
4. Phase 4 test/proof data.
5. Phase 5 UI/Cockpit sources.

Phase 6 is synthesis-only; it should use summaries from Phases 0-5 rather than new raw data.
