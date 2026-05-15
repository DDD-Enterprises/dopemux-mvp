# RTE-PKT-06 Transition Examples

## Preserved UNKNOWN through parse repair

```json
{
  "truth_label": "UNKNOWN",
  "provenance_kind": "deterministic_parse_repair",
  "source_lane": "parse_repair",
  "transition_action": "preserved",
  "unknown_reason_if_any": "source excerpt does not establish value",
  "evidence_refs": ["fixture:docs/example.md:1-2"]
}
```

## Preserved CONFLICTING through schema repair

```json
{
  "truth_label": "CONFLICTING",
  "provenance_kind": "primary_observed",
  "source_lane": "primary",
  "transition_action": "preserved",
  "conflicting_values_if_any": ["runtime:path_a", "runtime:path_b"],
  "evidence_refs": ["fixture:docs/example.md:1-2"]
}
```

## Blocked provider-repair upgrade

```json
{
  "truth_label": "UNKNOWN",
  "attempted_truth_label_if_any": "OBSERVED",
  "provenance_kind": "provider_repair",
  "source_lane": "repair",
  "transition_action": "blocked_protected_label_upgrade",
  "label_source": "protected_label_guard"
}
```

## Blocked sidefill label drop

```json
{
  "truth_label": "CONFLICTING",
  "attempted_truth_label_if_any": null,
  "provenance_kind": "sidefill",
  "source_lane": "sidefill",
  "transition_action": "blocked_protected_label_drop"
}
```

## Non-authoritative comparison record

```json
{
  "truth_label": "UNKNOWN",
  "provenance_kind": "comparison",
  "source_lane": "comparison",
  "transition_action": "preserved",
  "authoritative": false
}
```

## Allowed transition requirements

An allowed protected-label transition must include source-backed `evidence_refs`, an accepted `label_source`, and, for `CONFLICTING -> OBSERVED`, `resolution_reason_if_any`.

No allowed transition fixture was added in this packet because the observed repair, sidefill, prescan, and comparison lanes are not source-authoritative by default.
