"""Runner capability registry — DMX-DCP-MODEL-ROUTING-MVP-0009.

Static, non-authoritative inventory of runner CLIs with every invocation
permission forced false.

Pure load/validate. Does not execute models or runners.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional

_DEFAULT_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "dcp" / "runner_capabilities.json"
)


class CapabilityRegistryError(ValueError):
    """Fail-closed capability registry error."""


@dataclass(frozen=True)
class RunnerCapability:
    runner_id: str
    installed: bool
    resolved_path: Optional[str]
    version_text: Optional[str]
    invocation_authorized: bool
    mutation_authorized: bool
    paid_inference_authorized: bool
    notes: str


@dataclass(frozen=True)
class RunnerCapabilityRegistry:
    schema_version: str
    global_invocation_authorized: bool
    global_mutation_authorized: bool
    global_paid_inference_authorized: bool
    runners: tuple[RunnerCapability, ...]
    source_path: str

    def authorized_runners(self) -> list[str]:
        if self.global_invocation_authorized:
            raise CapabilityRegistryError("global_invocation_authorized must be false")
        bad = [r.runner_id for r in self.runners if r.invocation_authorized]
        if bad:
            raise CapabilityRegistryError(
                f"runners with invocation_authorized true forbidden: {bad}"
            )
        return []


def _validate(data: Mapping[str, Any]) -> None:
    for key in (
        "global_invocation_authorized",
        "global_mutation_authorized",
        "global_paid_inference_authorized",
    ):
        if data.get(key) is not False:
            raise CapabilityRegistryError(f"{key} must be false")
    runners = data.get("runners")
    if not isinstance(runners, list):
        raise CapabilityRegistryError("runners must be a list")
    for item in runners:
        if not isinstance(item, Mapping):
            raise CapabilityRegistryError("runner entries must be objects")
        for k in (
            "invocation_authorized",
            "mutation_authorized",
            "paid_inference_authorized",
        ):
            if item.get(k) is not False:
                raise CapabilityRegistryError(
                    f"runner {item.get('runner_id')!r} {k} must be false"
                )


def load_runner_capabilities(path: Optional[Path] = None) -> RunnerCapabilityRegistry:
    reg_path = Path(path) if path is not None else _DEFAULT_PATH
    raw = json.loads(reg_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise CapabilityRegistryError("root must be object")
    _validate(raw)
    runners = tuple(
        RunnerCapability(
            runner_id=str(item["runner_id"]),
            installed=bool(item.get("installed", False)),
            resolved_path=item.get("resolved_path"),
            version_text=item.get("version_text"),
            invocation_authorized=False,
            mutation_authorized=False,
            paid_inference_authorized=False,
            notes=str(item.get("notes") or ""),
        )
        for item in raw["runners"]
    )
    return RunnerCapabilityRegistry(
        schema_version=str(raw.get("schema_version") or "UNKNOWN"),
        global_invocation_authorized=False,
        global_mutation_authorized=False,
        global_paid_inference_authorized=False,
        runners=runners,
        source_path=str(reg_path),
    )


def assert_no_invocation_authorized(
    registry: Optional[RunnerCapabilityRegistry] = None,
) -> None:
    reg = registry or load_runner_capabilities()
    if reg.authorized_runners():
        raise CapabilityRegistryError("unexpected authorized runners")


__all__ = [
    "CapabilityRegistryError",
    "RunnerCapability",
    "RunnerCapabilityRegistry",
    "load_runner_capabilities",
    "assert_no_invocation_authorized",
]
