# RTE-PKT-15 Static Fixture Examples

## Enriched OpenRouter x-ai Route Metadata

```json
{
  "requested_provider": "openrouter",
  "requested_model_id": "x-ai/grok-fixture",
  "provider_route_kind": "openrouter_proxy_xai",
  "upstream_provider": "xai",
  "economic_surface": "openrouter",
  "api_key_env": "OPENROUTER_API_KEY",
  "endpoint_effective": "https://openrouter.ai/api/v1/chat/completions",
  "transport": "openai_sdk",
  "provider_signature": "provider=openrouter;model=x-ai/grok-fixture;host=openrouter.ai;path=/api/v1/chat/completions;auth_mode=bearer",
  "structured_output_mode": "json_schema",
  "provider_schema_variant": "openrouter_proxy_xai_relaxed",
  "live_validation_status": "LIVE_VALIDATION_REQUIRED",
  "direct_provider_guarantees_inherited": false,
  "fingerprint_authority": "static_request_route_metadata",
  "route_identity_authority": "static_request_route_metadata",
  "live_provider_behavior_proven": false,
  "route_fingerprint_material": {
    "requested_provider": "openrouter",
    "requested_model_id": "x-ai/grok-fixture",
    "provider_route_kind": "openrouter_proxy_xai",
    "upstream_provider": "xai",
    "economic_surface": "openrouter",
    "api_key_env": "OPENROUTER_API_KEY",
    "endpoint_effective": "https://openrouter.ai/api/v1/chat/completions",
    "transport": "openai_sdk",
    "provider_signature": "provider=openrouter;model=x-ai/grok-fixture;host=openrouter.ai;path=/api/v1/chat/completions;auth_mode=bearer",
    "structured_output_mode": "json_schema",
    "provider_schema_variant": "openrouter_proxy_xai_relaxed",
    "live_validation_status": "LIVE_VALIDATION_REQUIRED"
  },
  "route_fingerprint_hash": "<sha256>",
  "pricing_surface": "openrouter",
  "pricing_authority": "openrouter_catalog_or_unknown",
  "pricing_surface_source": "static_request_route_metadata",
  "pricing_live_validation_status": "LIVE_VALIDATION_REQUIRED",
  "direct_provider_billing_inherited": false
}
```

## Direct xAI Comparator Metadata

```json
{
  "requested_provider": "xai",
  "requested_model_id": "grok-fixture",
  "provider_route_kind": "direct_provider",
  "upstream_provider": "xai",
  "economic_surface": "xai_direct",
  "api_key_env": "XAI_API_KEY",
  "pricing_surface": "xai_direct",
  "pricing_authority": "direct_provider_catalog_or_unknown",
  "pricing_live_validation_status": "LIVE_VALIDATION_REQUIRED",
  "direct_provider_billing_inherited": null
}
```

## Response Metadata Policy

`returned_model_id` is accepted as response metadata when present in request metadata fixtures, but it is not included in `route_fingerprint_material` and does not rewrite `requested_provider`, `requested_model_id`, `economic_surface`, or `pricing_surface`.

## Spend Ledger Compatibility Fixture

```json
{
  "models": {
    "openrouter/x-ai/grok-4.1-fast": {
      "provider": "openrouter",
      "model_id": "x-ai/grok-4.1-fast",
      "pricing_key": "openrouter/x-ai/grok-4.1-fast",
      "pricing_source": "fixture",
      "upstream_provider": "xai",
      "economic_surface": "openrouter",
      "pricing_surface": "openrouter",
      "direct_provider_billing_inherited": false,
      "additive_future_field": "ignored_by_loader"
    }
  }
}
```

The loader preserves the known pricing/economic fields and ignores the future additive field rather than failing on strict row shape.
