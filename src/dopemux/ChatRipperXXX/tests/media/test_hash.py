"""Tests for media.hash utilities."""

import hashlib
from pathlib import Path

from chatx.media.hash import sha256_stream


def test_sha256_stream(tmp_path: Path) -> None:
    data = b"sexy hash"
    f = tmp_path / "blob.bin"
    f.write_bytes(data)
    assert sha256_stream(f) == hashlib.sha256(data).hexdigest()
