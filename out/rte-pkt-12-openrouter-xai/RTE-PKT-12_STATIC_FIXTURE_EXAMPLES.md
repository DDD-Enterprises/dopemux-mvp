# RTE-PKT-12 Static Fixture Examples

These examples are redacted static metadata shapes exercised by local tests. They are not live provider responses.

Direct xAI request metadata:

```json
{
  "requested_provider": "xai",
  "requested_model_id": "grok-fixture",
  "provider_route_kind": "direct_provider",
  "upstream_provider": "xai",
  "economic_surface": "xai_direct",
  "api_key_env": "XAI_API_KEY",
  "endpoint_base_url": "https://api.x.ai/v1",
  "endpoint_effective": "https://api.x.ai/v1/chat/completions",
  "transport": "openai_sdk",
  "structured_output_mode": "json_schema",
  "provider_schema_variant": "xai_relaxed_direct",
  "live_validation_status": "LIVE_VALIDATION_REQUIRED"
}
```
OpenRouter x-ai request metadata:

```json
{
  "requested_provider": "openrouter",
  "requested_model_id": "x-ai/grok-fixture",
  "provider_route_kind": "openrouter_proxy_xai",
  "upstream_provider": "xai",
  "economic_surface": "openrouter",
  "api_key_env": "OPENROUTER_API_KEY",
  "endpoint_base_url": "https://openrouter.ai/api/v1",
  "endpoint_effective": "https://openrouter.ai/api/v1/chat/completions",
  "transport": "openai_sdk",
  "structured_output_mode": "json_schema",
  "provider_schema_variant": "openrouter_proxy_xai_relaxed",
  "live_validation_status": "LIVE_VALIDATION_REQUIRED",
  "direct_provider_guarantees_inherited": false
}
```

Returned model metadata remains response metadata and does not rewrite requested route identity:

```json
{
  "requested_provider": "openrouter",
  "requested_model_id": "x-ai/grok-fixture",
  "provider": "openrouter",
  "model_id": "x-ai/grok-fixture",
  "returned_model_id": "grok-fixture-returned",
  "provider_route_kind": "openrouter_proxy_xai",
  "economic_surface": "openrouter",
  "live_validation_status": "LIVE_VALIDATION_REQUIRED"
}
```
