"""Hashing utilities."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_stream(path: str | Path, *, chunk_size: int = 65536) -> str:
    """Return the SHA-256 hex digest for *path*.

    The file is read in chunks to avoid loading the entire content into memory.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()
