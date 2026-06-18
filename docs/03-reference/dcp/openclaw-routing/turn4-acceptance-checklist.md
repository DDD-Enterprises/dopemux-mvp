---
id: TURN4_ACCEPTANCE_CHECKLIST
title: Turn4 Acceptance Checklist
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-17'
last_review: '2026-06-17'
next_review: '2026-09-15'
prelude: Turn4 Acceptance Checklist (explanation) for dopemux documentation and developer
  workflows.
---
# TURN4_ACCEPTANCE_CHECKLIST

schema_version: 1.0.0
status: PROPOSED

## Artifact completeness checklist

- [ ] `openclaw_dcp_routing_policy.yaml` present
- [ ] `routing_classifier.schema.json` present
- [ ] `route_decision.schema.json` present
- [ ] `model_pool_registry.yaml` present
- [ ] `privacy_class_policy.yaml` present
- [ ] `risk_class_policy.yaml` present
- [ ] `forbidden_routes.yaml` present
- [ ] `human_approval_gates.yaml` present
- [ ] `openrouter_route_profiles.json` present
- [ ] `structured_output_policy.json` present
- [ ] `proof_requirements.schema.json` present
- [ ] `audit_independence_rules.yaml` present
- [ ] `release_gate_policy.yaml` present
- [ ] `runner_adapter_contract.md` present
- [ ] `openclaw_proof_normalization_contract.md` present
- [ ] `route_decision_logger.schema.json` present
- [ ] `provider_availability_probe_spec.md` present
- [ ] `cost_policy.yaml` present
- [ ] `local_benchmark_harness_requirements.md` present
- [ ] `benchmark_fixture_manifest.yaml` present
- [ ] `benchmark_result.schema.json` present
- [ ] `route_certification_ledger.schema.json` present
- [ ] `pr_steward_merge_readiness.schema.json` present
- [ ] `example_route_decisions/` present with 8 examples
- [ ] `TURN4_ACCEPTANCE_CHECKLIST.md` present

## Schema validity checklist

- [ ] JSON schemas parse as valid JSON
- [ ] JSON config artifacts parse as valid JSON
- [ ] YAML artifacts parse as valid YAML
- [ ] JSON schemas use `additionalProperties: false` unless intentionally extensible
- [ ] Schemas include `schema_version`
- [ ] Enums exist for privacy classes
- [ ] Enums exist for risk classes
- [ ] Enums exist for routing roles
- [ ] Enums exist for audit verdicts where applicable
- [ ] Enums exist for gate/readiness statuses
- [ ] Example route decisions validate against `route_decision.schema.json`

## Fail-closed behavior checklist

- [ ] `UNKNOWN` privacy blocks or escalates
- [ ] `UNKNOWN` risk blocks or escalates
- [ ] Unknown actual provider/model blocks private/high-risk routes
- [ ] Missing benchmark certification blocks high-trust routes
- [ ] Missing proof blocks write/release gates
- [ ] Fallback weakening blocks route
- [ ] Provider drift blocks private/high-risk routes

## Privacy policy checklist

- [ ] OpenRouter free blocked for private/secret/client/security/release/schema authority
- [ ] Secret-bearing routes require redaction and approval
- [ ] Client data requires contract-approved route
- [ ] Consumer apps are manual/constrained only
- [ ] Direct APIs preferred for private/high-trust
- [ ] Local/self-hosted route still requires proof and benchmark guard

## Risk policy checklist

- [ ] R0 read permits cheap routes
- [ ] R1 draft cannot claim authority
- [ ] R2 tests cannot prove correctness alone
- [ ] R3 edits require git proof
- [ ] R4 multi-file edits require audit
- [ ] R5 security requires deep independent audit and human gate
- [ ] R6 release requires current proof, current CI, current head SHA, audit or human approval
- [ ] UNKNOWN risk fails closed

## OpenRouter policy checklist

- [ ] `provider.require_parameters=true` for structured routes
- [ ] `response_format.type=json_schema` for schema routes
- [ ] `strict=true` for schema routes
- [ ] `data_collection=deny` for private route profiles
- [ ] `zdr=true` where private/client/sensitive profile requires it
- [ ] `max_price` logged and enforced
- [ ] actual model/provider logged
- [ ] openrouter/free never used for deterministic authority
- [ ] provider drift fixture exists
- [ ] free timeout fixture exists

## Audit independence checklist

- [ ] Implementer cannot be sole final auditor
- [ ] Same runner/session self-audit blocks R4+
- [ ] R5/R6 require independent provider audit or explicit human approval
- [ ] Same-provider exception requires human approval
- [ ] Preview/experimental model cannot be sole high-risk authority
- [ ] Auditor verdict enum includes PASS, PASS_WITH_RISKS, FAIL, NEEDS_SUPERVISOR, SKIPPED

## Proof policy checklist

- [ ] Proof bundle includes model/provider/runner
- [ ] Proof bundle includes prompt/response hash
- [ ] Proof bundle includes files read/changed
- [ ] Write proof includes git status before/after
- [ ] Write proof includes diff stat and full diff
- [ ] Commands include stdout/stderr refs and exit codes
- [ ] Structured outputs include schema ID and validation result
- [ ] Cost estimate and actual usage captured
- [ ] Audit decision captured
- [ ] Approval event captured when required
- [ ] Redaction report present

## Release gate checklist

- [ ] PR number, repo, branch, base, head SHA captured
- [ ] Checks current to head SHA
- [ ] Failed checks block READY
- [ ] Stale checks block READY
- [ ] Stale proof blocks READY
- [ ] Unknown reviewer/bot blocks READY
- [ ] Unclassified review item blocks READY
- [ ] Blocking thread unresolved blocks READY
- [ ] Diff outside allowlist blocks READY
- [ ] Security/release missing approval blocks READY
- [ ] READY impossible unless all blockers empty/false

## Benchmark requirement checklist

- [ ] 100% valid JSON threshold
- [ ] 100% schema validity threshold
- [ ] 100% fail-closed unsupported-route threshold
- [ ] Evidence grounding precision >= 98%
- [ ] Unsupported-claim rate <= 1%
- [ ] Contradiction recall >= 90%
- [ ] Core-field stability >= 95%
- [ ] Hallucinated file/path tracking
- [ ] Diff applicability tracking
- [ ] Patch success tracking
- [ ] Test pass/fail tracking
- [ ] Latency/cost tracking
- [ ] Provider drift tracking
- [ ] Privacy mismatch tracking
- [ ] Local repo fixture requirement

## Unresolved UNKNOWN ledger

- [ ] Exact OpenClaw implementation paths for all OpenRouter profile settings are not proven here.
- [ ] Exact current provider model slugs/prices must be refreshed before implementation.
- [ ] Actual benchmark pass rates are UNKNOWN until harness execution.
- [ ] Gemini/Antigravity programmable surface stability remains route-specific.
- [ ] Consumer-plan legal/terms posture must be checked before automation use.
- [ ] Route certification storage location is not selected.
- [ ] PR Steward implementation location is not selected.
- [ ] DCP wrapper runtime location is not selected.
