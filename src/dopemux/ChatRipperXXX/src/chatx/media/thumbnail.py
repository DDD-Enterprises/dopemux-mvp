"""Thumbnail generation utilities."""

from pathlib import Path

from PIL import Image, ImageOps


def generate_thumbnail(src: Path, dest: Path, size: int = 256) -> None:
    """Generate an oriented JPEG thumbnail.

    Args:
        src: Source image path.
        dest: Destination thumbnail path.
        size: Maximum dimension in pixels (default 256).
    """
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as img:
        # Apply orientation from EXIF and resize preserving aspect ratio
        img = ImageOps.exif_transpose(img)
        img.thumbnail((size, size))
        img.save(dest, format="JPEG")
