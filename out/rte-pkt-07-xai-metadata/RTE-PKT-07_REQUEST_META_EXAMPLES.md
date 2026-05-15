# RTE-PKT-07 Request Meta Examples

Examples are synthetic and redacted.

## Direct xAI

```json
{
  "provider": "xai",
  "model_id": "grok-requested-fixture",
  "requested_provider": "xai",
  "requested_model_id": "grok-requested-fixture",
  "provider_route_kind": "direct_provider",
  "returned_model_id": "grok-effective-fixture",
  "effective_model_id": "grok-effective-fixture",
  "response_id": "xai-local-001",
  "finish_reason": "stop",
  "usage": {
    "input_tokens": 10,
    "output_tokens": 4,
    "total_tokens": 14
  },
  "api_key_env": "XAI_API_KEY",
  "transport": "openai_sdk"
}
```

## OpenRouter xAI Proxy

```json
{
  "provider": "openrouter",
  "model_id": "x-ai/grok-proxy-fixture",
  "requested_provider": "openrouter",
  "requested_model_id": "x-ai/grok-proxy-fixture",
  "provider_route_kind": "openrouter_proxy_xai",
  "returned_model_id": "x-ai/grok-proxy-fixture",
  "effective_model_id": "x-ai/grok-proxy-fixture",
  "response_id": "or-local-001",
  "finish_reason": "stop",
  "api_key_env": "OPENROUTER_API_KEY",
  "transport": "openai_sdk"
}
```

## Refusal

```json
{
  "provider": "openai",
  "model_id": "gpt-refusal-fixture",
  "response_id": "chatcmpl-refusal",
  "returned_model_id": "gpt-refusal-fixture",
  "finish_reason": "stop",
  "refusal": true,
  "refusal_reason": "Cannot comply with [REDACTED].",
  "failure_type": null
}
```

## Incomplete

```json
{
  "provider": "openai",
  "model_id": "gpt-incomplete-fixture",
  "response_id": "chatcmpl-incomplete",
  "returned_model_id": "gpt-incomplete-fixture",
  "response_status": "incomplete",
  "finish_reason": "length",
  "incomplete": true,
  "incomplete_reason": "max_output_tokens"
}
```

## Structured Output

```json
{
  "provider": "openai",
  "model_id": "gpt-structured-fixture",
  "structured_output_mode": "json_schema",
  "response_format_type": "json_schema",
  "json_schema_name_if_present": "RTEFixtureSchema",
  "strict_schema_required": true,
  "provider_schema_variant": "openai_strict_json_schema"
}
```
