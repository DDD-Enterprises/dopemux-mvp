---
id: provider_availability_probe_spec
title: Provider Availability Probe Spec
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-06-17'
last_review: '2026-06-17'
next_review: '2026-09-15'
prelude: Provider Availability Probe Spec (explanation) for dopemux documentation
  and developer workflows.
---
# Provider Availability Probe Spec

schema_version: 1.0.0
status: PROPOSED

## Purpose

Determine route availability without leaking secrets or weakening policy.

## Universal no-secret logging rule

Availability probes MUST NOT log:

- API keys
- bearer tokens
- cookies
- private keys
- prompts containing repo secrets
- client data
- raw environment values

Probe logs MAY include provider, route profile, status code, error class, latency, timestamp, and redacted request ID.

## Probe targets

### OpenAI API

Probe:

- auth validity
- selected model availability
- structured output support where required
- rate-limit status
- latency
- request ID capture if available

Failure classes:

- `AUTH_FAILED`
- `MODEL_UNAVAILABLE`
- `RATE_LIMITED`
- `PROVIDER_OUTAGE`
- `SCHEMA_FEATURE_UNAVAILABLE`
- `UNKNOWN`

### Anthropic API

Probe:

- auth validity
- model availability
- structured/tool schema capability
- rate-limit status
- latency

Failure classes match OpenAI API.

### Gemini API

Probe:

- auth validity
- model availability
- stable/preview/experimental status
- structured output capability
- multimodal support if needed
- quota status

Failure classes include `PREVIEW_ONLY_ROUTE`.

### OpenRouter

Probe:

- API key validity
- route profile settings accepted
- provider availability
- `require_parameters`
- `data_collection`
- `zdr`
- `max_price`
- provider pin/order acceptance
- returned actual model and provider metadata when available

Failure classes:

- `AUTH_FAILED`
- `NO_PROVIDER_SATISFIES_POLICY`
- `RATE_LIMITED`
- `PROVIDER_OUTAGE`
- `PROVIDER_DRIFT`
- `SCHEMA_FEATURE_UNAVAILABLE`
- `MAX_PRICE_FILTERED`
- `UNKNOWN`

### Codex

Probe:

- auth mode: API key or ChatGPT sign-in
- local runner availability
- repo access
- non-mutating dry command
- model availability

Failure classes:

- `AUTH_FAILED`
- `LOCAL_RUNNER_UNAVAILABLE`
- `SUBSCRIPTION_PATH_NOT_PROGRAMMABLE`
- `UNKNOWN`

### Claude Code

Probe:

- auth mode
- local binary availability
- model/runner availability
- non-mutating repo read
- command execution permission posture

Failure classes:

- `AUTH_FAILED`
- `LOCAL_RUNNER_UNAVAILABLE`
- `CONSUMER_CREDENTIALS_NOT_ALLOWED_FOR_BACKEND`
- `UNKNOWN`

### Gemini / Antigravity

Probe:

- CLI/app availability
- API-key-backed mode when automation required
- consumer path warning
- model status

Failure classes:

- `LOCAL_RUNNER_UNAVAILABLE`
- `CONSUMER_CLI_NOT_SUPPORTED_FOR_AUTOMATION`
- `PREVIEW_ONLY_ROUTE`
- `UNKNOWN`

### Local runners

Probe:

- binary exists
- version
- workspace access
- sandbox posture
- dry-run command
- no network unless approved

Failure classes:

- `LOCAL_RUNNER_UNAVAILABLE`
- `SANDBOX_UNSAFE`
- `WORKTREE_UNAVAILABLE`
- `UNKNOWN`

## Timeout behavior

- Default probe timeout: 10 seconds.
- CI-blocking probe timeout: 5 seconds.
- Slow frontier model probe timeout: 30 seconds if explicitly allowed.
- Timeout class: `PROBE_TIMEOUT`.
- Timeout does not imply provider down; it marks route stale/unknown.

## Quota/rate-limit classification

- `RATE_LIMITED_RETRYABLE`: retry-after present or short quota window.
- `RATE_LIMITED_BLOCKING`: no retry viable within task deadline.
- `QUOTA_EXHAUSTED`: account-level quota unavailable.
- `UNKNOWN_QUOTA`: cannot determine safely.

## Provider outage classification

- `PROVIDER_OUTAGE_PARTIAL`
- `PROVIDER_OUTAGE_TOTAL`
- `ROUTER_OUTAGE`
- `UPSTREAM_PROVIDER_OUTAGE`
- `NETWORK_LOCAL_FAILURE`
- `UNKNOWN`

## Stale availability behavior

Availability is stale when:

- last probe is older than route TTL
- provider has had a failure since probe
- route profile changed
- privacy/risk class changed
- requested model changed
- benchmark certification expired

Stale availability cannot authorize high-risk or private routes.

## Safe fallback behavior

Fallback may only occur when:

- fallback route is policy-equivalent or stricter
- fallback is benchmark-certified
- fallback preserves schema requirements
- fallback preserves privacy requirements
- fallback preserves cost ceiling
- actual provider/model is logged
- route decision log records fallback reason
