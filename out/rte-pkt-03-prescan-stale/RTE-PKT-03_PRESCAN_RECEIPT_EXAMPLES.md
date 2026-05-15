# RTE-PKT-03 Prescan Receipt Examples

Accepted imported prescan:

```json
{
  "mode": "imported_prescan_accepted",
  "verdict": "accepted",
  "reason_codes": ["identity_match"],
  "can_influence_execution": true,
  "advisory_only": false,
  "prescan_import_dir": "/tmp/import",
  "repo_root_current": "/tmp/repo",
  "repo_root_imported_if_present": "/tmp/repo",
  "source_root_current": "/tmp/repo",
  "source_root_imported_if_present": "/tmp/repo",
  "corpus_manifest_hash_current_if_available": "sha256-redacted",
  "corpus_manifest_hash_imported_if_present": "sha256-redacted"
}
```

Rejected stale imported prescan:

```json
{
  "mode": "imported_prescan_rejected_stale",
  "verdict": "rejected_stale",
  "reason_codes": ["corpus_manifest_hash_mismatch"],
  "can_influence_execution": false,
  "advisory_only": true,
  "scope_reduction_applied": false,
  "router_loaded": false
}
```

Missing metadata imported prescan:

```json
{
  "mode": "imported_prescan_missing_metadata",
  "verdict": "missing_metadata",
  "reason_codes": [
    "missing_repo_root",
    "missing_source_root",
    "missing_prescan_artifact_version",
    "missing_corpus_manifest_hash"
  ],
  "can_influence_execution": false,
  "advisory_only": true
}
```

Local prescan:

```json
{
  "mode": "local_prescan",
  "verdict": "local_prescan",
  "reason_codes": ["local_prescan_completed"],
  "online_mode": "online_prescan_not_authorized",
  "can_influence_execution": true,
  "advisory_only": false
}
```

Skipped prescan:

```json
{
  "mode": "skip_prescan",
  "verdict": "skipped",
  "reason_codes": ["prescan_skipped_by_operator"],
  "can_influence_execution": false,
  "advisory_only": true
}
```

Online/offline state is recorded in `online_mode` as `online_prescan_authorized` or `online_prescan_not_authorized`.

