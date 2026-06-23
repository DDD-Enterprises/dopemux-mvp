"""Fail-closed LIVE_WRITE_READY assertion authentication.

Production activation requires an injected verifier with a trusted issuer.
Without a verifier, unsigned or self-asserted READY objects cannot reach a
registered writer when ``execute is True``.
"""

from __future__ import annotations

from typing import Protocol


class ReadyAssertionVerifier(Protocol):
    """Verify assertion authenticity before writer delegation."""

    def verify(
        self, assertion: dict, *, operation: dict
    ) -> tuple[bool, list[str]]:
        """Return (permitted, reasons). Reasons are empty when permitted."""


class NoTrustedIssuerVerifier:
    """Default fail-closed verifier — no production issuer is configured."""

    def verify(
        self, assertion: dict, *, operation: dict
    ) -> tuple[bool, list[str]]:
        _ = (assertion, operation)
        return (False, ["ASSERTION_ISSUER_UNTRUSTED"])


def requires_assertion_verification(
    *,
    execute: bool,
    writer_registry: dict | None,
) -> bool:
    """True when live execution with a registered writer demands verifier PASS."""
    if execute is not True:
        return False
    registry = writer_registry or {}
    return bool(registry)