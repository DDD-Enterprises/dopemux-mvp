from __future__ import annotations

import sys
from pathlib import Path

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))

from benchmarking.direct_model.adapters.openrouter import OpenRouterDirectAdapter
from benchmarking.direct_model.adapters.xai import XaiDirectAdapter


def test_openrouter_adapter_exposes_expected_authority_fields() -> None:
    adapter = OpenRouterDirectAdapter()
    assert adapter.provider_name == "openrouter"
    assert adapter.surface_id == "surface_openrouter_api_v1"
    assert adapter.api_key_env == "OPENROUTER_API_KEY"


def test_xai_adapter_exposes_expected_authority_fields() -> None:
    adapter = XaiDirectAdapter()
    assert adapter.provider_name == "xai"
    assert adapter.surface_id == "surface_xai_api_v1"
    assert adapter.api_key_env == "XAI_API_KEY"
