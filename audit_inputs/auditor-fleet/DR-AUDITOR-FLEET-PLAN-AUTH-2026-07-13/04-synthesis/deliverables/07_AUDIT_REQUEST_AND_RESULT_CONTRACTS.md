# Audit Request and Result Contracts

**Campaign:** `DR-AUDITOR-FLEET-PLAN-AUTH-2026-07-13`  
**Artifact:** `07_AUDIT_REQUEST_AND_RESULT_CONTRACTS.md`  
**Synthesis gate:** `ACCEPT_WITH_CARRIED_UNKNOWNS`  
**Architecture verdict:** `READY_WITH_BLOCKING_QUESTIONS`  
**Scope:** Specification only. No implementation, credential change, runner registration, live model probe, API call, route certification, or repository mutation is authorized.


## Contract posture

`PROPOSED` The broker contracts are transport contracts. They must reference, not replace, the existing embedded-audit proof schema and handoff rules.

## Canonical request envelope

The request should be strict, versioned, canonicalized, and digest-bound.

```json
{
  "schema_version": "1.0.0",
  "request_id": "uuid",
  "campaign_or_policy_version": "string",
  "repository": {
    "id": 123,
    "full_name": "owner/repo",
    "owner_id": 456
  },
  "pull_request": {
    "number": 42,
    "base_ref": "main",
    "event_base_sha": "hex",
    "head_ref": "feature",
    "head_sha": "hex"
  },
  "source": {
    "mode": "OPERATOR_LOCAL_OR_GITHUB_PULL",
    "workflow_repository": "owner/repo",
    "workflow_path": ".github/workflows/audit-request.yml",
    "workflow_ref": "owner/repo/.github/workflows/audit-request.yml@trusted-sha",
    "run_id": 123456,
    "run_attempt": 1,
    "actor": "login",
    "actor_id": 789
  },
  "freshness": {
    "created_at": "RFC3339",
    "expires_at": "RFC3339",
    "nonce": "random-at-least-128-bit"
  },
  "input": {
    "diff_sha256": "hex",
    "diff_bytes": 12345,
    "file_count": 12,
    "metadata_sha256": "hex",
    "artifact_sha256": "hex-or-null"
  },
  "classification": {
    "risk_class": "E0|T1|R2|B3|S4",
    "privacy_class": "PUBLIC|PRIVATE|SENSITIVE|CLIENT|RELEASE",
    "complexity_band": "LOW|MEDIUM|HIGH|UNKNOWN",
    "fail_closed_triggers": []
  },
  "route": {
    "recommendation": "route-id",
    "allowed_route_ids": [],
    "human_approval_id": "string-or-null",
    "automatic_execution_permitted": false
  },
  "contract_refs": {
    "embedded_audit_schema": "existing-canonical-ref",
    "proof_contract_version": "string",
    "routing_policy_hash": "hex"
  },
  "payload_sha256": "hex"
}
```

### Request validation order

`PROPOSED`

1. Strict schema parse and size limits.
2. Verify canonical payload digest.
3. Verify source identity through local operator evidence or GitHub APIs.
4. Verify repository ID and name pairing.
5. Verify workflow path and trusted ref for GitHub-origin requests.
6. Verify PR number, base SHA, and head SHA.
7. Verify artifact and diff digests.
8. Enforce expiry and durable replay check.
9. Re-fetch current PR head immediately before dispatch.
10. Apply privacy and route eligibility gates.
11. Require human approval where policy says so.

## Canonical result envelope

```json
{
  "schema_version": "1.0.0",
  "result_id": "uuid",
  "request_id": "uuid",
  "request_sha256": "hex",
  "repository_id": 123,
  "pr_number": 42,
  "event_base_sha": "hex",
  "head_sha": "hex",
  "route": {
    "route_id": "string",
    "route_profile_hash": "hex",
    "execution_mode": "MECHANICAL|MANUAL_RECEIPT|PLAN_CLI|DIRECT_API|OPENROUTER",
    "certification_id": "string-or-null",
    "fallback_used": false
  },
  "execution": {
    "tool": "string",
    "tool_version": "string",
    "worker_isolation": "DISPOSABLE_VM|CONTAINER|DEDICATED_USER|MANUAL",
    "worker_image_sha256": "hex-or-null",
    "effective_config_sha256": "hex-or-null",
    "network_policy_id": "string",
    "started_at": "RFC3339",
    "ended_at": "RFC3339",
    "exit_code": 0,
    "timeout": false
  },
  "identity": {
    "auth_class": "string",
    "billing_route": "PLAN|DIRECT_API|OPENROUTER|NOT_APPLICABLE|UNKNOWN",
    "requested_model": "string-or-null",
    "observed_model": "string-or-null",
    "provider": "string-or-null",
    "identity_confidence": "ATTESTED|ROUTE_METADATA|DISPLAYED|UNKNOWN"
  },
  "outcome": {
    "class": "SUCCESS|EXECUTION_FAILURE|MODEL_OUTPUT_FAILURE|MODEL_QUALITY_FAILURE|POLICY_BLOCK|AUDITOR_CONFLICT|HUMAN_ESCALATION",
    "status": "PASS_EVIDENCE|FINDINGS|BLOCKED|FAILED|STALE_HEAD",
    "stale_head": false,
    "containment_violation": false
  },
  "findings": [],
  "mechanical_evidence": [],
  "usage": {
    "input_tokens": null,
    "output_tokens": null,
    "provider_cost": null,
    "currency": null,
    "plan_credit_debit": null,
    "measurement_status": "UNKNOWN"
  },
  "provenance": {
    "provider_request_id": "string-or-null",
    "upstream_request_id": "string-or-null",
    "output_sha256": "hex",
    "evidence_digests": [],
    "broker_seal": "string"
  }
}
```

## Manual receipt contract

`PROPOSED` Manual receipts are a first-class compatibility path, not an automation loophole.

Required fields:

- tool and exact version where visible;
- operator identity;
- invocation mode, app or CLI;
- request ID and exact head SHA shown to the operator;
- timestamp;
- prompt or instruction hash;
- output artifact digest;
- requested/displayed model;
- identity confidence, normally `DISPLAYED` or `UNKNOWN`;
- auth and billing route, with `UNKNOWN` allowed;
- screenshots or transcripts as supporting evidence only;
- operator attestation that no candidate code was executed outside approved containment;
- explicit `manual_receipt: true`.

A manual receipt cannot satisfy strong model/provider independence unless independent identity evidence exists.

## Proof integration

`PROPOSED`

- The result envelope is supporting execution evidence.
- The existing embedded-audit object retains canonical verdict semantics.
- A proof bundle records the primary report, manifest, warnings/blockers, and handoff when required.
- Model-routing fields are additive and must not fork the proof schema.
- PR Steward receives an exact-head-bound result plus proof references.

## Result acceptance gates

`PROPOSED` Reject governed proof when any of these occur:

- request or result schema invalid;
- head SHA mismatch;
- stale certification;
- unknown or mismatched actual provider/model where required;
- unapproved fallback;
- missing privacy or cost evidence;
- missing output digest;
- containment violation;
- manual receipt mislabeled as automated;
- parser salvage required to create a valid object.

## Redaction

`PROPOSED` Contracts must never contain raw credentials, cookies, keychain paths that reveal secrets, full auth files, or unredacted client data. Redaction occurs before storage and again before publication.
