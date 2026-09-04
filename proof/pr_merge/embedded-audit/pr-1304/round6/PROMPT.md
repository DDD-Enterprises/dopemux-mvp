# Independent embedded audit — PR #1304, round 6 (delta, repo mounted)

You are an independent auditor. You did not write this code. Your job is to
find what is wrong with it. CLOSED is only appropriate if you actively tried
to break the change and failed.

**You have real filesystem access.** Read files directly; do not rely on the
diff alone. In round 4 a HIGH finding was wrongly refuted by the implementer
because that round could only see a diff. In round 5, with the repo mounted,
you overturned that refutation and were correct. Hold the same standard here.

## Custody

* Repository: `DDD-Enterprises/dopemux-mvp`, PR **#1304** (draft)
* Head under audit: **`77f96ab55`**
* Round-5 head: `982ecd107` (verdict **OPEN**)
* Delta: `982ecd107..77f96ab55` — 4 files, +73/−1, in `REMEDIATION_DELTA.diff`
* Suite at this head: 123 passed, 1 skipped, 0 failed

**Custody proof requested:** recompute SHA-256 for
`services/dope-context/src/pipeline/indexing_pipeline.py` and
`services/dope-context/src/embeddings/voyage_embedder.py`. Report both and
name the algorithm.

## Mounted layout

```
services/dope-context/src/**        service under audit
services/dope-context/tests/**      its tests
src/dopemux/dcp/red_lane_rules.py   red-lane FORBIDDEN_PATHS
.claude/hooks/dcp_surface_guard.py  the PreToolUse guard
tests/test_dcp_surface_guard.py     repo-level guard tests
proof/round5/                       round-5 verdict + dispositions
REMEDIATION_DELTA.diff              982ecd107..77f96ab55
```

## What round 5 found, and what was done

1. **`SILENT_TRUNCATION` (HIGH).** You established that
   `VoyageEmbedder.embed` / `embed_batch` declare `truncation: bool = True` as
   the default, so the per-input guards conditioned on `not truncation` never
   fired. The implementer accepted this and withdrew the round-4 refutation.

   **Fix applied:** `truncation=False` is now passed explicitly at all six
   flat embed call sites — three in `pipeline/indexing_pipeline.py`, three in
   `mcp/server.py`. `voyage_embedder.py` was deliberately **not** modified,
   on the grounds that it is outside the ADR-226 carve-out and changing a
   default would affect callers beyond this packet.

   **Adjudicate rigorously:**
   * Do the guards now actually fire for these paths? Trace the parameter
     through to the `if ... not truncation` checks.
   * **Is the call-site fix complete?** Search the whole mounted service for
     any other path that reaches a flat embedding — other `embed`/
     `embed_batch` callers, helper wrappers, cached factories, retry paths,
     the docs pipeline, autonomous indexing, anything. A fix that covers six
     call sites is worthless if a seventh exists.
   * Does anything else consume `spec.per_input_tokens` in a way that still
     assumes truncation (e.g. batch-size arithmetic)?
   * Is leaving the library default as `True` defensible, or does it leave a
     live trap for the next caller? Say so plainly either way.

2. **Weak test assertion.** You judged
   `test_index_and_query_paths_both_derive_models_from_the_profile` weak
   because substring matching survives aliasing or a hardcoded module
   constant. Two AST-based tests were added:
   `test_flat_embeds_disable_truncation` and
   `test_flat_embed_models_are_read_from_the_profile`.

   **Adjudicate:** can each actually fail? What source change would defeat
   them while leaving a real defect in place? Note the original weak
   substring test was **retained** alongside the new ones — assess whether
   that is harmless or misleading.

Round-5 items you already confirmed closed — `INFERRED_MAX_TOKENS` and
`STRANDED_COLLECTIONS` — need no re-litigation unless the delta reopens them.

## Also audit, at this head

* **Carve-out containment.** Confirm F-001 and F-001-A remain closed. Build
  concrete bypass strings and test them against the regex.
* **Guard/fallback invariant.** `_FALLBACK_FORBIDDEN` in
  `dcp_surface_guard.py` must stay a subset of live `FORBIDDEN_PATHS`.
* **Endpoint/model coherence.** `contextualized_embed` accepts only
  `voyage-context-3`/`voyage-context-4`. Find any path where a flat model
  could reach it, or a contextualized model reach the flat endpoint.
* **Correctness of the D1 change as a whole**, now that you can read all of
  it. Prior rounds are not a scope limit. If you find something nobody has
  raised in five rounds, that is the most valuable thing you can return.

## Required output

Return **only** a JSON object:

```json
{
  "verdict": "CLOSED" | "CLOSED_WITH_RISKS" | "OPEN",
  "reasoning": "<why, citing file:line you actually read>",
  "subject_hashes_recomputed": {"indexing_pipeline.py":"", "voyage_embedder.py":"", "algorithm":""},
  "round5_findings_adjudication": [
    {"id":"SILENT_TRUNCATION","now_closed":true,"fix_complete":true,"evidence":"file:line","other_flat_embed_paths_found":[]},
    {"id":"WEAK_TEST_ASSERTION","now_closed":true,"can_the_new_tests_fail":"<how>","retained_weak_test_assessment":""}
  ],
  "residual_risks": [{"id":"","severity":"LOW|MEDIUM|HIGH|BLOCKER","detail":"","location":""}],
  "regressions_introduced": [{"id":"","severity":"","detail":"","location":""}],
  "f001_regression_check": "<evidence>",
  "new_findings_not_raised_in_prior_rounds": [{"id":"","severity":"","detail":"","location":""}],
  "bypass_attempts_considered": [""],
  "files_actually_read": [""]
}
```

Cite file and line for every claim. If you assert something you did not read,
say so explicitly.
