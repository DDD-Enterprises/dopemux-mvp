from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Protocol


@dataclass(frozen=True)
class ProviderEvent:
    provider: str
    delivery_id: str
    event_id: str
    event_type: str
    payload: Dict[str, object]
    headers: Dict[str, str]
    external_id: str = ""
    run_id: str = ""
    phase: str = ""
    step_id: str = ""
    partition_id: str = ""
    attempt: Optional[int] = None


class WebhookAdapter(Protocol):
    provider: str

    def verify_and_normalize(self, raw_body: bytes, headers: Dict[str, str]) -> ProviderEvent:
        raise NotImplementedError
