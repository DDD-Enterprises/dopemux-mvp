"""MIME sniffing utilities."""

from pathlib import Path
from typing import Tuple

# Known HEIF/HEIC brand identifiers within the ISO BMFF header
HEIF_BRANDS = {
    b"heic",
    b"heix",
    b"hevc",
    b"hevx",
    b"heif",
    b"heis",
    b"heim",
    b"hevm",
    b"mif1",
    b"msf1",
}

# Simple extension fallback mapping when magic sniffing fails
EXT_MAP: dict[str, Tuple[str, str]] = {
    ".jpg": ("image/jpeg", "public.jpeg"),
    ".jpeg": ("image/jpeg", "public.jpeg"),
    ".png": ("image/png", "public.png"),
    ".gif": ("image/gif", "public.gif"),
    ".webp": ("image/webp", "public.webp"),
    ".heic": ("image/heic", "public.heic"),
    ".heif": ("image/heif", "public.heif"),
}


def sniff_mime(path: str) -> Tuple[str | None, str | None]:
    """Return ``(mime_type, uti)`` detected from *path*.

    Detection is performed primarily via magic numbers. If no known
    signature is found, the function falls back to the file extension.
    Returns ``(None, None)`` when the type cannot be determined.
    """

    p = Path(path)
    with open(p, "rb") as f:
        header = f.read(12)

    # JPEG
    if header.startswith(b"\xFF\xD8\xFF"):
        return "image/jpeg", "public.jpeg"

    # PNG
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", "public.png"

    # GIF
    if header[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif", "public.gif"

    # WebP (RIFF container with WEBP signature)
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "image/webp", "public.webp"

    # HEIF/HEIC: ISO BMFF with ftyp brand
    if len(header) >= 12 and header[4:8] == b"ftyp" and header[8:12] in HEIF_BRANDS:
        brand = header[8:12]
        if brand in {b"heic", b"heix", b"hevc", b"hevx"}:
            return "image/heic", "public.heic"
        return "image/heif", "public.heif"

    # Fallback: extension mapping
    return EXT_MAP.get(p.suffix.lower(), (None, None))

