"""Shared definitions for per-route request options.

Two route fields — ``service_tier`` and ``reasoning_effort`` — are surfaced from
``model_map.yaml`` through the phase contract, normalized at the payload
boundary, and forwarded to OpenAI-compatible chat completions and batch JSONL
bodies. Centralizing the constant + helper here prevents the previous drift
that allowed five copies of the same tuple and two near-duplicate helpers to
diverge.

Invariants beyond the allowlist:

1. ``""`` (empty / whitespace-only) is always dropped — never a valid request
   option value for either field.
2. Non-string scalars are always dropped (a YAML footgun where
   ``service_tier: true`` would otherwise stringify to ``"True"`` and be
   forwarded). ``None`` is treated as absence and dropped.
3. ``service_tier="none"`` is always dropped — no provider documents ``none``
   as a valid ``service_tier`` value (OpenAI's enum is
   ``default|flex|priority|auto``).
4. ``reasoning_effort="none"`` is **gated by route**: preserved only when the
   route's ``(provider, model_id)`` documents ``none`` as a valid enum value
   (currently xAI ``grok-4.3``: per xAI's documentation,
   ``reasoning_effort`` accepts ``none|low|medium|high`` and ``none`` is the
   migration-recommended setting for non-reasoning workloads). For all other
   routes — including OpenAI's reasoning family, which accepts
   ``minimal|low|medium|high`` — ``"none"`` is dropped so the call gracefully
   falls back to the provider's default rather than 4xx-ing on an
   unrecognized enum value.

Route context is supplied two ways:

- **Explicit kwargs** ``provider`` / ``model_id`` (preferred at the SDK
  payload boundary, where the caller knows the route authoritatively).
- **Dict-self inference** from ``value["provider"]`` and ``value["model_id"]``
  (used by early-stage parsers that pass full route dicts; the allowlist
  filter strips these keys from the returned dict so they never leak to the
  SDK body).

When both are absent, ``reasoning_effort="none"`` is dropped — the safe
default for legacy callers whose route identity isn't recoverable.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


ROUTE_REQUEST_OPTION_KEYS: Tuple[str, ...] = ("service_tier", "reasoning_effort")
"""Allowlist of per-route request options forwarded to provider SDKs."""


# Provider/model prefixes whose ``reasoning_effort`` enum documents ``none`` as
# a valid value. Match shape: ``(provider_lower, model_id_lower_prefix)``.
# Adding a new entry requires citing the provider doc that lists ``none`` as
# accepted — silently extending this allowlist would re-introduce the 4xx risk
# the gating exists to prevent.
_REASONING_EFFORT_NONE_ROUTES: Tuple[Tuple[str, str], ...] = (
    # xAI grok-4.3: ``reasoning_effort`` enum is ``none|low|medium|high``;
    # xAI migration guidance recommends ``none`` for non-reasoning workloads.
    ("xai", "grok-4.3"),
)


def _supports_reasoning_effort_none(
    provider: Optional[str], model_id: Optional[str]
) -> bool:
    """Return ``True`` if ``(provider, model_id)`` documents
    ``reasoning_effort="none"`` as a valid enum value.

    Match is case-insensitive on ``provider`` (exact match) and ``model_id``
    (prefix match, e.g. ``grok-4.3`` matches ``grok-4.3`` and any future
    point-release suffix like ``grok-4.3-mini``).
    """
    if not provider or not model_id:
        return False
    provider_lower = str(provider).strip().lower()
    model_lower = str(model_id).strip().lower()
    if not provider_lower or not model_lower:
        return False
    for supported_provider, supported_model_prefix in _REASONING_EFFORT_NONE_ROUTES:
        if (
            provider_lower == supported_provider
            and model_lower.startswith(supported_model_prefix)
        ):
            return True
    return False


def normalize_route_request_options(
    value: Optional[Any],
    *,
    provider: Optional[str] = None,
    model_id: Optional[str] = None,
) -> Dict[str, str]:
    """Return only the allowlisted, gated options from ``value``.

    Args:
        value: A mapping that may contain ``service_tier`` / ``reasoning_effort``
            entries (typically a contract route dict). Non-mappings are
            tolerated and produce an empty dict.
        provider: Explicit provider name (``"xai"``, ``"openai"``, ...). When
            given, takes precedence over any ``value["provider"]``.
        model_id: Explicit model identifier (``"grok-4.3"``, ``"gpt-5.4-mini"``,
            ...). When given, takes precedence over any ``value["model_id"]``.

    Returns:
        A new dict with allowlisted keys only. ``""`` and non-string scalars
        are always dropped. ``service_tier="none"`` is always dropped (no
        provider documents it). ``reasoning_effort="none"`` is preserved only
        when the effective ``(provider, model_id)`` is in
        :data:`_REASONING_EFFORT_NONE_ROUTES`; otherwise dropped.
    """
    if not isinstance(value, dict):
        return {}
    effective_provider = (
        provider if provider is not None else value.get("provider")
    )
    effective_model_id = (
        model_id if model_id is not None else value.get("model_id")
    )
    reasoning_none_allowed = _supports_reasoning_effort_none(
        effective_provider, effective_model_id
    )
    out: Dict[str, str] = {}
    for option_key in ROUTE_REQUEST_OPTION_KEYS:
        raw = value.get(option_key)
        if raw is None or not isinstance(raw, str):
            continue
        option_value = raw.strip()
        if not option_value:
            continue
        if option_value.lower() == "none":
            if option_key == "reasoning_effort" and reasoning_none_allowed:
                out[option_key] = "none"
            # service_tier="none" or unsupported reasoning_effort route:
            # drop so the call falls back to the provider default rather
            # than 4xx-ing on an unrecognized enum value.
            continue
        out[option_key] = option_value
    return out
