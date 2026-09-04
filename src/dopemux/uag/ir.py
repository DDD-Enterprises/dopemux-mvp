"""UAG three-lane intermediate representation (IR).

The semantic core represents three disjoint lanes:

1. Canonical public core — the provider-neutral shared representation (public
   text and/or typed public values) that downstream systems may rely on.
2. Typed protocol-family envelopes — opaque per-family envelopes that only the
   matching family adapter may interpret.
3. Opaque private-state capsule metadata — digest references only. The core
   never interprets private-state bytes.

The lanes are kept separate; the core does not merge them. This mirrors the
C0-R2 requested output contract classes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dopemux.uag.enums import OutputContractClass
from dopemux.uag.primitives import DigestRef


@dataclass(frozen=True)
class PublicCore:
    """Canonical public lane: provider-neutral, deterministic representation."""

    public_text: str | None = None
    public_values: tuple[tuple[str, Any], ...] = ()

    def canonical(self) -> dict[str, Any]:
        return {
            "public_text": self.public_text,
            "public_values": sorted(self.public_values, key=lambda kv: kv[0]),
        }


@dataclass(frozen=True)
class FamilyEnvelope:
    """Typed protocol-family envelope lane.

    ``payload`` is opaque to the core and only meaningful to the matching family
    adapter. The core records it but never interprets it.
    """

    family_id: str
    payload: Any
    media_type: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.family_id, str) or not self.family_id:
            raise ValueError("family_id must be a non-empty string")


@dataclass(frozen=True)
class PrivateStateCapsuleRef:
    """Opaque private-state capsule lane.

    Holds only a digest reference. The referenced private-state bytes are never
    read or interpreted by the semantic core. Replay is process-lifetime only.
    """

    ref: DigestRef


@dataclass(frozen=True)
class RequestedOutputContract:
    """Requested output contract, selecting which IR lanes are expected."""

    output_class: OutputContractClass
    notes: str | None = None
