"""Principals, token generation and hashing (pure functions, no I/O)."""

from __future__ import annotations

import base64
import hashlib
import re
import secrets

from .errors import InvalidPrincipalError

# Same pattern the memory servers enforce when they load the hash file
# (services/working-memory-assistant/auth_identity.py:69,
# docker/mcp-servers-source/conport/auth_identity.py). `\Z`, not `$`: `$` also
# matches before a trailing newline, and a principal goes into a `security -i` line.
PRINCIPAL_RE = re.compile(r"^(runner|internal):[a-z0-9][a-z0-9_.-]{0,63}\Z")

# Design 5.1 (Wave 2A). Other principals matching PRINCIPAL_RE are accepted.
KNOWN_PRINCIPALS = (
    "runner:claude",
    "runner:codex",
    "internal:hooks",
    "internal:cli",
    "internal:wma",
    "internal:bridge-proxy",
    "internal:dopecon",
    "internal:adhd",
    "internal:brain",
)

TOKEN_BYTES = 32


def validate_principal(principal: str) -> str:
    """Return ``principal`` unchanged or raise ``InvalidPrincipalError``."""
    if not isinstance(principal, str) or not PRINCIPAL_RE.match(principal):
        raise InvalidPrincipalError(
            "principal must match (runner|internal):<name> with <name> in "
            "[a-z0-9][a-z0-9_.-]{0,63}"
        )
    return principal


def is_known_principal(principal: str) -> bool:
    return principal in KNOWN_PRINCIPALS


def generate_token() -> str:
    """32 random bytes as unpadded base64url.

    A token that would begin with ``-`` is redrawn so it can never be read as an
    option by ``security -i`` argument parsing.
    """
    while True:
        token = base64.urlsafe_b64encode(secrets.token_bytes(TOKEN_BYTES)).decode("ascii").rstrip("=")
        if not token.startswith("-"):
            return token


def hash_token(token: str) -> str:
    """Lowercase hex SHA-256 of the UTF-8 token (the hash-file key format)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
