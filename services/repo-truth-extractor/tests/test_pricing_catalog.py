from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SERVICE_ROOT = ROOT / "services" / "repo-truth-extractor"
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.pricing.catalog import load_pricing_catalog, load_rate_registry


def test_active_direct_model_candidates_have_catalog_entries() -> None:
    catalog = load_pricing_catalog()

    assert "openrouter/openai/gpt-5.4" in catalog.models
    assert "xai/grok-4.20" in catalog.models
    assert "openrouter/x-ai/grok-4.1-fast" in catalog.models


def test_rate_registry_skips_unknown_price_rows() -> None:
    registry, raw_text = load_rate_registry()

    assert "openrouter/openai/gpt-5.4" in registry
    assert "xai/grok-4.20" not in registry
    assert "RTE_PRICING_V2" in raw_text
