# RTE-PKT-05 Provenance Schema

## Runtime surface

Runtime partition success JSON now carries `request_meta.artifact_provenance`.

Schema version: `rte_artifact_provenance_v1`

Top-level keys:

- `schema_version`
- `generated_at`
- `field_records`
- `artifact_records`
- `summary`

## Field records

Every derived field record includes:

- `field_path`
- `artifact_name`
- `provenance_kind`
- `source_lane`
- `source_phase`
- `source_step_id`
- `source_partition_id`
- `reason_code`
- `confidence_if_available`
- `original_value_present`
- `original_value_ref`
- `replacement_value_present`
- `repair_or_sidefill_provider_if_any`
- `repair_or_sidefill_model_id_if_any`
- `request_meta_ref_if_any`
- `failed_sidecar_ref_if_any`
- `generated_at`

Allowed `provenance_kind` values:

- `primary_observed`
- `deterministic_parse_repair`
- `deterministic_schema_repair`
- `provider_repair`
- `sidefill`
- `enrichment`
- `comparison`
- `prescan_derived`
- `unknown_derived`

Field records intentionally do not include raw values. `original_value_ref` is a structural reference such as `ARTIFACT.json:payload.items[0].path` or a request-metadata reference.

## Artifact records

Every artifact record includes:

- `artifact_name`
- `provenance_kind`
- `source_lane`
- `source_phase`
- `source_step_id`
- `source_partition_id`
- `reason_code`
- `derived_field_count`
- `primary_observed_field_count`
- `failed_sidecar_refs`
- `raw_artifact_refs`
- `request_meta_refs`
- `prescan_influence_refs_if_any`
- `comparison_refs_if_any`
- `generated_at`

Primary-only artifacts are recorded as `primary_observed` with `derived_field_count = 0`.

Mixed artifacts use the single derived kind when only one derived lane touched fields, otherwise `unknown_derived`.

## Normalization companion

When raw partition provenance exists, `normalize_step` writes:

`qa/<STEP>_ARTIFACT_PROVENANCE.json`

The companion aggregates raw partition field and artifact provenance without changing normalized artifact payload schemas.

## Redaction boundary

The provenance records store paths, request-meta references, provider/model identifiers, booleans, counts, and reason codes. They do not store:

- raw secret-shaped values
- failed sidecar content
- raw provider payload text
- raw provider response text
