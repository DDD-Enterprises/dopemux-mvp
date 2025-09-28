"""Tests for media.exif."""

from pathlib import Path

from chatx.media.exif import read_exif
from tests.fixtures.tiny_heic import tiny_heic_file


def test_read_exif_heic(tmp_path: Path) -> None:
    """HEIC dimensions should be readable without transcoding."""
    path = tiny_heic_file(tmp_path)
    meta = read_exif(str(path))
    assert meta["width"] == 2
    assert meta["height"] == 2
