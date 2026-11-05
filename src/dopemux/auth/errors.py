"""Typed errors for ``dopemux.auth``. No message here ever carries a token."""

from __future__ import annotations


class AuthError(Exception):
    """Base class for every ``dopemux.auth`` failure."""


class InvalidPrincipalError(AuthError, ValueError):
    """A principal does not match ``(runner|internal):<name>``."""


class KeychainError(AuthError):
    """The macOS keychain could not be read or written (hard failure, no retry)."""


class TokenNotFoundError(KeychainError):
    """The keychain has no item for the principal."""


class HashFileError(AuthError):
    """The shared hash file exists but cannot be trusted or written."""
