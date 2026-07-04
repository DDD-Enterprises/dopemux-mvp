---
id: gpt55-mcp-architecture-prompt-00-evidence-triage
title: GPT55 MCP Architecture Prompt 00 Evidence Triage
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-04'
last_review: '2026-07-04'
next_review: '2026-10-02'
prelude: Phase 0 GPT-5.5 prompt for evidence triage and missing input discovery.
---
# Prompt 00: Evidence Triage

You are GPT-5.5 Pro performing Phase 0 of a Dopemux MCP/service architecture review.

Do not design the architecture yet. Your job is to classify evidence quality, identify missing inputs, and decide whether later phases can proceed.

## Inputs

Use the files in `bundle-00-evidence-triage.md`.

## Authority Order

1. Current repo source, config, compose wiring, tests, and active entrypoints.
2. Current branch diffs and commit history.
3. `AGENTS.md` and architecture/governance docs.
4. `claudedocs/*` audit/design docs.
5. Transcript digest and raw transcripts.
6. Inference.

## Required Output

Produce these sections only:

1. Evidence Inventory Table: source, type, date/commit, authority level, staleness risk, use/ignore guidance.
2. Missing Input Request Table: missing input, why it matters, blocking or non-blocking, exact command/file to collect.
3. Authority Conflict List: conflict, competing sources, current winner, unresolved risk.
4. PR #1002 Reconciliation Gate: current known state, what must be live-verified, and whether later design may rely on #1002 work.
5. Proceed/Stop Decision: whether Phase 1 can proceed now.
6. Carry-Forward Facts: max 20 facts, each labeled `OBSERVED`, `INFERRED`, `PROPOSED`, or `UNKNOWN`.

Do not answer architecture questions. Do not produce a roadmap.
