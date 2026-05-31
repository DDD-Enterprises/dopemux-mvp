"""Content-free operator identity resolution for local ADHD engine state."""

from __future__ import annotations

import os
import uuid
from pathlib import Path


_OVERRIDE_ENV_KEYS = ("DOPEMUX_ADHD_USER_ID", "ADHD_OPERATOR_USER_ID")
_DEFAULT_ID_PATH = Path("~/.dopemux/operator_id").expanduser()


def _validate_content_free_operator_id(value: str, *, source: str) -> str:
    operator_id = value.strip()
    if not operator_id:
        raise ValueError(f"ADHD operator identity from {source} is empty")
    if "/" in operator_id or "\\" in operator_id or operator_id in {".", ".."}:
        raise ValueError(
            f"ADHD operator identity from {source} must be content-free, not path-like"
        )
    if len(operator_id) > 128:
        raise ValueError(f"ADHD operator identity from {source} is too long")
    return operator_id


def _configured_override() -> str | None:
    for key in _OVERRIDE_ENV_KEYS:
        raw_value = os.getenv(key)
        if raw_value is not None:
            return _validate_content_free_operator_id(raw_value, source=key)
    return None


def _default_identity_path() -> Path:
    return Path(os.getenv("ADHD_OPERATOR_ID_PATH", str(_DEFAULT_ID_PATH))).expanduser()


def resolve_operator_user_id(identity_path: str | os.PathLike[str] | None = None) -> str:
    """Return the local operator id without deriving it from machine/user content.

    The normal path is a persisted random UUID stored at ``~/.dopemux/operator_id``.
    Environment overrides are intentionally explicit and never persisted.
    """

    override = _configured_override()
    if override is not None:
        return override

    path = (
        Path(identity_path).expanduser()
        if identity_path is not None
        else _default_identity_path()
    )
    if path.exists():
        return _validate_content_free_operator_id(
            path.read_text(encoding="utf-8"),
            source=str(path),
        )

    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    generated = str(uuid.uuid4())
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(path, flags, 0o600)
    except FileExistsError:
        return _validate_content_free_operator_id(
            path.read_text(encoding="utf-8"),
            source=str(path),
        )

    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(f"{generated}\n")
    os.chmod(path, 0o600)
    return generated
