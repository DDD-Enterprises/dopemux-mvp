# RTE-PKT-14 Static Fixture Examples

## Direct xAI

```json
{
  "requested_provider": "xai",
  "requested_model_id": "grok-fixture",
  "provider_route_kind": "direct_provider",
  "upstream_provider": "xai",
  "economic_surface": "xai_direct",
  "pricing_surface": "xai_direct",
  "api_key_env": "XAI_API_KEY",
  "pricing_authority": "direct_provider_catalog_or_unknown",
  "pricing_live_validation_status": "LIVE_VALIDATION_REQUIRED",
  "direct_provider_billing_inherited": null
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
  "pricing_surface": "openrouter",
  "api_key_env": "OPENROUTER_API_KEY",
  "pricing_authority": "openrouter_catalog_or_unknown",
  "pricing_live_validation_status": "LIVE_VALIDATION_REQUIRED",
  "direct_provider_billing_inherited": false
}
```

## Spend Row Preservation

```json
{
  "provider": "openrouter",
  "model_id": "x-ai/grok-4.1-fast",
  "pricing_key": "openrouter/x-ai/grok-4.1-fast",
  "upstream_provider": "xai",
  "economic_surface": "openrouter",
  "pricing_surface": "openrouter",
  "direct_provider_billing_inherited": false
}
```

## No Live Claim

OpenRouter x-ai examples are static request-route fixtures only. They do not prove provider billing equivalence, retention, ZDR, rate limits, schema acceptance, returned-model behavior, or upstream response metadata.
