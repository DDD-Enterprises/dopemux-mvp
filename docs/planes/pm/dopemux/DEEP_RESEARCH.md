---
id: DEEP_RESEARCH
title: Deep Research
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-02-13'
last_review: '2026-02-13'
next_review: '2026-05-14'
prelude: Deep Research (explanation) for dopemux documentation and developer workflows.
---
# Deep Research Spec (PACKET DR-1)

## Purpose
Resolve Open Questions into a structured, evidence-anchored bundle. Research happens in the Supervisor plane, and outputs are artifacts (bundles), not edits to history.

## Scope
- Triggered when FACT ANCHORS expose UNKNOWNs or external info (pricing, limits, undocumented MCP behavior) is needed.
- Operates on docs in `docs/planes/pm/dopemux/*`.
- Outputs to `docs/planes/pm/dopemux/research/`.

## Non-negotiable invariants
- Every claim must be labeled: Observed / Inferred / Assumption / Unknown.
- Hard rule: No source → no claim.
- Research does not modify spec docs directly; only proposes deltas.
- No invented pricing or inferred API limits unless labeled INFERRED.

## Required Structure

### 1) BUNDLE_INDEX.json
Canonical JSON tracking metadata, input sources, claim counts, and status (draft|validated|needs-more-evidence). Static sorting, no timestamps.

### 2) SOURCES_LEDGER.md
Table format linking Source ID to Type, URL/Path, Authority Level, and Notes.
Authority Levels: REPO_PRIMARY, OFFICIAL_DOC, OFFICIAL_PRICING, RELEASE_NOTE, ISSUE_THREAD, THIRD_PARTY, UNKNOWN.

### 3) CLAIMS_LEDGER.md
Every claim must have a Statement, Type (OBSERVED, VERIFIED_EXTERNAL, INFERRED, ASSUMPTION, UNKNOWN), Source IDs, and Confidence.
Unverified claims must appear in Open Questions.

### 4) EVIDENCE.md
Short quoted snippets with file paths (line-range) or URLs. No long dumps or summaries without citations.

### 5) OPEN_QUESTIONS.md
Each question includes what is unknown, why it matters, and the resolution path (file, command, URL).

### 6) PROPOSED_SPEC_DELTAS.md
Minimal diffs to spec docs with File, Section, Action (Add/Modify/Clarify), Justification, and Claim IDs.

## Research Rules
1. No invented pricing numbers.
2. No inferred API limits unless labeled INFERRED.
3. No summarizing without citations.
4. No mixing policy decisions into factual claims.
5. Do not modify spec docs directly.

## Stop Conditions
Stop and mark bundle as `needs-more-evidence` if:
- Conflicting sources.
- No authoritative source available.
- Claim depends on proprietary undocumented behavior.
- Tool capability cannot be verified.

## Lightweight Option
If overhead is too high, skip `BUNDLE_INDEX` and `EVIDENCE`. Provide only `SOURCES_LEDGER`, `CLAIMS_LEDGER`, `OPEN_QUESTIONS`, and `PROPOSED_SPEC_DELTAS`.
