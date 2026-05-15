# RTE-PKT-03 Prescan Import Identity Matrix

| Field | Current source | Imported source | Required | Accept rule | Reject or stale rule | Test coverage |
| --- | --- | --- | --- | --- | --- | --- |
| repo_root | `current_repo_root` passed to `IntelligenceRouter.load_imported()` | `repo_root` or `source_identity.repo_root` in `prescan_intelligence.json` | yes | normalized paths match exactly | `repo_root_mismatch` | `test_imported_prescan_with_mismatched_repo_root_is_rejected` |
| source_root | current source root, currently same root as RTE run root | `source_root` or `source_identity.source_root` | yes | normalized paths match exactly | `source_root_mismatch` or `missing_source_root` | missing-metadata test covers absence |
| prescan_artifact_version | `PRESCAN_ARTIFACT_VERSION` | `prescan_artifact_version` or `source_identity.prescan_artifact_version` | yes | version is in `SUPPORTED_PRESCAN_ARTIFACT_VERSIONS` | `unsupported_prescan_artifact_version` or `missing_prescan_artifact_version` | missing-metadata test covers absence |
| corpus_manifest_hash | local deterministic corpus identity hash from `CorpusWalker` entries | `corpus_manifest_hash` or `source_identity.corpus_manifest_hash` | yes | hashes match | `corpus_manifest_hash_mismatch` or `current_corpus_manifest_hash_unavailable` | `test_imported_prescan_with_mismatched_corpus_manifest_hash_is_rejected` |
| git_sha | `git rev-parse HEAD` when available | `git_sha` or `source_identity.git_sha` | no | if both present, values match; if one side missing, warn only | `git_sha_mismatch` if both present and differ | accepted test uses matching SHA |
| generated_at | not used for current freshness | imported metadata | no | recorded only | missing timestamp does not block | receipt tests cover recorded field shape |
| prescan_mode | not used for current freshness | imported metadata | no | recorded only | missing mode does not block | not separately asserted |

Identity hash rule: `corpus_manifest_identity_hash()` hashes sorted source identity rows containing `rel_path`, `size_bytes`, `extension`, `include`, `exclude_reason`, and `content_hash`. This is local-only and does not call providers.

