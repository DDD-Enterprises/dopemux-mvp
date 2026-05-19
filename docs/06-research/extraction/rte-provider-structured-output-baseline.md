---
id: rte-provider-structured-output-baseline
title: RTE Provider Structured Output Baseline
type: reference
owner: '@hu3mann'
author: codex
date: '2026-05-19'
last_review: '2026-05-19'
next_review: '2026-08-17'
prelude: External provider baseline for Repo Truth Extractor structured output, batch, streaming, and audit-state risks.
---
# RTE Provider Structured Output Baseline

This document imports an external research baseline for Repo Truth Extractor provider behavior.

Source report:

- `/Users/hue/Downloads/deep-research-report 12.md`

Status:

- `external_research`: provider claims are date-scoped to the imported report.
- `not_repo_truth`: this document does not prove current Dopemux runtime behavior.
- `NOT_RUN`: live provider verification was not rerun in this packet.
- `NOT_RUN`: live RTE extraction was not rerun in this packet.
- `NOT_RUN`: live Docker startup was not run in this packet.

## Core Finding

Structured output is shape control, not truth control.

Provider JSON-schema modes, function calling, tool calling, response schemas, and batch APIs can improve response shape. They do not prove that extracted facts are true, complete, source-grounded, policy-compliant, or safe to promote into repo authority.

For RTE, provider output must pass local validation before it is treated as an audit artifact:

- schema validation
- semantic validation
- source/provenance validation
- state validation
- truncation/refusal/content-filter validation
- deterministic post-processing where possible

## Audit-State Rules

RTE provider lanes should make these states first-class, not hidden exceptions:

- `ok`
- `refused`
- `truncated`
- `content_filtered`
- `tool_call_partial`
- `tool_call_invalid`
- `batch_pending`
- `batch_failed`
- `stream_interrupted`
- `schema_invalid`
- `semantic_invalid`
- `provenance_missing`
- `needs_human_review`

Do not collapse these into a single failed extraction string. The audit output should preserve state, provider, model, request mode, source paths, retry posture, and validation result.

## Provider Lane Baseline

### OpenAI Lane

The imported report identifies official OpenAI surfaces for function calling, structured outputs, streaming, batch processing, and enterprise privacy.

RTE implication:

- Record whether a response came from structured output, function/tool calling, streaming, or batch.
- Treat schema conformance as only the first validation step.
- Preserve refusal, truncation, tool-call, and content-filter states before promotion into audit output.
- Keep data-use and retention assumptions explicit in provider configuration and run metadata.

### Anthropic Lane

The imported report identifies official Anthropic surfaces for tool use, structured outputs, batch processing, rate limits, data retention, guardrails, memory, and fine-grained tool streaming.

RTE implication:

- Preserve the difference between tool-use structure and source-grounded truth.
- Treat fine-grained or partial tool streaming as a stateful audit hazard.
- Record provider memory and retention assumptions separately from repo memory systems.
- Do not promote model memory or managed-agent behavior into Dopemux repo truth.

### Gemini Lane

The imported report identifies official Gemini surfaces for structured output, function calling, thought signatures, tools, batch API, rate limits, usage policies, terms, zero data retention, and Deep Research.

RTE implication:

- Record structured-output and function-calling modes separately.
- Treat thought signatures and tool state as provider-specific operational context, not source evidence.
- Keep zero-data-retention and Vertex/Gemini behavior explicit by lane and account mode.
- Treat Deep Research outputs as external research unless separately grounded in repo evidence.

### xAI Lane

The imported report identifies official xAI surfaces for structured outputs, function calling, rate limits, security FAQ, model docs, and `llms.txt`.

RTE implication:

- Record schema mode, function-calling mode, model, and rate-limit posture.
- Treat security and retention claims as provider-lane metadata, not general RTE guarantees.
- Keep source provenance and local validation mandatory before artifact promotion.

## Required RTE Audit Criteria

Any future RTE provider implementation or audit packet should verify:

1. Provider lane identity is recorded for every extraction attempt.
2. Model identity and request mode are recorded.
3. Structured-output schema version is recorded.
4. Raw provider state is preserved enough to distinguish refusal, truncation, partial tool output, batch failure, and content filtering.
5. Local schema validation runs after provider output.
6. Semantic validation runs after schema validation.
7. Source/provenance validation ties claims back to repo files, line ranges, commits, or explicit external sources.
8. Repo content is treated as untrusted evidence, not as executable instructions.
9. External provider storage, retention, and training-use posture are captured in audit metadata.
10. Human-review gates exist for low-confidence or policy-sensitive extraction output.

## Security And Prompt-Injection Notes

Repo content must be treated as untrusted evidence.

Provider prompts should distinguish:

- operator instructions
- system/developer instructions
- repository content
- extracted snippets
- external research
- generated summaries

RTE should not let repository text override extraction policy, validation rules, provider routing, filesystem boundaries, or audit-promotion rules.

## Storage And Retention Notes

Provider storage and retention behavior is external to Dopemux and must be recorded per provider lane. Do not reuse a provider's privacy, zero-data-retention, or enterprise-retention statement as a generic RTE guarantee.

Each future provider audit should record:

- provider
- account or API mode when relevant
- model
- request mode
- batch or streaming mode
- data-retention posture
- whether prompts include repo content
- whether outputs include proprietary snippets
- whether outputs are stored locally

## Selected Source Ledger

The imported report used public provider documentation. These URLs are listed as source pointers from the report, not as live verification performed by this packet.

- OpenAI Function Calling: `https://developers.openai.com/api/docs/guides/function-calling`
- OpenAI Structured Outputs: `https://developers.openai.com/api/docs/guides/structured-outputs`
- OpenAI Streaming Responses: `https://developers.openai.com/api/docs/guides/streaming-responses`
- OpenAI Batch API: `https://platform.openai.com/docs/guides/batch`
- OpenAI Enterprise Privacy: `https://openai.com/enterprise-privacy/`
- Anthropic Tool Use: `https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview`
- Anthropic Structured Outputs: `https://platform.claude.com/docs/en/build-with-claude/structured-outputs`
- Anthropic Batch Processing: `https://platform.claude.com/docs/en/build-with-claude/batch-processing`
- Anthropic Data Retention: `https://platform.claude.com/docs/en/manage-claude/api-and-data-retention`
- Anthropic Prompt-Injection Mitigation: `https://platform.claude.com/docs/en/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks`
- Gemini Structured Output: `https://ai.google.dev/gemini-api/docs/structured-output`
- Gemini Function Calling: `https://ai.google.dev/gemini-api/docs/function-calling`
- Gemini Thought Signatures: `https://ai.google.dev/gemini-api/docs/thought-signatures`
- Gemini Batch API: `https://ai.google.dev/gemini-api/docs/batch-api`
- Gemini Zero Data Retention: `https://ai.google.dev/gemini-api/docs/zdr`
- Vertex AI Zero Data Retention: `https://cloud.google.com/vertex-ai/generative-ai/docs/vertex-ai-zero-data-retention`
- xAI Structured Outputs: `https://docs.x.ai/developers/model-capabilities/text/structured-outputs`
- xAI Function Calling: `https://docs.x.ai/developers/tools/function-calling`
- xAI Security FAQ: `https://docs.x.ai/developers/faq/security`
- xAI llms.txt: `https://docs.x.ai/llms.txt`

## Remaining Verification

This baseline is advisory until a future repo implementation or audit packet verifies current RTE behavior against active code and live provider behavior.

Remaining work:

- verify current RTE provider adapter architecture
- verify current schema and state taxonomy in runtime code
- verify live provider refusal/truncation/content-filter behavior in a controlled packet
- verify batch and streaming audit behavior if those modes are implemented
- verify storage and retention metadata capture for active provider lanes
