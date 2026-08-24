"""Trusted adapter registry — DMX-DCP-MODEL-ROUTING-MVP-0007A.

Loads a static registry config and enforces:
- mutation_adapters_enabled is always False at runtime for this packet era
- no adapter may report enabled_for_mutation=True
- active mutation adapter IDs are always empty

Pure: no network, no shell, no MCP, no Dopetask, no live writes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

from dopemux.dcp.input_adapters import active_trusted_adapters as _capability_active

_DEFAULT_REGISTRY_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "dcp" / "trusted_input_adapters.json"
)


class RegistryError(ValueError):
    """Fail-closed registry validation error."""


@dataclass(frozen=True)
class AdapterRecord:
    adapter_id: str
    enabled_for_mutation: bool
    derives_only: bool
    notes: str


@dataclass(frozen=True)
class TrustedAdapterRegistry:
    schema_version: str
    mutation_adapters_enabled: bool
    adapters: tuple[AdapterRecord, ...]
    source_path: str

    def active_mutation_adapter_ids(self) -> list[str]:
        """IDs authorized for mutation. Always empty under 0007A policy."""
        if self.mutation_adapters_enabled:
            # Hard stop even if config is tampered in memory.
            raise RegistryError("mutation_adapters_enabled must remain false")
        enabled = [a.adapter_id for a in self.adapters if a.enabled_for_mutation]
        if enabled:
            raise RegistryError(
                f"adapters enabled_for_mutation not allowed: {enabled}"
            )
        # Cross-check capability module: no live adapters.
        if _capability_active():
            raise RegistryError(
                "input_adapters.active_trusted_adapters is non-empty; refuse"
            )
        return []

    def get(self, adapter_id: str) -> Optional[AdapterRecord]:
        for a in self.adapters:
            if a.adapter_id == adapter_id:
                return a
        return None


def _validate_payload(data: Mapping[str, Any]) -> None:
    if data.get("mutation_adapters_enabled") is not False:
        raise RegistryError("mutation_adapters_enabled must be false")
    adapters = data.get("adapters")
    if not isinstance(adapters, list):
        raise RegistryError("adapters must be a list")
    for item in adapters:
        if not isinstance(item, Mapping):
            raise RegistryError("adapter entries must be objects")
        if item.get("enabled_for_mutation") is not False:
            raise RegistryError(
                f"adapter {item.get('adapter_id')!r} enabled_for_mutation must be false"
            )
        if item.get("derives_only") is not True:
            raise RegistryError(
                f"adapter {item.get('adapter_id')!r} derives_only must be true"
            )
        if not str(item.get("adapter_id") or "").strip():
            raise RegistryError("adapter_id must be non-empty")


def load_registry(path: Optional[Path] = None) -> TrustedAdapterRegistry:
    """Load and fail-closed validate the static registry file."""
    reg_path = Path(path) if path is not None else _DEFAULT_REGISTRY_PATH
    raw = json.loads(reg_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RegistryError("registry root must be an object")
    _validate_payload(raw)
    records = tuple(
        AdapterRecord(
            adapter_id=str(item["adapter_id"]),
            enabled_for_mutation=False,
            derives_only=True,
            notes=str(item.get("notes") or ""),
        )
        for item in raw["adapters"]
    )
    return TrustedAdapterRegistry(
        schema_version=str(raw.get("schema_version") or "UNKNOWN"),
        mutation_adapters_enabled=False,
        adapters=records,
        source_path=str(reg_path),
    )


def listed_adapter_ids(registry: Optional[TrustedAdapterRegistry] = None) -> list[str]:
    reg = registry or load_registry()
    return [a.adapter_id for a in reg.adapters]


def assert_no_mutation_adapters(registry: Optional[TrustedAdapterRegistry] = None) -> None:
    reg = registry or load_registry()
    ids = reg.active_mutation_adapter_ids()
    if ids:
        raise RegistryError(f"unexpected active mutation adapters: {ids}")


__all__ = [
    "AdapterRecord",
    "RegistryError",
    "TrustedAdapterRegistry",
    "load_registry",
    "listed_adapter_ids",
    "assert_no_mutation_adapters",
]
