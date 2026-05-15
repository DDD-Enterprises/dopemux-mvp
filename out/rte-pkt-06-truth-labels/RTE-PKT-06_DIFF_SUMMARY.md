# RTE-PKT-06 Diff Summary

## Runtime

`services/repo-truth-extractor/run_extraction_v5.py`

- Imports the truth-label helper.
- Adds `request_meta.truth_label_preservation`.
- Embeds truth-label records in RTE-PKT-05 artifact provenance.
- Guards deterministic schema repair, sidefill, provider targeted repair, provider envelope repair, and fail-closed fallback before merge.
- Marks comparison truth-label records as non-authoritative.
- Adds `qa/<STEP>_TRUTH_LABEL_PRESERVATION.json` rollup and QA summary.

## Helper

`services/repo-truth-extractor/lib/truth_labels.py`

- Defines protected label constants.
- Builds and validates truth-label preservation payloads.
- Preserves protected labels across candidate artifact updates.
- Records blocked upgrades and whole-artifact substitution context.
- Sanitizes secret-shaped values before records are emitted.

## Provenance helper

`services/repo-truth-extractor/lib/artifact_provenance.py`

- Accepts optional `truth_label_records`.
- Includes truth-label counts and labels in provenance summary.
- Does not change provider-facing structured output schema behavior.

## Tests

`services/repo-truth-extractor/tests/test_truth_label_preservation.py`

- Covers `UNKNOWN` through parse repair.
- Covers `CONFLICTING` through schema repair.
- Covers provider repair candidate upgrade rejection.
- Covers sidefill and prescan-derived candidate upgrade rejection.
- Covers comparison non-authoritative truth labels.
- Covers primary `OBSERVED` non-degradation and normalization rollup.

## Proof

`out/rte-pkt-06-truth-labels/`

- Contains packet manifest, schema, matrix, transition examples, test report, no-provider attestation, diff summary, and remaining unknowns ledger.

No prompt, promptset, model-map, provider route, pricing, config, compose, deployment, or external documentation files were changed.
