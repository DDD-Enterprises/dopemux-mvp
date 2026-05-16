from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


STATIC_PRICING_SURFACE_AUTHORITY = "static_request_route_metadata"

PROVIDER_API_KEY_ENV: Dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "xai": "XAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


def _api_key_env_or_default(
    value: Optional[str],
    provider: str,
) -> Optional[str]:
    token = str(value or "").strip()
    if token in {"***redacted***", "[REDACTED]", "REDACTED"}:
        token = ""
    return token or PROVIDER_API_KEY_ENV.get(provider) or None


def normalize_provider_model(
    provider: Optional[str],
    model_id: Optional[str],
    route: Optional[str] = None,
) -> Tuple[str, str]:
    route_token = str(route or "").strip()
    provider_token = str(provider or "").strip().lower()
    model_token = str(model_id or "").strip()
    if route_token and (not provider_token or not model_token):
        if "/" in route_token:
            route_provider, route_model_id = route_token.split("/", 1)
            provider_token = provider_token or route_provider.strip().lower()
            model_token = model_token or route_model_id.strip()
    if not provider_token and "/" in model_token:
        first, rest = model_token.split("/", 1)
        if first:
            return first.strip().lower(), rest.strip()
    return provider_token, model_token


def classify_static_route_identity(
    *,
    provider: Optional[str],
    model_id: Optional[str],
    api_key_env: Optional[str] = None,
    route: Optional[str] = None,
) -> Dict[str, Any]:
    normalized_provider, requested_model_id = normalize_provider_model(
        provider, model_id, route
    )
    normalized_model_id = requested_model_id.lower()
    upstream_provider = normalized_provider if normalized_provider else "unknown"
    provider_route_kind = "unknown"
    economic_surface = "unknown"

    if normalized_provider == "openrouter":
        prefix, sep, _rest = normalized_model_id.partition("/")
        normalized_prefix = {"x-ai": "xai", "google": "gemini"}.get(prefix, prefix)
        economic_surface = "openrouter"
        if sep and normalized_prefix == "xai":
            provider_route_kind = "openrouter_proxy_xai"
            upstream_provider = "xai"
        elif sep and normalized_prefix in {"openai", "gemini", "anthropic"}:
            provider_route_kind = "openrouter_proxy_other"
            upstream_provider = normalized_prefix
        else:
            provider_route_kind = "openrouter_native_or_unknown"
            upstream_provider = "unknown"
    elif normalized_provider in {"xai", "openai", "gemini"}:
        provider_route_kind = "direct_provider"
        upstream_provider = normalized_provider
        economic_surface = {
            "xai": "xai_direct",
            "openai": "openai_direct",
            "gemini": "gemini_direct",
        }[normalized_provider]

    resolved_api_key_env = _api_key_env_or_default(
        api_key_env,
        normalized_provider,
    )
    identity: Dict[str, Any] = {
        "requested_provider": normalized_provider or "unknown",
        "requested_model_id": requested_model_id,
        "provider_route_kind": provider_route_kind,
        "upstream_provider": upstream_provider or "unknown",
        "economic_surface": economic_surface,
        "api_key_env": resolved_api_key_env,
        "live_validation_status": (
            "LIVE_VALIDATION_REQUIRED"
            if normalized_provider in {"xai", "openai", "gemini", "openrouter"}
            else "UNKNOWN"
        ),
        "route_identity_authority": STATIC_PRICING_SURFACE_AUTHORITY,
        "direct_provider_guarantees_inherited": (
            False if normalized_provider == "openrouter" else None
        ),
    }
    return {key: value for key, value in identity.items() if value is not None}


def pricing_surface_metadata(
    *,
    provider: Optional[str] = None,
    model_id: Optional[str] = None,
    route: Optional[str] = None,
    api_key_env: Optional[str] = None,
    route_identity: Optional[Dict[str, Any]] = None,
    endpoint_effective: Optional[str] = None,
    transport: Optional[str] = None,
    provider_signature: Optional[str] = None,
    route_fingerprint_hash: Optional[str] = None,
) -> Dict[str, Any]:
    identity = dict(route_identity or {})
    if not identity:
        identity = classify_static_route_identity(
            provider=provider,
            model_id=model_id,
            api_key_env=api_key_env,
            route=route,
        )

    requested_provider = str(
        identity.get("requested_provider") or provider or "unknown"
    ).strip().lower()
    requested_model_id = str(
        identity.get("requested_model_id") or model_id or ""
    ).strip()
    provider_route_kind = str(identity.get("provider_route_kind") or "unknown")
    upstream_provider = str(identity.get("upstream_provider") or "unknown")
    economic_surface = str(identity.get("economic_surface") or "unknown")
    resolved_api_key_env = _api_key_env_or_default(
        str(identity.get("api_key_env") or api_key_env or ""),
        requested_provider,
    )

    pricing_surface = economic_surface if economic_surface else "unknown"
    if pricing_surface == "openrouter":
        pricing_authority = "openrouter_catalog_or_unknown"
        direct_provider_billing_inherited: Optional[bool] = False
    elif provider_route_kind == "direct_provider" and upstream_provider in {
        "xai",
        "openai",
        "gemini",
    }:
        pricing_authority = "direct_provider_catalog_or_unknown"
        direct_provider_billing_inherited = None
    else:
        pricing_authority = "unknown"
        direct_provider_billing_inherited = None

    return {
        "requested_provider": requested_provider or "unknown",
        "requested_model_id": requested_model_id,
        "provider_route_kind": provider_route_kind,
        "upstream_provider": upstream_provider,
        "economic_surface": economic_surface or "unknown",
        "api_key_env": resolved_api_key_env,
        "endpoint_effective": endpoint_effective
        if endpoint_effective is not None
        else identity.get("endpoint_effective"),
        "transport": transport if transport is not None else identity.get("transport"),
        "provider_signature": provider_signature
        if provider_signature is not None
        else identity.get("provider_signature"),
        "route_fingerprint_hash": route_fingerprint_hash
        if route_fingerprint_hash is not None
        else identity.get("route_fingerprint_hash"),
        "pricing_authority": pricing_authority,
        "pricing_surface": pricing_surface or "unknown",
        "pricing_surface_source": STATIC_PRICING_SURFACE_AUTHORITY,
        "pricing_live_validation_status": str(
            identity.get("live_validation_status") or "UNKNOWN"
        ),
        "direct_provider_billing_inherited": direct_provider_billing_inherited,
    }


def pricing_surface_matrix_rows() -> list[Dict[str, Any]]:
    fixtures = (
        ("Direct xAI", "xai", "grok-fixture", "XAI_API_KEY"),
        ("OpenRouter x-ai", "openrouter", "x-ai/grok-fixture", "OPENROUTER_API_KEY"),
        ("OpenRouter OpenAI", "openrouter", "openai/gpt-fixture", "OPENROUTER_API_KEY"),
        ("OpenRouter unknown/native", "openrouter", "native-fixture", "OPENROUTER_API_KEY"),
        ("Direct OpenAI", "openai", "gpt-fixture", "OPENAI_API_KEY"),
        ("Direct Gemini", "gemini", "gemini-fixture", "GEMINI_API_KEY"),
        ("Unknown provider", "unknown", "model-fixture", None),
    )
    rows: list[Dict[str, Any]] = []
    for label, provider, model_id, api_key_env in fixtures:
        metadata = pricing_surface_metadata(
            provider=provider,
            model_id=model_id,
            api_key_env=api_key_env,
        )
        rows.append(
            {
                "label": label,
                **metadata,
                "billing_authority": metadata["pricing_authority"],
            }
        )
    return rows
