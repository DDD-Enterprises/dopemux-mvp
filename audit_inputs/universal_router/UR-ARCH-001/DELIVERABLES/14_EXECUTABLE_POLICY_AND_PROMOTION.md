# Executable Policy and Promotion

## Policy owner

- **PROPOSED:** Dopemux Universal Router owns the executable universal routing-policy contract, parser, hard invariants, validation, and deterministic evaluation.
- **PROPOSED:** It does not own model/provider availability, Freeflow admission, RTE routing, benchmark verdicts, human approval, or release readiness.

## Exact repository locations

```text
schemas/universal-router/route-policy.schema.json
config/universal-router/policies/ur-policy-<semver>.yaml
config/universal-router/active-policy.json
src/dopemux/universal_router/policy.py
```

- **PROPOSED:** `active-policy.json` contains only `policy_id`, `policy_version`, `content_hash`, `certification_refs`, `activated_at`, and `promotion_ref`.
- **PROPOSED:** Versioned policy files are immutable after activation. Corrections create a new version.

## Policy layers and precedence

1. **PROPOSED:** Compiled hard invariants.
2. **PROPOSED:** Active tracked policy.
3. **PROPOSED:** Repository-local tightening-only overlay at `.dopemux/universal-router/policy-overlay.yaml`.
4. **PROPOSED:** Task packet and operator constraints.
5. **PROPOSED:** Operator preference hints.

- **PROPOSED:** Higher layers cannot be weakened by lower layers.
- **PROPOSED:** The local overlay can disable routes, lower ceilings, require stronger containment/audit, or shorten TTLs. It cannot broaden network, loosen identity, remove audit, increase cost ceilings, or enable execution.
- **PROPOSED:** Environment variables may disable the router or force advisory-only mode, but cannot loosen policy.

## Hard non-overridable invariants

- **PROPOSED:** No automatic execution in release one.
- **PROPOSED:** No automatic policy promotion.
- **PROPOSED:** No subagent fanout.
- **PROPOSED:** No revival of `services/task-router`.
- **PROPOSED:** No runtime authority for dormant agent families.
- **PROPOSED:** No duplicate proxy, quota ledger, proof/handoff schema, execution engine, workflow engine, or release gate.
- **PROPOSED:** Environment failure cannot cause automatic premium escalation.
- **PROPOSED:** Prompt-only containment cannot satisfy enforced containment.
- **PROPOSED:** Skipped audit is not pass.
- **PROPOSED:** Model self-report is not identity attestation.
- **PROPOSED:** Plan credits are not derived from tokens.

## Policy contents

- **PROPOSED:** Task class to capability requirements.
- **PROPOSED:** Risk/privacy/network/containment gates.
- **PROPOSED:** Snapshot freshness and confidence rules.
- **PROPOSED:** Candidate eligibility and ranking.
- **PROPOSED:** Reasoning selection and escalation budgets.
- **PROPOSED:** Cost/credit unknown handling.
- **PROPOSED:** Validation and audit assignment.
- **PROPOSED:** Certification requirements.
- **PROPOSED:** Disablement/revocation status.
- **PROPOSED:** No provider credentials or secret values.

## Policy validation

- **PROPOSED:** JSON Schema validation with `additionalProperties: false` for authority-bearing sections.
- **PROPOSED:** Semantic validation checks impossible combinations, unresolved refs, unsupported enums, weakening overlays, cycles, duplicate IDs, expired certifications, and unknown models.
- **PROPOSED:** Deterministic fixture tests cover every required task class and failure condition.
- **PROPOSED:** `dopemux route validate policy` emits machine-readable errors and never auto-repairs policy.

## Policy versioning

- **PROPOSED:** Semantic versioning:
  - major: contract or decision semantics change;
  - minor: new task class, route, or optional capability;
  - patch: non-semantic wording, metadata, or bug fix with identical decisions on certification corpus.
- **PROPOSED:** Policy hash, schema version, registry version, and adapter versions are captured in each decision.
- **PROPOSED:** A major or minor change requires recertification. A patch requires deterministic regression replay and independent review.

## Certification inputs

- **PROPOSED:** Historical replay results.
- **PROPOSED:** Shadow-mode results.
- **PROPOSED:** Hard-block and state-machine tests.
- **PROPOSED:** Route-specific benchmark certifications.
- **PROPOSED:** Identity/usage/containment adapter certifications.
- **PROPOSED:** Independent audit report.
- **PROPOSED:** Human review and PR Steward readiness for the policy change PR.

## Promotion workflow

1. **PROPOSED:** GPT-5.6 Pro writes or approves the macro packet for non-trivial policy changes.
2. **PROPOSED:** Codex implements policy/schema/fixtures in a dedicated worktree.
3. **PROPOSED:** Implementer runs required tests and embedded audit.
4. **PROPOSED:** Gemini CLI performs broad-context contradiction review for major policy changes when safely available.
5. **PROPOSED:** Independent auditor reviews decision diffs and certification evidence.
6. **PROPOSED:** PR Steward harvests reviews, threads, checks, commits, head SHA, and proof.
7. **PROPOSED:** Human reviewer approves the active-pointer change.
8. **PROPOSED:** Merge changes `active-policy.json`; the router never edits it automatically.

## Promotion gates

- **PROPOSED:** 100% schema validity on policy and fixtures.
- **PROPOSED:** 100% hard-boundary and forbidden-route tests.
- **PROPOSED:** No severe failure in historical or shadow certification corpus.
- **PROPOSED:** Required route certifications current to policy/adapter/model tuple.
- **PROPOSED:** Independent audit `PASS` or non-blocking `PASS_WITH_RISKS`.
- **PROPOSED:** PR Steward `READY` at current head.
- **PROPOSED:** No unresolved unknown reviewer/bot, blocking thread, failed check, stale proof, or scope escape.

## Migration from advisory policy

- **OBSERVED:** `config/ai/model-routing.policy.yaml` is advisory and has no observed runtime reader.
- **PROPOSED:** Do not rename it into executable authority.
- **PROPOSED:** Build a rule-by-rule migration matrix:
  - rule ID and source lines;
  - current advisory meaning;
  - target executable field;
  - evidence support;
  - conflicts;
  - test fixture;
  - disposition: `MIGRATE|REWRITE|DEFER|REJECT`.
- **PROPOSED:** Rules that promote DCP, proof, release, OpenRouter, or dormant agents beyond accepted boundaries are rejected or rewritten.
- **PROPOSED:** The advisory file remains readable history until a separate cleanup packet deprecates it.

## Human override

- **PROPOSED:** Overrides are external `HumanApprovalRef` values with scope, reason, approver, issue time, expiry, and evidence hash.
- **PROPOSED:** An override creates a new decision attempt.
- **PROPOSED:** Permitted examples: bounded cost ceiling increase, same-provider audit exception, stale low-risk snapshot acceptance, investigation-only benchmark bypass.
- **PROPOSED:** Prohibited examples: fabricate identity, expose secrets, treat skipped audit as pass, bypass current-head proof, revive forbidden authority, or enable release-one execution.

## Disablement and rollback

- **PROPOSED:** Global kill switch: `DOPEMUX_UNIVERSAL_ROUTER_DISABLED=1`.
- **PROPOSED:** Workspace kill switch: `.dopemux/universal-router/DISABLED` with operator-created reason metadata.
- **PROPOSED:** Policy rollback: revert the tracked active pointer to a prior certified policy hash.
- **PROPOSED:** Route revocation: mark a route/model/adapter certification revoked in a new registry/policy version.
- **PROPOSED:** No rollback deletes the journal.
- **PROPOSED:** Existing `dopemux routing`, Freeflow, LiteLLM, RTE, Task Orchestrator, and dopetask flows remain operational independently.

## Policy conflict behavior

- **PROPOSED:** Invalid active pointer, hash mismatch, duplicate active policy, expired required certification, or loosening overlay blocks `recommend`.
- **PROPOSED:** `explain` may still render the conflict and remediation using a safe built-in diagnostic policy, but cannot recommend a route.
- **PROPOSED:** Conflicting policy artifacts remain visible in the journal and require a reviewed correction.
