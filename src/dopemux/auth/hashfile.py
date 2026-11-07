"""The shared token-hash file and the date-only metadata sidecar.

``~/.config/dopemux/auth/memory-token-hashes.json`` is read by dope-memory
(W01) and ConPort (W02): one JSON object ``{"<lowercase hex sha256 of the
UTF-8 token>": "<principal>"}``. Directory mode 0700, file mode 0600, written
atomically (temp file in the same directory, fsync, rename).

``memory-token-meta.json`` beside it maps principal -> ``{"created", "rotated"}``
(UTC timestamps). It holds no tokens and no hashes; ``dopemux auth list`` reads it.

Atomic writes keep readers safe. Writers also need ``exclusive_lock``: each one
reads, changes and rewrites the whole file, so an overlapping run would otherwise
put back what the other removed.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from .errors import HashFileError
from .tokens import PRINCIPAL_RE

__all__ = [
    "HASH_FILE_NAME",
    "LOCK_FILE_NAME",
    "LOCK_TIMEOUT_SECONDS",
    "META_FILE_NAME",
    "HashFileError",
    "auth_dir",
    "exclusive_lock",
    "hash_file_path",
    "meta_file_path",
    "load_hashes",
    "write_hashes",
    "load_meta",
    "write_meta",
]

HASH_FILE_NAME = "memory-token-hashes.json"
LOCK_FILE_NAME = "memory-token-hashes.lock"
META_FILE_NAME = "memory-token-meta.json"

# Longer than the slowest holder: a keychain write plus its read-back, 10 s each.
LOCK_TIMEOUT_SECONDS = 30.0


def auth_dir() -> Path:
    return Path.home() / ".config" / "dopemux" / "auth"


def hash_file_path() -> Path:
    return auth_dir() / HASH_FILE_NAME


def meta_file_path() -> Path:
    return auth_dir() / META_FILE_NAME


def _ensure_private_dir(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    os.chmod(directory, 0o700)


@contextmanager
def exclusive_lock() -> Generator[None, None, None]:
    """Hold the writers' lock; load, change and write only inside this block.

    Covers the hash file, the sidecar and the keychain item, so a command's
    keychain call cannot let another command's change be overwritten. Raises
    ``HashFileError`` rather than proceed unlocked. Readers do not take it.
    """
    # Imported here so token reads, which the stdio bridge uses, stay stdlib-only.
    from filelock import FileLock, Timeout

    directory = auth_dir()
    _ensure_private_dir(directory)
    lock = FileLock(directory / LOCK_FILE_NAME, mode=0o600)
    try:
        lock.acquire(timeout=LOCK_TIMEOUT_SECONDS)
    except Timeout:
        raise HashFileError(
            "another `dopemux auth` command is still running; nothing changed, "
            "retry when it finishes"
        ) from None
    try:
        yield
    finally:
        lock.release()


def _write_json_atomic(path: Path, payload: Any) -> None:
    directory = path.parent
    _ensure_private_dir(directory)
    fd, tmp_name = tempfile.mkstemp(dir=directory, prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            os.fchmod(fh.fileno(), 0o600)
            json.dump(payload, fh, indent=2, sort_keys=True)
            fh.write("\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except FileNotFoundError:
            pass
        raise
    try:
        dir_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except OSError:
        pass


def load_hashes() -> dict[str, str]:
    """Return the hash -> principal mapping; ``{}`` if the file is absent.

    An unreadable, non-object or malformed file raises ``HashFileError`` so a
    write never silently discards entries.
    """
    path = hash_file_path()
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise HashFileError(f"cannot read {path} ({type(exc).__name__})") from None
    try:
        data = json.loads(raw)
    except ValueError:
        raise HashFileError(f"{path} is not valid JSON; fix or remove it first") from None
    if not isinstance(data, dict):
        raise HashFileError(f"{path} is not a JSON object; fix or remove it first")
    for digest, principal in data.items():
        if not (
            isinstance(digest, str)
            and len(digest) == 64
            and all(c in "0123456789abcdef" for c in digest)
            and isinstance(principal, str)
            and PRINCIPAL_RE.match(principal)
        ):
            raise HashFileError(f"{path} has a malformed entry; fix or remove it first")
    return dict(data)


def write_hashes(hashes: dict[str, str]) -> None:
    _write_json_atomic(hash_file_path(), hashes)


def load_meta() -> dict[str, dict[str, Any]]:
    """Return principal -> metadata; unreadable metadata reads as empty (dates only)."""
    try:
        data = json.loads(meta_file_path().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(data, dict):
        return {}
    return {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, dict)}


def write_meta(meta: dict[str, dict[str, Any]]) -> None:
    _write_json_atomic(meta_file_path(), meta)
