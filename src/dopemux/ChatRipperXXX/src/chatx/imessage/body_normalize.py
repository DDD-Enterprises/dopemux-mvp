from __future__ import annotations

import plistlib


def _clean_text(s: str) -> str:
    # Remove control chars, collapse whitespace
    cleaned = ''.join(ch if ch.isprintable() else ' ' for ch in s)
    return ' '.join(cleaned.split())


def normalize_attributed_body(data: bytes) -> str | None:
    """Normalize iMessage attributedBody bytes into a readable string.

    Tries binary plist parse first, then UTF-8 decode fallback. Returns None
    if no plausible text is found.
    """
    if not data:
        return None

    try:
        if data.startswith(b"bplist00"):
            try:
                obj = plistlib.loads(data)
                # Heuristic: stringify and clean
                return _clean_text(str(obj))
            except Exception:
                pass
        # Fallback: best-effort UTF-8
        txt = data.decode("utf-8", errors="ignore")
        txt = _clean_text(txt)
        return txt or None
    except Exception:
        return None

