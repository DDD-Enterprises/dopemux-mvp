# RTE-PKT-10 Proof Contract Gap Matrix

Generated: 2026-05-15T16:13:41Z

This matrix compares the packet proof-contract requirements against observed local RTE run-proof and packet-proof shapes. Status values use `SATISFIED`, `PARTIAL`, `MISSING`, `UNKNOWN`, and `NOT_APPLICABLE`.

## Observed Artifact Shapes

| Artifact family | Observed examples | Current conformance classification |
| --- | --- | --- |
| RTE runtime source | `services/repo-truth-extractor/run_extraction_v5.py`, `services/repo-truth-extractor/reporting.py` | Runtime authority, not proof artifact. |
| RTE generated run manifest | `services/repo-truth-extractor/extraction/repo-truth-extractor/v5/runs/*/RUN_MANIFEST.json` | Runtime-generated evidence, partial proof-contract shape. |
| RTE proof pack writer shape | `reporting.py::update_proof_pack` writes `PROOF_PACK.json` with run evidence fields | Run proof only unless governance declarations are also present. No local `PROOF_PACK.json` example was found under v5 runs in this worktree. |
| Packet proof manifests | `out/rte-pkt-01-*` through `out/rte-pkt-06-*`, `out/rte-pkt-15-*` where present | Proof/governance evidence, not runtime source authority. |
| TP proof files | `proof/TP-RTE-*.json` where present | Proof/governance evidence, not full proof-bundle-complete unless required fields are present. |

## Field Matrix

| Proof-contract field | Observed mapping | Status | Gap / risk |
| --- | --- | --- | --- |
| `bundle_id` | Not observed in RTE run manifests or sampled packet manifests. | MISSING | Required to distinguish governance bundle identity from run evidence identity. |
| `run_id` | Present in runtime `RUN_MANIFEST.json`; proof writer sets `run_id` in `PROOF_PACK.json`. | SATISFIED for run proof, PARTIAL for packet proof | Packet proof manifests often use packet IDs instead of run IDs. |
| `source_version` | Canonical proof docs require source version; RTE run proof uses runner hashes instead. | MISSING | Runner hash is useful evidence but is not the same declaration as source version. |
| `repo_root` | Present in local `RUN_MANIFEST.json`; packet manifests record worktree paths. | PARTIAL | Some proof artifacts have worktree/cwd instead of explicit repo root. |
| `git_sha` | Present in RTE `RUN_MANIFEST.json`, proof writer shape, and packet manifests. | SATISFIED | Keep as evidence, not as full custody by itself. |
| `runner_sha` | Proof writer shape records `runner_sha256`; some manifests omit it. | PARTIAL | Field naming drift exists between `runner_sha` and `runner_sha256`. |
| `command_argv` | Proof writer shape records `argv`; run manifests have `cli`. | PARTIAL | Existing names map to the concept but are not consistently declared. |
| `cwd` | Proof writer shape records `cwd`; packet manifests often record worktree path. | PARTIAL | Missing from several proof/governance manifests. |
| `status` | Packet manifests often include status; run manifests use `run_status` and `phase_status`. | PARTIAL | Runtime status is not equivalent to governance bundle status. |
| `validation_state` | Some packet proof files list validations; many lack explicit `validation_state`. | PARTIAL | Validation evidence without an explicit state must not become a pass. |
| `run_posture` | Static/no-provider posture can be derived in packet proofs but is not consistently explicit. | PARTIAL | Static-only and live-validated proof remain easy to confuse without explicit labeling. |
| `generated_at` | Present as `generated_at`, `generated_at_utc`, or `updated_at` depending artifact family. | PARTIAL | Timestamp naming drift exists. |
| `phase_list` | Present as `phases` or `routing_step_tiers` in run evidence. | PARTIAL | Packet proof manifests are not always phase-scoped. |
| `generated_artifact_list` | Present as `linked_artifacts`, `artifacts`, `proof_files`, or `changed_files`. | PARTIAL | Lists exist but roles are not canonicalized. |
| `authoritative_artifacts` | Required by proof contract; absent from sampled RTE run proof and packet manifests. | MISSING | Main overtrust risk: proof artifact presence is not the same as authoritative declaration. |
| `supporting_artifacts` | Required/expected by proof contract; absent from sampled RTE run proof and packet manifests. | MISSING | Reviewers cannot mechanically separate decision artifacts from context artifacts. |
| `runtime_authority_artifacts` | Not explicitly declared in sampled proof outputs. | MISSING | Generated proof can be mistaken for source truth without this boundary. |
| `generated_evidence_artifacts` | Not explicitly declared as a role list in sampled proof outputs. | MISSING | Evidence surfaces need role labels. |
| `proof_governance_artifacts` | Not explicitly declared as a role list in sampled proof outputs. | MISSING | Packet proof outputs need governance role labels. |
| `external_advisory_artifacts` | Not explicitly declared in sampled proof outputs. | MISSING | External advisory context must not outrank repo truth. |
| `sample_or_uncertain_lineage_artifacts` | Not explicitly declared in sampled proof outputs. | MISSING | Exact Pass 1 identity remains unsafe to infer without lineage labels. |
| `chain_of_custody` | Required by proof docs; absent from sampled RTE run evidence and many packet proof manifests. | MISSING | Custody is not complete without explicit source and parent declarations. |
| `warnings` | Present in some proof files, absent in others. | PARTIAL | Empty warnings should be declared explicitly when reviewed as a bundle. |
| `blockers` | Present in some proof files, absent in others. | PARTIAL | Empty blockers should be declared explicitly when reviewed as a bundle. |
| `handoff_refs` | Required/expected by packet; absent unless proof bundle declares no handoff. | MISSING | Absence is ambiguous without explicit empty list or NOT_APPLICABLE. |
| `parent_bundle_refs` | Required/expected by packet; absent in sampled outputs. | MISSING | Upstream chain cannot be reconstructed mechanically. |
| `review_order_hint` | Present in the active packet, absent from sampled proof outputs. | MISSING | Review sequencing is not embedded in most generated evidence. |
| `live_validation_status` | Present or derivable in some packet proofs as NOT_RUN/NOT_LIVE_VALIDATED; not universal. | PARTIAL | Static packet proof must not be treated as live provider proof. |
| `provider_call_status` | Present or derivable in no-provider attestations and safety boundaries. | PARTIAL | Must remain NOT_RUN unless live provider calls are actually observed. |
| `batch_operation_status` | Present or derivable in some packet proofs as NOT_RUN. | PARTIAL | Static batch proof does not prove provider batch behavior. |
| `redaction_status` | RTE-PKT-02 has redaction evidence, but sampled manifests do not consistently expose `redaction_status`. | PARTIAL | Provider-bound redaction must stay visible at bundle review time. |
| `artifact_hashes` | Required for exact lineage; not observed as a complete artifact hash map in sampled RTE packet proof manifests. | MISSING | Exact Pass 1 identity remains UNKNOWN without hashes plus run IDs. |

## Contract Conclusion

Observed RTE run proof is useful evidence, but sampled proof outputs are not full proof-contract-compliant governance bundles. Missing authoritative/supporting declarations, custody fields, role-specific artifact lists, and artifact hashes keep conformance at PARTIAL or MISSING.
