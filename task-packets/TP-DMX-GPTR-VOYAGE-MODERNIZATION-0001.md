---
id: TP-DMX-GPTR-VOYAGE-MODERNIZATION-0001
title: Tp Dmx Gptr Voyage Modernization 0001
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-07-26'
last_review: '2026-07-26'
next_review: '2026-10-24'
prelude: Audit and modernize the second, independent Voyage client inside
  dopemux-gpt-researcher, which the dope-context modernization never touched.
---
# Task Packet: TP-DMX-GPTR-VOYAGE-MODERNIZATION-0001

## Objective

Audit and modernize the **second** Voyage embedding client in this repository.
`services/dopemux-gpt-researcher` ships its own standalone `VoyageClient` with
its own model table, pricing, and rate limiter, entirely independent of
dope-context. The PR #1112 modernization did not touch it, so it still runs
legacy models with stale cost figures.

## Status

`INVESTIGATION_REQUIRED`

Discovered during the PR #1112 post-merge audit as an incidental finding, not a
blocker. Scope the audit before implementing.

## Risk

`MEDIUM`

Unknown blast radius. This client is not obviously wired into the same retrieval
path as dope-context, but that has not been verified, and its cost accounting
feeds spend reporting.

## What Was Observed

`OBSERVED` during the dope-context audit, not independently investigated:

- `services/dopemux-gpt-researcher/backend/embeddings/voyage_client.py` defines
  a standalone `VoyageClient` with its own `self.models` dictionary containing
  only `voyage-3` and `voyage-context-3` — both **legacy**.
- Its embedded cost figures are `cost_per_1k = 0.00012` for both models. Current
  vendor pricing is per million tokens: `voyage-3-lite` at `$0.02`,
  `voyage-context-3` at `$0.18`. The two models are priced identically in this
  table, which cannot be right.
- Its `max_tokens` entries are `512` for `voyage-3` and `4096` for
  `voyage-context-3`. Vendor documents a 32,000-token context window for both.
- `_select_model` routes by `len(text) // 4`, the English-only heuristic the
  dope-context audit specifically flagged as unsafe for code and non-Latin text.
- `services/dopemux-gpt-researcher/backend/extraction_pipeline.py:76` defaults to
  `voyage-context-3`.
- `research_api/embeddings/voyage_client.py` appears to be a **duplicate** of the
  backend client.
- Neither file references Qdrant or any dope-context collection name, so it does
  not appear to write shared collections — but this was a grep, not a trace.

## Scope

### IN — investigation first

- determine whether this client is live, dead, or partially wired
- determine whether it shares any index, collection, or cache with dope-context
- determine whether the two `voyage_client.py` copies have diverged
- verify current model availability, limits, and pricing against vendor docs
- decide whether to modernize it, consolidate it onto the dope-context registry,
  or delete it

### IN — implementation, only if investigation says modernize

- current models and correct per-million pricing
- correct context windows
- replace the `len // 4` heuristic with model-aware counting or an explicitly
  conservative estimator
- deduplicate the two client copies
- tests

### OUT

- anything under `services/dope-context/`
- changing gpt-researcher's research behaviour or output format
- the dope-context blockers, which are tracked separately

## Invariants

- No change until the investigation establishes whether the client is live.
- If any index is shared with dope-context, model changes are a migration, not
  an edit, and this packet stops.
- Cost accounting must not silently change reported historical spend.
- No live Voyage call without explicit approval.
- No secret enters source, tests, logs, or proof.

## Allowed Files

Investigation phase is read-only. Implementation phase, if approved:

- `services/dopemux-gpt-researcher/backend/embeddings/voyage_client.py`
- `services/dopemux-gpt-researcher/research_api/embeddings/voyage_client.py`
- `services/dopemux-gpt-researcher/backend/extraction_pipeline.py`
- tests under `services/dopemux-gpt-researcher/`
- `task-packets/TP-DMX-GPTR-VOYAGE-MODERNIZATION-0001.md`

## Required Chain

`analyze -> tracer -> apilookup -> thinkdeep -> planner -> challenge -> implement -> testgen -> codereview -> precommit -> embedded-audit -> PR-Steward`

`tracer` is required: the first question is whether this code executes at all.

## Plan

1. Trace every caller of `VoyageClient` and `extraction_pipeline`. Establish
   live, dead, or partially wired. If dead, propose deletion and stop.
2. Diff the two `voyage_client.py` copies and determine which is authoritative.
3. Determine what storage the embeddings land in and whether dope-context ever
   reads it. If shared, stop and escalate — it becomes a migration.
4. Re-verify current models, context windows, and per-million pricing against
   vendor documentation, recording retrieval date and URLs.
5. Choose: modernize in place, consolidate onto
   `services/dope-context/src/embeddings/model_registry.py`, or delete.
   Consolidation is preferred if the boundary permits, because a single registry
   is what made the dope-context pricing errors findable.
6. Implement the decision, with tests.

## Exact Commands

```bash
git status --short --branch
rg -n "VoyageClient|voyage_client|extraction_pipeline" services/ scripts/ src/
diff -u services/dopemux-gpt-researcher/backend/embeddings/voyage_client.py \
        services/dopemux-gpt-researcher/research_api/embeddings/voyage_client.py
rg -n "voyage-3|voyage-context-3|cost_per_1k|max_tokens" \
   services/dopemux-gpt-researcher
python -m compileall -q services/dopemux-gpt-researcher
git diff --stat
git diff
```

## Acceptance Criteria

Investigation phase:

- a recorded determination of live, dead, or partially wired, with call sites
- a recorded determination of whether any storage is shared with dope-context
- a diff verdict on the two client copies
- a recommendation: modernize, consolidate, or delete, with rationale

Implementation phase, if approved:

- no legacy model remains a default
- pricing matches current vendor documentation, in per-million units
- context windows match vendor documentation
- the `len // 4` heuristic is gone or explicitly documented as conservative
- the duplicate client is resolved
- tests cover model selection and cost accounting

## Proof Requirements

Return verbatim: the trace output establishing liveness, the diff of the two
copies, vendor documentation URLs with retrieval date, the recommendation with
rationale, and — if implementing — base and final head SHA, `git diff`, and the
test summary before and after.

## Rollback

1. Revert the packet commits.
2. If cost accounting changed, note that historical spend figures computed under
   the old table are not retroactively corrected.

## Stop Conditions

Stop and escalate if:

- the client shares an index or collection with dope-context
- the two copies have diverged in behaviour, not just formatting
- the client turns out to be dead code, in which case propose deletion instead
- modernizing would change reported historical spend
- a live Voyage call would be required without approval

## Current Evidence

### OBSERVED

- A standalone `VoyageClient` exists with its own model table, pricing, rate
  limiter, and Redis-backed cache.
- Only legacy models `voyage-3` and `voyage-context-3` appear in that table.
- Both are priced identically at `cost_per_1k = 0.00012`.
- `max_tokens` values of 512 and 4096 do not match the vendor's 32,000.
- `extraction_pipeline.py:76` defaults to `voyage-context-3`.
- Two copies of `voyage_client.py` exist.
- No Qdrant or dope-context collection reference found by grep in those files.

### UNKNOWN

- whether any of this code is reachable at runtime
- where the embeddings are stored
- whether the two copies have diverged
- whether anything consumes the cost figures
