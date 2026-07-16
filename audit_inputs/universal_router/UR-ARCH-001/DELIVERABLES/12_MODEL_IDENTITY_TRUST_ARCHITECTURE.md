# Model Identity Trust Architecture

## Required identity fields

```text
requested_model
configured_model
model_response_claim
proxy_reported_model
provider_attested_model
attested_actual_model
model_identity_confidence
provider_request_id
identity_evidence_ref
identity_adapter_version
```

## Field semantics

| Field | Label | Semantics |
|---|---|---|
| `requested_model` | **PROPOSED** | Model ID or alias requested by policy/operator. Intent only. |
| `configured_model` | **PROPOSED** | Model resolved by local runner/proxy config before dispatch. Configuration fact only. |
| `model_response_claim` | **OBSERVED** | Model-generated text claiming identity. Always untrusted. |
| `proxy_reported_model` | **PROPOSED** | Model value observed in LiteLLM or another proxy response/trace. Useful observation, not automatically attested. |
| `provider_attested_model` | **PROPOSED** | Provider-controlled response/generation metadata explicitly naming the served model and tied to the request. |
| `attested_actual_model` | **PROPOSED** | Normalized provider-attested model after adapter verification; otherwise `UNKNOWN`. |
| `model_identity_confidence` | **PROPOSED** | Confidence level derived from evidence type, not model agreement. |
| `provider_request_id` | **PROPOSED** | Correlation identifier. Alone it is not attestation. |
| `identity_evidence_ref` | **PROPOSED** | Hash-pinned provider/proxy/runner evidence location. |
| `identity_adapter_version` | **PROPOSED** | Version of provider-specific normalization logic. |

## Confidence levels

```text
NONE
REQUESTED_ONLY
CONFIGURED
MODEL_CLAIM_ONLY
PROXY_OBSERVED
PROVIDER_ATTESTED
CONFLICTING
UNKNOWN
```

- **PROPOSED:** `PROVIDER_ATTESTED` is the only level that may populate `attested_actual_model` with a non-unknown value.
- **PROPOSED:** Agreement between requested/configured/model-claim/proxy values does not manufacture provider attestation.
- **PROPOSED:** A provider request ID with no provider-controlled model metadata yields at most `CONFIGURED` or `PROXY_OBSERVED`.

## Attestation acceptance test

A provider identity adapter may emit `PROVIDER_ATTESTED` only when all are true:

1. **PROPOSED:** Evidence originates from a provider-controlled response, generation record, or billing/usage metadata surface.
2. **PROPOSED:** Evidence explicitly identifies the served model, not merely the requested alias.
3. **PROPOSED:** Evidence is tied to the same request through request ID or equivalent provider correlation.
4. **PROPOSED:** Adapter knows the evidence field semantics for the provider/API version.
5. **PROPOSED:** Evidence ref and adapter version are retained.
6. **PROPOSED:** No unresolved conflict exists with another provider-controlled record.

- **PROPOSED:** If any test fails, `attested_actual_model=UNKNOWN`.

## Evidence trust order

1. **PROPOSED:** Provider-controlled request-linked model metadata.
2. **PROPOSED:** Provider-controlled generation or usage lookup tied to request.
3. **PROPOSED:** Proxy-reported provider/model observation.
4. **PROPOSED:** Runner configuration and requested values.
5. **PROPOSED:** Model-generated self-report.

- **PROPOSED:** Lower layers remain visible even when higher evidence exists.

## Conflict handling

- **PROPOSED:** `requested != configured` is configuration drift.
- **PROPOSED:** `configured != proxy_reported` is proxy or fallback drift.
- **PROPOSED:** `proxy_reported != provider_attested` is identity conflict requiring adapter/provider investigation.
- **PROPOSED:** `model_response_claim` disagreement is recorded but does not reduce a valid provider attestation by itself.
- **PROPOSED:** Multiple provider-controlled values that disagree yield `CONFLICTING`, not last-write-wins.

## Route effects

| Route condition | Label | Identity requirement |
|---|---|---|
| Low-risk advisory read/draft | **PROPOSED** | Requested/configured may suffice if identity is not a control; uncertainty displayed. |
| Exact/pinned-model policy | **PROPOSED** | Provider-attested actual identity required. |
| Benchmark certification | **PROPOSED** | Provider-attested actual identity required. |
| Independent audit based on provider/model separation | **PROPOSED** | Provider-attested identity for implementer and auditor, or claim remains unproven. |
| Security/authority route | **PROPOSED** | Attestation required when model identity is part of the security control; otherwise explicit supervisor decision. |
| Release-sensitive route | **PROPOSED** | Unknown actual identity blocks identity-dependent approval or certification. |
| Provider fallback | **PROPOSED** | Fallback identity must be observed and checked against policy/certification. |

## Local evidence implications

- **OBSERVED:** The successful Codex smoke emitted token counts but no machine-readable actual model field. Its payload self-identified as `gpt-5`, which is untrusted.
- **PROPOSED:** Codex `attested_actual_model` remains `UNKNOWN` until a provider-controlled identity surface is proven.
- **OBSERVED:** Claude contained smoke did not reach a provider and had empty model usage.
- **PROPOSED:** Claude actual identity remains `UNKNOWN` for that evidence.
- **OBSERVED:** Gemini, AGY, OpenRouter, and local LiteLLM provider identity were not live-proven in UR-INV-003.
- **PROPOSED:** Their actual identity remains `UNKNOWN` until fresh adapter evidence exists.

## LiteLLM boundary

- **OBSERVED:** Dopemux trace code can record response model/provider fields.
- **PROPOSED:** These populate `proxy_reported_model` and proxy provider observations.
- **PROPOSED:** A provider-specific adapter may later accept certain LiteLLM-carried fields as provider attestation only if it proves they are unmodified provider-controlled metadata tied to the request.
- **PROPOSED:** Generic LiteLLM observation alone is not enough.

## Fallback and aliases

- **PROPOSED:** Aliases are recorded in `requested_model`; resolved target goes to `configured_model`.
- **PROPOSED:** Fallback changes create a new identity observation and must be visible in the decision/result.
- **PROPOSED:** A certified exact-model route becomes invalid when fallback serves a different model, even if output quality is acceptable.
- **PROPOSED:** Provider presets or external routing state must be versioned/ref-hashed where possible; otherwise identity confidence is reduced.

## Adapter versioning and revocation

- **PROPOSED:** Identity adapters are provider/API-version specific.
- **PROPOSED:** A field semantic change, provider API change, proxy transformation change, or unresolved conflict revokes the adapter's attestation eligibility.
- **PROPOSED:** Historical observations keep the adapter version for replay.
- **PROPOSED:** Revocation blocks future certification but does not rewrite past records.

## Privacy and storage

- **PROPOSED:** Store request IDs only when policy permits; treat them as potentially sensitive correlation data.
- **PROPOSED:** Store hashed evidence refs and minimal normalized fields, not full provider payloads in the router database.
- **PROPOSED:** Full provider evidence belongs in an approved proof/evidence store with redaction and access controls.
