"""EXIF parsing utilities."""

from typing import Any, Dict

from PIL import Image, ExifTags

try:  # pragma: no cover - optional dependency
    import pillow_heif

    pillow_heif.register_heif_opener()
except Exception:  # pragma: no cover - pillow-heif may be unavailable
    pass


def read_exif(path: str) -> Dict[str, Any]:
    """Return basic image metadata for *path*.

    Extracts width, height and available EXIF tags without
    performing any transcoding.
    """

    with Image.open(path) as img:
        width, height = img.size
        data: Dict[str, Any] = {"width": width, "height": height}
        exif: Dict[str, Any] = {}
        try:
            raw = img.getexif()
            for tag_id, value in raw.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                exif[tag] = value
        except Exception:  # pragma: no cover - EXIF may be absent
            pass
        data["exif"] = exif
    return data

