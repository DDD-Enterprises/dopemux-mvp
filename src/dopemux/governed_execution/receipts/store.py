"""Append-only, content-addressed evidence store.

Every entry is addressed by the sha256 hex digest of its own canonical bytes.
Writing bytes to an address that already holds different bytes raises
``ImmutabilityViolation``. There is no update or delete API: an
``EvidenceStore`` exposes only ``put``, ``get`` and ``ref``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

_ADDRESS_PREFIX_LEN = 2


class ImmutabilityViolation(Exception):
    """Raised when ``put`` would overwrite an existing address with different bytes."""


@dataclass(frozen=True)
class EvidenceRef:
    """A pointer to one entry in an ``EvidenceStore``."""

    path: str
    sha256: str


@dataclass(frozen=True)
class ValidationRef:
    """A referential pointer to a SliceValidation, CandidateValidation or
    Review record.

    These three record kinds have no schema file under
    ``schemas/governed_execution/`` and are never passed through
    ``validate_receipt``; they are modelled purely as this referential shape
    so a ``FreezeReceipt`` can cite them by content address without W04
    authoring or interpreting their content.
    """

    kind: str
    path: str
    sha256: str
    status: str

    def as_evidence_ref(self) -> EvidenceRef:
        """Return the ``{path, sha256}`` projection used inside receipts."""
        return EvidenceRef(path=self.path, sha256=self.sha256)


class EvidenceStore:
    """Append-only content-addressed store rooted at ``root``.

    Layout: ``root/<first-2-hex-chars-of-address>/<address>``. No delete or
    update method exists on this class.
    """

    def __init__(self, root: Path) -> None:
        self._root = root

    def _address_path(self, address: str) -> Path:
        return self._root / address[:_ADDRESS_PREFIX_LEN] / address

    def put(self, data: bytes) -> str:
        """Store ``data``, returning its content address (sha256 hex digest).

        Re-putting the same bytes at the address it already hashes to is a
        no-op that returns the same address. Because the address is a
        content hash, a caller can only observe an address collision with
        different bytes via a bug (e.g. a forged address); that case raises
        ``ImmutabilityViolation``.
        """
        address = hashlib.sha256(data).hexdigest()
        path = self._address_path(address)
        if path.exists():
            existing = path.read_bytes()
            if existing != data:
                raise ImmutabilityViolation(address)
            return address
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return address

    def get(self, address: str) -> bytes:
        """Return the bytes stored at ``address``."""
        return self._address_path(address).read_bytes()

    def ref(self, address: str) -> EvidenceRef:
        """Return an ``EvidenceRef`` for ``address``."""
        path = self._address_path(address)
        return EvidenceRef(path=str(path.relative_to(self._root)), sha256=address)
