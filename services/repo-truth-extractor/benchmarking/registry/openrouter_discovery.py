from __future__ import annotations

import argparse
import json
import os
import re
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


UNKNOWN = "UNKNOWN"
SNAPSHOT_SCHEMA_ID = "rte_openrouter_route_metadata_discovery_v1"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
LIVE_FETCH_ENV = "RTE_OPENROUTER_DISCOVERY_LIVE"

CLASSIFICATION_LABELS = (
    "DIRECT_OVERLAP_EXCLUDE",
    "DIRECT_OVERLAP_EXCEPTION",
    "OPENROUTER_VALUE_CANDIDATE",
    "FREE_EXPERIMENTAL",
    "BENCHMARK_ONLY",
    "DO_NOT_RECOMMEND",
)

_SECRET_PATTERNS = (
    re.compile(r"Authorization:\s*Bearer\s+[A-Za-z0-9_\-.]{10,}", re.IGNORECASE),
    re.compile(r"Bearer\s+[A-Za-z0-9_\-.]{10,}", re.IGNORECASE),
    re.compile(r"\bsk" r"-or-[A-Za-z0-9_\-.]{8,}\b", re.IGNORECASE),
    re.compile(r"\bOPENROUTER_API_KEY\s*=\s*\S+", re.IGNORECASE),
    re.compile(r"\bV5_OPENROUTER_API_KEY\s*=\s*\S+", re.IGNORECASE),
)

_DIRECT_OVERLAP_VENDORS = {
    "anthropic",
    "google_gemini",
    "mistral_flagship",
    "openai",
    "xai",
}
_EXPLICIT_EXCEPTION_VENDORS = {
    "anthropic",
    "deepseek",
    "stepfun",
    "zai",
}
_DIRECT_PLATFORM_BENCHMARK_VENDORS = {
    "cohere",
    "ibm_granite",
    "meta_llama",
}
_HOSTED_OPEN_WEIGHT_VENDORS = {
    "arcee",
    "gemma",
    "nvidia",
    "prime_intellect",
    "qwen",
    "reka",
}
_BENCHMARKABLE_OR_ADVANTAGE_MARKERS = (
    "pinned free",
    ":free",
    "hosted open-weight",
    "structured output",
    "require_parameters",
    "max_price",
    "data_collection",
    "zdr",
    "provider fallback",
    "route telemetry",
    "schema reliability",
)


class OpenRouterMetadataError(ValueError):
    """Raised when OpenRouter metadata cannot be normalized safely."""


def stable_snapshot_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _redact_string(value: str) -> str:
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def _safe_string(value: Any, *, field: str, required: bool = False) -> str:
    if value is None:
        if required:
            raise OpenRouterMetadataError(f"missing required field: {field}")
        return UNKNOWN
    if not isinstance(value, str):
        raise OpenRouterMetadataError(f"{field} must be a string")
    normalized = value.strip()
    if not normalized and required:
        raise OpenRouterMetadataError(f"missing required field: {field}")
    if any(pattern.search(normalized) for pattern in _SECRET_PATTERNS):
        if field == "id":
            raise OpenRouterMetadataError("model id contains sensitive token pattern")
        return _redact_string(normalized)
    return normalized or UNKNOWN


def _optional_number(model: dict[str, Any], field: str) -> int | float | str:
    if field not in model or model[field] is None:
        return UNKNOWN
    value = model[field]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise OpenRouterMetadataError(f"{field} must be a number when present")
    return value


def _supported_parameters(model: dict[str, Any]) -> list[str] | str:
    if "supported_parameters" not in model or model["supported_parameters"] is None:
        return UNKNOWN
    params = model["supported_parameters"]
    if not isinstance(params, list) or not all(isinstance(item, str) for item in params):
        raise OpenRouterMetadataError("supported_parameters must be a string array")
    return sorted({item.strip() for item in params if item.strip()})


def _pricing(model: dict[str, Any]) -> dict[str, Any] | str:
    if "pricing" not in model or model["pricing"] is None:
        return UNKNOWN
    pricing = model["pricing"]
    if not isinstance(pricing, dict):
        raise OpenRouterMetadataError("pricing must be an object when present")
    normalized: dict[str, Any] = {}
    for key, value in sorted(pricing.items()):
        if isinstance(value, bool) or (
            not isinstance(value, (str, int, float)) and value is not None
        ):
            raise OpenRouterMetadataError("pricing values must be scalar when present")
        normalized[str(key)] = _redact_string(value) if isinstance(value, str) else value
    return normalized


def _top_provider_context_length(model: dict[str, Any]) -> int | float | str:
    if "top_provider" not in model or model["top_provider"] is None:
        return UNKNOWN
    top_provider = model["top_provider"]
    if not isinstance(top_provider, dict):
        raise OpenRouterMetadataError("top_provider must be an object when present")
    value = top_provider.get("context_length")
    if value is None:
        return UNKNOWN
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise OpenRouterMetadataError(
            "top_provider.context_length must be a number when present"
        )
    return value


def _is_free(model_id: str, pricing: dict[str, Any] | str) -> bool:
    if model_id.lower().endswith(":free"):
        return True
    if not isinstance(pricing, dict):
        return False
    price_values = [
        pricing.get(key)
        for key in ("prompt", "completion", "request")
        if key in pricing
    ]
    if not price_values:
        return False
    try:
        return all(float(str(value)) == 0.0 for value in price_values)
    except (TypeError, ValueError):
        return False


def _free_or_paid(model_id: str, pricing: dict[str, Any] | str) -> str:
    if _is_free(model_id, pricing):
        return "FREE"
    if not isinstance(pricing, dict):
        return UNKNOWN
    price_values = [
        pricing.get(key)
        for key in ("prompt", "completion", "request")
        if key in pricing
    ]
    if not price_values:
        return UNKNOWN
    try:
        if any(float(str(value)) > 0.0 for value in price_values):
            return "PAID"
    except (TypeError, ValueError):
        return UNKNOWN
    return "FREE"


def _structured_output_support(supported_parameters: list[str] | str) -> str:
    if supported_parameters == UNKNOWN:
        return UNKNOWN
    params = {item.lower() for item in supported_parameters}
    if "structured_outputs" in params:
        return "SUPPORTED"
    if "response_format" in params:
        return "RESPONSE_FORMAT_DECLARED"
    return "NOT_DECLARED"


def _vendor_key(model_id: str) -> str:
    token = model_id.lower()
    prefix, _sep, slug = token.partition("/")
    if prefix == "openai":
        return "openai"
    if prefix == "google" and "gemini" in slug:
        return "google_gemini"
    if prefix == "google" and "gemma" in slug:
        return "gemma"
    if prefix == "anthropic" or "claude" in slug:
        return "anthropic"
    if prefix == "x-ai" or "grok" in slug:
        return "xai"
    if prefix == "mistralai" and slug.startswith(("mistral-large", "mistral-medium")):
        return "mistral_flagship"
    if prefix == "moonshotai" and "kimi-k2" in slug:
        return "kimi_k2"
    if prefix == "cohere":
        return "cohere"
    if prefix == "meta-llama":
        return "meta_llama"
    if prefix in {"ibm", "ibm-granite"} or "granite" in slug:
        return "ibm_granite"
    if prefix == "qwen":
        return "qwen"
    if prefix.startswith("arcee"):
        return "arcee"
    if prefix in {"primeintellect", "prime-intellect"}:
        return "prime_intellect"
    if prefix == "nvidia":
        return "nvidia"
    if prefix == "rekaai" or prefix == "reka":
        return "reka"
    if prefix == "deepseek":
        return "deepseek"
    if prefix in {"z-ai", "zai"} or "glm" in slug:
        return "zai"
    if prefix.startswith("stepfun"):
        return "stepfun"
    if prefix == "openrouter":
        return "openrouter_native"
    return "unknown"


def _vendor_family(vendor_key: str) -> tuple[str, str]:
    mapping = {
        "anthropic": ("Anthropic", "Claude"),
        "arcee": ("Arcee", "Open-weight hosted"),
        "cohere": ("Cohere", "Command"),
        "deepseek": ("DeepSeek", "DeepSeek"),
        "gemma": ("Google Gemma", "Gemma"),
        "google_gemini": ("Google Gemini", "Gemini"),
        "ibm_granite": ("IBM Granite", "Granite"),
        "kimi_k2": ("Moonshot AI", "Kimi K2"),
        "meta_llama": ("Meta Llama", "Llama"),
        "mistral_flagship": ("Mistral", "Mistral flagship"),
        "nvidia": ("NVIDIA", "Hosted open-weight"),
        "openai": ("OpenAI", "GPT"),
        "openrouter_native": ("OpenRouter", "OpenRouter-native"),
        "prime_intellect": ("Prime Intellect", "Hosted open-weight"),
        "qwen": ("Qwen", "Qwen"),
        "reka": ("Reka", "Reka"),
        "stepfun": ("StepFun", "StepFun"),
        "xai": ("xAI", "Grok"),
        "zai": ("Z.ai", "GLM"),
    }
    return mapping.get(vendor_key, (UNKNOWN, UNKNOWN))


def _privacy_warning(model: dict[str, Any], vendor_key: str) -> str:
    description = str(model.get("description") or "").lower()
    if vendor_key == "openrouter_native" and (
        "prompt" in description and "output" in description and "logged" in description
    ):
        return "PROVIDER_LOGGING_INDICATED"
    if "provider logging" in description or "data collection" in description:
        return "PROVIDER_LOGGING_INDICATED"
    return UNKNOWN


def _benchmark_priority(label: str, structured_output_support: str) -> str:
    if label == "DIRECT_OVERLAP_EXCLUDE":
        return "LOW"
    if label == "DIRECT_OVERLAP_EXCEPTION":
        return "HIGH"
    if label == "OPENROUTER_VALUE_CANDIDATE":
        return "HIGH" if structured_output_support == "SUPPORTED" else "MEDIUM"
    if label == "FREE_EXPERIMENTAL":
        return "MEDIUM"
    if label == "DO_NOT_RECOMMEND":
        return "LOW"
    return "MEDIUM"


def _is_benchmarkable_exception_reason(reason: str) -> bool:
    normalized = reason.lower()
    return "benchmark" in normalized and any(
        marker in normalized for marker in _BENCHMARKABLE_OR_ADVANTAGE_MARKERS
    )


def _direct_overlap_status(vendor_key: str, label: str) -> str:
    if label == "DIRECT_OVERLAP_EXCEPTION":
        return "DIRECT_OVERLAP_EXCEPTION"
    if vendor_key in _DIRECT_OVERLAP_VENDORS:
        return "DIRECT_OVERLAP"
    if vendor_key in _EXPLICIT_EXCEPTION_VENDORS:
        return "DIRECT_OVERLAP_EXCEPTION_REQUIRES_OR_ADVANTAGE"
    if vendor_key in _DIRECT_PLATFORM_BENCHMARK_VENDORS:
        return "DIRECT_PLATFORM_ROUTE"
    if vendor_key == "unknown":
        return UNKNOWN
    return "NOT_DIRECT_OVERLAP"


def _classify_label_and_reasons(
    *,
    model_id: str,
    vendor_key: str,
    free_or_paid: str,
    privacy_warning: str,
    structured_output_support: str,
    or_advantage_reasons: dict[str, str],
) -> tuple[str, list[str]]:
    lower_id = model_id.lower()
    explicit_reason = or_advantage_reasons.get(model_id) or or_advantage_reasons.get(
        lower_id
    )
    reasons: list[str] = []

    if free_or_paid == "FREE" and (
        lower_id.endswith(":free") or vendor_key == "openrouter_native"
    ):
        reasons.append("OpenRouter free route is experimental and not production-routed.")
        if lower_id.endswith(":free"):
            reasons.append("Pinned :free variant is OpenRouter-only value.")
        if vendor_key == "openrouter_native":
            reasons.append("OpenRouter-native free route.")
        if privacy_warning != UNKNOWN:
            reasons.append("Provider logging/privacy warning is indicated.")
        return "FREE_EXPERIMENTAL", reasons

    if explicit_reason and vendor_key in _EXPLICIT_EXCEPTION_VENDORS:
        if not _is_benchmarkable_exception_reason(explicit_reason):
            reasons.append(
                "Explicit exception reason lacks a benchmarkable OpenRouter advantage."
            )
            return "BENCHMARK_ONLY", reasons
        reasons.append("Explicit repo-needed OpenRouter exception supplied.")
        reasons.append(_redact_string(explicit_reason))
        if structured_output_support == "SUPPORTED":
            reasons.append("Structured output support is declared by metadata.")
        return "DIRECT_OVERLAP_EXCEPTION", reasons

    if vendor_key in _DIRECT_OVERLAP_VENDORS:
        reasons.append(
            "Closed direct-provider duplicate route; OpenRouter-only advantage is not established."
        )
        return "DIRECT_OVERLAP_EXCLUDE", reasons

    if vendor_key == "kimi_k2":
        reasons.append("Kimi K2.x remains benchmark-only in first implementation.")
        return "BENCHMARK_ONLY", reasons

    if vendor_key in _DIRECT_PLATFORM_BENCHMARK_VENDORS:
        reasons.append(
            "Direct-platform route requires benchmark evidence before recommendation."
        )
        return "BENCHMARK_ONLY", reasons

    if vendor_key in _HOSTED_OPEN_WEIGHT_VENDORS:
        reasons.append("Hosted open-weight/non-direct route has OpenRouter-only value.")
        if structured_output_support == "SUPPORTED":
            reasons.append("Structured output support is declared by metadata.")
        return "OPENROUTER_VALUE_CANDIDATE", reasons

    if vendor_key in _EXPLICIT_EXCEPTION_VENDORS:
        reasons.append(
            "Potential direct-overlap exception lacks explicit measurable OpenRouter advantage."
        )
        return "BENCHMARK_ONLY", reasons

    reasons.append("Model family is not classified by the first OpenRouter snapshot rules.")
    return "BENCHMARK_ONLY", reasons


def classify_openrouter_model(
    model: dict[str, Any],
    *,
    or_advantage_reasons: dict[str, str] | None = None,
) -> dict[str, Any]:
    if not isinstance(model, dict):
        raise OpenRouterMetadataError("model entry must be an object")

    model_id = _safe_string(model.get("id"), field="id", required=True)
    name = _safe_string(model.get("name"), field="name")
    vendor_key = _vendor_key(model_id)
    vendor, family = _vendor_family(vendor_key)
    supported_parameters = _supported_parameters(model)
    pricing = _pricing(model)
    context_length = _optional_number(model, "context_length")
    top_provider_context_length = _top_provider_context_length(model)
    free_or_paid = _free_or_paid(model_id, pricing)
    structured_output_support = _structured_output_support(supported_parameters)
    privacy_warning = _privacy_warning(model, vendor_key)
    label, reasons = _classify_label_and_reasons(
        model_id=model_id,
        vendor_key=vendor_key,
        free_or_paid=free_or_paid,
        privacy_warning=privacy_warning,
        structured_output_support=structured_output_support,
        or_advantage_reasons=or_advantage_reasons or {},
    )
    if label not in CLASSIFICATION_LABELS:
        raise OpenRouterMetadataError(f"unsupported classification label: {label}")

    return {
        "id": model_id,
        "name": name,
        "vendor": vendor,
        "family": family,
        "classification_label": label,
        "classification_reasons": reasons,
        "free_or_paid": free_or_paid,
        "structured_output_support": structured_output_support,
        "supported_parameters": supported_parameters,
        "context_length": context_length,
        "top_provider_context_length": top_provider_context_length,
        "pricing": pricing,
        "direct_overlap_status": _direct_overlap_status(vendor_key, label),
        "benchmark_priority": _benchmark_priority(label, structured_output_support),
        "privacy_warning": privacy_warning,
    }


def _validate_models_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise OpenRouterMetadataError("OpenRouter payload must be an object")
    models = payload.get("data")
    if not isinstance(models, list):
        raise OpenRouterMetadataError("OpenRouter payload missing data array")
    if not all(isinstance(item, dict) for item in models):
        raise OpenRouterMetadataError("OpenRouter data entries must be objects")
    return models


def build_openrouter_discovery_snapshot(
    payload: dict[str, Any],
    *,
    source_ref: str = "openrouter_models_api",
    generated_at: str = UNKNOWN,
    live_fetch: bool = False,
    or_advantage_reasons: dict[str, str] | None = None,
) -> dict[str, Any]:
    models = [
        classify_openrouter_model(
            item,
            or_advantage_reasons=or_advantage_reasons,
        )
        for item in _validate_models_payload(payload)
    ]
    models.sort(key=lambda item: item["id"])
    counts = {label: 0 for label in CLASSIFICATION_LABELS}
    for item in models:
        counts[item["classification_label"]] += 1
    counts = {label: count for label, count in counts.items() if count}
    return {
        "snapshot_schema_id": SNAPSHOT_SCHEMA_ID,
        "source_ref": _redact_string(source_ref),
        "generated_at": generated_at,
        "live_fetch": bool(live_fetch),
        "model_count": len(models),
        "classification_counts": counts,
        "models": models,
        "notes": [
            "Classification is advisory metadata for RTE benchmarking and route-profile follow-up only.",
            "No production route is enabled by this snapshot.",
            "UNKNOWN marks absent or unproven metadata instead of inferred facts.",
        ],
    }


def _api_key_from_env() -> str | None:
    return (
        os.environ.get("OPENROUTER_API_KEY", "").strip()
        or os.environ.get("V5_OPENROUTER_API_KEY", "").strip()
        or None
    )


def fetch_openrouter_models_live(timeout_seconds: float = 30.0) -> dict[str, Any]:
    if os.environ.get(LIVE_FETCH_ENV) != "1":
        raise OpenRouterMetadataError(
            f"live OpenRouter discovery requires {LIVE_FETCH_ENV}=1"
        )
    headers = {"Accept": "application/json"}
    api_key = _api_key_from_env()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    request = urllib.request.Request(OPENROUTER_MODELS_URL, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        raise OpenRouterMetadataError(
            f"OpenRouter models fetch failed with HTTP {exc.code}"
        ) from exc
    except urllib.error.URLError as exc:
        raise OpenRouterMetadataError("OpenRouter models fetch failed") from exc
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise OpenRouterMetadataError("OpenRouter models response was not JSON") from exc
    _validate_models_payload(payload)
    return payload


def write_openrouter_discovery_snapshot(
    *,
    input_payload: dict[str, Any] | None = None,
    output_path: Path | None = None,
    live_fetch: bool = False,
    or_advantage_reasons: dict[str, str] | None = None,
) -> Path:
    if live_fetch:
        payload = fetch_openrouter_models_live()
        generated_at = datetime.now(timezone.utc).isoformat()
        if output_path is None:
            output_path = (
                Path(tempfile.gettempdir())
                / "rte_openrouter_discovery_snapshot.json"
            )
    else:
        if input_payload is None:
            raise OpenRouterMetadataError("input_payload is required without live_fetch")
        payload = input_payload
        generated_at = UNKNOWN
        if output_path is None:
            raise OpenRouterMetadataError("output_path is required for snapshot writes")

    snapshot = build_openrouter_discovery_snapshot(
        payload,
        generated_at=generated_at,
        live_fetch=live_fetch,
        or_advantage_reasons=or_advantage_reasons,
    )
    assert output_path is not None
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(stable_snapshot_json(snapshot) + "\n", encoding="utf-8")
    return output_path


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise OpenRouterMetadataError(f"input JSON is malformed: {path}") from exc
    if not isinstance(payload, dict):
        raise OpenRouterMetadataError("input JSON root must be an object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build an RTE OpenRouter route metadata discovery snapshot."
    )
    parser.add_argument("--input-json", type=Path)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)

    if args.live:
        write_openrouter_discovery_snapshot(
            output_path=args.output_json,
            live_fetch=True,
        )
        return 0
    if args.input_json is None:
        raise OpenRouterMetadataError("--input-json is required without --live")
    write_openrouter_discovery_snapshot(
        input_payload=_load_json(args.input_json),
        output_path=args.output_json,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
