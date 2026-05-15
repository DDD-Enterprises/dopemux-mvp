# RTE-PKT-10 Conformance Examples

Generated: 2026-05-15T16:13:41Z

These examples describe the local helper behavior added in `services/repo-truth-extractor/lib/proof_contract.py`.

## SATISFIED Example

A payload containing every required field, explicit artifact role lists, custody, statuses, no-provider status, and artifact hashes returns:

```json
{
  "overall_status": "SATISFIED",
  "is_full_proof_contract_bundle": true,
  "provider_call_status": "NOT_RUN",
  "batch_operation_status": "NOT_RUN"
}
```

This is a governance-bundle example, not a claim that current RTE `PROOF_PACK.json` outputs have this shape.

## PARTIAL Example

A run-proof-shaped payload with `run_id`, `git_sha`, `runner_sha256`, `argv`, `cwd`, `updated_at`, `phases`, and `linked_artifacts` returns:

```json
{
  "overall_status": "PARTIAL",
  "proof_posture": "run_proof_or_packet_evidence_not_full_bundle",
  "missing_fields": [
    "bundle_id",
    "source_version",
    "authoritative_artifacts",
    "supporting_artifacts",
    "chain_of_custody",
    "artifact_hashes"
  ]
}
```

The important behavior is that run evidence remains useful without being promoted to full proof-bundle compliance.

## MISSING Example

If `authoritative_artifacts` and `supporting_artifacts` are absent, those fields return `MISSING`, and the full-bundle flag remains false. This prevents a manifest or proof pack from passing merely because it exists.

## UNKNOWN Example

For sample or uncertain-lineage artifacts without `run_id`, `artifact_hashes`, and `pass1_artifact_identity`, exact Pass 1 identity returns:

```json
{
  "status": "UNKNOWN",
  "reason": "exact Pass 1 identity lacks run_id, artifact_hashes, and pass1_artifact_identity evidence"
}
```

This preserves the RTE-FS-020 risk instead of hiding it.

## NOT_APPLICABLE Example

The helper supports explicit caller-declared `not_applicable_fields`. It does not infer NOT_APPLICABLE silently. For example, a caller may mark `handoff_refs` as not applicable only when the bundle is not a handoff:

```json
{
  "handoff_refs": {
    "status": "NOT_APPLICABLE",
    "reason": "field explicitly marked not applicable by caller"
  }
}
```

Silent absence still returns `MISSING`.

## Static / Live Boundary Example

Payloads with `live_validation_status=NOT_LIVE_VALIDATED`, `provider_call_status=NOT_RUN`, and `batch_operation_status=NOT_RUN` remain `static_only=true`. They do not prove live provider behavior.
