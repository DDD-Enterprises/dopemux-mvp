# RTE-PKT-05 Provenance Examples

Examples are redacted structural shapes. They intentionally omit raw values.

## Primary observed artifact record

```json
{
  "artifact_name": "DOC_INDEX.partX.json",
  "provenance_kind": "primary_observed",
  "source_lane": "primary",
  "derived_field_count": 0,
  "primary_observed_field_count": 6,
  "raw_artifact_refs": ["raw/D1__D_P0001.json"]
}
```

## Deterministic parse repair field record

```json
{
  "artifact_name": "DOC_INDEX.partX.json",
  "field_path": "payload.items[0].path",
  "provenance_kind": "deterministic_parse_repair",
  "source_lane": "parse_repair",
  "reason_code": "primary_response_parse_repair",
  "original_value_present": false,
  "replacement_value_present": true,
  "request_meta_ref_if_any": "request_meta.response_parse_provenance"
}
```

## Deterministic schema repair field record

```json
{
  "artifact_name": "DOC_INDEX.partX.json",
  "field_path": "payload.items[0].path",
  "provenance_kind": "deterministic_schema_repair",
  "source_lane": "schema_repair",
  "reason_code": "schema_path_repair:single_item_single_file:schema_missing_key:path",
  "original_value_present": false,
  "replacement_value_present": true,
  "request_meta_ref_if_any": "request_meta.schema_gate_context"
}
```

## Provider repair field record

```json
{
  "artifact_name": "DOC_INDEX.partX.json",
  "field_path": "payload.items[0].line_range[0]",
  "provenance_kind": "provider_repair",
  "source_lane": "repair",
  "repair_or_sidefill_provider_if_any": "openrouter",
  "repair_or_sidefill_model_id_if_any": "model-from-contract",
  "request_meta_ref_if_any": "request_meta.strict_route_attestations"
}
```

## Sidefill field record

```json
{
  "artifact_name": "CAP_NOTICES.partX.json",
  "field_path": "payload.items[0].id",
  "provenance_kind": "sidefill",
  "source_lane": "sidefill",
  "reason_code": "missing_expected_artifact:CAP_NOTICES.partX.json:missing_expected_artifacts:CAP_NOTICES.partX.json",
  "repair_or_sidefill_provider_if_any": "openrouter",
  "repair_or_sidefill_model_id_if_any": "model-from-contract"
}
```

## Comparison field record

```json
{
  "artifact_name": "OUT.json",
  "field_path": "payload.items[0].id",
  "provenance_kind": "comparison",
  "source_lane": "comparison",
  "reason_code": "comparison_lane_non_authoritative",
  "request_meta_ref_if_any": "request_meta.lane"
}
```

## Prescan-derived status

No inspected runtime path directly merges prescan-derived values into normalized artifacts. Prescan influence remains prompt/context influence in the observed path, so this packet records prescan value provenance as `UNKNOWN / not observed` rather than fabricating a `prescan_derived` example.
