"""Security configuration helpers for the legacy working-memory-assistant service."""

from __future__ import annotations

import os
import secrets

from cryptography.fernet import Fernet


DEV_ENVIRONMENTS = {"dev", "development", "local", "test", "testing"}
WEAK_SECRET_VALUES = {
    "dev-key-123",
    "dev-only-change-me",
    "your-secret-key-change-in-production",
    "CHANGE_ME_generate_with_openssl_rand_hex_32_placeholder",
}


def runtime_environment() -> str:
    return (
        os.getenv("ENVIRONMENT", os.getenv("DPMX_ENV", "development")).strip().lower()
        or "development"
    )


def is_development_environment(environment: str | None = None) -> bool:
    return (environment or runtime_environment()).strip().lower() in DEV_ENVIRONMENTS


def clean_secret_value(value: str | None) -> str:
    resolved = (value or "").strip()
    if not resolved or resolved in WEAK_SECRET_VALUES:
        return ""
    return resolved


def generate_token_secret() -> str:
    return secrets.token_urlsafe(32)


def generate_fernet_key() -> str:
    return Fernet.generate_key().decode("ascii")


def resolve_secret(
    var_name: str,
    *,
    allow_ephemeral_dev: bool = False,
    environment: str | None = None,
    generator=generate_token_secret,
) -> str:
    resolved = clean_secret_value(os.getenv(var_name))
    if resolved:
        return resolved

    resolved_environment = (
        (environment or runtime_environment()).strip().lower()
        or "development"
    )
    if is_development_environment(resolved_environment):
        return generator() if allow_ephemeral_dev else ""

    raise RuntimeError(
        f"{var_name} must be set to a non-placeholder value when ENVIRONMENT={resolved_environment}"
    )
