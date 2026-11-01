"""The only code that reads or writes the macOS keychain for runner tokens.

Decision (proof/MACRO-DMX-RUNNER-MEMORY-2A-001-R2/review_bundle/KEYCHAIN_ACL_RESULT.md):
- Items use the DEFAULT ACL: created by ``/usr/bin/security add-generic-password``
  with no ``-T`` and no ``-A``.
- Reads run ``/usr/bin/security find-generic-password -s dopemux-mcp -a <principal> -w``
  in a child process with stdin closed and a timeout. Any nonzero exit, timeout
  or empty output is a hard failure; the error names the likely cause. Nothing
  is retried, so a keychain prompt is never waited on.
- The token never goes on a command line (``ps`` would show it). Writes feed the
  command to ``security -i`` on stdin.
- Same-user processes can run the same read; that is a stated non-protection.

Nothing in this module logs or formats a token into a message.
"""

from __future__ import annotations

import hmac
import logging
import re
import subprocess

from .errors import KeychainError, TokenNotFoundError
from .tokens import validate_principal

logger = logging.getLogger(__name__)

SERVICE = "dopemux-mcp"
SECURITY_BIN = "/usr/bin/security"
TIMEOUT_SECONDS = 10.0

_ITEM_NOT_FOUND_EXIT = 44  # observed macOS security(1) exit for "item not found"
_WRITABLE_TOKEN_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_-]{15,511}$")

_HINT = (
    "The login keychain may be locked, or there is no login session "
    "(for example over SSH or from a launchd job). Unlock it in a logged-in "
    "terminal (`security unlock-keychain ~/Library/Keychains/login.keychain-db`) "
    "and retry."
)


def _run(args: list[str], stdin_bytes: bytes | None = None) -> subprocess.CompletedProcess:
    try:
        if stdin_bytes is None:
            return subprocess.run(
                [SECURITY_BIN, *args],
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=TIMEOUT_SECONDS,
                check=False,
            )
        return subprocess.run(
            [SECURITY_BIN, *args],
            input=stdin_bytes,
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise KeychainError(
            f"keychain call timed out after {TIMEOUT_SECONDS:g}s (no retry). {_HINT}"
        ) from None
    except OSError as exc:
        raise KeychainError(
            f"cannot run {SECURITY_BIN} ({type(exc).__name__}); the keychain helper "
            "needs macOS."
        ) from None


def get_token(principal: str) -> str:
    """Return the token stored for ``principal``.

    Raises ``InvalidPrincipalError`` for a malformed principal,
    ``TokenNotFoundError`` when the keychain has no item, and ``KeychainError``
    for every other failure (locked keychain, no login session, timeout, empty
    output). Never retries.
    """
    validate_principal(principal)
    proc = _run(["find-generic-password", "-s", SERVICE, "-a", principal, "-w"])
    if proc.returncode == _ITEM_NOT_FOUND_EXIT:
        raise TokenNotFoundError(
            f"no {SERVICE} keychain item for {principal}; "
            f"run `dopemux auth issue {principal} --apply`"
        )
    if proc.returncode != 0:
        logger.warning("keychain read failed for %s (exit %s)", principal, proc.returncode)
        raise KeychainError(
            f"keychain read for {principal} failed (exit {proc.returncode}). {_HINT}"
        )
    token = proc.stdout.decode("utf-8", errors="replace").strip()
    if not token:
        raise KeychainError(f"keychain read for {principal} returned no value. {_HINT}")
    return token


def store_token(principal: str, token: str) -> None:
    """Create or update the keychain item, then verify it by reading it back.

    The token is sent on ``security -i`` stdin, never in argv. ``security -i``
    can exit 0 after a failed command, so the read-back is part of success.
    """
    validate_principal(principal)
    if not _WRITABLE_TOKEN_RE.match(token):
        raise ValueError("token is not a base64url string produced by generate_token()")
    line = f"add-generic-password -U -s {SERVICE} -a {principal} -w {token}\n"
    proc = _run(["-i"], stdin_bytes=line.encode("utf-8"))
    if proc.returncode != 0:
        raise KeychainError(
            f"keychain write for {principal} failed (exit {proc.returncode}). {_HINT}"
        )
    stored = get_token(principal)
    if not hmac.compare_digest(stored.encode("utf-8"), token.encode("utf-8")):
        raise KeychainError(
            f"keychain write for {principal} did not take effect (read-back differs)"
        )
    logger.debug("stored keychain item for %s", principal)


def delete_token(principal: str) -> bool:
    """Delete the item. Return True if deleted, False if it was already absent."""
    validate_principal(principal)
    proc = _run(["delete-generic-password", "-s", SERVICE, "-a", principal])
    if proc.returncode == 0:
        return True
    if proc.returncode == _ITEM_NOT_FOUND_EXIT:
        return False
    raise KeychainError(
        f"keychain delete for {principal} failed (exit {proc.returncode}). {_HINT}"
    )
