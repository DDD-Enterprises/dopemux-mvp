"""Coldstart namespace re-exports for update orchestration."""

from dopemux.update.manager import UpdateConfig, UpdateManager, UpdateResult, VersionInfo

__all__ = ["UpdateConfig", "UpdateManager", "UpdateResult", "VersionInfo"]
