from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GovernancePacketRef:
    recommendation_id: str
    packet_path: str
    required_action: str
