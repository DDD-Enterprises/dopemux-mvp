# RTE-PKT-06 Remaining Unknowns

## Prescan value merge path

No direct prescan-derived value merge into normalized artifacts was observed in the allowed runtime paths inspected for this packet. The helper guards `prescan_derived` candidates if such a merge path is added or surfaced later, but current runtime proof remains helper-level rather than end-to-end prescan integration proof.

Recommendation: if a later packet introduces or identifies a concrete prescan value merge path, call `preserve_protected_truth_labels` before merge and add a runtime fixture for that exact path.

## Envelope repair fixture

Provider envelope repair uses the same truth-label guard as targeted repair, but this packet does not include a dedicated envelope fixture.

Recommendation: add an envelope-specific fixture if future work changes envelope repair behavior.

## Fail-closed fallback fixture

The fail-closed empty-payload fallback is guarded for protected original context, but this packet does not add a dedicated runtime fixture for that fallback path.

Recommendation: add a focused fixture if fallback semantics become a frequent operator path.

## Semantic label universe

The runtime helper treats explicit `truth_label` fields as semantic truth labels. It does not reinterpret unrelated fields such as pricing confidence or provider readiness status that may contain the string `UNKNOWN`.

Recommendation: keep semantic truth labels explicit. If future artifact schemas add another truth-label key, update the helper and tests rather than broad string matching.
