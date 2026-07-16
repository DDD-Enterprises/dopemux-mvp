# 07 — Identity, Usage, Containment, Network & Security Audit

## A. Model identity (`12`, T6)
Required fields all present and correctly separated: `requested_model, configured_model, model_response_claim,
proxy_reported_model, provider_attested_model, attested_actual_model, model_identity_confidence,
provider_request_id, identity_evidence_ref, identity_adapter_version`.

| Rule | Verdict |
|---|---|
| Model-generated text untrusted | PASS — `model_response_claim` "Always untrusted"; INV-003 Codex self-report `gpt-5` treated untrusted |
| Request ID ≠ attestation | PASS — "A provider request ID with no provider-controlled model metadata yields at most CONFIGURED or PROXY_OBSERVED" |
| Proxy observation ≠ provider attestation | PASS — `proxy_reported_model` separate; LiteLLM boundary explicit |
| Conflicts remain CONFLICTING (no last-write-wins) | PASS — "Multiple provider-controlled values that disagree yield CONFLICTING" |
| Insufficient evidence → attested_actual_model=UNKNOWN | PASS — 6-part attestation acceptance test; any failure → UNKNOWN |
| Unknown identity blocks pinned/benchmark/audit-independence/release routes | PASS — route-effects table + `17` red-lane controls |

**Attestation acceptance test** (`12`) is rigorous (provider-controlled + names served model + request-linked +
adapter knows semantics + evidence retained + no conflict). No path manufactures attestation from agreement.
This directly addresses UR-OQ-007 (CRITICAL) which correctly blocks benchmark/independent-audit/UR-TP-010/
release-sensitive routes until provider-controlled evidence exists. **No P0/P1.**

## B. Usage & cost (`13`, T7)
Required 12 fields present and separated. Verified rules:
- No token→plan-credit invention (INV-003: Codex reported tokens, no credits → `plan_credits=UNKNOWN`). PASS.
- Estimated cost never labeled actual (`estimated_cost` vs `api_cost` distinct; Freeflow cost stays `estimated_cost`). PASS.
- No subtraction-based fake runner overhead (INV-003: 17,298 effective-input vs tiny visible prompt → C-017 "do not infer overhead by subtraction"). PASS.
- Exact/estimated/session/unavailable kept separate (`exactness`, `observation_scope`). PASS.
- Historical decisions retain `pricing_version`; pricing updates don't rewrite past estimates. PASS.
- Unknown cost/credits do NOT auto-trigger premium escalation (a credit/cost error → same-tier alternate/operator choice/block). PASS.
- Freeflow remains state owner for quota/paid caps (referenced, not copied). PASS.

## C. Containment (`11`, T9)
Enforcement sources enumerated (`PROMPT_REQUESTED, RUNNER_ENFORCED, OS_ENFORCED, WRAPPER_ENFORCED,
OPERATOR_ENFORCED, UNVERIFIED`); every control records requested/effective/enforcement_source/evidence/confidence.
`PROMPT_REQUESTED` explicitly cannot satisfy an enforcement requirement (hard invariant). All 11 required
controls covered (read, write, worktree, file allowlist, command allowlist, MCP, network, env redaction,
session persistence, outputs, approvals). Profiles (`READ_ONLY_LOCAL`, `ADVISORY_PROVIDER`,
`BOUNDED_IMPLEMENTATION`, `INDEPENDENT_AUDIT`, `SECURITY_RELEASE`) enforce OS/wrapper for protected routes.
INV-003 flags Codex hard tool-denial UNKNOWN → correctly keeps Codex advisory only (UR-OQ-009 CRITICAL blocks
UR-TP-010). **No P0/P1.**

## D. Network (`11`, T10)
Six required postures present. Sandbox denial (`SANDBOX_NETWORK_DENIED`) scoped to environment, never provider/
host unhealth (C-014; observed live this run: python socket → PermissionError). DNS/auth/proxy/provider/policy/
sandbox failures kept distinct (`ENVIRONMENT_BLOCKED` taxonomy). Restricted-domain requires an enforcing layer;
`UNKNOWN` blocks networked routes. Environment repair never triggers premium escalation. **No P0/P1.**

## E. Security & failure model (`17`) — threat coverage
T1 authority capture · T2 policy tampering/shadow policy · T3 snapshot poisoning · T4 prompt injection ·
T5 secret leakage · T6 identity spoofing · T7 cost/credit laundering · T8 quota/admission bypass ·
T9 containment theatre · T10 environment misclassification · T11 audit collusion/self-cert ·
T12 proof/PR freshness · T13 journal tampering · T14 concurrent writer race · T15 path traversal/symlink/
output escape · T16 malformed/oversized input · T17 dependency/parser compromise · T18 provider drift/silent fallback.

Coverage is comprehensive and each threat has asset/threat/control/failure-result. Additional prompt threats
(acceptance replay → T14 idempotency keys + immutable acceptance; approval scope widening → override creates new
attempt, cannot widen; downgrade attacks / premium escalation loops → escalation budgets + env-failure lane;
stale-snapshot DoS → TTL + STALE handling; hidden subagent fanout → hard invariant NONE; recommendation-as-
execution → state limit; proof substitution → head SHA + content hash; cert replay after drift → tuple
invalidation) are all addressed.

**One substantive residual (P3, UR-AUDIT-R3-005):** T13's append-only relies on `BEFORE UPDATE/DELETE` triggers
(process-local integrity) plus parent_event + payload hash, but not an explicit cryptographic hash-chain, so a
direct-DB actor could rewrite history without guaranteed replay-time detection. Adequate for advisory evidence;
hardening recommended.

**Independence & attestation of THIS audit run (audit-independence audit):** the required audit states
(`NOT_REQUIRED..NEEDS_SUPERVISOR`) are correctly modeled; skipped ≠ pass and same-runner/session ≠ independent
are enforced. Per the prompt, I record this run's own limits: the auditor model identity is **runner-configured,
not provider-attested** (`RUNNER_CONFIGURED_NOT_PROVIDER_ATTESTED`); no provider-controlled served-model metadata
is available for this session, so I make **no provider-attested model-identity claim** for myself — mirroring the
architecture's own UR-OQ-007 posture.

**Domain verdict:** identity/usage/containment/network/security handling is rigorous and self-consistent; no
P0/P1; one P3 hardening (journal tamper-evidence).
