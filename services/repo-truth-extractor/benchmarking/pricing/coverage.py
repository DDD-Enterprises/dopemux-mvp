from __future__ import annotations

from collections import Counter
from typing import Any

from lib.pricing_surface import normalize_provider_model, pricing_surface_metadata

from .catalog import ACTIVE_BENCHMARK_UNIVERSE, PricingCatalog, load_pricing_catalog


def _coverage_class(status: str) -> str:
    if status == "PRICED_CONFIRMED":
        return "priced"
    if status == "PRICED_WITH_CAVEAT":
        return "partially_priced"
    if status == "NOT_APPLICABLE":
        return "not_applicable"
    if status == "STALE_NEEDS_REFRESH":
        return "stale"
    return "unknown"


def build_pricing_coverage_report(
    *,
    universe: list[str] | tuple[str, ...] = ACTIVE_BENCHMARK_UNIVERSE,
    catalog: PricingCatalog | None = None,
) -> dict[str, Any]:
    active_catalog = catalog or load_pricing_catalog()
    rows: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()

    for model_key in universe:
        normalized_key = str(model_key).strip().lower()
        provider, model_id = normalize_provider_model(None, normalized_key)
        surface = pricing_surface_metadata(provider=provider, model_id=model_id)
        entry = active_catalog.models.get(normalized_key)
        if entry is None:
            row = {
                "model_key": normalized_key,
                "coverage_class": "unknown",
                "pricing_status": "UNPRICED_UNKNOWN",
                "pricing_confidence": "UNKNOWN",
                "pricing_source_type": "unknown",
                "pricing_source_ref": "",
                "surface_scope": "unknown",
                "input_cost_per_m": None,
                "output_cost_per_m": None,
                "pricing_caveat": "No catalog entry present for active benchmark candidate.",
                **surface,
            }
        else:
            row = {
                "model_key": normalized_key,
                "coverage_class": _coverage_class(str(entry["pricing_status"])),
                "pricing_status": str(entry["pricing_status"]),
                "pricing_confidence": str(entry["pricing_confidence"]),
                "pricing_source_type": str(entry["pricing_source_type"]),
                "pricing_source_ref": str(entry["pricing_source_ref"]),
                "surface_scope": str(entry["surface_scope"]),
                "input_cost_per_m": (
                    None if entry["input_cost_per_m"] is None else float(entry["input_cost_per_m"])
                ),
                "output_cost_per_m": (
                    None if entry["output_cost_per_m"] is None else float(entry["output_cost_per_m"])
                ),
                "pricing_caveat": str(entry.get("pricing_caveat") or ""),
                **surface,
            }
        counts[row["coverage_class"]] += 1
        rows.append(row)

    rows.sort(key=lambda row: row["model_key"])
    return {
        "pricing_catalog_version": active_catalog.version,
        "pricing_catalog_source": active_catalog.source,
        "active_benchmark_universe_size": len(universe),
        "coverage_counts": dict(sorted(counts.items())),
        "rows": rows,
        "priced_candidates": [row["model_key"] for row in rows if row["coverage_class"] == "priced"],
        "partially_priced_candidates": [
            row["model_key"] for row in rows if row["coverage_class"] == "partially_priced"
        ],
        "unknown_candidates": [row["model_key"] for row in rows if row["coverage_class"] == "unknown"],
        "stale_candidates": [row["model_key"] for row in rows if row["coverage_class"] == "stale"],
    }
