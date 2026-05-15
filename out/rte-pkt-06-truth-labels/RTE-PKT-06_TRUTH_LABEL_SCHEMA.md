# RTE-PKT-06 Truth Label Schema

## Runtime surface

Runtime partition success JSON now carries `request_meta.truth_label_preservation`.

Schema version: `rte_truth_label_preservation_v1`

The same records are also embedded under `request_meta.artifact_provenance.truth_label_records` so the RTE-PKT-05 provenance companion and the RTE-PKT-06 semantic companion can be inspected together.

`normalize_step` writes a proof-visible QA companion when records exist:

`qa/<STEP>_TRUTH_LABEL_PRESERVATION.json`

The normal QA payload includes a `truth_label_preservation` summary with record counts, protected record counts, partition count, and rollup path.

## Protected labels

Protected labels:

- `UNKNOWN`
- `CONFLICTING`

These labels are not silently converted to:

- `OBSERVED`
- `INFERRED`
- `CLAIMED`
- `RECOMMENDED`
- unlabeled fact
- `primary_observed` provenance when a derived lane changed or supplied the field

## Record fields

Every truth-label record includes:

- `truth_label`
- `previous_truth_label_if_changed`
- `label_source`
- `label_reason`
- `evidence_refs`
- `conflicting_values_if_any`
- `unknown_reason_if_any`
- `resolution_reason_if_any`
- `provenance_kind`
- `source_lane`
- `generated_at`

Runtime records also include:

- `artifact_name`
- `field_path`
- `item_id`
- `attempted_truth_label_if_any`
- `transition_action`
- `authoritative`
- `source_phase`
- `source_step_id`
- `source_partition_id`
- `reason_code`

## Transition rules

Default behavior is preservation:

- `UNKNOWN -> UNKNOWN`
- `CONFLICTING -> CONFLICTING`

Derived lanes can add candidate context, but they cannot prove a protected label by themselves.

A protected label can move to `OBSERVED` only when the candidate carries source-backed evidence refs and an accepted label source such as `runtime_source`, `source_excerpt`, `source_artifact`, `test_fixture`, `higher_authority`, or `repo_truth`. `CONFLICTING -> OBSERVED` also requires `resolution_reason_if_any`.

Rejected attempted upgrades are recorded with `transition_action=blocked_protected_label_upgrade` and `attempted_truth_label_if_any`.

Rejected attempts to omit a protected label from a matching artifact item are recorded with `transition_action=blocked_protected_label_drop`.

Whole-artifact substitutions that remove protected labeled values preserve the original label context in transition records with `transition_action=protected_label_original_context_preserved`.

## Redaction boundary

Truth-label records store references, reason codes, booleans, and sanitized context. They do not store:

- raw secret-shaped values
- unredacted failed sidecar content
- raw provider payload text

Evidence excerpts are converted to safe structural refs such as `path:start-end`.
