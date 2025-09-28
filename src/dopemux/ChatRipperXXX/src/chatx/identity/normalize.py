"""Identity normalization and pseudonymization utilities.

Provides deterministic, pseudonymous identifiers using HMAC-SHA256 over a
normalized input string with a local secret salt. The salt is stored locally
and never included in artifacts.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import string
from pathlib import Path
from typing import Tuple


DEFAULT_SALT_PATHS = [
    Path(os.environ.get("CHATX_SALT_FILE", "")) if os.environ.get("CHATX_SALT_FILE") else None,
    Path.home() / ".config" / "chatx" / "salt.key",
    Path.home() / ".chatx_salt",
]


def _normalize_text(text: str) -> str:
    """Normalize a handle/user text to a canonical lowercased form.

    - Trim whitespace
    - Lowercase
    - For phone numbers: keep digits with leading '+' if present
    - For emails/usernames: collapse spaces
    """
    t = (text or "").strip().lower()
    if not t:
        return "unknown"
    # Phone-like: digits/spaces/()+- allowed → keep digits; preserve leading +
    digits = "".join(ch for ch in t if ch.isdigit())
    if t.startswith("+") and digits:
        return "+" + digits
    if digits and len(digits) >= 7 and any(ch in t for ch in "+()- "):
        return digits
    # Otherwise email/username: collapse inner whitespace
    return " ".join(t.split())


def pseudonymize(text: str, salt: bytes, prefix: str = "pid_") -> str:
    """Return a deterministic pseudonymous token for the input text.

    Uses HMAC-SHA256(salt, normalized_text) and returns a short hex token.
    """
    normalized = _normalize_text(text)
    mac = hmac.new(salt, normalized.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{prefix}{mac[:32]}"  # 128-bit hex (16 bytes) is plenty for IDs


def ensure_local_salt(path: Path) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        key = secrets.token_bytes(32)
        with open(path, "wb") as f:
            f.write(key)
        return key
    return path.read_bytes()


def load_local_salt() -> Tuple[bytes, Path]:
    """Load or create a local salt file at a standard location.

    Honors CHATX_SALT_FILE if set; else uses ~/.config/chatx/salt.key, then ~/.chatx_salt.
    Returns (salt_bytes, path).
    """
    for p in DEFAULT_SALT_PATHS:
        if p is None:
            continue
        try:
            if p.exists():
                return (p.read_bytes(), p)
        except Exception:
            continue
    # Create at preferred location
    create_path = DEFAULT_SALT_PATHS[1] or (Path.home() / ".chatx_salt")
    return (ensure_local_salt(create_path), create_path)


def normalize_sender(text: str, salt: bytes | None = None) -> dict:
    """Return sender_display and pseudonymous sender_id for a raw handle/name.

    If salt is None, loads/creates a local salt file.
    """
    display = text or "Unknown"
    if salt is None:
        salt, _ = load_local_salt()
    token = pseudonymize(display, salt)
    return {"sender_display": display, "sender_id": token}

