# OpenClaw Proof Normalization Contract
schema_version: 1.0.0
status: PROPOSED
## Purpose
Convert heterogeneous OpenClaw evidence into DCP proof bundles. OpenClaw logs are input evidence, not final governance authority.
## Input artifacts
The normalizer MAY consume:
- OpenClaw JSONL file logs
- session JSONL transcripts
- trajectory sidecar JSONL
- exported trajectory bundle
- tool events
- model messages
- runtime settings
- usage metadata
- timestamps
- diagnostics export
- failure reports
- patch/diff artifacts when present
- external wrapper git captures
- external wrapper command captures
## Required normalized output fields
The normalizer MUST emit or mark missing:
- `route_decision_id`
- `task_id`
- `packet_id`
- `privacy_class`
- `risk_class`
- `model_provider_used`
- `runner_used`
- `requested_model`
- `actual_model`
- `provider_endpoint_or_route_profile`
- `prompt_hash`
- `prompt_body_ref`
- `response_hash`
- `response_body_ref`
- `files_read`
- `files_changed`
- `git_status_before`
- `git_status_after`
- `git_diff_stat`
- `git_diff`
- `commands_run`
- `command_outputs`
- `exit_codes`
- `test_lint_typecheck_results`
- `structured_schema_id`
- `structured_validation_result`
- `cost_estimate`
- `actual_usage`
- `route_decision_reason`
- `audit_decision`
- `approval_event`
- `head_sha`
- `pr_metadata`
- `openclaw_trajectory_ref`
- `redaction_report`
- `remaining_risks`
## Hash requirements
Every proof bundle MUST include:
- SHA-256 hash of normalized prompt body or prompt reference file
- SHA-256 hash of normalized response body or response reference file
- SHA-256 hash of git diff for write tasks
- SHA-256 hash of command output artifact bundle
- SHA-256 hash of trajectory export when present
- schema hash for every structured output artifact
## Redaction rules
- Never include raw secrets in normalized proof.
- Preserve secret-detection evidence as category and path metadata only.
- Redact environment values.
- Redact tokens, API keys, private keys, credentials, cookies, and authorization headers.
- Redaction must be recorded in `redaction_report`.
- Redaction failure blocks external sharing.
## Privacy handling
- `PUBLIC_SANDBOX` and `PUBLIC_REPO`: full proof may be stored unless secrets are detected.
- `PRIVATE_REPO_NO_SECRETS`: proof may include paths/diffs if policy permits.
- `PRIVATE_REPO_POSSIBLE_SECRETS`: proof requires secret scan and redaction report.
- `SECRET_BEARING`: proof stores references and hashes, not raw secret content.
- `CLIENT_DATA`: proof follows client contract and approval event.
- `SECURITY_SENSITIVE`: proof access restricted to security/release reviewers.
- `RELEASE_AUTHORITY`: proof immutable or append-only after release judgment.
## Missing-evidence behavior
- Missing required evidence for read tasks: `validation_state=FAILED`.
- Missing required evidence for write tasks: `validation_state=FAILED` and release blocked.
- Missing git status/diff for write tasks: hard block.
- Missing actual model/provider for private or high-risk task: hard block.
- Missing audit proof for R5/R6: hard block.
- Missing approval event when required: hard block.
## Chain of custody
The normalizer MUST preserve:
- input artifact list
- input artifact hashes
- normalizer version
- created_at timestamp
- source runner
- source session
- route decision ref
- parent proof refs
- handoff refs
- validation result
- immutable storage ref if available
## Output bundle posture
Possible normalized proof statuses:
- `PLAN_ONLY`
- `SPECIFICATION_COMPLETE`
- `IMPLEMENTATION_COMPLETE`
- `READY_FOR_REVIEW`
- `VERIFIED`
- `BLOCKED`
Completion claims require `VERIFIED`.

validation_notes: This contract explicitly says OpenClaw proof is input evidence. DCP normalization supplies git/proof/release semantics.
