"""Tests for media.sniff."""

from pathlib import Path

from chatx.media.sniff import sniff_mime
from tests.fixtures.tiny_heic import tiny_heic_file


def test_sniff_heic(tmp_path: Path) -> None:
    """HEIC files should be detected via magic."""
    path = tiny_heic_file(tmp_path)
    mime, uti = sniff_mime(str(path))
    assert mime == "image/heic"
    assert uti == "public.heic"
