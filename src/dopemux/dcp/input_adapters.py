"""Trusted-input capability boundary — DMX-DCP-MODEL-ROUTING-MVP-0007I.

This module defines an **auditable code-authority** boundary so raw or restored
routing inputs cannot confer mutation / execution eligibility.

Non-claims (hard):
- This is NOT cryptographic isolation. Python privacy is a review boundary.
- No trusted mutation adapter is enabled in this packet.
- No runner, connector, MCP, Dopetask, Task Orchestrator, network, or shell I/O.
- Capability objects cannot be reconstructed from JSON or public booleans.
- Adapter activation is deferred to a later packet (0007A registry). Until then
  ``active_trusted_adapters()`` is always empty and
  ``is_execution_eligible(...)`` is always False.

Public surface
--------------
``TrustedInputCapability``
    Opaque, non-serializable capability token. Not reconstructible from dict.

``is_execution_eligible(source, capability=None)``
    Fail-closed gate. Returns True only when a live capability was minted by
    an *active* registered adapter path. With zero active adapters (0007I),
    this is always False.

``active_trusted_adapters()``
    Always ``[]`` until 0007A enables a registry. Documents non-claim.

``refuse_serialized_trust(payload)``
    Explicit rejection of any dict/JSON that asserts trust/attestation.

``untrusted_classify_source(source)``
    Documents that a raw ``RoutingClassificationInput`` / dict is untrusted
    for execution eligibility (returns the source unchanged).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping, Optional

# ---------------------------------------------------------------------------
# Private mint token — not importable as a meaningful forge value from JSON.
# Module object identity is the authority; equality of a string is not.
# ---------------------------------------------------------------------------

_MINT_TOKEN = object()


class TrustedInputError(ValueError):
    """Raised when a trusted-input boundary operation fails closed."""


@dataclass(frozen=True)
class TrustedInputCapability:
    """In-process execution-eligibility capability.

    Construction is only valid via ``_mint_capability`` with the private
    module token. Public callers cannot mint a live capability in 0007I
    because no adapter is registered / active.

    Immutability: frozen dataclass + MappingProxyType evidence.
    Serialization: ``to_dict`` / pickle / copy-restore intentionally refuse
    or produce objects that are **not** execution-eligible.
    """

    adapter_id: str
    _mint_token: object = field(default=None, repr=False, compare=False)
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self._mint_token is not _MINT_TOKEN:
            raise TrustedInputError(
                "TrustedInputCapability cannot be constructed publicly; "
                "no active trusted adapter may mint capability in 0007I"
            )
        if not self.adapter_id or not str(self.adapter_id).strip():
            raise TrustedInputError("adapter_id must be non-empty")
        # Freeze evidence mapping so callers cannot mutate post-mint.
        object.__setattr__(self, "evidence", MappingProxyType(dict(self.evidence)))

    def to_dict(self) -> dict[str, Any]:
        """Refuse serializing a live capability as reconstitutable trust.

        Returns a **non-authoritative** diagnostic dict that cannot be fed
        back into a constructor to mint eligibility.
        """
        return {
            "capability_type": "TrustedInputCapability",
            "serializable": False,
            "execution_eligible": False,
            "adapter_id": self.adapter_id,
            "note": "serialized_trust_supported=false; restore does not mint capability",
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "TrustedInputCapability":
        """Always fail closed — deserialization cannot mint capability."""
        raise TrustedInputError(
            "TrustedInputCapability.from_dict is forbidden; "
            "serialized trust is not supported"
        )

    def __reduce__(self):  # pragma: no cover - exercised by tests via pickle
        # Pickle must not restore a live capability.
        raise TrustedInputError(
            "TrustedInputCapability cannot be pickled; fail closed"
        )


def _mint_capability(
    *,
    adapter_id: str,
    evidence: Optional[Mapping[str, Any]] = None,
    mint_token: object,
) -> TrustedInputCapability:
    """Internal mint. Requires the private module token.

    0007I keeps this unexported from active adapter paths: there is no public
    function that calls it for mutation-authorized use.
    """
    if mint_token is not _MINT_TOKEN:
        raise TrustedInputError("invalid mint token")
    return TrustedInputCapability(
        adapter_id=adapter_id,
        evidence=dict(evidence or {}),
        _mint_token=_MINT_TOKEN,
    )


# ---------------------------------------------------------------------------
# Active adapter registry — empty until 0007A
# ---------------------------------------------------------------------------

# Names only; 0007I does not register any mutation-authorized adapter.
_ACTIVE_TRUSTED_ADAPTERS: tuple[str, ...] = ()


def active_trusted_adapters() -> list[str]:
    """Return currently active trusted adapter IDs.

    OBSERVED 0007I contract: always empty. 0007A may populate a registry;
    this packet must not enable mutation adapters.
    """
    return list(_ACTIVE_TRUSTED_ADAPTERS)


def is_execution_eligible(
    source: Any,
    capability: Optional[TrustedInputCapability] = None,
) -> bool:
    """Fail-closed execution-eligibility gate for trusted-input boundary.

    Rules (0007I):
    1. No active adapters ⇒ always False (regardless of capability object).
    2. capability is None ⇒ False.
    3. capability failed private-token construction ⇒ unreachable / False.
    4. Raw RoutingClassificationInput / dict / JSON-shaped data ⇒ False.
    5. Serialized fields like attested=true cannot mint eligibility.

    This gate is additive. Existing ``RouteDecision.is_runnable()`` remains
    the historical runnability API and is intentionally **not** rewritten
    here (out of allowlist). Downstream consumers that need the new boundary
    must consult this gate explicitly.
    """
    # (1) No active adapters in 0007I.
    if not _ACTIVE_TRUSTED_ADAPTERS:
        return False

    if capability is None:
        return False

    if not isinstance(capability, TrustedInputCapability):
        return False

    # Capability must have been minted with private token (enforced at init).
    if capability._mint_token is not _MINT_TOKEN:
        return False

    if capability.adapter_id not in _ACTIVE_TRUSTED_ADAPTERS:
        return False

    # Source must not itself be a forged trust dict.
    if isinstance(source, Mapping):
        if _looks_like_serialized_trust(source):
            return False

    return True


def _looks_like_serialized_trust(payload: Mapping[str, Any]) -> bool:
    """Detect caller-asserted trust markers that must never raise eligibility."""
    trust_keys = {
        "attested",
        "trusted",
        "adapter_id",
        "trusted_adapter",
        "execution_eligible",
        "is_execution_eligible",
        "mint_token",
        "_mint_token",
        "capability",
        "trusted_input",
    }
    return any(k in payload for k in trust_keys)


def refuse_serialized_trust(payload: Any) -> None:
    """Raise if *payload* asserts serializable trust / attestation.

    Safe no-op for non-mappings without trust markers.
    """
    if not isinstance(payload, Mapping):
        return
    if _looks_like_serialized_trust(payload):
        raise TrustedInputError(
            "serialized trust/attestation fields cannot mint capability "
            f"(keys present: {sorted(set(payload) & {'attested','trusted','adapter_id','trusted_adapter','execution_eligible','is_execution_eligible','mint_token','_mint_token','capability','trusted_input'})})"
        )


def untrusted_classify_source(source: Any) -> Any:
    """Mark a classification source as untrusted for execution eligibility.

    Returns *source* unchanged. Documents the untrusted path for code review.
    Does not return a ``TrustedInputCapability``.
    """
    if isinstance(source, Mapping):
        refuse_serialized_trust(source)
    return source


def capability_from_any(value: Any) -> None:
    """Explicit API: no value may be coerced into a live capability.

    Always raises. Exists so call sites fail loudly instead of silently
    treating a dict/bool as trusted.
    """
    raise TrustedInputError(
        f"cannot coerce {type(value).__name__!r} into TrustedInputCapability; "
        "serialized_trust_supported=false and active_trusted_adapters=[]"
    )


__all__ = [
    "TrustedInputCapability",
    "TrustedInputError",
    "active_trusted_adapters",
    "is_execution_eligible",
    "refuse_serialized_trust",
    "untrusted_classify_source",
    "capability_from_any",
]
