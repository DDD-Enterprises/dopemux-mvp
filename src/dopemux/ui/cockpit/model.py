"""Typed seed structures for the static cockpit renderer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SnapshotState:
    data: dict[str, Any]

    @property
    def modes(self) -> list[str]:
        return list(self.data["top_level_modes"])

    @property
    def services(self) -> dict[str, Any]:
        return dict(self.data["services"])

    @property
    def rte_child_surface(self) -> dict[str, Any]:
        return dict(self.data["rte_child_surface"])

    @property
    def placeholder_modes(self) -> dict[str, Any]:
        return dict(self.data["placeholder_modes"])

    @property
    def status_rail(self) -> dict[str, str]:
        return dict(self.data["status_rail"])


def state_from_seed(seed: dict[str, Any]) -> SnapshotState:
    return SnapshotState(seed)
