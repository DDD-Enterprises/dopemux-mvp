from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from .normalization import normalize_pricing_entry


SERVICE_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = SERVICE_ROOT.parents[1]
PRICING_CONFIG_PATH = REPO_ROOT / "config" / "pricing.yaml"
ACTIVE_BENCHMARK_UNIVERSE = (
    "openrouter/openai/gpt-5.4",
    "xai/grok-4.20",
    "openrouter/x-ai/grok-4.1-fast",
    "openai/gpt-5.4",
    "openai/gpt-5.4-mini",
    "openrouter/openai/gpt-5.3-codex",
    "xai/grok-4.20-beta-0309-reasoning",
    "gemini/gemini-3.1-pro-preview",
    "local/benchmark-fixture",
)


@dataclass(frozen=True)
class PricingCatalog:
    version: str
    source: str
    models: dict[str, dict[str, Any]]


def load_pricing_catalog(path: Path = PRICING_CONFIG_PATH) -> PricingCatalog:
    if not path.exists():
        raise RuntimeError(f"Pricing config missing: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError(f"Pricing config must decode to an object: {path}")
    models_payload = payload.get("models")
    if not isinstance(models_payload, dict) or not models_payload:
        raise RuntimeError(f"Pricing config missing models map: {path}")
    normalized_models = {
        str(model_key).strip().lower(): normalize_pricing_entry(str(model_key), row)
        for model_key, row in models_payload.items()
    }
    return PricingCatalog(
        version=str(payload.get("version") or "UNKNOWN"),
        source=str(payload.get("source") or str(path)),
        models=normalized_models,
    )


def load_rate_registry(path: Path = PRICING_CONFIG_PATH) -> tuple[dict[str, dict[str, Decimal | str]], str]:
    catalog = load_pricing_catalog(path)
    registry: dict[str, dict[str, Decimal | str]] = {}
    for model_key, row in catalog.models.items():
        input_cost = row.get("input_cost_per_m")
        output_cost = row.get("output_cost_per_m")
        if input_cost is None or output_cost is None:
            continue
        registry[model_key] = {
            "input_cost_per_m": input_cost,
            "output_cost_per_m": output_cost,
            "pricing_status": str(row["pricing_status"]),
            "pricing_confidence": str(row["pricing_confidence"]),
            "pricing_source_type": str(row["pricing_source_type"]),
            "pricing_source_ref": str(row["pricing_source_ref"]),
            "pricing_currency": str(row["pricing_currency"]),
            "surface_scope": str(row["surface_scope"]),
        }
    return registry, path.read_text(encoding="utf-8")
