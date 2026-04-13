from __future__ import annotations

from dataclasses import dataclass

from ..policies.loader import load_policy_pack


@dataclass(frozen=True)
class ArchetypePolicy:
    policy_id: str
    policy_version: str
    archetype_id: str
    dimensions: tuple[str, ...]
    weights: dict[str, float]
    threshold: float
    caveats: tuple[str, ...] = ()


_PACK = load_policy_pack("archetype_scoring_v1.json")
POLICIES: dict[str, ArchetypePolicy] = {
    str(item["archetype_id"]): ArchetypePolicy(
        policy_id=str(item["policy_id"]),
        policy_version=str(item["policy_version"]),
        archetype_id=str(item["archetype_id"]),
        dimensions=tuple(str(value) for value in item["dimensions"]),
        weights={str(key): float(value) for key, value in dict(item["weights"]).items()},
        threshold=float(item["threshold"]),
        caveats=tuple(str(value) for value in item.get("caveats", [])),
    )
    for item in _PACK["policies"]
}


def policy_for_archetype(archetype_id: str) -> ArchetypePolicy:
    if archetype_id not in POLICIES:
        raise ValueError(f"unsupported archetype policy for {archetype_id}")
    return POLICIES[archetype_id]
