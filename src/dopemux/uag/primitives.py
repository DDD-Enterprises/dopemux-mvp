"""UAG semantic-core primitives.

Deterministic digest handling and canonical serialization used to bind receipts
and identity records. Stdlib-only; no I/O on import.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any

_SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def is_sha256(value: object) -> bool:
    """Return True if ``value`` is a lowercase hex SHA-256 digest string."""
    return isinstance(value, str) and bool(_SHA256_RE.match(value))


def sha256_bytes(data: bytes) -> str:
    """Return the lowercase hex SHA-256 digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_text(data: str) -> str:
    """Return the lowercase hex SHA-256 digest of UTF-8 encoded text."""
    return sha256_bytes(data.encode("utf-8"))


def canonical_json(value: Any) -> str:
    """Serialize ``value`` deterministically (sorted keys, compact, UTF-8).

    Used to bind receipts. Ordering of mapping keys is normalized; list order is
    preserved because lists are ordered by meaning in this domain.
    """
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def canonical_digest(value: Any) -> str:
    """Return the canonical SHA-256 digest of ``value``."""
    return sha256_text(canonical_json(value))


@dataclass(frozen=True)
class DigestRef:
    """Exact-digest reference to a durable artifact (C0-R2 ``digestRef``).

    The referenced bytes are never interpreted by the semantic core; this is a
    binding reference only.
    """

    id: str
    sha256: str
    media_type: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.id, str) or not self.id:
            raise ValueError("DigestRef.id must be a non-empty string")
        if not is_sha256(self.sha256):
            raise ValueError("DigestRef.sha256 must be a lowercase 64-char hex digest")
