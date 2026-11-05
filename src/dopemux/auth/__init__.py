"""Runner/internal bearer tokens for the memory servers (Wave 2A R2, W03).

Public API (import from here):

- ``get_token(principal) -> str``: the token for a principal, read from the
  macOS keychain (service ``dopemux-mcp``). Raises ``TokenNotFoundError`` (no
  item), ``KeychainError`` (locked keychain, no login session, timeout, empty
  output) or ``InvalidPrincipalError``. Never retries, never prints a token.
  W04's bridge, W02's proxy fallback and W05's internal callers use this.
- ``store_token`` / ``delete_token``: keychain writes (used by ``dopemux auth``).
- ``generate_token()``, ``hash_token(token)``, ``validate_principal(p)``,
  ``is_known_principal(p)``, ``KNOWN_PRINCIPALS``.
- ``hashfile``: the shared ``memory-token-hashes.json`` and date-only sidecar.
"""

from . import hashfile
from .errors import (
    AuthError,
    HashFileError,
    InvalidPrincipalError,
    KeychainError,
    TokenNotFoundError,
)
from .keychain import SERVICE, delete_token, get_token, store_token
from .tokens import (
    KNOWN_PRINCIPALS,
    generate_token,
    hash_token,
    is_known_principal,
    validate_principal,
)

__all__ = [
    "AuthError",
    "HashFileError",
    "InvalidPrincipalError",
    "KNOWN_PRINCIPALS",
    "KeychainError",
    "SERVICE",
    "TokenNotFoundError",
    "delete_token",
    "generate_token",
    "get_token",
    "hash_token",
    "hashfile",
    "is_known_principal",
    "store_token",
    "validate_principal",
]
