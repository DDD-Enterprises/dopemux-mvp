---
id: fast-dev-os-evidence-notes
title: Fast Dev OS — Evidence Notes (External Corpus Provenance)
type: reference
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-05-23'
last_review: '2026-05-23'
next_review: '2026-08-21'
prelude: Provenance documentation for external evidence bases cited by the Fast Dev OS doctrine layer (primarily the chat-context-v2 corpus).
---
# Fast Dev OS — Evidence Notes

## Relationship to governance

This document **operationalizes** the governance layer at [`docs/03-reference/governance/codex-authority-refresh.md`](../governance/codex-authority-refresh.md) by recording the **advisory source** of chat-derived evidence cited in Fast Dev OS ledgers. It **does not override** that layer. Per the governance layer, generated artifacts (including chat extracts) do not outrank runtime/source truth.

## Why this file exists

Several Fast Dev OS ledgers ([`unknown-conflicting-stale.md`](unknown-conflicting-stale.md), [`pr-ledger.md`](pr-ledger.md), [`packet-ledger.md`](packet-ledger.md), [`proof-ledger.md`](proof-ledger.md)) reference the **chat-context-v2 corpus** as advisory evidence. That corpus is an **out-of-repo** artifact at `$HOME/Downloads/dopemux-chat-context-v2/`. Reviewers and future maintainers won't have it. This file documents what it is, where it came from, and the boundaries on its use.

## The chat-context-v2 corpus

### Root path
`$HOME/Downloads/dopemux-chat-context-v2/`

### Retrieval date
Built incrementally; final reconciliation timestamp recorded in `04_reconciled/RECONCILIATION_INDEX.json` `generated_at_utc`.

### Provenance chain
1. **Source**: 63 raw chat exports from ChatGPT conversations covering Dopemux design/audit/build sessions (see `00_raw/CHAT_RAW_001..063_*.md`).
2. **Extraction**: 6-phase pipeline (bootstrap → extract → workstreams → reconcile → thread-load → quality) producing 63 V2 packets at `02_extracted/CHAT_PACKET_001..063_*.md`.
3. **Workstream mapping**: 12 per-workstream views at `03_workstreams/WORKSTREAM_MAP_*.md`.
4. **Reconciliation**: cross-packet PR/TP conflict detection + load-order priority at `04_reconciled/` (RECONCILED_MASTER_LEDGER, CROSS_PACKET_CONFLICTS, LOAD_ORDER, PR_PACKET_PROOF_MAP, RECONCILIATION_INDEX).
5. **Thread bundles**: per-thread upload sets at `05_thread_load/00_INTAKE/` through `06_VENDOR_RESEARCH/` and `HIGH_VALUE_PACKETS/`.

### Pipeline state at TP-DMX-FDOS-004 authoring time
Per `INGESTION_STATE.json`:
- `extracted_count: 63`
- `quality_counts: {A: 32, B: 31, C: 0, D: 0, F: 0}`
- `workstreams_built: true`
- `reconciled: true`
- `thread_load_built: true`
- `quality_audited: true`

### What the corpus is good for (advisory uses)
- **Cross-session UNKNOWNs** — claims independently flagged by multiple chat sessions are stronger signal than single-source flags. Cited in [`unknown-conflicting-stale.md §4`](unknown-conflicting-stale.md).
- **Cross-packet PR/TP conflicts** — chat sessions across different times claimed different statuses for the same artifact. Helps surface true contradictions vs timeline progressions. Cited in [`unknown-conflicting-stale.md §2`](unknown-conflicting-stale.md), [`pr-ledger.md`](pr-ledger.md), [`packet-ledger.md`](packet-ledger.md).
- **PR/TP citation frequency** — which artifacts get talked about most across sessions, useful for prioritizing live validation.
- **Reusable prompts and templates extracted verbatim** from sessions — many V2 packets preserve durable prompts in their section 8 that may inform `TP-DMX-FDOS-005-EXECUTOR-PROMPT-PACK`.

### What the corpus is NOT good for (forbidden uses)
- **NOT runtime authority**: chat-derived claims never outrank live runtime code/config/tests/entrypoints. Per `AGENTS.md §2`, runtime beats docs and docs beat generated artifacts.
- **NOT a substitute for live `gh pr view`**: PR statuses in the corpus are point-in-time at session date; current state may differ.
- **NOT a substitute for live `task-packets/INDEX.md`**: TP statuses in the corpus may be stale.
- **NOT a basis for `OBSERVED` claims about repo state**: any repo claim derived from the corpus must be marked `CLAIMED_CHAT` or `NEEDS_LIVE_VALIDATION`.

## Citation patterns used in this layer

Where Fast Dev OS ledgers cite the corpus, they use this pattern:

> Source: `$HOME/Downloads/dopemux-chat-context-v2/<subpath>` (external evidence base; see `evidence-notes.md`). Do NOT use a markdown link target for external paths — they will break on GitHub.

Cited corpus files include:
- `04_reconciled/RECONCILED_MASTER_LEDGER.md`
- `04_reconciled/CROSS_PACKET_CONFLICTS.md`
- `04_reconciled/PR_PACKET_PROOF_MAP.md`
- `04_reconciled/RECONCILIATION_INDEX.json`

Critical excerpts may be inlined in the citing doc (rather than only linked) so future maintainers without access to the corpus can still read the salient claim. Section-level summaries are inlined; full per-packet detail stays in the corpus.

## Reproducibility caveats

If the chat-context-v2 corpus is moved, archived, or deleted, the references above will be dead links. Mitigation options (deferred to future TPs):
1. **Copy the reconciled summaries into the repo** at `docs/02-context/chat-history/` (one-time snapshot copy; would require legal/privacy review of the chat content).
2. **Build a public-facing manifest** with content hashes for the cited files (so any future regeneration can be verified against the same source).
3. **Pin the corpus to a content-addressed storage URL** (e.g., IPFS or a cold-storage bucket).

For now, the corpus is treated as **operator-side advisory tooling** — same trust class as a notebook of meeting notes. Don't promote it to repo authority without explicit review.

## Other external evidence bases

Currently none cited. If future Fast Dev OS work cites another external corpus (e.g., a separate research repo, a chat archive, a third-party doc set), add a new section here documenting:
- Root path / URL
- Retrieval date
- What it is good for
- What it is NOT good for
- Citation pattern
- Reproducibility caveat

## Truth posture

This file is a **provenance log**, not a content store. The corpus itself is the evidence; this file just says where it came from and how to use it. When the governance layer and any chat-derived claim conflict, the governance layer wins.
