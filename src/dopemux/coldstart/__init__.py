"""Cold-start extraction helpers for installer and update flows."""

from .compose_orchestrator import ComposeOrchestrator
from .network import ensure_docker_networks
from .platform import PlatformInfo, detect_platform
from .rollback_manager import RollbackManager
from .secrets_resolver import (
    SecretResolution,
    SecretResolutionError,
    SecretSource,
    is_placeholder_value,
    read_secret_from_1password,
    read_secret_from_command,
    read_secret_from_keychain,
    resolve_secret_value,
)
from .update_manager import UpdateConfig, UpdateManager, UpdateResult, VersionInfo

__all__ = [
    "ComposeOrchestrator",
    "PlatformInfo",
    "RollbackManager",
    "SecretResolution",
    "SecretResolutionError",
    "SecretSource",
    "UpdateConfig",
    "UpdateManager",
    "UpdateResult",
    "VersionInfo",
    "detect_platform",
    "ensure_docker_networks",
    "is_placeholder_value",
    "read_secret_from_1password",
    "read_secret_from_command",
    "read_secret_from_keychain",
    "resolve_secret_value",
]
