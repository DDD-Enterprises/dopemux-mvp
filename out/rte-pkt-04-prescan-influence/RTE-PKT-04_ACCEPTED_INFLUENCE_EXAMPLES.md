# RTE-PKT-04 Accepted Influence Examples

Examples are shape examples from the targeted local tests. They include labels, counts, and safe paths only. They do not include raw source content, provider payloads, or compression hint text.

## Accepted Local Prescan

```json
{
  "prescan_mode": "local_prescan",
  "can_influence_execution": true,
  "influence_applied": true,
  "influence_classes": [
    "scope_reduction",
    "partition_reorder",
    "tier_override",
    "routing_model_hint"
  ],
  "not_applied_influence_classes": [
    "phase_hint"
  ]
}
```

## Accepted Imported Prescan

```json
{
  "prescan_mode": "imported_prescan_accepted",
  "prescan_verdict": "accepted",
  "can_influence_execution": true,
  "influence_classes": [
    "scope_reduction"
  ],
  "reason_codes": [
    "identity_match"
  ]
}
```

## Scope Reduction Label

```json
{
  "class": "scope_reduction",
  "applied": true,
  "enabled_by_prescan_allow_scope_reduction": true,
  "paths_removed_or_count": {
    "count": 1,
    "paths": [
      "/tmp/.../repo/src/skipped.py"
    ]
  },
  "reason_source": "prescan.extraction_hints.skip_duplicates",
  "source_prescan_mode": "local_prescan",
  "advisory_model_derived": true
}
```

## Routing/Model Hint Label

```json
{
  "class": "routing_model_hint",
  "applied": true,
  "affected_phase_or_step_if_known": "A",
  "hinted_provider_or_model_if_present": [
    "premium"
  ],
  "hint_source": "prescan.grok_passes.optimize.model_routing_hints",
  "does_not_claim_executed_route": true,
  "source_prescan_mode": "local_prescan",
  "advisory_model_derived": true
}
```

## Compression Hint Proof Label

```json
{
  "class": "compression_hint",
  "applied": true,
  "affected_paths_or_count": {
    "count": 1,
    "paths": [
      "/tmp/.../repo/docs/old.md"
    ]
  },
  "hint_source": "prescan.extraction_hints.compress_candidates",
  "source_prescan_mode": "local_prescan",
  "advisory_model_derived": true
}
```

The compression prompt context may still use the prescan hint text because that is the existing runtime behavior. The proof label intentionally records only class, source, path/count, and advisory status.
