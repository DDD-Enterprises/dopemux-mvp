# TP-DMX-RTE-V5-TERMINAL-PROVENANCE-001 -- implementation scratch notes

Not a formal proof bundle (that is a later, out-of-scope step). Raw command
log / working notes for the independent auditor.

## S0 findings (caller inventory)

- `get_git_sha`: defined at `run_extraction_v5.py:5615` and separately (own
  copy, unchanged) at `validate_pre_live_gate_v25.py:251`. Also a distinct
  copy in `run_extraction_v3.py:2277` (out of scope, untouched). Called from
  ~11 sites in `run_extraction_v5.py` feeding RUN_MANIFEST.json,
  RUNNER_IDENTITY.json, `_reporting_deps()` (which feeds
  `reporting.py`/`rte_reports.py` writers), risk-dashboard inputs, and proof
  payloads.
- `run_batch_retrieval_and_integration`: defined once in `run_extraction_v5.py`
  (line ~24192 pre-edit), called from the `--batch-retrieve` CLI dispatch
  only. A separate, unrelated same-named function exists in
  `run_extraction_v3.py` (out of scope, untouched, does not call the v5
  version).
- `integrate_batch_results_with_webhook`: defined in `lib/batch_retriever.py`;
  imported by both `run_extraction_v5.py` and `run_extraction_v3.py` (out of
  scope) -- this is why the original int-returning function could not be
  changed in place; a companion `_detailed` function was added instead.
- `write_coverage_rollup` / `compute_run_status` / `write_run_manifest` /
  `write_runner_identity` / `write_certification_result`: canonical writers
  live in `reporting.py` + `rte_reports.py` thin wrappers, called from
  `run_extraction_v5.py`. Not touched except reused (read) for the new
  terminal-exit resolver.

Non-Git identity contract search (repo-wide, read-only, not limited to
allowlist): the only content-hash-based identity found is
`lib/intelligence_router.build_prescan_source_identity` /
`corpus_manifest_hash_identity_hash`, used by `lib/prescan/engine.py`. Its own
docstring says "local-only identity metadata used to decide whether imports
are fresh" -- it is scoped to prescan-freshness decisions only and is never
written into RUN_MANIFEST.json / RUNNER_IDENTITY.json / CERTIFICATION_RESULT.json
as a substitute for git identity. Conclusion: no repo-authoritative
non-Git *execution evidence* identity contract exists. Per system invariant
12, we did not invent one; a plain git checkout remains the only supported
evidence-producing path.

## S1 repro evidence (pre-fix, captured for own reference)

(a) Semantic-FAIL-without-exception exits 0: confirmed by reading `main()` --
    it fell off the end after the phase loop with no final exit call at all
    (implicit exit 0), regardless of the coverage rollup's `run_status`
    (which can be BLOCKED via `missing_required_artifacts_total > 0` or a
    phase status of FAIL, computed by `compute_run_status`, without any
    exception being raised).

(b) Batch-outcome bare-int collapse: confirmed by reading
    `run_batch_retrieval_and_integration` pre-fix -- `return 0` on missing
    module, missing API key, and event-store construction failure, then
    `sys.exit(0 if integrated >= 0 else 1)` at the call site, which is
    always true for a non-negative int, i.e. always exit 0.

(c) UNKNOWN git sha unblocked: confirmed by reading `get_git_sha` -- catches
    any exception and returns the literal `"UNKNOWN"`, which flowed
    unchecked into RUN_MANIFEST.json / RUNNER_IDENTITY.json / cert payloads
    with no gate anywhere in the phase-execution path.

## S4 baseline-vs-fixed regression found and repaired (in-scope)

`test_run_extraction_v5_operator_safety.py::test_dry_run_output_omits_unknown_failure_spotlight`
newly failed after the RTE-001 exit-code fix landed (real subprocess dry run,
exit 1 instead of 0). Root cause (traced, not out-of-scope): the default
cost profile ("value-default", $5.00) initializes the spend tracker even for
`--dry-run` runs; the dry-run request-meta stub lacks `response_summary.usage`
(no real request was ever sent), and `record_request_cost` treated "usage
unavailable" as a genuine cost-cap breach, setting
`cost_abort_triggered=True` with `abort_reason="cost_cap_usage_unavailable"`
even though phase A completed with `status=PASS`. This was previously masked
because `main()` exited 0 unconditionally. Repaired in-scope
(`run_extraction_v5.py`, allowlisted) by tagging dry-run request meta with
`"dry_run": True` and making `record_request_cost` a no-op for dry-run meta
(no real spend occurred, nothing to cap). Verified via direct subprocess
repro pre/post fix (see commands below) and via the full test file re-run
(all pass post-fix).

Repro commands used:
```
python services/repo-truth-extractor/run_extraction_v5.py --phase A --step A0 \
  --dry-run --ui plain --run-id probe2 --output-root /tmp/dryrun_repro2
echo $?      # 1 pre-fix (run_status=COST_ABORTED), 0 post-fix (run_status=OK)
```
