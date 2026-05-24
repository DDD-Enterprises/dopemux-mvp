"""Shared definitions for per-route request options.

Two route fields — ``service_tier`` and ``reasoning_effort`` — are surfaced from
``model_map.yaml`` through the phase contract, normalized at the payload
boundary, and forwarded to OpenAI-compatible chat completions and batch JSONL
bodies. Centralizing the constant + helper here prevents the previous drift
that allowed five copies of the same tuple and two near-duplicate helpers to
diverge.

The normalize helper enforces one invariant beyond the allowlist:
``"none"`` (case + whitespace insensitive) is treated as the *absence* of the
field. xAI's documented ``reasoning_effort`` enum is ``low|high`` and OpenAI's
reasoning models accept ``minimal|low|medium|high`` — forwarding a literal
``"none"`` would 4xx. The YAML may continue to declare the literal as
documentation of intent; the runtime simply drops it.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


ROUTE_REQUEST_OPTION_KEYS: Tuple[str, ...] = ("service_tier", "reasoning_effort")
"""Allowlist of per-route request options forwarded to provider SDKs."""


_DROP_VALUES = frozenset({"", "none"})


def normalize_route_request_options(value: Optional[Any]) -> Dict[str, str]:
    """Return only the allowlisted, non-empty, non-"none" options from ``value``.

    Args:
        value: A mapping that may contain ``service_tier`` / ``reasoning_effort``
            entries (typically a contract route dict). Non-mappings are
            tolerated and produce an empty dict.

    Returns:
        A new dict with the allowlisted keys only, stripped to ``str``. Any
        value that strips/lowercases to ``""`` or ``"none"`` is dropped — the
        runtime must treat the literal ``"none"`` as the absence of the field.
    """
    if not isinstance(value, dict):
        return {}
    out: Dict[str, str] = {}
    for option_key in ROUTE_REQUEST_OPTION_KEYS:
        option_value = str(value.get(option_key) or "").strip()
        if option_value.lower() in _DROP_VALUES:
            continue
        out[option_key] = option_value
    return out
