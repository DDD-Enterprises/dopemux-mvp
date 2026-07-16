# Contract Catalog

## Contract design rules

- **PROPOSED:** All Universal Router-owned records use `schema_version`, `record_id`, `created_at`, `workspace_id`, `source`, `claim_label`, `evidence_refs`, and `content_hash` where applicable.
- **PROPOSED:** Existing subsystem contracts are referenced by identifiers and artifact refs. They are not embedded or forked.
- **PROPOSED:** Unknown values are explicit `UNKNOWN` or null-with-status, never omitted to imply success.
- **PROPOSED:** Conflicting values remain in `conflicts[]` with evidence refs.
- **PROPOSED:** A record may be append-only corrected by a superseding record. Existing records are never mutated.

## Common reference type

### `SubsystemDecisionRef`

- **PROPOSED:** Owner: Universal Router as a reference record; underlying decision remains owned by the subsystem.
- **PROPOSED:** Minimal fields:
  - `subsystem`: `DCP|FREEFLOW|LITELLM|RTE|TASK_ORCHESTRATOR|DOPETASK|VALIDATION|AUDIT|PR_STEWARD|OTHER`
  - `decision_type`
  - `decision_id`
  - `schema_version`
  - `artifact_ref`
  - `artifact_hash`
  - `observed_at`
  - `source_confidence`
  - `authority_owner`
- **PROPOSED:** Invariant: reference validity never upgrades the referenced record's authority.

## Intake and classification contracts

### `TaskEnvelope`

- **PROPOSED:** Owner: Universal Router intake layer.
- **PROPOSED:** Purpose: normalize the minimum inputs needed to recommend a route without replacing a dopetask packet.
- **PROPOSED:** Minimal fields:
  - `task_id`
  - `task_text_ref` and `task_text_hash`
  - `task_class_hint`
  - `requested_operation`: `READ|DRAFT|IMPLEMENT|DIAGNOSE|ARCHITECT|AUDIT|RELEASE|OTHER`
  - `repo_binding`: repo ID, root marker, branch/ref, worktree ref
  - `scope_in[]`, `scope_out[]`, `file_allowlist[]`
  - `required_outputs[]`
  - `constraints[]`
  - `write_intent`
  - `network_need_hint`
  - `privacy_assertion`
  - `secret_scan_ref`
  - `cost_ceiling`
  - `plan_credit_ceiling`
  - `latency_class`
  - `context_refs[]`
  - `operator_preference_hints[]`
- **PROPOSED:** Invariant: no execution permission is encoded.
- **PROPOSED:** Invariant: task packet or handoff refs remain external.

### `DCPClassificationRef`

- **OBSERVED:** Underlying owner: DCP.
- **PROPOSED:** Minimal reference fields:
  - `dcp_decision_id`
  - `dcp_schema_version`
  - `route_id`
  - `task_type`
  - `risk_class`
  - `authority_class`
  - `runtime_impact`
  - `red_lane`
  - `backend_recommendation`
  - `classification_confidence`
  - `artifact_ref`
  - `artifact_hash`
- **PROPOSED:** Invariant: fields are imported verbatim and not rewritten.
- **PROPOSED:** Invariant: backend recommendation is not execution permission.

### `RiskPrivacyClassification`

- **PROPOSED:** Owner: Universal Router only for route-specific synthesis.
- **PROPOSED:** Inputs: TaskEnvelope privacy assertion, secret-scan ref, DCP risk ref, policy.
- **PROPOSED:** Minimal fields:
  - `classification_id`
  - `dcp_classification_ref`
  - `privacy_class`: `PUBLIC|INTERNAL|PRIVATE|SECRET_BEARING|CLIENT_DATA|SECURITY_SENSITIVE|RELEASE_SENSITIVE|UNKNOWN`
  - `privacy_source`: `OPERATOR|TASK_PACKET|SECRET_SCAN|POLICY|UNKNOWN`
  - `effective_route_risk`
  - `network_sensitivity`
  - `containment_class`
  - `unknown_fields[]`
  - `conflicts[]`
  - `result`: `PASS|BLOCK|ESCALATE`
- **PROPOSED:** Invariant: it does not replace DCP risk or claim universal privacy truth.
- **PROPOSED:** Invariant: `UNKNOWN` fails closed for networked, write, security, audit-independent, or release-sensitive routes.

## Capability and health contracts

### `RunnerCapabilitySnapshot`

- **PROPOSED:** Owner: Universal Router snapshot store.
- **PROPOSED:** Minimal fields:
  - `snapshot_id`
  - `runner_id`, `runner_version`, `executable_hash`
  - `acquisition_method`: `HELP|DIAGNOSTIC|SMOKE|IMPORTED_EVIDENCE|MANUAL_ASSERTION`
  - `model_selection_support`
  - `reasoning_control_support`
  - `structured_output_support`
  - `non_interactive_support`
  - `subagent_support`
  - `session_persistence_control`
  - `tool_control`
  - `filesystem_control`
  - `network_control`
  - `usage_fields[]`
  - `identity_fields[]`
  - `auth_status_without_secret`
  - `observed_at`, `expires_at`
  - `measurement_confidence`
  - `evidence_refs[]`
- **PROPOSED:** Invariant: installed does not imply authenticated or healthy.
- **PROPOSED:** Invariant: unsupported and untested are distinct.

### `ProviderHealthSnapshot`

- **PROPOSED:** Owner: Universal Router snapshot store; source health remains subsystem-specific.
- **PROPOSED:** Minimal fields:
  - `snapshot_id`
  - `provider_path_id`
  - `source_subsystem`
  - `network_posture`
  - `status`: `AVAILABLE|DEGRADED|RATE_LIMITED|AUTH_FAILURE|POLICY_BLOCKED|ENVIRONMENT_BLOCKED|UNAVAILABLE|UNKNOWN|STALE`
  - `scope`: host, sandbox, proxy instance, provider endpoint, account, route
  - `latency_observation`
  - `cooldown_ref`
  - `admission_ref`
  - `observed_at`, `expires_at`
  - `confidence`
  - `evidence_refs[]`
- **PROPOSED:** Invariant: `ENVIRONMENT_BLOCKED` is not provider unhealth.
- **PROPOSED:** Invariant: `POLICY_BLOCKED` is not provider unhealth.

### `ModelCapabilityRecord`

- **PROPOSED:** Owner: executable policy registry.
- **PROPOSED:** Minimal fields:
  - `model_record_id`
  - `provider_path_id`
  - `runner_id`
  - `requested_model_id_or_alias`
  - `configured_model_resolution`
  - `capability_flags[]`
  - `reasoning_levels[]`
  - `structured_output_modes[]`
  - `context_class`
  - `network_requirements`
  - `containment_requirements`
  - `identity_attestation_support`
  - `usage_observation_support`
  - `pricing_ref`
  - `certification_refs[]`
  - `status`: `DOCUMENTED|LOCALLY_PROVEN|CERTIFIED|DEPRECATED|REVOKED|UNKNOWN`
  - `source_dates[]`
- **PROPOSED:** Invariant: capability and current availability are separate.

## Policy and candidate contracts

### `RoutePolicy`

- **PROPOSED:** Owner: Dopemux Universal Router.
- **PROPOSED:** Minimal fields:
  - `policy_id`, `policy_version`, `schema_version`
  - `content_hash`
  - `effective_from`, `expires_at`
  - `hard_invariants[]`
  - `task_class_rules[]`
  - `candidate_filters[]`
  - `ranking_weights`
  - `snapshot_ttls`
  - `cost_credit_rules`
  - `reasoning_rules`
  - `network_rules`
  - `containment_rules`
  - `audit_rules`
  - `escalation_rules`
  - `certification_refs[]`
  - `supersedes_policy_id`
  - `promotion_ref`
- **PROPOSED:** Invariant: policy cannot weaken compiled hard invariants.
- **PROPOSED:** Invariant: policy activation is a reviewed tracked change.

### `RouteCandidate`

- **PROPOSED:** Owner: Universal Router, ephemeral or journaled with decision.
- **PROPOSED:** Minimal fields:
  - `candidate_id`
  - `runner_id`
  - `provider_path_id`
  - `model_record_ref`
  - `requested_reasoning_level`
  - `network_posture`
  - `containment_declaration_ref`
  - `subagent_pattern`
  - `validation_route`
  - `audit_route`
  - `admission_requirement`
  - `eligibility`: `ELIGIBLE|INELIGIBLE|STALE|UNKNOWN`
  - `hard_block_reasons[]`
  - `score_components`
  - `estimated_cost_observation`
  - `plan_credit_posture`
  - `snapshot_refs[]`
  - `certification_refs[]`
- **PROPOSED:** Invariant: score cannot override a hard block.

### `UniversalRouteDecision`

- **PROPOSED:** Owner: Universal Router.
- **PROPOSED:** Minimal fields:
  - `decision_id`, `attempt_id`, `parent_decision_id`
  - `task_envelope_ref`
  - `dcp_classification_ref`
  - `risk_privacy_classification_ref`
  - `policy_id`, `policy_hash`
  - `snapshot_refs[]`
  - `candidate_refs[]`
  - `selected_candidate_ref`
  - `alternative_candidate_refs[]`
  - `subsystem_decision_refs[]`
  - `decision_status`: `RECOMMENDED|BLOCKED|ESCALATED|NO_ELIGIBLE_ROUTE`
  - `decision_reasons[]`
  - `unknowns[]`
  - `conflicts[]`
  - `freshness_summary`
  - `next_action`
- **PROPOSED:** Invariant: it is not an execution authorization.

### `ExecutionRecommendation`

- **PROPOSED:** Owner: Universal Router presentation layer.
- **PROPOSED:** Minimal fields:
  - `recommendation_id`
  - `decision_ref`
  - `runner`
  - `provider_path`
  - `requested_model`
  - `requested_reasoning`
  - `network_posture`
  - `containment_declaration_ref`
  - `subagent_pattern`
  - `validation_route`
  - `audit_assignment_ref_or_template`
  - `estimated_usage_cost_posture`
  - `operator_actions[]`
  - `expires_at`
- **PROPOSED:** Invariant: expiration or evidence drift requires re-recommendation.

## Execution-facing future contracts

### `ExecutionRequest`

- **PROPOSED:** Owner: future integration caller; accepted by dopetask/runner boundary.
- **PROPOSED:** Minimal fields:
  - `execution_request_id`
  - `accepted_recommendation_ref`
  - `operator_acceptance_ref`
  - `human_approval_ref`
  - `task_packet_ref`
  - `handoff_ref`
  - `runner_adapter_id/version`
  - `requested_model`, `requested_reasoning`
  - `containment_declaration_ref`
  - `network_posture`
  - `input_manifest_ref`
  - `output_manifest_location`
  - `retry_budget`
- **PROPOSED:** Invariant: release one does not emit executable requests.
- **PROPOSED:** Invariant: an accepted dopetask handoff is required before execution.

### `RunnerResult`

- **PROPOSED:** Owner: runner adapter as normalized observation.
- **PROPOSED:** Minimal fields:
  - `runner_result_id`
  - `execution_request_ref`
  - `runner_session_id`
  - `status`: `SUCCEEDED|FAILED|CANCELLED|ENVIRONMENT_FAILURE|POLICY_BLOCKED|UNKNOWN`
  - `exit_code`
  - `output_refs[]`
  - `command_refs[]`
  - `model_identity_observation_ref`
  - `usage_observation_refs[]`
  - `containment_evidence_refs[]`
  - `started_at`, `finished_at`
  - `failure_classification`
- **PROPOSED:** Invariant: success is not validation or audit pass.

## Identity, usage, containment, and network contracts

### `ModelIdentityObservation`

- **PROPOSED:** Owner: identity adapter/observation normalizer.
- **PROPOSED:** Required fields:
  - `requested_model`
  - `configured_model`
  - `model_response_claim`
  - `proxy_reported_model`
  - `provider_attested_model`
  - `attested_actual_model`
  - `model_identity_confidence`
  - `provider_request_id`
  - `identity_evidence_ref`
  - `identity_adapter_version`
  - `conflicts[]`
- **PROPOSED:** Invariant: insufficient evidence yields `attested_actual_model=UNKNOWN`.

### `UsageObservation`

- **PROPOSED:** Owner: usage adapter/normalizer.
- **PROPOSED:** Required fields:
  - `visible_prompt_tokens`
  - `effective_input_tokens`
  - `cached_input_tokens`
  - `output_tokens`
  - `reasoning_output_tokens`
  - `runner_overhead_tokens`
  - `plan_credits`
  - `api_cost`
  - `estimated_cost`
  - `measurement_source`
  - `measurement_confidence`
  - `pricing_version`
  - `observation_scope`: `REQUEST|SESSION|ROLLUP`
  - `exactness`: `EXACT|ESTIMATED|UNAVAILABLE|MIXED`
- **PROPOSED:** Invariant: no derived plan credits or fabricated runner overhead.

### `ContainmentDeclaration`

- **PROPOSED:** Owner: route decision for requested posture; enforcement evidence comes from runner/wrapper/OS/operator.
- **PROPOSED:** Minimal fields:
  - `containment_id`
  - controls for read, write, worktree, file allowlist, command allowlist, MCP, network, environment redaction, session persistence, outputs, approvals
  - each control: `requested_value`, `effective_value`, `enforcement_source`, `evidence_ref`, `confidence`
  - `overall_status`: `ENFORCED|PARTIAL|UNVERIFIED|CONFLICTING`
- **PROPOSED:** Invariant: `PROMPT_REQUESTED` cannot satisfy an enforcement requirement.

### `NetworkPosture`

- **PROPOSED:** Owner: route decision.
- **PROPOSED:** Values: `OFFLINE`, `SANDBOX_NETWORK_DENIED`, `APPROVED_PROVIDER_NETWORK`, `RESTRICTED_DOMAIN_NETWORK`, `GENERAL_NETWORK_ALLOWED`, `UNKNOWN`.
- **PROPOSED:** Minimal fields: posture value, allowed domains/providers, enforcement source, evidence ref, expiry, approval ref.
- **PROPOSED:** Invariant: provider network authorization is not general web authorization.

## Validation, escalation, audit, approval, and certification contracts

### `ValidationResult`

- **PROPOSED:** Underlying owner: validator/test system.
- **PROPOSED:** Router reference fields: validation ID, type, command/artifact ref, status, exit code, head SHA, executed_at, freshness, evidence hash.
- **PROPOSED:** Invariant: skipped validation is not passed validation.

### `EscalationDecision`

- **PROPOSED:** Owner: Universal Router for route escalation recommendation.
- **PROPOSED:** Minimal fields:
  - `escalation_id`
  - `from_decision_ref`
  - `trigger_class`: quality, capability, identity, policy, environment, audit, cost, credit, operator
  - `action`: `RAISE_REASONING|RAISE_MODEL_TIER|CHANGE_RUNNER|SAME_TIER_ALTERNATIVE|DEMOTE|BLOCK|NEEDS_SUPERVISOR`
  - `target_candidate_ref`
  - `budget_consumed`
  - `allowed_by_policy`
  - `reasons[]`
- **PROPOSED:** Invariant: environment failure cannot choose `RAISE_MODEL_TIER`.

### `AuditAssignment`

- **PROPOSED:** Owner: route recommendation for assignment intent; actual audit authority remains external.
- **PROPOSED:** Minimal fields: assignment ID, task/execution ref, required state, auditor runner/provider/model constraints, independence requirements, bounded input manifest, containment requirements, retry count, due posture.
- **PROPOSED:** Invariant: same runner/session cannot satisfy independent audit.

### `AuditResultRef`

- **OBSERVED:** Underlying owner: audit/proof system.
- **PROPOSED:** Minimal fields: audit ID, state (`NOT_REQUIRED|REQUIRED_NOT_RUN|SKIPPED_WITH_REASON|PASS|PASS_WITH_RISKS|FAIL|NEEDS_SUPERVISOR`), auditor identity refs, independence status, report ref/hash, execution head/ref, findings summary, created_at.
- **PROPOSED:** Invariant: skipped is never pass.

### `HumanApprovalRef`

- **OBSERVED:** Underlying owner: external operator/governance system.
- **PROPOSED:** Minimal fields: approval ID, scope, approver identity ref, route/task refs, issued_at, expires_at, constraints, artifact ref/hash.
- **PROPOSED:** Invariant: router cannot issue its own approval.

### `BenchmarkCertification`

- **PROPOSED:** Owner: benchmark/certification system, referenced by router.
- **PROPOSED:** Minimal fields:
  - certification ID
  - route tuple: runner, provider path, model, reasoning, adapter, policy
  - corpus version
  - metric results
  - certification level
  - valid_from, expires_at
  - invalidation triggers
  - auditor ref
  - artifact ref/hash
- **PROPOSED:** Invariant: certification is invalid if any route tuple component changes.

## Existing governance references

### `ProofBundleRef`

- **OBSERVED:** Underlying owner: existing proof contract.
- **PROPOSED:** Fields: bundle ID, run ID, status, validation state, manifest ref/hash, head SHA, chain-of-custody ref.
- **PROPOSED:** Invariant: no duplicate proof body/schema in router state.

### `DopetaskHandoffRef`

- **OBSERVED:** Underlying owner: existing handoff/dopetask contract.
- **PROPOSED:** Fields: handoff ID, source/target, posture, recommended next step, status, accepted flag, artifact ref/hash, warnings/blockers.
- **PROPOSED:** Invariant: execution cannot begin without accepted handoff.

### `PRStewardReadinessRef`

- **OBSERVED:** Underlying owner: PR Steward.
- **PROPOSED:** Fields: readiness artifact ID, PR number, head SHA, status, check freshness, unresolved blocker count, unknown reviewer/bot count, artifact ref/hash, created_at.
- **PROPOSED:** Invariant: router cannot convert non-ready status into ready.

## Relationship constraints

- **PROPOSED:** One TaskEnvelope may have multiple decision attempts.
- **PROPOSED:** One decision attempt has exactly one active policy hash and one DCP ref.
- **PROPOSED:** One decision may contain zero or more subsystem refs and exactly one selected candidate when status is `RECOMMENDED`.
- **PROPOSED:** One execution request must point to one accepted recommendation and one accepted handoff.
- **PROPOSED:** Validation, audit, proof, and PR readiness remain independently versioned and can supersede earlier refs without mutating the route decision.
