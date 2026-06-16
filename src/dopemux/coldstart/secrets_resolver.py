"""Secret resolution policy extracted from install.sh."""

from __future__ import annotations

import os
import secrets
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Sequence


Runner = Callable[..., subprocess.CompletedProcess[str]]


class SecretSource(Enum):
    MANUAL = "manual"
    KEYCHAIN = "keychain"
    ONEPASSWORD = "1password"
    COMMAND = "command"
    ENV = "env"
    DEFER = "defer"
    DEFAULT = "default"


class SecretResolutionError(RuntimeError):
    """Raised when non-interactive resolution must fail closed."""


@dataclass(frozen=True)
class SecretResolution:
    value: str | None
    source: SecretSource
    is_sensitive: bool


LOCAL_DEFAULTABLE = {
    "AGE_PASSWORD",
    "LEANTIME_URL",
    "TASK_ORCHESTRATOR_API_KEY",
    "ADHD_ENGINE_API_KEY",
    "LITELLM_MASTER_KEY",
    "LITELLM_DATABASE_URL",
}

PROVIDER_OPTIONAL = {
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "OPENROUTER_API_KEY",
    "GEMINI_API_KEY",
    "XAI_API_KEY",
    "VOYAGE_API_KEY",
    "TAVILY_API_KEY",
    "EXA_API_KEY",
    "LEANTIME_TOKEN",
    "OPENAI_WEBHOOK_SECRET",
}

SENSITIVE_VARS = LOCAL_DEFAULTABLE | PROVIDER_OPTIONAL

_DANGEROUS_DB_PASSWORD = "dopemux_age_" + "dev_" + "password"


def is_placeholder_value(value: str | None) -> bool:
    if not value:
        return False

    lowered = value.lower()
    if lowered.startswith("your_secure_"):
        return True
    if lowered.startswith("your_") and lowered.endswith("_here"):
        return True
    if lowered.startswith("dev-key-"):
        return True
    if lowered.startswith("changeme") or lowered.startswith("change_me"):
        return True
    if lowered.endswith("_placeholder"):
        return True
    if lowered == _DANGEROUS_DB_PASSWORD:
        return True
    return lowered.startswith(f"postgresql://dopemux_age:{_DANGEROUS_DB_PASSWORD}@")


def _read_env_file_value(var: str, env_file: Path | None) -> str | None:
    if env_file is None or not env_file.exists():
        return None

    value: str | None = None
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        if key == var:
            value = raw_value
    return value


def _generated_secret() -> str:
    return secrets.token_hex(32)


def _default_value(var: str, env: Mapping[str, str]) -> str | None:
    if var in {"AGE_PASSWORD", "TASK_ORCHESTRATOR_API_KEY", "ADHD_ENGINE_API_KEY"}:
        return _generated_secret()
    if var == "LEANTIME_URL":
        return "http://localhost:8097"
    if var == "LITELLM_MASTER_KEY":
        return f"sk-{secrets.token_hex(32)}"
    if var == "LITELLM_DATABASE_URL":
        age_password = env.get("AGE_PASSWORD") or _generated_secret()
        return f"postgresql://dopemux_age:{age_password}@dopemux-postgres-age:5432/litellm"
    return None


def _policy(var: str) -> str:
    if var in LOCAL_DEFAULTABLE:
        return "local-defaultable"
    if var in PROVIDER_OPTIONAL:
        return "provider-optional"
    return "boot-critical"


def _run_secret_command(args: Sequence[str], runner: Runner) -> str | None:
    try:
        result = runner(list(args), capture_output=True, text=True, check=False)
    except OSError:
        return None
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def read_secret_from_keychain(service: str, *, runner: Runner = subprocess.run) -> str | None:
    if not service:
        return None
    return _run_secret_command(
        ["security", "find-generic-password", "-w", "-s", service],
        runner,
    )


def read_secret_from_1password(ref: str, *, runner: Runner = subprocess.run) -> str | None:
    if not ref:
        return None
    return _run_secret_command(["op", "read", ref], runner)


def read_secret_from_command(command_spec: str, *, runner: Runner = subprocess.run) -> str | None:
    if not command_spec:
        return None
    return _run_secret_command(["bash", "-lc", command_spec], runner)


def resolve_secret_value(
    var: str,
    current: str | None,
    env_file: Path | None,
    non_interactive: bool = False,
    *,
    env: Mapping[str, str] | None = None,
    source: SecretSource | None = None,
    manual_value: str | None = None,
    keychain_service: str | None = None,
    onepassword_ref: str | None = None,
    command_spec: str | None = None,
    runner: Runner = subprocess.run,
) -> SecretResolution:
    """Resolve a secret according to the installer policy without logging it."""

    env_map = env if env is not None else os.environ
    sensitive = var in SENSITIVE_VARS

    candidates = [
        (current, SecretSource.ENV),
        (env_map.get(var), SecretSource.ENV),
        (_read_env_file_value(var, env_file), SecretSource.ENV),
    ]
    for value, resolved_source in candidates:
        if value and not is_placeholder_value(value):
            return SecretResolution(value=value, source=resolved_source, is_sensitive=sensitive)

    chosen_source = source or SecretSource.DEFER
    if chosen_source is SecretSource.MANUAL and manual_value:
        return SecretResolution(value=manual_value, source=SecretSource.MANUAL, is_sensitive=sensitive)

    policy = _policy(var)
    if policy == "local-defaultable":
        default = _default_value(var, env_map)
        if default is not None and isinstance(env_map, dict):
            env_map[var] = default
        return SecretResolution(value=default, source=SecretSource.DEFAULT, is_sensitive=sensitive)

    if non_interactive:
        if policy == "provider-optional":
            return SecretResolution(value=None, source=SecretSource.DEFER, is_sensitive=sensitive)
        raise SecretResolutionError(
            f"{var} is not configured. Pre-populate the env file or export it before non-interactive use."
        )

    if chosen_source is SecretSource.KEYCHAIN:
        value = read_secret_from_keychain(keychain_service or var, runner=runner)
        if value:
            return SecretResolution(value=value, source=SecretSource.KEYCHAIN, is_sensitive=sensitive)
    if chosen_source is SecretSource.ONEPASSWORD:
        value = read_secret_from_1password(onepassword_ref or "", runner=runner)
        if value:
            return SecretResolution(value=value, source=SecretSource.ONEPASSWORD, is_sensitive=sensitive)
    if chosen_source is SecretSource.COMMAND:
        value = read_secret_from_command(command_spec or "", runner=runner)
        if value:
            return SecretResolution(value=value, source=SecretSource.COMMAND, is_sensitive=sensitive)

    return SecretResolution(value=None, source=SecretSource.DEFER, is_sensitive=sensitive)
