"""``dopemux auth``: issue, rotate, revoke and list runner/internal memory tokens.

Tokens live only in the macOS keychain (service ``dopemux-mcp``, account =
principal). The memory servers verify SHA-256 hashes from
``~/.config/dopemux/auth/memory-token-hashes.json``. Every command that writes
prints a dry-run plan unless ``--apply`` is given. No command prints a token or
a hash; ``list`` prints principals and dates only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import click

from ..auth import (
    SERVICE,
    AuthError,
    InvalidPrincipalError,
    delete_token,
    generate_token,
    hash_token,
    hashfile,
    is_known_principal,
    store_token,
    validate_principal,
)


def _principal_param(_ctx: click.Context, _param: click.Parameter, value: str) -> str:
    try:
        return validate_principal(value)
    except InvalidPrincipalError as exc:
        raise click.BadParameter(str(exc)) from None


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fail(exc: Exception) -> click.ClickException:
    return click.ClickException(str(exc))


def _load_hashes() -> dict[str, str]:
    try:
        return hashfile.load_hashes()
    except AuthError as exc:
        raise _fail(exc) from None


def _show_plan(title: str, principal: str, steps: list[str]) -> None:
    click.echo(f"DRY RUN: {title} {principal} (nothing changed; add --apply to execute)")
    if not is_known_principal(principal):
        click.echo(f"note: {principal} is not in the known 2A principal list")
    for step in steps:
        click.echo(f"  - {step}")


def _require_unissued(principal: str, hashes: dict[str, str]) -> None:
    if principal in hashes.values():
        raise click.ClickException(
            f"{principal} already has a token; use `dopemux auth rotate {principal}`"
        )


def _require_issued(principal: str, hashes: dict[str, str]) -> None:
    if principal not in hashes.values():
        raise click.ClickException(
            f"{principal} has no token; use `dopemux auth issue {principal}`"
        )


_HASH_STEP = f"write {hashfile.HASH_FILE_NAME} atomically in ~/.config/dopemux/auth (dir 0700, file 0600)"


@click.group()
def auth() -> None:
    """Manage runner and internal tokens for the memory servers (keychain-held)."""


apply_option = click.option(
    "--apply", "apply_", is_flag=True, help="Execute. Without it, print the plan only."
)


@auth.command()
@click.argument("principal", callback=_principal_param)
@apply_option
def issue(principal: str, apply_: bool) -> None:
    """Create a token for PRINCIPAL (for example runner:codex)."""
    if not apply_:
        _require_unissued(principal, _load_hashes())
        _show_plan(
            "issue",
            principal,
            [
                f"generate 32 random bytes (base64url) and store them in the keychain: "
                f"service {SERVICE}, account {principal}, default ACL",
                _HASH_STEP + " with the token's SHA-256 -> principal",
                "record the creation date in the sidecar (no token, no hash)",
            ],
        )
        return
    try:
        with hashfile.exclusive_lock():
            hashes = hashfile.load_hashes()
            _require_unissued(principal, hashes)
            token = generate_token()
            store_token(principal, token)
            hashes[hash_token(token)] = principal
            hashfile.write_hashes(hashes)
            meta = hashfile.load_meta()
            meta[principal] = {"created": _now(), "rotated": None}
            hashfile.write_meta(meta)
    except (AuthError, OSError) as exc:
        raise _fail(exc) from None
    click.echo(f"issued {principal}: token stored in keychain, hash recorded")


@auth.command()
@click.argument("principal", callback=_principal_param)
@apply_option
def rotate(principal: str, apply_: bool) -> None:
    """Replace the token for PRINCIPAL; the old hash stops verifying."""
    if not apply_:
        _require_issued(principal, _load_hashes())
        _show_plan(
            "rotate",
            principal,
            [
                f"generate a new token and overwrite the keychain item (service {SERVICE}, "
                f"account {principal})",
                _HASH_STEP + "; the old hash for this principal is removed",
                "record the rotation date in the sidecar (creation date kept)",
            ],
        )
        return
    try:
        with hashfile.exclusive_lock():
            hashes = hashfile.load_hashes()
            _require_issued(principal, hashes)
            token = generate_token()
            store_token(principal, token)
            kept = {h: p for h, p in hashes.items() if p != principal}
            kept[hash_token(token)] = principal
            hashfile.write_hashes(kept)
            meta = hashfile.load_meta()
            entry: dict[str, Any] = dict(meta.get(principal) or {})
            entry.setdefault("created", _now())
            entry["rotated"] = _now()
            meta[principal] = entry
            hashfile.write_meta(meta)
    except (AuthError, OSError) as exc:
        raise _fail(exc) from None
    click.echo(f"rotated {principal}: new token in keychain, old hash removed")


@auth.command()
@click.argument("principal", callback=_principal_param)
@apply_option
def revoke(principal: str, apply_: bool) -> None:
    """Remove PRINCIPAL's hash, metadata and keychain item."""
    if not apply_:
        _load_hashes()
        _show_plan(
            "revoke",
            principal,
            [
                _HASH_STEP + f"; every hash for {principal} is removed",
                "drop the principal from the sidecar",
                f"delete the keychain item (service {SERVICE}, account {principal})",
            ],
        )
        return
    try:
        with hashfile.exclusive_lock():
            hashes = hashfile.load_hashes()
            hashfile.write_hashes({h: p for h, p in hashes.items() if p != principal})
            meta = hashfile.load_meta()
            meta.pop(principal, None)
            hashfile.write_meta(meta)
            deleted = delete_token(principal)
    except (AuthError, OSError) as exc:
        raise _fail(exc) from None
    suffix = "keychain item deleted" if deleted else "keychain item was already absent"
    click.echo(f"revoked {principal}: hash removed, {suffix}")


@auth.command(name="list")
def list_principals() -> None:
    """List issued principals and creation dates (never tokens or hashes)."""
    principals = sorted(set(_load_hashes().values()))
    if not principals:
        click.echo("no principals issued")
        return
    meta = hashfile.load_meta()
    click.echo(f"{'PRINCIPAL':<32} {'CREATED':<21} ROTATED")
    for principal in principals:
        entry = meta.get(principal) or {}
        created = entry.get("created") or "unknown"
        rotated = entry.get("rotated") or "-"
        click.echo(f"{principal:<32} {created:<21} {rotated}")
