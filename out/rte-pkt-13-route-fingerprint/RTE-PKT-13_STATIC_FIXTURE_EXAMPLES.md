# RTE-PKT-13 Static Fixture Examples

## Direct xAI

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
  "provider_schema_variant": "xai_relaxed_direct",
  "live_validation_status": "LIVE_VALIDATION_REQUIRED",
  "fingerprint_authority": "static_request_route_metadata",
  "live_provider_behavior_proven": false
}
```

## OpenRouter x-ai

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
  "provider_schema_variant": "openrouter_proxy_xai_relaxed",
  "direct_provider_guarantees_inherited": false,
  "live_validation_status": "LIVE_VALIDATION_REQUIRED",
  "fingerprint_authority": "static_request_route_metadata",
  "live_provider_behavior_proven": false
}
```

## Returned model metadata boundary

`returned_model_id`, when present in response metadata, remains separate from requested route identity. It is not part of `route_fingerprint_material` and does not rewrite `requested_provider`, `requested_model_id`, `provider_route_kind`, or `economic_surface`.
