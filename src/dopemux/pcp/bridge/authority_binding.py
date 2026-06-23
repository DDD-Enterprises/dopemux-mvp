"""Authority-map binding for live-write activation.

A writer is unreachable unless ``target_surface`` and ``canonical_writer`` map
to a SOURCE entry with ``live_write_allowed=true`` and
``unknown_behavior=BLOCK_OR_ESCALATE``.
"""

from __future__ import annotations

from typing import Any, Protocol

_DERIVED_SURFACES = frozenset(
    {"ADAPTER", "PROJECTION", "MIRROR", "CACHE", "INDEX", "UNKNOWN"}
)


class AuthorityMapBinding(Protocol):
    """Authorize a live-write operation against an authority map."""

    def authorize(
        self,
        *,
        target_surface: str,
        canonical_writer: str,
        operation: dict,
    ) -> tuple[bool, list[str]]:
        """Return (permitted, reasons)."""


class FailClosedAuthorityBinding:
    """Reject all writes when no authority map is injected."""

    def authorize(
        self,
        *,
        target_surface: str,
        canonical_writer: str,
        operation: dict,
    ) -> tuple[bool, list[str]]:
        _ = (target_surface, canonical_writer, operation)
        return (False, ["AUTHORITY_MAP_ABSENT"])


def requires_authority_binding(
    *,
    execute: bool,
    writer_registry: dict | None,
) -> bool:
    if execute is not True:
        return False
    registry = writer_registry or {}
    return bool(registry)


def binding_from_entries(entries: list[dict[str, Any]]) -> AuthorityMapBinding:
    """Build an in-memory binding from authority-map entry dicts."""

    class _EntriesBinding:
        def authorize(
            self,
            *,
            target_surface: str,
            canonical_writer: str,
            operation: dict,
        ) -> tuple[bool, list[str]]:
            _ = operation
            if not target_surface or not canonical_writer:
                return (False, ["AUTHORITY_TARGET_UNKNOWN"])

            for entry in entries:
                if not isinstance(entry, dict):
                    continue
                domain = entry.get("domain", "")
                surface = entry.get("reader_or_projection_surface") or ""
                matches_surface = target_surface in {domain, surface}
                if not matches_surface:
                    continue

                surface_class = entry.get("surface_class")
                if surface_class in _DERIVED_SURFACES:
                    return (False, ["AUTHORITY_SURFACE_NOT_WRITABLE"])

                if entry.get("canonical_writer") != canonical_writer:
                    return (False, ["AUTHORITY_WRITER_MISMATCH"])

                if entry.get("live_write_allowed") is not True:
                    return (False, ["AUTHORITY_LIVE_WRITE_FORBIDDEN"])

                if entry.get("unknown_behavior") != "BLOCK_OR_ESCALATE":
                    return (False, ["AUTHORITY_UNKNOWN_BEHAVIOR"])

                if surface_class != "SOURCE":
                    return (False, ["AUTHORITY_SURFACE_NOT_SOURCE"])

                return (True, [])

            return (False, ["AUTHORITY_ENTRY_NOT_FOUND"])

    return _EntriesBinding()