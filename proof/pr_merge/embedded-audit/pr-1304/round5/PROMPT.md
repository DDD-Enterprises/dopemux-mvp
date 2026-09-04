# Independent embedded audit — PR #1304, round 5 (delta, repo mounted)

You are an independent auditor. You did not write this code. Your job is to
find what is wrong with it. CLOSED is only appropriate if you actively tried
to break the change and failed.

**You have real filesystem access this round.** A directory has been mounted
containing the relevant repository subtree. Read files directly. Do not rely
solely on the diff below — round 4 raised a HIGH finding that was wrong
precisely because it could only see a diff. Verify claims against source.

## Custody

* Repository: `DDD-Enterprises/dopemux-mvp`, PR **#1304** (draft)
* Head under audit: **`982ecd107`**
* Round-4 head: `e80cda77d` (verdict **OPEN**)
* Remediation delta: `e80cda77d..982ecd107` — 3 files, +66/−11, in
  `REMEDIATION_DELTA.diff` at the mount root
* Suite at this head: 121 passed, 1 skipped, 0 failed

**Custody proof requested:** recompute the SHA-256 of
`services/dope-context/src/embeddings/model_registry.py` and report it in
`subject_hash_recomputed`. State the algorithm you used.

## Mounted layout

```
services/dope-context/src/**            the service under audit
services/dope-context/tests/**          its tests
src/dopemux/dcp/red_lane_rules.py       the red-lane FORBIDDEN_PATHS
.claude/hooks/dcp_surface_guard.py      the PreToolUse guard that reads them
tests/test_dcp_surface_guard.py         repo-level guard tests
proof/round4/VERDICT.json               round-4 verdict
proof/round4/REMEDIATION.json           implementer's dispositions
REMEDIATION_DELTA.diff                  e80cda77d..982ecd107
```

## Round-4 findings and what was done — verify each independently

1. **`SILENT_TRUNCATION` (HIGH)** — you found that `voyage-code-4` silently
   truncates above 32K and said no upstream enforcement was added.
   **The implementer REFUTED this**, claiming `VoyageEmbedder.embed()` and
   `embed_batch()` already raise on oversize inputs unless `truncation=True`,
   and that no embedding caller passes it.
   **You can now read `services/dope-context/src/embeddings/voyage_embedder.py`
   directly. Adjudicate: was the refutation correct?** If the guard exists but
   has a hole (a path that bypasses it, a caller that sets `truncation=True`,
   a code path that embeds without going through those methods), say so.
2. **`WEAKENED_TEST_ASSERTIONS` (HIGH)** — accepted. Two tests were rewritten.
   **Verify the replacements are not themselves tautologies.** Specifically:
   can `test_endpoint_change_changes_collection_identity` actually fail? Can
   `test_index_and_query_paths_both_derive_models_from_the_profile` actually
   fail? Reason about what source change would break each. A source-scanning
   test that greps for a substring is weak if the substring could survive a
   real regression — assess that honestly.
3. **`INFERRED_MAX_TOKENS` (MEDIUM)** — accepted; `max_request_tokens` lowered
   `320_000` → `300_000`, the measured-accepted floor. Verify the value is
   consistent with how it is consumed (`partition_indices`).
4. **`STRANDED_COLLECTIONS` (HIGH)** — accepted in part; disclosure added to
   ADR-226 and the packet (not in the mount; the code is unchanged). The
   implementer argued the failure is loud and fail-closed rather than silent.
   Verify that characterisation against
   `compare_collection_manifests` in `model_registry.py`.
5. **`COMMIT_MESSAGE_DISCLOSURE` (LOW)** — not a finding; the commit does
   disclose it.

## Known-open, already identified — do not spend effort rediscovering

The `voyage-code-4` comment block in `model_registry.py` is
self-contradictory: it opens `max_request_tokens=320_000 rather than
voyage-code-3's 120_000` while the field is set to `300_000` and a later
paragraph explains the correction. Cause: a correction was appended instead of
reconciling the original sentence. Already logged for repair. **Report it only
if you find a *further* problem with it.**

## Also audit, at this head

* **Carve-out containment.** `red_lane_rules.py` now exempts `eval/**` plus
  six exact files under `services/dope-context/`. Construct bypass strings and
  test them against the actual regex. Confirm F-001 (lexical path reading) and
  F-001-A (case-variant bypass) remain closed.
* **Guard/fallback invariant.** The hardcoded `_FALLBACK_FORBIDDEN` tuple in
  `dcp_surface_guard.py` must remain a subset of the live `FORBIDDEN_PATHS`.
* **Endpoint/model coherence.** `contextualized_embed` accepts only
  `voyage-context-3`/`voyage-context-4`. Find any remaining path where a flat
  model could reach it or a contextualized model reach the flat endpoint.
  Check every construction site, cached factory, and default argument.
* **Anything else you find.** Prior rounds are not a scope limit.

## Required output

Return **only** a JSON object:

```json
{
  "verdict": "CLOSED" | "CLOSED_WITH_RISKS" | "OPEN",
  "reasoning": "<why, citing file:line you actually read>",
  "subject_hash_recomputed": "<sha256 of model_registry.py>",
  "hash_algorithm": "<what you used>",
  "round4_findings_adjudication": [
    {"id":"SILENT_TRUNCATION","implementer_disposition":"REFUTED","auditor_agrees":true,"evidence":"file:line"},
    {"id":"WEAKENED_TEST_ASSERTIONS","remediation_effective":true,"can_the_new_tests_fail":"<how>"},
    {"id":"INFERRED_MAX_TOKENS","remediation_effective":true,"evidence":""},
    {"id":"STRANDED_COLLECTIONS","characterisation_correct":true,"evidence":""}
  ],
  "residual_risks": [{"id":"","severity":"LOW|MEDIUM|HIGH|BLOCKER","detail":"","location":""}],
  "regressions_introduced": [{"id":"","severity":"","detail":"","location":""}],
  "f001_regression_check": "<evidence>",
  "bypass_attempts_considered": ["<each concrete string tested>"],
  "files_actually_read": ["<paths you opened>"]
}
```

Cite file and line for every claim. If you assert something you did not read,
say so explicitly.
